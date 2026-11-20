"""Bench profile: Adafruit Feather RP2040 Prop-Maker (5768) + LSM6DSOX breakout.

The handbell board was derived from the Prop-Maker and keeps the same I2S
(GPIO16-18), EXTERNAL_POWER (GPIO23), EXTERNAL_BUTTON (GPIO19) and I2C
(GPIO2/3) pins. Connect an LSM6DSOX breakout (for example Adafruit 4438) to
the STEMMA QT port at its default 0x6A address; the onboard LIS3DH (0x18)
has no gyroscope and is not used. There is no AMP_MUTE line: GPIO20 is the
servo pin, so mute is skipped and EXTERNAL_POWER alone gates the amplifier.
Wire a normally-open button between the EXTERNAL_BUTTON terminal and GND.
"""

NAME = "feather_propmaker_rp2040"

CAPS = {
    "imu": "lsm6dsox",
    "imu_address": 0x6A,
    "button_active_low": True,
    "mute": False,
    "vbat_ratio": None,
    "radio": None,
}


def pins():
    import board

    return {
        "sda": board.SDA,
        "scl": board.SCL,
        "imu_int1": None,
        "i2s_data": board.I2S_DATA,
        "i2s_bclk": board.I2S_BIT_CLOCK,
        "i2s_lrclk": board.I2S_WORD_SELECT,
        "button": board.EXTERNAL_BUTTON,
        "amp_mute": None,
        "power": board.EXTERNAL_POWER,
        "led": board.LED,
    }


def build(cfg):
    from handbell.hw.build import build_ports

    return build_ports(NAME, pins(), CAPS, cfg)
