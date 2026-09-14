# SPDX-License-Identifier: MIT
"""Apply only approved ordinary 0402 resistor identity fields to a pinned stage."""
import hashlib
import json
from pathlib import Path
import subprocess

from apply_clock_definition_revision import prop_edits
from kicad_sexpr import apply_edits, load
from route_clock_local import PACKAGE, ROOT

INPUT_COMMIT = "ac109c4"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report_path = PACKAGE / "reports" / "resistor-identities.json"
    if report_path.exists():
        raise ValueError("Existing resistor identity report refused")
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
    profile = register["profiles"]["yageo-0402"]
    parts = [p for p in register["parts"] if p["profile"] == "yageo-0402"]
    selected = {ref: p for p in parts for ref in p["references"]}
    if len(selected) != 27 or "R27" in selected or any("selected_value" in p for p in parts):
        raise ValueError("Ordinary-resistor scope changed")
    outputs, details = {}, {}
    for name, kind in (("handbell.kicad_pcb", "footprint"), ("handbell.kicad_sch", "symbol")):
        text, tree = load(PACKAGE / name)
        edits, seen = [], set()
        for item in tree.children(kind):
            props = item.properties()
            ref = props.get("Reference")
            if ref not in selected:
                continue
            if ref in seen:
                raise ValueError("Duplicate resistor instance: "+ref)
            seen.add(ref)
            part = selected[ref]
            if props["Value"] not in part["source_values"]:
                raise ValueError("Resistor nominal value differs: "+ref)
            for key, value in (("MPN", part["mpn"]), ("Manufacturer", profile["manufacturer"])):
                if props.get(key) and props[key] != value:
                    raise ValueError("Conflicting selected field: "+ref+"/"+key)
            values = {"MPN": part["mpn"], "Manufacturer": profile["manufacturer"],
                      "Datasheet": profile["datasheet_url"]}
            old_sheet = props.get("Datasheet", "")
            if old_sheet and old_sheet != profile["datasheet_url"]:
                if props.get("CircuitReference") not in (None, "", old_sheet):
                    raise ValueError("Conflicting circuit reference: "+ref)
                values["CircuitReference"] = old_sheet
            if kind == "footprint":
                if "0402" not in item.atoms()[1] or len(item.children("pad")) != 2:
                    raise ValueError("Unexpected resistor package: "+ref)
                xy, layer = "0 0", '(layer "F.Fab")'
                details[ref] = {"value": props["Value"], "mpn": part["mpn"],
                                "previous_mpn": props.get("MPN", ""),
                                "manufacturer": profile["manufacturer"],
                                "datasheet": profile["datasheet_url"],
                                "preserved_circuit_reference": values.get("CircuitReference")}
            else:
                xy, layer = " ".join(item.child("at").atoms()[1:3]), ""
            edits += prop_edits(item, values)
            fields = "".join(
                f'\n(property {json.dumps(key)} {json.dumps(value)} (at {xy} 0) {layer} '
                '(hide yes) (effects (font (size 1 1))))'
                for key, value in values.items() if key not in props)
            if fields:
                start = text.rfind("\n", item.start, item.end-1)+1
                insertion = item.end-1
                if not text[start:insertion].strip():
                    insertion, fields = start, fields.lstrip("\n")+"\n"
                edits.append((insertion, insertion, fields))
        if seen != selected.keys():
            raise ValueError("Resistor inventory mismatch: "+name)
        outputs[name] = apply_edits(text, edits).encode("utf-8")
    mf = PACKAGE / "placement-manifest.json"
    manifest = json.loads(mf.read_text(encoding="utf-8"))
    seen = set()
    for component in manifest["components"]:
        ref = component["reference"]
        if ref not in selected:
            continue
        seen.add(ref)
        if component["value"] not in selected[ref]["source_values"]:
            raise ValueError("Manifest nominal value differs: "+ref)
        if component.get("mpn") not in ("", selected[ref]["mpn"]):
            raise ValueError("Manifest MPN differs: "+ref)
        component.update(mpn=selected[ref]["mpn"], manufacturer=profile["manufacturer"])
    if seen != selected.keys():
        raise ValueError("Manifest resistor inventory mismatch")
    if any(sha(PACKAGE / name) != digest for name, digest in inputs.items()):
        raise ValueError("Inputs changed during operation")
    for name, content in outputs.items():
        (PACKAGE / name).write_bytes(content)
    manifest.update(generated_pcb_sha256=sha(PACKAGE / "handbell.kicad_pcb"),
                    schematic_sha256=sha(PACKAGE / "handbell.kicad_sch"),
                    current_stage_report="reports/resistor-identities.json")
    mf.write_bytes((json.dumps(manifest, indent=2)+"\n").encode("utf-8"))
    report = {
        "input_commit": INPUT_COMMIT, "input_sha256": inputs,
        "output_pcb_sha256": sha(PACKAGE / "handbell.kicad_pcb"),
        "output_schematic_sha256": sha(PACKAGE / "handbell.kicad_sch"),
        "placement_manifest_sha256": sha(mf), "generator_sha256": sha(Path(__file__)),
        "selection_register_sha256": sha(source), "references": details,
        "previously_blank_mpn_count": sum(not d["previous_mpn"] for d in details.values()),
        "existing_matching_mpn_count": sum(bool(d["previous_mpn"]) for d in details.values()),
        "scope": "27 ordinary 0402 resistors only. Identity fields only; nominal values, symbol/library types, all geometry, pads, nets and copper retained. R27 excluded.",
        "datasheet_policy": "Use the verified Yageo RC_L family sheet. Preserve four former BQ2970 links as CircuitReference instead of mislabelling them resistor datasheets.",
        "remaining_gates": register["remaining_gates"],
    }
    report_path.write_bytes((json.dumps(report, indent=2)+"\n").encode("utf-8"))
    print(json.dumps({"applied": len(details), "new_mpn": report["previously_blank_mpn_count"],
                      "confirmed_mpn": report["existing_matching_mpn_count"]}, indent=2))


if __name__ == "__main__":
    main()
