# SPDX-License-Identifier: MIT
"""Append one real native F.Cu GND fill without reserializing existing copper.

Run with KiCad 10.0.6 bundled Python, only after all routing/native jobs stop:
    python.exe fill_ground.py --self-test
    python.exe fill_ground.py --apply
    python.exe check.py --run-native

--apply is deliberately one-shot: existing zones or edited/unbound inputs fail.
There is no generator invocation, automatic refill, B pour, new track or via.
Solid pad connections avoid adding unreviewed thermal-spoke necks, but increase
assembly heat demand. Neither that choice nor this fill qualifies soldering,
current, noise, thermal performance, a continuous B return, or fabrication.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
from zone_graph import CopperGraph, IslandItem, bbox, native_polygon, rectangle, require, self_test
from kicad_sexpr import loads

ZONE_UUID = str(uuid.uuid5(uuid.NAMESPACE_URL, "handbell/quote/F.Cu/GND/native-fill/v1"))
ZONE_NAME = "quote-native-F-GND-v1"
REPORT = "reports/ground-fill.json"
BASELINE = "routing/ground-fill-input.kicad_pcb"
BEFORE_DRC = "reports/ground-fill-before-drc.json"
AFTER_DRC = "reports/ground-fill-drc.json"
ZONE_INPUTS = (REPORT, BASELINE, BEFORE_DRC, AFTER_DRC)
CLEARANCE_MM = .2
EDGE_MM = .25
MIN_THICKNESS_MM = .25
PRIVATE_GAP_MM = .25
POLYGON_ERROR_MM = .001
PAIRS = (("R26", "R27"), ("R24", "C28"))
_DLLS = []


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def encoded(value):
    return (json.dumps(value, indent=2) + "\n").encode("utf-8")


def native():
    import check
    pcb, identity = check.native_api()
    return pcb, identity


def rectangle_record(pcb, name, bounds, **extra):
    require(len(bounds) == 4 and bounds[0] < bounds[2] and bounds[1] < bounds[3],
            "Empty keepout bounds")
    return {"uuid": str(uuid.uuid5(uuid.NAMESPACE_URL, "handbell/quote/pour-only/v1/" + name)),
            "name": name, "bounds_absolute_iu": list(map(int, bounds)), **extra}


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
        polygon.Deflate(pcb.FromMM(inset), pcb.CORNER_STRATEGY_ALLOW_ACUTE_CORNERS,
                        pcb.FromMM(POLYGON_ERROR_MM))
    require(polygon.OutlineCount() == 1 and polygon.HoleCount(0) == 0,
            "Inset board outline is not one simple region; explicit review required")
    return polygon


def protection_plan(graph, data, contact):
    """Use real private branches AND validate quiet_paths against native tracks.

    Bounding boxes are deliberately conservative pour-only exclusions around
    actual copper shapes. Both off-pad annuli on a B-mediated path are included.
    The whole target land is excluded; its existing bus must exit elsewhere.
    """
    pcb = graph.pcb
    gap = pcb.FromMM(PRIVATE_GAP_MM + POLYGON_ERROR_MM)
    keepouts, witnesses, consumed = {}, [], set()
    quiet = data["quiet_paths"]
    require(quiet, "Private GND quiet_paths are absent")
    tracks = list(graph.board.GetTracks())

    def add(uid, name):
        item = graph.items[uid]
        if not item.IsOnLayer(pcb.F_Cu):
            return
        box = bbox(item.GetEffectiveShape(pcb.F_Cu))
        box = [box[0]-gap, box[1]-gap, box[2]+gap, box[3]+gap]
        record = rectangle_record(pcb, name + "/" + uid, box, protected_item_uuid=uid)
        keepouts[record["uuid"]] = record

    for start_ref, target_ref in PAIRS:
        start = graph.pad_uuid(start_ref, "2")
        target = graph.pad_uuid(target_ref, "2")
        require(graph.pads[start].GetNetname() == graph.pads[target].GetNetname() == "GND",
                "Private path net must remain GND")
        witness = graph.pickoff(start_ref, "2", target_ref, "2")
        require(witness["independent_until_terminal"], "Existing private pickoff is not independent: " + start_ref)
        branch = set(witness["branch_copper_uuids"])
        matched = []
        for index, record in enumerate(quiet):
            if record["terminal"]["uuid"] != target:
                continue
            require(record["terminal"]["reference"] == target_ref
                    and record["terminal"]["number"] == "2"
                    and record.get("net", "GND") == "GND", "Quiet path terminal/net changed")
            layer = {"F.Cu": pcb.F_Cu, "B.Cu": pcb.B_Cu}[record["layer"]]
            a, b = [[pcb.FromMM(v + 100) for v in record[key]] for key in ("a", "b")]
            matches = []
            for item in tracks:
                if isinstance(item, pcb.PCB_VIA) or item.GetNetname() != "GND" or item.GetLayer() != layer:
                    continue
                aa, bb = item.GetStart(), item.GetEnd()
                p, q = [aa.x, aa.y], [bb.x, bb.y]
                same = (math.dist(a, p) <= 2 and math.dist(b, q) <= 2)
                reverse = (math.dist(a, q) <= 2 and math.dist(b, p) <= 2)
                if (same or reverse) and abs(item.GetWidth()-pcb.FromMM(record["width"])) <= 2:
                    matches.append(item.m_Uuid.AsString())
            require(len(matches) == 1 and matches[0] in branch,
                    "quiet_paths segment is absent/ambiguous/outside actual private branch")
            matched.extend(matches)
            consumed.add(index)
        require(matched, "Missing actual quiet route segments: " + start_ref)
        name = f"private-{start_ref}.2-to-{target_ref}.2"
        for uid in sorted(branch | {start, target}):
            add(uid, name)
        witnesses.append({**witness, "quiet_path_native_track_uuids": matched,
                          "excluded_terminal_neighbourhood": target,
                          "F_annuli_included": sorted(uid for uid in branch
                                                     if isinstance(graph.items[uid], pcb.PCB_VIA))})
    require(consumed == set(range(len(quiet))), "Unknown/unprotected quiet_paths record")
    require(all(pad.IsOnLayer(pcb.B_Cu) and not pad.IsOnLayer(pcb.F_Cu)
                for pad in graph.pads.values() if pad.GetParentFootprint().GetReference() in ("BT1","BT2")),
            "Raw contacts must remain rear-only SMT pads")
    return {"pour_only_F_keepouts": sorted(keepouts.values(), key=lambda r: r["uuid"]),
            "private_pickoffs_before": witnesses, "private_copper_gap_mm": PRIVATE_GAP_MM,
            "bbox_extra_polygon_error_mm": POLYGON_ERROR_MM,
            "raw_contact_projection_excluded_on_F": False,
            "contact_scope": "Foreign B copper and through vias remain excluded; F ground is separated by FR4 and no new vias are added"}


def settings_for_fill(pcb, board, project):
    require(not (HERE / "handbell.kicad_dru").exists(),
            "Unbound custom rules require explicit integration before native filling")
    rules = project["board"]["design_settings"]["rules"]
    clearances = [CLEARANCE_MM, rules["min_clearance"]]
    clearances += [c["clearance"] for c in project["net_settings"]["classes"]]
    require(all(math.isfinite(v) and v > 0 for v in clearances), "Invalid project clearances")
    clearance = max(clearances)
    edge = max(EDGE_MM, rules["min_copper_edge_clearance"])
    settings = board.GetDesignSettings()
    settings.m_MinClearance = pcb.FromMM(clearance)
    settings.m_CopperEdgeClearance = pcb.FromMM(edge)
    settings.m_HoleClearance = pcb.FromMM(max(.25, rules["min_hole_clearance"]))
    settings.m_HoleToHoleMin = pcb.FromMM(max(.25, rules["min_hole_to_hole"]))
    settings.m_MaxError = pcb.FromMM(min(POLYGON_ERROR_MM, rules["max_error"]))
    return {
        "clearance_mm": pcb.ToMM(settings.m_MinClearance),
        "edge_clearance_mm": pcb.ToMM(settings.m_CopperEdgeClearance),
        "hole_clearance_mm": pcb.ToMM(settings.m_HoleClearance),
        "hole_to_hole_mm": pcb.ToMM(settings.m_HoleToHoleMin),
        "polygon_error_mm": pcb.ToMM(settings.m_MaxError),
        "min_thickness_mm": MIN_THICKNESS_MM, "pad_connection": "solid",
        "thermal_gap_mm": .25, "thermal_spoke_width_mm": .25,
        "island_removal": "always", "layer": "F.Cu", "net": "GND",
        "preserved_front_GND_connection_overrides": [
            {"pad_uuid": pad.m_Uuid.AsString(), "reference": fp.GetReference(),
             "number": pad.GetNumber(), "native_override": int(pad.GetZoneConnectionOverrides())}
            for fp in board.GetFootprints() for pad in fp.Pads()
            if pad.IsOnLayer(pcb.F_Cu) and pad.GetNetname() == "GND"
            and pad.GetZoneConnectionOverrides() != pcb.ZONE_CONNECTION_INHERITED
        ],
        "rule_basis": "Explicit conservative native settings: max of project netclass/global clearance and .2 mm; edge >=.25 mm. Project bytes unchanged.",
        "pad_connection_tradeoff": "Solid zone default, preserving all source pad/footprint overrides. Increased assembly heat demand is not solder-process or thermal qualification.",
    }


def add_native_zones(pcb, board, manifest, plan, parameters):
    zone = pcb.ZONE(board)
    zone.SetUuid(pcb.KIID(ZONE_UUID))
    zone.SetZoneName(ZONE_NAME)
    zone.SetLayer(pcb.F_Cu)
    zone.SetNetCode(board.FindNet("GND").GetNetCode())
    zone.SetLocalClearance(pcb.FromMM(parameters["clearance_mm"]))
    zone.SetMinThickness(pcb.FromMM(MIN_THICKNESS_MM))
    zone.SetPadConnection(pcb.ZONE_CONNECTION_FULL)
    zone.SetThermalReliefGap(pcb.FromMM(.25))
    zone.SetThermalReliefSpokeWidth(pcb.FromMM(.25))
    zone.SetFillMode(pcb.ZONE_FILL_MODE_POLYGONS)
    zone.SetIslandRemovalMode(pcb.ISLAND_REMOVAL_MODE_ALWAYS)
    zone.SetMinIslandArea(0)
    zone.SetAssignedPriority(0)
    # The outline itself also enforces the stronger edge floor if the in-memory
    # settings are not retained by a native rule resolver.
    zone.Outline().Append(board_polygon(pcb, manifest, parameters["edge_clearance_mm"] + POLYGON_ERROR_MM))
    board.Add(zone)
    for record in plan["pour_only_F_keepouts"]:
        area = pcb.ZONE(board)
        area.SetUuid(pcb.KIID(record["uuid"]))
        area.SetZoneName(record["name"])
        area.SetLayer(pcb.F_Cu)
        area.SetNetCode(0)
        area.SetIsRuleArea(True)
        area.SetDoNotAllowZoneFills(True)
        area.SetDoNotAllowTracks(False)
        area.SetDoNotAllowVias(False)
        area.SetDoNotAllowPads(False)
        area.SetDoNotAllowFootprints(False)
        area.Outline().Append(bounds_polygon(pcb, record))
        board.Add(area)
    return zone


def validate_zone_nodes(package, text, board):
    """Pure byte-bound allowlist, also used before the checker's native exports."""
    zones = board.children("zone")
    if not zones:
        require(not (package / REPORT).exists(), "Ground-fill report present but all zones removed")
        return None
    report = read(package / REPORT)
    require(report["schema_version"] == 1 and report["zone_uuid"] == ZONE_UUID,
            "Unknown zone support version/identity")
    require(report["saved_pcb_sha256"] == sha(package / "handbell.kicad_pcb"), "Stale filled-board binding")
    require(report["tool_hashes"] == {name: sha(package / name) for name in ("fill_ground.py", "zone_graph.py")},
            "Ground-fill implementation changed; evidence needs explicit revalidation")
    for name in (BASELINE, BEFORE_DRC, AFTER_DRC):
        require(report["artifacts"][name] == sha(package / name), "Stale zone input/report: " + name)
    baseline_bytes = (package / BASELINE).read_bytes()
    baseline_text = baseline_bytes.decode("utf-8-sig")
    baseline = loads(baseline_text)
    require(not baseline.children("zone"), "Prefill snapshot already contains zones")
    insertion = report["insertion_byte_offset"]
    require(isinstance(insertion, int) and 0 <= insertion < len(baseline_bytes), "Invalid zone insertion offset")
    actual = (package / "handbell.kicad_pcb").read_bytes()
    prefix, suffix = baseline_bytes[:insertion], baseline_bytes[insertion:]
    require(actual.startswith(prefix) and actual.endswith(suffix)
            and len(actual) > len(baseline_bytes), "Existing native PCB bytes were rewritten during fill")
    addition = actual[insertion:len(actual)-len(suffix)]
    require(digest(addition) == report["appended_zone_block_sha256"], "Zone append block changed")
    # Reject insertion outside the root's final close, even if bytes were bound.
    root_close = len(baseline_text[:baseline.end-1].encode("utf-8"))
    bom = 3 if baseline_bytes.startswith(b"\xef\xbb\xbf") else 0
    require(insertion == root_close + bom, "Zones were not appended at the PCB root")
    expected = {ZONE_UUID} | {r["uuid"] for r in report["protection"]["pour_only_F_keepouts"]}
    require(len(zones) == len(expected)
            and {z.value("uuid") for z in zones} == expected, "Unknown/missing/duplicate candidate zones")
    hashes = {z.value("uuid"): digest(text[z.start:z.end].encode("utf-8")) for z in zones}
    require(hashes == report["zone_literal_sha256"], "Native zone literals differ from filled evidence")
    for zone in zones:
        layers = zone.child("layers")
        require(zone.value("layer") == "F.Cu" and layers is None,
                "Only explicitly owned single-front-layer zones are permitted")
        if zone.value("uuid") == ZONE_UUID:
            require(zone.value("net") == "GND" and zone.value("name") == ZONE_NAME
                    and zone.child("keepout") is None, "Unexpected native GND zone")
            filled = zone.children("filled_polygon")
            require(filled and all(p.value("layer") == "F.Cu" for p in filled),
                    "Unfilled outline or B filled polygon cannot count as copper")
        else:
            keepout = zone.child("keepout")
            require(keepout is not None and not zone.children("filled_polygon")
                    and keepout.value("copperpour") == "not_allowed"
                    and all(keepout.value(k) == "allowed" for k in ("tracks", "vias", "pads", "footprints")),
                    "Private rule areas must exclude pours only, not existing copper/components")
    return report


def validate_filled_graph(graph, report, manifest):
    pcb = graph.pcb
    require(graph.zone_islands, "No native filled islands present")
    parameters = report["parameters"]
    regions = report["protection"]["pour_only_F_keepouts"]
    by_id = {zone.m_Uuid.AsString(): zone for zone in graph.board.Zones()}
    zone = by_id[ZONE_UUID]
    require(list(zone.GetLayerSet().Seq()) == [pcb.F_Cu]
            and zone.GetPadConnection() == pcb.ZONE_CONNECTION_FULL
            and zone.GetMinThickness() == pcb.FromMM(MIN_THICKNESS_MM)
            and zone.GetIslandRemovalMode() == pcb.ISLAND_REMOVAL_MODE_ALWAYS
            and zone.GetFillMode() == pcb.ZONE_FILL_MODE_POLYGONS
            and zone.GetThermalReliefGap() == pcb.FromMM(.25)
            and zone.GetThermalReliefSpokeWidth() == pcb.FromMM(.25),
            "Actual saved native zone settings differ")
    require(zone.GetLocalClearance() == pcb.FromMM(parameters["clearance_mm"]),
            "Actual native zone clearance differs")
    require(parameters["clearance_mm"] >= CLEARANCE_MM
            and parameters["edge_clearance_mm"] >= EDGE_MM,
            "Ground fill cannot lower the explicit clearance/edge floor")
    for record in regions:
        area = by_id[record["uuid"]]
        require(area.GetIsRuleArea() and list(area.GetLayerSet().Seq()) == [pcb.F_Cu]
                and area.GetDoNotAllowZoneFills()
                and not any((area.GetDoNotAllowTracks(), area.GetDoNotAllowVias(),
                             area.GetDoNotAllowPads(), area.GetDoNotAllowFootprints())),
                "Actual keepout is not an F-only pour-only rule area")
        expected = bounds_polygon(pcb, record)
        remainder = area.Outline().CloneDropTriangulation()
        remainder.BooleanSubtract(expected)
        expected.BooleanSubtract(area.Outline())
        require(remainder.IsEmpty() and expected.IsEmpty(), "Native private keepout geometry differs")
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
                                                pcb.FromMM(PRIVATE_GAP_MM)-1),
                        "F plane approaches protected private pad/trace/via copper")
        for other in graph.items.values():
            if isinstance(other, IslandItem) or not other.IsOnLayer(pcb.F_Cu) or other.GetNetname() == "GND":
                continue
            require(not item.polygon.Collide(other.GetEffectiveShape(pcb.F_Cu),
                                            pcb.FromMM(parameters["clearance_mm"])-1),
                    "Actual zone violates foreign-net clearance, including CELL_NEG")
    for a, b in PAIRS:
        require(graph.pickoff(a, "2", b, "2")["independent_until_terminal"],
                "Filled plane bypasses actual private pickoff terminal: " + a)
    require(not graph.shorts and not graph.floating_copper(),
            "Actual filled graph has cross-net shorts or floating copper")


def drc(path, output, environment):
    import check
    result = subprocess.run(
        [str(check.cli_path()), "pcb", "drc", "--format", "json", "--severity-all",
         "--output", str(output), str(path)],
        cwd=HERE, env=environment, capture_output=True, text=True, timeout=300,
    )
    require(result.returncode == 0, "Native DRC failed: " + check.sanitize(result.stdout + result.stderr))
    return read(output)


def compare_drc(before, after):
    import check
    holes = lambda r: Counter(json.dumps(f, sort_keys=True) for f in r["violations"] if f["type"] == "hole_clearance")
    require(sum(holes(before).values()) == 4 and holes(before) == holes(after),
            "Four inherited USB errors must remain exact and visible")
    allowed_silk = {f["type"] for f in before["violations"]} & check.SILK_TYPES
    for report in (before, after):
        require(not any(f.get("excluded") or
                        (f["type"] != "hole_clearance" and
                         not (f["type"] in allowed_silk and f.get("severity") == "warning"))
                        for f in report["violations"]), "New/unpermitted physical DRC findings")
    require(len(after["unconnected_items"]) <= len(before["unconnected_items"]),
            "Native DRC connectivity regressed during filling")


def apply():
    import check
    import route
    route.guard()
    bindings = route.source_bindings()
    geometry, parsed, owners, pad_ids = check.validate_geometry()
    data = check.validate_route_data(parsed, pad_ids)
    require(not parsed.children("zone"), "Existing zones refused: no blind refill or generator rewrite")
    require(not any((HERE / name).exists() for name in ZONE_INPUTS),
            "Existing ground-fill artifacts require explicit inspection, not overwrite")
    require(not (HERE / "reports" / ".native-check-work").exists(),
            "Native checker appears active/interrupted; do not run concurrently")
    work = HERE / "routing" / "ground-fill-work"
    require(not work.exists(), "Inspect interrupted routing/ground-fill-work before retrying")
    work.mkdir(parents=True)
    snapshots = {name: (HERE / name).read_bytes() for name in
                 ("handbell.kicad_pcb", "placement-manifest.json", "completion-build.json")}
    original_inputs = check.input_bindings()
    written = {}
    completed = False
    try:
        config = HERE / "routing" / "native-config"
        check.write(config / "10.0" / "sym-lib-table",
                    '(sym_lib_table (version 7) (lib (name "power") (type "KiCad") '
                    '(uri "${KICAD10_SYMBOL_DIR}/power.kicad_sym") (options "") (descr "Explicit installed KiCad power symbols")))\n')
        environment = dict(os.environ, KICAD_CONFIG_HOME=str(config),
                           KICAD10_SYMBOL_DIR=str(check.cli_path().parent.parent / "share" / "kicad" / "symbols"))
        # Set before importing pcbnew; never alter shared user configuration.
        os.environ.update({k: environment[k] for k in ("KICAD_CONFIG_HOME", "KICAD10_SYMBOL_DIR")})
        pcb, api_identity = native()
        self_test(pcb)
        before = CopperGraph(pcb, HERE / "handbell.kicad_pcb")
        require(not before.zone_islands, "Prefill native graph unexpectedly has zones")
        manifest = read(HERE / "placement-manifest.json")
        plan = protection_plan(before, data, read(HERE / "battery-contact-interface.json"))
        parameters = settings_for_fill(pcb, before.board, read(HERE / "handbell.kicad_pro"))
        report = {"schema_version": 1, "zone_uuid": ZONE_UUID, "parameters": parameters,
                  "protection": plan, "native_api": api_identity,
                  "tool_hashes": {name: sha(HERE / name) for name in ("fill_ground.py", "zone_graph.py")}}
        for name in check.source_files():
            if name in {"handbell.kicad_pcb", "placement-manifest.json", "routing-data.json"}:
                continue
            destination = work / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(HERE / name, destination)
        baseline_drc = drc(HERE / "handbell.kicad_pcb", work / "before-drc.json", environment)
        add_native_zones(pcb, before.board, manifest, plan, parameters)
        before.board.BuildConnectivity()
        filler = pcb.ZONE_FILLER(before.board)
        require(filler.Fill(before.board.Zones()), "Native ZONE_FILLER failed/cancelled")
        serialized = work / "native-serialized.kicad_pcb"
        require(pcb.SaveBoard(str(serialized), before.board, True), "Native zone serialization failed")
        serialized_text = serialized.read_bytes().decode("utf-8-sig")
        serialized_root = loads(serialized_text)
        zone_nodes = serialized_root.children("zone")
        require(len(zone_nodes) == 1 + len(plan["pour_only_F_keepouts"]), "Native zone inventory changed")
        block = ("\n" + "\n".join(serialized_text[n.start:n.end] for n in zone_nodes) + "\n").encode("utf-8")
        original = snapshots["handbell.kicad_pcb"]
        original_text = original.decode("utf-8-sig")
        root = loads(original_text)
        offset = len(original_text[:root.end-1].encode("utf-8")) + (3 if original.startswith(b"\xef\xbb\xbf") else 0)
        final_bytes = original[:offset] + block + original[offset:]
        staged = work / "handbell.kicad_pcb"
        staged.write_bytes(final_bytes)
        after = CopperGraph(pcb, staged)
        validate_filled_graph(after, report, manifest)
        for uid in before.pads:
            for other in before.pads:
                if uid < other and before.connected(uid, other):
                    require(after.connected(uid, other), "Previously joined native physical pads disconnected")
        staged_drc = drc(staged, work / "staged-drc.json", environment)
        compare_drc(baseline_drc, staged_drc)
        require(int(after.board.GetConnectivity().GetUnconnectedCount(False)) == len(staged_drc["unconnected_items"]),
                "Staged native engine and actual-filled-board DRC disagree")
        require(sum(len(net["islands"])-1 for net in after.nets()) == len(staged_drc["unconnected_items"]),
                "Staged independent filled-island graph and native DRC disagree")
        require(check.input_bindings() == original_inputs, "Candidate/tool inputs changed while filling")
        route.guard()

        def replace(name, payload):
            target = HERE / name
            if name in snapshots:
                require(target.read_bytes() == snapshots[name], "Concurrent candidate edit: " + name)
            else:
                require(not target.exists(), "Concurrent artifact creation: " + name)
            target.parent.mkdir(parents=True, exist_ok=True)
            pending = work / "commit" / name
            pending.parent.mkdir(parents=True, exist_ok=True)
            pending.write_bytes(payload)
            os.replace(pending, target)
            written[name] = payload

        replace("handbell.kicad_pcb", final_bytes)
        # This invocation names the ACTUAL final PCB, not the serialized copy.
        final_drc = drc(HERE / "handbell.kicad_pcb", work / "final-drc.json", environment)
        compare_drc(baseline_drc, final_drc)
        findings = lambda result, name: Counter(json.dumps(f, sort_keys=True) for f in result[name])
        require(findings(final_drc, "violations") == findings(staged_drc, "violations")
                and len(final_drc["unconnected_items"]) == len(staged_drc["unconnected_items"]),
                "Actual saved-board physical findings or unconnected count differs from staged identical bytes")
        actual = CopperGraph(pcb, HERE / "handbell.kicad_pcb")
        validate_filled_graph(actual, report, manifest)
        partitions = lambda graph: {
            net["net"]: sorted(tuple(sorted(pad["uuid"] for pad in island)) for island in net["islands"])
            for net in graph.nets()}
        require(partitions(actual) == partitions(after),
                "Actual saved-board physical pad-island partitions differ from staging")
        require(int(actual.board.GetConnectivity().GetUnconnectedCount(False)) == len(final_drc["unconnected_items"]),
                "Actual saved-board connectivity engine and DRC disagree")
        require(sum(len(net["islands"])-1 for net in actual.nets()) == len(final_drc["unconnected_items"]),
                "Actual saved-board filled-island graph and native DRC disagree")
        replace(BASELINE, original)
        replace(BEFORE_DRC, (work / "before-drc.json").read_bytes())
        replace(AFTER_DRC, (work / "final-drc.json").read_bytes())
        final_text = final_bytes.decode("utf-8-sig")
        report.update(
            saved_pcb_sha256=digest(final_bytes), insertion_byte_offset=offset,
            appended_zone_block_sha256=digest(block),
            zone_literal_sha256={z.value("uuid"): digest(final_text[z.start:z.end].encode("utf-8"))
                                 for z in loads(final_text).children("zone")},
            artifacts={name: sha(HERE / name) for name in (BASELINE, BEFORE_DRC, AFTER_DRC)},
            filled_islands=actual.zone_islands,
            native_unconnected_before=len(baseline_drc["unconnected_items"]),
            native_unconnected_after=len(final_drc["unconnected_items"]),
            actual_saved_pcb_native_drc_checked=True, existing_native_bytes_preserved=True,
            identical_staged_and_actual_pad_island_partitions=True,
            airwire_pairing_scope="Native DRC may select different representative airwire endpoints for the same disconnected islands; physical findings, total count and every actual pad-island partition must agree",
            added_tracks=0, added_vias=0, added_B_copper=0,
            limits=["F fill is not a continuous B plane or a qualified high-current return.",
                    "Solid pads require assembly-process/thermal review; no current or solder qualification.",
                    "Run check.py --run-native for fresh ERC, exact 4 USB/46 parity and full native gates.",
                    "Mechanical rebind, manufacturability and all existing release blockers remain."],
        )
        replace(REPORT, encoded(report))
        manifest["generated_pcb_sha256"] = digest(final_bytes)
        replace("placement-manifest.json", encoded(manifest))
        require((HERE / "completion-build.json").read_bytes() == snapshots["completion-build.json"],
                "Concurrent completion-state edit")
        try:
            route.save_state(bindings)
        finally:
            written["completion-build.json"] = (HERE / "completion-build.json").read_bytes()
        state = read(HERE / "completion-build.json")
        state.setdefault("interchange_bindings", {}).update({name: sha(HERE / name) for name in ZONE_INPUTS})
        payload = encoded(state)
        pending = work / "completion-state.json"
        pending.write_bytes(payload)
        os.replace(pending, HERE / "completion-build.json")
        written["completion-build.json"] = payload
        check.validate_geometry()
        route.guard()
        require(route.source_bindings() == bindings, "Authoritative source changed during filling")
        completed = True
        return report
    finally:
        if not completed:
            # Never overwrite another process's newer edit during rollback.
            for name, payload in reversed(list(written.items())):
                target = HERE / name
                if target.exists() and target.read_bytes() == payload:
                    if name in snapshots:
                        target.write_bytes(snapshots[name])
                    else:
                        target.unlink()
        shutil.rmtree(work)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--apply", action="store_true")
    operation.add_argument("--self-test", action="store_true",
                           help="Only synthetic native polygon checks; no candidate load/save/fill")
    args = parser.parse_args()
    try:
        if args.self_test:
            pcb, _ = native()
            result = self_test(pcb)
        else:
            report = apply()
            result = {k: report[k] for k in ("zone_uuid", "native_unconnected_before", "native_unconnected_after",
                                            "added_tracks", "added_vias", "added_B_copper", "limits")}
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, RuntimeError, AttributeError, ImportError,
            subprocess.SubprocessError) as error:
        import check
        print(json.dumps({"status": "FAILED; no fill acceptance", "error": check.sanitize(str(error))}, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
