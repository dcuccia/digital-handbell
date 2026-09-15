# SPDX-License-Identifier: MIT
"""Stage a small C6 move, shorter QSPI escape and local core-supply connection."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import uuid

import check_printed_bell_power_rework as check
from kicad_sexpr import apply_edits, load
from route_clock_local import PACKAGE, sha

BASE = "05889a98ea3b52861394930ebb34c306046f52fd88f9f100d5751a3dacce3be3"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--clear-c17-courtyard", action="store_true")
    parser.add_argument("--spread-core-column", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or sha(PACKAGE / "handbell.kicad_pcb") != BASE:
        raise ValueError("Require the pinned left-core checkpoint and a new staging directory")
    if args.spread_core_column and not args.clear_c17_courtyard:
        raise ValueError("Column correction requires the first courtyard-correction option")
    text, tree = load(PACKAGE / "handbell.kicad_pcb")
    fp = next(f for f in tree.children("footprint") if f.properties().get("Reference") == "C6")
    at = fp.child("at")
    assert at.atoms()[1:] == ["105.497898", "99.599744", "180"]
    edits = [(at.start, at.end, "(at 105.497898 99.999744 180)")]
    removed = {"4b83724d-1dab-5713-8037-94114a8745ff", "8149354a-fbd8-52cd-a5c8-eb324b57082e"}
    endpoints = {"5d8ee764-fc16-570b-bb11-c5fe22ef5e4c": ("end", [106.95, 99.4]),
                 "8cfb8500-6d1c-58c7-98cb-563715142538": ("start", [106.95, 99.4])}
    changes, deleted = [], []
    for segment in tree.children("segment"):
        uid = segment.value("uuid")
        if uid not in removed | endpoints.keys():
            continue
        assert segment.value("net") == "QSPI_DATA[3]" and float(segment.value("width")) == .1778
        old = {k: list(map(float, segment.child(k).atoms()[1:])) for k in ("start", "end")}
        if uid in removed:
            edits.append((segment.start, segment.end, ""))
            deleted.append({"uuid": uid, "old": old, "net": "QSPI_DATA[3]", "width_mm": .1778})
        else:
            key, point = endpoints[uid]
            node = segment.child(key)
            edits.append((node.start, node.end, f"({key} {point[0]} {point[1]})"))
            changes.append({"uuid": uid, "old": old, "new": {**old, key: point},
                            "net": "QSPI_DATA[3]", "width_mm_unchanged": .1778})
    assert len(changes) == len(deleted) == 2
    core_changes = []
    if args.clear_c17_courtyard:
        c17 = next(f for f in tree.children("footprint") if f.properties().get("Reference") == "C17")
        pose = c17.child("at")
        x, y, angle = pose.atoms()[1:]
        assert float(y) == 100.897675
        new_y = 101.217675 if args.spread_core_column else 101.007675
        edits.append((pose.start, pose.end, f"(at {x} {new_y} {angle})"))
        if args.spread_core_column:
            for ref, delta in (("C8", .23), ("C13", .14)):
                other = next(f for f in tree.children("footprint") if f.properties().get("Reference") == ref)
                pose = other.child("at")
                x, y, angle = pose.atoms()[1:]
                edits.append((pose.start, pose.end, f"(at {x} {float(y)+delta:.6f} {angle})"))
        bridge = {
            "e70cc137-e76b-5564-b300-9fc4582c0bfb": {"start"},
            "50ee0fe3-be40-5757-b167-5e4537bba4cf": {"start", "end"},
            "f466a216-ec52-563c-a64b-ada283d749fe": {"start", "end"},
            "f5cfecfa-ba37-5c71-b382-3d66e24e0eda": {"start", "end"},
            "75b4f4dd-4137-57a3-9222-82ffe72ea4b6": {"end"},
        }
        for segment in tree.children("segment"):
            uid = segment.value("uuid")
            if uid not in bridge:
                continue
            assert segment.value("net") == "VCORE"
            old = {k: list(map(float, segment.child(k).atoms()[1:])) for k in ("start", "end")}
            new = copy.deepcopy(old)
            for key in bridge[uid]:
                new[key][1] = round(new[key][1] + (.2711 if args.spread_core_column else .0561), 6)
                node = segment.child(key)
                edits.append((node.start, node.end, f"({key} {new[key][0]} {new[key][1]})"))
            if args.spread_core_column and uid == "75b4f4dd-4137-57a3-9222-82ffe72ea4b6":
                new["start"][1] = round(new["start"][1] + .23, 6)
                node = segment.child("start")
                edits.append((node.start, node.end, f'(start {new["start"][0]} {new["start"][1]})'))
            core_changes.append({"uuid": uid, "old": old, "new": new, "net": "VCORE",
                                 "width_mm_unchanged": float(segment.value("width"))})
        assert len(core_changes) == 5
    points = [(103.45, 99.8), (104.1, 99.8), (104.299744, 99.999744), (104.989898, 99.999744)]
    additions, records = [], []
    for index, (a, b) in enumerate(zip(points, points[1:])):
        uid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"digital-handbell/core-c6/{index}"))
        additions.append(f'\n(segment (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) '
                         f'(width 0.2) (layer "F.Cu") (net "VCORE") (uuid "{uid}"))')
        records.append({"uuid": uid, "start_mm": a, "end_mm": b, "width_mm": .2,
                        "layer": "F.Cu", "net": "VCORE"})
    for zone in tree.children("zone"):
        edits.extend((p.start, p.end, "") for p in zone.children("filled_polygon"))
    edits.append((tree.end - 1, tree.end - 1, "".join(additions)))
    baseline = json.loads((PACKAGE / "placement-manifest.json").read_text(encoding="utf-8"))
    assert baseline["generated_pcb_sha256"] == BASE
    manifest = copy.deepcopy(baseline)
    component = next(c for c in manifest["components"] if c["reference"] == "C6")
    old_component = copy.deepcopy(component)
    component["y_mm"] += .4
    component["native_origin_common_xy_mm"][1] += .4
    moves = [{"reference": "C6", "delta_mm": [0, .4], "before": old_component,
              "after": copy.deepcopy(component)}]
    if args.clear_c17_courtyard:
        c17 = next(c for c in manifest["components"] if c["reference"] == "C17")
        old_c17 = copy.deepcopy(c17)
        delta = .32 if args.spread_core_column else .11
        c17["y_mm"] += delta
        c17["native_origin_common_xy_mm"][1] += delta
        moves.append({"reference": "C17", "delta_mm": [0, delta], "before": old_c17,
                      "after": copy.deepcopy(c17)})
    if args.spread_core_column:
        for ref, delta in (("C8", .23), ("C13", .14)):
            other = next(c for c in manifest["components"] if c["reference"] == ref)
            old = copy.deepcopy(other)
            other["y_mm"] += delta
            other["native_origin_common_xy_mm"][1] += delta
            moves.append({"reference": ref, "delta_mm": [0, delta], "before": old,
                          "after": copy.deepcopy(other)})
    errors = []
    screen = check.placement_proxy_screen(check.generator(), {m["reference"] for m in moves}, errors,
                                         baseline=baseline, manifest=manifest, resized=set())
    if errors:
        raise ValueError("Placement repair required: " + json.dumps({"errors": errors, "screen": screen}))
    shutil.copytree(PACKAGE, output, ignore=shutil.ignore_patterns(
        "reports", "input-checkpoint", "*.kicad_prl", "*.lck", "*-backups"))
    (output / "handbell.kicad_pcb").write_bytes(apply_edits(text, edits).encode("utf-8"))
    manifest.update(generated_pcb_sha256=sha(output / "handbell.kicad_pcb"),
                    current_stage_report="reports/core-c6.json", mechanical_rebind_required=True)
    (output / "placement-manifest.json").write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    (output / "reports").mkdir()
    shutil.copyfile(PACKAGE / "reports" / "front-ground-plan.json", output / "reports" / "front-ground-plan.json")
    report = {"status": "STAGED_NOT_ACCEPTED", "input_commit": "fe3d2a7",
              "input_pcb_sha256": BASE, "output_pcb_sha256": sha(output / "handbell.kicad_pcb"),
              "schematic_sha256": sha(output / "handbell.kicad_sch"), "generator_sha256": sha(Path(__file__)),
              "component_moves": moves,
              "screen": screen, "added_tracks": records, "changed_tracks": changes + core_changes,
              "removed_tracks": deleted, "new_vias": [], "ground_fill_invalidated": True,
              "required_connections": [["IC1.50", "C6.2"], ["IC1.51", "U1.7"]],
              "remaining": "Native DRC, refill and preserved groups/private returns required. C8/core output and VCORE distribution remain incomplete."}
    (output / "reports" / "core-c6.json").write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"status": report["status"], "screen_errors": errors}))


if __name__ == "__main__":
    main()
