"""Instrument configuration (``bells.json`` on CIRCUITPY).

The shape mirrors HGP's ``assign`` message where the concepts overlap
(``bells``, ``select``, ``ring.sens``) so a future paired host could send
the same data over a link. Unknown top-level keys are rejected to catch
typos; missing keys take the defaults below.
"""

from handbell.core import bells as _bells
from handbell.core import controls as _controls
from handbell.core import gestures as _gestures

ACTIONS = (
    "none",
    "next",
    "previous",
    "lock",
    "damp",
    "ring",
    "maintenance",
    "exit",
    "toggle_accessible",
    "volume",
    "volume_up",
    "volume_down",
)
MODES = ("play", "accessible", "maintenance")
STATES = ("ready", "sounding", "any")
RETRIGGER = ("overlap", "restart")
WAKE_ODR_HZ = (13, 26, 52, 104)

DEFAULTS = {
    "v": 0,
    "name": "handbell",
    "bells": [
        {"id": "C5", "sound": "sounds/C5.mp3"},
        {"id": "D5", "sound": "sounds/D5.mp3"},
        {"id": "E5", "sound": "sounds/E5.mp3"},
        {"id": "F5", "sound": "sounds/F5.mp3"},
        {"id": "G5", "sound": "sounds/G5.mp3"},
        {"id": "A5", "sound": "sounds/A5.mp3"},
        {"id": "B5", "sound": "sounds/B5.mp3"},
        {"id": "C6", "sound": "sounds/C6.mp3"},
    ],
    "select": "cycle",
    "mode": "play",
    "ring": {"sens": "normal"},
    "detector": {},
    "damp": {
        "enabled": False,
        "min_after_ring_ms": 150,
        "max_omega": 120.0,
        "impact": {},
    },
    "controls": {
        "timing": {"double_ms": 300, "long_ms": 800, "very_long_ms": 5000},
        "key_velocity": 0.6,
        "play": {
            "ready": {"click": "next", "double": "previous", "long": "lock", "very_long": "maintenance"},
            "sounding": {"down": "damp", "very_long": "maintenance"},
        },
        "accessible": {
            "any": {"down": "ring", "very_long": "maintenance"},
        },
        "maintenance": {
            "any": {"click": "exit", "double": "toggle_accessible", "long": "volume", "very_long": "exit"},
        },
    },
    "audio": {
        "sample_rate": 22050,
        "voices": 2,
        "buffer_size": 2048,
        "retrigger": "overlap",
        "damp_ms": 60,
        # Conservative until speaker/level limits are measured (see docs).
        "level": {"min": 0.15, "max": 0.5, "curve": 0.7},
        "preview_level": 0.2,
        # Player volume steps: multipliers on every level above, so volume can
        # never exceed audio.level.max. "volume" is the default step (index);
        # the chosen step persists across power cycles.
        "volumes": [0.25, 0.5, 0.75, 1.0],
        "volume": 3,
    },
    "power": {
        "keep_awake_s": 20,
        "settle_ms": 50,
        "clock_ms": 5,
        "mute_ms": 5,
        "wake_on_motion": True,
        "wake_omega": 100.0,
    },
    "imu": {"rate_hz": 416, "gyro_dps": 2000, "accel_g": 16, "fast_read": True},
    # Inactivity deep sleep (boards with an IMU interrupt line). The IMU stays in
    # low-power wake-up mode; a shake (wake_mg) or the button wakes the board,
    # which restarts and plays the selected bell. after_s: 0 disables sleep.
    "sleep": {
        "after_s": 120,
        "activity_omega": 30.0,
        "wake_mg": 250,
        "wake_odr_hz": 26,
        "button_wakes": True,
        "announce_wake": True,
        "announce_power_on": True,
    },
    # Used only when the platform has a battery-sense line (not the Nov 2026 board).
    # Thresholds are provisional until measured with the selected cell under load.
    "battery": {
        "low_v": 3.5,
        "critical_v": 3.3,
        "hysteresis_v": 0.05,
        "samples": 8,
        "sample_s": 2,
        "critical_action": "silence",
    },
    "debug": {"events": True, "status_s": 5, "raw": False},
}


def merge(base, override):
    """Recursively merge ``override`` into a copy of ``base``.

    Dicts merge; every other value (including lists) replaces.
    """
    out = {}
    for key in base:
        out[key] = base[key]
    for key in override:
        b = out.get(key)
        o = override[key]
        if isinstance(b, dict) and isinstance(o, dict):
            out[key] = merge(b, o)
        else:
            out[key] = o
    return out


def _require(cond, message):
    if not cond:
        raise ValueError(message)


def _number(section, key, lo, hi):
    value = section[key]
    _require(
        isinstance(value, (int, float)) and not isinstance(value, bool) and lo <= value <= hi,
        "%s must be a number in [%s, %s], got %r" % (key, lo, hi, value),
    )
    return value


class Config:
    """Validated configuration. ``raw`` keeps the merged dictionary."""

    def __init__(self, raw):
        self.raw = raw
        for key in raw:
            _require(key in DEFAULTS, "unknown configuration key: %r" % (key,))
        self.name = str(raw["name"])
        self.select = raw["select"]
        _require(self.select in _bells.SELECT_SCHEMES, "select must be one of %r" % (_bells.SELECT_SCHEMES,))
        self.mode = raw["mode"]
        _require(self.mode in ("play", "accessible"), "mode must be 'play' or 'accessible'")
        self.bells = self._parse_bells(raw["bells"])
        self.sensitivity = raw["ring"].get("sens", "normal")
        _require(self.sensitivity in _gestures.SENSITIVITIES, "ring.sens must be one of %r" % (_gestures.SENSITIVITIES,))
        self.detector = dict(raw["detector"])
        _gestures.check_ring_params(self.detector)
        self.damp = raw["damp"]
        self.controls = raw["controls"]
        self._check_controls(self.controls)
        self.audio = raw["audio"]
        self._check_audio(self.audio)
        self.power = raw["power"]
        _number(self.power, "keep_awake_s", 0, 3600)
        _number(self.power, "settle_ms", 0, 2000)
        _number(self.power, "clock_ms", 0, 1000)
        _number(self.power, "mute_ms", 0, 1000)
        _number(self.power, "wake_omega", 0, 4000)
        self.imu = raw["imu"]
        _require(self.imu["rate_hz"] in (104, 208, 416, 833, 1660), "imu.rate_hz must be 104, 208, 416, 833 or 1660")
        _require(self.imu["gyro_dps"] in (125, 250, 500, 1000, 2000), "imu.gyro_dps must be 125..2000")
        _require(self.imu["accel_g"] in (2, 4, 8, 16), "imu.accel_g must be 2, 4, 8 or 16")
        self.battery = raw["battery"]
        b = self.battery
        _number(b, "low_v", 2.5, 4.3)
        _number(b, "critical_v", 2.5, 4.3)
        _number(b, "hysteresis_v", 0.0, 0.5)
        _number(b, "samples", 1, 64)
        _number(b, "sample_s", 0.1, 600)
        _require(b["critical_v"] < b["low_v"], "battery.critical_v must be below battery.low_v")
        _require(b["critical_action"] in ("silence", "warn"), "battery.critical_action must be 'silence' or 'warn'")
        self.sleep = raw["sleep"]
        s = self.sleep
        _number(s, "after_s", 0, 86400)
        _number(s, "activity_omega", 1, 2000)
        # Wake-up threshold LSB is 2 g / 64 = 31.25 mg (accelerometer at +/-2 g while asleep).
        _number(s, "wake_mg", 32, 1968)
        _require(s["wake_odr_hz"] in WAKE_ODR_HZ, "sleep.wake_odr_hz must be one of %r" % (WAKE_ODR_HZ,))
        for key in ("button_wakes", "announce_wake", "announce_power_on"):
            _require(isinstance(s[key], bool), "sleep.%s must be true or false" % key)
        self.debug = raw["debug"]

    @staticmethod
    def _parse_bells(items):
        _require(isinstance(items, list) and items, "bells must be a non-empty list")
        out = []
        seen = []
        for item in items:
            _require(isinstance(item, dict) and "id" in item, "each bell needs an 'id' such as 'C5'")
            bell = _bells.Bell(item["id"], item.get("sound", "synth"), item.get("gain", 1.0), item.get("label"))
            _require(bell.id not in seen, "duplicate bell id: %s" % bell.id)
            _require(bell.kind != "unknown", "bell %s: sound must be 'synth' or a .mp3/.wav path" % bell.id)
            _require(0.0 <= bell.gain <= 1.0, "bell %s: gain must be within [0, 1]" % bell.id)
            seen.append(bell.id)
            out.append(bell)
        return out

    @staticmethod
    def _check_controls(c):
        t = c["timing"]
        _controls.ButtonGrammar(t["double_ms"], t["long_ms"], t["very_long_ms"])
        _number(c, "key_velocity", 0.0, 1.0)
        for mode in MODES:
            table = c.get(mode, {})
            for state in table:
                _require(state in STATES, "controls.%s: unknown state %r" % (mode, state))
                for event in table[state]:
                    _require(event in _controls.EVENTS, "controls.%s.%s: unknown event %r" % (mode, state, event))
                    action = table[state][event]
                    _require(action in ACTIONS, "controls.%s.%s.%s: unknown action %r" % (mode, state, event, action))

    @staticmethod
    def _check_audio(a):
        _require(a["sample_rate"] in (8000, 11025, 16000, 22050, 32000, 44100), "audio.sample_rate unsupported")
        _require(a["voices"] in (1, 2, 3, 4), "audio.voices must be 1..4")
        _require(a["retrigger"] in RETRIGGER, "audio.retrigger must be one of %r" % (RETRIGGER,))
        _number(a, "damp_ms", 1, 2000)
        _number(a, "preview_level", 0.0, 1.0)
        level = a["level"]
        _number(level, "min", 0.0, 1.0)
        _number(level, "max", 0.0, 1.0)
        _number(level, "curve", 0.1, 5.0)
        _require(level["min"] <= level["max"], "audio.level.min must not exceed audio.level.max")
        steps = a["volumes"]
        _require(isinstance(steps, list) and 1 <= len(steps) <= 10, "audio.volumes must be a list of 1-10 steps")
        for v in steps:
            _require(
                isinstance(v, (int, float)) and not isinstance(v, bool) and 0.0 < v <= 1.0,
                "audio.volumes steps must be numbers in (0, 1], got %r" % (v,),
            )
        _require(
            isinstance(a["volume"], int) and not isinstance(a["volume"], bool) and 0 <= a["volume"] < len(steps),
            "audio.volume must be an index into audio.volumes (0..%d)" % (len(steps) - 1),
        )

    def action_for(self, mode, state, event):
        table = self.controls.get(mode, {})
        for key in (state, "any"):
            row = table.get(key)
            if row and event in row:
                return row[event]
        return "none"

    def has_event(self, mode, state, event):
        return self.action_for(mode, state, event) != "none"


def parse(raw=None):
    """Merge ``raw`` (a dict from bells.json, or None) over the defaults."""
    return Config(merge(DEFAULTS, raw or {}))


def level_for(audio, velocity):
    """Map HGP velocity (0..1) to a playback level within audio.level."""
    lv = audio["level"]
    v = max(0.0, min(1.0, velocity))
    return lv["min"] + (lv["max"] - lv["min"]) * (v ** lv["curve"])
