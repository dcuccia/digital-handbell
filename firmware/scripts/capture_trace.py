#!/usr/bin/env python3
"""Record the device's HGP-shaped serial output to a JSON-lines trace.

Works with ``import bringup.record_trace`` (raw IMU rows) or the instrument
with ``"debug": {"raw": true}`` in bells.json. Close other serial monitors
first. Traces are for non-identifying motion only; describe the motion in
--label, never a person.

    python firmware/scripts/capture_trace.py --label "full rings, slow" [--port COM5] [--seconds 60]
"""

import argparse
import datetime
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402

# Raspberry Pi (Pico build) and Adafruit USB vendor ids.
VENDOR_IDS = (0x2E8A, 0x239A)


def find_port():
    from serial.tools import list_ports

    ports = [p for p in list_ports.comports() if p.vid in VENDOR_IDS]
    if not ports:
        _common.fail("no CircuitPython serial port found; pass --port")
    if len(ports) > 1:
        _common.log("several candidate ports; using %s (pass --port to choose)" % ports[0].device)
    return ports[0].device


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--port")
    ap.add_argument("--label", required=True, help="motion description, e.g. 'full rings, slow tempo'")
    ap.add_argument("--seconds", type=float, default=0, help="stop after this long (0 = until Ctrl-C)")
    ap.add_argument("--out", help="output .jsonl (default firmware/traces/local/<timestamp>.jsonl)")
    args = ap.parse_args(argv)
    try:
        import serial
    except ImportError:
        _common.fail("pyserial is missing: python firmware/scripts/setup_dev.py")

    port = args.port or find_port()
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = Path(args.out) if args.out else _common.FIRMWARE / "traces" / "local" / ("%s.jsonl" % stamp)
    out.parent.mkdir(parents=True, exist_ok=True)
    meta = {"type": "meta", "label": args.label, "recorded": stamp, "tool": "capture_trace.py"}
    lines = rings = 0
    end = time.monotonic() + args.seconds if args.seconds else None
    _common.log("recording %s -> %s (Ctrl-C to stop)" % (port, out))
    with serial.Serial(port, 115200, timeout=0.5) as ser, open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(meta) + "\n")
        try:
            while end is None or time.monotonic() < end:
                raw = ser.readline()
                if not raw:
                    continue
                text = raw.decode("utf-8", "replace").strip()
                if not text.startswith("{"):
                    if text:
                        print("device:", text)
                    continue
                try:
                    msg = json.loads(text)
                except ValueError:
                    continue
                f.write(text + "\n")
                lines += 1
                if msg.get("type") == "gesture":
                    rings += 1
                    print("gesture", msg.get("g"), "t=%s vel=%s" % (msg.get("t"), msg.get("vel")))
        except KeyboardInterrupt:
            pass
    _common.log("saved %d messages (%d gestures) to %s" % (lines, rings, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
