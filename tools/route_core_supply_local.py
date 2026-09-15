# SPDX-License-Identifier: MIT
"""Stage the left RP2040 core-decoupling link and its local 3V3 bend correction."""
import argparse
import json
from pathlib import Path
import shutil
import uuid

from kicad_sexpr import apply_edits, load
from route_clock_local import PACKAGE, sha

BASE = "7be92d3e7b42049e6dcc60d6e58bfb3a1bf7f141f5e11592e9cfad6f8cbf680c"
POINTS = [(96.55, 100.6), (95.9, 100.6), (95.496551, 101.003449), (95.31164, 101.003449)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    output = parser.parse_args().output.resolve()
    if output.exists() or sha(PACKAGE / "handbell.kicad_pcb") != BASE:
        raise ValueError("Require the pinned land-closure board and a new staging directory")
    text, tree = load(PACKAGE / "handbell.kicad_pcb")
    edits, changes = [], []
    corrected = {"9784174c-99b0-5da3-9eb8-64c3cbabd240": "start",
                 "da55c48b-836c-5961-a238-29783736cd88": "end"}
    for segment in tree.children("segment"):
        uid = segment.value("uuid")
        if uid in corrected:
            node = segment.child(corrected[uid])
            assert node.atoms()[1:] == ["95.800000", "100.350000"]
            assert segment.value("net") == "+3V3" and float(segment.value("width")) == .1778
            edits.append((node.start, node.end, f"({corrected[uid]} 95.8 100.2)"))
            changes.append({"uuid": uid, "endpoint": corrected[uid],
                            "old_mm": [95.8, 100.35], "new_mm": [95.8, 100.2],
                            "net": "+3V3", "width_mm_unchanged": .1778})
    assert len(changes) == 2
    additions, records = [], []
    for index, (a, b) in enumerate(zip(POINTS, POINTS[1:])):
        uid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"digital-handbell/core-supply-left/{index}"))
        additions.append(f'\n(segment (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) '
                         f'(width 0.2) (layer "F.Cu") (net "VCORE") (uuid "{uid}"))')
        records.append({"uuid": uid, "start_mm": a, "end_mm": b,
                        "width_mm": .2, "layer": "F.Cu", "net": "VCORE"})
    for zone in tree.children("zone"):
        edits.extend((p.start, p.end, "") for p in zone.children("filled_polygon"))
    edits.append((tree.end - 1, tree.end - 1, "".join(additions)))
    shutil.copytree(PACKAGE, output, ignore=shutil.ignore_patterns(
        "reports", "input-checkpoint", "*.kicad_prl", "*.lck", "*-backups"))
    (output / "handbell.kicad_pcb").write_bytes(apply_edits(text, edits).encode("utf-8"))
    manifest = json.loads((PACKAGE / "placement-manifest.json").read_text(encoding="utf-8"))
    assert manifest["generated_pcb_sha256"] == BASE
    manifest.update(generated_pcb_sha256=sha(output / "handbell.kicad_pcb"),
                    current_stage_report="reports/core-supply-local.json")
    (output / "placement-manifest.json").write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    (output / "reports").mkdir()
    shutil.copyfile(PACKAGE / "reports" / "front-ground-plan.json", output / "reports" / "front-ground-plan.json")
    report = {"status": "STAGED_NOT_ACCEPTED", "input_commit": "1452462",
              "input_pcb_sha256": BASE, "output_pcb_sha256": sha(output / "handbell.kicad_pcb"),
              "schematic_sha256": sha(output / "handbell.kicad_sch"),
              "generator_sha256": sha(Path(__file__)), "added_tracks": records,
              "changed_tracks": changes, "component_moves": [], "new_vias": [],
              "target_connection": ["IC1.23", "C18.2"], "ground_fill_invalidated": True,
              "remaining": "Refill, native DRC and preserved groups/private returns plus the named connection must pass. Right-side VCORE approaches remain blocked by existing QSPI/3V3 routing; do not rerun an autorouter."}
    (output / "reports" / "core-supply-local.json").write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"status": report["status"], "new_tracks": len(records), "changed_tracks": len(changes)}))


if __name__ == "__main__":
    main()
