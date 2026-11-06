# SPDX-License-Identifier: MIT
"""Remove tracks/vias of selected nets near a component so a router can redo the area.

Experimental rip-up on a copy only. Items with any endpoint within --radius mm
of the component centre are removed; zones, pads and all other nets are kept.
"""
import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_routing_result as crr  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True)
    ap.add_argument("--ref", default="IC1")
    ap.add_argument("--radius", type=float, default=7.0)
    ap.add_argument("--nets", nargs="+", required=True)
    ap.add_argument("--keep-vias-of", nargs="*", default=["GND"])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    pcbnew, _h = crr.load_pcbnew()
    board = pcbnew.LoadBoard(args.board)
    mm = pcbnew.ToMM
    centre = board.FindFootprintByReference(args.ref).GetPosition()
    cx, cy = mm(centre.x), mm(centre.y)
    nets = set(args.nets)
    removed = {}
    for item in list(board.GetTracks()):
        net = item.GetNetname()
        if net not in nets:
            continue
        is_via = item.GetClass() == "PCB_VIA"
        if is_via and net in args.keep_vias_of:
            continue
        points = [item.GetPosition()] if is_via else [item.GetStart(), item.GetEnd()]
        if any(math.hypot(mm(p.x) - cx, mm(p.y) - cy) < args.radius for p in points):
            board.Remove(item)
            removed[net] = removed.get(net, 0) + 1
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(args.out, board)
    print(json.dumps({"radius_mm": args.radius, "removed_by_net": removed}, indent=2))


if __name__ == "__main__":
    main()
