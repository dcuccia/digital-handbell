"""Inactivity deep sleep with wake-on-motion and wake-on-button (``Sleeper`` port).

On CircuitPython 10.x RP2040, ``alarm.exit_and_deep_sleep_until_alarms`` with
only pin alarms stops the crystal (DORMANT) and wakes by resetting the chip;
code.py then starts again and ``alarm.wake_alarm`` says why. While USB is
connected CircuitPython only simulates deep sleep so the console stays up.

Unclaimed pins are reset with internal pulls disabled, so the board's own
resistors hold the safe states during sleep: R17 keeps POWER low (boost and
amplifier off) and R20 keeps AMP_MUTE high (muted).
"""


class DeepSleeper:
    def __init__(self, motion, int_pin, button=None, button_pin=None, button_active_low=True):
        self._motion = motion
        self._int_pin = int_pin
        self._button = button
        self._button_pin = button_pin
        self._button_active_low = button_active_low

    def wake_reason(self):
        """"motion", "button" or None for this start (call once, early)."""
        try:
            import alarm
        except ImportError:
            return None
        woke = alarm.wake_alarm
        pin = getattr(woke, "pin", None)
        if pin is None:
            return None
        if pin == self._int_pin:
            return "motion"
        if self._button_pin is not None and pin == self._button_pin:
            return "button"
        return "alarm"

    def sleep(self, sleep_cfg, audio=None, indicator=None):
        """Power down and deep sleep. Does not return on a device."""
        import alarm

        if audio is not None:
            audio.shutdown()
        if indicator is not None:
            indicator.set(False)
        self._motion.arm_wake(sleep_cfg["wake_mg"], sleep_cfg["wake_odr_hz"])
        alarms = [alarm.pin.PinAlarm(self._int_pin, value=True, edge=False, pull=False)]
        if sleep_cfg["button_wakes"] and self._button_pin is not None:
            if self._button is not None:
                self._button.deinit()  # release the pin from keypad
            alarms.append(alarm.pin.PinAlarm(self._button_pin, value=not self._button_active_low, edge=False, pull=False))
        alarm.exit_and_deep_sleep_until_alarms(*alarms)
