#!/usr/bin/env python3
"""Original MIT measured-shell T8 cartridge study; never writes electrical inputs.

Run with the exact protected-T8 manifest. FreeCADCmd uses project-local isolated
preferences, no GUI and a fresh completion marker. STEP precedes tessellation.
"""

from __future__ import annotations

import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import html
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

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "mechanical" / "studies" / "2026-09-11-t8-cartridge"
MEASUREMENTS = ROOT / "docs" / "measurements" / "2026-09-11-shell-speaker-inputs.json"
SPACING_FEEDBACK = ROOT / "docs" / "measurements" / "2026-09-11-spacing-feedback.json"
EPS = 1e-6
ANGLE = math.degrees(math.atan2(15.7, 10))
DEFAULTS = {
    "flange_diameter_mm": 75.5,
    "register_radial_gap_mm": 0.30,
    "register_depth_mm": 9.0,
    "register_wall_mm": 1.8,
    "shell_radial_wall_mm": 1.15,
    "grille_front_from_speaker_mm": -4.5,
    "magnet_aperture_diameter_mm": 22.1,
    "capture_bottom_from_speaker_mm": 12.3,
    "capture_top_from_speaker_mm": 14.8,
    "capture_outer_diameter_mm": 35.0,
    "lower_mount_radius_mm": 23.5,
    "nut_across_flats_mm": 4.0,
    "nut_height_mm": 1.6,
    "nut_pocket_across_flats_mm": 4.2,
    "screw_head_diameter_mm": 3.8,
    "plastic_proud_target_mm": 1.0,
    "cell_radial_clearance_mm": 0.10,
    "contact_clearance_mm": 0.10,
    "cell_default_center_z_mm": 31.88,
    "cell_provisional_diameter_mm": 16.4,
    "cell_provisional_length_mm": 34.0,
    "cover_split_above_board_back_mm": 9.9,
    "usb_slot_width_mm": 16.0,
    "usb_slot_top_z_mm": 24.0,
    "usb_bezel_width_mm": 15.4,
    "usb_bezel_top_z_mm": 23.7,
    "shell_attachment_z_mm": 3.0,
    "shell_attachment_clearance_mm": 2.4,
}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def digest_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def arguments():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--placement", required=True, type=Path)
    p.add_argument("--measurements", type=Path, default=MEASUREMENTS)
    p.add_argument("--parameters", type=Path)
    p.add_argument("--output", type=Path, default=STUDY)
    p.add_argument("--freecad-cmd", type=Path, default=Path(os.environ.get("LOCALAPPDATA", "")) /
                   "Programs" / "FreeCAD 1.1" / "bin" / "FreeCADCmd.exe")
    p.add_argument("--inside-freecad", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--token", help=argparse.SUPPRESS)
    p.add_argument("--expected-inputs", help=argparse.SUPPRESS)
    p.add_argument("--completion-file", type=Path, help=argparse.SUPPRESS)
    return p.parse_args()


def read_inputs(args):
    paths = {"placement": args.placement.resolve(), "measurements": args.measurements.resolve(),
             "spacing_feedback": SPACING_FEEDBACK,
             "builder": Path(__file__).resolve(), "helper": Path(base.__file__).resolve()}
    if args.parameters:
        paths["parameter_overrides"] = args.parameters.resolve()
    raw = {key: path.read_bytes() for key, path in paths.items()}
    hashes = {key: digest_bytes(value) for key, value in raw.items()}
    manifest = json.loads(raw["placement"].decode("utf-8-sig"))
    if manifest.get("battery_contact_interface"):
        interface_path = paths["placement"].parent / manifest["battery_contact_interface"]
        if interface_path.parent != paths["placement"].parent:
            raise ValueError("Contact interface must be local to supplied manifest")
        paths["contact_interface"] = interface_path
        raw["contact_interface"] = interface_path.read_bytes()
        hashes["contact_interface"] = digest_bytes(raw["contact_interface"])
        if hashes["contact_interface"] != manifest["battery_contact_interface_sha256"]:
            raise ValueError("Companion contact interface hash mismatch")
    measurements = json.loads(raw["measurements"].decode("utf-8-sig"))
    if manifest.get("schema_version") != 2 or manifest.get("units") != "mm":
        raise ValueError("Require explicit schema-2, mm protected-T8 placement")
    if "t8-protected-draft" not in str(paths["placement"]):
        raise ValueError("No wing/old-manifest fallback: require t8-protected-draft input")
    if manifest.get("interface_preview_only"):
        if (STUDY / "development") not in args.output.resolve().parents:
            raise ValueError("Interface-only preview cannot be published as the final study")
    else:
        if "contact_interface" not in paths:
            raise ValueError("Final T8 assembly requires the exact contact interface")
        for key, filename, metadata_key in (
                ("electrical_pcb", "handbell.kicad_pcb", "generated_pcb_sha256"),
                ("electrical_schematic", "handbell.kicad_sch", "schematic_sha256")):
            paths[key] = paths["placement"].parent / filename
            raw[key] = paths[key].read_bytes()
            hashes[key] = digest_bytes(raw[key])
            if hashes[key] != manifest[metadata_key]:
                raise ValueError("Actual electrical bytes disagree with manifest: " + filename)
    board = manifest["board"]
    for key, value in (("diameter_mm", 43), ("thickness_mm", 1.6)):
        if abs(board[key] - value) > 1e-8:
            raise ValueError("Shared interface changed: board." + key)
    front = base.finite_number(board["front_z_mm"], "board.front_z_mm")
    if board["front_face"] != "speaker":
        raise ValueError("Require speaker-facing F and handle-facing B")
    for key in ("generated_pcb_sha256", "schematic_sha256"):
        if len(manifest.get(key, "")) != 64:
            raise ValueError("Require exact electrical source hashes")
    refs = set()
    for c in manifest["components"]:
        if c["reference"] in refs:
            raise ValueError("Duplicate component")
        refs.add(c["reference"])
        for key in ("width_mm", "depth_mm", "height_mm"):
            base.finite_number(c[key], key, positive=True)
        for key in ("x_mm", "y_mm", "rotation_deg", "z_min_mm", "z_max_mm"):
            base.finite_number(c[key], key)
        if c["side"] not in ("F", "B") or abs(c["z_max_mm"] - c["z_min_mm"] - c["height_mm"]) > EPS:
            raise ValueError("Invalid face/z/height contract: " + c["reference"])
        expected_z = (front-c["height_mm"], front) if c["side"] == "F" else (front+1.6, front+1.6+c["height_mm"])
        if any(abs(c[key]-expected) > EPS for key, expected in zip(("z_min_mm", "z_max_mm"), expected_z)):
            raise ValueError("Component does not follow the supplied board axial interface: " + c["reference"])
    if not manifest["components"]:
        raise ValueError("Empty populated input is not a final assembly")
    holes = sorted(manifest["mounting_holes"], key=lambda h: h["reference"])
    if len(holes) != 2:
        raise ValueError("Need the two shared MH interfaces")
    for h, x, y in zip(holes, (10, -10), (15.7, -15.7)):
        for key, expected in (("x_mm", x), ("y_mm", y), ("drill_mm", 2.2)):
            if abs(h[key] - expected) > EPS:
                raise ValueError("Mount interface changed: " + key)
    dims = dict(DEFAULTS)
    if "parameter_overrides" in raw:
        overrides = json.loads(raw["parameter_overrides"].decode("utf-8-sig"))
        if set(overrides) - set(dims):
            raise ValueError("Unknown parameter overrides")
        for key, value in overrides.items():
            base.finite_number(value, key)
        dims.update(overrides)
    return paths, raw, hashes, manifest, measurements, dims


def launch(args):
    _, _, hashes, _, _, _ = read_inputs(args)
    out = args.output.resolve()
    if out != STUDY and STUDY not in out.parents:
        raise ValueError("Output must remain within the new T8 study")
    out.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    run = out / (".freecad-run-" + token)
    run.mkdir()
    marker = run / "complete.json"
    script = str(Path(__file__).resolve())
    argv = [script, "--inside-freecad", "--placement", str(args.placement.resolve()),
            "--measurements", str(args.measurements.resolve()), "--output", str(out),
            "--token", token, "--expected-inputs", json.dumps(hashes),
            "--completion-file", str(marker)]
    if args.parameters:
        argv.extend(("--parameters", str(args.parameters.resolve())))
    bootstrap = f"import runpy,sys\nsys.argv={argv!r}\nrunpy.run_path({script!r},run_name='__main__')\n"
    command = [str(args.freecad_cmd), "--user-cfg", str(run / "user.cfg"),
               "--system-cfg", str(run / "system.cfg")]
    write_json(out / "review-status.json", {"status": "BUILD_IN_PROGRESS_NOT_REVIEWABLE",
                                           "token": token, "input_hashes": hashes})
    try:
        result = subprocess.run(command, input=bootstrap, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, encoding="utf-8", errors="replace", timeout=1800)
        (out / "freecad-build.log").write_text(
            subprocess.list2cmdline(command) + "\n" + bootstrap + "\n" + result.stdout, encoding="utf-8")
        if result.returncode or not marker.is_file():
            print(result.stdout, file=sys.stderr)
            raise RuntimeError("FreeCAD did not finish this run; stale outputs are not success")
        completion = json.loads(marker.read_text(encoding="utf-8"))
        if completion["token"] != token or completion["input_hashes"] != hashes:
            raise RuntimeError("Completion-token/input mismatch")
        print(json.dumps(completion, indent=2))
    finally:
        shutil.rmtree(run)


def moved(shape, vector):
    s = shape.copy()
    s.translate(vector)
    return s


def pair(a, b):
    return {"intersection_mm3": max(0.0, a.common(b).Volume),
            "distance_mm": a.distToShape(b)[0]}


def add_display_metadata(native, styles):
    """Persist ordinary view-provider properties without starting a GUI."""
    providers = []
    for name, (color, transparency, visible) in styles.items():
        packed = 255 | sum(round(channel * 255) << shift for channel, shift in zip(color, (24, 16, 8)))
        providers.append(
            f'<ViewProvider name="{name}" expanded="0"><Properties Count="4">'
            f'<Property name="ShapeColor" type="App::PropertyColor"><PropertyColor value="{packed}"/></Property>'
            f'<Property name="LineColor" type="App::PropertyColor"><PropertyColor value="640034559"/></Property>'
            f'<Property name="Transparency" type="App::PropertyPercent"><Integer value="{transparency}"/></Property>'
            f'<Property name="Visibility" type="App::PropertyBool"><Bool value="{str(visible).lower()}"/></Property>'
            '</Properties></ViewProvider>')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<Document SchemaVersion="1"><ViewProviderData Count="' + str(len(providers)) + '">'
           + "".join(providers) + '</ViewProviderData></Document>')
    rewritten = native.with_suffix(".display.FCStd")
    with zipfile.ZipFile(native) as src, zipfile.ZipFile(rewritten, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            if info.filename != "GuiDocument.xml":
                dst.writestr(info, src.read(info.filename))
        dst.writestr("GuiDocument.xml", xml.encode("utf-8"))
    rewritten.replace(native)


def export_step(path, objects, Part):
    Part.export(objects, str(path))
    reimport = Part.Shape()
    reimport.read(str(path))
    compound = Part.makeCompound([obj.Shape for obj in objects])
    print(f"STEP {path.name}: before {compound.Volume:.9f}; after {reimport.Volume:.9f}; "
          f"delta {reimport.Volume-compound.Volume:.9f}", flush=True)
    if len(compound.Solids) != len(reimport.Solids):
        raise RuntimeError("STEP solid count changed")
    bound_error = max(abs(a-b) for key in ("min_mm", "max_mm")
                      for a, b in zip(base.bounds(compound)[key], base.bounds(reimport)[key]))
    if bound_error > .001:
        raise RuntimeError(f"STEP bounds changed by {bound_error}")
    text = path.read_text(encoding="ascii").replace(" ", "").replace("\n", "")
    if ".MILLI.,.METRE." not in text:
        raise RuntimeError("STEP lacks millimetre declaration")
    record = {"sha256": base.sha256(path), "units": "mm (STEP SI_UNIT)",
              "roundtrip": base.shape_stats(reimport), "maximum_bound_error_mm": bound_error,
              "volume_delta_mm3": reimport.Volume-compound.Volume}
    original = [s for obj in objects for s in obj.Shape.Solids]
    remaining = list(reimport.Solids)
    maximum = 0.0
    for shape in original:
        other = min(remaining, key=lambda s: abs(s.Volume - shape.Volume) +
                    (s.CenterOfMass - shape.CenterOfMass).Length)
        remaining.remove(other)
        difference = max(0, shape.cut(other).Volume) + max(0, other.cut(shape).Volume)
        maximum = max(maximum, difference)
        if difference > max(1e-5, shape.Volume * 1e-7):
            raise RuntimeError(f"STEP BRep symmetric difference {difference:.9f} on "
                               f"volume {shape.Volume:.9f}: {path.name}")
    record["maximum_per_solid_symmetric_difference_mm3"] = maximum
    record["brep_roundtrip_verified_not_only_bounds"] = True
    return record


def export_stl(path, shape, Part, Mesh, MeshPart):
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.045, AngularDeflection=0.12,
                                  Relative=False)
    mesh.write(str(path))
    restored = Mesh.Mesh(str(path))
    if not restored.isSolid() or restored.hasNonManifolds() or restored.hasSelfIntersections():
        raise RuntimeError("Nonmanifold/open/self-intersecting STL: " + path.name)
    if restored.countComponents() != len(shape.Solids):
        raise RuntimeError("STL connected-component count changed: " + path.name)
    brep = Part.Shape()
    brep.makeShapeFromMesh(restored.Topology, 0.001)
    solids = [Part.makeSolid(s) for s in brep.Shells]
    if any(not s.isValid() or not s.isClosed() for s in solids):
        raise RuntimeError("Invalid reconstructed STL BRep")
    error = abs(restored.Volume - shape.Volume) / shape.Volume
    if error > 0.012:
        raise RuntimeError("STL volume drift")
    return {"sha256": base.sha256(path), "units": "unitless; import mm at 100%",
            "connected_components": restored.countComponents(), "closed_manifold": True,
            "self_intersections": False, "reconstructed_brep_solid_count": len(solids),
            "relative_volume_error": error, "status": "INERT ONLY"}


def render_profiles(path, measurements, radius, dims, report):
    stack = report["stack_interface"]
    e = ['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="960" viewBox="0 0 1280 960">',
         '<rect width="1280" height="960" fill="#fafafa"/>',
         '<style>text{font-family:Arial,sans-serif;fill:#17202a}.small{font-size:14px}</style>',
         '<text x="25" y="35" font-size="24">Measured shell and coordinated mouthward cartridge</text>',
         '<text x="25" y="65" class="small">Original section illustration, mm. Mouth z=0; +z points toward the handle. Dimensions are not manufacturing tolerances.</text>']
    cx, top, scale = 345, 230, 8
    def rect(x1, x2, z1, z2, color):
        e.append(f'<rect x="{cx+x1*scale:.3f}" y="{top+z1*scale:.3f}" width="{(x2-x1)*scale:.3f}" '
                 f'height="{(z2-z1)*scale:.3f}" fill="{color}" fill-opacity=".45" stroke="{color}"/>')
    sf = stack["speaker_front_z_mm"]
    rect(-20, 20, sf, sf+12, "#808890")
    rect(-10.85, 10.85, sf+12, sf+19, "#47515c")
    rect(-21.5, 21.5, stack["pcb_front_z_mm"], stack["pcb_back_z_mm"], "#286bbb")
    rect(-17, 17, stack["cell_center_z_mm"]-8.2, stack["cell_center_z_mm"]+8.2, "#b064ad")
    for sign in (-1, 1):
        x1, x2 = sorted((sign*35, sign*dims["flange_diameter_mm"]/2))
        rect(x1, x2, sf, 0, "#3d9b70")
        x1, x2 = sorted((sign*18, sign*dims["flange_diameter_mm"]/2))
        rect(x1, x2, sf-3.7, sf, "#3d9b70")
        inside = " ".join(f"{cx+sign*radius(z)*scale:.2f},{top+z*scale:.2f}"
                          for z in [i*41.75/100 for i in range(101)])
        outside = " ".join(f"{cx+sign*(radius(z)+1.15)*scale:.2f},{top+z*scale:.2f}"
                           for z in [i*41.75/100 for i in range(101)])
        e += [f'<polyline points="{outside}" fill="none" stroke="#765a46" stroke-width="3"/>',
              f'<polyline points="{inside}" fill="none" stroke="#287c98" stroke-width="3"/>',
              f'<line x1="{cx+sign*(radius(41.75)+1.15)*scale}" y1="{top+41.75*scale}" '
              f'x2="{cx+sign*10.41*scale}" y2="{top+45.55*scale}" stroke="#765a46" stroke-dasharray="5"/>']
    rect(-19, 19, stack["grille_front_z_mm"], stack["grille_front_z_mm"]+1.8, "#3d9b70")
    for z, diameter in ((0, 71.68), (4.9, 69.75), (14.9, 50), (41.75, 36.12)):
        y = top+z*scale
        e.append(f'<line x1="{cx-diameter/2*scale}" y1="{y}" x2="{cx+diameter/2*scale}" y2="{y}" stroke="#999" stroke-dasharray="4"/>')
    e += [f'<line x1="{cx}" y1="110" x2="{cx}" y2="620" stroke="#777" stroke-dasharray="4"/>',
          '<text x="28" y="219" class="small">MOUTH z0</text>',
          '<text x="260" y="620" class="small">+z inward / toward handle</text>',
          '<text x="40" y="655" class="small">Green: external front body; grey: speaker bound</text>',
          '<text x="40" y="680" class="small">Blue: main PCB section; purple: full cell bound</text>',
          '<text x="40" y="705" class="small">Inside blue curve / radial-offset brown outside curve</text>']
    right = [
        "MEASURED / INFERRED SHELL STATIONS",
        "z0: ID71.68 measured; z4.9: ID69.75 measured",
        "z14.9: ID50 rough measured; 10mm travel after z4.9",
        "z41.75 approximate: ID36.12 INFERRED from OD38.42",
        "Owner assumes1.15 radial wall; not normal thickness",
        "Raw OD73.15 /73.15 /51.50 are preserved",
        "Working OD73.98 /72.05 /52.30 do not all match raw OD",
        "Concave interpolation and final closure are provisional",
        "",
        "CHOSEN WORKING STACK (not new measurements)",
        f"Entire internal stack moves {-sf:g}mm toward mouth",
        f"Speaker front z{sf:g}; grille front z{stack['grille_front_z_mm']:g}",
        f"PCB Fz{stack['pcb_front_z_mm']:g} / Bz{stack['pcb_back_z_mm']:g}",
        f"Cell axis z{stack['cell_center_z_mm']:g}; D16.4 x L34 remains provisional",
        f"Plastic target {dims['plastic_proud_target_mm']:g}; clearance {dims['contact_clearance_mm']:g}",
        f"Full guard-stock / shell gap {report['insulation_screens']['complete_rounded_contact_guard_stock']['cut_shell']['distance_mm']:.3f}mm",
        "Mouth register and shell-fastener locations stay fixed",
        "USB remains in a mouth-open -Y service slot",
        "Handle exterior H85.5; no usable interior assumed",
    ]
    for i, text in enumerate(right):
        e.append(f'<text x="715" y="{125+i*27}" class="small">{html.escape(text)}</text>')
    notes = [
        f"External flange D{dims['flange_diameter_mm']:g}; fixed register follows cavity to z{dims['register_depth_mm']:g} with assumed {dims['register_radial_gap_mm']:g} radial gap.",
        "Speaker D40/H19, rear basket D32 at speaker-relative z12, magnet D21.70/H7. Opening D22.1 is a0.4 diametral print allowance.",
        "Assemble outside bell: speaker -> removable yoke -> PCB/cradle -> inert cell/cover. Never push the D40 speaker through the installed yoke.",
        "Service: unplug USB, remove both shell screws, withdraw the whole cartridge toward mouth. The side slot is open to z0, not a trapping closed hole.",
        "Four structural prints, ordinary M2x6 screws and captive nuts. M2 means2mm thread; PCB drills2.2mm, not M3 or unqualified heat-set pilots.",
        "Shell screws follow the modeled lip normal; all drilling is a template proposal only. No fabrication or physical shell modification was performed.",
        "Nominal BRep fit is not loaded-contact, cell-wrapper/button, vent, torque, print-tolerance, insulation, temperature or child-use approval.",
    ]
    for i, text in enumerate(notes):
        e.append(f'<text x="25" y="{765+i*25}" class="small">{html.escape(text)}</text>')
    e.append("</svg>")
    path.write_text("\n".join(e)+"\n", encoding="utf-8")


def build(args):
    paths, raw, hashes, manifest, measured, d = read_inputs(args)
    if hashes != json.loads(args.expected_inputs):
        raise ValueError("Input changed after launch")
    import FreeCAD as App
    import Part
    import Mesh
    import MeshPart
    V = App.Vector
    front = manifest["board"]["front_z_mm"]
    back = front+manifest["board"]["thickness_mm"]
    stack_delta = front-20.5
    usb_delta_y = manifest.get("usb_interface", {}).get("body_mouth_center_common_xy_mm", [0, -25.15])[1]+25.15
    if stack_delta > EPS:
        raise ValueError("This revision supports mouthward stack shifts, not an unreviewed deeper stack")
    def sz(z):
        return z+stack_delta
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    def progress(stage):
        write_json(out / ".build-progress.json", {"stage": stage, "utc": datetime.now(timezone.utc).isoformat()})
        print(stage, flush=True)
    progress("Constructing original shell/body/yoke")
    App.ParamGet("User parameter:BaseApp/Preferences/Document").SetInt("CountBackupFiles", 0)
    doc = App.newDocument("MeasuredT8Cartridge")
    doc.Label = "T8 measured-shell cartridge — INERT REVIEW, NOT ROUTING APPROVAL"
    doc.Comment = "Original mechanics MIT; exact adapted electronics context CC BY-SA 3.0. Unqualified cell/fit."
    styles, objects, groups = {}, {}, {}

    def group(name):
        if name not in groups:
            groups[name] = doc.addObject("App::DocumentObjectGroup", name)
        return groups[name]

    def feature(name, shape, color=(.6, .6, .6), transparency=0, visible=True, section="Assembly"):
        base.shape_stats(shape)
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        group(section).addObject(obj)
        styles[name] = (color, transparency, visible)
        objects[name] = obj
        return obj

    def box(w, dep, h, x=0, y=0, z=0):
        return base.box_at(w, dep, h, x, y, z, Part, V)

    def cyl(r, h, x=0, y=0, z=0):
        return Part.makeCylinder(r, h, V(x, y, z))

    def ring(ro, ri, h, z):
        return cyl(ro, h, z=z).cut(cyl(ri, h, z=z))

    def rotate(s, a):
        s = s.copy()
        s.rotate(V(), V(0, 0, 1), a)
        return s

    def fuse(parts, single=True):
        s = parts[0].multiFuse(parts[1:]).removeSplitter() if len(parts) > 1 else parts[0]
        base.shape_stats(s)
        if single and len(s.Solids) != 1:
            raise RuntimeError(f"Structural union is disconnected ({len(s.Solids)} solids)")
        return s

    def hexagon(af, h, x=0, y=0, z=0):
        r = af / math.sqrt(3)
        vertices = [V(x+r*math.cos(math.radians(a)), y+r*math.sin(math.radians(a)), z)
                    for a in range(0, 360, 60)]
        return Part.Face(Part.makePolygon(vertices+[vertices[0]])).extrude(V(0, 0, h))

    def nut(x, y, z):
        return hexagon(d["nut_across_flats_mm"], d["nut_height_mm"], x, y, z).cut(cyl(1, 1.6, x, y, z))

    def screw(x, y, underhead, length):
        return cyl(1, length, x, y, underhead-length).fuse(
            cyl(d["screw_head_diameter_mm"]/2, 2, x, y, underhead)).removeSplitter()

    stations = measured["working_cad_profile"]["inside_stations"]
    expected_stations = [(0, 71.68), (4.9, 69.75), (14.9, 50), (41.75, 36.12)]
    if [(s["z_mm"], s["diameter_mm"]) for s in stations] != expected_stations:
        raise ValueError("Measurement stations changed; review the profile construction")
    r0, r1, r2, r3 = (s["diameter_mm"]/2 for s in stations)
    slope0, slope1 = (r1-r0)/4.9, (r3-r2)/(41.75-14.9)

    def radius(z):
        if z <= 4.9:
            return r0 + slope0*z
        if z <= 14.9:
            t = (z-4.9)/10
            return ((2*t**3-3*t*t+1)*r1 + (t**3-2*t*t+t)*10*slope0 +
                    (-2*t**3+3*t*t)*r2 + (t**3-t*t)*10*slope1)
        return r2 + slope1*(z-14.9)

    def profile(offset=0, top=41.75):
        curve = Part.BezierCurve()
        curve.setPoles([V(r1+offset, 0, 4.9), V(r1+offset+slope0*10/3, 0, 4.9+10/3),
                        V(r2+offset-slope1*10/3, 0, 14.9-10/3), V(r2+offset, 0, 14.9)])
        edges = [Part.makeLine(V(0, 0, 0), V(r0+offset, 0, 0)),
                 Part.makeLine(V(r0+offset, 0, 0), V(r1+offset, 0, 4.9)), curve.toShape(),
                 Part.makeLine(V(r2+offset, 0, 14.9), V(r3+offset, 0, 41.75))]
        if top > 41.75:
            edges.append(Part.makeLine(V(r3+offset, 0, 41.75), V(9.26+offset, 0, top)))
            end_r = 9.26+offset
        else:
            end_r = r3+offset
        edges += [Part.makeLine(V(end_r, 0, top), V(0, 0, top)),
                  Part.makeLine(V(0, 0, top), V(0, 0, 0))]
        return Part.Face(Part.Wire(edges)).revolve(V(), V(0, 0, 1), 360)

    cavity = profile(0, 44.4)
    shell_uncut = profile(d["shell_radial_wall_mm"], 45.55).cut(cavity)
    shell_slot = box(d["usb_slot_width_mm"], 70, sz(d["usb_slot_top_z_mm"])+.1, 0, -35, -.1)
    shell = shell_uncut.cut(shell_slot)
    shell_hole_tools = []
    shell_joint_axes = []
    for sign in (-1, 1):
        axis = V(sign, 0, -slope0)
        axis.normalize()
        head_plane = V(sign*(radius(d["shell_attachment_z_mm"])+d["shell_radial_wall_mm"]), 0,
                       d["shell_attachment_z_mm"])
        shell_joint_axes.append((sign, axis, head_plane))
        tool = Part.makeCylinder(d["shell_attachment_clearance_mm"]/2, 15,
                                 head_plane-axis*10, axis)
        shell_hole_tools.append(tool)
        shell = shell.cut(tool)
    feature("WorkingShellWithProposedOpenSlot", shell, (.67, .72, .79), 80, section="ShellContext")
    feature("UncutWorkingShellReference", shell_uncut, (.8, .4, .4), 85, False, "ConstructionReferences")
    feature("WorkingCavityReference", cavity, (.7, .85, .9), 95, False, "ConstructionReferences")
    handle = Part.makeCone(18.52/2, 15.01/2, 85.5, V(0, 0, 45.55))
    feature("HandleExteriorOnly", handle, (.72, .49, .27), 65, section="ShellContext")
    allowed = cavity.fuse(cyl(100, 100, z=-100)).fuse(shell_slot)

    grille_z = sz(d["grille_front_from_speaker_mm"])
    grille = cyl(19, 1.8, z=grille_z)
    for x in range(-16, 17, 4):
        grille = grille.cut(box(2.8, 36, 2.2, x, 0, grille_z-.2).common(cyl(17, 2.2, z=grille_z-.2)))
    register_outer = profile(-d["register_radial_gap_mm"]).common(cyl(50, d["register_depth_mm"]))
    register_inner = profile(-d["register_radial_gap_mm"]-d["register_wall_mm"])
    register = register_outer.cut(register_inner)
    body_parts = [ring(d["flange_diameter_mm"]/2, 18, 3.7, sz(-3.7)), grille,
                  ring(20.2, 18, 1.2, sz(-1.2)), register, ring(r0-.3, r0-2.1, 1.2, -1.2)]
    if stack_delta < -EPS:
        body_parts.append(ring(d["flange_diameter_mm"]/2, 35, -stack_delta, stack_delta))
    lower_mounts = []
    for angle in (ANGLE, ANGLE+180):
        x, y = d["lower_mount_radius_mm"]*math.cos(math.radians(angle)), d["lower_mount_radius_mm"]*math.sin(math.radians(angle))
        lower_mounts.append((x, y))
        body_parts.append(rotate(box(5.4, 7.4, 9.2, d["lower_mount_radius_mm"], 0, sz(-1.2)), angle))

    # The bezel is integral with the cartridge and slides in a mouth-open shell slot.
    bezel_outside = box(d["usb_bezel_width_mm"], 6.7, d["usb_bezel_top_z_mm"]+1, 0, -23.8+usb_delta_y, sz(-1))
    bezel_inside = box(12.6, 8, 26, 0, -23.8+usb_delta_y, sz(.5))
    bezel = bezel_outside.cut(bezel_inside)
    # Continuous ribs join the narrower port structure to the external front plate.
    body_parts.append(bezel)
    body_parts.append(box(14, 4.7, 1.25, 0, -22.8+usb_delta_y, sz(15.55)))
    pad_region = profile().fuse(cyl(r0, 1.2, z=-1.2))
    for sign in (-1, 1):
        attachment = box(7, 8, 7, sign*32.5, 0, -1).common(pad_region)
        body_parts.append(attachment)
    body = fuse(body_parts)
    body = body.cut(box(16, 3, 4.0, 0, -20.0+usb_delta_y, sz(20.3)))
    for x, y in lower_mounts:
        body = body.cut(hexagon(d["nut_pocket_across_flats_mm"], 1.9, x, y, sz(4.65)))
        body = body.cut(cyl(1.1, 5.2, x, y, sz(3.0)))
        a = math.degrees(math.atan2(y, x))
        body = body.cut(rotate(box(5, 4.7, 1.9, d["lower_mount_radius_mm"]+2, 0, sz(4.65)), a))
    shell_hardware = []
    for sign, axis, head_plane in shell_joint_axes:
        # Nylon hardware intentionally cannot electrically join bell and board.
        shank = Part.makeCylinder(1, 6, head_plane-axis*6, axis)
        head = Part.makeCylinder(1.9, 2, head_plane, axis)
        shell_hardware.append((f"InsulatingShellM2x6_{sign+2}", shank.fuse(head)))
        hole = Part.makeCylinder(1.1, 8, head_plane-axis*7, axis)
        body = body.cut(hole)
        n = nut(0, 0, 0)
        rotation = App.Rotation(V(0, 0, 1), axis)
        n.Placement = App.Placement(head_plane-axis*5.45, rotation)
        shell_hardware.append((f"InsulatingShellM2Nut_{sign+2}", n))
        pocket = hexagon(4.2, 5.15)
        pocket.Placement = App.Placement(head_plane-axis*9, rotation)
        body = body.cut(pocket)

    upper = [ring(d["capture_outer_diameter_mm"]/2, d["magnet_aperture_diameter_mm"]/2,
                  d["capture_top_from_speaker_mm"]-d["capture_bottom_from_speaker_mm"], d["capture_bottom_from_speaker_mm"])]
    for angle in (ANGLE, ANGLE+180):
        upper += [rotate(box(5.4, 7.4, 2.8, d["lower_mount_radius_mm"], 0, 8.0), angle),
                  rotate(box(2.9, 6.2, 4, 21.75, 0, 10.8), angle),
                  rotate(box(8, 6.2, 2.5, 19.3, 0, 12.3), angle)]
    for h in manifest["mounting_holes"]:
        upper.append(cyl(3.2, 6.1, h["x_mm"], h["y_mm"], 14.4))
    for x, y in lower_mounts:
        upper.append(cyl(1.9, 2, x, y, 9.4).makeOffsetShape(1.4, .001, fill=False, join=0))
    yoke = fuse(upper)
    metal_hardware = []
    for index, (x, y) in enumerate(lower_mounts, 1):
        yoke = yoke.cut(cyl(1.1, 7, x, y, 7.9))
        yoke = yoke.cut(cyl(2.15, 6, x, y, 9.4))
        metal_hardware += [(f"YokeM2x6_{index}", screw(x, y, 9.4, 6)),
                           (f"BodyCaptiveM2Nut_{index}", nut(x, y, 4.8))]
    for h in manifest["mounting_holes"]:
        x, y, ref = h["x_mm"], h["y_mm"], h["reference"]
        yoke = yoke.cut(hexagon(4.2, 1.9, x, y, 17.2)).cut(cyl(1.1, 4.8, x, y, 15.8))
        a, r = math.degrees(math.atan2(y, x)), math.hypot(x, y)
        yoke = yoke.cut(rotate(box(4, 4.7, 1.9, r+2, 0, 17.2), a))
        metal_hardware += [(ref+"M2x6", screw(x, y, 22.9, 6)),
                           (ref+"CaptiveM2Nut", nut(x, y, 17.35))]
    yoke = moved(yoke, V(0, 0, stack_delta))
    metal_hardware = [(name, moved(shape, V(0, 0, stack_delta))) for name, shape in metal_hardware]
    body, yoke = body.removeSplitter(), yoke.removeSplitter()
    feature("FrontBodyGrilleRegisterUSBBezel", body, (.33, .70, .55))
    feature("RemovableSpeakerCaptureYoke", yoke, (.91, .63, .27))
    speaker = cyl(20, 12, z=stack_delta).fuse(cyl(10.85, 7, z=sz(12))).removeSplitter()
    feature("SpeakerConditionalBodyScreen", speaker, (.42, .44, .48))
    illustrative = Part.makeCone(20, 16, 12, V(0, 0, stack_delta)).fuse(cyl(10.85, 7, z=sz(12))).removeSplitter()
    feature("SpeakerIllustrativeBasketOnly", illustrative, (.5, .5, .5), 0, False, "ConstructionReferences")

    if manifest["board"].get("outline_common_xy_mm"):
        points = [V(x, y, 20.5) for x, y in manifest["board"]["outline_common_xy_mm"]]
        pcb = Part.Face(Part.makePolygon(points+[points[0]])).extrude(V(0, 0, 1.6))
    else:
        pcb = cyl(21.5, 1.6, z=20.5)
    for h in manifest["mounting_holes"]:
        pcb = pcb.cut(cyl(h["drill_mm"]/2, 2, h["x_mm"], h["y_mm"], 20.3))
    pcb = moved(pcb, V(0, 0, stack_delta))
    feature("PCBSubstrateExactInterface", pcb, (.15, .38, .66))
    progress("Constructing exact supplied component/contact geometry")
    components, contact_records, contact_segments = [], [], {}
    for c in manifest["components"]:
        s = box(c["width_mm"], c["depth_mm"], c["height_mm"], z=c["z_min_mm"])
        s = moved(rotate(s, c["rotation_deg"]), V(c["x_mm"], c["y_mm"], 0))
        components.append((c, s))
        feature("Component_"+c["reference"], s, (.20, .24, .30) if c["side"] == "F" else (.55, .35, .22),
                section="FittedComponentProxies")

    # Detailed terminal primitives replace only their explicit manifest body boxes.
    # The electrical agent supplies this separate geometry contract, never inferred
    # from a tall rectangular battery-contact envelope.
    contract = manifest.get("mechanical_contract", {})
    contact_interface = json.loads(raw["contact_interface"].decode("utf-8-sig")) if "contact_interface" in raw else None
    if contact_interface:
        if abs(contact_interface["pcb_z_mm"]-back) > EPS:
            raise ValueError("Contact interface B plane differs from manifest board B")
        nominal = contact_interface["cell_nominal"]
        contract = {"battery": {"center_x_mm": nominal["center_mm"][0],
                                "center_y_mm": nominal["center_mm"][1],
                                "center_z_mm": nominal["center_mm"][2],
                                "diameter_mm": nominal["diameter_mm"],
                                "length_mm": nominal["total_length_mm"]},
                    "contact_interface_exact": contact_interface}
    battery_contract = contract.get("battery", {})
    cell_z = battery_contract.get("center_z_mm", d["cell_default_center_z_mm"])
    cell_x = battery_contract.get("center_x_mm", 0)
    cell_y = battery_contract.get("center_y_mm", 0)
    cell_length = battery_contract.get("length_mm", d["cell_provisional_length_mm"])
    cell_diam = battery_contract.get("diameter_mm", d["cell_provisional_diameter_mm"])
    cell = Part.makeCylinder(cell_diam/2, cell_length, V(cell_x-cell_length/2, cell_y, cell_z), V(1, 0, 0))
    feature("T8FullUnclippedCellCanEnvelope", cell, (.75, .35, .68))
    if contact_interface:
        cp = contact_interface["right_contact_original_primitives"]
        if "cell-facing surface" not in cp.get("spring_surface", "") or "toward +X" not in cp["spring_surface"]:
            raise ValueError("Require explicit cell-facing spring surface and outward +X thickness contract")
        segments = []
        for part in cp["base_tabs"]+[cp["under_cell_base"]]:
            segments.append(box(part["x_max"]-part["x_min"], part["y_width"], part["thickness"],
                                (part["x_max"]+part["x_min"])/2, 0, part["z_min"]))
        polyline = cp["spring_xz_polyline"]
        for (x1, z1), (x2, z2) in zip(polyline, polyline[1:]):
            thickness = cp["spring_thickness"]
            points = [V(x1, -cp["spring_y_width"]/2, z1),
                      V(x2, -cp["spring_y_width"]/2, z2),
                      V(x2+thickness, -cp["spring_y_width"]/2, z2),
                      V(x1+thickness, -cp["spring_y_width"]/2, z1)]
            segment = Part.Face(Part.makePolygon(points+[points[0]])).extrude(V(0, cp["spring_y_width"], 0))
            bb = segment.BoundBox
            expected = (min(x1, x2), max(x1, x2)+thickness, min(z1, z2), max(z1, z2))
            if any(abs(a-b) > EPS for a, b in zip((bb.XMin, bb.XMax, bb.ZMin, bb.ZMax), expected)):
                raise RuntimeError("Spring segment changed the supplied cell-facing polyline or outward thickness")
            segments.append(segment)
        ears = cp["ears"]
        for start, end in ears["angle_degrees"]:
            r, thickness = ears["inner_radius"], ears["thickness"]
            x, zc = ears["x_min"], ears["axis_center_yz"][1]
            def point(rad, angle):
                a = math.radians(angle)
                return V(x, rad*math.cos(a), zc+rad*math.sin(a))
            edges = [Part.Arc(point(r, start), point(r, (start+end)/2), point(r, end)).toShape(),
                     Part.makeLine(point(r, end), point(r+thickness, end)),
                     Part.Arc(point(r+thickness, end), point(r+thickness, (start+end)/2), point(r+thickness, start)).toShape(),
                     Part.makeLine(point(r+thickness, start), point(r, start))]
            segments.append(Part.Face(Part.Wire(edges)).extrude(V(ears["axial_length"], 0, 0)))
        right_contact = fuse(segments, False)
        for record in contact_interface["contacts"]:
            shape = rotate(right_contact, record["rotation_deg"])
            if shape.common(cell).Volume > EPS:
                raise RuntimeError("Cell-facing spring contract must touch, not penetrate, the nominal cell")
            contact_records.append((record, shape))
            contact_segments[record["reference"]] = [rotate(s, record["rotation_deg"]) for s in segments]
            feature("ContactMetal_"+record["reference"], shape, (.8, .79, .72), section="ActualContactGeometry")
            styles["Component_"+record["reference"]] = ((.8, .2, .2), 80, False)
    for record in contract.get("contacts", []):
        shapes = []
        for primitive in record["primitives"]:
            if primitive["type"] == "box":
                lo, size = primitive["min_mm"], primitive["size_mm"]
                shapes.append(Part.makeBox(*size, V(*lo)))
            elif primitive["type"] == "cylinder":
                shapes.append(Part.makeCylinder(primitive["radius_mm"], primitive["length_mm"],
                                               V(*primitive["base_mm"]), V(*primitive["axis"])))
            else:
                raise ValueError("Unsupported explicit contact primitive")
        shape = fuse(shapes, single=False)
        contact_records.append((record, shape))
        contact_segments[record["reference"]] = shapes
        feature("ContactMetal_"+record["reference"], shape, (.8, .79, .72), section="ActualContactGeometry")
        obj = objects.get("Component_"+record["reference"])
        if obj:
            styles[obj.Name] = ((.8, .2, .2), 80, False)
    contact_refs = {c["reference"] for c, _ in contact_records}
    physical_components = [(c, s) for c, s in components if c["reference"] not in contact_refs]

    # A rounded all-direction offset is less pessimistic than a rectangular box,
    # but is never clipped to the cavity to conceal insulation failures.
    clearance = d["cell_radial_clearance_mm"]
    contact_clearance = d["contact_clearance_mm"]
    proud = d["plastic_proud_target_mm"]
    cell_void = cell.makeOffsetShape(clearance, .001, fill=False, join=0)
    cell_outer = cell.makeOffsetShape(clearance+proud, .001, fill=False, join=0)
    guard = cell_outer.cut(cell_void)
    progress("Constructing independent cradle and cover")
    contact_outers = []
    contact_voids = []
    guard_wall_witnesses = []
    for record, shape in contact_records:
        parts = contact_segments[record["reference"]]
        # Conservative guard stock uses simple solids; metal remains the supplied
        # thin primitive geometry. Exact large offsets of bent sheet intersections
        # are not robust in OCC and are not a printable design authority.
        stock, pockets = [], []
        for index, s in enumerate(parts):
            bb = s.BoundBox
            a = proud+contact_clearance
            if contact_interface and index >= len(parts)-2:
                stock.append(Part.makeCylinder(cell_diam/2+.3+a, bb.XLength+2*a,
                                                V(bb.XMin-a, 0, cell_z), V(1, 0, 0)))
                ears = contact_interface["right_contact_original_primitives"]["ears"]
                start, end = ears["angle_degrees"][index-(len(parts)-2)]
                padding = math.degrees(math.asin(contact_clearance/(ears["inner_radius"]-contact_clearance)))
                start, end = start-padding, end+padding
                inner, outer = ears["inner_radius"]-contact_clearance, ears["inner_radius"]+ears["thickness"]+contact_clearance
                def pocket_point(radius_value, angle_value):
                    radians = math.radians(angle_value)
                    return V(ears["x_min"]-contact_clearance, radius_value*math.cos(radians),
                             cell_z+radius_value*math.sin(radians))
                edges = [
                    Part.Arc(pocket_point(inner, start), pocket_point(inner, (start+end)/2), pocket_point(inner, end)).toShape(),
                    Part.makeLine(pocket_point(inner, end), pocket_point(outer, end)),
                    Part.Arc(pocket_point(outer, end), pocket_point(outer, (start+end)/2), pocket_point(outer, start)).toShape(),
                    Part.makeLine(pocket_point(outer, start), pocket_point(inner, start))]
                pocket = Part.Face(Part.Wire(edges)).extrude(V(ears["axial_length"]+2*contact_clearance, 0, 0))
                pockets.append(rotate(pocket, record["rotation_deg"]))
            else:
                seed = box(bb.XLength, bb.YLength, bb.ZLength, (bb.XMin+bb.XMax)/2,
                           (bb.YMin+bb.YMax)/2, bb.ZMin)
                stock.append(seed.makeOffsetShape(a, .001, fill=False, join=0))
                pockets.append(seed.makeOffsetShape(contact_clearance, .001, fill=False, join=0))
            guard_wall_witnesses.append((record["reference"]+"_"+str(index), stock[-1], pockets[-1]))
        outer = fuse(stock, False)
        void = fuse(pockets, False)
        contact_voids.append(void)
        contact_outers.append(outer)
    if contact_outers:
        center_stock = Part.makeCylinder(cell_diam/2+clearance+proud, cell_length+2*(clearance+proud),
                                          V(-cell_length/2-clearance-proud, 0, cell_z), V(1, 0, 0))
        guard_outer = fuse([center_stock]+contact_outers, single=False)
        simple_cell_void = Part.makeCylinder(cell_diam/2+clearance, cell_length+2*clearance,
                                             V(-cell_length/2-clearance, 0, cell_z), V(1, 0, 0))
        guard_wall_witnesses.append(("cell", center_stock, simple_cell_void))
        guard_void = fuse([simple_cell_void]+contact_voids, single=False)
        guard = guard_outer.cut(guard_void).removeSplitter()
        base.shape_stats(guard)
        guard = guard.cut(box(100, 100, 100, z=back-100)).removeSplitter()
    split = back+d["cover_split_above_board_back_mm"]
    lower_half = box(100, 100, 100, z=split-100)
    cradle = guard.common(lower_half)
    cover = guard.cut(lower_half)
    cradle_parts = [cradle]
    for h in manifest["mounting_holes"]:
        x, y = h["x_mm"], h["y_mm"]
        cradle_parts.append(cyl(3.2, 4.05, x, y, back))
        a, r = math.degrees(math.atan2(y, x)), math.hypot(x, y)
        cradle_parts.append(rotate(box(4.0, 4.5, 3.5, r-1.3, 0, sz(24.6)), a))
        sign = 1 if y > 0 else -1
        cradle_parts.append(box(6.4, 9.0, 1.5, x, sign*12.0, sz(26.6)))
    cradle = fuse(cradle_parts, single=False)
    for h in manifest["mounting_holes"]:
        cradle = cradle.cut(cyl(1.1, 8, h["x_mm"], h["y_mm"], sz(21)))
        cradle = cradle.cut(cyl(2.15, 10, h["x_mm"], h["y_mm"], sz(22.9)))

    # End-positioned cover ears avoid battery radial motion and PCB screw heads.
    cover_hardware = []
    for sign in (-1, 1):
        x, y = sign*10.0, -sign*10.9
        lower_ear = box(6.4, 4.8, 4.6, x, y, split-4.6)
        upper_ear = box(6.4, 4.8, 2.0, x, y, split)
        cradle = cradle.fuse(lower_ear)
        cover = cover.fuse(upper_ear)
        cover = cover.fuse(cyl(3.3, 5.4, x, y, split))
        cradle = cradle.cut(hexagon(4.2, 1.9, x, y, split-3.35))
        cradle = cradle.cut(box(6, 4.7, 1.9, x+sign*3, y, split-3.35))
        cradle = cradle.cut(cyl(1.1, 4.4, x, y, split-4.3))
        cover = cover.cut(cyl(1.1, 2.2, x, y, split-.1))
        cover = cover.cut(cyl(2.15, 20, x, y, split+2))
        cover_hardware += [(f"CoverM2x6_{sign+2}", screw(x, y, split+2, 6)),
                           (f"CoverCaptiveM2Nut_{sign+2}", nut(x, y, split-3.2))]
    if contact_records:
        cradle = cradle.cut(guard_void)
        cover = cover.cut(guard_void)
    else:
        cradle = cradle.cut(cell_void)
        cover = cover.cut(cell_void)
    cradle, cover = cradle.removeSplitter(), cover.removeSplitter()
    feature("LoadBearingInsulatingBatteryCradle", cradle, (.29, .65, .78))
    feature("RemovableBatteryCaptureCover", cover, (.37, .77, .87), 20)
    metal_hardware += cover_hardware
    for name, shape in metal_hardware:
        feature(name, shape, (.77, .78, .82), section="M2MetalHardware")
    for name, shape in shell_hardware:
        feature(name, shape, (.94, .91, .78), section="InsulatingShellHardware")
    feature("CellGuardOuterEnvelopeReference", cell_outer, (.8, .2, .2), 80, False, "ConstructionReferences")
    physical = {"body": body, "yoke": yoke, "cradle": cradle, "cover": cover,
                "speaker": speaker, "pcb": pcb, "cell": cell}
    physical.update({"component_"+c["reference"]: s for c, s in physical_components})
    physical.update({"contact_"+c["reference"]: s for c, s in contact_records})
    physical.update(dict(metal_hardware+shell_hardware))

    def scene(s):
        return {**base.shape_stats(s), "uncut_shell": pair(s, shell_uncut), "cut_shell": pair(s, shell),
                "outside_working_cavity_excluding_port_and_open_mouth_mm3": max(0, s.cut(allowed).Volume)}

    progress("Exact BRep shell/physical-part checks")
    report = {
        "schema_version": 1, "units": "mm", "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "INERT PARAMETRIC ASSEMBLY REVIEW — NOT FABRICATION, LIVE-CELL OR ROUTING APPROVAL",
        "input": {"paths": {k: str(v) for k, v in paths.items()}, "sha256": hashes,
                  "electrical_pcb_sha256": manifest["generated_pcb_sha256"],
                  "electrical_schematic_sha256": manifest["schematic_sha256"]},
        "toolchain": {"freecad": App.Version(), "opencascade": Part.OCC_VERSION, "python": sys.version},
        "dimensions": d, "exact_mechanical_contract_consumed": contract,
        "stack_interface": {
            "rigid_stack_mouthward_shift_mm": -stack_delta,
            "speaker_front_z_mm": stack_delta, "pcb_front_z_mm": front, "pcb_back_z_mm": back,
            "cell_center_z_mm": cell_z, "grille_front_z_mm": grille_z,
            "capture_ring_z_mm": [sz(d["capture_bottom_from_speaker_mm"]), sz(d["capture_top_from_speaker_mm"])],
            "cover_split_z_mm": split, "usb_delta_y_from_fixed_stack_mm": usb_delta_y,
            "shell_register_and_shell_fasteners_translate": False,
            "component_and_contact_z_basis": "Exact new electrical manifest/interface, not a hidden geometry override",
            "relative_speaker_yoke_pcb_cell_gaps_preserved": True,
            "external_front_skirt_height_mm": -stack_delta,
            "body_bearing": "Flange/skirt ends at mouth z0; two local conformal carrier pads bear against the modeled inner shell.",
            "shell_screw_axes": [{"sign": sign, "axis": list(axis), "head_underface_center_mm": list(head_plane)}
                                  for sign, axis, head_plane in shell_joint_axes],
            "shell_screw_pitch_from_radial_deg": math.degrees(math.atan(-slope0))},
        "shell_profile": {"inside_stations": stations, "wall_rule": "1.15 mm RADIAL offset, not normal thickness",
                          "curve": "Cubic Hermite/Bezier z4.9..14.9, tangent to adjacent linear sections",
                          "raw_measurements_preserved": True,
                          "final_closure": "Provisional cone to D18.52 at z44.4 cavity; outside ends z45.55"},
        "primary_printed_piece_count": 4, "structural_parts": {},
        "fastener_stack": {
            "steel_screws": "Six M2x6 ISO4762-style cap screws; no hidden insert pilot",
            "steel_nuts": "Six ordinary M2 DIN934-style hex nuts, AF4/H1.6",
            "shell_hardware": "Two nylon M2x6 screws and two nylon M2 nuts; dimension/strength screen",
            "shell_joint": {"nut_normal_distance_inside_head_mm": [3.85, 5.45],
                            "nominal_thread_engagement_mm": 1.6,
                            "screw_tip_beyond_nut_mm": .55,
                            "nut_loading": "From the open inner end of a hexagonal socket along the screw axis, not vertically through a blocked chute."},
            "lower_joint": {"underhead_z_mm": sz(9.4), "tip_z_mm": sz(3.4), "nut_z_mm": [sz(4.8), sz(6.4)],
                            "pocket_z_mm": [sz(4.65), sz(6.55)], "roof_mm": 1.45,
                            "head_guard": "Rounded1.4mm outer setback, D4.3 tool/head well; at least1.25 target outside nominal D3.8 head",
                            "full_nominal_nut_engagement_mm": 1.6, "blind_tip_gap_mm": .4},
            "pcb_cradle_joint": {"underhead_z_mm": sz(22.9), "tip_z_mm": sz(16.9),
                                 "nut_z_mm": [sz(17.35), sz(18.95)], "pocket_z_mm": [sz(17.2), sz(19.1)],
                                 "roof_mm": 1.4, "cradle_clamping_floor_mm": .8,
                                 "head_top_z_mm": sz(24.9), "cup_top_z_mm": sz(26.15),
                                 "head_recess_below_cup_mm": 1.25,
                                 "head_radial_setback_from_cup_outer_mm": 1.3,
                                 "full_nominal_nut_engagement_mm": 1.6, "blind_tip_gap_mm": 1.1},
            "cover_joint": {"underhead_z_mm": split+2, "tip_z_mm": split-4,
                            "nut_z_mm": [split-3.2, split-1.6], "roof_mm": 1.45,
                            "head_top_z_mm": split+4, "cup_top_z_mm": split+5.4,
                            "nominal_axial_and_radial_head_setback_mm": 1.4,
                            "full_nominal_nut_engagement_mm": 1.6, "blind_tip_gap_mm": .3},
            "nut_loading": "Horizontal side insertion below a real plastic roof. Top-loading into an uncovered hex pocket would NOT clamp its parent part.",
            "qualification": "Nominal geometry only: thread form, fastener lots, print allowances, torque/creep/pullout and tool handles unqualified."
        },
        "physical_parts": {name: scene(s) for name, s in physical.items()},
        "cross_face_planning_reservations": {},
        "material_intersections": [], "assembly_paths": {}, "insulation_screens": {},
        "license_scope": "Original mechanics/code/docs MIT under mechanical/LICENSE. Mixed electronics remains CC BY-SA 3.0.",
        "assumptions_and_gates": [
            "Owner print-fit feedback is not measured installed clearance, loaded retention or finished-PCBA fit.",
            "No source component is shrunk, re-heighted or silently translated. Detailed contacts only use the explicit new contract.",
            "Cell D16.4/L34, button geometry, contact loaded force/travel and vent space remain unqualified.",
            "Full cell body and its all-direction guard remain unclipped even when they intersect shell/PCB.",
            "Speaker rim bearing, intermediate basket, terminals, rear vent, lead routing and excursion are unmeasured.",
            "M2 DIN934-style AF4/H1.6 nuts and ISO4762-style headD3.8/H2 are dimension screens, not qualified supplier lots.",
            "Nut-pocket AF4.2, screw D2.2 and register gaps are print assumptions, not measured manufacturing tolerance.",
            "Plastic proud target is geometric only: seams, tools, abrasion, temperature, flammability and dielectric behavior remain gates.",
            "Raw cell negative can must be isolated from both shell and protected system GND when low-side protection opens.",
            "No PCB routing, purchase, physical shell drilling, fabrication, live-cell work or GUI launch was performed.",
            "USB anchor/solder heights and individual anchor-hole solids are not supplied. The hidden full-depth cross-face prism is a planning reservation, not physical metal or a measured height.",
        ],
    }
    for name in ("body", "yoke", "cradle", "cover"):
        report["structural_parts"][name] = scene(physical[name])
    for index, reservation in enumerate(manifest.get("cross_face_keepouts", []), 1):
        z_min, z_max = (back, 41.75) if reservation["side"] == "B" else (stack_delta, front)
        prism = box(reservation["plan_w"], reservation["plan_h"], z_max-z_min, z=z_min)
        prism = moved(rotate(prism, reservation["angle"]), V(reservation["x"], reservation["y"], 0))
        feature(f"USBAnchorReservation{index}", prism, (.86, .20, .20), 85, False, "ConstructionReferences")
        report["cross_face_planning_reservations"][str(index)] = {
            "input": reservation, "z_range_mm": [z_min, z_max],
            "interpretation": "Unqualified anchor-height projection to the last measured/inferred cavity station; NOT physical occupied metal",
            "components_on_reserved_face": {c["reference"]: pair(prism, s) for c, s in physical_components
                                             if c["side"] == reservation["side"]},
            "structure_cell_hardware": {n: pair(prism, s) for n, s in physical.items()
                                        if not n.startswith("component_")}}
    progress("Exact BRep pair/insulation checks")
    # Disjoint bounding boxes are a sound rejection; remaining pairs get Booleans.
    items = list(physical.items())
    for i, (name, shape) in enumerate(items):
        for other, target in items[i+1:]:
            if shape.BoundBox.intersect(target.BoundBox):
                volume = max(0.0, shape.common(target).Volume)
                if volume > EPS:
                    intended = ((name == "cell" and other.startswith("contact_")) or
                                (other == "cell" and name.startswith("contact_")))
                    report["material_intersections"].append({"a": name, "b": other,
                                                             "intersection_mm3": volume,
                                                             "intended_contact": intended})
    for name, shape in [("cell", cell)] + [("contact_"+r["reference"], s) for r, s in contact_records] + metal_hardware:
        report["insulation_screens"][name] = {
            "cut_shell": pair(shape, shell), "uncut_shell": pair(shape, shell_uncut),
            "pcb": pair(shape, pcb),
            "target_mm": proud,
            "shell_distance_meets_nominal_target": shape.distToShape(shell)[0] >= proud-EPS,
            "note": "Distance is not proof of a continuous polymer barrier; contact zones/tool wells/seams need separate qualification."}
    report["insulation_screens"]["full_unclipped_cell_guard"] = {
        **scene(cell_outer), "construction": f"Exact rounded offset of full cylinder by clearance{clearance:g}+wall{proud:g}",
        "material": scene(guard), "cell_to_guard_material": pair(cell, guard)}
    wall_proof = []
    for name, outer_part, inner_part in guard_wall_witnesses:
        base.shape_stats(outer_part)
        base.shape_stats(inner_part)
        dilated_pocket = inner_part.makeOffsetShape(proud, .001, fill=False, join=0)
        base.shape_stats(dilated_pocket)
        missing_inner = max(0, inner_part.cut(outer_part).Volume)
        missing_dilation = max(0, dilated_pocket.cut(outer_part).Volume)
        missing_outer = max(0, outer_part.cut(guard_outer).Volume)
        if missing_inner > EPS or missing_dilation > EPS or missing_outer > EPS:
            raise RuntimeError(f"Guard-wall containment proof failed: {name}; inner={missing_inner:g}, "
                               f"dilation={missing_dilation:g}, outer={missing_outer:g}")
        wall_proof.append({"primitive": name, "proved_dilation_radius_mm": proud,
                           "inner_outside_own_stock_mm3": missing_inner,
                           "dilated_pocket_outside_own_stock_mm3": missing_dilation,
                           "stock_outside_global_stock_mm3": missing_outer})
    unexplained_void = max(0, guard_void.cut(Part.makeCompound([s for _, _, s in guard_wall_witnesses])).Volume)
    if unexplained_void > EPS:
        raise RuntimeError("Global guard pocket has volume outside its proved constituent pockets")
    stock_wall = min(p["proved_dilation_radius_mm"] for p in wall_proof)
    if stock_wall < proud-EPS:
        raise RuntimeError("Closed guard stock has less than the chosen minimum three-dimensional wall")
    report["insulation_screens"]["complete_rounded_contact_guard_stock"] = {
        **scene(guard_outer), "plastic_wall_target_mm": proud,
        "contact_clearance_assumption_mm": contact_clearance,
        "nominal_minimum_shell_margin_target_mm": .25,
        "closed_stock_wall_lower_bound_mm": stock_wall,
        "wall_bound_witnesses": wall_proof,
        "global_void_outside_proved_pocket_union_mm3": unexplained_void,
        "shell_margin_target_met": guard_outer.distToShape(shell)[0] >= .25-EPS,
        "note": "Each ACTUAL pocket is positively offset by the tested wall radius and the full resulting BRep is contained in its own stock. Every stock is contained in global stock; global pocket equals the proved pocket union. Dilation distributes over union, so closed-stock wall is at least the tested radius. This avoids OCC's unsupported nested-shell extrema operation without substituting a bounding-box distance. Before intentional PCB landing/fastener reliefs; no clipping to bell shell."}
    floor_top = cell_z-cell_diam/2-clearance
    floor_bottom = back+contact_interface["drawing_dimensions_mm"]["steel_thickness"]+contact_clearance
    floor_line = Part.makeLine(V(8, 0, floor_bottom), V(8, 0, floor_top))
    report["insulation_screens"]["under_cell_base_section"] = {
        "section_x_mm": 8, "section_y_mm": 0, "z_range_mm": [floor_bottom, floor_top],
        "available_nominal_wall_mm": floor_top-floor_bottom,
        "actual_cradle_material_on_section_mm": cradle.common(floor_line).Length,
        "note": "Specific nominal section, not a global insulation/creep/tolerance qualification."}
    if cradle.common(floor_line).Length < proud-EPS:
        raise RuntimeError("Under-cell section does not retain the chosen minimum plastic wall")
    structures = {"body": body, "yoke": yoke, "cradle": cradle, "cover": cover}
    report["component_structure_gaps"] = {
        c["reference"]: {name: pair(s, shape) for name, shape in structures.items()}
        for c, s in physical_components}
    report["speaker_structure_gaps"] = {name: pair(speaker, shape) for name, shape in structures.items()}
    report["speaker_component_gaps"] = {c["reference"]: pair(speaker, s) for c, s in physical_components}
    progress("Owner-requested speaker-to-PCB spacing comparison")
    spacing_cases = []
    for reduction in (0.5, 1.0):
        shifted_front_parts = [(c["reference"], moved(s, V(0, 0, -reduction)))
                               for c, s in physical_components if c["side"] == "F"]
        targets = {}
        for name, target in (("speaker", speaker), ("unchanged_yoke", yoke)):
            results = {ref: pair(s, target) for ref, s in shifted_front_parts}
            targets[name] = {
                "component_results": results,
                "intersecting_components": sorted(ref for ref, r in results.items()
                                                  if r["intersection_mm3"] > EPS),
                "touching_without_material_overlap": sorted(ref for ref, r in results.items()
                                                             if r["distance_mm"] <= EPS
                                                             and r["intersection_mm3"] <= EPS),
                "minimum_distance_mm": min(r["distance_mm"] for r in results.values()),
            }
        spacing_cases.append({"pcb_mouthward_reduction_mm": reduction,
                              "speaker_fixed": True, "component_xy_and_heights_unchanged": True,
                              "targets": targets})
    report["speaker_pcb_spacing_sensitivity"] = {
        "owner_feedback": json.loads(raw["spacing_feedback"].decode("utf-8-sig")),
        "baseline_minimum_fitted_component_to_speaker_mm": min(
            r["distance_mm"] for r in report["speaker_component_gaps"].values()),
        "cases": spacing_cases, "applied_to_released_geometry": False,
        "scope": "Rigid PCB/component-only reductions, not a revised support or USB design. "
                 "Bare-board air space is not minimum fitted-part clearance. Zero-distance "
                 "contact is not an acceptable positive clearance; any yoke/part repositioning "
                 "would require a new coordinated placement and support review.",
    }
    report["hardware_nearest_shell"] = {name: pair(s, shell) for name, s in metal_hardware}
    report["cell_retention_probes"] = {
        "note": "Finite rigid displacement into plastic demonstrates stops, not contact force or qualified restraint.",
        "probes": {axis+str(sign): {"cradle": pair(moved(cell, vector), cradle),
                                   "cover": pair(moved(cell, vector), cover)}
                   for axis, positive in (("X", V(.5, 0, 0)), ("Y", V(0, .5, 0)), ("Z", V(0, 0, .5)))
                   for sign, vector in ((1, positive), (-1, -positive))}}
    report["tool_access"] = {}
    for sign, axis, head_plane in shell_joint_axes:
        tool = Part.makeCylinder(.95, 30, head_plane+axis*2, axis)
        report["tool_access"]["ShellScrew_"+str(sign)] = {
            "tool_assumption": "D1.9 straight tool, aligned to the working lip normal; handle and physical drilling unqualified.",
            "obstacles": {"shell": pair(tool, shell), "body": pair(tool, body)}}
    for name, metal in metal_hardware:
        if "x6" not in name:
            continue
        bb = metal.BoundBox
        tool = cyl(.95, 40, (bb.XMin+bb.XMax)/2, (bb.YMin+bb.YMax)/2, bb.ZMax)
        obstacles = {"body": body, "yoke": yoke, "speaker": speaker}
        if not name.startswith("Yoke"):
            obstacles.update({"pcb": pcb, "cradle": cradle})
            obstacles.update({"contact_"+r["reference"]: s for r, s in contact_records})
        if name.startswith("Cover"):
            obstacles.update({"cell": cell, "cover": cover})
        report["tool_access"][name] = {
            "tool_assumption": "D1.9 straight shaft for nominal1.5AF hex key; handle/tilted access not modeled. Cartridge outside bell.",
            "obstacles": {n: pair(tool, s) for n, s in obstacles.items()}}
    report["contact_subpart_checks"] = {
        ref: [{"index": i, "cell": pair(s, cell), "cut_shell": pair(s, shell),
               "interpretation": "Base tabs/base, segmented spring, then two assumed loaded ears; order preserved from source"}
              for i, s in enumerate(parts)] for ref, parts in contact_segments.items()}
    report["contact_geometry_contract_checks"] = {
        "spring_polyline_interpretation": "Exact cell-facing surface; add stated thickness along +X before mirroring BT2",
        "spring_thickness_mm": contact_interface["right_contact_original_primitives"]["spring_thickness"] if contact_interface else None,
        "spring_segment_coordinate_checks_passed": bool(contact_interface),
        "loaded_ear_angles_consumed": contact_interface["right_contact_original_primitives"]["ears"]["angle_degrees"] if contact_interface else None,
        "loaded_outer_width_mm": contact_interface["right_contact_original_primitives"]["candidate_loaded_outer_width_mm"] if contact_interface else None,
        "loaded_force_travel_qualified": False,
        "cell_material_intersection_mm3": {r["reference"]: max(0, s.common(cell).Volume) for r, s in contact_records}}
    progress("Assembly/service path checks")
    # Analytic speaker sweep plus explicit rigid translation samples.
    speaker_sweep = cyl(20, 62, z=stack_delta).fuse(cyl(10.85, 57, z=sz(12)))
    report["assembly_paths"]["speaker_before_yoke"] = {
        "motion": f"Speaker front z{stack_delta+50:g} to z{stack_delta:g} outside bell; yoke/PCB absent",
        "exact_swept_union_vs_body": pair(speaker_sweep, body),
        "wrong_order_swept_union_vs_installed_yoke": pair(speaker_sweep, yoke)}
    lower_nut_paths = {}
    for index, (x, y) in enumerate(lower_mounts, 1):
        r = math.hypot(x, y)
        direction = V(x/r, y/r, 0)
        target = dict(metal_hardware)[f"BodyCaptiveM2Nut_{index}"]
        base_z = sz(4.8)
        staging_z = sz(8)+.45
        poses = [(26.5, staging_z+20), (26.5, staging_z), (29.1, staging_z),
                 (29.1, base_z), (r, base_z)]
        samples = []
        for (r1p, z1p), (r2p, z2p) in zip(poses, poses[1:]):
            for t in (0, .25, .5, .75, 1):
                rr, zz = r1p+(r2p-r1p)*t, z1p+(z2p-z1p)*t
                pose = moved(target, direction*(rr-r)+V(0, 0, zz-base_z))
                samples.append({"radius_mm": rr, "base_z_mm": zz, "body": pair(pose, body),
                                "speaker": pair(pose, speaker)})
        lower_nut_paths[str(index)] = {"waypoints_radius_base_z_mm": poses, "samples": samples}
    report["assembly_paths"]["lower_nut_loading"] = {
        "motion": "Before yoke: lower through register atR26.5, shift out above support, lower atR29.1, then slide inward under captive roof. Never push through external skirt.",
        "continuous_path_proven": False, "paths": lower_nut_paths}
    shell_nut_paths = {}
    for sign, axis, head_plane in shell_joint_axes:
        target = dict(shell_hardware)[f"InsulatingShellM2Nut_{sign+2}"]
        samples = []
        for offset in (0, .25, .5, 1, 2, 3, 4, 5):
            position = moved(target, -axis*offset)
            samples.append({"inward_offset_mm": offset, "body": pair(position, body),
                            "speaker": pair(position, speaker)})
        if any(p[key]["intersection_mm3"] > EPS for p in samples for key in ("body", "speaker")):
            raise RuntimeError("Insulating shell nut cannot follow its declared inner-socket loading path")
        shell_nut_paths[str(sign)] = samples
    report["assembly_paths"]["shell_nut_loading"] = {
        "motion": "Before yoke/PCB, insert from bell-axis side along the inclined screw axis; work outside bell. Hexagonal socket opens inward.",
        "continuous_path_proven": False, "samples": shell_nut_paths}
    for name, moving, obstacles, travel in (
            ("yoke_over_magnet", yoke, {"speaker": speaker, "body": body}, 30),
            ("pcb_onto_yoke", fuse([pcb]+[s for _, s in physical_components]+[s for _, s in contact_records], False),
             {"speaker": speaker, "body": body, "yoke": yoke}, 30),
            ("cover_off_cell", cover, {"cell": cell, "cradle": cradle}, 20)):
        samples = []
        for z in range(0, travel+1, 2):
            position = moved(moving, V(0, 0, z))
            samples.append({"offset_z_mm": z,
                            "collisions_mm3": {n: max(0, position.common(s).Volume) for n, s in obstacles.items()}})
        report["assembly_paths"][name] = {"samples": samples, "sample_step_mm": 2,
                                         "continuous_path_proven": False}
    initially_conflicting = [(n, s) for n, s in physical.items() if not n.startswith("InsulatingShell")
                             and report["physical_parts"][n]["cut_shell"]["intersection_mm3"] > EPS]
    cartridge = Part.makeCompound([s for _, s in initially_conflicting]) if initially_conflicting else None
    withdrawal = []
    for z in (0, 1, 2, 3, 5, 8, 12, 20, 30, 45, 60):
        withdrawal.append({"mouthward_translation_mm": z,
                           "cut_shell_intersection_mm3": max(0, moved(cartridge, V(0, 0, -z)).common(shell).Volume) if cartridge else 0})
    report["assembly_paths"]["complete_cartridge_mouthward_withdrawal"] = {
        "prerequisite": "Unplug cable and remove BOTH radial shell screws completely; shell nuts remain with carrier.",
        "slot": "Axially open -Y cutout all the way to mouth; no closed side port traps connector.",
        "screened_initial_blockers": [n for n, _ in initially_conflicting],
        "clear_part_reasoning": "The working cavity widens monotonically toward z0 and the constant-X USB slot is open to z0. Initially-contained parts remain contained under -z translation; no closed side port is assumed.",
        "continuous_path_proven": False, "samples": withdrawal}
    usb = next((s for c, s in physical_components if c["reference"] == "X6"), None)
    if usb:
        bb = usb.BoundBox
        exterior = -(radius((bb.ZMin+bb.ZMax)/2)+d["shell_radial_wall_mm"])
        plug = box(8.8, 8, 2.6, 0, bb.YMin-4, (bb.ZMin+bb.ZMax)/2-1.3)
        feature("UnselectedUSBPlugNoseScreen", plug, (.9, .4, .3), 60, False, "ConstructionReferences")
        report["usb_access"] = {
            "exact_source_interface": manifest.get("usb_interface"),
            "component_bounds_consumed": base.bounds(usb), "working_exterior_y_at_center_z_mm": exterior,
            "connector_front_y_from_body_proxy_mm": bb.YMin,
            "body_proxy_recess_from_working_outer_wall_mm": bb.YMin-exterior,
            "flush_claim": False, "plug_nose_unselected_assumption_mm": [8.8, 8, 2.6],
            "plug_vs_body": pair(plug, body), "plug_vs_shell": pair(plug, shell),
            "note": "The explicit interface retains the source F.Fab mouth datum. Approximate midheight alignment is not whole-face flush against a curved shell. No actual mating plug or anchor height is selected."}

    for name, content in raw.items():
        doc.addObject("App::TextDocument", "Raw_"+name).Text = base64.b64encode(content).decode("ascii")
    doc.addObject("App::TextDocument", "InputRawByteEncoding").Text = "Raw_* are base64 of exact source bytes; SHA256 in provenance."
    doc.addObject("App::TextDocument", "Assumptions").Text = json.dumps(report["assumptions_and_gates"], indent=2)
    doc.addObject("App::TextDocument", "InputProvenance").Text = json.dumps(report["input"], indent=2)
    sheet = doc.addObject("Spreadsheet::Sheet", "Parameters")
    sheet.set("A1", "mm; change parameter JSON and regenerate, not live expressions")
    for row, (key, value) in enumerate(d.items(), 2):
        sheet.set(f"A{row}", key)
        sheet.set(f"B{row}", str(value))
    sheet.setColumnWidth("A", 370)
    doc.recompute()

    write_json(out / "fit-report.in-progress.json", report)
    progress("STEP export and exact BRep round-trip checks")
    # All STEP operations deliberately precede mesh tessellation.
    assembly = [objects[n] for n in ("FrontBodyGrilleRegisterUSBBezel", "RemovableSpeakerCaptureYoke",
                                    "LoadBearingInsulatingBatteryCradle", "RemovableBatteryCaptureCover",
                                    "SpeakerConditionalBodyScreen", "PCBSubstrateExactInterface", "T8FullUnclippedCellCanEnvelope")]
    assembly += [objects["Component_"+c["reference"]] for c, _ in physical_components]
    assembly += [objects["ContactMetal_"+r["reference"]] for r, _ in contact_records]
    assembly += [objects[n] for n, _ in metal_hardware+shell_hardware]
    artifacts = {"t8-cartridge-assembly.step": export_step(out / "t8-cartridge-assembly.step", assembly, Part)}
    artifacts["t8-cartridge-with-shell.step"] = export_step(
        out / "t8-cartridge-with-shell.step", assembly+[objects["WorkingShellWithProposedOpenSlot"], objects["HandleExteriorOnly"]], Part)
    for name, object_name in (("body", "FrontBodyGrilleRegisterUSBBezel"),
                              ("yoke", "RemovableSpeakerCaptureYoke"),
                              ("battery-cradle", "LoadBearingInsulatingBatteryCradle"),
                              ("battery-cover", "RemovableBatteryCaptureCover")):
        artifacts[name+".step"] = export_step(out / (name+".step"), [objects[object_name]], Part)
    pcba = fuse([pcb]+[s for _, s in physical_components]+[s for _, s in contact_records], False)
    pcba_obj = feature("PopulatedT8PCBAExportOnly", pcba, (.2, .5, .3), 0, False, "ConstructionReferences")
    artifacts["populated-t8-pcba.step"] = export_step(out / "populated-t8-pcba.step", [pcba_obj], Part)
    print_pcba = fuse([pcb]+[s for _, s in physical_components])
    print_pcba_obj = feature("INERTPCBWithoutContacts", print_pcba, (.2, .5, .3), 0, False, "ConstructionReferences")
    artifacts["populated-t8-pcba-without-contacts.step"] = export_step(
        out / "populated-t8-pcba-without-contacts.step", [print_pcba_obj], Part)
    progress("STL tessellation and manifold/BRep checks")
    full_mesh = MeshPart.meshFromShape(Shape=pcba, LinearDeflection=.045, AngularDeflection=.12, Relative=False)
    mesh_points, mesh_faces = full_mesh.Topology
    edge_counts = Counter(tuple(sorted((face[i], face[(i+1) % 3]))) for face in mesh_faces for i in range(3))
    nonmanifold_edges = [{"incident_facets": count, "endpoints_mm": [list(mesh_points[a]), list(mesh_points[b])]}
                         for (a, b), count in edge_counts.items() if count != 2]
    report["pcba_inert_print_scope"] = {
        "released_stl": "INERT-populated-t8-pcba-without-contacts.stl",
        "omitted_only_from_inert_dummy": sorted(contact_refs),
        "full_contacts_retained_in_native_and_step": True,
        "full_contact_mesh_edge_defects": nonmanifold_edges,
        "reason": "Supplied cell-facing spring/base primitives meet along zero-width edges outside the narrow outer solder tab. Do not invent connecting metal or release a nonmanifold full-contact STL.",
        "qualification": "Not a contact-fit gauge. Fold roots and loaded contact geometry require review."}
    for name, shape in (("body", body), ("yoke", yoke), ("battery-cradle", cradle), ("battery-cover", cover),
                        ("speaker-body-screen", speaker), ("T8-full-cell", cell),
                        ("populated-t8-pcba-without-contacts", print_pcba)):
        filename = "INERT-"+name+".stl"
        artifacts[filename] = export_stl(out / filename, shape, Part, Mesh, MeshPart)
    (out / "INERT-populated-t8-pcba.stl").unlink(missing_ok=True)
    native = out / "t8-cartridge.FCStd"
    progress("Native file and raw-byte round-trip checks")
    expected = {n: obj.Shape.copy() for n, obj in objects.items()}
    doc.recompute()
    doc.saveAs(str(native))
    App.closeDocument(doc.Name)
    add_display_metadata(native, styles)
    reopened = App.openDocument(str(native))
    max_native_diff = 0.0
    for name, original in expected.items():
        restored = reopened.getObject(name).Shape
        base.shape_stats(restored)
        diff = max(0, original.cut(restored).Volume) + max(0, restored.cut(original).Volume)
        max_native_diff = max(max_native_diff, diff)
        if diff > 1e-5:
            raise RuntimeError("Native BRep changed: " + name)
    for name, content in raw.items():
        if base64.b64decode(reopened.getObject("Raw_"+name).Text) != content:
            raise RuntimeError("Native raw source bytes changed")
    App.closeDocument(reopened.Name)
    artifacts[native.name] = {"sha256": base.sha256(native), "reopened_shape_count": len(expected),
                              "maximum_brep_symmetric_difference_mm3": max_native_diff,
                              "raw_source_bytes_verified": True, "display_metadata_written": True,
                              "GUI_display_exercised": False}
    for key in ("placement", "measurements", "contact_interface"):
        if key not in raw:
            continue
        name = key+"-snapshot.json"
        (out / name).write_bytes(raw[key])
        artifacts[name] = {"sha256": base.sha256(out / name), "exact_source_bytes": True}
    write_json(out / "parameters.json", d)
    render_profiles(out / "inner-outer-profile-and-datums.svg", measured, radius, d, report)
    report["artifacts"] = artifacts
    report["summary"] = {
        "fitted_manifest_components": len(components), "explicit_contact_objects": len(contact_records),
        "explicit_contact_brep_solids": sum(len(s.Solids) for _, s in contact_records),
        "primary_printed_pieces": 4,
        "structural_solid_counts": {n: len(s.Solids) for n, s in structures.items()},
        "nonintentional_material_intersections": len([r for r in report["material_intersections"] if not r["intended_contact"]]),
        "shell_conflicting_parts": [n for n, r in report["physical_parts"].items() if r["cut_shell"]["intersection_mm3"] > EPS],
        "complete_cartridge_withdrawal_max_intersection_mm3": max(r["cut_shell_intersection_mm3"] for r in withdrawal),
        "nominal_guard_shell_margin_mm": guard_outer.distToShape(shell)[0],
        "nominal_geometry_fit_clear": not report["material_intersections"] and
            all(r["cut_shell"]["intersection_mm3"] <= EPS for r in report["physical_parts"].values()) and
            guard_outer.distToShape(shell)[0] >= .25-EPS and cradle.common(floor_line).Length >= proud-EPS,
        "live_cell_or_child_use_qualified": False,
        "routing_approved": False,
    }
    write_json(out / "fit-report.json", report)
    for name in ("fit-report.json", "parameters.json", "inner-outer-profile-and-datums.svg", "README.md", "REPRODUCE.md"):
        if (out / name).is_file():
            artifacts[name] = {"sha256": base.sha256(out / name)}
    write_json(out / "artifact-manifest.json", {"input_hashes": hashes, "artifacts": artifacts})
    if any(base.sha256(path) != hashes[key] for key, path in paths.items()):
        raise RuntimeError("Source/input changed during generation; regenerate exact final inputs")
    completion = {"token": args.token, "input_hashes": hashes, "summary": report["summary"],
                  "artifact_manifest_sha256": base.sha256(out / "artifact-manifest.json")}
    write_json(out / "completion.json", completion)
    write_json(out / "review-status.json", {"status": "INERT_REVIEW_WITH_EXPLICIT_OPEN_GATES",
                                           "completion_token": args.token, "input_hashes": hashes,
                                           "qualified": False, "routing_approved": False})
    write_json(args.completion_file, completion)
    (out / "fit-report.in-progress.json").unlink(missing_ok=True)
    (out / ".build-progress.json").unlink(missing_ok=True)


if __name__ == "__main__":
    options = arguments()
    build(options) if options.inside_freecad else launch(options)
