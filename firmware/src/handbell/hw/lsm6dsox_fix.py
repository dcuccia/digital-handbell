"""Post-initialization correction for the LSM6DSOX CTRL9_XL register.

The pinned ``adafruit_lsm6ds`` (4.6.3, commit cdfc14a6) declares
``_i3c_disable`` on CTRL9_XL bit 1 and then redeclares it on bit 0, so the
constructor sets reserved bit 0 instead of I3C_disable (bit 1). ST DS12814
requires bit 0 to stay 0. See issue #13.

Rather than patch the library, read-modify-write CTRL9_XL after the driver
is constructed: set bit 1, clear bit 0, preserve bits 7..2, then verify.
"""

CTRL9_XL = 0x18
I3C_DISABLE = 0x02
RESERVED_BIT0 = 0x01


def corrected(value):
    return (value | I3C_DISABLE) & ~RESERVED_BIT0 & 0xFF


def read_register(device, register):
    buf = bytearray(1)
    with device as i2c:
        i2c.write_then_readinto(bytes((register,)), buf)
    return buf[0]


def write_register(device, register, value):
    with device as i2c:
        i2c.write(bytes((register, value & 0xFF)))


def fix_ctrl9_xl(device):
    """Correct CTRL9_XL on an ``adafruit_bus_device`` I2CDevice.

    Returns ``(before, after)``. Raises RuntimeError if the readback is wrong.
    """
    before = read_register(device, CTRL9_XL)
    want = corrected(before)
    if want != before:
        write_register(device, CTRL9_XL, want)
    after = read_register(device, CTRL9_XL)
    if after != want:
        raise RuntimeError("CTRL9_XL readback 0x%02X, expected 0x%02X" % (after, want))
    return before, after
