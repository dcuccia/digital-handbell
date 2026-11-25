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


MP3_BELLS = {"bells": [{"id": n, "sound": "sounds/%s.mp3" % n} for n in ("C5", "D5", "E5")]}


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
    order = [log.index(e) for e in ("GPIO23=1", "i2s.init", "i2s.play", "GPIO20=0", "voice0.play:sounds/C5.wav")]
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
    cfg, audio = make_audio({"audio": {"mp3_decoders": 2}})
    audio.wake(0)
    run_until(audio, 0, 60)
    audio.play(cfg.bells[0], 0.4, 61 * MS)
    audio.play(cfg.bells[0], 0.4, 70 * MS)
    assert audio.mixer.voice[0].playing and audio.mixer.voice[1].playing


def test_strike_with_no_free_voice_fades_oldest_instead_of_cutting(cp):
    cfg, audio = make_audio()  # 3 voices, steal_ms 40
    audio.wake(0)
    run_until(audio, 0, 60)
    c5, g5 = cfg.bells
    for k, t in enumerate((100, 600, 1100)):
        audio.play((c5, g5)[k % 2], 0.5, t * MS)
    voices = audio.mixer.voice
    assert [v.playing for v in voices] == [True, True, True]
    # The oldest note fades through a once-only LFO level instead of a hard stop.
    lfo = voices[0].level
    assert isinstance(lfo, fcp.LFO) and lfo.kw["once"] and lfo.kw["scale"] == pytest.approx(0.5)
    run_until(audio, 1101, 1100 + 40 + 100 + 1)
    assert [v.playing for v in voices] == [False, True, True]
    audio.play(g5, 0.5, 1300 * MS)
    assert voices[0].playing and voices[0].level == pytest.approx(0.5)


def test_strike_during_fade_reuses_fading_voice(cp):
    cfg, audio = make_audio()
    audio.wake(0)
    run_until(audio, 0, 60)
    c5, g5 = cfg.bells
    for k, t in enumerate((100, 600, 1100)):
        audio.play((c5, g5)[k % 2], 0.5, t * MS)
    audio.play(c5, 0.5, 1110 * MS)
    voices = audio.mixer.voice
    # Voice 0 (fading) was reused; the two newer notes keep sounding.
    assert audio._voice_start[0] == 1110 * MS and voices[1].playing and voices[2].playing


def test_fade_falls_back_to_tick_ramp_without_lfo(cp, monkeypatch):
    import synthio

    monkeypatch.delattr(synthio, "LFO")
    cfg, audio = make_audio()
    audio.wake(0)
    run_until(audio, 0, 60)
    c5, g5 = cfg.bells
    for k, t in enumerate((100, 600, 1100)):
        audio.play((c5, g5)[k % 2], 0.5, t * MS)
    run_until(audio, 1101, 1120)
    assert 0.0 < audio.mixer.voice[0].level < 0.5


def test_single_mp3_decoder_restarts_instead_of_overlapping(cp):
    cfg, audio = make_audio(MP3_BELLS)  # default: one shared MP3 decoder
    audio.wake(0)
    run_until(audio, 0, 60)
    audio.play(cfg.bells[0], 0.4, 61 * MS)
    audio.play(cfg.bells[1], 0.4, 70 * MS)
    voices = audio.mixer.voice
    assert [v.playing for v in voices[:2]] == [False, True]
    assert voices[1].sample.name == "sounds/D5.mp3"
    audio.play(cfg.bells[2], 0.4, 80 * MS)
    assert [v.playing for v in voices[:2]] == [True, False]
    assert sum(v.playing for v in voices[:2]) == 1


def test_synth_bell_presses_partials_and_releases_after_decay(cp):
    cfg, audio = make_audio({"bells": [{"id": "A5", "sound": "synth"}]})
    assert len(audio.mixer.voice) == cfg.audio["voices"] + 1  # file voices + synth
    audio.play(cfg.bells[0], 0.5, 0)
    run_until(audio, 0, 60)
    assert "voice%d.play:synth" % cfg.audio["voices"] in fcp.LOG and any(e.startswith("synth.press:") for e in fcp.LOG)
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


def test_power_sense_scales_divider_and_reads_flags(cp):
    from handbell.hw.power import AnalogPowerSense

    pin = cp["microcontroller"].pin
    sense = AnalogPowerSense(pin.GPIO29, 3.0, pin.GPIO24, pin.GPIO25)
    sense._adc.value = int(1.3 / 3.3 * 65535)  # 1.3 V at the pin = 3.9 V cell
    sense._vbus.input_value = True
    sense._stat.input_value = False  # STAT pulled low by the charger
    volts, usb, charging = sense.read()
    assert volts == pytest.approx(3.9, abs=0.001)
    assert usb is True and charging is True
    assert sense._stat.pull == "up"


def test_profile_without_sense_line_has_no_power_port(cp):
    from handbell import platforms

    ports = platforms.load().build(config.parse())
    assert ports.power is None and ports.info["battery_sense"] is False


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
    store.save({"index": 5, "locked": True, "accessible": True, "volume": 2})
    assert store.load() == {"index": 5, "locked": True, "accessible": True, "volume": 2}


def test_nvm_store_reads_version_1_layout_without_volume(cp):
    from handbell.hw.io import NvmStore

    nvm = cp["microcontroller"].nvm
    nvm[0:5] = bytes((0xB7, 1, 4, 1, 0xFF))
    assert NvmStore().load() == {"index": 4, "locked": True, "accessible": False}


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

def test_decoders_are_preallocated_so_plays_never_allocate(cp, tmp_path, monkeypatch):
    # MP3Decoder/WaveFile allocate without garbage collection on CircuitPython,
    # so a decoder built mid-performance raised MemoryError on the first board.
    fcp.MP3Decoder.constructed = 0
    wav = tmp_path / "x.wav"
    wav.write_bytes(b"RIFF")
    cfg, audio = make_audio({"bells": [{"id": "C5", "sound": "sounds/C5.mp3"}, {"id": "D5", "sound": str(wav)}]})
    assert fcp.MP3Decoder.constructed == 1  # one shared decoder (~37 KB), at startup
    assert all(b is not None and len(b) % 8 == 0 for b in audio._wav_buffers)
    audio.wake(0)
    run_until(audio, 0, 60)
    t = 61
    for i in range(10):
        audio.play(cfg.bells[i % 2], 0.3, t * MS)
        t += 5
    assert fcp.MP3Decoder.constructed == 1
    wav_samples = [v.sample for v in audio.mixer.voice if isinstance(v.sample, fcp.WaveFile)]
    assert wav_samples and all(any(s.buffer is b for b in audio._wav_buffers) for s in wav_samples)
