"""IMU wake-on-motion: arm the LSM6DSOX wake-up interrupt and watch GPIO22.

Checks the motion path that wakes the board from deep sleep, without
sleeping: shake or tap the bell and each wake-up should print once. Then
check that ordinary handling and table knocks do not trigger. The threshold
and data rate come from bells.json ``sleep`` (defaults 250 mg, 26 Hz).
"""

import time

import busio
import digitalio

from bringup._board import CAPS, PINS, SafeAudioPins, banner
from handbell.core import config
from handbell.hw.imu import WAKE_UP_SRC, Lsm6dsoxMotion
from handbell.hw.lsm6dsox_fix import read_register

SECONDS = 30

try:
    import json

    with open("/bells.json") as f:
        cfg = config.parse(json.load(f))
except (OSError, ValueError):
    cfg = config.parse()

banner("wake: shake to trigger (%d s), threshold %d mg" % (SECONDS, cfg.sleep["wake_mg"]))
if PINS.get("imu_int1") is None:
    print("This profile has no IMU interrupt line; deep sleep wake-on-motion is unavailable.")
else:
    with SafeAudioPins():
        i2c = busio.I2C(PINS["scl"], PINS["sda"], frequency=400000)
        try:
            motion = Lsm6dsoxMotion(i2c, CAPS["imu_address"], cfg.imu)
            cleared = motion.arm_wake(cfg.sleep["wake_mg"], cfg.sleep["wake_odr_hz"])
            print("armed; WAKE_UP_SRC at arm 0x%02X" % cleared)
            irq = digitalio.DigitalInOut(PINS["imu_int1"])
            irq.switch_to_input()
            print("INT1 now", "HIGH (stale event?)" if irq.value else "low (good)")
            start = time.monotonic()
            count = 0
            while time.monotonic() - start < SECONDS:
                if irq.value:
                    src = read_register(motion.sensor.i2c_device, WAKE_UP_SRC)
                    count += 1
                    axes = "".join(a for a, bit in (("x", 4), ("y", 2), ("z", 1)) if src & bit)
                    print("%6.2f s  wake #%d  WAKE_UP_SRC 0x%02X axes %s" % (time.monotonic() - start, count, src, axes))
                    time.sleep(0.2)
                time.sleep(0.005)
            irq.deinit()
            print("%d wake events in %d s" % (count, SECONDS))
        finally:
            i2c.deinit()
    print("Record: does a deliberate shake always trigger? Do pick-up, set-down or knocks trigger?")
    print("Adjust sleep.wake_mg in bells.json if needed (31.25 mg steps).")
