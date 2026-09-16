# SPDX-License-Identifier: MIT
"""Bounded additive completion from actual disconnected native pad islands."""
from __future__ import annotations

import argparse
import copy
import math
import shutil

import route
from kicad_sexpr import apply_edits, load, loads
from zone_graph import CopperGraph

HERE = route.HERE


def width_for(net, a, b):
    refs = {a["reference"], b["reference"]}
    if net in ("VHI", "VBAT", "VBUS"):
        if refs & {"R16", "R25", "TP11"} or net == "VBUS" and "Q3" in refs:
            return .1778
        return .8
    return .1778 if net != "+3V3" else .25


def apply():
    route.guard()
    report = HERE / "reports" / "additive-completion.json"
    route.require(not report.exists(), "Existing completion attempt refused")
    text, board = load(HERE / "handbell.kicad_pcb")
    route.require(not board.children("zone"), "Filled copper requires an explicit refill workflow")
    baseline = HERE / "routing" / "pre-additive"
    route.require(not baseline.exists(), "Existing additive checkpoint refused")
    baseline.mkdir()
    for name in ("handbell.kicad_pcb", "placement-manifest.json", "routing-data.json", "completion-build.json"):
        shutil.copyfile(HERE / name, baseline / name)
    input_hash = route.sha(HERE / "handbell.kicad_pcb")
    graph = CopperGraph(route.native(), HERE / "handbell.kicad_pcb")
    text = apply_edits(text, [(n.start, n.end, "") for kind in ("segment", "via") for n in board.children(kind)])
    manifest = route.read(HERE / "placement-manifest.json")
    data = route.read(HERE / "routing-data.json")
    router = route.Router(manifest, loads(text))
    router.tracks, router.vias = copy.deepcopy(data["tracks"]), copy.deepcopy(data["vias"])
    router.results, router.quiet = data["connections"], data["quiet_paths"]
    priorities = {"VCORE": 0, "+3V3": 1, "VHI": 2, "VBUS": 3, "VBAT": 4}
    attempts = []
    for net in sorted(graph.nets(), key=lambda n: (priorities.get(n["net"], 5), n["net"])):
        islands = net["islands"]
        if net["net"] == "GND" or len(islands) < 2:
            continue
        parents = list(range(len(islands)))

        def root(index):
            while parents[index] != index:
                index = parents[index]
            return index

        pairs = []
        for i, left in enumerate(islands):
            for j, right in enumerate(islands):
                if i >= j:
                    continue
                choices = []
                for a in left:
                    for b in right:
                        pa, pb = router.pad(a["reference"], a["number"]), router.pad(b["reference"], b["number"])
                        choices.append((math.dist(pa["center"], pb["center"]), i, j, a, b))
                pairs.extend(sorted(choices, key=lambda p: p[0])[:2])
        for _, i, j, a, b in sorted(pairs, key=lambda p: p[0]):
            if root(i) == root(j):
                continue
            pa, pb = router.pad(a["reference"], a["number"]), router.pad(b["reference"], b["number"])
            width = width_for(net["net"], a, b)
            layers = tuple(0 if "F.Cu" in p["layers"] else 1 for p in (pa, pb))
            path = None
            for margin in (3, 7):
                path = router.search(pa["center"], pb["center"], net["net"], width, True,
                                     margin, 60000, layers)
                if path:
                    break
            record = {"net": net["net"], "from": pa["id"], "to": pb["id"], "width_mm": width,
                      "routed": bool(path), "tracks_before": len(router.tracks), "vias_before": len(router.vias)}
            if path:
                group = "additive native-island completion " + pa["id"] + " to " + pb["id"]
                router.add_path(path, net["net"], width, group)
                router.mark_pair(a["reference"], a["number"], b["reference"], b["number"], group)
                parents[root(j)] = root(i)
            record.update(tracks_after=len(router.tracks), vias_after=len(router.vias))
            attempts.append(record)
            print(net["net"], pa["id"], pb["id"], "routed" if path else "blocked search", flush=True)
    route.guard()
    route.emit(text, manifest, route.read(HERE / "reports" / "footprint-movements.json"),
               router, route.source_bindings())
    route.write(report, {"input_pcb_sha256": input_hash, "output_pcb_sha256": route.sha(HERE / "handbell.kicad_pcb"),
                         "tool_sha256": route.sha(__file__), "attempts": attempts,
                         "scope": "Additive endpoint search; native connectivity/DRC still required. Search failure is not proof of physical impossibility."})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", required=True)
    parser.parse_args()
    apply()
