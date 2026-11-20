"""Blink the GPIO13 status LED ten times."""

import time

from bringup._board import PINS, SafeAudioPins, banner, output

banner("blink: GPIO13 status LED")
with SafeAudioPins():
    led = output(PINS["led"], False)
    try:
        for i in range(10):
            led.value = True
            time.sleep(0.2)
            led.value = False
            time.sleep(0.2)
            print("blink", i + 1)
    finally:
        led.deinit()
print("PASS if the LED blinked ten times (it faces inward; it may need a light path).")
