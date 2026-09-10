# SPDX-License-Identifier: MIT
"""Check the wing draft using native reports bound to their exact input CAD."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from kicad_sexpr import apply_edits, load, pcb_net_name
from draft_wing_placement import read_parts
from place_handbell import rotate

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "hardware" / "handbell"
DRAFT = BASE / "iterations" / "wing-draft"
NATIVE_INPUTS = ("handbell.kicad_sch", "handbell.kicad_pcb", "handbell.kicad_pro",
                 "fp-lib-table", "sym-lib-table")
NATIVE_REPORTS = ("erc.json", "drc.json", "handbell-netlist.xml")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def input_hashes(folder):
    return {name: sha(folder / name) for name in NATIVE_INPUTS}


def run_native(cli):
    require(cli.is_file(), f"KiCad CLI not found: {cli}")
    before = input_hashes(DRAFT)
    with tempfile.TemporaryDirectory(prefix="handbell-wing-native-") as temporary:
        temporary = Path(temporary)
        commands = [
            ["sch", "erc", "--format", "json", "--severity-all",
             "--output", str(temporary / "erc.json"), str(DRAFT / "handbell.kicad_sch")],
            ["sch", "export", "netlist", "--format", "kicadxml",
             "--output", str(temporary / "handbell-netlist.xml"), str(DRAFT / "handbell.kicad_sch")],
            ["pcb", "drc", "--format", "json", "--schematic-parity", "--severity-all",
             "--output", str(temporary / "drc.json"), str(DRAFT / "handbell.kicad_pcb")],
        ]
        for command in commands:
            result = subprocess.run([str(cli), *command], cwd=ROOT, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                    errors="replace", timeout=300)
            require(result.returncode == 0, f"Native command failed: {command}\n{result.stdout}")
            if result.stdout.strip():
                print(result.stdout.strip())
        require(before == input_hashes(DRAFT), "CAD changed while native reports were running")
        hashes = {name: sha(temporary / name) for name in NATIVE_REPORTS}
        reports = DRAFT / "reports"
        reports.mkdir(exist_ok=True)
        for name in NATIVE_REPORTS:
            (reports / name).write_bytes((temporary / name).read_bytes())
        binding = {"generated_utc": datetime.now(timezone.utc).isoformat(),
                   "inputs": before, "reports": hashes, "kicad_cli_sha256": sha(cli)}
        (reports / "native-input-bindings.json").write_text(
            json.dumps(binding, indent=2) + "\n", encoding="utf-8")


def verify_native_evidence(folder):
    path = folder / "reports" / "native-input-bindings.json"
    require(path.is_file(), "Native evidence is unbound; run check_wing_placement.py --run-native")
    binding = json.loads(path.read_text())
    require(binding["inputs"] == input_hashes(folder), "Native reports refer to different CAD; rerun --run-native")
    require(binding["reports"] == {name: sha(folder / "reports" / name) for name in NATIVE_REPORTS},
            "Native report bytes changed after generation; rerun --run-native")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-native", action="store_true", help="Run fresh ERC/netlist/DRC and bind their input bytes.")
    parser.add_argument("--kicad-cli", type=Path,
                        default=Path(os.environ.get("LOCALAPPDATA", "")) /
                        "Programs" / "KiCad" / "10.0" / "bin" / "kicad-cli.exe")
    args = parser.parse_args()
    if args.run_native:
        run_native(args.kicad_cli)
    verify_native_evidence(DRAFT)
    manifest = json.loads((DRAFT / "placement-manifest.json").read_text())
    report = json.loads((DRAFT / "placement-build-report.json").read_text())
    require(manifest["schema_version"] == 2, "Wrong wing manifest schema")
    require(sha(DRAFT / "handbell.kicad_pcb") == manifest["generated_pcb_sha256"], "PCB/manifest mismatch")
    require(sha(DRAFT / "handbell.kicad_sch") == manifest["schematic_sha256"], "Schematic/manifest mismatch")
    require(sha(BASE / "handbell.kicad_pcb") == manifest["baseline_pcb_sha256"], "Baseline PCB changed")
    require(sha(BASE / "handbell.kicad_sch") == manifest["baseline_schematic_sha256"], "Baseline schematic changed")
    require(sha(DRAFT / "handbell.kicad_pro") == sha(BASE / "handbell.kicad_pro"), "Project/rule settings changed")
    require(report["script_sha256"] == sha(ROOT / "tools" / "draft_wing_placement.py"), "Generator report stale")
    require(not manifest["planning"]["intercluster_overlaps"], "Intercluster planning overlap")
    require(not manifest["planning"]["constraint_violations"], "Planning keepout violation")
    old_text, old_sch = load(BASE / "handbell.kicad_sch")
    new_text, new_sch = load(DRAFT / "handbell.kicad_sch")
    old_title, new_title = old_sch.child("title_block"), new_sch.child("title_block")
    edits = [(new_title.start, new_title.end, old_text[old_title.start:old_title.end])]
    dnp_units = 0
    for symbol in new_sch.children("symbol"):
        if symbol.properties().get("Reference") == "X1":
            require(symbol.value("dnp") == "yes", "Every X1 unit must be DNP")
            flag = symbol.child("dnp")
            edits.append((flag.items[1].start, flag.items[1].end, "no"))
            dnp_units += 1
    require(apply_edits(new_text, edits) == old_text, "Schematic changed beyond title and X1 DNP")
    source_xml = ET.parse(BASE / "reports" / "handbell-netlist.xml").getroot()
    draft_xml = ET.parse(DRAFT / "reports" / "handbell-netlist.xml").getroot()

    def connections(xml):
        return {(pin.get("ref"), pin.get("pin")): net.get("name")
                for net in xml.findall("nets/net") for pin in net.findall("node")}

    expected = connections(source_xml)
    require(connections(draft_xml) == expected, "Native netlist connectivity changed")
    _, original = load(BASE / "handbell.kicad_pcb")
    _, board = load(DRAFT / "handbell.kicad_pcb")
    require(not any(board.children(kind) for kind in ("segment", "via", "zone")), "Not a placement-only board")
    old_fp = {fp.properties()["Reference"]: fp for fp in original.children("footprint")}
    footprints = {fp.properties()["Reference"]: fp for fp in board.children("footprint")}
    mounts = {m["reference"]: m for m in manifest["mounting_holes"]}
    require(set(footprints) == set(old_fp) | set(mounts), "Unexpected footprint inventory")
    require(len(footprints) == len(board.children("footprint")), "Duplicate references")
    components = {c["reference"]: c for c in manifest["components"]}
    require(len(components) == 73, "Unexpected fitted count")
    library_parts, _, _ = read_parts(old_sch)
    pads_checked = 0
    for ref, fp in footprints.items():
        if ref in mounts:
            mount, pad = mounts[ref], fp.child("pad")
            require(pad.atoms()[2] == "thru_hole" and pad.value("net") == "GND", "Mount must be GND-assigned PTH")
            require(float(pad.value("drill")) == mount["drill_mm"], "Mount drill differs")
            require(list(map(float, pad.child("size").atoms()[1:])) == [mount["pad_diameter_mm"]] * 2,
                    "Mount copper diameter differs")
            at = list(map(float, fp.child("at").atoms()[1:]))
            local = list(map(float, pad.child("at").atoms()[1:3]))
            dx, dy = rotate(*local, at[2] if len(at) > 2 else 0)
            require(abs(at[0] + dx - 100 - mount["x_mm"]) < 1e-6
                    and abs(at[1] + dy - 100 - mount["y_mm"]) < 1e-6,
                    "Mounting bore does not match the shared mechanical interface")
            require("board_only" in fp.child("attr").atoms(), "Mechanical mount must be board-only")
        else:
            require(fp.atoms()[1] == old_fp[ref].atoms()[1], f"Footprint identity changed: {ref}")
            require(fp.properties()["Value"] == old_fp[ref].properties()["Value"], f"Value changed: {ref}")
            require(len(fp.children("pad")) == len(old_fp[ref].children("pad")), f"Pad inventory changed: {ref}")
        for pad in fp.children("pad"):
            expected_net = "GND" if ref in mounts else pcb_net_name(expected.get((ref, pad.atoms()[1])))
            require(pad.value("net") == expected_net, f"Physical pad/net mismatch: {ref}.{pad.atoms()[1]}")
            pads_checked += 1
        if ref in components:
            c = components[ref]
            require(fp.value("layer") == c["side"] + ".Cu", f"Wrong face: {ref}")
            flags = set(fp.child("attr").atoms()[1:]) if fp.child("attr") else set()
            require(not flags & {"dnp", "exclude_from_bom", "exclude_from_pos_files"}, f"Fitted part excluded: {ref}")
            at = list(map(float, fp.child("at").atoms()[1:]))
            require(abs(((at[2] + c["rotation_deg"] + 180) % 360) - 180) < 1e-6,
                    f"Manifest/native rotation mismatch: {ref}")
            source = library_parts[ref]
            cy = -source["raw_cy"] if c["side"] == "B" else source["raw_cy"]
            dx, dy = rotate(source["raw_cx"], cy, at[2])
            require(abs(at[0] - 100 + dx - c["x_mm"]) <= 1e-6
                    and abs(at[1] - 100 + dy - c["y_mm"]) <= 1e-6,
                    f"Manifest/native body-center mismatch: {ref}")
            require([c["width_mm"], c["depth_mm"], c["height_mm"]] ==
                    [source["raw_w"], source["raw_h"], source["height"]],
                    f"Source body proxy was resized: {ref}")
            z = manifest["board"]["front_z_mm"]
            back = z + manifest["board"]["thickness_mm"]
            expected_z = [z - c["height_mm"], z] if c["side"] == "F" else [back, back + c["height_mm"]]
            require([c["z_min_mm"], c["z_max_mm"]] == expected_z, f"Incorrect physical face height: {ref}")
    require(pads_checked == 300 == report["physical_pads_checked"], "Physical pad count mismatch")
    erc = json.loads((DRAFT / "reports" / "erc.json").read_text())
    erc_findings = [v for sheet in erc["sheets"] for v in sheet["violations"]]
    require(not erc_findings, "ERC findings remain")
    drc = json.loads((DRAFT / "reports" / "drc.json").read_text())
    allowed = {"silk_over_copper", "text_height", "silk_overlap", "text_thickness", "silk_edge_clearance",
               "hole_clearance"}
    require(all(v["type"] in allowed for v in drc["violations"]), "New substantive native DRC finding")
    holes = [v for v in drc["violations"] if v["type"] == "hole_clearance"]
    require(len(holes) == 4 and all(all("X6" in item["description"] for item in row["items"]) for row in holes),
            "Only the four retained internal X6 hole findings are expected")
    require(len(drc["schematic_parity"]) == 46 and all(
        "No corresponding pin found in schematic" in row["description"] for row in drc["schematic_parity"]),
        "Unexpected schematic parity finding; do not suppress it")
    output = {
        "status": "Draft correspondence, not routing/hardware/fabrication approval",
        "physical_pads_checked": pads_checked, "x1_dnp_units": dnp_units,
        "native_manifest_body_poses_checked": len(components),
        "native_erc_findings": 0, "native_physical_findings": len(drc["violations"]),
        "retained_usb_hole_findings": 4, "unconnected_items": len(drc["unconnected_items"]),
        "cli_auto_pin_fallback_findings": 46, "paired_editor_gui_review_performed_for_this_variant": False,
        "inputs": {name: sha(DRAFT / name) for name in (
            "handbell.kicad_sch", "handbell.kicad_pcb", "handbell.kicad_pro", "placement-manifest.json",
            "reports/erc.json", "reports/drc.json", "reports/handbell-netlist.xml",
            "reports/native-input-bindings.json")},
        "limits": ["No new GUI parity approval is inferred from the baseline's GUI review.",
                   "The known CLI fallback and all native findings remain in the complete report.",
                   "Source geometry fit, exact contacts/cell, power/thermal routing and mechanical retention remain gates."],
    }
    (DRAFT / "reports" / "correspondence-review.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in output.items() if key != "inputs"}, indent=2))


if __name__ == "__main__":
    main()
