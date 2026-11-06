# SPDX-License-Identifier: MIT
"""Add GND stitching vias to front-pour islands that have no path to the In1 plane.

Deterministic, conservative helper: each candidate via must sit inside the
F.Cu GND fill island and the In1 GND fill, clear of all non-GND copper on the
other layers, existing holes, via keep-outs and the board edge. Existing copper
and parts are never changed. Results must still pass DRC and the standard check.
"""
import argparse
import json
import sys
from pathlib import Path

from shapely.geometry import Point, Polygon
from shapely.ops import polylabel, unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_routing_result as crr  # noqa: E402

VIA_DIAMETER = 0.6
VIA_DRILL = 0.3
CLEARANCE = 0.2
HOLE_TO_HOLE = 0.25
EDGE_CLEARANCE = 0.3
NET = "GND"


def poly_set_to_shapely(pcbnew, polys):
    parts = []
    mm = pcbnew.ToMM
    for i in range(polys.OutlineCount()):
        outline = polys.Outline(i)
        shell = [(mm(outline.CPoint(j).x), mm(outline.CPoint(j).y)) for j in range(outline.PointCount())]
        holes = []
        for h in range(polys.HoleCount(i)):
            hole = polys.Hole(i, h)
            holes.append([(mm(hole.CPoint(j).x), mm(hole.CPoint(j).y)) for j in range(hole.PointCount())])
        if len(shell) >= 3:
            parts.append(Polygon(shell, holes).buffer(0))
    return parts


def item_shape(pcbnew, item, layer):
    polys = pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(polys, layer, 0, pcbnew.FromMM(0.005), pcbnew.ERROR_INSIDE)
    return unary_union(poly_set_to_shapely(pcbnew, polys))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    pcbnew, _handle = crr.load_pcbnew()
    board = pcbnew.LoadBoard(args.board)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    mm, radius = pcbnew.ToMM, VIA_DIAMETER / 2
    layers = {"F.Cu": pcbnew.F_Cu, "In1.Cu": pcbnew.In1_Cu, "In2.Cu": pcbnew.In2_Cu, "B.Cu": pcbnew.B_Cu}

    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline, False)
    board_area = unary_union(poly_set_to_shapely(pcbnew, outline))

    f_islands, in1_fill, via_keepouts = [], [], []
    for zone in board.Zones():
        if zone.GetIsRuleArea():
            if zone.GetDoNotAllowVias():
                via_keepouts += poly_set_to_shapely(pcbnew, zone.Outline())
            continue
        if zone.GetNetname() != NET:
            continue
        if zone.IsOnLayer(pcbnew.F_Cu):
            f_islands += poly_set_to_shapely(pcbnew, zone.GetFilledPolysList(pcbnew.F_Cu))
        if zone.IsOnLayer(pcbnew.In1_Cu):
            in1_fill += poly_set_to_shapely(pcbnew, zone.GetFilledPolysList(pcbnew.In1_Cu))
    in1_fill = unary_union(in1_fill)

    through_gnd, holes = [], []
    blockers = {name: [] for name in ("In2.Cu", "B.Cu")}
    for item in board.GetTracks():
        if item.GetClass() == "PCB_VIA":
            p = Point(mm(item.GetPosition().x), mm(item.GetPosition().y))
            holes.append(p.buffer(mm(item.GetDrillValue()) / 2))
            if item.GetNetname() == NET:
                through_gnd.append(p)
        for name in blockers:
            if item.GetNetname() != NET and item.IsOnLayer(layers[name]):
                blockers[name].append(item_shape(pcbnew, item, layers[name]))
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.HasHole():
                p = Point(mm(pad.GetPosition().x), mm(pad.GetPosition().y))
                holes.append(p.buffer(mm(max(pad.GetDrillSize().x, pad.GetDrillSize().y)) / 2))
                if pad.GetNetname() == NET:
                    through_gnd.append(p)
            for name in blockers:
                if pad.GetNetname() != NET and pad.IsOnLayer(layers[name]):
                    blockers[name].append(item_shape(pcbnew, pad, layers[name]))

    forbidden_parts = [unary_union(shapes).buffer(CLEARANCE + radius) for shapes in blockers.values() if shapes]
    forbidden_parts.append(unary_union(holes).buffer(HOLE_TO_HOLE + VIA_DRILL / 2))
    if via_keepouts:
        forbidden_parts.append(unary_union(via_keepouts).buffer(radius))
    forbidden = unary_union(forbidden_parts)
    allowed_base = board_area.buffer(-(EDGE_CLEARANCE + radius)).intersection(in1_fill.buffer(-radius))

    added, skipped = [], []
    for index, island in enumerate(f_islands):
        if any(island.contains(p) for p in through_gnd):
            continue
        region = island.buffer(-radius).intersection(allowed_base).difference(forbidden)
        if region.is_empty:
            skipped.append({"island": index, "area_mm2": round(island.area, 3)})
            continue
        best = max(getattr(region, "geoms", [region]), key=lambda g: g.area)
        point = polylabel(best, tolerance=0.01)
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(point.x), pcbnew.FromMM(point.y)))
        via.SetWidth(pcbnew.FromMM(VIA_DIAMETER))
        via.SetDrill(pcbnew.FromMM(VIA_DRILL))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetNet(board.FindNet(NET))
        board.Add(via)
        added.append({"island": index, "x": round(point.x, 4), "y": round(point.y, 4),
                      "island_area_mm2": round(island.area, 3)})

    filler.Fill(board.Zones())
    pcbnew.SaveBoard(args.out, board)
    report = {"islands": len(f_islands), "vias_added": added, "islands_without_site": skipped,
              "via": [VIA_DIAMETER, VIA_DRILL]}
    Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
