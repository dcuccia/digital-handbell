# SPDX-License-Identifier: MIT
"""Route remaining unconnected pairs with a clearance-aware multi-layer grid A*.

For each unconnected pair in a KiCad DRC report, search F.Cu/In2.Cu/B.Cu
(never In1, the protected GND plane) between the two copper items, avoiding
other-net copper, keep-out rule areas, holes and the board edge, with
optional through-via transitions. Existing copper is never modified; every
result must still pass DRC and the standard check. Intended for short tails.
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

LAYERS = ["F.Cu", "In2.Cu", "B.Cu"]  # overridden by --layers
GRID = 0.05
VIA_D, VIA_DRILL = 0.5, 0.3
HOLE_TO_HOLE = 0.25
EDGE = 0.3
MARGIN = 4.0
VIA_COST = 12.0
POWER = {"VBAT": (0.8, 0.2), "VHI": (0.8, 0.2), "V+": (0.8, 0.2), "VBUS": (0.5, 0.2), "VAMP": (0.5, 0.2),
         "+3V3": (0.25, 0.15), "VCORE": (0.25, 0.15)}  # approved Gate A widths (track, clearance)
SIGNAL = (0.15, 0.15)
SKIP_NETS = {"/CELL_NEG"}
SAFETY = 0.025  # grid/polygon discretization margin added to every clearance


def net_clearance(net):
    return POWER.get(net, SIGNAL)[1]


def blocked(entries, own_net, own_clear, extra):
    """Union of other-net shapes buffered by the stricter of both clearances (+extra)."""
    groups = {}
    for n, s in entries:
        if n != own_net:
            groups.setdefault(max(own_clear, net_clearance(n)), []).append(s)
    parts = [unary_union(shapes).buffer(c + extra + SAFETY) for c, shapes in groups.items()]
    return unary_union(parts) if parts else Point(0, 0).buffer(0)


class Board:
    def __init__(self, pcbnew, board):
        self.p, self.b = pcbnew, board
        mm = pcbnew.ToMM
        self.lay = {name: board.GetLayerID(name) for name in LAYERS}
        outline = pcbnew.SHAPE_POLY_SET()
        board.GetBoardPolygonOutlines(outline, False)
        self.area = unary_union(poly_set_to_shapely(pcbnew, outline))
        self.copper = {n: [] for n in LAYERS}
        self.holes = []
        self.objects = {}
        for item in board.GetTracks():
            self.objects[item.m_Uuid.AsString()] = item
            for name, layer in self.lay.items():
                if item.IsOnLayer(layer):
                    self.copper[name].append((item.GetNetname(), item_shape(pcbnew, item, layer)))
            if item.GetClass() == "PCB_VIA":
                self.holes.append((item.GetNetname(), Point(mm(item.GetPosition().x), mm(item.GetPosition().y)).buffer(
                    mm(item.GetDrillValue()) / 2)))
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                self.objects[pad.m_Uuid.AsString()] = pad
                for name, layer in self.lay.items():
                    if pad.IsOnLayer(layer):
                        self.copper[name].append((pad.GetNetname(), item_shape(pcbnew, pad, layer)))
                if pad.HasHole():
                    self.holes.append((pad.GetNetname(), Point(mm(pad.GetPosition().x), mm(pad.GetPosition().y)).buffer(
                        mm(max(pad.GetDrillSize().x, pad.GetDrillSize().y)) / 2)))
        self.track_keepout = {n: [] for n in LAYERS}
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
        """Copper of one DRC item as {layer: shape}; zones use a small disk at the reported point."""
        p, mm = self.p, self.p.ToMM
        obj = self.objects.get(uuid)
        if obj is None:
            return {}
        out = {}
        if obj.GetClass() == "ZONE":
            disk = Point(pos).buffer(0.25)
            for name, layer in self.lay.items():
                if obj.IsOnLayer(layer):
                    out[name] = disk
            return out
        for name, layer in self.lay.items():
            if obj.IsOnLayer(layer):
                out[name] = item_shape(p, obj, layer)
        return out


def route_pair(bd, net, start, goal):
    width, clear = POWER.get(net, SIGNAL)
    shapes = [s for n in LAYERS for s in list(start.values()) + list(goal.values())]
    x0, y0, x1, y1 = unary_union(shapes).bounds
    x0, y0, x1, y1 = x0 - MARGIN, y0 - MARGIN, x1 + MARGIN, y1 + MARGIN
    xs = np.arange(x0, x1, GRID)
    ys = np.arange(y0, y1, GRID)
    gx, gy = np.meshgrid(xs, ys)
    inner = bd.area.buffer(-(EDGE + width / 2 + SAFETY))
    hole_block = unary_union([s for n, s in bd.holes if n != net]).buffer(HOLE_TO_HOLE + width / 2 + SAFETY)
    free = []
    for name in LAYERS:
        block = blocked(bd.copper[name], net, clear, width / 2).union(hole_block)
        if bd.track_keepout[name]:
            block = block.union(unary_union(bd.track_keepout[name]).buffer(width / 2 + SAFETY))
        f = shapely.contains_xy(inner, gx, gy) & ~shapely.contains_xy(block, gx, gy)
        free.append(f)
    via_block = unary_union([blocked(bd.copper[name], net, clear, VIA_D / 2) for name in LAYERS]
                            + [unary_union([s for _n, s in bd.holes]).buffer(HOLE_TO_HOLE + VIA_DRILL / 2 + SAFETY)])
    if bd.via_keepout:
        via_block = via_block.union(unary_union(bd.via_keepout).buffer(VIA_D / 2 + SAFETY))
    via_ok = shapely.contains_xy(bd.area.buffer(-(EDGE + VIA_D / 2 + SAFETY)), gx, gy) & ~shapely.contains_xy(via_block, gx, gy)
    for f in free:
        via_ok &= f

    def cells(region):
        out = []
        for name, shape in region.items():
            li = LAYERS.index(name)
            core = shape.buffer(-0.02)
            if core.is_empty:
                core = shape
            mask = shapely.contains_xy(core, gx, gy)
            for r, c in np.argwhere(mask):
                out.append((li, r, c))
        return out

    starts, goals = cells(start), set(cells(goal))
    if not starts or not goals:
        return None
    gr = np.array([g[1] for g in goals]).mean()
    gc = np.array([g[2] for g in goals]).mean()
    rows, cols = gx.shape
    steps = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1),
             (-1, -1, math.sqrt(2)), (-1, 1, math.sqrt(2)), (1, -1, math.sqrt(2)), (1, 1, math.sqrt(2))]
    dist, prev, heap = {}, {}, []
    for s in starts:
        dist[s] = 0.0
        heapq.heappush(heap, (math.hypot(s[1] - gr, s[2] - gc), 0.0, s))
    expanded = 0
    while heap:
        _, d, node = heapq.heappop(heap)
        if d > dist.get(node, math.inf) + 1e-9:
            continue
        if node in goals:
            path = [node]
            while path[-1] in prev:
                path.append(prev[path[-1]])
            return path[::-1], xs, ys
        expanded += 1
        if expanded > 3_000_000:
            return None
        li, r, c = node
        moves = []
        for dr, dc, cost in steps:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                inside_start = (li, nr, nc) in goals or (li, nr, nc) in dist and dist[(li, nr, nc)] == 0.0
                if free[li][nr, nc] or inside_start:
                    moves.append(((li, nr, nc), cost))
        if via_ok[r, c]:
            for lj in range(len(LAYERS)):
                if lj != li:
                    moves.append(((lj, r, c), VIA_COST))
        for nxt, cost in moves:
            nd = d + cost
            if nd < dist.get(nxt, math.inf):
                dist[nxt] = nd
                prev[nxt] = node
                heapq.heappush(heap, (nd + math.hypot(nxt[1] - gr, nxt[2] - gc), nd, nxt))
    return None


def add_path(bd, net, path, xs, ys):
    p = bd.p
    width, _ = POWER.get(net, SIGNAL)
    netobj = bd.b.FindNet(net)
    added = 0
    run = [path[0]]

    def flush(run):
        nonlocal added
        pts = simplify([(float(xs[c]), float(ys[r])) for _, r, c in run])
        layer = LAYERS[run[0][0]]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            if math.hypot(bx - ax, by - ay) < 1e-6:
                continue
            t = p.PCB_TRACK(bd.b)
            t.SetStart(p.VECTOR2I(p.FromMM(ax), p.FromMM(ay)))
            t.SetEnd(p.VECTOR2I(p.FromMM(bx), p.FromMM(by)))
            t.SetWidth(p.FromMM(width))
            t.SetLayer(bd.lay[layer])
            t.SetNet(netobj)
            bd.b.Add(t)
            bd.copper[layer].append((net, LineString([(ax, ay), (bx, by)]).buffer(width / 2)))
            added += 1

    for node in path[1:]:
        if node[0] != run[-1][0]:
            flush(run)
            x, y = float(xs[node[2]]), float(ys[node[1]])
            v = p.PCB_VIA(bd.b)
            v.SetPosition(p.VECTOR2I(p.FromMM(x), p.FromMM(y)))
            v.SetWidth(p.FromMM(VIA_D))
            v.SetDrill(p.FromMM(VIA_DRILL))
            v.SetLayerPair(p.F_Cu, p.B_Cu)
            v.SetNet(netobj)
            bd.b.Add(v)
            for name in LAYERS:
                bd.copper[name].append((net, Point(x, y).buffer(VIA_D / 2)))
            bd.holes.append((net, Point(x, y).buffer(VIA_DRILL / 2)))
            added += 1
            run = [node]
        else:
            run.append(node)
    if len(run) > 1:
        flush(run)
    return added


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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True)
    ap.add_argument("--drc", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--skip-net", nargs="*", default=[])
    ap.add_argument("--only-net", nargs="*", default=[], help="route only these nets")
    ap.add_argument("--layers", nargs="+", default=["F.Cu", "In2.Cu", "B.Cu"],
                    help="signal layers the router may use (never plane layers)")
    ap.add_argument("--via-cost", type=float, default=12.0)
    ap.add_argument("--margin", type=float, default=4.0, help="search window margin around each pair (mm)")
    ap.add_argument("--narrow-net", nargs="*", default=[], help="route these supply nets at signal width")
    ap.add_argument("--net-width", nargs=2, action="append", default=[], metavar=("NET", "MM"),
                    help="explicit per-net track width; clearance remains the established net clearance")
    ap.add_argument("--nearest-own-copper", action="store_true",
                    help="replace each reported goal with nearest copper outside the start's own-net group")
    args = ap.parse_args()
    global VIA_COST, MARGIN
    LAYERS[:] = args.layers
    VIA_COST = args.via_cost
    MARGIN = args.margin
    for net in args.narrow_net:  # narrower track only; the net class clearance still applies
        if net in POWER:
            POWER[net] = (SIGNAL[0], POWER[net][1])
    for net, width in args.net_width:
        POWER[net] = (float(width), net_clearance(net))

    pcbnew, _h = crr.load_pcbnew()
    board = pcbnew.LoadBoard(args.board)
    bd = Board(pcbnew, board)
    report = json.loads(Path(args.drc).read_text(encoding="utf-8"))
    pairs = []
    for u in report.get("unconnected_items", []):
        a, b = u["items"][0], u["items"][1]
        net = crr.drc_net(a["description"])
        if not net or net in SKIP_NETS or net in args.skip_net or (args.only_net and net not in args.only_net):
            continue
        d = math.hypot(a["pos"]["x"] - b["pos"]["x"], a["pos"]["y"] - b["pos"]["y"])
        pairs.append((d, net, a, b))
    pairs.sort(key=lambda t: t[0])
    results = []
    for d, net, a, b in pairs:
        start = bd.region(a["uuid"], (a["pos"]["x"], a["pos"]["y"]))
        goal = bd.region(b["uuid"], (b["pos"]["x"], b["pos"]["y"]))
        if not start or not goal:
            results.append({"net": net, "status": "unresolved item"})
            continue
        if args.nearest_own_copper:
            nearest = {}
            for name in LAYERS:
                reached = start.get(name, Point(0, 0).buffer(0))
                own = [shape for own_net, shape in bd.copper[name] if own_net == net]
                members, changed = set(), True
                while changed:
                    changed = False
                    for index, shape in enumerate(own):
                        if index not in members and shape.intersects(reached):
                            members.add(index)
                            reached = reached.union(shape)
                            changed = True
                outside = [shape for index, shape in enumerate(own) if index not in members]
                if outside:
                    nearest[name] = unary_union(outside)
            goal = nearest
            if not goal:
                results.append({"net": net, "distance_mm": round(d, 2),
                                "status": "no outside own-net copper"})
                continue
        found = route_pair(bd, net, start, goal)
        if found is None:
            results.append({"net": net, "distance_mm": round(d, 2), "status": "no path"})
            continue
        path, xs, ys = found
        n = add_path(bd, net, path, xs, ys)
        results.append({"net": net, "distance_mm": round(d, 2), "status": "routed", "items": n})
        print(json.dumps(results[-1]), flush=True)
    pcbnew.SaveBoard(args.out, board)
    summary = {"routed": sum(r["status"] == "routed" for r in results), "pairs": len(results), "results": results}
    Path(args.report).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "results"}))


if __name__ == "__main__":
    main()
