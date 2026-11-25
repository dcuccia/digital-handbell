"""Inactivity deep sleep, wake-on-motion and the wake announce (#23)."""

import json

import pytest

import fake_circuitpython as fcp
from handbell.core import config
from handbell.core.instrument import Instrument
from handbell.platforms.desktop import ListLink, SimAudio
from handbell.ports import MemoryStore
from motion import still, stroke

MS = 1000


@pytest.fixture
def cp(monkeypatch):
    return fcp.install(monkeypatch)


def make(raw=None, store_state=None):
    cfg = config.parse(raw)
    audio = SimAudio(cfg.power["settle_ms"], cfg.power["clock_ms"], tail_s=1.0)
    link = ListLink()
    store = MemoryStore(store_state)
    return cfg, audio, link, store, Instrument(cfg, audio, None, store, link)


def idle(inst, start_ms, end_ms, step_ms=10):
    t = start_ms
    while t <= end_ms:
        inst.tick(t * MS)
        t += step_ms
    return t * MS


def test_sleep_due_after_inactivity_only_when_quiet():
    cfg, audio, link, store, inst = make({"sleep": {"after_s": 2}, "power": {"keep_awake_s": 1}})
    inst.start(0)
    idle(inst, 0, 1900)
    assert not inst.sleep_due(1900 * MS)
    assert inst.sleep_due(2000 * MS)


def test_motion_and_buttons_postpone_sleep_but_noise_does_not():
    cfg, audio, link, store, inst = make({"sleep": {"after_s": 2}})
    inst.start(0)
    for t, s in still(0, 1500):  # gyro ~0: no activity
        inst.on_motion(t, s)
    assert inst._last_activity == 0
    inst.on_motion(1500 * MS, (0, 0, 9.8, 40.0, 0, 0))  # gentle handling (>30 deg/s)
    assert not inst.sleep_due(3000 * MS) and inst.sleep_due(3600 * MS)
    inst.on_button(True, 3700 * MS)
    inst.on_button(False, 3750 * MS)
    assert not inst.sleep_due(5000 * MS)


def test_not_due_while_amplifier_awake_after_ring():
    cfg, audio, link, store, inst = make({"sleep": {"after_s": 2}})  # keep_awake 20 s
    inst.start(0)
    for t, s in stroke(1000, 600, 150, 30):
        inst.on_motion(t, s)
        inst.tick(t)
    end = idle(inst, 1500, 5000)
    assert audio.is_awake() and not inst.sleep_due(end)


def test_sleep_disabled_with_zero():
    cfg, audio, link, store, inst = make({"sleep": {"after_s": 0}})
    inst.start(0)
    assert not inst.sleep_due(10 ** 10)


def test_prepare_sleep_saves_state_and_reports():
    cfg, audio, link, store, inst = make()
    inst.start(0)
    inst.volume_index = 1
    inst.prepare_sleep(5 * MS)
    assert store.state == {"index": 0, "locked": False, "accessible": False, "volume": 1}
    msg = link.messages("status")[-1]
    assert msg["sleep"] is True and msg["volume"] == 2


@pytest.mark.parametrize(
    "wake,power_on,raw,plays",
    [
        ("motion", False, None, 1),
        ("button", False, None, 1),
        (None, True, None, 1),
        (None, False, None, 0),  # code reload: no chime
        ("motion", False, {"sleep": {"announce_wake": False}}, 0),
        (None, True, {"sleep": {"announce_power_on": False}}, 0),
    ],
)
def test_announce_on_wake_and_power_on(wake, power_on, raw, plays):
    cfg, audio, link, store, inst = make(raw, store_state={"index": 1, "locked": False, "accessible": False, "volume": 1})
    inst.start(0, wake=wake, power_on=power_on)
    idle(inst, 0, 200)
    got = audio.plays()
    assert len(got) == plays
    if plays:
        assert got[0][2] == "G5"  # the persisted bell
        assert got[0][3] == pytest.approx(0.2 * 0.5)  # preview level x persisted volume
    if wake:
        assert inst.status(0)["wake"] == wake


def test_hw_arm_wake_register_sequence(cp):
    from handbell.hw import imu

    motion = imu.Lsm6dsoxMotion(object(), 0x6A, config.parse().imu)
    regs = fcp.LSM6DSOX.last.i2c_device.regs
    regs[imu.CTRL6_C] = 0x00
    regs[imu.TAP_CFG2] = 0x00
    regs[imu.WAKE_UP_SRC] = 0x08
    assert motion.arm_wake(250, 26, settle_s=0) == 0x08
    assert regs[imu.CTRL2_G] == 0x00  # gyro off
    assert regs[imu.CTRL1_XL] == 0x20  # 26 Hz, +/-2 g
    assert regs[imu.CTRL6_C] & 0x10  # low-power (HM off)
    assert regs[imu.WAKE_UP_THS] == 8  # 250 mg / 31.25 mg
    assert regs[imu.WAKE_UP_DUR] == 0x20
    assert regs[imu.TAP_CFG0] == 0x41  # latched, clear on read, slope filter
    assert regs[imu.TAP_CFG2] & 0x80
    assert regs[imu.MD1_CFG] == 0x20  # wake-up on INT1
    assert regs[imu.INT1_CTRL] == 0x00
    motion.arm_wake(5000, 104, settle_s=0)
    assert regs[imu.WAKE_UP_THS] == 63 and regs[imu.CTRL1_XL] == 0x40


def test_hw_sleep_powers_down_then_sleeps_with_both_alarms(cp):
    from handbell import platforms

    cfg = config.parse()
    ports = platforms.load().build(cfg)
    assert ports.info["sleep"] is True
    ports.audio.wake(0)
    del fcp.LOG[:]
    ports.sleep(cfg.sleep)
    log = fcp.LOG
    assert log.index("GPIO23=0") < log.index("keys.deinit") < log.index("deep_sleep")
    alarms = cp["alarm"].slept_with
    pin = cp["microcontroller"].pin
    assert [(a.pin, a.value, a.edge, a.pull) for a in alarms] == [
        (pin.GPIO22, True, False, False),  # IMU INT1, latched active high
        (pin.GPIO19, False, False, False),  # J2 button, active low, external pull-up
    ]


def test_hw_button_wake_can_be_disabled(cp):
    from handbell import platforms

    cfg = config.parse({"sleep": {"button_wakes": False}})
    ports = platforms.load().build(cfg)
    ports.sleep(cfg.sleep)
    assert len(cp["alarm"].slept_with) == 1


def test_hw_wake_reason(cp):
    from handbell import platforms

    ports = platforms.load().build(config.parse())
    pin = cp["microcontroller"].pin
    assert ports.sleeper.wake_reason() is None
    cp["alarm"].wake_alarm = fcp.PinAlarm(pin.GPIO22, True)
    assert ports.sleeper.wake_reason() == "motion"
    cp["alarm"].wake_alarm = fcp.PinAlarm(pin.GPIO19, False)
    assert ports.sleeper.wake_reason() == "button"


def test_runtime_sleeps_after_inactivity(cp, capsys):
    from handbell import platforms, runtime
    from test_hw_adapters import SteppingClock

    cfg = config.parse({"sleep": {"after_s": 0.05}, "debug": {"status_s": 0}})
    ports = platforms.load().build(cfg)
    ports.clock = SteppingClock(step_us=100)
    fcp.LSM6DSOX.last.i2c_device.set_burst(0x03, (0, 0, 0), (0, 0, 2049))
    inst = Instrument(cfg, ports.audio, ports.indicator, ports.store, ports.link)
    loops = runtime.run(ports, inst, cfg, app="t", device_id="hb-t", max_loops=10000)
    assert loops < 10000 and cp["alarm"].slept_with
    lines = [json.loads(l) for l in capsys.readouterr().out.splitlines() if l.startswith("{")]
    assert lines[-1]["type"] == "status" and lines[-1]["sleep"] is True


def test_bench_profile_without_int_line_has_no_sleeper(cp, monkeypatch):
    from handbell import platforms

    monkeypatch.setenv("HANDBELL_PLATFORM", "feather_propmaker_rp2040")
    board = cp["board"]
    for name in ("SDA", "SCL", "I2S_DATA", "I2S_BIT_CLOCK", "I2S_WORD_SELECT", "EXTERNAL_BUTTON", "EXTERNAL_POWER", "LED"):
        monkeypatch.setattr(board, name, fcp.Pin(name), raising=False)
    ports = platforms.load().build(config.parse())
    assert ports.sleeper is None


def test_cold_start_detection(cp):
    from handbell import main

    assert main._cold_start() is True
    cp["supervisor"].runtime.run_reason = "auto_reload"
    assert main._cold_start() is False
