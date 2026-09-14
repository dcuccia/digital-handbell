# SPDX-License-Identifier: MIT
"""Read-only filled-ground continuity/protection check; not a DRC or release gate.

Use an external process deadline; native graph construction can take minutes.
Requires KiCad 10.0.6,
an already-filled baseline, the candidate's bound manifest and the public plan.
Never loads the private recovery package, fills zones or saves either board.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

import zone_graph
from zone_graph import CopperGraph, IslandItem, require, self_test

ZONE_UUID = "42e3abc5-2c92-5943-8944-bee0da8523c3"
PAIRS = (("R26", "R27"), ("R24", "C28"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounds_polygon(pcb, record):
    polygon = pcb.SHAPE_POLY_SET()
    index = polygon.NewOutline()
    a, b, c, d = record["bounds_absolute_iu"]
    for x, y in ((a, b), (c, b), (c, d), (a, d)):
        polygon.Append(x, y, index)
    return polygon


def board_polygon(pcb, manifest, inset):
    polygon = pcb.SHAPE_POLY_SET()
    index = polygon.NewOutline()
    points = manifest["board"]["outline_common_xy_mm"]
    require(len(points) >= 3, "Actual manifest outline is missing")
    for x, y in points:
        require(math.isfinite(x) and math.isfinite(y), "Invalid manifest outline")
        polygon.Append(pcb.FromMM(x + 100), pcb.FromMM(y + 100), index)
    if inset:
        polygon.Deflate(pcb.FromMM(inset), pcb.CORNER_STRATEGY_ALLOW_ACUTE_CORNERS, pcb.FromMM(.001))
    require(polygon.OutlineCount() == 1 and polygon.HoleCount(0) == 0,
            "Inset board outline is not one simple region; explicit review required")
    return polygon


def validate_filled_graph(graph, plan, manifest):
    """Retain the exercised filled-area, foreign-net and private-terminal guards."""
    pcb = graph.pcb
    require(graph.zone_islands, "No native filled islands present")
    parameters = plan["parameters"]
    regions = plan["protection"]["pour_only_F_keepouts"]
    by_id = {zone.m_Uuid.AsString(): zone for zone in graph.board.Zones()}
    expected = {ZONE_UUID} | {r["uuid"] for r in regions}
    require(len(regions) == 10 and len(expected) == 11 and set(by_id) == expected,
            "Expected the recorded one-zone/ten-exclusion plan exactly")
    zone = by_id[ZONE_UUID]
    require(list(zone.GetLayerSet().Seq()) == [pcb.F_Cu]
            and zone.GetPadConnection() == pcb.ZONE_CONNECTION_FULL
            and zone.GetMinThickness() == pcb.FromMM(.25)
            and zone.GetIslandRemovalMode() == pcb.ISLAND_REMOVAL_MODE_ALWAYS
            and zone.GetFillMode() == pcb.ZONE_FILL_MODE_POLYGONS
            and zone.GetThermalReliefGap() == pcb.FromMM(.25)
            and zone.GetThermalReliefSpokeWidth() == pcb.FromMM(.25),
            "Actual saved native zone settings differ")
    require(zone.GetLocalClearance() == pcb.FromMM(parameters["clearance_mm"]),
            "Actual native zone clearance differs")
    require(parameters["clearance_mm"] >= .2 and parameters["edge_clearance_mm"] >= .25,
            "Ground fill cannot lower the explicit clearance/edge floor")
    for record in regions:
        area = by_id[record["uuid"]]
        require(area.GetIsRuleArea() and list(area.GetLayerSet().Seq()) == [pcb.F_Cu]
                and area.GetDoNotAllowZoneFills()
                and not any((area.GetDoNotAllowTracks(), area.GetDoNotAllowVias(),
                             area.GetDoNotAllowPads(), area.GetDoNotAllowFootprints())),
                "Actual keepout is not an F-only pour-only rule area")
        expected_polygon = bounds_polygon(pcb, record)
        remainder = area.Outline().CloneDropTriangulation()
        remainder.BooleanSubtract(expected_polygon)
        expected_polygon.BooleanSubtract(area.Outline())
        require(remainder.IsEmpty() and expected_polygon.IsEmpty(), "Native private keepout geometry differs")
    boundary = board_polygon(pcb, manifest, parameters["edge_clearance_mm"])
    for item in graph.items.values():
        if not isinstance(item, IslandItem):
            continue
        require(item.zone_uuid == ZONE_UUID and item.layer == pcb.F_Cu, "Unknown/B filled copper")
        outside = item.polygon.CloneDropTriangulation()
        outside.BooleanSubtract(boundary)
        require(outside.IsEmpty(), "Filled copper violates the explicit edge setback")
        for record in regions:
            overlap = item.polygon.CloneDropTriangulation()
            overlap.BooleanIntersection(bounds_polygon(pcb, record))
            require(overlap.IsEmpty(), "F fill enters a protected private branch/raw-contact exclusion")
            uid = record.get("protected_item_uuid")
            if uid and graph.items[uid].IsOnLayer(pcb.F_Cu):
                require(not item.polygon.Collide(graph.items[uid].GetEffectiveShape(pcb.F_Cu),
                                                pcb.FromMM(.25) - 1),
                        "F plane approaches protected private pad/trace/via copper")
        for other in graph.items.values():
            if isinstance(other, IslandItem) or not other.IsOnLayer(pcb.F_Cu) or other.GetNetname() == "GND":
                continue
            require(not item.polygon.Collide(other.GetEffectiveShape(pcb.F_Cu),
                                            pcb.FromMM(parameters["clearance_mm"]) - 1),
                    "Actual zone violates foreign-net clearance, including CELL_NEG")
    for a, b in PAIRS:
        require(graph.pickoff(a, "2", b, "2")["independent_until_terminal"],
                "Filled plane bypasses actual private pickoff terminal: " + a)
    require(not graph.shorts and not graph.floating_copper(),
            "Actual filled graph has cross-net shorts or floating copper")


def compare_components(before, after):
    require(before.pads.keys() == after.pads.keys(), "Physical pad inventory changed")
    groups = defaultdict(list)
    for uid, pad in before.pads.items():
        require(pad.GetNetname() == after.pads[uid].GetNetname(), "Physical pad net changed: " + uid)
        if not pad.GetNetname():
            continue
        components = {before.components[v] for v in before.by_uuid[uid]}
        require(len(components) == 1 and bool(after.by_uuid[uid]), "Missing/disjoint pad copper: " + uid)
        groups[next(iter(components))].append(uid)
    splits = [members for members in groups.values()
              if len({after.components[v] for uid in members for v in after.by_uuid[uid]}) != 1]
    require(not splits, "Previously connected pad groups split: " + json.dumps(splits))
    return len(groups)


def component_comparison_self_test():
    from copy import deepcopy
    from types import SimpleNamespace

    class Pad:
        def GetNetname(self):
            return "GND"

    before = SimpleNamespace(
        pads={key: Pad() for key in ("a", "b", "c")},
        by_uuid={key: [(key, 0)] for key in ("a", "b", "c")},
        components={("a", 0): 0, ("b", 0): 0, ("c", 0): 1})
    merged = deepcopy(before)
    merged.components[("c", 0)] = 0
    require(compare_components(before, merged) == 2, "Harmless component merge rejected")
    for failure in ("split", "missing_pad", "missing_copper"):
        after = deepcopy(before)
        if failure == "split":
            after.components[("b", 0)] = 2
        elif failure == "missing_pad":
            del after.pads["b"]
        else:
            after.by_uuid["b"] = []
        try:
            compare_components(before, after)
        except ValueError:
            continue
        raise ValueError("Component comparison missed " + failure)
    return {"merge_allowed": True, "split_rejected": True,
            "missing_pad_rejected": True, "missing_copper_rejected": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest_path = args.manifest or args.candidate.parent / "placement-manifest.json"
    sources = {"candidate": args.candidate, "baseline": args.baseline,
               "plan": args.plan, "manifest": manifest_path}
    require(not args.output.exists() and args.output.resolve() not in {p.resolve() for p in sources.values()},
            "Output must be a new report, not an input file")
    bindings = {name: sha(path) for name, path in sources.items()}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    plan = json.loads(args.plan.read_text(encoding="utf-8-sig"))
    require(manifest["generated_pcb_sha256"] == bindings["candidate"], "Manifest does not bind the candidate")
    require(plan["schema_version"] == 1 and plan["zone_uuid"] == ZONE_UUID, "Unexpected public plan contract")
    if os.name == "nt":
        folder = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin"
        dll_handle = os.add_dll_directory(str(folder))
        sys.path.insert(0, str(folder / "Lib" / "site-packages"))
    import pcbnew as pcb

    require(pcb.GetBuildVersion() == "10.0.6", "KiCad 10.0.6 required")
    started = time.monotonic()
    cpu_started = time.process_time()
    synthetic = self_test(pcb)
    component_tests = component_comparison_self_test()
    before = CopperGraph(pcb, args.baseline)
    baseline_seconds = time.monotonic() - started
    print("Baseline graph complete", round(baseline_seconds, 2), "s", flush=True)
    after = CopperGraph(pcb, args.candidate)
    graphs_seconds = time.monotonic() - started
    print("Candidate graph complete", round(graphs_seconds, 2), "s", flush=True)
    validate_filled_graph(after, plan, manifest)
    group_count = compare_components(before, after)
    after.board.BuildConnectivity()
    native_opens = int(after.board.GetConnectivity().GetUnconnectedCount(False))
    nets = after.nets()
    graph_opens = sum(len(n["islands"]) - 1 for n in nets)
    require(native_opens == graph_opens, "Native and independent connectivity counts differ")
    require(bindings == {name: sha(path) for name, path in sources.items()}, "An input changed during checking")
    report = {
        "status": "GROUND_CHECK_PASSED_WITH_REMAINING_OPENS" if native_opens else "GROUND_CHECK_PASSED",
        "scope": "Filled-ground connectivity and protection only. Does not run or replace DRC, complete CAD, assembly or powered qualification.",
        "input_sha256": bindings, "kicad_version": pcb.GetBuildVersion(),
        "tool_sha256": {
            "check_front_ground.py": sha(Path(__file__)),
            "zone_graph.py": sha(Path(zone_graph.__file__)),
            "check_printed_bell_power_rework.py": sha(Path(__file__).with_name("check_printed_bell_power_rework.py")),
        },
        "synthetic_geometry_checks": synthetic, "previous_connected_groups_preserved": group_count,
        "component_comparison_checks": component_tests,
        "split_previously_connected_groups": [],
        "native_unconnected": native_opens, "independent_graph_unconnected": graph_opens,
        "private_pickoffs": [after.pickoff(a, "2", b, "2") for a, b in PAIRS],
        "filled_islands": after.zone_islands, "shorts": after.shorts, "floating_copper": after.floating_copper(),
        "remaining_nets": [{"net": n["net"], "opens": len(n["islands"]) - 1} for n in nets if len(n["islands"]) > 1],
        "elapsed_seconds": {"baseline_graph": baseline_seconds, "both_graphs": graphs_seconds,
                            "total": time.monotonic() - started,
                            "process_cpu": time.process_time() - cpu_started},
        "design_files_written": False, "private_recovery_dependency": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"status": report["status"], "native_opens": native_opens,
                      "seconds": round(report["elapsed_seconds"]["total"], 2)}))


if __name__ == "__main__":
    main()
