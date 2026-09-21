# SPDX-License-Identifier: MIT
"""Read-only review artifacts and supplemental assertions for a saved In1 candidate."""
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "hardware/handbell/iterations/printed-bell-four-layer"
SOURCE = PACKAGE / "handbell.kicad_pcb"
INVENTORY = PACKAGE / "reports/in1-exclusion-inventory.json"
PLAN = PACKAGE.parent / "printed-bell-clock-draft/reports/front-ground-plan.json"
REPORT = PACKAGE / "reports/in1-plane-review-supplement.json"
NATIVE_SVG = PACKAGE / "reports/in1-plane-native.svg"
DETAIL_PNG = PACKAGE / "reports/in1-plane-review-details.png"
CLI = Path(os.environ["LOCALAPPDATA"]) / "Programs/KiCad/10.0/bin/kicad-cli.exe"
CANDIDATE_SHA = "19d3bf9a1ab37dcc7af29f0cc99cc44a98564f878402beee15af3ce0a731ff78"
IN1_ZONE = "332d3ba8-ed46-550f-912f-bb402cd2a16b"

sys.path.insert(0, str(ROOT / "tools"))
from kicad_sexpr import load


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(value, message):
    if not value: raise AssertionError(message)


def run(command, work):
    out, err, stage = work/"native-svg.stdout.txt", work/"native-svg.stderr.txt", work/"stage.json"
    public = ["<kicad-cli>" if x == str(CLI) else
              x.replace(str(work), "<work>").replace(str(ROOT), "<repo>") for x in command]
    stage.write_text(json.dumps({"status": "started", "command": public}, indent=2)+"\n")
    started = time.monotonic()
    with out.open("w") as stdout, err.open("w") as stderr:
        result = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=60)
    record = {"status": "complete", "command": public, "exit_code": result.returncode,
              "seconds": time.monotonic()-started, "stdout": out.name, "stderr": err.name}
    stage.write_text(json.dumps(record, indent=2)+"\n")
    require(result.returncode == 0, "Native SVG export failed")
    return record


def raw_nonzone(text, root):
    return [text[item.start:item.end] for item in root.items
            if not (getattr(item, "head", None) == "zone")]


def zone_children(text, zone):
    return [text[item.start:item.end] for item in zone.items
            if getattr(item, "head", None) != "filled_polygon"]


def draw_poly(draw, pcb, poly, transform, fill, outline):
    for index in range(poly.OutlineCount()):
        chain = poly.COutline(index)
        points = [transform(pcb.ToMM(chain.CPoint(i).x), pcb.ToMM(chain.CPoint(i).y))
                  for i in range(chain.PointCount())]
        if len(points) >= 3:
            draw.polygon(points, fill=fill, outline=outline)
        for hole_index in range(poly.HoleCount(index)):
            hole = poly.CHole(index, hole_index)
            points = [transform(pcb.ToMM(hole.CPoint(i).x), pcb.ToMM(hole.CPoint(i).y))
                      for i in range(hole.PointCount())]
            if len(points) >= 3:
                draw.polygon(points, fill="white", outline=outline)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    args = parser.parse_args()
    candidate, work = args.candidate.resolve(), args.work_dir.resolve()
    require(sha(candidate) == CANDIDATE_SHA, "Unexpected staged candidate")
    require(not work.exists(), "Work directory must be new")
    work.mkdir(parents=True)
    native_svg = work/"in1-plane-native.svg"
    command = [str(CLI), "pcb", "export", "svg", "--mode-single",
               "--layers", "In1.Cu,Edge.Cuts", "--fit-page-to-board",
               "--exclude-drawing-sheet", "--output", str(native_svg), str(candidate)]
    native_stage = run(command, work)
    native_stage["command"][-1] = "<candidate>"
    shutil.copy2(native_svg, NATIVE_SVG)

    native_dir = CLI.parent
    dll_handle = os.add_dll_directory(str(native_dir))
    sys.path.insert(0, str(native_dir/"Lib/site-packages"))
    import pcbnew as pcb
    from PIL import Image, ImageDraw, ImageFont
    from zone_graph import CopperGraph, IslandItem
    from check_front_ground import bounds_polygon
    from check_printed_bell_power_rework import CopperGraph as PrimitiveGraph

    graph = CopperGraph(pcb, candidate)
    primitive = PrimitiveGraph(pcb, candidate)
    plan, inventory = json.loads(PLAN.read_text()), json.loads(INVENTORY.read_text())
    replay = json.loads((PACKAGE/"reports/in1-plane-settings-replay.json").read_text())
    other_crossings = {row["uuid"]: row["net"]
                       for row in replay["projected_f_trace_crossings_of_in1_sensitive_voids"]
                       if not row["intended_sensitive_net"]}
    require(Counter(other_crossings.values()) == Counter({"+3V3": 5, "VAMP": 2, "V+": 3}),
            "Recorded ten-track other-power crossing inventory changed")
    by_zone = {z.m_Uuid.AsString(): z for z in graph.board.Zones()}
    f_islands = [x for x in graph.items.values()
                 if isinstance(x, IslandItem) and x.layer == pcb.F_Cu]
    comparisons = 0
    for record in plan["protection"]["pour_only_F_keepouts"]:
        uid = record["protected_item_uuid"]
        item = graph.items[uid]
        if not item.IsOnLayer(pcb.F_Cu):
            continue
        for island in f_islands:
            comparisons += 1
            require(not island.polygon.Collide(item.GetEffectiveShape(pcb.F_Cu), pcb.FromMM(.25)-1),
                    "F island approaches protected item: " + uid)

    expected_guards = {}
    for row in inventory["existing_pour_only_exclusions"]:
        if row["protected_item_uuid"] in {
                "6623be95-c657-5a8e-bedb-c5a73d42d40b",
                "eafa404c-be47-5f5c-8167-d39a967ba2e5"}:
            expected_guards["in1-private/"+row["protected_item_uuid"]] = row["bounds_absolute_iu"]
    for row in inventory["sensitive_regions"]["BOOST_SW"]["items"]:
        b = row["bounds_iu"]
        expected_guards["in1-boost-sw/"+row["uuid"]] = [b[0]-250000, b[1]-250000, b[2]+250000, b[3]+250000]
    expected_guards["in1-clock-region"] = [90103600, 96152596, 97237500, 100263901]
    guard_checks = []
    for name, bounds in expected_guards.items():
        zone = next(z for z in by_zone.values() if z.GetZoneName() == name)
        expected = bounds_polygon(pcb, {"bounds_absolute_iu": bounds})
        actual_only = zone.Outline().CloneDropTriangulation()
        expected_only = expected.CloneDropTriangulation()
        actual_only.BooleanSubtract(expected)
        expected_only.BooleanSubtract(zone.Outline())
        require(actual_only.IsEmpty() and expected_only.IsEmpty(), "In1 guard polygon differs: " + name)
        guard_checks.append({"name": name, "bounds_iu": bounds, "symmetric_difference_empty": True})

    source_text, source_root = load(SOURCE)
    candidate_text, candidate_root = load(candidate)
    source_nonzone, candidate_nonzone = raw_nonzone(source_text, source_root), raw_nonzone(candidate_text, candidate_root)
    require(source_nonzone == candidate_nonzone, "Original top-level non-zone source blocks changed")
    source_zones = {z.value("uuid"): z for z in source_root.children("zone")}
    candidate_zones = {z.value("uuid"): z for z in candidate_root.children("zone")}
    for uid, zone in source_zones.items():
        require(zone_children(source_text, zone) == zone_children(candidate_text, candidate_zones[uid]),
                "Original zone child changed outside fill cache: " + uid)

    paths = []
    for a, b in (("U5.4", "C27.2"), ("U5.4", "C28.2"), ("U5.6", "C27.1"), ("U5.6", "C28.1")):
        ar, ap = a.split("."); br, bp = b.split(".")
        nodes = primitive.path(primitive.pad_uuid(ar, ap), primitive.pad_uuid(br, bp), pcb.F_Cu)
        require(nodes, "No F-only primitive path: " + a + "->" + b)
        paths.append({"from": a, "to": b, "net": primitive.pads[primitive.pad_uuid(ar, ap)].GetNetname(),
                      "all_F_Cu": all(x["layer"] == "F.Cu" for x in nodes),
                      "copper_uuids": list(dict.fromkeys(x["uuid"] for x in nodes)),
                      "via_uuids": sorted({x["uuid"] for x in nodes
                                          if isinstance(primitive.items[x["uuid"]], pcb.PCB_VIA)})})

    windows = [("Clock detail", (88, 95, 99, 103)), ("Boost detail", (93, 111, 101, 119))]
    image = Image.new("RGB", (1320, 570), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(Path(os.environ["WINDIR"])/"Fonts/arial.ttf"), 14)
    in1_shapes = [x.polygon for x in graph.items.values()
                  if isinstance(x, IslandItem) and x.layer == pcb.In1_Cu and x.zone_uuid == IN1_ZONE]
    other_counts = Counter()
    for panel, (title, bounds) in enumerate(windows):
        x0, y0, x1, y1 = bounds
        left, top, width, height = panel*660+20, 35, 620, 450
        panel_image = Image.new("RGB", (width, height), "white")
        panel_draw = ImageDraw.Draw(panel_image)
        transform = lambda x, y: ((x-x0)*width/(x1-x0), (y-y0)*height/(y1-y0))
        for poly in in1_shapes:
            draw_poly(panel_draw, pcb, poly, transform, "#9bd39b", "#4d8b4d")
        for uid, item in primitive.items.items():
            if not hasattr(item, "GetClass") or item.GetClass() != "PCB_TRACK" or not item.IsOnLayer(pcb.F_Cu):
                continue
            box = item.GetEffectiveShape(pcb.F_Cu).BBox()
            if (pcb.ToMM(box.GetRight()) < x0 or pcb.ToMM(box.GetLeft()) > x1
                    or pcb.ToMM(box.GetBottom()) < y0 or pcb.ToMM(box.GetTop()) > y1):
                continue
            net = item.GetNetname()
            intended = net == "BOOST_SW" or any(token in net for token in ("XIN", "XOUT", "C3-Pad2"))
            other = uid in other_crossings
            if net != "GND" and not intended and not other:
                continue
            if other:
                other_counts[net] += 1
            poly = pcb.SHAPE_POLY_SET()
            item.TransformShapeToPolygon(poly, pcb.F_Cu, 0, pcb.FromMM(.001), pcb.ERROR_OUTSIDE)
            color = "#176b3a" if net == "GND" else "#cc5500" if intended else "#7048a8"
            draw_poly(panel_draw, pcb, poly, transform, color, color)
        for guard_bounds in expected_guards.values():
            gx0, gy0, gx1, gy1 = [value/1e6 for value in guard_bounds]
            if gx1 < x0 or gx0 > x1 or gy1 < y0 or gy0 > y1:
                continue
            ax, ay = transform(gx0, gy0)
            bx, by = transform(gx1, gy1)
            panel_draw.rectangle((ax, ay, bx, by), outline="#d22", width=2)
        panel_draw.rectangle((0, 0, width-1, height-1), outline="black")
        image.paste(panel_image, (left, top))
        draw.text((left, 12), f"{title}: actual In1 fill + selected existing F.Cu tracks", font=font, fill="black")
    draw.text((20, 505), "Green fill: actual saved In1 native polygon; dark green: F GND; orange: intended clock/BOOST_SW; purple: other power crossings.", font=font, fill="black")
    draw.text((20, 530), "Red guard rectangles are policy guides, not filled copper. Review rendering only; no AC impedance, thermal, or functional approval.", font=font, fill="black")
    image.save(DETAIL_PNG)
    require(other_counts == Counter({"+3V3": 5, "VAMP": 2, "V+": 3}),
            "Rendered other-power crossing inventory changed")

    report = {
        "status": "READ_ONLY_REVIEW_SUPPLEMENT", "candidate_sha256": sha(candidate),
        "source_pcb_sha256": sha(SOURCE), "review_tool_sha256": sha(__file__),
        "native_svg": {"file": NATIVE_SVG.name, "sha256": sha(NATIVE_SVG),
                       "layers": ["In1.Cu", "Edge.Cuts"], "command": native_stage},
        "detail_png": {"file": DETAIL_PNG.name, "sha256": sha(DETAIL_PNG),
                       "windows_mm": [{"name": n, "bounds": list(b)} for n, b in windows],
                       "render_source": "Exact native saved In1 filled polygons and native F.Cu primitive shapes; rasterized for review.",
                       "other_power_crossing_track_counts": dict(other_counts)},
        "actual_fill": {"zone_uuid": IN1_ZONE,
                        "islands": [x for x in graph.zone_islands if x["zone_uuid"] == IN1_ZONE],
                        "guide_guards_are_not_fill": True},
        "supplemental_assertions": {
            "ten_F_protected_items_checked_against_every_F_island_at_0_25_mm": True,
            "F_protected_item_island_comparisons": comparisons,
            "nine_In1_guard_native_outlines_exact_by_symmetric_difference": guard_checks,
            "all_original_top_level_nonzone_nodes_exact_raw_strings": True,
            "original_nonzone_block_count": len(source_nonzone),
            "original_nonzone_blocks_sha256": hashlib.sha256("".join(source_nonzone).encode()).hexdigest(),
            "all_original_zone_children_except_filled_polygon_exact_raw_strings": True},
        "boost_local_F_paths": paths,
        "limits": ["Read-only staged-candidate evidence; no refill or geometry change.",
                   "Connectivity is topological only; no AC impedance, current, thermal, or manufacturing approval."] }
    REPORT.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"report_sha256": sha(REPORT), "native_svg_sha256": sha(NATIVE_SVG),
                      "detail_png_sha256": sha(DETAIL_PNG)}, indent=2))
    dll_handle.close()


if __name__ == "__main__":
    main()
