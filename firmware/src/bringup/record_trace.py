"""Stream HGP ``raw`` batches (and detected rings) over USB serial until Ctrl-C.

On a computer run ``python firmware/scripts/capture_trace.py`` to save the
stream as JSON lines in firmware/traces/. Close any other serial monitor
first. Never record identifiable people; describe motions in the label.
"""

import busio

from bringup._board import CAPS, PINS, SafeAudioPins, banner
from handbell.core import config, events
from handbell.core.gestures import RingDetector
from handbell.hw.imu import Lsm6dsoxMotion
from handbell.hw.io import MonotonicClock, device_id

BATCH_US = 250000

banner("record_trace: streaming raw IMU rows; Ctrl-C to stop")
with SafeAudioPins():
    i2c = busio.I2C(PINS["scl"], PINS["sda"], frequency=400000)
    try:
        imu_cfg = config.parse().imu
        motion = Lsm6dsoxMotion(i2c, CAPS["imu_address"], imu_cfg)
        det = RingDetector()
        clock = MonotonicClock()
        print(events.hello(device_id(), "trace", "bringup.record_trace", motion.info, ("ring",), False))
        rows = []
        seq = 0
        next_batch = clock.now_us() + BATCH_US
        while True:
            now = clock.now_us()
            s = motion.read()
            if s is not None:
                rows.append((now, s[0], s[1], s[2], s[3], s[4], s[5]))
                strike = det.push(now, s[0], s[1], s[2], s[3], s[4], s[5])
                if strike is not None:
                    seq += 1
                    print(events.gesture(seq, "ring", strike.t, vel=strike.intensity, det_us=strike.fired_at - strike.t))
            if now >= next_batch:
                print(events.raw_batch(rows))
                rows = []
                next_batch = now + BATCH_US
    except KeyboardInterrupt:
        print("stopped")
    finally:
        i2c.deinit()
