"""Assemble CircuitPython ports from a profile's pin table and capabilities."""

from handbell.ports import NullLink


class Ports:
    def __init__(self, clock, motion, button, audio, indicator, store, link, info):
        self.clock = clock
        self.motion = motion
        self.button = button
        self.audio = audio
        self.indicator = indicator
        self.store = store
        self.link = link
        self.info = info

    def shutdown(self):
        if self.audio is not None:
            self.audio.shutdown()


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
        ports.info = {
            "profile": profile,
            "sensors": ports.motion.info,
            "ctrl9_xl": ports.motion.ctrl9,
            "battery_sense": caps.get("battery_sense", False),
        }
    except Exception:
        ports.shutdown()
        raise
    return ports
