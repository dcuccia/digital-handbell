#!/usr/bin/env python3
"""Replay recorded IMU traces through the detector and instrument on a computer.

Use it to tune ``detector`` parameters without hardware: the same core code
runs here and on the board. Reports detected rings, the gestures the device
logged during recording (if any), and what the instrument would have played.

    python firmware/scripts/replay.py firmware/traces/local/x.jsonl [--params '{"min_decel": 5000}'] [--json]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402

_common.add_src_to_path()
from handbell.core import config as hb_config  # noqa: E402
from handbell.core.instrument import Instrument  # noqa: E402
from handbell.platforms.desktop import ListLink, SimAudio, read_gestures, read_trace  # noqa: E402


def replay(path, overrides=None, config_path=None):
    raw_cfg = {}
    if config_path:
        with open(config_path, encoding="utf-8") as f:
            raw_cfg = json.load(f)
    if overrides:
        raw_cfg = hb_config.merge(raw_cfg, {"detector": overrides})
    cfg = hb_config.parse(raw_cfg)
    audio = SimAudio(cfg.power["settle_ms"], cfg.power["clock_ms"])
    link = ListLink()
    inst = Instrument(cfg, audio, link=link)
    started = False
    samples = 0
    last_t = 0
    for t_us, sample in read_trace(path):
        if not started:
            inst.start(t_us)
            started = True
        inst.on_motion(t_us, sample)
        inst.tick(t_us)
        samples += 1
        last_t = t_us
    rings = [m for m in link.messages("gesture") if m["g"] == "ring"]
    recorded = [g for g in read_gestures(path) if g.get("g") == "ring"]
    return {
        "trace": str(path),
        "samples": samples,
        "duration_s": round(last_t / 1e6, 3) if samples else 0,
        "detector": inst.ring.effective(),
        "rings": [{"t": r["t"], "vel": r["vel"], "det": r["det"]} for r in rings],
        "recorded_rings": len(recorded),
        "plays": [{"t_ms": p[1] / 1000.0, "bell": p[2], "level": p[3], "start_delay_ms": p[4] / 1000.0} for p in audio.plays()],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("traces", nargs="+")
    ap.add_argument("--params", help="JSON detector overrides, e.g. '{\"min_decel\": 5000}'")
    ap.add_argument("--config", help="bells.json to use (default: built-in defaults)")
    ap.add_argument("--json", action="store_true", help="print full JSON results")
    args = ap.parse_args(argv)
    overrides = json.loads(args.params) if args.params else None
    results = [replay(Path(t), overrides, args.config) for t in args.traces]
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            print(
                "%s: %d samples over %.1f s -> %d rings detected (device logged %d), %d plays"
                % (r["trace"], r["samples"], r["duration_s"], len(r["rings"]), r["recorded_rings"], len(r["plays"]))
            )
            for ring in r["rings"]:
                print("  ring t=%s ms vel=%.2f det=%s ms" % (ring["t"], ring["vel"], ring["det"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
