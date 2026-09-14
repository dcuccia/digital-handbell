# SPDX-License-Identifier: MIT
"""Measure the final printed-bell-power-rework PCB, without changing its copper.

Run ONLY after the generator has finished, with its final PCB SHA-256:
  python -B tools\\analyze_printed_bell_power_paths.py --pcb-sha256 <64 hex digits>

Writes only that package's reports/power-path-measurements.{json,md}. Requires
the existing KiCad 10.0.6 Python API and numpy; installs nothing. --help does not
import the generator or load a board. No DRC, generation, or parent review runs.

This is a finite, overlap-aware, shortest sampled geometric walk, NOT a 2-D
resistance solver. Finite pad travel is included. A conservative chosen-strip
1-D resistance screen and exposed-centerline neck inventory accompany each
walk; neither is an equivalent resistance or a thermal/current qualification.
An open path never acquires a fabricated round-trip resistance.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import heapq
import itertools
import json
import math
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "hardware" / "handbell" / "iterations" / "printed-bell-routing"
OUTPUT = SOURCE.parent / "printed-bell-power-rework"
RHO = .0172                       # ohm.mm^2/m, nominal 20 C
FOIL_MM = .035
BOARD_MM = 1.6
WALL_MM = .025
HOT_FACTOR = 1.35
VIA_HOT_FACTOR = 1 + .00393 * 40
EPS = .000002                    # mm; native polygonization is bounded at 1 nm
SLICE_MM = .25
NECK_WIDTH_MM = .35
np = None                        # Loaded only for an explicitly requested final PCB.
EXPECTED_NETS = {
    "cell_vbat": "VBAT", "cell_vhi": "VHI", "cell_vplus": "V+", "cell_gnd": "GND",
    "cell_prot_a2": "/PROT_FET_RETURN", "cell_prot_c2": "/PROT_FET_RETURN",
    "cell_neg_a1": "/CELL_NEG", "cell_neg_c1": "/CELL_NEG",
    "v5_to_bulk": "VAMP", "v5_to_amp7": "VAMP", "v5_to_amp8": "VAMP",
    "v5_return_thermal": "GND", "v5_return_11": "GND", "v5_bulk_return": "GND",
    "sw_escape": "BOOST_SW", "input_cap_feed": "V+", "vin_bias": "V+",
    "feedback_ground": "GND", "protector_sense": "GND", "amp_local_ground11": "GND",
}

ASSUMPTIONS = [
    "Native KiCad copper, not authored route groups, owns connectivity and path selection.",
    "Only F.Cu/B.Cu straight tracks, native pads and through vias are supported; no zones/arcs.",
    "Native inward copper polygons and outward drill polygons use a 1 nm polygonization bound; "
    "positive-width walk contacts use a 2 nm numerical guard. Boundary-only contact is not a usable walk.",
    "Dijkstra minimizes XY walk length plus 1.6 mm per layer transition on a finite portal graph. "
    "It is not the exact geometric shortest path, least-resistance path, or a 2-D current solution.",
    "An identical-XY overlap join has zero length; travel across a pad or between different contacts "
    "does not. Separate physical pads sharing a pin number are never internally shorted.",
    "Foil screening uses rho*L/(w*t). Each <=0.25 mm walk slice uses an inscribed strip width "
    "equal to twice its minimum distance to the same-net copper-union boundary, including holes.",
    "These restrictive chosen-strip estimates intentionally ignore parallel current redistribution. "
    "They can overstate drop; bends, junction spreading, barrel entry crowding, terminal injection "
    "and overlapping strips prevent calling them a rigorous upper bound or equivalent resistance.",
    "Neck inventory subtracts actual same-net pad, via-annulus and strictly broader-track coverage "
    "from drawn centerlines. Coverage is not proof of full-width bypass or absence of a 2-D bottleneck.",
    "A chosen-path current is a conditional load case, not a measured branch current. Bias, sense, "
    "feedback and capacitor-ripple spurs receive no blanket 2 A assignment.",
    "Nominal foil is assumed 35 um/20 C. The requested 30 um/60 C sensitivity is 1.35x nominal. "
    "60 C is a calculation case, not an allowed cell/enclosure temperature.",
    "Via DCR uses thin-wall rho*board_thickness/(pi*drill*wall), conditional on 25 um wall plating "
    "and 1.6 mm board thickness. Neither plating nor finished copper is selected/qualified.",
    "Each selected barrel is charged once per traversal at its full conditional DCR. No equal "
    "sharing, parallel Q5 via division, or thermal-via-array resistance reduction is assumed.",
    "JSON decimal places preserve computational reproducibility, not measurement accuracy. "
    "Markdown resistance/drop screens are intentionally shown to about two significant digits.",
    "A barrel edge is a lumped annulus-to-annulus connection, not a vertical copper column at "
    "the reported annular XY port; its entry/exit spreading is not solved.",
    "Cell copper sections are concatenated only conditionally across the excluded ON-state "
    "selector/audio/protector FETs, shunt and converter. No copper edge bridges different nets.",
    "Copper budgets exclude contacts, solder interfaces, FETs, the deliberate 33 mOhm shunt, "
    "inductor winding, IC internals and capacitor ESR. These are separate additional losses.",
    "No IPC-2152 or 10 C temperature-rise claim, ampacity, functional, fault, fabrication, "
    "mechanical, live-cell or child-use signoff follows. Prior QSPI/GND losses are not waived.",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def rounded(value):
    return round(float(value), 6)


def xy(point):
    return [rounded(v - 100) for v in point]


def interpolate(a, b, fraction):
    return tuple(a[i] + fraction * (b[i] - a[i]) for i in (0, 1))


def merge_intervals(intervals):
    result = []
    for start, end in sorted(intervals):
        if end <= start:
            continue
        if result and start <= result[-1][1] + 1e-10:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    return result


def complement(intervals):
    result, cursor = [], 0.
    for start, end in merge_intervals(intervals):
        if start > cursor:
            result.append([cursor, start])
        cursor = max(cursor, end)
    if cursor < 1:
        result.append([cursor, 1.])
    return result


def foil_mohm(length, width):
    return RHO * length / (width * FOIL_MM)


def barrel_mohm(drill):
    return RHO * BOARD_MM / (math.pi * drill * WALL_MM)


def resistance_record(foil, barrels):
    nominal = foil + barrels
    return {
        "foil_35um_20C_mOhm": rounded(foil),
        "barrels_conditional_25um_wall_20C_mOhm": rounded(barrels),
        "nominal_chosen_strip_mOhm": rounded(nominal),
        "requested_1p35x_total_mOhm": rounded(nominal * HOT_FACTOR),
        "foil_1p35x_plus_same_wall_barrels_60C_mOhm":
            rounded(foil * HOT_FACTOR + barrels * VIA_HOT_FACTOR),
        "interpretation": "1-D chosen-strip screen; NOT equivalent R or a rigorous upper bound",
    }


def coherent_inputs(check, route, expected):
    """Fail before loading native copper if the generated package is in flight."""
    require(route.ROOT == ROOT and route.SOURCE == SOURCE and route.OUTPUT == OUTPUT,
            "Generator package paths changed; review analyzer scope")
    build = read_json(OUTPUT / "routing-build.json")
    manifest = read_json(OUTPUT / "placement-manifest.json")
    require(sha(OUTPUT / "handbell.kicad_pcb") == expected == build["pcb_sha256"]
            == manifest["generated_pcb_sha256"], "Final PCB/build/manifest hash mismatch; do not analyze an in-flight build")
    require(build["script_sha256"] == sha(route.__file__), "Generator changed since this PCB was built")
    require(build.get("protected_files") and build.get("source_bindings"), "Missing generator coherence bindings")
    paths = {
        Path(__file__), Path(check.__file__), Path(route.__file__),
        ROOT / "tools" / "route_printed_bell.py", ROOT / "tools" / "kicad_sexpr.py",
        Path(route.prep.__file__), OUTPUT / "handbell.kicad_pcb",
        OUTPUT / "routing-data.json", OUTPUT / "routing-build.json",
        OUTPUT / "placement-manifest.json", SOURCE / "handbell.kicad_pcb",
        SOURCE / "routing-data.json", SOURCE / "placement-manifest.json",
        SOURCE / "reports" / "power-routing-review.md",
    }
    for name, digest in check.PINNED_SOURCE.items():
        require(sha(SOURCE / name) == digest, "Frozen source changed: " + name)
    for mapping, base in ((build["protected_files"], OUTPUT), (build["source_bindings"], ROOT)):
        for name, digest in mapping.items():
            path = (base / name).resolve()
            require(path.is_relative_to(base), "Binding escapes its allowed root: " + name)
            require(sha(path) == digest, "Stale build dependency: " + name)
            paths.add(path)
    bindings = {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}
    require(bindings[str(OUTPUT.relative_to(ROOT) / "handbell.kicad_pcb")] == expected,
            "PCB changed while capturing bindings")
    return bindings, build


def assert_unchanged(bindings):
    for name, digest in bindings.items():
        require(sha(ROOT / name) == digest, "Inputs changed during analysis; discard this run: " + name)


def route_inventory(check, package):
    """Match every authored record to native literal copper before using labels."""
    _, board = check.literal_board(package / "handbell.kicad_pcb")
    require(not any(board.children(kind) for kind in ("zone", "arc", "group")),
            "Zones/arcs/groups require a new native path model")
    data = read_json(package / "routing-data.json")
    records = {}
    for kind, field in (("segment", "tracks"), ("via", "vias")):
        nodes, rows = board.children(kind), data[field]
        require(len(nodes) == len(rows), f"{package.name}: native/{field} inventory mismatch")
        for node, row in zip(nodes, rows):
            uid = node.value("uuid")
            require(uid and uid not in records, "Missing/duplicate native copper UUID")
            require(node.value("net") == row["net"], "Native/route-data net mismatch")
            if kind == "segment":
                for key, value in (("start", row["a"]), ("end", row["b"])):
                    native = list(map(float, node.child(key).atoms()[1:3]))
                    require(len(value) == 2 and all(math.isfinite(x) for x in value)
                            and math.dist(native, [x + 100 for x in value]) < EPS,
                            "Native/route-data track position mismatch")
                require(node.value("layer") == row["layer"] and row["layer"] in ("F.Cu", "B.Cu")
                        and abs(float(node.value("width")) - row["width"]) < EPS
                        and row["width"] > 0 and math.dist(row["a"], row["b"]) > EPS,
                        "Unsupported/mismatched native track")
            else:
                native = list(map(float, node.child("at").atoms()[1:3]))
                require(math.dist(native, [x + 100 for x in row["xy"]]) < EPS
                        and abs(float(node.value("size")) - row["diameter"]) < EPS
                        and abs(float(node.value("drill")) - row["drill"]) < EPS
                        and row["diameter"] > row["drill"] > 0
                        and node.child("layers").atoms()[1:] == ["F.Cu", "B.Cu"],
                        "Unsupported/mismatched native via")
            records[uid] = {"kind": kind, **row}
    return records


class Polygon:
    """Native polygon plus vectorized boundary-distance and line-clipping queries."""

    def __init__(self, pcb, native):
        self.pcb, self.native = pcb, native
        self.rings, self.outlines = [], []
        for index in range(native.OutlineCount()):
            chains = [native.Outline(index)]
            chains.extend(native.Hole(index, h) for h in range(native.HoleCount(index)))
            for offset, chain in enumerate(chains):
                points = [(pcb.ToMM(chain.CPoint(i).x), pcb.ToMM(chain.CPoint(i).y))
                          for i in range(chain.PointCount())]
                if len(points) >= 3:
                    self.rings.append(points)
                    if offset == 0:
                        self.outlines.append(points)
        require(self.rings, "Empty copper polygon needs an explicit unavailable result")
        self.a = np.array([p for ring in self.rings for p in ring], dtype=float)
        self.b = np.array([p for ring in self.rings for p in ring[1:] + ring[:1]], dtype=float)
        self.delta = self.b - self.a
        self.denominator = np.sum(self.delta * self.delta, axis=1)
        self.denominator[self.denominator == 0] = 1

    def contains(self, point):
        return self.native.Contains(self.pcb.VECTOR2I(*(round(x * 1e6) for x in point)))

    def point_clearance(self, point):
        point = np.asarray(point)
        t = np.clip(np.sum((point - self.a) * self.delta, axis=1) / self.denominator, 0, 1)
        return float(np.sqrt(np.min(np.sum((point - self.a - t[:, None] * self.delta) ** 2, axis=1))))

    def crossings(self, start, end):
        start, end = np.asarray(start), np.asarray(end)
        d = end - start
        e, v = self.delta, self.a - start
        cross = d[0] * e[:, 1] - d[1] * e[:, 0]
        good = np.abs(cross) > 1e-14
        t = np.zeros(len(cross))
        u = np.zeros(len(cross))
        t[good] = (v[good, 0] * e[good, 1] - v[good, 1] * e[good, 0]) / cross[good]
        u[good] = (v[good, 0] * d[1] - v[good, 1] * d[0]) / cross[good]
        hits = good & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)
        return t[hits].tolist()

    def covered_intervals(self, start, end):
        if math.dist(start, end) <= EPS:
            return [[0., 1.]] if self.contains(start) else []
        cuts = sorted({0., 1., *self.crossings(start, end)})
        return merge_intervals([[a, b] for a, b in zip(cuts, cuts[1:])
                                if self.contains(interpolate(start, end, (a + b) / 2))])

    def segment_clearance(self, start, end):
        if not self.contains(start) or not self.contains(end) or self.crossings(start, end):
            return 0.
        start, end = np.asarray(start), np.asarray(end)
        d = end - start
        length2 = float(np.dot(d, d))
        if length2 == 0:
            return self.point_clearance(start)
        t = np.clip(np.sum((self.a - start) * d, axis=1) / length2, 0, 1)
        vertex_distance = np.sqrt(np.min(np.sum((self.a - start - t[:, None] * d) ** 2, axis=1)))
        return min(self.point_clearance(start), self.point_clearance(end), float(vertex_distance))

    def candidates(self, seeds=(), limit=3):
        candidates = list(seeds)
        for ring in self.outlines:
            xs, ys = zip(*ring)
            candidates.append((sum(xs) / len(xs), sum(ys) / len(ys)))
            for x in (.2, .5, .8):
                for y in (.2, .5, .8):
                    candidates.append((min(xs) + x * (max(xs) - min(xs)),
                                       min(ys) + y * (max(ys) - min(ys))))
        scores = []
        for p in sorted({tuple(round(v, 6) for v in p) for p in candidates}):
            if self.contains(p):
                clearance = self.point_clearance(p)
                if clearance > EPS:
                    scores.append((clearance, p))
        scores.sort(reverse=True)
        result = []
        for _, point in scores:
            if not result or min(math.dist(point, p) for p in result) > .02:
                result.append(point)
            if len(result) == limit:
                break
        return result


class NativeWalk:
    def __init__(self, check, pcb, package, records):
        self.check, self.pcb, self.package, self.records = check, pcb, package, records
        self.graph = check.CopperGraph(pcb, package / "handbell.kicad_pcb")
        require(self.graph.board.GetCopperLayerCount() == 2, "Only two copper layers are modeled")
        native_thickness = pcb.ToMM(self.graph.board.GetDesignSettings().GetBoardThickness())
        require(abs(native_thickness - BOARD_MM) < EPS, "The conditional barrel model requires a 1.6 mm board")
        self.geometry, self.unions, self.coverage_cache = {}, {}, {}
        self.nodes, self.adj, self.local_nodes = [], defaultdict(list), defaultdict(dict)
        self.anchors, self.built_nets = {}, set()
        self.issues = []
        self.holes = []
        self.barrels = {}
        for uid, item in self.graph.items.items():
            hole = pcb.SHAPE_POLY_SET()
            if isinstance(item, pcb.PCB_VIA):
                drill = item.GetDrillValue()
                # Reuse KiCad's native round-drill polygonizer, without adding a board item.
                dummy = pcb.PAD(None)
                dummy.SetAttribute(pcb.PAD_ATTRIB_PTH)
                dummy.SetPosition(item.GetPosition())
                dummy.SetDrillSize(pcb.VECTOR2I(drill, drill))
                dummy.TransformHoleToPolygon(hole, 0, 1, pcb.ERROR_OUTSIDE)
                self.barrels[uid] = (pcb.ToMM(drill), pcb.ToMM(item.GetWidth(pcb.F_Cu)))
            elif uid in self.graph.pads:
                size = item.GetDrillSize()
                if size.x > 0 and size.y > 0:
                    item.TransformHoleToPolygon(hole, 0, 1, pcb.ERROR_OUTSIDE)
                    if item.GetAttribute() == pcb.PAD_ATTRIB_PTH:
                        if size.x == size.y:
                            self.barrels[uid] = (pcb.ToMM(size.x), pcb.ToMM(min(item.GetSize().x, item.GetSize().y)))
                        else:
                            self.issues.append({"uuid": uid, "reason": "Slotted plated-pad barrel not modeled"})
            if not hole.IsEmpty():
                self.holes.append((check.bbox(hole), hole))

    def layer_name(self, layer):
        return self.graph.layer_name(layer)

    def item_kind(self, uid):
        return "pad" if uid in self.graph.pads else self.records[uid]["kind"]

    def polygon(self, key):
        if key not in self.geometry:
            item = self.graph.vertices[key]["item"]
            native = self.check.native_polygon(self.pcb, item, key[1], outside=False)
            bounds = self.check.bbox(native)
            for hole_bounds, hole in self.holes:
                if self.check.boxes_touch(bounds, hole_bounds):
                    native.BooleanSubtract(hole)
            self.geometry[key] = None if native.IsEmpty() else Polygon(self.pcb, native)
        return self.geometry[key]

    def point(self, key, point):
        point = tuple(round(v, 6) for v in point)
        if point not in self.local_nodes[key]:
            node = len(self.nodes)
            self.local_nodes[key][point] = node
            self.nodes.append((key, point))
        return self.local_nodes[key][point]

    def join(self, a, b, kind, owner):
        if a == b:
            return
        length = BOARD_MM if kind == "barrel" else math.dist(self.nodes[a][1], self.nodes[b][1])
        edge = {"kind": kind, "owner_uuid": owner, "length_mm": length}
        self.adj[a].append((b, edge))
        self.adj[b].append((a, edge))

    def initialize_item(self, key):
        poly = self.polygon(key)
        if poly is None:
            self.issues.append({"uuid": key[0], "reason": "Native copper removed entirely by actual drills"})
            return
        uid, layer = key
        item = self.graph.items[uid]
        position = item.GetPosition()
        center = (self.pcb.ToMM(position.x), self.pcb.ToMM(position.y))
        points = poly.candidates([center], limit=1)
        if uid in self.graph.pads and points:
            anchor = center if poly.contains(center) and poly.point_clearance(center) > EPS else points[0]
            self.anchors[key] = self.point(key, anchor)
        if self.item_kind(uid) == "segment":
            row = self.records[uid]
            points += [tuple(v + 100 for v in row[end]) for end in ("a", "b")]
        if uid in self.barrels:
            drill, diameter = self.barrels[uid]
            radius = (drill + diameter) / 4
            points += [(center[0] + radius * math.cos(i * math.tau / 24),
                        center[1] + radius * math.sin(i * math.tau / 24)) for i in range(24)]
        # Small interior scaffolds support nonconvex/custom pads and drilled tracks.
        if poly.native.HoleCount(0) or poly.native.OutlineCount() > 1 or (
                uid in self.graph.pads and item.GetShape() == self.pcb.PAD_SHAPE_CUSTOM):
            for ring in poly.outlines:
                xs, ys = zip(*ring)
                points += [(min(xs) + i * (max(xs) - min(xs)) / 6,
                            min(ys) + j * (max(ys) - min(ys)) / 6)
                           for i in range(1, 6) for j in range(1, 6)]
        for point in points:
            if poly.contains(point) and poly.point_clearance(point) > EPS:
                self.point(key, point)

    def build_net(self, net):
        if net in self.built_nets:
            return
        keys = sorted(k for k, v in self.graph.vertices.items() if v["net"] == net)
        for key in keys:
            self.initialize_item(key)
        for a in keys:
            for b in sorted(self.graph.adj[a]):
                if a >= b or a[1] != b[1]:
                    continue
                aa, bb = self.polygon(a), self.polygon(b)
                if aa is None or bb is None:
                    continue
                overlap = self.pcb.SHAPE_POLY_SET()
                overlap.BooleanIntersection(aa.native, bb.native)
                if overlap.IsEmpty():
                    self.issues.append({"a_uuid": a[0], "b_uuid": b[0],
                                        "layer": self.layer_name(a[1]),
                                        "reason": "Native touch has no positive-area drilled inward overlap"})
                    continue
                region = Polygon(self.pcb, overlap)
                seeds = list(self.local_nodes[a]) + list(self.local_nodes[b])
                ports = region.candidates(seeds, limit=3)
                if not ports:
                    self.issues.append({"a_uuid": a[0], "b_uuid": b[0],
                                        "reason": "Finite contact sampling found no interior portal"})
                for port in ports:
                    self.join(self.point(a, port), self.point(b, port), "overlap", a[0])
        for key in keys:
            poly = self.polygon(key)
            if poly is None:
                continue
            points = sorted(self.local_nodes[key].items())
            for (a, ai), (b, bi) in itertools.combinations(points, 2):
                if poly.segment_clearance(a, b) > EPS:
                    self.join(ai, bi, "foil", key[0])
        for uid, (drill, diameter) in sorted(self.barrels.items()):
            front, back = (uid, self.pcb.F_Cu), (uid, self.pcb.B_Cu)
            if front not in self.local_nodes or back not in self.local_nodes:
                continue
            if self.graph.vertices[front]["net"] != net:
                continue
            # Only native plated same-item layer joins can become barrel edges.
            require(back in self.graph.adj[front], "Missing native plated barrel join")
            center = self.graph.items[uid].GetPosition()
            center = (self.pcb.ToMM(center.x), self.pcb.ToMM(center.y))
            radius = (drill + diameter) / 4
            for point in sorted(self.local_nodes[front].keys() & self.local_nodes[back].keys()):
                if abs(math.dist(point, center) - radius) < EPS:
                    self.join(self.local_nodes[front][point], self.local_nodes[back][point], "barrel", uid)
        for layer in (self.pcb.F_Cu, self.pcb.B_Cu):
            union = self.pcb.SHAPE_POLY_SET()
            for key in keys:
                if key[1] == layer and self.polygon(key) is not None:
                    union.BooleanAdd(self.polygon(key).native)
            if not union.IsEmpty():
                self.unions[(net, layer)] = Polygon(self.pcb, union)
        self.built_nets.add(net)

    def endpoints(self, label):
        ref, number = label.split(".", 1)
        ids = sorted(self.graph.lookup.get((ref, number), []))
        return [{"uuid": uid, "net": self.graph.pads[uid].GetNetname(),
                 "layers": [self.layer_name(k[1]) for k in self.graph.by_uuid[uid]]}
                for uid in ids]

    def path(self, name, start, end, role, current=None, layer=None):
        aa, bb = self.endpoints(start), self.endpoints(end)
        result = {
            "id": name, "from": start, "to": end, "role": role,
            "conditional_screen_current_A": current, "layer_constraint": layer or "F.Cu/B.Cu",
            "from_physical_pads": aa, "to_physical_pads": bb,
            "terminal_policy": "Choose one actual physical pad at each end; never short duplicate pin pads",
            "status": "NOT_DEMONSTRATED", "native_connected": False,
            "walk": [], "resistance": None,
        }
        if not aa or not bb:
            result["reason"] = "Missing required endpoint"
            return result
        nets = {p["net"] for p in aa + bb}
        if len(nets) != 1 or not next(iter(nets)):
            result["reason"] = "Endpoints are not on one named native net; no invented bridge"
            return result
        net = next(iter(nets))
        result["net"] = net
        expected = EXPECTED_NETS.get(name)
        if start == "U5.6" and end in ("C27.1", "C28.1"):
            expected = "VAMP"
        elif start in ("C27.2", "C28.2") and end == "U5.4":
            expected = "GND"
        result["expected_net"] = expected
        if expected is not None and net != expected:
            result["reason"] = "Required current corridor has a different native net than its declared circuit role"
            return result
        self.build_net(net)
        layer_id = None if layer is None else (self.pcb.F_Cu if layer == "F.Cu" else self.pcb.B_Cu)
        pairs = []
        for a, b in itertools.product(aa, bb):
            connected = bool(self.graph.path(a["uuid"], b["uuid"], layer_id))
            pairs.append({"from_uuid": a["uuid"], "to_uuid": b["uuid"], "connected": connected})
        result["native_terminal_pairs"] = pairs
        result["native_connected"] = any(p["connected"] for p in pairs)
        if not result["native_connected"]:
            result.update(status="OPEN", reason="No native same-net copper connection under this layer constraint")
            return result
        starts = [self.anchors[k] for p in aa for k in self.graph.by_uuid[p["uuid"]]
                  if k in self.anchors and (layer_id is None or k[1] == layer_id)]
        targets = {self.anchors[k] for p in bb for k in self.graph.by_uuid[p["uuid"]]
                   if k in self.anchors and (layer_id is None or k[1] == layer_id)}
        distance, previous = {n: 0. for n in starts}, {n: None for n in starts}
        queue = [(0., n) for n in starts]
        heapq.heapify(queue)
        found = None
        while queue:
            cost, node = heapq.heappop(queue)
            if cost != distance[node]:
                continue
            if node in targets:
                found = node
                break
            for other, edge in self.adj[node]:
                if layer_id is not None and self.nodes[other][0][1] != layer_id:
                    continue
                total = cost + edge["length_mm"]
                if total < distance.get(other, math.inf):
                    distance[other] = total
                    previous[other] = (node, edge)
                    heapq.heappush(queue, (total, other))
        if found is None:
            result["reason"] = "Native-connected, but sampled positive-width walk NOT_DEMONSTRATED; not an OPEN verdict"
            return result
        edges, node = [], found
        while previous[node] is not None:
            parent, edge = previous[node]
            edges.append((parent, node, edge))
            node = parent
        edges.reverse()
        result.update(status="CONNECTED_CHOSEN_WALK", selected_from_uuid=self.nodes[node][0][0],
                      selected_to_uuid=self.nodes[found][0][0])
        result["walk_start_xy_mm"] = xy(self.nodes[node][1])
        result["walk_end_xy_mm"] = xy(self.nodes[found][1])
        foil, barrels, xy_length, vertical = 0., 0., 0., 0.
        finite_resistance = True
        for ai, bi, edge in edges:
            (akey, a), (bkey, b) = self.nodes[ai], self.nodes[bi]
            if edge["kind"] == "overlap":
                continue
            uid = edge["owner_uuid"]
            row = {"kind": edge["kind"], "owner_uuid": uid, "owner_kind": self.item_kind(uid),
                   "from_xy_mm": xy(a), "to_xy_mm": xy(b),
                   "from_layer": self.layer_name(akey[1]), "to_layer": self.layer_name(bkey[1]),
                   "length_mm": rounded(edge["length_mm"]),
                   "author_group_annotation_only": self.records.get(uid, {}).get("group")}
            if row["owner_kind"] == "segment":
                row["drawn_width_mm"] = self.records[uid]["width"]
            elif row["owner_kind"] == "pad":
                row["physical_pad"] = self.graph.describe_pad(uid)
            if edge["kind"] == "barrel":
                drill = self.barrels[uid][0]
                r = barrel_mohm(drill)
                row.update(drill_mm=rounded(drill), conditional_barrel_mOhm=rounded(r))
                barrels += r
                vertical += BOARD_MM
            else:
                length = math.dist(a, b)
                xy_length += length
                count = max(1, math.ceil(length / SLICE_MM))
                union = self.unions[(net, akey[1])]
                slices = []
                for index in range(count):
                    c, d = interpolate(a, b, index / count), interpolate(a, b, (index + 1) / count)
                    width = 2 * union.segment_clearance(c, d)
                    r = foil_mohm(math.dist(c, d), width) if width > 2 * EPS else None
                    slices.append({"from_xy_mm": xy(c), "to_xy_mm": xy(d),
                                   "inscribed_width_mm": rounded(width),
                                   "foil_mOhm": None if r is None else rounded(r)})
                    if r is None:
                        finite_resistance = False
                    else:
                        foil += r
                row["chosen_strip_slices"] = slices
            result["walk"].append(row)
        result.update(xy_length_including_pad_travel_mm=rounded(xy_length),
                      barrel_length_mm=rounded(vertical), barrel_traversals=sum(
                          s["kind"] == "barrel" for s in result["walk"]),
                      objective_length_mm=rounded(xy_length + vertical))
        if finite_resistance:
            result["resistance"] = resistance_record(foil, barrels)
            if current is not None:
                result["conditional_drop_mV"] = {
                    "nominal": rounded(current * (foil + barrels)),
                    "requested_1p35x_total": rounded(current * (foil + barrels) * HOT_FACTOR),
                }
                if name.startswith("cell_"):
                    result["sensitivity_3A_drop_mV"] = {
                        "nominal": rounded(3 * (foil + barrels)),
                        "requested_1p35x_total": rounded(3 * (foil + barrels) * HOT_FACTOR),
                    }
        else:
            result["resistance_unavailable_reason"] = "A copper-union slice has unresolved/nonpositive clearance"
        return result

    def covering(self, key):
        if key not in self.coverage_cache:
            width = self.records[key[0]]["width"]
            groups = defaultdict(list)
            for other in sorted(self.graph.adj[key]):
                if other[1] != key[1]:
                    continue
                kind = self.item_kind(other[0])
                if kind == "segment" and self.records[other[0]]["width"] <= width + EPS:
                    continue
                if self.polygon(other) is not None:
                    groups[{"pad": "pad", "via": "via_annulus", "segment": "broader_track"}[kind]].append(other)
            self.coverage_cache[key] = groups
        return self.coverage_cache[key]

    def exposed(self, key, a, b):
        coverage, covered = {}, []
        for category, keys in self.covering(key).items():
            intervals = []
            owners = []
            for other in keys:
                portion = self.polygon(other).covered_intervals(a, b)
                if portion:
                    intervals.extend(portion)
                    owners.append(other[0])
            coverage[category] = {"uuids": owners, "intervals": merge_intervals(intervals)}
            covered.extend(intervals)
        # A drilled-out centerline is not exposed copper.
        own = self.polygon(key)
        own_intervals = [] if own is None else own.covered_intervals(a, b)
        uncovered = complement(covered)
        exposed = merge_intervals([[max(c, e), min(d, f)] for c, d in uncovered
                                   for e, f in own_intervals if min(d, f) > max(c, e)])
        return coverage, exposed, own_intervals

    def necks(self, paths):
        ownership = defaultdict(list)
        for path in paths:
            for step in path["walk"]:
                if step["kind"] == "foil" and step["owner_kind"] == "segment":
                    ownership[step["owner_uuid"]].append((path, step))
        inventory = []
        for uid, row in sorted(self.records.items()):
            if row["kind"] != "segment" or row["width"] > NECK_WIDTH_MM + EPS or row["net"] not in self.built_nets:
                continue
            layer = self.pcb.F_Cu if row["layer"] == "F.Cu" else self.pcb.B_Cu
            key = (uid, layer)
            a, b = [tuple(v + 100 for v in row[k]) for k in ("a", "b")]
            covered, pieces, own = self.exposed(key, a, b)
            length = math.dist(a, b)
            exposed_length = sum(d - c for c, d in pieces) * length
            own_length = sum(d - c for c, d in own) * length
            touches = sorted({self.graph.pads[k[0]].GetParentFootprint().GetReference() + "." +
                              self.graph.pads[k[0]].GetNumber() for k in self.graph.adj[key]
                              if k[1] == layer and k[0] in self.graph.pads})
            selected = []
            for path, step in ownership[uid]:
                c, d = [tuple(v + 100 for v in step[k]) for k in ("from_xy_mm", "to_xy_mm")]
                _, portions, _ = self.exposed(key, c, d)
                selected.append({
                    "path_id": path["id"], "conditional_screen_current_A": path["conditional_screen_current_A"],
                    "role": path["role"],
                    "selected_walk_uncovered_length_mm": rounded(sum(v - u for u, v in portions) * math.dist(c, d)),
                    "pieces_xy_mm": [[xy(interpolate(c, d, u)), xy(interpolate(c, d, v))] for u, v in portions],
                })
            inventory.append({
                "uuid": uid, "net": row["net"], "layer": row["layer"], "width_mm": row["width"],
                "from_xy_mm": row["a"], "to_xy_mm": row["b"], "total_drawn_length_mm": rounded(length),
                "drilled_out_centerline_mm": rounded(length - own_length),
                "covered_copper_centerline_mm": rounded(own_length - exposed_length),
                "uncovered_copper_centerline_mm": rounded(exposed_length),
                "coverage": covered,
                "uncovered_pieces": [{
                    "from_xy_mm": xy(interpolate(a, b, c)), "to_xy_mm": xy(interpolate(a, b, d)),
                    "length_mm": rounded((d - c) * length),
                    "full_width_1D_nominal_mOhm": rounded(foil_mohm((d - c) * length, row["width"])),
                } for c, d in pieces],
                "full_drawn_1D_nominal_mOhm": rounded(foil_mohm(length, row["width"])),
                "uncovered_full_width_1D_nominal_mOhm": rounded(foil_mohm(exposed_length, row["width"])),
                "directly_touching_pads": touches, "selected_walk_ownership": selected,
                "author_group_annotation_only": row.get("group"),
                "current_assignment": "Only selected_walk_ownership carries conditional cases; no whole-net/group current",
                "interpretation": "Centerline exposure and isolated full-width 1-D screen, not equivalent R or bottleneck proof",
            })
        return inventory

    def barrel_inventory(self, paths):
        selected = defaultdict(set)
        for path in paths:
            for step in path["walk"]:
                if step["kind"] == "barrel":
                    selected[step["owner_uuid"]].add(path["id"])
        return [{
            "uuid": uid, "owner_kind": self.item_kind(uid),
            "net": self.graph.items[uid].GetNetname(),
            "drill_mm": rounded(drill),
            "conditional_20C_mOhm": rounded(barrel_mohm(drill)),
            "conditional_60C_same_wall_mOhm": rounded(barrel_mohm(drill) * VIA_HOT_FACTOR),
            "selected_path_ids": sorted(selected[uid]),
            "author_group_annotation_only": self.records.get(uid, {}).get("group"),
            "interpretation": "Individual barrel inventory; no parallel division or equal-sharing assumption",
        } for uid, (drill, _) in sorted(self.barrels.items())]


def requested_paths(model):
    cases = [
        ("cell_vbat", "BT1.1", "Q3.3", "Cell positive to selector", 2),
        ("cell_vhi", "Q3.2", "Q1.2", "Selected cell supply to audio switch", 2),
        ("cell_vplus", "Q1.3", "L1.P$1", "Switched cell supply to inductor input", 2),
        ("cell_gnd", "U5.4", "R27.2", "Boost load return to system-side shunt land", 2),
        ("cell_prot_a2", "R27.1", "Q5.A2", "Protected return to one physical Q5 source exit; no sharing assumed", 2),
        ("cell_prot_c2", "R27.1", "Q5.C2", "Protected return alternate Q5 source exit; do not add parallel branches", 2),
        ("cell_neg_a1", "Q5.A1", "BT2.1", "Raw-negative return from one Q5 source exit", 2),
        ("cell_neg_c1", "Q5.C1", "BT2.1", "Raw-negative alternate Q5 exit; do not add parallel branches", 2),
        ("v5_to_bulk", "C28.1", "C19.1", "5 V distribution to amplifier bulk land", 1),
        ("v5_to_amp7", "C28.1", "U4.7", "5 V supply to actual amplifier supply pin", 1),
        ("v5_to_amp8", "C28.1", "U4.8", "5 V supply to alternate amplifier supply pin", 1),
        ("v5_return_thermal", "U4.THERMAL", "C27.2", "Actual amplifier ground to boost capacitor return", 1),
        ("v5_return_11", "U4.11", "C27.2", "Actual amplifier small ground-pin return", 1),
        ("v5_bulk_return", "C19.2", "C27.2", "Bulk-capacitor-endpoint return, not an internal amplifier bridge", 1),
        ("sw_escape", "U5.5", "L1.P$2", "Inductor switching/ripple path; RMS/peak current unqualified", None),
        ("input_cap_feed", "C26.1", "L1.P$1", "Input-capacitor feed; branch ripple/load split unsolved", None),
        ("vin_bias", "C26.1", "U5.3", "VIN bias/local-decoupling spur, NOT full inductor input current", None),
        ("feedback_ground", "R24.2", "C28.2", "Feedback ground pickoff; no automatic load-current assignment", None),
        ("protector_sense", "R26.2", "R27.2", "Sense pickoff; no automatic 2 A assignment", None),
        ("amp_local_ground11", "U4.11", "U4.THERMAL", "Small-pin local ground exit; internal sharing unknown", None),
    ]
    paths = [model.path(*case) for case in cases]
    for cap in ("C27", "C28"):
        paths += [
            model.path(f"{cap.lower()}_supply", "U5.6", cap + ".1", "Output-capacitor switching-current corridor"),
            model.path(f"{cap.lower()}_return", cap + ".2", "U5.4", "Output-capacitor switching return"),
        ]
    return paths


def roundtrips(paths, native_shorts):
    lookup = {p["id"]: p for p in paths}
    cases = []
    common = ["cell_vbat", "cell_vhi", "cell_vplus", "cell_gnd"]
    for pos, neg in itertools.product(("a2", "c2"), ("a1", "c1")):
        cases.append((f"cell_via_{pos}_{neg}", common + ["cell_prot_" + pos, "cell_neg_" + neg], [2, 3], 50))
    for supply, ret in itertools.product(("7", "8"), ("thermal", "11")):
        cases.append((f"5V_amp{supply}_{ret}", ["v5_to_amp" + supply, "v5_return_" + ret], [1], 100))
    cases.append(("5V_bulk_capacitor_endpoints", ["v5_to_bulk", "v5_bulk_return"], [1], 100))
    result = []
    for name, members, currents, target in cases:
        missing = [p for p in members if lookup[p]["status"] != "CONNECTED_CHOSEN_WALK"
                   or lookup[p]["resistance"] is None]
        record = {
            "id": name, "path_ids": members, "target_mV": target, "target_current_A": currents[0],
            "target_status": "NOT_DEMONSTRATED", "unavailable_path_ids": missing,
            "resistance": None, "current_cases": [],
            "connectivity_status": ("OPEN" if any(lookup[p]["status"] == "OPEN" for p in members) else
                                    "NOT_DEMONSTRATED" if missing else "CONNECTED_CONDITIONAL_SECTIONS"),
            "boundary": ("Copper contact-to-inductor and boost-ground-to-contact sections, with excluded "
                         "ON-state components between nets" if name.startswith("cell") else
                         "Paired supply/return at the named amplifier pins or both bulk-capacitor lands"),
        }
        if missing:
            record["reason"] = "OPEN or unmeasured section: no numerical round-trip total is reported"
        else:
            foil = sum(lookup[p]["resistance"]["foil_35um_20C_mOhm"] for p in members)
            via = sum(lookup[p]["resistance"]["barrels_conditional_25um_wall_20C_mOhm"] for p in members)
            record["resistance"] = resistance_record(foil, via)
            for current in currents:
                nominal, hot = current * (foil + via), current * (foil + via) * HOT_FACTOR
                record["current_cases"].append({
                    "current_A": current, "nominal_chosen_strip_drop_mV": rounded(nominal),
                    "requested_1p35x_drop_mV": rounded(hot),
                    "foil_hot_same_wall_barrels_drop_mV": rounded(current * (foil * HOT_FACTOR + via * VIA_HOT_FACTOR)),
                    "numerical_screen_vs_budget": ("INVALID_NATIVE_SHORTS" if native_shorts else
                                                   ("WITHIN" if hot <= target else "ABOVE") + "_CHOSEN_WALK_ONLY"),
                    "is_target_current": current == currents[0],
                })
            record["reason"] = ("Native shorts invalidate the electrical screen" if native_shorts else
                                "Numerical chosen-strip comparison only; actual equivalent drop and component behavior unqualified")
        result.append(record)
    return result


def rough_loop_area(supply, ground):
    if any(p["status"] != "CONNECTED_CHOSEN_WALK" for p in (supply, ground)):
        return {"area_mm2": None, "reason": "No complete selected copper loop"}
    steps = supply["walk"] + ground["walk"]
    if any(s["from_layer"] != "F.Cu" or s["to_layer"] != "F.Cu" for s in steps):
        return {"area_mm2": None, "reason": "Mixed-face path; a planar loop area would conceal layer separation"}
    points = [supply["walk_start_xy_mm"]]
    points.extend(s["to_xy_mm"] for s in supply["walk"])
    points.append(ground["walk_start_xy_mm"])
    points.extend(s["to_xy_mm"] for s in ground["walk"])
    cleaned = []
    for p in points:
        if not cleaned or math.dist(cleaned[-1], p) > EPS:
            cleaned.append(p)
    if len(cleaned) > 1 and math.dist(cleaned[0], cleaned[-1]) <= EPS:
        cleaned.pop()
    if len(cleaned) < 3:
        return {"area_mm2": None, "reason": "Degenerate loop polygon"}
    def cross(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    segments = list(zip(cleaned, cleaned[1:] + cleaned[:1]))
    for i, (a, b) in enumerate(segments):
        for j, (c, d) in enumerate(segments):
            if j <= i + 1 or (i == 0 and j == len(segments) - 1):
                continue
            values = (cross(a, b, c), cross(a, b, d), cross(c, d, a), cross(c, d, b))
            if (max(min(a[0], b[0]), min(c[0], d[0])) <= min(max(a[0], b[0]), max(c[0], d[0])) + EPS
                    and max(min(a[1], b[1]), min(c[1], d[1])) <= min(max(a[1], b[1]), max(c[1], d[1])) + EPS
                    and values[0] * values[1] <= 0 and values[2] * values[3] <= 0):
                return {"area_mm2": None, "reason": "Selected loop crosses/touches itself; shoelace area would be misleading"}
    area = abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in segments)) / 2
    return {"area_mm2": rounded(area), "polygon_xy_mm": cleaned,
            "method": "Simple all-F chosen-walk polygon, closed by straight cap/IC pin chords. "
                      "Internal component paths are unknown; this is NOT an inductance or magnetic-field area."}


def capacitor_comparison(before, after):
    result = []
    for cap in ("C27", "C28"):
        record = {"capacitor": cap}
        for label, model in (("source", before), ("candidate", after)):
            variants = {}
            for constraint in (None, "F.Cu"):
                paths = [
                    model.path(f"{cap}_{label}_positive", "U5.6", cap + ".1",
                               "Hot-loop positive; pulse/RMS current not assigned", layer=constraint),
                    model.path(f"{cap}_{label}_return", cap + ".2", "U5.4",
                               "Hot-loop ground; pulse/RMS current not assigned", layer=constraint),
                ]
                connected = all(p["status"] == "CONNECTED_CHOSEN_WALK" for p in paths)
                variants["unrestricted" if constraint is None else "all_F"] = {
                    "paths": paths, "connected": connected,
                    "sum_paired_xy_walk_mm": rounded(sum(p["xy_length_including_pad_travel_mm"] for p in paths))
                    if connected else None,
                    "barrel_traversals": sum(p["barrel_traversals"] for p in paths) if connected else None,
                    "rough_area": rough_loop_area(*paths),
                }
            record[label] = variants
        old, new = record["source"]["unrestricted"], record["candidate"]["unrestricted"]
        record["paired_xy_change_mm"] = (rounded(new["sum_paired_xy_walk_mm"] - old["sum_paired_xy_walk_mm"])
                                         if old["connected"] and new["connected"] else None)
        record["comparison_limits"] = "Same finite-pad-walk method on both native boards; not authored group lengths. "
        record["comparison_limits"] += "Each capacitor is evaluated separately; no capacitance or parallel-branch sums."
        result.append(record)
    return result


def neck_focus(necks, paths):
    groups = {
        "U5_SW_minimum_escape": {"U5.5"},
        "output_VAMP_small_pin_exits": {"U5.6"},
        "output_GND_small_pin_exits": {"U5.4"},
        "Q5_pad_adjacent_fine_including_bias_branches": {"Q5.A1", "Q5.C1", "Q5.A2", "Q5.C2"},
        "amplifier_small_ground_exits": {"U4.11", "U4.3", "U4.15"},
    }
    result = {}
    for name, pads in groups.items():
        records = ([n for n in necks if n["net"] == "BOOST_SW"] if name == "U5_SW_minimum_escape" else
                   [n for n in necks if pads.intersection(n["directly_touching_pads"])])
        uncovered = [n for n in records if n["uncovered_copper_centerline_mm"] > EPS]
        result[name] = {
            "pads": sorted(pads), "track_uuids": [n["uuid"] for n in records],
            "minimum_exposed_drawn_width_mm": min((n["width_mm"] for n in uncovered), default=None),
            "drawn_length_mm": rounded(sum(n["total_drawn_length_mm"] for n in records)),
            "uncovered_centerline_inventory_mm": rounded(sum(n["uncovered_copper_centerline_mm"] for n in records)),
            "status": "EXPOSED_FINE_COPPER" if uncovered else "NO_EXPOSED_FINE_CENTERLINE_IN_DIRECTLY_TOUCHING_TRACKS",
            "scope": ("Whole actual BOOST_SW net, including the under-package continuation beyond the pad-adjacent segment. "
                      if name == "U5_SW_minimum_escape" else "Direct native pad contacts among tracks <=0.35 mm. ") +
                     "Inventory, not a series-path sum. "
                     "Inspect per-path ownership and remaining escape tracks before calling this a bottleneck.",
        }
    main_ids = {p["id"] for p in paths if p["conditional_screen_current_A"] is not None}
    for path in paths:
        owned = [(n, owner) for n in necks for owner in n["selected_walk_ownership"]
                 if owner["path_id"] == path["id"] and owner["selected_walk_uncovered_length_mm"] > EPS]
        path["exposed_fine_walk_pieces"] = [
            {"track_uuid": n["uuid"], "width_mm": n["width_mm"], **owner} for n, owner in owned]
        path["minimum_exposed_drawn_track_width_mm"] = min((n["width_mm"] for n, _ in owned), default=None)
        path["minimum_exposed_width_scope"] = "Selected uncovered walk pieces on drawn tracks <=0.35 mm; "
        path["minimum_exposed_width_scope"] += "null does not prove the absence of a pad/2-D bottleneck"
    result["actual_narrow_pieces_on_main_chosen_walks"] = [
        {"track_uuid": n["uuid"], "width_mm": n["width_mm"], **owner}
        for n in necks for owner in n["selected_walk_ownership"]
        if owner["path_id"] in main_ids and owner["selected_walk_uncovered_length_mm"] > EPS
    ]
    return result


def markdown(report):
    lines = [
        "# Printed-bell actual-copper path measurements", "",
        "**Screening only; copper-drop targets remain NOT_DEMONSTRATED.**",
        "A connected row has a finite sampled copper walk, not a measured/equivalent resistance. "
        "OPEN rows have no invented round-trip total.", "",
        f"Candidate PCB SHA-256: `{report['candidate_pcb_sha256']}`",
        f"Source PCB SHA-256: `{report['source_pcb_sha256']}`",
        f"Analyzer SHA-256: `{report['tool_sha256']}`",
        f"KiCad `{report['versions']['kicad']}`; Python `{report['versions']['python']}`; "
        f"numpy `{report['versions']['numpy']}`. E04/#4, E05/#5, E07/#7.", "",
        "## Connected current corridors", "",
        "| Path | Status | XY incl. pad travel (mm) | Barrels | Nominal chosen-strip (mOhm) |",
        "|---|---|---:|---:|---:|",
    ]
    for p in report["paths"]:
        resistance = p["resistance"]
        value = f"{resistance['nominal_chosen_strip_mOhm']:.2g}" if resistance else "-"
        length = f"{p['xy_length_including_pad_travel_mm']:.3g}" if "xy_length_including_pad_travel_mm" in p else "-"
        lines.append(f"| {p['from']} -> {p['to']} | {p['status']} | {length} | {p.get('barrel_traversals', '-')} | {value} |")
    lines += ["", "## Paired copper-only budgets", "",
              "| Conditional loop | Case (A) | Nominal / 1.35x drop (mV) | Budget at target current | Result |",
              "|---|---:|---:|---:|---|"]
    for loop in report["roundtrips"]:
        if not loop["current_cases"]:
            lines.append(f"| {loop['id']} | - | - | {loop['target_mV']} mV @ {loop['target_current_A']} A | "
                         f"NOT_DEMONSTRATED: {', '.join(loop['unavailable_path_ids'])} |")
        for case in loop["current_cases"]:
            lines.append(f"| {loop['id']} | {case['current_A']} | "
                         f"{case['nominal_chosen_strip_drop_mV']:.2g} / {case['requested_1p35x_drop_mV']:.2g} | "
                         f"{loop['target_mV']} mV @ {loop['target_current_A']} A | "
                         f"{case['numerical_screen_vs_budget']}; target NOT_DEMONSTRATED |")
    lines += ["", "Cell Q5 alternatives are separate whole-current chosen walks, never parallel sums or equal-sharing claims. "
              "3 A is sensitivity, not an approved operating current. An above-budget chosen strip does not prove "
              "the actual parallel-copper network fails; a below-budget strip does not qualify it.",
              "", "Contacts and FET losses are unknown and excluded. The separate nominal 33 mOhm shunt alone "
              "adds 66 mV at 2 A or 99 mV at 3 A, before tolerance/temperature.", "",
              "## Boost capacitor native source-to-candidate comparison", "",
              "| Capacitor | Source paired XY / vias | Candidate paired XY / vias | Native all-F source -> candidate | Candidate rough all-F area |",
              "|---|---:|---:|---|---:|"]
    for cap in report["capacitor_loop_comparisons"]:
        def pair(label):
            value = cap[label]["unrestricted"]
            return (f"{value['sum_paired_xy_walk_mm']:.3g} mm / {value['barrel_traversals']}"
                    if value["connected"] else "NOT_DEMONSTRATED")
        old_f = all(p["native_connected"] for p in cap["source"]["all_F"]["paths"])
        new_f = all(p["native_connected"] for p in cap["candidate"]["all_F"]["paths"])
        area = cap["candidate"]["all_F"]["rough_area"]["area_mm2"]
        lines.append(f"| {cap['capacitor']} | {pair('source')} | {pair('candidate')} | {old_f} -> {new_f} | "
                     + (f"{area:.3g} mm2 |" if area is not None else "not meaningful/available |"))
    lines += ["", "Loop lengths include finite pad travel; they are not the frozen review's pad-as-region numbers. "
              "Area is only a simple all-F walk polygon with straight IC/capacitor pin closures, not an inductance model. "
              "Each capacitor is separate; capacitances/parallel branches are not added.", "",
              "## Exposed fine copper", "",
              "| Native pad-adjacent inventory | Minimum exposed width (mm) | Total drawn (mm) | Uncovered centerline (mm) |",
              "|---|---:|---:|---:|"]
    for name, focus in report["neck_focus"].items():
        if isinstance(focus, dict):
            width = focus["minimum_exposed_drawn_width_mm"]
            lines.append(f"| {name} | {width if width is not None else '-'} | {focus['drawn_length_mm']:.3g} | "
                         f"{focus['uncovered_centerline_inventory_mm']:.3g} |")
    lines += ["", "Lengths here are inventories, not series resistance. The JSON contains exact native owners, "
              "covered/exposed intervals, actual narrow pieces on each selected main walk, and conditional currents. "
              "Pad/annulus/broader-trace coverage is subtracted; drilled-out centerline is not counted as copper. "
              "R24/R26/VIN bias and ripple branches have no automatic 2 A load.", "",
              "## Counts and unresolved gates", "",
              f"Candidate: {report['counts']['candidate']}. Source: {report['counts']['source']}.",
              f"Candidate native shape shorts: {len(report['native_shorts'])}; "
              f"geometry-walk diagnostics: {len(report['geometry_diagnostics']['candidate'])}.",
              "The complete diagnostic and input-hash inventories are in the JSON. Native shape connectivity "
              "is not DRC; previous QSPI/GND losses, USB findings, unfinished routing and parent-review gates remain open.",
              "", "## Method and assumptions", ""]
    lines.extend("- " + note for note in report["assumptions"])
    lines += ["", "Inputs were hash-checked before and after the calculation; this is not a cross-process generator lock. "
              "Rerun only after a coherent final build. These reports do not alter the parent-owned review.", ""]
    return "\n".join(lines)


def write_reports(report, bindings):
    directory = OUTPUT / "reports"
    directory.mkdir(parents=True, exist_ok=True)
    payloads = {
        "power-path-measurements.json": json.dumps(report, indent=2, allow_nan=False) + "\n",
        "power-path-measurements.md": markdown(report),
    }
    temporary = []
    try:
        for name, content in payloads.items():
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                             dir=directory, prefix=name + ".", suffix=".tmp", delete=False) as stream:
                temporary.append((Path(stream.name), directory / name))
                stream.write(content)
        assert_unchanged(bindings)
        for path, target in temporary:
            path.replace(target)
    finally:
        for path, _ in temporary:
            path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pcb-sha256", required=True,
                        help="Exact SHA-256 of the coherent FINAL new-package PCB; refuses stale/in-flight inputs")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-fA-F]{64}", args.pcb_sha256):
        parser.error("--pcb-sha256 must be exactly 64 hexadecimal digits")
    sys.dont_write_bytecode = True
    import check_printed_bell_power_rework as check
    global np
    import numpy as np
    route = check.generator()
    bindings, build = coherent_inputs(check, route, args.pcb_sha256.lower())
    before_records, after_records = route_inventory(check, SOURCE), route_inventory(check, OUTPUT)
    require(build["tracks"] == sum(r["kind"] == "segment" for r in after_records.values())
            and build["vias"] == sum(r["kind"] == "via" for r in after_records.values()),
            "Routing-build native counts differ")
    assert_unchanged(bindings)
    pcb = check.native_api(route)
    before, after = (NativeWalk(check, pcb, SOURCE, before_records),
                     NativeWalk(check, pcb, OUTPUT, after_records))
    print("Measuring connected candidate power walks", flush=True)
    paths = requested_paths(after)
    print("Comparing output-capacitor loops", flush=True)
    comparison = capacitor_comparison(before, after)
    print("Measuring uncovered neck intervals", flush=True)
    necks = after.necks(paths)
    def counts(model):
        nets = model.graph.nets()
        return {"physical_pads": len(model.graph.pads),
                "tracks": sum(r["kind"] == "segment" for r in model.records.values()),
                "vias": sum(r["kind"] == "via" for r in model.records.values()),
                "physical_net_islands": sum(len(n["islands"]) for n in nets),
                "multi_pad_nets_not_complete": sum(n["status"] in ("partial", "unrouted") for n in nets)}
    report = {
        "schema_version": 1, "status": "SCREENING_ONLY_TARGETS_NOT_DEMONSTRATED",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_package": str(OUTPUT.relative_to(ROOT)), "source_package": str(SOURCE.relative_to(ROOT)),
        "candidate_pcb_sha256": args.pcb_sha256.lower(), "source_pcb_sha256": sha(SOURCE / "handbell.kicad_pcb"),
        "tool_sha256": sha(__file__), "input_bindings": bindings,
        "versions": {"kicad": pcb.GetBuildVersion(), "python": sys.version.split()[0], "numpy": np.__version__},
        "coordinate_convention": "mm, native PCB XY minus (100,100); F.Cu/B.Cu preserved",
        "assumptions": ASSUMPTIONS,
        "parameters": {"rho_20C_ohm_mm2_per_m": RHO, "nominal_foil_um": FOIL_MM * 1000,
                       "conditional_wall_plating_um": WALL_MM * 1000, "board_thickness_mm": BOARD_MM,
                       "via_0p30mm_conditional_mOhm": rounded(barrel_mohm(.30)),
                       "requested_30um_60C_multiplier": HOT_FACTOR,
                       "same_wall_via_60C_rho_multiplier": VIA_HOT_FACTOR,
                       "strip_slice_max_mm": SLICE_MM, "fine_track_inventory_max_width_mm": NECK_WIDTH_MM},
        "counts": {"source": counts(before), "candidate": counts(after)},
        "paths": paths, "roundtrips": roundtrips(paths, after.graph.shorts),
        "capacitor_loop_comparisons": comparison, "exposed_neck_inventory": necks,
        "conditional_barrel_inventory": after.barrel_inventory(paths),
        "neck_focus": neck_focus(necks, paths), "native_shorts": after.graph.shorts,
        "geometry_diagnostics": {"source": before.issues, "candidate": after.issues},
        "excluded_series_elements": {
            "contacts": "Unknown contact/solder-interface resistance; not in copper budget",
            "FETs": "Q3/Q1/Q5 ON-state, gate bias, temperature, SOA and protection behavior not solved",
            "R27_shunt": {"nominal_mOhm": 33, "drop_at_2A_mV": 66, "drop_at_3A_mV": 99,
                          "note": "Separate intentional resistance; tolerance and self-heating not modeled"},
            "other": "Converter/amplifier internals, inductor winding and capacitor ESR excluded",
        },
        "open_gates": [
            "Every OPEN or NOT_DEMONSTRATED requested path; no round-trip extrapolation over absent copper",
            "Current distribution, terminal injection, neck crowding and Q5 parallel-barrel sharing",
            "Finished minimum foil/width/plating, thermal, electrical, component and fault qualification",
            "Parent native review including prior QSPI/GND losses, shorts/clearances and USB findings",
            "Exact mechanical rebind; no fabrication, purchase or live-cell approval",
        ],
        "tracking": ["E04/#4", "E05/#5", "E07/#7"],
    }
    assert_unchanged(bindings)
    write_reports(report, bindings)
    print(json.dumps({"status": report["status"], "pcb_sha256": report["candidate_pcb_sha256"],
                      "path_status_counts": dict(Counter(p["status"] for p in paths)),
                      "reports": [str(OUTPUT / "reports" / ("power-path-measurements." + ext))
                                  for ext in ("json", "md")]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
