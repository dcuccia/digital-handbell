# SPDX-License-Identifier: MIT
"""Validate all-front stage-1 CAD, electrical floorplanning and exact native evidence."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import draft_printed_bell_placement as draft
from kicad_sexpr import load, pcb_net_name

ROOT, SOURCE, OUTPUT = draft.ROOT, draft.SOURCE, draft.OUTPUT
REPORTS = ["erc.json", "drc.json", "handbell-netlist.xml", "handbell-schematic.pdf",
           "schematic-svg/handbell.svg", "front-native.svg", "back-native.svg",
           "front-native.pdf", "back-native.pdf"]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inputs():
    files = [OUTPUT / name for name in (
        "handbell.kicad_sch", "handbell.kicad_pcb", "handbell.kicad_pro", "Handbell.kicad_sym",
        "T8.kicad_sym", "fp-lib-table", "sym-lib-table", "placement-manifest.json",
        "battery-contact-interface.json", "design-input-snapshot.json", "placement-build-report.json",
        "source-evidence.json")]
    files += sorted((OUTPUT / "libraries").rglob("*.kicad_mod"))
    files += [SOURCE / name for name in (
        "handbell.kicad_sch", "handbell.kicad_pcb", "handbell.kicad_pro", "placement-manifest.json",
        "battery-contact-interface.json", "source-evidence.json", "reports/handbell-netlist.xml", "reports/drc.json")]
    files += [ROOT / "tools" / name for name in (
        "draft_printed_bell_placement.py", "check_printed_bell_placement.py", "draft_t8_placement.py",
        "draft_wing_placement.py", "place_handbell.py", "placement_geometry.py", "kicad_sexpr.py")]
    for directory in draft.local_libraries().values():
        used = OUTPUT / "libraries" / directory.name
        if used.is_dir():
            files += [directory / path.name for path in used.glob("*.kicad_mod")]
    return {str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path): draft.sha(path)
            for path in files}


def run_native(cli):
    require(cli.is_file(), "Missing KiCad CLI")
    version = subprocess.check_output([str(cli), "--version"], text=True).strip()
    require(version == "10.0.6", "This release requires exercised KiCad 10.0.6, found "+version)
    before = inputs()
    work = OUTPUT / "reports" / ".native-run"
    require(not work.exists(), "Inspect existing native staging directory before retrying")
    work.mkdir()
    schematic, pcb = str(OUTPUT / "handbell.kicad_sch"), str(OUTPUT / "handbell.kicad_pcb")
    commands = [
        ["sch", "erc", "--format", "json", "--severity-all", "--output", str(work / "erc.json"), schematic],
        ["sch", "export", "netlist", "--format", "kicadxml", "--output", str(work / "handbell-netlist.xml"), schematic],
        ["pcb", "drc", "--format", "json", "--schematic-parity", "--severity-all", "--output", str(work / "drc.json"), pcb],
        ["sch", "export", "pdf", "--exclude-pdf-metadata", "--output", str(work / "handbell-schematic.pdf"), schematic],
        ["sch", "export", "svg", "--output", str(work / "schematic-svg"), schematic],
    ]
    for side, label in (("F", "front"), ("B", "back")):
        layers = f"{side}.Cu,{side}.Fab,{side}.SilkS,Edge.Cuts"
        commands += [
            ["pcb", "export", "svg", "--mode-single", "--layers", layers, "--fit-page-to-board",
             "--exclude-drawing-sheet", "--output", str(work / f"{label}-native.svg"), pcb],
            ["pcb", "export", "pdf", "--mode-single", "--layers", layers, "--scale", "3", "--exclude-value",
             "--output", str(work / f"{label}-native.pdf"), pcb],
        ]
    try:
        logs = []
        for command in commands:
            result = subprocess.run([str(cli), *command], cwd=ROOT, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=600)
            logs.append({"command": command, "exit_code": result.returncode,
                         "stdout": result.stdout, "stderr": result.stderr})
            require(result.returncode == 0, f"Native command failed: {command}\n{result.stdout}\n{result.stderr}")
            print(result.stdout.strip())
        require(before == inputs(), "CAD or bound dependencies changed during native validation")
        for name in REPORTS:
            target = OUTPUT / "reports" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(work / name, target)
        binding = {"generated_utc": datetime.now(timezone.utc).isoformat(), "kicad_version": version,
                   "kicad_cli_sha256": draft.sha(cli), "inputs": before,
                   "reports": {name: draft.sha(OUTPUT / "reports" / name) for name in REPORTS},
                   "commands": logs,
                   "scope": "Stage-1 native evidence only; no route, thermal, charging or functional approval"}
        draft.write(OUTPUT / "reports" / "native-input-bindings.json", json.dumps(binding, indent=2)+"\n")
    finally:
        shutil.rmtree(work)


def connections(path):
    xml = ET.parse(path).getroot()
    return {(pin.get("ref"), pin.get("pin")): net.get("name")
            for net in xml.findall("nets/net") for pin in net.findall("node")}


def canonical(node, flip=False):
    """Pad geometry, including local rotations and custom polygon copper, in F convention."""
    if node.head in {"uuid", "net", "pinfunction", "pintype"}:
        return None
    atoms = node.atoms()
    values = []
    atom_index = 0
    for item in node.items:
        if hasattr(item, "head"):
            child = canonical(item, flip)
            if child is not None:
                values.append(child)
        else:
            value = item.value
            if atom_index and node.head != "pad":
                try:
                    value = round(float(value), 9)
                    if flip and ((node.head in {"at", "xy", "start", "end", "mid", "center"} and atom_index == 2)
                                 or (node.head == "at" and atom_index == 3)):
                        value = -value
                except ValueError:
                    if flip and node.head in {"layer", "layers"} and value.startswith("B."):
                        value = "F."+value[2:]
            values.append(value)
            atom_index += 1
    return values


def pad_xy(fp, pad):
    at = list(map(float, fp.child("at").atoms()[1:]))
    local = list(map(float, pad.child("at").atoms()[1:3]))
    dx, dy = draft.base.rotate(*local, at[2] if len(at) > 2 else 0)
    return at[0]-100+dx, at[1]-100+dy


def electrical_screen(footprints):
    points = {(ref, pad.atoms()[1]): pad_xy(fp, pad) for ref, fp in footprints.items()
              for pad in fp.children("pad") if pad.atoms()[1]}
    def distance(a, b):
        return round(math.dist(points[a], points[b]), 6)
    metrics = []
    for name, left, right, limit in (
        ("QSPI clock", ("IC1", "52"), ("U1", "6"), 8.0),
        ("Flash bypass", ("U1", "8"), ("C10", "1"), 3.0),
        ("VREG input 1uF", ("IC1", "44"), ("C15", "1"), 3.5),
        ("VREG output 1uF", ("IC1", "45"), ("C8", "1"), 3.0),
        ("USB series D-", ("IC1", "46"), ("R9", "2"), 6.0),
        ("USB series D+", ("IC1", "47"), ("R10", "2"), 6.0),
        ("Crystal input", ("IC1", "20"), ("Y1", "3"), 6.0),
        ("Crystal output series resistor", ("IC1", "21"), ("R6", "2"), 4.0),
        ("Inductor SW", ("L1", "P$2"), ("U5", "5"), 4.0),
        ("Boost VIN capacitor", ("U5", "3"), ("C26", "1"), 4.0),
        ("Boost VIN capacitor return", ("U5", "4"), ("C26", "2"), 4.0),
        ("Boost output capacitor", ("U5", "6"), ("C27", "1"), 4.5),
        ("Boost output capacitor return", ("U5", "4"), ("C27", "2"), 5.0),
        ("Boost FB upper", ("U5", "1"), ("R23", "2"), 4.0),
        ("Boost FB lower", ("U5", "1"), ("R24", "1"), 5.0),
        ("Amplifier local PVDD", ("U4", "7"), ("C16", "1"), 3.0),
        ("Amplifier bulk PVDD", ("U4", "8"), ("C19", "1"), 5.0),
        ("BTL positive ferrite", ("U4", "9"), ("FB1", "1"), 4.0),
        ("BTL negative ferrite", ("U4", "10"), ("FB2", "1"), 4.5),
        ("Protector filtered supply", ("U6", "5"), ("C30", "1"), 3.5),
    ):
        d = distance(left, right)
        metrics.append({"name": name, "from": ".".join(left), "to": ".".join(right),
                        "straight_line_pad_distance_mm": d, "project_floorplan_max_mm": limit})
        require(d <= limit, f"Electrical floorplan spread: {name} {d} > {limit}")
    decoupling = []
    for pad in footprints["IC1"].children("pad"):
        net = pad.value("net")
        if net not in {"+3V3", "VCORE"}:
            continue
        candidates = []
        for ref in draft.POSES["core"]:
            if not ref.startswith("C"):
                continue
            for cap in footprints[ref].children("pad"):
                if cap.value("net") == net:
                    candidates.append((distance(("IC1", pad.atoms()[1]), (ref, cap.atoms()[1])), ref))
        d, ref = min(candidates)
        require(d <= 3.5, f"RP2040 power pad {pad.atoms()[1]} lacks local capacitor: {d}")
        decoupling.append({"mcu_pin": pad.atoms()[1], "net": net, "closest_capacitor": ref,
                           "power_pad_distance_mm": d})
    return {"critical_pairs": metrics, "rp2040_decoupling": decoupling,
            "scope": "Pad-to-pad straight lines, not routed lengths or manufacturer-approved distance limits. "
                     "Local copper loops, return paths, Kelvin sensing, thermal vias and BTL symmetry remain routing gates."}


def check():
    binding = json.loads((OUTPUT / "reports" / "native-input-bindings.json").read_text())
    require(binding["inputs"] == inputs(), "Stale native inputs: run --run-native")
    require(binding["reports"] == {name: draft.sha(OUTPUT / "reports" / name) for name in REPORTS},
            "Native report bytes changed after binding")
    manifest = json.loads((OUTPUT / "placement-manifest.json").read_text())
    build = json.loads((OUTPUT / "placement-build-report.json").read_text())
    require(manifest["schema_version"] == 2, "Schema-2 required")
    for field, name in (("generated_pcb_sha256", "handbell.kicad_pcb"),
                        ("schematic_sha256", "handbell.kicad_sch"),
                        ("battery_contact_interface_sha256", "battery-contact-interface.json")):
        require(manifest[field] == draft.sha(OUTPUT / name), "Manifest byte mismatch: "+name)
    require(draft.sha(OUTPUT / "handbell.kicad_sch") == draft.sha(SOURCE / "handbell.kicad_sch"),
            "Stage 1 must not change schematic logic, pin maps, values or charging profile")
    require(draft.sha(OUTPUT / "handbell.kicad_pro") == draft.sha(SOURCE / "handbell.kicad_pro"),
            "Unpermitted project-rule change")
    require(manifest["design_input_sha256"] == manifest["design_input_snapshot_sha256"] ==
            draft.sha(OUTPUT / "design-input-snapshot.json"), "Raw design-input snapshot changed")
    require(build["script_sha256"] == draft.sha(ROOT / "tools" / "draft_printed_bell_placement.py"), "Stale build report")
    require(not build["planning"]["planning_overlaps"], "Unresolved planning rectangle overlap")
    require(not build["planning"]["constraint_violations"], "Unresolved placement constraint")
    old_nets = connections(SOURCE / "reports" / "handbell-netlist.xml")
    new_nets = connections(OUTPUT / "reports" / "handbell-netlist.xml")
    require(old_nets == new_nets, "A schematic pin or net changed")
    _, old_board = load(SOURCE / "handbell.kicad_pcb")
    _, board = load(OUTPUT / "handbell.kicad_pcb")
    old_fp = {fp.properties()["Reference"]: fp for fp in old_board.children("footprint")}
    fp = {f.properties()["Reference"]: f for f in board.children("footprint")}
    require(set(fp) == set(old_fp) and len(fp) == 104, "Reference inventory changed")
    require(not any(board.children(kind) for kind in ("segment", "via", "zone")), "Stage 1 must remain unrouted")
    layers = [layer for layer in board.child("layers").children() if "signal" in layer.atoms()]
    require(len(layers) == 2, "Unexpected copper layer count")
    by_ref = {p["reference"]: p for p in manifest["components"]}
    actual_parts, _, _, _ = draft.read_parts()
    require(Counter(p["side"] for p in by_ref.values()) == {"F": 81, "B": 2}, "Incorrect fitted F/B accounting")
    require({p["reference"] for p in by_ref.values() if p["side"] == "B"} == draft.CONTACTS,
            "Only BT1/BT2 may remain on B")
    require(set(c["reference"] for c in manifest["copper_only_features"]) == draft.base.COPPER,
            "Copper-only feature inventory changed")
    require(manifest["dnp_footprint_reservations"] == ["C29"], "DNP inventory changed")
    pad_review = []
    for ref, footprint in fp.items():
        require(footprint.atoms()[1] == old_fp[ref].atoms()[1], "Replaced footprint: "+ref)
        require(footprint.properties()["Value"] == old_fp[ref].properties()["Value"], "Changed value: "+ref)
        old_pads, new_pads = old_fp[ref].children("pad"), footprint.children("pad")
        require(len(old_pads) == len(new_pads), "Pad count changed: "+ref)
        flip = old_fp[ref].value("layer") == "B.Cu" and footprint.value("layer") == "F.Cu"
        for index, (previous, current) in enumerate(zip(old_pads, new_pads)):
            number = current.atoms()[1]
            require(previous.atoms()[1] == number and previous.value("net") == current.value("net"),
                    f"Physical pad/net changed: {ref}.{number}")
            require(canonical(previous, flip) == canonical(current), f"Physical copper geometry changed: {ref}.{number}")
            expected = "GND" if ref.startswith("MH") else pcb_net_name(new_nets.get((ref, number)))
            require(current.value("net") == expected, f"Schematic/physical-pad mismatch: {ref}.{number}")
            pad_review.append({"reference": ref, "physical_pad_index": index, "pad_number": number,
                               "net": current.value("net"), "geometry_preserved": True, "B_to_F_transform": flip})
        if ref in by_ref:
            component = by_ref[ref]
            require(footprint.value("layer") == component["side"]+".Cu", "Manifest/native face mismatch: "+ref)
            attr = set(footprint.child("attr").atoms()[1:]) if footprint.child("attr") else set()
            require(not attr & {"exclude_from_bom", "exclude_from_pos_files", "dnp"}, "Fitted part excluded: "+ref)
            at = list(map(float, footprint.child("at").atoms()[1:]))
            require(math.dist(at[:2], [v+100 for v in component["native_origin_common_xy_mm"]]) < .000002,
                    "Manifest/native origin mismatch: "+ref)
            require(abs(at[2]+component["rotation_deg"]) < .000002, "Manifest/native rotation mismatch: "+ref)
            zmin, zmax = ((25-component["height_mm"], 25) if component["side"] == "F"
                          else (26.6, 26.6+component["height_mm"]))
            require([component["z_min_mm"], component["z_max_mm"]] == [zmin, zmax], "Wrong Z bounds: "+ref)
            part = actual_parts[ref]
            require([component["width_mm"], component["depth_mm"], component["height_mm"]] ==
                    [part["raw_w"], part["raw_h"], part["height"]], "Resized source body/height: "+ref)
            dx, dy = draft.base.rotate(part["raw_cx"], -part["raw_cy"] if component["side"] == "B"
                                       else part["raw_cy"], at[2])
            require(math.dist([at[0]-100+dx, at[1]-100+dy], [component["x_mm"], component["y_mm"]]) < .000002,
                    "Manifest proxy center is not actual native body center: "+ref)
        if ref in actual_parts:
            at = list(map(float, footprint.child("at").atoms()[1:]))
            draft.set_origin(actual_parts[ref], at[0]-100, at[1]-100, at[2])
    require(len(pad_review) == 325, "Physical pad accounting changed")
    require(fp["U1"].properties()["MPN"] == "W25Q16JVUXIQ TR", "Wrong 2 MB USON ordering code")
    require(all(p.value("net") is None for p in fp["X6"].children("pad") if p.atoms()[1] in {"M1", "M2", "M3", "M4"}),
            "USB anchors silently assigned")
    old_edges = [canonical(e) for e in old_board.children("gr_line") if e.value("layer") == "Edge.Cuts"]
    new_edges = [canonical(e) for e in board.children("gr_line") if e.value("layer") == "Edge.Cuts"]
    require(new_edges == old_edges, "T8 exact outline/tabs/tongue changed")
    require(manifest["board"]["outline_common_xy_mm"] ==
            json.loads((SOURCE / "placement-manifest.json").read_text())["board"]["outline_common_xy_mm"],
            "Manifest outline differs from the retained exact substrate")
    require(manifest["board"]["diameter_mm"] == 43 and manifest["board"]["thickness_mm"] == 1.6, "Board dimensions changed")
    for mount in manifest["mounting_holes"]:
        require(canonical(fp[mount["reference"]]) == canonical(old_fp[mount["reference"]]), "M2 interface changed")
    require(manifest["usb_interface"]["native_origin_common_xy_mm"] == [0, -22.82] and
            manifest["usb_interface"]["body_mouth_center_common_xy_mm"] == [0, -27.9], "USB interface changed")
    require(by_ref["L1"]["height_mm"] == 5 and by_ref["L1"]["z_min_mm"] == 20, "Inductor height shortened")
    native_planning = draft.plan_report(actual_parts)
    require(not native_planning["planning_overlaps"] and not native_planning["constraint_violations"],
            "Independent native-origin planning screen failed")
    speaker_screen = []
    for component in by_ref.values():
        if component["side"] != "F":
            continue
        part = actual_parts[component["reference"]]
        raw = {**part, "plan_w": part["raw_w"], "plan_h": part["raw_h"]}
        radius = draft.wing.rectangle_distance(raw, 0, 0)
        zmin = component["z_min_mm"]
        require(zmin > 16.5 or radius > 20, "Conservative speaker basket collision")
        require(zmin > 23.5 or radius > 10.85, "Conservative speaker magnet collision")
        speaker_screen.append({"reference": part["ref"], "minimum_proxy_radius_mm": round(radius, 6),
                               "z_min_mm": zmin, "magnet_radial_gap_mm": round(radius-10.85, 6),
                               "magnet_axial_gap_mm": round(zmin-23.5, 6)})
    contact = json.loads((OUTPUT / "battery-contact-interface.json").read_text())
    require(contact == draft.t8.contact_interface(25), "Contact datums or thin primitives changed beyond declared Z translation")
    electrical = electrical_screen(fp)
    erc = json.loads((OUTPUT / "reports" / "erc.json").read_text())
    erc_count = sum(len(sheet["violations"]) for sheet in erc["sheets"])
    require(erc_count == 0, "ERC is not clean")
    drc = json.loads((OUTPUT / "reports" / "drc.json").read_text())
    physical_types = Counter(v["type"] for v in drc["violations"])
    unexpected = set(physical_types)-{"silk_overlap", "silk_over_copper", "silk_edge_clearance",
                                      "text_height", "text_thickness", "hole_clearance"}
    require(not unexpected, "Unexpected physical DRC types: "+str(unexpected))
    require(physical_types["hole_clearance"] == 4, "Inherited four USB clearance findings changed")
    baseline_drc = json.loads((SOURCE / "reports" / "drc.json").read_text())
    def holes(report):
        return sorted(json.dumps(v, sort_keys=True) for v in report["violations"] if v["type"] == "hole_clearance")
    require(holes(drc) == holes(baseline_drc), "Inherited USB finding details changed")
    def parity(report):
        return sorted((v["type"], v["description"],
                       tuple(sorted((i["uuid"], i["description"].replace(" on B.Cu", " on F.Cu"))
                                    for i in v["items"]))) for v in report["schematic_parity"])
    require(parity(drc) == parity(baseline_drc), "New CLI parity finding identity")
    review = {
        "status": "Stage 1 completed; unrouted, conditional mechanical consumer interface, not functional signoff",
        "hashes": {name: draft.sha(OUTPUT / name) for name in (
            "placement-manifest.json", "handbell.kicad_pcb", "handbell.kicad_sch", "battery-contact-interface.json")},
        "native_binding_sha256": draft.sha(OUTPUT / "reports" / "native-input-bindings.json"),
        "inventory": {"references": 104, "fitted": 83, "F": 81, "B": 2, "copper_only": 18,
                      "DNP": ["C29"], "mounts": ["MH1", "MH2"], "physical_pad_records": 325,
                      "numbered_copper_pad_records": sum(bool(p["pad_number"]) for p in pad_review)},
        "erc_count": erc_count, "physical_drc_types": dict(physical_types),
        "unconnected_count": len(drc["unconnected_items"]),
        "schematic_parity_count": len(drc.get("schematic_parity", [])),
        "electrical_floorplan": electrical, "all_physical_pads": pad_review,
        "speaker_proxy_screen": speaker_screen,
        "native_geometry_scope": "Every physical pad's net and complete local copper/paste/mask/drill/custom-polygon "
                                 "geometry compared, including inverse B/F mirror and KiCad 10 local pad angles.",
    }
    draft.write(OUTPUT / "reports" / "correspondence-review.json", json.dumps(review, indent=2)+"\n")
    print(json.dumps({k: v for k, v in review.items()
                      if k not in {"all_physical_pads", "electrical_floorplan", "speaker_proxy_screen"}}, indent=2))


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
