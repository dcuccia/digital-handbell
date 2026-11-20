"""Small CircuitPython adapters: clock, button, LED, persistent state, link."""

import time


class MonotonicClock:
    """Integer microseconds from ``time.monotonic_ns`` (no float precision loss)."""

    def now_us(self):
        return time.monotonic_ns() // 1000


class KeypadButton:
    """Debounced button using the built-in ``keypad`` module.

    J2 on the handbell is active low with an external 10 kohm pull-up; the
    internal pull is also enabled so an unpopulated resistor fails safe.
    """

    def __init__(self, pin, active_low=True, pull=True, interval_s=0.01):
        import keypad

        self._keys = keypad.Keys((pin,), value_when_pressed=not active_low, pull=pull, interval=interval_s)
        self._event = keypad.Event()

    def poll(self):
        out = None
        events = self._keys.events
        while events.get_into(self._event):
            if out is None:
                out = []
            out.append(self._event.pressed)
        return out or ()

    def deinit(self):
        self._keys.deinit()


class PinLed:
    def __init__(self, pin, active_high=True):
        import digitalio

        self._active_high = active_high
        self._out = digitalio.DigitalInOut(pin)
        self._out.switch_to_output(value=not active_high)

    def set(self, on):
        self._out.value = on if self._active_high else not on


class NvmStore:
    """Selected bell, lock and accessibility mode in ``microcontroller.nvm``.

    CIRCUITPY is read-only to code while USB-mounted, so this small state
    lives in the separate NVM sector. Layout: magic, version, index, flags.
    """

    MAGIC = 0xB7
    VERSION = 1

    def __init__(self):
        import microcontroller

        self._nvm = microcontroller.nvm

    def load(self):
        nvm = self._nvm
        if nvm is None or len(nvm) < 4 or nvm[0] != self.MAGIC or nvm[1] != self.VERSION:
            return None
        flags = nvm[3]
        return {"index": nvm[2], "locked": bool(flags & 1), "accessible": bool(flags & 2)}

    def save(self, state):
        if self._nvm is None:
            return
        flags = (1 if state.get("locked") else 0) | (2 if state.get("accessible") else 0)
        data = bytes((self.MAGIC, self.VERSION, state.get("index", 0) & 0xFF, flags))
        if bytes(self._nvm[0:4]) != data:
            self._nvm[0:4] = data


class ConsoleLink:
    """HGP-shaped JSON lines on the USB serial console.

    This is HGP's "serial" binding in its simplest form: one message per line.
    ``scripts/capture_trace.py`` records it on a computer.
    """

    def send(self, line):
        print(line)

    def poll(self):
        return ()


def device_id():
    try:
        import microcontroller

        return "hb-" + "".join("%02x" % b for b in microcontroller.cpu.uid)
    except (ImportError, AttributeError):
        return "hb-unknown"
