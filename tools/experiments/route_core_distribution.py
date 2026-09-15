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
from check_front_ground import bounds_polygon
from kicad_sexpr import apply_edits, load
from route_clock_local import PACKAGE, sha
from route_printed_bell import GRID, Router

BASE = "57ae2c0b54e1313fb175ccdecdee07ebda07abed5151e776c9767511135d440f"
PAIRS = (("C6.2", "C8.1"), ("C18.2", "C8.1"))


class NativeRouter(Router):
    def __init__(self, board, pcb):
        self.pcb = pcb
        self.tracks, self.vias, self.results = [], [], []
        self.obstacles = [p for f in board.GetFootprints() for p in f.Pads()] + list(board.GetTracks())
        self.metal = []
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
        # This experiment is restricted to a rectangle well inside the D43 outline.
        for j, y in enumerate(ys):
            for i, x in enumerate(xs):
                if abs(x) > 12 or abs(y) > 10:
                    masks[:, j, i] = True
                    via_mask[j, i] = True
        return masks, via_mask


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
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
    pads = {f.GetReference()+"."+p.GetNumber(): p for f in board.GetFootprints() for p in f.Pads()}
    router = NativeRouter(board, pcb)
    started = time.monotonic()
    for a, b in PAIRS:
        assert pads[a].GetNetname() == pads[b].GetNetname() == "VCORE"
        points = [[pcb.ToMM(v)-100 for v in pads[n].GetPosition()] for n in (a, b)]
        path = router.search(*points, "VCORE", .2, True, 4, expansion_limit=80000)
        if path is None:
            out.mkdir(parents=True)
            failure = {"status": "NO_BOUNDED_PAD_PAIR_PATH_NOT_PROOF_OF_IMPOSSIBILITY",
                       "input_pcb_sha256": BASE, "from": a, "to": b,
                       "tool_sha256": sha(Path(__file__)), "source_modified": False,
                       "completed_pairs": len(router.results),
                       "elapsed_seconds": time.monotonic()-started,
                       "note": "Inspect existing connected-group terminals before changing layout or widening search."}
            (out / "failure.json").write_bytes((json.dumps(failure, indent=2)+"\n").encode("utf-8"))
            raise RuntimeError(f"No bounded native-mask path: {a}/{b}")
        router.add_path(path, "VCORE", .2, a+" to "+b)
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
            if obstacle.IsOnLayer(layer) and obstacle.GetNetname() != "VCORE":
                if shape.Collide(obstacle.GetEffectiveShape(layer), pcb.FromMM(.2)-1):
                    raise ValueError("Exact candidate edge clearance: "+obstacle.m_Uuid.AsString())
        if layer == pcb.B_Cu:
            assert all(not metal.Collide(shape, pcb.FromMM(.2)-1) for metal, _ in router.metal)
    text, tree = load(PACKAGE / "handbell.kicad_pcb")
    edits = [(p.start, p.end, "") for z in tree.children("zone") for p in z.children("filled_polygon")]
    additions, tracks, vias = [], [], []
    for i, t in enumerate(router.tracks):
        a, b = [[round(v+100, 6) for v in t[k]] for k in ("a", "b")]
        uid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"digital-handbell/core-distribution/track/{i}"))
        additions.append(f'\n(segment (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) '
                         f'(width {t["width"]}) (layer "{t["layer"]}") (net "VCORE") (uuid "{uid}"))')
        tracks.append({"uuid": uid, "start_mm": a, "end_mm": b, "width_mm": t["width"],
                       "layer": t["layer"], "net": "VCORE"})
    for i, v in enumerate(router.vias):
        at = [round(x+100, 6) for x in v["xy"]]
        uid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"digital-handbell/core-distribution/via/{i}"))
        additions.append(f'\n(via (at {at[0]} {at[1]}) (size 0.6) (drill 0.3) '
                         f'(layers "F.Cu" "B.Cu") (net "VCORE") (uuid "{uid}"))')
        vias.append({"uuid": uid, "at_mm": at, "diameter_mm": .6, "drill_mm": .3, "net": "VCORE"})
    edits.append((tree.end-1, tree.end-1, "".join(additions)))
    shutil.copytree(PACKAGE, out, ignore=shutil.ignore_patterns(
        "reports", "input-checkpoint", "*.kicad_prl", "*.lck", "*-backups"))
    (out / "handbell.kicad_pcb").write_bytes(apply_edits(text, edits).encode("utf-8"))
    manifest = json.loads((PACKAGE / "placement-manifest.json").read_text(encoding="utf-8"))
    manifest.update(generated_pcb_sha256=sha(out / "handbell.kicad_pcb"),
                    current_stage_report="reports/core-distribution.json")
    (out / "placement-manifest.json").write_bytes((json.dumps(manifest, indent=2)+"\n").encode("utf-8"))
    (out / "reports").mkdir()
    shutil.copyfile(PACKAGE / "reports" / "front-ground-plan.json", out / "reports" / "front-ground-plan.json")
    report = {"status": "STAGED_NOT_ACCEPTED", "input_commit": "0d2f726", "input_pcb_sha256": BASE,
              "output_pcb_sha256": sha(out / "handbell.kicad_pcb"), "generator_sha256": sha(Path(__file__)),
              "search_tool_sha256": sha(Path(__file__).parents[1] / "route_printed_bell.py"),
              "component_moves": [], "added_tracks": tracks, "changed_tracks": [], "removed_tracks": [],
              "new_vias": vias, "required_connections": PAIRS, "search_seconds": time.monotonic()-started,
              "grid_mm": GRID, "expansion_limit_per_connection": 80000, "search_margin_mm": 4,
              "contact_interface_sha256": sha(PACKAGE / "battery-contact-interface.json"),
              "ground_fill_invalidated": True,
              "remaining": "Exact edge/via DRC, filled independent continuity and unchanged-source gates required."}
    (out / "reports" / "core-distribution.json").write_bytes((json.dumps(report, indent=2)+"\n").encode("utf-8"))
    print(json.dumps(report))


if __name__ == "__main__":
    main()
