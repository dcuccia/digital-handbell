"""Placeholder for a future ESP32-S3 handbell (epic E12, not designed yet).

CircuitPython on ESP32-S3 provides the same ``audiobusio``, ``audiomixer``,
``audiomp3``, ``synthio``, ``keypad`` and ``busio`` APIs, so a profile
should only need:

1. A pin table like ``handbell_rp2040.pins()`` (any free GPIOs can carry I2S
   on S3; there is no BCLK/LRCLK adjacency rule).
2. ``CAPS["radio"] = "ble"`` or ``"wifi"`` and a ``Link`` adapter that
   carries the same HGP-shaped lines (``_bleio`` or ``socketpool``). The
   local strike-to-sound path must not wait on it.
3. Optionally a ``Store`` that accepts a host's ``assign`` (bell set) and
   writes ``bells.json`` through a boot.py remount policy.

Everything in ``handbell.core`` is reused unchanged.
"""

NAME = "esp32s3_handbell"

CAPS = {
    "imu": "lsm6dsox",
    "imu_address": 0x6A,
    "button_active_low": True,
    "mute": True,
    "battery_sense": None,
    "radio": "ble",
}


def pins():
    raise NotImplementedError(
        "No ESP32-S3 handbell hardware is defined yet; see "
        "docs/firmware/architecture.md (ESP32-S3 seam) and issue #12"
    )


def build(cfg):
    pins()
