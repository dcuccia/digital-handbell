"""Shared helpers for bring-up scripts: the active profile's pins, safe audio off."""

from handbell import platforms

PROFILE = platforms.load()
PINS = PROFILE.pins()
CAPS = PROFILE.CAPS


def output(pin, value):
    if pin is None:
        return None
    import digitalio

    out = digitalio.DigitalInOut(pin)
    out.switch_to_output(value=value)
    return out


class SafeAudioPins:
    """Hold AMP_MUTE high and POWER low; restore that state on exit."""

    def __init__(self):
        self.mute = output(PINS.get("amp_mute"), True)
        self.power = output(PINS.get("power"), False)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.off()
        for pin in (self.mute, self.power):
            if pin is not None:
                pin.deinit()
        return False

    def off(self):
        if self.mute is not None:
            self.mute.value = True
        if self.power is not None:
            self.power.value = False


def banner(title):
    print()
    print("=" * 60)
    print(title, "| profile", PROFILE.NAME)
    print("=" * 60)
