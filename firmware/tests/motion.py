"""Synthetic motion helpers (ported from the S1 detector tests, times in microseconds)."""

import json
import math

GRAVITY = 9.80665


def stroke(t0_ms, peak, rise_ms, stop_ms, sign=1, rate_hz=416, axis=0, gravity=True):
    """Angular speed profile: sin^2 rise to ``peak`` deg/s, cos^2 stop.

    Returns [(t_us, (ax, ay, az, gx, gy, gz))] from t0-200 ms to after the stop.
    """
    return strokes([(t0_ms, peak, rise_ms, stop_ms, sign)], rate_hz, axis, gravity, t0_ms - 200.0, t0_ms + rise_ms + stop_ms + 300.0)


def _profile(tau, peak, rise_ms, stop_ms):
    if 0 <= tau < rise_ms:
        return peak * math.sin(math.pi / 2 * tau / rise_ms) ** 2
    if rise_ms <= tau < rise_ms + stop_ms:
        return peak * math.cos(math.pi / 2 * (tau - rise_ms) / stop_ms) ** 2
    return 0.0


def strokes(specs, rate_hz=416, axis=0, gravity=True, start_ms=None, end_ms=None):
    """Sum several (t0_ms, peak, rise_ms, stop_ms, sign) strokes on one sample grid."""
    if start_ms is None:
        start_ms = min(s[0] for s in specs) - 200.0
    if end_ms is None:
        end_ms = max(s[0] + s[2] + s[3] for s in specs) + 300.0
    out = []
    period = 1000.0 / rate_hz
    t = start_ms
    while t < end_ms:
        w = 0.0
        for t0, peak, rise, stop, sign in specs:
            w += sign * _profile(t - t0, peak, rise, stop)
        g = [0.0, 0.0, 0.0]
        g[axis] = w
        az = GRAVITY if gravity else 0.0
        out.append((int(round(t * 1000)), (0.0, 0.0, az, g[0], g[1], g[2])))
        t += period
    return out


def still(t0_ms, t1_ms, rate_hz=416):
    out = []
    period = 1000.0 / rate_hz
    t = t0_ms
    while t < t1_ms:
        out.append((int(round(t * 1000)), (0.0, 0.0, GRAVITY, 0.0, 0.0, 0.0)))
        t += period
    return out


def run(detector, samples):
    found = []
    for t, s in samples:
        e = detector.push(t, *s)
        if e is not None:
            found.append(e)
    return found


def write_trace(path, samples, gestures=()):
    """Write samples as HGP raw batches (ms, m/s^2, deg/s) in JSON lines."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"type": "meta", "label": "synthetic"}) + "\n")
        batch = []
        for t, s in samples:
            batch.append([t / 1000.0] + list(s))
            if len(batch) == 100:
                f.write(json.dumps({"type": "raw", "off": 0, "cols": ["t", "ax", "ay", "az", "gx", "gy", "gz"], "s": batch}) + "\n")
                batch = []
        if batch:
            f.write(json.dumps({"type": "raw", "off": 0, "cols": ["t", "ax", "ay", "az", "gx", "gy", "gz"], "s": batch}) + "\n")
        for g in gestures:
            f.write(json.dumps(g) + "\n")
