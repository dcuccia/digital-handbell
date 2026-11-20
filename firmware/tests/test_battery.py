import pytest

from handbell.core.battery import BatteryMonitor, percent
from handbell.core import config
from handbell.core.instrument import Instrument
from handbell.platforms.desktop import ListLink, RecordingIndicator, SimAudio
from motion import stroke

MS = 1000


def test_percent_curve_is_monotonic_and_clamped():
    assert percent(3.0) == 0 and percent(4.3) == 100
    values = [percent(3.3 + i * 0.01) for i in range(91)]
    assert values == sorted(values)
    assert percent(3.8) == 55


def test_monitor_averages_and_uses_hysteresis():
    m = BatteryMonitor(low_v=3.5, critical_v=3.3, hysteresis_v=0.05, samples=2)
    assert m.update(3.9) is None and m.state == "ok"
    assert m.update(3.45) is None  # average 3.675: one dip is not enough
    assert m.update(3.45) == "low"
    assert m.update(3.52) is None and m.state == "low"  # average 3.485
    assert m.update(3.57) is None and m.state == "low"  # 3.545: inside the 3.50-3.55 band
    assert m.update(3.6) == "ok"  # 3.585: above low_v + hysteresis
    assert m.update(3.2) == "low"  # average 3.4
    assert m.update(3.2) == "critical"
    assert m.status() == {"v": 3.2, "pct": 0, "state": "critical"}


def test_monitor_reports_usb_and_charging_and_rejects_bad_thresholds():
    m = BatteryMonitor()
    m.update(4.1, usb=True, charging=True)
    assert m.status()["usb"] is True and m.status()["charging"] is True
    assert BatteryMonitor().status() is None
    with pytest.raises(ValueError):
        BatteryMonitor(low_v=3.3, critical_v=3.5)


def test_battery_config_validation():
    assert config.parse().battery["critical_action"] == "silence"
    with pytest.raises(ValueError, match="critical_v must be below"):
        config.parse({"battery": {"low_v": 3.2, "critical_v": 3.4}})


class FakePower:
    def __init__(self, volts, usb=None, charging=None):
        self.volts = volts
        self.usb = usb
        self.charging = charging
        self.reads = 0

    def read(self):
        self.reads += 1
        return self.volts, self.usb, self.charging


def rig(volts, raw=None, tail_s=1.0):
    raw = config.merge({"battery": {"samples": 1, "sample_s": 1}}, raw or {})
    cfg = config.parse(raw)
    audio = SimAudio(tail_s=tail_s)
    link = ListLink()
    power = FakePower(volts)
    inst = Instrument(cfg, audio, RecordingIndicator(), None, link, power)
    inst.start(0)
    inst.tick(0)
    return inst, audio, link, power


def test_no_power_sense_means_no_battery_in_status():
    cfg = config.parse()
    inst = Instrument(cfg, SimAudio())
    inst.start(0)
    inst.tick(0)
    assert "battery" not in inst.status(0)


def test_battery_reading_reported_in_status():
    inst, audio, link, power = rig(4.0)
    assert inst.status(0)["battery"] == {"v": 4.0, "pct": 82, "state": "ok"}


def test_low_battery_changes_led_and_sends_status():
    inst, audio, link, power = rig(4.0)
    power.volts = 3.4
    inst.tick(1100 * MS)
    assert link.messages("status")[-1]["battery"]["state"] == "low"
    assert inst._idle_background() == "low_battery"


def test_critical_battery_silences_playing_but_still_detects():
    inst, audio, link, power = rig(3.2)
    assert inst.silenced
    t = 0
    for t, s in stroke(1000, 600, 150, 30):
        inst.on_motion(t, s)
        inst.tick(t)
    assert audio.plays() == [] and audio.state == "off"
    assert link.messages("gesture")[-1]["g"] == "ring"


def test_critical_warn_only_keeps_playing():
    inst, audio, link, power = rig(3.2, {"battery": {"critical_action": "warn"}})
    for t, s in stroke(1000, 600, 150, 30):
        inst.on_motion(t, s)
        inst.tick(t)
    assert len(audio.plays()) == 1


def test_battery_is_not_sampled_while_sounding():
    inst, audio, link, power = rig(4.0, tail_s=3.0)
    for t, s in stroke(1000, 600, 150, 30):
        inst.on_motion(t, s)
        inst.tick(t)
    reads = power.reads
    inst.tick(2500 * MS)  # a sample is due (every 1 s) but the note still sounds
    assert audio.is_sounding(2500 * MS) and power.reads == reads
    inst.tick(4500 * MS)
    assert power.reads == reads + 1
