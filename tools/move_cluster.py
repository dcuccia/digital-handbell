# SPDX-License-Identifier: MIT
"""Translate groups of footprints (and the copper in their old region) on a copy.

Placement-experiment helper: each group moves rigidly by (dx, dy) together with
tracks/vias that lie entirely inside its source region, so internal routing is
kept. Copper on protected nets is never moved. Reports courtyard overlaps and
moved vias that land in via keep-outs so they can be resolved before routing.
"""
import argparse
import json
import sys
from pathlib import Path

from shapely.geometry import box
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_routing_result as crr  # noqa: E402
from stitch_gnd_islands import poly_set_to_shapely  # noqa: E402

PROTECTED_NETS = {"/CELL_NEG", "VBAT"}


def footprint_area(pcbnew, fp):
    mm = pcbnew.ToMM
    layer = pcbnew.F_CrtYd if fp.GetLayer() == pcbnew.F_Cu else pcbnew.B_CrtYd
    try:
        shapes = poly_set_to_shapely(pcbnew, fp.GetCourtyard(layer))
    except Exception:  # noqa: BLE001 - fall back to the body box
        shapes = []
    if shapes:
        return unary_union(shapes)
    bb = fp.GetBoundingBox(False)
    return box(mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom()))


def legalize(pcbnew, board, areas, movable, min_overlap, iterations=300, radius=3.0, step=0.2):
    """Local search: move overlapping movable parts to the nearby offset with least overlap."""
    from shapely import affinity
    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline, False)
    board_area = unary_union(poly_set_to_shapely(pcbnew, outline)).buffer(-0.3)

    def total_overlap(ref, shape):
        side = areas[ref][0]
        return sum(shape.intersection(s).area for r, (sd, s) in areas.items()
                   if r != ref and sd == side and shape.intersects(s))

    offsets = sorted(((dx * step, dy * step) for dx in range(-int(radius / step), int(radius / step) + 1)
                      for dy in range(-int(radius / step), int(radius / step) + 1)),
                     key=lambda d: d[0] ** 2 + d[1] ** 2)
    for _ in range(iterations):
        worst = None
        for ref in movable:
            ov = total_overlap(ref, areas[ref][1])
            if ov > min_overlap and (worst is None or ov > worst[0]):
                worst = (ov, ref)
        if worst is None:
            return
        current, ref = worst
        shape = areas[ref][1]
        best = None
        for dx, dy in offsets[1:]:
            cand = affinity.translate(shape, dx, dy)
            if not board_area.contains(cand):
                continue
            score = total_overlap(ref, cand) + 0.02 * (abs(dx) + abs(dy))
            if best is None or score < best[0]:
                best = (score, dx, dy, cand)
            if score <= 0.02 * (abs(dx) + abs(dy)) + 1e-9:
                break
        if best is None or best[0] >= current:
            movable.discard(ref)
            continue
        _, dx, dy, cand = best
        board.FindFootprintByReference(ref).Move(pcbnew.VECTOR2I(pcbnew.FromMM(dx), pcbnew.FromMM(dy)))
        areas[ref] = (areas[ref][0], cand)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True)
    ap.add_argument("--plan", required=True, help="JSON: [{name, refs, dx, dy, region:[x0,y0,x1,y1]}]")
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--legalize", action="store_true", help="push overlapping moved parts apart")
    ap.add_argument("--anchor", nargs="*", default=["IC1", "U1"], help="moved parts the legalizer must not push")
    ap.add_argument("--min-overlap", type=float, default=0.15, help="ignore courtyard overlaps below this (mm2)")
    ap.add_argument("--radius", type=float, default=3.0, help="legalizer search radius (mm)")
    args = ap.parse_args()
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))

    pcbnew, _h = crr.load_pcbnew()
    board = pcbnew.LoadBoard(args.board)
    mm, frm = pcbnew.ToMM, pcbnew.FromMM

    def inside(region, item):
        x0, y0, x1, y1 = region
        pts = [item.GetPosition()] if item.GetClass() == "PCB_VIA" else [item.GetStart(), item.GetEnd()]
        return all(x0 <= mm(p.x) <= x1 and y0 <= mm(p.y) <= y1 for p in pts)

    # Decide copper ownership before anything moves.
    assignments = []
    tracks = list(board.GetTracks())
    for group in plan:
        region = group.get("region")
        owned = [t for t in tracks if region and t.GetNetname() not in PROTECTED_NETS and inside(region, t)
                 and not any(t in o for _, o in assignments)]
        assignments.append((group, owned))
    moved_refs, moved_copper = [], 0
    for group, owned in assignments:
        delta = pcbnew.VECTOR2I(frm(group["dx"]), frm(group["dy"]))
        for ref in group["refs"]:
            fp = board.FindFootprintByReference(ref)
            if fp is None:
                raise SystemExit(f"Unknown reference {ref}")
            fp.Move(delta)
            moved_refs.append(ref)
        for item in owned:
            item.Move(delta)
            moved_copper += 1

    # Overlap report (same side only).
    areas = {fp.GetReference(): (fp.GetLayer(), footprint_area(pcbnew, fp)) for fp in board.GetFootprints()}
    if args.legalize:
        legalize(pcbnew, board, areas, set(moved_refs) - set(args.anchor), args.min_overlap, radius=args.radius)
    overlaps = []
    refs = sorted(areas)
    for i, a in enumerate(refs):
        for b in refs[i + 1:]:
            if areas[a][0] == areas[b][0] and (a in moved_refs or b in moved_refs):
                inter = areas[a][1].intersection(areas[b][1]).area
                if inter > args.min_overlap:
                    overlaps.append({"a": a, "b": b, "area_mm2": round(inter, 3)})
    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline, False)
    board_area = unary_union(poly_set_to_shapely(pcbnew, outline))
    outside = [r for r in moved_refs if not board_area.contains(areas[r][1])]
    via_keepout = unary_union([unary_union(poly_set_to_shapely(pcbnew, z.Outline()))
                               for z in board.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()])
    bad_vias = []
    for item in board.GetTracks():
        if item.GetClass() == "PCB_VIA" and item.GetNetname() not in PROTECTED_NETS:
            p = item.GetPosition()
            from shapely.geometry import Point
            if via_keepout.intersects(Point(mm(p.x), mm(p.y)).buffer(mm(item.GetWidth(pcbnew.F_Cu)) / 2)):
                bad_vias.append(item)
    removed_vias = len(bad_vias)
    for v in bad_vias:
        board.Remove(v)

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(args.out, board)
    report = {"moved_refs": moved_refs, "moved_copper_items": moved_copper,
              "courtyard_overlaps": overlaps, "parts_outside_board": outside,
              "vias_removed_from_keepouts": removed_vias}
    Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: (v if k != "moved_refs" else len(v)) for k, v in report.items()}, indent=2))


if __name__ == "__main__":
    main()
