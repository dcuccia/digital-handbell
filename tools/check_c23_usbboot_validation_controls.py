# SPDX-License-Identifier: MIT
"""Exercise native geometry bindings used by C23 USBBOOT candidate validation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def rectangle(pcb, left, top, right, bottom):
    result = pcb.SHAPE_POLY_SET()
    outline = result.NewOutline()
    for x, y in ((left, top), (right, top), (right, bottom), (left, bottom)):
        result.Append(x, y, outline)
    return result


def contained_after_inflation(pcb, piece, reference, amount):
    expanded = reference.CloneDropTriangulation()
    if amount:
        expanded.Inflate(
            amount,
            pcb.CORNER_STRATEGY_ROUND_ALL_CORNERS,
            1,
            True,
        )
    residual = piece.CloneDropTriangulation()
    residual.BooleanSubtract(expanded)
    return residual.IsEmpty()


def clearance_bracket(component, shape, maximum):
    if component.Collide(shape, 0):
        return 0, 0
    require(component.Collide(shape, maximum), "Clearance control maximum does not collide")
    low, high = 0, maximum
    while high - low > 1:
        middle = (low + high) // 2
        if component.Collide(shape, middle):
            high = middle
        else:
            low = middle
    return low, high


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--saved-drc", type=Path, required=True)
    parser.add_argument("--expected-drc-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    report = {"status": "FAILED", "controls": []}

    def passed(name, detail):
        report["controls"].append({"name": name, "passed": True, "detail": detail})

    try:
        require(args.saved_drc.is_file(), "Explicit saved DRC path does not exist")
        actual_drc_hash = sha(args.saved_drc)
        require(actual_drc_hash == args.expected_drc_sha256, "Explicit saved DRC hash differs")
        drc = json.loads(args.saved_drc.read_text(encoding="utf-8-sig"))
        require(isinstance(drc.get("unconnected_items"), list), "Saved DRC lacks unconnected_items")
        require(isinstance(drc.get("violations"), list), "Saved DRC lacks violations")
        passed("explicit_saved_DRC_binding", {
            "sha256": actual_drc_hash,
            "unconnected_item_count": len(drc["unconnected_items"]),
            "violation_count": len(drc["violations"]),
            "resolution": "Exact caller-provided path only; no fallback glob or directory search.",
        })

        native = Path(os.environ["LOCALAPPDATA"]) / r"Programs\KiCad\10.0\bin"
        dll_handle = os.add_dll_directory(str(native))
        sys.path.insert(0, str(native / "Lib/site-packages"))
        import pcbnew as pcb

        require(pcb.GetBuildVersion() == "10.0.6", "KiCad 10.0.6 required")
        iu_per_mm = pcb.FromMM(1.0)
        require(iu_per_mm == 1_000_000, "Runtime IU/mm differs")
        require(pcb.ToMM(iu_per_mm) == 1.0, "Runtime IU roundtrip differs")
        ten_nm_iu = pcb.FromMM(0.000010)
        require(ten_nm_iu == 10, "10 nm does not equal 10 IU")
        passed("runtime_unit_conversion", {
            "FromMM_1_0": iu_per_mm,
            "ToMM_roundtrip": pcb.ToMM(iu_per_mm),
            "FromMM_0_000010": ten_nm_iu,
            "interpretation": "1 IU = 1 nm on this KiCad runtime.",
        })

        reference = rectangle(pcb, 0, 0, 1000, 1000)
        within_10 = rectangle(pcb, 1000, 200, 1010, 800)
        beyond_10 = rectangle(pcb, 1000, 200, 1011, 800)
        require(contained_after_inflation(pcb, within_10, reference, 10),
                "10-IU positive containment control failed")
        require(not contained_after_inflation(pcb, beyond_10, reference, 10),
                ">10-IU negative containment control passed")
        require(not contained_after_inflation(pcb, within_10, reference, 9),
                "9-IU negative containment control passed")
        intersection = within_10.CloneDropTriangulation()
        intersection.BooleanIntersection(reference)
        difference = within_10.CloneDropTriangulation()
        difference.BooleanSubtract(reference)
        require(intersection.Area() == 0 and difference.Area() == within_10.Area(),
                "Boolean boundary controls differ")
        passed("native_offset_and_boolean_containment", {
            "positive_10_IU_contained": True,
            "same_piece_9_IU_not_contained": True,
            "11_IU_piece_not_contained_at_10_IU": True,
            "boundary_intersection_area_IU2": intersection.Area(),
            "boundary_difference_area_IU2": difference.Area(),
            "offset": {
                "corner_strategy": "CORNER_STRATEGY_ROUND_ALL_CORNERS",
                "max_error_IU": 1,
                "simplify": True,
            },
        })

        clearance_component = rectangle(
            pcb,
            pcb.FromMM(0.0),
            pcb.FromMM(0.0),
            pcb.FromMM(1.0),
            pcb.FromMM(1.0),
        )
        circle = pcb.SHAPE_CIRCLE(
            pcb.VECTOR2I(pcb.FromMM(1.3), pcb.FromMM(0.5)),
            pcb.FromMM(0.1),
        )
        require(not clearance_component.Collide(circle, pcb.FromMM(0.2) - 1),
                "0.20 mm boundary control collides one IU below")
        require(not clearance_component.Collide(circle, pcb.FromMM(0.2)),
                "0.20 mm boundary control rejects exact equality")
        require(clearance_component.Collide(circle, pcb.FromMM(0.2) + 1),
                "0.20 mm boundary control does not collide one IU inside")
        bracket_020 = clearance_bracket(clearance_component, circle, pcb.FromMM(0.3))
        require(bracket_020 == (pcb.FromMM(0.2), pcb.FromMM(0.2) + 1),
                "0.20 mm clearance bracket differs")

        private_circle = pcb.SHAPE_CIRCLE(
            pcb.VECTOR2I(pcb.FromMM(1.35), pcb.FromMM(0.5)),
            pcb.FromMM(0.1),
        )
        require(not clearance_component.Collide(private_circle, pcb.FromMM(0.25) - 1),
                "0.25 mm boundary control collides one IU below")
        require(not clearance_component.Collide(private_circle, pcb.FromMM(0.25)),
                "0.25 mm boundary control rejects exact equality")
        require(clearance_component.Collide(private_circle, pcb.FromMM(0.25) + 1),
                "0.25 mm boundary control does not collide one IU inside")
        bracket_025 = clearance_bracket(clearance_component, private_circle, pcb.FromMM(0.35))
        require(bracket_025 == (pcb.FromMM(0.25), pcb.FromMM(0.25) + 1),
                "0.25 mm clearance bracket differs")
        passed("native_clearance_boundary_semantics", {
            "foreign_0_20mm_collision_bracket_IU": list(bracket_020),
            "private_0_25mm_collision_bracket_IU": list(bracket_025),
            "acceptance_predicate": "No collision at exact required clearance; collision begins one IU inside.",
        })

        report["status"] = "PASSED"
        report["kicad_version"] = pcb.GetBuildVersion()
        report["new_native_bindings_exercised"] = [
            "pcb.FromMM", "pcb.ToMM", "SHAPE_POLY_SET.Inflate",
            "SHAPE_POLY_SET.BooleanSubtract", "SHAPE_POLY_SET.BooleanIntersection",
            "SHAPE_POLY_SET.Collide",
        ]
        report["untested_new_native_bindings"] = []
        dll_handle.close()
    except Exception as error:
        report["failure"] = {"type": type(error).__name__, "message": str(error)}

    report["elapsed_seconds"] = time.monotonic() - started
    report["tool_sha256"] = sha(__file__)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "report_sha256": sha(args.output),
        "failure": report.get("failure"),
    }, indent=2))
    if report["status"] != "PASSED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
