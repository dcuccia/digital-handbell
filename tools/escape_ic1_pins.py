# SPDX-License-Identifier: MIT
"""Add clearance-checked F.Cu escape stubs and vias for blocked pins of one part.

For each requested pad: grid A* on F.Cu from the pad centre to the nearest
legal through-via site, avoiding other-net copper, track/via keep-outs and the
board edge. Existing copper and parts are never changed. An external router is
expected to continue from the new vias; every result must pass DRC and the
standard check (dangling-stub warnings aside).
"""
import argparse
import heapq
import json
import math
import sys
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_routing_result as crr  # noqa: E402
from stitch_gnd_islands import item_shape, poly_set_to_shapely  # noqa: E402

TRACK = 0.15
CLEAR = 0.15
VIA_D, VIA_DRILL = 0.5, 0.3
HOLE_TO_HOLE = 0.25
EDGE = 0.3
GRID = 0.025
WINDOW = 9.0  # mm search radius around the part centre


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True)
    ap.add_argument("--ref", default="IC1")
    ap.add_argument("--pads", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--body-halfsize", type=float, default=3.2,
                    help="square no-go half-size around the part centre (keeps stubs out from under the body)")
    args = ap.parse_args()

    pcbnew, _h = crr.load_pcbnew()
    board = pcbnew.LoadBoard(args.board)
    mm = pcbnew.ToMM
    lay = {"F.Cu": pcbnew.F_Cu, "In2.Cu": pcbnew.In2_Cu, "B.Cu": pcbnew.B_Cu}
    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline, False)
    board_area = unary_union(poly_set_to_shapely(pcbnew, outline))

    # Per-layer copper shapes grouped by net; holes; keep-outs.
    copper = {name: [] for name in lay}
    holes = []
    for item in board.GetTracks():
        for name, layer in lay.items():
            if item.IsOnLayer(layer):
                copper[name].append((item.GetNetname(), item_shape(pcbnew, item, layer)))
        if item.GetClass() == "PCB_VIA":
            holes.append(Point(mm(item.GetPosition().x), mm(item.GetPosition().y)).buffer(mm(item.GetDrillValue()) / 2))
    pads = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            pads[(fp.GetReference(), pad.GetNumber())] = pad
            for name, layer in lay.items():
                if pad.IsOnLayer(layer):
                    copper[name].append((pad.GetNetname(), item_shape(pcbnew, pad, layer)))
            if pad.HasHole():
                holes.append(Point(mm(pad.GetPosition().x), mm(pad.GetPosition().y)).buffer(
                    mm(max(pad.GetDrillSize().x, pad.GetDrillSize().y)) / 2))
    track_keepout_f, via_keepout = [], []
    for zone in board.Zones():
        if not zone.GetIsRuleArea():
            continue
        shape = unary_union(poly_set_to_shapely(pcbnew, zone.Outline()))
        if zone.GetDoNotAllowVias():
            via_keepout.append(shape)
        if zone.GetDoNotAllowTracks() and zone.IsOnLayer(pcbnew.F_Cu):
            track_keepout_f.append(shape)
    holes_u = unary_union(holes)
    via_keepout_u = unary_union(via_keepout) if via_keepout else None

    centre = board.FindFootprintByReference(args.ref).GetPosition()
    cx, cy = mm(centre.x), mm(centre.y)
    xs = np.arange(cx - WINDOW, cx + WINDOW, GRID)
    ys = np.arange(cy - WINDOW, cy + WINDOW, GRID)
    gx, gy = np.meshgrid(xs, ys)
    added, failed = [], []
    new_shapes = {name: [] for name in lay}

    for pad_no in args.pads:
        pad = pads[(args.ref, pad_no)]
        net = pad.GetNetname()

        def others(name):
            return [s for n, s in copper[name] + new_shapes[name] if n != net]

        f_block = unary_union(others("F.Cu")).buffer(CLEAR + TRACK / 2)
        if args.body_halfsize > 0:
            f_block = f_block.union(Point(cx, cy).buffer(args.body_halfsize, cap_style=3))
        if track_keepout_f:
            f_block = f_block.union(unary_union(track_keepout_f).buffer(TRACK / 2))
        f_block = f_block.union(board_area.exterior.buffer(EDGE + TRACK / 2)) if hasattr(board_area, "exterior") else f_block
        via_bad = unary_union([unary_union(others(n)).buffer(CLEAR + VIA_D / 2) for n in lay]
                              + [holes_u.buffer(HOLE_TO_HOLE + VIA_DRILL / 2)])
        if via_keepout_u is not None:
            via_bad = via_bad.union(via_keepout_u.buffer(VIA_D / 2))
        via_ok_area = board_area.buffer(-(EDGE + VIA_D / 2)).difference(via_bad)

        free = ~shapely.contains_xy(f_block, gx, gy)
        goal = shapely.contains_xy(via_ok_area, gx, gy) & free
        px, py = mm(pad.GetPosition().x), mm(pad.GetPosition().y)
        start = (int(round((py - ys[0]) / GRID)), int(round((px - xs[0]) / GRID)))
        # The pad centre itself sits inside neighbour-pad clearance bands only if pitch is tiny; allow it.
        free[start] = True
        path = astar(free, goal, start)
        if path is None:
            reach = flood(free, start)
            failed.append({"pad": pad_no, "net": net, "reason": "no legal F.Cu path to a via site",
                           "reachable_cells": reach, "goal_cells_in_window": int(goal.sum())})
            continue
        points = simplify([(float(xs[c]), float(ys[r])) for r, c in path])
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x0), pcbnew.FromMM(y0)))
            t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
            t.SetWidth(pcbnew.FromMM(TRACK))
            t.SetLayer(pcbnew.F_Cu)
            t.SetNet(board.FindNet(net))
            board.Add(t)
        vx, vy = points[-1]
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(vx), pcbnew.FromMM(vy)))
        v.SetWidth(pcbnew.FromMM(VIA_D))
        v.SetDrill(pcbnew.FromMM(VIA_DRILL))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(board.FindNet(net))
        board.Add(v)
        stub = LineString(points).buffer(TRACK / 2) if len(points) > 1 else Point(points[0]).buffer(TRACK / 2)
        new_shapes["F.Cu"].append((net, stub.union(Point(vx, vy).buffer(VIA_D / 2))))
        for name in ("In2.Cu", "B.Cu"):
            new_shapes[name].append((net, Point(vx, vy).buffer(VIA_D / 2)))
        holes_u = holes_u.union(Point(vx, vy).buffer(VIA_DRILL / 2))
        length = sum(math.dist(a, b) for a, b in zip(points, points[1:]))
        added.append({"pad": pad_no, "net": net, "via": [round(vx, 4), round(vy, 4)],
                      "stub_mm": round(length, 3), "segments": len(points) - 1})

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(args.out, board)
    report = {"ref": args.ref, "added": added, "failed": failed,
              "rules": {"track": TRACK, "clearance": CLEAR, "via": [VIA_D, VIA_DRILL]}}
    Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


def flood(free, start):
    seen, stack = {start}, [start]
    rows, cols = free.shape
    while stack and len(seen) < 200000:
        r, c = stack.pop()
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nr < rows and 0 <= nc < cols and free[nr, nc] and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))
    return len(seen)


def astar(free, goal, start):
    rows, cols = free.shape
    if not free[start]:
        return None
    goal_idx = np.argwhere(goal)
    if len(goal_idx) == 0:
        return None
    steps = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1),
             (-1, -1, math.sqrt(2)), (-1, 1, math.sqrt(2)), (1, -1, math.sqrt(2)), (1, 1, math.sqrt(2))]
    dist = {start: 0.0}
    prev = {}
    heap = [(0.0, start, None)]
    while heap:
        d, node, last = heapq.heappop(heap)
        if d > dist.get(node, math.inf) + 1e-9:
            continue
        if goal[node]:
            path = [node]
            while path[-1] in prev:
                path.append(prev[path[-1]])
            return path[::-1]
        r, c = node
        for dr, dc, cost in steps:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and free[nr, nc]:
                turn = 0.3 if last is not None and (dr, dc) != last else 0.0
                nd = d + cost + turn
                if nd < dist.get((nr, nc), math.inf):
                    dist[(nr, nc)] = nd
                    prev[(nr, nc)] = node
                    heapq.heappush(heap, (nd, (nr, nc), (dr, dc)))
    return None


def simplify(points):
    out = [points[0]]
    for i in range(1, len(points) - 1):
        ax, ay = out[-1]
        bx, by = points[i]
        cx, cy = points[i + 1]
        if abs((bx - ax) * (cy - by) - (by - ay) * (cx - bx)) > 1e-9:
            out.append(points[i])
    out.append(points[-1])
    return out


if __name__ == "__main__":
    main()
