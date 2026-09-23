# SPDX-License-Identifier: MIT
"""Read-only validation of one preserved local GND stitch candidate.

This tool never fills, routes, or saves a board. It derives guard layers from
the native rule areas, runs a deliberately wrong mapping as a negative control,
then validates the candidate with the corrected same-layer mapping.
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

from kicad_sexpr import load

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from check_front_ground import board_polygon, compare_components
from zone_graph import CopperGraph, IslandItem, require

F_ZONE = "42e3abc5-2c92-5943-8944-bee0da8523c3"
IN1_ZONE = "332d3ba8-ed46-550f-912f-bb402cd2a16b"
ADDED_TRACK = "d8b2f3e7-cf20-5f17-a1d0-9a3e4ac6e256"
ADDED_VIA = "444b2c40-c122-5d7f-b56f-37b9a9100a99"
PRIVATE_VIAS = {
    "6623be95-c657-5a8e-bedb-c5a73d42d40b",
    "eafa404c-be47-5f5c-8167-d39a967ba2e5",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finding_signature(finding):
    return (
        finding["type"],
        finding["severity"],
        tuple(sorted(item.get("uuid", "") for item in finding.get("items", []))),
    )


def layer_name(pcb, layer):
    return pcb.LayerName(layer)


def circular_holes_violate_clearance(a, a_radius, b, b_radius, clearance):
    """Exact integer test: equality at the required clearance is accepted."""
    dx, dy = a.x - b.x, a.y - b.y
    limit = a_radius + b_radius + clearance
    return dx * dx + dy * dy < limit * limit


def polygon_delta(pcb, before, after):
    before_only = before.CloneDropTriangulation()
    after_only = after.CloneDropTriangulation()
    before_only.BooleanSubtract(after)
    after_only.BooleanSubtract(before)
    combined = before_only.CloneDropTriangulation()
    combined.Append(after_only)
    if combined.IsEmpty():
        bounds = None
    else:
        box = combined.BBox()
        bounds = [
            pcb.ToMM(box.GetLeft()), pcb.ToMM(box.GetTop()),
            pcb.ToMM(box.GetRight()), pcb.ToMM(box.GetBottom()),
        ]
    return {
        "before_only_area_mm2": before_only.Area() / 1e12,
        "candidate_only_area_mm2": after_only.Area() / 1e12,
        "symmetric_difference_area_mm2": (before_only.Area() + after_only.Area()) / 1e12,
        "symmetric_difference_bounds_native_mm": bounds,
    }


def raw_checks(source_path, candidate_path):
    source_text, source_root = load(source_path)
    candidate_text, candidate_root = load(candidate_path)
    excluded = {"segment", "via", "zone"}
    source_other = [source_text[node.start:node.end] for node in source_root.items
                    if getattr(node, "head", None) not in excluded]
    candidate_other = [candidate_text[node.start:node.end] for node in candidate_root.items
                       if getattr(node, "head", None) not in excluded]
    require(source_other == candidate_other, "Top-level non-track/non-via/non-zone source block changed")

    additions = {}
    for head in ("segment", "via"):
        old_nodes = source_root.children(head)
        new_nodes = candidate_root.children(head)
        old_raw = [source_text[node.start:node.end] for node in old_nodes]
        new_raw = [candidate_text[node.start:node.end] for node in new_nodes]
        require(new_raw[:len(old_raw)] == old_raw, "Existing raw " + head + " block changed")
        additions[head] = new_nodes[len(old_nodes):]
    require(len(additions["segment"]) == 1 and len(additions["via"]) == 1,
            "Candidate does not contain exactly one added segment and one added via")

    segment = additions["segment"][0]
    via = additions["via"][0]
    require(segment.value("uuid") == ADDED_TRACK and segment.value("layer") == "F.Cu"
            and segment.value("net") == "GND", "Added segment identity/layer/net differs")
    require(via.value("uuid") == ADDED_VIA and via.value("net") == "GND",
            "Added via identity/net differs")
    via_raw = candidate_text[via.start:via.end]
    require('(layers "F.Cu" "B.Cu")' in via_raw,
            "Added via source declaration is not explicitly F.Cu-to-B.Cu")

    source_zones = {zone.value("uuid"): zone for zone in source_root.children("zone")}
    candidate_zones = {zone.value("uuid"): zone for zone in candidate_root.children("zone")}
    require(len(source_zones) == len(candidate_zones) == 21
            and source_zones.keys() == candidate_zones.keys(), "Zone inventory changed")
    for uid, source_zone in source_zones.items():
        candidate_zone = candidate_zones[uid]
        source_children = [source_text[node.start:node.end] for node in source_zone.items
                           if getattr(node, "head", None) != "filled_polygon"]
        candidate_children = [candidate_text[node.start:node.end] for node in candidate_zone.items
                              if getattr(node, "head", None) != "filled_polygon"]
        require(source_children == candidate_children, "Zone definition changed: " + uid)
    return {
        "top_level_nontrack_nonvia_nonzone_blocks_exact": True,
        "existing_tracks_raw_exact": True,
        "existing_vias_raw_exact": True,
        "zone_definition_count": 21,
        "zone_definitions_except_fill_cache_exact": True,
        "added_segment_uuid": ADDED_TRACK,
        "added_via_uuid": ADDED_VIA,
        "added_via_declared_span": ["F.Cu", "B.Cu"],
    }


def partitions(graph, net):
    groups = defaultdict(list)
    for uid, pad in graph.pads.items():
        if pad.GetNetname() == net:
            groups[graph.components[graph.by_uuid[uid][0]]].append(
                pad.GetParentFootprint().GetReference() + "." + pad.GetNumber())
    return sorted(sorted(group) for group in groups.values())


def guard_inventory(pcb, graph):
    guards = []
    for zone in graph.board.Zones():
        if not zone.GetIsRuleArea():
            continue
        name = zone.GetZoneName()
        layers = list(zone.GetLayerSet().Seq())
        require(len(layers) == 1, "Guard has multiple/no layers: " + name)
        if name.startswith("private-"):
            expected_family = "F-private"
        elif name.startswith("in1-private/"):
            expected_family = "In1-private"
        elif name.startswith("in1-boost-sw/"):
            expected_family = "In1-BOOST_SW"
        elif name == "in1-clock-region":
            expected_family = "In1-clock"
        else:
            continue
        require(zone.GetDoNotAllowZoneFills()
                and not any((zone.GetDoNotAllowTracks(), zone.GetDoNotAllowVias(),
                             zone.GetDoNotAllowPads(), zone.GetDoNotAllowFootprints())),
                "Guard is not pour-only: " + name)
        guards.append({
            "uuid": zone.m_Uuid.AsString(),
            "name": name,
            "family": expected_family,
            "layer": layers[0],
            "polygon": zone.Outline().CloneDropTriangulation(),
        })
    counts = defaultdict(int)
    for guard in guards:
        counts[(guard["family"], layer_name(pcb, guard["layer"]))] += 1
    require(counts == {
        ("F-private", "F.Cu"): 10,
        ("In1-private", "In1.Cu"): 2,
        ("In1-BOOST_SW", "In1.Cu"): 6,
        ("In1-clock", "In1.Cu"): 1,
    }, "Native rule-area family/layer inventory differs")
    return guards


def guard_intersections(pcb, graph, guards, wrong_mapping=False):
    overlaps = []
    for item_uid, item in graph.items.items():
        if not isinstance(item, IslandItem):
            continue
        for guard in guards:
            assigned_layer = pcb.In1_Cu if wrong_mapping and guard["family"] == "F-private" else guard["layer"]
            if item.layer != assigned_layer:
                continue
            overlap = item.polygon.CloneDropTriangulation()
            overlap.BooleanIntersection(guard["polygon"])
            if not overlap.IsEmpty():
                box = overlap.BBox()
                overlaps.append({
                    "island_uuid": item_uid,
                    "island_layer": layer_name(pcb, item.layer),
                    "guard_uuid": guard["uuid"],
                    "guard_name": guard["name"],
                    "native_guard_layer": layer_name(pcb, guard["layer"]),
                    "assigned_layer": layer_name(pcb, assigned_layer),
                    "area_mm2": overlap.Area() / 1e12,
                    "bounds_native_mm": [
                        pcb.ToMM(box.GetLeft()), pcb.ToMM(box.GetTop()),
                        pcb.ToMM(box.GetRight()), pcb.ToMM(box.GetBottom()),
                    ],
                })
    return overlaps


def filled_checks(pcb, graph, manifest, guards):
    boundary = board_polygon(pcb, manifest, .25)
    checked = {"islands": 0, "guard_comparisons": 0, "foreign_comparisons": 0,
               "F_private_item_comparisons": 0, "In1_private_via_comparisons": 0}
    for item in graph.items.values():
        if not isinstance(item, IslandItem):
            continue
        require(item.layer in (pcb.F_Cu, pcb.In1_Cu), "Unexpected filled copper layer")
        checked["islands"] += 1
        outside = item.polygon.CloneDropTriangulation()
        outside.BooleanSubtract(boundary)
        require(outside.IsEmpty(), "Filled copper violates 0.25 mm board edge")
        for guard in guards:
            if guard["layer"] != item.layer:
                continue
            checked["guard_comparisons"] += 1
            overlap = item.polygon.CloneDropTriangulation()
            overlap.BooleanIntersection(guard["polygon"])
            require(overlap.IsEmpty(), "Same-layer guard overlap: " + guard["name"])
        for other in graph.items.values():
            if isinstance(other, IslandItem) or not other.IsOnLayer(item.layer) or other.GetNetname() == "GND":
                continue
            checked["foreign_comparisons"] += 1
            require(not item.polygon.Collide(other.GetEffectiveShape(item.layer), pcb.FromMM(.2) - 1),
                    "Filled copper violates 0.20 mm foreign-net clearance")
        if item.layer == pcb.F_Cu:
            for guard in guards:
                if guard["family"] != "F-private":
                    continue
                protected = guard["name"].rsplit("/", 1)[-1]
                checked["F_private_item_comparisons"] += 1
                require(not item.polygon.Collide(
                    graph.items[protected].GetEffectiveShape(pcb.F_Cu), pcb.FromMM(.25) - 1),
                    "F fill approaches protected private copper")
        if item.layer == pcb.In1_Cu:
            for uid in PRIVATE_VIAS:
                checked["In1_private_via_comparisons"] += 1
                require(not item.polygon.Collide(
                    graph.items[uid].GetEffectiveShape(pcb.In1_Cu), pcb.FromMM(.25) - 1),
                    "In1 fill approaches private through-via")
    return checked


def contact_metal_polygons(pcb, interface):
    result = []
    primitives = interface["right_contact_original_primitives"]
    for sign in (1, -1):
        for primitive in [*primitives["base_tabs"], primitives["under_cell_base"]]:
            xs = sorted(100 + sign * primitive[key] for key in ("x_min", "x_max"))
            ys = [100 - primitive["y_width"] / 2, 100 + primitive["y_width"] / 2]
            polygon = pcb.SHAPE_POLY_SET()
            index = polygon.NewOutline()
            for x, y in ((xs[0], ys[0]), (xs[1], ys[0]), (xs[1], ys[1]), (xs[0], ys[1])):
                polygon.Append(pcb.FromMM(x), pcb.FromMM(y), index)
            result.append(polygon)
    return result


def via_checks(pcb, before, after, interface):
    via = after.items[ADDED_VIA]
    require(isinstance(via, pcb.PCB_VIA), "Declared added via is not a via")
    require(abs(pcb.ToMM(via.GetWidth(pcb.F_Cu)) - .604) < 1e-6
            and abs(pcb.ToMM(via.GetDrillValue()) - .35) < 1e-6,
            "Added via diameter/drill differs")
    raw_layers = list(via.GetLayerSet().Seq())
    expected_layers = {pcb.F_Cu, pcb.In1_Cu, pcb.In2_Cu, pcb.B_Cu}

    def complete_layer_set(values):
        return set(values) == expected_layers

    require(complete_layer_set([pcb.In2_Cu, pcb.F_Cu, pcb.B_Cu, pcb.In1_Cu]),
            "Via layer-set control rejected a shuffled complete set")
    require(not complete_layer_set([pcb.F_Cu, pcb.B_Cu, pcb.In1_Cu]),
            "Via layer-set control accepted a set missing In2.Cu")
    require(complete_layer_set(raw_layers), "Added via does not span every enabled copper layer")
    physical_layers = sorted(raw_layers, key=pcb.CopperLayerToOrdinal)
    center = via.GetPosition()
    annulus = pcb.SHAPE_CIRCLE(center, pcb.FromMM(.302))
    hole = pcb.SHAPE_CIRCLE(center, pcb.FromMM(.175))
    pad_hits = []
    foreign_hits = []
    drill_hits = []
    circular_drills_checked = 0
    native_slot_drills_checked = 0
    for uid, item in before.items.items():
        if isinstance(item, IslandItem):
            continue
        if isinstance(item, pcb.PAD):
            for layer in (pcb.F_Cu, pcb.In1_Cu, pcb.In2_Cu, pcb.B_Cu):
                if item.IsOnLayer(layer) and item.GetEffectiveShape(layer).Collide(annulus, 0):
                    pad_hits.append(uid)
                    break
        if item.GetNetname() != "GND":
            for layer in (pcb.F_Cu, pcb.In1_Cu, pcb.In2_Cu, pcb.B_Cu):
                if item.IsOnLayer(layer) and item.GetEffectiveShape(layer).Collide(annulus, pcb.FromMM(.2) - 1):
                    foreign_hits.append(uid)
                    break
        if isinstance(item, pcb.PCB_VIA):
            circular_drills_checked += 1
            if circular_holes_violate_clearance(
                    center, pcb.FromMM(.175), item.GetPosition(),
                    item.GetDrillValue() // 2, pcb.FromMM(.2)):
                drill_hits.append(uid)
        elif isinstance(item, pcb.PAD):
            drill = item.GetDrillSize()
            if drill.x <= 0 or drill.y <= 0:
                continue
            if drill.x == drill.y:
                circular_drills_checked += 1
                if circular_holes_violate_clearance(
                        center, pcb.FromMM(.175), item.GetPosition(),
                        drill.x // 2, pcb.FromMM(.2)):
                    drill_hits.append(uid)
            else:
                require(hasattr(item, "GetEffectiveHoleShape"),
                        "KiCad PAD lacks native effective-hole geometry API")
                native_slot_drills_checked += 1
                if item.GetEffectiveHoleShape().Collide(hole, pcb.FromMM(.2) - 1):
                    drill_hits.append(uid)
    require(not pad_hits, "Added via overlaps a pad")
    require(not foreign_hits, "Added via violates foreign copper clearance")
    require(not drill_hits, "Added via violates existing drill clearance")
    metal_hits = [index for index, polygon in enumerate(contact_metal_polygons(pcb, interface))
                  if polygon.Collide(annulus, pcb.FromMM(.2) - 1)]
    require(not metal_hits, "Added via violates B contact-metal keepout")
    in1_island = next(item for item in after.items.values()
                      if isinstance(item, IslandItem) and item.zone_uuid == IN1_ZONE
                      and item.layer == pcb.In1_Cu)
    require(in1_island.polygon.Collide(annulus, 0), "Added via does not contact main In1 island")
    return {
        "uuid": ADDED_VIA,
        "position_native_mm": [pcb.ToMM(center.x), pcb.ToMM(center.y)],
        "diameter_mm": pcb.ToMM(via.GetWidth(pcb.F_Cu)),
        "drill_mm": pcb.ToMM(via.GetDrillValue()),
        "ordinary_through_via": True,
        "native_class": via.GetClass(),
        "source_declared_end_layers": ["F.Cu", "B.Cu"],
        "native_raw_layer_sequence": [layer_name(pcb, layer) for layer in raw_layers],
        "native_physical_layer_order": [layer_name(pcb, layer) for layer in physical_layers],
        "span_evidence": "Source explicitly declares F.Cu/B.Cu endpoints and native layer set contains exactly all four enabled copper layers.",
        "native_type_endpoint_API": "Not called: no repository-verified KiCad 10 Python usage was available; no signature was guessed.",
        "layer_set_negative_controls": {
            "shuffled_complete_set_accepted": True,
            "missing_In2_set_rejected": True,
        },
        "off_pad": True,
        "foreign_copper_clearance_mm": .2,
        "drill_clearance_mm": .2,
        "drill_geometry_checks": {
            "exact_integer_circular_holes": circular_drills_checked,
            "native_effective_slot_holes": native_slot_drills_checked,
            "minimum_clearance_boundary_is_accepted": True,
        },
        "B_contact_metal_keepout_clearance_mm": .2,
        "contacts_main_In1_island": True,
    }


def c9_path(pcb, graph):
    start = graph.pad_uuid("C9", "2")
    path = graph.path(start, ADDED_VIA, pcb.F_Cu)
    require(path, "No native F.Cu path from C9.2 to the added via")
    uuids = list(dict.fromkeys(node["uuid"] for node in path))
    track_lengths = {}
    for uid in uuids:
        item = graph.items[uid]
        if isinstance(item, pcb.PCB_TRACK) and not isinstance(item, pcb.PCB_VIA):
            track_lengths[uid] = pcb.ToMM(item.GetLength())
    return {
        "from": "C9.2",
        "to_added_via_uuid": ADDED_VIA,
        "all_F_Cu": all(node["layer"] == "F.Cu" for node in path),
        "copper_uuids": uuids,
        "track_lengths_mm": track_lengths,
        "total_track_length_mm": sum(track_lengths.values()),
        "declared_new_stub_length_mm": track_lengths.get(ADDED_TRACK),
        "interpretation": "Existing reachable-group path length; the 0.65 mm new stub is not a local C9 decoupler-return length.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--candidate-sha256", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--saved-drc", type=Path, required=True)
    parser.add_argument("--baseline-drc", type=Path, required=True)
    parser.add_argument("--interface", type=Path, required=True)
    parser.add_argument("--previous-failed-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    report = {
        "status": "FAILED",
        "scope": "Read-only validation of preserved candidate geometry; no route, refill, board save, or promotion.",
        "gates": [],
        "missing_history": {
            "finite_candidate_site_count": "NOT_RECORDED; not re-screened",
            "remaining_released_group_blockers": "UNKNOWN; not re-screened",
        },
        "design_files_written": False,
    }

    def gate(name, detail=True):
        report["gates"].append({"name": name, "passed": True, "detail": detail})

    try:
        bindings = {
            "source_pcb_sha256": sha(args.source),
            "candidate_pcb_sha256": sha(args.candidate),
            "manifest_sha256": sha(args.manifest),
            "saved_drc_sha256": sha(args.saved_drc),
            "baseline_drc_sha256": sha(args.baseline_drc),
            "battery_contact_interface_sha256": sha(args.interface),
            "previous_failed_report_sha256": sha(args.previous_failed_report),
            "source_project_sha256": sha(args.source.with_suffix(".kicad_pro")),
            "candidate_project_sha256": sha(args.candidate.with_suffix(".kicad_pro")),
        }
        require(bindings["source_pcb_sha256"] == args.source_sha256, "Source PCB hash guard failed")
        require(bindings["candidate_pcb_sha256"] == args.candidate_sha256, "Candidate PCB hash guard failed")
        require(bindings["manifest_sha256"] == args.manifest_sha256, "Manifest hash guard failed")
        require(bindings["source_project_sha256"] == bindings["candidate_project_sha256"],
                "Candidate project bytes differ from source project")
        for name in ("handbell.kicad_sch", "fp-lib-table", "sym-lib-table",
                     "Handbell.kicad_sym", "T8.kicad_sym", "Clock.kicad_sym",
                     "battery-contact-interface.json"):
            require(sha(args.source.parent / name) == sha(args.candidate.parent / name),
                    "Candidate dependency differs: " + name)
        gate("hash_and_project_dependency_binding", bindings)

        raw = raw_checks(args.source, args.candidate)
        gate("source_preserving_geometry", raw)

        native = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin"
        dll_handle = os.add_dll_directory(str(native))
        sys.path.insert(0, str(native / "Lib/site-packages"))
        import pcbnew as pcb
        require(pcb.GetBuildVersion() == "10.0.6", "KiCad 10.0.6 required")
        before = CopperGraph(pcb, args.source)
        after = CopperGraph(pcb, args.candidate)
        gate("native_board_loads", {"kicad_version": pcb.GetBuildVersion()})

        guards_before = guard_inventory(pcb, before)
        guards_after = guard_inventory(pcb, after)
        require([(x["uuid"], x["name"], x["family"], x["layer"]) for x in guards_before]
                == [(x["uuid"], x["name"], x["family"], x["layer"]) for x in guards_after],
                "Native guard inventory changed")
        wrong = guard_intersections(pcb, before, guards_before, wrong_mapping=True)
        correct_baseline = guard_intersections(pcb, before, guards_before)
        correct_candidate = guard_intersections(pcb, after, guards_after)
        require(wrong, "Negative control did not reproduce the original wrong-layer failure")
        require(not correct_baseline, "Correct same-layer mapping fails accepted baseline")
        require(not correct_candidate, "Correct same-layer mapping fails candidate")
        gate("guard_layer_controls", {
            "native_rule_area_counts": {"F.Cu": 10, "In1.Cu": 9},
            "negative_control_wrong_mapping_baseline_overlap_count": len(wrong),
            "negative_control_first_overlap": wrong[0],
            "correct_same_layer_baseline_overlap_count": 0,
            "correct_same_layer_candidate_overlap_count": 0,
        })

        manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
        interface = json.loads(args.interface.read_text(encoding="utf-8-sig"))
        fill_checks = filled_checks(pcb, after, manifest, guards_after)
        gate("actual_F_In1_edge_foreign_guard_private_checks", fill_checks)

        preserved = compare_components(before, after)
        before_parts = {net: partitions(before, net) for net in ("GND", "+3V3", "VCORE")}
        after_parts = {net: partitions(after, net) for net in ("GND", "+3V3", "VCORE")}
        require(before_parts["+3V3"] == after_parts["+3V3"] and len(after_parts["+3V3"]) == 1,
                "+3V3 partition changed")
        require(before_parts["VCORE"] == after_parts["VCORE"] and len(after_parts["VCORE"]) == 3,
                "VCORE partition changed")
        require(len(before_parts["GND"]) - len(after_parts["GND"]) == 1, "GND did not merge exactly one group")
        main = next(group for group in after_parts["GND"] if "MH1.1" in group)
        require(all(name in main for name in ("C9.2", "R4.1", "R8.2")), "C9/R4/R8 group did not join MAIN GND")
        pickoffs = [after.pickoff("R26", "2", "R27", "2"),
                    after.pickoff("R24", "2", "C28", "2")]
        require(all(row["independent_until_terminal"] for row in pickoffs), "Private pickoff bypass")
        require(not after.shorts and not after.floating_copper(), "Short or floating copper")
        for net in sorted({pad.GetNetname() for pad in before.pads.values()} - {"", "GND"}):
            require(partitions(before, net) == partitions(after, net), "Other-net partition changed: " + net)
        gate("full_connectivity_and_component_comparison", {
            "source_connected_pad_groups_preserved": preserved,
            "GND_group_count_before": len(before_parts["GND"]),
            "GND_group_count_candidate": len(after_parts["GND"]),
            "plus3V3_group_count": 1,
            "VCORE_group_count": 3,
            "target_group_joined_MAIN": True,
            "private_pickoffs": pickoffs,
            "shorts": [],
            "floating_copper": [],
            "other_net_partitions_unchanged": True,
        })

        via = via_checks(pcb, before, after, interface)
        path = c9_path(pcb, after)
        track = after.items[ADDED_TRACK]
        require(isinstance(track, pcb.PCB_TRACK) and not isinstance(track, pcb.PCB_VIA)
                and track.GetLayer() == pcb.F_Cu
                and abs(pcb.ToMM(track.GetWidth()) - .3) < 1e-6
                and abs(pcb.ToMM(track.GetLength()) - .65) < 1e-6,
                "Declared added F stub geometry differs")
        gate("released_geometry_and_clearance", {"stub": {
            "uuid": ADDED_TRACK, "layer": "F.Cu", "width_mm": pcb.ToMM(track.GetWidth()),
            "length_mm": pcb.ToMM(track.GetLength())}, "via": via, "C9_to_via_path": path})

        fill_delta = {}
        for layer in (pcb.F_Cu, pcb.In1_Cu):
            source_zone = next(zone for zone in before.board.Zones()
                               if not zone.GetIsRuleArea() and zone.IsOnLayer(layer))
            candidate_zone = next(zone for zone in after.board.Zones()
                                  if not zone.GetIsRuleArea() and zone.m_Uuid.AsString() == source_zone.m_Uuid.AsString())
            fill_delta[layer_name(pcb, layer)] = polygon_delta(
                pcb, source_zone.GetFilledPolysList(layer), candidate_zone.GetFilledPolysList(layer))
        gate("actual_fill_symmetric_difference", fill_delta)

        baseline_drc = json.loads(args.baseline_drc.read_text(encoding="utf-8-sig"))
        saved_drc = json.loads(args.saved_drc.read_text(encoding="utf-8-sig"))
        require(saved_drc["source"] == args.candidate.name
                and baseline_drc["source"] == args.source.name, "Saved DRC source stem differs")
        baseline_signatures = {finding_signature(row) for row in baseline_drc["violations"]}
        new_findings = [row for row in saved_drc["violations"]
                        if finding_signature(row) not in baseline_signatures]
        baseline_warnings = sum(row["severity"] == "warning" for row in baseline_drc["violations"])
        candidate_warnings = sum(row["severity"] == "warning" for row in saved_drc["violations"])
        require(len(baseline_drc["unconnected_items"]) == 48
                and len(saved_drc["unconnected_items"]) == 47, "Saved DRC open-count delta differs")
        require(baseline_warnings == candidate_warnings == 233, "Saved DRC warning count differs")
        require(not new_findings, "Saved DRC contains a new non-open finding")
        after.board.BuildConnectivity()
        native_opens = int(after.board.GetConnectivity().GetUnconnectedCount(False))
        graph_opens = sum(len(net["islands"]) - 1 for net in after.nets())
        require(native_opens == graph_opens == 47, "Native/graph/saved DRC open counts differ")
        gate("saved_native_DRC_reuse", {
            "reuse_basis": "Candidate, same-stem project, source dependencies and saved DRC bytes hash-bound before reuse; no refill or fresh DRC.",
            "source_opens": 48, "candidate_opens": 47,
            "source_warnings": 233, "candidate_warnings": 233,
            "new_non_open_findings": [],
            "native_read_only_connectivity_opens": native_opens,
            "independent_graph_opens": graph_opens,
        })

        require(bindings["source_pcb_sha256"] == sha(args.source)
                and bindings["candidate_pcb_sha256"] == sha(args.candidate)
                and bindings["manifest_sha256"] == sha(args.manifest),
                "An immutable board/manifest input changed during validation")
        report.update({
            "status": "PASSED_READ_ONLY_CONNECTIVITY_MILESTONE_VALIDATION",
            "input_sha256": bindings,
            "previous_failed_validation_history": {
                "file": args.previous_failed_report.name,
                "sha256": bindings["previous_failed_report_sha256"],
                "status": "Preserved immutable failed history; this result is a separate corrective execution and is not retroactive.",
            },
            "corrected_validator": {
                "filename": Path(__file__).name,
                "sha256": sha(__file__),
                "preserved_failed_checker_sha256": "635803e78df35fc261bd07fb76e300515cc8971b96e229c960dd4b9e74715e5a",
            },
            "engineering_disposition": {
                "candidate_connectivity_milestone_full_gates_passed": True,
                "C9_local_return_qualified": False,
                "reason": "The accepted witness uses the remote reachable R4.1 terminal; connectivity does not qualify a local C9 decoupler return.",
                "remaining_release_gates": [
                    "Astra/root promotion decision",
                    "Remaining released GND groups require separate finite screening history",
                    "VCORE remains open",
                    "Physical stackup, SI/PI, current, thermal and manufacturing qualification remain pending",
                ],
            },
        })
        dll_handle.close()
    except Exception as error:
        report["failure"] = {"type": type(error).__name__, "message": str(error)}
    report["elapsed_seconds"] = time.monotonic() - started
    report["report_tool_sha256"] = sha(__file__)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "report_sha256": sha(args.output),
        "failure": report.get("failure"),
        "elapsed_seconds": report["elapsed_seconds"],
    }, indent=2))
    if report["status"] == "FAILED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
