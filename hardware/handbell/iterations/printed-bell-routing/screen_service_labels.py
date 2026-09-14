# SPDX-License-Identifier: MIT
"""Screen actual KiCad glyphs against pinned or explicitly rebound capture CAD."""
import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MECHANICAL = ROOT / "mechanical" / "studies" / "2026-09-13-printed-bell"
VISIBILITY_COMMIT = "4bbdcbb0ee1724b450b66f3a03abcaa8c48333d1"
VISIBILITY_GIT_PATH = "mechanical/studies/2026-09-13-printed-bell/printed-bell.FCStd"
VISIBILITY_NATIVE_SHA256 = "f0dae8f6e5c62fa41f64d16ebe4bbf2f22cd5f65a266f279c2537c6fae2416fc"
TEXT_RESERVATIONS = {
    "+ POS": (15.7, 11, 4.4, 1.4),
    "- NEG": (-15.7, 11, 4.4, 1.4),
    "< T8 BUTTON END": (0, 10.5, 12, 1.4),
}


def visibility_native():
    raw = subprocess.check_output(["git", "show", VISIBILITY_COMMIT+":"+VISIBILITY_GIT_PATH], cwd=ROOT)
    if hashlib.sha256(raw).hexdigest() != VISIBILITY_NATIVE_SHA256:
        raise ValueError("Corrected visibility native differs from parent's explicit hash")
    return raw


def mechanical_screen(work):
    import FreeCAD as App
    import Part
    request = json.loads((work / "request.json").read_text())
    document = App.openDocument(str(work / "released.FCStd"))
    names = [
        "RetainedInsulatingCellCradle", "INERTUnqualifiedFullCellD16p4L34",
        "ContactMetal_BT1", "ContactMetal_BT2", "YokeM2x6_1", "YokeM2x6_2",
        "BodyCaptiveM2Nut_1", "BodyCaptiveM2Nut_2", "MH1M2x6", "MH2M2x6",
        "MH1CaptiveM2Nut", "MH2CaptiveM2Nut", "CoverCaptiveM2Nut_1", "CoverCaptiveM2Nut_3",
    ]
    try:
        obstacles = {name: document.getObject(name).Shape for name in names}
        pcb = document.getObject("PCBExactSuppliedOutlineAndMounts").Shape
        results = []
        for label in request:
            xmin, ymin, xmax, ymax = label["screen_bounds_xy_mm"]
            column = Part.makeBox(xmax-xmin, ymax-ymin, 20, App.Vector(xmin, ymin, 26.6001))
            footprint = Part.makeBox(xmax-xmin, ymax-ymin, .01, App.Vector(xmin, ymin, 26.59))
            intersections = {name: max(0, column.common(shape).Volume) for name, shape in obstacles.items()}
            outside = max(0, footprint.cut(pcb).Volume)
            results.append({"text": label["text"], "outside_actual_pcb_mm3": outside,
                            "sight_column_obstruction_mm3": intersections,
                            "clear": outside < 1e-5 and max(intersections.values()) < 1e-5})
        (work / "completed.json").write_text(json.dumps({
            "freecad_version": App.Version(), "opencascade_version": Part.OCC_VERSION,
            "request_sha256": hashlib.sha256((work / "request.json").read_bytes()).hexdigest(),
            "labels": results,
        }, indent=2))
    finally:
        App.closeDocument(document.Name)


def review(current_mechanical=False):
    sys.path.insert(0, str(ROOT / "tools"))
    import route_printed_bell as route
    route.verify_release()
    handle = os.add_dll_directory(str(route.CLI.parent))
    sys.path.append(str(route.CLI.parent / "Lib" / "site-packages"))
    import pcbnew as pcb
    route.prep.require(pcb.GetBuildVersion() == "10.0.6", "Expected KiCad10.0.6 glyph geometry")
    board_path = HERE / "handbell.kicad_pcb"
    before = route.sha(board_path)
    board = pcb.LoadBoard(str(board_path))
    marks = [n for n in board.GetDrawings() if isinstance(n, pcb.PCB_TEXT) and n.GetLayer() == pcb.B_SilkS]
    route.prep.require({n.GetText() for n in marks} == {s[0] for s in route.SERVICE_LABELS}, "Missing service labels")
    copper = list(board.GetTracks()) + [p for f in board.GetFootprints() for p in f.Pads()]
    copper = [p for p in copper if p.IsOnLayer(pcb.B_Cu)]
    labels = []
    for mark in marks:
        shape = mark.GetEffectiveTextShape()
        bounds = shape.BBox()
        raw = [pcb.ToMM(v)-100 for v in (bounds.GetLeft(), bounds.GetTop(), bounds.GetRight(), bounds.GetBottom())]
        screen = [raw[0]-.2, raw[1]-.2, raw[2]+.2, raw[3]+.2]
        conflicts = [p.m_Uuid.AsString() for p in copper if shape.Collide(p.GetEffectiveShape(pcb.B_Cu), pcb.FromMM(.25))]
        route.prep.require(mark.IsMirrored(), "Service label is not readable from B")
        route.prep.require(not conflicts, "Service label enters B copper clearance: "+mark.GetText())
        reservation = None
        if mark.GetText() in TEXT_RESERVATIONS:
            x, y, width, height = TEXT_RESERVATIONS[mark.GetText()]
            position = mark.GetPosition()
            route.prep.require(abs(pcb.ToMM(position.x)-100-x) < .000002 and
                               abs(pcb.ToMM(position.y)-100-y) < .000002, "Service label center moved")
            margins = [raw[0]-(x-width/2), raw[1]-(y-height/2),
                       (x+width/2)-raw[2], (y+height/2)-raw[3]]
            route.prep.require(min(margins) >= 0, "Actual glyph exceeds mechanical text reservation: "+mark.GetText())
            reservation = {"center_xy_mm": [x, y], "maximum_width_height_mm": [width, height],
                           "actual_glyph_width_height_mm": [raw[2]-raw[0], raw[3]-raw[1]],
                           "glyph_to_reservation_edge_margins_mm": margins}
        mount_distances = []
        for x, y in ((10, 15.7), (-10, -15.7)):
            distance = (max(screen[0]-x, 0, x-screen[2])**2 + max(screen[1]-y, 0, y-screen[3])**2)**.5
            route.prep.require(distance >= 3.2, "Service envelope enters M2 keepout: "+mark.GetText())
            mount_distances.append(distance-3.2)
        labels.append({"text": mark.GetText(), "glyph_bounds_xy_mm": raw, "screen_bounds_xy_mm": screen,
                       "mirrored_B": True, "B_copper_clearance_screen_mm": .25,
                       "B_copper_conflicts": conflicts, "mount_keepout_margins_mm": mount_distances,
                       "mechanical_text_reservation": reservation})
    labels.sort(key=lambda item: item["text"])
    if current_mechanical:
        checked = subprocess.run([sys.executable, str(ROOT / "tools" / "check_printed_bell.py")],
                                 cwd=ROOT, capture_output=True, text=True, timeout=120)
        route.prep.require(checked.returncode == 0,
                           "Current mechanical evidence is not valid: "+checked.stdout+checked.stderr)
        mechanical_paths = [MECHANICAL / name for name in (
            "printed-bell.FCStd", "artifact-manifest.json", "fit-report.json",
            "completion.json", "review-status.json")]
        mechanical_bindings = {str(p.relative_to(ROOT)): route.sha(p) for p in mechanical_paths}
        native = mechanical_paths[0].read_bytes()
        visibility_basis = {"current_mechanical_bindings_sha256": mechanical_bindings}
        expected_source = HERE
    else:
        native = visibility_native()
        visibility_basis = {"mechanical_visibility_commit": VISIBILITY_COMMIT,
                            "mechanical_visibility_git_path": VISIBILITY_GIT_PATH}
        expected_source = route.SOURCE
    embedded_inputs = {}
    with ZipFile(io.BytesIO(native)) as archive:
        tree = ET.fromstring(archive.read("Document.xml"))
        for key, filename in (("placement", "placement-manifest.json"), ("pcb", "handbell.kicad_pcb"),
                              ("schematic", "handbell.kicad_sch"), ("contact_interface", "battery-contact-interface.json")):
            item = tree.find(f".//ObjectData/Object[@name='Raw_{key}']/Properties/Property[@name='Text']/String")
            route.prep.require(item is not None, "Corrected model lacks embedded interface: "+key)
            digest = hashlib.sha256(base64.b64decode(item.attrib["value"], validate=True)).hexdigest()
            message = ("Current model is not bound to routed candidate: " if current_mechanical
                       else "Corrected model interface changed: ")
            route.prep.require(digest == route.sha(expected_source / filename), message+key)
            embedded_inputs[key] = digest
    freecad = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "FreeCAD 1.1" / "bin" / "FreeCADCmd.exe"
    with tempfile.TemporaryDirectory(prefix=".service-label-", dir=HERE / "reports") as directory:
        work = Path(directory)
        (work / "released.FCStd").write_bytes(native)
        (work / "request.json").write_text(json.dumps(labels, indent=2))
        bootstrap = (f"import runpy\nm=runpy.run_path({str(Path(__file__).resolve())!r})\n"
                     f"m['mechanical_screen'](m['Path']({str(work)!r}))\n")
        result = subprocess.run([str(freecad), "--user-cfg", str(work / "user.cfg"),
                                 "--system-cfg", str(work / "system.cfg")], input=bootstrap, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
        route.prep.require(result.returncode == 0 and (work / "completed.json").exists(),
                           "Fresh FreeCAD service screen absent: "+result.stdout)
        mechanical = json.loads((work / "completed.json").read_text())
        route.prep.require(mechanical["request_sha256"] == route.sha(work / "request.json"), "Stale service screen")
        route.prep.require(route.sha(work / "released.FCStd") == hashlib.sha256(native).hexdigest(),
                           "Read-only service screen modified released model")
    route.prep.require(all(item["clear"] for item in mechanical["labels"]),
                       "Service text obscured by capture: "+json.dumps(mechanical["labels"]))
    route.prep.require(before == route.sha(board_path), "Service screen changed native PCB")
    if current_mechanical:
        route.prep.require(mechanical_bindings == {str(p.relative_to(ROOT)): route.sha(p) for p in mechanical_paths},
                           "Current mechanical evidence changed during the service screen")
    report = {
        "scope": "Nominal CAD/glyph service-view screen, not readability, chemistry, reversal or safety qualification",
        "view": "Cartridge outside shell; cover and its screws removed; cell, cradle, contacts and retained hardware installed; look along -Z",
        "pcb_sha256": before, "tool_sha256": route.sha(__file__),
        "mechanical_release_commit": route.RELEASE_COMMIT,
        **visibility_basis,
        "mechanical_native_sha256": hashlib.sha256(native).hexdigest(),
        ("embedded_routed_inputs_sha256" if current_mechanical else "embedded_stage1_inputs_sha256"): embedded_inputs,
        "freecad_cli_sha256": route.sha(freecad),
        "kicad_version": pcb.GetBuildVersion(), "glyph_envelope_margin_mm": .2,
        "labels": labels, "mechanical": mechanical,
        "required_compartment_label": ["1S Li-ion 4.2V ONLY", "NO PRIMARY CR123A"],
        "gates": [
            ("Repeat after any PCB, label or mechanical change" if current_mechanical else
             "Parent must repeat visibility review after rebinding this corrected model to actual routed candidate"),
            "Print legibility and actual service-state visibility require physical review",
            "Use a visible compartment label if PCB guidance is obscured in any supported insertion workflow",
            "Charger cannot identify primary-cell chemistry; polarity marks do not prevent wrong-cell charging",
            "No live-cell, charging, reversal or safety approval",
        ],
    }
    name = "service-label-current-mechanical-review.json" if current_mechanical else "service-label-review.json"
    route.write(HERE / "reports" / name, report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current-mechanical", action="store_true",
                        help="Require the current completed model to embed this routed candidate; write a separate report.")
    review(current_mechanical=parser.parse_args().current_mechanical)
