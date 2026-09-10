#!/usr/bin/env python3
"""Original MIT mechanical draft. Two printed parts, explicit schema-2 input.

Uses installed FreeCADCmd only, isolated preferences and a fresh completion
token. Never regenerates the frozen kit, modifies electronics or opens a GUI.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_mechanical as base

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "mechanical" / "studies" / "2026-09-09-integrated-cartridge"
HELPER_HASH = "c9ef5a33a86cd8f3635f6aa6171c2d84b6d7662f68bcb578d9cd9a43bdfb3aab"
ANGLE = math.degrees(math.atan2(15.7, 10))
EPS = base.VOLUME_EPSILON
DIMENSIONS = {
    "board_diameter_mm": 43.0, "board_front_z_mm": 20.5, "board_back_z_mm": 22.1,
    "speaker_diameter_mm": 40.0, "speaker_basket_rear_z_mm": 12.0,
    "speaker_basket_rear_diameter_mm": 32.0, "speaker_magnet_diameter_mm": 22.0,
    "speaker_depth_mm": 19.0, "speaker_front_z_mm": 0.0,
    "grille_outer_diameter_mm": 72.0, "grille_bottom_z_mm": -4.5,
    "annular_body_plate_thickness_mm": 2.7, "grille_root_axial_overlap_mm": 1.0,
    "speaker_seat_aperture_mm": 36.0, "speaker_seat_top_z_mm": 0.0,
    "integral_lip_register_diameter_mm": 69.0,
    "lower_support_radius_mm": 22.6, "lower_support_radial_mm": 4.6,
    "lower_support_tangential_mm": 7.0, "lower_support_top_z_mm": 9.0,
    "capture_ear_tangential_mm": 8.0, "capture_ear_bottom_z_mm": 9.0,
    "capture_inner_diameter_mm": 22.8, "capture_outer_diameter_mm": 37.0,
    "capture_bottom_z_mm": 12.3, "capture_top_z_mm": 14.8,
    "board_boss_diameter_mm": 6.4, "board_boss_bottom_z_mm": 14.0,
    "insert_pocket_diameter_mm": 3.0, "insert_length_mm": 4.0,
    "lower_screw_underhead_z_mm": 11.5, "lower_screw_length_mm": 8.0,
    "board_screw_underhead_z_mm": 22.4, "board_screw_length_mm": 6.0,
    "screw_shank_diameter_mm": 2.0, "screw_head_diameter_mm": 3.8,
    "screw_head_height_mm": 2.0, "board_washer_diameter_mm": 4.0,
    "board_washer_thickness_mm": 0.3,
}


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--placement", required=True, type=Path,
                        help="Actual schema-2 wing manifest; missing/invalid input is an error.")
    parser.add_argument("--freecad-cmd", type=Path, default=Path(
        os.environ.get("LOCALAPPDATA", "")) / "Programs" / "FreeCAD 1.1" / "bin" / "FreeCADCmd.exe")
    parser.add_argument("--inside-freecad", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--completion-file", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--token", help=argparse.SUPPRESS)
    parser.add_argument("--expected-placement-sha256", help=argparse.SUPPRESS)
    return parser.parse_args()


def read_manifest(path):
    raw = path.read_bytes()
    manifest = json.loads(raw.decode("utf-8-sig"))
    if (not isinstance(manifest, dict) or type(manifest.get("schema_version")) is not int
            or manifest["schema_version"] != 2 or manifest.get("units") != "mm"):
        raise ValueError("Require schema_version 2, units mm")
    board = manifest["board"]
    for key, expected in (("diameter_mm", 43), ("thickness_mm", 1.6), ("front_z_mm", 20.5)):
        if abs(base.finite_number(board[key], "board." + key) - expected) > 1e-8:
            raise ValueError("Shared board interface changed: " + key)
    if board["front_face"] != "speaker":
        raise ValueError("F substrate surface must face speaker")
    components = manifest["components"]
    if not isinstance(components, list) or not components:
        raise ValueError("Need actual populated component array")
    refs = set()
    for c in components:
        for key in ("reference", "footprint", "height_source"):
            if not isinstance(c[key], str) or not c[key].strip():
                raise ValueError("Missing component " + key)
        if c["reference"] in refs:
            raise ValueError("Duplicate component " + c["reference"])
        refs.add(c["reference"])
        for key in ("x_mm", "y_mm", "rotation_deg", "z_min_mm", "z_max_mm"):
            base.finite_number(c[key], c["reference"] + "." + key)
        for key in ("width_mm", "depth_mm", "height_mm"):
            base.finite_number(c[key], c["reference"] + "." + key, positive=True)
        if c["side"] not in ("F", "B") or type(c["requires_shell_cutout"]) is not bool:
            raise ValueError("Invalid side or cutout flag")
        expected = (20.5 - c["height_mm"], 20.5) if c["side"] == "F" else (22.1, 22.1 + c["height_mm"])
        if any(abs(c[k] - v) > 1e-7 for k, v in zip(("z_min_mm", "z_max_mm"), expected)):
            raise ValueError("Side/height/z mismatch: " + c["reference"])
    holes = manifest["mounting_holes"]
    if not isinstance(holes, list) or len(holes) != 2:
        raise ValueError("Require two shared mounting holes")
    for h, ref, x, y in zip(sorted(holes, key=lambda h: h["reference"]),
                            ("MH1", "MH2"), (10, -10), (15.7, -15.7)):
        if h["reference"] != ref or h.get("net") != "GND":
            raise ValueError("Expected GND-assigned " + ref)
        for key, expected in (("x_mm", x), ("y_mm", y), ("drill_mm", 2.2), ("keepout_radius_mm", 3.2)):
            if abs(base.finite_number(h[key], ref + "." + key) - expected) > 1e-8:
                raise ValueError("Shared mounting interface changed: " + ref + "." + key)
        pad = base.finite_number(h["pad_diameter_mm"], ref + ".pad_diameter_mm", positive=True)
        if not h["drill_mm"] < pad <= 6.4:
            raise ValueError("Pad must fit the shared support reservation")
    for key in ("generated_pcb_sha256", "schematic_sha256"):
        value = manifest[key]
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError("Missing/invalid electrical source hash: " + key)
    keepouts = manifest["cross_face_keepouts"]
    if not isinstance(keepouts, list) or not keepouts:
        raise ValueError("Require explicit USB cross-face planning reservations")
    for keepout in keepouts:
        for key in ("x", "y", "angle"):
            base.finite_number(keepout[key], "cross_face_keepouts." + key)
        for key in ("plan_w", "plan_h"):
            base.finite_number(keepout[key], "cross_face_keepouts." + key, positive=True)
        if keepout["side"] not in ("F", "B"):
            raise ValueError("Cross-face reservation side must be F or B")
        if not isinstance(keepout["source"], str) or not keepout["source"].strip():
            raise ValueError("Cross-face reservation needs a source/assumption")
    return raw, manifest


def launch(args):
    raw, _ = read_manifest(args.placement)
    if base.sha256(Path(base.__file__)) != HELPER_HASH:
        raise ValueError("Frozen geometry helper hash changed")
    if not args.freecad_cmd.is_file():
        raise FileNotFoundError(args.freecad_cmd)
    digest = hashlib.sha256(raw).hexdigest()
    with tempfile.TemporaryDirectory(prefix="handbell-integrated-") as tmp:
        tmp = Path(tmp)
        marker, token = tmp / "complete.json", uuid.uuid4().hex
        script = str(Path(__file__).resolve())
        argv = [script, "--placement", str(args.placement.resolve()), "--inside-freecad",
                "--completion-file", str(marker), "--token", token,
                "--expected-placement-sha256", digest]
        bootstrap = f"import runpy, sys\nsys.argv = {argv!r}\nrunpy.run_path({script!r}, run_name='__main__')\n"
        command = [str(args.freecad_cmd), "--user-cfg", str(tmp / "user.cfg"),
                   "--system-cfg", str(tmp / "system.cfg")]
        result = subprocess.run(command, input=bootstrap, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, encoding="utf-8", errors="replace", timeout=900)
        STUDY.mkdir(parents=True, exist_ok=True)
        (STUDY / "freecad-build.log").write_text(
            "Command: " + subprocess.list2cmdline(command) + "\n" + bootstrap + "\n" + result.stdout,
            encoding="utf-8")
        if result.returncode != 0 or not marker.is_file():
            print(result.stdout, file=sys.stderr)
            raise RuntimeError("FreeCAD did not complete this run; old artifacts are not proof of success")
        completion = json.loads(marker.read_text(encoding="utf-8"))
        if completion["token"] != token or completion["placement_sha256"] != digest:
            raise RuntimeError("Completion does not match this invocation")
        print(json.dumps(completion, indent=2))


def translated(shape, vector):
    result = shape.copy()
    result.translate(vector)
    return result


def pair_record(a, b):
    return {"intersection_mm3": base.common_volume(a, b), "distance_mm": a.distToShape(b)[0]}


def make_keepout_prism(keepout, inward_limit, Part, Vector):
    z_min, z_max = (22.1, inward_limit) if keepout["side"] == "B" else (0.0, 20.5)
    shape = base.box_at(keepout["plan_w"], keepout["plan_h"], z_max-z_min, 0, 0, z_min, Part, Vector)
    shape.rotate(Vector(), Vector(0, 0, 1), keepout["angle"])
    shape.translate(Vector(keepout["x"], keepout["y"], 0))
    return shape, [z_min, z_max]


def export_stl(path, shape, Part, Mesh, MeshPart):
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.05, AngularDeflection=0.15, Relative=False)
    mesh.write(str(path))
    read = Mesh.Mesh(str(path))
    if not read.isSolid() or read.countComponents() != 1 or read.hasNonManifolds() or read.hasSelfIntersections():
        raise RuntimeError(path.name + ": invalid/disconnected mesh")
    brep = Part.Shape()
    brep.makeShapeFromMesh(read.Topology, 0.001)
    if len(brep.Shells) != 1 or not brep.Shells[0].isClosed():
        raise RuntimeError(path.name + ": reimport not one closed shell")
    solid = Part.makeSolid(brep.Shells[0])
    stats = base.shape_stats(solid)
    volume_error = abs(read.Volume - shape.Volume) / shape.Volume
    error = max(abs(a - b) for key in ("min_mm", "max_mm")
                for a, b in zip(base.bounds(shape)[key], base.bounds(solid)[key]))
    if volume_error > 0.01 or error > 0.1:
        raise RuntimeError(path.name + ": mesh dimension/volume drift")
    return {"sha256": base.sha256(path), "units": "unitless STL; import as mm at 100 percent",
            "connected_components": 1, "manifold": True, "self_intersections": False,
            "roundtrip": stats, "relative_volume_error": volume_error, "maximum_bound_error_mm": error}


def render_svg(path, manifest, report):
    elements = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="870" viewBox="0 0 1200 870">',
                '<rect width="1200" height="870" fill="#fafafa"/>',
                '<style>text{font-family:Arial,sans-serif;fill:#17202a} .note{font-size:14px}</style>',
                '<text x="24" y="32" font-size="23">Two-piece integrated cartridge - ORIGINAL DRAFT</text>',
                '<text x="24" y="59" class="note">Direct speaker insertion before rear yoke. No battery holder, shell attachment or loaded-use approval.</text>']
    # Section is along mounting radial axis u, not global X.
    cx, top, scale = 270, 150, 6.4
    def rect(x1, z1, x2, z2, color, dash=""):
        elements.append(f'<rect x="{cx+x1*scale:.2f}" y="{top+z1*scale:.2f}" width="{(x2-x1)*scale:.2f}" '
                        f'height="{(z2-z1)*scale:.2f}" fill="{color}" stroke="#35424a" {dash}/>')
    elements.append('<text x="30" y="99" font-size="18">Section along MH1-MH2 axis (z inward/down)</text>')
    rect(-36, -3.7, 36, -1, "#86c5ac")
    rect(-19, -4.5, 19, -2.7, "#86c5ac")
    rect(-20.2, -1, -18, 0, "#86c5ac")
    rect(18, -1, 20.2, 0, "#86c5ac")
    rect(-20, 0, 20, 12, "#e6eaf0")
    rect(-11, 12, 11, 19, "#bfc8d4")
    for sign in (-1, 1):
        a, b = sorted((sign*20.3, sign*24.9))
        rect(a, -1, b, 9, "#86c5ac")
        a, b = sorted((sign*11.4, sign*18.5))
        rect(a, 12.3, b, 14.8, "#f1c27c")
        a, b = sorted((sign*(math.hypot(10, 15.7)-3.2), sign*(math.hypot(10, 15.7)+3.2)))
        rect(a, 14, b, 20.5, "#f1c27c")
    rect(-21.5, 20.5, 21.5, 22.1, "#6690cb")
    elements.extend([
        '<path d="M550 290 L550 155 M542 165 L550 155 L558 165" fill="none" stroke="#b33b34" stroke-width="3"/>',
        '<text x="440" y="312" font-size="13">Speaker moves toward seat (-z)</text>',
        '<text x="440" y="330" font-size="13">before yoke and PCB are fitted</text>',
    ])
    elements.extend([
        '<text x="28" y="334" class="note">Green: integral grille/seat/lip register/lower supports</text>',
        '<text x="28" y="357" class="note">Amber: removable capture yoke + D6.4 PCB bosses</text>',
        '<text x="28" y="380" class="note">Grey: D40 x 12 basket bound + D22 x 7 magnet</text>',
        '<text x="28" y="403" class="note">Capture ID22.8; rear face gap0.3; rim bearing unknown</text>',
        '<text x="650" y="99" font-size="18">Assembly XY plan - both faces overlaid</text>'])
    px, py, s = 905, 269, 6.2
    elements.append(f'<circle cx="{px}" cy="{py}" r="{21.5*s}" fill="#e6edf6" stroke="#304b72"/>')
    elements.append(f'<rect x="{px-19*s}" y="{py-10*s}" width="{38*s}" height="{20*s}" fill="#f7dddd" stroke="#be5656" stroke-dasharray="5,4"/>')
    for c in manifest["components"]:
        corners = base.rotated_corners(c)
        points = " ".join(f"{px+corners[i][0]*s:.2f},{py-corners[i][1]*s:.2f}" for i in (0, 1, 3, 2))
        color = "#b889d0" if c["side"] == "B" else "#92b6d9"
        elements.append(f'<polygon points="{points}" fill="{color}" stroke="#4d5661" stroke-width=".5"><title>'
                        f'{html.escape(c["reference"])} {c["side"]} z{c["z_min_mm"]:g}..{c["z_max_mm"]:g}</title></polygon>')
    for hole in manifest["mounting_holes"]:
        x, y = px + hole["x_mm"]*s, py - hole["y_mm"]*s
        elements.append(f'<circle cx="{x}" cy="{y}" r="{3.2*s}" fill="none" stroke="#d98020" stroke-width="2"/>')
        elements.append(f'<circle cx="{x}" cy="{y}" r="{1.1*s}" fill="white" stroke="#263441"/>')
    for keepout in manifest["cross_face_keepouts"]:
        corners = base.rotated_corners({
            "x_mm": keepout["x"], "y_mm": keepout["y"], "rotation_deg": keepout["angle"],
            "width_mm": keepout["plan_w"], "depth_mm": keepout["plan_h"]})
        points = " ".join(f"{px+corners[i][0]*s:.2f},{py-corners[i][1]*s:.2f}" for i in (0, 1, 3, 2))
        elements.append(f'<polygon points="{points}" fill="none" stroke="#573629" stroke-width="2" '
                        f'stroke-dasharray="4,3"><title>{html.escape(keepout["source"])}</title></polygon>')
    elements.extend([
        '<text x="650" y="425" class="note">Blue F/speaker; purple B/handle; orange mount reservations</text>',
        '<text x="650" y="448" class="note">Red: planning corridor only, NOT a retained battery</text>',
        '<text x="650" y="471" class="note">Brown dashed: cross-face USB anchor planning projection</text>',
        '<text x="24" y="490" font-size="18">Assembly sequence (all outside the bell)</text>',
        '<text x="24" y="518" class="note">1. Fit metal inserts in both printed pieces; inspect blind-hole depths without a live cell.</text>',
        '<text x="24" y="544" class="note">2. Lower D40 speaker directly onto body seat with rear yoke and PCB absent.</text>',
        '<text x="24" y="570" class="note">3. Lower rear yoke over D22 magnet; two M2x8 screws attach it to lower supports.</text>',
        '<text x="24" y="596" class="note">4. Lower populated PCB onto D6.4 bosses; washers and M2x6 screws from handle side.</text>',
        '<text x="24" y="622" class="note">5. Inspect clearances; do not install an unselected cell. Shell attachment/USB slot remain design gates.</text>',
        '<text x="24" y="660" font-size="17">Limits that the geometry must not hide</text>',
        '<text x="24" y="688" class="note">No claim of rear insertion through the installed yoke. No PLA flex clips, custom printed threads or loose printed ring.</text>',
        '<text x="24" y="714" class="note">No excursion, terminals, vent, wire, fastener tooling, tolerance, load, child-use or PLA temperature qualification.</text>',
        f'<text x="24" y="740" class="note">Actual placement SHA256: {report["input"]["placement_sha256"]}</text>',
        '<text x="24" y="768" class="note">Drawing is explanatory; native BReps and raw fit-report values govern the draft.</text>',
        '<text x="24" y="801" class="note">Original mechanical primitives / illustration MIT. Adapted electronics context retains CC BY-SA 3.0 notices.</text>',
        '</svg>'])
    path.write_text("\n".join(elements) + "\n", encoding="utf-8")


def build(args):
    if not args.completion_file or not args.token or not args.expected_placement_sha256:
        raise ValueError("Internal execution requires a fresh launch token and expected input hash")
    raw, manifest = read_manifest(args.placement)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != args.expected_placement_sha256 or base.sha256(Path(base.__file__)) != HELPER_HASH:
        raise ValueError("Input/helper changed after launch")
    import FreeCAD as App
    import Part
    import Mesh
    import MeshPart
    V = App.Vector
    STUDY.mkdir(parents=True, exist_ok=True)
    App.ParamGet("User parameter:BaseApp/Preferences/Document").SetInt("CountBackupFiles", 0)
    shell_path = ROOT / "mechanical" / "parameters.json"
    p = json.loads(shell_path.read_text(encoding="utf-8-sig"))
    cavity = base.make_profile(p, Part, V)
    shell = base.make_profile(p, Part, V, 0.7, capped=True).cut(cavity)
    mouth_outside = Part.makeCylinder(100, 100, V(0, 0, -100))
    allowed = cavity.fuse(mouth_outside)
    doc = App.newDocument("IntegratedCartridgeDraft")
    doc.Label = "Original two-piece cartridge - inert fit draft"
    doc.Comment = "Original mechanics MIT; electronics context CC BY-SA 3.0. No live battery or structural qualification."

    def feature(name, shape, label=None):
        base.shape_stats(shape)
        obj = doc.addObject("Part::Feature", name)
        obj.Label = label or name
        obj.Shape = shape
        return obj

    def box(w, d, h, x, y, z):
        return base.box_at(w, d, h, x, y, z, Part, V)

    def cylinder(r, h, x=0, y=0, z=0):
        return Part.makeCylinder(r, h, V(x, y, z))

    def radial(shape, degrees):
        result = shape.copy()
        result.rotate(V(), V(0, 0, 1), degrees)
        return result

    def fuse(shapes):
        result = shapes[0].multiFuse(shapes[1:]).removeSplitter() if len(shapes) > 1 else shapes[0]
        if base.shape_stats(result)["solid_count"] != 1:
            raise RuntimeError("A primary part is not a single connected solid")
        return result

    def scene_record(shape):
        return {**base.shape_stats(shape), "uncut_shell_intersection_mm3": base.common_volume(shape, shell),
                "outside_cavity_mm3": max(0, shape.cut(cavity).Volume),
                "outside_cavity_excluding_open_mouth_mm3": max(0, shape.cut(allowed).Volume),
                "distance_to_uncut_shell_mm": shape.distToShape(shell)[0]}

    ring = lambda ro, ri, h, z: base.ring(ro, ri, h, z, Part, V)
    grille = cylinder(19, 1.8, z=-4.5)
    slot_region = cylinder(17, 2.2, z=-4.7)
    for x in range(-16, 17, 4):
        grille = grille.cut(box(2.8, 36, 2.2, x, 0, -4.7).common(slot_region))
    lower = [ring(36, 18, 2.7, -3.7), grille, ring(20.2, 18, 1.2, -1.2),
             ring(34.5, 31, 3, -1)]
    for a in (ANGLE, ANGLE + 180):
        lower.append(radial(box(4.6, 7, 10.2, 22.6, 0, -1.2), a))
    body = fuse(lower)
    upper = [ring(18.5, 11.4, 2.5, 12.3)]
    lower_mounts = []
    for a in (ANGLE, ANGLE + 180):
        x, y = 22.6 * math.cos(math.radians(a)), 22.6 * math.sin(math.radians(a))
        lower_mounts.append((x, y))
        upper.extend((radial(box(4, 8, 3.5, 22.6, 0, 9), a),
                      radial(box(5.0, 8, 2.0, 20.5, 0, 12.3), a)))
        body = body.cut(cylinder(1.5, 4.2, x, y, 4.8)).cut(cylinder(1.1, 5.8, x, y, 3.2))
    for h in manifest["mounting_holes"]:
        upper.append(cylinder(3.2, 6.5, h["x_mm"], h["y_mm"], 14))
    yoke = fuse(upper)
    for x, y in lower_mounts:
        yoke = yoke.cut(cylinder(1.1, 6, x, y, 8.9))
        yoke = yoke.cut(cylinder(2.05, 4, x, y, 11.5))
    for h in manifest["mounting_holes"]:
        x, y = h["x_mm"], h["y_mm"]
        yoke = yoke.cut(cylinder(1.5, 4.2, x, y, 16.3)).cut(cylinder(1.1, 4.7, x, y, 15.8))
    body, yoke = body.removeSplitter(), yoke.removeSplitter()
    for shape in (body, yoke):
        if base.shape_stats(shape)["solid_count"] != 1:
            raise RuntimeError("Disconnected structural piece")
    speaker = cylinder(20, 12).fuse(cylinder(11, 7, z=12)).removeSplitter()
    illustrative = Part.makeCone(20, 16, 12).fuse(cylinder(11, 7, z=12)).removeSplitter()
    pcb = cylinder(21.5, 1.6, z=20.5)
    for h in manifest["mounting_holes"]:
        pcb = pcb.cut(cylinder(h["drill_mm"]/2, 1.8, h["x_mm"], h["y_mm"], 20.4))
    components = []
    for c in manifest["components"]:
        shape = box(c["width_mm"], c["depth_mm"], c["height_mm"], 0, 0, c["z_min_mm"])
        shape = radial(shape, c["rotation_deg"])
        shape.translate(V(c["x_mm"], c["y_mm"], 0))
        components.append((c, shape))
    pcba = fuse([pcb] + [s for _, s in components])
    expected_volume = pcb.Volume + sum(s.Volume for _, s in components)
    if abs(pcba.Volume - expected_volume) > 1e-5:
        raise RuntimeError("PCBA proxies overlap or fusion altered the supplied envelopes")
    hardware = []
    for index, (x, y) in enumerate(lower_mounts, 1):
        hardware.append((f"YokeScrew{index}", cylinder(1, 8, x, y, 3.5).fuse(cylinder(1.9, 2, x, y, 11.5))))
        hardware.append((f"LowerInsert{index}", cylinder(1.5, 4, x, y, 5).cut(cylinder(1, 4, x, y, 5))))
    for h in manifest["mounting_holes"]:
        x, y, ref = h["x_mm"], h["y_mm"], h["reference"]
        hardware.append((ref + "Screw", cylinder(1, 6, x, y, 16.4).fuse(cylinder(1.9, 2, x, y, 22.4))))
        hardware.append((ref + "Washer", cylinder(2, .3, x, y, 22.1).cut(cylinder(1.1, .3, x, y, 22.1))))
        hardware.append((ref + "Insert", cylinder(1.5, 4, x, y, 16.5).cut(cylinder(1, 4, x, y, 16.5))))
    assembly = [feature("IntegratedGrilleSeatBody", body), feature("RemovableCaptureYoke", yoke),
                feature("MeasuredSpeakerBodyScreen", speaker), feature("PopulatedWingPCBA", pcba)]
    for name, shape in hardware:
        assembly.append(feature(name, shape, name + " - ordinary M2 placeholder, not selected hardware"))
    feature("AssumedShellUncut", shell, "ASSUMED shell; required USB cutout not subtracted")
    feature("IllustrativeBasketOnly", illustrative, "ILLUSTRATIVE straight basket; not the collision screen")
    feature("SubstrateWithTwoDrills", pcb)
    proxy_group = doc.addObject("App::DocumentObjectGroup", "IndividualComponentEnvelopes")
    for c, shape in components:
        proxy_group.addObject(feature("Proxy_" + c["reference"], shape, c["reference"] + " " + c["side"]))
    for name, contents in (("PlacementManifest", raw.decode("utf-8-sig")),
                           ("BuildSource", Path(__file__).read_text(encoding="utf-8")),
                           ("FrozenHelperSource", Path(base.__file__).read_text(encoding="utf-8")),
                           ("ShellParameters", json.dumps(p, indent=2))):
        doc.addObject("App::TextDocument", name).Text = contents
    sheet = doc.addObject("Spreadsheet::Sheet", "Parameters")
    sheet.set("A1", "Screening dimensions in mm; regenerate source, not live expressions")
    for row, (key, value) in enumerate(DIMENSIONS.items(), 2):
        sheet.set(f"A{row}", key)
        sheet.set(f"B{row}", str(value))
    sheet.setColumnWidth("A", 360)
    report = {
        "schema_version": 1, "units": "mm", "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "Two-piece structural concept; NOT a complete battery-retained or shell-mounted assembly",
        "input": {"placement_path": str(args.placement.resolve()), "placement_sha256": digest,
                  "electrical_pcb_sha256": manifest["generated_pcb_sha256"],
                  "electrical_schematic_sha256": manifest["schematic_sha256"],
                  "builder_sha256": base.sha256(Path(__file__)), "helper_sha256": HELPER_HASH,
                  "shell_parameters_sha256": base.sha256(shell_path)},
        "toolchain": {"freecad": App.Version(), "opencascade": Part.OCC_VERSION, "python": sys.version},
        "dimensions": DIMENSIONS, "mounting_holes_consumed": manifest["mounting_holes"],
        "primary_printed_piece_count": 2, "structural_parts": {},
        "fastener_stack": {
            "note": "Nominal smooth envelopes only, not chosen fasteners or insert installation dimensions",
            "lower_joint": {"screw": "M2x8", "head_z_mm": [11.5, 13.5],
                            "shank_z_mm": [3.5, 11.5], "insert_z_mm": [5, 9],
                            "thread_engagement_envelope_mm": 4, "blind_bottom_clearance_mm": 0.3,
                            "minimum_insert_pocket_radial_wall_mm": 0.8,
                            "ear_head_counterbore_side_ligament_mm": 1.95},
            "pcb_joint": {"screw": "M2x6", "washer_z_mm": [22.1, 22.4],
                          "head_z_mm": [22.4, 24.4], "shank_z_mm": [16.4, 22.4],
                          "insert_z_mm": [16.5, 20.5], "thread_engagement_envelope_mm": 4,
                          "blind_bottom_clearance_mm": 0.6, "local_support_diameter_mm": 6.4},
            "load_path": "PCB washer -> locally supported substrate -> yoke boss -> capture ring/arms -> two M2 lower joints -> grille/seat body. Speaker front seat and rear basket/magnet stops do not rely on PCB or contacts.",
            "unresolved": "Actual insert OD/knurl/installation, plastic creep, torque, stress near IMU, cell insulation, shell attachment."
        },
        "speaker": scene_record(speaker), "substrate": scene_record(pcb),
        "pcba_proxy": {**base.shape_stats(pcba), "fusion_added_volume_mm3": pcba.Volume - expected_volume,
                       "fitted_components": len(components), "hole_diameter_mm": 2.2,
                       "envelopes_enlarged_or_bridged": False,
                       "omitted_unqualified_details": "USB anchor/solder volumes and individual USB PTH/NPTH drills are not supplied as 3D primitives. The separate cross-face reservation is not physical PCBA material."},
        "components": {}, "required_shell_cutouts": [], "mechanical_pairs": {},
        "hardware": {}, "battery_alternatives": [], "assembly_paths": {}, "cross_face_reservations": {},
        "limits": [
            "Front z0 is assumed. D40 x z0..12 plus D22 x z12..19 is a conditional BODY bound, not complete speaker geometry.",
            "D32 rear basket station is measured; load-bearing annulus, rim, terminal, wire, vent and excursion geometry are unknown.",
            "The capture ring limits translation by magnet/basket body geometry, but must not load a vent, cone, terminal or unsuitable basket surface.",
            "The grille has only 2.7 mm nominal front-plane separation locally; no acoustic/excursion approval.",
            "No battery retainer or contacts are supplied. An optional floor sensitivity is NOT a retained or attached holder.",
            "Lip registration is not shell attachment. Adhesive/fastened attachment and supported USB access remain unresolved.",
            "M2 cylinders/inserts are placeholders without helical threads, torque, pullout, creep, fatigue or dimensional approval.",
            "GND is an unrouted net assignment, not a grounding or cell insulation result. PCB screw torque can stress the IMU.",
            "Sweeps cover ideal rigid translation outside the shell, not cables, screwdriver access, deformation or a complete assembly inserted through the shell.",
            "No live-cell, electrical, child-use, PLA temperature, shake, drop or strength qualification."
        ],
        "license_scope": "Original mechanics/code/SVG MIT under mechanical/LICENSE. Mixed electronics context retains hardware/handbell CC BY-SA 3.0 notices."
    }
    for name, shape in (("integrated_grille_seat_body", body), ("removable_capture_yoke", yoke)):
        report["structural_parts"][name] = scene_record(shape)
    solids = {"body": body, "yoke": yoke, "speaker": speaker, "pcba": pcba}
    for i, (name, shape) in enumerate(solids.items()):
        for other, target in list(solids.items())[i+1:]:
            report["mechanical_pairs"][name + "__" + other] = pair_record(shape, target)
    for c, shape in components:
        record = {**c, **scene_record(shape), "speaker": pair_record(shape, speaker),
                  "body": pair_record(shape, body), "yoke": pair_record(shape, yoke)}
        report["components"][c["reference"]] = record
        if c["requires_shell_cutout"]:
            report["required_shell_cutouts"].append({
                "reference": c["reference"], "status": "required_not_implemented",
                "proxy_bounds": base.bounds(shape), "raw_shell_intersection_mm3": base.common_volume(shape, shell),
                "outside_cavity_mm3": shape.cut(cavity).Volume,
                "note": "Full proxy retained. Not a USB plug, underside-anchor, cable, slot or supporting-bracket specification."})
    for name, shape in hardware:
        report["hardware"][name] = {**scene_record(shape),
                                    "structure": {n: pair_record(shape, s) for n, s in solids.items()}}
    keepout_shapes = {}
    keepout_group = doc.addObject("App::DocumentObjectGroup", "CrossFacePlanningReservations")
    for index, keepout in enumerate(manifest["cross_face_keepouts"], 1):
        name = f"CrossFaceReservation{index}"
        prism, z_range = make_keepout_prism(keepout, p["linear_end_z_mm"], Part, V)
        keepout_shapes[name] = prism
        keepout_group.addObject(feature(name, prism, "PLANNING ONLY: " + keepout["source"]))
        report["cross_face_reservations"][name] = {
            "input": keepout, "screened_z_range_mm": z_range,
            "interpretation": "Full face-to-cavity-depth projection because anchor height is unknown; NOT physical metal or a measured occupied height. Excluded from PCBA fusion and assembly exports.",
            "components": {c["reference"]: pair_record(prism, shape)
                           for c, shape in components if c["side"] == keepout["side"]},
            "structure": {n: pair_record(prism, s) for n, s in
                          [("body", body), ("yoke", yoke), ("speaker", speaker)] + hardware}}

    # Exact translation bounds: cylindrical segments sweep to longer cylinders.
    # PCBA boxes extrude axially to the union of every pose, preserving XY.
    speaker_sweep = cylinder(20, 62).fuse(cylinder(11, 57, z=12))
    report["assembly_paths"]["speaker_into_body"] = {
        "motion": "Axial translation from front z50 down to z0; yoke, PCB and screws absent",
        "exact_swept_solid": pair_record(speaker_sweep, body),
        "minimum_unobstructed_basket_aperture_mm": 40.6,
        "sample_step_mm": 2.0,
        "samples": [{"front_z_mm": z, **pair_record(translated(speaker, V(0, 0, z)), body)}
                    for z in range(0, 51, 2)]}
    # Every yoke point stays inside this conservative union during +Z translation.
    yoke_sweep_segments = [ring(18.5, 11.4, 42.5, 12.3)]
    for a in (ANGLE, ANGLE + 180):
        yoke_sweep_segments.extend((radial(box(4, 8, 43.5, 22.6, 0, 9), a),
                                   radial(box(5, 8, 42, 20.5, 0, 12.3), a)))
    for h in manifest["mounting_holes"]:
        yoke_sweep_segments.append(cylinder(3.2, 46.5, h["x_mm"], h["y_mm"], 14))
    yoke_sweep = Part.makeCompound(yoke_sweep_segments)
    report["assembly_paths"]["yoke_over_seated_speaker"] = {
        "motion": "Axial translation +40 to 0 mm; PCB and hardware absent",
        "conservative_sweep_without_hole_subtractions": {
            "speaker": pair_record(yoke_sweep, speaker), "body": pair_record(yoke_sweep, body)},
        "sample_step_mm": 2,
        "samples": [{"offset_z_mm": z, "speaker": pair_record(translated(yoke, V(0, 0, z)), speaker),
                     "body": pair_record(translated(yoke, V(0, 0, z)), body)} for z in range(0, 41, 2)]}
    pcba_sweep = cylinder(21.5, 31.6, z=20.5)
    for c, shape in components:
        swept = box(c["width_mm"], c["depth_mm"], c["height_mm"] + 30, 0, 0, c["z_min_mm"])
        swept = radial(swept, c["rotation_deg"])
        pcba_sweep = pcba_sweep.fuse(translated(swept, V(c["x_mm"], c["y_mm"], 0)))
    report["assembly_paths"]["pcba_onto_yoke"] = {
        "motion": "Axial translation +30 to 0 mm; board screws absent, lower yoke screws installed",
        "conservative_sweep_with_drills_filled": {
            name: pair_record(pcba_sweep, shape) for name, shape in
            [("body", body), ("yoke", yoke), ("speaker", speaker)] + hardware[:4]}}
    report["assembly_paths"]["forbidden_speaker_after_yoke"] = {
        "note": "Rear axial insertion with yoke installed is BLOCKED; do not use this sequence",
        "swept_collision": pair_record(speaker_sweep, yoke)}
    report["capture_displacement_probes"] = {
        "note": "Collision at finite rigid displacement demonstrates stops, not load-bearing approval or full six-DOF escape proof.",
        "radial_nominal_magnet_play_mm": 0.4, "axial_nominal_basket_gap_mm": 0.3,
        "up_0_5": pair_record(translated(speaker, V(0, 0, .5)), yoke),
        "down_0_5": pair_record(translated(speaker, V(0, 0, -.5)), body),
        **{f"lateral_{angle}_1mm": pair_record(translated(speaker, V(
            math.cos(math.radians(angle)), math.sin(math.radians(angle)), 0)), yoke)
           for angle in range(0, 360, 45)}}

    battery_group = doc.addObject("App::DocumentObjectGroup", "UNSELECTEDBatteryAlternatives")
    floor = box(38, 20, 1.5, 0, 0, 22.6)
    battery_group.addObject(feature("OptionalFloorSensitivity", floor, "UNATTACHED optional floor sensitivity, not a printed holder"))
    report["optional_floor_sensitivity"] = {**scene_record(floor), "dimensions_mm": [38, 20, 1.5],
                                           "z_mm": [22.6, 24.1], "pcba": pair_record(floor, pcba),
                                           "cross_face_reservations": {n: pair_record(floor, s) for n, s in keepout_shapes.items()},
                                           "attachment_and_retention": "NONE - not part of primary assembly"}
    for name, width, length, height, cylindrical in (
            ("compact_protected_16340_example", 16.8, 34, 16.8, True),
            ("fenix_arb_l16_700up_published_body", 16.8, 35.5, 16.8, True),
            ("compact_pouch_placeholder", 18, 28, 8, False),
            ("larger_pouch_placeholder", 20, 30, 8, False)):
        for bottom, lift_note in ((23.1, "1 mm above PCB; no cradle floor"),
                                  (24.6, "1.5 mm floor + 0.5 mm above floor; complete body lifted")):
            for clearance in (0, .5, 1.0):
                if cylindrical:
                    shape = Part.makeCylinder(width/2 + clearance, length + 2*clearance,
                                              V(-length/2-clearance, 0, bottom+width/2), V(1, 0, 0))
                else:
                    shape = box(length+2*clearance, width+2*clearance, height+2*clearance, 0, 0, bottom-clearance)
                record = {"name": name, "nominal_body_mm": {"length_X": length, "width_Y": width, "height_Z": height},
                          "body_bottom_z_mm": bottom, "clearance_mm": clearance, "lift_assumption": lift_note,
                          **scene_record(shape), "pcba": pair_record(shape, pcba),
                          "mechanical": {n: pair_record(shape, s) for n, s in
                                         (("body", body), ("yoke", yoke), ("speaker", speaker))},
                          "hardware": {n: pair_record(shape, s) for n, s in hardware},
                          "cross_face_reservations": {n: pair_record(shape, s) for n, s in keepout_shapes.items()},
                          "floor": pair_record(shape, floor) if bottom == 24.6 else None,
                          "retention_status": "NOT QUALIFIED: no side/end/top restraint or selected contacts/insulation"}
                report["battery_alternatives"].append(record)
                if clearance == 0:
                    battery_group.addObject(feature(name + ("_floor_lift" if bottom == 24.6 else "_bare"),
                                                    shape, name + f" full inert body at z{bottom:g}; alternative only"))
    artifacts = {}
    artifacts["integrated-cartridge-assembly.step"] = base.export_step_and_check(
        STUDY / "integrated-cartridge-assembly.step", assembly, Part)
    artifacts["populated-wing-pcba-proxy.step"] = base.export_step_and_check(
        STUDY / "populated-wing-pcba-proxy.step", [doc.getObject("PopulatedWingPCBA")], Part)
    for filename, shape in (("INERT-integrated-grille-seat-body.stl", body),
                            ("INERT-removable-capture-yoke.stl", yoke),
                            ("INERT-populated-wing-pcba-proxy.stl", pcba),
                            ("INERT-measured-speaker-body-screen.stl", speaker)):
        artifacts[filename] = export_stl(STUDY / filename, shape, Part, Mesh, MeshPart)
    native = STUDY / "integrated-cartridge-draft.FCStd"
    expected = {o.Name: base.shape_stats(o.Shape) for o in doc.Objects if hasattr(o, "Shape")}
    doc.recompute()
    doc.saveAs(str(native))
    App.closeDocument(doc.Name)
    reopened = App.openDocument(str(native))
    for name, stats in expected.items():
        obj = reopened.getObject(name)
        if obj is None or abs(base.shape_stats(obj.Shape)["volume_mm3"] - stats["volume_mm3"]) > 1e-6:
            raise RuntimeError("Native roundtrip lost " + name)
    for name in ("Parameters", "BuildSource", "FrozenHelperSource", "PlacementManifest"):
        if reopened.getObject(name) is None:
            raise RuntimeError("Native roundtrip lost source/parameters: " + name)
    App.closeDocument(reopened.Name)
    artifacts[native.name] = {"sha256": base.sha256(native), "reopened_shape_count": len(expected),
                              "source_snapshots_present": True, "parameters_sheet_present": True}
    (STUDY / "placement-snapshot.json").write_bytes(raw)
    base.write_json(STUDY / "parameters.json", DIMENSIONS)
    base.write_json(STUDY / "shell-parameters-snapshot.json", p)
    render_svg(STUDY / "integrated-cartridge-views.svg", manifest, report)
    for filename in ("placement-snapshot.json", "parameters.json", "shell-parameters-snapshot.json",
                     "integrated-cartridge-views.svg", "README.md"):
        artifacts[filename] = {"sha256": base.sha256(STUDY / filename)}
    report["artifacts"] = artifacts
    report["summary"] = {
        "speaker_component_conflicts": [r for r, c in report["components"].items() if c["speaker"]["intersection_mm3"] > EPS],
        "yoke_component_conflicts": [r for r, c in report["components"].items() if c["yoke"]["intersection_mm3"] > EPS],
        "minimum_component_speaker_distance_mm": min(c["speaker"]["distance_mm"] for c in report["components"].values()),
        "minimum_component_yoke_distance_mm": min(c["yoke"]["distance_mm"] for c in report["components"].values()),
        "cross_face_component_conflicts": [
            {"reservation": name, "reference": ref, **row}
            for name, keepout in report["cross_face_reservations"].items()
            for ref, row in keepout["components"].items() if row["intersection_mm3"] > EPS],
        "body_yoke_overlap_mm3": base.common_volume(body, yoke),
        "retained_cell_qualified": False, "shell_attachment_qualified": False}
    if base.sha256(args.placement) != digest:
        raise RuntimeError("Actual placement changed during export; rerun with new final input")
    review_status = {
        "schema_version": 1, "status": "draft_exports_regenerated",
        "final_export_on_hold": False, "completion_token": args.token,
        "placement_sha256": digest, "builder_sha256": report["input"]["builder_sha256"],
        "generated_utc": report["generated_utc"],
        "scope": "Two-piece original mechanical draft using the supplied manifest, including cross-face planning reservations.",
        "qualification": "NOT a retained-cell, attached-shell, electrical, structural-load or child-use approval."
    }
    review_status_bytes = (json.dumps(review_status, indent=2, allow_nan=False) + "\n").encode("utf-8")
    artifacts["review-status.json"] = {"sha256": hashlib.sha256(review_status_bytes).hexdigest()}
    base.write_json(STUDY / "fit-report.json", report)
    artifact_manifest = {"schema_version": 1, "input": report["input"], "artifacts": artifacts,
                         "fit_report_sha256": base.sha256(STUDY / "fit-report.json"),
                         "license_scope": report["license_scope"]}
    base.write_json(STUDY / "artifact-manifest.json", artifact_manifest)
    completion = {"token": args.token, "placement_sha256": digest, "output": str(STUDY),
                  "primary_printed_pieces": 2, "summary": report["summary"],
                  "artifact_manifest_sha256": base.sha256(STUDY / "artifact-manifest.json")}
    base.write_json(STUDY / "completion.json", completion)
    (STUDY / "review-status.json").write_bytes(review_status_bytes)
    base.write_json(args.completion_file, completion)


if __name__ == "__main__":
    options = arguments()
    build(options) if options.inside_freecad else launch(options)
