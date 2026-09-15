# SPDX-License-Identifier: MIT
"""Released, separate critical-routing candidate. Never rewrite printed-bell-front."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import heapq
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import uuid

import numpy as np
from kicad_sexpr import apply_edits, load, loads

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "hardware" / "handbell" / "iterations" / "printed-bell-front"
OUTPUT = SOURCE.parent / "printed-bell-routing"
RELEASE = SOURCE / "routing" / "mechanical-release.json"
RELEASE_COMMIT = "6e7ef9ef4dd1f6611695e73227630fdc5c8dae7a"
RELEASE_GIT_PATH = "hardware/handbell/iterations/printed-bell-front/routing/mechanical-release.json"
MECHANICAL_GIT_BASE = "mechanical/studies/2026-09-13-printed-bell/"
SPEC = importlib.util.spec_from_file_location("front_routing_preparation", SOURCE / "routing" / "prepare.py")
prep = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prep)
GRID = .05
CLEARANCE = .2
FINE = .1778
CLI = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin" / "kicad-cli.exe"
SERVICE_LABELS = (
    ("+ POS", 15.7, 11, .9), ("- NEG", -15.7, 11, .9),
    ("< T8 BUTTON END", 0, 10.5, .8),
    ("1S Li-ion", 0, -15.6, 1), ("4.2V ONLY", 0, -14, 1),
    ("NO PRIMARY", 0, -12.1, 1), ("CR123A", 0, -10.5, 1),
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value, indent=2)+"\n", encoding="utf-8")


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "digital-handbell/printed-routing/"+name))


def released_git_bytes(path):
    return subprocess.check_output(["git", "show", RELEASE_COMMIT+":"+path], cwd=ROOT)


def release_objects():
    paths = {"release": RELEASE_GIT_PATH}
    paths.update({key: MECHANICAL_GIT_BASE+name for key, name in (
        ("native", "printed-bell.FCStd"), ("artifact_manifest", "artifact-manifest.json"),
        ("fit_report", "fit-report.json"), ("completion", "completion.json"), ("review_status", "review-status.json"))})
    return {key: {"path": path, "raw": released_git_bytes(path)} for key, path in paths.items()}


def verify_release():
    objects = release_objects()
    hashes = {key: hashlib.sha256(value["raw"]).hexdigest() for key, value in objects.items()}
    prep.require(hashes["release"] == "1ec81f6dfede4c040a78f164c91c21a3d77a3ec02ce7b7284b89bad5ddb217e5",
                 "Committed authorization record changed")
    release = json.loads(objects["release"]["raw"])
    prep.require(release["status"] == "AUTHORIZED_TO_BEGIN_CRITICAL_ROUTING_NOT_FABRICATION", "No explicit copper release")
    prep.require(release["mechanical_completion_token"] == "578113de769f41d193bd85828117fe36", "Wrong release token")
    for key, name in (("placement_sha256", "placement-manifest.json"), ("pcb_sha256", "handbell.kicad_pcb"),
                      ("schematic_sha256", "handbell.kicad_sch"), ("contact_sha256", "battery-contact-interface.json")):
        prep.require(sha(SOURCE / name) == release[key] == prep.EXPECTED[name], "Release/source mismatch: "+name)
    artifact = json.loads(objects["artifact_manifest"]["raw"])
    fit = json.loads(objects["fit_report"]["raw"])
    completion = json.loads(objects["completion"]["raw"])
    status = json.loads(objects["review_status"]["raw"])
    prep.require(hashes["artifact_manifest"] == release["mechanical_artifact_manifest_sha256"] ==
                 completion["artifact_manifest_sha256"], "Committed mechanical manifest binding mismatch")
    prep.require(hashes["native"] == release["mechanical_native_sha256"] ==
                 artifact["artifacts"]["printed-bell.FCStd"]["sha256"], "Committed native binding mismatch")
    prep.require(hashes["fit_report"] == artifact["artifacts"]["fit-report.json"]["sha256"],
                 "Committed fit-report binding mismatch")
    prep.require(completion["token"] == status["token"] == release["mechanical_completion_token"],
                 "Committed mechanical completion token mismatch")
    prep.require(completion["input_hashes"] == artifact["input_hashes"] == fit["input"]["sha256"],
                 "Committed mechanical input bindings disagree")
    for key, field in (("placement", "placement_sha256"), ("pcb", "pcb_sha256"),
                       ("schematic", "schematic_sha256"), ("contact_interface", "contact_sha256")):
        prep.require(fit["input"]["sha256"][key] == release[field], "Committed fit used different interface: "+key)
    prep.require(fit["routing_interface"]["mechanical_freeze_recommended"] and
                 fit["routing_interface"]["mechanically_bound_to_final_all_front_manifest"] and
                 fit["routing_interface"]["outline_mounts_usb_contacts_may_change_without_rebind"] is False,
                 "Committed fit did not freeze these exact interfaces")
    review = release["mechanical_interface_review"]
    prep.require(review["mechanical_freeze_recommended"] and review["exact_current_input_binding"]
                 and review["reported_static_material_overlaps"] == 0 and review["reported_service_paths_clear"],
                 "Mechanical release gates not satisfied")
    native_evidence = {
        "source": "Explicit parent-pinned immutable initial routing release; no mutable mechanical-root or HEAD lookup",
        "git_commit": RELEASE_COMMIT,
        "objects": {key: {"git_path": value["path"], "sha256": hashes[key]} for key, value in objects.items()},
        "stage1_interfaces_verified_exact": True,
        "mutable_mechanical_root_not_consumed": True,
        "cosmetic_revision_scope": "Parent reports shell retaining joints/lugs only; PCB M2/USB/contacts/electronic poses remain frozen",
        "mechanical_rebind_required": True,
    }
    return release, native_evidence


def source_bindings():
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(SOURCE.rglob("*")) if p.is_file()
            and p != RELEASE and "__pycache__" not in str(p) and not p.name.endswith(".lck")}


def segment_distance(a, b, p):
    return prep.point_segment_distance(p, a, b)


class Router:
    def __init__(self, manifest, board):
        self.pads, self.holes = prep.read_pads(board)
        for fp in board.children("footprint"):
            for i, node in enumerate(fp.children("pad")):
                key = f'{fp.properties()["Reference"]}.{node.atoms()[1]}#{i}'
                found = next((p for p in self.pads if p["id"] == key), None)
                if found:
                    found["uuid"] = node.value("uuid")
        self.lookup = {}
        for p in self.pads:
            self.lookup.setdefault((p["reference"], p["number"]), []).append(p)
        self.outline = manifest["board"]["outline_common_xy_mm"]
        self.metal = prep.contact_metal_reservations(json.loads((SOURCE / "battery-contact-interface.json").read_text()))
        self.tracks, self.vias, self.results = [], [], []

    def pad(self, ref, number):
        return self.lookup[(ref, number)][0]

    def add_segment(self, a, b, net, layer, width, group):
        a, b = [round(v, 6) for v in a], [round(v, 6) for v in b]
        if math.dist(a, b) < .000001:
            return
        item = {"a": a, "b": b, "net": net, "layer": layer, "width": width, "group": group}
        if not any(p["net"] == net and p["layer"] == layer and p["width"] == width
                   and {tuple(p["a"]), tuple(p["b"])} == {tuple(a), tuple(b)} for p in self.tracks):
            self.tracks.append(item)

    def add_via(self, xy, net, diameter=.6, drill=.3, group="automatic off-pad transition"):
        xy = [round(v, 6) for v in xy]
        if not any(v["xy"] == xy and v["net"] == net for v in self.vias):
            self.vias.append({"xy": xy, "net": net, "diameter": diameter, "drill": drill, "group": group})

    def setup_escapes(self):
        plan = json.loads((SOURCE / "routing" / "routing-preparation.json").read_text())
        for v in plan["thermal_via_candidates"]:
            self.add_via(v["xy_mm"], "GND", v["diameter_mm"], v["drill_mm"],
                         v["reference"]+" filled/capped thermal via process gate")
        for ref in ("IC1", "U4"):
            points = [v["xy_mm"] for v in plan["thermal_via_candidates"] if v["reference"] == ref]
            for a in points:
                for axis in (0, 1):
                    others = [p for p in points if p[1-axis] == a[1-axis] and p[axis] > a[axis]]
                    if others:
                        self.add_segment(a, min(others, key=lambda p: p[axis]), "GND", "B.Cu", .6,
                                         ref+" local thermal mesh; not a central high-current return")
        for v in plan["Q5_source_fanout_candidates"]:
            self.add_via(v["via_xy_mm"], v["net"], v["diameter_mm"], v["drill_mm"], "Q5 outside source escape")
            self.add_segment(v["pad_xy_mm"], v["via_xy_mm"], v["net"], "F.Cu", FINE, "Q5 bounded source neck")
        for bus in plan["Q5_source_bus_candidates"]:
            self.add_segment(*bus["candidate_polyline_xy_mm"], bus["net"], "B.Cu", .6, "Q5 separate source bus")

    def local_grid(self, a, b, margin):
        xmin = max(-23, math.floor((min(a[0], b[0])-margin)/GRID)*GRID)
        ymin = max(-27.5, math.floor((min(a[1], b[1])-margin)/GRID)*GRID)
        xmax = min(23, math.ceil((max(a[0], b[0])+margin)/GRID)*GRID)
        ymax = min(22, math.ceil((max(a[1], b[1])+margin)/GRID)*GRID)
        return xmin, ymin, np.arange(xmin, xmax+GRID/2, GRID), np.arange(ymin, ymax+GRID/2, GRID)

    def masks(self, net, width, xs, ys, allow_vias):
        ny, nx = len(ys), len(xs)
        masks = np.zeros((2, ny, nx), dtype=bool)
        X, Y = np.meshgrid(xs, ys)
        # Polygon containment, including the exact contact tabs and USB tongue.
        inside = np.zeros((ny, nx), dtype=bool)
        for a, b in zip(self.outline, self.outline[1:]+self.outline[:1]):
            if a[1] != b[1]:
                inside ^= ((Y > min(a[1], b[1])) & (Y <= max(a[1], b[1])) &
                           (X < (b[0]-a[0])*(Y-a[1])/(b[1]-a[1])+a[0]))
        masks[:] = ~inside

        def box_indices(xmin, ymin, xmax, ymax):
            i0, i1 = max(0, int(math.floor((xmin-xs[0])/GRID))), min(nx, int(math.ceil((xmax-xs[0])/GRID))+1)
            j0, j1 = max(0, int(math.floor((ymin-ys[0])/GRID))), min(ny, int(math.ceil((ymax-ys[0])/GRID))+1)
            return i0, i1, j0, j1

        def shape(mask, p, radius):
            angle = math.radians(p["angle_deg"])
            w, h = p["size"]
            ew, eh = abs(math.cos(angle))*w+abs(math.sin(angle))*h, abs(math.sin(angle))*w+abs(math.cos(angle))*h
            if p["shape"] == "custom":
                points = [q for poly in p["polygons"] for q in poly]
                xmin, xmax = min(q[0] for q in points), max(q[0] for q in points)
                ymin, ymax = min(q[1] for q in points), max(q[1] for q in points)
            else:
                xmin, xmax = p["center"][0]-ew/2, p["center"][0]+ew/2
                ymin, ymax = p["center"][1]-eh/2, p["center"][1]+eh/2
            i0, i1, j0, j1 = box_indices(xmin-radius, ymin-radius, xmax+radius, ymax+radius)
            if i1 <= i0 or j1 <= j0:
                return
            xx, yy = np.meshgrid(xs[i0:i1]-p["center"][0], ys[j0:j1]-p["center"][1])
            lx, ly = xx*math.cos(angle)-yy*math.sin(angle), xx*math.sin(angle)+yy*math.cos(angle)
            if p["shape"] == "circle":
                blocked = xx*xx+yy*yy <= (w/2+radius)**2
            elif p["shape"] == "custom":
                blocked = np.ones_like(xx, dtype=bool)  # conservative complete custom-copper bounding box
            else:
                blocked = np.maximum(np.abs(lx)-w/2, 0)**2+np.maximum(np.abs(ly)-h/2, 0)**2 <= radius**2
            mask[j0:j1, i0:i1] |= blocked

        def line(mask, a, b, radius):
            i0, i1, j0, j1 = box_indices(min(a[0], b[0])-radius, min(a[1], b[1])-radius,
                                        max(a[0], b[0])+radius, max(a[1], b[1])+radius)
            if i1 <= i0 or j1 <= j0:
                return
            xx, yy = np.meshgrid(xs[i0:i1], ys[j0:j1])
            dx, dy = b[0]-a[0], b[1]-a[1]
            t = np.clip(((xx-a[0])*dx+(yy-a[1])*dy)/(dx*dx+dy*dy), 0, 1) if dx or dy else 0
            mask[j0:j1, i0:i1] |= (xx-a[0]-t*dx)**2+(yy-a[1]-t*dy)**2 <= radius*radius

        for edge_a, edge_b in zip(self.outline, self.outline[1:]+self.outline[:1]):
            for mask in masks:
                line(mask, edge_a, edge_b, width/2+.25)
        for pad in self.pads:
            if pad["net"] != net:
                for i, layer in enumerate(("F.Cu", "B.Cu")):
                    if layer in pad["layers"]:
                        shape(masks[i], pad, width/2+CLEARANCE+.002)
        for hole in self.holes:
            for mask in masks:
                shape(mask, hole, width/2+.25+.002)
        for metal in self.metal:
            if metal["net"] != net:
                shape(masks[1], metal, width/2+CLEARANCE+.002)
        if net == "GND" and width >= .4:
            masks[1, np.abs(ys) < 7, :] = True  # no power return through the central B neck
        for track in self.tracks:
            if track["net"] != net:
                line(masks[1 if track["layer"] == "B.Cu" else 0], track["a"], track["b"], (track["width"]+width)/2+CLEARANCE+.003)
        for via in self.vias:
            if via["net"] != net:
                for mask in masks:
                    shape(mask, {"shape": "circle", "center": via["xy"], "angle_deg": 0,
                                 "size": [via["diameter"]]*2}, width/2+CLEARANCE+.003)
        via_mask = np.ones_like(masks[0])
        if allow_vias:
            via_mask = masks[0] | masks[1]
            for pad in self.pads:
                shape(via_mask, pad, .3+(CLEARANCE+.005 if pad["net"] != net else .1))
            for hole in self.holes:
                shape(via_mask, hole, .3+.25+.005)
            for metal in self.metal:
                shape(via_mask, metal, .3+CLEARANCE+.005)
            for via in self.vias:
                shape(via_mask, {"shape": "circle", "center": via["xy"], "angle_deg": 0,
                                "size": [via["diameter"]]*2}, .3+CLEARANCE+.005)
            for track in self.tracks:
                if track["net"] != net:
                    line(via_mask, track["a"], track["b"], track["width"]/2+.3+CLEARANCE+.005)
        return masks, via_mask

    def search(self, a, b, net, width, allow_vias=False, margin=3, expansion_limit=220000, endpoint_layers=(0, 0)):
        self.last_search_statistics = {"status": "building_masks", "expanded": 0, "limit": expansion_limit}
        xmin, ymin, xs, ys = self.local_grid(a, b, margin)
        masks, via_mask = self.masks(net, width, xs, ys, allow_vias)
        ny, nx = masks.shape[1:]
        def closest(p, layer):
            x, y = round((p[0]-xmin)/GRID), round((p[1]-ymin)/GRID)
            options = [(x+dx, y+dy) for dx in range(-2, 3) for dy in range(-2, 3)
                       if 0 <= x+dx < nx and 0 <= y+dy < ny and not masks[layer, y+dy, x+dx]]
            return min(options, key=lambda q: math.dist([xs[q[0]], ys[q[1]]], p)) if options else None
        start, goal = closest(a, endpoint_layers[0]), closest(b, endpoint_layers[1])
        if start is None or goal is None:
            self.last_search_statistics.update(status="endpoint_unavailable", start_available=start is not None,
                                               goal_available=goal is not None)
            return None
        def encode(x, y, layer):
            return (layer*ny+y)*nx+x
        def decode(k):
            layer, rem = divmod(k, nx*ny)
            y, x = divmod(rem, nx)
            return x, y, layer
        initial, target = encode(*start, endpoint_layers[0]), encode(*goal, endpoint_layers[1])
        costs = {initial: 0.0}
        previous = {}
        heap = [(0, initial)]
        directions = ((1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1),
                      (1, 1, 1.414214), (1, -1, 1.414214), (-1, 1, 1.414214), (-1, -1, 1.414214))
        count = 0
        closed = set()
        while heap:
            _, current = heapq.heappop(heap)
            if current in closed:
                continue
            if current == target:
                self.last_search_statistics.update(status="found", expanded=count)
                nodes = [current]
                while current != initial:
                    current = previous[current]
                    nodes.append(current)
                result = [[float(xs[x]), float(ys[y]), layer] for x, y, layer in map(decode, nodes[::-1])]
                return [[*a, endpoint_layers[0]], *result, [*b, endpoint_layers[1]]]
            closed.add(current)
            count += 1
            if count > expansion_limit:
                self.last_search_statistics.update(status="expansion_limit", expanded=count)
                return None
            x, y, layer = decode(current)
            neighbors = []
            for dx, dy, weight in directions:
                xx, yy = x+dx, y+dy
                if not (0 <= xx < nx and 0 <= yy < ny) or masks[layer, yy, xx]:
                    continue
                if dx and dy and (masks[layer, yy, x] or masks[layer, y, xx]):
                    continue
                neighbors.append((xx, yy, layer, weight*(1.06 if layer else 1)))
            if allow_vias and not via_mask[y, x]:
                neighbors.append((x, y, 1-layer, 80))
            for xx, yy, ll, step in neighbors:
                node = encode(xx, yy, ll)
                score = costs[current]+step
                if score < costs.get(node, math.inf):
                    costs[node] = score
                    previous[node] = current
                    dx, dy = abs(goal[0]-xx), abs(goal[1]-yy)
                    heuristic = max(dx, dy)+.414214*min(dx, dy)+(80 if ll != endpoint_layers[1] else 0)
                    heapq.heappush(heap, (score+heuristic, node))
        self.last_search_statistics.update(status="no_path_in_masked_domain", expanded=count)
        return None

    def add_path(self, path, net, width, group):
        simplified = []
        for p in path:
            if simplified and math.dist(p[:2], simplified[-1][:2]) < 1e-8 and p[2] == simplified[-1][2]:
                continue
            if len(simplified) >= 2:
                a, b = simplified[-2:]
                dx1, dy1, dx2, dy2 = b[0]-a[0], b[1]-a[1], p[0]-b[0], p[1]-b[1]
                if a[2] == b[2] == p[2] and abs(dx1*dy2-dy1*dx2) < 1e-8 and dx1*dx2+dy1*dy2 >= 0:
                    simplified.pop()
            simplified.append(p)
        for a, b in zip(simplified, simplified[1:]):
            if a[2] != b[2]:
                self.add_via(a[:2], net, group=group+" off-pad layer transition")
            else:
                self.add_segment(a[:2], b[:2], net, "B.Cu" if a[2] else "F.Cu", width, group)

    def connection(self, a, b, group, width=FINE, allow_vias=True, forced=False):
        prep.require(a["net"] and a["net"] == b["net"], "Net-crossing routing request")
        record = {"from": a["id"], "to": b["id"], "from_uuid": a["uuid"], "to_uuid": b["uuid"],
                  "net": a["net"], "group": group, "width_mm": width, "forced_F_return": forced}
        old_tracks, old_vias = len(self.tracks), len(self.vias)
        path = None
        for margin, vias in ((3, False), (6, False), (4, allow_vias)):
            if path is None:
                path = self.search(a["center"], b["center"], a["net"], width, vias, margin)
        if path:
            self.add_path(path, a["net"], width, group)
            record.update(status="routed_endpoint_pair_pending_native_validation",
                          added_tracks=len(self.tracks)-old_tracks, added_vias=len(self.vias)-old_vias,
                          path_length_mm=round(sum(math.dist(p[:2], q[:2]) for p, q in zip(path, path[1:])), 6))
        else:
            record["status"] = "unrouted_no_safe_path_found_in_bounded_search"
        self.results.append(record)
        print(record["status"], group, a["id"], b["id"], flush=True)
        return bool(path)

    def wide_connection(self, a, b, group, width=.6):
        # Only the native small lands get a bounded fine neck; the body route is wider.
        at, av = len(self.tracks), len(self.vias)
        def escapes(p, towards):
            choices = [(p["center"], None)]
            for radius in (.7, 1.0, 1.3):
                for angle in range(0, 360, 45):
                    rad = math.radians(angle)
                    xy = [p["center"][0]+radius*math.cos(rad), p["center"][1]+radius*math.sin(rad)]
                    choices.append((xy, radius))
            return sorted(choices, key=lambda t: (math.dist(t[0], towards), t[1] or 0))
        left, right = escapes(a, b["center"]), escapes(b, a["center"])
        valid = []
        for p, choices in ((a, left), (b, right)):
            options = []
            for xy, radius in choices:
                _, _, xs, ys = self.local_grid(xy, xy, .2)
                mask, _ = self.masks(p["net"], width, xs, ys, False)
                i, j = round((xy[0]-xs[0])/GRID), round((xy[1]-ys[0])/GRID)
                if mask[0, j, i]:
                    continue
                neck = self.search(p["center"], xy, p["net"], FINE, False, 1, 10000) if radius else [[*xy, 0]]
                if neck and sum(math.dist(x[:2], y[:2]) for x, y in zip(neck, neck[1:])) <= 1.6:
                    options.append((xy, neck))
                if len(options) >= 3:
                    break
            valid.append(options)
        for ax, an in valid[0]:
            for bx, bn in valid[1]:
                local_B_return = a["net"] == "GND" and (
                    min(a["center"][1], b["center"][1]) > 7 or max(a["center"][1], b["center"][1]) < -7)
                middle = self.search(ax, bx, a["net"], width, False, 5, 180000)
                if middle is None and local_B_return:
                    middle = self.search(ax, bx, a["net"], width, True, 5, 180000)
                if middle:
                    self.add_path(an, a["net"], FINE, group+" bounded neck")
                    self.add_path(middle, a["net"], width, group)
                    self.add_path(bn, a["net"], FINE, group+" bounded neck")
                    self.results.append({"from": a["id"], "to": b["id"], "from_uuid": a["uuid"], "to_uuid": b["uuid"],
                                         "net": a["net"], "group": group, "width_mm": width,
                                         "forced_F_return": not local_B_return,
                                         "local_B_return_stays_outside_center_band_y_pm7": local_B_return,
                                         "status": "routed_endpoint_pair_pending_native_validation",
                                         "fine_neck_lengths_mm": [round(sum(math.dist(x[:2], y[:2]) for x, y in zip(n, n[1:])), 6) for n in (an, bn)],
                                         "added_tracks": len(self.tracks)-at, "added_vias": len(self.vias)-av})
                    print("wide routed", group, a["id"], b["id"], flush=True)
                    return True
        self.results.append({"from": a["id"], "to": b["id"], "from_uuid": a["uuid"], "to_uuid": b["uuid"],
                             "net": a["net"], "group": group, "width_mm": width, "forced_F_return": True,
                             "status": "unrouted_wide_F_corridor_not_found"})
        print("wide blocked", group, a["id"], b["id"], flush=True)
        return False

    def finish_protected_return(self):
        # The long preliminary min-width route is not an acceptable main-return neck.
        self.tracks = [t for t in self.tracks if not (
            t["net"] == "/PROT_FET_RETURN" and t["group"] == "protection-sense-and-gates")]
        self.results = [r for r in self.results if not (
            r["net"] == "/PROT_FET_RETURN" and r["group"] == "protection-sense-and-gates")]
        a, b = self.pad("Q5", "A2"), self.pad("R27", "1")
        source_via = next(v for v in self.vias if v["net"] == a["net"] and v["xy"][0] < -15)
        for xy in ((-14.7, 9.55), (-16.5, 8.4), (-16.45, 8.6), (-16.5, 9.7), (-17.0, 8.2)):
            _, _, xs, ys = self.local_grid(xy, xy, .2)
            _, vm = self.masks(a["net"], .6, xs, ys, True)
            if vm[round((xy[1]-ys[0])/GRID), round((xy[0]-xs[0])/GRID)]:
                continue
            front = self.search(b["center"], xy, a["net"], .6, False, 2)
            back = self.search(source_via["xy"], xy, a["net"], .6, False, 3, endpoint_layers=(1, 1))
            if front and back:
                self.add_path(front, a["net"], .6, "Q5 main protected-return F link")
                self.add_path(back, a["net"], .6, "Q5 main protected-return B link outside raw base")
                self.add_via(xy, a["net"], group="Q5 main return off-pad under-R27-body transition; tenting/assembly gate")
                self.results.append({"from": a["id"], "to": b["id"], "from_uuid": a["uuid"], "to_uuid": b["uuid"],
                                     "net": a["net"], "group": "Q5 widened main protected return",
                                     "width_mm": .6, "status": "routed_endpoint_pair_pending_native_validation",
                                     "neck_basis": "Only the existing two0.772mm ball-to-via source necks remain min-width; no8.3mm min-width main return"})
                self.connection(self.pad("R29", "2"), b, "low-current gate-discharge return", allow_vias=False)
                return
        raise ValueError("Main protection return needs explicit review; thin preliminary main path removed")


def seed_package():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "reports").mkdir(exist_ok=True)
    for name in ("handbell.kicad_sch", "handbell.kicad_pro", "Handbell.kicad_sym", "T8.kicad_sym",
                 "fp-lib-table", "sym-lib-table", "LICENSE.txt", "battery-contact-interface.json",
                 "design-input-snapshot.json", "source-evidence.json"):
        shutil.copyfile(SOURCE / name, OUTPUT / name)
    for directory in ("libraries", "notices"):
        shutil.copytree(SOURCE / directory, OUTPUT / directory, dirs_exist_ok=True)
    shutil.copyfile(SOURCE / "reports" / "bom-draft.csv", OUTPUT / "reports" / "bom-draft.csv")
    (OUTPUT / "mechanical-release.json").write_bytes(released_git_bytes(RELEASE_GIT_PATH))


def guard():
    report = OUTPUT / "routing-build.json"
    if report.exists():
        old = json.loads(report.read_text())
        prep.require(sha(OUTPUT / "handbell.kicad_pcb") == old["pcb_sha256"], "Manually edited routed board: refusing overwrite")
        for name, value in old.get("protected_files", {}).items():
            prep.require(sha(OUTPUT / name) == value, "Edited routed dependency: "+name)
    else:
        prep.require(not (OUTPUT / "handbell.kicad_pcb").exists(), "Existing candidate lacks overwrite binding")


def service_silk(i, label):
    text, x, y, size = label
    return (f'(gr_text {json.dumps(text)} (at {100+x:g} {100+y:g} 0) (layer "B.SilkS") '
            f'(uuid "{uid("polarity/"+str(i))}") '
            f'(effects (font (size {size:g} {size:g}) (thickness .15)) (justify mirror)))')


def update_service_silk():
    guard()
    before = source_bindings()
    path = OUTPUT / "handbell.kicad_pcb"
    original, board = load(path)
    old_hash = sha(path)
    existing = {n.value("uuid"): n for n in board.children("gr_text") if n.value("layer") == "B.SilkS"}
    prep.require(set(existing) <= {uid("polarity/"+str(i)) for i in range(len(SERVICE_LABELS))},
                 "Unknown B service text: refusing overwrite")
    block = "\n".join(service_silk(i, label) for i, label in enumerate(SERVICE_LABELS))
    if existing:
        edits = [(min(n.start for n in existing.values()), max(n.end for n in existing.values()), block)]
    else:
        edits = [(board.end-1, board.end-1, "\n"+block+"\n")]
    updated = apply_edits(original, edits)
    def unchanged_nodes(text, root):
        return [text[n.start:n.end] for n in root.children()
                if not (n.head == "gr_text" and n.value("layer") == "B.SilkS")]
    unchanged = unchanged_nodes(original, board)
    prep.require(unchanged == unchanged_nodes(updated, loads(updated)), "Silk-only update changed another native item")
    if updated == original:
        print("Service silk already current; no candidate bytes rewritten")
        return
    write(path, updated)
    manifest = json.loads((OUTPUT / "placement-manifest.json").read_text())
    manifest["generated_pcb_sha256"] = sha(path)
    write(OUTPUT / "placement-manifest.json", manifest)
    build = json.loads((OUTPUT / "routing-build.json").read_text())
    build["pcb_sha256"] = sha(path)
    build["protected_files"]["placement-manifest.json"] = sha(OUTPUT / "placement-manifest.json")
    build["last_silk_update"] = {
        "before_pcb_sha256": old_hash, "after_pcb_sha256": sha(path), "tool_sha256": sha(__file__),
        "all_non_B_service_text_native_items_identical": True,
        "unchanged_native_items_sha256": hashlib.sha256(json.dumps(unchanged).encode()).hexdigest(),
        "labels": SERVICE_LABELS,
        "scope": "Only B service silk and dependent byte bindings; no copper, footprints or interface changes",
    }
    write(OUTPUT / "routing-build.json", build)
    prep.require(source_bindings() == before, "Stage1 changed during service-silk update")
    print(json.dumps(build["last_silk_update"], indent=2))


def emit(router, original, manifest, release, before):
    _, source_board = load(SOURCE / "handbell.kicad_pcb")
    additions = []
    for i, t in enumerate(router.tracks):
        additions.append(f'(segment (start {100+t["a"][0]:.6f} {100+t["a"][1]:.6f}) '
                         f'(end {100+t["b"][0]:.6f} {100+t["b"][1]:.6f}) (width {t["width"]:g}) '
                         f'(layer "{t["layer"]}") (net {json.dumps(t["net"])}) (uuid "{uid("track/"+str(i))}"))')
    for i, v in enumerate(router.vias):
        additions.append(f'(via (at {100+v["xy"][0]:.6f} {100+v["xy"][1]:.6f}) (size {v["diameter"]:g}) '
                         f'(drill {v["drill"]:g}) (layers "F.Cu" "B.Cu") (net {json.dumps(v["net"])}) '
                         f'(uuid "{uid("via/"+str(i))}"))')
    additions.extend(service_silk(i, label) for i, label in enumerate(SERVICE_LABELS))
    title = source_board.child("title_block")
    pcb = apply_edits(original, [(source_board.end-1, source_board.end-1, "\n"+"\n".join(additions)+"\n"),
                                 (title.start, title.end, '(title_block (title "Printed bell critical routing - PARTIAL DRAFT") '
                                  '(rev "0.6-critical-routing") (comment 1 "Adafruit-derived CC BY-SA3.0; LICENSE and notices"))')])
    write(OUTPUT / "handbell.kicad_pcb", pcb)
    current = copy.deepcopy(manifest)
    current.update(status="Partial critical routed candidate; not fabrication/live-cell approval",
                   generated_pcb_sha256=sha(OUTPUT / "handbell.kicad_pcb"),
                   source_baseline=str(SOURCE.relative_to(ROOT)),
                   baseline_pcb_sha256=sha(SOURCE / "handbell.kicad_pcb"),
                   baseline_schematic_sha256=sha(SOURCE / "handbell.kicad_sch"),
                   stage1_manifest_sha256=sha(SOURCE / "placement-manifest.json"),
                   routing_report="reports/routing-review.json",
                   mechanical_release_sha256=sha(OUTPUT / "mechanical-release.json"),
                   mechanical_rebind_required=True)
    current["limits"] = [s for s in current["limits"] if not s.startswith("No tracks") and not s.startswith("Final mechanics")]
    current["limits"] += ["Partial tracks/vias; no claim of complete circuit or current/thermal/USB-impedance qualification.",
                          "Exact geometry retained; mechanics must rebind to these new native bytes.",
                          "Thermal via-in-pad fill/cap/stencil and retained assembly qualification gates remain open."]
    write(OUTPUT / "placement-manifest.json", current)
    write(OUTPUT / "routing-data.json", {"tracks": router.tracks, "vias": router.vias, "connections": router.results})
    protected = [OUTPUT / name for name in ("handbell.kicad_sch", "handbell.kicad_pro", "placement-manifest.json",
                 "battery-contact-interface.json", "fp-lib-table", "sym-lib-table", "Handbell.kicad_sym", "T8.kicad_sym")]
    protected += sorted((OUTPUT / "libraries").rglob("*.kicad_mod"))
    report = {"pcb_sha256": sha(OUTPUT / "handbell.kicad_pcb"), "source_bindings": before,
              "script_sha256": sha(__file__), "release_sha256": sha(OUTPUT / "mechanical-release.json"),
              "protected_files": {str(p.relative_to(OUTPUT)): sha(p) for p in protected},
              "tracks": len(router.tracks), "vias": len(router.vias),
              "connection_results": dict(Counter(r["status"] for r in router.results)),
              "width_policy": {"fine_mm": FINE, "local_power_body_mm": .6, "main_F_return_mm": .8,
                               "fine_power_neck_max_each_mm": 1.6, "copper_thickness_assumption_um": 35,
                               "resistivity_assumption_ohm_mm2_per_m": .0172,
                               "main_return_design_screen": "0.8mm x35um x40mm ~24.6mohm; hypothetical2A drop49mV. "
                               "A working50mV corridor budget, NOT a2A current, thermal, fault/SOA or copper-thickness qualification.",
                               "fabrication_status": "No copper weight or via-in-pad process qualified"},
    }
    write(OUTPUT / "routing-build.json", report)
    prep.require(source_bindings() == before, "Stage1 changed during routing")
    print(json.dumps({k: report[k] for k in ("pcb_sha256", "tracks", "vias", "connection_results")}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", action="store_true", help="Preserve last generated paths and retry missing connections")
    parser.add_argument("--max-connections", type=int, default=120)
    parser.add_argument("--prune-only", action="store_true", help="Prune native-reported sub0.1mm dead ends in the last generated candidate")
    parser.add_argument("--finish-return", action="store_true", help="Replace preliminary thin protection-current path with reviewed outside source escape")
    parser.add_argument("--refresh-release", action="store_true", help="Refresh pinned release provenance without rewriting PCB or manifest")
    parser.add_argument("--update-silk", action="store_true", help="Update only B service labels, preserving every other native item")
    args = parser.parse_args()
    release, native_evidence = verify_release()
    if args.update_silk:
        prep.require(not (args.resume or args.prune_only or args.finish_return or args.refresh_release),
                     "Use --update-silk alone")
        update_service_silk()
        return
    if args.refresh_release:
        prep.require(not (args.resume or args.prune_only or args.finish_return), "Use --refresh-release alone")
        guard()
        before_native = {name: sha(OUTPUT / name) for name in ("handbell.kicad_pcb", "placement-manifest.json")}
        (OUTPUT / "mechanical-release.json").write_bytes(released_git_bytes(RELEASE_GIT_PATH))
        write(OUTPUT / "released-mechanical-evidence.json", native_evidence)
        prep.require(before_native == {name: sha(OUTPUT / name) for name in before_native},
                     "Release refresh must not rewrite native PCB/manifest")
        print(json.dumps({"release_commit": RELEASE_COMMIT, "unchanged_native_hashes": before_native}, indent=2))
        return
    before = source_bindings()
    guard()
    seed_package()
    write(OUTPUT / "released-mechanical-evidence.json", native_evidence)
    original, board = load(SOURCE / "handbell.kicad_pcb")
    manifest = json.loads((SOURCE / "placement-manifest.json").read_text())
    router = Router(manifest, board)
    done = set()
    if (args.resume or args.prune_only or args.finish_return) and (OUTPUT / "routing-data.json").exists():
        data = json.loads((OUTPUT / "routing-data.json").read_text())
        router.tracks, router.vias = data["tracks"], data["vias"]
        router.results = data["connections"] if (args.prune_only or args.finish_return) else [
            r for r in data["connections"] if r["status"].startswith("routed")]
        done = {(r["from"], r["to"], r["group"]) for r in router.results}
        for item in [*router.tracks, *router.vias, *router.results]:
            item["group"] = item["group"].replace("dedicated boost F return", "boost protected return above contact row")
    else:
        router.setup_escapes()
    requests = []
    def pair(ar, ap, br, bp, group, wide=None, allow_vias=True):
        requests.append((router.pad(ar, ap), router.pad(br, bp), group, wide, allow_vias))
    pair("U4", "3", "R27", "2", "dedicated amplifier F return", .8, False)
    pair("U5", "4", "R27", "2", "boost protected return above contact row", .8, False)
    plan = prep.critical_connections(router.pads)
    for group in plan:
        if group["name"] == "protection-sense-and-gates":
            group["connections"].sort(key=lambda c: (0 if c["net"] in {"/PROT_COUT", "/PROT_DOUT", "/PROT_VM"} else 1))
        if group["name"] == "crystal-and-qspi":
            group["connections"].sort(key=lambda c: (
                0 if c["net"].startswith("QSPI") else 1,
                -int(c["from"].split(".")[1].split("#")[0]) if c["from"].startswith("IC1.") else 0))
    byid = {p["id"]: p for p in router.pads}
    for name in ("protection-sense-and-gates", "crystal-and-qspi", "mcu-local-supplies",
                 "boost-power-loop", "amplifier-power-and-btl", "system-power-topology", "battery-physical-land-pairs"):
        group = next(g for g in plan if g["name"] == name)
        for link in group["connections"]:
            a, b = byid[link["from"]], byid[link["to"]]
            if a["reference"] == b["reference"] == "Q5":
                continue
            is_bulk = name in {"boost-power-loop", "amplifier-power-and-btl", "system-power-topology"} and (
                a["net"] in {"V+", "VAMP", "VBAT", "GND", "/PROT_FET_RETURN", "/CELL_NEG", "BOOST_SW",
                             "Net-(FB1-P$1)", "Net-(FB2-P$1)", "VO+", "VO-"})
            if a["net"] == "GND" and a["reference"] == "R26":
                is_bulk = False
            requests.append((a, b, name, .6 if is_bulk else None,
                             name not in {"boost-power-loop", "amplifier-power-and-btl", "system-power-topology"}))
    for ref in ("C2", "C3", "C6", "C7", "C8", "C9", "C10", "C11", "C12", "C13", "C14", "C15", "C17", "C18"):
        pad = next(p for p in router.pads if p["reference"] == ref and p["net"] == "GND")
        requests.append((pad, router.pad("IC1", "P$1"), "MCU local protected-GND return", None, True))
    pair("IC1", "19", "IC1", "P$1", "MCU ground pin to thermal bank", None, False)
    pair("IC1", "19", "R27", "2", "logic protected-GND F return", None, False)
    for a, b, group, width, vias in requests[:0 if (args.prune_only or args.finish_return) else args.max_connections]:
        if (a["id"], b["id"], group) in done:
            continue
        if width:
            router.wide_connection(a, b, group, width)
        else:
            router.connection(a, b, group, allow_vias=vias)
    if args.finish_return:
        router.finish_protected_return()
    emit(router, original, manifest, release, before)
    pruned = []
    for iteration in range(6):
        report_path = OUTPUT / "reports" / "drc-development.json"
        subprocess.run([str(CLI), "pcb", "drc", "--format", "json", "--severity-all",
                        "--output", str(report_path), str(OUTPUT / "handbell.kicad_pcb")],
                       check=True, cwd=ROOT, capture_output=True, timeout=300)
        drc = json.loads(report_path.read_text())
        ids = {item["uuid"] for v in drc["violations"] if v["type"] == "track_dangling" for item in v["items"]}
        if not ids:
            break
        doomed = [i for i, t in enumerate(router.tracks) if uid("track/"+str(i)) in ids]
        prep.require(doomed and all(math.dist(router.tracks[i]["a"], router.tracks[i]["b"]) < .1 for i in doomed),
                     "Nontrivial dangling route requires explicit repair, not pruning")
        pruned.extend(router.tracks[i] for i in doomed)
        router.tracks = [t for i, t in enumerate(router.tracks) if i not in doomed]
        emit(router, original, manifest, release, before)
    else:
        raise ValueError("Dangling spur cleanup did not converge")
    write(OUTPUT / "reports" / "removed-native-spurs.json",
          {"scope": "Actual sub0.1mm grid/neck overshoot copper removed, not a DRC waiver",
           "removed": pruned, "native_dangling_remaining": 0})


if __name__ == "__main__":
    main()
