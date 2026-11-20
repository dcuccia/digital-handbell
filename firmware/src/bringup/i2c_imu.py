"""I2C scan, LSM6DSOX identity, CTRL9_XL correction (#13) and sample reads."""

import time

import busio

from bringup._board import CAPS, PINS, SafeAudioPins, banner
from handbell.core import config
from handbell.hw.imu import Lsm6dsoxMotion
from handbell.hw.lsm6dsox_fix import CTRL9_XL, read_register

ADDRESS = CAPS["imu_address"]
WHO_AM_I = 0x0F
EXPECTED_ID = 0x6C

banner("i2c_imu: LSM6DSOX at 0x%02X" % ADDRESS)
with SafeAudioPins():
    i2c = busio.I2C(PINS["scl"], PINS["sda"], frequency=400000)
    try:
        while not i2c.try_lock():
            pass
        try:
            found = i2c.scan()
            print("I2C devices:", [hex(a) for a in found])
            buf = bytearray(1)
            i2c.writeto_then_readfrom(ADDRESS, bytes((WHO_AM_I,)), buf)
            print("WHO_AM_I: 0x%02X (expected 0x%02X) %s" % (buf[0], EXPECTED_ID, "PASS" if buf[0] == EXPECTED_ID else "FAIL"))
        finally:
            i2c.unlock()

        imu_cfg = config.parse().imu
        motion = Lsm6dsoxMotion(i2c, ADDRESS, imu_cfg)
        before, after = motion.ctrl9
        print("CTRL9_XL after driver init: 0x%02X (bit0=%d bit1=%d)" % (before, before & 1, (before >> 1) & 1))
        print("CTRL9_XL after correction:  0x%02X (bit0=%d bit1=%d)" % (after, after & 1, (after >> 1) & 1))
        again = read_register(motion.sensor.i2c_device, CTRL9_XL)
        ok = (again & 0x02) and not (again & 0x01) and (again & 0xFC) == (before & 0xFC)
        print("CTRL9_XL re-read: 0x%02X %s" % (again, "PASS" if ok else "FAIL"))

        print("Keep the board still. 10 samples (m/s^2, deg/s):")
        n = 0
        while n < 10:
            s = motion.read()
            if s is None:
                continue
            a = (s[0] ** 2 + s[1] ** 2 + s[2] ** 2) ** 0.5
            print("  a=(%7.3f %7.3f %7.3f) |a|=%6.3f  g=(%7.2f %7.2f %7.2f)" % (s[0], s[1], s[2], a, s[3], s[4], s[5]))
            n += 1
            time.sleep(0.05)
        print("Fast burst read vs driver properties (should agree within noise):")
        for _ in range(3):
            fast = None
            while fast is None:
                fast = motion.read()
            drv = motion.read_driver()
            print("  fast a=(%.2f %.2f %.2f) g=(%.1f %.1f %.1f)" % fast)
            print("  drvr a=(%.2f %.2f %.2f) g=(%.1f %.1f %.1f)" % drv)
        print("PASS if |a| is about 9.8 at rest and the gyro is near 0 deg/s.")
    finally:
        i2c.deinit()
