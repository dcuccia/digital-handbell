#!/usr/bin/env python3
"""Verify T8 mechanical artifacts and exact current input binding, not safety."""

import base64
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "mechanical" / "studies" / "2026-09-11-t8-cartridge"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report = json.loads((STUDY / "fit-report.json").read_text(encoding="utf-8"))
    inventory = json.loads((STUDY / "artifact-manifest.json").read_text(encoding="utf-8"))
    completion = json.loads((STUDY / "completion.json").read_text(encoding="utf-8"))
    status = json.loads((STUDY / "review-status.json").read_text(encoding="utf-8"))
    assert digest(STUDY / "artifact-manifest.json") == completion["artifact_manifest_sha256"], "Artifact manifest changed"
    assert completion["token"] == status["completion_token"], "Incomplete generation"
    assert completion["input_hashes"] == inventory["input_hashes"] == report["input"]["sha256"], "Input hashes disagree"
    for name, record in inventory["artifacts"].items():
        assert digest(STUDY / name) == record["sha256"], "Changed output: " + name
        if name.endswith(".step"):
            assert record["brep_roundtrip_verified_not_only_bounds"], name
            assert record["maximum_per_solid_symmetric_difference_mm3"] < 1e-4, name
        if name.endswith(".stl"):
            assert name.startswith("INERT-"), name
            assert record["closed_manifold"] and not record["self_intersections"], name
    for key, path in report["input"]["paths"].items():
        assert digest(Path(path)) == report["input"]["sha256"][key], "Current source changed: " + key
    for key in ("placement", "measurements", "contact_interface"):
        original = Path(report["input"]["paths"][key]).read_bytes()
        assert (STUDY / (key+"-snapshot.json")).read_bytes() == original, "Snapshot not exact raw bytes"
    placement_path = Path(report["input"]["paths"]["placement"])
    placement = json.loads(placement_path.read_text(encoding="utf-8-sig"))
    for filename, key in (("handbell.kicad_pcb", "generated_pcb_sha256"),
                           ("handbell.kicad_sch", "schematic_sha256")):
        assert digest(placement_path.parent / filename) == placement[key], "Actual electrical source hash mismatch: " + filename
    native = STUDY / "t8-cartridge.FCStd"
    with ZipFile(native) as z:
        assert z.testzip() is None, "Native ZIP member CRC failure"
        document = ET.fromstring(z.read("Document.xml"))
        display = ET.fromstring(z.read("GuiDocument.xml"))
        names = {e.attrib.get("name") for e in document.iter("Object")}
        for required in ("Parameters", "InputProvenance", "Assumptions", "PCBSubstrateExactInterface",
                         "LoadBearingInsulatingBatteryCradle", "RemovableBatteryCaptureCover",
                         "WorkingShellWithProposedOpenSlot", "T8FullUnclippedCellCanEnvelope"):
            assert required in names, "Missing native object: " + required
        providers = {e.attrib["name"]: e for e in display.iter("ViewProvider")}
        shell = providers["WorkingShellWithProposedOpenSlot"]
        assert any(p.attrib.get("name") == "Transparency" for p in shell.iter("Property"))
        for key in report["input"]["paths"]:
            assert "Raw_"+key in names, "Missing embedded source: " + key
            saved = document.find(f".//ObjectData/Object[@name='Raw_{key}']/Properties/Property[@name='Text']/String")
            assert saved is not None, "Missing native raw source value: " + key
            assert base64.b64decode(saved.attrib["value"]) == Path(report["input"]["paths"][key]).read_bytes(), "Native source bytes changed: " + key
    assert report["artifacts"]["t8-cartridge.FCStd"]["raw_source_bytes_verified"]
    assert report["summary"]["primary_printed_pieces"] == 4
    assert report["summary"]["nominal_geometry_fit_clear"], "Nominal shifted geometry still has an open material/guard fit"
    assert report["summary"]["nominal_guard_shell_margin_mm"] >= .25-1e-6, "Guard margin below chosen target"
    stock = report["insulation_screens"]["complete_rounded_contact_guard_stock"]
    assert stock["closed_stock_wall_lower_bound_mm"] >= report["dimensions"]["plastic_proud_target_mm"]-1e-6
    assert stock["global_void_outside_proved_pocket_union_mm3"] <= 1e-6
    assert all(w["inner_outside_own_stock_mm3"] <= 1e-6 and w["dilated_pocket_outside_own_stock_mm3"] <= 1e-6
               and w["stock_outside_global_stock_mm3"] <= 1e-6
               for w in stock["wall_bound_witnesses"])
    floor = report["insulation_screens"]["under_cell_base_section"]
    assert floor["actual_cradle_material_on_section_mm"] >= report["dimensions"]["plastic_proud_target_mm"]-1e-6
    for samples in report["assembly_paths"]["shell_nut_loading"]["samples"].values():
        assert all(p[key]["intersection_mm3"] <= 1e-6 for p in samples for key in ("body", "speaker"))
    assert report["summary"]["explicit_contact_objects"] == 2
    spacing = report["speaker_pcb_spacing_sensitivity"]
    assert [c["pcb_mouthward_reduction_mm"] for c in spacing["cases"]] == [0.5, 1.0]
    assert not spacing["applied_to_released_geometry"]
    assert all(c["speaker_fixed"] and c["component_xy_and_heights_unchanged"] for c in spacing["cases"])
    contact_checks = report["contact_geometry_contract_checks"]
    assert contact_checks["spring_segment_coordinate_checks_passed"]
    assert all(v <= 1e-6 for v in contact_checks["cell_material_intersection_mm3"].values()), "Contact thickness penetrates cell"
    assert not (STUDY / "INERT-populated-t8-pcba.stl").exists(), "Obsolete full-contact mesh must not be released"
    dummy = report["pcba_inert_print_scope"]
    assert dummy["full_contacts_retained_in_native_and_step"]
    assert dummy["omitted_only_from_inert_dummy"] == ["BT1", "BT2"]
    assert report["artifacts"][dummy["released_stl"]]["connected_components"] == 1
    assert not report["summary"]["routing_approved"]
    print(json.dumps({"artifact_integrity": "PASS", "current_exact_input_binding": "PASS",
                      "qualified": False, "open_fit_findings": report["summary"]}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, KeyError, OSError, ValueError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        sys.exit(1)
