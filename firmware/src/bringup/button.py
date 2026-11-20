"""J2 button: raw edges and the gestures the instrument would recognize."""

import time

from bringup._board import CAPS, PINS, SafeAudioPins, banner
from handbell.core.controls import ButtonGrammar
from handbell.hw.io import KeypadButton, MonotonicClock

SECONDS = 30

banner("button: press, double-press, hold 1 s, hold 5 s (%d s)" % SECONDS)
with SafeAudioPins():
    button = KeypadButton(PINS["button"], active_low=CAPS["button_active_low"], pull=True)
    clock = MonotonicClock()
    grammar = ButtonGrammar()
    try:
        start = clock.now_us()
        down = None
        while clock.now_us() - start < SECONDS * 1000000:
            now = clock.now_us()
            for pressed in button.poll():
                if pressed:
                    down = now
                    print("pressed")
                    events = grammar.press(now)
                else:
                    held = (now - down) / 1000 if down is not None else 0
                    print("released after %d ms" % held)
                    events = grammar.release(now)
                for e in events:
                    if e not in ("down", "up"):
                        print("  ->", e)
            for e in grammar.tick(now):
                print("  ->", e)
            time.sleep(0.002)
    finally:
        button.deinit()
print("PASS if every press/release appears once (no chatter) and gestures match.")
