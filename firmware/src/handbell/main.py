"""Device entry point (called from code.py).

On any startup or runtime error the audio path is shut down first (muted,
clocks stopped, power off), then the error is printed and the status LED
blinks rapidly. Ctrl-C at the serial console also shuts down audio first.
"""

import json
import os
import time

CONFIG_PATH = "/bells.json"
BUILD_INFO_PATH = "/build_info.json"


def load_config(path=CONFIG_PATH):
    from handbell.core import config

    try:
        f = open(path)
    except OSError:
        return config.parse(None), "defaults (no %s)" % path
    with f:
        raw = json.load(f)
    return config.parse(raw), path


def missing_assets(cfg):
    missing = []
    for bell in cfg.bells:
        if bell.kind in ("mp3", "wav"):
            try:
                os.stat(bell.sound)
            except OSError:
                missing.append(bell.sound)
    return missing


def build_info():
    try:
        with open(BUILD_INFO_PATH) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _cold_start():
    """True on power-up or reset, False when code.py reloads (file save, Ctrl-D)."""
    try:
        import supervisor

        return supervisor.runtime.run_reason == supervisor.RunReason.STARTUP
    except (ImportError, AttributeError):
        return False


def _error_blink(ports, message):
    led = getattr(ports, "indicator", None) if ports is not None else None
    last_print = time.monotonic()
    on = False
    while True:
        if led is not None:
            on = not on
            led.set(on)
        time.sleep(0.1)
        if time.monotonic() - last_print > 10:
            print("handbell error:", message)
            last_print = time.monotonic()


def main():
    from handbell import __version__

    ports = None
    try:
        cfg, source = load_config()
        missing = missing_assets(cfg)
        if missing:
            raise RuntimeError("missing sound files: %s (deploy with scripts/deploy.py)" % ", ".join(missing))
        from handbell import platforms
        from handbell.hw.io import device_id

        profile = platforms.load()
        ports = profile.build(cfg)
        from handbell.core.instrument import Instrument
        from handbell import runtime

        info = build_info()
        app = "digital-handbell/%s" % info.get("version", __version__)
        print("digital-handbell", app, "profile", profile.NAME, "config", source)
        print("CTRL9_XL before/after: 0x%02X/0x%02X" % ports.info["ctrl9_xl"])
        wake = ports.sleeper.wake_reason() if ports.sleeper is not None else None
        power_on = _cold_start()
        if wake is not None:
            print("woke from deep sleep:", wake)
        inst = Instrument(cfg, ports.audio, ports.indicator, ports.store, ports.link, ports.power)
        runtime.run(ports, inst, cfg, app=app, device_id=device_id(), wake=wake, power_on=power_on)
    except KeyboardInterrupt:
        if ports is not None:
            ports.shutdown()
        raise
    except Exception as e:  # noqa: BLE001 - last-resort safety handler
        if ports is not None:
            ports.shutdown()
        import traceback

        traceback.print_exception(e)
        _error_blink(ports, repr(e))
