# SPDX-License-Identifier: MIT
"""Check capacitor-to-pin adjacency before routing (placement rule screen).

For every two-pin capacitor whose one pad is GND and whose other pad shares a
net with an IC pin (references U*, IC*, Q*, Y*, X* by default), report the
distance from the capacitor's non-GND pad to the nearest such pin.
Explicit rules (JSON list of {"cap": "C1", "pin": "U2.1", "max_mm": 3.0})
override the nearest-pin guess, so the rule names the pin the capacitor serves.

Optionally compare with a reference board (e.g. the vendor layout) and flag
capacitors that are much farther from their pin than in the reference.
Read-only; prints a table and writes a JSON report.
"""
import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_routing_result as crr  # noqa: E402

IC_PREFIXES = ("U", "IC", "Q", "Y", "X")


def pad_xy(p):
    q = p.GetPosition()
    return q.x / 1e6, q.y / 1e6


def measure(pcbnew, path, rules):
    board = pcbnew.LoadBoard(path)
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    ic_pins = {}
    for ref, fp in fps.items():
        if ref.startswith(IC_PREFIXES):
            for p in fp.Pads():
                if p.GetNetname():
                    ic_pins.setdefault(p.GetNetname(), []).append((f"{ref}.{p.GetNumber()}", pad_xy(p)))
    rule_by_cap = {r["cap"]: r for r in rules}
    out = {}
    for ref, fp in fps.items():
        if not ref.startswith("C"):
            continue
        pads = [p for p in fp.Pads() if p.GetNetname()]
        if len(pads) != 2:
            continue
        nets = [p.GetNetname() for p in pads]
        if "GND" not in nets:
            continue
        sig = pads[0] if nets[1] == "GND" else pads[1]
        sx, sy = pad_xy(sig)
        rule = rule_by_cap.get(ref)
        if rule:
            pref, pnum = rule["pin"].split(".", 1)
            tfp = fps.get(pref)
            tp = next((p for p in tfp.Pads() if p.GetNumber() == pnum), None) if tfp else None
            if tp is None:
                out[ref] = {"net": sig.GetNetname(), "pin": rule["pin"], "error": "pin not found"}
                continue
            tx, ty = pad_xy(tp)
            out[ref] = {"net": sig.GetNetname(), "pin": rule["pin"], "dist_mm": round(math.hypot(sx - tx, sy - ty), 2),
                        "max_mm": rule.get("max_mm"), "rule": True}
            continue
        cands = [(math.hypot(sx - x, sy - y), name) for name, (x, y) in ic_pins.get(sig.GetNetname(), [])]
        if cands:
            d, name = min(cands)
            out[ref] = {"net": sig.GetNetname(), "pin": name, "dist_mm": round(d, 2), "rule": False}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True)
    ap.add_argument("--reference", help="reference layout to compare against")
    ap.add_argument("--rules", help="JSON list of explicit cap->pin rules")
    ap.add_argument("--default-max", type=float, default=3.0, help="flag threshold without a rule (mm)")
    ap.add_argument("--report", required=True)
    args = ap.parse_args()
    rules = json.loads(Path(args.rules).read_text(encoding="utf-8")) if args.rules else []
    pcbnew, _ = crr.load_pcbnew()
    cur = measure(pcbnew, args.board, rules)
    ref = measure(pcbnew, args.reference, rules) if args.reference else {}
    flagged = []
    for cap in sorted(cur, key=lambda c: (len(c), c)):
        r = cur[cap]
        if "dist_mm" not in r:
            flagged.append(cap)
            continue
        limit = r.get("max_mm") or args.default_max
        rd = ref.get(cap, {}).get("dist_mm")
        r["reference_mm"] = rd
        r["flag"] = r["dist_mm"] > limit or (rd is not None and r["dist_mm"] > max(2 * rd, rd + 2.0))
        if r["flag"]:
            flagged.append(cap)
        print(f"{cap:5} {r['net']:12} -> {r['pin']:8} {r['dist_mm']:6.2f} mm"
              f"{'' if rd is None else f'  (ref {rd:.2f})'}{'  FLAG' if r['flag'] else ''}")
    Path(args.report).write_text(json.dumps({"board": args.board, "reference": args.reference,
                                             "capacitors": cur, "flagged": flagged}, indent=2), encoding="utf-8")
    print(f"flagged: {', '.join(flagged) or 'none'}")


if __name__ == "__main__":
    main()
