"""Durable volume setting (#24)."""

import pytest

from handbell.core import config
from handbell.core.instrument import Instrument
from handbell.platforms.desktop import ListLink, SimAudio
from handbell.ports import MemoryStore
from motion import stroke

MS = 1000


def make(raw=None, state=None):
    cfg = config.parse(raw)
    audio = SimAudio(tail_s=0.5)
    store = MemoryStore(state)
    link = ListLink()
    inst = Instrument(cfg, audio, None, store, link)
    inst.start(0)
    return inst, audio, store, link


def ring(inst, at_ms):
    for t, s in stroke(at_ms, 1000, 150, 30):
        inst.on_motion(t, s)
        inst.tick(t)


def hold(inst, at_ms, ms):
    inst.on_button(True, at_ms * MS)
    t = at_ms
    while t < at_ms + ms:
        t += 10
        inst.tick(t * MS)
    inst.on_button(False, t * MS)
    for _ in range(10):  # let the amplifier power up so a queued preview starts
        t += 10
        inst.tick(t * MS)
    return t


def test_volume_scales_ring_level_and_never_exceeds_ceiling():
    inst, audio, store, link = make()
    ring(inst, 1000)
    full = audio.plays()[-1][3]
    assert full == pytest.approx(1.0, abs=1e-3)  # vel 1.0 -> audio.level.max at volume 1.0
    inst.volume_index = 0
    ring(inst, 4000)
    assert audio.plays()[-1][3] == pytest.approx(1.0 * 0.25, abs=1e-3)


def test_volume_action_cycles_wraps_previews_and_persists():
    inst, audio, store, link = make()
    inst.mode = "maintenance"
    t = hold(inst, 0, 900)  # long press in maintenance = volume
    assert inst.volume_index == 0  # 3 wraps to 0
    preview = audio.plays()[-1]
    assert preview[2] == "C5"
    t = hold(inst, t + 500, 900)
    assert inst.volume_index == 1
    for _ in range(300):
        t += 10
        inst.tick(t * MS)
    assert store.state["volume"] == 1
    assert link.messages("status")[-1]["volume"] == 2


def test_volume_up_down_clamp():
    inst, audio, store, link = make(
        {"controls": {"play": {"ready": {"click": "volume_up", "double": "volume_down"}}}}
    )
    inst._dispatch("click", 0, "ready")
    assert inst.volume_index == 3
    for _ in range(5):
        inst._dispatch("double", 0, "ready")
    assert inst.volume_index == 0


def test_persisted_volume_restored_and_invalid_ignored():
    inst, *_ = make(state={"index": 0, "locked": False, "accessible": False, "volume": 1})
    assert inst.volume == 0.5
    inst, *_ = make(state={"index": 0, "locked": False, "accessible": False, "volume": 9})
    assert inst.volume_index == 3


@pytest.mark.parametrize(
    "raw,message",
    [
        ({"audio": {"volumes": []}}, "1-10 steps"),
        ({"audio": {"volumes": [0.5, 1.5]}}, "steps must be numbers"),
        ({"audio": {"volume": 4}}, "index into audio.volumes"),
        ({"sleep": {"wake_mg": 10}}, "wake_mg"),
        ({"sleep": {"wake_odr_hz": 30}}, "wake_odr_hz"),
        ({"sleep": {"announce_wake": "yes"}}, "true or false"),
    ],
)
def test_config_validation(raw, message):
    with pytest.raises(ValueError) as e:
        config.parse(raw)
    assert message in str(e.value)
