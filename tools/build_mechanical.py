#!/usr/bin/env python3
"""Original MIT-licensed, headless FreeCAD packaging study; never edits KiCad.

Run with ordinary Python. The launcher uses the installed FreeCADCmd interpreter
with temporary, isolated preferences; no GUI, plugins, or pip packages are needed.
CAD dimensions and coordinates are millimetres. Positive z points into the bell.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import html
import itertools
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = {
    "lip_id_mm": 70.0,
    "flat_end_z_mm": 5.0,
    "linear_start_z_mm": 13.0,
    "linear_start_id_mm": 50.0,
    "linear_end_z_mm": 43.0,
    "linear_end_id_mm": 34.0,
    "body_height_mm": 44.0,
    "shell_radial_thickness_mm": 0.7,
    "handle_height_mm": 85.0,
    "handle_placeholder_diameter_mm": 16.0,
    "speaker_diameter_mm": 40.9,
    "speaker_depth_mm": 18.5,
    "speaker_front_z_mm": 0.0,
    "board_diameter_mm": 43.0,
    "board_thickness_mm": 1.6,
    "board_front_z_mm": 20.0,
    "board_component_face": "inward",
    "battery_width_mm": 20.0,
    "battery_depth_mm": 30.0,
    "battery_height_mm": 8.0,
    "battery_front_z_mm": 28.0,
    "battery_clearance_mm": 1.0,
    "interface_outer_diameter_mm": 69.0,
    "interface_inner_diameter_mm": 56.0,
    "interface_height_mm": 3.0,
    "baffle_diameter_mm": 65.0,
    "baffle_aperture_diameter_mm": 38.0,
    "baffle_thickness_mm": 2.0,
    "speaker_seat_radial_clearance_mm": 0.3,
    "speaker_seat_wall_mm": 1.5,
    "speaker_seat_height_mm": 3.0,
    "grille_inner_face_z_mm": -4.0,
    "grille_thickness_mm": 1.8,
    "grille_slot_pitch_mm": 4.0,
    "grille_slot_width_mm": 2.8,
    "fastener_pitch_radius_mm": 30.5,
    "fastener_clearance_diameter_mm": 2.4,
    "support_start_radius_mm": 25.0,
    "support_radial_thickness_mm": 1.2,
    "support_tangential_width_mm": 2.5,
    "support_board_edge_gap_mm": 0.2,
    "support_tab_underlap_mm": 0.6,
    "support_tab_thickness_mm": 0.8,
    "mesh_linear_deflection_mm": 0.05,
    "mesh_angular_deflection_rad": 0.15,
}
GAUGE_DEFAULTS = {
    "gauge_speaker_nominal_diameter_mm": 40.5,
    "gauge_speaker_nominal_depth_mm": 18.0,
    "gauge_speaker_nominal_magnet_diameter_mm": 22.0,
    "gauge_speaker_nominal_rim_thickness_mm": 2.7,
    "gauge_speaker_assumed_basket_front_diameter_mm": 37.0,
    "gauge_speaker_assumed_basket_rear_diameter_mm": 26.0,
    "gauge_speaker_assumed_magnet_front_z_mm": 12.0,
    "gauge_compact_battery_width_mm": 18.0,
    "gauge_compact_battery_depth_mm": 28.0,
    "gauge_compact_battery_height_mm": 8.0,
}
DEFAULTS.update(GAUGE_DEFAULTS)
VOLUME_EPSILON = 1e-5


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--placement", type=Path, help="Strict schema-v1 placement JSON; never auto-discovered.")
    parser.add_argument("--parameters", type=Path, help="JSON object of parameter overrides.")
    parser.add_argument("--parameters-from", type=Path, help="Read the Parameters spreadsheet in a saved FCStd.")
    parser.add_argument("--speaker-front-z", type=float, help="Override the speaker front datum, in mm.")
    parser.add_argument("--component-height", action="append", default=[], metavar="REFERENCE=MM",
                        help="Explicit model-only component height override; repeatable, requires --placement.")
    parser.add_argument("--component-height-note",
                        default="Explicit model-only screening assumption; not a qualified manufacturer maximum.",
                        help="Provenance note recorded for every requested component height override.")
    parser.add_argument("--output", type=Path, default=ROOT / "mechanical")
    parser.add_argument("--freecad-cmd", type=Path, help="Path to installed FreeCADCmd.exe.")
    parser.add_argument("--inside-freecad", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--completion-file", type=Path, help=argparse.SUPPRESS)
    return parser.parse_args()


def finite_number(value, context, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{context}: expected a finite numeric value")
    if positive and value <= 0:
        raise ValueError(f"{context}: expected a positive value")
    return float(value)


def read_manifest(path, *, contents=None):
    if path is None:
        return None
    contents = path.read_bytes() if contents is None else contents
    manifest = json.loads(contents.decode("utf-8-sig"))
    if (not isinstance(manifest, dict) or type(manifest.get("schema_version")) is not int
            or manifest["schema_version"] != 1 or manifest.get("units") != "mm"):
        raise ValueError("Placement must be an object with schema_version=1 and units='mm'")
    board = manifest["board"]
    for key in ("diameter_mm", "thickness_mm"):
        finite_number(board[key], f"board.{key}", positive=True)
    finite_number(board["front_z_mm"], "board.front_z_mm")
    if board["component_face"] not in ("inward", "outward"):
        raise ValueError("board.component_face must be inward or outward")
    if not isinstance(manifest["components"], list):
        raise ValueError("components must be a list")
    references = set()
    for component in manifest["components"]:
        for key in ("reference", "footprint", "height_source"):
            if not isinstance(component[key], str) or not component[key].strip():
                raise ValueError(f"component.{key}: expected nonempty text")
        reference = component["reference"]
        if reference in references:
            raise ValueError(f"Duplicate component reference: {reference}")
        references.add(reference)
        for key in ("x_mm", "y_mm", "rotation_deg"):
            finite_number(component[key], f"{reference}.{key}")
        for key in ("width_mm", "depth_mm", "height_mm"):
            finite_number(component[key], f"{reference}.{key}", positive=True)
        if "requires_shell_cutout" in component and not isinstance(component["requires_shell_cutout"], bool):
            raise ValueError(f"{reference}.requires_shell_cutout must be boolean")
    return manifest


def prepare_components(manifest, specifications, note):
    if specifications and manifest is None:
        raise ValueError("Component height overrides require an explicit placement manifest")
    if specifications and not note.strip():
        raise ValueError("Component height overrides require a nonempty provenance note")
    components = [] if manifest is None else [dict(component) for component in manifest["components"]]
    by_reference = {component["reference"]: component for component in components}
    overrides = []
    seen = set()
    for specification in specifications:
        reference, separator, raw_height = specification.partition("=")
        if not separator or reference not in by_reference:
            raise ValueError(f"Expected a fitted component reference and height as REFERENCE=MM: {specification}")
        if reference in seen:
            raise ValueError(f"Duplicate component height override: {reference}")
        seen.add(reference)
        height = finite_number(float(raw_height), f"{reference} model-only height", positive=True)
        component = by_reference[reference]
        overrides.append({"reference": reference, "manifest_height_mm": component["height_mm"],
                          "model_height_mm": height, "manifest_height_source": component["height_source"],
                          "footprint_unchanged": component["footprint"], "note": note})
        component["height_source"] = (
            f"MODEL-ONLY height override: {component['height_mm']:g} -> {height:g} mm. {note} "
            f"Original manifest height source: {component['height_source']}")
        component["height_mm"] = height
    return components, overrides


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def launcher(args):
    manifest = read_manifest(args.placement)
    prepare_components(manifest, args.component_height, args.component_height_note)
    for path in (args.parameters, args.parameters_from):
        if path is not None and not path.is_file():
            raise FileNotFoundError(path)
    executable = args.freecad_cmd
    if executable is None:
        found = shutil.which("FreeCADCmd") or shutil.which("FreeCADCmd.exe")
        if found:
            executable = Path(found)
        else:
            candidates = sorted((Path(os.environ.get("LOCALAPPDATA", "")) / "Programs").glob(
                "FreeCAD*\\bin\\FreeCADCmd.exe"))
            if candidates:
                executable = candidates[-1]
    if executable is None or not executable.is_file():
        raise FileNotFoundError("FreeCADCmd not found; supply --freecad-cmd with its installed executable path")
    with tempfile.TemporaryDirectory(prefix="handbell-freecad-") as temporary:
        temporary = Path(temporary)
        completion = temporary / "complete.json"
        argv = [str(Path(__file__).resolve()), *sys.argv[1:], "--inside-freecad",
                "--completion-file", str(completion)]
        source = (
            "import runpy, sys\n"
            f"sys.argv = {argv!r}\n"
            f"runpy.run_path({str(Path(__file__).resolve())!r}, run_name='__main__')\n"
        )
        command = [str(executable), "--user-cfg", str(temporary / "user.cfg"),
                   "--system-cfg", str(temporary / "system.cfg")]
        result = subprocess.run(command, input=source, text=True, check=False,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                encoding="utf-8", errors="replace", timeout=300)
        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=True)
        log = output / "freecad-build.log"
        log.write_text("Command: " + subprocess.list2cmdline(command)
                       + "\nConsole input:\n" + source + "\nOutput:\n" + result.stdout, encoding="utf-8")
        # FreeCAD's REPL may return zero after a Python exception. Never trust
        # that status alone or treat old output files as this run's success.
        if result.returncode != 0 or not completion.is_file():
            print(result.stdout, file=sys.stderr)
            raise RuntimeError(f"FreeCAD did not complete the build (process status {result.returncode}); see {log}")
        print(completion.read_text(encoding="utf-8"))


def load_parameters(args, manifest, App):
    parameters = DEFAULTS.copy()
    if args.parameters_from:
        source = App.openDocument(str(args.parameters_from.resolve()))
        sheet = source.getObject("Parameters")
        if sheet is None:
            raise ValueError("Saved FCStd has no Parameters spreadsheet")
        populated_cells = set(sheet.getNonEmptyCells())
        for row, key in enumerate(DEFAULTS, start=2):
            if key in GAUGE_DEFAULTS and f"A{row}" not in populated_cells and f"B{row}" not in populated_cells:
                print(f"Older spreadsheet: adding new gauge parameter {key}={GAUGE_DEFAULTS[key]}")
                continue
            if sheet.get(f"A{row}") != key:
                raise ValueError(f"Spreadsheet parameter mismatch at row {row}")
            raw = sheet.get(f"B{row}")
            parameters[key] = raw if isinstance(DEFAULTS[key], str) else float(raw)
        App.closeDocument(source.Name)
    if args.parameters:
        overrides = json.loads(args.parameters.read_text(encoding="utf-8-sig"))
        if not isinstance(overrides, dict):
            raise ValueError("Parameters must be a JSON object")
        unknown = set(overrides) - set(DEFAULTS)
        if unknown:
            raise ValueError(f"Unknown parameters: {sorted(unknown)}")
        parameters.update(overrides)
    if manifest is not None:
        for key in ("diameter_mm", "thickness_mm", "front_z_mm", "component_face"):
            parameters[f"board_{key}"] = manifest["board"][key]
    if args.speaker_front_z is not None:
        parameters["speaker_front_z_mm"] = args.speaker_front_z
    signed = {"speaker_front_z_mm", "grille_inner_face_z_mm", "board_front_z_mm", "battery_front_z_mm"}
    for key, value in parameters.items():
        if key == "board_component_face":
            if value not in ("inward", "outward"):
                raise ValueError("board_component_face must be inward or outward")
        else:
            parameters[key] = finite_number(value, key, positive=key not in signed)
    p = parameters
    if not (0 < p["flat_end_z_mm"] < p["linear_start_z_mm"] < p["linear_end_z_mm"] < p["body_height_mm"]):
        raise ValueError("Require 0 < flat end < linear start < linear end < body height")
    if not (p["lip_id_mm"] > p["linear_start_id_mm"] > p["linear_end_id_mm"]):
        raise ValueError("Cavity diameters must decrease")
    slope = (p["linear_end_id_mm"] - p["linear_start_id_mm"]) / (
        2 * (p["linear_end_z_mm"] - p["linear_start_z_mm"]))
    control_radius = p["linear_start_id_mm"] / 2 - slope * (
        p["linear_start_z_mm"] - p["flat_end_z_mm"]) / 3
    if control_radius > p["lip_id_mm"] / 2:
        raise ValueError("Near-mouth Bezier controls would cease to be monotone")
    if not (p["grille_inner_face_z_mm"] < -p["baffle_thickness_mm"] < 0):
        raise ValueError("Grille must leave a positive stand-off below the baffle")
    if not (0 < p["grille_slot_width_mm"] < p["grille_slot_pitch_mm"]):
        raise ValueError("Grille slots need a positive intervening web")
    if not (p["baffle_aperture_diameter_mm"] < p["baffle_diameter_mm"] < p["interface_outer_diameter_mm"]):
        raise ValueError("Require aperture < baffle < interface outer diameter")
    if p["interface_inner_diameter_mm"] >= p["interface_outer_diameter_mm"]:
        raise ValueError("Interface ring must have positive radial thickness")
    if p["board_front_z_mm"] <= p["speaker_seat_height_mm"] + p["support_tab_thickness_mm"]:
        raise ValueError("Board must be behind the mouth support roots")
    hole_r = p["fastener_clearance_diameter_mm"] / 2
    pitch = p["fastener_pitch_radius_mm"]
    if not (p["interface_inner_diameter_mm"] / 2 + hole_r < pitch
            < min(p["interface_outer_diameter_mm"], p["baffle_diameter_mm"]) / 2 - hole_r):
        raise ValueError("Alignment holes must lie within both interface ring and baffle")
    if not (p["gauge_speaker_nominal_diameter_mm"] <= p["speaker_diameter_mm"]
            and p["gauge_speaker_nominal_depth_mm"] <= p["speaker_depth_mm"]):
        raise ValueError("Nominal speaker gauge must not exceed the maximum collision envelope")
    if not (p["gauge_speaker_nominal_diameter_mm"]
            >= p["gauge_speaker_assumed_basket_front_diameter_mm"]
            > p["gauge_speaker_assumed_basket_rear_diameter_mm"]
            >= p["gauge_speaker_nominal_magnet_diameter_mm"]):
        raise ValueError("Illustrative speaker requires frame >= basket front > basket rear >= magnet diameter")
    if not (p["gauge_speaker_nominal_rim_thickness_mm"]
            < p["gauge_speaker_assumed_magnet_front_z_mm"] < p["gauge_speaker_nominal_depth_mm"]):
        raise ValueError("Illustrative speaker requires rim end < assumed magnet front < overall depth")
    return p


def cavity_radius(z, p):
    if not 0 <= z <= p["linear_end_z_mm"]:
        return None
    if z <= p["flat_end_z_mm"]:
        return p["lip_id_mm"] / 2
    slope = (p["linear_end_id_mm"] - p["linear_start_id_mm"]) / (
        2 * (p["linear_end_z_mm"] - p["linear_start_z_mm"]))
    if z >= p["linear_start_z_mm"]:
        return p["linear_start_id_mm"] / 2 + slope * (z - p["linear_start_z_mm"])
    length = p["linear_start_z_mm"] - p["flat_end_z_mm"]
    t = (z - p["flat_end_z_mm"]) / length
    return ((2*t**3 - 3*t**2 + 1) * p["lip_id_mm"] / 2
            + (-2*t**3 + 3*t**2) * p["linear_start_id_mm"] / 2
            + (t**3 - t**2) * length * slope)


def bounds(shape):
    box = shape.BoundBox
    return {"min_mm": [box.XMin, box.YMin, box.ZMin],
            "max_mm": [box.XMax, box.YMax, box.ZMax],
            "size_mm": [box.XLength, box.YLength, box.ZLength]}


def shape_stats(shape):
    if shape.isNull() or not shape.isValid() or not shape.Solids:
        raise RuntimeError("Invalid or non-solid BRep")
    if any(not solid.isClosed() or solid.Volume <= 0 for solid in shape.Solids):
        raise RuntimeError("BRep contains an open or non-positive solid")
    return {"valid": True, "solid_count": len(shape.Solids), "volume_mm3": shape.Volume,
            "bounds": bounds(shape)}


def rotated_corners(component):
    angle = math.radians(component["rotation_deg"])
    cosine, sine = math.cos(angle), math.sin(angle)
    return [(component["x_mm"] + x*cosine - y*sine,
             component["y_mm"] + x*sine + y*cosine)
            for x in (-component["width_mm"]/2, component["width_mm"]/2)
            for y in (-component["depth_mm"]/2, component["depth_mm"]/2)]


def make_profile(p, Part, Vector, offset=0.0, capped=False):
    r0 = p["lip_id_mm"]/2 + offset
    r1 = p["linear_start_id_mm"]/2 + offset
    r2 = p["linear_end_id_mm"]/2 + offset
    z0, z1, z2 = p["flat_end_z_mm"], p["linear_start_z_mm"], p["linear_end_z_mm"]
    slope = (r2-r1)/(z2-z1)
    length = z1-z0
    curve = Part.BezierCurve()
    curve.setPoles([Vector(r0, 0, z0), Vector(r0, 0, z0+length/3),
                    Vector(r1-slope*length/3, 0, z1-length/3), Vector(r1, 0, z1)])
    edges = [Part.makeLine(Vector(0, 0, 0), Vector(r0, 0, 0)),
             Part.makeLine(Vector(r0, 0, 0), Vector(r0, 0, z0)), curve.toShape(),
             Part.makeLine(Vector(r1, 0, z1), Vector(r2, 0, z2))]
    top = p["body_height_mm"] if capped else z2
    if capped:
        edges.append(Part.makeLine(Vector(r2, 0, z2), Vector(r2, 0, top)))
    edges.extend([Part.makeLine(Vector(r2, 0, top), Vector(0, 0, top)),
                  Part.makeLine(Vector(0, 0, top), Vector(0, 0, 0))])
    return Part.Face(Part.Wire(edges)).revolve(Vector(0, 0, 0), Vector(0, 0, 1), 360)


def ring(outer_radius, inner_radius, height, z, Part, Vector):
    return Part.makeCylinder(outer_radius, height, Vector(0, 0, z)).cut(
        Part.makeCylinder(inner_radius, height, Vector(0, 0, z)))


def box_at(width, depth, height, x, y, z, Part, Vector):
    return Part.makeBox(width, depth, height, Vector(x-width/2, y-depth/2, z))


def component_shape(component, board, Part, Vector):
    z = (board["front_z_mm"] + board["thickness_mm"] if board["component_face"] == "inward"
         else board["front_z_mm"] - component["height_mm"])
    shape = box_at(component["width_mm"], component["depth_mm"], component["height_mm"],
                   0, 0, z, Part, Vector)
    shape.rotate(Vector(0, 0, 0), Vector(0, 0, 1), component["rotation_deg"])
    shape.translate(Vector(component["x_mm"], component["y_mm"], 0))
    return shape


def make_print_parts(p, Part, Vector):
    interface = ring(p["interface_outer_diameter_mm"]/2, p["interface_inner_diameter_mm"]/2,
                     p["interface_height_mm"], 0, Part, Vector)
    baffle = ring(p["baffle_diameter_mm"]/2, p["baffle_aperture_diameter_mm"]/2,
                  p["baffle_thickness_mm"], -p["baffle_thickness_mm"], Part, Vector)
    seat_inner = p["speaker_diameter_mm"]/2 + p["speaker_seat_radial_clearance_mm"]
    seat = ring(seat_inner+p["speaker_seat_wall_mm"], seat_inner,
                p["speaker_seat_height_mm"], 0, Part, Vector)
    parts = [baffle, seat]
    angles = (0, 120, 240)
    board_z = p["board_front_z_mm"]
    half_radial = p["support_radial_thickness_mm"]/2
    half_width = p["support_tangential_width_mm"]/2
    top_radius = p["board_diameter_mm"]/2 + p["support_board_edge_gap_mm"] + half_radial
    for angle in angles:
        wires = []
        for z, radius in ((-0.2, p["support_start_radius_mm"]), (board_z, top_radius)):
            points = [Vector(radius-half_radial, -half_width, z),
                      Vector(radius+half_radial, -half_width, z),
                      Vector(radius+half_radial, half_width, z),
                      Vector(radius-half_radial, half_width, z)]
            wires.append(Part.makePolygon(points+[points[0]]))
        rail = Part.makeLoft(wires, True, True)
        inner = p["board_diameter_mm"]/2 - p["support_tab_underlap_mm"]
        outer = top_radius+half_radial
        tab = Part.makeBox(outer-inner, 2*half_width, p["support_tab_thickness_mm"],
                          Vector(inner, -half_width, board_z-p["support_tab_thickness_mm"]))
        rail = rail.fuse(tab)
        rail.rotate(Vector(0, 0, 0), Vector(0, 0, 1), angle)
        parts.append(rail)
        theta = math.radians(angle)
        x = p["fastener_pitch_radius_mm"]*math.cos(theta)
        y = p["fastener_pitch_radius_mm"]*math.sin(theta)
        boss = Part.makeCylinder(2.6, -p["baffle_thickness_mm"]-p["grille_inner_face_z_mm"]+0.2,
                                 Vector(x, y, p["grille_inner_face_z_mm"]))
        parts.append(boss)
    carrier = parts[0].multiFuse(parts[1:]).removeSplitter()
    grille_z = p["grille_inner_face_z_mm"] - p["grille_thickness_mm"]
    grille = Part.makeCylinder(p["baffle_diameter_mm"]/2, p["grille_thickness_mm"], Vector(0, 0, grille_z))
    aperture = Part.makeCylinder(p["baffle_aperture_diameter_mm"]/2, p["grille_thickness_mm"]+2,
                                 Vector(0, 0, grille_z-1))
    slots = []
    count = math.ceil(p["baffle_aperture_diameter_mm"]/p["grille_slot_pitch_mm"])
    for index in range(-count, count+1):
        slot = box_at(p["grille_slot_width_mm"], p["baffle_aperture_diameter_mm"]+2,
                      p["grille_thickness_mm"]+2, index*p["grille_slot_pitch_mm"], 0,
                      grille_z-1, Part, Vector).common(aperture)
        if slot.Volume > VOLUME_EPSILON:
            slots.append(slot)
    vents = Part.makeCompound(slots)
    grille = grille.cut(vents)
    holes = []
    for angle in angles:
        theta = math.radians(angle)
        holes.append(Part.makeCylinder(
            p["fastener_clearance_diameter_mm"]/2, p["interface_height_mm"]-grille_z+2,
            Vector(p["fastener_pitch_radius_mm"]*math.cos(theta),
                   p["fastener_pitch_radius_mm"]*math.sin(theta), grille_z-1)))
    hole_tool = Part.makeCompound(holes)
    result = {"BondedInterface": interface.cut(hole_tool).removeSplitter(),
              "FitCarrier": carrier.cut(hole_tool).removeSplitter(),
              "Grille": grille.cut(hole_tool).removeSplitter()}
    for name, shape in result.items():
        if shape_stats(shape)["solid_count"] != 1:
            raise RuntimeError(f"{name} must be one connected, closed printable solid")
    open_area = sum(slot.Volume for slot in slots)/(p["grille_thickness_mm"]+2)
    return result, {"open_area_mm2": open_area,
                    "open_fraction_of_aperture": open_area/(math.pi*(p["baffle_aperture_diameter_mm"]/2)**2),
                    "speaker_to_grille_inner_face_mm": p["speaker_front_z_mm"]-p["grille_inner_face_z_mm"],
                    "aperture_is_assumed_not_measured_cone": True}


def common_volume(a, b):
    if not a.BoundBox.intersect(b.BoundBox):
        return 0.0
    return max(0.0, a.common(b).Volume)


def fit_record(shape, radius, cavity, shell, p):
    box = shape.BoundBox
    wall_radius = cavity_radius(box.ZMax, p)
    outside = max(0.0, shape.cut(cavity).Volume)
    return {"bounds": bounds(shape), "max_xy_radius_mm": radius,
            "radial_margin_at_deepest_plane_mm": None if wall_radius is None else wall_radius-radius,
            "inward_axial_margin_mm": p["linear_end_z_mm"]-box.ZMax,
            "outside_cavity_volume_mm3": outside,
            "shell_intersection_volume_mm3": common_volume(shape, shell),
            "contained_in_assumed_cavity": outside <= VOLUME_EPSILON}


def scenario(name, board, components, cavity, shell, speaker, p, Part, Vector):
    substrate = Part.makeCylinder(board["diameter_mm"]/2, board["thickness_mm"],
                                 Vector(0, 0, board["front_z_mm"]))
    report = {"name": name, "board": board,
              "substrate": fit_record(substrate, board["diameter_mm"]/2, cavity, shell, p),
              "speaker_substrate_overlap_mm3": common_volume(substrate, speaker),
              "components": [], "component_pair_intersections": [],
              "note": "Same XY/rotation/body proxies in every scenario; never scaled or clipped. "
                      "A different board diameter is not a new routed or approved placement."}
    component_shapes = []
    for component in components:
        shape = component_shape(component, board, Part, Vector)
        maximum = max(math.hypot(x, y) for x, y in rotated_corners(component))
        row = {"reference": component["reference"], "footprint": component["footprint"],
               "height_source": component["height_source"],
               "height_mm": component["height_mm"], "rotation_deg": component["rotation_deg"],
               "requires_shell_cutout": component.get("requires_shell_cutout", False),
               "board_edge_radial_margin_mm": board["diameter_mm"]/2-maximum,
               **fit_record(shape, maximum, cavity, shell, p),
               "speaker_intersection_volume_mm3": common_volume(shape, speaker)}
        report["components"].append(row)
        component_shapes.append((component["reference"], shape))
    for (left_name, left), (right_name, right) in itertools.combinations(component_shapes, 2):
        overlap = common_volume(left, right)
        if overlap > VOLUME_EPSILON:
            report["component_pair_intersections"].append(
                {"left": left_name, "right": right_name, "volume_mm3": overlap})
    report["cavity_conflicts"] = [row["reference"] for row in report["components"]
                                if not row["contained_in_assumed_cavity"]]
    report["speaker_conflicts"] = [row["reference"] for row in report["components"]
                                  if row["speaker_intersection_volume_mm3"] > VOLUME_EPSILON]
    report["board_overhangs"] = [row["reference"] for row in report["components"]
                               if row["board_edge_radial_margin_mm"] < 0]
    report["required_shell_cutouts"] = [
        {"reference": row["reference"], "status": "required_not_implemented",
         "proxy_bounds": row["bounds"],
         "raw_uncut_shell_intersection_volume_mm3": row["shell_intersection_volume_mm3"],
         "note": "Proxy bounds are not a fabricated slot specification; plug, cable, insulation and load path unresolved."}
        for row in report["components"] if row["requires_shell_cutout"]]
    report["unplanned_cavity_conflicts"] = [row["reference"] for row in report["components"]
                                          if not row["contained_in_assumed_cavity"] and not row["requires_shell_cutout"]]
    return report, substrate, component_shapes


def make_fit_dummies(p, board, components, Part, Vector):
    shapes, descriptions = {}, {}

    def add(name, shape, stem, description, assembly_z, step=False, extra=None):
        stats = shape_stats(shape)
        if stats["solid_count"] != 1 or abs(shape.BoundBox.ZMin) > 1e-6:
            raise RuntimeError(f"{name}: fit dummy must be one connected solid with print-bed Z=0")
        shapes[name] = shape
        descriptions[name] = {
            "stl": stem+".stl", "step": stem+".step" if step else None,
            "description": description, "assembly_reference_z_mm": assembly_z,
            "print_origin": "XY centered; flat print bed at Z=0; coordinates in mm",
            "shape": stats, **(extra or {})}

    substrate = Part.makeCylinder(board["diameter_mm"]/2, board["thickness_mm"],
                                 Vector(0, 0, board["front_z_mm"]))
    bodies = [component_shape(component, board, Part, Vector) for component in components]
    pcba = substrate.multiFuse(bodies).removeSplitter() if bodies else substrate
    if len(pcba.Solids) != 1:
        raise RuntimeError("PCBA dummy is disconnected; cannot add out-of-envelope bridges or move components to hide it")
    rotation = 0 if board["component_face"] == "inward" else 180
    if rotation:
        pcba.rotate(Vector(0, 0, 0), Vector(1, 0, 0), rotation)
    z_translation = -pcba.BoundBox.ZMin
    pcba.translate(Vector(0, 0, z_translation))
    name = "PopulatedPCBAFitDummy" if components else "PCBSubstrateFitDummy"
    stem = "populated-pcba-proxy" if components else "pcb-substrate-placeholder"
    add(name, pcba, stem,
        "INERT bonded union of physical board and exact supplied rectangular proxies. "
        "No detail enlargement, added bridges, cables, underside anchors or copper-only/DNP solids. "
        "Not manufacturer bodies, a routed board, or a qualified physical assembly.",
        board["front_z_mm"], step=True,
        extra={"component_count": len(components), "component_detail_scale": 1.0,
               "source_board": board, "print_rotation_x_deg": rotation,
               "print_translation_z_mm": z_translation})
    add("SpeakerNominalFitDummy",
        Part.makeCylinder(p["gauge_speaker_nominal_diameter_mm"]/2, p["gauge_speaker_nominal_depth_mm"]),
        "speaker-envelope-nominal", "Nominal full cylinder; retail frame/depth, not basket/terminals/excursion.",
        p["speaker_front_z_mm"])
    maximum = Part.makeCylinder(p["speaker_diameter_mm"]/2, p["speaker_depth_mm"])
    add("SpeakerMaximumFitDummy", maximum, "speaker-envelope-maximum",
        "Full worst-case frame/depth cylinder, also used for hard collision screening. "
        "Terminal and excursion envelopes remain unknown.", p["speaker_front_z_mm"])
    rim_height = p["gauge_speaker_nominal_rim_thickness_mm"]
    magnet_front = p["gauge_speaker_assumed_magnet_front_z_mm"]
    rim = Part.makeCylinder(p["gauge_speaker_nominal_diameter_mm"]/2, rim_height)
    basket = Part.makeCone(p["gauge_speaker_assumed_basket_front_diameter_mm"]/2,
                           p["gauge_speaker_assumed_basket_rear_diameter_mm"]/2,
                           magnet_front-rim_height, Vector(0, 0, rim_height))
    magnet = Part.makeCylinder(p["gauge_speaker_nominal_magnet_diameter_mm"]/2,
                               p["gauge_speaker_nominal_depth_mm"]-magnet_front, Vector(0, 0, magnet_front))
    illustrative = rim.multiFuse([basket, magnet]).removeSplitter()
    if illustrative.cut(maximum).Volume > VOLUME_EPSILON:
        raise RuntimeError("Illustrative speaker extends beyond the conservative collision cylinder")
    add("SpeakerIllustrativeFitDummy", illustrative, "speaker-illustrative-unmeasured",
        "ILLUSTRATIVE ONLY: nominal frame, overall depth, rim and magnet diameter. "
        "Solid tapered basket diameters and magnet start/depth are adjustable inventions, not image measurements. "
        "Rim is included in overall depth. Never replaces the full collision cylinder.",
        p["speaker_front_z_mm"], step=True,
        extra={"assumed_basket_front_diameter_mm": p["gauge_speaker_assumed_basket_front_diameter_mm"],
               "assumed_basket_rear_diameter_mm": p["gauge_speaker_assumed_basket_rear_diameter_mm"],
               "assumed_magnet_front_z_mm": magnet_front,
               "derived_unmeasured_magnet_height_mm": p["gauge_speaker_nominal_depth_mm"]-magnet_front,
               "used_for_hard_collision_screen": False})
    for variant, width, depth, height in (
            ("Primary", p["battery_width_mm"], p["battery_depth_mm"], p["battery_height_mm"]),
            ("Compact", p["gauge_compact_battery_width_mm"], p["gauge_compact_battery_depth_mm"],
             p["gauge_compact_battery_height_mm"])):
        add("Battery"+variant+"FitDummy", box_at(width, depth, height, 0, 0, 0, Part, Vector),
            "battery-dummy-"+variant.lower(),
            "INERT dimensional block only; no selected pack, capacity, current, charge or swelling qualification.",
            p["battery_front_z_mm"])
        clearance = p["battery_clearance_mm"]
        add("Battery"+variant+"ClearanceGauge",
            box_at(width+2*clearance, depth+2*clearance, height+2*clearance, 0, 0, 0, Part, Vector),
            "battery-clearance-"+variant.lower(),
            "SOLID CLEARANCE GAUGE, not a battery: includes assumed free space on all six faces. "
            "Never compress a live cell to achieve this fit.", p["battery_front_z_mm"]-clearance,
            extra={"represented_dummy_dimensions_mm": [width, depth, height],
                   "clearance_per_face_mm": clearance})
    return shapes, descriptions


def export_step_and_check(step, objects, Part):
    Part.export(objects, str(step))
    imported = Part.Shape()
    imported.read(str(step))
    original = Part.makeCompound([obj.Shape for obj in objects])
    original_stats, roundtrip_stats = shape_stats(original), shape_stats(imported)
    if original_stats["solid_count"] != roundtrip_stats["solid_count"]:
        raise RuntimeError("STEP round-trip solid count changed")
    if abs(original.Volume-imported.Volume) > max(1e-4, original.Volume*1e-7):
        raise RuntimeError("STEP round-trip volume changed")
    bound_error = max(abs(a-b) for axis in ("min_mm", "max_mm")
                      for a, b in zip(bounds(original)[axis], bounds(imported)[axis]))
    if bound_error > 0.001:
        raise RuntimeError("STEP units/bounds changed")
    step_text = step.read_text(encoding="ascii", errors="strict")
    if ".MILLI.,.METRE." not in step_text.replace(" ", "").replace("\n", ""):
        raise RuntimeError("STEP does not declare millimetre SI length units")
    return {"sha256": sha256(step), "bytes": step.stat().st_size,
            "units": "mm (STEP SI_UNIT)", "roundtrip": roundtrip_stats,
            "maximum_bound_error_mm": bound_error}


def export_and_check(output, doc, assembly, print_shapes, dummy_shapes, dummy_descriptions,
                     p, App, Part, Mesh, MeshPart):
    artifacts = {"handbell-assembly.step": export_step_and_check(output / "handbell-assembly.step", assembly, Part)}
    filenames = {"BondedInterface": "bonded-interface.stl", "FitCarrier": "fit-carrier.stl", "Grille": "grille.stl"}
    for name, description in dummy_descriptions.items():
        filenames[name] = description["stl"]
        if description["step"]:
            path = output / description["step"]
            artifacts[path.name] = export_step_and_check(path, [doc.getObject(name)], Part)
    for name, shape in {**print_shapes, **dummy_shapes}.items():
        path = output / filenames[name]
        mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=p["mesh_linear_deflection_mm"],
                                     AngularDeflection=p["mesh_angular_deflection_rad"], Relative=False)
        mesh.write(str(path))
        reread = Mesh.Mesh(str(path))
        if not reread.isSolid() or reread.countComponents() != 1 or reread.Volume <= 0:
            raise RuntimeError(f"{path.name}: STL is not a single closed oriented mesh")
        if reread.hasNonManifolds() or reread.hasSelfIntersections():
            raise RuntimeError(f"{path.name}: STL is non-manifold or self-intersecting")
        rebuilt = Part.Shape()
        rebuilt.makeShapeFromMesh(reread.Topology, 0.001)
        if len(rebuilt.Shells) != 1 or not rebuilt.Shells[0].isClosed():
            raise RuntimeError(f"{path.name}: reimport did not produce one closed shell")
        solid = Part.makeSolid(rebuilt.Shells[0])
        shape_stats(solid)
        volume_error = abs(reread.Volume-shape.Volume)/shape.Volume
        bound_error = max(abs(a-b) for axis in ("min_mm", "max_mm")
                          for a, b in zip(bounds(shape)[axis], bounds(solid)[axis]))
        if volume_error > 0.01 or bound_error > 0.1:
            raise RuntimeError(f"{path.name}: tessellation lost units, size, or excessive volume")
        artifacts[path.name] = {"sha256": sha256(path), "bytes": path.stat().st_size,
                                "units": "unitless STL; coordinates represent mm, import at 1:1",
                                "facets": reread.CountFacets, "closed": True, "manifold": True,
                                "self_intersections": False, "connected_components": 1,
                                "relative_volume_error": volume_error,
                                "maximum_bound_error_mm": bound_error, "roundtrip": shape_stats(solid)}
    fcstd = output / "handbell-feasibility.FCStd"
    doc.recompute()
    doc.saveAs(str(fcstd))
    expected = {obj.Name: shape_stats(obj.Shape) for obj in doc.Objects if hasattr(obj, "Shape")}
    App.closeDocument(doc.Name)
    reopened = App.openDocument(str(fcstd))
    for name, stats in expected.items():
        obj = reopened.getObject(name)
        if obj is None or abs(shape_stats(obj.Shape)["volume_mm3"]-stats["volume_mm3"]) > 1e-6:
            raise RuntimeError(f"FCStd reopen failed for {name}")
    if reopened.getObject("Parameters") is None or reopened.getObject("BuildSource") is None:
        raise RuntimeError("FCStd lost editable parameters or source snapshot")
    artifacts[fcstd.name] = {"sha256": sha256(fcstd), "bytes": fcstd.stat().st_size,
                            "readable_after_reopen": True, "shape_object_count": len(expected),
                            "units": "mm", "has_parameters_spreadsheet": True, "has_source_snapshot": True}
    App.closeDocument(reopened.Name)
    return artifacts


def render_dummy_views(output, p, descriptions):
    fragments = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="680" viewBox="0 0 1100 680">',
        '<rect width="1100" height="680" fill="#fafafa"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#17202a}</style>',
        '<text x="25" y="32" font-size="22">Original inert fit dummies - PLA, mm, 100% scale</text>',
        '<text x="25" y="58" font-size="13">Illustrative speaker geometry is invented between supplied dimensions. No source image is included.</text>',
    ]
    scale, cx, bottom = 6, 175, 245
    rim = p["gauge_speaker_nominal_rim_thickness_mm"]
    rear = p["gauge_speaker_assumed_magnet_front_z_mm"]
    depth = p["gauge_speaker_nominal_depth_mm"]
    profile = [
        (-p["gauge_speaker_nominal_diameter_mm"]/2, 0),
        (-p["gauge_speaker_nominal_diameter_mm"]/2, rim),
        (-p["gauge_speaker_assumed_basket_front_diameter_mm"]/2, rim),
        (-p["gauge_speaker_assumed_basket_rear_diameter_mm"]/2, rear),
        (-p["gauge_speaker_nominal_magnet_diameter_mm"]/2, rear),
        (-p["gauge_speaker_nominal_magnet_diameter_mm"]/2, depth),
        (p["gauge_speaker_nominal_magnet_diameter_mm"]/2, depth),
        (p["gauge_speaker_nominal_magnet_diameter_mm"]/2, rear),
        (p["gauge_speaker_assumed_basket_rear_diameter_mm"]/2, rear),
        (p["gauge_speaker_assumed_basket_front_diameter_mm"]/2, rim),
        (p["gauge_speaker_nominal_diameter_mm"]/2, rim),
        (p["gauge_speaker_nominal_diameter_mm"]/2, 0),
    ]
    points = " ".join(f"{cx+x*scale:.3f},{bottom-z*scale:.3f}" for x, z in profile)
    fragments.append(f'<polygon points="{points}" fill="#bcd4e6" stroke="#1d3557" stroke-width="2"/>')
    fragments.append(f'<rect x="{cx-p["speaker_diameter_mm"]/2*scale:.3f}" '
                     f'y="{bottom-p["speaker_depth_mm"]*scale:.3f}" width="{p["speaker_diameter_mm"]*scale:.3f}" '
                     f'height="{p["speaker_depth_mm"]*scale:.3f}" fill="none" stroke="#b22222" stroke-dasharray="6,4"/>')
    fragments.append('<text x="25" y="282" font-size="13">Blue: illustrative only. Red: maximum collision envelope.</text>')
    fragments.append('<text x="25" y="306" font-size="13">Print wide frame face down; no hollow basket, terminals or cone.</text>')
    fragments.append('<text x="530" y="100" font-size="17">Standalone print dimensions (X x Y x Z, mm)</text>')
    for index, description in enumerate(descriptions.values()):
        dimensions = " x ".join(f"{value:.3f}" for value in description["shape"]["bounds"]["size_mm"])
        text = f"{description['stl']}: {dimensions}"
        fragments.append(f'<text x="530" y="{128+index*29}" font-size="12">{html.escape(text)}</text>')
    notes = [
        "PCBA: one fused solid. Component proxies remain at 1:1 scale; small 0402 details are not enlarged.",
        "Battery clearance gauges include free space; they are not battery dimensions or live-cell restraints.",
        "All new dummy STL/STEP files have Z=0 at the print bed; restore the reported datum when checking the assembly.",
        "Use the installed K1C/nozzle PLA profile. Inspect tiny features and the USB overhang in the slicer.",
        "No image, thermal model, mass/acoustic equivalence, retention qualification or routing approval is implied.",
    ]
    for index, note in enumerate(notes):
        fragments.append(f'<text x="25" y="{490+index*29}" font-size="13">{html.escape(note)}</text>')
    fragments.append("</svg>")
    (output / "views" / "fit-dummies.svg").write_text("\n".join(fragments)+"\n", encoding="utf-8")


def render_views(output, p, components, board, report):
    scale = 6.0
    cx, zy = 260, 145
    fragments = ['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="650" viewBox="0 0 1120 650">',
                 '<rect width="1120" height="650" fill="#fafafa"/>',
                 '<style>text{font-family:Arial,sans-serif;fill:#17202a} .small{font-size:12px}</style>',
                 '<text x="25" y="28" font-size="22">Handbell packaging - original assumption/proxy views</text>',
                 '<text x="25" y="52" class="small">mm; z=0 at opening, +z inward. Not a measured shell or manufacturer component model.</text>',
                 '<text x="25" y="82" font-size="16">Axial shell section + projected envelopes (handle omitted)</text>']
    def rectangle(x, z, width, height, fill, stroke, opacity=0.5):
        fragments.append(f'<rect x="{cx+x*scale:.3f}" y="{zy+z*scale:.3f}" width="{width*scale:.3f}" '
                         f'height="{height*scale:.3f}" fill="{fill}" stroke="{stroke}" fill-opacity="{opacity}"/>')
    for sign in (-1, 1):
        points = " ".join(f"{cx+sign*cavity_radius(i*p['linear_end_z_mm']/200,p)*scale:.3f},"
                          f"{zy+i*p['linear_end_z_mm']/200*scale:.3f}" for i in range(201))
        fragments.append(f'<polyline points="{points}" fill="none" stroke="#555" stroke-width="4"/>')
    for z in (0, p["flat_end_z_mm"], p["linear_start_z_mm"], p["linear_end_z_mm"]):
        radius = cavity_radius(z, p)
        fragments.append(f'<path d="M {cx-radius*scale:.3f} {zy+z*scale:.3f} H {cx+radius*scale:.3f}" '
                         'stroke="#bbb" stroke-dasharray="3,3"/>')
        fragments.append(f'<text x="25" y="{zy+z*scale-6:.3f}" class="small">z{z:g}: ID{2*radius:g}</text>')
    rectangle(-p["speaker_diameter_mm"]/2, p["speaker_front_z_mm"], p["speaker_diameter_mm"],
              p["speaker_depth_mm"], "#f4a261", "#bc6c25")
    rectangle(-board["diameter_mm"]/2, board["front_z_mm"], board["diameter_mm"],
              board["thickness_mm"], "#2a9d8f", "#14655d", 0.9)
    for component in components:
        corners = rotated_corners(component)
        xmin, xmax = min(x for x, _ in corners), max(x for x, _ in corners)
        z = (board["front_z_mm"]+board["thickness_mm"] if board["component_face"] == "inward"
             else board["front_z_mm"]-component["height_mm"])
        rectangle(xmin, z, xmax-xmin, component["height_mm"], "#457b9d", "#1d3557", 0.18)
    clearance = p["battery_clearance_mm"]
    rectangle(-p["battery_width_mm"]/2-clearance, p["battery_front_z_mm"]-clearance,
              p["battery_width_mm"]+2*clearance, p["battery_height_mm"]+2*clearance,
              "#e76f51", "#b22222", 0.15)
    rectangle(-p["battery_width_mm"]/2, p["battery_front_z_mm"], p["battery_width_mm"],
              p["battery_height_mm"], "#bd96cd", "#663399", 0.5)
    rectangle(-p["baffle_diameter_mm"]/2, -p["baffle_thickness_mm"], p["baffle_diameter_mm"],
              p["baffle_thickness_mm"], "#888", "#555")
    rectangle(-p["baffle_diameter_mm"]/2, p["grille_inner_face_z_mm"]-p["grille_thickness_mm"],
              p["baffle_diameter_mm"], p["grille_thickness_mm"], "#ccc", "#555")
    px, py = 825, 270
    fragments.append('<text x="590" y="82" font-size="16">PCB proxy plan (+X right, +Y up)</text>')
    fragments.append(f'<circle cx="{px}" cy="{py}" r="{board["diameter_mm"]/2*scale:.3f}" '
                     'fill="#d7efeb" stroke="#14655d" stroke-width="2"/>')
    for component, row in zip(components, report["scenarios"][0]["components"]):
        color = "#cc3333" if not row["contained_in_assumed_cavity"] else "#457b9d"
        x, y = px+component["x_mm"]*scale, py-component["y_mm"]*scale
        w, d = component["width_mm"]*scale, component["depth_mm"]*scale
        fragments.append(f'<rect x="{x-w/2:.3f}" y="{y-d/2:.3f}" width="{w:.3f}" height="{d:.3f}" '
                         f'transform="rotate({-component["rotation_deg"]:.4f} {x:.3f} {y:.3f})" '
                         f'fill="{color}" fill-opacity=".35" stroke="{color}"/>')
        if component["height_mm"] >= 3:
            fragments.append(f'<text x="{x:.3f}" y="{y:.3f}" font-size="10">{html.escape(component["reference"])}</text>')
    lines = [
        "Orange: full worst-case speaker envelope. Green: physical PCB substrate.",
        "Blue: rectangular component proxies. Red plan rectangles: cavity conflicts.",
        f"Purple: inert {p['battery_width_mm']:g} x {p['battery_depth_mm']:g} x {p['battery_height_mm']:g} mm block; "
        "pale red: required clearance envelope.",
        "Profile z0..13 is an adjustable interpretation; only z13..43 is the owner-specified linear segment.",
        "No selected pack, cone excursion, terminals, mating leads, shell slot, battery restraint or load qualification.",
        "STL files are inert fit gauges; a complete powered or child-ready assembly is NOT demonstrated.",
    ]
    for index, text in enumerate(lines):
        fragments.append(f'<text x="25" y="{480+index*23}" class="small">{html.escape(text)}</text>')
    fragments.append("</svg>")
    (output / "views").mkdir(exist_ok=True)
    (output / "views" / "packaging-views.svg").write_text("\n".join(fragments)+"\n", encoding="utf-8")


def build(args):
    import FreeCAD as App
    import Part
    import Mesh
    import MeshPart
    Vector = App.Vector
    manifest_contents = None if args.placement is None else args.placement.read_bytes()
    manifest = read_manifest(args.placement, contents=manifest_contents)
    components, height_overrides = prepare_components(manifest, args.component_height, args.component_height_note)
    p = load_parameters(args, manifest, App)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    # Disable backup creation only inside this invocation's isolated preferences.
    App.ParamGet("User parameter:BaseApp/Preferences/Document").SetInt("CountBackupFiles", 0)
    doc = App.newDocument("HandbellFeasibility")
    doc.Label = "Handbell - INERT FIT STUDY, assumptions and proxies"
    doc.Comment = ("Original mechanical geometry/source: MIT. Embedded electronics placement context retains "
                   "CC BY-SA 3.0 notices; see mechanical/README.md. No measured shell or child-use qualification.")
    sheet = doc.addObject("Spreadsheet::Sheet", "Parameters")
    sheet.Label = "Parameters - edit values, save, regenerate with --parameters-from"
    sheet.set("A1", "Parameter")
    sheet.set("B1", "Value (mm unless named otherwise)")
    for row, (key, value) in enumerate(p.items(), start=2):
        sheet.set(f"A{row}", key)
        sheet.set(f"B{row}", str(value))
        sheet.setAlias(f"B{row}", key)
    sheet.setColumnWidth("A", 280)
    sheet.setColumnWidth("B", 240)
    source = doc.addObject("App::TextDocument", "BuildSource")
    source.Label = "Original build_mechanical.py source snapshot (regeneration authority)"
    source.Text = Path(__file__).read_text(encoding="utf-8")
    assumptions = doc.addObject("App::TextDocument", "Assumptions")
    assumptions.Text = (
        "Datum z=0 opening, +z inward; all mm. z13 ID50 to z43 ID34 is an owner working assumption, "
        "not a measurement. z0..5 ID70 is an axial interpretation of an ambiguous lip description; "
        "z5..13 uses a monotone cubic transition tangent to the linear segment. "
        "Shell radial wall 0.7 and 1 mm closed crown are visual placeholders. Handle solid is exterior-only. "
        "Speaker 40.9 x 18.5 is a conservative cylinder, not a measured basket; terminals/excursion unknown. "
        "Battery is an inert dimensional block, no selected pack or capacity/current approval. "
        "Feature BReps are editable via this source and Parameters; spreadsheet edits alone do not rebuild them. "
        "Regenerate with --parameters-from and the same --placement; manifest board values take precedence. "
        "All component solids are original bounding-box proxies, NOT manufacturer STEP models. "
        "No trimming for USB or hidden collisions. Mounting/alignment holes and board seats are fit concepts "
        "only: no retention, USB-load, adhesive, acoustic, electrical, or child-use qualification."
    )
    groups = {}
    for name, label in (("Context", "Assumed shell and exterior context"),
                        ("Envelopes", "Speaker and inert battery - dimensional proxies"),
                        ("Electronics", "Physical PCB and placement-based body proxies"),
                        ("PrintParts", "Inert fit prints - no retention qualification"),
                        ("FitDummies", "Standalone inert dummy print coordinates - HIDE for assembly view"),
                        ("References", "Construction / clearance references (not assembly export)")):
        group = doc.addObject("App::DocumentObjectGroup", name)
        group.Label = label
        groups[name] = group
    def feature(name, shape, label, group, role):
        shape_stats(shape)
        obj = doc.addObject("Part::Feature", name)
        obj.Label = label
        obj.Shape = shape
        obj.addProperty("App::PropertyString", "Evidence", "Provenance")
        obj.Evidence = role
        groups[group].addObject(obj)
        return obj
    cavity = make_profile(p, Part, Vector)
    shell = make_profile(p, Part, Vector, p["shell_radial_thickness_mm"], capped=True).cut(cavity).removeSplitter()
    handle = Part.makeCylinder(p["handle_placeholder_diameter_mm"]/2, p["handle_height_mm"],
                               Vector(0, 0, p["body_height_mm"]))
    feature("CavityReference", cavity, "Cavity construction solid - hide for assembly view", "References",
            "Owner-assumed linear segment; near-mouth cubic interpretation, no measurements")
    assembly = [
        feature("BellShell", shell, "Bell shell - assumed inner profile / placeholder wall", "Context",
                "Not a measured shell: wall thickness and crown closure are invented visual context"),
        feature("HandleExterior", handle, "Handle EXTERIOR ONLY - no usable interior assumed", "Context",
                "85 mm owner approximate height; 16 mm diameter invented, solid keepout"),
    ]
    speaker = Part.makeCylinder(p["speaker_diameter_mm"]/2, p["speaker_depth_mm"],
                                Vector(0, 0, p["speaker_front_z_mm"]))
    assembly.append(feature("SpeakerEnvelope", speaker, "EK1794 full 40.9 x 18.5 max envelope PROXY", "Envelopes",
                            "Retail drawing maxima; rim included; no basket/terminal/excursion qualification"))
    battery = box_at(p["battery_width_mm"], p["battery_depth_mm"], p["battery_height_mm"], 0, 0,
                     p["battery_front_z_mm"], Part, Vector)
    clearance = p["battery_clearance_mm"]
    battery_keepout = box_at(p["battery_width_mm"]+2*clearance, p["battery_depth_mm"]+2*clearance,
                             p["battery_height_mm"]+2*clearance, 0, 0, p["battery_front_z_mm"]-clearance, Part, Vector)
    assembly.append(feature("BatteryDummy", battery, "INERT battery-sized block - NOT a selected pack", "Envelopes",
                            "Pure dimensional assumption, no capacity/current/charge approval"))
    feature("BatteryClearance", battery_keepout, "Battery no-compression clearance - reference, not material", "References",
            "Assumed clearance per face; cannot replace pack manufacturer's expansion/lead requirements")
    board = {key: p[f"board_{key}"] for key in ("diameter_mm", "thickness_mm", "front_z_mm", "component_face")}
    if manifest is not None:
        embedded = doc.addObject("App::TextDocument", "PlacementManifest")
        embedded.Label = "Read-only placement input snapshot; electronics provenance remains upstream"
        embedded.Text = json.dumps(manifest, indent=2)
    if height_overrides:
        overrides_object = doc.addObject("App::TextDocument", "ComponentHeightOverrides")
        overrides_object.Label = "Explicit model-only height parameters - repeat CLI flags to regenerate"
        overrides_object.Text = json.dumps(height_overrides, indent=2)
    report = {
        "schema_version": 1, "units": "mm", "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "Engineering screening only; real fit, routing, acoustic and safety qualification remain open",
        "scope": "placeholder-only: no placement manifest supplied" if manifest is None else "placement-based rectangular proxies",
        "toolchain": {"freecad_version": App.Version(), "python_version": sys.version,
                      "freecad_executable": sys.executable, "opencascade_version": Part.OCC_VERSION,
                      "gui_used": False},
        "input": {"placement": None if args.placement is None else os.path.relpath(args.placement.resolve(), ROOT),
                  "placement_sha256": None if manifest_contents is None else hashlib.sha256(manifest_contents).hexdigest(),
                  "component_count": len(components), "script_sha256": sha256(Path(__file__)),
                  "component_height_overrides": height_overrides,
                  "copper_only_back_features": [] if manifest is None else manifest.get("copper_only_back_features", []),
                  "dnp_footprint_reservations": [] if manifest is None else manifest.get("dnp_footprint_reservations", []),
                  "rotation_convention": "Supplied mathematical degrees about +Z; no additional KiCad angle negation",
                  "invocation_argv": sys.argv[1:sys.argv.index("--inside-freecad")]},
        "parameters": p, "scenarios": [], "volume_epsilon_mm3": VOLUME_EPSILON,
        "license_scope": "Original mechanical geometry and code: MIT. Electronics placement context "
                         "retains hardware/handbell CC BY-SA 3.0 attribution; see mechanical/README.md.",
        "profile": {"exact_linear_segment": "D(z)=50-(16/30)*(z-13), z13..43 for default parameters",
                    "near_mouth": "ID70 z0..5; monotone cubic Hermite z5..13, dR/dz=0 at5 and -8/30 at13. "
                                  "Adjustable axial interpretation, not an owner measurement or photo-derived dimension.",
                    "stations": [{"z_mm": z, "id_mm": 2*cavity_radius(z, p)}
                                 for z in (0, 5, 13, 18.5, 20, 21.6, 25, 26.6, 30, 37, 43)
                                 if cavity_radius(z, p) is not None]},
    }
    configurations = [("primary", board),
                      ("43mm_inward_z20", {"diameter_mm": 43, "thickness_mm": 1.6, "front_z_mm": 20, "component_face": "inward"}),
                      ("43mm_outward_z20", {"diameter_mm": 43, "thickness_mm": 1.6, "front_z_mm": 20, "component_face": "outward"}),
                      ("40mm_outward_z25", {"diameter_mm": 40, "thickness_mm": 1.6, "front_z_mm": 25, "component_face": "outward"}),
                      ("40mm_inward_z25", {"diameter_mm": 40, "thickness_mm": 1.6, "front_z_mm": 25, "component_face": "inward"})]
    for name, variant_board in configurations:
        result, substrate, component_shapes = scenario(name, variant_board, components, cavity, shell, speaker, p, Part, Vector)
        report["scenarios"].append(result)
        if name == "primary":
            assembly.append(feature("PCBSubstrate", substrate, "PCB physical substrate (not a routed board)", "Electronics",
                                    "Manifest board dimensions" if manifest else "Placeholder dimensions only"))
            for component, (reference, shape) in zip(components, component_shapes):
                obj = feature("Proxy_"+reference, shape, reference+" - approximate component PROXY", "Electronics",
                              component["height_source"])
                obj.addProperty("App::PropertyString", "FootprintReference", "Provenance")
                obj.FootprintReference = component["footprint"]
                assembly.append(obj)
    print_shapes, grille_report = make_print_parts(p, Part, Vector)
    for name, shape in print_shapes.items():
        assembly.append(feature(name, shape, name+" - INERT FIT ONLY", "PrintParts",
                                "Original conceptual geometry. Alignment holes, not qualified threads or structural retention."))
    report["grille"] = grille_report
    rail_corner_radius = math.hypot(
        p["board_diameter_mm"]/2+p["support_board_edge_gap_mm"]+p["support_radial_thickness_mm"],
        p["support_tangential_width_mm"]/2)
    support_wall_radius = cavity_radius(p["board_front_z_mm"], p)
    report["carrier_interfaces"] = {
        "bond_radial_gap_at_lip_mm": (p["lip_id_mm"]-p["interface_outer_diameter_mm"])/2,
        "seat_radial_clearance_to_speaker_mm": p["speaker_seat_radial_clearance_mm"],
        "rail_top_corner_radial_margin_mm": None if support_wall_radius is None else support_wall_radius-rail_corner_radius,
        "board_support_plane_z_mm": p["board_front_z_mm"],
        "grille_alignment_hole_count": 3,
        "alignment_hole_diameter_mm": p["fastener_clearance_diameter_mm"],
        "alignment_pitch_radius_mm": p["fastener_pitch_radius_mm"],
        "note": "Contact/alignment concepts only. Holes are unthreaded; no inserts, screw lengths, "
                "clamps, positive board/speaker restraint or USB/retention load qualification."
    }
    report["speaker"] = fit_record(speaker, p["speaker_diameter_mm"]/2, cavity, shell, p)
    comparison = Part.makeCylinder(25.4, 30)
    report["ek1725_seller_cylinder_comparison"] = {
        "note": "Nominal seller 2 inch x 30 mm cylinder, not measured basket/terminals or a definitive part rejection",
        **fit_record(comparison, 25.4, cavity, shell, p)}
    named_solids = [(obj.Name, obj.Shape) for obj in assembly]
    report["battery"] = {
        "dummy": fit_record(battery, math.hypot(p["battery_width_mm"]/2, p["battery_depth_mm"]/2), cavity, shell, p),
        "clearance_envelope": fit_record(battery_keepout, math.hypot(p["battery_width_mm"]/2+clearance,
                                                                  p["battery_depth_mm"]/2+clearance), cavity, shell, p),
        "variants": []}
    compact_dimensions = (p["gauge_compact_battery_width_mm"], p["gauge_compact_battery_depth_mm"],
                          p["gauge_compact_battery_height_mm"])
    for width, depth, height, front_z in (
            (*compact_dimensions, p["battery_front_z_mm"]),
            (20, 30, 6, p["battery_front_z_mm"]),
            (20, 30, 8, p["battery_front_z_mm"]),
            (*compact_dimensions, p["battery_front_z_mm"]+0.5)):
        keepout = box_at(width+2*clearance, depth+2*clearance, height+2*clearance, 0, 0,
                         front_z-clearance, Part, Vector)
        intersections = []
        for name, shape in named_solids:
            if name == "BatteryDummy":
                continue
            overlap = common_volume(keepout, shape)
            if overlap > VOLUME_EPSILON:
                intersections.append({"other": name, "volume_mm3": overlap})
        report["battery"]["variants"].append({
            "dummy_dimensions_mm": [width, depth, height], "dummy_front_z_mm": front_z,
            "clearance_per_face_mm": clearance, "material_intersections": intersections,
            "note": "Dimensional comparison only; no selected pack/capacity/current. "
                    "Cavity containment alone does not establish component clearance.",
            **fit_record(keepout, math.hypot(width/2+clearance, depth/2+clearance), cavity, shell, p)})
    report["assembly_intersections"] = []
    # Exact BRep common volumes, not bounding-box overlap alone; contact with
    # zero volume is allowed. The shell is never cut to excuse the USB proxy.
    for (left_name, left), (right_name, right) in itertools.combinations(named_solids, 2):
        overlap = common_volume(left, right)
        if overlap > VOLUME_EPSILON:
            report["assembly_intersections"].append({"left": left_name, "right": right_name, "volume_mm3": overlap})
    report["battery_clearance_intersections"] = []
    for name, shape in named_solids:
        if name == "BatteryDummy":
            continue
        overlap = common_volume(battery_keepout, shape)
        if overlap > VOLUME_EPSILON:
            report["battery_clearance_intersections"].append({"other": name, "volume_mm3": overlap})
    report["print_parts"] = {name: shape_stats(shape) for name, shape in print_shapes.items()}
    dummy_shapes, dummy_descriptions = make_fit_dummies(p, board, components, Part, Vector)
    for name, shape in dummy_shapes.items():
        feature(name, shape, name+" - INERT PRINT DUMMY", "FitDummies", dummy_descriptions[name]["description"])
    report["fit_dummies"] = {
        "units": "mm", "scale": "100%; no fit-to-bed resizing",
        "scope": "Exact supplied proxy geometry, not manufacturer bodies; illustrative speaker explicitly separate",
        "placement_sha256": report["input"]["placement_sha256"],
        "objects": dummy_descriptions,
        "print_guidance": "Creality K1C, PLA: use the installed nozzle/filament PLA profile. "
                          "Inspect fine details and USB overhang; no verified slicer profile or G-code supplied. "
                          "Fit-only, never live battery retention, heated parts or a child-use assembly.",
    }
    report["limits"] = [
        "No real-shell measurement/tolerance/ovality, clapper intrusion or usable handle interior.",
        "Speaker cylinder cannot qualify basket, terminals, cone excursion, rear vent or sound output.",
        "EK1794 seller 3 W title versus 2 W description unresolved; no live acoustic qualification.",
        "No pack selected; clearance is an assumption, never permission to compress a live cell.",
        "No USB slot or mating plug/cable/strain relief model; interference remains visible.",
        "No battery tray/restraint, final board fastening, captive inserts, adhesive selection, or retention qualification.",
        "Different PCB scenarios reuse unchanged XY proxies, not new KiCad placements or routing.",
        "Component heights/proxies are not manufacturer models and do not prove real mated envelope fit.",
        "FCStd feature solids are script-generated; edit Parameters and regenerate, not spreadsheet-only live recompute.",
        "Print parts are inert adult-supervised fit gauges, not assembled electronics or child-ready hardware.",
        "New standalone dummies are print-bed normalized; existing carrier/interface/grille retain assembly coordinates.",
        "Populated PCBA print is a fused proxy union, not an electronics/thermal model; fine details may not resolve in PLA.",
        "Illustrative speaker basket and magnet axial split are unmeasured and never used instead of the collision cylinder.",
    ]
    render_views(output, p, components, board, report)
    render_dummy_views(output, p, dummy_descriptions)
    write_json(output / "parameters.json", p)
    write_json(output / "fit-dummies.json", report["fit_dummies"])
    report["artifacts"] = export_and_check(output, doc, assembly, print_shapes, dummy_shapes, dummy_descriptions,
                                         p, App, Part, Mesh, MeshPart)
    for filename in ("packaging-views.svg", "fit-dummies.svg"):
        report["artifacts"]["views/"+filename] = {
            "sha256": sha256(output / "views" / filename), "kind": "original generated SVG, no photo assets"}
    report["artifacts"]["fit-dummies.json"] = {
        "sha256": sha256(output / "fit-dummies.json"), "kind": "standalone inert fit dummy inventory"}
    write_json(output / "fit-report.json", report)
    summary = {"output": str(output), "scope": report["scope"], "component_count": len(components),
               "component_height_overrides": height_overrides,
               "primary_cavity_conflicts": report["scenarios"][0]["cavity_conflicts"],
               "primary_required_shell_cutouts": report["scenarios"][0]["required_shell_cutouts"],
               "primary_unplanned_cavity_conflicts": report["scenarios"][0]["unplanned_cavity_conflicts"],
               "assembly_intersections": report["assembly_intersections"],
               "battery_clearance_contained": report["battery"]["clearance_envelope"]["contained_in_assumed_cavity"],
               "exported_artifacts": list(report["artifacts"])}
    if args.completion_file is None:
        raise RuntimeError("Internal FreeCAD invocation requires a completion file")
    write_json(args.completion_file, summary)


if __name__ == "__main__":
    options = arguments()
    if options.inside_freecad:
        build(options)
    else:
        launcher(options)
