#!/usr/bin/env python3
"""Original September 13 printed bell. Headless FreeCAD, exact input binding.

Without --placement, explicitly writes DEVELOPMENT only. Final mode requires
all-front electronics and the unchanged, translated T8 contact interface.
"""
from __future__ import annotations

import argparse
import base64
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
import zipfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_mechanical as base
import build_t8_cartridge as helpers

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "mechanical" / "studies" / "2026-09-13-printed-bell"
T8 = ROOT / "mechanical" / "studies" / "2026-09-11-t8-cartridge"
INPUT = ROOT / "docs" / "design-inputs" / "2026-09-13-printed-bell.json"
SHIFT = 10.75
EPS = 1e-5
BODY_H = 55.8
OUTER = [
    [(35, 0), (31.5, 5), (28.7, 14), (27.0, 27)],
    [(27.0, 27), (26.25, 33), (24.9, 38), (23.9, 42)],
    [(23.9, 42), (22.0, 49.6), (17, 55.8), (10, 55.8)],
]
INNER = [
    [(33.0, 0), (29.5, 5), (26.7, 14), (25.0, 27)],
    [(25.0, 27), (24.25, 33), (22.9, 38), (21.9, 42)],
    [(21.9, 42), (21.4, 44), (21, 45.0), (20.5, 46.5)],
    [(20.5, 46.5), (17, 48), (11.0, 51.3), (6.3, 51.3)],
]
HANDLE = [
    [(10, 55.8), (10, 61.8), (8, 67), (7.7, 77.8)],
    [(7.7, 77.8), (7.2, 95), (8.2, 107), (10.5, 117.8)],
    [(10.5, 117.8), (12.7, 128), (11.5, 135.8), (0, 135.8)],
]


def write(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def args_parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--placement", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--freecad-cmd", type=Path, default=Path(os.environ.get("LOCALAPPDATA", "")) /
                   "Programs" / "FreeCAD 1.1" / "bin" / "FreeCADCmd.exe")
    p.add_argument("--inside-freecad", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--token", help=argparse.SUPPRESS)
    p.add_argument("--expected", help=argparse.SUPPRESS)
    p.add_argument("--marker", type=Path, help=argparse.SUPPRESS)
    return p.parse_args()


def translated_contact(source):
    c = copy.deepcopy(source)
    c["pcb_z_mm"] += SHIFT
    c["cell_nominal"]["center_mm"][2] += SHIFT
    for contact in c["contacts"]:
        contact["center_mm"][2] += SHIFT
        for pad in contact["pads"]:
            pad["center_mm"][2] += SHIFT
    primitives = c["right_contact_original_primitives"]
    for part in primitives["base_tabs"] + [primitives["under_cell_base"]]:
        part["z_min"] += SHIFT
    for point in primitives["spring_xz_polyline"]:
        point[1] += SHIFT
    primitives["ears"]["axis_center_yz"][1] += SHIFT
    return c


def numeric_contract(value):
    """Compare geometric records, allowing descriptive provenance text to evolve."""
    if isinstance(value, dict):
        return {k: numeric_contract(v) for k, v in value.items()
                if not isinstance(v, str) or k in ("reference", "polarity", "net", "cell_axis", "pcb_side")}
    if isinstance(value, list):
        return [numeric_contract(v) for v in value]
    if isinstance(value, (float, int)):
        return round(value, 7)
    return value


def inputs(args):
    paths = {
        "design_input": INPUT, "builder": Path(__file__).resolve(),
        "checker": ROOT / "tools" / "check_printed_bell.py",
        "geometry_helper": Path(base.__file__).resolve(),
        "export_helper": Path(helpers.__file__).resolve(),
        "frozen_t8_native": T8 / "t8-cartridge.FCStd",
        "frozen_t8_report": T8 / "fit-report.json",
        "frozen_t8_placement": T8 / "placement-snapshot.json",
        "frozen_t8_contact": T8 / "contact_interface-snapshot.json",
    }
    source = json.loads(paths["frozen_t8_placement"].read_text(encoding="utf-8-sig"))
    original_contact = json.loads(paths["frozen_t8_contact"].read_text(encoding="utf-8-sig"))
    expected_contact = translated_contact(original_contact)
    if args.placement:
        paths["placement"] = args.placement.resolve()
        manifest = json.loads(paths["placement"].read_text(encoding="utf-8-sig"))
        if manifest.get("interface_preview_only"):
            raise ValueError("A preview is not a final placement")
        paths["contact_interface"] = paths["placement"].parent / manifest["battery_contact_interface"]
        if paths["contact_interface"].resolve().parent != paths["placement"].parent:
            raise ValueError("Contact companion must be beside the actual placement")
        if sha(paths["contact_interface"]) != manifest["battery_contact_interface_sha256"]:
            raise ValueError("Contact companion does not match manifest")
        contact = json.loads(paths["contact_interface"].read_text(encoding="utf-8-sig"))
        for key, name, field in (
            ("pcb", "handbell.kicad_pcb", "generated_pcb_sha256"),
            ("schematic", "handbell.kicad_sch", "schematic_sha256"),
        ):
            paths[key] = paths["placement"].parent / name
            if sha(paths[key]) != manifest[field]:
                raise ValueError("Actual source bytes changed: " + name)
        for path in sorted(paths["placement"].parent.rglob("*")):
            if path.is_file() and (path.suffix in (".kicad_sym", ".kicad_mod") or
                                  path.name in ("sym-lib-table", "fp-lib-table")):
                paths["library_" + str(len(paths))] = path
        if numeric_contract(contact) != numeric_contract(expected_contact):
            raise ValueError("Contact geometry changed; retained T8 insulation requires engineering review")
        if any(c["side"] != ("B" if c["reference"] in ("BT1", "BT2") else "F")
               for c in manifest["components"]):
            raise ValueError("Final mode requires only BT1/BT2 on B")
    else:
        manifest = copy.deepcopy(source)
        manifest["board"]["front_z_mm"] += SHIFT
        for component in manifest["components"]:
            component["z_min_mm"] += SHIFT
            component["z_max_mm"] += SHIFT
        contact = expected_contact
    b = manifest["board"]
    if manifest["schema_version"] != 2 or manifest["units"] != "mm":
        raise ValueError("Require mm schema-2 manifest")
    if b["diameter_mm"] not in (43, 46, 48) or abs(b["front_z_mm"]-25) > EPS or b["thickness_mm"] != 1.6:
        raise ValueError("PCB diameter/thickness/z interface changed")
    if b["front_face"] != "speaker":
        raise ValueError("F must face the speaker")
    expected_holes = [(10, 15.7, 2.2), (-10, -15.7, 2.2)]
    holes = sorted(manifest["mounting_holes"], key=lambda h: h["reference"])
    if [(h["x_mm"], h["y_mm"], h["drill_mm"]) for h in holes] != expected_holes:
        raise ValueError("Mount-hole interface changed")
    usb = next(c for c in manifest["components"] if c["reference"] == "X6")
    old_usb = next(c for c in source["components"] if c["reference"] == "X6")
    for key in ("x_mm", "y_mm", "width_mm", "depth_mm", "height_mm", "rotation_deg"):
        if abs(usb[key]-old_usb[key]) > EPS:
            raise ValueError("USB source envelope/XY changed: " + key)
    for c in manifest["components"]:
        lo, hi = (25-c["height_mm"], 25) if c["side"] == "F" else (26.6, 26.6+c["height_mm"])
        if abs(c["z_min_mm"]-lo) > EPS or abs(c["z_max_mm"]-hi) > EPS:
            raise ValueError("Invalid component height/face interface: " + c["reference"])
    hashes = {k: sha(v) for k, v in paths.items()}
    return paths, hashes, manifest, contact


def launch(args):
    _, hashes, _, _ = inputs(args)
    out = args.output or (STUDY if args.placement else STUDY / "development")
    out = out.resolve()
    if out != STUDY and STUDY not in out.parents:
        raise ValueError("Only the September 13 study may be written")
    if not args.placement and out == STUDY:
        raise ValueError("Development geometry must remain in development/")
    out.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    run = out / (".freecad-run-" + token)
    run.mkdir()
    marker = run / "completed.json"
    argv = [str(Path(__file__).resolve()), "--inside-freecad", "--output", str(out),
            "--token", token, "--expected", json.dumps(hashes), "--marker", str(marker)]
    if args.placement:
        argv += ["--placement", str(args.placement.resolve())]
    bootstrap = f"import runpy,sys\nsys.argv={argv!r}\nrunpy.run_path(sys.argv[0],run_name='__main__')\n"
    write(out / "review-status.json", {"state": "BUILD_IN_PROGRESS", "token": token})
    try:
        command = [str(args.freecad_cmd), "--user-cfg", str(run / "user.cfg"),
                   "--system-cfg", str(run / "system.cfg")]
        result = subprocess.run(command, input=bootstrap, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, encoding="utf-8", errors="replace", timeout=2400)
        (out / "freecad-build.log").write_text(result.stdout, encoding="utf-8")
        if result.returncode or not marker.exists():
            print(result.stdout, file=sys.stderr)
            raise RuntimeError("Fresh FreeCAD completion absent; old exports are not success")
        completed = json.loads(marker.read_text(encoding="utf-8"))
        if completed["token"] != token or completed["input_hashes"] != hashes:
            raise RuntimeError("Completion binding changed")
        print(json.dumps(completed, indent=2))
    finally:
        shutil.rmtree(run)


def build(args):
    import FreeCAD as App
    import Part
    import Mesh
    import MeshPart
    V = App.Vector
    paths, hashes, manifest, contact = inputs(args)
    if hashes != json.loads(args.expected):
        raise RuntimeError("Inputs changed during launch")
    out = args.output.resolve()
    development = not bool(args.placement)
    print("Constructing original one-piece shell and keyed handle", flush=True)
    old = App.openDocument(str(paths["frozen_t8_native"]))
    doc = App.newDocument("PrintedBellSeptember13")
    doc.Label = ("DEVELOPMENT — frozen mixed-face T8" if development else "Printed bell — exact all-front placement")
    doc.Comment = "Original mechanics MIT; adapted populated electronics CC BY-SA 3.0. INERT engineering review."
    objects, styles, groups = {}, {}, {}

    def feature(name, shape, color=(.65, .65, .65), visible=True, group="Cartridge", transparency=0):
        base.shape_stats(shape)
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        if group not in groups:
            groups[group] = doc.addObject("App::DocumentObjectGroup", group)
        groups[group].addObject(obj)
        objects[name] = obj
        styles[name] = (color, transparency, visible)
        return obj

    def box(w, d, h, x=0, y=0, z=0):
        return base.box_at(w, d, h, x, y, z, Part, V)

    def cyl(r, h, x=0, y=0, z=0):
        return Part.makeCylinder(r, h, V(x, y, z))

    def moved(s, x=0, y=0, z=0):
        return helpers.moved(s, V(x, y, z))

    def rotate(s, angle):
        s = s.copy()
        s.rotate(V(), V(0, 0, 1), angle)
        return s

    def union(shapes, one=True):
        s = shapes[0].multiFuse(shapes[1:]).removeSplitter() if len(shapes) > 1 else shapes[0]
        base.shape_stats(s)
        if one and len(s.Solids) != 1:
            raise RuntimeError(f"Disconnected structural union: {len(s.Solids)}")
        return s

    def hexagon(af, h, x=0, y=0, z=0):
        r = af/math.sqrt(3)
        points = [V(x+r*math.cos(a*math.pi/3), y+r*math.sin(a*math.pi/3), z) for a in range(6)]
        return Part.Face(Part.makePolygon(points+[points[0]])).extrude(V(0, 0, h))

    def revolved(curves):
        edges = []
        first, last = curves[0][0], curves[-1][-1]
        edges.append(Part.makeLine(V(0, 0, first[1]), V(first[0], 0, first[1])))
        for poles in curves:
            curve = Part.BezierCurve()
            curve.setPoles([V(r, 0, z) for r, z in poles])
            edges.append(curve.toShape())
        if last[0]:
            edges.append(Part.makeLine(V(last[0], 0, last[1]), V(0, 0, last[1])))
        edges.append(Part.makeLine(V(0, 0, last[1]), V(0, 0, first[1])))
        return Part.Face(Part.Wire(edges)).revolve(V(), V(0, 0, 1), 360)

    def inherited(name):
        return moved(old.getObject(name).Shape, z=SHIFT)

    exterior, cavity = revolved(OUTER), revolved(INNER)
    shell_stock = exterior.cut(cavity)
    # A mouth-open slot cannot trap a connector on axial cartridge withdrawal.
    channel = box(15.0, 45, 27.4, y=-32.5, z=-.1)
    shell = shell_stock.cut(channel)
    shell = shell.cut(cyl(6.3, 8, z=43.3)).cut(cyl(2.2, 12, z=50))
    key_pocket = box(12.3, 10.3, 3, z=53.65)
    shell = shell.cut(key_pocket)
    joints = []
    lugs = []
    shell_nuts = []
    shell_screws = []
    for index, angle in enumerate((0, 120, 240), 1):
        x, y = 29.5*math.cos(math.radians(angle)), 29.5*math.sin(math.radians(angle))
        joints.append((x, y, angle))
        lug = rotate(box(7.8, 7, 8.2, x=31.4, z=3.3), angle).common(exterior)
        lugs.append(lug)
        nut = hexagon(4, 1.6, x, y, 7.15).cut(cyl(1, 1.6, x, y, 7.15))
        screw = cyl(1, 8, x, y, 2.3).fuse(cyl(1.9, 2, x, y, .3))
        shell_nuts.append(feature(f"ShellCaptiveM2Nut_{index}", nut, group="ShellHardware"))
        shell_screws.append(feature(f"FrontM2x8Screw_{index}", screw, group="ShellHardware"))
    shell = union([shell]+lugs)
    for x, y, angle in joints:
        shell = shell.cut(cyl(1.1, 9, x, y, 3.2))
        shell = shell.cut(hexagon(4.2, 1.9, x, y, 7.0))
        shell = shell.cut(rotate(box(8, 4.5, 1.9, x=27.3, z=7.0), angle))
    shell = shell.removeSplitter()
    shell_obj = feature("OnePiecePrintedBellShell", shell, (.72, .52, .19), group="ShellAndHandle", transparency=65)
    handle = revolved(HANDLE).fuse(box(12, 10, 2, z=53.8)).removeSplitter()
    handle = handle.cut(cyl(2.15, 14.3, z=53.7))
    nut_pocket = hexagon(7.3, 3.5, z=59.65).fuse(box(8.3, 15, 3.5, y=7.5, z=59.65))
    handle = handle.cut(nut_pocket).removeSplitter()
    handle_obj = feature("BlackKeyedHandleCaptiveMetalNut", handle, (.07, .07, .075), group="ShellAndHandle")
    washer = cyl(6, 1, z=50.3).cut(cyl(2.15, 1, z=50.3))
    screw = cyl(2, 16, z=50.3).fuse(cyl(4, 3.1, z=47.2)).removeSplitter()
    nut = hexagon(7, 3.2, z=59.65).cut(cyl(2, 3.2, z=59.65))
    handle_hardware = [
        feature("M4x16WorkingPanHeadScrew", screw, group="HandleHardware"),
        feature("M4LargeSeriesWasher12x4p3x1", washer, group="HandleHardware"),
        feature("M4CaptiveMetalNut7AFx3p2", nut, group="HandleHardware"),
    ]
    tolerance_hardware = {}
    for name, washer_h, length in (
        ("MaximumMouthwardHead", 1.1, 15.65),
        ("MaximumHandlewardTip", .9, 16.35),
        ("MaximumWasherAndLength", 1.1, 16.35),
    ):
        underhead = 51.3-washer_h
        sh = cyl(2, length, z=underhead).fuse(cyl(4, 3.25, z=underhead-3.25)).removeSplitter()
        wh = cyl(6, washer_h, z=underhead).cut(cyl(2.15, washer_h, z=underhead))
        tolerance_hardware[name] = (sh, wh, underhead, length)
        feature("M4Tolerance_"+name, Part.makeCompound([sh, wh]), (.9, .25, .2),
                False, "ConstructionReferences", 75)

    print("Constructing flush cartridge, retaining proven T8 yoke/capture solids", flush=True)
    grille = cyl(19, 1.8)
    for x in range(-16, 17, 4):
        grille = grille.cut(box(2.8, 36, 2.2, x=x, z=-.2).common(cyl(17, 2.2, z=-.2)))
    # Profile matching avoids the previous broad external skirt/band.
    register_clear = revolved([[(r-.3, z) for r, z in poles] for poles in INNER])
    plate = cyl(40, 3.3).common(register_clear).cut(cyl(18, 4))
    seat = cyl(20.2, 1.2, z=3.3).cut(cyl(18, 1.2, z=3.3))
    body_parts = [plate, grille, seat]
    for angle in (helpers.ANGLE, helpers.ANGLE+180):
        x, y = 23.5*math.cos(math.radians(angle)), 23.5*math.sin(math.radians(angle))
        support = rotate(box(5.4, 7.4, 9.2, x=23.5, z=3.3), angle)
        support = support.cut(hexagon(4.2, 1.9, x, y, 9.15)).cut(cyl(1.1, 5.2, x, y, 7.5))
        support = support.cut(rotate(box(5, 4.7, 1.9, x=25.5, z=9.15), angle))
        body_parts.append(support)
    bezel = shell_stock.common(box(14.4, 45, 27.0, y=-32.5))
    # Thin cosmetic port wall and two supported vertical rails; no load claim
    # about unmeasured through-board solder tails.
    body_parts += [bezel, box(14.4, 5, 1.2, y=-24.3, z=20.1)]
    for sign in (-1, 1):
        body_parts.append(box(1.8, 5, 23.7, x=sign*6.3, y=-26, z=3.3))
    body = union(body_parts)
    body = body.cut(box(10.2, 8.4, 50, y=-23.8, z=21.3))
    body = body.cut(box(12.1, 8.4, 50, y=-23.8, z=24.9))
    body = body.cut(box(9.2, 20, 3.1, y=-38, z=21.7))
    for x, y, _ in joints:
        body = body.cut(cyl(1.1, 4, x, y, z=-.1)).cut(cyl(2.15, 2.4, x, y, z=-.1))
    body = body.removeSplitter()
    body_obj = feature("FlushGrilleCarrierAndConcealedPortBezel", body, (.72, .52, .19))
    yoke = inherited("RemovableSpeakerCaptureYoke")
    cradle = inherited("LoadBearingInsulatingBatteryCradle")
    cover = inherited("RemovableBatteryCaptureCover")
    # The old fit study never checked cover withdrawal against the full
    # outward-flared spring tips. Straight end channels avoid forcing those
    # thin contacts; added outside stock keeps real 1 mm end/side/top walls.
    spring = contact["right_contact_original_primitives"]
    split_z = 36.5
    pocket_top = max(p[1] for p in spring["spring_xz_polyline"])+.1
    pocket_y = spring["spring_y_width"]/2+.1
    channel_stock, channel_voids, wall_witnesses = [], [], []
    for sign in (-1, 1):
        stock = box(2.5, 2*(pocket_y+1), pocket_top+1-split_z,
                    x=18.35, z=split_z)
        void = box(1.7, 2*pocket_y, pocket_top-split_z, x=17.75, z=split_z)
        witnesses = [
            box(1, 2*pocket_y, pocket_top-split_z, x=19.1, z=split_z),
            box(1.5, 1, pocket_top-split_z, x=17.85, y=pocket_y+.5, z=split_z),
            box(1.5, 1, pocket_top-split_z, x=17.85, y=-pocket_y-.5, z=split_z),
            box(1.5, 2*pocket_y, 1, x=17.85, z=pocket_top),
        ]
        angle = 0 if sign == 1 else 180
        channel_stock.append(rotate(stock, angle))
        channel_voids.append(rotate(void, angle))
        wall_witnesses += [rotate(w, angle) for w in witnesses]
    cover = union([cover]+channel_stock)
    for void in channel_voids:
        cover = cover.cut(void)
    cover = cover.removeSplitter()
    service_wall_missing = [max(0, w.cut(cover).Volume) for w in wall_witnesses]
    if max(service_wall_missing) > EPS:
        raise RuntimeError("Cover service channel lacks the declared external wall material")
    yoke_obj = feature("RetainedSpeakerCaptureYoke", yoke, (.91, .63, .27))
    cradle_obj = feature("RetainedInsulatingCellCradle", cradle, (.29, .65, .78))
    cover_obj = feature("RetainedRemovableCellCover", cover, (.37, .77, .87))
    speaker = inherited("SpeakerConditionalBodyScreen")
    cell = inherited("T8FullUnclippedCellCanEnvelope")
    speaker_obj = feature("ConservativeMeasuredSpeakerBody", speaker, (.38, .4, .43))
    cell_obj = feature("INERTUnqualifiedFullCellD16p4L34", cell, (.70, .34, .64))
    retained_hardware = []
    for old_obj in old.Objects:
        if old_obj.Name.startswith(("YokeM2", "BodyCaptive", "MH1", "MH2", "CoverM2", "CoverCaptive")):
            retained_hardware.append(feature(old_obj.Name, inherited(old_obj.Name), group="RetainedM2Hardware"))
    contact_objs = [feature("ContactMetal_"+ref, inherited("ContactMetal_"+ref), (.80, .79, .73),
                            group="ActualThinContactMetal") for ref in ("BT1", "BT2")]
    points = [V(x, y, 25) for x, y in manifest["board"]["outline_common_xy_mm"]]
    pcb = Part.Face(Part.makePolygon(points+[points[0]])).extrude(V(0, 0, 1.6))
    for hole in manifest["mounting_holes"]:
        pcb = pcb.cut(cyl(hole["drill_mm"]/2, 2, hole["x_mm"], hole["y_mm"], 24.8))
    pcb_obj = feature("PCBExactSuppliedOutlineAndMounts", pcb, (.12, .36, .60))
    component_objs = []
    for component in manifest["components"]:
        if component["reference"] in ("BT1", "BT2"):
            continue
        s = box(component["width_mm"], component["depth_mm"], component["height_mm"], z=component["z_min_mm"])
        s = moved(rotate(s, component["rotation_deg"]), component["x_mm"], component["y_mm"])
        component_objs.append(feature("Component_"+component["reference"], s,
                                      (.18, .20, .24) if component["side"] == "F" else (.55, .30, .18),
                                      group="ActualPlacementProxies"))
    pcba = Part.makeCompound([pcb]+[o.Shape for o in component_objs+contact_objs])
    pcba_obj = feature("FullPopulatedPCBAExport", pcba, visible=False, group="ConstructionReferences")
    inert_pcba = union([pcb]+[o.Shape for o in component_objs])
    inert_obj = feature("INERTPCBAExplicitlyWithoutBT1BT2", inert_pcba, visible=False, group="ConstructionReferences")
    anchor_reservations = {}
    for index, reservation in enumerate(manifest.get("cross_face_keepouts", []), 1):
        s = box(reservation["plan_w"], reservation["plan_h"], 19.9, z=26.6)
        s = moved(rotate(s, reservation["angle"]), reservation["x"], reservation["y"])
        feature(f"UNQUALIFIEDUSBAnchorProjection_{index}", s, (.9, .25, .2),
                False, "ConstructionReferences", 85)
        anchor_reservations[str(index)] = {
            "exact_manifest_record": reservation,
            "planning_projection_z_mm": [26.6, 46.5],
            "physical_occupied_height": False,
            "note": "Reservation only; real through-board tails remain unmeasured. Not an all-front BOM exclusion.",
        }
    structural = [shell_obj, handle_obj, body_obj, yoke_obj, cradle_obj, cover_obj]
    cartridge = [body_obj, yoke_obj, cradle_obj, cover_obj, speaker_obj, cell_obj, pcb_obj]+component_objs+contact_objs+retained_hardware
    physical = structural+[speaker_obj, cell_obj, pcb_obj]+component_objs+contact_objs+retained_hardware+shell_nuts+shell_screws+handle_hardware
    print("Checking physical BRep overlaps and bounded assembly motions", flush=True)
    overlaps = []
    for index, a in enumerate(physical):
        for b in physical[index+1:]:
            if a.Shape.BoundBox.intersect(b.Shape.BoundBox):
                volume = max(0, a.Shape.common(b.Shape).Volume)
                if volume > EPS:
                    overlaps.append({"a": a.Name, "b": b.Name, "intersection_mm3": volume})
    source_report = json.loads(paths["frozen_t8_report"].read_text(encoding="utf-8"))
    floor_line = Part.makeLine(V(8, 0, 27.0), V(8, 0, 28.08))
    floor_length = cradle.common(floor_line).Length
    if floor_length < 1.08-EPS:
        raise RuntimeError("Retained under-cell insulation lost material")
    bearing_witness = cyl(6, 2.35, z=51.3).cut(cyl(2.2, 2.35, z=51.3))
    bearing_missing = max(0, bearing_witness.cut(shell).Volume)
    if bearing_missing > EPS:
        raise RuntimeError("Actual shell does not contain the declared washer bearing annulus")

    def collisions(moving, obstacles):
        return {name: max(0, moving.common(shape).Volume) for name, shape in obstacles.items()}

    fixed_shell = {"shell": shell, "handle_screw": screw, "handle_washer": washer}
    assembly_paths = {}
    tolerance_screen = {}
    for name, (sh, wh, underhead, length) in tolerance_hardware.items():
        tolerance_screen[name] = {
            "underhead_z_mm": underhead, "head_bottom_z_mm": underhead-3.25,
            "length_mm": length, "tip_z_mm": underhead+length,
            "screw_to_cell": helpers.pair(sh, cell), "screw_to_cover": helpers.pair(sh, cover),
            "washer_to_cell": helpers.pair(wh, cell),
            "installed_overlap_mm3": collisions(Part.makeCompound([sh, wh]), {"shell": shell, "handle": handle}),
            "insertion_empty_shell": [
                {"mouthward_z_mm": dz,
                 "overlaps_mm3": collisions(moved(Part.makeCompound([sh, wh]), z=-dz), {"shell": shell})}
                for dz in (0, 2, 8, 20, 45, 65)],
        }
    complete = Part.makeCompound([o.Shape for o in cartridge])
    assembly_paths["cartridge_withdrawal_minus_z"] = [
        {"translation_mm": dz, "overlaps_mm3": collisions(moved(complete, z=-dz), fixed_shell)}
        for dz in (0, .3, 1, 3.3, 8, 16, 28, 48, 58)]
    plug = box(8.8, 8, 2.6, y=-31.9, z=21.95)
    feature("UNQUALIFIEDUSBMaleNoseApproach8p8x8x2p6", plug, (.9, .3, .2), False, "ConstructionReferences", 70)
    assembly_paths["unselected_usb_plug_approach"] = [
        {"outward_y_mm": dy, "overlaps_mm3": collisions(moved(plug, y=-dy), {"shell": shell, "bezel": body})}
        for dy in (0, 2, 5, 12)]
    tool = cyl(1.9, 48, z=-.8)
    feature("EmptyShellM4StraightDriverAccess", tool, (.9, .3, .2), False, "ConstructionReferences", 80)
    assembly_paths["handle_tool_empty_shell"] = collisions(tool, {"shell": shell, "handle": handle})
    assembly_paths["handle_nut_side_load"] = [
        {"positive_y_mm": dy, "overlap_mm3": max(0, moved(nut, y=dy).common(handle).Volume)}
        for dy in (0, 2, 5, 8, 12, 18)]
    assembly_paths["handle_screw_washer_insertion_empty_shell"] = [
        {"mouthward_z_mm": dz,
         "overlaps_mm3": collisions(moved(Part.makeCompound([screw, washer]), z=-dz), {"shell": shell})}
        for dz in (0, 2, 8, 20, 45, 65)]
    assembly_paths["shell_nut_radial_insertion_before_cartridge"] = []
    for (x, y, angle), obj in zip(joints, shell_nuts):
        assembly_paths["shell_nut_radial_insertion_before_cartridge"].append([
            {"radial_inward_mm": dr, "overlap_mm3": max(0, moved(obj.Shape,
             -dr*math.cos(math.radians(angle)), -dr*math.sin(math.radians(angle))).common(shell).Volume)}
            for dr in (0, 2, 5, 10, 16)])
    assembly_paths["speaker_load_before_yoke"] = [
        {"handleward_mm": dz, "body_overlap_mm3": max(0, moved(speaker, z=dz).common(body).Volume)}
        for dz in (0, 1, 5, 12, 25, 40)]
    assembly_paths["yoke_over_magnet_before_pcba"] = [
        {"handleward_mm": dz, "overlaps_mm3": collisions(moved(yoke, z=dz), {"speaker": speaker, "body": body})}
        for dz in (0, 1, 5, 12, 25, 40)]
    assembly_paths["pcba_lowering_into_open_top_carrier"] = [
        {"handleward_mm": dz, "overlaps_mm3": collisions(moved(pcba, z=dz), {"speaker": speaker, "body": body, "yoke": yoke})}
        for dz in (0, .5, 2, 6, 15, 35)]
    assembly_paths["cover_removal_with_cell_still_captured_by_cradle"] = [
        {"handleward_mm": dz, "overlaps_mm3": collisions(moved(cover, z=dz), {"cell": cell, "cradle": cradle, "pcba": pcba})}
        for dz in (0, .5, 2, 6, 15, 35)]
    assembly_paths["retained_m2_straight_tool_access"] = {}
    for obj in retained_hardware:
        if "M2x6" not in obj.Name:
            continue
        bb = obj.Shape.BoundBox
        tool_shape = cyl(.95, 30, (bb.XMin+bb.XMax)/2, (bb.YMin+bb.YMax)/2, bb.ZMax)
        obstacles = {"body": body, "yoke": yoke}
        if not obj.Name.startswith("Yoke"):
            obstacles.update({"cradle": cradle, "cover": cover})
        assembly_paths["retained_m2_straight_tool_access"][obj.Name] = collisions(tool_shape, obstacles)
    assembly_paths["cell_capture_outside_shell"] = {
        axis+str(sign): collisions(moved(cell, **{axis.lower(): sign*.5}), {"cradle": cradle, "cover": cover})
        for axis in ("X", "Y", "Z") for sign in (-1, 1)}
    assembly_paths["sequence"] = [
        "Empty shell: slide M4 nut into handle, key shoulder into crown, insert washer/screw and tighten from mouth.",
        "Empty shell: radially side-load the three roofed M2 nut pockets from cavity; no cartridge present.",
        "Outside shell: load body M2 nuts, speaker first, then retained yoke and two M2x6 screws.",
        "Side-load yoke nuts, lower PCBA through open-top USB carrier, add empty cradle and two M2x6 screws.",
        "Evaluate only an inert cell; side-load cover nuts, fit retained capture cover and two M2x6 screws.",
        "Unplug first; align integral port bezel with mouth-open shell channel; insert complete captured cartridge.",
        "Fit three recessed front M2x8 screws. Reverse for service; shell/handle load path stays independent of PCB.",
    ]
    gap_records = {}
    for obj in component_objs:
        gap_records[obj.Name] = {name: helpers.pair(obj.Shape, shape)
                                for name, shape in (("speaker", speaker), ("yoke", yoke), ("body", body),
                                                    ("cradle", cradle), ("cover", cover))}
    retention = assembly_paths["cell_capture_outside_shell"]
    report = {
        "status": "DEVELOPMENT_FROZEN_MIXED_FACE_NOT_FINAL" if development else "EXACT_ALL_FRONT_ENGINEERING_REVIEW",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "input": {"paths": {k: str(v.relative_to(ROOT)) for k, v in paths.items()}, "sha256": hashes},
        "toolchain": {"freecad": App.Version(), "opencascade": Part.OCC_VERSION, "python": sys.version},
        "frame": {"mouth_grille_z": 0, "speaker_front_z": 4.5, "speaker_basket_rear_z": 16.5,
                  "speaker_magnet_rear_z": 23.5, "pcb_F_z": 25, "pcb_B_z": 26.6, "cell_center_z": 36.38},
        "dimensions": {"maximum_shell_diameter_mm": 70, "body_height_mm": BODY_H,
                       "handle_above_crown_mm": 80, "overall_height_mm": 135.8,
                       "comparison_old_diameter_mm": 75.5, "comparison_old_body_height_mm": 56.3,
                       "grille_projection_mm": 0, "pcb_diameter_mm": manifest["board"]["diameter_mm"]},
        "profiles": {"original_outer_bezier_poles_rz_mm": OUTER, "original_inner_bezier_poles_rz_mm": INNER,
                     "original_handle_bezier_poles_rz_mm": HANDLE,
                     "wall_rule": "Independently authored cavity; no constant normal wall claim. Crown intentionally thickened.",
                     "reference_photographs_used_as_geometry": False},
        "structural_parts": {o.Name: base.shape_stats(o.Shape) for o in structural},
        "material_intersections": overlaps,
        "assembly_paths": assembly_paths,
        "component_clearances": gap_records,
        "cross_face_usb_anchor_reservations": anchor_reservations,
        "contact_retention": {
            "geometry": "Unchanged frozen T8 yoke/cradle and actual thin contacts translated +10.75 mm; cover has straight upper-spring service channels with added exterior stock.",
            "actual_under_cell_section_mm": floor_length, "section_xyz_mm": [[8, 0, 27.0], [8, 0, 28.08]],
            "steel_base_mm": .3, "dimple_above_B_mm": 9.78,
            "inherited_constructive_guard_stock_evidence": source_report["insulation_screens"]["complete_rounded_contact_guard_stock"],
            "wall_proof_scope": "Unchanged cradle/local guard evidence; historical shell margins do not apply. Cover end-pocket modification is separately witnessed below.",
            "cover_service_channels": {
                "reason": "Old cover withdrawal check excluded contact metal; full thin spring tips obstructed rigid removal.",
                "pocket_positive_x_mm": [16.9, 18.6], "pocket_y_mm": [-pocket_y, pocket_y],
                "pocket_z_mm": [split_z, pocket_top], "external_end_side_top_wall_mm": 1.0,
                "actual_wall_witness_missing_volumes_mm3": service_wall_missing,
                "scope": "Full rectangular external end, side and top wall witness solids contained in released cover. Split seam and cell-facing contact opening intentional; not a global dielectric rating."},
            "no_internal_insulation_removed": True,
            "all_six_half_mm_displacements_meet_plastic": all(sum(v.values()) > EPS for v in retention.values())},
        "handle_joint": {"working_screw": "M4x16 pan head, nominal D8/H3.1; supplier dimensional-table tolerance screen, not hardware-lot qualification",
                         "washer_OD_ID_H_mm": [12, 4.3, 1], "nut_AF_H_mm": [7, 3.2],
                         "screw_head_z_mm": [47.2, 50.3], "washer_z_mm": [50.3, 51.3],
                         "nut_z_mm": [59.65, 62.85], "screw_tip_z_mm": 66.3,
                         "nominal_full_nut_height_covered_mm": 3.2, "nominal_tip_beyond_nut_mm": 3.45,
                         "supplier_dimension_evidence": {
                             "scope": "Parent-confirmed supplier dimensional tables, not inspected ISO primary standards.",
                             "screw_url": "https://www.fasteners.eu/standards/ISO/7045/",
                             "screw_table_label": "Page explicitly displays DIN 7985 table",
                             "head_diameter_min_max_mm": [7.64, 8.0],
                             "head_height_nominal_max_mm": [3.1, 3.25],
                             "M4x16_underhead_length_min_max_mm": [15.65, 16.35],
                             "M4x20_underhead_length_min_max_mm": [19.6, 20.4],
                             "nut_url": "https://www.fasteners.eu/standards/ISO/4032/",
                             "nut_AF_min_max_mm": [6.78, 7.0], "nut_height_min_max_mm": [2.9, 3.2],
                             "washer_url": "https://www.fasteners.eu/standards/DIN/9021/",
                             "washer_ID_min_max_mm": [4.3, 4.48],
                             "washer_OD_min_max_mm": [11.57, 12],
                             "washer_height_min_max_mm": [.9, 1.1]},
                         "supplier_tolerance_screen": tolerance_screen,
                         "worst_case_head_bottom_z_mm": 46.95,
                         "worst_case_tip_z_range_mm": [65.85, 66.75],
                         "minimum_tip_past_maximum_height_nut_mm": 3.0,
                         "full_nut_body_height_covered_range_mm": [2.9, 3.2],
                         "engagement_scope": "Screw covers the complete nut body even at minimum length; usable threads/chamfers and fully threaded supplier part require confirmation. Nut body height is not certified effective thread engagement.",
                         "blind_bore_end_z_mm": 68,
                         "minimum_tip_to_blind_end_gap_mm": 1.25,
                         "minimum_supplier_washer_annular_face_area_mm2": math.pi/4*(11.57**2-4.48**2),
                         "M4x20_alternative": "Not interchangeable: maximum tip z70.8 exceeds the current blind bore end z68 by2.8 mm; redesign/rebind before use.",
                         "bearing_material_below_key_pocket_mm": 2.35,
                         "bearing_annulus_OD_ID_H_mm": [12, 4.4, 2.35],
                         "bearing_witness_outside_actual_shell_mm3": bearing_missing,
                         "key_tenon_xyz_mm": [12, 10, 2], "key_pocket_xyz_mm": [12.3, 10.3, 2.15],
                         "screw_to_cell": helpers.pair(screw, cell), "screw_to_cover": helpers.pair(screw, cover),
                         "washer_to_cell": helpers.pair(washer, cell),
                         "load_path": "Handle nut -> metal screw/washer -> integral shell crown; keyed shoulder resists rotation. Cartridge not a structural tie.",
                         "wood_option": "Same original external turning silhouette; metal cross-dowel/insert and keyed interface require separate design. No wood pilot or plastic thread qualified."},
        "usb": {"actual_source_reference": "X6", "source_proxy_bounds": base.bounds(objects["Component_X6"].Shape),
                "native_origin_xy_mm": [0, -22.82], "mouth_xy_mm": [0, -27.9],
                "mouth_open_channel_width_height_mm": [15, 27.3], "color_matched_integral_bezel_width_mm": 14.4,
                "nominal_nose_opening_width_height_mm": [9.2, 3.1],
                "source_body_to_underledge_nominal_gap_mm": .2,
                "plug_scope": "Unselected 8.8x8x2.6 male nose only; final pose touches source mouth, not a mating-depth/overmold qualification.",
                "load_path": "Carrier ledge/rails and keyed bezel react handling loads through carrier/front screws/shell, not a claim of solder-tail load capacity.",
                "tails": "Through-board anchor height/real tails unmeasured; no invented occupied tail-height solid."},
        "print_orientation": {"shell": "Mouth down, handle up. One solid including three attachment lugs.",
                              "carrier": "Grille face down, separately printed.",
                              "handle": "Base down; sideways nut tunnel and closed crown require slicer support review.",
                              "supports": "Upper internal crown slopes and nut-pocket roofs need explicit slicer support/bridging review. Mouth gives support-removal access BEFORE assembly. No universal support-free claim."},
        "pcba_stl_scope": {"omitted_only_from_inert_stl": ["BT1", "BT2"], "full_native_step_contacts": True,
                           "reason": "Preserved thin T8 contacts have known fold-root mesh defects; no metal bridge added."},
        "routing_interface": {"mechanically_bound_to_final_all_front_manifest": not development,
                              "mechanical_freeze_recommended": not development and not overlaps,
                              "outline_mounts_usb_contacts_may_change_without_rebind": False,
                              "routing_is_not_fabrication_approval": True},
        "gates": ["No live cell, fabrication, purchase, child-use or print-strength approval.",
                  "Cell loaded geometry/contact forces, positive button, wrapper abrasion and contact insulation remain unqualified.",
                  "Speaker rim, terminals, wire routing, cone excursion and acoustics remain unqualified.",
                  "Silk PLA finish is not creep, impact, thermal, dielectric or flame qualification.",
                  "Printed allowances are nominal CAD choices, not measured tolerances.",
                  "USB male nose is not a selected mating cable; no connector-tail height is inferred.",
                  "M2/M4 hardware dimensions, screw engagement, nut retention and torque require actual part/slicer/physical review.",
                  "Service paths are declared finite rigid poses, not an exhaustive continuous/deforming-motion proof.",
                  "Original photos/artwork are not imported or redistributed."],
    }
    path_clear = all(
        max(p["overlaps_mm3"].values()) < EPS
        for name in ("cartridge_withdrawal_minus_z", "unselected_usb_plug_approach",
                     "handle_screw_washer_insertion_empty_shell", "yoke_over_magnet_before_pcba",
                     "pcba_lowering_into_open_top_carrier", "cover_removal_with_cell_still_captured_by_cradle")
        for p in assembly_paths[name])
    path_clear &= all(max(v.values()) < EPS for v in assembly_paths["retained_m2_straight_tool_access"].values())
    report["routing_interface"]["mechanical_freeze_recommended"] &= path_clear
    for case in tolerance_screen.values():
        if max(case["installed_overlap_mm3"].values()) > EPS:
            raise RuntimeError("M4 supplier-tolerance hardware intersects the shell/handle")
        if case["screw_to_cell"]["intersection_mm3"] > EPS or case["screw_to_cover"]["intersection_mm3"] > EPS:
            raise RuntimeError("M4 supplier-tolerance head intersects cell capture")
        if any(max(p["overlaps_mm3"].values()) > EPS for p in case["insertion_empty_shell"]):
            raise RuntimeError("M4 supplier-tolerance hardware cannot follow empty-shell insertion path")
    for name, curves in (("OriginalShellProfile", OUTER), ("OriginalCavityProfile", INNER), ("OriginalHandleProfile", HANDLE)):
        doc.addObject("App::TextDocument", name).Text = json.dumps(curves)
    for key, path in paths.items():
        if key not in ("frozen_t8_native", "frozen_t8_report"):
            doc.addObject("App::TextDocument", "Raw_"+key).Text = base64.b64encode(path.read_bytes()).decode("ascii")
    doc.addObject("App::TextDocument", "InputProvenance").Text = json.dumps(report["input"], indent=2)
    doc.addObject("App::TextDocument", "EngineeringGates").Text = json.dumps(report["gates"], indent=2)
    doc.addObject("App::TextDocument", "AssemblyServiceSequence").Text = "\n".join(assembly_paths["sequence"])
    doc.recompute()
    native = out / "printed-bell.FCStd"
    doc.saveAs(str(native))
    helpers.add_display_metadata(native, styles)
    App.closeDocument(old.Name)

    print("Exporting STEP before all tessellation", flush=True)
    artifact = {}
    exports = {"printed-bell-complete.step": physical, "removable-cartridge.step": cartridge,
               "full-populated-pcba.step": [pcba_obj], "INERT-pcba-without-contacts.step": [inert_obj],
               "shell.step": [shell_obj], "black-handle.step": [handle_obj], "flush-carrier.step": [body_obj],
               "yoke.step": [yoke_obj], "cell-cradle.step": [cradle_obj], "cell-cover.step": [cover_obj],
               "speaker.step": [speaker_obj], "inert-cell.step": [cell_obj]}
    for name, objs in exports.items():
        artifact[name] = helpers.export_step(out / name, objs, Part)
    reopened = App.openDocument(str(native))
    native_max = 0
    for obj in physical:
        saved = reopened.getObject(obj.Name).Shape
        delta = max(0, obj.Shape.cut(saved).Volume)+max(0, saved.cut(obj.Shape).Volume)
        if delta > EPS:
            raise RuntimeError("Native BRep round-trip changed: " + obj.Name)
        native_max = max(native_max, delta)
    artifact[native.name] = {"sha256": sha(native), "brep_roundtrip_verified": True,
                             "maximum_object_symmetric_difference_mm3": native_max}
    App.closeDocument(reopened.Name)
    print("Exporting and validating connected INERT structural meshes", flush=True)
    stls = {"INERT-shell.stl": shell, "INERT-black-handle.stl": handle,
            "INERT-flush-carrier.stl": body, "INERT-yoke.stl": yoke,
            "INERT-cell-cradle.stl": cradle, "INERT-cell-cover.stl": cover,
            "INERT-pcba-without-contacts.stl": inert_pcba,
            "INERT-speaker.stl": speaker, "INERT-full-cell.stl": cell}
    for name, shape in stls.items():
        artifact[name] = helpers.export_stl(out / name, shape, Part, Mesh, MeshPart)
    svg_profile(out / "original-profile.svg", report)
    write(out / "fit-report.json", report)
    for key in ("design_input", "placement", "contact_interface"):
        if key in paths:
            (out / (key+"-snapshot.json")).write_bytes(paths[key].read_bytes())
    for name in ("fit-report.json", "original-profile.svg", "design_input-snapshot.json",
                 "placement-snapshot.json", "contact_interface-snapshot.json"):
        if (out / name).exists():
            artifact[name] = {"sha256": sha(out / name)}
    if {k: sha(v) for k, v in paths.items()} != hashes:
        raise RuntimeError("Bound input changed during build")
    write(out / "artifact-manifest.json", {"input_hashes": hashes, "artifacts": artifact})
    completed = {"token": args.token, "input_hashes": hashes,
                 "artifact_manifest_sha256": sha(out / "artifact-manifest.json"),
                 "status": report["status"], "nominal_overlap_count": len(overlaps)}
    write(out / "completion.json", completed)
    write(out / "review-status.json", {"state": report["status"], "token": args.token})
    write(args.marker, completed)
    print("Completed persistent geometry and exports", flush=True)


def svg_profile(path, report):
    def curve_path(curves, sign):
        r, z = curves[0][0]
        result = f"M {250+sign*r*4:.3f},{650-z*4:.3f}"
        for poles in curves:
            result += " C " + " ".join(f"{250+sign*r*4:.3f},{650-z*4:.3f}" for r, z in poles[1:])
        return result
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="720" viewBox="0 0 1120 720">',
        '<rect width="1120" height="720" fill="#fafafa"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#17202a;font-size:15px}</style>',
        '<text x="30" y="30" font-size="22">Original September 13 printed handbell profile — mm</text>',
        f'<text x="510" y="70">{report["status"]}</text>',
    ]
    for curves, color in ((OUTER, "#ad852e"), (INNER, "#478a9d"), (HANDLE, "#25272b")):
        for sign in (-1, 1):
            lines.append(f'<path d="{curve_path(curves, sign)}" fill="none" stroke="{color}" stroke-width="2"/>')
    for z, name in ((0, "Flush grille / mouth 0"), (4.5, "Speaker front 4.5"), (23.5, "Magnet rear 23.5"),
                    (25, "PCB F25 / B26.6"), (36.38, "Cell axis 36.38"), (55.8, "Crown55.8")):
        y = 650-z*4
        lines.append(f'<path d="M100,{y} H480" stroke="#999" stroke-dasharray="4 4"/>')
        lines.append(f'<text x="510" y="{y+5}">{name}</text>')
    for index, text in enumerate((
        "Maximum body D70 / H55.8; handle above crown80; overall135.8",
        "Old comparison ceiling: D75.5 / bodyH56.3 / handle85.5",
        "Original Bezier poles are embedded in native and fit-report.",
        "Gold: shell exterior; blue: independent cavity; black: handle.",
        "No traced image, copied artwork or broad handguard disk.",
        "Not a constant-normal-thickness or support-free claim.",
        "Mouth-open -Y service channel is filled by cartridge bezel.",
        "M4x16 / large washer / metal captive nut / keyed shoulder.",
        "INERT engineering dimensions; no physical tolerances qualified.",
    )):
        lines.append(f'<text x="510" y="{100+index*25}">{text}</text>')
    lines.append("</svg>")
    path.write_text("\n".join(lines)+"\n", encoding="utf-8")


if __name__ == "__main__":
    a = args_parser()
    build(a) if a.inside_freecad else launch(a)
