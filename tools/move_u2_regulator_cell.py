# SPDX-License-Identifier: MIT
"""Co-place and reconnect U2 input/output capacitors C1 and C4.

U2 and C5 remain fixed.  C1/C4 candidates use four orthogonal rotations,
explicit adjacency limits, zero courtyard overlap, applicable keep-outs,
direct supply links at 0.50/0.25 mm, and one adjacent GND via per capacitor.
Only router/agent copper is removed, except C4's frozen pad-only GND stub,
which is explicitly reported and replaced by C4's own via.
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
from stitch_gnd_islands import item_shape, poly_set_to_shapely  # noqa: E402

LAYERS = ["F.Cu", "In2.Cu", "In3.Cu", "B.Cu"]
VIA_D, VIA_DRILL = 0.6, 0.3
CLEARANCE, EDGE = 0.2, 0.3
GND_TRACK = 0.3
CAPS = {
    "C1": {"target": "1", "net": "VHI", "width": 0.5},
    "C4": {"target": "5", "net": "+3V3", "width": 0.25},
    "C5": {"target": "5", "net": "+3V3", "width": 0.25},
}


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
    u2 = board.FindFootprintByReference("U2")
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    layer_ids = {name: board.GetLayerID(name) for name in LAYERS}

    _lost, added = crr.compare_copper(crr.copper_items(pcbnew, base), crr.copper_items(pcbnew, board))
    removable = {item[-1].m_Uuid.AsString() for _key, item in added}
    old = {}
    remove = set()
    frozen_pad_stubs = []
    for ref, rule in CAPS.items():
        fp = footprints[ref]
        pads = {p.GetNumber(): p for p in fp.Pads()}
        center = fp.GetPosition()
        ox, oy = mm(center.x), mm(center.y)
        shapes = {n: item_shape(pcbnew, p, pcbnew.F_Cu) for n, p in pads.items()}
        points = {n: Point(mm(p.GetPosition().x), mm(p.GetPosition().y)) for n, p in pads.items()}
        old[ref] = {
            "fp": fp, "pads": pads, "center": (ox, oy), "orientation": fp.GetOrientationDegrees(),
            "shapes": shapes, "points": points, "court": mc.footprint_area(pcbnew, fp),
        }
        # Removable branches attached to either old capacitor pad.
        for pad in pads.values():
            net = pad.GetNetname()
            reached = item_shape(pcbnew, pad, pcbnew.F_Cu)
            changed = True
            while changed:
                changed = False
                for item in board.GetTracks():
                    uid = item.m_Uuid.AsString()
                    if (uid in remove or uid not in removable or item.GetNetname() != net
                            or not item.IsOnLayer(pcbnew.F_Cu)):
                        continue
                    shape = item_shape(pcbnew, item, pcbnew.F_Cu)
                    if shape.intersects(reached):
                        remove.add(uid)
                        reached = reached.union(shape)
                        changed = True
        # C4 has one frozen GND trace whose endpoint is exactly its pad centre.
        if ref == "C4":
            pad = pads["2"]
            centre = pad.GetPosition()
            for item in board.GetTracks():
                if (item.GetNetname() == "GND" and item.GetClass() != "PCB_VIA"
                        and item.m_Uuid.AsString() not in removable
                        and (item.GetStart() == centre or item.GetEnd() == centre)):
                    remove.add(item.m_Uuid.AsString())
                    frozen_pad_stubs.append(item.m_Uuid.AsString())

    # Include C1's sole thin inner continuation from its old branch via.
    old_branch_vias = [item for item in board.GetTracks()
                       if item.m_Uuid.AsString() in remove and item.GetClass() == "PCB_VIA"]
    for via in old_branch_vias:
        point = Point(mm(via.GetPosition().x), mm(via.GetPosition().y))
        for item in board.GetTracks():
            uid = item.m_Uuid.AsString()
            if (uid in remove or uid not in removable or item.GetNetname() != "VHI"
                    or item.GetClass() == "PCB_VIA" or mm(item.GetWidth()) >= 0.5):
                continue
            if item_shape(pcbnew, item, item.GetLayer()).intersects(point.buffer(0.25)):
                remove.add(uid)

    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline, False)
    board_area = unary_union(poly_set_to_shapely(pcbnew, outline))
    inner = board_area.buffer(-EDGE)
    f_rules = unary_union([unary_union(poly_set_to_shapely(pcbnew, zone.Outline()))
                           for zone in board.Zones() if zone.GetIsRuleArea()
                           and zone.IsOnLayer(pcbnew.F_Cu)
                           and (zone.GetDoNotAllowFootprints() or zone.GetDoNotAllowPads()
                                or "CONTACT_METAL_GUARD" in zone.GetZoneName())]
                          or [Point().buffer(0)])
    via_rules = unary_union([unary_union(poly_set_to_shapely(pcbnew, zone.Outline()))
                             for zone in board.Zones() if zone.GetIsRuleArea()
                             and zone.GetDoNotAllowVias()] or [Point().buffer(0)])
    other_courts = [(fp.GetReference(), mc.footprint_area(pcbnew, fp))
                    for fp in board.GetFootprints()
                    if fp.GetReference() not in CAPS and fp.GetLayer() == pcbnew.F_Cu]

    copper = {name: [] for name in LAYERS}
    holes = []
    existing_gnd_vias = []
    for item in board.GetTracks():
        if item.m_Uuid.AsString() in remove:
            continue
        for name, layer in layer_ids.items():
            if item.IsOnLayer(layer):
                copper[name].append((item.GetNetname(), item_shape(pcbnew, item, layer)))
        if item.GetClass() == "PCB_VIA":
            q = item.GetPosition()
            holes.append(Point(mm(q.x), mm(q.y)).buffer(mm(item.GetDrillValue()) / 2))
            if item.GetNetname() == "GND":
                existing_gnd_vias.append(Point(mm(q.x), mm(q.y)))
    for fp in board.GetFootprints():
        if fp.GetReference() in CAPS:
            continue
        for pad in fp.Pads():
            for name, layer in layer_ids.items():
                if pad.IsOnLayer(layer):
                    copper[name].append((pad.GetNetname(), item_shape(pcbnew, pad, layer)))
            if pad.HasHole():
                q = pad.GetPosition()
                holes.append(Point(mm(q.x), mm(q.y)).buffer(
                    mm(max(pad.GetDrillSize().x, pad.GetDrillSize().y)) / 2))

    other_by_layer = {}
    for name in LAYERS:
        other_by_layer[name] = {
            net: unary_union([shape for own, shape in copper[name] if own != net])
            for net in {"VHI", "+3V3", "GND"}
        }
    via_block = unary_union([
        other_by_layer[name]["GND"].buffer(CLEARANCE + VIA_D / 2) for name in LAYERS
        if not other_by_layer[name]["GND"].is_empty
    ])
    if holes:
        via_block = via_block.union(unary_union(holes).buffer(0.25 + VIA_DRILL / 2))
    if not via_rules.is_empty:
        via_block = via_block.union(via_rules.buffer(VIA_D / 2))
    via_area = board_area.buffer(-(EDGE + VIA_D / 2))

    def transform(ref, shape, rotation, dx, dy):
        ox, oy = old[ref]["center"]
        return affinity.translate(
            affinity.rotate(shape, rotation - old[ref]["orientation"], origin=(ox, oy)), dx, dy)

    def gnd_site(gnd_point):
        # Prefer an existing GND via when the pad-to-via trace is <= 1 mm.
        for site in sorted(existing_gnd_vias, key=lambda point: point.distance(gnd_point)):
            if site.distance(gnd_point) > 1.0 + 1e-9:
                break
            trace = LineString([(gnd_point.x, gnd_point.y), (site.x, site.y)]).buffer(
                GND_TRACK / 2)
            if (not other_by_layer["F.Cu"]["GND"].is_empty
                    and trace.buffer(CLEARANCE).intersects(other_by_layer["F.Cu"]["GND"])):
                continue
            return site, trace, True
        for radius in (0.65, 0.8, 1.0):
            for index in range(16):
                angle = 2 * math.pi * index / 16
                site = Point(gnd_point.x + radius * math.cos(angle),
                             gnd_point.y + radius * math.sin(angle))
                if not via_area.contains(site) or via_block.intersects(site):
                    continue
                trace = LineString([(gnd_point.x, gnd_point.y), (site.x, site.y)]).buffer(
                    GND_TRACK / 2)
                if (not other_by_layer["F.Cu"]["GND"].is_empty
                        and trace.buffer(CLEARANCE).intersects(other_by_layer["F.Cu"]["GND"])):
                    continue
                return site, trace, False
        return None, None, False

    candidates = {}
    reject_counts = {}
    for ref, rule in CAPS.items():
        target_pad = next(p for p in u2.Pads() if p.GetNumber() == rule["target"])
        target = Point(mm(target_pad.GetPosition().x), mm(target_pad.GetPosition().y))
        ox, oy = old[ref]["center"]
        span = args.max_adjacency + 2.0
        count = int(2 * span / args.step) + 1
        accepted = []
        counts = {}
        for rotation in (0.0, 90.0, 180.0, 270.0):
            for ix in range(count):
                for iy in range(count):
                    cx, cy = target.x - span + ix * args.step, target.y - span + iy * args.step
                    dx, dy = cx - ox, cy - oy
                    p1 = transform(ref, old[ref]["points"]["1"], rotation, dx, dy)
                    adjacency = p1.distance(target)
                    if adjacency > args.max_adjacency:
                        continue
                    court = transform(ref, old[ref]["court"], rotation, dx, dy)
                    blocker = None
                    if not inner.contains(court):
                        blocker = "edge"
                    elif court.intersects(f_rules):
                        blocker = "rule"
                    else:
                        hit = next((name for name, shape in other_courts
                                    if court.intersects(shape)
                                    and court.intersection(shape).area > 1e-6), None)
                        if hit:
                            blocker = f"courtyard {hit}"
                    shapes = {n: transform(ref, shape, rotation, dx, dy)
                              for n, shape in old[ref]["shapes"].items()}
                    for number, net in (("1", rule["net"]), ("2", "GND")):
                        obstacle = other_by_layer["F.Cu"][net]
                        if blocker is None and not obstacle.is_empty and shapes[number].distance(obstacle) < CLEARANCE:
                            blocker = f"copper C{number}"
                    supply = LineString([(target.x, target.y), (p1.x, p1.y)]).buffer(
                        rule["width"] / 2)
                    obstacle = other_by_layer["F.Cu"][rule["net"]]
                    if (blocker is None and not obstacle.is_empty
                            and supply.buffer(CLEARANCE).intersects(obstacle)):
                        blocker = "supply corridor"
                    gpoint = transform(ref, old[ref]["points"]["2"], rotation, dx, dy)
                    site, gtrace, existing_via = gnd_site(gpoint) if blocker is None else (None, None, False)
                    if blocker is None and site is None:
                        blocker = "GND via"
                    if blocker:
                        counts[blocker] = counts.get(blocker, 0) + 1
                        continue
                    accepted.append({
                        "ref": ref, "center": (cx, cy), "rotation": rotation,
                        "adjacency": adjacency, "court": court, "pads": shapes,
                        "supply": supply, "gpoint": gpoint, "site": site,
                        "gtrace": gtrace, "existing_via": existing_via,
                        "target": target, "rule": rule,
                    })
        accepted.sort(key=lambda row: (row["adjacency"], row["center"]))
        candidates[ref] = accepted[:300]
        reject_counts[ref] = counts

    output_pairs = []
    for c4 in candidates["C4"]:
        for c5 in candidates["C5"]:
            if c4["court"].intersects(c5["court"]):
                continue
            if (c4["site"].distance(c5["site"]) < 0.85
                    and not (c4["existing_via"] and c5["existing_via"]
                             and c4["site"].distance(c5["site"]) < 0.002)):
                continue
            if (c4["supply"].buffer(CLEARANCE).intersects(c5["gtrace"])
                    or c5["supply"].buffer(CLEARANCE).intersects(c4["gtrace"])):
                continue
            output_pairs.append((c4["adjacency"] + c5["adjacency"], c4, c5))
    output_pairs.sort(key=lambda row: row[0])
    chosen = None
    for c1 in candidates["C1"]:
        for output_score, c4, c5 in output_pairs[:500]:
            if c1["court"].intersects(c4["court"]) or c1["court"].intersects(c5["court"]):
                continue
            if (c1["supply"].buffer(CLEARANCE).intersects(c4["supply"])
                    or c1["supply"].buffer(CLEARANCE).intersects(c5["supply"])):
                continue
            if ((c1["site"].distance(c4["site"]) < 0.85
                 and not (c1["existing_via"] and c4["existing_via"]
                          and c1["site"].distance(c4["site"]) < 0.002))
                    or (c1["site"].distance(c5["site"]) < 0.85
                        and not (c1["existing_via"] and c5["existing_via"]
                                 and c1["site"].distance(c5["site"]) < 0.002))):
                continue
            if (c1["supply"].buffer(CLEARANCE).intersects(c4["gtrace"])
                    or c1["supply"].buffer(CLEARANCE).intersects(c5["gtrace"])
                    or c4["supply"].buffer(CLEARANCE).intersects(c1["gtrace"])
                    or c5["supply"].buffer(CLEARANCE).intersects(c1["gtrace"])):
                continue
            score = c1["adjacency"] + output_score
            if chosen is None or score < chosen[0]:
                chosen = (score, c1, c4, c5)
    if chosen is None:
        report = {"status": "NO_JOINT_CANDIDATE",
                  "candidate_counts": {ref: len(rows) for ref, rows in candidates.items()},
                  "reject_counts": reject_counts, "frozen_pad_stubs": frozen_pad_stubs}
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 2

    _score, c1row, c4row, c5row = chosen
    for row in (c1row, c4row, c5row):
        fp = old[row["ref"]]["fp"]
        ox, oy = old[row["ref"]]["center"]
        fp.SetOrientationDegrees(row["rotation"])
        fp.Move(pcbnew.VECTOR2I(pcbnew.FromMM(row["center"][0] - ox),
                                pcbnew.FromMM(row["center"][1] - oy)))
        net = board.FindNet(row["rule"]["net"])
        supply = pcbnew.PCB_TRACK(board)
        supply.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(row["target"].x),
                                        pcbnew.FromMM(row["target"].y)))
        moved_pad = next(pad for pad in fp.Pads() if pad.GetNumber() == "1")
        p1 = Point(moved_pad.GetPosition().x / 1e6, moved_pad.GetPosition().y / 1e6)
        supply.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(p1.x), pcbnew.FromMM(p1.y)))
        supply.SetWidth(pcbnew.FromMM(row["rule"]["width"]))
        supply.SetLayer(pcbnew.F_Cu)
        supply.SetNet(net)
        board.Add(supply)
        gnd = board.FindNet("GND")
        trace = pcbnew.PCB_TRACK(board)
        trace.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(row["gpoint"].x),
                                      pcbnew.FromMM(row["gpoint"].y)))
        trace.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(row["site"].x),
                                    pcbnew.FromMM(row["site"].y)))
        trace.SetWidth(pcbnew.FromMM(GND_TRACK))
        trace.SetLayer(pcbnew.F_Cu)
        trace.SetNet(gnd)
        board.Add(trace)
        if not row["existing_via"]:
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(row["site"].x),
                                           pcbnew.FromMM(row["site"].y)))
            via.SetWidth(pcbnew.FromMM(VIA_D))
            via.SetDrill(pcbnew.FromMM(VIA_DRILL))
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            via.SetNet(gnd)
            board.Add(via)

    removed = {}
    for item in list(board.GetTracks()):
        if item.m_Uuid.AsString() in remove:
            removed[item.GetNetname()] = removed.get(item.GetNetname(), 0) + 1
            board.Remove(item)
    pcbnew.SaveBoard(args.out, board)
    report_rows = {}
    for row in (c1row, c4row, c5row):
        report_rows[row["ref"]] = {
            "center": [round(x, 4) for x in row["center"]], "rotation": row["rotation"],
            "adjacency_mm": round(row["adjacency"], 4),
            "supply_width_mm": row["rule"]["width"],
            "gnd_via": [round(row["site"].x, 4), round(row["site"].y, 4)],
            "gnd_via_existing": row["existing_via"],
        }
    report = {"status": "MOVED_AND_ROUTED", "placements": report_rows,
              "candidate_counts": {ref: len(rows) for ref, rows in candidates.items()},
              "removed_by_net": removed, "frozen_pad_stubs_replaced": frozen_pad_stubs,
              "moved": ["C1", "C4", "C5"], "unchanged": ["U2"]}
    Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
