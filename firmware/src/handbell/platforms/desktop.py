"""CPython simulation platform for tests, trace replay and tuning.

Not copied to the device (``build.py`` excludes it).
"""

import json

from handbell.core import bell_model, events


class FakeClock:
    def __init__(self, t=0):
        self.t = t

    def now_us(self):
        return self.t

    def advance_ms(self, ms):
        self.t += int(ms * 1000)
        return self.t


class ListLink:
    def __init__(self):
        self.lines = []

    def send(self, line):
        self.lines.append(line)

    def poll(self):
        return ()

    def messages(self, kind=None):
        out = [json.loads(line) for line in self.lines]
        if kind is None:
            return out
        return [m for m in out if m.get("type") == kind]


class RecordingIndicator:
    def __init__(self):
        self.on = False
        self.changes = 0

    def set(self, on):
        self.on = on
        self.changes += 1


class SimAudio:
    """Models the real engine's observable behavior without sound.

    Power-up takes ``settle_ms + clock_ms``; plays requested before then are
    queued (latest wins), as on hardware. A note sounds for its modelled tail
    unless damped.
    """

    OFF, POWERING, READY = "off", "powering", "ready"

    def __init__(self, settle_ms=50, clock_ms=5, tail_s=None):
        self.state = self.OFF
        self._ready_at = 0
        self._pending = None
        self._tail_us = int((tail_s if tail_s is not None else bell_model.tail_seconds()) * 1000000)
        self._settle_us = int((settle_ms + clock_ms) * 1000)
        self.voices = []
        self.log = []

    def wake(self, now):
        if self.state == self.OFF:
            self.state = self.POWERING
            self._ready_at = now + self._settle_us
            self.log.append(("wake", now))

    def sleep(self, now):
        if self.state != self.OFF and not self.is_sounding(now):
            self.state = self.OFF
            self._pending = None
            self.log.append(("sleep", now))

    def is_awake(self):
        return self.state == self.READY

    def play(self, bell, level, now):
        if self.state != self.READY:
            self.wake(now)
        if self.state == self.READY:
            self._start(bell, level, now, now)
            return
        self._pending = (bell, level, now)

    def _start(self, bell, level, now, requested):
        self.voices.append([bell, level, now, now + self._tail_us])
        self.log.append(("play", now, bell.id, round(level, 4), now - requested))

    def damp(self, now, ms):
        end = now + int(ms * 1000)
        for v in self.voices:
            if v[3] > end:
                v[3] = end
        self.log.append(("damp", now))

    def is_sounding(self, now):
        for v in self.voices:
            if v[3] > now:
                return True
        return self._pending is not None

    def tick(self, now):
        if self.state == self.POWERING and now >= self._ready_at:
            self.state = self.READY
            if self._pending is not None:
                bell, level, requested = self._pending
                self._pending = None
                self._start(bell, level, now, requested)
        self.voices = [v for v in self.voices if v[3] > now]

    def shutdown(self):
        self.state = self.OFF
        self.voices = []

    def plays(self):
        return [entry for entry in self.log if entry[0] == "play"]


def read_trace(path):
    """Yield ``(t_us, (ax, ay, az, gx, gy, gz))`` from a JSON-lines trace.

    Accepts HGP ``raw`` batches (``cols`` + ``s`` rows in ms, m/s^2, deg/s)
    and ignores other message types.
    """
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            msg = json.loads(line)
            if msg.get("type") != "raw":
                continue
            cols = msg.get("cols", list(events.RAW_COLS))
            idx = [cols.index(c) for c in events.RAW_COLS]
            for row in msg["s"]:
                t_us = int(round(float(row[idx[0]]) * 1000))
                yield t_us, tuple(float(row[i]) for i in idx[1:])


def read_gestures(path):
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("{"):
                msg = json.loads(line)
                if msg.get("type") == "gesture":
                    out.append(msg)
    return out
