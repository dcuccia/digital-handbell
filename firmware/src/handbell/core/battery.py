"""Battery state from a measured cell voltage (and optional USB/charge flags).

The current board has no battery-sense line (see docs/hardware-revision-requests.md),
so this runs only when a platform provides a ``PowerSense`` port. Readings
are averaged and classified with hysteresis so a voltage sag during a note
does not flicker between states. The percentage is a rough open-circuit
estimate for a 1S Li-ion cell, not a fuel gauge.
"""

STATES = ("ok", "low", "critical")

# Approximate resting voltage vs. state of charge for a 1S Li-ion cell.
# Provisional: replace with the selected cell's measured curve.
OCV_TABLE = (
    (3.30, 0),
    (3.50, 5),
    (3.60, 10),
    (3.70, 25),
    (3.75, 40),
    (3.80, 55),
    (3.90, 70),
    (4.00, 82),
    (4.10, 92),
    (4.20, 100),
)


def percent(volts):
    """Piecewise-linear estimate from ``OCV_TABLE``, clamped to 0..100."""
    if volts <= OCV_TABLE[0][0]:
        return 0
    for i in range(1, len(OCV_TABLE)):
        v1, p1 = OCV_TABLE[i]
        if volts <= v1:
            v0, p0 = OCV_TABLE[i - 1]
            return int(round(p0 + (p1 - p0) * (volts - v0) / (v1 - v0)))
    return 100


class BatteryMonitor:
    def __init__(self, low_v=3.5, critical_v=3.3, hysteresis_v=0.05, samples=8):
        if not 0 < critical_v < low_v:
            raise ValueError("battery thresholds must satisfy 0 < critical_v < low_v")
        if hysteresis_v < 0 or samples < 1:
            raise ValueError("battery hysteresis must be >= 0 and samples >= 1")
        self.low_v = low_v
        self.critical_v = critical_v
        self.hysteresis_v = hysteresis_v
        self._window = [0.0] * int(samples)
        self._count = 0
        self._next = 0
        self.volts = None
        self.state = "ok"
        self.usb = None
        self.charging = None

    def update(self, volts, usb=None, charging=None):
        """Add one reading. Return the new state if it changed, else None."""
        self.usb = usb
        self.charging = charging
        if volts is None:
            return None
        self._window[self._next] = volts
        self._next = (self._next + 1) % len(self._window)
        if self._count < len(self._window):
            self._count += 1
        total = 0.0
        for i in range(self._count):
            total += self._window[i]
        self.volts = total / self._count
        new = self._classify(self.volts)
        if new != self.state:
            self.state = new
            return new
        return None

    def _classify(self, v):
        h = self.hysteresis_v
        state = self.state
        if state == "critical":
            if v < self.critical_v + h:
                return "critical"
            return "low" if v < self.low_v + h else "ok"
        if state == "low":
            if v < self.critical_v:
                return "critical"
            return "low" if v < self.low_v + h else "ok"
        if v < self.critical_v:
            return "critical"
        return "low" if v < self.low_v else "ok"

    def status(self):
        """HGP ``status.battery`` value (None until a voltage is read)."""
        if self.volts is None:
            return None
        out = {"v": round(self.volts, 2), "pct": percent(self.volts), "state": self.state}
        if self.usb is not None:
            out["usb"] = self.usb
        if self.charging is not None:
            out["charging"] = self.charging
        return out
