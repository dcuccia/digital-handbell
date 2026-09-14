#!/usr/bin/env python3
"""Check exact September 13 artifact binding, not live-cell/strength safety."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "mechanical" / "studies" / "2026-09-13-printed-bell"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    out = args.output or (STUDY / "development" if args.development else STUDY)
    report = json.loads((out / "fit-report.json").read_text(encoding="utf-8"))
    manifest = json.loads((out / "artifact-manifest.json").read_text(encoding="utf-8"))
    completion = json.loads((out / "completion.json").read_text(encoding="utf-8"))
    status = json.loads((out / "review-status.json").read_text(encoding="utf-8"))
    assert completion["token"] == status["token"], "Incomplete build"
    assert sha(out / "artifact-manifest.json") == completion["artifact_manifest_sha256"]
    assert completion["input_hashes"] == manifest["input_hashes"] == report["input"]["sha256"]
    expected = "DEVELOPMENT_FROZEN_MIXED_FACE_NOT_FINAL" if args.development else "EXACT_ALL_FRONT_ENGINEERING_REVIEW"
    assert status["state"] == report["status"] == expected, "Development is not a final all-front assembly"
    for name, record in manifest["artifacts"].items():
        assert sha(out / name) == record["sha256"], "Changed output: " + name
        if name.endswith(".step"):
            assert record["brep_roundtrip_verified_not_only_bounds"], name
            assert record["maximum_per_solid_symmetric_difference_mm3"] < 1e-4, name
        if name.endswith(".stl"):
            assert record["closed_manifold"] and not record["self_intersections"], name
            assert record["connected_components"] == 1, name
    for key, name in report["input"]["paths"].items():
        assert not Path(name).is_absolute(), "Public input paths must be repository-relative"
        assert sha(ROOT / name) == report["input"]["sha256"][key], "Changed source: " + key
    with ZipFile(out / "printed-bell.FCStd") as z:
        assert z.testzip() is None
        tree = ET.fromstring(z.read("Document.xml"))
        display = ET.fromstring(z.read("GuiDocument.xml"))
        names = {e.attrib.get("name") for e in tree.findall("./Objects/Object")}
        for name in ("OnePiecePrintedBellShell", "BlackKeyedHandleCaptiveMetalNut",
                     "FlushGrilleCarrierAndConcealedPortBezel", "RetainedInsulatingCellCradle",
                     "RetainedRemovableCellCover", "ContactMetal_BT1", "ContactMetal_BT2"):
            assert name in names, name
        assert len(list(display.iter("ViewProvider"))) > 80
        for key, name in report["input"]["paths"].items():
            if key in ("frozen_t8_native", "frozen_t8_report"):
                continue
            saved = tree.find(f".//ObjectData/Object[@name='Raw_{key}']/Properties/Property[@name='Text']/String")
            assert saved is not None and base64.b64decode(saved.attrib["value"]) == (ROOT / name).read_bytes(), key
    assert report["dimensions"]["maximum_shell_diameter_mm"] <= 75.5
    assert report["dimensions"]["body_height_mm"] <= 56.3
    assert report["dimensions"]["handle_above_crown_mm"] <= 85.5
    assert all(p["solid_count"] == 1 and p["valid"] for p in report["structural_parts"].values())
    assert report["contact_retention"]["actual_under_cell_section_mm"] >= 1.08-1e-5
    assert max(report["contact_retention"]["cover_service_channels"]["actual_wall_witness_missing_volumes_mm3"]) < 1e-5
    assert report["handle_joint"]["bearing_witness_outside_actual_shell_mm3"] < 1e-5
    joint = report["handle_joint"]
    assert joint["minimum_tip_to_blind_end_gap_mm"] >= 1.25-1e-5
    assert joint["minimum_tip_past_maximum_height_nut_mm"] >= 3-1e-5
    for case in joint["supplier_tolerance_screen"].values():
        assert max(case["installed_overlap_mm3"].values()) < 1e-5
        assert case["screw_to_cell"]["distance_mm"] > 0 and case["screw_to_cover"]["distance_mm"] > 0
        assert all(max(p["overlaps_mm3"].values()) < 1e-5 for p in case["insertion_empty_shell"])
    assert report["contact_retention"]["all_six_half_mm_displacements_meet_plastic"]
    shell_joints = report["shell_cartridge_joints"]
    assert shell_joints["exterior_stock_lower_bound_mm"] >= 1
    assert shell_joints["missing_authored_cosmetic_side_skin_except_usb_mm2"] < 1e-4
    assert max(shell_joints["roof_witness_missing_mm3"]) < 1e-5
    assert max(shell_joints["bearing_floor_witness_missing_mm3"]) < 1e-5
    assert shell_joints["expanded_lower_cavity_outside_outer_envelope_mm3"] < 1e-5
    assert all(p["positive_offset_mm"] >= 1 and
               p["expanded_void_outside_outer_envelope_mm3"] < 1e-5 and
               p["expanded_void_intersection_intentional_usb_opening_mm3"] < 1e-5
               for p in shell_joints["primitive_positive_offset_containment"])
    assert all(v["recommended"] is not None and v["recommended"]["clear_with_cover_removed_cell_installed"]
               for v in report["back_silk_visibility"]["assessments"].values()), "No unobstructed B-silk recommendation for at least one label"
    assert report["pcba_stl_scope"]["omitted_only_from_inert_stl"] == ["BT1", "BT2"]
    skin = report["usb"]["front_skin"]
    assert skin["full_frame_witness_missing_mm3"] < 1e-5, "USB front frame material missing"
    assert skin["extra_effective_opening_area_mm2"] < 1e-5, "USB actual opening exceeds declared aperture"
    assert skin["blocked_intended_opening_area_mm2"] < 1e-5, "USB intended aperture obstructed"
    assert abs(skin["actual_front_face_open_area_mm2"]-9.2*3.1) < 1e-5
    assert skin["pcb_edge_front_mask_missing_mm3"] < 1e-5, "PCB edge not physically concealed"
    assert skin["all_pcba_pure_z_loading_plane_separation_mm"] >= .2-1e-5
    assert skin["whole_carrier_outside_D70_mm3"] < 1e-5
    for name in ("skin_to_actual_pcb", "skin_to_source_usb", "skin_to_shell"):
        assert skin[name]["intersection_mm3"] < 1e-5 and skin[name]["distance_mm"] > 0, name
    assert not report["material_intersections"], json.dumps(report["material_intersections"], indent=2)
    paths = report["assembly_paths"]
    for name in ("cartridge_withdrawal_minus_z", "unselected_usb_plug_approach",
                 "handle_screw_washer_insertion_empty_shell", "yoke_over_magnet_before_pcba",
                 "pcba_lowering_into_open_top_carrier", "cover_removal_with_cell_still_captured_by_cradle"):
        assert all(max(p["overlaps_mm3"].values()) < 1e-5 for p in paths[name]), name
    assert max(paths["handle_tool_empty_shell"].values()) < 1e-5
    assert all(p["overlap_mm3"] < 1e-5 for p in paths["handle_nut_side_load"])
    assert all(p["overlap_mm3"] < 1e-5 for group in paths["shell_nut_radial_insertion_before_cartridge"] for p in group)
    assert all(p["body_overlap_mm3"] < 1e-5 for p in paths["speaker_load_before_yoke"])
    assert all(max(v.values()) < 1e-5 for v in paths["retained_m2_straight_tool_access"].values())
    assert all(max(p["overlaps_mm3"].values()) < 1e-5
               for samples in paths["front_shell_screw_installation"].values() for p in samples)
    assert all(max(v.values()) < 1e-5 for v in paths["front_shell_screw_tool_access"].values())
    assert max(paths["unselected_usb_nose_continuous_straight_sweep"]["overlaps_mm3"].values()) < 1e-5
    if not args.development:
        assert report["routing_interface"]["mechanical_freeze_recommended"]
    print(json.dumps({"artifact_integrity": "PASS", "exact_current_input_binding": "PASS",
                      "status": report["status"], "nominal_geometry": "PASS", "qualified": False,
                      "dimensions": report["dimensions"]}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, ValueError, KeyError, OSError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        sys.exit(1)
