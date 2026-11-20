"""Battery voltage, USB presence and charge status, where the board has them.

The November 2026 board has no sense lines, so this only reports that.
A board revision with the requested VBAT/3 divider (GPIO29) and VBUS sense
(GPIO24) prints readings to compare against a meter.
"""

import time

from bringup._board import CAPS, PINS, SafeAudioPins, banner

banner("battery: PowerSense readings")
if PINS.get("vbat_sense") is None:
    print("This board has no battery-sense line (see docs/hardware-revision-requests.md).")
else:
    from handbell.core.battery import percent
    from handbell.hw.power import AnalogPowerSense

    with SafeAudioPins():
        sense = AnalogPowerSense(PINS["vbat_sense"], CAPS["vbat_ratio"], PINS.get("vbus_sense"), PINS.get("charge_stat"))
        for _ in range(10):
            volts, usb, charging = sense.read()
            print("VBAT %.3f V (~%d%%)  usb=%s  charging=%s" % (volts, percent(volts), usb, charging))
            time.sleep(0.5)
    print("Record: meter reading at the cell, and the ratio to these values (divider tolerance).")
