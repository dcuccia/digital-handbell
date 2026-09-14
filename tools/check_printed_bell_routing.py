# SPDX-License-Identifier: MIT
"""Byte-bound native validation and real KiCad connectivity for the separate routed draft."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

import route_printed_bell as route
from kicad_sexpr import load

ROOT, SOURCE, OUTPUT = route.ROOT, route.SOURCE, route.OUTPUT
REPORTS = ["erc.json", "drc.json", "handbell-netlist.xml", "handbell-schematic.pdf",
           "front-native.pdf", "rear-native.pdf", "front-native.svg", "rear-native.svg", "schematic-svg/handbell.svg"]
require = route.prep.require
SERVICE_SPEC = importlib.util.spec_from_file_location("printed_service_labels", OUTPUT / "screen_service_labels.py")
service_labels = importlib.util.module_from_spec(SERVICE_SPEC)
SERVICE_SPEC.loader.exec_module(service_labels)


def inputs():
    files = [OUTPUT / name for name in ("handbell.kicad_pcb", "handbell.kicad_sch", "handbell.kicad_pro",
             "placement-manifest.json", "battery-contact-interface.json", "fp-lib-table", "sym-lib-table",
             "Handbell.kicad_sym", "T8.kicad_sym", "mechanical-release.json", "released-mechanical-evidence.json",
             "routing-data.json", "routing-build.json", "source-evidence.json")]
    files += [OUTPUT / "screen_service_labels.py", OUTPUT / "reports" / "service-label-review.json"]
    files += sorted((OUTPUT / "libraries").rglob("*.kicad_mod"))
    files += [ROOT / "tools" / name for name in ("route_printed_bell.py", "check_printed_bell_routing.py", "kicad_sexpr.py")]
    files += [SOURCE / name for name in ("handbell.kicad_pcb", "handbell.kicad_sch", "handbell.kicad_pro",
              "placement-manifest.json", "battery-contact-interface.json", "reports/drc.json", "routing/prepare.py",
              "routing/routing-preparation.json")]
    result = {str(p.relative_to(ROOT)): route.sha(p) for p in files}
    result.update({f'git:{route.RELEASE_COMMIT}:{entry["path"]}': hashlib.sha256(entry["raw"]).hexdigest()
                   for entry in route.release_objects().values()})
    result[f"git:{service_labels.VISIBILITY_COMMIT}:{service_labels.VISIBILITY_GIT_PATH}"] = hashlib.sha256(
        service_labels.visibility_native()).hexdigest()
    return result


def run_native():
    subprocess.run([sys.executable, str(OUTPUT / "screen_service_labels.py")], cwd=ROOT, check=True, timeout=240)
    before = inputs()
    cli = route.CLI
    version = subprocess.check_output([str(cli), "--version"], text=True).strip()
    require(version == "10.0.6", "Expected exercised KiCad10.0.6")
    work = OUTPUT / "reports" / ".native-run"
    require(not work.exists(), "Inspect existing new-candidate native staging before rerunning")
    work.mkdir()
    sch, pcb = str(OUTPUT / "handbell.kicad_sch"), str(OUTPUT / "handbell.kicad_pcb")
    commands = [
        ["sch", "erc", "--format", "json", "--severity-all", "--output", str(work / "erc.json"), sch],
        ["sch", "export", "netlist", "--format", "kicadxml", "--output", str(work / "handbell-netlist.xml"), sch],
        ["pcb", "drc", "--format", "json", "--schematic-parity", "--severity-all", "--output", str(work / "drc.json"), pcb],
        ["sch", "export", "pdf", "--exclude-pdf-metadata", "--output", str(work / "handbell-schematic.pdf"), sch],
        ["sch", "export", "svg", "--output", str(work / "schematic-svg"), sch],
    ]
    for side, name in (("F", "front"), ("B", "rear")):
        mirror = ["--mirror"] if side == "B" else []
        layers = f"{side}.Cu,{side}.Fab,{side}.SilkS,Edge.Cuts"
        commands += [
            ["pcb", "export", "pdf", "--mode-single", "--layers", layers, "--scale", "3", "--exclude-value",
             *mirror, "--output", str(work / f"{name}-native.pdf"), pcb],
            ["pcb", "export", "svg", "--mode-single", "--layers", layers, "--fit-page-to-board",
             "--exclude-drawing-sheet", *mirror, "--output", str(work / f"{name}-native.svg"), pcb],
        ]
    try:
        logs = []
        for command in commands:
            result = subprocess.run([str(cli), *command], cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace", timeout=600)
            require(result.returncode == 0, "Native command failed: "+result.stdout+result.stderr)
            logs.append({"command": command, "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        require(inputs() == before, "Candidate inputs changed during native run")
        for name in REPORTS:
            target = OUTPUT / "reports" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(work / name, target)
        route.write(OUTPUT / "reports" / "native-input-bindings.json",
                    {"generated_utc": datetime.now(timezone.utc).isoformat(), "kicad_version": version,
                     "cli_sha256": route.sha(cli), "inputs": before,
                     "reports": {name: route.sha(OUTPUT / "reports" / name) for name in REPORTS}, "commands": logs})
    finally:
        shutil.rmtree(work)


def native_connectivity():
    bindir = route.CLI.parent
    handle = os.add_dll_directory(str(bindir))
    sys.path.append(str(bindir / "Lib" / "site-packages"))
    import pcbnew
    require(pcbnew.GetBuildVersion() == "10.0.6", "Native connectivity API version mismatch")
    board = pcbnew.LoadBoard(str(OUTPUT / "handbell.kicad_pcb"))
    connectivity = board.GetConnectivity()
    items = [p for f in board.GetFootprints() for p in f.Pads()] + list(board.GetTracks())
    pads = [p for f in board.GetFootprints() for p in f.Pads() if p.GetNetname()]
    comp = {}
    for item in items:
        key = item.m_Uuid.AsString()
        if key in comp or not item.GetNetname():
            continue
        linked = connectivity.GetConnectedItems(item)
        ids = {x.m_Uuid.AsString() for x in linked} | {key}
        require(all(x.GetNetname() == item.GetNetname() for x in linked), "Native connectivity crosses nets")
        component = min(ids)
        comp.update({key: component for key in ids})
    net_pads = defaultdict(list)
    for p in pads:
        net_pads[p.GetNetname()].append({"uuid": p.m_Uuid.AsString(),
                                       "reference": p.GetParentFootprint().GetReference(), "number": p.GetNumber()})
    nets = []
    for net, members in sorted(net_pads.items()):
        groups = defaultdict(list)
        for pad in members:
            groups[comp.get(pad["uuid"], pad["uuid"])].append(pad)
        if len(members) <= 1:
            status = "single-pad/NC—not counted as routed net"
        elif len(groups) == 1:
            status = "complete_all_physical_pads_connected"
        elif any(len(v) > 1 for v in groups.values()):
            status = "partial_connected_branches"
        else:
            status = "unrouted"
        nets.append({"net": net, "status": status, "physical_pad_count": len(members),
                     "connected_pad_islands": list(groups.values())})
    routed_pairs = []
    data = json.loads((OUTPUT / "routing-data.json").read_text())
    require(any(r["group"] == "Q5 widened main protected return" and r["status"].startswith("routed")
                for r in data["connections"]), "Run --finish-return; preliminary thin main protection return is not final")
    require(not any(t["net"] == "/PROT_FET_RETURN" and t["group"] == "protection-sense-and-gates"
                    for t in data["tracks"]), "Long preliminary fine-width protection-current path remains")
    for intent in data["connections"]:
        if not intent["status"].startswith("routed"):
            continue
        connected = comp.get(intent["from_uuid"]) == comp.get(intent["to_uuid"]) and intent["from_uuid"] in comp
        require(connected, "Reported route endpoints not actually connected: "+intent["from"]+" -> "+intent["to"])
        routed_pairs.append({"from": intent["from"], "to": intent["to"], "net": intent["net"], "connected": True})
    unattached = []
    pad_components = {comp.get(p["uuid"]) for members in net_pads.values() for p in members}
    for track in board.GetTracks():
        if comp.get(track.m_Uuid.AsString()) not in pad_components:
            unattached.append(track.m_Uuid.AsString())
    require(not unattached, "Floating copper component with no physical pad")
    return nets, routed_pairs, int(connectivity.GetUnconnectedCount(False))


def check():
    binding = json.loads((OUTPUT / "reports" / "native-input-bindings.json").read_text())
    require(inputs() == binding["inputs"], "Stale native routed inputs")
    require(binding["reports"] == {name: route.sha(OUTPUT / "reports" / name) for name in REPORTS}, "Changed routed reports")
    _, release_evidence = route.verify_release()
    require(json.loads((OUTPUT / "released-mechanical-evidence.json").read_text()) == release_evidence,
            "Candidate release provenance does not match the explicit immutable commit")
    require((OUTPUT / "mechanical-release.json").read_bytes() == route.released_git_bytes(route.RELEASE_GIT_PATH),
            "Candidate authorization differs from committed release")
    old_text, old = load(SOURCE / "handbell.kicad_pcb")
    text, board = load(OUTPUT / "handbell.kicad_pcb")
    fps = {f.properties()["Reference"]: f for f in board.children("footprint")}
    previous = {f.properties()["Reference"]: f for f in old.children("footprint")}
    require(set(fps) == set(previous) and len(fps) == 104, "Footprint inventory changed")
    pad_count = 0
    footprint_proof = {}
    for ref, fp in fps.items():
        before, after = old_text[previous[ref].start:previous[ref].end], text[fp.start:fp.end]
        require(before == after, "Footprint pose/local pad/net/library bytes changed: "+ref)
        footprint_proof[ref] = hashlib.sha256(after.encode()).hexdigest()
        pad_count += len(fp.children("pad"))
    require(pad_count == 325, "Physical pad inventory changed")
    for kind in ("gr_line", "layers", "setup", "general"):
        require([old_text[n.start:n.end] for n in old.children(kind)] == [text[n.start:n.end] for n in board.children(kind)],
                "Substrate/layers/rules changed: "+kind)
    require(not board.children("zone"), "Unreviewed zones added")
    for name in ("handbell.kicad_sch", "handbell.kicad_pro", "battery-contact-interface.json",
                 "Handbell.kicad_sym", "T8.kicad_sym", "fp-lib-table", "sym-lib-table"):
        require(route.sha(OUTPUT / name) == route.sha(SOURCE / name), "Changed retained circuit/interface/library: "+name)
    for path in (OUTPUT / "libraries").rglob("*.kicad_mod"):
        require(route.sha(path) == route.sha(SOURCE / path.relative_to(OUTPUT)), "Changed source footprint library")
    current = json.loads((OUTPUT / "placement-manifest.json").read_text())
    baseline = json.loads((SOURCE / "placement-manifest.json").read_text())
    geometry_keys = ("board", "components", "mounting_holes", "usb_interface", "cross_face_keepouts", "copper_only_features",
                     "dnp_footprint_reservations", "electrical_landmarks", "battery_reservation", "speaker_dimensions_mm", "speaker_screen")
    require(all(current[key] == baseline[key] for key in geometry_keys), "Manifest geometry differs from released placement")
    require(current["generated_pcb_sha256"] == route.sha(OUTPUT / "handbell.kicad_pcb"), "Manifest PCB hash mismatch")
    require(current["battery_contact_interface_sha256"] == route.sha(OUTPUT / "battery-contact-interface.json"), "Contact hash mismatch")
    erc = json.loads((OUTPUT / "reports" / "erc.json").read_text())
    require(sum(len(s["violations"]) for s in erc["sheets"]) == 0, "ERC violation")
    import xml.etree.ElementTree as ET
    def pins(path):
        root = ET.parse(path).getroot()
        return {(p.get("ref"), p.get("pin")): n.get("name") for n in root.findall("nets/net") for p in n.findall("node")}
    require(pins(OUTPUT / "reports" / "handbell-netlist.xml") == pins(SOURCE / "reports" / "handbell-netlist.xml"),
            "Schematic connectivity changed")
    drc = json.loads((OUTPUT / "reports" / "drc.json").read_text())
    types = Counter(v["type"] for v in drc["violations"])
    allowed = {"hole_clearance", "silk_overlap", "silk_over_copper", "silk_edge_clearance", "text_height", "text_thickness"}
    require(not set(types)-allowed, "New routed physical/dangling DRC findings: "+str(types))
    previous_drc = json.loads((SOURCE / "reports" / "drc.json").read_text())
    holes = lambda r: sorted(json.dumps(v, sort_keys=True) for v in r["violations"] if v["type"] == "hole_clearance")
    require(holes(drc) == holes(previous_drc) and types["hole_clearance"] == 4, "Original USB clearance findings changed")
    require(sorted(json.dumps(v, sort_keys=True) for v in drc["schematic_parity"]) ==
            sorted(json.dumps(v, sort_keys=True) for v in previous_drc["schematic_parity"]),
            "New schematic-parity finding identity")
    pads, obstacles = route.prep.read_pads(board)
    metal = route.prep.contact_metal_reservations(json.loads((OUTPUT / "battery-contact-interface.json").read_text()))
    data = json.loads((OUTPUT / "routing-data.json").read_text())
    require(len(data["tracks"]) == len(board.children("segment")) and len(data["vias"]) == len(board.children("via")),
            "Routing data/native inventory mismatch")
    for node, track in zip(board.children("segment"), data["tracks"]):
        for key, coordinate in (("start", track["a"]), ("end", track["b"])):
            require(math.dist(route.prep.point(node.child(key)), [v+100 for v in coordinate]) < .000002,
                    "Native track path differs from routing data")
        require(node.value("net") == track["net"] and node.value("layer") == track["layer"]
                and abs(float(node.value("width"))-track["width"]) < .000001, "Native track net/width differs")
    for node, via in zip(board.children("via"), data["vias"]):
        require(math.dist(route.prep.point(node.child("at")), [v+100 for v in via["xy"]]) < .000002
                and node.value("net") == via["net"] and abs(float(node.value("size"))-via["diameter"]) < .000001
                and abs(float(node.value("drill"))-via["drill"]) < .000001, "Native via data differs")
    for v in data["vias"]:
        if v["net"] == "GND":
            require(all(route.prep.geometry_distance(v["xy"], region)-v["diameter"]/2 >= .2-.000002 for region in metal),
                    "GND via touches raw contact base")
    for t in data["tracks"]:
        if t["net"] == "GND" and t["layer"] == "B.Cu":
            count = max(1, math.ceil(math.dist(t["a"], t["b"])/.005))
            for i in range(count+1):
                xy = [t["a"][axis]+(t["b"][axis]-t["a"][axis])*i/count for axis in (0, 1)]
                require(all(route.prep.geometry_distance(xy, region)-t["width"]/2 >= .2-.000002 for region in metal),
                        "B GND track enters raw contact base")
            if not t["group"].startswith(("IC1 local thermal", "U4 local thermal")) and t["width"] >= .4:
                require(min(abs(t["a"][1]), abs(t["b"][1])) >= 7 and t["a"][1]*t["b"][1] > 0,
                        "Wide power-return track uses central B corridor")
    marks = [g for g in board.children("gr_text") if g.value("layer") == "B.SilkS"]
    require({g.atoms()[1] for g in marks} == {s[0] for s in route.SERVICE_LABELS},
            "Missing useful polarity/orientation/chemistry silk")
    require(all("mirror" in g.child("effects").child("justify").atoms() for g in marks), "B silk not mirrored")
    for i, label in enumerate(route.SERVICE_LABELS):
        mark = next(g for g in marks if g.atoms()[1] == label[0])
        require(text[mark.start:mark.end] == route.service_silk(i, label), "Service label geometry changed")
    label_ids = {g.value("uuid") for g in marks}
    require(not any(item["uuid"] in label_ids for v in drc["violations"] for item in v["items"]),
            "New service label has a native DRC finding")
    service = json.loads((OUTPUT / "reports" / "service-label-review.json").read_text())
    require(service["pcb_sha256"] == route.sha(OUTPUT / "handbell.kicad_pcb")
            and service["tool_sha256"] == route.sha(OUTPUT / "screen_service_labels.py"),
            "Stale actual service-glyph screen")
    require(service["mechanical_visibility_commit"] == service_labels.VISIBILITY_COMMIT
            and service["mechanical_native_sha256"] == service_labels.VISIBILITY_NATIVE_SHA256,
            "Service visibility evidence uses a different corrected model")
    require(all(item["clear"] for item in service["mechanical"]["labels"]), "Capture obscures service label")
    nets, pairs, native_unconnected = native_connectivity()
    require(native_unconnected == len(drc["unconnected_items"]), "Native connectivity/DRC unconnected counts differ")
    lengths = defaultdict(float)
    for t in data["tracks"]:
        lengths[f'{t["layer"]} / {t["width"]}mm'] += math.dist(t["a"], t["b"])
    necks = [{"group": t["group"], "net": t["net"], "length_mm": round(math.dist(t["a"], t["b"]), 6)}
             for t in data["tracks"] if "neck" in t["group"]]
    maximum_neck = max(max(r.get("fine_neck_lengths_mm", [0])) for r in data["connections"])
    report = {
        "status": "Partial routed engineering candidate, NOT a functional, thermal, charging or fabrication approval",
        "hashes": {name: route.sha(OUTPUT / name) for name in ("handbell.kicad_pcb", "handbell.kicad_sch",
                    "placement-manifest.json", "battery-contact-interface.json")},
        "native_binding_sha256": route.sha(OUTPUT / "reports" / "native-input-bindings.json"),
        "tracks": len(data["tracks"]), "vias": len(data["vias"]), "zones": 0,
        "tracks_by_layer": dict(Counter(t["layer"] for t in data["tracks"])),
        "routed_net_names": sorted({t["net"] for t in data["tracks"]}),
        "complete_nets": [n["net"] for n in nets if n["status"].startswith("complete")],
        "partially_connected_nets": [n["net"] for n in nets if n["status"].startswith("partial")],
        "unconnected_items": native_unconnected, "baseline_unconnected_items": 222,
        "erc": 0, "physical_drc": dict(types), "cli_parity_warnings": len(drc["schematic_parity"]),
        "native_connected_endpoint_pairs": pairs, "native_net_connectivity": nets,
        "track_lengths_mm_by_layer_width": {k: round(v, 6) for k, v in lengths.items()},
        "bounded_power_neck_segments": necks,
        "power_connection_necks": [r for r in data["connections"] if r.get("fine_neck_lengths_mm")],
        "conditional_neck_DC_screen": {
            "maximum_recorded_endpoint_neck_mm": maximum_neck, "width_mm": .1778,
            "assumed_copper_thickness_um": 35, "assumed_resistivity_ohm_mm2_per_m": .0172,
            "estimated_maximum_neck_resistance_ohm": .0172*maximum_neck/(1000*.1778*.035),
            "scope": "Nominal isolated trace DC estimate only; excludes vias, junctions, copper tolerance, temperature and current sharing. "
                     "No current, thermal or fault/SOA qualification."},
        "remaining_routing_intents": [r for r in data["connections"] if not r["status"].startswith("routed")],
        "geometry_proof": {"changed_footprints": [], "physical_pad_records_preserved": 325,
                           "footprint_literal_sha256": footprint_proof, "manifest_geometry_keys_equal": list(geometry_keys),
                           "unchanged_stage1_manifest_sha256": route.sha(SOURCE / "placement-manifest.json")},
        "manufacturing_gates": ["Via-in-pad thermal fill/cap and stencil process unqualified",
                                "35um copper and calculated DC drops are assumptions, not selected stackup or current ratings",
                                "No live-cell/charge/reversal/thermal/fault/USB impedance qualification",
                                "Parent must rebind mechanical artifacts to final candidate bytes and inspect label visibility"],
        "service_label_review_sha256": route.sha(OUTPUT / "reports" / "service-label-review.json"),
        "chemistry_guidance": "1S Li-ion 4.2V ONLY / NO PRIMARY CR123A; charger cannot identify primary chemistry",
    }
    route.write(OUTPUT / "reports" / "routing-review.json", report)
    summary = {key: report[key] for key in ("hashes", "tracks", "vias", "zones", "complete_nets",
               "partially_connected_nets", "unconnected_items", "erc", "physical_drc", "cli_parity_warnings")}
    summary["native_connected_endpoint_pairs"] = len(pairs)
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-native", action="store_true")
    args = parser.parse_args()
    if args.run_native:
        run_native()
    check()


if __name__ == "__main__":
    main()
