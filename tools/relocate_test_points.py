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
import route_gaps as rg  # noqa: E402
from stitch_gnd_islands import item_shape, poly_set_to_shapely  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True)
    ap.add_argument("--refs", nargs="+", required=True)
    ap.add_argument("--clearance", type=float, default=0.2)
    ap.add_argument("--step", type=float, default=0.1)
    ap.add_argument("--near", type=float, default=0.0,
                    help="if >0, also try free spots within this distance (mm) of own-net pads of other parts")
    ap.add_argument("--near-step", type=float, default=0.25,
                    help="grid step for --near candidates (mm)")
    ap.add_argument("--path-aware-drc",
                    help="accept a free position only when route_gaps finds a path to its reported endpoint")
    ap.add_argument("--allow-back", action="store_true",
                    help="also search B.Cu positions outside every B-side rule area")
    ap.add_argument("--layers", nargs="+", default=["F.Cu", "In2.Cu", "In3.Cu", "B.Cu"])
    ap.add_argument("--margin", type=float, default=4.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    pcbnew, _h = crr.load_pcbnew()
    mm = pcbnew.ToMM
    board = pcbnew.LoadBoard(args.board)
    route_board = None
    drc_pairs = {}
    if args.path_aware_drc:
        rg.LAYERS[:] = args.layers
        rg.MARGIN = args.margin
        route_board = rg.Board(pcbnew, board)
        drc = json.loads(Path(args.path_aware_drc).read_text(encoding="utf-8"))
        for violation in drc.get("unconnected_items", []):
            a, b = violation["items"][:2]
            drc_pairs[a["uuid"]] = b
            drc_pairs[b["uuid"]] = a
    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline, False)
    inner = unary_union(poly_set_to_shapely(pcbnew, outline)).buffer(-0.3)
    f_rules = unary_union([unary_union(poly_set_to_shapely(pcbnew, z.Outline())) for z in board.Zones()
                           if z.GetIsRuleArea() and z.IsOnLayer(pcbnew.F_Cu)] or [Point(0, 0).buffer(0)])
    b_rules = unary_union([unary_union(poly_set_to_shapely(pcbnew, z.Outline())) for z in board.Zones()
                           if z.GetIsRuleArea() and z.IsOnLayer(pcbnew.B_Cu)] or [Point(0, 0).buffer(0)])
    copper = [(t.GetNetname(), item_shape(pcbnew, t, pcbnew.F_Cu)) for t in board.GetTracks() if t.IsOnLayer(pcbnew.F_Cu)]
    b_copper = [(t.GetNetname(), item_shape(pcbnew, t, pcbnew.B_Cu))
                for t in board.GetTracks() if t.IsOnLayer(pcbnew.B_Cu)]
    courts = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.IsOnLayer(pcbnew.F_Cu):
                copper.append((pad.GetNetname(), item_shape(pcbnew, pad, pcbnew.F_Cu)))
            if pad.IsOnLayer(pcbnew.B_Cu):
                b_copper.append((pad.GetNetname(), item_shape(pcbnew, pad, pcbnew.B_Cu)))
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
                grid = [(ax0 - args.near + i * args.near_step,
                         ay0 - args.near + j * args.near_step)
                        for i in range(int((ax1 - ax0 + 2 * args.near) / args.near_step) + 1)
                        for j in range(int((ay1 - ay0 + 2 * args.near) / args.near_step) + 1)]
                grid = [g for g in grid if anchor.distance(Point(g)) <= args.near]
                grid.sort(key=lambda g: anchor.distance(Point(g)))
                cands += [(g[0], g[1], "near") for g in grid]
        side, court = courts[ref]
        placed = None
        placed_side = "F.Cu"
        path_nodes = None
        tested = 0
        legal = []
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
            legal.append((dx, dy, s, c))
            if route_board is None:
                placed = (dx, dy)
                break
        if route_board is not None and legal:
            tested = len(legal)
            other = drc_pairs.get(pad.m_Uuid.AsString())
            start = route_board.region(other["uuid"], (other["pos"]["x"], other["pos"]["y"])) if other else {}
            found = rg.route_pair(route_board, net, start,
                                  {"F.Cu": unary_union([row[2] for row in legal])}) if start else None
            if found is not None:
                path, xs, ys = found
                _layer, row, col = path[-1]
                endpoint = Point(float(xs[col]), float(ys[row]))
                choice = min(legal, key=lambda item: item[2].distance(endpoint))
                placed = choice[:2]
                path_nodes = len(path)
        if placed is None and route_board is not None and args.allow_back:
            back_block = unary_union([s for _n, s in b_copper])
            back_legal = []
            for cx, cy, _kind in cands:
                dx, dy = cx - px, cy - py
                s = affinity.translate(shape, dx, dy)
                c = affinity.translate(court, dx, dy)
                if (s.distance(back_block) < args.clearance or not inner.contains(c)
                        or c.intersects(b_rules)):
                    continue
                if any(r != ref and sd == pcbnew.B_Cu and c.intersects(o)
                       and c.intersection(o).area > 0 for r, (sd, o) in courts.items()):
                    continue
                back_legal.append((dx, dy, s, c))
            tested += len(back_legal)
            other = drc_pairs.get(pad.m_Uuid.AsString())
            start = route_board.region(other["uuid"], (other["pos"]["x"], other["pos"]["y"])) if other else {}
            found = rg.route_pair(route_board, net, start,
                                  {"B.Cu": unary_union([row[2] for row in back_legal])}
                                  ) if start and back_legal else None
            if found is not None:
                path, xs, ys = found
                _layer, row, col = path[-1]
                endpoint = Point(float(xs[col]), float(ys[row]))
                choice = min(back_legal, key=lambda item: item[2].distance(endpoint))
                placed = choice[:2]
                placed_side = "B.Cu"
                path_nodes = len(path)
        if placed is None:
            results[ref] = {
                "net": net,
                "status": "no path from legal relocation candidates",
                "path_candidates_tested": tested,
                "searched_sides": ["F.Cu", "B.Cu"] if args.allow_back else ["F.Cu"],
                "radius_mm": args.near,
            }
            continue
        if placed_side == "B.Cu":
            fp.Flip(fp.GetPosition(), False)
            side = pcbnew.B_Cu
        fp.Move(pcbnew.VECTOR2I(pcbnew.FromMM(placed[0]), pcbnew.FromMM(placed[1])))
        courts[ref] = (side, affinity.translate(court, *placed))
        results[ref] = {"net": net, "moved_mm": [round(placed[0], 3), round(placed[1], 3)],
                        "side": placed_side, "path_candidates_tested": tested,
                        "path_nodes": path_nodes}

    pcbnew.SaveBoard(args.out, board)
    Path(args.report).write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
