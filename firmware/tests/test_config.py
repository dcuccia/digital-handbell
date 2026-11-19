import json
from pathlib import Path

import pytest

from handbell.core import config, events

SRC = Path(__file__).resolve().parents[1] / "src"


def test_shipped_bells_json_is_valid_and_matches_defaults():
    with open(SRC / "bells.json", encoding="utf-8") as f:
        raw = json.load(f)
    cfg = config.parse(raw)
    assert [b.id for b in cfg.bells] == [b["id"] for b in config.DEFAULTS["bells"]]
    assert cfg.controls == config.DEFAULTS["controls"]


def test_merge_is_deep_and_lists_replace():
    cfg = config.parse({"audio": {"level": {"max": 0.3}}, "bells": [{"id": "A4", "sound": "synth"}]})
    assert cfg.audio["level"] == {"min": 0.15, "max": 0.3, "curve": 0.7}
    assert cfg.audio["sample_rate"] == 22050
    assert [b.id for b in cfg.bells] == ["A4"]


@pytest.mark.parametrize(
    "raw,message",
    [
        ({"colour": 1}, "unknown configuration key"),
        ({"bells": []}, "non-empty"),
        ({"bells": [{"id": "C5", "sound": "x.ogg"}]}, "sound must be"),
        ({"bells": [{"id": "C5", "sound": "synth"}, {"id": "C5", "sound": "synth"}]}, "duplicate"),
        ({"detector": {"armOmega": 3}}, "unknown ring detector parameter"),
        ({"controls": {"play": {"ready": {"click": "explode"}}}}, "unknown action"),
        ({"controls": {"play": {"ready": {"tripple": "next"}}}}, "unknown event"),
        ({"audio": {"level": {"min": 0.9, "max": 0.5}}}, "must not exceed"),
        ({"imu": {"rate_hz": 400}}, "imu.rate_hz"),
        ({"select": "random"}, "select must be"),
    ],
)
def test_validation_errors(raw, message):
    with pytest.raises(ValueError) as e:
        config.parse(raw)
    assert message in str(e.value)


def test_action_lookup_falls_back_to_any():
    cfg = config.parse()
    assert cfg.action_for("play", "ready", "click") == "next"
    assert cfg.action_for("play", "sounding", "click") == "none"
    assert cfg.action_for("accessible", "sounding", "down") == "ring"


def test_level_mapping_bounds():
    audio = config.parse().audio
    assert config.level_for(audio, 0) == pytest.approx(0.15)
    assert config.level_for(audio, 1) == pytest.approx(0.5)
    assert config.level_for(audio, 2) == pytest.approx(0.5)


def test_hgp_messages_are_valid_json_with_exact_ms():
    g = json.loads(events.gesture(3, "ring", 123456789, bell="C5", sel_us=1000, vel=0.41234, det_us=12500))
    assert g == {"type": "gesture", "seq": 3, "g": "ring", "t": 123456.789, "bell": "C5", "sel": 1.0, "vel": 0.412, "det": 12.5, "src": "motion"}
    assert events.ms_text(-1500) == "-1.500"
    h = json.loads(events.hello("hb-1", 'a "bell"', "app", {"api": "x"}, ("ring",)))
    assert h["kind"] == "bell" and h["name"] == 'a "bell"' and h["v"] == 0
    raw = json.loads(events.raw_batch([(1000, 0.0, 0.0, 9.80665, 1.5, -2.0, 0.25)]))
    assert raw["cols"] == ["t", "ax", "ay", "az", "gx", "gy", "gz"]
    assert raw["s"] == [[1.0, 0, 0, 9.807, 1.5, -2, 0.25]]
