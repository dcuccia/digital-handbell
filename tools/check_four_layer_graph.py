# SPDX-License-Identifier: MIT
"""Preserved, unqualified saved-fixture experiment; automatic reruns are disabled."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
NATIVE = Path(os.environ["LOCALAPPDATA"]) / "Programs/KiCad/10.0/bin"
CLI = NATIVE / "kicad-cli.exe"
REPORT = ROOT / "hardware/handbell/iterations/printed-bell-four-layer/reports/four-layer-graph-file-control.json"
EXPECTED = {
    "source": ("hardware/handbell/iterations/printed-bell-clock-draft/handbell.kicad_pcb",
               "a83cc417c96b05dd15c187e648b9fd2a35ba857c3a66f7d13aaaa42ae3bd9fff"),
    "baseline": ("hardware/handbell/iterations/printed-bell-four-layer/handbell.kicad_pcb",
                 "d91837ed9f5cff10d709521e448f6deae3aac3a52abed88c34271ee809e25418"),
    "manifest": ("hardware/handbell/iterations/printed-bell-four-layer/placement-manifest.json",
                 "ed64e9c92bd2cc7dc90a00cd98689f511517151c909052e7b23b3840d101f381"),
    "primitive_graph": ("tools/check_printed_bell_power_rework.py",
                        "f9f0ccb985c43a655b07d3a21a55cbbd8cb79cc459dc7b72888ac9630ccbffd3"),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise AssertionError(message)


def native():
    handle = os.add_dll_directory(str(NATIVE))
    sys.path.insert(0, str(NATIVE / "Lib/site-packages"))
    import pcbnew
    require(pcbnew.GetBuildVersion() == "10.0.6", "KiCad 10.0.6 required")
    return pcbnew, handle


def configure(pcb, board):
    board.SetCopperLayerCount(4)
    settings = board.GetDesignSettings()
    settings.m_MinClearance = pcb.FromMM(.2)
    settings.m_CopperEdgeClearance = pcb.FromMM(.25)
    settings.m_HoleClearance = pcb.FromMM(.25)
    settings.m_HoleToHoleMin = pcb.FromMM(.25)
    settings.m_MaxError = pcb.FromMM(.001)
    for a, b in (((0, 0), (24, 0)), ((24, 0), (24, 16)),
                 ((24, 16), (0, 16)), ((0, 16), (0, 0))):
        edge = pcb.PCB_SHAPE(board)
        edge.SetShape(pcb.SHAPE_T_SEGMENT)
        edge.SetStart(pcb.VECTOR2I(pcb.FromMM(a[0]), pcb.FromMM(a[1])))
        edge.SetEnd(pcb.VECTOR2I(pcb.FromMM(b[0]), pcb.FromMM(b[1])))
        edge.SetWidth(pcb.FromMM(.05))
        edge.SetLayer(pcb.Edge_Cuts)
        board.Add(edge)


def add_net(pcb, board, name):
    item = pcb.NETINFO_ITEM(board, name)
    board.Add(item)
    return item


def add_pad(pcb, board, ref, number, net, layer, xy):
    fp = pcb.FOOTPRINT(board)
    fp.SetReference(ref)
    fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(xy[0]), pcb.FromMM(xy[1])))
    board.Add(fp)
    pad = pcb.PAD(fp)
    pad.SetNumber(number)
    pad.SetAttribute(pcb.PAD_ATTRIB_SMD)
    pad.SetShape(pcb.PAD_SHAPE_RECT)
    pad.SetSize(pcb.VECTOR2I(pcb.FromMM(1), pcb.FromMM(1)))
    pad.SetPosition(pcb.VECTOR2I(pcb.FromMM(xy[0]), pcb.FromMM(xy[1])))
    layers = pcb.LSET()
    layers.AddLayer(layer)
    pad.SetLayerSet(layers)
    pad.SetNetCode(net.GetNetCode())
    fp.Add(pad)
    return pad


def add_pth(pcb, board, ref, number, net, xy):
    fp = pcb.FOOTPRINT(board)
    fp.SetReference(ref)
    fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(xy[0]), pcb.FromMM(xy[1])))
    board.Add(fp)
    pad = pcb.PAD(fp)
    pad.SetNumber(number)
    pad.SetAttribute(pcb.PAD_ATTRIB_PTH)
    pad.SetShape(pcb.PAD_SHAPE_CIRCLE)
    pad.SetSize(pcb.VECTOR2I(pcb.FromMM(1.2), pcb.FromMM(1.2)))
    pad.SetDrillSize(pcb.VECTOR2I(pcb.FromMM(.6), pcb.FromMM(.6)))
    pad.SetPosition(pcb.VECTOR2I(pcb.FromMM(xy[0]), pcb.FromMM(xy[1])))
    pad.SetLayerSet(pcb.LSET.AllCuMask())
    pad.SetNetCode(net.GetNetCode())
    fp.Add(pad)
    return pad


def add_track(pcb, board, net, layer, a, b):
    item = pcb.PCB_TRACK(board)
    item.SetStart(pcb.VECTOR2I(pcb.FromMM(a[0]), pcb.FromMM(a[1])))
    item.SetEnd(pcb.VECTOR2I(pcb.FromMM(b[0]), pcb.FromMM(b[1])))
    item.SetWidth(pcb.FromMM(.3))
    item.SetLayer(layer)
    item.SetNetCode(net.GetNetCode())
    board.Add(item)
    return item


def add_via(pcb, board, net, xy):
    item = pcb.PCB_VIA(board)
    item.SetPosition(pcb.VECTOR2I(pcb.FromMM(xy[0]), pcb.FromMM(xy[1])))
    item.SetWidth(pcb.FromMM(.8))
    item.SetDrill(pcb.FromMM(.4))
    item.SetLayerPair(pcb.F_Cu, pcb.B_Cu)
    item.SetNetCode(net.GetNetCode())
    board.Add(item)
    return item


def rectangle(pcb, bounds):
    polygon = pcb.SHAPE_POLY_SET()
    index = polygon.NewOutline()
    xmin, ymin, xmax, ymax = bounds
    for x, y in ((xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)):
        polygon.Append(pcb.FromMM(x), pcb.FromMM(y), index)
    return polygon


def create(kind, output):
    pcb, handle = native()
    board = pcb.BOARD()
    configure(pcb, board)
    witnesses = {}
    if kind == "short":
        sig, other, iso = (add_net(pcb, board, name) for name in ("SIG", "OTHER", "ISO"))
        add_pad(pcb, board, "SIG_F", "1", sig, pcb.F_Cu, (3, 5))
        add_track(pcb, board, sig, pcb.F_Cu, (3, 5), (8, 5))
        add_via(pcb, board, sig, (8, 5))
        add_track(pcb, board, sig, pcb.In1_Cu, (8, 5), (12, 5))
        add_pad(pcb, board, "OTHER_F", "1", other, pcb.F_Cu, (18, 2))
        add_track(pcb, board, other, pcb.F_Cu, (18, 2), (15, 2))
        add_via(pcb, board, other, (15, 2))
        add_track(pcb, board, other, pcb.In1_Cu, (15, 2), (15, 5))
        add_track(pcb, board, other, pcb.In1_Cu, (15, 5), (6, 5))
        add_pad(pcb, board, "ISO_F", "1", iso, pcb.F_Cu, (4, 12))
        witnesses["iso_f"] = add_track(pcb, board, iso, pcb.F_Cu, (4, 12), (7, 12))
        witnesses["iso_i"] = add_track(pcb, board, iso, pcb.In1_Cu, (4, 12), (7, 12))
    else:
        gnd, control = add_net(pcb, board, "GND"), add_net(pcb, board, "CONTROL")
        add_pad(pcb, board, "GND_F", "1", gnd, pcb.F_Cu, (4, 6))
        add_track(pcb, board, gnd, pcb.F_Cu, (4, 6), (7, 6))
        add_via(pcb, board, gnd, (7, 6))
        add_pth(pcb, board, "GND_I", "1", gnd, (16, 6))
        add_track(pcb, board, gnd, pcb.In1_Cu, (14, 6), (16, 6))
        add_pad(pcb, board, "CONTROL_F", "1", control, pcb.F_Cu, (21, 13))
        witnesses["control_i2"] = add_track(pcb, board, control, pcb.In2_Cu, (12, 9), (15, 9))
        zone = pcb.ZONE(board)
        zone.SetLayer(pcb.In1_Cu)
        zone.SetNetCode(gnd.GetNetCode())
        zone.SetOutline(rectangle(pcb, [6, 3, 18, 11]))
        zone.SetMinThickness(pcb.FromMM(.2))
        zone.SetClearance(pcb.FromMM(.2))
        zone.SetPadConnection(pcb.ZONE_CONNECTION_FULL)
        board.Add(zone)
    require(pcb.SaveBoard(str(output), board), "Could not save fixture")
    output.with_suffix(".witnesses.json").write_bytes((json.dumps(
        {name: item.m_Uuid.AsString() for name, item in witnesses.items()}, indent=2) + "\n").encode())
    print(json.dumps({"stage": "created", "kind": kind, "sha256": sha(output)}, indent=2), flush=True)


def item_snapshot(graph, refs):
    result = {}
    for ref in refs:
        uid = graph.pad_uuid(ref, "1")
        item = graph.items[uid]
        result[ref] = {"uuid": uid, "net": item.GetNetname(), "code": item.GetNetCode(),
                       "layers": [graph.layer_name(x[1]) for x in graph.by_uuid[uid]]}
    return result


def check(kind, path, output):
    pcb, handle = native()
    sys.path.insert(0, str(ROOT / "tools"))
    from check_printed_bell_power_rework import CopperGraph
    from zone_graph import CopperGraph as FilledGraph
    graph = CopperGraph(pcb, path)
    witnesses = json.loads(path.with_suffix(".witnesses.json").read_text())
    if kind == "short":
        refs = ("SIG_F", "OTHER_F", "ISO_F")
        pads = item_snapshot(graph, refs)
        require(pads["SIG_F"]["net"] == "SIG", "SIG pad net changed")
        require(pads["OTHER_F"]["net"] == "OTHER", "OTHER pad net changed")
        require(not graph.connected(witnesses["iso_f"], witnesses["iso_i"]),
                "Same-XY F/In1 no-via groups falsely joined")
        require(not graph.connected(graph.pad_uuid("SIG_F", "1"), graph.pad_uuid("OTHER_F", "1")),
                "Distinct anchored SIG/OTHER groups falsely joined")
        require(any(set(row["nets"]) == {"SIG", "OTHER"} for row in graph.shorts),
                "Graph omitted deliberate SIG/OTHER short")
        vias = [item for item in graph.items.values() if isinstance(item, pcb.PCB_VIA)]
        result = {"pads": pads, "via": [{"uuid": v.m_Uuid.AsString(), "net": v.GetNetname(),
                                        "code": v.GetNetCode(),
                                        "layers": [graph.layer_name(x[1]) for x in graph.by_uuid[v.m_Uuid.AsString()]]}
                                       for v in vias],
                  "shorts": graph.shorts,
                  "path_sig_other": graph.path(graph.pad_uuid("SIG_F", "1"),
                                               graph.pad_uuid("OTHER_F", "1"))}
    else:
        primitive = graph
        gnd_f, gnd_i = primitive.pad_uuid("GND_F", "1"), primitive.pad_uuid("GND_I", "1")
        control = witnesses["control_i2"]
        require(not primitive.connected(gnd_f, gnd_i), "Unfilled GND witnesses already connected")
        require(not primitive.connected(gnd_i, control), "Unfilled In1/In2 witnesses joined")
        if kind == "plane-before":
            result = {"before_fill_disconnected": True, "in1_in2_isolated": True,
                      "pads": item_snapshot(primitive, ("GND_F", "GND_I", "CONTROL_F"))}
            Path(output).write_bytes((json.dumps(result, indent=2) + "\n").encode())
            print(json.dumps({"stage": "checked", "kind": kind, "result": result}, indent=2), flush=True)
            return
        filled = FilledGraph(pcb, path)
        require(filled.connected(gnd_f, gnd_i), "Native In1 fill did not join GND witnesses")
        require(not filled.connected(gnd_i, control), "Native In1 fill joined In2 control")
        require(any(row["layer"] == "In1.Cu" for row in filled.zone_islands),
                "No exact native In1 filled island")
        result = {"pads": item_snapshot(filled, ("GND_F", "GND_I", "CONTROL_F")),
                  "before_fill_disconnected": True, "after_fill_ground_connected": True,
                  "in2_control_isolated": True, "zone_islands": filled.zone_islands}
    Path(output).write_bytes((json.dumps(result, indent=2) + "\n").encode())
    print(json.dumps({"stage": "checked", "kind": kind, "result": result}, indent=2), flush=True)


def orchestrate():
    for _, (relative, expected) in EXPECTED.items():
        require(sha(ROOT / relative) == expected, "Source-bound guard changed: " + relative)
    with tempfile.TemporaryDirectory(prefix="four-layer-graph-") as directory:
        work = Path(directory)
        short, plane = work / "short.kicad_pcb", work / "plane.kicad_pcb"
        stage = []
        def run(args, timeout):
            started = time.monotonic()
            completed = subprocess.run(args, check=True, timeout=timeout, capture_output=True, text=True)
            stage.append({"command": [Path(args[0]).name, *args[1:]], "seconds": time.monotonic()-started,
                          "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()})
        run([sys.executable, __file__, "create", "short", str(short)], 45)
        run([str(CLI), "pcb", "drc", "--format", "json", "--severity-all",
             "--output", str(work / "short-drc.json"), str(short)], 60)
        run([sys.executable, __file__, "check", "short", str(short), str(work / "short-check.json")], 45)
        run([sys.executable, __file__, "create", "plane", str(plane)], 45)
        run([sys.executable, __file__, "check", "plane-before", str(plane),
             str(work / "plane-before.json")], 45)
        run([str(CLI), "pcb", "drc", "--format", "json", "--severity-all", "--refill-zones",
             "--save-board", "--output", str(work / "plane-drc.json"), str(plane)], 60)
        run([sys.executable, __file__, "check", "plane", str(plane), str(work / "plane-check.json")], 45)
        short_drc = json.loads((work / "short-drc.json").read_text())
        plane_drc = json.loads((work / "plane-drc.json").read_text())
        short_check = json.loads((work / "short-check.json").read_text())
        plane_check = json.loads((work / "plane-check.json").read_text())
        require(any(row["type"] == "clearance" for row in short_drc["violations"]),
                "CLI DRC omitted deliberate short")
        report = {
            "status": "SAVED_FILE_ALL_LAYER_GRAPH_CONTROLS_PASSED",
            "native_version": "10.0.6",
            "production_inputs_modified": False,
            "fixtures": {"short_sha256": sha(short), "plane_filled_sha256": sha(plane)},
            "short_control": {"drc_violations": len(short_drc["violations"]),
                              "drc_unconnected": len(short_drc["unconnected_items"]),
                              "graph": short_check},
            "plane_control": {"drc_violations": len(plane_drc["violations"]),
                              "drc_unconnected": len(plane_drc["unconnected_items"]),
                              "graph": plane_check},
            "commands": stage,
            "reused_regression": {
                "pad_group_fingerprint_sha256": "c49025fc1bfa8f6f21a63c1864dfbf9f1a04cff5af9f10b762ff9ba13c712939",
                "guards": EXPECTED
            },
            "tool_hashes": {
                "tools/check_four_layer_graph.py": sha(__file__),
                "tools/check_printed_bell_power_rework.py": sha(ROOT / "tools/check_printed_bell_power_rework.py"),
                "tools/zone_graph.py": sha(ROOT / "tools/zone_graph.py")
            },
            "history": "Prior in-memory fixture assertion and later 0xC0000005 diagnostic remain unresolved; this control replaces that unsupported shared-live-object workflow.",
            "remaining_unqualified": [
                "routing masks/search layer state", "production plane topology and exclusions",
                "contact exclusions and private sense/current-path preservation"
            ]
        }
        REPORT.write_bytes((json.dumps(report, indent=2) + "\n").encode())
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", nargs="?", default="run", choices=("run", "create", "check"))
    parser.add_argument("kind", nargs="?")
    parser.add_argument("path", nargs="?")
    parser.add_argument("output", nargs="?")
    args = parser.parse_args()
    if args.operation == "create":
        create(args.kind, Path(args.path))
    elif args.operation == "check":
        check(args.kind, Path(args.path), Path(args.output))
    else:
        raise SystemExit(
            "Saved-fixture control remains unqualified; automatic reruns are disabled. "
            "See reports/four-layer-graph-file-control.json in printed-bell-four-layer. "
            "Review native plane creation, retained failure artifacts, exact short "
            "detection and the same-net layer-isolation witness before another run."
        )
