"""Port interfaces between ``handbell.core`` and a platform.

These are documented duck-typed interfaces (CircuitPython has no ``abc`` or
``typing.Protocol``). Platforms implement them in ``handbell.hw`` (devices)
or ``handbell.platforms.desktop`` (CPython simulation). All times are integer
microseconds from the platform clock.

Clock
    now_us() -> int

MotionSource
    read() -> (ax, ay, az, gx, gy, gz) or None when no new sample is ready.
    Acceleration in m/s^2 (gravity included), angular rate in deg/s.
    info -> dict for the HGP ``hello`` ``sensors`` field.

ButtonSource
    poll() -> list of bools (True = pressed edge, False = released edge).

Audio
    wake(now)            begin powering the amplifier path (idempotent)
    sleep(now)           begin powering down when silent (idempotent)
    is_awake() -> bool   True when a play() would start sounding immediately
    play(bell, level, now)  start a bell; queued until awake
    damp(now, ms)        fade every voice to silence over ``ms``
    is_sounding(now) -> bool
    tick(now)            advance power sequencing and fades
    shutdown()           immediately mute, stop clocks and remove power

Indicator
    set(on: bool)

PowerSense (optional; absent on the November 2026 board)
    read() -> (volts or None, usb or None, charging or None)
    ``volts`` is the battery voltage in volts; ``usb`` True when USB power
    is present; ``charging`` True/False from the charger status, or None.

Store
    load() -> dict or None ({"index": int, "locked": bool, "accessible": bool})
    save(state: dict)

Link
    send(line: str)      one JSON message (HGP-shaped)
    poll() -> list of str  incoming messages (unused until a radio exists)
"""


class NullLink:
    def send(self, line):
        pass

    def poll(self):
        return ()


class MemoryStore:
    def __init__(self, state=None):
        self.state = state
        self.saves = 0

    def load(self):
        return self.state

    def save(self, state):
        self.state = dict(state)
        self.saves += 1


class NullIndicator:
    def set(self, on):
        pass
