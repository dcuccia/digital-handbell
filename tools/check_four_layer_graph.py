# SPDX-License-Identifier: MIT
"""Deterministic in-memory qualification controls for all-layer copper graphs."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from check_printed_bell_power_rework import CopperGraph as PrimitiveGraph, rectangle
from zone_graph import CopperGraph as FilledGraph


def require(value, message):
    if not value:
        raise AssertionError(message)


def main():
    reused_inputs = {
        ROOT / "hardware/handbell/iterations/printed-bell-clock-draft/handbell.kicad_pcb":
            "a83cc417c96b05dd15c187e648b9fd2a35ba857c3a66f7d13aaaa42ae3bd9fff",
        ROOT / "hardware/handbell/iterations/printed-bell-four-layer/handbell.kicad_pcb":
            "d91837ed9f5cff10d709521e448f6deae3aac3a52abed88c34271ee809e25418",
        ROOT / "tools/check_printed_bell_power_rework.py":
            "f9f0ccb985c43a655b07d3a21a55cbbd8cb79cc459dc7b72888ac9630ccbffd3",
    }
    for path, expected in reused_inputs.items():
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                "Prior pad-group fingerprint cannot be reused after an input change: " + str(path))
    native = Path(os.environ["LOCALAPPDATA"]) / "Programs/KiCad/10.0/bin"
    dll_handle = os.add_dll_directory(str(native))
    sys.path.insert(0, str(native / "Lib/site-packages"))
    import pcbnew as pcb
    require(pcb.GetBuildVersion() == "10.0.6", "KiCad 10.0.6 required")

    class MemoryApi:
        def __init__(self, board):
            self.board = board
        def __getattr__(self, name):
            return getattr(pcb, name)
        def LoadBoard(self, path):
            return self.board

    def net(board, name):
        value = pcb.NETINFO_ITEM(board, name)
        board.Add(value)
        return value

    def track(board, value, layer, a, b):
        item = pcb.PCB_TRACK(board)
        item.SetStart(pcb.VECTOR2I(pcb.FromMM(a[0]), pcb.FromMM(a[1])))
        item.SetEnd(pcb.VECTOR2I(pcb.FromMM(b[0]), pcb.FromMM(b[1])))
        item.SetWidth(pcb.FromMM(.3))
        item.SetLayer(layer)
        item.SetNetCode(value.GetNetCode())
        board.Add(item)
        return item

    def via(board, value, at):
        item = pcb.PCB_VIA(board)
        item.SetPosition(pcb.VECTOR2I(pcb.FromMM(at[0]), pcb.FromMM(at[1])))
        item.SetWidth(pcb.FromMM(.8))
        item.SetDrill(pcb.FromMM(.4))
        item.SetLayerPair(pcb.F_Cu, pcb.B_Cu)
        item.SetNetCode(value.GetNetCode())
        board.Add(item)
        return item

    def graph(board, filled=False):
        return (FilledGraph if filled else PrimitiveGraph)(MemoryApi(board), "<memory>")

    four = pcb.BOARD()
    four.SetCopperLayerCount(4)
    settings = four.GetDesignSettings()
    settings.m_MinClearance = pcb.FromMM(.2)
    settings.m_CopperEdgeClearance = pcb.FromMM(.25)
    settings.m_HoleClearance = pcb.FromMM(.25)
    settings.m_HoleToHoleMin = pcb.FromMM(.25)
    settings.m_MaxError = pcb.FromMM(.001)
    for a, b in (((0, 0), (24, 0)), ((24, 0), (24, 14)),
                 ((24, 14), (0, 14)), ((0, 14), (0, 0))):
        edge = pcb.PCB_SHAPE(four)
        edge.SetShape(pcb.SHAPE_T_SEGMENT)
        edge.SetStart(pcb.VECTOR2I(pcb.FromMM(a[0]), pcb.FromMM(a[1])))
        edge.SetEnd(pcb.VECTOR2I(pcb.FromMM(b[0]), pcb.FromMM(b[1])))
        edge.SetWidth(pcb.FromMM(.05))
        edge.SetLayer(pcb.Edge_Cuts)
        four.Add(edge)
    sig, other, gnd = (net(four, name) for name in ("SIG", "OTHER", "GND"))
    f_alone = track(four, sig, pcb.F_Cu, (2, 2), (6, 2))
    i_alone = track(four, sig, pcb.In1_Cu, (2, 2), (6, 2))
    f_join = track(four, sig, pcb.F_Cu, (2, 6), (6, 6))
    i_join = track(four, sig, pcb.In1_Cu, (2, 6), (6, 6))
    through = via(four, sig, (6, 6))
    foreign = track(four, other, pcb.In1_Cu, (6, 4), (6, 8))

    zone = pcb.ZONE(four)
    zone.SetLayer(pcb.In1_Cu)
    zone.SetNetCode(gnd.GetNetCode())
    zone.SetOutline(rectangle(pcb, [12, 2, 20, 10]))
    zone.SetMinThickness(pcb.FromMM(.2))
    zone.SetPadConnection(pcb.ZONE_CONNECTION_FULL)
    four.Add(zone)
    ground_via = via(four, gnd, (14, 4))
    ground_f = track(four, gnd, pcb.F_Cu, (11, 4), (14, 4))
    ground_inner = track(four, gnd, pcb.In1_Cu, (18, 4), (19, 4))
    unrelated_in2 = track(four, gnd, pcb.In2_Cu, (16, 7), (19, 7))
    primitive = graph(four)
    uid = lambda item: item.m_Uuid.AsString()
    require(not primitive.connected(uid(ground_f), uid(ground_inner)),
            "Unfilled separated In1 GND witness is already connected")
    require(not primitive.connected(uid(ground_inner), uid(unrelated_in2)),
            "Unfilled In1/In2 witnesses are already connected")
    four.BuildConnectivity()
    fill_started = time.monotonic()
    require(pcb.ZONE_FILLER(four).Fill(four.Zones()), "Native In1 zone fill failed")
    fill_seconds = time.monotonic() - fill_started
    require(zone.HasFilledPolysForLayer(pcb.In1_Cu),
            "Native filler produced no In1 filled polygons")

    primitive = graph(four)
    require(not primitive.connected(uid(f_alone), uid(i_alone)),
            "Same-XY F/inner traces connected without a via")
    require(primitive.connected(uid(f_join), uid(i_join)),
            "Through via did not join F and inner trace")
    require(any(key[1] == pcb.In1_Cu for key in primitive.by_uuid[uid(through)]),
            "Through-via inner annulus was omitted")
    require(not primitive.connected(uid(through), uid(foreign)),
            "Different-net inner crossing was silently connected")
    require(any("OTHER" in short["nets"] and "SIG" in short["nets"]
                for short in primitive.shorts), "Different-net inner crossing was not reported")

    filled_graph = graph(four, True)
    require(filled_graph.connected(uid(ground_f), uid(ground_inner)),
            "Actual In1 filled island did not connect intended GND through via")
    require(not filled_graph.connected(uid(ground_inner), uid(unrelated_in2)),
            "In1 fill falsely connected unrelated In2-only conductor")
    require(any(row["layer"] == "In1.Cu" for row in filled_graph.zone_islands),
            "No exact native In1 filled-island witness")

    two = pcb.BOARD()
    two.SetCopperLayerCount(2)
    n2 = net(two, "TWO")
    two_f = track(two, n2, pcb.F_Cu, (2, 2), (5, 2))
    two_b = track(two, n2, pcb.B_Cu, (2, 2), (5, 2))
    two_unjoined_f = track(two, n2, pcb.F_Cu, (8, 2), (10, 2))
    two_unjoined_b = track(two, n2, pcb.B_Cu, (8, 2), (10, 2))
    two_via = via(two, n2, (5, 2))
    old = graph(two)
    require(old.connected(uid(two_f), uid(two_b)), "Two-layer via behavior regressed")
    require(not old.connected(uid(two_unjoined_f), uid(two_unjoined_b)),
            "Two-layer same-XY traces falsely connected")

    source = ROOT / "hardware/handbell/iterations/printed-bell-clock-draft/handbell.kicad_pcb"
    baseline = ROOT / "hardware/handbell/iterations/printed-bell-four-layer/handbell.kicad_pcb"
    source_fp = "c49025fc1bfa8f6f21a63c1864dfbf9f1a04cff5af9f10b762ff9ba13c712939"

    report = {
        "status": "GRAPH_ONLY_ALL_LAYER_CONTROL_PASSED",
        "stage": "graph qualification only; no production PCB, routing, plane, zone, or fill modified",
        "native_version": pcb.GetBuildVersion(),
        "physical_layer_order": [
            four.GetLayerName(layer) for layer in sorted(
                (x for x in four.GetEnabledLayers().Seq() if pcb.IsCopperLayer(x)),
                key=pcb.CopperLayerToOrdinal)],
        "controls": {
            "same_xy_f_inner_without_via_disconnected": True,
            "through_via_joins_declared_layers": True,
            "through_via_inner_pad_shape_included": True,
            "different_net_inner_crossing_reported_not_connected": True,
            "exact_native_filled_in1_island_connects_intended_ground_through_via": True,
            "in1_fill_does_not_connect_unrelated_in2_conductor": True,
            "two_layer_expected_connections_unchanged": True,
            "source_vs_baseline_existing_pad_group_fingerprint_equal": "reused from prior run; primitive graph source hash unchanged"
        },
        "native_fill_seconds": fill_seconds,
        "pad_group_fingerprint_sha256": source_fp,
        "source_pcb_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "baseline_pcb_sha256": hashlib.sha256(baseline.read_bytes()).hexdigest(),
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "graph_sources": {
            "tools/check_printed_bell_power_rework.py": hashlib.sha256(
                (ROOT / "tools/check_printed_bell_power_rework.py").read_bytes()).hexdigest(),
            "tools/zone_graph.py": hashlib.sha256(
                (ROOT / "tools/zone_graph.py").read_bytes()).hexdigest()
        },
        "fixture": "Fresh in-memory native boards; In1 zone produced by KiCad ZONE_FILLER and consumed through exact GetFilledPolysList islands; no fixture files serialized",
        "fixture_invariants": {
            "closed_edge_cuts_rectangle_mm": [0, 0, 24, 14],
            "explicit_min_clearance_mm": 0.2,
            "explicit_copper_edge_clearance_mm": 0.25,
            "unfilled_ground_witness_disconnected": True,
            "filled_ground_witness_connected": True,
            "in2_only_witness_isolated_before_and_after_fill": True
        },
        "prior_failed_fixture": "The first native-fill attempt lacked Edge.Cuts and used an invalid already-connected positive witness; it timed out after a kimath overflow assertion and is not evidence about real four-layer fill.",
        "remaining_unqualified": [
            "routing masks/search layer state",
            "production inner-plane fill and continuity",
            "contact exclusions and private sense/current-path preservation on inner layers"
        ]
    }
    encoded = (json.dumps(report, indent=2) + "\n").encode("utf-8")
    output = ROOT / "hardware/handbell/iterations/printed-bell-four-layer/reports/four-layer-graph-control.json"
    output.write_bytes(encoded)
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
