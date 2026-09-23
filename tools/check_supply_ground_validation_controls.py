# SPDX-License-Identifier: MIT
"""Isolated native-shape controls for the supply-ground read-only validator."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from validate_supply_ground_stitch import (
    circular_holes_violate_clearance, contact_metal_polygons, sha,
)


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--candidate-sha256", required=True)
    parser.add_argument("--interface", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    report = {"status": "FAILED", "candidate_sha256": sha(args.candidate),
              "design_files_written": False}
    try:
        require(report["candidate_sha256"] == args.candidate_sha256, "Candidate hash guard failed")
        native = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin"
        dll_handle = os.add_dll_directory(str(native))
        sys.path.insert(0, str(native / "Lib" / "site-packages"))
        import pcbnew as pcb
        require(pcb.GetBuildVersion() == "10.0.6", "KiCad 10.0.6 required")
        board = pcb.LoadBoard(str(args.candidate))
        clearance = pcb.FromMM(.2)
        radius = pcb.FromMM(.175)
        origin = pcb.VECTOR2I(0, 0)
        circle_cases = {
            "separated": circular_holes_violate_clearance(
                origin, radius, pcb.VECTOR2I(2 * radius + clearance + 1, 0), radius, clearance),
            "exact_required_clearance": circular_holes_violate_clearance(
                origin, radius, pcb.VECTOR2I(2 * radius + clearance, 0), radius, clearance),
            "one_IU_inside_required_clearance": circular_holes_violate_clearance(
                origin, radius, pcb.VECTOR2I(2 * radius + clearance - 1, 0), radius, clearance),
            "overlapping": circular_holes_violate_clearance(
                origin, radius, pcb.VECTOR2I(radius, 0), radius, clearance),
        }
        require(circle_cases == {
            "separated": False, "exact_required_clearance": False,
            "one_IU_inside_required_clearance": True, "overlapping": True,
        }, "Circular-hole signed-clearance controls failed")

        slotted = []
        for footprint in board.GetFootprints():
            for pad in footprint.Pads():
                drill = pad.GetDrillSize()
                if drill.x > 0 and drill.y > 0 and drill.x != drill.y:
                    slotted.append(pad)
        require(slotted, "Saved candidate has no native slotted pad witness")
        slot = slotted[0]
        require(hasattr(slot, "GetEffectiveHoleShape"), "Native effective-hole API unavailable")
        slot_shape = slot.GetEffectiveHoleShape()
        box = slot_shape.BBox()
        y = (box.GetTop() + box.GetBottom()) // 2
        slot_cases = {
            "overlap": slot_shape.Collide(pcb.SHAPE_CIRCLE(
                pcb.VECTOR2I((box.GetLeft() + box.GetRight()) // 2, y), radius), 0),
            "one_IU_inside_required_clearance": slot_shape.Collide(pcb.SHAPE_CIRCLE(
                pcb.VECTOR2I(box.GetRight() + radius + clearance - 2, y), radius), clearance - 1),
            "one_IU_outside_required_clearance": slot_shape.Collide(pcb.SHAPE_CIRCLE(
                pcb.VECTOR2I(box.GetRight() + radius + clearance, y), radius), clearance - 1),
        }
        report["raw_slot_cases"] = slot_cases
        require(slot_cases == {
            "overlap": True, "one_IU_inside_required_clearance": True,
            "one_IU_outside_required_clearance": False,
        }, "Native slot signed-clearance controls failed")

        interface = json.loads(args.interface.read_text(encoding="utf-8-sig"))
        contact = contact_metal_polygons(pcb, interface)[0]
        box = contact.BBox()
        y = (box.GetTop() + box.GetBottom()) // 2
        contact_cases = {
            "overlap": contact.Collide(pcb.SHAPE_CIRCLE(
                pcb.VECTOR2I((box.GetLeft() + box.GetRight()) // 2, y), radius), 0),
            "one_IU_inside_required_clearance": contact.Collide(pcb.SHAPE_CIRCLE(
                pcb.VECTOR2I(box.GetRight() + radius + clearance - 2, y), radius), clearance - 1),
            "one_IU_outside_required_clearance": contact.Collide(pcb.SHAPE_CIRCLE(
                pcb.VECTOR2I(box.GetRight() + radius + clearance, y), radius), clearance - 1),
        }
        report["raw_contact_cases"] = contact_cases
        require(contact_cases == {
            "overlap": True, "one_IU_inside_required_clearance": True,
            "one_IU_outside_required_clearance": False,
        }, "Contact rectangle signed-clearance controls failed")
        report.update({
            "status": "PASSED",
            "kicad_version": pcb.GetBuildVersion(),
            "circle_controls": circle_cases,
            "slot_controls": {
                "pad_uuid": slot.m_Uuid.AsString(),
                "reference": slot.GetParentFootprint().GetReference(),
                "number": slot.GetNumber(),
                "drill_size_mm": [pcb.ToMM(slot.GetDrillSize().x), pcb.ToMM(slot.GetDrillSize().y)],
                "native_shape_class": type(slot_shape).__name__,
                "cases": slot_cases,
            },
            "contact_rectangle_controls": contact_cases,
            "methods": {
                "circular_holes": "Exact integer squared-center-distance; equality at minimum clearance passes.",
                "slotted_holes": "Saved-pad GetEffectiveHoleShape().Collide(candidate_circle, clearance-1).",
                "contact_metal": "Native SHAPE_POLY_SET.Collide(candidate_circle, clearance-1).",
            },
        })
        dll_handle.close()
    except Exception as error:
        report["failure"] = {"type": type(error).__name__, "message": str(error)}
    report["elapsed_seconds"] = time.monotonic() - started
    report["tool_sha256"] = sha(__file__)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report_sha256": sha(args.output),
                      "failure": report.get("failure")}, indent=2))
    if report["status"] != "PASSED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
