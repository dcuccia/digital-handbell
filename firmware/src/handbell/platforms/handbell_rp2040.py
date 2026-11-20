"""The custom RP2040 handbell board (six-layer prototype, November 2026).

Pin table from the ordered schematic netlist (hardware/handbell). Uses
``microcontroller.pin`` names so it works on the stock Raspberry Pi Pico
CircuitPython build as well as a future custom board definition.

This board has no battery, USB-presence or charge-status inputs. A next
revision that adds them (see docs/hardware-revision-requests.md) needs only
new entries here, for example ``"vbat_sense": pin.GPIO29`` with
``CAPS["vbat_ratio"] = 3.0`` and ``"vbus_sense": pin.GPIO24``.
"""

NAME = "handbell_rp2040"

CAPS = {
    "imu": "lsm6dsox",
    "imu_address": 0x6A,  # SDO tied to GND
    "button_active_low": True,  # J2 pin 1 BUTTON_EXT, pin 2 GND; 10 kohm pull-up
    "mute": True,
    "vbat_ratio": None,  # GPIO26-29 are unconnected on this board
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
        "vbat_sense": None,
        "vbus_sense": None,
        "charge_stat": None,
    }


def build(cfg):
    from handbell.hw.build import build_ports

    return build_ports(NAME, pins(), CAPS, cfg)
