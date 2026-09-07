# SPDX-License-Identifier: MIT
"""Generate an unrouted, actual-footprint placement candidate and FreeCAD manifest."""
import argparse
import hashlib
import html
import json
import math
import os
from pathlib import Path
import random
import xml.etree.ElementTree as ET
import uuid

from kicad_sexpr import apply_edits, load, loads, pcb_net_name
from placement_geometry import footprint_bounds

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "hardware" / "handbell"
OUT = DRAFT / "placement"
STANDARD = Path(os.environ.get("KICAD10_FOOTPRINT_DIR",
                str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "KiCad" / "10.0" / "share" / "kicad" / "footprints")))
LIBRARIES = {
    "Handbell": DRAFT / "Handbell.pretty",
    "Adafruit Feather RP2040 Prop-Maker-import-fps": ROOT / "hardware" / "reference" / "adafruit-5768" / "kicad" / "Adafruit Feather RP2040 Prop-Maker-import-fps.pretty",
    "Adafruit_LSM6DSOX-import-fps": ROOT / "hardware" / "reference" / "adafruit-4438" / "kicad" / "Adafruit_LSM6DSOX-import-fps.pretty",
    "Adafruit TPS61023-import-fps": ROOT / "hardware" / "reference" / "adafruit-4654" / "kicad" / "Adafruit TPS61023-import-fps.pretty",
}
COPPER = {"D+1", "D-1", "GAIN0", "CHG_EN0"} | {f"TP{i}" for i in range(3, 17)}
CORE = {"IC1", "U1", "C2", "C3", "C6", "C7", "C8", "C9", "C10", "C11", "C12", "C13",
        "C14", "C15", "C17", "C18", "R5", "R6", "Y1"}
BOOST_MAP = {"IC1": "U5", "L1": "L1", "C1": "C27", "C2": "C26", "C3": "C28", "R2": "R23", "R3": "R24"}


def uid(label):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "digital-handbell/placement/0.2/"+label))


def rotate(x, y, angle):
    # KiCad angles are counterclockwise in its screen-coordinate (Y-down) plane.
    a = math.radians(-angle)
    return x*math.cos(a)-y*math.sin(a), x*math.sin(a)+y*math.cos(a)


def height(ref, footprint):
    values = {"IC1": 1.0, "IC4": 1.0, "U1": 1.0, "U2": 1.5, "U3": 1.5, "U4": 1.0,
              "U5": .65, "Q1": 1.5, "Q2": 1.5, "Q3": 1.0, "Q4": 1.5,
              "L1": 5.0, "X1": 5.0, "X6": 3.5, "J1": 3.1, "J2": 3.1, "Y1": 1.0}
    values.update({"D3": 1.1, "D4": 1.0})
    if ref in values:
        return values[ref]
    if "0805" in footprint:
        return 2.0
    if "0603" in footprint or ref.startswith("FB"):
        return 1.0
    if "_0402" in footprint or ref.startswith("R"):
        return .65
    raise ValueError(f"No explicit screening height for {ref}: {footprint}")


def source_poses(path):
    _, board = load(path)
    return {p.properties()["Reference"]: tuple(map(float, p.child("at").atoms()[1:])) for p in board.children("footprint")}


def dimensions(part):
    w, h = part["plan_w"], part["plan_h"]
    return (h, w) if int(round(part["angle"]/90)) % 2 else (w, h)


def pair_overlap(a, b):
    aw, ah = dimensions(a)
    bw, bh = dimensions(b)
    dx = (aw+bw)/2-abs(a["x"]-b["x"])
    dy = (ah+bh)/2-abs(a["y"]-b["y"])
    return max(0.0, dx)*max(0.0, dy)


def outside(part, diameter, z, thickness):
    if part["ref"] == "X6":
        return max(0, abs(part["x"])-diameter/2+part["plan_w"]/2)**2
    w, h = dimensions(part)
    cavity = (50-(16/30)*(z+thickness+part["height"]-13))/2
    limit = min(diameter/2-.5, cavity-.5)
    return max(0, math.hypot(abs(part["x"])+w/2, abs(part["y"])+h/2)-limit)**2


def optimize(parts, diameter, z, thickness, seed, steps):
    rng = random.Random(seed)
    movable = [p for p in parts if p["ref"] not in {"IC1", "X6"}]
    def local(p):
        attraction = .002*((p["x"]-p["anchor_x"])**2+(p["y"]-p["anchor_y"])**2)
        return 80*sum(pair_overlap(p, q) for q in parts if q is not p) + 160*outside(p, diameter, z, thickness)+attraction
    for iteration in range(steps):
        p = rng.choice(movable)
        old = p["x"], p["y"], p["angle"]
        before = local(p)
        fraction = iteration/steps
        scale = 1.5*(1-fraction)+.05
        temperature = .4*(1-fraction)**2+.0001
        p["x"] += rng.uniform(-scale, scale)
        p["y"] += rng.uniform(-scale, scale)
        if rng.random() < .02 and p["ref"] not in CORE and p["ref"] not in BOOST_MAP.values():
            p["angle"] = (p["angle"]+90) % 360
        after = local(p)
        if after > before and rng.random() >= math.exp(min(0, (before-after)/temperature)):
            p["x"], p["y"], p["angle"] = old
    return [(p["ref"], q["ref"], round(pair_overlap(p, q), 5))
            for i, p in enumerate(parts) for q in parts[i+1:] if pair_overlap(p, q) > .001]


def embedded_footprint(part, nets, pin_info, sheet_uuid, symbol_uuid):
    raw = part["text"]
    fp = loads(raw)
    edits = [(fp.items[1].start, fp.items[1].end, json.dumps(part["footprint"]))]
    angle = part["angle"]
    cx, cy = part["raw_cx"], part["raw_cy"]
    if part["side"] == "B":
        cy = -cy
    dx, dy = rotate(cx, cy, angle)
    origin = (100+part["x"]-dx, 100+part["y"]-dy)
    remove = {"version", "generator", "generator_version", "uuid", "path", "sheetname", "sheetfile",
              "pintype", "pinfunction"}
    index = 0
    for n in fp.walk():
        if n.head in remove or n.head == "net" or n is fp.child("at"):
            edits.append((n.start, n.end, ""))
        elif n.head == "property":
            a = n.atoms()
            if a[1] in {"Reference", "Value"}:
                value = part["ref"] if a[1] == "Reference" else part["value"]
                edits.append((n.items[2].start, n.items[2].end, json.dumps(value)))
        elif n.head == "pad":
            net = nets.get(n.atoms()[1])
            if net:
                edits.append((n.end-1, n.end-1, f'\n(net {json.dumps(pcb_net_name(net))})'))
            for field in ("pinfunction", "pintype"):
                value = pin_info.get(n.atoms()[1], {}).get(field)
                if value:
                    edits.append((n.end-1, n.end-1, f'\n({field} {json.dumps(value)})'))
        if n.head in {"pad", "fp_line", "fp_rect", "fp_poly", "fp_arc", "fp_circle", "fp_text", "property"}:
            edits.append((n.end-1, n.end-1, f'\n(uuid "{uid(part["ref"]+"/"+str(index)+"/"+n.head)}")'))
        index += 1
    raw = apply_edits(raw, edits)
    fp = loads(raw)
    extra = f'\n(at {origin[0]:.6f} {origin[1]:.6f} {angle:g})\n(uuid "{uid(part["ref"])}")\n(path "/{sheet_uuid}/{symbol_uuid}")'
    fields = {n.atoms()[1]: n for n in fp.children("property")}
    field_edits = []
    for name, value in part["fields"].items():
        if name in {"Reference", "Value", "Footprint"}:
            continue
        if name in fields:
            n = fields[name].items[2]
            field_edits.append((n.start, n.end, json.dumps(value)))
        else:
            extra += (f'\n(property {json.dumps(name)} {json.dumps(value)} (at 0 0) (layer "F.Fab")'
                      f' (hide yes) (uuid "{uid(part["ref"]+"/field/"+name)}")'
                      ' (effects (font (size 1 1) (thickness 0.15))))')
    raw = apply_edits(raw, field_edits)
    fp = loads(raw)
    attr = fp.child("attr")
    flags = set(attr.atoms()[1:]) if attr else set()
    if part["dnp"]:
        flags.add("dnp")
    if part["side"] == "B":
        flags.update({"exclude_from_bom", "exclude_from_pos_files"})
    if flags:
        declaration = "(attr "+" ".join(sorted(flags))+")"
        if attr:
            raw = apply_edits(raw, [(attr.start, attr.end, declaration)])
            fp = loads(raw)
        else:
            extra += "\n"+declaration
    raw = apply_edits(raw, [(fp.end-1, fp.end-1, extra)])
    if part["side"] == "B":
        # Flip local Y, including the asymmetric jumper pin-1 marker, onto the back.
        fp = loads(raw)
        edit = []
        for n in fp.walk():
            if n.head in {"start", "end", "mid", "center", "xy", "at"} and n is not fp.child("at"):
                edit.append((n.items[2].start, n.items[2].end, f"{-float(n.atoms()[2]):g}"))
                if n.head == "at" and len(n.atoms()) > 3:
                    edit.append((n.items[3].start, n.items[3].end, f"{-float(n.atoms()[3]):g}"))
            elif n.head == "layer":
                a = n.atoms()[1]
                if a.startswith("F."):
                    edit.append((n.items[1].start, n.items[1].end, json.dumps("B."+a[2:])))
            elif n.head == "layers":
                for a in n.items[1:]:
                    if a.value.startswith("F."):
                        edit.append((a.start, a.end, json.dumps("B."+a.value[2:])))
            elif n.head == "effects":
                justification = n.child("justify")
                if justification and "mirror" not in justification.atoms():
                    edit.append((justification.end-1, justification.end-1, " mirror"))
                elif not justification:
                    edit.append((n.end-1, n.end-1, " (justify mirror)"))
        raw = apply_edits(raw, edit)
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diameter", type=float, default=43)
    parser.add_argument("--front-z", type=float, default=20)
    parser.add_argument("--steps", type=int, default=160000)
    parser.add_argument("--seed", type=int, default=2040)
    args = parser.parse_args()
    if not 20 <= args.diameter <= 70 or not 13 <= args.front_z <= 35 or args.steps < 0:
        parser.error("Screen requires 20..70 mm diameter, z=13..35 mm and nonnegative steps.")
    OUT.mkdir(exist_ok=True)
    board_path = DRAFT / "handbell.kicad_pcb"
    manifest_path = OUT / "placement-manifest.json"
    if board_path.exists():
        _, existing = load(board_path)
        if existing.children("segment") or existing.children("via") or existing.children("zone"):
            raise ValueError("Refusing to overwrite a PCB containing routing or zones.")
        prior = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
        if prior.get("generated_pcb_sha256") != hashlib.sha256(board_path.read_bytes()).hexdigest():
            raise ValueError("PCB differs from last generated placement; preserve manual edits.")
    xml = ET.parse(DRAFT / "reports" / "handbell-netlist.xml").getroot()
    _, schematic = load(DRAFT / "handbell.kicad_sch")
    instances = {p.properties()["Reference"]: p for p in schematic.children("symbol")
                 if not p.properties()["Reference"].startswith("#") and p.value("unit") == "1"}
    parts = {}
    for c in xml.findall("components/comp"):
        ref, identifier = c.get("ref"), c.findtext("footprint")
        lib, name = identifier.split(":", 1)
        directory = LIBRARIES.get(lib, STANDARD / (lib+".pretty"))
        text, fp = load(directory / (name+".kicad_mod"))
        raw, planning, has_courtyard = footprint_bounds(fp)
        if ref == "J2":
            # The JST side-entry assembly is 6.25 mm deep; reserve an additional front allowance.
            raw[3] += .7
            planning[3] = max(planning[3], raw[3]+.25)
        parts[ref] = {
            "ref": ref, "value": c.findtext("value"), "footprint": identifier, "text": text,
            "fields": {**instances[ref].properties(),
                       **{f.get("name"): f.text or "" for f in c.findall("fields/field")}},
            "raw_cx": (raw[0]+raw[2])/2, "raw_cy": (raw[1]+raw[3])/2,
            "raw_w": raw[2]-raw[0], "raw_h": raw[3]-raw[1],
            "plan_w": 2*max((raw[0]+raw[2])/2-planning[0], planning[2]-(raw[0]+raw[2])/2),
            "plan_h": 2*max((raw[1]+raw[3])/2-planning[1], planning[3]-(raw[1]+raw[3])/2),
            "has_courtyard": has_courtyard,
            "height": 0 if ref in COPPER else height(ref, identifier),
            "side": "B" if ref in COPPER else "F",
            "dnp": instances[ref].value("dnp") == "yes",
            "x": 0, "y": 0, "angle": 0,
        }
    base = source_poses(ROOT / "hardware" / "reference" / "adafruit-5768" / "kicad" / "Adafruit Feather RP2040 Prop-Maker.kicad_pcb")
    core_origin = base["IC1"]
    for ref in CORE:
        x, y, *a = base[ref]
        part = parts[ref]
        part["angle"] = (a[0] if a else 0) % 360
        dx, dy = rotate(part["raw_cx"], part["raw_cy"], part["angle"])
        part["x"], part["y"] = x-core_origin[0]-1+dx, y-core_origin[1]-1.5+dy
    boost = source_poses(ROOT / "hardware" / "reference" / "adafruit-4654" / "kicad" / "Adafruit TPS61023.kicad_pcb")
    for source_ref, ref in BOOST_MAP.items():
        x, y, *a = boost[source_ref]
        part = parts[ref]
        part["angle"] = (a[0] if a else 0) % 360
        dx, dy = rotate(part["raw_cx"], part["raw_cy"], part["angle"])
        part["x"], part["y"] = x-5.5425-8+dx, y+8.70075+11+dy
    manual = {
        "X6": (0, -18.0, 180), "X1": (4, 14, 0), "J1": (15, 3, 270), "J2": (10, 10, 0),
        "U4": (14, -6, 0), "C16": (10, -5, 90), "C19": (10, -8, 0),
        "R18": (15, -10, 0), "FB1": (18, -4, 90), "FB2": (18, -1, 90),
        "C21": (17, 1, 0), "C22": (15, 1, 0),
        "IC4": (-14, -4, 0), "C23": (-16, -1, 0), "C24": (-12, -1, 0),
        "R14": (-17, -4, 90), "R15": (-17, -7, 90),
        "U3": (1, 9, 0), "R8": (-2, 7, 0), "C20": (2, 6, 0),
        "CHG0": (10, 15, 0), "R2": (12, 13, 0), "L0": (-11, -13, 0), "R7": (-9, -12, 0),
        "U2": (-11, -9, 0), "C4": (-7, -10, 0), "C5": (-5, -12, 0), "R3": (-14, -9, 0),
        "Q1": (-15, 5, 0), "Q2": (-17, 2, 0), "R16": (-18, 5, 90), "R17": (-15, 8, 90),
        "Q3": (-4, -14, 0), "D4": (-7, -14, 0), "R4": (-3, -12, 0), "C1": (-1, -12, 0),
        "R9": (6, -13, 0), "R10": (6, -15, 0), "R12": (8, -13, 90), "R13": (8, -15, 90),
        "R1": (-6, 7, 0), "R11": (-4, 5, 0), "D3": (-6, 5, 0),
        "Q4": (9, 3, 0), "R20": (10, 1, 0), "R21": (6, 8, 0), "R22": (8, 8, 0),
        "C25": (6, 10, 0), "C29": (-1, 10, 0),
    }
    for ref, pose in manual.items():
        parts[ref]["x"], parts[ref]["y"], parts[ref]["angle"] = pose
    for i, ref in enumerate(sorted(COPPER)):
        if ref in parts:
            parts[ref]["x"], parts[ref]["y"], parts[ref]["angle"] = -12+(i % 6)*4.5, -5+(i//6)*5, 0
    assigned = CORE | set(BOOST_MAP.values()) | set(manual) | COPPER
    if set(parts)-assigned:
        raise ValueError(f"Missing initial placement: {set(parts)-assigned}")
    for p in parts.values():
        p["anchor_x"], p["anchor_y"] = p["x"], p["y"]
    top = [p for p in parts.values() if p["side"] == "F"]
    overlaps = optimize(top, args.diameter, args.front_z, 1.6, args.seed, args.steps)
    outside_parts = [{"reference": p["ref"], "squared_violation": round(outside(p, args.diameter, args.front_z, 1.6), 5)}
                     for p in top if outside(p, args.diameter, args.front_z, 1.6) > .001]
    pin_nets = {}
    pin_info = {}
    for n in xml.findall("nets/net"):
        for p in n.findall("node"):
            pin_nets.setdefault(p.get("ref"), {})[p.get("pin")] = n.get("name")
            pin_info.setdefault(p.get("ref"), {})[p.get("pin")] = p.attrib
    reference_text, reference_board = load(ROOT / "hardware" / "reference" / "adafruit-4654" / "kicad" / "Adafruit TPS61023.kicad_pcb")
    layers = reference_board.child("layers")
    footprints = [embedded_footprint(p, pin_nets[p["ref"]], pin_info[p["ref"]], schematic.value("uuid"),
                                    instances[p["ref"]].value("uuid")) for p in parts.values()]
    pcb = f'''(kicad_pcb (version 20260206) (generator "pcbnew") (generator_version "10.0")
      (general (thickness 1.6)) (paper "A4")
      (title_block (title "Handbell 0.2 - UNROUTED PLACEMENT ONLY") (rev "0.2-feasibility")
        (comment 1 "Adafruit 5768 / 4438 / 4654-derived; CC BY-SA 3.0; see README and ATTRIBUTION.")
        (comment 2 "Independent digital-handbell project; not an Adafruit product."))
      {reference_text[layers.start:layers.end]}
      (setup (pad_to_mask_clearance 0))
      {"".join(footprints)}
      (gr_circle (center 100 100) (end {100+args.diameter/2} 100)
        (stroke (width 0.05) (type solid)) (fill none) (layer "Edge.Cuts") (uuid "{uid("outline")}"))
      (gr_text "UNROUTED PLACEMENT - NOT FOR FABRICATION" (at 100 127)
        (layer "Dwgs.User") (effects (font (size 1 1) (thickness 0.15))) (uuid "{uid("warning")}"))
    )'''
    loads(pcb)
    board_path.write_text(pcb+"\n", encoding="utf-8")
    manifest = {
        "schema_version": 1, "units": "mm",
        "status": "Unrouted placement candidate; proxies and provisional heights, not a fabrication release",
        "board": {"diameter_mm": args.diameter, "thickness_mm": 1.6, "front_z_mm": args.front_z, "component_face": "inward"},
        "generated_pcb_sha256": hashlib.sha256(board_path.read_bytes()).hexdigest(),
        "schematic_sha256": hashlib.sha256((DRAFT/"handbell.kicad_sch").read_bytes()).hexdigest(),
        "components": [{
            "reference": p["ref"], "x_mm": p["x"], "y_mm": p["y"],
            "width_mm": p["raw_w"], "depth_mm": p["raw_h"], "height_mm": p["height"],
            "rotation_deg": -p["angle"], "footprint": p["footprint"],
            "height_source": (
                "JST SH side-entry assembly: 2.95mm reference height, screened at3.1mm; wire bend not included"
                if p["ref"] == "J2" else
                "Provisional screening height; not a qualified manufacturer maximum or mated cable envelope"),
            "requires_shell_cutout": p["ref"] == "X6",
        } for p in top if not p["dnp"]],
        "dnp_footprint_reservations": [p["ref"] for p in top if p["dnp"]],
        "copper_only_back_features": [{"reference": p["ref"], "x_mm": p["x"], "y_mm": p["y"]} for p in parts.values() if p["side"] == "B"],
        "planning_envelope_method": "Pad/F.Fab/non-text F.SilkS bounding boxes, expanded 0.25mm per edge or to larger existing courtyard. Not authoritative body/courtyard geometry.",
        "remaining_planning_envelope_overlaps_mm2": overlaps,
        "remaining_conservative_boundary_violations": outside_parts,
        "limitations": [
            "No traces/vias/zones; no routing, signal-integrity, thermal or manufacturability proof.",
            "USB body intentionally requires a shell opening; its exception is not a demonstrated slot/load path.",
            "Battery, mating harnesses, underside protrusions and exact component bodies need further evidence.",
            "Source MCU and boost positions seed placement, but optimization moves parts; source routing is not reused.",
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="950" viewBox="-30 -33 60 64"><rect x="-30" y="-33" width="60" height="64" fill="white"/><circle r="{args.diameter/2}" fill="#f1f5f9" stroke="#334155" stroke-width=".15"/>']
    for p in top:
        color = "#ddd6fe" if p["ref"] in CORE else "#fde68a" if p["ref"] in BOOST_MAP.values() else "#bfdbfe"
        if p["dnp"]:
            color = "#e5e7eb"
        svg.append(f'<g transform="translate({p["x"]:.4f} {p["y"]:.4f}) rotate({-p["angle"]})"><rect x="{-p["raw_w"]/2}" y="{-p["raw_h"]/2}" width="{p["raw_w"]}" height="{p["raw_h"]}" fill="{color}" stroke="#334155" stroke-width=".08"/></g><text x="{p["x"]:.4f}" y="{p["y"]+.3:.4f}" text-anchor="middle" font-family="sans-serif" font-size=".8">{html.escape(p["ref"])}</text>')
    svg.extend(['<text x="-28" y="-29" font-family="sans-serif" font-size="1.5">Actual-footprint placement / NOT ROUTED</text>',
                f'<text x="-28" y="27" font-family="sans-serif" font-size="1.1">Diameter {args.diameter:g} mm; {len(overlaps)} envelope overlaps; {len(outside_parts)} boundary exceptions</text>',
                '<text x="-28" y="29" font-family="sans-serif" font-size="1">Purple: core; yellow: boost; copper-only pads on reverse face.</text></svg>'])
    (OUT/"placement-top.svg").write_text("".join(svg)+"\n", encoding="utf-8")
    print(json.dumps({"footprints": len(parts), "fitted_top_parts": len(manifest["components"]),
                      "overlaps": overlaps, "boundary_violations": outside_parts}, indent=2))


if __name__ == "__main__":
    main()
