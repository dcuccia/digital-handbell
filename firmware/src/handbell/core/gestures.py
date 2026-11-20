"""Motion gesture detectors.

``RingDetector``, ``adapt_params``, ``expected_ioi``, ``learn_axis`` and
``ImpactDetector`` are ported from Go Go HarmoniYo's phone spike
(spikes/s1-phone-bell/src/core/ring-detector.ts and impact-detector.ts at
commit 51ae4af578c76cec15783dfa6c8bcf16d40cb9dc, MIT). The port keeps the same
parameter names (snake_case), defaults and units (deg/s, deg/s^2, ms), so
tuning knowledge and recorded traces transfer between the projects.

Differences from the original:

- Sample times are integer microseconds (see handbell.core docstring).
- The stroke's deceleration history is tracked incrementally around its
  maximum instead of storing a list, to avoid allocation on the device.
- Phone accelerations exclude gravity; IMU accelerations include it. Only
  ``peak_accel`` (diagnostic) and the impact detector use acceleration. The
  impact threshold is therefore ``mean + max(min_jump, k * dev)`` instead of
  S1's ``max(min_jump, mean + k * dev)``: identical for a zero-mean phone
  signal, but the ``min_jump`` floor stays meaningful on top of gravity.
"""

import math

US_PER_MS = 1000

DEFAULT_RING_PARAMS = {
    "arm_omega": 150.0,
    "min_peak_omega": 200.0,
    "min_decel": 6000.0,
    "release_ratio": 0.5,
    "rearm_omega": 100.0,
    "refractory_ms": 150.0,
    "max_stroke_ms": 600.0,
    "time_offset_ms": 0.0,
    "axis": None,
    "interpolate": True,
    "bidirectional": False,
    "bounce_ms": 90.0,
    "bounce_ratio": 0.45,
    "reverse_ratio": 0.55,
    "reverse_window_ms": 600.0,
    "reverse_ref_max": 450.0,
    # HGP v0: vel = peak angular speed / 1000 deg/s.
    "full_scale_omega": 1000.0,
}

SENSITIVITIES = ("normal", "quick")
FAST_IOI_MS = {"normal": 400.0, "quick": 450.0}
QUICK_PARAMS = {"arm_omega": 130.0, "min_peak_omega": 170.0, "min_decel": 4500.0, "refractory_ms": 120.0}
FAST_PARAMS = {
    "normal": {"arm_omega": 110.0, "min_peak_omega": 140.0, "min_decel": 3500.0, "rearm_omega": 80.0},
    "quick": {"arm_omega": 100.0, "min_peak_omega": 120.0, "min_decel": 3000.0, "rearm_omega": 70.0},
}
FAST_REFRACTORY_RATIO = 0.6
FAST_REFRACTORY_MIN_MS = 65.0

_IDLE = 0
_STROKE = 1
_COOLDOWN = 2


def _finite(x):
    return x - x == 0


def norm3(x, y, z):
    return math.sqrt(x * x + y * y + z * z)


def normalize3(v):
    n = norm3(v[0], v[1], v[2])
    if n > 0:
        return (v[0] / n, v[1] / n, v[2] / n)
    return (0.0, 0.0, 0.0)


def dot3(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def check_ring_params(params):
    for key in params:
        if key not in DEFAULT_RING_PARAMS:
            raise ValueError("unknown ring detector parameter: %r" % (key,))
    axis = params.get("axis")
    if axis is not None:
        if len(axis) != 3 or norm3(axis[0], axis[1], axis[2]) == 0:
            raise ValueError("ring axis must be a non-zero 3-vector")


def adapt_params(base, sensitivity="normal", ioi_ms=None):
    """Effective parameters for a context (port of S1 ``adaptParams``).

    Normal sensitivity outside fast passages returns ``base`` unchanged.
    Thresholds only ever go down from ``base``.
    """
    if sensitivity not in SENSITIVITIES:
        sensitivity = "normal"
    ioi = ioi_ms if (ioi_ms is not None and _finite(ioi_ms) and ioi_ms > 0) else None
    fast = ioi is not None and ioi <= FAST_IOI_MS[sensitivity]
    if sensitivity == "normal" and not fast:
        return base
    p = dict(base)
    if sensitivity == "quick":
        for key in QUICK_PARAMS:
            p[key] = min(p[key], QUICK_PARAMS[key])
    if fast:
        f = FAST_PARAMS[sensitivity]
        for key in f:
            p[key] = min(p[key], f[key])
        p["refractory_ms"] = min(p["refractory_ms"], max(FAST_REFRACTORY_MIN_MS, FAST_REFRACTORY_RATIO * ioi))
        p["max_stroke_ms"] = min(p["max_stroke_ms"], max(250.0, 2.0 * ioi))
        p["bidirectional"] = p["axis"] is not None
    return p


def expected_ioi(times_ms, now_ms, lead_ms=250.0, tail_ms=150.0, min_gap_ms=40.0):
    """Expected inter-onset interval around ``now_ms`` from sorted note times.

    Port of S1 ``expectedIoi``; useful when a host sends cues over a link.
    """
    lo = 0
    hi = len(times_ms)
    start = now_ms - 2000.0 - tail_ms
    while lo < hi:
        mid = (lo + hi) >> 1
        if times_ms[mid] < start:
            lo = mid + 1
        else:
            hi = mid
    best = None
    prev = times_ms[lo - 1] if lo > 0 else None
    for i in range(lo, len(times_ms)):
        t = times_ms[i]
        if t - lead_ms > now_ms + 2000.0:
            break
        if prev is not None:
            gap = t - prev
            if gap >= min_gap_ms and prev - lead_ms <= now_ms <= t + tail_ms and (best is None or gap < best):
                best = gap
            if gap < min_gap_ms:
                continue
        prev = t
    return best


class Strike:
    """A detected ring. ``t`` is back-dated to the moment the stroke stopped."""

    def __init__(self, t, fired_at, peak_omega, max_decel, peak_accel, intensity, axis):
        self.t = t
        self.fired_at = fired_at
        self.peak_omega = peak_omega
        self.max_decel = max_decel
        self.peak_accel = peak_accel
        self.intensity = intensity
        self.axis = axis

    @property
    def detection_delay_us(self):
        return self.fired_at - self.t

    def __repr__(self):
        return "Strike(t=%d, peak=%.0f, decel=%.0f, vel=%.2f)" % (
            self.t,
            self.peak_omega,
            self.max_decel,
            self.intensity,
        )


class RingDetector:
    """Handbell stroke detector on gyroscope angular speed (deg/s).

    A stroke arms above ``arm_omega``, tracks its peak and ends below
    ``release_ratio * peak``. It is a ring only if the peak is high enough and
    the stop was abrupt (maximum deceleration above ``min_decel``). The strike
    time is the moment of maximum deceleration, with parabolic interpolation.
    """

    def __init__(self, params=None):
        p = dict(DEFAULT_RING_PARAMS)
        if params:
            check_ring_params(params)
            p.update(params)
        if p["axis"] is not None:
            p["axis"] = normalize3(p["axis"])
        self.params = p
        self._sensitivity = "normal"
        self._ioi_ms = None
        self._apply()
        self.reset()

    def set_params(self, params):
        check_ring_params(params)
        self.params.update(params)
        if self.params["axis"] is not None:
            self.params["axis"] = normalize3(self.params["axis"])
        self._apply()

    def set_context(self, sensitivity="normal", ioi_ms=None):
        self._sensitivity = sensitivity
        self._ioi_ms = ioi_ms
        self._apply()

    def effective(self):
        return adapt_params(self.params, self._sensitivity, self._ioi_ms)

    def _apply(self):
        e = self.effective()
        self._arm = e["arm_omega"]
        self._min_peak = e["min_peak_omega"]
        self._min_decel = e["min_decel"]
        self._release = e["release_ratio"]
        self._rearm = e["rearm_omega"]
        self._refractory_us = int(e["refractory_ms"] * US_PER_MS)
        self._max_stroke_us = int(e["max_stroke_ms"] * US_PER_MS)
        self._offset_us = int(e["time_offset_ms"] * US_PER_MS)
        self._axis = e["axis"]
        self._interpolate = e["interpolate"]
        self._both = bool(e["bidirectional"]) and e["axis"] is not None
        self._bounce_us = int(e["bounce_ms"] * US_PER_MS)
        self._bounce_ratio = e["bounce_ratio"]
        self._reverse_ratio = e["reverse_ratio"]
        self._reverse_window_us = int(e["reverse_window_ms"] * US_PER_MS)
        self._reverse_ref_max = e["reverse_ref_max"]
        self._full_scale = e["full_scale_omega"]

    def reset(self):
        self._state = _IDLE
        self._prev_t = None
        self._prev_w = 0.0
        self._dir = 1
        self._stroke_start = 0
        self._peak = 0.0
        self._peak_vec = (0.0, 0.0, 0.0)
        self._peak_acc = 0.0
        self._last_fire = None
        self._last_peak = 0.0
        self._bounce_candidate = False
        self._reverse_candidate = False
        self.last_signal = 0.0
        self._reset_decels()

    def _reset_decels(self):
        self._n = 0
        self._best_i = -1
        self._best_t = 0.0
        self._best_d = 0.0
        self._prev_dt = None
        self._prev_dd = 0.0
        self._next_dt = None
        self._next_dd = 0.0
        self._last_dt = None
        self._last_dd = 0.0

    @property
    def armed(self):
        """True while a stroke is in progress (useful to pre-wake audio)."""
        return self._state == _STROKE

    def _since_fire(self, t):
        if self._last_fire is None:
            return 1 << 40
        return t - self._last_fire

    def signal(self, gx, gy, gz):
        if self._axis is not None:
            a = self._axis
            return gx * a[0] + gy * a[1] + gz * a[2]
        return norm3(gx, gy, gz)

    def push(self, t, ax, ay, az, gx, gy, gz):
        """Feed one sample. Return a ``Strike`` when a ring completes."""
        w = self.signal(gx, gy, gz)
        if not _finite(w):
            return None
        self.last_signal = w
        acc = norm3(ax, ay, az) if _finite(ax) else 0.0
        prev_t = self._prev_t
        prev_w = self._prev_w
        self._prev_t = t
        self._prev_w = w
        if prev_t is None:
            return None
        dt_us = t - prev_t
        if not dt_us > 0 or dt_us > 200000:
            self._state = _COOLDOWN
            return None

        if self._state == _COOLDOWN:
            if self._both and -self._dir * w >= self._arm:
                self._start(-self._dir, t, w, acc, gx, gy, gz)
                return None
            if self._dir * w < self._rearm and self._since_fire(t) >= self._refractory_us:
                self._state = _IDLE
            return None

        if self._state == _IDLE:
            if w >= self._arm:
                self._start(1, t, w, acc, gx, gy, gz)
            elif self._both and -w >= self._arm:
                self._start(-1, t, w, acc, gx, gy, gz)
            return None

        sw = self._dir * w
        rel_mid = (prev_t - self._stroke_start) + dt_us / 2.0
        self._add_decel(rel_mid, self._dir * (prev_w - w) / (dt_us / 1e6))
        if sw > self._peak:
            self._peak = sw
            self._peak_vec = (gx, gy, gz)
        if acc > self._peak_acc:
            self._peak_acc = acc
        if sw < self._release * self._peak:
            self._state = _COOLDOWN
            return self._finish(t)
        if t - self._stroke_start > self._max_stroke_us:
            self._state = _COOLDOWN
        return None

    def _start(self, direction, t, w, acc, gx, gy, gz):
        since = self._since_fire(t)
        self._bounce_candidate = direction != self._dir and since < self._bounce_us
        self._reverse_candidate = direction == -1 and since < self._reverse_window_us
        self._dir = direction
        self._state = _STROKE
        self._stroke_start = t
        self._peak = direction * w
        self._peak_vec = (gx, gy, gz)
        self._peak_acc = acc
        self._reset_decels()

    def _add_decel(self, rel_t, d):
        i = self._n
        if i == 0 or d > self._best_d:
            self._best_i = i
            self._best_t = rel_t
            self._best_d = d
            self._prev_dt = self._last_dt
            self._prev_dd = self._last_dd
            self._next_dt = None
        elif self._next_dt is None and i == self._best_i + 1:
            self._next_dt = rel_t
            self._next_dd = d
        self._last_dt = rel_t
        self._last_dd = d
        self._n = i + 1

    def _finish(self, now):
        if self._n == 0:
            return None
        peak = self._peak
        max_decel = self._best_d
        if peak < self._min_peak or max_decel < self._min_decel or self._since_fire(now) < self._refractory_us:
            return None
        if self._bounce_candidate and peak < self._bounce_ratio * self._last_peak:
            return None
        if self._reverse_candidate and peak < self._reverse_ratio * min(self._last_peak, self._reverse_ref_max):
            return None
        rel = self._best_t
        if self._interpolate and self._prev_dt is not None and self._next_dt is not None:
            a = self._prev_dd
            b = self._best_d
            c = self._next_dd
            den = a - 2.0 * b + c
            if den < 0:
                delta = max(-0.5, min(0.5, (0.5 * (a - c)) / den))
                spacing = (self._next_dt - rel) if delta > 0 else (rel - self._prev_dt)
                rel += delta * spacing
        self._last_fire = now
        self._last_peak = peak
        intensity = max(0.0, min(1.0, peak / self._full_scale))
        return Strike(
            self._stroke_start + int(round(rel)) + self._offset_us,
            now,
            peak,
            max_decel,
            self._peak_acc,
            intensity,
            normalize3(self._peak_vec),
        )


def learn_axis(strikes, min_strikes=3):
    """Learn the forward-stroke axis from direction-agnostic strikes.

    Port of S1 ``learnAxis``: strikes are split by sign relative to the most
    abrupt one; the larger group is "forward" (ties: sharper stops).
    """
    if len(strikes) < min_strikes:
        return None
    ref = strikes[0]
    for s in strikes:
        if s.max_decel > ref.max_decel:
            ref = s
    r = ref.axis
    sums = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    decel = [0.0, 0.0]
    count = [0, 0]
    for s in strikes:
        g = 0 if dot3(s.axis, r) >= 0 else 1
        sign = 1.0 if g == 0 else -1.0
        for k in range(3):
            sums[g][k] += sign * s.axis[k]
        decel[g] += s.max_decel
        count[g] += 1

    def mean(g):
        return decel[g] / count[g] if count[g] else 0.0

    if count[0] != count[1]:
        fwd = 0 if count[0] > count[1] else 1
    else:
        fwd = 0 if mean(0) >= mean(1) else 1
    if count[fwd] < min_strikes:
        return None
    axis = normalize3(sums[fwd])
    if fwd == 0:
        return axis
    return (-axis[0], -axis[1], -axis[2])


DEFAULT_IMPACT_PARAMS = {
    "min_jump": 4.0,
    "k": 10.0,
    "refractory_ms": 250.0,
    "alpha": 0.05,
    "time_offset_ms": 0.0,
}


class Impact:
    def __init__(self, t, fired_at, peak, threshold):
        self.t = t
        self.fired_at = fired_at
        self.peak = peak
        self.threshold = threshold


class ImpactDetector:
    """Sharp knock detector on acceleration magnitude (m/s^2).

    The threshold adapts to the noise floor:
    ``mean + max(min_jump, k * mean_abs_dev)`` (see module notes).
    """

    def __init__(self, params=None):
        p = dict(DEFAULT_IMPACT_PARAMS)
        if params:
            for key in params:
                if key not in DEFAULT_IMPACT_PARAMS:
                    raise ValueError("unknown impact detector parameter: %r" % (key,))
            p.update(params)
        self.params = p
        self._refractory_us = int(p["refractory_ms"] * US_PER_MS)
        self._offset_us = int(p["time_offset_ms"] * US_PER_MS)
        self.reset()

    def reset(self):
        self._mean = None
        self._dev = 0.0
        self._prev_t = None
        self._prev_a = 0.0
        self._last_fire = None
        self._pending = None

    def _since_fire(self, t):
        if self._last_fire is None:
            return 1 << 40
        return t - self._last_fire

    def push(self, t, ax, ay, az):
        p = self.params
        if not _finite(ax):
            return None
        a = norm3(ax, ay, az)
        prev_t = self._prev_t
        prev_a = self._prev_a
        self._prev_t = t
        self._prev_a = a
        if self._mean is None:
            self._mean = a
            return None
        thr = self._mean + max(p["min_jump"], p["k"] * self._dev)
        out = None
        if a > thr and prev_t is not None and prev_a <= thr and self._since_fire(t) >= self._refractory_us:
            self._last_fire = t
            out = Impact((prev_t + t) // 2 + self._offset_us, t, a, thr)
            self._pending = out
        elif self._pending is not None and a > self._pending.peak and t - self._pending.fired_at < self._refractory_us:
            self._pending.peak = a
        if self._since_fire(t) >= self._refractory_us and a <= thr:
            self._mean += p["alpha"] * (a - self._mean)
            self._dev += p["alpha"] * (abs(a - self._mean) - self._dev)
        return out
