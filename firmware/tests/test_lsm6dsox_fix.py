import pytest

from handbell.hw.lsm6dsox_fix import CTRL9_XL, corrected, fix_ctrl9_xl


class FakeI2CDevice:
    """Mimics adafruit_bus_device.I2CDevice for one register file."""

    def __init__(self, regs, stuck=False):
        self.regs = dict(regs)
        self.stuck = stuck
        self.writes = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def write_then_readinto(self, out, buf):
        buf[0] = self.regs[out[0]]

    def write(self, data):
        self.writes.append(bytes(data))
        if not self.stuck:
            self.regs[data[0]] = data[1]


def test_corrected_sets_i3c_disable_and_clears_reserved_bit():
    assert corrected(0xE1) == 0xE2
    assert corrected(0xE0) == 0xE2
    assert corrected(0xE2) == 0xE2
    assert corrected(0xFF) == 0xFE


def test_fix_after_driver_init_preserves_other_bits():
    # The pinned driver leaves CTRL9_XL at reset 0xE0 with bit 0 set.
    dev = FakeI2CDevice({CTRL9_XL: 0xE1})
    assert fix_ctrl9_xl(dev) == (0xE1, 0xE2)
    assert dev.writes == [bytes((CTRL9_XL, 0xE2))]


def test_no_write_when_already_correct():
    dev = FakeI2CDevice({CTRL9_XL: 0xE2})
    assert fix_ctrl9_xl(dev) == (0xE2, 0xE2)
    assert dev.writes == []


def test_readback_mismatch_raises():
    with pytest.raises(RuntimeError):
        fix_ctrl9_xl(FakeI2CDevice({CTRL9_XL: 0xE1}, stuck=True))
