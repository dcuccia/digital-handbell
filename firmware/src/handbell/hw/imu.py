"""LSM6DSOX motion source using the unmodified Adafruit driver.

The driver configures the sensor. Reads then use one 16-byte burst from
STATUS_REG (0x1E) through OUTZ_H_A (0x2D) on the driver's own I2CDevice, so
each loop costs one I2C transaction, allocates nothing and skips samples
the sensor has not refreshed (gyro data-ready bit). ``fast_read: false`` in
bells.json uses the driver's ``acceleration``/``gyro`` properties instead.
"""

import struct

from handbell.hw.lsm6dsox_fix import fix_ctrl9_xl

DEG_PER_RAD = 57.29577951308232
STANDARD_GRAVITY = 9.80665
STATUS_REG = 0x1E
GYRO_DATA_READY = 0x02
GYRO_MDPS_PER_LSB = {125: 4.375, 250: 8.75, 500: 17.5, 1000: 35.0, 2000: 70.0}
ACCEL_MG_PER_LSB = {2: 0.061, 4: 0.122, 8: 0.244, 16: 0.488}


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
