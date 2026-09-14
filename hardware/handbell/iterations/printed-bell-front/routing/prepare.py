# SPDX-License-Identifier: MIT
"""Read-only routing preparation. No copper writer is enabled before parent release."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import html
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
ROOT = PACKAGE.parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from kicad_sexpr import load

PUBLISHED_COMMIT = "23cb3fe26707f094ce3eaf365807c322bd2844ed"
EXPECTED = {
    "placement-manifest.json": "710717186d5ecc795edaf3da7eec8f6532f34077906645a8fca32318320f23c4",
    "handbell.kicad_pcb": "17dc83ce5dce2af72a816bc6d5224a874ad6c7fac6eac0bc59d0ced8662adf53",
    "handbell.kicad_sch": "e131a8d093795df7285bcae4a8886ffe01106c6513a19bd588ee7c29c6993b4f",
    "battery-contact-interface.json": "f96133d9f044600167477bcddbf67c43311ed0897066db9fa63d8e7f8118467b",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def rotate(x, y, angle):
    a = math.radians(-angle)
    return x*math.cos(a)-y*math.sin(a), x*math.sin(a)+y*math.cos(a)


def point(node):
    return list(map(float, node.atoms()[1:3]))


def bindings():
    paths = [path for path in PACKAGE.rglob("*") if path.is_file() and not path.is_relative_to(HERE)
             and not path.name.endswith((".lck", ".bak"))]
    return {str(p.relative_to(PACKAGE)): digest(p) for p in sorted(paths)}


def point_segment_distance(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    fraction = min(1, max(0, ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy))) if dx or dy else 0
    return math.dist(p, [a[0]+fraction*dx, a[1]+fraction*dy])


def polygon_distance(p, points):
    inside = False
    for a, b in zip(points, points[1:]+points[:1]):
        if (a[1] > p[1]) != (b[1] > p[1]) and p[0] < (b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:
            inside = not inside
    return 0 if inside else min(point_segment_distance(p, a, b) for a, b in zip(points, points[1:]+points[:1]))


def geometry_distance(p, shape):
    x, y = rotate(p[0]-shape["center"][0], p[1]-shape["center"][1], -shape["angle_deg"])
    if shape["shape"] == "circle":
        return max(0, math.hypot(x, y)-shape["size"][0]/2)
    if shape["shape"] == "custom":
        return min(polygon_distance(p, poly) for poly in shape["polygons"])
    # Rounded/oval corners are conservatively filled, never cut away.
    return math.hypot(max(abs(x)-shape["size"][0]/2, 0), max(abs(y)-shape["size"][1]/2, 0))


def read_pads(board):
    pads, holes = [], []
    for fp in board.children("footprint"):
        ref = fp.properties()["Reference"]
        at = list(map(float, fp.child("at").atoms()[1:]))
        angle = at[2] if len(at) > 2 else 0
        for index, pad in enumerate(fp.children("pad")):
            local = list(map(float, pad.child("at").atoms()[1:]))
            dx, dy = rotate(*local[:2], angle)
            center = [at[0]-100+dx, at[1]-100+dy]
            local_angle = local[2] if len(local) > 2 else 0
            layers = pad.child("layers").atoms()[1:]
            copper = [layer for layer in ("F.Cu", "B.Cu") if layer in layers or "*.Cu" in layers]
            data = {
                "id": f"{ref}.{pad.atoms()[1]}#{index}", "reference": ref, "number": pad.atoms()[1],
                "net": pad.value("net"), "shape": pad.atoms()[3], "center": center,
                "size": point(pad.child("size")), "angle_deg": angle+local_angle, "layers": copper,
                "paste_layers": [layer for layer in layers if layer.endswith(".Paste")],
                "local_pad_rotation_deg": local_angle, "footprint_rotation_deg": angle,
            }
            if data["shape"] == "custom":
                polygons = []
                for primitive in pad.child("primitives").children():
                    require(primitive.head == "gr_poly", "Unimplemented custom copper primitive")
                    polygon = []
                    for vertex in primitive.child("pts").children("xy"):
                        dx, dy = rotate(*point(vertex), angle+local_angle)
                        polygon.append([center[0]+dx, center[1]+dy])
                    polygons.append(polygon)
                data["polygons"] = polygons
            if copper:
                pads.append(data)
            drill = pad.child("drill")
            if drill:
                values = [float(a) for a in drill.atoms()[1:] if a != "oval"]
                holes.append({"id": data["id"], "shape": "rect" if "oval" in drill.atoms() else "circle",
                              "center": center, "angle_deg": angle+local_angle,
                              "size": values if len(values) == 2 else values*2})
    return pads, holes


def contact_metal_reservations(contact):
    primitives = contact["right_contact_original_primitives"]
    reservations = []
    for ref, sign, net in (("BT1", 1, "VBAT"), ("BT2", -1, "/CELL_NEG")):
        for i, item in enumerate([*primitives["base_tabs"], primitives["under_cell_base"]]):
            reservations.append({
                "id": f"{ref}.conductive-base-{i}", "net": net, "shape": "rect", "angle_deg": 0,
                "center": [sign*(item["x_min"]+item["x_max"])/2, 0],
                "size": [item["x_max"]-item["x_min"], item["y_width"]],
                "basis": "Actual retained thin-primitives base metal projection, not a new keepout footprint",
            })
    return reservations


def via_rejections(xy, net, pads, holes, metal, outline, diameter, drill, clearance, hole_clearance, allow_in_pad=False):
    reasons = []
    if polygon_distance(xy, outline) != 0:
        reasons.append("outside-board")
    edge_gap = min(point_segment_distance(xy, a, b) for a, b in zip(outline, outline[1:]+outline[:1]))
    if edge_gap < diameter/2+.25:
        reasons.append("working-0.25mm-edge-reserve")
    for pad in pads:
        separation = geometry_distance(xy, pad)
        if pad["net"] != net and separation < diameter/2+clearance-1e-9:
            reasons.append("copper:"+pad["id"])
        elif not allow_in_pad and separation < diameter/2+.1-1e-9:
            reasons.append("avoid-via-in-smd-land:"+pad["id"])
    for hole in holes:
        if geometry_distance(xy, hole) < diameter/2+hole_clearance-1e-9:
            reasons.append("hole:"+hole["id"])
    for region in metal:
        if geometry_distance(xy, region) < diameter/2+clearance-1e-9:
            reasons.append("B-contact-base-metal:"+region["id"])
    return sorted(set(reasons))


def screen_candidate_segment(a, b, layer, net, pads, holes, metal, width, clearance, hole_clearance):
    length = math.dist(a, b)
    intervals = max(1, math.ceil(length/.02))
    # The extra half-step covers the distance-function change between samples.
    slack = length/intervals/2
    for i in range(intervals+1):
        xy = [a[axis]+(b[axis]-a[axis])*i/intervals for axis in (0, 1)]
        for pad in pads:
            if layer in pad["layers"] and pad["net"] != net:
                require(geometry_distance(xy, pad) >= width/2+clearance+slack,
                        "Proposed minimum-width corridor crosses "+pad["id"])
        for hole in holes:
            require(geometry_distance(xy, hole) >= width/2+hole_clearance+slack, "Proposed corridor crosses drill")
        if layer == "B.Cu":
            require(all(geometry_distance(xy, body) >= width/2+clearance+slack for body in metal),
                    "Proposed corridor enters unqualified contact base")


def critical_connections(pads):
    lookup = {}
    for pad in pads:
        lookup.setdefault((pad["reference"], pad["number"]), []).append(pad)
    groups = []
    definitions = [
        ("mcu-local-supplies", "Local logic geometry only; not a whole-rail current rating", [
            ("IC1", "1", "C9", "1"), ("IC1", "10", "C12", "1"),
            ("IC1", "22", "C14", "1"), ("IC1", "33", "C11", "1"),
            ("IC1", "42", "C15", "1"), ("IC1", "43", "C13", "1"),
            ("IC1", "44", "C17", "1"), ("IC1", "44", "C15", "1"),
            ("IC1", "48", "C17", "1"), ("IC1", "49", "C17", "1"),
            ("IC1", "45", "C8", "1"), ("IC1", "23", "C18", "2"),
            ("IC1", "50", "C6", "2"), ("C8", "1", "C6", "2"),
            ("C8", "1", "C18", "2"), ("C8", "1", "C7", "2"),
            ("U1", "8", "C10", "1"), ("U1", "4", "C10", "2"), ("U1", "PAD", "U1", "4"),
        ]),
        ("crystal-and-qspi", "Signal geometry; no impedance/timing approval", [
            ("IC1", "20", "Y1", "3"), ("Y1", "3", "C2", "2"),
            ("IC1", "21", "R6", "2"), ("R6", "1", "Y1", "1"), ("Y1", "1", "C3", "2"),
            ("IC1", "51", "U1", "7"), ("IC1", "52", "U1", "6"),
            ("IC1", "53", "U1", "5"), ("IC1", "54", "U1", "3"),
            ("IC1", "55", "U1", "2"), ("IC1", "56", "U1", "1"), ("U1", "1", "R5", "1"),
            ("IC1", "46", "R9", "2"), ("IC1", "47", "R10", "2"),
        ]),
        ("boost-power-loop", "High-current widths/copper areas NOT selected by this preparation", [
            ("L1", "P$2", "U5", "5"), ("U5", "3", "C26", "1"), ("L1", "P$1", "C26", "1"),
            ("U5", "4", "C26", "2"), ("U5", "6", "C27", "1"), ("U5", "6", "C28", "1"),
            ("U5", "4", "C27", "2"), ("U5", "4", "C28", "2"),
            ("U5", "1", "R23", "2"), ("U5", "1", "R24", "1"),
            ("R23", "1", "C27", "1"), ("R24", "2", "C27", "2"),
        ]),
        ("amplifier-power-and-btl", "Local bypass then thermal return; symmetric outward BTL routing required", [
            ("U4", "7", "U4", "8"), ("U4", "7", "C16", "1"), ("U4", "8", "C19", "1"),
            ("U4", "THERMAL", "U4", "3"), ("U4", "THERMAL", "U4", "11"),
            ("U4", "THERMAL", "U4", "15"), ("C16", "2", "U4", "THERMAL"),
            ("C19", "2", "U4", "THERMAL"), ("U4", "9", "FB1", "1"), ("U4", "10", "FB2", "1"),
            ("FB1", "2", "C22", "1"), ("FB2", "2", "C21", "1"),
            ("FB1", "2", "J1", "1"), ("FB2", "2", "J1", "2"),
        ]),
        ("protection-sense-and-gates", "Kelvin-style VM/GND and VSS/CELL_NEG sensing; no alternate bypass", [
            ("U6", "5", "C30", "1"), ("U6", "5", "R25", "2"), ("U6", "4", "C30", "2"),
            ("U6", "6", "R26", "1"), ("R26", "2", "R27", "2"),
            ("U6", "3", "Q5", "B1"), ("U6", "2", "Q5", "B2"),
            ("Q5", "B1", "R28", "1"), ("Q5", "A1", "R28", "2"),
            ("Q5", "B2", "R29", "1"), ("Q5", "A2", "R29", "2"),
            ("Q5", "A1", "Q5", "C1"), ("Q5", "A2", "Q5", "C2"),
            ("Q5", "A2", "R27", "1"), ("Q5", "A1", "U6", "4"),
        ]),
        ("system-power-topology", "Physical corridors only: copper sizing/current/thermal/fault review still required", [
            ("BT2", "1", "Q5", "A1"), ("BT1", "1", "R25", "1"),
            ("BT1", "1", "C20", "1"), ("BT1", "1", "Q3", "3"),
            ("U5", "4", "R27", "2"), ("U4", "THERMAL", "R27", "2"),
            ("U3", "2", "R27", "2"), ("U2", "2", "R27", "2"),
            ("Q1", "3", "L1", "P$1"), ("U5", "6", "U4", "7"),
        ]),
    ]
    for name, scope, links in definitions:
        rows = []
        for ar, ap, br, bp in links:
            a, b = lookup[(ar, ap)][0], lookup[(br, bp)][0]
            require(a["net"] == b["net"] and a["net"], f"Routing intent would cross nets: {ar}.{ap} -> {br}.{bp}")
            rows.append({"from": a["id"], "to": b["id"], "net": a["net"],
                         "from_xy_mm": a["center"], "to_xy_mm": b["center"],
                         "straight_line_mm": round(math.dist(a["center"], b["center"]), 6),
                         "copper_width_mm": None, "path": None,
                         "note": "Endpoint intent only, not emitted traces or a collision-checked path"})
        groups.append({"name": name, "scope": scope, "connections": rows})
    rows = []
    for ref in ("BT1", "BT2"):
        a, b = lookup[(ref, "1")]
        rows.append({"from": a["id"], "to": b["id"], "net": a["net"],
                     "from_xy_mm": a["center"], "to_xy_mm": b["center"],
                     "straight_line_mm": round(math.dist(a["center"], b["center"]), 6),
                     "copper_width_mm": None, "path": None,
                     "note": "Account for BOTH physical lands; do not silently rely on fitted contact metal as a PCB routing jumper"})
    groups.append({"name": "battery-physical-land-pairs", "scope": "Same-pin duplicates remain real physical copper lands",
                   "connections": rows})
    return groups


def prepare():
    before = bindings()
    require(all(before.get(name) == digest for name, digest in EXPECTED.items()), "Published stage-1 hashes changed")
    native_binding = json.loads((PACKAGE / "reports" / "native-input-bindings.json").read_text())
    for name, value in native_binding["inputs"].items():
        path = Path(name) if Path(name).is_absolute() else ROOT / name
        require(digest(path) == value, "Stale published native input: "+name)
    for name, value in native_binding["reports"].items():
        require(digest(PACKAGE / "reports" / name) == value, "Published native report changed: "+name)
    manifest = json.loads((PACKAGE / "placement-manifest.json").read_text())
    contact = json.loads((PACKAGE / "battery-contact-interface.json").read_text())
    project = json.loads((PACKAGE / "handbell.kicad_pro").read_text())
    _, board = load(PACKAGE / "handbell.kicad_pcb")
    require(not any(board.children(kind) for kind in ("segment", "via", "zone")), "Preparation expects unrouted stage1")
    pads, holes = read_pads(board)
    metal = contact_metal_reservations(contact)
    classes = {c["name"]: c for c in project["net_settings"]["classes"]}
    ground_class = classes["power"]
    diameter, drill, clearance = ground_class["via_diameter"], ground_class["via_drill"], ground_class["clearance"]
    hole_clearance = project["board"]["design_settings"]["rules"]["min_hole_to_hole"]
    outline = manifest["board"]["outline_common_xy_mm"]
    blockers = [p for p in pads if p["reference"] in {"BT1", "BT2"}]
    thermal = []
    for ref, padnum, offsets in (
        ("IC1", "P$1", [(x, y) for x in (-.8, 0, .8) for y in (-.8, 0, .8)]),
        ("U4", "THERMAL", [(x, y) for x in (-.325, .325) for y in (-.325, .325)]),
    ):
        land = next(p for p in pads if p["reference"] == ref and p["number"] == padnum)
        for dx, dy in offsets:
            xy = [round(land["center"][0]+dx, 6), round(land["center"][1]+dy, 6)]
            reasons = via_rejections(xy, "GND", pads, holes, metal, outline, diameter, drill, clearance,
                                     hole_clearance, allow_in_pad=True)
            require(not reasons, f"Unsafe proposed {ref} ground/thermal via at {xy}: {reasons}")
            require(abs(dx)+diameter/2 <= land["size"][0]/2 and abs(dy)+diameter/2 <= land["size"][1]/2,
                    "Thermal via annulus exceeds source ground land")
            thermal.append({"reference": ref, "xy_mm": xy, "net": "GND", "layers": ["F.Cu", "B.Cu"],
                            "diameter_mm": diameter, "drill_mm": drill,
                            "contact_copper_gap_mm": round(min(geometry_distance(xy, p)-diameter/2 for p in blockers), 6),
                            "status": "Geometric candidate only; via-in-pad fill/tent/stencil/thermal qualification unresolved"})
    for i, a in enumerate(thermal):
        for b in thermal[i+1:]:
            require(math.dist(a["xy_mm"], b["xy_mm"])-drill >= hole_clearance-1e-9,
                    "Candidate drill-to-drill clearance failure")
    fet_pads = {p["number"]: p for p in pads if p["reference"] == "Q5"}
    fet_vias = []
    for number, dx, dy in (("A1", -.7, .075), ("C1", .7, .075), ("A2", -.7, -.325), ("C2", .7, -.325)):
        pad = fet_pads[number]
        xy = [round(pad["center"][0]+dx, 6), round(pad["center"][1]+dy, 6)]
        size, bore = classes["Default"]["via_diameter"], classes["Default"]["via_drill"]
        failures = via_rejections(xy, pad["net"], pads, holes, metal, outline, size, bore, clearance, hole_clearance)
        require(not failures, f"Q5 outside fanout candidate blocked: {number}: {failures}")
        fet_vias.append({"pad": pad["id"], "pad_xy_mm": pad["center"], "via_xy_mm": xy, "net": pad["net"],
                         "diameter_mm": size, "drill_mm": bore,
                         "status": "Outside-ball-field candidate, NOT an approved current-carrying via count or width"})
    fet_buses = [{"net": fet_vias[a]["net"], "layer": "B.Cu",
                  "candidate_polyline_xy_mm": [fet_vias[a]["via_xy_mm"], fet_vias[b]["via_xy_mm"]],
                  "copper_width_mm": None, "note": "Same SOURCE bus behind F-only gate; no common-drain pad exists"}
                 for a, b in ((0, 1), (2, 3))]
    minimum_width = project["board"]["design_settings"]["rules"]["min_track_width"]
    for candidate in fet_vias:
        screen_candidate_segment(candidate["pad_xy_mm"], candidate["via_xy_mm"], "F.Cu", candidate["net"],
                                 pads, holes, metal, minimum_width, clearance, hole_clearance)
        candidate["F_stub_screen"] = {"geometric_screen_width_mm": minimum_width,
                                     "scope": "Inherited minimum-width feasibility only; NOT a chosen power width"}
    for candidate in fet_buses:
        screen_candidate_segment(*candidate["candidate_polyline_xy_mm"], "B.Cu", candidate["net"],
                                 pads, holes, metal, minimum_width, clearance, hole_clearance)
        candidate["geometric_screen_width_mm"] = minimum_width
        candidate["current_capacity_qualification"] = False
    all_candidates = [{"xy": p["xy_mm"], "diameter": p["diameter_mm"], "drill": p["drill_mm"], "net": p["net"]}
                      for p in thermal]
    all_candidates += [{"xy": p["via_xy_mm"], "diameter": p["diameter_mm"], "drill": p["drill_mm"], "net": p["net"]}
                       for p in fet_vias]
    for i, a in enumerate(all_candidates):
        for b in all_candidates[i+1:]:
            gap = math.dist(a["xy"], b["xy"])
            require(gap-(a["drill"]+b["drill"])/2 >= hole_clearance-1e-9, "Candidate hole spacing")
            if a["net"] != b["net"]:
                require(gap-(a["diameter"]+b["diameter"])/2 >= clearance-1e-9, "Candidate via net conflict")
    examples = []
    for xy in ([0, 0], [1.3, 0], [-1.3, 0], [3.62, 0], [-3.62, 0], [10, 0], [-10, 0]):
        failures = via_rejections(xy, "GND", pads, holes, metal, outline, diameter, drill, clearance,
                                  hole_clearance, allow_in_pad=True)
        examples.append({"xy_mm": xy, "accepted": not failures, "rejections": failures})
    require(examples[0]["accepted"] and all(not item["accepted"] for item in examples[1:]),
            "Raw-contact ground-via regression cases failed")
    ground_stubs = []
    offsets = [(r*math.cos(a*math.pi/8), r*math.sin(a*math.pi/8))
               for r in (.8, 1.0, 1.2, 1.5, 1.8, 2.0) for a in range(16)]
    for pad in pads:
        if not pad["reference"].startswith("C") or pad["net"] != "GND":
            continue
        candidates = []
        for dx, dy in offsets:
            xy = [round(pad["center"][0]+dx, 6), round(pad["center"][1]+dy, 6)]
            if not via_rejections(xy, "GND", pads, holes, metal, outline, diameter, drill, clearance, hole_clearance):
                candidates.append(xy)
        chosen = candidates[0] if candidates else None
        ground_stubs.append({"pad": pad["id"], "pad_xy_mm": pad["center"], "candidate_xy_mm": chosen,
                             "straight_line_stub_mm": round(math.dist(pad["center"], chosen), 6) if chosen else None,
                             "status": "Point screened; F stub path NOT checked" if chosen else
                                       "No screened off-pad GND via within2mm: design F return to safe bank/thermal corner, do not drill into B contacts"})
    labels = [
        {"text": "+ POS", "center_mm": [11, 10.5], "size_mm": [5, 1.2], "native_angle_deg": 0, "mirror": True},
        {"text": "- NEG", "center_mm": [-11, 10.5], "size_mm": [5, 1.2], "native_angle_deg": 0, "mirror": True},
        {"text": "T8 BUTTON END >", "center_mm": [0, 10.5], "size_mm": [11, 1.0], "native_angle_deg": 0, "mirror": True},
    ]
    for label in labels:
        cx, cy = label["center_mm"]
        w, h = label["size_mm"]
        # Densely sample the entire text reservation, not just its center.
        for i in range(math.ceil(w/.1)+1):
            for j in range(math.ceil(h/.1)+1):
                xy = [cx-w/2+min(i*.1, w), cy-h/2+min(j*.1, h)]
                require(polygon_distance(xy, outline) == 0, "Polarity mark exceeds substrate")
                require(all(geometry_distance(xy, p) >= .5 for p in pads if "B.Cu" in p["layers"]),
                        "Polarity marking too close to B copper")
                require(all(geometry_distance(xy, p) >= .5 for p in metal), "Polarity mark concealed by contact base")
                require(all(math.dist(xy, [m["x_mm"], m["y_mm"]]) >= m["keepout_radius_mm"]
                            for m in manifest["mounting_holes"]), "Polarity mark enters mounting keepout")
        label.update(layer="B.SilkS", thickness_mm=.15, role="Future silk only, no footprint/pad movement",
                     visibility_gate="Mechanical consumer must confirm visible in service state; rear-view rendering must confirm readable mirroring")
    result = {
        "status": "READ-ONLY PREPARATION; parent copper release absent; no candidate/native PCB emitted",
        "published_stage1_commit": PUBLISHED_COMMIT, "published_stage1_hashes": EXPECTED,
        "source_bindings": before, "preparation_script_sha256": digest(Path(__file__)),
        "coordinate_frame": "Centered common assembly XY; preserve actual KiCad10 footprint PLUS local pad rotation",
        "inherited_rules": project["board"]["design_settings"]["rules"], "inherited_netclasses": classes,
        "width_policy": "Inherited netclass names/widths are provenance, NOT current/thermal qualification. "
                        "Signal geometry may start at existing0.2mm; high-current copper widths/areas remain explicitly unselected.",
        "layer_policy": "F.Cu and B.Cu only. No ground-plane continuity assumed across contact exclusions.",
        "B_raw_contact_pad_geometry": blockers, "B_contact_base_metal_reservations": metal,
        "B_ground_zone_policy": {
            "net": "GND", "status": "Planning only; zero zones emitted",
            "exclude": "Both VBAT and CELL_NEG contact pads plus conductive base projections, expanded by0.2mm; "
                       "all other different-net pads/tracks, holes and native clearances still apply",
            "bare_inner_contact_pad_gap_mm": 3.0, "ground_copper_corridor_width_after_clearance_mm": 2.6,
            "ground_via_center_x_range_in_contact_row_mm": [-1.5+diameter/2+clearance, 1.5-diameter/2-clearance],
            "required_checks": ["Keep both raw contact nets and base metal out of GND, not just CELL_NEG",
                                "Fill then inspect actual islands/necks; prove every retained GND pad connected",
                                "Do not use the central neck as an assumed qualified boost/amplifier current return",
                                "Route deliberate high-current F return corridors to R27.2; Kelvin-style R26.2 also ends there",
                                "No stitch via through raw contact pads, metal bases or contact keepouts"],
        },
        "thermal_via_candidates": thermal, "ground_via_negative_tests": examples,
        "Q5_source_fanout_candidates": fet_vias, "Q5_source_bus_candidates": fet_buses,
        "critical_obstacle_notes": [
            "Q5 A1/C1 share SOURCE1 but B1 gate lies between them; A2/C2 share SOURCE2 with B2 between. "
            "A straight F source-to-source segment would short a gate. Use outside F fanouts and separate B source buses, "
            "or another actually checked escape; do not invent a PCB common-drain pad.",
            "Q5 adjacent circular-land gap is0.35mm; inherited minimum track0.1778 plus two0.2mm clearances requires0.5778mm. "
            "Do not pretend an inner inter-ball channel is routable with these rules.",
            "C2/C3 oscillator returns have raw-negative/base projections below them, not an uninterrupted GND reference. "
            "Plan a local F guard/return to IC1.19/thermal GND, keeping Y1.2/Y1.4 unassigned.",
            "Right-side MCU supply capacitors cannot indiscriminately receive ground vias: VBAT pad/base metal is directly behind them. "
            "Use checked F corner-return geometry toward the central safe GND bank, or safe outside vias with actually routed returns.",
            "The C10/flash return must not assume GND beneath the positive contact base; avoid unreviewed B QSPI return discontinuities.",
        ],
        "capacitor_ground_via_candidates": ground_stubs,
        "critical_routing_groups": critical_connections(pads), "back_polarity_silkscreen_candidates": labels,
        "release_gate": {
            "released": False, "copper_writer_enabled": False,
            "required_before_apply": ["Separate explicit parent copper-release instruction",
                                      "Mechanical review/report exact path and SHA256 binding this exact stage1 manifest/contact/PCB",
                                      "Reviewed mounts, USB insertion/removal, contact insulation/capture and actual service paths",
                                      "Deliberate signal and high-current route geometry choices, without declaring qualification",
                                      "Gated candidate writer preserving all footprint/pad/net/rule/interface bytes"],
            "not_authorization": ["This generated plan", "The published stage1 commit", "Earlier fit feedback",
                                  "An arbitrary file named release.json"],
        },
        "unclosed_gates": ["No reverse-cell circuit, temperature charge inhibit or charge safety timer",
                           "Unchanged charge/termination profile is not approved for the supplied T8",
                           "Fault SOA, contact/load current, thermal behavior and complete manufacturing process unqualified",
                           "Four original USB hole-clearance findings and all pad/library transforms must remain unchanged",
                           "No Gerbers, purchase, fabrication or live-cell authorization"],
    }
    require(before == bindings(), "Published package changed during read-only preparation")
    (HERE / "routing-preparation.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    draw(result, outline)
    require(before == bindings(), "Preparation modified a published stage1 artifact")
    missing = [p["pad"] for p in ground_stubs if p["candidate_xy_mm"] is None]
    print(json.dumps({"status": result["status"], "plan_sha256": digest(HERE / "routing-preparation.json"),
                      "thermal_candidates": dict(Counter(p["reference"] for p in thermal)),
                      "outside_Q5_source_via_candidates": len(fet_vias),
                      "critical_connection_intents": sum(len(g["connections"]) for g in result["critical_routing_groups"]),
                      "capacitor_returns_needing_F_solution": missing, "published_bytes_unchanged": True}, indent=2))


def draw(result, outline):
    scale, cx, cy = 14, 430, 480
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1240" height="950" viewBox="0 0 1240 950">',
           '<rect width="1240" height="950" fill="white"/><g font-family="sans-serif">',
           '<text x="25" y="35" font-size="23">Routing PREPARATION — B contact exclusions and proposed GND vias</text>']
    pts = " ".join(f"{cx+x*scale:.3f},{cy-y*scale:.3f}" for x, y in outline)
    svg.append(f'<polygon points="{pts}" fill="#eff6ff" stroke="#334155"/>')
    for region in [*result["B_contact_base_metal_reservations"], *result["B_raw_contact_pad_geometry"]]:
        x, y = region["center"]
        w, h = region["size"]
        color = "#fca5a5" if region["net"] == "/CELL_NEG" else "#fdba74"
        svg.append(f'<rect x="{cx+(x-w/2)*scale:.3f}" y="{cy-(y+h/2)*scale:.3f}" width="{w*scale:.3f}" height="{h*scale:.3f}" fill="{color}" stroke="#7c2d12" fill-opacity=".7"/>')
    for via in result["thermal_via_candidates"]:
        x, y = via["xy_mm"]
        svg.append(f'<circle cx="{cx+x*scale:.3f}" cy="{cy-y*scale:.3f}" r="{via["diameter_mm"]*scale/2:.3f}" fill="#22c55e" stroke="#14532d"/>')
    for proposed in result["capacitor_ground_via_candidates"]:
        xy = proposed["candidate_xy_mm"] or proposed["pad_xy_mm"]
        x, y = xy
        color = "#2563eb" if proposed["candidate_xy_mm"] else "#be123c"
        svg.append(f'<circle cx="{cx+x*scale:.3f}" cy="{cy-y*scale:.3f}" r="3" fill="{color}"/>')
        svg.append(f'<text x="{cx+x*scale+5:.3f}" y="{cy-y*scale:.3f}" font-size="9" fill="{color}">{html.escape(proposed["pad"].split(".")[0])}</text>')
    for label in result["back_polarity_silkscreen_candidates"]:
        x, y = label["center_mm"]
        svg.append(f'<text x="{cx+x*scale}" y="{cy-y*scale}" text-anchor="middle" font-size="12">{html.escape(label["text"])}</text>')
    notes = [
        "Orange: VBAT pad/base metal",
        "Red: CELL_NEG pad/base metal",
        "Green: thermal-via candidates",
        "Blue: nearby GND-via candidates",
        "Crimson: no sampled via within2mm",
        "All F/B copper and drill obstacles checked.",
        "Via/stub PATHS are not routed or checked.",
        "Filled/tented via process remains open.",
        "B GND central neck is only2.6mm.",
        "No current/thermal rating follows.",
        "No ground stitch into EITHER contact net.",
        "Ground zone has NOT been created.",
        "Common XY (+Y up), not a rear photo.",
        "Silk text will require native B mirroring.",
        "No copper-release instruction received.",
    ]
    for i, text in enumerate(notes):
        svg.append(f'<text x="790" y="{160+i*35}" font-size="14">{html.escape(text)}</text>')
    svg += ['<text x="25" y="910" font-size="16">Prepared from immutable stage1 pad geometry; all native files, manifests and native bindings untouched.</text>',
            '</g></svg>']
    (HERE / "routing-preparation.svg").write_text("\n".join(svg)+"\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Intentionally unavailable until explicit parent copper release")
    args = parser.parse_args()
    if args.apply:
        parser.error("COPPER RELEASE ABSENT: preparation has no native writer. Separate parent release and reviewed implementation required.")
    prepare()


if __name__ == "__main__":
    main()
