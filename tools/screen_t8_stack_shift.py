#!/usr/bin/env python3
"""Bounded original T8 whole-stack/guard screen, not an electrical placement edit."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "mechanical" / "studies" / "2026-09-11-t8-cartridge"
OUT = STUDY / "alternatives" / "whole-stack-screen"
BASELINE = STUDY / "alternatives" / "baseline-fixed-stack"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def run():
    import FreeCAD as App
    import Part
    V = App.Vector
    interface_path = BASELINE / "contact_interface-snapshot.json"
    manifest_path = BASELINE / "placement-snapshot.json"
    interface = json.loads(interface_path.read_text(encoding="utf-8-sig"))
    doc = App.openDocument(str(BASELINE / "t8-cartridge.FCStd"))
    shell = doc.getObject("WorkingShellWithProposedOpenSlot").Shape
    cell = doc.getObject("T8FullUnclippedCellCanEnvelope").Shape
    contacts = [doc.getObject("ContactMetal_"+ref).Shape for ref in ("BT1", "BT2")]
    p = interface["right_contact_original_primitives"]
    cz = interface["cell_nominal"]["center_mm"][2]
    rad = interface["cell_nominal"]["diameter_mm"]/2
    length = interface["cell_nominal"]["total_length_mm"]

    def box(lo, size):
        return Part.makeBox(*size, V(*lo))

    def shifted(s, distance):
        s = s.copy()
        s.translate(V(0, 0, -distance))
        return s

    def union(parts):
        s = parts[0].multiFuse(parts[1:]).removeSplitter()
        if not s.isValid() or len(s.Solids) != 1:
            raise RuntimeError("Invalid/disconnected conservative guard-envelope stock")
        return s

    def pair(s):
        return {"shell_intersection_mm3": max(0, s.common(shell).Volume),
                "shell_distance_mm": s.distToShape(shell)[0]}

    report = {"generated_utc": datetime.now(timezone.utc).isoformat(), "units": "mm",
              "input": {"manifest_sha256": digest(manifest_path), "interface_sha256": digest(interface_path),
                        "native_sha256": digest(BASELINE / "t8-cartridge.FCStd"), "script_sha256": digest(Path(__file__)),
                        "source": "Frozen baseline-fixed-stack snapshot, not mutable current output"},
              "method": "Test requested1.5/2 shifts, then two quarter-mm brackets from analytic limiting upper-contact corner. Not a blind optimizer. Whole stack translates rigidly; no cell/metal/relative-gap changes.",
              "guard_clearance_assumption_mm": .10, "desired_nominal_guard_shell_margin_mm": .25,
              "cases": [], "qualifications": "No contact-force, positive-ear/can insulation, print-tolerance or live-cell approval."}
    slope = -6.94/26.85
    top = p["spring_xz_polyline"][-1]
    corner_radius = math.hypot(top[0]+p["spring_thickness"], p["spring_y_width"]/2)
    cavity_radius = 25+slope*(top[1]-14.9)
    for wall in (1.0, 1.25):
        clearance = .10
        a = wall+clearance
        pieces = [Part.makeCylinder(rad+a, length+2*a, V(-length/2-a, 0, cz), V(1, 0, 0))]
        right = []
        for b in p["base_tabs"]+[p["under_cell_base"]]:
            stock = box([b["x_min"], -b["y_width"]/2, b["z_min"]],
                        [b["x_max"]-b["x_min"], b["y_width"], b["thickness"]])
            right.append(stock.makeOffsetShape(a, .001, fill=False, join=0))
        for (x1, z1), (x2, z2) in zip(p["spring_xz_polyline"], p["spring_xz_polyline"][1:]):
            stock = box([min(x1, x2), -p["spring_y_width"]/2, min(z1, z2)],
                        [abs(x2-x1)+p["spring_thickness"], p["spring_y_width"], abs(z2-z1)])
            right.append(stock.makeOffsetShape(a, .001, fill=False, join=0))
        ears = p["ears"]
        right.append(Part.makeCylinder(ears["inner_radius"]+ears["thickness"]+a,
                                        ears["axial_length"]+2*a, V(ears["x_min"]-a, 0, cz), V(1, 0, 0)))
        for s in right:
            pieces.append(s)
            mirrored = s.copy()
            mirrored.rotate(V(), V(0, 0, 1), 180)
            pieces.append(mirrored)
        envelope = union(pieces)
        required = ((a+.25)*math.sqrt(1+slope*slope) - (cavity_radius-corner_radius))/(-slope)
        candidate = math.ceil(required*4)/4
        report.setdefault("analytic_brackets", []).append({"wall_mm": wall, "limiting_corner_radius_mm": corner_radius,
                                                           "analytic_shift_for_margin_mm": required,
                                                           "quarter_mm_candidate": candidate})
        for shift in (1.5, 2.0, candidate-.25, candidate):
            case = {"whole_stack_mouthward_shift_mm": shift, "plastic_wall_mm": wall,
                    "cell": pair(shifted(cell, shift)),
                    "contacts": [pair(shifted(s, shift)) for s in contacts],
                    "complete_conservative_guard_stock": pair(shifted(envelope, shift))}
            report["cases"].append(case)
            print(json.dumps(case), flush=True)
        envelope.exportBrep(str(OUT / f"guard-stock-wall-{wall:g}.brep"))
    write(OUT / "stack-shift-fit-report.json", report)
    App.closeDocument(doc.Name)
    write(OUT / "complete.json", {"token": sys.argv[-1], "report_sha256": digest(OUT / "stack-shift-fit-report.json")})


def launch():
    OUT.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    script = str(Path(__file__).resolve())
    command = [str(Path.home() / "AppData" / "Local" / "Programs" / "FreeCAD 1.1" / "bin" / "FreeCADCmd.exe"),
               "--user-cfg", str(OUT / "user.cfg"), "--system-cfg", str(OUT / "system.cfg")]
    bootstrap = f"import runpy,sys\nsys.argv={[script, '--inside-freecad', token]!r}\nrunpy.run_path({script!r},run_name='__main__')\n"
    result = subprocess.run(command, input=bootstrap, text=True, encoding="utf-8", errors="replace",
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
    (OUT / "screen.log").write_text(result.stdout, encoding="utf-8")
    marker = OUT / "complete.json"
    if result.returncode or not marker.exists() or json.loads(marker.read_text())["token"] != token:
        print(result.stdout)
        raise RuntimeError("Stack shift screen did not finish")
    print((OUT / "stack-shift-fit-report.json").read_text())
    for name in ("user.cfg", "system.cfg"):
        (OUT / name).unlink(missing_ok=True)


if __name__ == "__main__":
    run() if "--inside-freecad" in sys.argv else launch()
