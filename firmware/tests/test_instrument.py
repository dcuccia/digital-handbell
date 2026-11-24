"""Instrument behavior with the simulated platform (no hardware)."""

import pytest

from handbell.core import config
from handbell.core.instrument import Instrument
from handbell.platforms.desktop import ListLink, RecordingIndicator, SimAudio
from handbell.ports import MemoryStore
from motion import still, stroke

MS = 1000


class Rig:
    def __init__(self, raw=None, store_state=None):
        self.cfg = config.parse(raw)
        self.audio = SimAudio(self.cfg.power["settle_ms"], self.cfg.power["clock_ms"], tail_s=2.0)
        self.link = ListLink()
        self.led = RecordingIndicator()
        self.store = MemoryStore(store_state)
        self.inst = Instrument(self.cfg, self.audio, self.led, self.store, self.link)
        self.t = 0
        self.inst.start(0)

    def motion(self, samples):
        for t, s in samples:
            self.t = t
            self.inst.on_motion(t, s)
            self.inst.tick(t)

    def idle(self, ms, step_ms=5):
        end = self.t + int(ms * MS)
        while self.t < end:
            self.t += step_ms * MS
            self.inst.tick(self.t)

    def press(self, hold_ms=60):
        self.inst.on_button(True, self.t)
        self.idle(hold_ms)
        self.inst.on_button(False, self.t)


def test_ring_plays_selected_bell_after_power_up_and_reports_hgp_gesture():
    rig = Rig()
    rig.motion(stroke(1000, 600, 150, 30))
    plays = rig.audio.plays()
    assert len(plays) == 1
    _, t, bell, level, delay = plays[0]
    assert bell == "C5"
    assert 0.15 < level < 0.5
    # Motion pre-wakes the amplifier while the stroke is under way, so the
    # strike starts immediately instead of waiting for power-up.
    assert delay == 0
    msg = rig.link.messages("gesture")[0]
    assert msg["g"] == "ring" and msg["bell"] == "C5" and msg["src"] == "motion"
    assert msg["det"] >= 0 and 1150 <= msg["t"] <= 1180


def test_cold_strike_without_prewake_waits_for_power_up():
    rig = Rig({"power": {"wake_on_motion": False}})
    rig.motion(stroke(1000, 600, 150, 30))
    rig.idle(100)
    _, _, _, _, delay = rig.audio.plays()[0]
    assert delay == pytest.approx(55 * MS, abs=6 * MS)


def test_click_selects_next_bell_with_preview_and_persists_after_delay():
    rig = Rig()
    rig.press()
    rig.idle(400)
    assert rig.inst.selected.id == "D5"
    assert rig.audio.plays()[-1][2] == "D5"
    assert rig.audio.plays()[-1][3] == pytest.approx(0.2)
    assert rig.link.messages("select")[-1]["bell"] == "D5"
    assert rig.store.saves == 0
    rig.idle(2100)
    assert rig.store.state == {"index": 1, "locked": False, "accessible": False, "volume": 3}


def test_double_click_selects_previous():
    rig = Rig()
    rig.press()
    rig.idle(100)
    rig.press()
    rig.idle(3000)
    assert rig.inst.selected.id == "C6"


def test_press_while_sounding_damps_immediately():
    rig = Rig()
    rig.motion(stroke(1000, 600, 150, 30))
    assert rig.audio.is_sounding(rig.t)
    rig.inst.on_button(True, rig.t)
    assert rig.audio.log[-1][0] == "damp"
    assert rig.link.messages("gesture")[-1]["g"] == "damp"
    rig.inst.on_button(False, rig.t + 50 * MS)
    rig.idle(400)
    assert rig.inst.selected.id == "C5"


@pytest.mark.parametrize("hold_ms", [100, 1000])
def test_damp_press_release_does_not_also_select_or_lock(hold_ms):
    # The sound stops (damp_ms = 60) while the button is still held, so the
    # release happens in the "ready" state; it must not count as a click/long.
    rig = Rig()
    rig.motion(stroke(1000, 600, 150, 30))
    rig.press(hold_ms=hold_ms)
    rig.idle(600)
    assert rig.inst.selected.id == "C5"
    assert not rig.inst.locked
    assert [p[2] for p in rig.audio.plays()] == ["C5"]


def test_accessible_mode_can_still_reach_maintenance():
    rig = Rig({"mode": "accessible"})
    rig.inst.on_button(True, 0)
    rig.idle(5100)
    rig.inst.on_button(False, rig.t)
    assert rig.inst.mode == "maintenance"


def test_long_press_locks_selection():
    rig = Rig()
    rig.press(hold_ms=1000)
    assert rig.inst.locked
    rig.idle(500)
    rig.press()
    rig.idle(400)
    assert rig.inst.selected.id == "C5"


def test_very_long_press_enters_maintenance_where_rings_are_silent():
    rig = Rig()
    rig.inst.on_button(True, 0)
    rig.idle(5100)
    rig.inst.on_button(False, rig.t)
    assert rig.inst.mode == "maintenance"
    start = rig.t // MS + 500
    rig.motion(stroke(start, 600, 150, 30))
    assert rig.audio.plays() == []
    assert rig.link.messages("gesture")[-1]["g"] == "ring"
    rig.idle(200)
    rig.press()
    rig.idle(400)
    assert rig.inst.mode == "play"


def test_accessible_mode_rings_on_button_down():
    rig = Rig({"mode": "accessible"})
    rig.inst.on_button(True, 0)
    rig.idle(100)
    plays = rig.audio.plays()
    assert len(plays) == 1 and plays[0][2] == "C5"
    assert rig.link.messages("gesture")[-1]["src"] == "key"


def test_restores_persisted_state():
    rig = Rig(store_state={"index": 3, "locked": True, "accessible": False})
    assert rig.inst.selected.id == "F5" and rig.inst.locked


def test_sleeps_after_keep_awake_when_silent():
    rig = Rig({"power": {"keep_awake_s": 1}})
    rig.motion(stroke(1000, 600, 150, 30))
    rig.motion(still(rig.t // MS + 3, rig.t // MS + 1500))
    assert rig.audio.state == "ready"
    rig.idle(2500)
    assert rig.audio.state == "off"
    assert ("sleep",) == rig.audio.log[-1][:1]


def test_fixed_select_refuses_changes():
    rig = Rig({"select": "fixed"})
    rig.press()
    rig.idle(400)
    assert rig.inst.selected.id == "C5"
    assert rig.audio.plays() == []


def test_led_shows_activity():
    rig = Rig()
    before = rig.led.changes
    rig.motion(stroke(1000, 600, 150, 30))
    assert rig.led.changes > before
