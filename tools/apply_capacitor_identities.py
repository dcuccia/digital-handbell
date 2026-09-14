# SPDX-License-Identifier: MIT
"""Apply selected non-boost capacitor identities; never change values or geometry."""
import hashlib
import json
from pathlib import Path
import subprocess

from kicad_sexpr import load
from native_identity_fields import apply_manifest_fields, prepare_fields
from route_clock_local import PACKAGE, ROOT

INPUT_COMMIT = "b9aa839"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report_path = PACKAGE / "reports" / "capacitor-identities.json"
    if report_path.exists():
        raise ValueError("Existing capacitor identity report refused")
    inputs = {}
    for name in ("handbell.kicad_pcb", "handbell.kicad_sch", "placement-manifest.json"):
        git_path = (PACKAGE / name).relative_to(ROOT).as_posix()
        raw = subprocess.run(["git", "show", INPUT_COMMIT+":"+git_path], cwd=ROOT,
                             capture_output=True, check=True, timeout=10).stdout
        inputs[name] = hashlib.sha256(raw).hexdigest()
        if sha(PACKAGE / name) != inputs[name]:
            raise ValueError("Pinned input changed: "+name)
    source = ROOT / "hardware" / "handbell" / "parts" / "standard-passive-candidates.json"
    register = json.loads(source.read_text(encoding="utf-8"))
    specifications = {}
    for part in register["parts"]:
        profile = register["profiles"][part["profile"]]
        if profile["kind"] != "capacitor":
            continue
        for ref in part["references"]:
            if ref in specifications:
                raise ValueError("Duplicate capacitor selection: "+ref)
            footprint = ("Clock:GRM1555C1H150JA01D" if ref in ("C2", "C3") else
                         "Adafruit Feather RP2040 Prop-Maker-import-fps:" +
                         {"0805": "0805-NO", "0402": "_0402NO"}[profile["package_imperial"]])
            specifications[ref] = {
                "expected_values": [part["selected_value"]] if "selected_value" in part else part["source_values"],
                "expected_footprints": [footprint],
                "properties": {"MPN": part["mpn"], "Manufacturer": profile["manufacturer"],
                               "Datasheet": part["datasheet_url"]},
            }
    if len(specifications) != 26 or {"C26", "C27", "C28"} & specifications.keys():
        raise ValueError("Non-boost capacitor scope changed")
    outputs, evidence = {}, {}
    for name, kind in (("handbell.kicad_pcb", "footprint"), ("handbell.kicad_sch", "symbol")):
        text, tree = load(PACKAGE / name)
        outputs[name], evidence[name] = prepare_fields(text, tree, kind, specifications)
    mf = PACKAGE / "placement-manifest.json"
    manifest = json.loads(mf.read_text(encoding="utf-8"))
    apply_manifest_fields(manifest, specifications)
    if any(sha(PACKAGE / name) != digest for name, digest in inputs.items()):
        raise ValueError("Inputs changed during operation")
    for name, text in outputs.items():
        (PACKAGE / name).write_bytes(text.encode("utf-8"))
    manifest.update(generated_pcb_sha256=sha(PACKAGE / "handbell.kicad_pcb"),
                    schematic_sha256=sha(PACKAGE / "handbell.kicad_sch"),
                    current_stage_report="reports/capacitor-identities.json")
    mf.write_bytes((json.dumps(manifest, indent=2)+"\n").encode("utf-8"))
    details = evidence["handbell.kicad_pcb"]
    report = {
        "input_commit": INPUT_COMMIT, "input_sha256": inputs,
        "output_pcb_sha256": sha(PACKAGE / "handbell.kicad_pcb"),
        "output_schematic_sha256": sha(PACKAGE / "handbell.kicad_sch"),
        "placement_manifest_sha256": sha(mf), "generator_sha256": sha(Path(__file__)),
        "shared_editor_sha256": sha(ROOT / "tools" / "native_identity_fields.py"),
        "selection_register_sha256": sha(source), "references": details,
        "previously_blank_mpn_count": sum(not d["previous_mpn"] for d in details.values()),
        "existing_matching_mpn_count": sum(bool(d["previous_mpn"]) for d in details.values()),
        "scope": "26 non-boost capacitor identities only; no values, ratings, footprints, poses, nets or copper changed. Preserve the already-applied C2/C3 15pF revision.",
        "remaining_gates": register["remaining_gates"] + [
            "C1/C4/C5/C19/C20 10uF land/paste treatment in power-component-candidates remains unapplied.",
            "No effective-capacitance, startup/clock-drive, thermal or supplier qualification is implied.",
            "C26-C28, inductor, ferrites and other selected devices remain separate items."
        ],
    }
    report_path.write_bytes((json.dumps(report, indent=2)+"\n").encode("utf-8"))
    print(json.dumps({"applied": len(details), "new_mpn": report["previously_blank_mpn_count"],
                      "confirmed_mpn": report["existing_matching_mpn_count"]}, indent=2))


if __name__ == "__main__":
    main()
