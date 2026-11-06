# SPDX-License-Identifier: MIT
"""Plan one open-net route through removable copper, then rip only crossed items.

The frozen board defines immutable copper.  Router-made tracks and vias absent
from that board are soft A* obstacles: the search may cross them at a fixed
penalty, while pads, frozen copper, holes, keep-outs and the edge remain hard.
This tool performs only the destructive half in a fresh process and records
the exact path and replacement obligations.  Run ``route_gaps.py`` on the
output in a second process, then reroute every disturbed net and validate with
native DRC plus ``check_routing_result.py``.
"""
import argparse
import heapq
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_routing_result as crr  # noqa: E402
import route_gaps as rg  # noqa: E402
from stitch_gnd_islands import item_shape, poly_set_to_shapely  # noqa: E402

PROTECTED = {"/CELL_NEG", "VBAT"}
GRID = 0.05
EDGE = 0.3
SAFETY = 0.025
HOLE_TO_HOLE = 0.25
VIA_D = 0.5
VIA_DRILL = 0.3


def removable_uuids(pcbnew, base, board):
    """Return UUIDs of candidate copper not geometrically covered by frozen copper."""
    _lost, new = crr.compare_copper(crr.copper_items(pcbnew, base),
                                    crr.copper_items(pcbnew, board))
    return {item[-1].m_Uuid.AsString() for _key, item in new}


class SoftBoard:
    def __init__(self, pcbnew, board, removable, layers):
        self.p, self.b, self.layers = pcbnew, board, layers
        self.lay = {name: board.GetLayerID(name) for name in layers}
        outline = pcbnew.SHAPE_POLY_SET()
        board.GetBoardPolygonOutlines(outline, False)
        self.area = unary_union(poly_set_to_shapely(pcbnew, outline))
        self.hard = {name: [] for name in layers}
        self.soft = {name: [] for name in layers}
        self.hard_holes, self.soft_holes = [], []
        self.objects, self.soft_items = {}, {}
        mm = pcbnew.ToMM
        for item in board.GetTracks():
            uid = item.m_Uuid.AsString()
            self.objects[uid] = item
            is_soft = uid in removable
            target = self.soft if is_soft else self.hard
            for name, layer in self.lay.items():
                if item.IsOnLayer(layer):
                    target[name].append((item.GetNetname(), item_shape(pcbnew, item, layer), uid))
            if is_soft:
                self.soft_items[uid] = item
            if item.GetClass() == "PCB_VIA":
                hole = Point(mm(item.GetPosition().x), mm(item.GetPosition().y)).buffer(
                    mm(item.GetDrillValue()) / 2)
                (self.soft_holes if is_soft else self.hard_holes).append((item.GetNetname(), hole, uid))
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                self.objects[pad.m_Uuid.AsString()] = pad
                for name, layer in self.lay.items():
                    if pad.IsOnLayer(layer):
                        self.hard[name].append((pad.GetNetname(), item_shape(pcbnew, pad, layer), None))
                if pad.HasHole():
                    hole = Point(mm(pad.GetPosition().x), mm(pad.GetPosition().y)).buffer(
                        mm(max(pad.GetDrillSize().x, pad.GetDrillSize().y)) / 2)
                    self.hard_holes.append((pad.GetNetname(), hole, None))
        self.track_keepout = {name: [] for name in layers}
        self.via_keepout = []
        for zone in board.Zones():
            self.objects[zone.m_Uuid.AsString()] = zone
            if not zone.GetIsRuleArea():
                continue
            shape = unary_union(poly_set_to_shapely(pcbnew, zone.Outline()))
            if zone.GetDoNotAllowVias():
                self.via_keepout.append(shape)
            if zone.GetDoNotAllowTracks():
                for name, layer in self.lay.items():
                    if zone.IsOnLayer(layer):
                        self.track_keepout[name].append(shape)

    def region(self, uuid, pos):
        obj = self.objects.get(uuid)
        if obj is None:
            return {}
        if obj.GetClass() == "ZONE":
            return {name: Point(pos).buffer(0.25) for name, layer in self.lay.items()
                    if obj.IsOnLayer(layer)}
        return {name: item_shape(self.p, obj, layer) for name, layer in self.lay.items()
                if obj.IsOnLayer(layer)}


def buffered(entries, own_net, own_clear, extra):
    groups = {}
    for net, shape, _uid in entries:
        if net != own_net:
            groups.setdefault(max(own_clear, rg.net_clearance(net)), []).append(shape)
    parts = [unary_union(shapes).buffer(clear + extra + SAFETY)
             for clear, shapes in groups.items()]
    return unary_union(parts) if parts else Point(0, 0).buffer(0)


def search(bd, net, start, goal, margin, via_cost, soft_cost, expansion_limit):
    width, clear = rg.POWER.get(net, rg.SIGNAL)
    all_shapes = list(start.values()) + list(goal.values())
    x0, y0, x1, y1 = unary_union(all_shapes).bounds
    xs = np.arange(x0 - margin, x1 + margin, GRID)
    ys = np.arange(y0 - margin, y1 + margin, GRID)
    gx, gy = np.meshgrid(xs, ys)
    inner = bd.area.buffer(-(EDGE + width / 2 + SAFETY))
    hard_holes = unary_union([s for n, s, _ in bd.hard_holes if n != net])
    if not hard_holes.is_empty:
        hard_holes = hard_holes.buffer(HOLE_TO_HOLE + width / 2 + SAFETY)
    free, soft = [], []
    for name in bd.layers:
        hard_block = buffered(bd.hard[name], net, clear, width / 2).union(hard_holes)
        if bd.track_keepout[name]:
            hard_block = hard_block.union(
                unary_union(bd.track_keepout[name]).buffer(width / 2 + SAFETY))
        free.append(shapely.contains_xy(inner, gx, gy)
                    & ~shapely.contains_xy(hard_block, gx, gy))
        soft_block = buffered(bd.soft[name], net, clear, width / 2)
        soft.append(shapely.intersects_xy(soft_block, gx, gy))

    via_hard = unary_union(
        [buffered(bd.hard[name], net, clear, VIA_D / 2) for name in bd.layers]
        + ([unary_union([s for _n, s, _ in bd.hard_holes]).buffer(
            HOLE_TO_HOLE + VIA_DRILL / 2 + SAFETY)] if bd.hard_holes else []))
    if bd.via_keepout:
        via_hard = via_hard.union(unary_union(bd.via_keepout).buffer(VIA_D / 2 + SAFETY))
    via_ok = (shapely.contains_xy(bd.area.buffer(-(EDGE + VIA_D / 2 + SAFETY)), gx, gy)
              & ~shapely.intersects_xy(via_hard, gx, gy))
    via_soft_shape = unary_union(
        [buffered(bd.soft[name], net, clear, VIA_D / 2) for name in bd.layers]
        + ([unary_union([s for _n, s, _ in bd.soft_holes]).buffer(
            HOLE_TO_HOLE + VIA_DRILL / 2 + SAFETY)] if bd.soft_holes else []))
    via_soft = shapely.intersects_xy(via_soft_shape, gx, gy)

    def cells(region):
        result = []
        for name, shape in region.items():
            li = bd.layers.index(name)
            core = shape.buffer(-0.02)
            mask = shapely.contains_xy(core if not core.is_empty else shape, gx, gy)
            result.extend((li, int(r), int(c)) for r, c in np.argwhere(mask))
        return result

    starts, goals = cells(start), set(cells(goal))
    if not starts or not goals:
        return None, {"stop_reason": "endpoint-not-on-grid", "expansions": 0}
    gr = sum(g[1] for g in goals) / len(goals)
    gc = sum(g[2] for g in goals) / len(goals)
    rows, cols = gx.shape
    steps = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1),
             (-1, -1, math.sqrt(2)), (-1, 1, math.sqrt(2)),
             (1, -1, math.sqrt(2)), (1, 1, math.sqrt(2))]
    dist, prev, heap = {}, {}, []
    for node in starts:
        dist[node] = 0.0
        heapq.heappush(heap, (math.hypot(node[1] - gr, node[2] - gc), 0.0, node))
    expanded = 0
    while heap:
        _score, d, node = heapq.heappop(heap)
        if d > dist.get(node, math.inf) + 1e-9:
            continue
        if node in goals:
            path = [node]
            while path[-1] in prev:
                path.append(prev[path[-1]])
            return (path[::-1], xs, ys), {"stop_reason": "path-found", "expansions": expanded}
        expanded += 1
        if expanded >= expansion_limit:
            return None, {"stop_reason": "expansion-limit", "expansions": expanded}
        li, row, col = node
        moves = []
        for dr, dc, step_cost in steps:
            nr, nc = row + dr, col + dc
            if 0 <= nr < rows and 0 <= nc < cols and free[li][nr, nc]:
                moves.append(((li, nr, nc), step_cost + (soft_cost if soft[li][nr, nc] else 0)))
        if via_ok[row, col]:
            for lj in range(len(bd.layers)):
                if lj != li:
                    moves.append(((lj, row, col),
                                  via_cost + (soft_cost if via_soft[row, col] else 0)))
        for nxt, cost in moves:
            nd = d + cost
            if nd < dist.get(nxt, math.inf):
                dist[nxt], prev[nxt] = nd, node
                h = math.hypot(nxt[1] - gr, nxt[2] - gc)
                heapq.heappush(heap, (nd + h, nd, nxt))
    return None, {"stop_reason": "search-space-exhausted", "expansions": expanded}


def proposed_shapes(bd, net, path, xs, ys):
    width, clear = rg.POWER.get(net, rg.SIGNAL)
    by_layer = {name: [] for name in bd.layers}
    vias = []
    for a, b in zip(path, path[1:]):
        ax, ay = float(xs[a[2]]), float(ys[a[1]])
        bx, by = float(xs[b[2]]), float(ys[b[1]])
        if a[0] == b[0]:
            by_layer[bd.layers[a[0]]].append(LineString([(ax, ay), (bx, by)]).buffer(width / 2))
        else:
            vias.append(Point(ax, ay).buffer(VIA_D / 2))
    return {name: unary_union(shapes) for name, shapes in by_layer.items() if shapes}, vias, clear


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True)
    ap.add_argument("--base-board", required=True)
    ap.add_argument("--drc", required=True)
    ap.add_argument("--net", required=True)
    ap.add_argument("--pair-index", type=int, default=0,
                    help="zero-based pair after sorting this net's opens shortest-first")
    ap.add_argument("--layers", nargs="+", default=["F.Cu", "In2.Cu", "In3.Cu", "B.Cu"])
    ap.add_argument("--margin", type=float, default=5.0)
    ap.add_argument("--via-cost", type=float, default=12.0)
    ap.add_argument("--soft-cost", type=float, default=80.0)
    ap.add_argument("--expansion-limit", type=int, default=3_000_000)
    ap.add_argument("--narrow-net", nargs="*", default=[],
                    help="plan these approved supply nets at signal width, retaining class clearance")
    ap.add_argument("--net-width", nargs=2, action="append", default=[], metavar=("NET", "MM"),
                    help="explicit per-net width matching the subsequent route_gaps invocation")
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()
    for net in args.narrow_net:
        if net in rg.POWER:
            rg.POWER[net] = (rg.SIGNAL[0], rg.POWER[net][1])
    for net, width in args.net_width:
        rg.POWER[net] = (float(width), rg.net_clearance(net))
    started = time.monotonic()
    pcbnew, _handle = crr.load_pcbnew()
    base = pcbnew.LoadBoard(args.base_board)
    board = pcbnew.LoadBoard(args.board)
    removable = removable_uuids(pcbnew, base, board)
    bd = SoftBoard(pcbnew, board, removable, args.layers)
    drc = json.loads(Path(args.drc).read_text(encoding="utf-8"))
    pairs = []
    for item in drc.get("unconnected_items", []):
        a, b = item["items"][:2]
        if crr.drc_net(a["description"]) == args.net:
            distance = math.hypot(a["pos"]["x"] - b["pos"]["x"],
                                  a["pos"]["y"] - b["pos"]["y"])
            pairs.append((distance, a, b))
    pairs.sort(key=lambda row: (row[0], row[1]["description"], row[2]["description"]))
    if args.pair_index >= len(pairs):
        raise SystemExit(f"net {args.net!r} has only {len(pairs)} open pair(s)")
    distance, a, b = pairs[args.pair_index]
    start = bd.region(a["uuid"], (a["pos"]["x"], a["pos"]["y"]))
    goal = bd.region(b["uuid"], (b["pos"]["x"], b["pos"]["y"]))
    found, stats = search(bd, args.net, start, goal, args.margin, args.via_cost,
                          args.soft_cost, args.expansion_limit)
    report = {
        "net": args.net, "pair_index": args.pair_index,
        "endpoints": [a["description"], b["description"]],
        "endpoint_uuids": [a["uuid"], b["uuid"]],
        "distance_mm": round(distance, 4), "layers": args.layers,
        "margin_mm": args.margin, "soft_cost": args.soft_cost,
        **stats,
    }
    if found is None:
        report["elapsed_s"] = round(time.monotonic() - started, 3)
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 2
    path, xs, ys = found
    route_shapes, via_shapes, own_clear = proposed_shapes(bd, args.net, path, xs, ys)
    crossed = []
    for uid, obj in bd.soft_items.items():
        net = obj.GetNetname()
        if net == args.net or net in PROTECTED or net.startswith("/PROT"):
            continue
        clearance = max(own_clear, rg.net_clearance(net)) + SAFETY
        hit = False
        for name, route_shape in route_shapes.items():
            if obj.IsOnLayer(bd.lay[name]):
                hit |= route_shape.buffer(clearance).intersects(
                    item_shape(pcbnew, obj, bd.lay[name]))
        if via_shapes:
            hit |= any(v.buffer(clearance).intersects(
                item_shape(pcbnew, obj, pcbnew.F_Cu if obj.GetClass() == "PCB_VIA"
                           else obj.GetLayer())) for v in via_shapes)
        if hit:
            crossed.append((uid, obj))
    obligations = []
    for uid, obj in crossed:
        pos = obj.GetPosition()
        obligations.append({
            "uuid": uid, "net": obj.GetNetname(), "kind": obj.GetClass(),
            "position_mm": [round(pcbnew.ToMM(pos.x), 4), round(pcbnew.ToMM(pos.y), 4)],
        })
    # Removal is deliberately last: pcbnew SWIG wrappers become unreliable afterwards.
    for _uid, obj in crossed:
        board.Remove(obj)
    pcbnew.SaveBoard(args.out, board)
    report.update({
        "path_nodes": len(path),
        "path_layer_changes": sum(a[0] != b[0] for a, b in zip(path, path[1:])),
        "replacement_obligations": obligations,
        "removed_by_net": dict(sorted(__import__("collections").Counter(
            row["net"] for row in obligations).items())),
        "elapsed_s": round(time.monotonic() - started, 3),
        "output": str(Path(args.out).resolve()),
    })
    Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
