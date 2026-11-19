"""handbell.hw adapters against stand-in CircuitPython modules.

These check wiring, units and sequencing that matter for first power-up;
they do not replace bring-up on real hardware.
"""

import json

import pytest

import fake_circuitpython as fcp
from handbell.core import config

MS = 1000


class SteppingClock:
    def __init__(self, step_us):
        self.t = 0
        self.step = step_us

    def now_us(self):
        self.t += self.step
        return self.t


@pytest.fixture
def cp(monkeypatch):
    return fcp.install(monkeypatch)


def make_audio(raw=None):
    from handbell.hw.audio import CircuitPythonAudio
    from handbell.platforms import handbell_rp2040

    cfg = config.parse(raw)
    return cfg, CircuitPythonAudio(handbell_rp2040.pins(), cfg.audio, cfg.power, cfg.bells)


def run_until(audio, start, end, step=1):
    t = start
    while t <= end:
        audio.tick(t * MS)
        t += step


def test_audio_starts_muted_and_unpowered(cp):
    make_audio()
    assert fcp.LOG[:2] == ["GPIO20=1", "GPIO23=0"]


def test_cold_play_sequences_power_clocks_unmute_then_note(cp):
    cfg, audio = make_audio()
    bell = cfg.bells[0]
    audio.play(bell, 0.3, 0)
    assert "GPIO23=1" in fcp.LOG and "i2s.init" not in fcp.LOG
    run_until(audio, 0, 49)
    assert "i2s.init" not in fcp.LOG
    run_until(audio, 50, 60)
    log = fcp.LOG
    order = [log.index(e) for e in ("GPIO23=1", "i2s.init", "i2s.play", "GPIO20=0", "voice0.play:sounds/C5.mp3")]
    assert order == sorted(order)
    assert audio.is_awake() and audio.last_start_latency_us >= 55 * MS
    assert audio.mixer.voice[0].level == pytest.approx(0.3)


def test_sleep_mutes_then_stops_clocks_then_removes_power(cp):
    cfg, audio = make_audio()
    audio.wake(0)
    run_until(audio, 0, 60)
    del fcp.LOG[:]
    audio.sleep(100 * MS)
    run_until(audio, 100, 110)
    assert fcp.LOG == ["GPIO20=1", "i2s.stop", "i2s.deinit", "GPIO23=0"]
    assert audio.state_name == "off"


def test_shutdown_order(cp):
    cfg, audio = make_audio()
    audio.wake(0)
    run_until(audio, 0, 60)
    del fcp.LOG[:]
    audio.shutdown()
    assert fcp.LOG == ["GPIO20=1", "i2s.stop", "i2s.deinit", "GPIO23=0"]


def test_damp_fades_file_voice_then_stops(cp):
    cfg, audio = make_audio()
    audio.wake(0)
    run_until(audio, 0, 60)
    audio.play(cfg.bells[0], 0.4, 61 * MS)
    voice = audio.mixer.voice[0]
    audio.damp(100 * MS, 60)
    audio.tick(130 * MS)
    assert voice.level == pytest.approx(0.2, abs=0.01)
    audio.tick(161 * MS)
    assert not voice.playing and not audio.is_sounding(161 * MS)


def test_overlap_retrigger_uses_second_voice(cp):
    cfg, audio = make_audio()
    audio.wake(0)
    run_until(audio, 0, 60)
    audio.play(cfg.bells[0], 0.4, 61 * MS)
    audio.play(cfg.bells[0], 0.4, 70 * MS)
    assert audio.mixer.voice[0].playing and audio.mixer.voice[1].playing


def test_synth_bell_presses_partials_and_releases_after_decay(cp):
    cfg, audio = make_audio({"bells": [{"id": "A5", "sound": "synth"}]})
    assert len(audio.mixer.voice) == 3
    audio.play(cfg.bells[0], 0.5, 0)
    run_until(audio, 0, 60)
    assert "voice2.play:synth" in fcp.LOG and any(e.startswith("synth.press:") for e in fcp.LOG)
    assert audio.is_sounding(61 * MS)
    run_until(audio, 61, 4100, step=20)
    assert any(e.startswith("synth.release:") for e in fcp.LOG)
    assert not audio.is_sounding(4200 * MS)


def test_play_during_muting_cancels_sleep_and_starts_at_once(cp):
    cfg, audio = make_audio()
    audio.wake(0)
    run_until(audio, 0, 60)
    audio.sleep(100 * MS)
    assert audio.state_name == "muting"
    audio.play(cfg.bells[0], 0.3, 101 * MS)
    assert audio.state_name == "ready" and audio.mixer.voice[0].playing
    assert fcp.LOG[-1].startswith("voice0.play") and "GPIO20=0" in fcp.LOG[-2:]
    run_until(audio, 101, 200)
    assert audio.state_name == "ready"


def test_imu_fixes_ctrl9_and_parses_burst_in_si_units(cp):
    from handbell.hw.imu import Lsm6dsoxMotion

    motion = Lsm6dsoxMotion(object(), 0x6A, config.parse().imu)
    assert motion.ctrl9 == (0xE1, 0xE2)
    dev = fcp.LSM6DSOX.last.i2c_device
    dev.set_burst(0x00, (1000, 0, -1000), (0, 0, 2049))
    assert motion.read() is None
    dev.set_burst(0x03, (1000, 0, -1000), (0, 0, 2049))
    ax, ay, az, gx, gy, gz = motion.read()
    assert gx == pytest.approx(70.0) and gz == pytest.approx(-70.0)
    assert az == pytest.approx(9.806, abs=0.01)


def test_nvm_store_round_trip(cp):
    from handbell.hw.io import NvmStore

    store = NvmStore()
    assert store.load() is None
    store.save({"index": 5, "locked": True, "accessible": True})
    assert store.load() == {"index": 5, "locked": True, "accessible": True}


def test_profile_builds_ports_and_runtime_emits_hello_and_status(cp, capsys):
    from handbell import platforms, runtime
    from handbell.core.instrument import Instrument

    profile = platforms.load()
    assert profile.NAME == "handbell_rp2040"
    cfg = config.parse({"debug": {"status_s": 0.001}})
    ports = profile.build(cfg)
    # Deterministic clock: Windows' monotonic clock ticks only every ~15.6 ms.
    ports.clock = SteppingClock(step_us=10)
    fcp.LSM6DSOX.last.i2c_device.set_burst(0x03, (0, 0, 0), (0, 0, 2049))
    fcp.Keys.last.events.queue = [True, False]
    inst = Instrument(cfg, ports.audio, ports.indicator, ports.store, ports.link)
    runtime.run(ports, inst, cfg, app="test", device_id="hb-test", max_loops=2000)
    lines = [json.loads(l) for l in capsys.readouterr().out.splitlines() if l.startswith("{")]
    kinds = [m["type"] for m in lines]
    assert kinds[0] == "hello" and lines[0]["kind"] == "bell"
    assert "status" in kinds
    assert ports.info["ctrl9_xl"] == (0xE1, 0xE2)


def test_unknown_board_needs_explicit_platform(cp, monkeypatch):
    from handbell import platforms

    monkeypatch.setattr(fcp.sys.modules["board"], "board_id", "some_other_board")
    monkeypatch.delenv("HANDBELL_PLATFORM", raising=False)
    with pytest.raises(RuntimeError, match="HANDBELL_PLATFORM"):
        platforms.load()
    monkeypatch.setenv("HANDBELL_PLATFORM", "esp32s3_handbell")
    with pytest.raises(NotImplementedError):
        platforms.load().build(config.parse())
