"""The custom RP2040 handbell board (six-layer prototype, November 2026).

Pin table from the ordered schematic netlist (hardware/handbell). Uses
``microcontroller.pin`` names so it works on the stock Raspberry Pi Pico
CircuitPython build as well as a future custom board definition.
"""

NAME = "handbell_rp2040"

CAPS = {
    "imu": "lsm6dsox",
    "imu_address": 0x6A,  # SDO tied to GND
    "button_active_low": True,  # J2 pin 1 BUTTON_EXT, pin 2 GND; 10 kohm pull-up
    "mute": True,
    "battery_sense": False,  # GPIO26-29 are unconnected
    "radio": None,
}


def pins():
    from microcontroller import pin

    return {
        "sda": pin.GPIO2,
        "scl": pin.GPIO3,
        "imu_int1": pin.GPIO22,
        "i2s_data": pin.GPIO16,
        "i2s_bclk": pin.GPIO17,
        "i2s_lrclk": pin.GPIO18,
        "button": pin.GPIO19,
        "amp_mute": pin.GPIO20,  # high = mute
        "power": pin.GPIO23,  # high = boost/amplifier input on
        "led": pin.GPIO13,
    }


def build(cfg):
    from handbell.hw.build import build_ports

    return build_ports(NAME, pins(), CAPS, cfg)
