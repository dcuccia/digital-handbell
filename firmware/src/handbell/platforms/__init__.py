"""Platform selection.

The active platform comes from ``HANDBELL_PLATFORM`` in settings.toml, or
from ``board.board_id``. The day-one custom board runs the stock Raspberry
Pi Pico build (same W25Q16JV flash family), so ``raspberry_pi_pico`` maps to
the handbell profile. A future custom board definition adds its own id here.
"""

PROFILES = {
    "handbell_rp2040": "handbell.platforms.handbell_rp2040",
    "feather_propmaker_rp2040": "handbell.platforms.feather_propmaker_rp2040",
    "esp32s3_handbell": "handbell.platforms.esp32s3_handbell",
}

BOARD_IDS = {
    "raspberry_pi_pico": "handbell_rp2040",
    "digital_handbell_rp2040": "handbell_rp2040",
    "adafruit_feather_rp2040_prop_maker": "feather_propmaker_rp2040",
}


def profile_name(explicit=None):
    if explicit:
        return explicit
    try:
        import os

        name = os.getenv("HANDBELL_PLATFORM")
        if name:
            return name
    except (ImportError, AttributeError):
        pass
    import board

    board_id = getattr(board, "board_id", "")
    if board_id in BOARD_IDS:
        return BOARD_IDS[board_id]
    raise RuntimeError(
        "No handbell platform for board_id %r; set HANDBELL_PLATFORM in settings.toml to one of %s"
        % (board_id, ", ".join(sorted(PROFILES)))
    )


def load(name=None):
    name = profile_name(name)
    if name == "handbell_rp2040":
        from handbell.platforms import handbell_rp2040 as module
    elif name == "feather_propmaker_rp2040":
        from handbell.platforms import feather_propmaker_rp2040 as module
    elif name == "esp32s3_handbell":
        from handbell.platforms import esp32s3_handbell as module
    else:
        raise RuntimeError("Unknown HANDBELL_PLATFORM %r; expected one of %s" % (name, ", ".join(sorted(PROFILES))))
    return module
