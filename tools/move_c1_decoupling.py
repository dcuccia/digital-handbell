# SPDX-License-Identifier: MIT
"""Move C1 beside U2, remove its obsolete removable branches, and reconnect it.

Candidates are sampled on F.Cu at four orthogonal rotations.  A candidate must
meet the C1.1-to-U2.1 adjacency limit, have zero courtyard overlap, avoid rule
areas and other-net pad copper, admit a clearance-aware 0.5 mm VHI route, and
provide a legal adjacent GND through-via plus short F.Cu trace.  Frozen-board
copper is never removed.  Native refill/DRC and the standard result checker
remain authoritative.
"""
import argparse
import json
import math
import sys
from pathlib import Path

from shapely import affinity
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_routing_result as crr  # noqa: E402
import move_cluster as mc  # noqa: E402
import route_gaps as rg  # noqa: E402
from stitch_gnd_islands import item_shape, poly_set_to_shapely  # noqa: E402

VIA_D, VIA_DRILL = 0.6, 0.3
GND_TRACK = 0.3
CLEARANCE = 0.2
EDGE = 0.3


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True)
    ap.add_argument("--base-board", required=True)
    ap.add_argument("--max-adjacency", type=float, default=3.0)
    ap.add_argument("--step", type=float, default=0.25)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    pcbnew, _handle = crr.load_pcbnew()
    board = pcbnew.LoadBoard(args.board)
    base = pcbnew.LoadBoard(args.base_board)
    mm = pcbnew.ToMM
    c1 = board.FindFootprintByReference("C1")
    u2 = board.FindFootprintByReference("U2")
    pads = {p.GetNumber(): p for p in c1.Pads()}
    u2p = next(p for p in u2.Pads() if p.GetNumber() == "1")
    old_center = c1.GetPosition()
    ox, oy = mm(old_center.x), mm(old_center.y)
    ux, uy = mm(u2p.GetPosition().x), mm(u2p.GetPosition().y)
    old_orientation = c1.GetOrientationDegrees()
    old_pad_shapes = {n: item_shape(pcbnew, p, pcbnew.F_Cu) for n, p in pads.items()}
    old_pad_points = {n: Point(mm(p.GetPosition().x), mm(p.GetPosition().y)) for n, p in pads.items()}
    old_court = mc.footprint_area(pcbnew, c1)

    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline, False)
    board_area = unary_union(poly_set_to_shapely(pcbnew, outline))
    inner_court = board_area.buffer(-EDGE)
    f_rules = unary_union([unary_union(poly_set_to_shapely(pcbnew, z.Outline()))
                           for z in board.Zones() if z.GetIsRuleArea()
                           and z.IsOnLayer(pcbnew.F_Cu)
                           and (z.GetDoNotAllowFootprints() or z.GetDoNotAllowPads()
                                or "CONTACT_METAL_GUARD" in z.GetZoneName())]
                          or [Point().buffer(0)])
    via_rules = unary_union([unary_union(poly_set_to_shapely(pcbnew, z.Outline()))
                             for z in board.Zones() if z.GetIsRuleArea()
                             and z.GetDoNotAllowVias()] or [Point().buffer(0)])
    other_courts = [(fp.GetReference(), mc.footprint_area(pcbnew, fp))
                    for fp in board.GetFootprints()
                    if fp.GetReference() != "C1" and fp.GetLayer() == pcbnew.F_Cu]

    layers = ["F.Cu", "In2.Cu", "In3.Cu", "B.Cu"]
    layer_ids = {name: board.GetLayerID(name) for name in layers}
    copper = {name: [] for name in layers}
    holes = []
    for item in board.GetTracks():
        for name, layer in layer_ids.items():
            if item.IsOnLayer(layer):
                copper[name].append((item.GetNetname(), item_shape(pcbnew, item, layer)))
        if item.GetClass() == "PCB_VIA":
            q = item.GetPosition()
            holes.append(Point(mm(q.x), mm(q.y)).buffer(mm(item.GetDrillValue()) / 2))
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if fp.GetReference() == "C1":
                continue
            for name, layer in layer_ids.items():
                if pad.IsOnLayer(layer):
                    copper[name].append((pad.GetNetname(), item_shape(pcbnew, pad, layer)))
            if pad.HasHole():
                q = pad.GetPosition()
                holes.append(Point(mm(q.x), mm(q.y)).buffer(
                    mm(max(pad.GetDrillSize().x, pad.GetDrillSize().y)) / 2))

    def transform(shape, rotation, dx, dy):
        return affinity.translate(
            affinity.rotate(shape, rotation - old_orientation, origin=(ox, oy)), dx, dy)

    def via_site(gnd_point):
        other_all = []
        for name in layers:
            shapes = [shape for net, shape in copper[name] if net != "GND"]
            if shapes:
                other_all.append(unary_union(shapes).buffer(CLEARANCE + VIA_D / 2))
        blocked = unary_union(other_all)
        if holes:
            blocked = blocked.union(unary_union(holes).buffer(0.25 + VIA_DRILL / 2))
        if not via_rules.is_empty:
            blocked = blocked.union(via_rules.buffer(VIA_D / 2))
        allowed = board_area.buffer(-(EDGE + VIA_D / 2))
        f_other = unary_union([shape for net, shape in copper["F.Cu"] if net != "GND"])
        for radius in (0.65, 0.8, 1.0):
            for index in range(16):
                angle = 2 * math.pi * index / 16
                point = Point(gnd_point.x + radius * math.cos(angle),
                              gnd_point.y + radius * math.sin(angle))
                if not allowed.contains(point) or blocked.intersects(point):
                    continue
                trace = LineString([(gnd_point.x, gnd_point.y), (point.x, point.y)]).buffer(
                    GND_TRACK / 2)
                if not f_other.is_empty and trace.buffer(CLEARANCE).intersects(f_other):
                    continue
                return point
        return None

    rejects, legal = [], []
    span = args.max_adjacency + 2.0
    count = int(2 * span / args.step) + 1
    for rotation in (0.0, 90.0, 180.0, 270.0):
        for ix in range(count):
            for iy in range(count):
                cx, cy = ux - span + ix * args.step, uy - span + iy * args.step
                dx, dy = cx - ox, cy - oy
                p1 = transform(old_pad_points["1"], rotation, dx, dy)
                adjacency = p1.distance(Point(ux, uy))
                if adjacency > args.max_adjacency + 1e-9:
                    continue
                court = transform(old_court, rotation, dx, dy)
                blocker = None
                if not inner_court.contains(court):
                    blocker = "board edge"
                elif court.intersects(f_rules):
                    blocker = "F.Cu rule area"
                else:
                    overlap = next((ref for ref, shape in other_courts
                                    if court.intersects(shape)
                                    and court.intersection(shape).area > 1e-6), None)
                    if overlap:
                        blocker = f"courtyard {overlap}"
                new_pads = {n: transform(shape, rotation, dx, dy)
                            for n, shape in old_pad_shapes.items()}
                if blocker is None:
                    for number, net in (("1", "VHI"), ("2", "GND")):
                        other = unary_union([shape for own, shape in copper["F.Cu"] if own != net])
                        if not other.is_empty and new_pads[number].distance(other) < CLEARANCE:
                            blocker = f"other-net F.Cu at C1.{number}"
                            break
                gpoint = transform(old_pad_points["2"], rotation, dx, dy)
                site = via_site(gpoint) if blocker is None else None
                if blocker is None and site is None:
                    blocker = "no adjacent GND via site"
                row = {"center": [round(cx, 4), round(cy, 4)], "rotation": rotation,
                       "adjacency_mm": round(adjacency, 4), "blocker": blocker}
                if blocker:
                    rejects.append(row)
                else:
                    legal.append((row, dx, dy, new_pads, court, gpoint, site))

    rg.LAYERS[:] = layers
    rg.MARGIN = 4.0
    rg.POWER["VHI"] = (0.5, rg.net_clearance("VHI"))
    route_board = rg.Board(pcbnew, board)
    start = route_board.region(u2p.m_Uuid.AsString(), (ux, uy))
    found = None
    chosen = None
    if legal:
        found = rg.route_pair(route_board, "VHI", start,
                              {"F.Cu": unary_union([row[3]["1"] for row in legal])})
    if found is not None:
        path, xs, ys = found
        _layer, row_index, col_index = path[-1]
        endpoint = Point(float(xs[col_index]), float(ys[row_index]))
        chosen = min(legal, key=lambda row: row[3]["1"].distance(endpoint))
    if chosen is None:
        ranked = sorted(rejects, key=lambda row: row["adjacency_mm"])
        useful = [row for row in ranked if row["blocker"] != "courtyard U2"]
        best = (useful or ranked)[:3]
        report = {"status": "NO_LEGAL_PLACEMENT_OR_ROUTE", "legal_geometry_candidates": len(legal),
                  "top_rejected": best}
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 2

    row, dx, dy, _new_pads, new_court, gpoint, site = chosen
    c1.SetOrientationDegrees(row["rotation"])
    c1.Move(pcbnew.VECTOR2I(pcbnew.FromMM(dx), pcbnew.FromMM(dy)))
    path, xs, ys = found
    vhi_items = rg.add_path(route_board, "VHI", path, xs, ys)

    gnd = board.FindNet("GND")
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(gpoint.x), pcbnew.FromMM(gpoint.y)))
    track.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(site.x), pcbnew.FromMM(site.y)))
    track.SetWidth(pcbnew.FromMM(GND_TRACK))
    track.SetLayer(pcbnew.F_Cu)
    track.SetNet(gnd)
    board.Add(track)
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(site.x), pcbnew.FromMM(site.y)))
    via.SetWidth(pcbnew.FromMM(VIA_D))
    via.SetDrill(pcbnew.FromMM(VIA_DRILL))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetNet(gnd)
    board.Add(via)

    _lost, new = crr.compare_copper(crr.copper_items(pcbnew, base), crr.copper_items(pcbnew, board))
    removable = {item[-1].m_Uuid.AsString() for _key, item in new}
    old_vhi = old_pad_shapes["1"]
    old_gnd = old_pad_shapes["2"]
    remove = []
    # Remove the old F branches attached to each old pad.
    for net, reached in (("VHI", old_vhi), ("GND", old_gnd)):
        changed = True
        while changed:
            changed = False
            for item in board.GetTracks():
                uid = item.m_Uuid.AsString()
                if uid in remove or uid not in removable or item.GetNetname() != net:
                    continue
                if not item.IsOnLayer(pcbnew.F_Cu):
                    continue
                shape = item_shape(pcbnew, item, pcbnew.F_Cu)
                if shape.intersects(reached):
                    remove.append(uid)
                    reached = reached.union(shape)
                    changed = True
    # The old C1 VHI F branch ends in one removable via; remove its sole thin
    # inner continuation, stopping before the shared VHI junction.
    removed_vias = [item for item in board.GetTracks()
                    if item.m_Uuid.AsString() in remove and item.GetClass() == "PCB_VIA"]
    for old_via in removed_vias:
        q = Point(mm(old_via.GetPosition().x), mm(old_via.GetPosition().y))
        for item in board.GetTracks():
            uid = item.m_Uuid.AsString()
            if (uid in remove or uid not in removable or item.GetNetname() != "VHI"
                    or item.GetClass() == "PCB_VIA" or mm(item.GetWidth()) >= 0.5):
                continue
            if item_shape(pcbnew, item, item.GetLayer()).intersects(q.buffer(VIA_D / 2)):
                remove.append(uid)

    removed = {}
    for item in list(board.GetTracks()):
        if item.m_Uuid.AsString() in remove:
            removed[item.GetNetname()] = removed.get(item.GetNetname(), 0) + 1
            board.Remove(item)
    pcbnew.SaveBoard(args.out, board)
    report = {
        "status": "MOVED_AND_ROUTED", "candidate": row,
        "c1_center": [round(ox + dx, 4), round(oy + dy, 4)],
        "gnd_via": [round(site.x, 4), round(site.y, 4)],
        "vhi_width_mm": 0.5, "vhi_items": vhi_items,
        "gnd_track_width_mm": GND_TRACK, "removed_by_net": removed,
        "courtyard_overlaps": 0, "legal_geometry_candidates": len(legal),
    }
    Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
