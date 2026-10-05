#!/usr/bin/env python3
"""Build and check the two source-bound October 5 Quilter input derivatives."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

from kicad_sexpr import apply_edits, load, loads


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "hardware" / "handbell" / "iterations" / "printed-bell-four-layer"
REPORTS = REPO / "docs" / "measurements" / "2026-09-27-router-bakeoff"
WORKFLOW = REPO / "docs" / "design-inputs" / "2026-10-02-quilter-workflow.json"
SOURCE_HASHES = {
    "handbell.kicad_pcb": "adc262b3e7056cb9031387c55262b5cf99e599ae6e28970f9784f5237e662314",
    "handbell.kicad_pro": "8213261803c4a032c6351311ed43db6249720a8cb334ebd15e3daca210899990",
    "handbell.kicad_sch": "ec93cc6f6f03bb91dd05199d2e0b4cab6b542567031e484fe8098056992ab69e",
    "placement-manifest.json": "b849b5defb95f010f555d43b6d261fdea3ef37e240aee0190a607fb519c642f8",
    "battery-contact-interface.json": "f96133d9f044600167477bcddbf67c43311ed0897066db9fa63d8e7f8118467b",
}
NS = uuid.UUID("cc59ed69-b83e-4553-93eb-1d497151a26e")
REQUIRED_REPORT_HASHES = {
    "quilter-prot-cout-release-contract-2026-10-04.json":
        "cc23592a8060db8a2732ff91954ff55e3177fbf733b22173b74062b7d4e5f896",
    "quilter-preserved-clock-qualification-2026-10-04.json":
        "e5e407129d1d7983c26921d09541ada6c623494adc6e32e356443ddd9d59ecc9",
    "quilter-preserved-clock-boundary-recovery-2026-10-05.json":
        "f436c0811eca7ec0e6893256c0ddd72444ee2c70cd012c83912695db42a000e1",
    "quilter-trial-envelope-2026-10-03.json":
        "4178978d8e52db4d0b498e9e12aafdca5e43f098e43a7d084877ece1ed0da655",
}
PROFILES = {
    "four-3313": {
        "construction": "JLC04161H-3313",
        "layers": [("F.Cu", "signal"), ("In1.Cu", "power"), ("In2.Cu", "signal"), ("B.Cu", "signal")],
        "gaps": [(0.0994, "3313*1 prepreg", 4.1), (1.265, "core", 4.6),
                 (0.0994, "3313*1 prepreg", 4.1)],
        "planes": ["In1.Cu"],
    },
    "six-3313": {
        "construction": "JLC06161H-3313",
        "layers": [("F.Cu", "signal"), ("In1.Cu", "power"), ("In2.Cu", "signal"),
                   ("In3.Cu", "power"), ("In4.Cu", "power"), ("B.Cu", "signal")],
        "gaps": [(0.0994, "3313*1 prepreg", 4.1), (0.55, "core", 4.6),
                 (0.1088, "2116*1 prepreg", 4.16), (0.55, "core", 4.6),
                 (0.0994, "3313*1 prepreg", 4.1)],
        "planes": ["In1.Cu", "In3.Cu", "In4.Cu"],
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ident(name: str) -> str:
    return str(uuid.uuid5(NS, name))


def q(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def net_name(node) -> str:
    net = node.child("net")
    if net is None or len(net.atoms()) != 2:
        raise ValueError(f"unexpected net syntax on {node.head}")
    return net.atoms()[1]


def outline_polygon() -> list[tuple[float, float]]:
    points = []
    # Clockwise D45 disk plus USB tongue; 48 segments bound arc sag below 0.0121 mm.
    for i in range(49):
        angle = math.pi - math.pi * i / 48
        points.append((100 + 22.5 * math.cos(angle), 100 + 22.5 * math.sin(angle)))
    edge_angle = math.asin(5.75 / 22.5)
    for i in range(1, 25):
        angle = -math.pi * i / 48
        if angle <= -math.pi / 2 + edge_angle:
            break
        points.append((100 + 22.5 * math.cos(angle), 100 + 22.5 * math.sin(angle)))
    points.extend([(105.75, 78.247127), (105.75, 73.15), (94.25, 73.15),
                   (94.25, 78.247127)])
    for i in range(24, 0, -1):
        angle = -math.pi + math.pi * i / 48
        if angle >= -math.pi / 2 - edge_angle:
            continue
        points.append((100 + 22.5 * math.cos(angle), 100 + 22.5 * math.sin(angle)))
    return points


def polygon_text(points) -> str:
    return " ".join(f"(xy {x:.6f} {y:.6f})" for x, y in points)


def edge_items() -> list[str]:
    records = read_json(REPORTS / "quilter-trial-envelope-2026-10-03.json")[
        "analytic_outline"]["ordered_closed_clockwise_records"]
    result = []
    for index, row in enumerate(records):
        if row["type"] == "line":
            result.append(
                f'(gr_line (start {row["start_native_xy_mm"][0]} {row["start_native_xy_mm"][1]}) '
                f'(end {row["end_native_xy_mm"][0]} {row["end_native_xy_mm"][1]}) '
                f'(stroke (width 0.05) (type default)) (layer "Edge.Cuts") '
                f'(uuid "{ident("edge/" + str(index))}"))'
            )
        else:
            result.append(
                f'(gr_arc (start {row["start_native_xy_mm"][0]} {row["start_native_xy_mm"][1]}) '
                f'(mid {row["mid_native_xy_mm"][0]} {row["mid_native_xy_mm"][1]}) '
                f'(end {row["end_native_xy_mm"][0]} {row["end_native_xy_mm"][1]}) '
                f'(stroke (width 0.05) (type default)) (layer "Edge.Cuts") '
                f'(uuid "{ident("edge/" + str(index))}"))'
            )
    return result


def rule_area(name: str, layer: str, points, key: str, flags=None, allowed=False) -> str:
    if flags is None:
        state = "allowed" if allowed else "not_allowed"
        flags = {field: state for field in
                 ("tracks", "vias", "pads", "copperpour", "footprints")}
    serialized_flags = " ".join(f"({field} {flags[field]})" for field in
                                ("tracks", "vias", "pads", "copperpour", "footprints"))
    return (
        f'(zone (layer {q(layer)}) (uuid "{ident(key)}") (name {q(name)}) '
        f'(hatch edge 0.5) (connect_pads (clearance 0)) (min_thickness 0.25) '
        f'(keepout {serialized_flags}) (polygon (pts {polygon_text(points)})))'
    )


def setup_text(profile) -> str:
    rows = ['(setup', '  (stackup']
    for index, ((layer, _), copper) in enumerate(zip(profile["layers"], [0.035] +
                                                       [0.0152] * (len(profile["layers"]) - 2) +
                                                       [0.035])):
        rows.append(f'    (layer "{layer}" (type "copper") (thickness {copper}))')
        if index < len(profile["gaps"]):
            thickness, material, dk = profile["gaps"][index]
            dielectric_type = "core" if material == "core" else "prepreg"
            rows.append(
                f'    (layer "dielectric {index + 1}" (type "{dielectric_type}") '
                f'(thickness {thickness}) (material "{material}") (epsilon_r {dk}))'
            )
    rows.extend([
        '    (copper_finish "None")', '    (dielectric_constraints no)', '  )',
        '  (pad_to_mask_clearance 0)', ')',
    ])
    return "\n".join(rows)


def layers_text(profile) -> str:
    ids = {"F.Cu": 0, "B.Cu": 2, "In1.Cu": 4, "In2.Cu": 6, "In3.Cu": 8, "In4.Cu": 10}
    rows = ["(layers"]
    for name, role in profile["layers"]:
        rows.append(f'  ({ids[name]} "{name}" {role})')
    rows.extend([
        '  (9 "F.Adhes" user "F.Adhesive")', '  (11 "B.Adhes" user "B.Adhesive")',
        '  (13 "F.Paste" user)', '  (15 "B.Paste" user)',
        '  (5 "F.SilkS" user "F.Silkscreen")', '  (7 "B.SilkS" user "B.Silkscreen")',
        '  (1 "F.Mask" user)', '  (3 "B.Mask" user)', '  (17 "Dwgs.User" user "User.Drawings")',
        '  (19 "Cmts.User" user "User.Comments")', '  (21 "Eco1.User" user "User.Eco1")',
        '  (23 "Eco2.User" user "User.Eco2")', '  (25 "Edge.Cuts" user)', '  (27 "Margin" user)',
        '  (31 "F.CrtYd" user "F.Courtyard")', '  (29 "B.CrtYd" user "B.Courtyard")',
        '  (35 "F.Fab" user)', '  (33 "B.Fab" user)', '  (39 "User.1" user)',
        '  (41 "User.2" user)', '  (43 "User.3" user)', '  (45 "User.4" user)', ')',
    ])
    return "\n".join(rows)


def build(output: Path) -> dict:
    for name, expected in SOURCE_HASHES.items():
        if sha(SOURCE / name) != expected:
            raise RuntimeError(f"source hash mismatch: {name}")
    for name, expected in REQUIRED_REPORT_HASHES.items():
        if sha(REPORTS / name) != expected:
            raise RuntimeError(f"report hash mismatch: {name}")
    workflow = read_json(WORKFLOW)
    fixed = workflow["selected_comparison_retention"]["fixed_references"]
    if len(fixed) != 32 or len(set(fixed)) != 32:
        raise RuntimeError("fixed32 contract mismatch")
    cout = read_json(REPORTS / "quilter-prot-cout-release-contract-2026-10-04.json")
    clock = read_json(REPORTS / "quilter-preserved-clock-qualification-2026-10-04.json")
    selected = set(cout["selection"]["retained_uuids"])
    selected.update(clock["union_with_original177"]["addition_uuids"])
    if len(selected) != 209:
        raise RuntimeError("selected209 contract mismatch")
    source_text, root = load(SOURCE / "handbell.kicad_pcb")
    footprints = root.children("footprint")
    refs = {fp.properties()["Reference"]: fp for fp in footprints}
    if len(refs) != 104 or len(footprints) != 104:
        raise RuntimeError("source footprint population mismatch")
    if sum(len(fp.children("pad")) for fp in footprints) != 325:
        raise RuntimeError("source pad population mismatch")
    eligible = sorted(set(refs) - set(fixed))
    if len(eligible) != 72:
        raise RuntimeError("eligible72 contract mismatch")
    guards = read_json(REPORTS / "quilter-native-guard-encoding-2026-10-04.json")["native_encoding"]
    contacts = read_json(REPORTS / "quilter-contact-via-mask-2026-10-03.json")[
        "domains"]["native_via_only_rule_areas_expanded_each_edge_0_25_mm"]
    move_map = {}
    summaries = {}
    for profile_id, profile in PROFILES.items():
        package = output / profile_id
        package.mkdir(parents=True)
        parts = []
        for item in root.children():
            raw = source_text[item.start:item.end]
            if item.head == "layers":
                parts.append(layers_text(profile))
            elif item.head == "setup":
                parts.append(setup_text(profile))
            elif item.head == "footprint":
                ref = item.properties()["Reference"]
                if ref in fixed:
                    parts.append(raw)
                else:
                    at = item.child("at")
                    atoms = at.atoms()
                    old = [float(atoms[1]), float(atoms[2])]
                    index = eligible.index(ref)
                    new = [140.0 + 20.0 * (index % 9), 140.0 + 20.0 * (index // 9)]
                    replacement = f'(at {new[0]:.6f} {new[1]:.6f}'
                    if len(atoms) > 3:
                        replacement += " " + " ".join(atoms[3:])
                    replacement += ")"
                    moved = apply_edits(raw, [(at.start - item.start, at.end - item.start, replacement)])
                    parts.append(moved)
                    move_map.setdefault(ref, {"from_native_xy_mm": old, "to_native_xy_mm": new})
            elif item.head in {"segment", "via"}:
                if item.value("uuid") in selected:
                    parts.append(raw)
            elif item.head == "zone":
                if item.child("keepout") is not None:
                    parts.append(raw)
            elif item.head in {"gr_line", "gr_arc"} and item.value("layer") == "Edge.Cuts":
                continue
            else:
                parts.append(raw)
        parts.extend(edge_items())
        room_points = outline_polygon()
        parts.append(rule_area("QUILTER_F_PLACEMENT_ROOM", "F.Cu", room_points,
                               f"{profile_id}/placement-room", allowed=True))
        for row in guards["source_obligation_mapping"]:
            if not row["all_five_flags_not_allowed"]:
                raise RuntimeError("selected private guard flags are not the exercised all-five policy")
            points = [tuple(p) for p in row["native_polygon_points_mm"]]
            parts.append(rule_area(row["native_name"], row["layer"], points,
                                   f'{profile_id}/private/{row["native_guard_uuid"]}'))
        if profile_id == "six-3313":
            for row in guards["six_extra_via_guards"]:
                x0, y0, x1, y1 = row["native_bounds_mm"]
                points = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
                parts.append(rule_area(row["name"], row["layer"], points,
                                       f'{profile_id}/private/{row["native_guard_uuid"]}'))
        for row in contacts:
            x0, x1 = row["x_min_mm"] + 100, row["x_max_mm"] + 100
            y0, y1 = row["y_min_mm"] + 100, row["y_max_mm"] + 100
            points = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            contact_flags = {
                "tracks": "not_allowed", "vias": "not_allowed", "pads": "allowed",
                "copperpour": "not_allowed", "footprints": "allowed",
            }
            parts.append(rule_area("CONTACT_METAL_GUARD_" + row["name"], "B.Cu", points,
                                   f'{profile_id}/contact/{row["name"]}', flags=contact_flags))
        for layer in profile["planes"]:
            parts.append(
                f'(zone (net "GND") (layer "{layer}") '
                f'(uuid "{ident(profile_id + "/plane/" + layer)}") '
                f'(name "PROTECTED_GND_{layer}") (hatch edge 0.5) '
                f'(connect_pads (clearance 0.2)) (min_thickness 0.1778) '
                f'(fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3)) '
                f'(polygon (pts {polygon_text(room_points)})))'
            )
        pcb_text = "(kicad_pcb\n" + "\n".join(parts) + "\n)\n"
        parsed = loads(pcb_text)
        ids = [n.value("uuid") for n in parsed.walk() if n.child("uuid")]
        if len(ids) != len(set(ids)):
            raise RuntimeError(f"duplicate UUID in {profile_id}")
        (package / "handbell.kicad_pcb").write_text(pcb_text, encoding="utf-8")
        shutil.copyfile(SOURCE / "handbell.kicad_sch", package / "handbell.kicad_sch")
        project = read_json(SOURCE / "handbell.kicad_pro")
        rules = project["board"]["design_settings"]["rules"]
        rules.update(min_clearance=0.2, min_copper_edge_clearance=0.25,
                     min_track_width=0.1778, min_via_diameter=0.65,
                     min_through_hole_diameter=0.35, min_via_annular_width=0.15)
        project["net_settings"]["classes"][0].update(
            clearance=0.2, track_width=0.1778, via_diameter=0.65, via_drill=0.35)
        write_json(package / "handbell.kicad_pro", project)
        retained = [x for x in parsed.children() if x.head in {"segment", "via"}]
        summary = {
            "status": "CONSTRUCTED_STATIC_CHECKED_NATIVE_PENDING",
            "profile": profile_id,
            "supplier_construction": profile["construction"],
            "physical_copper_order": [x[0] for x in profile["layers"]],
            "dielectric_gaps_mm": [x[0] for x in profile["gaps"]],
            "material_rows": [{"material": x[1], "thickness_mm": x[0], "Dk": x[2]}
                              for x in profile["gaps"]],
            "outer_copper_mm": 0.035,
            "inner_copper_mm": 0.0152,
            "finished_thickness_nominal_mm": 1.6,
            "displayed_copper_dielectric_sum_not_padded_mm":
                1.5642 if profile_id == "four-3313" else 1.5384,
            "counts": {
                "references": len(parsed.children("footprint")),
                "pads": sum(len(x.children("pad")) for x in parsed.children("footprint")),
                "fixed_references": len(fixed), "eligible_references": len(eligible),
                "retained_tracks": sum(x.head == "segment" for x in retained),
                "retained_vias": sum(x.head == "via" for x in retained),
                "private_guards": 18 if profile_id == "four-3313" else 22,
                "contact_guards": 8, "source_rule_areas": 19,
                "new_plane_definitions_unfilled": len(profile["planes"]),
            },
            "fixed_references": fixed,
            "eligible_references": eligible,
            "move_map": move_map,
            "placement_room": {
                "layer": "F.Cu", "all_keepout_restrictions": "allowed",
                "assignment_semantics": "Manifest obligation; native room alone is not proof of Quilter F-only enforcement",
                "polygon_vertex_count": len(room_points),
                "maximum_arc_chord_error_mm": 22.5 * (1 - math.cos(math.pi / 96)),
            },
            "reservations": {
                "source": "quilter-trial-envelope-2026-10-03.json#/reservation_layer",
                "MH1_MH2": "R3.2 whole-mount reservations",
                "planning_proxies": ["J1", "J2", "X6"],
                "J2_allowance_mm_already_in_proxy": 0.7,
                "encoding": "MISSING NATIVE FOOTPRINT-ONLY RESERVATIONS; manifest is not enforcement",
            },
            "electrical_obligations": {
                "COUT_restore": ["U6.2", "Q5.B2", "R29.1"],
                "R29.2_unchanged": "/PROT_FET_RETURN",
                "protected_ground_planes": profile["planes"],
                "CELL_NEG_is_ground": False,
                "USB_differential_target_ohms": 90,
                "source_pin_and_circuit_comprehension": "explicit later importer review; sidecar is not asserted imported",
            },
            "new_route_rules_mm": {
                "clearance": 0.2, "edge": 0.25, "width_floor": 0.1778,
                "via_diameter": 0.65, "via_drill": 0.35, "annular_ring": 0.15,
            },
            "retained_conflicts_expected": [
                "Four U4 0.604/0.350 vias have 0.127 mm rings below the new-via rule.",
                "C24 0.600/0.300 is retained unchanged; all 18 retained vias are exempt from resizing only, not DRC review.",
                "All opens from removed replaceable copper are expected but must be classified.",
                "Exact inherited source/guard overlaps require differential review; no global waiver is encoded.",
            ],
            "mandatory_process": "Four U4 and one C24 vias remain resin-filled, planarized and copper-capped obligations.",
            "hashes": {name: sha(package / name) for name in
                       ("handbell.kicad_pcb", "handbell.kicad_pro", "handbell.kicad_sch")},
        }
        write_json(package / "input-manifest.json", summary)
        summaries[profile_id] = summary
    write_json(output / "construction-result.json", {
        "source_hashes": SOURCE_HASHES,
        "selected_membership": {"total": 209, "tracks": 191, "vias": 18},
        "packages": summaries,
        "source_native_loads": 0,
        "cloud_actions": 0,
    })
    return summaries


def native_check(output: Path, kicad_bin: Path) -> dict:
    handle = os.add_dll_directory(str(kicad_bin))
    try:
        sys.path.insert(0, str(kicad_bin / "Lib" / "site-packages"))
        pcbnew = importlib.import_module("pcbnew")
        result = {"pcbnew_version": pcbnew.GetBuildVersion(), "source_native_loads": 0, "packages": {}}
        for profile_id in PROFILES:
            package = output / profile_id
            pcb_path = package / "handbell.kicad_pcb"
            board = pcbnew.LoadBoard(str(pcb_path))
            pcbnew.SaveBoard(str(pcb_path), board)
            del board
            board = pcbnew.LoadBoard(str(pcb_path))
            refs = list(board.GetFootprints())
            pads = [pad for fp in refs for pad in fp.Pads()]
            zones = list(board.Zones())
            native = {
                "loads": 2, "saves": 1, "references": len(refs), "pads": len(pads),
                "tracks": len(list(board.Tracks())),
                "rule_areas": sum(z.GetIsRuleArea() for z in zones),
                "zones_total": len(zones),
                "copper_layer_count": board.GetCopperLayerCount(),
                "pcb_sha256_after_native_save": sha(pcb_path),
            }
            del board
            if profile_id == "four-3313":
                native["drc"] = {
                    "status": "NOT_RERUN_PER_ROOT_REVIEW",
                    "prior_r1_result": "timed out after 30.171 seconds without a report",
                }
                result["packages"][profile_id] = native
                manifest_path = package / "input-manifest.json"
                manifest = read_json(manifest_path)
                manifest["status"] = "NATIVE_ROUNDTRIPPED_HELD"
                manifest["final_native_hashes"] = {
                    "handbell.kicad_pcb": sha(pcb_path),
                    "handbell.kicad_pro": sha(package / "handbell.kicad_pro"),
                    "handbell.kicad_sch": sha(package / "handbell.kicad_sch"),
                }
                manifest["native_result"] = native
                write_json(manifest_path, manifest)
                continue
            drc_path = package / "drc.json"
            started = time.monotonic()
            command = [str(kicad_bin / "kicad-cli.exe"), "pcb", "drc", "--format", "json",
                       "--output", str(drc_path), str(pcb_path)]
            try:
                child = subprocess.run(command, cwd=package, capture_output=True, timeout=30)
                native["drc"] = {
                    "numeric_child_returncode": child.returncode,
                    "timed_out": False,
                    "elapsed_seconds": round(time.monotonic() - started, 6),
                    "stdout": child.stdout.decode(errors="replace"),
                    "stderr": child.stderr.decode(errors="replace"),
                    "output_exists": drc_path.is_file(),
                }
                if drc_path.is_file():
                    parsed = read_json(drc_path)
                    native["drc"].update(
                        violations=len(parsed.get("violations", [])),
                        unconnected_items=len(parsed.get("unconnected_items", [])),
                        schematic_parity=len(parsed.get("schematic_parity", [])),
                        output_sha256=sha(drc_path),
                    )
            except subprocess.TimeoutExpired as exc:
                native["drc"] = {
                    "numeric_child_returncode": None, "timed_out": True,
                    "elapsed_seconds": round(time.monotonic() - started, 6),
                    "stdout": (exc.stdout or b"").decode(errors="replace"),
                    "stderr": (exc.stderr or b"").decode(errors="replace"),
                    "output_exists": drc_path.is_file(),
                }
            result["packages"][profile_id] = native
            manifest_path = package / "input-manifest.json"
            manifest = read_json(manifest_path)
            manifest["status"] = "NATIVE_ROUNDTRIPPED_HELD"
            manifest["final_native_hashes"] = {
                "handbell.kicad_pcb": sha(pcb_path),
                "handbell.kicad_pro": sha(package / "handbell.kicad_pro"),
                "handbell.kicad_sch": sha(package / "handbell.kicad_sch"),
            }
            manifest["native_result"] = native
            write_json(manifest_path, manifest)
        write_json(output / "native-result.json", result)
        return result
    finally:
        handle.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--native-check", action="store_true")
    parser.add_argument("--kicad-bin", type=Path)
    args = parser.parse_args()
    if "SUPERVISED_PROCESS_RECEIPT" not in os.environ:
        raise RuntimeError("direct execution forbidden; use tools/supervise_process.py")
    if args.native_check:
        if not args.output.is_dir() or args.kicad_bin is None:
            raise RuntimeError("native check needs an existing output and --kicad-bin")
        native_check(args.output, args.kicad_bin)
    else:
        if args.output.exists():
            raise RuntimeError("output already exists")
        args.output.mkdir(parents=True)
        build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
