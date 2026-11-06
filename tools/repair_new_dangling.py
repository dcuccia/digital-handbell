# SPDX-License-Identifier: MIT
"""Reconnect newly dangling base tracks/vias without removing preserved copper.

The candidate and baseline DRC reports select only newly reported dangling
items.  For a track, the less-connected endpoint is routed back to nearest
same-net copper on that layer.  For a via, the signal layer with the nearest
same-net copper not already touching the via is selected.  The established
clearance-aware ``route_gaps`` A* supplies the repair; native DRC remains
authoritative.
"""
import argparse
import json
import sys
from pathlib import Path

from shapely.geometry import Point
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_routing_result as crr  # noqa: E402
import clean_drc_conflicts as cdc  # noqa: E402
import route_gaps as rg  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True)
    ap.add_argument("--drc", required=True)
    ap.add_argument("--baseline-drc", required=True)
    ap.add_argument("--only-net", nargs="*", default=[])
    ap.add_argument("--layers", nargs="+", default=["F.Cu", "In2.Cu", "In3.Cu", "B.Cu"])
    ap.add_argument("--margin", type=float, default=4.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    current = cdc.violation_items(json.loads(Path(args.drc).read_text(encoding="utf-8")))
    baseline = cdc.violation_items(json.loads(Path(args.baseline_drc).read_text(encoding="utf-8")))
    old = {(t, kind, net, x, y) for t, _u, kind, net, x, y in baseline}
    fresh = [(t, uid, kind, net, x, y) for t, uid, kind, net, x, y in current
             if t in {"track_dangling", "via_dangling"}
             and (t, kind, net, x, y) not in old
             and (not args.only_net or net in args.only_net)]

    pcbnew, _handle = crr.load_pcbnew()
    board = pcbnew.LoadBoard(args.board)
    rg.LAYERS[:] = args.layers
    rg.MARGIN = args.margin
    bd = rg.Board(pcbnew, board)
    objects = {item.m_Uuid.AsString(): item for item in board.GetTracks()}
    mm = pcbnew.ToMM
    results = []
    for violation, uid, kind, net, _x, _y in fresh:
        obj = objects.get(uid)
        if obj is None:
            results.append({"net": net, "uuid": uid, "status": "item-not-found"})
            continue
        candidates = []
        if kind == "track":
            layer = obj.GetLayerName()
            for endpoint in (obj.GetStart(), obj.GetEnd()):
                point = Point(mm(endpoint.x), mm(endpoint.y))
                touching = sum(shape.distance(point) < 0.002 for own, shape in bd.copper[layer]
                               if own == net)
                candidates.append((touching, layer, point))
        else:
            point = Point(mm(obj.GetPosition().x), mm(obj.GetPosition().y))
            for layer in args.layers:
                # Board.copper includes the via annulus itself on every layer.
                # A layer with another touching shape is already connected and
                # cannot cure a one-layer-only dangling via.
                touching = sum(shape.distance(point) < 0.002 for own, shape in bd.copper[layer]
                               if own == net)
                if touching > 1:
                    continue
                goals = [shape for own, shape in bd.copper[layer]
                         if own == net and shape.distance(point) >= 0.002]
                if goals:
                    candidates.append((min(shape.distance(point) for shape in goals), layer, point))
        candidates.sort(key=lambda row: row[0])
        found = None
        selected = None
        for _rank, layer, point in candidates:
            goals = [shape for own, shape in bd.copper[layer]
                     if own == net and shape.distance(point) >= 0.002]
            if not goals:
                continue
            start = {layer: point.buffer(max(0.08, rg.POWER.get(net, rg.SIGNAL)[0] / 2))}
            goal = {layer: unary_union(goals)}
            found = rg.route_pair(bd, net, start, goal)
            if found is not None:
                selected = (layer, point)
                break
        if found is None:
            results.append({"net": net, "uuid": uid, "status": "no-path"})
            continue
        path, xs, ys = found
        count = rg.add_path(bd, net, path, xs, ys)
        results.append({
            "net": net, "uuid": uid, "violation": violation, "status": "routed",
            "layer": selected[0], "start": [round(selected[1].x, 4), round(selected[1].y, 4)],
            "items": count,
        })

    pcbnew.SaveBoard(args.out, board)
    report = {"fresh_dangling": len(fresh), "routed": sum(r["status"] == "routed" for r in results),
              "results": results}
    Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if all(r["status"] == "routed" for r in results) else 2


if __name__ == "__main__":
    sys.exit(main())
