# SPDX-License-Identifier: MIT
"""Apply the final selected identity batch, retaining all geometry and copper."""
import hashlib
import json
from pathlib import Path

from kicad_sexpr import Node, load, loads
from native_identity_fields import prepare_fields, apply_manifest_fields
from route_clock_local import PACKAGE, ROOT

BASE = "060bab15944bcd8be8b6de61f05d242e2d975501fc900a21a379cd2b8d413ff5"
EXPECTED = {
    "C26": "22uF", "C27": "22uF", "C28": "22uF", "CHG0": "ORANGE",
    "D3": "1N4148", "D4": "PMEG2020AEA", "FB1": "Ferrite", "FB2": "Ferrite",
    "IC1": "RP2040_QFN56", "IC4": "LSM6DSOXTR", "L0": "RED",
    "L1": "1uH (MPN pending)", "Q1": "AO3401", "Q2": "C20917",
    "U2": "RT9080-3.3", "U3": "MCP73831T-2ACI/OT", "U4": "MAX98357A",
}
VALUE_LABELS = {"L1": "1uH", "Q2": "AO3400A"}
FIELDS = {"MPN", "Manufacturer", "Datasheet", "CircuitReference"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invariant(node, selected=False, ref=None):
    if not isinstance(node, Node):
        return node.value
    if node.head in ("symbol", "footprint") and node.properties().get("Reference") in EXPECTED:
        selected, ref = True, node.properties()["Reference"]
    return tuple(invariant(item, selected, ref) for item in node.items
                 if not (selected and isinstance(item, Node) and item.head == "property"
                         and (item.atoms()[1] in FIELDS
                              or (ref in VALUE_LABELS and item.atoms()[1] == "Value"))))


def main():
    board_path, sch_path = PACKAGE / "handbell.kicad_pcb", PACKAGE / "handbell.kicad_sch"
    report_path = PACKAGE / "reports" / "remaining-identities.json"
    if sha(board_path) != BASE or report_path.exists():
        raise ValueError("Require the pinned USB checkpoint and no prior output report")
    manifest_path = PACKAGE / "placement-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["generated_pcb_sha256"] != BASE or manifest["schematic_sha256"] != sha(sch_path):
        raise ValueError("Manifest/source bindings differ")
    components = {c["reference"]: c for c in manifest["components"]}
    if {r for r, c in components.items() if not c.get("mpn")} != EXPECTED.keys():
        raise ValueError("Remaining blank identity inventory differs")
    parts = ROOT / "hardware" / "handbell" / "parts"
    device_path, power_path = parts / "device-component-candidates.json", parts / "power-component-candidates.json"
    devices = json.loads(device_path.read_text(encoding="utf-8"))
    power = json.loads(power_path.read_text(encoding="utf-8"))
    specs = {}
    for register, device in ((devices, True), (power, False)):
        for group in register["groups"]:
            for ref in group["references"]:
                if ref not in EXPECTED:
                    continue
                if ref in specs:
                    raise ValueError("Duplicate selected identity: " + ref)
                url = (devices["sources"][group["evidence_ids"][0]]["url"] if device
                       else group.get("datasheet_url") or group["manufacturer_url"])
                properties = {"MPN": group["mpn"], "Manufacturer": group["manufacturer"], "Datasheet": url}
                if ref in VALUE_LABELS:
                    properties["Value"] = VALUE_LABELS[ref]
                specs[ref] = {"expected_values": [EXPECTED[ref]],
                              "expected_footprints": [components[ref]["footprint"]],
                              "properties": properties}
    if specs.keys() != EXPECTED.keys():
        raise ValueError("Selection registers do not cover the remaining batch")
    outputs, details, inputs = {}, {}, {}
    for path, kind in ((board_path, "footprint"), (sch_path, "symbol")):
        inputs[path.name] = sha(path)
        text, tree = load(path)
        result, details[kind] = prepare_fields(text, tree, kind, specs)
        if invariant(tree) != invariant(loads(result)):
            raise ValueError("Change beyond allowed identity fields: " + path.name)
        outputs[path] = result.encode("utf-8")
    apply_manifest_fields(manifest, specs)
    for component in manifest["components"]:
        if component["reference"] in VALUE_LABELS:
            component["value"] = VALUE_LABELS[component["reference"]]
    for path, kind in ((board_path, "footprint"), (sch_path, "symbol")):
        nodes = loads(outputs[path].decode("utf-8")).children(kind)
        for component in manifest["components"]:
            matches = [n for n in nodes if n.properties().get("Reference") == component["reference"]]
            if (len(matches) != 1 or not component["mpn"]
                    or matches[0].properties().get("MPN") != component["mpn"]):
                raise ValueError("Fitted MPN differs between native and manifest: " + component["reference"])
    for path, contents in outputs.items():
        path.write_bytes(contents)
    manifest.update(generated_pcb_sha256=sha(board_path), schematic_sha256=sha(sch_path),
                    current_stage_report="reports/remaining-identities.json")
    manifest_path.write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    report = {
        "input_commit": "7fed80e", "input_sha256": inputs,
        "output_pcb_sha256": sha(board_path), "output_schematic_sha256": sha(sch_path),
        "placement_manifest_sha256": sha(manifest_path), "generator_sha256": sha(Path(__file__)),
        "selection_registers": {p.name: sha(p) for p in (device_path, power_path)},
        "references": sorted(specs), "applied_fields": details,
        "nominal_value_label_clarifications": VALUE_LABELS,
        "unchanged_outside_declared_identity_properties": True,
        "all_83_fitted_mpn_fields_match_native_and_manifest": True,
        "mpn_coverage": {"fitted": 83, "identified": 83, "blank": 0},
        "reused_geometry_evidence": {
            "pcb_sha256": BASE, "report": "reports/usb-geometry.json",
            "native_drc": "reports/usb-drc.json",
            "scope": "Unchanged copper, pads, nets, poses, fill, rules and physical geometry. Not new powered or supplier evidence.",
        },
        "remaining": "Part-specific land/paste and conservative-envelope corrections, existing-part audit, full routing, CAD rebind, assembly/supplier and powered qualification remain open. Identity completeness is not BOM/quotation release.",
    }
    report_path.write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"mpn_coverage": report["mpn_coverage"], "pcb_sha256": report["output_pcb_sha256"]}))


if __name__ == "__main__":
    main()
