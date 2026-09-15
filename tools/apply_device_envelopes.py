# SPDX-License-Identifier: MIT
"""Apply six reviewed conservative device envelopes; never move or route parts."""
import copy
import hashlib
import json
from pathlib import Path

import check_printed_bell_power_rework as check
from route_clock_local import PACKAGE, ROOT

REFERENCES = {"D3", "D4", "Q1", "Q2", "Q4", "U3"}
BASE = "f6a9d31192c7e59c4b81b7bcb281e23fd06cdc201e8a7a1f180ae7a8f860e3e4"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report_path = PACKAGE / "reports" / "device-envelopes.json"
    manifest_path = PACKAGE / "placement-manifest.json"
    if report_path.exists() or sha(PACKAGE / "handbell.kicad_pcb") != BASE:
        raise ValueError("Require the pinned power-land checkpoint and no existing envelope report")
    baseline = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = copy.deepcopy(baseline)
    register_path = ROOT / "hardware" / "handbell" / "parts" / "device-component-candidates.json"
    register = json.loads(register_path.read_text(encoding="utf-8"))
    selected = {}
    for group in register["groups"]:
        for ref in REFERENCES.intersection(group["references"]):
            dimensions = (group.get("proposed_proxy_minimum_local_xyz_mm")
                          or group.get("proposed_flash_screen_proxy_minimum_local_xyz_mm")
                          or group["proposed_flash_screen_proxy_minimum_by_reference"][ref])
            selected[ref] = (group, dimensions)
    if selected.keys() != REFERENCES:
        raise ValueError("Device envelope register does not cover the six references")
    changes = {}
    for component in manifest["components"]:
        ref = component["reference"]
        if ref not in selected:
            continue
        group, dimensions = selected[ref]
        old = copy.deepcopy(component)
        prior = group["current_proxy"][ref]
        for key, minimum in zip(("width_mm", "depth_mm", "height_mm"), dimensions, strict=True):
            if abs(component[key] - prior[key]) > 1e-6 or minimum < component[key] - 1e-6:
                raise ValueError("Unexpected or shrinking envelope: " + ref)
            component[key] = max(component[key], minimum)
        if component["side"] != "F" or component["z_max_mm"] != manifest["board"]["front_z_mm"]:
            raise ValueError("Unexpected seating plane: " + ref)
        component["z_min_mm"] = component["z_max_mm"] - component["height_mm"]
        component["height_source"] = "Documented conservative manufacturer-based screen; not a measured mounted height. See reports/device-envelopes.json."
        changes[ref] = {"before": old, "after": copy.deepcopy(component),
                        "evidence_ids": group["evidence_ids"]}
    errors = []
    screen = check.placement_proxy_screen(check.generator(), set(), errors,
                                         baseline=baseline, manifest=manifest, resized=REFERENCES)
    if errors:
        raise ValueError("Envelope screen requires a separate local repair: " + json.dumps(errors)
                         + "; results=" + json.dumps(screen))
    report = {
        "input_commit": "f4c260b", "pcb_sha256": BASE,
        "input_manifest_sha256": sha(manifest_path), "register_sha256": sha(register_path),
        "generator_sha256": sha(Path(__file__)), "screen_helper_sha256": sha(Path(check.__file__)),
        "changes": changes, "screen": screen, "component_moves": [],
        "native_design_files_changed": False,
        "scope": "Six conservative envelope enlargements only; retain current centers, rotations and native-to-proxy offsets, including the already moved Q1.",
        "remaining": "Remaining land/paste dispositions, complete CAD/bezel rebind and physical/supplier qualification. Conservative boxes are not qualified parts.",
    }
    manifest.update(current_stage_report="reports/device-envelopes.json", mechanical_rebind_required=True)
    manifest_path.write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    report["output_manifest_sha256"] = sha(manifest_path)
    report_path.write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"references": sorted(changes), "new_overlap_pairs": screen["new_proxy_overlap_pairs"],
                      "native_design_files_changed": False}))


if __name__ == "__main__":
    main()
