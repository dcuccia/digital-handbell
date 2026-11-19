"""The instrument: gestures and button events in, sound/indication/messages out.

``Instrument`` holds no hardware. A platform feeds it timestamped IMU
samples and button edges, calls ``tick`` every loop, and supplies the audio,
indicator, store and link ports described in ``handbell.ports``.

Local playing never waits on the link: messages are sent after the sound has
been requested.
"""

from handbell.core import config as _config
from handbell.core import events as _events
from handbell.core.bells import BellSet
from handbell.core.controls import ButtonGrammar
from handbell.core.gestures import ImpactDetector, RingDetector
from handbell.core.indicator import LedPattern

SAVE_DELAY_US = 2000000


class _NullLink:
    def send(self, line):
        pass


class _NullIndicator:
    def set(self, on):
        pass


class _NullStore:
    def load(self):
        return None

    def save(self, state):
        pass


class Instrument:
    def __init__(self, config, audio, indicator=None, store=None, link=None):
        self.cfg = config
        self.audio = audio
        self.led = indicator if indicator is not None else _NullIndicator()
        self.store = store if store is not None else _NullStore()
        self.link = link if link is not None else _NullLink()
        self.bellset = BellSet(config.bells, config.select)
        self.ring = RingDetector(config.detector)
        self.ring.set_context(config.sensitivity)
        damp = config.damp
        self.impact = ImpactDetector(damp.get("impact") or None) if damp.get("enabled") else None
        self._damp_after_us = int(damp.get("min_after_ring_ms", 150) * 1000)
        self._damp_max_omega = damp.get("max_omega", 120.0)
        timing = config.controls["timing"]
        self.grammar = ButtonGrammar(timing["double_ms"], timing["long_ms"], timing["very_long_ms"])
        self.pattern = LedPattern("heartbeat")
        self.base_mode = config.mode
        self.mode = config.mode
        self.locked = False
        power = config.power
        self._keep_awake_us = int(power["keep_awake_s"] * 1000000)
        self._wake_on_motion = power["wake_on_motion"]
        self._wake_omega = power["wake_omega"]
        self._damp_ms = config.audio["damp_ms"]
        self._seq = 0
        self._sel_t = 0
        self._awake_until = 0
        self._awake_requested = False
        self._last_ring = None
        self._led_on = None
        self._save_due = None
        self.last_strike = None
        self.counters = {"rings": 0, "damps": 0, "selects": 0, "key_rings": 0}

    # ----- lifecycle -------------------------------------------------

    def start(self, now):
        state = self.store.load()
        if state:
            index = state.get("index", 0)
            if isinstance(index, int) and 0 <= index < len(self.bellset):
                self.bellset.index = index
            self.locked = bool(state.get("locked", False))
            if state.get("accessible"):
                self.base_mode = "accessible"
                self.mode = "accessible"
        self._sel_t = now
        self.pattern.show("boot", now)
        self._update_led(now)

    @property
    def selected(self):
        return self.bellset.selected

    def state(self, now):
        return "sounding" if self.audio.is_sounding(now) else "ready"

    def quiet(self, now):
        """True when it is a good moment for garbage collection."""
        return not self.ring.armed and not self.grammar.pressed and not self.audio.is_sounding(now)

    # ----- inputs ----------------------------------------------------

    def on_motion(self, now, sample):
        if sample is None:
            return None
        ax, ay, az, gx, gy, gz = sample
        strike = self.ring.push(now, ax, ay, az, gx, gy, gz)
        if self._wake_on_motion and (self.ring.armed or abs(self.ring.last_signal) >= self._wake_omega):
            self._wake(now)
        if strike is not None:
            self._on_strike(strike, now)
        if self.impact is not None:
            hit = self.impact.push(now, ax, ay, az)
            if (
                hit is not None
                and self._last_ring is not None
                and hit.t - self._last_ring >= self._damp_after_us
                and abs(self.ring.last_signal) <= self._damp_max_omega
            ):
                self._damp(now, hit.t, "motion")
        return strike

    def on_button(self, pressed, now):
        state = self.state(now)
        self.grammar.double_enabled = self.cfg.has_event(self.mode, state, "double")
        self._keep_awake(now)
        events = self.grammar.press(now) if pressed else self.grammar.release(now)
        for event in events:
            acted = self._dispatch(event, now, state)
            if acted and event == "down":
                # The press already did its job (damp, key ring). Its release
                # must not also select, lock or preview once the sound stops.
                self.grammar.consume_release()

    def tick(self, now):
        events = self.grammar.tick(now)
        if events:
            state = self.state(now)
            for event in events:
                self._dispatch(event, now, state)
        self.audio.tick(now)
        if self._awake_requested and now >= self._awake_until and not self.audio.is_sounding(now):
            if not self.ring.armed and not self.grammar.pressed:
                self._awake_requested = False
                self.audio.sleep(now)
        if self._save_due is not None and now >= self._save_due:
            self._save_due = None
            self.store.save(self._persisted())
        self._update_led(now)

    # ----- behavior --------------------------------------------------

    def _on_strike(self, strike, now):
        self.last_strike = strike
        self._last_ring = strike.t
        bell = self.bellset.selected
        if self.mode != "maintenance":
            level = _config.level_for(self.cfg.audio, strike.intensity) * bell.gain
            self._wake(now)
            self.audio.play(bell, level, now)
            self.counters["rings"] += 1
        self.pattern.show("ring", now)
        self._seq += 1
        self.link.send(
            _events.gesture(
                self._seq,
                "ring",
                strike.t,
                bell=bell.id,
                sel_us=self._sel_t,
                vel=strike.intensity,
                det_us=strike.fired_at - strike.t,
                src="motion",
            )
        )

    def _dispatch(self, event, now, state):
        """Perform the mapped action. Return True if an action was taken."""
        if event == "long_hint":
            self.pattern.show("hint", now)
            return False
        action = self.cfg.action_for(self.mode, state, event)
        if action == "none":
            return False
        if action == "next":
            self._select(1, now)
        elif action == "previous":
            self._select(-1, now)
        elif action == "lock":
            self.locked = not self.locked
            self.pattern.show("locked" if self.locked else "unlocked", now)
            self._schedule_save(now)
            self._send_select(now)
        elif action == "damp":
            self._damp(now, now, "key")
        elif action == "ring":
            self._key_ring(now)
        elif action == "maintenance":
            if self.mode != "maintenance":
                self.mode = "maintenance"
                if self.audio.is_sounding(now):
                    self.audio.damp(now, self._damp_ms)
                self.pattern.background("maintenance", now)
                self._send_status(now)
        elif action == "exit":
            self.mode = self.base_mode
            self.pattern.background("heartbeat", now)
            self.pattern.show("mode", now)
            self._send_status(now)
        elif action == "toggle_accessible":
            self.base_mode = "accessible" if self.base_mode == "play" else "play"
            self.mode = self.base_mode
            self.pattern.background("heartbeat", now)
            self.pattern.show("mode", now)
            self._schedule_save(now)
            self._send_status(now)
        return True

    def _select(self, delta, now):
        if self.locked or not self.bellset.can_change:
            self.pattern.show("locked", now)
            return
        self.bellset.step(delta)
        self._sel_t = now
        self.counters["selects"] += 1
        bell = self.bellset.selected
        if self.audio.is_sounding(now):
            self.audio.damp(now, self._damp_ms)
        self._wake(now)
        self.audio.play(bell, self.cfg.audio["preview_level"] * bell.gain, now)
        self.pattern.show("count", now, count=self.bellset.index + 1)
        self._schedule_save(now)
        self._send_select(now)

    def _key_ring(self, now):
        bell = self.bellset.selected
        vel = self.cfg.controls["key_velocity"]
        self._wake(now)
        self.audio.play(bell, _config.level_for(self.cfg.audio, vel) * bell.gain, now)
        self.counters["key_rings"] += 1
        self.pattern.show("ring", now)
        self._seq += 1
        self.link.send(
            _events.gesture(self._seq, "ring", now, bell=bell.id, sel_us=self._sel_t, vel=vel, det_us=0, src="key")
        )

    def _damp(self, now, t, src):
        if not self.audio.is_sounding(now):
            return
        self.audio.damp(now, self._damp_ms)
        self.counters["damps"] += 1
        self._seq += 1
        self.link.send(
            _events.gesture(self._seq, "damp", t, bell=self.bellset.selected.id, det_us=now - t, src=src)
        )

    def _wake(self, now):
        self._keep_awake(now)
        if not self._awake_requested:
            self._awake_requested = True
            self.audio.wake(now)

    def _keep_awake(self, now):
        until = now + self._keep_awake_us
        if until > self._awake_until:
            self._awake_until = until

    def _schedule_save(self, now):
        self._save_due = now + SAVE_DELAY_US

    def _persisted(self):
        return {"index": self.bellset.index, "locked": self.locked, "accessible": self.base_mode == "accessible"}

    def _update_led(self, now):
        on = self.pattern.level(now)
        if on != self._led_on:
            self._led_on = on
            self.led.set(on)

    def _send_select(self, now):
        self.link.send(
            _events.select(self.bellset.selected.id, self._sel_t, self.bellset.index, len(self.bellset), self.locked)
        )

    def _send_status(self, now):
        self.link.send(_events.status(self.status(now)))

    def status(self, now):
        return {
            "mode": self.mode,
            "bell": self.bellset.selected.id,
            "locked": self.locked,
            "awake": self.audio.is_awake(),
            "sounding": self.audio.is_sounding(now),
            "rings": self.counters["rings"],
        }
