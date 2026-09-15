# SPDX-License-Identifier: MIT
"""UNACCEPTED C8 experiment: the inner bridge shorts VHI. Never promote as-is."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kicad_sexpr import apply_edits, load
from route_clock_local import PACKAGE, sha

BASE = "f2c1fa15129ce8d2042492ff73c8d945222f3fe638e59096a4411ef2e13767f0"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    output = parser.parse_args().output.resolve()
    if output.exists() or sha(PACKAGE / "handbell.kicad_pcb") != BASE:
        raise ValueError("Require the pinned C6 checkpoint and a new staging directory")
    text, tree = load(PACKAGE / "handbell.kicad_pcb")
    removed = {"dfa8490e-8000-5249-b0a8-1cf320355dc8", "5f6e624a-350b-5d4e-b7a6-cd0d9d14c783",
               "8571d067-fffb-5cbc-924f-b908f7a41fc9", "1c0a79bc-d976-5533-bc9b-b86583e647aa",
               "f6b1afb9-58ce-5e2d-af3e-cdc94c95662b", "ace8c05b-519e-5823-aef0-da67149a6b3e"}
    endpoints = {"1e8b18db-09da-595b-adc8-261f93ec17ea": ("start", [104.35, 102.4]),
                 "cb55f8f2-ef3e-5359-9c5d-d3510b66e7b6": ("end", [103.9, 102.2])}
    edits, changes, deleted = [], [], []
    for segment in tree.children("segment"):
        uid = segment.value("uuid")
        if uid not in removed | endpoints.keys():
            continue
        assert segment.value("net") == "+3V3"
        old = {k: list(map(float, segment.child(k).atoms()[1:])) for k in ("start", "end")}
        width = float(segment.value("width"))
        if uid in removed:
            edits.append((segment.start, segment.end, ""))
            deleted.append({"uuid": uid, "old": old, "net": "+3V3", "width_mm": width})
        else:
            key, point = endpoints[uid]
            node = segment.child(key)
            edits.append((node.start, node.end, f"({key} {point[0]} {point[1]})"))
            changes.append({"uuid": uid, "old": old, "new": {**old, key: point},
                            "net": "+3V3", "width_mm_unchanged": width})
    assert len(changes) == 2 and len(deleted) == 6
    routes = [
        ("+3V3", .2, [(103.45, 100.2), (102.65, 100.2)]),
        ("+3V3", .25, [(102.65, 100.2), (102.65, 102.2)]),
        ("+3V3", .2, [(102.65, 102.2), (103.45, 102.2)]),
        ("+3V3", .2, [(103.9, 102.2), (104.1, 102.4), (104.35, 102.4)]),
        ("VCORE", .2, [(103.45, 101.8), (104.1, 101.8), (104.2, 101.9), (104.9931, 101.9)]),
    ]
    additions, records = [], []
    for group, (net, width, points) in enumerate(routes):
        for index, (a, b) in enumerate(zip(points, points[1:])):
            uid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"digital-handbell/core-c8/{group}/{index}"))
            additions.append(f'\n(segment (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) '
                             f'(width {width}) (layer "F.Cu") (net "{net}") (uuid "{uid}"))')
            records.append({"uuid": uid, "start_mm": a, "end_mm": b,
                            "width_mm": width, "layer": "F.Cu", "net": net})
    for zone in tree.children("zone"):
        edits.extend((p.start, p.end, "") for p in zone.children("filled_polygon"))
    edits.append((tree.end - 1, tree.end - 1, "".join(additions)))
    shutil.copytree(PACKAGE, output, ignore=shutil.ignore_patterns(
        "reports", "input-checkpoint", "*.kicad_prl", "*.lck", "*-backups"))
    (output / "handbell.kicad_pcb").write_bytes(apply_edits(text, edits).encode("utf-8"))
    manifest = json.loads((PACKAGE / "placement-manifest.json").read_text(encoding="utf-8"))
    assert manifest["generated_pcb_sha256"] == BASE
    manifest.update(generated_pcb_sha256=sha(output / "handbell.kicad_pcb"),
                    current_stage_report="reports/core-c8.json")
    (output / "placement-manifest.json").write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    (output / "reports").mkdir()
    shutil.copyfile(PACKAGE / "reports" / "front-ground-plan.json", output / "reports" / "front-ground-plan.json")
    report = {"status": "STAGED_NOT_ACCEPTED", "input_commit": "58a8990",
              "input_pcb_sha256": BASE, "output_pcb_sha256": sha(output / "handbell.kicad_pcb"),
              "schematic_sha256": sha(output / "handbell.kicad_sch"), "generator_sha256": sha(Path(__file__)),
              "component_moves": [], "added_tracks": records, "changed_tracks": changes,
              "removed_tracks": deleted, "new_vias": [], "ground_fill_invalidated": True,
              "required_connections": [["IC1.45", "C8.1"], ["IC1.49", "IC1.44"]],
              "remaining": "Native DRC, refill and preserved groups/private returns required. Remaining VCORE distribution and other routing are incomplete."}
    (output / "reports" / "core-c8.json").write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"status": report["status"], "new_tracks": len(records)}))


if __name__ == "__main__":
    main()
