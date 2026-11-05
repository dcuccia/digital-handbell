# SPDX-License-Identifier: MIT
"""Standard acceptance check for an externally routed copy of the handbell board.

Compares a candidate PCB and its KiCad DRC report against the frozen baseline:
existing copper must survive, parts may move only if allowed, opens must fall,
no new DRC error classes may grow, and protected nets/pads must not gain copper.
Run with the Python that matches KiCad's pcbnew (3.11 for KiCad 10).
"""
import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

KICAD_BIN = Path(os.environ.get("KICAD_BIN", r"C:\Users\david.cuccia\AppData\Local\Programs\KiCad\10.0\bin"))
# Pads whose local return path must not be bypassed by new copper (see AGENTS.md).
PRIVATE_PADS = {("R24", "2"), ("C28", "2"), ("R26", "2"), ("R27", "2")}
ISOLATED_NETS = {"/CELL_NEG"}
REQUIRED_ZONES = {"in1-protected-gnd-v1"}
# DRC types that are informational for this comparison; everything else may not grow.
IGNORED_TYPES = {"unconnected_items"}


def load_pcbnew():
    handle = os.add_dll_directory(str(KICAD_BIN))
    sys.path.insert(0, str(KICAD_BIN / "Lib" / "site-packages"))
    import pcbnew
    return pcbnew, handle


def snapshot(pcbnew, path):
    board = pcbnew.LoadBoard(str(path))
    mm = pcbnew.ToMM
    parts, pads, copper = {}, {}, Counter()
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        pos = fp.GetPosition()
        parts[ref] = (round(mm(pos.x), 4), round(mm(pos.y), 4),
                      round(fp.GetOrientationDegrees(), 3), fp.GetLayerName())
        for pad in fp.Pads():
            pads[(ref, pad.GetNumber())] = pad
    for item in board.GetTracks():
        net = item.GetNetname()
        if item.GetClass() == "PCB_VIA":
            p = item.GetPosition()
            key = ("via", net, round(mm(p.x), 4), round(mm(p.y), 4),
                   round(mm(item.GetWidth(pcbnew.F_Cu)), 4), round(mm(item.GetDrillValue()), 4))
        else:
            a, b = item.GetStart(), item.GetEnd()
            ends = sorted([(round(mm(a.x), 4), round(mm(a.y), 4)), (round(mm(b.x), 4), round(mm(b.y), 4))])
            key = ("track", net, item.GetLayerName(), *ends[0], *ends[1], round(mm(item.GetWidth()), 4))
        copper[key] += 1
    zones = {z.GetZoneName() for z in board.Zones()}
    return board, parts, pads, copper, zones


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
    _, base_parts, _, base_copper, base_zones = snapshot(pcbnew, args.base)
    cand_board, cand_parts, cand_pads, cand_copper, cand_zones = snapshot(pcbnew, args.candidate)
    failures, notes = [], []

    if set(base_parts) != set(cand_parts):
        failures.append(f"Footprint set changed: missing {sorted(set(base_parts) - set(cand_parts))}, "
                        f"added {sorted(set(cand_parts) - set(base_parts))}")
    moved = sorted(r for r in base_parts if r in cand_parts and base_parts[r] != cand_parts[r])
    unapproved = [r for r in moved if r not in set(args.allow_move)]
    if unapproved:
        failures.append(f"Unapproved part moves: {unapproved}")

    lost = base_copper - cand_copper
    added = cand_copper - base_copper
    if lost:
        failures.append(f"{sum(lost.values())} existing track/via items changed or removed")
    missing_zones = (REQUIRED_ZONES & base_zones) - cand_zones
    if missing_zones:
        failures.append(f"Required zones missing: {sorted(missing_zones)}")

    bad_net = [k for k in added if k[1] in ISOLATED_NETS]
    if bad_net:
        failures.append(f"{len(bad_net)} new copper items on isolated nets {sorted(ISOLATED_NETS)}")
    touching = []
    new_tracks = [t for t in cand_board.GetTracks()]
    for item in new_tracks:
        if item.GetClass() == "PCB_VIA":
            p = item.GetPosition()
            key = ("via", item.GetNetname(), round(pcbnew.ToMM(p.x), 4), round(pcbnew.ToMM(p.y), 4),
                   round(pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu)), 4), round(pcbnew.ToMM(item.GetDrillValue()), 4))
            points = [p]
        else:
            a, b = item.GetStart(), item.GetEnd()
            ends = sorted([(round(pcbnew.ToMM(a.x), 4), round(pcbnew.ToMM(a.y), 4)),
                           (round(pcbnew.ToMM(b.x), 4), round(pcbnew.ToMM(b.y), 4))])
            key = ("track", item.GetNetname(), item.GetLayerName(), *ends[0], *ends[1],
                   round(pcbnew.ToMM(item.GetWidth()), 4))
            points = [a, b]
        if key not in added:
            continue
        for ref_pad in PRIVATE_PADS:
            pad = cand_pads.get(ref_pad)
            if pad and any(pad.HitTest(pt) for pt in points) and pad.IsOnLayer(item.GetLayer()):
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
    notes.append(f"new copper items: {sum(added.values())}; moved parts: {moved}")

    result = {"status": "PASS" if not failures else "FAIL", "failures": failures, "notes": notes,
              "drc_base": dict(base_drc), "drc_candidate": dict(cand_drc),
              "added_by_net": dict(Counter(k[1] for k in added.elements()))}
    Path(args.report).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
