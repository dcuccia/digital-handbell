"""Audio engine: I2S + audiomixer, MP3/WAV/synthio voices, power/mute sequencing.

Sequencing follows docs/electrical-reduction-and-placement.md:

wake:   POWER high -> wait ``settle_ms`` -> start I2S (mixer silence)
        -> wait ``clock_ms`` -> AMP_MUTE low (play) -> start queued note
sleep:  stop voices -> AMP_MUTE high -> wait ``mute_ms`` -> stop and
        deinit I2S (BCLK and LRCLK stop together) -> POWER low

I2S is deinitialized while the amplifier is unpowered so the RP2040 does not
drive clocks into an unpowered MAX98357A. Notes requested while powering up
are queued (latest wins); motion pre-wakes the path when a stroke begins.
All sources must match the mixer: mono, 16-bit signed, ``sample_rate``.
"""

import array
import math

from handbell.core import bell_model

OFF = 0
POWERING = 1
CLOCKING = 2
READY = 3
MUTING = 4
STATE_NAMES = ("off", "powering", "clocking", "ready", "muting")


def _output(pin, value):
    if pin is None:
        return None
    import digitalio

    out = digitalio.DigitalInOut(pin)
    out.switch_to_output(value=value)
    return out


class _Ramp:
    def __init__(self, start_level, now, duration_us):
        self.start_level = start_level
        self.t0 = now
        self.duration = max(1, duration_us)

    def level(self, now):
        f = (now - self.t0) / self.duration
        if f >= 1.0:
            return 0.0
        return self.start_level * (1.0 - f)


class CircuitPythonAudio:
    def __init__(self, pins, audio_cfg, power_cfg, bells):
        import audiomixer

        # Assert safe defaults first: muted, boost/amplifier input off.
        self._mute = _output(pins.get("amp_mute"), True)
        self._power = _output(pins.get("power"), False)
        self._bclk = pins["i2s_bclk"]
        self._lrclk = pins["i2s_lrclk"]
        self._data = pins["i2s_data"]
        self.sample_rate = audio_cfg["sample_rate"]
        self._file_voices = audio_cfg["voices"]
        self._retrigger = audio_cfg["retrigger"]
        self._release_s = audio_cfg["damp_ms"] / 1000.0
        kinds = [b.kind for b in bells]
        self._has_synth = "synth" in kinds
        voice_count = self._file_voices + (1 if self._has_synth else 0)
        self.mixer = audiomixer.Mixer(
            voice_count=voice_count,
            sample_rate=self.sample_rate,
            channel_count=1,
            bits_per_sample=16,
            samples_signed=True,
            buffer_size=audio_cfg["buffer_size"],
        )
        self._decoders = [None] * self._file_voices
        self._files = [None] * self._file_voices
        self._voice_bell = [None] * self._file_voices
        self._voice_start = [0] * self._file_voices
        self._ramps = [None] * self._file_voices
        self._synth = None
        self._synth_voice = self._file_voices if self._has_synth else None
        self._synth_groups = []
        self._synth_release_until = 0
        self._envelopes = {}
        if self._has_synth:
            import synthio

            self._synthio = synthio
            self._sine = array.array("h", [int(32000 * math.sin(2 * math.pi * i / 256)) for i in range(256)])
            self._synth = synthio.Synthesizer(sample_rate=self.sample_rate, channel_count=1)
        self._settle_us = int(power_cfg["settle_ms"] * 1000)
        self._clock_us = int(power_cfg["clock_ms"] * 1000)
        self._mute_us = int(power_cfg["mute_ms"] * 1000)
        self._state = OFF
        self._t_next = 0
        self._pending = None
        self._i2s = None
        self.last_start_latency_us = None

    # ----- port interface -------------------------------------------

    @property
    def state_name(self):
        return STATE_NAMES[self._state]

    def is_awake(self):
        return self._state == READY

    def wake(self, now):
        if self._state == OFF:
            if self._power is not None:
                self._power.value = True
            self._state = POWERING
            self._t_next = now + self._settle_us
        elif self._state == MUTING:
            # Cancel a sleep in progress: clocks and power are still on.
            self._set_mute(False)
            self._state = READY

    def sleep(self, now):
        if self._state == OFF or self.is_sounding(now):
            return
        if self._state == POWERING:
            if self._power is not None:
                self._power.value = False
            self._state = OFF
            return
        self._stop_voices()
        self._set_mute(True)
        self._state = MUTING
        self._t_next = now + self._mute_us

    def play(self, bell, level, now):
        if self._state != READY:
            self.wake(now)
        if self._state == READY:
            # Already awake, or a sleep in progress was just cancelled.
            self._start(bell, level, now, now)
            return
        self._pending = (bell, level, now)

    def damp(self, now, ms):
        duration = int(ms * 1000)
        for i in range(self._file_voices):
            voice = self.mixer.voice[i]
            if voice.playing:
                self._ramps[i] = _Ramp(voice.level, now, duration)
        if self._synth is not None and self._synth_groups:
            for group in self._synth_groups:
                self._synth.release(group[0])
            self._synth_groups = []
            self._synth_release_until = now + int(self._release_s * 1000000)
        self._pending = None

    def is_sounding(self, now):
        if self._pending is not None:
            return True
        if self._state != READY:
            return False
        for i in range(self._file_voices):
            if self.mixer.voice[i].playing:
                return True
        return bool(self._synth_groups) or now < self._synth_release_until

    def tick(self, now):
        state = self._state
        if state == READY:
            self._tick_ready(now)
        elif state == POWERING and now >= self._t_next:
            self._start_clocks()
            self._state = CLOCKING
            self._t_next = now + self._clock_us
        elif state == CLOCKING and now >= self._t_next:
            self._set_mute(False)
            self._state = READY
            if self._pending is not None:
                bell, level, requested = self._pending
                self._pending = None
                self._start(bell, level, now, requested)
        elif state == MUTING and now >= self._t_next:
            self._stop_clocks()
            if self._power is not None:
                self._power.value = False
            self._state = OFF

    def shutdown(self):
        self._set_mute(True)
        try:
            self._stop_voices()
        except Exception:
            pass
        self._stop_clocks()
        if self._power is not None:
            self._power.value = False
        self._state = OFF
        self._pending = None

    # ----- internals -------------------------------------------------

    def _set_mute(self, muted):
        if self._mute is not None:
            self._mute.value = muted

    def _start_clocks(self):
        import audiobusio

        self._i2s = audiobusio.I2SOut(self._bclk, self._lrclk, self._data)
        self._i2s.play(self.mixer)
        if self._synth is not None:
            self.mixer.voice[self._synth_voice].play(self._synth)

    def _stop_clocks(self):
        if self._i2s is not None:
            try:
                self._i2s.stop()
            finally:
                self._i2s.deinit()
                self._i2s = None

    def _stop_voices(self):
        for i in range(self._file_voices):
            self.mixer.voice[i].stop()
            self._ramps[i] = None
        if self._synth is not None:
            self._synth.release_all()
            self._synth_groups = []
            self._synth_release_until = 0

    def _tick_ready(self, now):
        for i in range(self._file_voices):
            ramp = self._ramps[i]
            if ramp is not None:
                level = ramp.level(now)
                voice = self.mixer.voice[i]
                if level <= 0.0:
                    voice.stop()
                    self._ramps[i] = None
                else:
                    voice.level = level
        if self._synth_groups:
            keep = []
            for group in self._synth_groups:
                if now >= group[1]:
                    self._synth.release(group[0])
                    self._synth_release_until = now + int(self._release_s * 1000000)
                else:
                    keep.append(group)
            self._synth_groups = keep

    def _start(self, bell, level, now, requested):
        self.last_start_latency_us = now - requested
        if bell.kind == "synth":
            self._start_synth(bell, level, now)
        else:
            self._start_file(bell, level, now)

    def _pick_voice(self, bell):
        if self._retrigger == "restart":
            for i in range(self._file_voices):
                if self._voice_bell[i] == bell.id and self.mixer.voice[i].playing:
                    return i
        oldest = 0
        for i in range(self._file_voices):
            if not self.mixer.voice[i].playing:
                return i
            if self._voice_start[i] < self._voice_start[oldest]:
                oldest = i
        return oldest

    def _start_file(self, bell, level, now):
        i = self._pick_voice(bell)
        voice = self.mixer.voice[i]
        voice.stop()
        self._ramps[i] = None
        if bell.kind == "mp3":
            import audiomp3

            decoder = self._decoders[i]
            if decoder is None:
                decoder = audiomp3.MP3Decoder(bell.sound)
                self._decoders[i] = decoder
            else:
                decoder.open(bell.sound)
            sample = decoder
        else:
            import audiocore

            old = self._files[i]
            if old is not None:
                old.close()
            f = open(bell.sound, "rb")
            self._files[i] = f
            sample = audiocore.WaveFile(f)
        voice.level = max(0.0, min(1.0, level))
        voice.play(sample)
        self._voice_bell[i] = bell.id
        self._voice_start[i] = now

    def _envelope(self, decay_s):
        key = int(decay_s * 1000)
        env = self._envelopes.get(key)
        if env is None:
            env = self._synthio.Envelope(
                attack_time=bell_model.ATTACK_SECONDS,
                decay_time=decay_s * bell_model.SYNTH_DECAY_FACTOR,
                release_time=self._release_s,
                attack_level=1.0,
                sustain_level=0.0,
            )
            self._envelopes[key] = env
        return env

    def _start_synth(self, bell, level, now):
        synthio = self._synthio
        notes = []
        longest = 0.0
        for freq, amp, decay in bell_model.audible_partials(bell.frequency, self.sample_rate):
            notes.append(
                synthio.Note(
                    frequency=freq,
                    waveform=self._sine,
                    envelope=self._envelope(decay),
                    amplitude=amp * level,
                )
            )
            if decay > longest:
                longest = decay
        self._synth.press(notes)
        duration = bell_model.ATTACK_SECONDS + longest * bell_model.SYNTH_DECAY_FACTOR
        self._synth_groups.append((notes, now + int(duration * 1000000)))
