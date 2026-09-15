# SPDX-License-Identifier: MIT
"""Stage C8 closure with VHI in the central B corridor and nine retained ground vias."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from check_front_ground import bounds_polygon
from kicad_sexpr import apply_edits, load
from route_clock_local import PACKAGE, ROOT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    output = parser.parse_args().output.resolve()
    experiment = ROOT / "tools" / "experiments" / "route_core_c8.py"
    subprocess.run([sys.executable, str(experiment), str(output)], check=True, timeout=60)
    report = json.loads((output / "reports" / "core-c8.json").read_text(encoding="utf-8"))
    text, tree = load(output / "handbell.kicad_pcb")
    edits = []
    extra_removed = {"d4c4be10-c85c-53ad-9480-b98a602ff455", "2af66fa2-da42-56a5-b76a-3da8c97042ed"}
    vhi_paths = {
        "f3cf6086-b923-5ac5-b36a-96f7bc7a9364": ([100, 97.7], [100.8, 98.5]),
        "f65734e6-a23d-5b8f-9f86-b9c463595aa2": ([100.8, 98.5], [100.8, 101.5]),
        "44c981e1-c131-5c74-89b2-361ded83799d": ([100.8, 101.5], [100, 102.3]),
    }
    left = [(99.15, 98.76 + .62*i) for i in range(5)]
    right = [(99.8, 99.07 + .62*i) for i in range(4)]
    points = [[round(x, 6), round(y, 6)] for x, y in left + right]
    grid_vias = [n for n in tree.children("via") if n.value("net") == "GND"
                 and all(98.5 < float(v) < 101.5 for v in n.child("at").atoms()[1:])]
    grid_vias.sort(key=lambda n: tuple(map(float, n.child("at").atoms()[1:])))
    assert len(grid_vias) == 9
    via_moves = []
    for via, point in zip(grid_vias, points, strict=True):
        assert float(via.value("size")) == .604 and float(via.value("drill")) == .35
        at = via.child("at")
        via_moves.append({"uuid": via.value("uuid"), "old_mm": list(map(float, at.atoms()[1:])),
                          "new_mm": point, "net": "GND", "diameter_mm": .604, "drill_mm": .35})
        edits.append((at.start, at.end, f"(at {point[0]} {point[1]})"))
    grid_tracks = [n for n in tree.children("segment")
                   if n.value("net") == "GND" and n.value("layer") == "B.Cu"
                   and all(98.5 < float(v) < 101.5 for k in ("start", "end")
                           for v in n.child(k).atoms()[1:])]
    grid_tracks.sort(key=lambda n: n.value("uuid"))
    pairs = [(i, i+1) for i in range(4)] + [(i, i+1) for i in range(5, 8)]
    pairs += [(0, 5), (1, 5), (2, 6), (3, 7), (4, 8)]
    assert len(grid_tracks) == len(pairs) == 12
    grid_paths = {n.value("uuid"): (points[a], points[b]) for n, (a, b) in zip(grid_tracks, pairs, strict=True)}
    for segment in tree.children("segment"):
        uid = segment.value("uuid")
        old = {k: list(map(float, segment.child(k).atoms()[1:])) for k in ("start", "end")}
        if uid in extra_removed:
            assert segment.value("net") == "+3V3"
            edits.append((segment.start, segment.end, ""))
            report["removed_tracks"].append({"uuid": uid, "old": old, "net": "+3V3",
                                             "width_mm": float(segment.value("width"))})
        elif uid in vhi_paths or uid in grid_paths:
            a, b = (vhi_paths if uid in vhi_paths else grid_paths)[uid]
            expected_net, expected_width = ("VHI", .8) if uid in vhi_paths else ("GND", .6)
            assert segment.value("net") == expected_net and float(segment.value("width")) == expected_width
            for key, point in (("start", a), ("end", b)):
                node = segment.child(key)
                edits.append((node.start, node.end, f"({key} {point[0]} {point[1]})"))
            old_layer = segment.value("layer")
            if old_layer != "B.Cu":
                layer = segment.child("layer")
                edits.append((layer.start, layer.end, '(layer "B.Cu")'))
            report["changed_tracks"].append({"uuid": uid, "old": old, "new": {"start": a, "end": b},
                                             "net": expected_net, "width_mm_unchanged": expected_width,
                                             "old_layer": old_layer, "new_layer": "B.Cu"})
    assert len(report["removed_tracks"]) == 8 and len(report["changed_tracks"]) == 17
    (output / "handbell.kicad_pcb").write_bytes(apply_edits(text, edits).encode("utf-8"))
    manifest = json.loads((output / "placement-manifest.json").read_text(encoding="utf-8"))
    manifest.update(generated_pcb_sha256=sha(output / "handbell.kicad_pcb"),
                    current_stage_report="reports/core-power-corridor.json")
    (output / "placement-manifest.json").write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))

    native = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin"
    dll_handle = os.add_dll_directory(str(native))
    sys.path.insert(0, str(native / "Lib" / "site-packages"))
    import pcbnew as pcb
    board = pcb.LoadBoard(str(output / "handbell.kicad_pcb"))
    items = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    # A central rectangle wholly inside the original rounded exposed pad bounds.
    for move in via_moves:
        x, y = move["new_mm"]
        assert 98.56 <= x-.302 and x+.302 <= 101.44
        assert 98.4 <= y-.302 and y+.302 <= 101.6
    contact_path = PACKAGE / "battery-contact-interface.json"
    contact = json.loads(contact_path.read_text(encoding="utf-8"))
    primitives = contact["right_contact_original_primitives"]
    metal = []
    for sign in (1, -1):
        for primitive in [*primitives["base_tabs"], primitives["under_cell_base"]]:
            xs = sorted([100+sign*primitive[k] for k in ("x_min", "x_max")])
            bounds = [xs[0], 100-primitive["y_width"]/2, xs[1], 100+primitive["y_width"]/2]
            metal.append(bounds_polygon(pcb, {"bounds_absolute_iu": [pcb.FromMM(v) for v in bounds]}))
    checked = set(grid_paths) | set(vhi_paths) | {m["uuid"] for m in via_moves}
    for uid in checked:
        shape = items[uid].GetEffectiveShape(pcb.B_Cu)
        assert all(not region.Collide(shape, pcb.FromMM(.2)-1) for region in metal), uid
    assert sha(PACKAGE / "handbell.kicad_pcb") == report["input_pcb_sha256"]
    report.update(
        status="STAGED_NOT_ACCEPTED", input_commit="70bfab3",
        c8_experiment_generator_sha256=report["generator_sha256"],
        generator_sha256=sha(Path(__file__)), output_pcb_sha256=sha(output / "handbell.kicad_pcb"),
        changed_vias=via_moves, contact_interface_sha256=sha(contact_path),
        new_B_geometry_checked_against_retained_base_metal=True,
        contact_metal_clearance_floor_mm=.2,
        thermal_vias_retained={"count": 9, "diameter_mm": .604, "drill_mm": .35,
                               "all_annuli_inside_original_exposed_pad": True},
        thermal_limit="Array and B spreading changed; retained count/widths are not measured thermal equivalence. Existing exposed-pad mask and four paste shapes unchanged; assembler via/stencil review remains required.",
        remaining="Native DRC, filled continuity, required connections and power topology must pass before promotion.",
    )
    (output / "reports" / "core-power-corridor.json").write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"status": report["status"], "retained_ground_vias": 9, "B_metal_screen": "passed"}))


if __name__ == "__main__":
    main()
