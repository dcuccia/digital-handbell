# SPDX-License-Identifier: MIT
"""Build only the separate T8 protection/contact/USON draft; no routing."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import uuid
import xml.etree.ElementTree as ET

import draft_wing_placement as wing
import place_handbell as base
from kicad_sexpr import apply_edits, load, loads, pcb_net_name
from placement_geometry import footprint_bounds

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "hardware" / "handbell" / "iterations" / "wing-draft"
OUTPUT = SOURCE.parent / "t8-protected-draft"
MEASUREMENTS = ROOT / "docs" / "measurements" / "2026-09-11-shell-speaker-inputs.json"
WORKING_STATIONS = json.loads(MEASUREMENTS.read_text())["working_cad_profile"]["inside_stations"]
CLI = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "KiCad" / "10.0" / "bin" / "kicad-cli.exe"
PROTECTION = {"U6", "Q5", "R25", "R26", "R27", "R28", "R29", "C30"}
CONTACTS = {"BT1", "BT2"}
NEW_PINS = {
    "U6": {"1": None, "2": "PROT_COUT", "3": "PROT_DOUT", "4": "CELL_NEG",
           "5": "PROT_BAT", "6": "PROT_VM"},
    "Q5": {"A1": "CELL_NEG", "C1": "CELL_NEG", "B1": "PROT_DOUT",
           "A2": "PROT_FET_RETURN", "C2": "PROT_FET_RETURN", "B2": "PROT_COUT"},
    "R25": {"1": "VBAT", "2": "PROT_BAT"},
    "R26": {"1": "PROT_VM", "2": "GND"},
    "R27": {"1": "PROT_FET_RETURN", "2": "GND"},
    "R28": {"1": "PROT_DOUT", "2": "CELL_NEG"},
    "R29": {"1": "PROT_COUT", "2": "PROT_FET_RETURN"},
    "C30": {"1": "PROT_BAT", "2": "CELL_NEG"},
    "BT1": {"1": "VBAT"}, "BT2": {"1": "CELL_NEG"},
}
PARTS = {
    "U6": ("BQ29700DSER", "T8:BQ29700_DSE6", "T8:BQ29700",
           "https://www.ti.com/lit/ds/symlink/bq2970.pdf", .8),
    "Q5": ("CSD83325L", "T8:CSD83325L_YJE6", "T8:CSD83325L",
           "https://www.ti.com/lit/ds/symlink/csd83325l.pdf", .22),
    "R25": ("330R", "Adafruit Feather RP2040 Prop-Maker-import-fps:_0402NO", "T8:R",
            "https://www.ti.com/lit/ds/symlink/bq2970.pdf", .65),
    "R26": ("2.2k", "Adafruit Feather RP2040 Prop-Maker-import-fps:_0402NO", "T8:R",
            "https://www.ti.com/lit/ds/symlink/bq2970.pdf", .65),
    "R27": ("33m 1% 0.5W", "T8:ERJ6BW_0805", "T8:R",
            "https://industrial.panasonic.com/ww/products/pt/thick-film-chip-resistors", .7),
    "R28": ("5.1M gate discharge", "Adafruit Feather RP2040 Prop-Maker-import-fps:_0402NO", "T8:R",
            "https://www.ti.com/lit/ds/symlink/bq2970.pdf", .65),
    "R29": ("5.1M gate discharge", "Adafruit Feather RP2040 Prop-Maker-import-fps:_0402NO", "T8:R",
            "https://www.ti.com/lit/ds/symlink/bq2970.pdf", .65),
    "C30": ("100n 16V X7R", "Adafruit Feather RP2040 Prop-Maker-import-fps:_0402NO", "T8:C",
            "https://www.ti.com/lit/ds/symlink/bq2970.pdf", .65),
    "BT1": ("Keystone 254 POS", "T8:Keystone_254_RevC", "T8:Contact",
            "https://ken.keyeuro.eu/pdf/254.pdf", 16.59),
    "BT2": ("Keystone 254 NEG", "T8:Keystone_254_RevC", "T8:Contact",
            "https://ken.keyeuro.eu/pdf/254.pdf", 16.59),
}
MPNS = {"U1": "W25Q16JVUXIQ TR", "U6": "BQ29700DSER", "Q5": "CSD83325L",
        "R25": "RC0402FR-07330RL", "R26": "RC0402FR-072K2L",
        "R27": "ERJ-6BWFR033V", "C30": "GRM155R71C104KA88D",
        "R28": "RC0402FR-075M1L", "R29": "RC0402FR-075M1L",
        "BT1": "254", "BT2": "254"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "digital-handbell/t8-draft/" + name))


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def label(name, x, y, justify="left"):
    kind = 'global_label' if name in {"VBAT", "GND"} else 'label'
    shape = '(shape input)' if kind == 'global_label' else ''
    return (f'({kind} {json.dumps(name)} {shape} (at {x:g} {y:g} 0) '
            f'(effects (font (size 1.016 1.016)) (justify {justify} bottom)) '
            f'(uuid "{uid(f"label/{name}/{x}/{y}")}"))')


def wire(x1, y1, x2, y2):
    return (f'(wire (pts (xy {x1:g} {y1:g}) (xy {x2:g} {y2:g})) '
            f'(stroke (width 0) (type default)) (uuid "{uid(f"wire/{x1}/{y1}/{x2}/{y2}")}"))')


def note(text, x, y, size=1.27):
    return (f'(text {json.dumps(text)} (at {x:g} {y:g} 0) '
            f'(effects (font (size {size:g} {size:g})) (justify left top)) '
            f'(uuid "{uid("note/"+text)}"))')


def symbol_library(name, pins, width=15.24, height=15.24, graphic=""):
    stem = name.split(":")[-1]
    pin_text = []
    for number, function, kind, x, y, angle in pins:
        pin_text.append(
            f'(pin {kind} line (at {x:g} {y:g} {angle}) (length 2.54) '
            f'(name "{function}" (effects (font (size 1.016 1.016)))) '
            f'(number "{number}" (effects (font (size 1.016 1.016)))))')
    return (f'(symbol "{name}" (pin_names (offset 0.508)) (in_bom yes) (on_board yes) '
            f'(property "Reference" "U" (at 0 {height/2+2.54:g} 0) (effects (font (size 1.27 1.27)))) '
            f'(property "Value" "{stem}" (at 0 {-height/2-2.54:g} 0) (effects (font (size 1.27 1.27)))) '
            '(property "Footprint" "" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27)))) '
            f'(symbol "{stem}_0_1" (rectangle (start {-width/2:g} {height/2:g}) '
            f'(end {width/2:g} {-height/2:g}) (stroke (width .254) (type default)) '
            f'(fill (type background))) {graphic}) '
            f'(symbol "{stem}_1_1" {" ".join(pin_text)}))')


PIN_DEFS = {
    "T8:BQ29700": [
        ("5", "BAT", "power_in", -10.16, 5.08, 0),
        ("4", "VSS_CELL_NEG", "power_in", -10.16, -5.08, 0),
        ("3", "DOUT", "output", 10.16, 5.08, 180),
        ("2", "COUT", "output", 10.16, 0, 180),
        ("6", "V-", "input", 10.16, -5.08, 180),
        ("1", "NC", "no_connect", 0, 10.16, 270),
    ],
    "T8:CSD83325L": [
        ("A1", "S1", "passive", -10.16, -2.54, 0),
        ("C1", "S1", "passive", -10.16, -2.54, 0),
        ("B1", "G1_DSG", "input", -10.16, 5.08, 0),
        ("A2", "S2", "passive", 10.16, -2.54, 180),
        ("C2", "S2", "passive", 10.16, -2.54, 180),
        ("B2", "G2_CHG", "input", 10.16, 5.08, 180),
    ],
    "T8:R": [("1", "1", "passive", -5.08, 0, 0), ("2", "2", "passive", 5.08, 0, 180)],
    "T8:C": [("1", "1", "passive", -5.08, 0, 0), ("2", "2", "passive", 5.08, 0, 180)],
    "T8:Contact": [("1", "METAL", "passive", 5.08, 0, 180)],
}


def instance(ref, x, y, sheet_uuid):
    value, footprint, lib_id, datasheet, _ = PARTS[ref]
    properties = {"Reference": ref, "Value": value, "Footprint": footprint,
                  "Datasheet": datasheet, "MPN": MPNS[ref]}
    fields = []
    for key, val in properties.items():
        offset = 3.81 if lib_id in {"T8:R", "T8:C", "T8:Contact"} else 12.7
        fy = y - offset if key == "Reference" else y + offset if key == "Value" else y
        fields.append(f'(property "{key}" {json.dumps(val)} (at {x:g} {fy:g} 0) '
                      f'{"(hide yes)" if key not in {"Reference", "Value"} else ""} '
                      '(effects (font (size 1.016 1.016))))')
    pins = "".join(f'(pin "{pin[0]}" (uuid "{uid(ref+"/"+pin[0])}"))' for pin in PIN_DEFS[lib_id])
    result = [f'(symbol (lib_id "{lib_id}") (at {x:g} {y:g} 0) (unit 1) (in_bom yes) '
              f'(on_board yes) (dnp no) (uuid "{uid(ref)}") {" ".join(fields)} {pins} '
              f'(instances (project "handbell" (path "/{sheet_uuid}" (reference "{ref}") (unit 1)))))']
    seen = set()
    for number, _, _, dx, dy, angle in PIN_DEFS[lib_id]:
        if (dx, dy) in seen:
            continue
        seen.add((dx, dy))
        net = NEW_PINS[ref][number]
        px, py = x + dx, y - dy
        if net is None:
            result.append(f'(no_connect (at {px:g} {py:g}) (uuid "{uid(ref+"/nc")}"))')
        else:
            endx = px - 5.08 if angle == 0 else px + 5.08
            result.extend([wire(px, py, endx, py), label(net, endx, py, "right" if angle == 0 else "left")])
    return "\n".join(result)


def make_schematic():
    text, sch = load(SOURCE / "handbell.kicad_sch")
    edits, additions, libraries = [], [], []
    for lib, pins in PIN_DEFS.items():
        dimensions = (5.08, 2.54) if lib in {"T8:R", "T8:C", "T8:Contact"} else (15.24, 15.24)
        libraries.append(symbol_library(lib, pins, *dimensions))
    old_flash = next(s for s in sch.child("lib_symbols").children("symbol")
                     if s.atoms()[1] == "Handbell:SPIFLASH_8PIN_4X4")
    flash = text[old_flash.start:old_flash.end].replace(
        "Handbell:SPIFLASH_8PIN_4X4", "T8:W25Q16JVUX").replace("SPIFLASH_8PIN_4X4_", "W25Q16JVUX_")
    flash = flash.replace("Adafruit Feather RP2040 Prop-Maker-import-fps:USON8_4X4", "T8:Winbond_USON8_UX_2x3")
    libraries.append(flash)
    ls = sch.child("lib_symbols")
    edits.append((ls.end - 1, ls.end - 1, "\n" + "\n".join(libraries)))
    for node in sch.children():
        if node.head == "symbol":
            ref = node.properties().get("Reference")
            if ref in {"X1", "#U$22", "#U$16"}:
                edits.append((node.start, node.end, ""))
            elif ref == "U1":
                for field, value in {"Value": "W25Q16JVUXIQ TR / 2MB",
                                     "Footprint": "T8:Winbond_USON8_UX_2x3",
                                     "Datasheet": "https://www.winbond.com/resource-files/W25Q16JV%20SPI%20RevI%2012242024.pdf"}.items():
                    prop = next(p for p in node.children("property") if p.atoms()[1] == field)
                    edits.append((prop.items[2].start, prop.items[2].end, json.dumps(value)))
                lib_id = node.child("lib_id").items[1]
                edits.append((lib_id.start, lib_id.end, '"T8:W25Q16JVUX"'))
                edits.append((node.end - 1, node.end - 1,
                              '(property "MPN" "W25Q16JVUXIQ TR" (at 284.48 109.22 0) (hide yes) '
                              '(effects (font (size 1.27 1.27))))'))
        elif node.head == "wire" and node.value("uuid") in {
            "1b611772-0ee1-4cde-af14-cfa68502f896", "1ebb9921-8b7d-44b4-a11c-87f19dee0642",
            "f73098f4-fbb6-4530-8e21-996e731c13d8", "f93824fd-d3f0-4597-8cb5-d207b74f4880"}:
            edits.append((node.start, node.end, ""))
        elif node.head == "junction" and node.child("at").atoms()[1:] in [
                ["231.14", "60.96"], ["231.14", "63.5"]]:
            edits.append((node.start, node.end, ""))
    paper = sch.child("paper")
    edits.append((paper.start, paper.end, '(paper "User" 425.45 431.8)'))
    title = sch.child("title_block")
    for key, val in (("title", "T8 protected contact draft - NOT FOR LIVE CELL / FABRICATION"),
                     ("rev", "0.4-t8-draft"), ("date", "2026-09-11")):
        atom = title.child(key).items[1]
        edits.append((atom.start, atom.end, json.dumps(val)))
    placements = {"BT1": (35.56, 332.74), "BT2": (35.56, 375.92),
                  "R25": (99.06, 327.66), "C30": (99.06, 365.76),
                  "U6": (165.10, 347.98), "Q5": (246.38, 347.98),
                  "R27": (317.50, 350.52), "R26": (317.50, 383.54)}
    placements.update(R28=(205.74, 378.46), R29=(266.70, 378.46))
    additions.extend(instance(ref, x, y, sch.value("uuid")) for ref, (x, y) in placements.items())
    # Explicit flags model the raw cell supply and its resistively filtered BAT supply.
    flag = next(s for s in sch.children("symbol") if s.value("lib_id") == "power:PWR_FLAG")
    for i, (net, x, y) in enumerate([("CELL_NEG", 73.66, 398.78), ("PROT_BAT", 124.46, 398.78)]):
        raw = text[flag.start:flag.end]
        n = loads(raw)
        at = n.child("at")
        ox, oy = map(float, at.atoms()[1:3])
        changes = []
        for item in n.walk():
            if item.head == "at":
                a = item.atoms()
                changes.extend([(item.items[1].start, item.items[1].end, f"{float(a[1])-ox+x:g}"),
                                (item.items[2].start, item.items[2].end, f"{float(a[2])-oy+y:g}")])
            if item.head == "uuid":
                changes.append((item.items[1].start, item.items[1].end,
                                json.dumps(uid("flag/"+net+"/"+item.atoms()[1]))))
            if item.head == "property" and item.atoms()[1] == "Reference":
                changes.append((item.items[2].start, item.items[2].end, f'"#FLG0{90+i}"'))
            if item.head == "reference":
                changes.append((item.items[1].start, item.items[1].end, f'"#FLG0{90+i}"'))
        additions.extend([apply_edits(raw, changes), label(net, x, y)])
    additions.extend([
        note("T8 LOW-SIDE PROTECTION: raw CELL_NEG is NOT board/USB GND", 20.32, 302.26, 2.032),
        note("BQ29700 + common-drain dual N-FET + 33mR series sense: all charge/load return crosses cutoff.",
             20.32, 309.88),
        note("No parallel JST battery inlet. BT1/BT2 are identical Keystone254revC SMT contacts.", 20.32, 314.96),
        note("Internal body diodes: S1(CELL_NEG) -> common D <- S2(PROT_FET_RETURN).",
             180.34, 398.78),
        note("DOUT drives G1: blocks discharge return. COUT drives G2: blocks charge return.",
             180.34, 403.86),
        note("NO LIVE CELL: reverse insertion, cell-temperature charging and charge-profile gates OPEN.",
             20.32, 411.48),
        note("R8 stays 5.1k (~196mA; AC termination~14.7mA). NOT a complete BMS or safety approval.",
             20.32, 416.56),
    ])
    edits.append((sch.end - 1, sch.end - 1, "\n" + "\n".join(additions)))
    write(OUTPUT / "handbell.kicad_sch", apply_edits(text, edits))
    local = [s.replace('"T8:', '"', 1) for s in libraries]
    write(OUTPUT / "T8.kicad_sym", '(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n'
          + "\n".join(local) + "\n)\n")
    shutil.copyfile(SOURCE / "handbell.kicad_pro", OUTPUT / "handbell.kicad_pro")
    for name, entry in [
        ("fp-lib-table", '(lib (name "T8") (type "KiCad") (uri "${KIPRJMOD}/T8.pretty") (options "") (descr "Original factual-drawing implementations"))'),
        ("sym-lib-table", '(lib (name "T8") (type "KiCad") (uri "${KIPRJMOD}/T8.kicad_sym") (options "") (descr "T8 protection and flash"))'),
    ]:
        src = (SOURCE / name).read_text()
        write(OUTPUT / name, src[:src.rfind(")")] + entry + "\n)\n")


def fp_pad(number, x, y, w, h, shape="rect", layers='"F.Cu" "F.Paste" "F.Mask"', extra=""):
    return (f'(pad "{number}" smd {shape} (at {x:g} {y:g}) (size {w:g} {h:g}) '
            f'(layers {layers}) {extra})')


def footprint(name, w, h, pads, fab=None, courtyard=None):
    fw, fh = fab or (w, h)
    cw, ch = courtyard or (max(w, fw) + .5, max(h, fh) + .5)
    return (f'(footprint "{name}" (version 20260206) (generator "pcbnew") (layer "F.Cu") '
            '(attr smd) (property "Reference" "REF**" (at 0 0) (layer "F.Fab") '
            '(effects (font (size .8 .8) (thickness .12)))) '
            f'(property "Value" "{name}" (at 0 {fh/2+1:g}) (layer "F.Fab") '
            '(hide yes) (effects (font (size .8 .8) (thickness .12)))) '
            f'(fp_rect (start {-fw/2:g} {-fh/2:g}) (end {fw/2:g} {fh/2:g}) '
            '(stroke (width .05) (type solid)) (fill none) (layer "F.Fab")) '
            f'(fp_rect (start {-cw/2:g} {-ch/2:g}) (end {cw/2:g} {ch/2:g}) '
            '(stroke (width .05) (type solid)) (fill none) (layer "F.CrtYd")) '
            + "\n".join(pads) + "\n)\n")


def make_footprints():
    pads = [fp_pad(i + 1, -1.25, -.75 + .5*i, .6, .3) for i in range(4)]
    pads += [fp_pad(8 - i, 1.25, -.75 + .5*i, .6, .3) for i in range(4)]
    pads.append(fp_pad("PAD", 0, 0, .2, 1.6, layers='"F.Cu" "F.Mask"'))
    pads.append(fp_pad("", 0, 0, .15, 1.2, layers='"F.Paste"'))
    # The UX exposed metal is a narrow D1=0.20 x E1=1.60 strip, NOT the XG 2.3x3 pad.
    files = {"Winbond_USON8_UX_2x3": footprint("Winbond_USON8_UX_2x3", 3.1, 2.1, pads, (3, 2))}
    pads = []
    for i in range(3):
        # Independently adapted all-NSMD option, using the drawing's exposed-metal
        # dimensions; not the example's left-side SMD copper expansion.
        pads.append(fp_pad(i+1, -.55 if i == 0 else -.6, -.5+.5*i,
                           .8 if i == 0 else .7, .25, "roundrect",
                           extra="(roundrect_rratio .2) (solder_mask_margin .05)"))
        pads.append(fp_pad(6-i, .6, -.5+.5*i, .7, .25, "roundrect",
                           extra="(roundrect_rratio .2) (solder_mask_margin .05)"))
    files["BQ29700_DSE6"] = footprint("BQ29700_DSE6", 2.0, 1.5, pads, (1.5, 1.5))
    pads = [fp_pad(f"{row}{col}", x, y, .3, .3, "circle", extra="(solder_mask_margin .05)")
            for row, y in (("A", -.65), ("B", 0), ("C", .65))
            for col, x in ((1, -.325), (2, .325))]
    files["CSD83325L_YJE6"] = footprint("CSD83325L_YJE6", 1.15, 2.2, pads)
    files["ERJ6BW_0805"] = footprint("ERJ6BW_0805", 3.0, 1.4,
                                   [fp_pad(1, -1.0, 0, 1.0, 1.4), fp_pad(2, 1.0, 0, 1.0, 1.4)],
                                   (2.0, 1.25))
    pads = [fp_pad("1", -8.005, 0, 4.24, 5.2), fp_pad("1", 8.005, 0, 4.24, 3.3)]
    files["Keystone_254_RevC"] = footprint("Keystone_254_RevC", 20.25, 17.0, pads,
                                         (19.88, 17.0), (20.75, 17.5))
    for name, text in files.items():
        write(OUTPUT / "T8.pretty" / (name + ".kicad_mod"), text)


def read_parts():
    text, sch = load(OUTPUT / "handbell.kicad_sch")
    symbols = {s.properties()["Reference"]: s for s in sch.children("symbol")
               if not s.properties()["Reference"].startswith("#") and s.value("unit") == "1"}
    old = json.loads((SOURCE / "placement-manifest.json").read_text())
    poses = {r["reference"]: r for r in old["components"]}
    _, old_board = load(SOURCE / "handbell.kicad_pcb")
    old_fp = {p.properties()["Reference"]: p for p in old_board.children("footprint")}
    xml = ET.parse(OUTPUT / "reports" / "handbell-netlist.xml").getroot()
    parts = {}
    for c in xml.findall("components/comp"):
        ref, identifier = c.get("ref"), c.findtext("footprint")
        lib, name = identifier.split(":", 1)
        directory = OUTPUT / "T8.pretty" if lib == "T8" else base.LIBRARIES.get(lib, base.STANDARD / (lib + ".pretty"))
        raw_text, fp = load(directory / (name + ".kicad_mod"))
        raw, planning, has_courtyard = footprint_bounds(fp)
        if ref == "J2":
            raw[3] += .7
            planning[3] = max(planning[3], raw[3]+.25)
        cx, cy = (raw[0]+raw[2])/2, (raw[1]+raw[3])/2
        copper = ref in base.COPPER
        if ref in poses:
            row = poses[ref]
            x, y, angle, side = row["x_mm"], row["y_mm"], -row["rotation_deg"], row["side"]
        elif ref in old_fp:
            at = list(map(float, old_fp[ref].child("at").atoms()[1:]))
            angle = at[2] if len(at) > 2 else 0
            dx, dy = base.rotate(cx, cy, angle)
            x, y, side = at[0]-100+dx, at[1]-100+dy, old_fp[ref].value("layer")[0]
        else:
            x, y, angle, side = 0, 0, 0, "B" if ref in CONTACTS else "F"
        p = {"ref": ref, "value": c.findtext("value"), "footprint": identifier, "text": raw_text,
             "fields": {**symbols[ref].properties(), **{f.get("name"): f.text or "" for f in c.findall("fields/field")}},
             "raw_cx": cx, "raw_cy": cy, "raw_w": raw[2]-raw[0], "raw_h": raw[3]-raw[1],
             "plan_w": 2*max(cx-planning[0], planning[2]-cx),
             "plan_h": 2*max(cy-planning[1], planning[3]-cy), "has_courtyard": has_courtyard,
             "height": (PARTS[ref][4] if ref in PARTS else .6 if ref == "U1" else
                        0 if copper else base.height(ref, identifier)),
             "side": side, "dnp": ref == "C29", "copper_only": copper,
             "x": x, "y": y, "angle": angle, "cluster": poses.get(ref, {}).get("cluster"),
             "core_cap_adjustment_local_mm": poses.get(ref, {}).get("core_cap_adjustment_local_mm")}
        parts[ref] = p
    for ref, (x, y, angle) in {
        "U6": (-12.3, 7.0, 0), "Q5": (-15.2, 7.0, 90),
        "R25": (-12.4, 9.0, 0), "C30": (-12.4, 5.2, 0),
        "R26": (-15.4, 5.2, 0), "R27": (-15.4, 9.2, 0),
        "R28": (-18.0, 6.4, 90), "R29": (-18.0, 9.0, 90),
        "BT1": (11.625, 0, 0), "BT2": (-11.625, 0, 180),
    }.items():
        parts[ref].update(x=x, y=y, angle=angle, cluster="protection" if ref in PROTECTION else "contact")
    # Place by the actual retained F.Fab mouth, not by the footprint envelope center.
    usb = parts["X6"]
    usb.update(y=-25.15 + 5.08 - usb["raw_cy"], angle=180)
    for p in parts.values():
        p["anchor_x"], p["anchor_y"] = p["x"], p["y"]
    return parts, xml, symbols, sch


def constraints(p, usb_back, front_z=20.5):
    if p["ref"] in CONTACTS | {"X6"}:
        return 0
    w, h = base.dimensions(p)
    physical_height = 0 if p["dnp"] or p["copper_only"] else p["height"]
    deepest = front_z + 1.6 + physical_height if p["side"] == "B" else front_z
    interval = next(((low, high) for low, high in zip(WORKING_STATIONS, WORKING_STATIONS[1:])
                     if low["z_mm"] <= deepest <= high["z_mm"]), None)
    if interval is None:
        raise ValueError("Placement extends outside the documented inside-station range")
    low, high = interval
    cavity_radius = (low["diameter_mm"] + (high["diameter_mm"]-low["diameter_mm"]) *
                     (deepest-low["z_mm"])/(high["z_mm"]-low["z_mm"]))/2
    limit = min(21.0, cavity_radius-.5)
    penalty = max(0, math.hypot(abs(p["x"])+w/2, abs(p["y"])+h/2)-limit)**2
    for m in wing.MOUNTS:
        penalty += max(0, 3.2-wing.rectangle_distance(p, m["x_mm"], m["y_mm"]))**2
    if p["side"] == "B":
        dx = min(p["x"]+w/2, 19)-max(p["x"]-w/2, -19)
        dy = min(p["y"]+h/2, 10)-max(p["y"]-h/2, -10)
        penalty += max(dx, 0)*max(dy, 0) + base.pair_overlap(p, usb_back)
    elif physical_height > 1.0:
        penalty += max(0, 11.5-wing.rectangle_distance(p, 0, 0))**2
    return penalty


def solve(parts, steps, front_z=20.5):
    rng = random.Random(163404)
    rows = list(parts.values())
    usb_back = {**wing.USB_BACK, "y": parts["X6"]["y"]}
    fixed = set(base.CORE) | wing.BOOST | wing.AMP | CONTACTS | {"X6"}
    units = [[parts[r] for r in sorted(PROTECTION)]]
    units += [[p] for p in rows if p["ref"] not in fixed | PROTECTION]

    def overlap(a, b):
        if a["side"] != b["side"] or (a.get("cluster") and a.get("cluster") == b.get("cluster")):
            return 0
        return base.pair_overlap(a, b)

    def local(unit):
        ids = {p["ref"] for p in unit}
        return sum(400*constraints(p, usb_back, front_z) +
                   100*sum(overlap(p, q) for q in rows if q["ref"] not in ids) +
                   .02*((p["x"]-p["anchor_x"])**2+(p["y"]-p["anchor_y"])**2) for p in unit)

    for i in range(steps):
        unit = rng.choice(units)
        previous = [(p["x"], p["y"], p["angle"]) for p in unit]
        before = local(unit)
        fraction = i/max(steps, 1)
        scale = .9*(1-fraction)+.004
        dx, dy = rng.uniform(-scale, scale), rng.uniform(-scale, scale)
        turn = rng.choice((-90, 90)) if rng.random() < .008 else 0
        cx = sum(p["x"] for p in unit)/len(unit)
        cy = sum(p["y"] for p in unit)/len(unit)
        for p in unit:
            x, y = base.rotate(p["x"]-cx, p["y"]-cy, turn)
            p.update(x=x+cx+dx, y=y+cy+dy, angle=(p["angle"]+turn)%360)
        after = local(unit)
        temperature = .3*(1-fraction)**3+.00001
        if after > before and rng.random() >= math.exp(min(0, (before-after)/temperature)):
            for p, (x, y, a) in zip(unit, previous):
                p.update(x=x, y=y, angle=a)
    return {
        "intercluster_overlaps": [{"left": a["ref"], "right": b["ref"], "area_mm2": overlap(a, b)}
                                 for i, a in enumerate(rows) for b in rows[i+1:] if overlap(a, b) > .001],
        "constraint_violations": [{"reference": p["ref"], "penalty": constraints(p, usb_back, front_z)}
                                 for p in rows if constraints(p, usb_back, front_z) > .001],
        "retained_source_cluster_planning_overlaps": [
            {"left": a["ref"], "right": b["ref"], "area_mm2": base.pair_overlap(a, b)}
            for i, a in enumerate(rows) for b in rows[i+1:]
            if a.get("cluster") and a.get("cluster") == b.get("cluster") and base.pair_overlap(a, b) > .001],
    }, usb_back


def outline(usb_mouth_y=-25.15):
    r, tab_y, usb_x = 21.5, 2.3, 5.75
    right_angle = math.asin(tab_y/r)
    usb_angle = math.acos(usb_x/r)
    points = []
    def arc(start, end):
        count = math.ceil((end-start)*r/.75)
        points.extend([[r*math.cos(start+(end-start)*i/count), r*math.sin(start+(end-start)*i/count)]
                       for i in range(count+1)])
    arc(right_angle, math.pi-right_angle)
    points += [[-22.25, tab_y], [-22.25, -tab_y]]
    arc(math.pi+right_angle, math.pi+usb_angle)
    tongue_y = usb_mouth_y + 1.05
    points += [[-usb_x, tongue_y], [usb_x, tongue_y]]
    arc(2*math.pi-usb_angle, 2*math.pi-right_angle)
    points += [[22.25, -tab_y], [22.25, tab_y]]
    return points


def contact_interface(front_z=20.5):
    result = {
        "mpn": "Keystone 254", "drawing": "254 revision C, 2023-09-14",
        "source": "https://ken.keyeuro.eu/pdf/254.pdf",
        "coordinate_frame": "Common assembly XYZ; right contact BT1; left BT2 is X/Y rotation180.",
        "pcb_side": "B", "pcb_z_mm": 22.1, "cell_axis": "X",
        "cell_nominal": {"diameter_mm": 16.4, "total_length_mm": 34.0, "center_mm": [0, 0, 31.88],
                         "positive_end_x_mm": 17.0, "negative_end_x_mm": -17.0,
                         "status": "Retailer approximate button-top length; manufacturer generic button addition conflicts. Not maximum/tolerance."},
        "contacts": [{"reference": ref, "polarity": polarity, "center_mm": [sign*11.625, 0, 22.1],
                      "rotation_deg": 0 if sign == 1 else 180, "net": net,
                      "pads": [{"center_mm": [sign*3.62, 0, 22.1], "size_mm": [4.24, 5.2]},
                               {"center_mm": [sign*19.63, 0, 22.1], "size_mm": [4.24, 3.3]}]}
                     for ref, polarity, sign, net in (("BT1", "+", 1, "VBAT"), ("BT2", "-", -1, "CELL_NEG"))],
        "drawing_dimensions_mm": {"steel_thickness": .30, "base_length": 19.88, "base_width": 11.13,
                                  "overall_height_nominal": 16.59, "overall_height_tolerance": .38,
                                  "dimple_height_nominal": 9.78, "dimple_height_tolerance": .38,
                                  "unloaded_transverse_envelope_reference": 16.61, "ear_axial_length": 9.53,
                                  "spring_face_width": 8.89, "outer_solder_tab_width": 3.18},
        "right_contact_original_primitives": {
            "status": "Original kinematic screening interpretation, NOT vendor CAD or measured loaded spring geometry. Mirror for BT2.",
            "base_tabs": [{"x_min": 1.685, "x_max": 5.685, "y_width": 5.08, "z_min": 22.1, "thickness": .30},
                          {"x_min": 18.685, "x_max": 21.565, "y_width": 3.18, "z_min": 22.1, "thickness": .30}],
            "under_cell_base": {"x_min": 5.685, "x_max": 18.685, "y_width": 11.13,
                                "z_min": 22.1, "thickness": .30},
            "spring_xz_polyline": [[18.685, 22.4], [18.685, 24.0], [17.8, 28.0],
                                   [17.0, 31.88], [17.8, 35.5], [18.2, 38.69]],
            "spring_y_width": 8.89, "spring_thickness": .30,
            "spring_surface": "Polyline is the cell-facing surface; build thickness toward +X for BT1, -X for mirrored BT2, NOT symmetrically into the cell.",
            "ears": {"x_min": 5.685, "axial_length": 9.53, "axis_center_yz": [0, 31.88],
                     "inner_radius": 8.2, "thickness": .30, "angle_degrees": [[-80, 52], [128, 260]],
                     "status": "Assumed conforming loaded arcs, not an allowed travel/force envelope; reconcile unloaded16.61 with actual samples."},
            "candidate_loaded_outer_width_mm": 17.0,
        },
        "pair_inner_pad_edge_gap_mm": 3.0,
        "pair_gap_basis": "Project adjustable spacing; <= drawing CR123A L3.66max. L is NOT cell length.",
        "loaded_end_contact_x_mm": [-17.0, 17.0],
        "loaded_state_gate": "Dimple longitudinal datum, free span, spring travel/load and exact positive button geometry not specified; no preload qualified.",
        "insulation_gate": "CELL_NEG/cell can/contact metal must not touch USB GND, grounded screws or metal shell. Plastic capture carries mechanical load.",
    }
    shift = front_z - 20.5
    result["pcb_z_mm"] = round(front_z + 1.6, 6)
    result["cell_nominal"]["center_mm"][2] = round(31.88 + shift, 6)
    for contact in result["contacts"]:
        contact["center_mm"][2] = result["pcb_z_mm"]
        for pad in contact["pads"]:
            pad["center_mm"][2] = result["pcb_z_mm"]
    primitives = result["right_contact_original_primitives"]
    for body in [*primitives["base_tabs"], primitives["under_cell_base"]]:
        body["z_min"] = result["pcb_z_mm"]
    for point in primitives["spring_xz_polyline"]:
        point[1] = round(point[1] + shift, 6)
    primitives["ears"]["axis_center_yz"][1] = round(31.88 + shift, 6)
    return result


def generate_board(parts, xml, symbols, sch, planning, usb_back, steps,
                   front_z=20.5, usb_mouth_y=-25.15, guard_mm=None, pose_seed=None):
    pin_nets, pin_info = {}, {}
    for net in xml.findall("nets/net"):
        for pin in net.findall("node"):
            pin_nets.setdefault(pin.get("ref"), {})[pin.get("pin")] = net.get("name")
            pin_info.setdefault(pin.get("ref"), {})[pin.get("pin")] = pin.attrib
    footprints = [wing.rendered_footprint(p, pin_nets[p["ref"]], pin_info[p["ref"]],
                                         sch.value("uuid"), symbols[p["ref"]].value("uuid")) for p in parts.values()]
    footprints.extend(wing.mounting_footprint(m) for m in wing.MOUNTS)
    source_text, source_board = load(SOURCE / "handbell.kicad_pcb")
    layers = source_board.child("layers")
    perimeter = outline(usb_mouth_y)
    edges = []
    for i, (a, b) in enumerate(zip(perimeter, perimeter[1:]+perimeter[:1])):
        edges.append(f'(gr_line (start {100+a[0]:.6f} {100+a[1]:.6f}) '
                     f'(end {100+b[0]:.6f} {100+b[1]:.6f}) (stroke (width .05) (type solid)) '
                     f'(layer "Edge.Cuts") (uuid "{uid("edge/"+str(i))}"))')
    pcb = ('(kicad_pcb (version 20260206) (generator "pcbnew") (generator_version "10.0") '
           '(general (thickness 1.6)) (paper "A4") '
           '(title_block (title "T8 protected contact DRAFT - UNROUTED / NOT FOR LIVE CELL") (rev "0.4-t8-draft") '
           '(comment 1 "Adafruit 5768/4438/4654-derived CC BY-SA3.0; see LICENSE and notices.")) '
           + source_text[layers.start:layers.end] + '(setup (pad_to_mask_clearance 0))\n'
           + "\n".join(footprints+edges) + "\n)\n")
    write(OUTPUT / "handbell.kicad_pcb", pcb)
    usb = parts["X6"]
    usb_origin_y = usb["y"]+usb["raw_cy"]
    fit_evidence = OUTPUT / "reports" / "stack-shift-screen-evidence.json"
    manifest = {
        "schema_version": 2, "units": "mm", "status": "T8 native placed engineering draft; no routing/live-cell/fabrication approval",
        "board": {"diameter_mm": 43.0, "thickness_mm": 1.6, "front_z_mm": front_z,
                  "front_face": "speaker", "component_face": "mixed",
                  "outline_common_xy_mm": perimeter,
                  "outline_note": "D43 body with original local contact-pad support tabs and supported USB tongue; polygonized circle segments <=0.75mm.",
                  "contact_tabs": {"outer_x_mm": 22.25, "half_width_y_mm": 2.3},
                  "usb_tongue": {"half_width_x_mm": 5.75, "outer_y_mm": round(usb_mouth_y+1.05, 6)}},
        "stack_translation_z_mm": round(front_z-20.5, 6),
        "speaker_front_z_mm": round(front_z-20.5, 6),
        "mechanical_guard_target_mm": guard_mm,
        "stack_shift_screen_evidence": {
            "path": "reports/stack-shift-screen-evidence.json",
            "sha256": sha(fit_evidence),
            "scope": "Bounded external guard-stock BRep only; final full mechanical assembly must rebind to this native manifest.",
        } if fit_evidence.exists() else None,
        "measurement_source": str(MEASUREMENTS.relative_to(ROOT)),
        "measurement_sha256": sha(MEASUREMENTS),
        "planning_profile": "Station chords for 2D floorplanning only; complete mechanical BRep uses its explicitly declared curved working profile.",
        "placement_method": "Preserved recorded XY/angles; USB translation only" if pose_seed else "Seeded deterministic optimization",
        "placement_xy_seed_sha256": sha(OUTPUT / "placement-xy-seed.json") if pose_seed else None,
        "coordinate_convention": "Exact wing convention: common centered assembly XY; mathematical rotation=-native KiCad rotation. F speaker/B handle. Native origin100,100.",
        "generated_pcb_sha256": sha(OUTPUT / "handbell.kicad_pcb"),
        "schematic_sha256": sha(OUTPUT / "handbell.kicad_sch"),
        "baseline_pcb_sha256": sha(SOURCE / "handbell.kicad_pcb"),
        "baseline_schematic_sha256": sha(SOURCE / "handbell.kicad_sch"),
        "source_baseline": str(SOURCE.relative_to(ROOT)),
        "components": [{
            "reference": p["ref"], "value": p["value"], "mpn": MPNS.get(p["ref"], p["fields"].get("MPN", "")),
            "footprint": p["footprint"], "x_mm": p["x"], "y_mm": p["y"], "width_mm": p["raw_w"],
            "depth_mm": p["raw_h"], "height_mm": p["height"], "rotation_deg": -p["angle"], "side": p["side"],
            "z_min_mm": round(front_z-p["height"], 6) if p["side"] == "F" else round(front_z+1.6, 6),
            "z_max_mm": front_z if p["side"] == "F" else round(front_z+1.6+p["height"], 6),
            "height_source": "Manufacturer package maximum" if p["ref"] in {"U1", "U6", "Q5"} else
                             "254 drawing nominal; loaded geometry remains gate" if p["ref"] in CONTACTS else
                             "Unqualified component-height planning proxy",
            "proxy_kind": "dimensioned_contact_primitives" if p["ref"] in CONTACTS else "envelope",
            "geometry_interface": "battery-contact-interface.json" if p["ref"] in CONTACTS else None,
            "requires_shell_cutout": p["ref"] == "X6", "cluster": p.get("cluster"),
            "core_cap_adjustment_local_mm": p.get("core_cap_adjustment_local_mm"),
        } for p in parts.values() if not p["dnp"] and not p["copper_only"]],
        "mounting_holes": wing.MOUNTS, "battery_reservation": wing.BATTERY,
        "battery_contact_interface": "battery-contact-interface.json",
        "battery_contact_interface_sha256": sha(OUTPUT / "battery-contact-interface.json"),
        "usb_interface": {"reference": "X6", "native_origin_common_xy_mm": [0, usb_origin_y],
                          "body_mouth_center_common_xy_mm": [0, usb_mouth_y],
                          "body_fab_width_mm": 8.94, "body_fab_depth_mm": 7.35,
                          "body_back_y_mm": usb_origin_y+2.27,
                          "body_front_z_mm": round(front_z-3.5, 6), "body_back_z_mm": front_z,
                          "signal_ground_net": "GND",
                          "shell_anchor_nets": {"M1": None, "M2": None, "M3": None, "M4": None},
                          "shield_bond_status": "Retained shell-anchor pads unassigned; no reviewed shield bond. Insulate conductive shield independently.",
                          "mouth_basis": "Retained CUSB31-CFM2AX-01-X F.Fab y=5.08 transformed by180deg. Width/height are source/proxy, not qualified plug envelope.",
                          "support_gate": "Tongue requires matched shell opening and repeatable carrier support. Flush target at approximate midheight only; no physical USB approval."},
        "cross_face_keepouts": [usb_back], "dnp_footprint_reservations": ["C29"],
        "copper_only_features": [{"reference": p["ref"], "x_mm": p["x"], "y_mm": p["y"], "side": p["side"]}
                                 for p in parts.values() if p["copper_only"]],
        "planning": planning,
        "limits": ["No copper routing; all net assignments require routing before electrical continuity exists.",
                   "Core/boost/amplifier relative poses retained; new protector shares no copper/ground with raw-cell return except specified cutoff.",
                   "Contacts use thin kinematic geometry, not solid collision boxes. Loaded spring/positive button/current rating unqualified.",
                   "Temperature charge inhibit and reverse-insertion protection NOT implemented: no live cell authorization.",
                   "R8 remains5.1k; charger termination mismatch needs exact cell review.",
                   "Four inherited USB hole clearances remain open; no GUI parity approval transferred."],
    }
    write(OUTPUT / "placement-manifest.json", json.dumps(manifest, indent=2)+"\n")
    report = {"generated_pcb_sha256": manifest["generated_pcb_sha256"], "script_sha256": sha(__file__),
              "steps": steps, "seed": 163404, "fitted_by_side": dict(Counter(p["side"] for p in manifest["components"])),
              "front_z_mm": front_z, "usb_mouth_y_mm": usb_mouth_y, "guard_target_mm": guard_mm,
              "preserved_xy": bool(pose_seed),
              "physical_pads": sum(len(f.children("pad")) for f in loads(pcb).children("footprint")),
              "planning": planning,
              "editable_artifacts": {str(p.relative_to(OUTPUT)): sha(p) for p in
                                     [OUTPUT / "T8.kicad_sym", OUTPUT / "fp-lib-table", OUTPUT / "sym-lib-table",
                                      OUTPUT / "battery-contact-interface.json",
                                      *sorted((OUTPUT / "T8.pretty").glob("*.kicad_mod"))]}}
    write(OUTPUT / "placement-build-report.json", json.dumps(report, indent=2)+"\n")
    draw(manifest)
    with (OUTPUT / "reports" / "bom-draft.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Reference", "Value", "MPN", "Footprint", "Side", "Status"])
        for p in parts.values():
            writer.writerow([p["ref"], p["value"], MPNS.get(p["ref"], p["fields"].get("MPN", "")),
                             p["footprint"], p["side"], "DNP" if p["dnp"] else "copper-only" if p["copper_only"] else "fitted-draft"])
    print(json.dumps(report, indent=2))


def draw(manifest):
    import html
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1240" height="720" viewBox="0 0 1240 720">',
           '<rect width="1240" height="720" fill="white"/>',
           '<text x="25" y="28" font-family="sans-serif" font-size="20">T8 PROTECTED CONTACT DRAFT - UNROUTED / NOT FOR LIVE CELL</text>']
    for side, cx, title in (("F", 300, "F: speaker-facing electronics"), ("B", 925, "B: contacts + retained boost/audio wings")):
        cy, scale = 350, 11
        svg.append(f'<text x="{cx-265}" y="65" font-family="sans-serif" font-size="17">{title}</text>')
        points = " ".join(f"{cx+x*scale:.2f},{cy-y*scale:.2f}" for x, y in manifest["board"]["outline_common_xy_mm"])
        svg.append(f'<polygon points="{points}" fill="#f1f5f9" stroke="#334155"/>')
        if side == "B":
            svg.append(f'<rect x="{cx-17*scale}" y="{cy-8.2*scale}" width="{34*scale}" height="{16.4*scale}" '
                       'fill="#dcfce7" stroke="#15803d" stroke-dasharray="5,4"/>')
        for m in wing.MOUNTS:
            svg.append(f'<circle cx="{cx+m["x_mm"]*scale}" cy="{cy-m["y_mm"]*scale}" r="{3.2*scale}" fill="none" stroke="#15803d"/>')
        for p in manifest["components"]:
            if p["side"] != side:
                continue
            x, y = cx+p["x_mm"]*scale, cy-p["y_mm"]*scale
            color = "#fed7aa" if p["reference"] in PROTECTION else "#d8b4fe" if p["cluster"] == "core-refined" else "#bfdbfe"
            if p["reference"] in CONTACTS:
                sign = 1 if p["reference"] == "BT1" else -1
                for pad_x, pw, ph in ((sign*3.62, 4.24, 5.2), (sign*19.63, 4.24, 3.3)):
                    svg.append(f'<rect x="{cx+(pad_x-pw/2)*scale}" y="{cy-ph/2*scale}" width="{pw*scale}" height="{ph*scale}" fill="#d1d5db" stroke="#374151"/>')
            else:
                svg.append(f'<g transform="translate({x:.3f} {y:.3f}) rotate({-p["rotation_deg"]:g})"><rect '
                           f'x="{-p["width_mm"]*scale/2}" y="{-p["depth_mm"]*scale/2}" width="{p["width_mm"]*scale}" '
                           f'height="{p["depth_mm"]*scale}" fill="{color}" stroke="#334155" stroke-width=".6"/></g>')
            svg.append(f'<text x="{x}" y="{y+3}" text-anchor="middle" font-family="sans-serif" font-size="8">{html.escape(p["reference"])}</text>')
    svg += ['<text x="25" y="660" font-family="sans-serif" font-size="14">Common assembly XY, not mirrored photographs. Contact metal uses separate dimensioned primitives; drawing shows lands, not filled holders.</text>',
            '<text x="25" y="687" font-family="sans-serif" font-size="14">Tiny side pad-support tabs + USB tongue are intentional. Mechanical shell/capture/support must consume this exact manifest before routing.</text>', '</svg>']
    write(OUTPUT / "t8-placement.svg", "\n".join(svg)+"\n")


def guard():
    manifest_path = OUTPUT / "placement-manifest.json"
    prior = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for name, key in (("handbell.kicad_pcb", "generated_pcb_sha256"), ("handbell.kicad_sch", "schematic_sha256")):
        path = OUTPUT / name
        if path.exists() and sha(path) != prior.get(key):
            raise ValueError("Refusing to overwrite manually changed/untracked "+str(path))
    board = OUTPUT / "handbell.kicad_pcb"
    if board.exists() and any(load(board)[1].children(k) for k in ("segment", "via", "zone")):
        raise ValueError("Refusing to overwrite routed board")
    seed = OUTPUT / "placement-xy-seed.json"
    if prior.get("placement_xy_seed_sha256") and (
            not seed.exists() or sha(seed) != prior["placement_xy_seed_sha256"]):
        raise ValueError("Refusing changed or missing frozen XY seed")
    project = OUTPUT / "handbell.kicad_pro"
    if project.exists() and sha(project) != sha(SOURCE / project.name):
        raise ValueError("Refusing to overwrite changed rule/project settings")
    build = OUTPUT / "placement-build-report.json"
    if build.exists():
        for name, expected in json.loads(build.read_text()).get("editable_artifacts", {}).items():
            path = OUTPUT / name
            if not path.exists() or sha(path) != expected:
                raise ValueError("Refusing to overwrite changed library/interface: "+str(path))


def preserved_poses(parts):
    path = OUTPUT / "placement-xy-seed.json"
    if path.exists():
        seed = json.loads(path.read_text())
    else:
        old = json.loads((OUTPUT / "placement-manifest.json").read_text())
        components = {c["reference"]: c for c in old["components"]}
        _, board = load(OUTPUT / "handbell.kicad_pcb")
        poses = {}
        for fp in board.children("footprint"):
            ref = fp.properties()["Reference"]
            if ref.startswith("MH"):
                continue
            if ref in components:
                c = components[ref]
                poses[ref] = {"x": c["x_mm"], "y": c["y_mm"], "angle": -c["rotation_deg"], "side": c["side"]}
            else:
                p = parts[ref]
                at = list(map(float, fp.child("at").atoms()[1:]))
                side = fp.value("layer")[0]
                dx, dy = base.rotate(p["raw_cx"], -p["raw_cy"] if side == "B" else p["raw_cy"], at[2])
                poses[ref] = {"x": at[0]-100+dx, "y": at[1]-100+dy, "angle": at[2], "side": side}
        seed = {"status": "Recorded native XY before bounded axial/USB alternative; never re-optimize implicitly",
                "source_manifest_sha256": sha(OUTPUT / "placement-manifest.json"),
                "source_pcb_sha256": sha(OUTPUT / "handbell.kicad_pcb"), "poses": poses}
    if set(seed["poses"]) != set(parts):
        raise ValueError("Recorded XY inventory differs from the current native schematic")
    for ref, pose in seed["poses"].items():
        parts[ref].update(pose)
    return seed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=90000)
    parser.add_argument("--front-z", type=float, help="Common assembly F-surface Z; preserve speaker/cell relative stack.")
    parser.add_argument("--usb-mouth-y", type=float, help="Actual retained USB F.Fab mouth Y, not envelope center.")
    parser.add_argument("--guard-mm", type=float, choices=(1.0, 1.25, 1.5), help="Mechanical screening target, not safety approval.")
    parser.add_argument("--preserve-xy", action="store_true", help="Record/reuse existing native poses; move only USB in XY.")
    parser.add_argument("--preview", action="store_true", help="Evaluate the bounded alternative without writing CAD or a new manifest.")
    args = parser.parse_args()
    if args.steps < 0:
        parser.error("--steps must be nonnegative")
    guard()
    prior_path = OUTPUT / "placement-manifest.json"
    prior = json.loads(prior_path.read_text()) if prior_path.exists() else {}
    front_z = args.front_z if args.front_z is not None else prior.get("board", {}).get("front_z_mm", 20.5)
    usb_mouth_y = args.usb_mouth_y if args.usb_mouth_y is not None else prior.get(
        "usb_interface", {}).get("body_mouth_center_common_xy_mm", [0, -25.15])[1]
    guard_mm = args.guard_mm if args.guard_mm is not None else prior.get("mechanical_guard_target_mm")
    if not 12 <= front_z <= 22 or not -28 <= usb_mouth_y <= -22:
        parser.error("Bounded study accepts Fz12..22 and USB mouthY-28..-22 only")
    preserve = args.preserve_xy or (OUTPUT / "placement-xy-seed.json").exists()
    if args.preview and not preserve:
        parser.error("--preview requires existing native CAD and --preserve-xy")
    pose_seed = None
    if preserve:
        parts, xml, symbols, sch = read_parts()
        pose_seed = preserved_poses(parts)
        parts["X6"]["y"] = usb_mouth_y + 5.08 - parts["X6"]["raw_cy"]
        planning, usb_back = solve(parts, 0, front_z)
        if args.preview:
            print(json.dumps({"front_z_mm": front_z, "speaker_shift_z_mm": round(front_z-20.5, 6),
                              "cell_center_z_mm": contact_interface(front_z)["cell_nominal"]["center_mm"][2],
                              "usb_mouth_y_mm": usb_mouth_y, "guard_target_mm": guard_mm,
                              "planning": planning}, indent=2))
            return
        write(OUTPUT / "placement-xy-seed.json", json.dumps(pose_seed, indent=2)+"\n")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "reports").mkdir(exist_ok=True)
    make_footprints()
    make_schematic()
    write(OUTPUT / "battery-contact-interface.json", json.dumps(contact_interface(front_z), indent=2)+"\n")
    subprocess.run([str(CLI), "sch", "export", "netlist", "--format", "kicadxml", "--output",
                    str(OUTPUT / "reports" / "handbell-netlist.xml"), str(OUTPUT / "handbell.kicad_sch")],
                   check=True, cwd=ROOT, timeout=300)
    parts, xml, symbols, sch = read_parts()
    if preserve:
        preserved_poses(parts)
    parts["X6"]["y"] = usb_mouth_y + 5.08 - parts["X6"]["raw_cy"]
    steps = 0 if preserve else args.steps
    planning, usb_back = solve(parts, steps, front_z)
    generate_board(parts, xml, symbols, sch, planning, usb_back, steps,
                   front_z, usb_mouth_y, guard_mm, pose_seed)


if __name__ == "__main__":
    main()
