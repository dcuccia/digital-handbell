# SPDX-License-Identifier: MIT
"""Verify the T8 draft's explicit electrical changes and byte-bound native evidence."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import draft_t8_placement as draft
from kicad_sexpr import load, pcb_net_name

ROOT, OUTPUT, SOURCE = draft.ROOT, draft.OUTPUT, draft.SOURCE
REPORTS = ("erc.json", "drc.json", "handbell-netlist.xml", "handbell-schematic.pdf")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inputs():
    files = [OUTPUT / name for name in (
        "handbell.kicad_sch", "handbell.kicad_pcb", "handbell.kicad_pro",
        "fp-lib-table", "sym-lib-table", "T8.kicad_sym", "placement-manifest.json",
        "battery-contact-interface.json")]
    files.extend(sorted((OUTPUT / "T8.pretty").glob("*.kicad_mod")))
    files.append(draft.MEASUREMENTS)
    if (OUTPUT / "placement-xy-seed.json").exists():
        files.append(OUTPUT / "placement-xy-seed.json")
    if (OUTPUT / "reports" / "stack-shift-screen-evidence.json").exists():
        files.append(OUTPUT / "reports" / "stack-shift-screen-evidence.json")
    files += [SOURCE / name for name in ("handbell.kicad_sch", "handbell.kicad_pcb", "handbell.kicad_pro")]
    files += [ROOT / "tools" / name for name in (
        "draft_t8_placement.py", "draft_wing_placement.py", "place_handbell.py",
        "placement_geometry.py", "kicad_sexpr.py")]
    files.append(ROOT / "hardware" / "handbell" / "Handbell.kicad_sym")
    for directory in draft.base.LIBRARIES.values():
        files.extend(sorted(directory.glob("*.kicad_mod")))
    return {str(path.relative_to(ROOT)): draft.sha(path) for path in files}


def run_native(cli):
    require(cli.is_file(), "KiCad CLI missing: "+str(cli))
    before = inputs()
    work = OUTPUT / "reports" / ".native-run"
    require(not work.exists(), "Native staging directory already exists; inspect it before retrying")
    work.mkdir()
    try:
        commands = [
            ["sch", "erc", "--format", "json", "--severity-all", "--output", str(work / "erc.json"),
             str(OUTPUT / "handbell.kicad_sch")],
            ["sch", "export", "netlist", "--format", "kicadxml", "--output", str(work / "handbell-netlist.xml"),
             str(OUTPUT / "handbell.kicad_sch")],
            ["pcb", "drc", "--format", "json", "--schematic-parity", "--severity-all",
             "--output", str(work / "drc.json"), str(OUTPUT / "handbell.kicad_pcb")],
            ["sch", "export", "pdf", "--exclude-pdf-metadata", "--output",
             str(work / "handbell-schematic.pdf"), str(OUTPUT / "handbell.kicad_sch")],
        ]
        for command in commands:
            result = subprocess.run([str(cli), *command], cwd=ROOT, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                    errors="replace", timeout=600)
            require(result.returncode == 0, f"Native command failed: {command}\n{result.stdout}")
            print(result.stdout.strip())
        require(before == inputs(), "CAD/dependencies changed during native validation")
        for name in REPORTS:
            shutil.copyfile(work / name, OUTPUT / "reports" / name)
        binding = {"generated_utc": datetime.now(timezone.utc).isoformat(),
                   "kicad_version": subprocess.check_output([str(cli), "--version"], text=True).strip(),
                   "kicad_cli_sha256": draft.sha(cli), "inputs": before,
                   "reports": {name: draft.sha(OUTPUT / "reports" / name) for name in REPORTS},
                   "commands": commands,
                   "scope": "Native tool evidence, not functional, battery-safety or fabrication approval"}
        draft.write(OUTPUT / "reports" / "native-input-bindings.json", json.dumps(binding, indent=2)+"\n")
    finally:
        shutil.rmtree(work)


def connections(path):
    root = ET.parse(path).getroot()
    return {(node.get("ref"), node.get("pin")): net.get("name")
            for net in root.findall("nets/net") for node in net.findall("node")}


def normalized(name):
    return name.lstrip("/") if name else name


def check():
    binding = json.loads((OUTPUT / "reports" / "native-input-bindings.json").read_text())
    require(binding["inputs"] == inputs(), "Stale input binding; regenerate with --run-native")
    require(binding["reports"] == {n: draft.sha(OUTPUT / "reports" / n) for n in REPORTS},
            "Native report bytes changed after binding")
    manifest = json.loads((OUTPUT / "placement-manifest.json").read_text())
    require(manifest["schema_version"] == 2, "Wrong manifest schema")
    require(manifest["generated_pcb_sha256"] == draft.sha(OUTPUT / "handbell.kicad_pcb"), "PCB/manifest mismatch")
    require(manifest["schematic_sha256"] == draft.sha(OUTPUT / "handbell.kicad_sch"), "Schematic/manifest mismatch")
    require(manifest["baseline_pcb_sha256"] == draft.sha(SOURCE / "handbell.kicad_pcb"), "Frozen wing board changed")
    require(manifest["baseline_schematic_sha256"] == draft.sha(SOURCE / "handbell.kicad_sch"), "Frozen wing schematic changed")
    require(draft.sha(OUTPUT / "handbell.kicad_pro") == draft.sha(SOURCE / "handbell.kicad_pro"),
            "Rule settings changed; no blanket waiver allowed")
    require(manifest["battery_contact_interface_sha256"] == draft.sha(OUTPUT / "battery-contact-interface.json"),
            "Contact interface not bound to manifest")
    front_z = manifest["board"]["front_z_mm"]
    back_z = round(front_z+manifest["board"]["thickness_mm"], 6)
    require(manifest["measurement_sha256"] == draft.sha(draft.MEASUREMENTS), "Measurement/profile binding changed")
    require(manifest["stack_translation_z_mm"] == manifest["speaker_front_z_mm"] == round(front_z-20.5, 6),
            "Speaker/PCB axial translation is inconsistent")
    if manifest["placement_xy_seed_sha256"]:
        require(manifest["placement_xy_seed_sha256"] == draft.sha(OUTPUT / "placement-xy-seed.json"),
                "Recorded native XY seed changed")
    if manifest.get("stack_shift_screen_evidence"):
        evidence = manifest["stack_shift_screen_evidence"]
        path = OUTPUT / evidence["path"]
        require(draft.sha(path) == evidence["sha256"], "Mechanical selection evidence changed")
        screen = json.loads(path.read_text())
        case = next((c for c in screen["cases"] if
                     c["whole_stack_mouthward_shift_mm"] == -manifest["stack_translation_z_mm"] and
                     c["plastic_wall_mm"] == manifest["mechanical_guard_target_mm"]), None)
        require(case is not None, "Selected shift/guard lacks its bounded mechanical screening case")
        stock = case["complete_conservative_guard_stock"]
        require(stock["shell_intersection_mm3"] == 0 and
                stock["shell_distance_mm"] >= screen["desired_nominal_guard_shell_margin_mm"],
                "Selected bounded guard-stock result does not meet its declared nominal margin")
    report = json.loads((OUTPUT / "placement-build-report.json").read_text())
    require(report["script_sha256"] == draft.sha(ROOT / "tools" / "draft_t8_placement.py"), "Stale generation report")
    require(not manifest["planning"]["intercluster_overlaps"], "Intercluster overlap")
    require(not manifest["planning"]["constraint_violations"], "Placement constraint violation")
    old_nets = connections(SOURCE / "reports" / "handbell-netlist.xml")
    new_nets = connections(OUTPUT / "reports" / "handbell-netlist.xml")
    retained = {pin: net for pin, net in old_nets.items() if pin[0] != "X1"}
    require({pin: new_nets.get(pin) for pin in retained} == retained,
            "A retained pin/net changed outside the explicit X1 removal/new protection contract")
    require(not any(ref == "X1" for ref, _ in new_nets), "Unprotected parallel JST input remains")
    for ref, pins in draft.NEW_PINS.items():
        for pin, net in pins.items():
            actual = new_nets.get((ref, pin))
            if net is None:
                require(actual and actual.startswith("unconnected-"), f"{ref}.{pin} missing explicit NC")
            else:
                require(normalized(actual) == net, f"New pin mapping incorrect: {ref}.{pin}: {actual}, expected {net}")
    raw_neg = {pin for pin, net in new_nets.items() if normalized(net) == "CELL_NEG"}
    require(raw_neg == {("BT2", "1"), ("U6", "4"), ("Q5", "A1"), ("Q5", "C1"), ("C30", "2"), ("R28", "2")},
            "Raw cell negative has an unexpected bypass/user-access connection")
    require(new_nets[("U3", "2")] == "GND", "Charger negative bypasses protection")
    require(new_nets[("U2", "2")] == "GND", "Logic regulator negative bypasses protection")
    _, board = load(OUTPUT / "handbell.kicad_pcb")
    _, old_board = load(SOURCE / "handbell.kicad_pcb")
    _, schematic = load(OUTPUT / "handbell.kicad_sch")
    old_fp = {fp.properties()["Reference"]: fp for fp in old_board.children("footprint")}
    footprints = {fp.properties()["Reference"]: fp for fp in board.children("footprint")}
    expected_refs = (set(old_fp)-{"X1"}) | set(draft.NEW_PINS)
    require(set(footprints) == expected_refs, "Unexpected footprint inventory")
    require(len(footprints) == len(board.children("footprint")), "Duplicate PCB reference")
    require(not any(board.children(kind) for kind in ("segment", "via", "zone")), "Unexpected routing/copper zones")
    physical, electrical = 0, 0
    parts, _, _, _ = draft.read_parts()
    by_ref = {p["reference"]: p for p in manifest["components"]}
    require(len(by_ref) == 83, "Unexpected fitted inventory")
    require(Counter(p["side"] for p in by_ref.values()) == {"F": 70, "B": 13},
            "Backside fitted parts omitted or wrong face")
    for ref, fp in footprints.items():
        expected = {"1": "GND"} if ref.startswith("MH") else {pin: net for (r, pin), net in new_nets.items() if r == ref}
        for pad in fp.children("pad"):
            number = pad.atoms()[1]
            actual = pad.value("net")
            require(actual == pcb_net_name(expected.get(number)), f"Physical pad/net mismatch: {ref}.{number}")
            physical += 1
            electrical += bool(number)
        if ref in old_fp and ref != "U1":
            require(fp.atoms()[1] == old_fp[ref].atoms()[1], f"Unpermitted footprint replacement: {ref}")
            require(fp.properties()["Value"] == old_fp[ref].properties()["Value"], f"Retained value changed: {ref}")
            require(len(fp.children("pad")) == len(old_fp[ref].children("pad")), f"Retained pads changed: {ref}")
            for new_pad, old_pad in zip(fp.children("pad"), old_fp[ref].children("pad")):
                for key in ("at", "size", "drill", "layers", "roundrect_rratio", "solder_mask_margin"):
                    new_field, old_field = new_pad.child(key), old_pad.child(key)
                    require((new_field.atoms() if new_field else None) == (old_field.atoms() if old_field else None),
                            f"Retained local pad geometry changed: {ref}.{new_pad.atoms()[1]} {key}")
        if ref.startswith("MH"):
            pad = fp.child("pad")
            require(pad.value("drill") == "2.2" and pad.child("size").atoms()[1:] == ["4.4", "4.4"],
                    "M2 bore/copper changed")
            mount = next(m for m in manifest["mounting_holes"] if m["reference"] == ref)
            at = list(map(float, fp.child("at").atoms()[1:3]))
            require(abs(at[0]-100-mount["x_mm"]) < 1e-6 and abs(at[1]-100-mount["y_mm"]) < 1e-6,
                    "Mounting center changed")
            continue
        if ref in by_ref:
            c, source = by_ref[ref], parts[ref]
            require(fp.value("layer") == c["side"]+".Cu", "Incorrect fitted face: "+ref)
            flags = set(fp.child("attr").atoms()[1:]) if fp.child("attr") else set()
            require(not flags & {"dnp", "exclude_from_bom", "exclude_from_pos_files"}, "Fitted part excluded: "+ref)
            at = list(map(float, fp.child("at").atoms()[1:]))
            require(abs(((at[2]+c["rotation_deg"]+180)%360)-180) < 1e-6, "Native rotation mismatch: "+ref)
            cy = -source["raw_cy"] if c["side"] == "B" else source["raw_cy"]
            dx, dy = draft.base.rotate(source["raw_cx"], cy, at[2])
            require(abs(at[0]-100+dx-c["x_mm"]) < 1e-6 and abs(at[1]-100+dy-c["y_mm"]) < 1e-6,
                    "Native body center mismatch: "+ref)
            require([c["width_mm"], c["depth_mm"], c["height_mm"]] ==
                    [source["raw_w"], source["raw_h"], source["height"]], "Resized body proxy: "+ref)
            z = [round(front_z-c["height_mm"], 6), front_z] if c["side"] == "F" else [
                back_z, round(back_z+c["height_mm"], 6)]
            require([c["z_min_mm"], c["z_max_mm"]] == z, "Wrong explicit Z bounds: "+ref)
    require(physical == report["physical_pads"] == 325, "Physical pad inventory changed")
    require(footprints["U1"].atoms()[1] == "T8:Winbond_USON8_UX_2x3", "Incorrect flash package")
    require(footprints["U1"].properties()["MPN"] == "W25Q16JVUXIQ TR", "Wrong exact flash ordering code")
    flash_pads = {p.atoms()[1]: p for p in footprints["U1"].children("pad") if p.atoms()[1]}
    require(flash_pads["PAD"].child("size").atoms()[1:] == ["0.2", "1.6"], "UX exposed strip mistaken for XG pad")
    require(flash_pads["PAD"].value("net") == "GND", "Flash exposed strip must retain permitted GND assignment")
    perimeter = manifest["board"]["outline_common_xy_mm"]
    edges = [g for g in board.children("gr_line") if g.value("layer") == "Edge.Cuts"]
    require(len(edges) == len(perimeter), "Native outline/manifest edge count differs")
    for edge, a, b in zip(edges, perimeter, perimeter[1:]+perimeter[:1]):
        for key, point in (("start", a), ("end", b)):
            native = list(map(float, edge.child(key).atoms()[1:3]))
            require(all(abs(n-100-p) < 1e-6 for n, p in zip(native, point)),
                    "Native substrate outline differs from mechanical handoff")
    contact_interface = json.loads((OUTPUT / "battery-contact-interface.json").read_text())
    require(contact_interface == draft.contact_interface(front_z), "Contact primitive axial translation/geometry differs")
    usb = manifest["usb_interface"]
    require(usb["signal_ground_net"] == "GND" and
            usb["shell_anchor_nets"] == {"M1": None, "M2": None, "M3": None, "M4": None},
            "USB signal-ground/shield assignment was misrepresented")
    for pad in footprints["X6"].children("pad"):
        if pad.atoms()[1] in usb["shell_anchor_nets"]:
            require(pad.value("net") is None, "Unreviewed USB shield bond added")
    usb_at = list(map(float, footprints["X6"].child("at").atoms()[1:]))
    require(abs(usb_at[1]-100-5.08-usb["body_mouth_center_common_xy_mm"][1]) < 1e-6,
            "USB mouth coordinate differs from actual native F.Fab location")
    require([usb["body_front_z_mm"], usb["body_back_z_mm"]] == [round(front_z-3.5, 6), front_z],
            "USB body was not translated with the complete stack")
    require(abs(manifest["board"]["usb_tongue"]["outer_y_mm"] -
                usb["body_mouth_center_common_xy_mm"][1] - 1.05) < 1e-6,
            "USB tongue lost its retained body/anchor support offset")
    if manifest["placement_xy_seed_sha256"]:
        seed = json.loads((OUTPUT / "placement-xy-seed.json").read_text())
        for ref, pose in seed["poses"].items():
            if ref == "X6":
                continue
            fp = footprints[ref]
            source = parts[ref]
            at = list(map(float, fp.child("at").atoms()[1:]))
            dx, dy = draft.base.rotate(source["raw_cx"], -source["raw_cy"] if pose["side"] == "B" else source["raw_cy"], at[2])
            require(abs(at[0]-100+dx-pose["x"]) < 1e-6 and abs(at[1]-100+dy-pose["y"]) < 1e-6 and
                    abs(((at[2]-pose["angle"]+180)%360)-180) < 1e-6 and fp.value("layer")[0] == pose["side"],
                    "Non-USB XY/rotation/face changed during bounded stack translation: "+ref)
    for contact in contact_interface["contacts"]:
        fp = footprints[contact["reference"]]
        at = list(map(float, fp.child("at").atoms()[1:]))
        actual = []
        for pad in fp.children("pad"):
            px, py = map(float, pad.child("at").atoms()[1:3])
            dx, dy = draft.base.rotate(px, py, at[2])
            actual.append([at[0]-100+dx, at[1]-100+dy])
        require(all(all(abs(a-b) < 1e-6 for a, b in zip(xy, expected["center_mm"][:2]))
                    for xy, expected in zip(actual, contact["pads"])),
                "Drawing-based contact lands differ from mechanical interface")
    require({s.properties().get("Reference") for s in schematic.children("symbol")} >= set(draft.NEW_PINS),
            "Missing native schematic symbols")
    # Preserve the original core/boost/audio relative placements; U1 is smaller, not rerouted.
    old_manifest = json.loads((SOURCE / "placement-manifest.json").read_text())
    old_components = {p["reference"]: p for p in old_manifest["components"]}
    for ref in draft.base.CORE | draft.wing.BOOST | draft.wing.AMP:
        require(all(by_ref[ref][k] == old_components[ref][k] for k in ("x_mm", "y_mm", "rotation_deg", "side")),
                "Quiet core/power-loop cluster altered: "+ref)
    erc = json.loads((OUTPUT / "reports" / "erc.json").read_text())
    findings = [v for s in erc["sheets"] for v in s["violations"]]
    require(not findings, "Native ERC findings remain")
    drc = json.loads((OUTPUT / "reports" / "drc.json").read_text())
    unfinished = {"silk_over_copper", "text_height", "silk_overlap", "text_thickness", "silk_edge_clearance"}
    require(all(v["type"] in unfinished | {"hole_clearance"} for v in drc["violations"]),
            "Substantive native DRC findings remain; inspect the complete report")
    holes = [v for v in drc["violations"] if v["type"] == "hole_clearance"]
    require(len(holes) == 4 and all(all("X6" in i["description"] for i in v["items"]) for v in holes),
            "Unexpected hole clearance finding; only the inherited four X6 findings are documented")
    parity = drc["schematic_parity"]
    require(len(parity) == 46 and all("No corresponding pin found in schematic" in v["description"] for v in parity),
            "Unexpected CLI schematic parity finding")
    result = {"status": "Native correspondence verified; NOT electrical function/safety/fabrication approval",
              "fitted_components": len(by_ref), "fitted_by_side": dict(Counter(p["side"] for p in by_ref.values())),
              "physical_pad_records": physical, "numbered_copper_pad_records": electrical,
              "retained_pin_net_assignments_checked": len(retained), "raw_cell_negative_pins": sorted(raw_neg),
              "x1_removed_all_units_and_footprint": True, "native_erc_findings": 0,
              "native_drc_counts": dict(Counter(v["type"] for v in drc["violations"])),
              "unconnected_items": len(drc["unconnected_items"]), "known_cli_parity_findings": len(parity),
              "paired_editor_gui_review_performed": False,
              "manifest_sha256": draft.sha(OUTPUT / "placement-manifest.json"),
              "native_binding_sha256": draft.sha(OUTPUT / "reports" / "native-input-bindings.json"),
              "checker_sha256": draft.sha(__file__),
              "gates": ["No routing; four inherited USB hole clearance violations are open, not waived.",
                        "Reversed cell and hot/cold charging are NOT electronically inhibited in this draft.",
                        "Charge profile, low-cell nuisance cutoff, fault-current/thermal/SOA and reset behavior need bench review.",
                        "No live cell or child-use approval; use inert models for current mechanical review."]}
    draft.write(OUTPUT / "reports" / "correspondence-review.json", json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-native", action="store_true")
    parser.add_argument("--kicad-cli", type=Path, default=draft.CLI)
    args = parser.parse_args()
    if args.run_native:
        run_native(args.kicad_cli)
    check()


if __name__ == "__main__":
    main()
