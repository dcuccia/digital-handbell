# SPDX-License-Identifier: MIT
"""Resolve placement-vs-copper conflicts after a placement change (private copies).

1. Parts named with --movable whose pads short or crowd other-net copper are
   nudged (search within --radius) to the nearest position where every pad
   clears other-net copper by --clearance and the courtyard overlaps nothing.
2. Track/via islands named by DRC items_not_allowed and absent from the
   keep-list nets are removed so the router can redo them.
Existing kept copper is never moved.
"""
import argparse
import json
import math
import sys
from pathlib import Path

from shapely import affinity
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_routing_result as crr  # noqa: E402
import move_cluster as mc  # noqa: E402
from stitch_gnd_islands import item_shape  # noqa: E402

LAYERS = ("F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True)
    ap.add_argument("--drc", required=True)
    ap.add_argument("--movable", nargs="+", required=True)
    ap.add_argument("--keep-nets", nargs="*", default=["/CELL_NEG", "VBAT", "GND"])
    ap.add_argument("--clearance", type=float, default=0.2)
    ap.add_argument("--radius", type=float, default=3.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--skip-removal", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--avoid-circle", nargs=3, type=float, metavar=("X", "Y", "R"),
                    help="keep the movable parts' courtyards outside this circle (e.g. a tall-part height zone)")
    args = ap.parse_args()

    pcbnew, _h = crr.load_pcbnew()
    mm = pcbnew.ToMM
    board = pcbnew.LoadBoard(args.board)
    report = json.loads(Path(args.drc).read_text(encoding="utf-8"))
    layer_ids = {n: board.GetLayerID(n) for n in LAYERS}

    # Step 2 first (needs only DRC positions): drop non-kept copper in keep-outs.
    bad = [(i["description"], i["pos"]["x"], i["pos"]["y"]) for v in report["violations"]
           if v["type"] == "items_not_allowed" for i in v["items"]]
    removed = []
    for item in ([] if args.skip_removal else list(board.GetTracks())):
        net = item.GetNetname()
        if net in args.keep_nets or net.startswith("/PROT") or net == "/CELL_NEG":
            continue
        pts = [item.GetPosition()] if item.GetClass() == "PCB_VIA" else [item.GetStart(), item.GetEnd()]
        for desc, x, y in bad:
            if f"[{net}]" in desc and any(abs(mm(p.x) - x) < 0.01 and abs(mm(p.y) - y) < 0.01 for p in pts):
                removed.append(net)
                board.Remove(item)
                break
    # pcbnew's Python wrappers break process-wide after Remove(); fit in a fresh process.
    if removed and not args.skip_removal:
        tmp = args.out + ".tmp.kicad_pcb"
        pcbnew.SaveBoard(tmp, board)
        import subprocess
        cmd = [sys.executable, __file__, "--board", tmp, "--drc", args.drc, "--skip-removal",
               "--clearance", str(args.clearance), "--radius", str(args.radius),
               "--out", args.out, "--report", args.report, "--movable", *args.movable,
               "--keep-nets", *args.keep_nets]
        rc = subprocess.call(cmd)
        Path(tmp).unlink()
        rep = json.loads(Path(args.report).read_text(encoding="utf-8"))
        rep["removed_in_keepouts"] = len(removed)
        rep["removed_nets"] = sorted(set(removed))
        Path(args.report).write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
        sys.exit(rc)

    copper = {n: [] for n in LAYERS}
    for item in board.GetTracks():
        for n, lid in layer_ids.items():
            if item.IsOnLayer(lid):
                copper[n].append((item.GetNetname(), None, item_shape(pcbnew, item, lid)))
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            for n, lid in layer_ids.items():
                if pad.IsOnLayer(lid):
                    copper[n].append((pad.GetNetname(), fp.GetReference(), item_shape(pcbnew, pad, lid)))
    courts = {fp.GetReference(): (fp.GetLayer(), mc.footprint_area(pcbnew, fp)) for fp in board.GetFootprints()}
    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline, False)
    from stitch_gnd_islands import poly_set_to_shapely
    inner = unary_union(poly_set_to_shapely(pcbnew, outline)).buffer(-0.3)
    from shapely.geometry import Point
    avoid = Point(args.avoid_circle[0], args.avoid_circle[1]).buffer(args.avoid_circle[2]) if args.avoid_circle else None

    def conflicts(ref, pads, court, dx, dy):
        for n, lid in layer_ids.items():
            mine = [(net, affinity.translate(s, dx, dy)) for net, s in pads.get(n, [])]
            if not mine:
                continue
            for onet, oref, oshape in copper[n]:
                if oref == ref:
                    continue
                for net, s in mine:
                    if net != onet and s.distance(oshape) < args.clearance:
                        return True
        moved = affinity.translate(court[1], dx, dy)
        if not inner.contains(moved):
            return True
        if avoid is not None and moved.intersects(avoid):
            return True
        return any(r != ref and side == court[0] and moved.intersects(c) and moved.intersection(c).area > 0
                   for r, (side, c) in courts.items())

    moves = {}
    offsets = sorted(((x * 0.1, y * 0.1) for x in range(-int(args.radius * 10), int(args.radius * 10) + 1)
                      for y in range(-int(args.radius * 10), int(args.radius * 10) + 1)),
                     key=lambda d: math.hypot(*d))
    for ref in args.movable:
        fp = board.FindFootprintByReference(ref)
        pads = {}
        for pad in fp.Pads():
            for n, lid in layer_ids.items():
                if pad.IsOnLayer(lid):
                    pads.setdefault(n, []).append((pad.GetNetname(), item_shape(pcbnew, pad, lid)))
        court = courts[ref]
        if not conflicts(ref, pads, court, 0, 0):
            continue
        for dx, dy in offsets:
            if not conflicts(ref, pads, court, dx, dy):
                fp.Move(pcbnew.VECTOR2I(pcbnew.FromMM(dx), pcbnew.FromMM(dy)))
                courts[ref] = (court[0], affinity.translate(court[1], dx, dy))
                for n in pads:
                    copper[n] = [(on, orf, s if orf != ref else affinity.translate(s, dx, dy))
                                 for on, orf, s in copper[n]]
                moves[ref] = [round(dx, 2), round(dy, 2)]
                break
        else:
            moves[ref] = "no legal position within radius"

    pcbnew.SaveBoard(args.out, board)
    result = {"removed_in_keepouts": len(removed), "removed_nets": sorted(set(removed)), "moves": moves}
    Path(args.report).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
