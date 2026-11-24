"""Assemble CircuitPython ports from a profile's pin table and capabilities."""

from handbell.ports import NullLink


class Ports:
    def __init__(self, clock, motion, button, audio, indicator, store, link, info, power=None, sleeper=None):
        self.clock = clock
        self.motion = motion
        self.button = button
        self.audio = audio
        self.indicator = indicator
        self.store = store
        self.link = link
        self.info = info
        self.power = power
        self.sleeper = sleeper

    def shutdown(self):
        if self.audio is not None:
            self.audio.shutdown()

    def sleep(self, sleep_cfg):
        """Deep sleep via the sleeper (never returns on a device)."""
        self.sleeper.sleep(sleep_cfg, self.audio, self.indicator)


def build_ports(profile, pins, caps, cfg, i2c=None):
    from handbell.hw.audio import CircuitPythonAudio
    from handbell.hw.imu import Lsm6dsoxMotion
    from handbell.hw.io import ConsoleLink, KeypadButton, MonotonicClock, NvmStore, PinLed

    # Audio first: it drives AMP_MUTE high and POWER low before anything can fail.
    audio = CircuitPythonAudio(pins, cfg.audio, cfg.power, cfg.bells)
    ports = Ports(MonotonicClock(), None, None, audio, None, None, None, {})
    try:
        led = PinLed(pins["led"]) if pins.get("led") is not None else None
        ports.indicator = led
        if i2c is None:
            import busio

            i2c = busio.I2C(pins["scl"], pins["sda"], frequency=400000)
        ports.motion = Lsm6dsoxMotion(i2c, caps["imu_address"], cfg.imu)
        ports.button = KeypadButton(pins["button"], active_low=caps["button_active_low"], pull=True)
        ports.store = NvmStore()
        ports.link = ConsoleLink() if cfg.debug.get("events", True) else NullLink()
        if pins.get("vbat_sense") is not None:
            from handbell.hw.power import AnalogPowerSense

            ports.power = AnalogPowerSense(
                pins["vbat_sense"], caps["vbat_ratio"], pins.get("vbus_sense"), pins.get("charge_stat")
            )
        if pins.get("imu_int1") is not None:
            from handbell.hw.sleep import DeepSleeper

            ports.sleeper = DeepSleeper(
                ports.motion, pins["imu_int1"], ports.button, pins["button"], caps["button_active_low"]
            )
        ports.info = {
            "profile": profile,
            "sensors": ports.motion.info,
            "ctrl9_xl": ports.motion.ctrl9,
            "battery_sense": ports.power is not None,
            "sleep": ports.sleeper is not None,
        }
    except Exception:
        ports.shutdown()
        raise
    return ports
