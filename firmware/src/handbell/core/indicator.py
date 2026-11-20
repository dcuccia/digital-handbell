"""Non-blocking status LED patterns.

A background pattern loops (heartbeat, maintenance, error). One-shot overlays
(ring flash, selection count, locked) take priority until they finish.
Segments alternate on/off durations in milliseconds, starting with "on".
"""

BACKGROUND = {
    "off": (),
    "heartbeat": (30, 2970),
    "low_battery": (30, 150, 30, 2790),
    "critical_battery": (30, 150, 30, 150, 30, 560),
    "maintenance": (500, 500),
    "error": (100, 100),
    "on": (1000, 0),
}

ONE_SHOT = {
    "boot": (60, 80, 60, 80, 60, 300),
    "ring": (40, 40),
    "locked": (80, 80, 80, 300),
    "unlocked": (400, 200),
    "mode": (150, 100, 150, 100, 150, 300),
    "hint": (200, 100),
}

COUNT_ON_MS = 150
COUNT_OFF_MS = 200


def count_pattern(n):
    seg = []
    for _ in range(max(1, int(n))):
        seg.append(COUNT_ON_MS)
        seg.append(COUNT_OFF_MS)
    seg[-1] = 400
    return tuple(seg)


def _level(segments, elapsed_ms):
    for i, d in enumerate(segments):
        if elapsed_ms < d:
            return i % 2 == 0
        elapsed_ms -= d
    return None


class LedPattern:
    def __init__(self, background="heartbeat"):
        self._background = BACKGROUND[background]
        self._bg_start = 0
        self._overlay = None
        self._ov_start = 0

    def background(self, name, now):
        segments = BACKGROUND[name]
        if segments is not self._background:
            self._background = segments
            self._bg_start = now

    def show(self, name, now, count=None):
        self._overlay = count_pattern(count) if name == "count" else ONE_SHOT[name]
        self._ov_start = now

    def level(self, now):
        if self._overlay is not None:
            on = _level(self._overlay, (now - self._ov_start) // 1000)
            if on is not None:
                return on
            self._overlay = None
        segments = self._background
        if not segments:
            return False
        period = 0
        for d in segments:
            period += d
        if period <= 0:
            return False
        on = _level(segments, ((now - self._bg_start) // 1000) % period)
        return bool(on)
