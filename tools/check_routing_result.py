# SPDX-License-Identifier: MIT
"""Standard acceptance check for an externally routed copy of the handbell board.

Compares a candidate PCB and its KiCad DRC report against the frozen baseline:
existing copper must survive, parts may move only if allowed, opens must fall,
no new DRC error classes may grow, and protected nets/pads must not gain copper.
Run with the Python that matches KiCad's pcbnew (3.11 for KiCad 10).
"""
import argparse
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path

KICAD_BIN = Path(os.environ.get("KICAD_BIN", r"C:\Users\david.cuccia\AppData\Local\Programs\KiCad\10.0\bin"))
# Pads whose local return path must not be bypassed by new copper (see AGENTS.md).
PRIVATE_PADS = {("R24", "2"), ("C28", "2"), ("R26", "2"), ("R27", "2")}
ISOLATED_NETS = {"/CELL_NEG"}
PLANE_LAYERS = {"In1.Cu"}  # protected GND plane: no new tracks allowed
REQUIRED_ZONES = {"in1-protected-gnd-v1"}
# DRC types that are informational for this comparison; everything else may not grow.
IGNORED_TYPES = {"unconnected_items"}
TOL_MM = 0.002  # export rounding observed from DeepPCB is below 1 um
STEP_MM = 0.05


def load_pcbnew():
    handle = os.add_dll_directory(str(KICAD_BIN))
    sys.path.insert(0, str(KICAD_BIN / "Lib" / "site-packages"))
    import pcbnew
    return pcbnew, handle


def copper_items(pcbnew, board):
    """Return tracks and vias as plain tuples in mm, grouped by (net, layer)."""
    mm = pcbnew.ToMM
    tracks, vias = {}, {}
    for item in board.GetTracks():
        net = item.GetNetname()
        if item.GetClass() == "PCB_VIA":
            p = item.GetPosition()
            vias.setdefault(net, []).append((mm(p.x), mm(p.y), mm(item.GetWidth(pcbnew.F_Cu)),
                                             mm(item.GetDrillValue()), item))
        else:
            a, b = item.GetStart(), item.GetEnd()
            tracks.setdefault((net, item.GetLayerName()), []).append(
                (mm(a.x), mm(a.y), mm(b.x), mm(b.y), mm(item.GetWidth()), item))
    return tracks, vias


def _dist_point_segment(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    length2 = dx * dx + dy * dy
    t = 0.0 if length2 == 0 else max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / length2))
    return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def track_covered(seg, others):
    """True if every sample point of seg lies on some other centreline at least as wide."""
    x0, y0, x1, y1, width = seg[:5]
    length = math.hypot(x1 - x0, y1 - y0)
    steps = max(1, int(length / STEP_MM))
    for i in range(steps + 1):
        px, py = x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps
        if not any(o[4] >= width - TOL_MM and _dist_point_segment(px, py, *o[:4]) <= TOL_MM for o in others):
            return False
    return True


def via_covered(via, others):
    return any(math.hypot(via[0] - o[0], via[1] - o[1]) <= TOL_MM and abs(via[2] - o[2]) <= TOL_MM
               and abs(via[3] - o[3]) <= TOL_MM for o in others)


def compare_copper(base, cand):
    """Return (lost base items, new candidate items) with geometric tolerance."""
    (bt, bv), (ct, cv) = base, cand
    lost = [(k, s) for k, segs in bt.items() for s in segs if not track_covered(s, ct.get(k, []))]
    lost += [(n, v) for n, vs in bv.items() for v in vs if not via_covered(v, cv.get(n, []))]
    new = [(k, s) for k, segs in ct.items() for s in segs if not track_covered(s, bt.get(k, []))]
    new += [(n, v) for n, vs in cv.items() for v in vs if not via_covered(v, bv.get(n, []))]
    return lost, new


def parts(pcbnew, board):
    mm = pcbnew.ToMM
    return {fp.GetReference(): (mm(fp.GetPosition().x), mm(fp.GetPosition().y),
                                fp.GetOrientationDegrees(), fp.GetLayerName())
            for fp in board.GetFootprints()}


def moved(a, b):
    turn = (a[2] - b[2]) % 360
    return (math.hypot(a[0] - b[0], a[1] - b[1]) > 0.001 or min(turn, 360 - turn) > 0.01
            or a[3] != b[3])


def drc_counts(path):
    report = json.loads(Path(path).read_text(encoding="utf-8"))
    counts = Counter(v["type"] for v in report.get("violations", []))
    counts["unconnected_items"] = len(report.get("unconnected_items", []))
    counts["schematic_parity"] = len(report.get("schematic_parity", []))
    return counts


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--base-drc", required=True)
    ap.add_argument("--candidate-drc", required=True)
    ap.add_argument("--allow-move", nargs="*", default=[])
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    pcbnew, _handle = load_pcbnew()
    base_board = pcbnew.LoadBoard(str(args.base))
    cand_board = pcbnew.LoadBoard(str(args.candidate))
    base_parts, cand_parts = parts(pcbnew, base_board), parts(pcbnew, cand_board)
    cand_pads = {(fp.GetReference(), p.GetNumber()): p for fp in cand_board.GetFootprints() for p in fp.Pads()}
    base_zones = {z.GetZoneName() for z in base_board.Zones()}
    cand_zones = {z.GetZoneName() for z in cand_board.Zones()}
    failures, notes = [], []

    if set(base_parts) != set(cand_parts):
        failures.append(f"Footprint set changed: missing {sorted(set(base_parts) - set(cand_parts))}, "
                        f"added {sorted(set(cand_parts) - set(base_parts))}")
    moved_refs = sorted(r for r in base_parts if r in cand_parts and moved(base_parts[r], cand_parts[r]))
    unapproved = [r for r in moved_refs if r not in set(args.allow_move)]
    if unapproved:
        failures.append(f"Unapproved part moves: {unapproved}")

    lost, new = compare_copper(copper_items(pcbnew, base_board), copper_items(pcbnew, cand_board))
    if lost:
        failures.append(f"{len(lost)} existing track/via items not preserved")
        notes.append("lost examples: " + "; ".join(f"{k} {[round(v, 4) for v in s[:4]]}" for k, s in lost[:6]))
    missing_zones = (REQUIRED_ZONES & base_zones) - cand_zones
    if missing_zones:
        failures.append(f"Required zones missing: {sorted(missing_zones)}")

    def net_of(key):
        return key[0] if isinstance(key, tuple) else key

    bad_net = [k for k, _ in new if net_of(k) in ISOLATED_NETS]
    if bad_net:
        failures.append(f"{len(bad_net)} new copper items on isolated nets {sorted(ISOLATED_NETS)}")
    plane_tracks = [k for k, _ in new if isinstance(k, tuple) and k[1] in PLANE_LAYERS]
    if plane_tracks:
        failures.append(f"{len(plane_tracks)} new tracks on plane layers {sorted(PLANE_LAYERS)}")
    touching = []
    for _key, item in new:
        obj = item[-1]
        if obj.GetClass() == "PCB_VIA":
            points = [obj.GetPosition()]
        else:
            points = [obj.GetStart(), obj.GetEnd()]
        for ref_pad in PRIVATE_PADS:
            pad = cand_pads.get(ref_pad)
            if pad and any(pad.HitTest(pt) for pt in points) and (
                    obj.GetClass() == "PCB_VIA" or pad.IsOnLayer(obj.GetLayer())):
                touching.append(f"{ref_pad[0]}.{ref_pad[1]}")
    if touching:
        failures.append(f"New copper lands on private-return pads: {sorted(set(touching))}")

    base_drc, cand_drc = drc_counts(args.base_drc), drc_counts(args.candidate_drc)
    grown = {t: (base_drc[t], cand_drc[t]) for t in set(base_drc) | set(cand_drc)
             if t not in IGNORED_TYPES and cand_drc[t] > base_drc[t]}
    if grown:
        failures.append(f"DRC types increased (base, candidate): {grown}")
    if cand_drc["unconnected_items"] >= base_drc["unconnected_items"] and not grown:
        failures.append("Open count did not decrease")
    notes.append(f"opens {base_drc['unconnected_items']} -> {cand_drc['unconnected_items']}")
    notes.append(f"new copper items: {len(new)}; moved parts: {moved_refs}")

    result = {"status": "PASS" if not failures else "FAIL", "failures": failures, "notes": notes,
              "drc_base": dict(base_drc), "drc_candidate": dict(cand_drc),
              "added_by_net": dict(Counter(net_of(k) for k, _ in new))}
    Path(args.report).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
