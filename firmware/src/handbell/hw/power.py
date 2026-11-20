"""Battery-voltage, USB-presence and charge-status sensing (``PowerSense`` port).

Not fitted on the November 2026 board. The requested next-revision circuit
(docs/hardware-revision-requests.md) follows the Raspberry Pi Pico
convention so the stock Pico CircuitPython build already names the pins:
VBAT through a 3:1 divider on GPIO29 (``board.VOLTAGE_MONITOR``) and USB
VBUS sense on GPIO24 (``board.VBUS_SENSE``).
"""


class AnalogPowerSense:
    def __init__(self, vbat_pin, ratio, vbus_pin=None, charge_stat_pin=None, reads=4):
        import analogio
        import digitalio

        self._adc = analogio.AnalogIn(vbat_pin)
        self._scale = self._adc.reference_voltage * ratio / 65535.0
        self._reads = max(1, int(reads))
        self._vbus = None
        self._stat = None
        if vbus_pin is not None:
            self._vbus = digitalio.DigitalInOut(vbus_pin)
            self._vbus.switch_to_input()
        if charge_stat_pin is not None:
            # MCP73831 STAT: low = charging, high = complete, high-Z = no charge
            # cycle. With a pull-up, only "charging" reads low.
            self._stat = digitalio.DigitalInOut(charge_stat_pin)
            self._stat.switch_to_input(pull=digitalio.Pull.UP)

    def read(self):
        total = 0
        for _ in range(self._reads):
            total += self._adc.value
        volts = total * self._scale / self._reads
        usb = self._vbus.value if self._vbus is not None else None
        charging = (not self._stat.value) if self._stat is not None else None
        return volts, usb, charging
