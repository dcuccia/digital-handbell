# SPDX-License-Identifier: MIT
"""Qualify all-layer graphs with saved fixtures extracted from a known-good PCB."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "hardware/handbell/iterations/printed-bell-four-layer/handbell.kicad_pcb"
MANIFEST = ROOT / "hardware/handbell/iterations/printed-bell-four-layer/placement-manifest.json"
REPORT = ROOT / "hardware/handbell/iterations/printed-bell-four-layer/reports/four-layer-graph-saved-native-control.json"
WORK = None
CLI = Path(os.environ["LOCALAPPDATA"]) / "Programs/KiCad/10.0/bin/kicad-cli.exe"
EXPECTED_PCB = "d91837ed9f5cff10d709521e448f6deae3aac3a52abed88c34271ee809e25418"
EXPECTED_MANIFEST = "ed64e9c92bd2cc7dc90a00cd98689f511517151c909052e7b23b3840d101f381"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise AssertionError(message)


def uid(name):
    return str(uuid.uuid5(uuid.UUID("9ba12632-f038-4df5-9ac7-a8c2bdbabddd"), name))


def segment(a, b, layer, net, name):
    return (f'(segment (start {a[0]:.6f} {a[1]:.6f}) (end {b[0]:.6f} {b[1]:.6f}) '
            f'(width 0.2) (layer "{layer}") (net "{net}") (uuid "{uid(name)}"))')


def via(at, net, name):
    return (f'(via (at {at[0]:.6f} {at[1]:.6f}) (size 0.6) (drill 0.3) '
            f'(layers "F.Cu" "B.Cu") (net "{net}") (uuid "{uid(name)}"))')


def build_fixtures():
    sys.path.insert(0, str(ROOT / "tools"))
    from kicad_sexpr import load, apply_edits
    text, board = load(SOURCE)
    header = [board.child(name) for name in
              ("version", "generator", "generator_version", "general", "paper",
               "title_block", "layers", "setup")]
    footprints = [fp for fp in board.children("footprint")
                  if fp.properties().get("Reference") in {"C23", "C24"}]
    edges = [node for head in ("gr_line", "gr_arc")
             for node in board.children(head) if node.value("layer") == "Edge.Cuts"]
    require(len(footprints) == 2 and edges, "Known-good source extraction failed")
    base_nodes = header + footprints + edges
    render = lambda nodes: "(kicad_pcb\n" + "\n".join(text[n.start:n.end] for n in nodes) + "\n)\n"

    short_extra = [
        segment((89.810835, 91.491614), (90.5, 91.491614), "F.Cu", "GND", "short-gnd-f"),
        via((90.5, 91.491614), "GND", "short-gnd-via"),
        segment((90.5, 91.491614), (94, 91.491614), "In1.Cu", "GND", "short-gnd-in1"),
        segment((88.794835, 91.491614), (92, 89.5), "F.Cu", "+3V3", "short-3v3-f"),
        via((92, 89.5), "+3V3", "short-3v3-via"),
        segment((92, 89.5), (92, 93), "In1.Cu", "+3V3", "short-3v3-in1"),
        segment((95, 96), (97, 96), "F.Cu", "GND", "short-isolation-f"),
        segment((95, 96), (97, 96), "In1.Cu", "GND", "short-isolation-in1"),
    ]
    short_text = render(base_nodes)[:-2] + "\n" + "\n".join(short_extra) + "\n)\n"

    zone = next(z for z in board.children("zone") if z.value("name") == "quote-native-F-GND-v1")
    edits = []
    layer = zone.child("layer")
    edits.append((layer.start, layer.end, '(layer "In1.Cu")'))
    edits.extend((child.start, child.end, "") for child in zone.children("filled_polygon"))
    zone_text = apply_edits(text[zone.start:zone.end],
                            [(a-zone.start, b-zone.start, value) for a, b, value in edits])
    plane_extra = [
        segment((89.810835, 91.491614), (90.5, 91.491614), "F.Cu", "GND", "plane-c23-f"),
        via((90.5, 91.491614), "GND", "plane-c23-via"),
        segment((92.004083, 93.491669), (94, 93.491669), "F.Cu", "GND", "plane-c24-f"),
        via((94, 93.491669), "GND", "plane-c24-via"),
        segment((91, 95), (93, 95), "In2.Cu", "GND", "plane-in2-control"),
    ]
    plane_text = render(base_nodes)[:-2] + "\n" + zone_text + "\n" + "\n".join(plane_extra) + "\n)\n"
    WORK.mkdir(parents=True, exist_ok=False)
    (WORK / "short.kicad_pcb").write_bytes(short_text.encode("utf-8"))
    (WORK / "plane-unfilled.kicad_pcb").write_bytes(plane_text.encode("utf-8"))
    return {"short": sha(WORK / "short.kicad_pcb"),
            "plane_unfilled": sha(WORK / "plane-unfilled.kicad_pcb")}


def native_worker(mode, board_path, output):
    native = CLI.parent
    dll_handle = os.add_dll_directory(str(native))
    sys.path.insert(0, str(native / "Lib/site-packages"))
    sys.path.insert(0, str(ROOT / "tools"))
    import pcbnew as pcb
    from check_printed_bell_power_rework import CopperGraph
    from zone_graph import CopperGraph as FilledGraph
    require(pcb.GetBuildVersion() == "10.0.6", "KiCad 10.0.6 required")
    graph = (FilledGraph if mode == "plane-filled" else CopperGraph)(pcb, board_path)
    def exact_vertex(uid_value, net, layers):
        require(uid_value in graph.items, "Missing witness UUID: " + uid_value)
        require(graph.items[uid_value].GetNetname() == net, "Witness net changed: " + uid_value)
        actual = {graph.layer_name(vertex[1]) for vertex in graph.by_uuid[uid_value]}
        require(actual == set(layers), f"Witness layers changed: {uid_value}: {actual}")
    if mode == "short":
        c23g, c23p = graph.pad_uuid("C23", "2"), graph.pad_uuid("C23", "1")
        iso_f, iso_i = uid("short-isolation-f"), uid("short-isolation-in1")
        exact_vertex(iso_f, "GND", {"F.Cu"})
        exact_vertex(iso_i, "GND", {"In1.Cu"})
        require(not graph.connected(iso_f, iso_i), "Same-XY F/In1 GND witnesses joined")
        require(not graph.connected(c23g, c23p), "Anchored GND/+3V3 groups falsely joined")
        expected = {uid("short-gnd-in1"), uid("short-3v3-in1")}
        require(any(set(row["nets"]) == {"GND", "+3V3"} and row["layer"] == "In1.Cu"
                    and {row["a_uuid"], row["b_uuid"]} == expected
                    for row in graph.shorts), "Graph omitted deliberate In1 GND/+3V3 short")
        result = {"connected_anchored_groups": False, "shorts": graph.shorts,
                  "path_anchored_groups": graph.path(c23g, c23p),
                  "same_xy_gnd_witnesses_disconnected": True}
    elif mode == "plane-before":
        a, b = graph.pad_uuid("C23", "2"), graph.pad_uuid("C24", "2")
        control = uid("plane-in2-control")
        exact_vertex(control, "GND", {"In2.Cu"})
        for via_uid in (uid("plane-c23-via"), uid("plane-c24-via")):
            require({"F.Cu", "In1.Cu"} <=
                    {graph.layer_name(vertex[1]) for vertex in graph.by_uuid[via_uid]},
                    "Plane via lacks F/In1 vertices: " + via_uid)
        require(not graph.connected(a, b), "GND groups connected before fill")
        require(not graph.connected(a, control) and not graph.connected(b, control),
                "In2 same-net control connected before fill")
        result = {"c23_c24_connected": False, "in2_control_connected": False}
    else:
        primitive = CopperGraph(pcb, board_path)
        a, b = graph.pad_uuid("C23", "2"), graph.pad_uuid("C24", "2")
        control = uid("plane-in2-control")
        exact_vertex(control, "GND", {"In2.Cu"})
        for via_uid in (uid("plane-c23-via"), uid("plane-c24-via")):
            require({"F.Cu", "In1.Cu"} <=
                    {graph.layer_name(vertex[1]) for vertex in graph.by_uuid[via_uid]},
                    "Plane via lacks F/In1 vertices: " + via_uid)
        require(not primitive.connected(primitive.pad_uuid("C23", "2"),
                                        primitive.pad_uuid("C24", "2")),
                "CLI refill created a primitive-only C23/C24 path")
        require(graph.connected(a, b), "In1 fill did not connect GND groups")
        require(not graph.connected(a, control) and not graph.connected(b, control),
                "In1 fill falsely joined same-net In2-only copper")
        path = graph.path(a, b)
        require(any(step.get("filled_island_index") is not None and step["layer"] == "In1.Cu"
                    for step in path), "Filled path lacks an In1 native-island witness")
        result = {"c23_c24_connected": True, "primitive_c23_c24_connected": False,
                  "in2_control_connected": False, "zone_islands": graph.zone_islands,
                  "path": path}
    board = graph.board
    nets = sorted({item.GetNetname() for item in graph.items.values() if item.GetNetname()})
    result.update(native_version=pcb.GetBuildVersion(), current_net_names=nets)
    Path(output).write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))


def append_stage(record):
    path = WORK / "stages.json"
    stages = json.loads(path.read_text()) if path.exists() else []
    stages.append(record)
    path.write_bytes((json.dumps(stages, indent=2) + "\n").encode("utf-8"))


def run_stage(name, command, timeout):
    append_stage({"name": name, "status": "starting", "command": command,
                  "timeout_seconds": timeout, "started_unix": time.time()})
    stdout, stderr = WORK / f"{name}.stdout.txt", WORK / f"{name}.stderr.txt"
    started = time.monotonic()
    with stdout.open("w") as out, stderr.open("w") as err:
        try:
            result = subprocess.run(command, stdout=out, stderr=err, timeout=timeout)
            code, status = result.returncode, "completed"
        except subprocess.TimeoutExpired:
            code, status = None, "timeout"
    append_stage({"name": name, "status": status, "exit_code": code,
                  "seconds": time.monotonic()-started, "stdout": str(stdout), "stderr": str(stderr)})
    require(status == "completed" and code == 0, f"{name} failed: {status}/{code}")


def sanitize_stages(stages):
    cleaned = []
    for stage in stages:
        row = dict(stage)
        if "command" in row:
            values = []
            for value in row["command"]:
                value = str(value).replace(str(CLI), "<kicad-cli>")
                value = value.replace(sys.executable, "<python>")
                value = value.replace(str(ROOT), "<repo>")
                value = value.replace(str(WORK), "<work>")
                values.append(value)
            row["command"] = values
        for key in ("stdout", "stderr"):
            if key in row:
                row[key] = Path(row[key]).name
        cleaned.append(row)
    return cleaned


def controller(work_dir):
    global WORK
    WORK = Path(work_dir).resolve()
    require(not WORK.exists(), "Controller --work-dir must not already exist")
    require(sha(SOURCE) == EXPECTED_PCB and sha(MANIFEST) == EXPECTED_MANIFEST,
            "Production source guard changed")
    short, plane = WORK / "short.kicad_pcb", WORK / "plane-unfilled.kicad_pcb"
    filled = WORK / "plane-filled.kicad_pcb"
    fixture_hashes = build_fixtures()
    if REPORT.exists():
        (WORK / "previous-public-report.json").write_bytes(REPORT.read_bytes())
    py = sys.executable
    run_stage("short-drc", [str(CLI), "pcb", "drc", "--format", "json", "--severity-all",
              "--output", str(WORK / "short-drc.json"), str(short)], 60)
    run_stage("short-graph", [py, __file__, "worker", "short", str(short),
              str(WORK / "short-graph.json")], 60)
    run_stage("plane-before", [py, __file__, "worker", "plane-before", str(plane),
              str(WORK / "plane-before.json")], 60)
    filled.write_bytes(plane.read_bytes())
    run_stage("plane-refill-drc", [str(CLI), "pcb", "drc", "--format", "json", "--severity-all",
              "--refill-zones", "--save-board", "--output", str(WORK / "plane-drc.json"),
              str(filled)], 60)
    run_stage("plane-filled", [py, __file__, "worker", "plane-filled", str(filled),
              str(WORK / "plane-filled.json")], 60)
    required = ("short-drc.json", "short-graph.json", "plane-before.json", "plane-drc.json",
                "plane-filled.json", "stages.json")
    require(all((WORK / name).exists() for name in required), "Incomplete persisted stage evidence")
    fixture_hashes = {"short": sha(short), "plane_unfilled": sha(plane)}
    before_fill_hash, after_fill_hash = sha(plane), sha(filled)
    require(after_fill_hash != before_fill_hash, "CLI refill/save did not change the board")
    short_drc = json.loads((WORK / "short-drc.json").read_text())
    short_graph = json.loads((WORK / "short-graph.json").read_text())
    plane_before = json.loads((WORK / "plane-before.json").read_text())
    plane_after = json.loads((WORK / "plane-filled.json").read_text())
    short_specific = [row for row in short_drc["violations"]
                      if row["type"] == "tracks_crossing"
                      and {item["uuid"] for item in row["items"]}
                      == {uid("short-gnd-in1"), uid("short-3v3-in1")}
                      and {net for item in row["items"]
                           for net in ("GND", "+3V3") if f"[{net}]" in item["description"]}
                      == {"GND", "+3V3"}]
    require(short_specific, "CLI DRC omitted the deliberate GND/+3V3 short identity")
    report = {
        "status": "SAVED_NATIVE_ALL_LAYER_GRAPH_CONTROL_PASSED",
        "source_pcb_sha256": sha(SOURCE), "manifest_sha256": sha(MANIFEST),
        "fixture_hashes": {**fixture_hashes, "plane_filled": after_fill_hash},
        "short": {"specific_cli_findings": short_specific, "graph": short_graph,
                  "drc_unconnected": len(short_drc["unconnected_items"])},
        "plane": {"before": plane_before, "after": plane_after,
                  "unfilled_sha256": before_fill_hash, "filled_sha256": after_fill_hash},
        "stages": sanitize_stages(json.loads((WORK / "stages.json").read_text())),
        "private_evidence_workspace": WORK.name,
        "tool_hashes": {
            "tools/check_four_layer_graph.py": sha(__file__),
            "tools/check_printed_bell_power_rework.py": sha(ROOT / "tools/check_printed_bell_power_rework.py"),
            "tools/zone_graph.py": sha(ROOT / "tools/zone_graph.py"),
        },
        "provenance": "Fixtures extract native KiCad syntax, C23/C24, Edge.Cuts, setup, and the GND zone from the CC BY-SA package; no fixture is promoted as production.",
        "remaining_unqualified": ["routing masks/search", "production plane topology/exclusions",
                                  "contacts and private sense/current paths"]
    }
    REPORT.write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        native_worker(sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4]))
    else:
        require(len(sys.argv) == 3 and sys.argv[1] == "--work-dir",
                "Usage: check_four_layer_graph.py --work-dir NEW_DIRECTORY")
        controller(sys.argv[2])
