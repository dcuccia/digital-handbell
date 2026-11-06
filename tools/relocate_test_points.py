# SPDX-License-Identifier: MIT
"""Relocate single-pad test points onto existing copper of their own net (private copies).

For each test point, candidate positions are sampled along its net's F.Cu
tracks. The first position (nearest the current one) where the pad clears all
other-net F.Cu copper, the courtyard overlaps no other courtyard, the part is
inside the board and outside F.Cu rule areas is used. Copper is never changed.
"""
import argparse
import json
import math
import sys
from pathlib import Path

from shapely import affinity
from shapely.geometry import Point
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_routing_result as crr  # noqa: E402
import move_cluster as mc  # noqa: E402
from stitch_gnd_islands import item_shape, poly_set_to_shapely  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True)
    ap.add_argument("--refs", nargs="+", required=True)
    ap.add_argument("--clearance", type=float, default=0.2)
    ap.add_argument("--step", type=float, default=0.1)
    ap.add_argument("--near", type=float, default=0.0,
                    help="if >0, also try free spots within this distance (mm) of own-net pads of other parts")
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    pcbnew, _h = crr.load_pcbnew()
    mm = pcbnew.ToMM
    board = pcbnew.LoadBoard(args.board)
    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline, False)
    inner = unary_union(poly_set_to_shapely(pcbnew, outline)).buffer(-0.3)
    f_rules = unary_union([unary_union(poly_set_to_shapely(pcbnew, z.Outline())) for z in board.Zones()
                           if z.GetIsRuleArea() and z.IsOnLayer(pcbnew.F_Cu)] or [Point(0, 0).buffer(0)])
    copper = [(t.GetNetname(), item_shape(pcbnew, t, pcbnew.F_Cu)) for t in board.GetTracks() if t.IsOnLayer(pcbnew.F_Cu)]
    courts = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.IsOnLayer(pcbnew.F_Cu):
                copper.append((pad.GetNetname(), item_shape(pcbnew, pad, pcbnew.F_Cu)))
        courts[fp.GetReference()] = (fp.GetLayer(), mc.footprint_area(pcbnew, fp))

    results = {}
    for ref in args.refs:
        fp = board.FindFootprintByReference(ref)
        pads = list(fp.Pads())
        if len(pads) != 1:
            results[ref] = "not a single-pad part"
            continue
        pad = pads[0]
        net = pad.GetNetname()
        shape = item_shape(pcbnew, pad, pcbnew.F_Cu)
        px, py = mm(pad.GetPosition().x), mm(pad.GetPosition().y)
        others = unary_union([s for n, s in copper if n != net and not s.equals(shape)])
        anchors = []
        hard = None
        cands = []
        for t in board.GetTracks():
            if t.GetNetname() != net or t.GetClass() == "PCB_VIA" or not t.IsOnLayer(pcbnew.F_Cu):
                continue
            ax, ay, bx, by = mm(t.GetStart().x), mm(t.GetStart().y), mm(t.GetEnd().x), mm(t.GetEnd().y)
            n = max(1, int(math.hypot(bx - ax, by - ay) / args.step))
            cands += [(ax + (bx - ax) * i / n, ay + (by - ay) * i / n, "track") for i in range(n + 1)]
        cands.sort(key=lambda c: math.hypot(c[0] - px, c[1] - py))
        if args.near:
            # Also allow free spots near own-net pads of other parts; a router adds the short link.
            for ofp in board.GetFootprints():
                if ofp.GetReference() == ref:
                    continue
                for opad in ofp.Pads():
                    if opad.GetNetname() == net and opad.IsOnLayer(pcbnew.F_Cu):
                        anchors.append(item_shape(pcbnew, opad, pcbnew.F_Cu))
            hard = unary_union([s for n, s in copper if not s.equals(shape)])  # pads may not touch any copper
            if anchors:
                anchor = unary_union(anchors)
                ax0, ay0, ax1, ay1 = anchor.bounds
                grid = [(ax0 - args.near + i * 0.25, ay0 - args.near + j * 0.25)
                        for i in range(int((ax1 - ax0 + 2 * args.near) / 0.25) + 1)
                        for j in range(int((ay1 - ay0 + 2 * args.near) / 0.25) + 1)]
                grid = [g for g in grid if anchor.distance(Point(g)) <= args.near]
                grid.sort(key=lambda g: anchor.distance(Point(g)))
                cands += [(g[0], g[1], "near") for g in grid]
        side, court = courts[ref]
        placed = None
        for cx, cy, kind in cands:
            dx, dy = cx - px, cy - py
            s = affinity.translate(shape, dx, dy)
            c = affinity.translate(court, dx, dy)
            blocking = hard if kind == "near" else others
            if s.distance(blocking) < args.clearance or not inner.contains(c) or c.intersects(f_rules):
                continue
            if any(r != ref and sd == side and c.intersects(o) and c.intersection(o).area > 0
                   for r, (sd, o) in courts.items()):
                continue
            placed = (dx, dy)
            break
        if placed is None:
            results[ref] = f"no legal spot on {net} copper"
            continue
        fp.Move(pcbnew.VECTOR2I(pcbnew.FromMM(placed[0]), pcbnew.FromMM(placed[1])))
        courts[ref] = (side, affinity.translate(court, *placed))
        results[ref] = {"net": net, "moved_mm": [round(placed[0], 3), round(placed[1], 3)]}

    pcbnew.SaveBoard(args.out, board)
    Path(args.report).write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
