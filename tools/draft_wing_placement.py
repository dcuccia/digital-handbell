# SPDX-License-Identifier: MIT
"""Separate unrouted two-face wing-placement draft; never overwrite the 0.2 board."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import html
import json
import math
from pathlib import Path
import random
import subprocess
import xml.etree.ElementTree as ET

import place_handbell as base
from kicad_sexpr import apply_edits, load, loads, pcb_net_name
from placement_geometry import footprint_bounds

ROOT = base.ROOT
SOURCE = ROOT / "hardware" / "handbell"
OUTPUT = SOURCE / "iterations" / "wing-draft"
BOARD_Z = 20.5
THICKNESS = 1.6
MOUNTS = [
    {"reference": "MH1", "x_mm": 10.0, "y_mm": 15.7},
    {"reference": "MH2", "x_mm": -10.0, "y_mm": -15.7},
]
for mount in MOUNTS:
    mount.update(drill_mm=2.2, pad_diameter_mm=4.4, keepout_radius_mm=3.2, net="GND")
BATTERY = {"x_min_mm": -19.0, "x_max_mm": 19.0, "y_min_mm": -10.0, "y_max_mm": 10.0,
           "status": "Planning reservation only; no fitted contacts, selected cell or retained assembly approval"}
BOOST = set(base.BOOST_MAP.values())
AMP = {"U4", "C16", "C19", "R18"}
REAR = BOOST | AMP
USB_BACK = {"x": 0.0, "y": -18.0, "plan_w": 10.64, "plan_h": 8.93, "angle": 0.0,
            "side": "B", "source": "X6 body/drill projection plus 0.5 mm per edge; anchor height unqualified"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_parts(schematic):
    xml = ET.parse(SOURCE / "reports" / "handbell-netlist.xml").getroot()
    symbols = {p.properties()["Reference"]: p for p in schematic.children("symbol")
               if not p.properties()["Reference"].startswith("#") and p.value("unit") == "1"}
    parts = {}
    for c in xml.findall("components/comp"):
        ref, identifier = c.get("ref"), c.findtext("footprint")
        lib, name = identifier.split(":", 1)
        directory = base.LIBRARIES.get(lib, base.STANDARD / (lib + ".pretty"))
        raw_text, fp = load(directory / (name + ".kicad_mod"))
        raw, planning, has_courtyard = footprint_bounds(fp)
        if ref == "J2":
            raw[3] += 0.7
            planning[3] = max(planning[3], raw[3] + 0.25)
        cx, cy = (raw[0] + raw[2]) / 2, (raw[1] + raw[3]) / 2
        copper = ref in base.COPPER
        parts[ref] = {
            "ref": ref, "value": c.findtext("value"), "footprint": identifier, "text": raw_text,
            "fields": {**symbols[ref].properties(),
                       **{f.get("name"): f.text or "" for f in c.findall("fields/field")}},
            "raw_cx": cx, "raw_cy": cy, "raw_w": raw[2] - raw[0], "raw_h": raw[3] - raw[1],
            "plan_w": 2 * max(cx - planning[0], planning[2] - cx),
            "plan_h": 2 * max(cy - planning[1], planning[3] - cy),
            "has_courtyard": has_courtyard,
            "height": 0 if copper else base.height(ref, identifier),
            "side": "B" if ref in REAR else "F",
            "dnp": ref in {"X1", "C29"}, "copper_only": copper,
            "x": 0.0, "y": 0.0, "angle": 0.0,
        }
    return parts, xml, symbols


def seed_cluster(parts, poses, references, names, side, cx, cy, cluster_name):
    members = []
    for source_ref in references:
        ref = names.get(source_ref, source_ref)
        p = parts[ref]
        x, y, *angle = poses[source_ref]
        angle = angle[0] if angle else 0.0
        dx, dy = base.rotate(p["raw_cx"], p["raw_cy"], angle)
        x, y = x + dx, y + dy
        if side == "B":
            y, angle = -y, -angle
        members.append((p, x, y, angle))
    xmin = min(x - base.dimensions({**p, "angle": a})[0] / 2 for p, x, y, a in members)
    xmax = max(x + base.dimensions({**p, "angle": a})[0] / 2 for p, x, y, a in members)
    ymin = min(y - base.dimensions({**p, "angle": a})[1] / 2 for p, x, y, a in members)
    ymax = max(y + base.dimensions({**p, "angle": a})[1] / 2 for p, x, y, a in members)
    ox, oy = (xmin + xmax) / 2, (ymin + ymax) / 2
    for p, x, y, a in members:
        p.update(x=x - ox + cx, y=y - oy + cy, angle=a % 360, cluster=cluster_name,
                 local_x=x - ox, local_y=y - oy, local_angle=a % 360)


def rectangle_distance(p, x, y):
    w, h = base.dimensions(p)
    return math.hypot(max(abs(p["x"] - x) - w / 2, 0),
                      max(abs(p["y"] - y) - h / 2, 0))


def constraints(p):
    w, h = base.dimensions(p)
    penalty = 0.0
    if p["ref"] == "X6":
        return 0.0
    physical_height = 0 if p["dnp"] or p["copper_only"] else p["height"]
    deepest = BOARD_Z + THICKNESS + physical_height if p["side"] == "B" else BOARD_Z
    cavity_radius = (50 - (16 / 30) * (deepest - 13)) / 2
    limit = min(21.0, cavity_radius - 0.5)
    penalty += max(0, math.hypot(abs(p["x"]) + w / 2, abs(p["y"]) + h / 2) - limit) ** 2
    for mount in MOUNTS:
        penalty += max(0, mount["keepout_radius_mm"] -
                       rectangle_distance(p, mount["x_mm"], mount["y_mm"])) ** 2
    if p["side"] == "B":
        dx = min(p["x"] + w / 2, 19) - max(p["x"] - w / 2, -19)
        dy = min(p["y"] + h / 2, 10) - max(p["y"] - h / 2, -10)
        penalty += max(dx, 0) * max(dy, 0)
        penalty += base.pair_overlap(p, USB_BACK)
    elif physical_height > 1.0:
        penalty += max(0, 11.5 - rectangle_distance(p, 0, 0)) ** 2
    return penalty


def relax_core_caps(parts):
    core = [parts[ref] for ref in sorted(base.CORE)]
    movable = [p for p in core if p["ref"].startswith("C")]
    original = {p["ref"]: (p["x"], p["y"]) for p in core}
    rng = random.Random(204003)

    def cost(p):
        x, y = original[p["ref"]]
        displacement = math.hypot(p["x"] - x, p["y"] - y)
        if displacement > 1.2:
            return math.inf
        return (100 * sum(base.pair_overlap(p, other) for other in core if other is not p)
                + 0.2 * displacement ** 2)

    for step in range(30000):
        p = rng.choice(movable)
        previous = p["x"], p["y"]
        before = cost(p)
        amplitude = 0.25 * (1 - step / 30000) + 0.002
        p["x"] += rng.uniform(-amplitude, amplitude)
        p["y"] += rng.uniform(-amplitude, amplitude)
        if cost(p) > before:
            p["x"], p["y"] = previous
    for p in core:
        p["cluster"] = "core-refined"
        x, y = original[p["ref"]]
        p["core_cap_adjustment_local_mm"] = [p["x"] - x, p["y"] - y]


def seed(parts):
    old = json.loads((SOURCE / "placement" / "placement-manifest.json").read_text())
    for row in old["components"]:
        p = parts[row["reference"]]
        p.update(x=row["x_mm"], y=row["y_mm"], angle=(-row["rotation_deg"]) % 360)
    feather = base.source_poses(ROOT / "hardware" / "reference" / "adafruit-5768" /
                               "kicad" / "Adafruit Feather RP2040 Prop-Maker.kicad_pcb")
    mini = base.source_poses(ROOT / "hardware" / "reference" / "adafruit-4654" /
                            "kicad" / "Adafruit TPS61023.kicad_pcb")
    seed_cluster(parts, feather, sorted(base.CORE), {}, "F", 0, 0, "core-source")
    relax_core_caps(parts)
    seed_cluster(parts, mini, list(base.BOOST_MAP), base.BOOST_MAP, "B", -3.5, 14.5, "boost-source")
    # The reference's C16 is remote from U4. This draft instead places it next
    # to the B-side-transformed PVDD pads 7/8, and keeps bulk C19 adjacent.
    for ref, (x, y, angle) in {
            "U4": (9.9, -12.4, 0), "C16": (10.55, -15.25, 0),
            "C19": (7.4, -15.8, 0), "R18": (6.5, -11.7, 90)}.items():
        parts[ref].update(x=x, y=y, angle=angle, cluster="amp-local-bypass")
    overrides = {"X6": (0, -18, 180), "J1": (15.3, 0, 90),
                 "FB1": (13, -5, 90), "FB2": (15, -5, 90),
                 "C21": (13, -7, 0), "C22": (15, -7, 0),
                 "J2": (12, 9, 0), "X1": (-13, 7, 0), "C29": (-15, -1, 0),
                 "C1": (-7, -14, 90), "C4": (-14, -7, 0), "C5": (-12, -10, 90),
                 "U2": (-15, -5, 0), "U3": (8, 12, 0), "C20": (4, 14, 90),
                 "D3": (-10, 10, 0), "Q4": (13, -7, 0)}
    for ref, (x, y, angle) in overrides.items():
        parts[ref].update(x=x, y=y, angle=angle)
    for i, ref in enumerate(sorted(base.COPPER)):
        angle = 2 * math.pi * i / len(base.COPPER)
        parts[ref].update(x=17.5 * math.cos(angle), y=17.5 * math.sin(angle), angle=0)
    for p in parts.values():
        p["anchor_x"], p["anchor_y"] = p["x"], p["y"]


def overlap(a, b):
    if a["side"] != b["side"]:
        return 0.0
    if a.get("cluster") and a.get("cluster") == b.get("cluster"):
        return 0.0
    return base.pair_overlap(a, b)


def solve(parts, steps, seed_value):
    rng = random.Random(seed_value)
    rows = list(parts.values())
    units = []
    for cluster in ("core-refined", "boost-source", "amp-local-bypass"):
        units.append([p for p in rows if p.get("cluster") == cluster])
    units.extend([[p] for p in rows if not p.get("cluster") and p["ref"] != "X6"])

    def local(unit):
        ids = {p["ref"] for p in unit}
        result = sum(250 * constraints(p) for p in unit)
        for p in unit:
            result += 100 * sum(overlap(p, q) for q in rows if q["ref"] not in ids)
            result += 0.004 * ((p["x"] - p["anchor_x"]) ** 2 + (p["y"] - p["anchor_y"]) ** 2)
        return result

    for iteration in range(steps):
        unit = rng.choice(units)
        previous = [(p["x"], p["y"], p["angle"]) for p in unit]
        before = local(unit)
        fraction = iteration / max(steps, 1)
        scale = 1.8 * (1 - fraction) + 0.015
        dx, dy = rng.uniform(-scale, scale), rng.uniform(-scale, scale)
        cx = sum(p["x"] for p in unit) / len(unit)
        cy = sum(p["y"] for p in unit) / len(unit)
        turn = rng.choice((-90, 90)) if rng.random() < 0.015 else 0
        for p in unit:
            x, y = base.rotate(p["x"] - cx, p["y"] - cy, turn)
            p.update(x=x + cx + dx, y=y + cy + dy, angle=(p["angle"] + turn) % 360)
        after = local(unit)
        temperature = 2.0 * (1 - fraction) ** 3 + 0.0001
        if after > before and rng.random() >= math.exp(min(0, (before - after) / temperature)):
            for p, (x, y, angle) in zip(unit, previous):
                p.update(x=x, y=y, angle=angle)
    return {
        "intercluster_overlaps": [{"left": a["ref"], "right": b["ref"], "area_mm2": overlap(a, b)}
                                 for i, a in enumerate(rows) for b in rows[i + 1:]
                                 if overlap(a, b) > 0.001],
        "constraint_violations": [{"reference": p["ref"], "penalty": constraints(p)}
                                 for p in rows if constraints(p) > 0.001],
        "retained_source_cluster_planning_overlaps": [
            {"left": a["ref"], "right": b["ref"], "area_mm2": base.pair_overlap(a, b)}
            for i, a in enumerate(rows) for b in rows[i + 1:]
            if a.get("cluster") and a.get("cluster") == b.get("cluster")
            and base.pair_overlap(a, b) > 0.001],
    }


def rendered_footprint(p, nets, info, sheet_uuid, symbol_uuid):
    raw = base.embedded_footprint(p, nets, info, sheet_uuid, symbol_uuid)
    fp = loads(raw)
    original = loads(p["text"]).child("attr")
    original_flags = set(original.atoms()[1:]) if original else set()
    attr = fp.child("attr")
    flags = set(attr.atoms()[1:]) if attr else set()
    excludes = {"exclude_from_bom", "exclude_from_pos_files"}
    if p["copper_only"]:
        flags |= excludes
    elif p["side"] == "B":
        # The frozen generator's B-side branch is for copper-only features.
        # Material parts on this new back face must remain in BOM/CPL scope.
        flags -= excludes - original_flags
    replacement = "(attr " + " ".join(sorted(flags)) + ")"
    if attr:
        raw = apply_edits(raw, [(attr.start, attr.end, replacement)])
    elif flags:
        raw = apply_edits(raw, [(fp.end - 1, fp.end - 1, "\n" + replacement)])
    return raw


def mounting_footprint(mount):
    path = base.STANDARD / "MountingHole.pretty" / "MountingHole_2.2mm_M2_Pad.kicad_mod"
    text, fp = load(path)
    raw, planning, has_courtyard = footprint_bounds(fp)
    p = {"ref": mount["reference"], "value": "M2 GND mounting hole",
         "footprint": "MountingHole:MountingHole_2.2mm_M2_Pad", "text": text,
         "fields": {}, "raw_cx": 0, "raw_cy": 0, "side": "F",
         "x": mount["x_mm"], "y": mount["y_mm"], "angle": 0, "dnp": False}
    result = base.embedded_footprint(p, {"1": "GND"}, {"1": {"pintype": "passive"}},
                                     "unused", "unused")
    node = loads(result)
    edits = [(child.start, child.end, "") for child in node.children("path")]
    attr = node.child("attr")
    flags = set(attr.atoms()[1:]) if attr else set()
    flags |= {"board_only", "exclude_from_bom", "exclude_from_pos_files"}
    declaration = "(attr " + " ".join(sorted(flags)) + ")"
    if attr:
        edits.append((attr.start, attr.end, declaration))
    else:
        edits.append((node.end - 1, node.end - 1, "\n" + declaration))
    return apply_edits(result, edits)


def draw(path, parts):
    elements = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="690" viewBox="0 0 1200 690">',
                '<rect width="1200" height="690" fill="white"/>',
                '<text x="25" y="30" font-family="sans-serif" font-size="21">Wing placement DRAFT - unrouted, unselected battery/contact hardware</text>']
    for side, cx, title in (("F", 300, "Speaker-facing F: MCU / control / service"),
                            ("B", 895, "Handle-facing B: boost / audio wing groups")):
        cy, scale = 340, 11
        elements.extend([f'<text x="{cx-260}" y="75" font-family="sans-serif" font-size="17">{title}</text>',
                         f'<circle cx="{cx}" cy="{cy}" r="{21.5*scale}" fill="#f1f5f9" stroke="#334155"/>'])
        if side == "B":
            elements.append(f'<rect x="{cx-19*scale}" y="{cy-10*scale}" width="{38*scale}" height="{20*scale}" fill="#ffe8e8" stroke="#b22" stroke-dasharray="6,4"/>')
            elements.append(f'<rect x="{cx+(USB_BACK["x"]-USB_BACK["plan_w"]/2)*scale}" y="{cy-(USB_BACK["y"]+USB_BACK["plan_h"]/2)*scale}" width="{USB_BACK["plan_w"]*scale}" height="{USB_BACK["plan_h"]*scale}" fill="#ffe5b4" stroke="#a65f00" stroke-dasharray="6,4"/>')
        else:
            elements.append(f'<circle cx="{cx}" cy="{cy}" r="{11.5*scale}" fill="none" stroke="#b22" stroke-dasharray="6,4"/>')
        for m in MOUNTS:
            x, y = cx + m["x_mm"] * scale, cy - m["y_mm"] * scale
            elements.extend([f'<circle cx="{x}" cy="{y}" r="{3.2*scale}" fill="#d1fae5" stroke="#064e3b"/>',
                             f'<circle cx="{x}" cy="{y}" r="{1.1*scale}" fill="white" stroke="#064e3b"/>'])
        for p in parts.values():
            if p["side"] != side:
                continue
            x, y = cx + p["x"] * scale, cy - p["y"] * scale
            color = ("#ddd" if p["dnp"] else "#a7f3d0" if p["copper_only"]
                     else "#fde68a" if p["ref"] in BOOST else "#c4b5fd" if p["ref"] in base.CORE else "#bfdbfe")
            elements.append(f'<g transform="translate({x:.3f} {y:.3f}) rotate({p["angle"]:g})"><rect x="{-p["raw_w"]*scale/2:.3f}" y="{-p["raw_h"]*scale/2:.3f}" width="{p["raw_w"]*scale:.3f}" height="{p["raw_h"]*scale:.3f}" fill="{color}" stroke="#334155" stroke-width=".6"/></g>')
            elements.append(f'<text x="{x:.3f}" y="{y+3:.3f}" text-anchor="middle" font-family="sans-serif" font-size="8">{html.escape(p["ref"])}</text>')
    elements.extend(['<text x="25" y="625" font-family="sans-serif" font-size="14">Both views use common assembly XY (+Y up), NOT mirrored photographic views. Green circles: mounting/tool reservations.</text>',
                     '<text x="25" y="651" font-family="sans-serif" font-size="14">Red: magnet / battery reservations. Orange: USB anchors on reverse. X1/C29 DNP; mounting pads GND-assigned, unrouted.</text>',
                     '</svg>'])
    path.write_text("\n".join(elements) + "\n", encoding="utf-8")


def generate(parts, xml, symbols, schematic_text, schematic, planning, output):
    output.mkdir(parents=True, exist_ok=True)
    edits = []
    for symbol in schematic.children("symbol"):
        if symbol.properties().get("Reference") == "X1":
            x1 = symbol.child("dnp")
            edits.append((x1.items[1].start, x1.items[1].end, "yes"))
    title = schematic.child("title_block")
    if title:
        for key, value in (("title", "Handbell wing placement - battery interface NOT FROZEN"),
                           ("rev", "0.3-wing-draft")):
            n = title.child(key)
            if n:
                edits.append((n.items[1].start, n.items[1].end, json.dumps(value)))
    (output / "handbell.kicad_sch").write_text(apply_edits(schematic_text, edits), encoding="utf-8")
    (output / "handbell.kicad_pro").write_bytes((SOURCE / "handbell.kicad_pro").read_bytes())
    for name in ("fp-lib-table", "sym-lib-table"):
        (output / name).write_text((SOURCE / name).read_text().replace(
            "${KIPRJMOD}/", "${KIPRJMOD}/../../"), encoding="utf-8")
    pin_nets, pin_info = {}, {}
    for net in xml.findall("nets/net"):
        for pin in net.findall("node"):
            pin_nets.setdefault(pin.get("ref"), {})[pin.get("pin")] = net.get("name")
            pin_info.setdefault(pin.get("ref"), {})[pin.get("pin")] = pin.attrib
    footprints = [rendered_footprint(p, pin_nets[p["ref"]], pin_info[p["ref"]],
                                     schematic.value("uuid"), symbols[p["ref"]].value("uuid"))
                  for p in parts.values()]
    footprints.extend(mounting_footprint(m) for m in MOUNTS)
    ref_text, ref_board = load(SOURCE / "handbell.kicad_pcb")
    layers = ref_board.child("layers")
    pcb = f'''(kicad_pcb (version 20260206) (generator "pcbnew") (generator_version "10.0")
      (general (thickness 1.6)) (paper "A4")
      (title_block (title "Handbell wing placement DRAFT - NOT FOR FABRICATION") (rev "0.3-wing-draft")
        (comment 1 "Adafruit 5768 / 4438 / 4654-derived; CC BY-SA 3.0; see project notices."))
      {ref_text[layers.start:layers.end]}
      (setup (pad_to_mask_clearance 0))
      {"".join(footprints)}
      (gr_circle (center 100 100) (end 121.5 100) (stroke (width 0.05) (type solid))
        (fill none) (layer "Edge.Cuts") (uuid "{base.uid("wing-outline")}"))
      (gr_rect (start 81 90) (end 119 110) (stroke (width 0.1) (type dash))
        (fill none) (layer "Dwgs.User") (uuid "{base.uid("wing-battery-reservation")}"))
      (gr_text "UNROUTED WING DRAFT - BATTERY/CONTACTS NOT SELECTED" (at 100 127)
        (layer "Dwgs.User") (effects (font (size 1 1) (thickness .15)))
        (uuid "{base.uid("wing-warning")}"))
    )'''
    for m in MOUNTS:
        index = pcb.rfind(")")
        circle = (f'(gr_circle (center {100+m["x_mm"]} {100+m["y_mm"]}) '
                  f'(end {100+m["x_mm"]+m["keepout_radius_mm"]} {100+m["y_mm"]}) '
                  '(stroke (width 0.1) (type dash)) (fill none) (layer "Dwgs.User") '
                  f'(uuid "{base.uid(m["reference"]+"/mechanical-reservation")}"))')
        pcb = pcb[:index] + circle + pcb[index:]
    loads(pcb)
    board_path = output / "handbell.kicad_pcb"
    board_path.write_text(pcb + "\n", encoding="utf-8")
    manifest = {
        "schema_version": 2, "units": "mm", "status": "Separate unrouted wing draft; no final battery/retention/fabrication approval",
        "board": {"diameter_mm": 43.0, "thickness_mm": THICKNESS, "front_z_mm": BOARD_Z,
                  "front_face": "speaker", "component_face": "mixed"},
        "coordinate_convention": "Common centered assembly XY, right-handed +Z inward; mathematical component rotation = -KiCad rotation. F toward speaker, B toward handle.",
        "generated_pcb_sha256": sha(board_path), "schematic_sha256": sha(output / "handbell.kicad_sch"),
        "baseline_pcb_sha256": sha(SOURCE / "handbell.kicad_pcb"),
        "baseline_schematic_sha256": sha(SOURCE / "handbell.kicad_sch"),
        "components": [{
            "reference": p["ref"], "footprint": p["footprint"], "x_mm": p["x"], "y_mm": p["y"],
            "width_mm": p["raw_w"], "depth_mm": p["raw_h"], "height_mm": p["height"],
            "rotation_deg": -p["angle"], "side": p["side"],
            "z_min_mm": BOARD_Z - p["height"] if p["side"] == "F" else BOARD_Z + THICKNESS,
            "z_max_mm": BOARD_Z if p["side"] == "F" else BOARD_Z + THICKNESS + p["height"],
            "height_source": "Unchanged original planning proxy height; not a qualified manufacturer/mated maximum",
            "requires_shell_cutout": p["ref"] == "X6", "cluster": p.get("cluster"),
            "core_cap_adjustment_local_mm": p.get("core_cap_adjustment_local_mm"),
        } for p in parts.values() if not p["dnp"] and not p["copper_only"]],
        "mounting_holes": MOUNTS, "battery_reservation": BATTERY,
        "cross_face_keepouts": [USB_BACK],
        "dnp_footprint_reservations": [p["ref"] for p in parts.values() if p["dnp"]],
        "copper_only_features": [{"reference": p["ref"], "x_mm": p["x"], "y_mm": p["y"], "side": p["side"]}
                                 for p in parts.values() if p["copper_only"]],
        "planning": planning,
        "limits": ["No tracks/vias/zones; GND mounting pads require routing to become grounded.",
                   "Core is source-seeded with bounded local capacitor spacing adjustments; active core/crystal relative poses remain fixed. Boost is a rigid source cluster; amplifier uses an explicit local-bypass draft. No source copper is reused.",
                   "Other placements are mechanical/electrical draft anchors; bypass, return paths, thermal and routing review remain open.",
                   "X1 is DNP pending the unselected battery interface; this is not a complete power-input design.",
                   "Reverse battery/contact reservation is not a demonstrated cell/clip/cradle fit.",
                   "Grounded metal hardware must not contact cell cans, terminals or the bell without deliberate insulation/bonding design."],
    }
    (output / "placement-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    draw(output / "wing-placement.svg", parts)
    # Independently check every serialized physical pin against the retained
    # netlist, rather than relying on a successful S-expression parse.
    _, board = load(board_path)
    count = 0
    for fp in board.children("footprint"):
        ref = fp.properties()["Reference"]
        expected = {"1": "GND"} if ref.startswith("MH") else pin_nets[ref]
        if ref.startswith("MH"):
            mount = next(m for m in MOUNTS if m["reference"] == ref)
            pad = fp.child("pad")
            if (pad.atoms()[2] != "thru_hole"
                    or float(pad.value("drill")) != mount["drill_mm"]
                    or list(map(float, pad.child("size").atoms()[1:])) != [mount["pad_diameter_mm"]] * 2):
                raise ValueError(f"Mounting-hole manifest differs from physical footprint: {ref}")
        for pad in fp.children("pad"):
            number = pad.atoms()[1]
            if pad.value("net") != pcb_net_name(expected.get(number)):
                raise ValueError(f"Serialized net mismatch: {ref}.{number}")
            count += 1
        if ref in REAR:
            if fp.value("layer") != "B.Cu":
                raise ValueError(f"Backside material not flipped: {ref}")
            flags = set(fp.child("attr").atoms()[1:])
            if "exclude_from_bom" in flags or "exclude_from_pos_files" in flags:
                raise ValueError(f"Backside fitted part incorrectly excluded: {ref}")
    report = {"generated_pcb_sha256": sha(board_path), "physical_pads_checked": count,
              "fitted_by_side": dict(Counter(p["side"] for p in manifest["components"])),
              "dnp": manifest["dnp_footprint_reservations"], "board_only_mounts": MOUNTS,
              "planning": planning, "script_sha256": sha(Path(__file__))}
    (output / "placement-build-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


def check_overwrite(output):
    board_path = output / "handbell.kicad_pcb"
    prior_path = output / "placement-manifest.json"
    prior = json.loads(prior_path.read_text()) if prior_path.exists() else {}
    for name, key in (("handbell.kicad_pcb", "generated_pcb_sha256"),
                      ("handbell.kicad_sch", "schematic_sha256")):
        path = output / name
        if path.exists() and prior.get(key) != sha(path):
            raise ValueError(f"Refusing to overwrite manually changed or untracked candidate {name}")
    if board_path.exists():
        _, pcb = load(board_path)
        if any(pcb.children(kind) for kind in ("segment", "via", "zone")):
            raise ValueError("Refusing to overwrite a routed candidate PCB")
    project = output / "handbell.kicad_pro"
    if project.exists() and sha(project) != sha(SOURCE / project.name):
        raise ValueError("Refusing to overwrite changed candidate project/rule settings")
    for name in ("fp-lib-table", "sym-lib-table"):
        path = output / name
        expected = (SOURCE / name).read_text().replace("${KIPRJMOD}/", "${KIPRJMOD}/../../")
        if path.exists() and path.read_text() != expected:
            raise ValueError(f"Refusing to overwrite changed candidate {name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=160000)
    parser.add_argument("--seed", type=int, default=163402)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--preview", action="store_true", help="Solve/report without writing native CAD.")
    args = parser.parse_args()
    if args.steps < 0:
        parser.error("steps must be nonnegative")
    output = args.output.resolve()
    if output.parent != SOURCE / "iterations":
        raise ValueError("Use a direct child folder of hardware/handbell/iterations for portable library paths")
    check_overwrite(output)
    text, schematic = load(SOURCE / "handbell.kicad_sch")
    parts, xml, symbols = read_parts(schematic)
    seed(parts)
    planning = solve(parts, args.steps, args.seed)
    if args.preview:
        print(json.dumps(planning, indent=2))
    else:
        generate(parts, xml, symbols, text, schematic, planning, output)


if __name__ == "__main__":
    main()
