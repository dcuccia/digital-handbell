# SPDX-License-Identifier: MIT
"""Apply the selected Q3 orderable without changing circuitry or package geometry."""
import hashlib
import json
from pathlib import Path

from apply_clock_definition_revision import prop_edits
from kicad_sexpr import apply_edits, load
from route_clock_local import PACKAGE, ROOT

PINNED = {
    "handbell.kicad_pcb": "19459cd32d8a8f58f0ff790e55a61294bbd580a0680c723f6f7a5695faee014c",
    "handbell.kicad_sch": "51fec9d33a95ea712f26df13689ce1321f0c6084110fef97cd927fdc0ea4f865",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if any(sha(PACKAGE / name) != digest for name, digest in PINNED.items()):
        raise ValueError("Q3 input checkpoint changed; refusing overwrite")
    report_path = PACKAGE / "reports" / "q3-native-identity.json"
    if report_path.exists():
        raise ValueError("Existing Q3 report refused")
    source = ROOT / "hardware" / "handbell" / "parts" / "device-component-candidates.json"
    register = json.loads(source.read_text(encoding="utf-8"))
    selected = next(g for g in register["groups"] if g["references"] == ["Q3"])
    if selected["mpn"] != "DMP2045UFY4-7":
        raise ValueError("Selected Q3 identity changed")
    values = {
        "Value": "DMP2045UFY4",
        "Datasheet": "https://www.diodes.com/datasheet/download/DMP2045UFY4.pdf",
        "Description": "P-channel MOSFET; X2-DFN2015-3; G=1, S=2, D=3. Selected replacement, not electrically identical.",
    }
    outputs = {}
    for name, kind in (("handbell.kicad_pcb", "footprint"), ("handbell.kicad_sch", "symbol")):
        text, tree = load(PACKAGE / name)
        item = next(n for n in tree.children(kind) if n.properties().get("Reference") == "Q3")
        if item.properties()["Value"] != "DMG3415UFY":
            raise ValueError("Unexpected current Q3 value")
        if any(key in item.properties() for key in ("MPN", "Manufacturer")):
            raise ValueError("Existing Q3 sourced fields require review")
        if kind == "footprint":
            if item.atoms()[1] != "Handbell:DFN2015-3_DrainPad":
                raise ValueError("Corrected Q3 footprint absent")
            actual = {p.atoms()[1]: p.value("net") for p in item.children("pad")}
            if actual != {p["native_pin"]: p["net"] for p in selected["pin_map"]}:
                raise ValueError("Q3 pin/net mapping changed")
            xy, layer = "0 0", '(layer "F.Fab")'
        else:
            if item.value("lib_id") != "Handbell:MOSFET-P_DFN2015":
                raise ValueError("Expected generic P-channel symbol absent")
            xy, layer = " ".join(item.child("at").atoms()[1:3]), ""
        fields = "".join(
            f'\n(property "{key}" {json.dumps(value)} (at {xy} 0) {layer} '
            '(hide yes) (effects (font (size 1 1))))'
            for key, value in (("MPN", selected["mpn"]), ("Manufacturer", selected["manufacturer"])))
        close_line = text.rfind("\n", item.start, item.end-1) + 1
        insertion = item.end-1
        if not text[close_line:insertion].strip():
            insertion = close_line
            fields = fields.lstrip("\n") + "\n"
        edits = prop_edits(item, values) + [(insertion, insertion, fields)]
        outputs[name] = apply_edits(text, edits).encode("utf-8")
    manifest_path = PACKAGE / "placement-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    component = next(c for c in manifest["components"] if c["reference"] == "Q3")
    retained_geometry = {k: v for k, v in component.items() if k not in ("value", "mpn", "manufacturer")}
    component.update(value=values["Value"], mpn=selected["mpn"], manufacturer=selected["manufacturer"])
    for name, content in outputs.items():
        (PACKAGE / name).write_bytes(content)
    manifest.update(generated_pcb_sha256=sha(PACKAGE / "handbell.kicad_pcb"),
                    schematic_sha256=sha(PACKAGE / "handbell.kicad_sch"),
                    current_stage_report="reports/q3-native-identity.json")
    manifest_path.write_bytes((json.dumps(manifest, indent=2)+"\n").encode("utf-8"))
    report = {
        "input_commit": "db9d867", "input_sha256": PINNED,
        "output_pcb_sha256": sha(PACKAGE / "handbell.kicad_pcb"),
        "output_schematic_sha256": sha(PACKAGE / "handbell.kicad_sch"),
        "placement_manifest_sha256": sha(manifest_path), "generator_sha256": sha(Path(__file__)),
        "selection_register_sha256": sha(source), "reference": "Q3",
        "old_value": "DMG3415UFY", "selected_mpn": selected["mpn"],
        "retained_generic_symbol": "Handbell:MOSFET-P_DFN2015",
        "pin_map": selected["pin_map"], "retained_geometry": retained_geometry,
        "scope": "Value, manufacturer, MPN, datasheet and instance description only; no pad, net, library, pose or copper changes.",
        "limits": selected["remaining_gates"] + [
            "Source-transition, standby leakage, voltage-drop and thermal qualification remain open.",
            "No reverse-cell protection, supplier stock guarantee or fabrication/child-use approval."
        ],
    }
    report_path.write_bytes((json.dumps(report, indent=2)+"\n").encode("utf-8"))
    print(json.dumps({"mpn": selected["mpn"], "pcb_sha256": report["output_pcb_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
