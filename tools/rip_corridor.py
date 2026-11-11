# SPDX-License-Identifier: MIT
"""Rip up router-added copper of other nets along the corridor of selected open links.

Experimental rip-up step for rip-up-and-reroute on private copies. Only copper
absent from the frozen base board is eligible; protected nets are never touched.
Run DRC afterwards and re-route (target nets first, then all).
"""
import argparse
import json
import sys
from pathlib import Path

from shapely.geometry import LineString

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_routing_result as crr  # noqa: E402
from stitch_gnd_islands import item_shape  # noqa: E402

PROTECTED = {"/CELL_NEG", "VBAT"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True)
    ap.add_argument("--base-board", required=True, help="frozen board; its copper is never removed")
    ap.add_argument("--drc", required=True)
    ap.add_argument("--nets", nargs="+", required=True)
    ap.add_argument("--width", type=float, default=1.0, help="corridor width (mm)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    report = json.loads(Path(args.drc).read_text(encoding="utf-8"))
    corridors = []
    for u in report.get("unconnected_items", []):
        a, b = u["items"][0], u["items"][1]
        if crr.drc_net(a["description"]) in args.nets:
            corridors.append(LineString([(a["pos"]["x"], a["pos"]["y"]), (b["pos"]["x"], b["pos"]["y"])])
                             .buffer(args.width / 2))
    pcbnew, _h = crr.load_pcbnew()
    base = pcbnew.LoadBoard(args.base_board)
    board = pcbnew.LoadBoard(args.board)
    _, new = crr.compare_copper(crr.copper_items(pcbnew, base), crr.copper_items(pcbnew, board))
    removed = {}
    for key, item in new:
        obj = item[-1]
        net = obj.GetNetname()
        if net in args.nets or net in PROTECTED or net.startswith("/PROT"):
            continue
        layer = pcbnew.F_Cu if obj.GetClass() == "PCB_VIA" else obj.GetLayer()
        shape = item_shape(pcbnew, obj, layer)
        if any(shape.intersects(c) for c in corridors):
            removed[net] = removed.get(net, 0) + 1
            board.Remove(obj)
    pcbnew.SaveBoard(args.out, board)
    print(json.dumps({"corridors": len(corridors), "removed_by_net": removed}, indent=2))


if __name__ == "__main__":
    main()
