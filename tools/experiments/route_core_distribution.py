# SPDX-License-Identifier: MIT
"""Bounded VCORE candidate using the existing search with native obstacle masks."""
import argparse
import json
import math
import os
from pathlib import Path
import shutil
import sys
import time
import uuid

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_front_ground import board_polygon, bounds_polygon
from kicad_sexpr import apply_edits, load
from route_clock_local import PACKAGE, sha
from route_printed_bell import GRID, Router

BASE = "57ae2c0b54e1313fb175ccdecdee07ebda07abed5151e776c9767511135d440f"
PAIRS = (("C6.2", "C7.2"),)
STAGE = "core-distribution-right"
INPUT_COMMIT = "60db9b4"
ROUTING_BOUNDS = (-12, -10, 12, 10)
SEARCH_MARGIN = 4
SEARCH_LIMIT = 80000


class NativeRouter(Router):
    def __init__(self, board, pcb):
        self.pcb = pcb
        self.tracks, self.vias, self.results = [], [], []
        self.obstacles = [p for f in board.GetFootprints() for p in f.Pads()] + list(board.GetTracks())
        self.metal = []
        manifest = json.loads((PACKAGE / "placement-manifest.json").read_text(encoding="utf-8"))
        self.boundary = board_polygon(pcb, manifest, .55)
        contact = json.loads((PACKAGE / "battery-contact-interface.json").read_text(encoding="utf-8"))
        primitives = contact["right_contact_original_primitives"]
        for sign in (1, -1):
            for primitive in [*primitives["base_tabs"], primitives["under_cell_base"]]:
                xs = sorted(100 + sign * primitive[k] for k in ("x_min", "x_max"))
                bounds = [xs[0], 100-primitive["y_width"]/2, xs[1], 100+primitive["y_width"]/2]
                shape = bounds_polygon(pcb, {"bounds_absolute_iu": [pcb.FromMM(v) for v in bounds]})
                self.metal.append((shape, bounds))

    def masks(self, net, width, xs, ys, allow_vias):
        pcb = self.pcb
        masks = np.zeros((2, len(ys), len(xs)), dtype=bool)
        via_mask = np.zeros((len(ys), len(xs)), dtype=bool)
        # Existing MCU escapes use the exact clearance floor. Check full edges
        # after searching instead of inflating away those usable corridors.
        guard = -.000001

        def mark(mask, shape, bounds, radius, clearance):
            margin = radius + clearance
            lo_x, lo_y, hi_x, hi_y = bounds
            i0 = max(0, math.floor((lo_x-100-margin-xs[0])/GRID))
            i1 = min(len(xs), math.ceil((hi_x-100+margin-xs[0])/GRID)+1)
            j0 = max(0, math.floor((lo_y-100-margin-ys[0])/GRID))
            j1 = min(len(ys), math.ceil((hi_y-100+margin-ys[0])/GRID)+1)
            for j in range(j0, j1):
                for i in range(i0, i1):
                    if mask[j, i]:
                        continue
                    circle = pcb.SHAPE_CIRCLE(
                        pcb.VECTOR2I(pcb.FromMM(float(xs[i]+100)), pcb.FromMM(float(ys[j]+100))),
                        pcb.FromMM(radius))
                    if shape.Collide(circle, pcb.FromMM(clearance)):
                        mask[j, i] = True

        for obstacle in self.obstacles:
            box = obstacle.GetBoundingBox()
            bounds = [pcb.ToMM(v) for v in (box.GetLeft(), box.GetTop(), box.GetRight(), box.GetBottom())]
            for layer_index, layer in enumerate((pcb.F_Cu, pcb.B_Cu)):
                if not obstacle.IsOnLayer(layer):
                    continue
                shape = obstacle.GetEffectiveShape(layer)
                if obstacle.GetNetname() != net:
                    mark(masks[layer_index], shape, bounds, width/2, .2+guard)
                    if allow_vias:
                        mark(via_mask, shape, bounds, .3, .25+guard)
                elif allow_vias and isinstance(obstacle, pcb.PAD):
                    mark(via_mask, shape, bounds, .3, .1+guard)
        for shape, bounds in self.metal:
            mark(masks[1], shape, bounds, width/2, .2+guard)
            if allow_vias:
                mark(via_mask, shape, bounds, .3, .25+guard)
        # Retain both the requested search scope and an actual outline setback.
        for j, y in enumerate(ys):
            for i, x in enumerate(xs):
                point = pcb.VECTOR2I(pcb.FromMM(float(x+100)), pcb.FromMM(float(y+100)))
                if (not ROUTING_BOUNDS[0] <= x <= ROUTING_BOUNDS[2]
                        or not ROUTING_BOUNDS[1] <= y <= ROUTING_BOUNDS[3]
                        or not self.boundary.Contains(point)):
                    masks[:, j, i] = True
                    via_mask[j, i] = True
        return masks, via_mask


def main():
    global GRID
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--reserve-ground", action="store_true",
                        help="Route the affected ground group first, then route VCORE around it")
    parser.add_argument("--fine-grid", action="store_true", help="One bounded 0.025 mm sampling correction")
    parser.add_argument("--gain-escape", action="store_true", help="Move the identified obstructing 3V3 via and its two incident endpoints")
    args = parser.parse_args()
    if args.fine_grid:
        import route_printed_bell
        route_printed_bell.GRID = GRID = .025
    out = args.output.resolve()
    if out.exists() or sha(PACKAGE / "handbell.kicad_pcb") != BASE:
        raise ValueError("Require pinned corridor board and a new output directory")
    native = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin"
    dll_handle = os.add_dll_directory(str(native))
    sys.path.insert(0, str(native / "Lib" / "site-packages"))
    import pcbnew as pcb
    if pcb.GetBuildVersion() != "10.0.6":
        raise ValueError("KiCad 10.0.6 required")
    board = pcb.LoadBoard(str(PACKAGE / "handbell.kicad_pcb"))
    changed_tracks, changed_vias = [], []
    if args.gain_escape:
        assert STAGE == "gain-routing"
        by_id = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
        via = by_id["b86f2ac1-88d2-59d4-863c-429ca8108ae3"]
        old_point, new_point = [108.3, 89.8], [107.9, 89.4]
        assert [pcb.ToMM(v) for v in via.GetPosition()] == old_point
        assert via.GetNetname() == "+3V3" and via.GetWidth(pcb.F_Cu) == pcb.FromMM(.6)
        assert via.GetDrillValue() == pcb.FromMM(.3)
        position = pcb.VECTOR2I(*(pcb.FromMM(v) for v in new_point))
        via.SetPosition(position)
        changed_vias.append({"uuid": via.m_Uuid.AsString(), "old_mm": old_point, "new_mm": new_point,
                             "net": "+3V3", "diameter_mm": .6, "drill_mm": .3})
        for uid, key in (("9a956178-8111-529e-9a8e-751c4638af6e", "start"),
                         ("66f2c2c9-98fa-5aa7-aadd-fc70574ee365", "end")):
            track = by_id[uid]
            old = {"start": [pcb.ToMM(v) for v in track.GetStart()], "end": [pcb.ToMM(v) for v in track.GetEnd()]}
            assert old[key] == old_point and track.GetNetname() == "+3V3"
            assert track.GetWidth() == pcb.FromMM(.25)
            (track.SetStart if key == "start" else track.SetEnd)(position)
            changed_tracks.append({"uuid": uid, "old": old, "new": {**old, key: new_point},
                                   "net": "+3V3", "width_mm_unchanged": .25})
    pads = {f.GetReference()+"."+p.GetNumber(): p for f in board.GetFootprints() for p in f.Pads()}
    router = NativeRouter(board, pcb)
    started = time.monotonic()
    pairs = list(PAIRS)
    if args.reserve_ground:
        pairs = [("C6.1", "C7.1"), ("C17.2", "C7.1"), ("C7.1", "C8.2"), ("C8.2", "C13.2")] + pairs
    for a, b in pairs:
        net = pads[a].GetNetname()
        assert net and net == pads[b].GetNetname()
        points = [[pcb.ToMM(v)-100 for v in pads[n].GetPosition()] for n in (a, b)]
        path = router.search(*points, net, .2, net != "GND", SEARCH_MARGIN, expansion_limit=SEARCH_LIMIT)
        if path is None:
            out.mkdir(parents=True)
            failure = {"status": "NO_BOUNDED_PAD_PAIR_PATH_NOT_PROOF_OF_IMPOSSIBILITY",
                       "input_pcb_sha256": BASE, "from": a, "to": b,
                       "tool_sha256": sha(Path(__file__)), "source_modified": False,
                       "completed_pairs": len(router.results),
                       "planned_tracks": router.tracks, "planned_vias": router.vias,
                       "search_statistics": router.last_search_statistics,
                       "elapsed_seconds": time.monotonic()-started,
                       "note": "Inspect existing connected-group terminals before changing layout or widening search."}
            (out / "failure.json").write_bytes((json.dumps(failure, indent=2)+"\n").encode("utf-8"))
            raise RuntimeError(f"No bounded native-mask path: {a}/{b}")
        first = len(router.tracks)
        router.add_path(path, net, .2, a+" to "+b)
        for track in router.tracks[first:]:
            item = pcb.PCB_TRACK(board)
            item.SetLayer(pcb.F_Cu if track["layer"] == "F.Cu" else pcb.B_Cu)
            item.SetWidth(pcb.FromMM(track["width"]))
            item.SetNetCode(pads[a].GetNetCode())
            item.SetStart(pcb.VECTOR2I(*(pcb.FromMM(v+100) for v in track["a"])))
            item.SetEnd(pcb.VECTOR2I(*(pcb.FromMM(v+100) for v in track["b"])))
            board.Add(item)
            router.obstacles.append(item)
        router.results.append({"from": a, "to": b, "path": path})
    for track in router.tracks:
        layer = pcb.F_Cu if track["layer"] == "F.Cu" else pcb.B_Cu
        item = pcb.PCB_TRACK(board)
        item.SetLayer(layer)
        item.SetWidth(pcb.FromMM(track["width"]))
        item.SetStart(pcb.VECTOR2I(*(pcb.FromMM(v+100) for v in track["a"])))
        item.SetEnd(pcb.VECTOR2I(*(pcb.FromMM(v+100) for v in track["b"])))
        shape = item.GetEffectiveShape(layer)
        for obstacle in router.obstacles:
            if obstacle.IsOnLayer(layer) and obstacle.GetNetname() != track["net"]:
                if shape.Collide(obstacle.GetEffectiveShape(layer), pcb.FromMM(.2)-1):
                    raise ValueError("Exact candidate edge clearance: "+obstacle.m_Uuid.AsString())
        if layer == pcb.B_Cu:
            assert all(not metal.Collide(shape, pcb.FromMM(.2)-1) for metal, _ in router.metal)
    text, tree = load(PACKAGE / "handbell.kicad_pcb")
    edits = [(p.start, p.end, "") for z in tree.children("zone") for p in z.children("filled_polygon")]
    for kind, records in (("segment", changed_tracks), ("via", changed_vias)):
        by_id = {n.value("uuid"): n for n in tree.children(kind)}
        for record in records:
            node = by_id[record["uuid"]]
            changes = record["new"] if kind == "segment" else {"at": record["new_mm"]}
            for key, point in changes.items():
                old = node.child(key)
                edits.append((old.start, old.end, f"({key} {point[0]} {point[1]})"))
    additions, tracks, vias = [], [], []
    for i, t in enumerate(router.tracks):
        a, b = [[round(v+100, 6) for v in t[k]] for k in ("a", "b")]
        uid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"digital-handbell/{STAGE}/track/{i}"))
        additions.append(f'\n(segment (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) '
                         f'(width {t["width"]}) (layer "{t["layer"]}") (net "{t["net"]}") (uuid "{uid}"))')
        tracks.append({"uuid": uid, "start_mm": a, "end_mm": b, "width_mm": t["width"],
                       "layer": t["layer"], "net": t["net"]})
    for i, v in enumerate(router.vias):
        at = [round(x+100, 6) for x in v["xy"]]
        uid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"digital-handbell/{STAGE}/via/{i}"))
        additions.append(f'\n(via (at {at[0]} {at[1]}) (size 0.6) (drill 0.3) '
                         f'(layers "F.Cu" "B.Cu") (net "{v["net"]}") (uuid "{uid}"))')
        vias.append({"uuid": uid, "at_mm": at, "diameter_mm": .6, "drill_mm": .3, "net": v["net"]})
    edits.append((tree.end-1, tree.end-1, "".join(additions)))
    shutil.copytree(PACKAGE, out, ignore=shutil.ignore_patterns(
        "reports", "input-checkpoint", "*.kicad_prl", "*.lck", "*-backups"))
    (out / "handbell.kicad_pcb").write_bytes(apply_edits(text, edits).encode("utf-8"))
    manifest = json.loads((PACKAGE / "placement-manifest.json").read_text(encoding="utf-8"))
    manifest.update(generated_pcb_sha256=sha(out / "handbell.kicad_pcb"),
                    current_stage_report=f"reports/{STAGE}.json")
    (out / "placement-manifest.json").write_bytes((json.dumps(manifest, indent=2)+"\n").encode("utf-8"))
    (out / "reports").mkdir()
    shutil.copyfile(PACKAGE / "reports" / "front-ground-plan.json", out / "reports" / "front-ground-plan.json")
    report = {"status": "STAGED_NOT_ACCEPTED", "input_commit": INPUT_COMMIT, "input_pcb_sha256": BASE,
              "output_pcb_sha256": sha(out / "handbell.kicad_pcb"), "generator_sha256": sha(Path(__file__)),
              "entrypoint_sha256": sha(Path(sys.argv[0])),
              "search_tool_sha256": sha(Path(__file__).parents[1] / "route_printed_bell.py"),
              "component_moves": [], "added_tracks": tracks, "changed_tracks": changed_tracks, "removed_tracks": [],
              "changed_vias": changed_vias,
              "new_vias": vias, "required_connections": pairs, "search_seconds": time.monotonic()-started,
              "ground_group_routed_first": args.reserve_ground,
              "grid_mm": GRID, "expansion_limit_per_connection": SEARCH_LIMIT, "search_margin_mm": SEARCH_MARGIN,
              "routing_bounds_common_mm": ROUTING_BOUNDS, "outline_setback_mm": .55,
              "contact_interface_sha256": sha(PACKAGE / "battery-contact-interface.json"),
              "ground_fill_invalidated": True,
              "remaining": "Exact edge/via DRC, filled independent continuity and unchanged-source gates required."}
    (out / "reports" / f"{STAGE}.json").write_bytes((json.dumps(report, indent=2)+"\n").encode("utf-8"))
    print(json.dumps(report))


if __name__ == "__main__":
    main()
