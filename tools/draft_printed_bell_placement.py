# SPDX-License-Identifier: MIT
"""Separate September 13 front-electronics floorplan. Never route or rewrite T8."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import csv
import hashlib
import html
import json
import math
from pathlib import Path
import random
import shutil
import xml.etree.ElementTree as ET

import draft_t8_placement as t8
import draft_wing_placement as wing
import place_handbell as base
from kicad_sexpr import apply_edits, load, loads
from placement_geometry import footprint_bounds

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "hardware" / "handbell" / "iterations" / "t8-protected-draft"
OUTPUT = SOURCE.parent / "printed-bell-front"
INPUT = ROOT / "docs" / "design-inputs" / "2026-09-13-printed-bell.json"
CLI = t8.CLI
FRONT, BACK, DIAMETER = 25.0, 26.6, 43.0
CONTACTS = {"BT1", "BT2"}
sha = t8.sha
write = t8.write

# Native footprint origins and KiCad angles, in centered assembly XY.
# These are electrical groups, not freely interchangeable packing rectangles.
POSES = {
    "core": {
        "IC1": (0, 0, 270), "U1": (6.3, -3.3, 90),
        "Y1": (-6.9, -2.0, 90), "C2": (-9.1, -3.1, 90),
        "C3": (-9.1, -.8, 270), "R6": (-4.95, -.8, 90),
        "C14": (-5.15, 2.3, 180), "C18": (-5.15, 1.0, 0),
        "C9": (2.6, -5.15, 90), "C12": (-1, -5.15, 90),
        "C10": (5.3, -6.2, 90), "C6": (5.5, -.4, 180),
        "C7": (7.8, 2.2, 180), "C8": (5.5, 2.2, 0),
        "C13": (5.5, 3.5, 0), "C17": (5.5, .9, 0),
        "C15": (2.6, 5.15, 270), "C11": (-1, 5.15, 270),
        "R5": (7.0, -6.3, 90), "R9": (8.1, .2, 180),
        "R10": (8.1, -1.1, 180),
    },
    "boost": {
        "U5": (-4.2, 16, 0), "L1": (0, 16, 180),
        "C26": (-4.2, 18.4, 0), "C27": (-7.2, 15.8, 270),
        "C28": (-9.4, 15.8, 270), "R23": (-4.2, 13.8, 180),
        "R24": (-4.2, 12.6, 0), "C29": (-6.6, 12.1, 0),
    },
    "amplifier": {
        "U4": (11, -10, 0),         "C16": (11.5, -7.0, 0),
        "C19": (14.1, -7.1, 0), "R18": (8.0, -9.0, 90),
        "FB1": (14.5, -10, 0), "FB2": (14.5, -12.1, 0),
        "C22": (17, -9.3, 90), "C21": (16.9, -11.4, 90),
        "Q4": (10.5, -13.8, 0), "R20": (8, -12.7, 90),
    },
    "imu": {
        "IC4": (-10.5, -6, 270), "C23": (-10.7, -8.5, 0),
        "C24": (-8, -6, 90), "R14": (-12.9, -5.3, 90),
        "R15": (-12.9, -7.3, 90),
    },
    "protection": {
        "U6": (-11.5, 7.35, 0), "Q5": (-14.4, 7.35, 90),
        "C30": (-11.6, 5.55, 0), "R25": (-11.6, 9.35, 0),
        "R26": (-14.6, 5.55, 0), "R27": (-14.6, 9.55, 0),
        "R28": (-17.2, 6.75, 90), "R29": (-17.2, 9.35, 90),
    },
    "logic-power": {
        "U2": (-16, -6, 180), "C4": (-16, -9.5, 0),
        "C5": (-16, -2.5, 0), "R3": (-18.4, -6.2, 90),
    },
    "charger": {
        "U3": (2, -16, 90), "C20": (5.5, -16.5, 90),
        "R8": (5.7, -13.5, 0), "CHG_EN0": (2, -18.6, 0),
        "CHG0": (6.5, -18.7, 90), "R2": (4.5, -18.7, 0),
    },
    "source-selection": {
        "Q3": (-2, -11.5, 90), "D4": (-2, -8.5, 0),
        "C1": (-4, -13.8, 90), "R4": (.2, -11.5, 90),
    },
    "audio-switch": {
        "Q1": (-18, 1.3, 0), "Q2": (-13.5, 1.3, 0),
        "R16": (-16.5, 3.8, 0), "R17": (-13.5, -1.5, 0),
    },
    "interfaces": {
        "X6": (0, -22.82, 180), "J1": (16.5, -1, 90),
        "J2": (14, 8, 0), "BT1": (11.625, 0, 0),
        "BT2": (-11.625, 0, 180),
    },
}
ANCHORS = {
    "C25": (5, 7.5, 0), "R21": (3, 7.5, 0), "R22": (8, 7.5, 0),
    "R1": (-4.5, 5, 90), "R11": (5, -8, 0), "D3": (8, -7, 90),
    "L0": (-5, 9, 0), "R7": (-3, 8, 0),
    "R12": (5.5, -19.5, 90), "R13": (-5.5, -19.5, 90),
}


def local_libraries():
    libraries = dict(base.LIBRARIES)
    libraries["T8"] = SOURCE / "T8.pretty"
    libraries["MountingHole"] = base.STANDARD / "MountingHole.pretty"
    libraries["Connector_Molex"] = base.STANDARD / "Connector_Molex.pretty"
    libraries["Connector_JST"] = base.STANDARD / "Connector_JST.pretty"
    libraries["Jumper"] = base.STANDARD / "Jumper.pretty"
    return libraries


def seed_package():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "reports").mkdir(exist_ok=True)
    for name in ("handbell.kicad_sch", "handbell.kicad_pro", "LICENSE.txt", "T8.kicad_sym"):
        shutil.copyfile(SOURCE / name, OUTPUT / name)
    shutil.copyfile(ROOT / "hardware" / "handbell" / "Handbell.kicad_sym", OUTPUT / "Handbell.kicad_sym")
    shutil.copytree(SOURCE / "notices", OUTPUT / "notices", dirs_exist_ok=True)
    _, pcb = load(SOURCE / "handbell.kicad_pcb")
    used = {}
    for fp in pcb.children("footprint"):
        lib, name = fp.atoms()[1].split(":", 1)
        used.setdefault(lib, set()).add(name)
    entries = []
    for lib, names in sorted(used.items()):
        directory = local_libraries().get(lib, base.STANDARD / (lib + ".pretty"))
        dest = OUTPUT / "libraries" / (lib + ".pretty")
        dest.mkdir(parents=True, exist_ok=True)
        for name in sorted(names):
            shutil.copyfile(directory / (name + ".kicad_mod"), dest / (name + ".kicad_mod"))
        entries.append(f'(lib (name {json.dumps(lib)}) (type "KiCad") '
                       f'(uri "${{KIPRJMOD}}/libraries/{lib}.pretty") (options "") (descr "Exact retained source lands"))')
    write(OUTPUT / "fp-lib-table", '(fp_lib_table (version 7)\n' + "\n".join(entries) + "\n)\n")
    write(OUTPUT / "sym-lib-table", '(sym_lib_table (version 7)\n'
          '(lib (name "Handbell") (type "KiCad") (uri "${KIPRJMOD}/Handbell.kicad_sym") (options "") (descr ""))\n'
          '(lib (name "T8") (type "KiCad") (uri "${KIPRJMOD}/T8.kicad_sym") (options "") (descr ""))\n)\n')
    shutil.copyfile(INPUT, OUTPUT / "design-input-snapshot.json")


def read_parts():
    text, sch = load(SOURCE / "handbell.kicad_sch")
    symbols = {s.properties()["Reference"]: s for s in sch.children("symbol")
               if s.value("unit") == "1" and not s.properties()["Reference"].startswith("#")}
    xml = ET.parse(SOURCE / "reports" / "handbell-netlist.xml").getroot()
    old = json.loads((SOURCE / "placement-manifest.json").read_text())
    prior = {p["reference"]: p for p in old["components"]}
    _, board = load(SOURCE / "handbell.kicad_pcb")
    fps = {fp.properties()["Reference"]: fp for fp in board.children("footprint")}
    parts = {}
    for comp in xml.findall("components/comp"):
        ref, identifier = comp.get("ref"), comp.findtext("footprint")
        lib, name = identifier.split(":", 1)
        raw_text, fp = load(OUTPUT / "libraries" / (lib + ".pretty") / (name + ".kicad_mod"))
        raw, planning, courtyard = footprint_bounds(fp)
        if ref == "J2":
            raw[3] += .7
            planning[3] = max(planning[3], raw[3]+.25)
        cx, cy = (raw[0]+raw[2])/2, (raw[1]+raw[3])/2
        at = list(map(float, fps[ref].child("at").atoms()[1:]))
        side = "B" if ref in CONTACTS else "F"
        dx, dy = base.rotate(cx, -cy if side == "B" else cy, at[2])
        p = {"ref": ref, "value": comp.findtext("value"), "footprint": identifier, "text": raw_text,
             "fields": {**symbols[ref].properties(),
                        **{f.get("name"): f.text or "" for f in comp.findall("fields/field")}},
             "raw_cx": cx, "raw_cy": cy, "raw_w": raw[2]-raw[0], "raw_h": raw[3]-raw[1],
             "plan_w": 2*max(cx-planning[0], planning[2]-cx),
             "plan_h": 2*max(cy-planning[1], planning[3]-cy),
             "has_courtyard": courtyard, "height": prior.get(ref, {}).get("height_mm", 0),
             "side": side, "dnp": ref == "C29", "copper_only": ref in base.COPPER,
             "x": at[0]-100+dx, "y": at[1]-100+dy, "angle": at[2],
             "cluster": None, "old_native_pose": at, "old_side": fps[ref].value("layer")[0]}
        parts[ref] = p
    for cluster, poses in POSES.items():
        for ref, pose in poses.items():
            set_origin(parts[ref], *pose)
            parts[ref]["cluster"] = cluster
    for ref, pose in ANCHORS.items():
        set_origin(parts[ref], *pose)
    for i, ref in enumerate(sorted(base.COPPER - {"CHG_EN0"})):
        a = i*2*math.pi/17
        set_origin(parts[ref], 18*math.cos(a), 18*math.sin(a), 0)
    set_origin(parts["GAIN0"], 0, 9, 0)
    for p in parts.values():
        p["anchor_x"], p["anchor_y"] = p["x"], p["y"]
    return parts, xml, symbols, sch


def set_origin(p, x, y, angle):
    dx, dy = base.rotate(p["raw_cx"], -p["raw_cy"] if p["side"] == "B" else p["raw_cy"], angle)
    p.update(x=x+dx, y=y+dy, angle=angle)


def origin(p):
    dx, dy = base.rotate(p["raw_cx"], -p["raw_cy"] if p["side"] == "B" else p["raw_cy"], p["angle"])
    return [round(p["x"]-dx, 6), round(p["y"]-dy, 6), p["angle"]]


def constraint(p):
    if p["ref"] in CONTACTS | {"X6"}:
        return 0
    w, h = base.dimensions(p)
    cost = max(0, math.hypot(abs(p["x"])+w/2, abs(p["y"])+h/2)-(DIAMETER/2-.25))**2
    for mount in wing.MOUNTS:
        cost += max(0, 3.2-wing.rectangle_distance(p, mount["x_mm"], mount["y_mm"]))**2
    if not p["copper_only"] and not p["dnp"] and p["height"] >= FRONT-23.5:
        # D21.70 magnet, plus a declared 0.25 mm planning separation.
        cost += max(0, 11.1-wing.rectangle_distance(p, 0, 0))**2
    return cost


def overlap(a, b):
    return base.pair_overlap(a, b) if a["side"] == b["side"] else 0


def plan_report(parts):
    rows = list(parts.values())
    return {
        "constraint_violations": [{"reference": p["ref"], "penalty": constraint(p)}
                                 for p in rows if constraint(p) > .000001],
        "planning_overlaps": [{"left": a["ref"], "right": b["ref"], "area_mm2": overlap(a, b)}
                              for i, a in enumerate(rows) for b in rows[i+1:] if overlap(a, b) > .000001],
        "scope": "All footprint/drawing planning rectangles checked, including intracluster pairs. Not a router.",
    }


def optimize(parts, steps):
    rng = random.Random(13092026)
    rows = list(parts.values())
    movable = [p for p in rows if p["cluster"] != "interfaces" and p["ref"] != "IC1"]
    def cost(p):
        displacement = math.hypot(p["x"]-p["anchor_x"], p["y"]-p["anchor_y"])
        limit = 1.2 if p["cluster"] == "core" else 2.5 if p["cluster"] else 30
        return (400*constraint(p) + 150*sum(overlap(p, q) for q in rows if p is not q)
                + 800*max(0, displacement-limit)**2
                + (.3 if p["cluster"] else .015)*displacement**2)
    for i in range(steps):
        p = rng.choice(movable)
        before, old = cost(p), (p["x"], p["y"], p["angle"])
        f = i/max(steps, 1)
        scale = 1.2*(1-f)+.002
        p["x"] += rng.uniform(-scale, scale)
        p["y"] += rng.uniform(-scale, scale)
        if not p["cluster"] and rng.random() < .015:
            p["angle"] = (p["angle"]+90) % 360
        delta = cost(p)-before
        if delta > 0 and rng.random() >= math.exp(-delta/(.3*(1-f)**3+.000001)):
            p["x"], p["y"], p["angle"] = old
    # Finish with feasibility alone; anchor attraction must not buy a small collision.
    def feasibility(p):
        return constraint(p) + sum(overlap(p, q) for q in rows if p is not q)
    for i in range(30000 if steps else 0):
        p = rng.choice(movable)
        before = feasibility(p)
        if before == 0:
            continue
        old = p["x"], p["y"]
        scale = .08*(1-i/30000)+.00001
        p["x"] += rng.uniform(-scale, scale)
        p["y"] += rng.uniform(-scale, scale)
        if feasibility(p) >= before:
            p["x"], p["y"] = old


def build(parts, xml, symbols, sch, steps):
    source_text, board = load(SOURCE / "handbell.kicad_pcb")
    nets, info = {}, {}
    for net in xml.findall("nets/net"):
        for pin in net.findall("node"):
            nets.setdefault(pin.get("ref"), {})[pin.get("pin")] = net.get("name")
            info.setdefault(pin.get("ref"), {})[pin.get("pin")] = pin.attrib
    footprints = [wing.rendered_footprint(p, nets[p["ref"]], info[p["ref"]],
                                         sch.value("uuid"), symbols[p["ref"]].value("uuid"))
                  for p in parts.values()]
    # Keep exact T8 lands, mount poses, outline segments, rules and UUIDs.
    edits = []
    for fp in board.children("footprint"):
        if not fp.properties()["Reference"].startswith("MH"):
            edits.append((fp.start, fp.end, ""))
    title = board.child("title_block")
    edits.append((title.start, title.end, '(title_block '
                  '(title "Printed bell front electronics - FLOORPLAN ONLY") (rev "0.5-front-stage1") '
                  '(comment 1 "Adafruit-derived CC BY-SA 3.0; LICENSE.txt and notices"))'))
    edits.append((board.end-1, board.end-1, "\n"+"\n".join(footprints)+"\n"))
    write(OUTPUT / "handbell.kicad_pcb", apply_edits(source_text, edits))
    contacts = t8.contact_interface(FRONT)
    write(OUTPUT / "battery-contact-interface.json", json.dumps(contacts, indent=2)+"\n")
    old = json.loads((SOURCE / "placement-manifest.json").read_text())
    manifest = {key: copy.deepcopy(old[key]) for key in (
        "schema_version", "units", "board", "coordinate_convention", "mounting_holes",
        "usb_interface", "cross_face_keepouts", "dnp_footprint_reservations")}
    manifest["board"].update(front_z_mm=FRONT, back_z_mm=BACK, component_face="mixed",
                             electronic_component_face="F", rear_fitted_exceptions=["BT1", "BT2"])
    manifest.update(
        status="Stage 1 electrical floorplan only; no routing or mechanical interface release",
        generated_pcb_sha256=sha(OUTPUT / "handbell.kicad_pcb"),
        schematic_sha256=sha(OUTPUT / "handbell.kicad_sch"),
        baseline_pcb_sha256=sha(SOURCE / "handbell.kicad_pcb"),
        baseline_schematic_sha256=sha(SOURCE / "handbell.kicad_sch"),
        source_baseline=str(SOURCE.relative_to(ROOT)),
        preserved_reference_commit="fefa8bce4e02f1c6c216f7053fb5d7abb16f3d44",
        design_input_source=str(INPUT.relative_to(ROOT)), design_input_sha256=sha(INPUT),
        design_input_snapshot="design-input-snapshot.json",
        design_input_snapshot_sha256=sha(OUTPUT / "design-input-snapshot.json"),
        speaker_front_z_mm=4.5, speaker_basket_rear_z_mm=16.5, speaker_magnet_rear_z_mm=23.5,
        speaker_dimensions_mm={"overall_diameter": 40, "overall_height": 19,
                               "basket_rear_diameter": 32, "magnet_diameter": 21.70, "magnet_height": 7},
        speaker_screen={"envelope": "D40 to z16.5, D21.70 to z23.5; conservative stepped radial body",
                        "radial_planning_margin_mm": .25, "yoke_top_z_mm": 19.3,
                        "inductor_min_z_mm": 20.0, "inductor_yoke_axial_gap_mm": .7},
        battery_contact_interface="battery-contact-interface.json",
        battery_contact_interface_sha256=sha(OUTPUT / "battery-contact-interface.json"),
        battery_reservation={"cell_axis": "X", "diameter_mm": 16.4, "length_mm": 34.0,
                             "cell_center_z_mm": 36.38, "status": "Nominal, not tolerance/loaded-spring qualification"},
        components=[], copper_only_features=[], planning=plan_report(parts),
        placement_method="Manually defined electrically coupled front groups; seeded secondary/service optimization",
        electrical_landmarks={group: {ref: origin(parts[ref]) for ref in poses} for group, poses in POSES.items()},
        limits=["No tracks, vias or zones; no claim of continuity, thermal adequacy or route approval.",
                "No automatic cell-temperature charge inhibit, safety timer or reverse-cell protection.",
                "Retained MCP73831 charge/termination profile requires cell approval.",
                "Unselected inductor/capacitors/ferrites are not qualified by footprint or screening height.",
                "BT1/BT2 are fitted B SMT operations: no single-side-reflow or Economic-tier claim.",
                "USB anchors M1-M4 remain unassigned. Four inherited 0.25 mm hole-clearance findings remain.",
                "Final mechanics must bind this exact manifest before the separate routing stage."])
    manifest["usb_interface"].update(body_front_z_mm=21.5, body_back_z_mm=FRONT)
    for p in parts.values():
        x, y, angle = origin(p)
        if p["copper_only"]:
            manifest["copper_only_features"].append(
                {"reference": p["ref"], "x_mm": p["x"], "y_mm": p["y"], "side": p["side"]})
        elif not p["dnp"]:
            manifest["components"].append({
                "reference": p["ref"], "value": p["value"], "mpn": p["fields"].get("MPN", ""),
                "footprint": p["footprint"], "x_mm": p["x"], "y_mm": p["y"],
                "width_mm": p["raw_w"], "depth_mm": p["raw_h"], "height_mm": p["height"],
                "rotation_deg": -angle, "side": p["side"],
                "native_origin_common_xy_mm": [x, y],
                "z_min_mm": FRONT-p["height"] if p["side"] == "F" else BACK,
                "z_max_mm": FRONT if p["side"] == "F" else BACK+p["height"],
                "height_source": next(c["height_source"] for c in old["components"] if c["reference"] == p["ref"]),
                "proxy_kind": "dimensioned_contact_primitives" if p["ref"] in CONTACTS else "envelope",
                "geometry_interface": "battery-contact-interface.json" if p["ref"] in CONTACTS else None,
                "requires_shell_cutout": p["ref"] == "X6", "cluster": p["cluster"],
            })
    write(OUTPUT / "placement-manifest.json", json.dumps(manifest, indent=2)+"\n")
    movements = []
    for p in parts.values():
        previous = [round(p["old_native_pose"][0]-100, 6), round(p["old_native_pose"][1]-100, 6),
                    p["old_native_pose"][2]]
        current = origin(p)
        if previous != current or p["old_side"] != p["side"]:
            movements.append({"reference": p["ref"], "from_native_xy_angle": previous,
                              "to_native_xy_angle": current, "from_side": p["old_side"], "to_side": p["side"]})
    report = {"script_sha256": sha(__file__), "seed": 13092026, "steps": steps,
              "diameters_attempted_mm": [DIAMETER], "fitted_by_side": dict(Counter(c["side"] for c in manifest["components"])),
              "movements": movements, "planning": manifest["planning"],
              "generated_pcb_sha256": manifest["generated_pcb_sha256"]}
    write(OUTPUT / "placement-build-report.json", json.dumps(report, indent=2)+"\n")
    with (OUTPUT / "reports" / "footprint-movements.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(movements[0]))
        writer.writeheader()
        writer.writerows(movements)
    with (OUTPUT / "reports" / "bom-draft.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["Reference", "Value", "MPN", "Footprint", "Face", "Population", "Assembly_note"])
        for p in parts.values():
            population = "DNP" if p["dnp"] else "copper-only" if p["copper_only"] else "fitted"
            note = ("B-side SMT attachment operation; process/retention not qualified" if p["ref"] in CONTACTS
                    else "MPN/assembly qualification remains open" if not p["fields"].get("MPN") else "Not an order authorization")
            writer.writerow([p["ref"], p["value"], p["fields"].get("MPN", ""), p["footprint"], p["side"], population, note])
        for mount in wing.MOUNTS:
            writer.writerow([mount["reference"], "M2 GND mounting pad", "", "MountingHole:MountingHole_2.2mm_M2_Pad",
                             "through-board", "board-only mount", "Fasteners belong to mechanical BOM"])
    draw(manifest)
    protected = [OUTPUT / name for name in ("handbell.kicad_sch", "handbell.kicad_pro", "fp-lib-table",
                 "sym-lib-table", "Handbell.kicad_sym", "T8.kicad_sym", "placement-manifest.json",
                 "battery-contact-interface.json", "design-input-snapshot.json")]
    protected += sorted((OUTPUT / "libraries").rglob("*.kicad_mod"))
    report["protected_output_hashes"] = {str(p.relative_to(OUTPUT)): sha(p) for p in protected}
    write(OUTPUT / "placement-build-report.json", json.dumps(report, indent=2)+"\n")
    return report


def draw(manifest):
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="950" viewBox="0 0 1500 950">',
           '<rect width="1500" height="950" fill="white"/>',
           '<g font-family="sans-serif"><text x="25" y="35" font-size="24">Printed-bell front-electronics FLOORPLAN — NO ROUTING</text>']
    for side, cx in (("F", 380), ("B", 1120)):
        cy, scale = 460, 13
        svg.append(f'<text x="{cx-300}" y="85" font-size="20">{side}: {"81 electronic parts" if side == "F" else "2 fitted SMT contacts; separate attachment operation"}</text>')
        pts = " ".join(f"{cx+x*scale:.3f},{cy-y*scale:.3f}" for x, y in manifest["board"]["outline_common_xy_mm"])
        svg.append(f'<polygon points="{pts}" fill="#edf2f7" stroke="#334155"/>')
        if side == "F":
            svg.append(f'<circle cx="{cx}" cy="{cy}" r="{10.85*scale}" fill="#fff4e4" stroke="#c76d08" stroke-dasharray="5 4"/>')
        for m in manifest["mounting_holes"]:
            x, y = cx+m["x_mm"]*scale, cy-m["y_mm"]*scale
            svg.append(f'<circle cx="{x}" cy="{y}" r="{3.2*scale}" fill="#bbf7d0" stroke="#166534"/>')
            svg.append(f'<circle cx="{x}" cy="{y}" r="{1.1*scale}" fill="white" stroke="#166534"/>')
        for p in manifest["components"]:
            if p["side"] != side:
                continue
            x, y = cx+p["x_mm"]*scale, cy-p["y_mm"]*scale
            color = {"core": "#c4b5fd", "boost": "#fde68a", "amplifier": "#a5f3fc",
                     "protection": "#fecaca"}.get(p["cluster"], "#bfdbfe")
            svg.append(f'<g transform="translate({x:.3f} {y:.3f}) rotate({-p["rotation_deg"]:g})">'
                       f'<rect x="{-p["width_mm"]*scale/2:.3f}" y="{-p["depth_mm"]*scale/2:.3f}" '
                       f'width="{p["width_mm"]*scale:.3f}" height="{p["depth_mm"]*scale:.3f}" fill="{color}" stroke="#334155" stroke-width=".6"/></g>')
            svg.append(f'<text x="{x:.3f}" y="{y+3:.3f}" text-anchor="middle" font-size="10">{html.escape(p["reference"])}</text>')
    svg += ['<text x="25" y="865" font-size="17">Common assembly XY, +Y up; not mirrored photographs. Orange: measured magnet projection; green: M2 support/tool reserves.</text>',
            '<text x="25" y="895" font-size="17">Body proxies include source lands/drawings, not qualified vendor models. Contacts use the separate thin-primitives interface.</text>',
            '<text x="25" y="925" font-size="17">D43 main body, retained tabs/USB tongue. F25.0 / B26.6. No live-cell, thermal, charging, fabrication or child-use approval.</text></g></svg>']
    write(OUTPUT / "front-placement.svg", "\n".join(svg)+"\n")


def guard():
    path = OUTPUT / "placement-build-report.json"
    if not path.exists():
        return
    report = json.loads(path.read_text())
    if sha(OUTPUT / "handbell.kicad_pcb") != report["generated_pcb_sha256"]:
        raise ValueError("Native PCB edited since generation; refusing to overwrite")
    for name, digest in report.get("protected_output_hashes", {}).items():
        if sha(OUTPUT / name) != digest:
            raise ValueError("Edited local CAD/library/interface; refusing to overwrite "+name)
    _, board = load(OUTPUT / "handbell.kicad_pcb")
    if any(board.children(kind) for kind in ("segment", "via", "zone")):
        raise ValueError("Routing exists; this stage-1 generator must never overwrite it")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=140000)
    args = parser.parse_args()
    guard()
    seed_package()
    parts, xml, symbols, sch = read_parts()
    optimize(parts, args.steps)
    result = build(parts, xml, symbols, sch, args.steps)
    print(json.dumps({key: result[key] for key in ("fitted_by_side", "planning")}, indent=2))


if __name__ == "__main__":
    main()
