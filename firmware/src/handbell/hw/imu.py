"""LSM6DSOX motion source using the unmodified Adafruit driver.

The driver configures the sensor. Reads then use one 16-byte burst from
STATUS_REG (0x1E) through OUTZ_H_A (0x2D) on the driver's own I2CDevice, so
each loop costs one I2C transaction, allocates nothing and skips samples
the sensor has not refreshed (gyro data-ready bit). ``fast_read: false`` in
bells.json uses the driver's ``acceleration``/``gyro`` properties instead.
"""

import struct

from handbell.hw.lsm6dsox_fix import fix_ctrl9_xl, read_register, write_register

DEG_PER_RAD = 57.29577951308232
STANDARD_GRAVITY = 9.80665
STATUS_REG = 0x1E
GYRO_DATA_READY = 0x02
GYRO_MDPS_PER_LSB = {125: 4.375, 250: 8.75, 500: 17.5, 1000: 35.0, 2000: 70.0}
ACCEL_MG_PER_LSB = {2: 0.061, 4: 0.122, 8: 0.244, 16: 0.488}

# Wake-up registers (ST lsm6dsox_reg.h, commit 9570c27f).
INT1_CTRL = 0x0D
CTRL1_XL = 0x10
CTRL2_G = 0x11
CTRL6_C = 0x15
XL_HM_MODE = 0x10  # bit 4: 1 = high-performance mode disabled (low-power below 52 Hz)
WAKE_UP_SRC = 0x1B
WAKE_UP_SRC_WU_IA = 0x08
TAP_CFG0 = 0x56
TAP_CFG0_LIR = 0x01
TAP_CFG0_INT_CLR_ON_READ = 0x40
TAP_CFG2 = 0x58
TAP_CFG2_INTERRUPTS_ENABLE = 0x80
WAKE_UP_THS = 0x5B
WAKE_UP_DUR = 0x5C
MD1_CFG = 0x5E
MD1_CFG_INT1_WU = 0x20
WAKE_ODR_CODES = {13: 0x1, 26: 0x2, 52: 0x3, 104: 0x4}  # 12.5, 26, 52, 104 Hz
WAKE_MG_PER_LSB = 2000.0 / 64  # +/-2 g full scale, WAKE_THS_W = 0


class Lsm6dsoxMotion:
    def __init__(self, i2c, address, imu_cfg):
        from adafruit_lsm6ds import AccelRange, GyroRange, Rate
        from adafruit_lsm6ds.lsm6dsox import LSM6DSOX

        self.sensor = LSM6DSOX(i2c, address)
        self.ctrl9 = fix_ctrl9_xl(self.sensor.i2c_device)
        rate_hz = imu_cfg["rate_hz"]
        rate = {
            104: Rate.RATE_104_HZ,
            208: Rate.RATE_208_HZ,
            416: Rate.RATE_416_HZ,
            833: Rate.RATE_833_HZ,
            1660: Rate.RATE_1_66K_HZ,
        }[rate_hz]
        dps = imu_cfg["gyro_dps"]
        g = imu_cfg["accel_g"]
        self.sensor.gyro_range = {
            125: GyroRange.RANGE_125_DPS,
            250: GyroRange.RANGE_250_DPS,
            500: GyroRange.RANGE_500_DPS,
            1000: GyroRange.RANGE_1000_DPS,
            2000: GyroRange.RANGE_2000_DPS,
        }[dps]
        self.sensor.accelerometer_range = {
            2: AccelRange.RANGE_2G,
            4: AccelRange.RANGE_4G,
            8: AccelRange.RANGE_8G,
            16: AccelRange.RANGE_16G,
        }[g]
        self.sensor.accelerometer_data_rate = rate
        self.sensor.gyro_data_rate = rate
        self._g_scale = GYRO_MDPS_PER_LSB[dps] / 1000.0
        self._a_scale = ACCEL_MG_PER_LSB[g] / 1000.0 * STANDARD_GRAVITY
        self._fast = imu_cfg.get("fast_read", True)
        self._reg = bytes((STATUS_REG,))
        self._buf = bytearray(16)
        self.info = {"api": "lsm6dsox", "rateHz": rate_hz, "gyro": True}

    def read(self):
        if not self._fast:
            ax, ay, az = self.sensor.acceleration
            gx, gy, gz = self.sensor.gyro
            return ax, ay, az, gx * DEG_PER_RAD, gy * DEG_PER_RAD, gz * DEG_PER_RAD
        buf = self._buf
        with self.sensor.i2c_device as dev:
            dev.write_then_readinto(self._reg, buf)
        if not buf[0] & GYRO_DATA_READY:
            return None
        gx, gy, gz, ax, ay, az = struct.unpack_from("<hhhhhh", buf, 4)
        a = self._a_scale
        g = self._g_scale
        return ax * a, ay * a, az * a, gx * g, gy * g, gz * g

    def read_driver(self):
        """Driver-property read in the same units, for bring-up comparison."""
        ax, ay, az = self.sensor.acceleration
        gx, gy, gz = self.sensor.gyro
        return ax, ay, az, gx * DEG_PER_RAD, gy * DEG_PER_RAD, gz * DEG_PER_RAD

    def arm_wake(self, threshold_mg, odr_hz=26, settle_s=None):
        """Low-power wake-on-motion for deep sleep (LSM6DSOX DS12814, AN5272).

        Gyro off; accelerometer at ``odr_hz`` in low-power mode, +/-2 g; the
        slope (high-pass) wake-up detector raises a *latched* INT1 (active
        high, push-pull) until WAKE_UP_SRC is read. A latch means motion during
        the last milliseconds before sleep still wakes the board. The driver's
        software reset on the next start clears all of this.

        Returns the WAKE_UP_SRC value read to clear any stale event.
        """
        import time

        threshold = int(round(threshold_mg / WAKE_MG_PER_LSB))
        threshold = max(1, min(63, threshold))
        dev = self.sensor.i2c_device
        write_register(dev, INT1_CTRL, 0x00)  # no data-ready routing on INT1
        write_register(dev, CTRL2_G, 0x00)  # gyro power-down
        write_register(dev, CTRL6_C, read_register(dev, CTRL6_C) | XL_HM_MODE)  # high-performance off
        write_register(dev, CTRL1_XL, WAKE_ODR_CODES[odr_hz] << 4)  # ODR, FS = +/-2 g
        write_register(dev, WAKE_UP_DUR, 1 << 5)  # WAKE_DUR = 1 sample; WAKE_THS_W = FS/64
        write_register(dev, WAKE_UP_THS, threshold)
        write_register(dev, TAP_CFG0, TAP_CFG0_LIR | TAP_CFG0_INT_CLR_ON_READ)  # slope filter, latched
        write_register(dev, TAP_CFG2, read_register(dev, TAP_CFG2) | TAP_CFG2_INTERRUPTS_ENABLE)
        write_register(dev, MD1_CFG, MD1_CFG_INT1_WU)
        # Let the slope filter settle (its first outputs can exceed the threshold),
        # then clear any event latched meanwhile.
        time.sleep(settle_s if settle_s is not None else 4.0 / odr_hz)
        return read_register(dev, WAKE_UP_SRC)
