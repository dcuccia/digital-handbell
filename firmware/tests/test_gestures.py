import pytest

from handbell.core.gestures import (
    DEFAULT_RING_PARAMS,
    ImpactDetector,
    RingDetector,
    Strike,
    adapt_params,
    expected_ioi,
    learn_axis,
)
from motion import run, stroke, strokes


@pytest.mark.parametrize("rate", [60, 416])
def test_one_abrupt_stroke_gives_one_strike_near_max_deceleration(rate):
    d = RingDetector()
    events = run(d, stroke(1000, 500, 150, 30, rate_hz=rate))
    assert len(events) == 1
    truth_us = (1000 + 150 + 15) * 1000
    assert abs(events[0].t - truth_us) < 10000
    assert events[0].fired_at >= events[0].t
    assert [round(v) for v in events[0].axis] == [1, 0, 0]


def test_416hz_strike_time_is_close():
    events = run(RingDetector(), stroke(1000, 500, 150, 30, rate_hz=416))
    assert abs(events[0].t - 1165000) < 3000


def test_smooth_swing_is_rejected():
    assert run(RingDetector(), stroke(1000, 400, 300, 300)) == []


def test_calibrated_axis_ignores_return_direction():
    d = RingDetector({"axis": [1, 0, 0]})
    assert run(d, stroke(1000, 500, 150, 30, sign=-1)) == []
    assert len(run(d, stroke(3000, 500, 150, 30, sign=1))) == 1


def test_refractory_suppresses_immediate_double_trigger():
    # Second abrupt stroke stops ~100 ms after the first: inside the 150 ms refractory.
    d = RingDetector()
    assert len(run(d, strokes([(1000, 500, 150, 30, 1), (1200, 500, 60, 20, 1)]))) == 1
    d = RingDetector()
    assert len(run(d, strokes([(1000, 500, 150, 30, 1), (1400, 500, 60, 20, 1)]))) == 2


def test_velocity_is_peak_over_full_scale():
    e = run(RingDetector(), stroke(1000, 500, 150, 30))[0]
    assert 0.45 < e.intensity <= 0.5
    e2 = run(RingDetector(), stroke(1000, 1800, 150, 30))[0]
    assert e2.intensity == 1.0


def test_armed_while_stroke_in_progress():
    d = RingDetector()
    armed = False
    for t, s in stroke(1000, 500, 150, 30):
        d.push(t, *s)
        armed = armed or d.armed
    assert armed and not d.armed


def test_sensor_gap_abandons_stroke():
    d = RingDetector()
    samples = stroke(1000, 500, 150, 30)
    cut = [s for s in samples if not (1100000 < s[0] < 1400000)]
    assert run(d, cut) == []


def test_unknown_parameter_rejected():
    with pytest.raises(ValueError):
        RingDetector({"armOmega": 1})


def test_learn_axis_picks_majority_direction():
    def mk(sign, decel):
        return Strike(0, 0, 500, decel, 0, 0.5, (sign, 0, 0))

    axis = learn_axis([mk(-1, 9000), mk(-1, 8000), mk(-1, 7000), mk(1, 20000)])
    assert [round(v) for v in axis] == [-1, 0, 0]
    assert learn_axis([mk(1, 1)]) is None


def test_adapt_params_normal_unchanged_and_fast_lowers_thresholds():
    base = dict(DEFAULT_RING_PARAMS)
    assert adapt_params(base) is base
    fast = adapt_params(base, "normal", 200)
    assert fast["arm_omega"] == 110 and fast["refractory_ms"] == pytest.approx(120)
    assert fast["max_stroke_ms"] == 400
    assert fast["bidirectional"] is False
    assert adapt_params(dict(base, axis=(1, 0, 0)), "normal", 200)["bidirectional"] is True
    quick = adapt_params(base, "quick")
    assert quick["min_decel"] == 4500 and quick["refractory_ms"] == 120


def test_expected_ioi_shortest_gap_around_now():
    times = [0, 500, 1000, 1250, 1500, 3000]
    assert expected_ioi(times, 1100) == 250
    assert expected_ioi(times, 10000) is None


def test_impact_detector_fires_once_on_spike_with_gravity_floor():
    d = ImpactDetector()
    events = []
    for i in range(240):
        t = i * 2404
        a = 9.8 + (25.0 if i == 120 else (8.0 if i == 121 else 0.05 * ((i % 7) - 3)))
        e = d.push(t, 0.0, 0.0, a)
        if e:
            events.append(e)
    assert len(events) == 1
    assert events[0].t == (119 * 2404 + 120 * 2404) // 2
