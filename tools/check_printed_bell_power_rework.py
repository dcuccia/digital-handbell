# SPDX-License-Identifier: MIT
"""Validate only printed-bell-power-rework, against the frozen first copper checkpoint.

Run with --run-native to refresh byte-bound KiCad reports/exports, then validate.
Without that flag, stale/missing reports fail closed. This tool never generates
copper, modifies the frozen package, or transfers its mechanical approval.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
import copy
from datetime import datetime, timezone
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

from kicad_sexpr import loads

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "hardware" / "handbell" / "iterations" / "printed-bell-routing"
OUTPUT = SOURCE.parent / "printed-bell-power-rework"
MOVABLE = frozenset(("U5", "L1", "C26", "C27", "C28", "R23", "R24", "C29",
                     "R26", "U6", "R25", "C30", "Q5", "R27", "R28", "R29"))
BOOST = frozenset(("U5", "L1", "C26", "C27", "C28", "R23", "R24", "C29"))
AUTHORIZED_PROXY_DEPTHS = {"U1": (2.0, 2.1), "U6": (1.5, 1.55)}
PINNED_SOURCE = {
    "handbell.kicad_pcb": "075c7b7cb0a98e302af29f5985bbf020111df5b1be385e5ebfa61be236b04250",
    "placement-manifest.json": "cc935ef468e8fb8d0fda5d55010e8883eab1f8b578078f2dcc4f77fe456fe69f",
}
RETAINED = ("handbell.kicad_sch", "handbell.kicad_pro", "battery-contact-interface.json",
            "Handbell.kicad_sym", "T8.kicad_sym", "fp-lib-table", "sym-lib-table",
            "source-evidence.json", "design-input-snapshot.json", "LICENSE.txt")
FIXED_GEOMETRY = ("board", "coordinate_convention", "mounting_holes", "usb_interface",
                  "cross_face_keepouts", "copper_only_features", "dnp_footprint_reservations",
                  "battery_reservation", "speaker_dimensions_mm", "speaker_screen",
                  "speaker_front_z_mm", "speaker_basket_rear_z_mm", "speaker_magnet_rear_z_mm")
REPORT_FILES = (
    "erc.json", "drc.json", "handbell-netlist.xml", "handbell-schematic.pdf",
    "schematic-svg/handbell.svg", "front-native.pdf", "rear-native.pdf",
    "front-native.svg", "rear-native.svg",
    "boost-before-front-sheet.svg", "boost-after-front-sheet.svg",
    "boost-before-back-sheet.svg", "boost-after-back-sheet.svg",
    "boost-before-front-detail.svg", "boost-after-front-detail.svg",
    "boost-before-back-detail.svg", "boost-after-back-detail.svg",
)
SILK_TYPES = frozenset(("silk_overlap", "silk_over_copper", "silk_edge_clearance",
                        "text_height", "text_thickness"))
TOL = .000002
_DLL_HANDLES = []


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def generator():
    # Importing a helper must not create __pycache__ inside frozen packages.
    sys.dont_write_bytecode = True
    route = importlib.import_module("route_printed_bell_power_rework")
    require(route.ROOT.resolve() == ROOT and route.SOURCE.resolve() == SOURCE
            and route.OUTPUT.resolve() == OUTPUT, "New generator targets an unexpected package")
    return route


def literal_board(path):
    text = Path(path).read_bytes().decode("utf-8-sig")
    return text, loads(text)


def literal(text, node):
    return text[node.start:node.end]


def pose(fp):
    values = list(map(float, fp.child("at").atoms()[1:]))
    return values[:2] + [values[2] if len(values) > 2 else 0.]


def same_pose(a, b):
    return math.dist(a[:2], b[:2]) < TOL and abs((a[2] - b[2] + 180) % 360 - 180) < TOL


def transform(point, old, new):
    angle = math.radians(old[2] - new[2])
    x, y = point[0] - old[0], point[1] - old[1]
    return [new[0] + x * math.cos(angle) - y * math.sin(angle),
            new[1] + x * math.sin(angle) + y * math.cos(angle)]


def input_bindings(route):
    paths = {OUTPUT / name for name in (*RETAINED, "handbell.kicad_pcb",
             "placement-manifest.json", "routing-data.json", "routing-build.json")}
    paths.add(OUTPUT / "reports" / "footprint-movements.json")
    paths.add(OUTPUT / "reports" / "proxy-envelope-adjustments.json")
    paths.update(p for p in (OUTPUT / "libraries").rglob("*") if p.is_file())
    paths.update(ROOT / relative for relative in route.bindings())
    paths.update((Path(__file__), Path(route.__file__), ROOT / "tools" / "kicad_sexpr.py",
                  ROOT / "tools" / "route_printed_bell.py", Path(route.prep.__file__)))
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}


def validate_geometry():
    for name, digest in PINNED_SOURCE.items():
        require(sha(SOURCE / name) == digest, "Frozen reviewed baseline changed: " + name)
    old_text, old = literal_board(SOURCE / "handbell.kicad_pcb")
    text, board = literal_board(OUTPUT / "handbell.kicad_pcb")
    previous = {f.properties()["Reference"]: f for f in old.children("footprint")}
    current = {f.properties()["Reference"]: f for f in board.children("footprint")}
    require(len(previous) == len(old.children("footprint"))
            and len(current) == len(board.children("footprint")), "Duplicate footprint reference")
    require(current.keys() == previous.keys(), "Physical footprint inventory changed")
    moves = read_json(OUTPUT / "reports" / "footprint-movements.json")
    require(isinstance(moves, list), "footprint-movements.json must be a list")
    declared = {m["reference"]: m for m in moves}
    require(len(declared) == len(moves), "Duplicate movement record")
    changed, proofs, pad_owners, pad_ids = {}, {}, {}, {}
    for ref, fp in current.items():
        before, after = previous[ref], fp
        old_literal, new_literal = literal(old_text, before), literal(text, after)
        a, b = pose(before), pose(after)
        if old_literal != new_literal:
            require(ref in MOVABLE, "Unrelated footprint changed: " + ref)
            old_at, new_at = before.child("at"), after.child("at")
            old_rest = old_literal[:old_at.start-before.start] + "<ROOT-POSE>" + old_literal[old_at.end-before.start:]
            new_rest = new_literal[:new_at.start-after.start] + "<ROOT-POSE>" + new_literal[new_at.end-after.start:]
            require(old_rest == new_rest, "Change beyond root footprint pose: " + ref)
            require(not same_pose(a, b), "Footprint reformatted without a real move: " + ref)
            changed[ref] = {"old_native_pose": a, "new_native_pose": b}
        old_pads = [literal(old_text, p) for p in before.children("pad")]
        new_pads = [literal(text, p) for p in after.children("pad")]
        require(old_pads == new_pads, "Full local pad primitive/net/angle/UUID changed: " + ref)
        for index, pad in enumerate(after.children("pad")):
            uid = pad.value("uuid")
            require(uid and uid not in pad_owners, "Missing or duplicated physical pad UUID")
            pad_owners[uid] = ref
            pad_ids[uid] = f'{ref}.{pad.atoms()[1]}#{index}'
        proofs[ref] = {
            "footprint_literal_sha256": hashlib.sha256(new_literal.encode()).hexdigest(),
            "full_local_pad_literal_sha256": hashlib.sha256("\n".join(new_pads).encode()).hexdigest(),
            "pad_count": len(new_pads), "root_pose_changed": ref in changed,
        }
    require(len(pad_owners) == 325, "Expected 325 preserved physical pad identities")
    require(changed.keys() == declared.keys(), "Movement report differs from actual changed footprints")
    for ref, movement in changed.items():
        a, b = movement["old_native_pose"], movement["new_native_pose"]
        require(same_pose(declared[ref]["old_native_pose"], [a[0]-100, a[1]-100, a[2]])
                and same_pose(declared[ref]["new_native_pose"], [b[0]-100, b[1]-100, b[2]]),
                "Movement report must use common board-relative XY and native angle: " + ref)
        require(bool(str(declared[ref].get("rationale", "")).strip()), "Missing movement rationale: " + ref)
    for kind in {n.head for n in old.children()} | {n.head for n in board.children()}:
        if kind in {"footprint", "segment", "via", "title_block"}:
            continue
        require([literal(old_text, n) for n in old.children(kind)] ==
                [literal(text, n) for n in board.children(kind)], "Fixed native board object changed: " + kind)
    require(not any(board.children(k) for k in ("zone", "arc", "group")),
            "Unsupported zones, track arcs or board groups require independent review")
    for name in RETAINED:
        require((OUTPUT / name).read_bytes() == (SOURCE / name).read_bytes(),
                "Retained circuit, provenance or library file changed: " + name)
    old_libraries = {str(p.relative_to(SOURCE)): sha(p) for p in (SOURCE / "libraries").rglob("*") if p.is_file()}
    new_libraries = {str(p.relative_to(OUTPUT)): sha(p) for p in (OUTPUT / "libraries").rglob("*") if p.is_file()}
    require(old_libraries == new_libraries, "Source library file inventory or literal bytes changed")
    manifest, baseline = read_json(OUTPUT / "placement-manifest.json"), read_json(SOURCE / "placement-manifest.json")
    require(manifest["schema_version"] == baseline["schema_version"] == 2, "Expected manifest schema 2")
    for key in FIXED_GEOMETRY:
        require(manifest[key] == baseline[key], "Fixed manifest geometry changed: " + key)
    require(manifest["board"]["diameter_mm"] == 43 and manifest["board"]["front_z_mm"] == 25
            and manifest["board"]["back_z_mm"] == 26.6, "D43/F25/B26.6 interface changed")
    components = {c["reference"]: c for c in manifest["components"]}
    old_components = {c["reference"]: c for c in baseline["components"]}
    require(len(components) == len(manifest["components"]) == 83 and components.keys() == old_components.keys(),
            "Fitted component inventory changed")
    require(Counter(c["side"] for c in components.values()) == {"F": 81, "B": 2}
            and {r for r, c in components.items() if c["side"] == "B"} == {"BT1", "BT2"},
            "81F + two rear contacts changed")
    variable = {"x_mm", "y_mm", "rotation_deg", "native_origin_common_xy_mm"}
    envelope_evidence = manifest["proxy_envelope_adjustments"]
    require(envelope_evidence == read_json(OUTPUT / "reports" / "proxy-envelope-adjustments.json"),
            "Proxy envelope evidence differs from exact manifest")
    envelopes = {item["reference"]: item for item in envelope_evidence["changes"]}
    require(len(envelopes) == len(envelope_evidence["changes"]) == len(AUTHORIZED_PROXY_DEPTHS)
            and envelopes.keys() == AUTHORIZED_PROXY_DEPTHS.keys(), "Unexpected proxy enlargement inventory")
    for ref, component in components.items():
        previous_component = copy.deepcopy(old_components[ref])
        if ref in AUTHORIZED_PROXY_DEPTHS:
            old_depth, new_depth = AUTHORIZED_PROXY_DEPTHS[ref]
            record = envelopes[ref]
            require(previous_component["depth_mm"] == old_depth and component["depth_mm"] == new_depth
                    and record["old_depth_mm"] == old_depth and record["new_depth_mm"] == new_depth,
                    "Authorized maximum-depth correction differs: " + ref)
            angle = math.radians(component["rotation_deg"])
            require(record["rotation_deg"] == component["rotation_deg"]
                    and math.dist(record["local_depth_axis_board_xy_unit"], [-math.sin(angle), math.cos(angle)]) < TOL
                    and record["unchanged_width_height_mm"] == [component["width_mm"], component["height_mm"]]
                    and record["native_geometry_changed_by_envelope_adjustment"] is False,
                    "Proxy correction applied along wrong local/board axis or changes native geometry: " + ref)
            previous_component["depth_mm"] = new_depth
        if ref not in changed:
            require(component == previous_component, "Unmoved component proxy changed: " + ref)
            continue
        require({k: v for k, v in component.items() if k not in variable} ==
                {k: v for k, v in previous_component.items() if k not in variable},
                "Moved component dimensions/height/face/proxy semantics changed: " + ref)
        a, b = changed[ref]["old_native_pose"], changed[ref]["new_native_pose"]
        expected = transform([previous_component["x_mm"] + 100, previous_component["y_mm"] + 100], a, b)
        require(math.dist(expected, [component["x_mm"] + 100, component["y_mm"] + 100]) < TOL,
                "Manifest component center does not follow root pose: " + ref)
        require(math.dist(component["native_origin_common_xy_mm"], [b[0]-100, b[1]-100]) < TOL
                and abs((component["rotation_deg"] + b[2] + 180) % 360 - 180) < TOL,
                "Manifest native origin/rotation differs from native footprint: " + ref)
    expected_landmarks = copy.deepcopy(baseline["electrical_landmarks"])
    for cluster in expected_landmarks.values():
        for ref in cluster:
            if ref in changed:
                a = changed[ref]["new_native_pose"]
                cluster[ref] = [a[0]-100, a[1]-100, a[2]]
    require(manifest["electrical_landmarks"].keys() == expected_landmarks.keys(), "Landmark cluster inventory changed")
    for group, refs in expected_landmarks.items():
        require(manifest["electrical_landmarks"][group].keys() == refs.keys(), "Landmark reference inventory changed")
        for ref, expected in refs.items():
            require(same_pose(manifest["electrical_landmarks"][group][ref], expected), "Stale electrical landmark: " + ref)
    require(manifest["generated_pcb_sha256"] == sha(OUTPUT / "handbell.kicad_pcb"), "Manifest PCB binding is stale")
    require(manifest["schematic_sha256"] == sha(OUTPUT / "handbell.kicad_sch"), "Manifest schematic binding is stale")
    require(manifest["battery_contact_interface_sha256"] == sha(OUTPUT / "battery-contact-interface.json"),
            "Manifest contact binding is stale")
    require(manifest.get("mechanical_rebind_required") is True, "New poses must explicitly require mechanical rebind")
    return {"changed_footprints": changed, "proxy_envelope_adjustments": envelope_evidence,
            "physical_pad_records_preserved": len(pad_owners),
            "footprint_proof": proofs, "fixed_manifest_keys": list(FIXED_GEOMETRY),
            "pose_coordinates": "This geometry proof uses absolute PCB XY; movement input uses common XY (absolute minus 100)",
            "source_pcb_sha256": sha(SOURCE / "handbell.kicad_pcb"),
            "source_manifest_sha256": sha(SOURCE / "placement-manifest.json")}, board, pad_owners, pad_ids


def validate_route_data(board, pad_ids):
    data = read_json(OUTPUT / "routing-data.json")
    tracks, vias = board.children("segment"), board.children("via")
    require(len(tracks) == len(data["tracks"]) and len(vias) == len(data["vias"]), "Native/route-data inventory differs")
    copper_ids = set()
    for node, item in zip(tracks, data["tracks"]):
        for key, xy in (("start", item["a"]), ("end", item["b"])):
            require(len(xy) == 2 and all(math.isfinite(x) for x in xy)
                    and math.dist(list(map(float, node.child(key).atoms()[1:3])), [v+100 for v in xy]) < TOL,
                    "Native track coordinates differ from route-data")
        require(node.value("net") == item["net"] and node.value("layer") == item["layer"]
                and abs(float(node.value("width")) - item["width"]) < TOL,
                "Native track net/layer/width differs from route-data")
        require(item["layer"] in {"F.Cu", "B.Cu"} and item["net"] and item["width"] > 0,
                "Invalid track layer/net/width")
        require(math.dist(item["a"], item["b"]) > .000001, "Zero-length copper segment")
        require(node.value("uuid") and node.value("uuid") not in copper_ids | pad_ids.keys(), "Duplicate copper UUID")
        copper_ids.add(node.value("uuid"))
    for node, item in zip(vias, data["vias"]):
        require(math.dist(list(map(float, node.child("at").atoms()[1:3])), [v+100 for v in item["xy"]]) < TOL
                and node.value("net") == item["net"]
                and abs(float(node.value("size")) - item["diameter"]) < TOL
                and abs(float(node.value("drill")) - item["drill"]) < TOL,
                "Native via net/position/geometry differs from route-data")
        require(node.child("layers").atoms()[1:] == ["F.Cu", "B.Cu"] and item["diameter"] > item["drill"] > 0,
                "Unsupported via layer pair or geometry")
        require(node.value("uuid") and node.value("uuid") not in copper_ids | pad_ids.keys(), "Duplicate copper UUID")
        copper_ids.add(node.value("uuid"))
    for intent in data["connections"]:
        for end in ("from", "to"):
            require(intent[end+"_uuid"] in pad_ids and pad_ids[intent[end+"_uuid"]] == intent[end],
                    "Routing endpoint name/physical UUID mismatch: " + intent[end])
    build = read_json(OUTPUT / "routing-build.json")
    require(build["pcb_sha256"] == sha(OUTPUT / "handbell.kicad_pcb"), "Routing-build PCB binding is stale")
    require(build["tracks"] == len(tracks) and build["vias"] == len(vias), "Routing-build inventory is stale")
    require(build["script_sha256"] == sha(ROOT / "tools" / "route_printed_bell_power_rework.py"),
            "Routing-build generator binding is stale")
    require(build.get("source_bindings") and build.get("protected_files"), "Missing build input/protected-file bindings")
    for key, expected in build["source_bindings"].items():
        path = ROOT / key
        helpers = {ROOT / "tools" / "route_printed_bell.py", ROOT / "tools" / "kicad_sexpr.py",
                   SOURCE.parent / "printed-bell-front" / "routing" / "prepare.py"}
        require(path.resolve().is_relative_to(SOURCE) or path.resolve() in helpers,
                "Build source binding outside frozen package/helpers: " + key)
        require(sha(path) == expected, "Build source input changed: " + key)
    for name, expected in build["protected_files"].items():
        path = OUTPUT / name
        require(path.resolve().is_relative_to(OUTPUT), "Build protected file escapes new package")
        require(sha(path) == expected, "Build protected file changed: " + name)
    return data


def native_api(route):
    bindir = route.CLI.parent
    _DLL_HANDLES.append(os.add_dll_directory(str(bindir)))
    package = str(bindir / "Lib" / "site-packages")
    if package not in sys.path:
        sys.path.append(package)
    pcb = importlib.import_module("pcbnew")
    require(pcb.GetBuildVersion() == "10.0.6", "Expected native KiCad API 10.0.6")
    return pcb


def native_polygon(pcb, item, layer, outside=True):
    """Expose actual KiCad pad/track polygons, not parser bounding-box proxies.

    A 1 nm polygonization bound is used only for contact-location proofs.
    Connectivity of ordinary connected primitives uses GetEffectiveShape.
    """
    polygon = pcb.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(polygon, layer, 0, 1, pcb.ERROR_OUTSIDE if outside else pcb.ERROR_INSIDE)
    return polygon


def rectangle(pcb, bounds):
    xmin, ymin, xmax, ymax = bounds
    polygon = pcb.SHAPE_POLY_SET()
    index = polygon.NewOutline()
    for x, y in ((xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)):
        polygon.Append(pcb.FromMM(x), pcb.FromMM(y), index)
    return polygon


def bbox(shape):
    box = shape.BBox()
    return box.GetLeft(), box.GetTop(), box.GetRight(), box.GetBottom()


def boxes_touch(a, b, clearance=0):
    return not (a[2]+clearance < b[0] or b[2]+clearance < a[0]
                or a[3]+clearance < b[1] or b[3]+clearance < a[1])


class CopperGraph:
    """A graph of touching native copper shapes per layer, never route groups.

    Different physical pads sharing a logical pin number remain separate.
    Only plated pad/via barrels join layers. Disjoint effective pad outlines
    are rejected rather than silently shorted by a common native item UUID.
    """

    def __init__(self, pcb, path):
        self.pcb = pcb
        self.board = pcb.LoadBoard(str(path))
        self.copper_layers = sorted(
            (layer for layer in self.board.GetEnabledLayers().Seq()
             if pcb.IsCopperLayer(layer)),
            key=pcb.CopperLayerToOrdinal)
        self.pads = {p.m_Uuid.AsString(): p for f in self.board.GetFootprints() for p in f.Pads()}
        self.items = dict(self.pads)
        self.items.update({t.m_Uuid.AsString(): t for t in self.board.GetTracks()})
        self.vertices, self.adj, self.by_uuid = {}, defaultdict(set), defaultdict(list)
        self.lookup = defaultdict(list)
        self.shorts = []
        for uid, item in self.items.items():
            if uid in self.pads:
                self.lookup[(item.GetParentFootprint().GetReference(), item.GetNumber())].append(uid)
            if not item.GetNetname():
                continue
            for layer in self.copper_layers:
                if not item.IsOnLayer(layer):
                    continue
                shape = item.GetEffectiveShape(layer)
                if shape.IsNull():
                    continue
                poly = native_polygon(pcb, item, layer)
                require(poly.OutlineCount() == 1, "Disjoint native item copper needs explicit island splitting: " + uid)
                key = (uid, layer)
                self.vertices[key] = {"item": item, "shape": shape, "bbox": bbox(shape), "net": item.GetNetname()}
                self.by_uuid[uid].append(key)
                self.adj[key]
            vertices = self.by_uuid[uid]
            if len(vertices) > 1:
                plated = isinstance(item, pcb.PCB_VIA) or (uid in self.pads and item.GetAttribute() == pcb.PAD_ATTRIB_PTH)
                require(plated, "Unplated item cannot electrically join copper layers: " + uid)
                for vertex in vertices[1:]:
                    self.join(vertices[0], vertex)
        for layer in self.copper_layers:
            nodes = sorted((k for k in self.vertices if k[1] == layer), key=lambda k: self.vertices[k]["bbox"][0])
            for index, a in enumerate(nodes):
                aa = self.vertices[a]
                for b in nodes[index+1:]:
                    bb = self.vertices[b]
                    if bb["bbox"][0] > aa["bbox"][2]:
                        break
                    if not boxes_touch(aa["bbox"], bb["bbox"]) or not aa["shape"].Collide(bb["shape"], 0):
                        continue
                    if aa["net"] != bb["net"]:
                        self.shorts.append({"a_uuid": a[0], "b_uuid": b[0], "layer": self.layer_name(layer),
                                            "nets": [aa["net"], bb["net"]]})
                    else:
                        self.join(a, b)
        self.components = {}
        for node in self.vertices:
            if node not in self.components:
                reached = self.reachable([node])
                identity = min(reached)
                self.components.update({key: identity for key in reached})

    def join(self, a, b):
        self.adj[a].add(b)
        self.adj[b].add(a)

    def layer_name(self, layer):
        return self.board.GetLayerName(layer)

    def pad_uuid(self, ref, number):
        values = self.lookup[(ref, number)]
        require(len(values) == 1, f"Specify a physical UUID for ambiguous/missing {ref}.{number}")
        return values[0]

    def reachable(self, starts, allowed=None, edge=None):
        found = {n for n in starts if allowed is None or n in allowed}
        queue = deque(found)
        while queue:
            a = queue.popleft()
            for b in self.adj[a]:
                if b in found or (allowed is not None and b not in allowed) or (edge and not edge(a, b)):
                    continue
                found.add(b)
                queue.append(b)
        return found

    def connected(self, a, b):
        return bool({self.components[v] for v in self.by_uuid[a]} &
                    {self.components[v] for v in self.by_uuid[b]})

    def path(self, a, b, layer=None):
        starts = [n for n in self.by_uuid[a] if layer is None or n[1] == layer]
        targets = {n for n in self.by_uuid[b] if layer is None or n[1] == layer}
        queue, previous = deque(starts), dict.fromkeys(starts)
        end = None
        while queue:
            here = queue.popleft()
            if here in targets:
                end = here
                break
            for other in sorted(self.adj[here]):
                if other not in previous and (layer is None or other[1] == layer):
                    previous[other] = here
                    queue.append(other)
        nodes = []
        while end is not None:
            nodes.append(end)
            end = previous[end]
        nodes.reverse()
        return [{"uuid": uid, "layer": self.layer_name(layer_id)} for uid, layer_id in nodes]

    def describe_pad(self, uid):
        pad = self.pads[uid]
        return {"uuid": uid, "reference": pad.GetParentFootprint().GetReference(), "number": pad.GetNumber()}

    def nets(self):
        members = defaultdict(list)
        for uid, pad in self.pads.items():
            if pad.GetNetname():
                members[pad.GetNetname()].append(uid)
        result = []
        for net, ids in sorted(members.items()):
            islands = defaultdict(list)
            for uid in ids:
                components = {self.components[v] for v in self.by_uuid[uid]}
                require(len(components) == 1, "Physical pad has absent/disjoint copper: " + uid)
                islands[next(iter(components))].append(self.describe_pad(uid))
            groups = [sorted(v, key=lambda p: p["uuid"]) for _, v in sorted(islands.items())]
            status = ("single_pad_or_NC" if len(ids) < 2 else "complete" if len(groups) == 1 else
                      "partial" if any(len(v) > 1 for v in groups) else "unrouted")
            result.append({"net": net, "status": status, "physical_pad_count": len(ids), "islands": groups})
        return result

    def floating_copper(self):
        with_pad = {self.components[v] for uid in self.pads for v in self.by_uuid[uid]}
        return sorted(uid for uid in self.items if uid not in self.pads and
                      (not self.by_uuid[uid] or any(self.components[v] not in with_pad for v in self.by_uuid[uid])))

    def pickoff(self, start_ref, start_pin, target_ref, target_pin):
        """Remove only joins wholly inside the intended native terminal land.

        This also cuts track-to-track joins inside the land: deleting only the
        pad node would wrongly retain such legitimate terminal connections.
        Outside-overlap tests conservatively polygonize copper outward and the
        terminal inward at 1 nm; uncertain boundary contacts fail closed.
        """
        start, target = self.pad_uuid(start_ref, start_pin), self.pad_uuid(target_ref, target_pin)
        pcb, target_pad = self.pcb, self.pads[target]
        terminal = {layer: native_polygon(pcb, target_pad, layer, outside=False)
                    for _, layer in self.by_uuid[target]}
        allowed = {n for n in self.vertices if n[0] != target}
        cache, cuts = {}, []

        def edge(a, b):
            if a[1] != b[1] or a[1] not in terminal:
                return True
            token = tuple(sorted((a, b)))
            if token not in cache:
                aa, bb = self.vertices[a], self.vertices[b]
                if not boxes_touch(aa["bbox"], bbox(terminal[a[1]])) or not boxes_touch(bb["bbox"], bbox(terminal[a[1]])):
                    cache[token] = True
                else:
                    overlap = native_polygon(pcb, aa["item"], a[1])
                    overlap.BooleanIntersection(native_polygon(pcb, bb["item"], b[1]))
                    overlap.BooleanSubtract(terminal[a[1]])
                    cache[token] = not overlap.IsEmpty()
                    if not cache[token]:
                        cuts.append({"a_uuid": a[0], "b_uuid": b[0], "layer": self.layer_name(a[1])})
            return cache[token]

        reached = self.reachable(self.by_uuid[start], allowed, edge)
        other = sorted({uid for uid, _ in reached if uid in self.pads and uid != start})
        return {"from": f"{start_ref}.{start_pin}", "to": f"{target_ref}.{target_pin}",
                "connected": self.connected(start, target),
                "independent_until_terminal": self.connected(start, target) and not other,
                "other_pad_connections_before_terminal": [self.describe_pad(uid) for uid in other],
                "branch_copper_uuids": sorted({uid for uid, _ in reached if uid not in self.pads}),
                "joins_cut_wholly_inside_terminal": cuts,
                "method": "Native copper graph, removing only joins inside actual terminal copper; no route-group assumptions",
                "scope": "Topological pickoff screen, not current sharing, voltage error or fault qualification"}


def normalized_finding(finding, pad_owners, moves):
    result = copy.deepcopy(finding)
    for item in result["items"]:
        ref = pad_owners.get(item["uuid"])
        if ref in moves:
            move = moves[ref]
            xy = transform([item["pos"]["x"], item["pos"]["y"]],
                           move["new_native_pose"], move["old_native_pose"])
            item["pos"] = {"x": round(xy[0], 6), "y": round(xy[1], 6)}
        else:
            item["pos"] = {k: round(v, 6) for k, v in item["pos"].items()}
    result["items"].sort(key=lambda i: json.dumps(i, sort_keys=True))
    return json.dumps(result, sort_keys=True)


def native_rules(pad_owners, moves, errors):
    erc = read_json(OUTPUT / "reports" / "erc.json")
    violations = [v for sheet in erc["sheets"] for v in sheet["violations"]]
    if violations:
        errors.append("Native schematic ERC is not clean")
    def pins(path):
        root = ET.parse(path).getroot()
        return Counter((n.get("name"), tuple(sorted(p.attrib.items())))
                       for n in root.findall("nets/net") for p in n.findall("node"))
    require(pins(OUTPUT / "reports" / "handbell-netlist.xml") ==
            pins(SOURCE / "reports" / "handbell-netlist.xml"), "Exported schematic connectivity changed")
    drc = read_json(OUTPUT / "reports" / "drc.json")
    baseline = read_json(SOURCE / "reports" / "drc.json")
    types = Counter(v["type"] for v in drc["violations"])
    inherited_types = {v["type"] for v in baseline["violations"]} & SILK_TYPES
    forbidden = [v for v in drc["violations"] if v["type"] not in inherited_types | {"hole_clearance"}]
    if forbidden:
        errors.append("New physical copper/clearance/short/dangling or non-inherited DRC finding")
    holes = lambda r: Counter(json.dumps(v, sort_keys=True) for v in r["violations"] if v["type"] == "hole_clearance")
    require(holes(drc) == holes(baseline) and types["hole_clearance"] == 4, "The four USB hole errors changed")
    old_parity = Counter(normalized_finding(v, pad_owners, {}) for v in baseline["schematic_parity"])
    new_parity = Counter(normalized_finding(v, pad_owners, moves) for v in drc["schematic_parity"])
    require(len(drc["schematic_parity"]) == len(baseline["schematic_parity"]) == 46 and old_parity == new_parity,
            "Inherited 46 CLI parity tuples changed beyond allowed physical pad pose transforms")
    return {"erc_violations": violations, "physical_drc": dict(types), "forbidden_physical_findings": forbidden,
            "cli_parity_findings": len(drc["schematic_parity"]),
            "parity_comparison": "Exact multiset of full findings; only authorized moved-pad positions inverse-transformed",
            "baseline_unconnected_items": len(baseline["unconnected_items"]),
            "unconnected_items": len(drc["unconnected_items"])}


def service_and_contact_screen(route, graph, errors):
    pcb = graph.pcb
    old_text, old = literal_board(SOURCE / "handbell.kicad_pcb")
    text, board = literal_board(OUTPUT / "handbell.kicad_pcb")
    marks = [n for n in board.children("gr_text") if n.value("layer") == "B.SilkS"]
    previous = [n for n in old.children("gr_text") if n.value("layer") == "B.SilkS"]
    require(len(marks) == len(previous) == 7
            and [literal(text, n) for n in marks] == [literal(old_text, n) for n in previous],
            "The seven retained rear service labels changed")
    baseline = read_json(SOURCE / "reports" / "service-label-review.json")
    prior = {item["text"]: item for item in baseline["labels"]}
    native_marks = [m for m in graph.board.GetDrawings() if isinstance(m, pcb.PCB_TEXT) and m.GetLayer() == pcb.B_SilkS]
    rear = {uid: item for uid, item in graph.items.items() if item.IsOnLayer(pcb.B_Cu)}
    labels = []
    for mark in native_marks:
        require(mark.IsMirrored(), "Rear label is not mirrored")
        shape = mark.GetEffectiveTextShape()
        bounds = [pcb.ToMM(v)-100 for v in bbox(shape)]
        record = prior[mark.GetText()]
        require(max(abs(a-b) for a, b in zip(bounds, record["glyph_bounds_xy_mm"])) < TOL,
                "Native service glyph bounds changed")
        reserve = list(record["screen_bounds_xy_mm"])
        named = record.get("mechanical_text_reservation")
        if named:
            x, y = named["center_xy_mm"]
            w, h = named["maximum_width_height_mm"]
            reserve = [min(reserve[0], x-w/2), min(reserve[1], y-h/2),
                       max(reserve[2], x+w/2), max(reserve[3], y+h/2)]
        rect = rectangle(pcb, [v+100 for v in reserve])
        rect_conflicts, glyph_conflicts = [], []
        for uid, item in rear.items():
            copper = item.GetEffectiveShape(pcb.B_Cu)
            if rect.Collide(copper, 0):
                rect_conflicts.append(uid)
            if shape.Collide(copper, pcb.FromMM(.25)):
                glyph_conflicts.append(uid)
        if rect_conflicts or glyph_conflicts:
            errors.append("Rear copper enters full service rectangle/glyph clearance: " + mark.GetText())
        labels.append({"text": mark.GetText(), "glyph_bounds_xy_mm": bounds,
                       "reserved_full_rectangle_xy_mm": reserve, "rectangle_copper_conflicts": rect_conflicts,
                       "glyph_clearance_mm": .25, "glyph_copper_conflicts": glyph_conflicts})
    contact = read_json(OUTPUT / "battery-contact-interface.json")
    regions = route.prep.contact_metal_reservations(contact)
    conflicts = []
    for region in regions:
        x, y = region["center"]
        w, h = region["size"]
        rect = rectangle(pcb, [100+x-w/2, 100+y-h/2, 100+x+w/2, 100+y+h/2])
        for uid, item in rear.items():
            if item.GetNetname() == region["net"]:
                continue
            if rect.Collide(item.GetEffectiveShape(pcb.B_Cu), pcb.FromMM(.2)):
                conflicts.append({"region": region["id"], "uuid": uid, "net": item.GetNetname()})
    if conflicts:
        errors.append("Opposite-net rear copper enters raw-contact conductive base reservation")
    return {"labels": labels, "contact_base_clearance_mm": .2, "contact_base_conflicts": conflicts,
            "mechanical_visibility": "NOT VALIDATED: old checker has package-bound globals; it is deliberately not invoked",
            "mechanical_rebind_required": True,
            "scope": "Native copper/glyph and retained base-metal projections only, not assembled visibility or insulation qualification"}


def placement_proxy_screen(route, changed, errors, *, baseline=None, manifest=None, resized=None):
    baseline = read_json(SOURCE / "placement-manifest.json") if baseline is None else baseline
    manifest = read_json(OUTPUT / "placement-manifest.json") if manifest is None else manifest
    resized = set(AUTHORIZED_PROXY_DEPTHS) if resized is None else set(resized)

    def corners(component):
        angle = math.radians(component["rotation_deg"])
        return [(component["x_mm"] + x*math.cos(angle) - y*math.sin(angle),
                 component["y_mm"] + x*math.sin(angle) + y*math.cos(angle))
                for x, y in ((-component["width_mm"]/2, -component["depth_mm"]/2),
                             (component["width_mm"]/2, -component["depth_mm"]/2),
                             (component["width_mm"]/2, component["depth_mm"]/2),
                             (-component["width_mm"]/2, component["depth_mm"]/2))]

    def overlaps(components):
        result = set()
        for index, a in enumerate(components):
            for b in components[index+1:]:
                if min(a["z_max_mm"], b["z_max_mm"]) - max(a["z_min_mm"], b["z_min_mm"]) <= TOL:
                    continue
                ac, bc = corners(a), corners(b)
                axes = []
                for component in (a, b):
                    angle = math.radians(component["rotation_deg"])
                    axes.extend(((math.cos(angle), math.sin(angle)), (-math.sin(angle), math.cos(angle))))
                for axis in axes:
                    ap = [p[0]*axis[0] + p[1]*axis[1] for p in ac]
                    bp = [p[0]*axis[0] + p[1]*axis[1] for p in bc]
                    if min(max(ap), max(bp)) - max(min(ap), min(bp)) <= TOL:
                        break
                else:
                    result.add(tuple(sorted((a["reference"], b["reference"]))))
        return result

    old, new = overlaps(baseline["components"]), overlaps(manifest["components"])
    introduced = sorted(new-old)
    affected = set(changed) | resized
    outside = [c["reference"] for c in manifest["components"] if c["reference"] in affected
               and any(route.prep.polygon_distance(p, manifest["board"]["outline_common_xy_mm"]) > TOL
                       for p in corners(c))]
    if introduced:
        errors.append("New same-Z component proxy overlap after local pose changes")
    if outside:
        errors.append("Moved or resized component proxy corner outside unchanged board outline")
    speaker_clearances = []
    bands = ((manifest["speaker_front_z_mm"], manifest["speaker_basket_rear_z_mm"],
              manifest["speaker_dimensions_mm"]["overall_diameter"]/2),
             (manifest["speaker_basket_rear_z_mm"], manifest["speaker_magnet_rear_z_mm"],
              manifest["speaker_dimensions_mm"]["magnet_diameter"]/2))
    for component in manifest["components"]:
        for zmin, zmax, radius in bands:
            if component["side"] != "F" or min(component["z_max_mm"], zmax)-max(component["z_min_mm"], zmin) <= TOL:
                continue
            clearance = route.prep.polygon_distance((0, 0), corners(component))-radius
            speaker_clearances.append({"reference": component["reference"], "radial_clearance_mm": clearance,
                                       "speaker_band_z_mm": [zmin, zmax]})
            if clearance < manifest["speaker_screen"]["radial_planning_margin_mm"]-TOL:
                errors.append("Component proxy enters conservative speaker envelope: "+component["reference"])
    inductor = next(c for c in manifest["components"] if c["reference"] == "L1")
    yoke_gap = inductor["z_min_mm"]-manifest["speaker_screen"]["yoke_top_z_mm"]
    require(inductor["height_mm"] == 5 and yoke_gap >= .7-TOL, "Full-height L1/yoke clearance changed")
    return {"new_proxy_overlap_pairs": introduced, "inherited_proxy_overlap_pairs": sorted(new & old),
            "moved_proxy_corners_outside_outline": [ref for ref in outside if ref in changed],
            "resized_proxy_corners_outside_outline": [ref for ref in outside if ref in resized],
            "resized_proxy_bounds_xy_mm": {
                c["reference"]: [min(p[0] for p in corners(c)), min(p[1] for p in corners(c)),
                                 max(p[0] for p in corners(c)), max(p[1] for p in corners(c))]
                for c in manifest["components"] if c["reference"] in resized},
            "conservative_speaker_clearances": speaker_clearances, "L1_yoke_axial_gap_mm": yoke_gap,
            "scope": "Unqualified component-envelope SAT/intersection screen only; not actual part or mechanical-fit approval",
            "numerical_comparison_epsilon_mm": TOL}


def connection_report(before, after, data, errors):
    baseline, current = before.nets(), after.nets()
    old_nets = {n["net"]: n for n in baseline}
    old_pairs = set()
    for net in baseline:
        for island in net["islands"]:
            ids = sorted(p["uuid"] for p in island)
            old_pairs.update((a, b) for i, a in enumerate(ids) for b in ids[i+1:])
    regressions = [{"from": after.describe_pad(a), "to": after.describe_pad(b),
                    "net": after.pads[a].GetNetname()} for a, b in sorted(old_pairs) if not after.connected(a, b)]
    if regressions and data.get("regression_policy") != (
            "Explicit partial power-first reallocation; report every lost physical-pad pair and never waive copper errors"):
        errors.append(f"{len(regressions)} previously connected physical-pad pairs regressed")
    pairs = []
    for intent in data["connections"]:
        a, b = intent["from_uuid"], intent["to_uuid"]
        require(after.pads[a].GetNetname() == after.pads[b].GetNetname() == intent["net"], "Endpoint intent has wrong net")
        connected = after.connected(a, b)
        if intent["status"].startswith("routed") and not connected:
            errors.append("Claimed route is not native-connected: " + intent["from"] + " -> " + intent["to"])
        pairs.append({"from": intent["from"], "to": intent["to"], "from_uuid": a, "to_uuid": b,
                      "net": intent["net"], "declared_status": intent["status"], "connected": connected,
                      "baseline_connected": before.connected(a, b),
                      "native_shape_path": after.path(a, b) if connected else []})
    transitions = [{"net": n["net"], "before_status": old_nets[n["net"]]["status"], "after_status": n["status"],
                    "before_islands": len(old_nets[n["net"]]["islands"]), "after_islands": len(n["islands"])}
                   for n in current]
    floats = after.floating_copper()
    if floats:
        errors.append(f"{len(floats)} floating/unassigned copper items have no physical pad")
    if after.shorts:
        errors.append("Native effective copper shapes cross nets")
    return {"native_net_connectivity": current, "baseline_native_net_connectivity": baseline,
            "net_transitions": transitions, "regressed_physical_pad_pairs": regressions,
            "native_connected_endpoint_pairs": pairs, "floating_copper_uuids": floats,
            "native_shape_shorts": after.shorts,
            "complete_nets": [n["net"] for n in current if n["status"] == "complete"],
            "partially_connected_nets": [n["net"] for n in current if n["status"] == "partial"],
            "method": "Per-layer native effective-shape contacts and actual plated barrels; no group-name joins",
            "path_caveat": "Reported paths are native item-hop witnesses, not shortest centerline lengths or isolated series resistance"}


def power_topology(before, after, errors):
    loops = []
    for cap in ("C27", "C28"):
        for pin, upin, name in (("1", "6", "positive"), ("2", "4", "ground")):
            a, b = after.pad_uuid("U5", upin), after.pad_uuid(cap, pin)
            old_path, new_path = before.path(a, b, before.pcb.F_Cu), after.path(a, b, after.pcb.F_Cu)
            if not new_path:
                errors.append(f"Mandatory all-front boost {name} path missing: U5.{upin} -> {cap}.{pin}")
            loops.append({"from": f"U5.{upin}", "to": f"{cap}.{pin}", "net": after.pads[a].GetNetname(),
                          "before_all_F": bool(old_path), "after_all_F": bool(new_path),
                          "before_path": old_path, "after_path": new_path})
    sense_before = before.pickoff("R26", "2", "R27", "2")
    sense_after = after.pickoff("R26", "2", "R27", "2")
    if not sense_after["independent_until_terminal"]:
        errors.append("Protector R26.2 is not an independent pickoff to the actual R27.2 land")
    bypass = []
    for cap in ("C16", "C19"):
        a, b = after.pad_uuid(cap, "2"), after.pad_uuid("U4", "THERMAL")
        bypass.append({"from": cap+".2", "to": "U4.THERMAL", "before_connected": before.connected(a, b),
                       "after_connected": after.connected(a, b), "path": after.path(a, b)})
    feedback = after.pickoff("R24", "2", "C28", "2")
    if not feedback["independent_until_terminal"]:
        errors.append("R24 quiet ground merges before its output-capacitor ground pickoff")
    sw_a, sw_b = after.pad_uuid("U5", "5"), after.pad_uuid("L1", "P$2")
    sw_path = after.path(sw_a, sw_b, after.pcb.F_Cu)
    if not sw_path:
        errors.append("Boost switch-to-inductor F-side route is incomplete")
    return {"output_capacitor_all_front_paths": loops,
            "protector_pickoff_before": sense_before, "protector_pickoff_after": sense_after,
            "feedback_ground_capacitor_pickoff": feedback, "amplifier_bypass_returns": bypass,
            "switch_to_inductor_front_path": sw_path,
            "remaining_engineering_review": [
                "All-F connectivity alone does not prove compact loops, low inductance or adequate exposed widths",
                "Inspect native boost details for SW escape under U5 toward the inductor and bounded switch-node area",
                "R24 independent capacitor-ground pickoff is topological evidence, not qualified noise performance",
                "Unfinished source-switch feed and other routing remain explicit; connected amplifier paths still need electrical review",
                "No current/thermal/charge/fault/functional/fabrication or mechanical-fit approval",
            ]}


def detail_bounds():
    points = []
    for package in (SOURCE, OUTPUT):
        m = read_json(package / "placement-manifest.json")
        for c in m["components"]:
            if c["reference"] not in BOOST:
                continue
            angle = math.radians(c["rotation_deg"])
            for x in (-c["width_mm"]/2, c["width_mm"]/2):
                for y in (-c["depth_mm"]/2, c["depth_mm"]/2):
                    points.append((100+c["x_mm"]+x*math.cos(angle)-y*math.sin(angle),
                                   100+c["y_mm"]+x*math.sin(angle)+y*math.cos(angle)))
    return [min(p[0] for p in points)-2, min(p[1] for p in points)-2,
            max(p[0] for p in points)+2, max(p[1] for p in points)+2]


def crop_native_svg(source, target, bounds):
    text = source.read_text(encoding="utf-8")
    match = re.search(r"<svg\b[^>]*>", text, re.DOTALL)
    require(match is not None, "Native SVG has no root")
    root = ET.fromstring(text)
    view = list(map(float, root.attrib["viewBox"].split()))
    require(view[:2] == [0, 0] and root.attrib["width"].endswith("mm"), "Unexpected native full-sheet SVG coordinates")
    xmin, ymin, xmax, ymax = bounds
    require(0 < xmin < xmax < view[2] and 0 < ymin < ymax < view[3], "Native crop extends outside full sheet")
    tag = match.group()
    replacements = {"viewBox": f"{xmin:.6f} {ymin:.6f} {xmax-xmin:.6f} {ymax-ymin:.6f}",
                    "width": f"{(xmax-xmin)*6:.6f}mm", "height": f"{(ymax-ymin)*6:.6f}mm"}
    for name, value in replacements.items():
        tag, count = re.subn(rf'\b{name}="[^"]*"', f'{name}="{value}"', tag)
        require(count == 1, "Unexpected SVG viewport attribute: " + name)
    target.write_text(text[:match.start()] + tag + text[match.end():], encoding="utf-8")
    return {"source_native_svg": source.name, "source_sha256": sha(source),
            "cropped_svg": target.name, "native_absolute_xy_bounds_mm": bounds,
            "method": "Unmodified native KiCad plotted primitives; root viewport/physical display size only changed",
            "view": "F copper from front" if "front" in target.name else "B copper through board, intentionally not mirrored"}


def run_native(route):
    validate_geometry()
    before = input_bindings(route)
    version = subprocess.check_output([str(route.CLI), "--version"], text=True).strip()
    require(version == "10.0.6", "Expected exercised KiCad CLI 10.0.6")
    reports = OUTPUT / "reports"
    work = reports / ".native-validation-work"
    require(not work.exists(), "Inspect existing candidate native work directory before rerunning")
    work.mkdir(parents=True)
    sch, board = str(OUTPUT / "handbell.kicad_sch"), str(OUTPUT / "handbell.kicad_pcb")
    commands = [
        ["sch", "erc", "--format", "json", "--severity-all", "--output", str(work / "erc.json"), sch],
        ["sch", "export", "netlist", "--format", "kicadxml", "--output", str(work / "handbell-netlist.xml"), sch],
        ["pcb", "drc", "--format", "json", "--schematic-parity", "--severity-all", "--output", str(work / "drc.json"), board],
        ["sch", "export", "pdf", "--exclude-pdf-metadata", "--output", str(work / "handbell-schematic.pdf"), sch],
        ["sch", "export", "svg", "--output", str(work / "schematic-svg"), sch],
    ]
    for side, name in (("F", "front"), ("B", "rear")):
        layers = f"{side}.Cu,{side}.Fab,{side}.SilkS,Edge.Cuts"
        mirror = ["--mirror"] if side == "B" else []
        commands.extend([
            ["pcb", "export", "pdf", "--mode-single", "--layers", layers, "--scale", "3", "--exclude-value",
             *mirror, "--output", str(work / f"{name}-native.pdf"), board],
            ["pcb", "export", "svg", "--mode-single", "--layers", layers, "--fit-page-to-board",
             "--exclude-drawing-sheet", *mirror, "--output", str(work / f"{name}-native.svg"), board],
        ])
    for when, package in (("before", SOURCE), ("after", OUTPUT)):
        for side, name in (("F", "front"), ("B", "back")):
            commands.append(["pcb", "export", "svg", "--mode-single", "--layers",
                             f"{side}.Cu,F.SilkS,Edge.Cuts", "--page-size-mode", "1",
                             "--exclude-drawing-sheet", "--scale", "1", "--output",
                             str(work / f"boost-{when}-{name}-sheet.svg"), str(package / "handbell.kicad_pcb")])
    logs = []
    try:
        for command in commands:
            result = subprocess.run([str(route.CLI), *command], cwd=ROOT, capture_output=True,
                                    encoding="utf-8", errors="replace", timeout=600)
            require(result.returncode == 0, "Native command failed: " + result.stdout + result.stderr)
            logs.append({"command": [route.CLI.name, *command], "exit": result.returncode,
                         "stdout": result.stdout, "stderr": result.stderr})
        bounds = detail_bounds()
        crops = [crop_native_svg(work / f"boost-{when}-{side}-sheet.svg",
                                 work / f"boost-{when}-{side}-detail.svg", bounds)
                 for when in ("before", "after") for side in ("front", "back")]
        require(input_bindings(route) == before, "Inputs changed during native validation/export")
        for name in REPORT_FILES:
            target = reports / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(work / name, target)
        write_json(reports / "native-input-bindings.json",
                   {"generated_utc": datetime.now(timezone.utc).isoformat(), "kicad_version": version,
                    "cli_sha256": sha(route.CLI), "inputs": before, "commands": logs, "native_svg_crops": crops,
                    "reports": {name: sha(reports / name) for name in REPORT_FILES}})
    finally:
        shutil.rmtree(work)


def markdown_report(report):
    rules, geometry = report["native_rules"], report["geometry_proof"]
    lines = ["# Printed-bell power-rework native review", "", "**" + report["status"] + "**", "",
             "Not a functional, current, thermal, charge/fault, fabrication or mechanical-fit approval.", "",
             f"- KiCad: {report['kicad_version']}; PCB SHA-256 `{report['hashes']['handbell.kicad_pcb']}`.",
             f"- {report['tracks']} tracks / {report['vias']} vias / no zones; 325 unchanged physical pads.",
             "- Changed root poses: " + (", ".join(sorted(geometry["changed_footprints"])) or "none") + ".",
             f"- ERC: {len(rules['erc_violations'])}; retained USB hole findings: 4; inherited CLI parity: 46.",
             f"- Unconnected items: {rules['baseline_unconnected_items']} -> {rules['unconnected_items']}.",
             f"- Previously connected physical-pad pair regressions: {len(report['regressed_physical_pad_pairs'])}.",
             "", "## Native views", "",
             "[Front PDF](front-native.pdf) / [rear mirrored PDF](rear-native.pdf) / "
             "[front SVG](front-native.svg) / [rear mirrored SVG](rear-native.svg).",
             "[Schematic PDF](handbell-schematic.pdf).",
             "Same-coordinate boost crops: [before F](boost-before-front-detail.svg) / "
             "[after F](boost-after-front-detail.svg) / [before B](boost-before-back-detail.svg) / "
             "[after B](boost-after-back-detail.svg). B detail is a through-board view, not mirrored.",
             "", "## Native power topology", "",
             "| Endpoint pair | Before all-F | After all-F |", "|---|---|---|"]
    for p in report["power_topology"]["output_capacitor_all_front_paths"]:
        lines.append(f"| {p['from']} - {p['to']} | {p['before_all_F']} | {p['after_all_F']} |")
    sense = report["power_topology"]["protector_pickoff_after"]
    lines.extend(["", f"R26.2 -> actual R27.2 terminal independent pickoff: **{sense['independent_until_terminal']}**.",
                  "Pad/track contacts and barrel transitions are derived from native copper shapes, not route groups.",
                  "Paths are contact-hop witnesses, not shortest walks or isolated series-resistance calculations.", "",
                  "## Net completion", "", "| Net | Before | After | Pad islands before/after |", "|---|---|---|---|"])
    for n in report["net_transitions"]:
        lines.append(f"| {n['net']} | {n['before_status']} | {n['after_status']} | "
                     f"{n['before_islands']} / {n['after_islands']} |")
    lines.extend(["", "## Validation failures", ""])
    lines.extend("- " + e for e in report["errors"])
    if not report["errors"]:
        lines.append("No failure of the implemented screens. Routing and qualification remain incomplete.")
    lines.extend(["", "## Remaining gates", "",
                  "The former mechanical/service-label checker is not run against this package. Its package-bound",
                  "globals and prior fit approval are not reusable evidence for moved electronics. The exact new",
                  "manifest/PCB still require mechanical rebind, assembled label visibility and physical review.",
                  "Native service glyphs and all seven full rectangles are separately screened against rear copper.",
                  "Review exposed power widths, loop area, SW escape, R24 quiet ground, source/return completion,",
                  "finished copper and via process, current/thermal/charge/fault behavior before any release.", ""])
    return "\n".join(lines)


def check(route):
    geometry, board, pad_owners, pad_ids = validate_geometry()
    data = validate_route_data(board, pad_ids)
    bindings = read_json(OUTPUT / "reports" / "native-input-bindings.json")
    require(bindings["kicad_version"] == "10.0.6" and bindings["cli_sha256"] == sha(route.CLI),
            "Native tool version/binary binding changed")
    inputs = input_bindings(route)
    require(inputs == bindings["inputs"], "Missing or stale power-rework native input binding; use --run-native")
    require(bindings["reports"] == {name: sha(OUTPUT / "reports" / name) for name in REPORT_FILES},
            "Native reports or native SVG crops changed")
    errors = []
    rules = native_rules(pad_owners, geometry["changed_footprints"], errors)
    pcb = native_api(route)
    before, after = CopperGraph(pcb, SOURCE / "handbell.kicad_pcb"), CopperGraph(pcb, OUTPUT / "handbell.kicad_pcb")
    native_unconnected = int(after.board.GetConnectivity().GetUnconnectedCount(False))
    if native_unconnected != rules["unconnected_items"]:
        errors.append("Native connectivity engine and DRC unconnected counts disagree")
    connectivity = connection_report(before, after, data, errors)
    power = power_topology(before, after, errors)
    service = service_and_contact_screen(route, after, errors)
    proxies = placement_proxy_screen(route, geometry["changed_footprints"], errors)
    lengths = defaultdict(float)
    for track in data["tracks"]:
        lengths[f'{track["layer"]} / {track["width"]:g}mm'] += math.dist(track["a"], track["b"])
    report = {
        "schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FAILED native power-rework validation" if errors else
                  "PASS implemented native screens; PARTIAL ENGINEERING CANDIDATE, NOT APPROVED",
        "kicad_version": pcb.GetBuildVersion(), "errors": errors,
        "hashes": {name: sha(OUTPUT / name) for name in ("handbell.kicad_pcb", "handbell.kicad_sch",
                   "placement-manifest.json", "battery-contact-interface.json", "routing-data.json", "routing-build.json")},
        "native_binding_sha256": sha(OUTPUT / "reports" / "native-input-bindings.json"),
        "tracks": len(data["tracks"]), "vias": len(data["vias"]), "zones": 0,
        "geometry_proof": geometry, "native_rules": rules, **connectivity,
        "native_engine_unconnected_items": native_unconnected,
        "power_topology": power, "service_label_and_contact_screen": service,
        "placement_proxy_screen": proxies,
        "drawn_track_lengths_mm_by_layer_width": {k: round(v, 6) for k, v in sorted(lengths.items())},
        "remaining_routing_intents": [r for r in data["connections"] if not r["status"].startswith("routed")],
        "mechanical_rebind_required": True,
        "gates": ["No former mechanical approval transfers to moved poses",
                  "No fabrication, purchasing, live-cell, charge/fault or child-use authorization",
                  "All-F connectivity is not proof of low inductance, current capacity or short-loop quality",
                  "Native inherited silk types remain review work; four USB hole errors are not waived"],
    }
    require(input_bindings(route) == inputs, "Inputs changed during read-only native graph checks")
    write_json(OUTPUT / "reports" / "routing-review.json", report)
    (OUTPUT / "reports" / "routing-review.md").write_text(markdown_report(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "tracks": report["tracks"], "vias": report["vias"],
                      "unconnected_items": rules["unconnected_items"], "errors": errors}, indent=2))
    require(not errors, "Native validation failed; see candidate reports/routing-review.json")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-native", action="store_true", help="Refresh KiCad ERC/DRC/netlist/PDF/SVG evidence, then check")
    args = parser.parse_args()
    route = generator()
    if args.run_native:
        run_native(route)
    check(route)


if __name__ == "__main__":
    main()
