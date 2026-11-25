"""Host scripts: sound generation, trace replay, deploy and budget logic."""

import json
import wave

import pytest

import deploy
import make_sounds
import replay
from motion import still, stroke, write_trace


def test_make_sounds_is_deterministic_and_writes_provenance(tmp_path):
    items = [("A5", 81, "sounds/A5.wav")]
    a = make_sounds.generate(tmp_path / "a", items, 22050, 0.5, 64, masters=None)
    b = make_sounds.generate(tmp_path / "b", items, 22050, 0.5, 64, masters=None)
    assert a[0]["sha256"] == b[0]["sha256"]
    with wave.open(str(tmp_path / "a" / "sounds" / "A5.wav")) as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()) == (1, 2, 22050, 11025)
    assert a[0]["license"] == "MIT"


def test_device_sounds_come_from_masters(tmp_path):
    masters = tmp_path / "masters"
    make_sounds.write_masters(masters, ["G5"], 22050, 0.25)
    master = masters / "G5.wav"
    # A master that differs from the synthesis must win, byte for byte.
    with wave.open(str(master), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(22050)
        w.writeframes(b"\x01\x02" * 100)
    recs = make_sounds.generate(tmp_path / "out", [("G5", 79, "sounds/G5.wav")], 22050, 4.0, 64, masters=masters)
    assert (tmp_path / "out" / "sounds" / "G5.wav").read_bytes() == master.read_bytes()
    assert recs[0]["source"].startswith("master ") and recs[0]["seconds"] == round(100 / 22050, 3)


def test_unfetched_lfs_master_fails_clearly(tmp_path):
    (tmp_path / "C5.wav").write_bytes(b"version https://git-lfs.github.com/spec/v1\noid sha256:00\nsize 1\n")
    with pytest.raises(SystemExit):
        make_sounds.generate(tmp_path / "out", [("C5", 72, "sounds/C5.wav")], 22050, 1.0, 64, masters=tmp_path)


def test_shipped_bells_have_committed_masters():
    config = make_sounds._common.SRC / "bells.json"
    for _, midi, rel in make_sounds.plan_from_config(config, 22050):
        assert rel.endswith(".wav"), "instrument bells play WAV; MP3 drops out under load"
        master = make_sounds.master_path(midi)
        assert master.exists() and master.read_bytes()[:4] == b"RIFF", "missing master or LFS not pulled: %s" % master


def test_make_sounds_mp3_is_small_cbr(tmp_path):
    pytest.importorskip("lameenc")
    recs = make_sounds.generate(tmp_path, [("C5", 72, "sounds/C5.mp3")], 22050, 4.0, 64)
    # 64 kbit/s x 4 s = 32 kB, plus encoder flush frames.
    assert 30000 < recs[0]["bytes"] < 36000
    assert (tmp_path / "sounds" / "C5.mp3").read_bytes()[:2] in (b"\xff\xf3", b"\xff\xf2", b"\xff\xe3", b"\xff\xe2")


def test_provided_sounds_are_not_regenerated(tmp_path):
    (tmp_path / "sounds").mkdir()
    (tmp_path / "sounds" / "C5.wav").write_bytes(b"mine")
    config = make_sounds._common.SRC / "bells.json"
    items = make_sounds.plan_from_config(config, 22050, user_root=tmp_path)
    assert [i[2] for i in items] == ["sounds/G5.wav"]


def test_replay_detects_rings_in_trace(tmp_path):
    samples = still(0, 500) + stroke(1000, 600, 150, 30) + stroke(2500, 400, 150, 25)
    path = tmp_path / "t.jsonl"
    write_trace(path, samples, gestures=[{"type": "gesture", "g": "ring", "t": 1165.0}])
    result = replay.replay(path)
    assert len(result["rings"]) == 2
    assert result["recorded_rings"] == 1
    assert len(result["plays"]) == 2
    stricter = replay.replay(path, {"min_peak_omega": 500})
    assert len(stricter["rings"]) == 1


def test_deploy_copies_changes_keeps_user_files_and_config(tmp_path, monkeypatch):
    build = tmp_path / "build"
    (build / "handbell").mkdir(parents=True)
    (build / "handbell" / "a.mpy").write_bytes(b"new")
    (build / "code.py").write_text("main")
    (build / "bells.json").write_text('{"v": 0}')
    drive = tmp_path / "drive"
    (drive / "handbell").mkdir(parents=True)
    (drive / "boot_out.txt").write_text("CircuitPython")
    (drive / "settings.toml").write_text("mine")
    (drive / "handbell" / "stale.mpy").write_bytes(b"old")
    (drive / "bells.json").write_text('{"v": 0, "name": "edited"}')
    monkeypatch.setattr(deploy._common, "CIRCUITPY", build)
    deploy.main(["--drive", str(drive)])
    assert (drive / "handbell" / "a.mpy").read_bytes() == b"new"
    assert not (drive / "handbell" / "stale.mpy").exists()
    assert (drive / "settings.toml").read_text() == "mine"
    assert json.loads((drive / "bells.json").read_text())["name"] == "edited"
    deploy.main(["--drive", str(drive), "--config"])
    assert json.loads((drive / "bells.json").read_text()) == {"v": 0}


def test_code_only_build_does_not_wipe_device_sounds(tmp_path, monkeypatch):
    build = tmp_path / "build"
    build.mkdir()
    (build / "code.py").write_text("main")
    (build / "build_info.json").write_text('{"sounds": false}')
    drive = tmp_path / "drive"
    (drive / "sounds").mkdir(parents=True)
    (drive / "boot_out.txt").write_text("CircuitPython")
    (drive / "sounds" / "C5.mp3").write_bytes(b"keep")
    monkeypatch.setattr(deploy._common, "CIRCUITPY", build)
    deploy.main(["--drive", str(drive)])
    assert (drive / "sounds" / "C5.mp3").read_bytes() == b"keep"
