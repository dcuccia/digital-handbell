"""IMU sample rate and loop timing, with and without garbage collection."""

import gc

import busio

from bringup._board import CAPS, PINS, SafeAudioPins, banner
from handbell.core import config
from handbell.core.gestures import RingDetector
from handbell.hw.imu import Lsm6dsoxMotion
from handbell.hw.io import MonotonicClock

SECONDS = 3

banner("loop_rate: IMU at configured ODR, ring detector in the loop")
with SafeAudioPins():
    i2c = busio.I2C(PINS["scl"], PINS["sda"], frequency=400000)
    try:
        imu_cfg = config.parse().imu
        clock = MonotonicClock()
        for fast in (True, False):
            imu_cfg["fast_read"] = fast
            motion = Lsm6dsoxMotion(i2c, CAPS["imu_address"], imu_cfg)
            det = RingDetector()
            gc.collect()
            start = clock.now_us()
            prev = start
            loops = samples = 0
            max_gap = 0
            while clock.now_us() - start < SECONDS * 1000000:
                now = clock.now_us()
                gap = now - prev
                prev = now
                if gap > max_gap:
                    max_gap = gap
                s = motion.read()
                loops += 1
                if s is not None:
                    samples += 1
                    det.push(now, s[0], s[1], s[2], s[3], s[4], s[5])
            elapsed = (clock.now_us() - start) / 1e6
            print(
                "%s: %d loops/s, %d new samples/s (ODR %d Hz), max loop gap %.2f ms"
                % ("burst read" if fast else "driver read", loops / elapsed, samples / elapsed, imu_cfg["rate_hz"], max_gap / 1000)
            )
        t0 = clock.now_us()
        gc.collect()
        print("gc.collect() took %.2f ms; free %d bytes" % ((clock.now_us() - t0) / 1000, gc.mem_free()))
    finally:
        i2c.deinit()
print("Record these numbers; they bound detector timing (see gesture-tuning.md).")
