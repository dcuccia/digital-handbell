#!/usr/bin/env python3
"""Separate MIT-licensed measured-speaker study; preserve the original print kit.

Run with ordinary Python and installed FreeCADCmd. Imports the frozen mechanical
builder's geometry/export helpers without changing its source or output files.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_mechanical as base

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "mechanical" / "studies" / "2026-09-09-measured-speaker"
DEPTHS = (20.0, 20.5, 21.0, 22.0, 23.0, 24.0)
SPEAKER_GAP = 0.5
CELL_STANDOFF = 1.0


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measurements", type=Path,
                        default=ROOT / "docs" / "measurements" / "shell-speaker-inputs.json")
    parser.add_argument("--placement", type=Path,
                        default=ROOT / "hardware" / "handbell" / "placement" / "placement-manifest.json")
    parser.add_argument("--shell-parameters", type=Path, default=ROOT / "mechanical" / "parameters.json")
    parser.add_argument("--output", type=Path, default=STUDY)
    parser.add_argument("--freecad-cmd", type=Path,
                        default=Path(os.environ.get("LOCALAPPDATA", "")) /
                        "Programs" / "FreeCAD 1.1" / "bin" / "FreeCADCmd.exe")
    parser.add_argument("--inside-freecad", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--completion-file", type=Path, help=argparse.SUPPRESS)
    return parser.parse_args()


def launch(args):
    if not args.freecad_cmd.is_file():
        raise FileNotFoundError(args.freecad_cmd)
    for path in (args.measurements, args.placement, args.shell_parameters):
        if not path.is_file():
            raise FileNotFoundError(path)
    output = args.output.resolve()
    if output in (ROOT, ROOT / "mechanical"):
        raise ValueError("Use a separate study directory, never the root or original print-kit directory")
    # The frozen builder's launcher hard-codes its own script; use a separate
    # invocation so the historical generator and hash-bound artifacts stay intact.
    with tempfile.TemporaryDirectory(prefix="handbell-speaker-study-") as temporary:
        temporary = Path(temporary)
        marker = temporary / "completed.json"
        script = str(Path(__file__).resolve())
        argv = [script, *sys.argv[1:], "--inside-freecad", "--completion-file", str(marker)]
        source = f"import runpy, sys\nsys.argv = {argv!r}\nrunpy.run_path({script!r}, run_name='__main__')\n"
        command = [str(args.freecad_cmd), "--user-cfg", str(temporary / "user.cfg"),
                   "--system-cfg", str(temporary / "system.cfg")]
        result = subprocess.run(command, input=source, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, encoding="utf-8", errors="replace", timeout=300)
        output.mkdir(parents=True, exist_ok=True)
        (output / "freecad-build.log").write_text(result.stdout, encoding="utf-8")
        if result.returncode != 0 or not marker.is_file():
            print(result.stdout, file=sys.stderr)
            raise RuntimeError("Measured-speaker build did not complete; see the study's local log")
        print(marker.read_text(encoding="utf-8"))


def read_speaker(inputs):
    if inputs["units"] != "mm":
        raise ValueError("Measurements must use millimetres")
    measured = inputs["speaker_40mm_candidate"]["owner_measurements"]
    keys = ("frame_diameter_mm", "overall_depth_mm", "basket_rear_z_mm",
            "basket_rear_diameter_mm", "magnet_height_mm", "magnet_diameter_mm")
    values = {key: base.finite_number(measured[key], key, positive=True) for key in keys}
    if abs(values["basket_rear_z_mm"] + values["magnet_height_mm"] - values["overall_depth_mm"]) > 1e-6:
        raise ValueError("Basket/magnet axial reports are inconsistent; resolve their datums explicitly")
    if not values["frame_diameter_mm"] > values["basket_rear_diameter_mm"] > values["magnet_diameter_mm"]:
        raise ValueError("Expected frame > rear basket > magnet diameter")
    return measured, values


def body_record(shape, cavity, shell):
    outside = max(0.0, shape.cut(cavity).Volume)
    return {**base.shape_stats(shape), "outside_cavity_volume_mm3": outside,
            "contained_in_assumed_cavity": outside <= base.VOLUME_EPSILON,
            "shell_overlap_mm3": base.common_volume(shape, shell),
            "distance_to_shell_mm": shape.distToShape(shell)[0]}


def battery_shapes(board_z, Part, Vector):
    bottom = board_z + 1.6 + CELL_STANDOFF
    for name, diameter, length in (("compact_16340_example", 16.8, 34.0),
                                  ("fenix_arb_l16_700up_published_body", 16.8, 35.5),
                                  ("nominal_18350_not_protected_maximum", 18.0, 35.0)):
        for clearance in (0.0, 0.5, 1.0):
            shape = Part.makeCylinder(diameter / 2 + clearance, length + 2 * clearance,
                                      Vector(-length / 2 - clearance, 0, bottom + diameter / 2),
                                      Vector(1, 0, 0))
            yield name, clearance, shape, {"diameter_mm": diameter, "length_mm": length,
                                         "body_bottom_z_mm": bottom}
    for name, width, length, height in (("compact_pouch_placeholder", 18.0, 28.0, 8.0),
                                      ("larger_pouch_placeholder", 20.0, 30.0, 8.0)):
        for clearance in (0.0, 0.5, 1.0):
            shape = base.box_at(width + 2 * clearance, length + 2 * clearance, height + 2 * clearance,
                                0, 0, bottom - clearance, Part, Vector)
            yield name, clearance, shape, {"width_mm": width, "length_mm": length, "height_mm": height,
                                         "body_bottom_z_mm": bottom}


def export_stl(path, shape, Mesh, MeshPart):
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.05,
                                 AngularDeflection=0.15, Relative=False)
    mesh.write(str(path))
    imported = Mesh.Mesh(str(path))
    if (not imported.isSolid() or imported.countComponents() != 1
            or imported.hasNonManifolds() or imported.hasSelfIntersections()):
        raise RuntimeError(f"{path.name}: invalid printable mesh")
    volume_error = abs(imported.Volume - shape.Volume) / shape.Volume
    mesh_box = imported.BoundBox
    original_box = shape.BoundBox
    bound_error = max(abs(getattr(mesh_box, key) - getattr(original_box, key))
                      for key in ("XMin", "YMin", "ZMin", "XMax", "YMax", "ZMax"))
    if volume_error > 0.01 or bound_error > 0.1:
        raise RuntimeError(f"{path.name}: mesh dimensions/volume changed")
    return {"sha256": base.sha256(path), "units": "STL is unitless; import as mm at 100%",
            "connected_components": 1, "closed": True, "manifold": True,
            "self_intersections": False, "relative_volume_error": volume_error,
            "maximum_bound_error_mm": bound_error, "bounds": base.bounds(shape)}


def render_view(path, dimensions, scenes):
    d = dimensions
    text = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="520" viewBox="0 0 1120 520">',
        '<rect width="1120" height="520" fill="#fafafa"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#17202a}</style>',
        '<text x="24" y="32" font-size="22">Measured speaker stations - 2026-09-09</text>',
        '<text x="24" y="58" font-size="13">Original geometry; basket interpolation is assumed. No terminal, vent, tolerance or retention approval.</text>',
    ]
    scale, cx, top = 7, 190, 102
    frame, basket, magnet = (d[key] / 2 for key in
                             ("frame_diameter_mm", "basket_rear_diameter_mm", "magnet_diameter_mm"))
    rear, depth = d["basket_rear_z_mm"], d["overall_depth_mm"]
    points = [(-frame, 0), (-basket, rear), (-magnet, rear), (-magnet, depth),
              (magnet, depth), (magnet, rear), (basket, rear), (frame, 0)]
    coords = " ".join(f"{cx+x*scale:.2f},{top+z*scale:.2f}" for x, z in points)
    text.extend([
        f'<rect x="{cx-frame*scale}" y="{top}" width="{frame*2*scale}" height="{rear*scale}" fill="#fff0d1" stroke="#a65f00" stroke-dasharray="5,4"/>',
        f'<polygon points="{coords}" fill="#d9eaf8" stroke="#21618c" stroke-width="2"/>',
        '<text x="42" y="270" font-size="14">Blue: linear basket interpolation + magnet</text>',
        '<text x="42" y="294" font-size="14">Dashed: full-width basket screening envelope</text>',
        f'<text x="42" y="326" font-size="14">Frame D{2*frame:g}; rear basket D{2*basket:g} at z{rear:g}</text>',
        f'<text x="42" y="350" font-size="14">Magnet D{2*magnet:g} x H{d["magnet_height_mm"]:g}; total depth {depth:g} mm</text>',
        '<text x="455" y="106" font-size="17">Speaker-facing components; unchanged rigidly flipped PCB</text>',
        '<text x="455" y="134" font-size="13">Board front z | body overlaps | min speaker gap | board contained</text>',
    ])
    for index, scene in enumerate(scenes):
        summary = scene["summary"]
        line = (f'{scene["board"]["front_z_mm"]:g} mm | '
                f'{", ".join(summary["speaker_conflicts"]) or "none"} | '
                f'{summary["minimum_speaker_distance_mm"]:.2f} mm | '
                f'{"yes" if summary["substrate_contained"] else "NO"}')
        text.append(f'<text x="455" y="{164+index*29}" font-size="14">{html.escape(line)}</text>')
    text.extend([
        '<text x="24" y="425" font-size="14">All depths are modeled choices, NOT measured insertion depths. Existing print and KiCad files are unchanged.</text>',
        '<text x="24" y="453" font-size="14">Cylindrical/pouch alternatives are in fit-report.json; no contacts, cradle or cell rating has been qualified.</text>',
        '<text x="24" y="481" font-size="14">No reinforced carrier/grille is released here: the owner did not identify which other parts were flimsy.</text>',
        '</svg>',
    ])
    path.write_text("\n".join(text) + "\n", encoding="utf-8")


def build(args):
    import FreeCAD as App
    import Part
    import Mesh
    import MeshPart
    Vector = App.Vector
    inputs = json.loads(args.measurements.read_text(encoding="utf-8-sig"))
    measured, d = read_speaker(inputs)
    manifest = base.read_manifest(args.placement)
    if manifest["board"]["diameter_mm"] != 43 or manifest["board"]["thickness_mm"] != 1.6:
        raise ValueError("This dated screen requires the original 43 x 1.6 mm board")
    p = base.load_parameters(SimpleNamespace(parameters_from=None, parameters=args.shell_parameters,
                                             speaker_front_z=None), manifest, App)
    output = args.output.resolve()
    if output in (ROOT, ROOT / "mechanical"):
        raise ValueError("Refusing to overwrite the original print kit")
    output.mkdir(parents=True, exist_ok=True)
    App.ParamGet("User parameter:BaseApp/Preferences/Document").SetInt("CountBackupFiles", 0)
    doc = App.newDocument("MeasuredSpeakerStudy")
    doc.Label = "Measured speaker stations - assumed basket / unrouted PCB screen"
    doc.Comment = ("Original mechanical primitives/code MIT; electronics context retains CC BY-SA 3.0 "
                   "notices from hardware/handbell. No manufacturer CAD or photos copied.")
    for name, value in (("Measurements", inputs), ("PlacementManifest", manifest),
                        ("ShellParameters", p)):
        item = doc.addObject("App::TextDocument", name)
        item.Text = json.dumps(value, indent=2)
    for name, source in (("StudySource", Path(__file__)), ("GeometryHelperSource", Path(base.__file__))):
        doc.addObject("App::TextDocument", name).Text = source.read_text(encoding="utf-8")
    sheet = doc.addObject("Spreadsheet::Sheet", "MeasuredStations")
    sheet.set("A1", "Owner measurement; mm, not tolerance limits")
    sheet.set("B1", "Value")
    for row, (key, value) in enumerate(d.items(), start=2):
        sheet.set(f"A{row}", key)
        sheet.set(f"B{row}", str(value))
    sheet.setColumnWidth("A", 330)

    def feature(name, shape, label):
        base.shape_stats(shape)
        item = doc.addObject("Part::Feature", name)
        item.Label = label
        item.Shape = shape
        return item

    cavity = base.make_profile(p, Part, Vector)
    shell = base.make_profile(p, Part, Vector, p["shell_radial_thickness_mm"], capped=True).cut(cavity)
    feature("AssumedShell", shell, "ASSUMED shell; no USB slot; hide to inspect")
    magnet = Part.makeCylinder(d["magnet_diameter_mm"] / 2, d["magnet_height_mm"],
                               Vector(0, 0, d["basket_rear_z_mm"]))
    stepped = Part.makeCylinder(d["frame_diameter_mm"] / 2, d["basket_rear_z_mm"]).fuse(magnet).removeSplitter()
    interpolated = Part.makeCone(d["frame_diameter_mm"] / 2, d["basket_rear_diameter_mm"] / 2,
                                  d["basket_rear_z_mm"]).fuse(magnet).removeSplitter()
    full = Part.makeCylinder(d["frame_diameter_mm"] / 2, d["overall_depth_mm"])
    speakers = {
        "speaker-stepped-body-envelope": feature("SteppedSpeaker", stepped, "SCREEN: full-width basket + measured magnet"),
        "speaker-interpolated-stations": feature("InterpolatedSpeaker", interpolated, "ILLUSTRATIVE: straight basket interpolation"),
        "speaker-full-body-cylinder": feature("FullSpeaker", full, "SCREEN: full measured D40 x H19 body cylinder"),
    }
    # A real 180-degree flip about X reverses Y and the in-plane rotation.
    # The reused helper then puts each body's Z range on the outward face.
    components = [{**c, "y_mm": -c["y_mm"], "rotation_deg": -c["rotation_deg"]}
                  for c in manifest["components"]]
    scenes, bodies = [], {}
    for z in DEPTHS:
        board = {**manifest["board"], "front_z_mm": z, "component_face": "outward"}
        result, substrate, parts = base.scenario(
            f"outward_z{z:g}", board, components, cavity, shell, stepped, p, Part, Vector)
        speaker_distances = {"PCB": substrate.distToShape(stepped)[0],
                             **{ref: shape.distToShape(stepped)[0] for ref, shape in parts}}
        result["summary"] = {
            "speaker_conflicts": result["speaker_conflicts"],
            "minimum_speaker_distance_mm": min(speaker_distances.values()),
            "substrate_contained": result["substrate"]["contained_in_assumed_cavity"],
            "interpolated_basket_conflicts": [ref for ref, shape in parts
                                            if base.common_volume(shape, interpolated) > base.VOLUME_EPSILON],
            "full_body_cylinder_conflicts": [ref for ref, shape in parts
                                           if base.common_volume(shape, full) > base.VOLUME_EPSILON],
        }
        result["note"] = ("Original proxies rotated rigidly 180 degrees about X, then translated to this depth. "
                          "No KiCad placement edit, component clipping, holder or carrier model.")
        result["speaker_distances_mm"] = speaker_distances
        result["battery_alternatives"] = []
        for name, clearance, shape, dimensions in battery_shapes(z, Part, Vector):
            result["battery_alternatives"].append({
                "name": name, "clearance_mm": clearance, "body": dimensions,
                "board_to_cell_body_standoff_mm": CELL_STANDOFF,
                "status": "Body/clearance-only; no contacts, cradle, leads, current or retention qualification",
                **body_record(shape, cavity, shell),
                "pcb_overlap_mm3": base.common_volume(shape, substrate),
                "speaker_overlap_mm3": base.common_volume(shape, stepped),
                "component_conflicts": [ref for ref, part in parts
                                        if base.common_volume(shape, part) > base.VOLUME_EPSILON],
            })
        scenes.append(result)
        bodies[z] = substrate, parts
    qualifying = [scene for scene in scenes if scene["summary"]["substrate_contained"]
                  and not scene["speaker_conflicts"] and not scene["unplanned_cavity_conflicts"]
                  and scene["speaker_substrate_overlap_mm3"] <= base.VOLUME_EPSILON
                  and scene["summary"]["minimum_speaker_distance_mm"] >= SPEAKER_GAP]
    selected_z = qualifying[0]["board"]["front_z_mm"] if qualifying else None
    display_z = DEPTHS[0] if selected_z is None else selected_z
    substrate, parts = bodies[display_z]
    assembly = [speakers["speaker-stepped-body-envelope"],
                feature("PCB", substrate, f"Unrouted substrate at z{display_z:g}")]
    for ref, shape in parts:
        assembly.append(feature("Proxy_" + ref, shape, ref + " - original unscaled component proxy"))
    display_group = doc.addObject("App::DocumentObjectGroup", "AssemblyDisplay")
    display_group.Label = f"Outward body screen at z{display_z:g}; no carrier or contacts"
    for obj in assembly:
        display_group.addObject(obj)
    battery_group = doc.addObject("App::DocumentObjectGroup", "BatteryAlternatives")
    battery_group.Label = "Alternative bare bodies - show ONE only; no qualified contacts"
    for name, clearance, shape, _ in battery_shapes(display_z, Part, Vector):
        if clearance == 0:
            battery_group.addObject(feature(name, shape, name + " - bare body, not selected"))
    artifacts = {}
    for stem, obj in speakers.items():
        artifacts[stem + ".step"] = base.export_step_and_check(output / (stem + ".step"), [obj], Part)
        artifacts[stem + ".stl"] = export_stl(output / (stem + ".stl"), obj.Shape, Mesh, MeshPart)
    artifacts["outward-body-screen.step"] = base.export_step_and_check(
        output / "outward-body-screen.step", assembly, Part)
    base.write_json(output / "measurements-snapshot.json", inputs)
    base.write_json(output / "placement-snapshot.json", manifest)
    base.write_json(output / "shell-parameters-snapshot.json", p)
    native = output / "measured-speaker-study.FCStd"
    doc.recompute()
    expected = {obj.Name: base.shape_stats(obj.Shape) for obj in doc.Objects if hasattr(obj, "Shape")}
    doc.saveAs(str(native))
    App.closeDocument(doc.Name)
    reopened = App.openDocument(str(native))
    for name, stats in expected.items():
        obj = reopened.getObject(name)
        if obj is None or abs(base.shape_stats(obj.Shape)["volume_mm3"] - stats["volume_mm3"]) > 1e-6:
            raise RuntimeError(f"Native document did not preserve {name}")
    for name in ("MeasuredStations", "Measurements", "StudySource", "GeometryHelperSource", "PlacementManifest"):
        if reopened.getObject(name) is None:
            raise RuntimeError(f"Native document lost {name}")
    App.closeDocument(reopened.Name)
    artifacts[native.name] = {"sha256": base.sha256(native), "reopened_shape_count": len(expected)}
    render_view(output / "measured-speaker-screen.svg", d, scenes)
    for name in ("measurements-snapshot.json", "placement-snapshot.json", "shell-parameters-snapshot.json",
                 "measured-speaker-screen.svg"):
        artifacts[name] = {"sha256": base.sha256(output / name)}
    report = {
        "schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(), "units": "mm",
        "status": "Measured stations plus assumed geometry; not a routed, fully fitted or structural design",
        "measurements": measured, "input": {
            "measurements_sha256": base.sha256(args.measurements),
            "placement_sha256": base.sha256(args.placement),
            "shell_parameters_sha256": base.sha256(args.shell_parameters),
            "script_sha256": base.sha256(Path(__file__)),
            "geometry_helper_sha256": base.sha256(Path(base.__file__)),
        },
        "toolchain": {"freecad": App.Version(), "opencascade": Part.OCC_VERSION, "python": sys.version},
        "speaker_models": {name: base.shape_stats(obj_shape) for name, obj_shape in
                           (("stepped_body", stepped), ("linear_interpolation", interpolated), ("full_body", full))},
        "scenarios": scenes, "selected_screen_depth_mm": selected_z, "display_depth_mm": display_z,
        "selection_rule": f"First listed depth with substrate contained, no unplanned component cavity conflicts, "
                          f"no speaker body overlap, and >= {SPEAKER_GAP:g} mm nominal speaker-body distance. "
                          "Does not approve USB, battery, terminal/vent clearances, retention or electrical placement.",
        "artifacts": artifacts,
        "limits": [
            "Shell taper is still an assumption; physical PCB fit feedback has no measured depth/orientation.",
            "Speaker front is at bell opening z0 by assumption; mounting that shifts it changes the results.",
            "Basket interpolation and stepped screening bounds omit rim detail, terminals, wires, vent and tolerances.",
            "0.5 mm body gap is an illustrative screening threshold, not a validated acoustic/thermal clearance.",
            "Uniform battery clearances and 1 mm standoff are sensitivities, not a holder/cradle footprint.",
            "Fenix ARB-L16-700UP published body dimensions omit tolerances, positive-button detail and contact geometry.",
            "Nominal 18350 dimensions exclude any protection/button-top enlargement.",
            "No retained carrier/grille is included or strengthened; unspecified flimsy-part feedback remains open.",
            "No footprints, nets, existing print artifacts or source placement were modified.",
            "No battery part/current/charge approval, reverse-insertion protection or manufacturing release.",
        ],
        "license_scope": "Original mechanical primitives and code MIT. Electronics placement context "
                         "retains hardware/handbell CC BY-SA 3.0 attribution; see mechanical/README.md.",
    }
    base.write_json(output / "fit-report.json", report)
    if args.completion_file is None:
        raise ValueError("Internal build requires a fresh completion marker")
    base.write_json(args.completion_file, {
        "output": str(output), "selected_screen_depth_mm": selected_z,
        "scenarios": [{"z_mm": row["board"]["front_z_mm"], **row["summary"]} for row in scenes],
        "artifact_count": len(artifacts),
    })


if __name__ == "__main__":
    options = arguments()
    if options.inside_freecad:
        build(options)
    else:
        launch(options)
