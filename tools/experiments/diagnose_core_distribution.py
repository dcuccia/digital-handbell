# SPDX-License-Identifier: MIT
"""Read-only grid reachability diagnostic; neither routes nor modifies a board."""
import argparse
from collections import deque
import json
import os
from pathlib import Path
import sys

from route_core_distribution import BASE, GRID, NativeRouter, PACKAGE, sha


def component(mask, seed):
    """Use the existing search's eight-neighbor, no-corner-cut adjacency."""
    assert not mask[seed[1], seed[0]]
    queue, seen = deque([seed]), {seed}
    while queue:
        x, y = queue.popleft()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if not (dx or dy):
                    continue
                xx, yy = x+dx, y+dy
                if not (0 <= xx < mask.shape[1] and 0 <= yy < mask.shape[0]) or mask[yy, xx]:
                    continue
                if dx and dy and (mask[yy, x] or mask[y, xx]):
                    continue
                if (xx, yy) not in seen:
                    seen.add((xx, yy))
                    queue.append((xx, yy))
    return seen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    output = parser.parse_args().output.resolve()
    if output.exists() or sha(PACKAGE / "handbell.kicad_pcb") != BASE:
        raise ValueError("Require pinned source and new report")
    native = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin"
    handle = os.add_dll_directory(str(native))
    sys.path.insert(0, str(native / "Lib" / "site-packages"))
    import pcbnew as pcb
    if pcb.GetBuildVersion() != "10.0.6":
        raise ValueError("KiCad 10.0.6 required")
    board = pcb.LoadBoard(str(PACKAGE / "handbell.kicad_pcb"))
    pads = {f.GetReference()+"."+p.GetNumber(): p for f in board.GetFootprints() for p in f.Pads()}
    endpoints = [[pcb.ToMM(v)-100 for v in pads[n].GetPosition()] for n in ("C6.2", "C8.1")]
    router = NativeRouter(board, pcb)
    xmin, ymin, xs, ys = router.local_grid(*endpoints, 4)
    masks, via_mask = router.masks("VCORE", .2, xs, ys, True)

    def node(pad):
        return tuple(round((pcb.ToMM(v)-100-origin)/GRID)
                     for v, origin in zip(pad.GetPosition(), (xmin, ymin)))

    results = {}
    for seed in ("C6.2", "C8.1"):
        seen = component(masks[0], node(pads[seed]))
        results[seed] = {
            "reachable_F_nodes": len(seen),
            "bounds_native_mm": [round(float(f), 6) for f in (
                min(xs[x] for x,y in seen)+100, min(ys[y] for x,y in seen)+100,
                max(xs[x] for x,y in seen)+100, max(ys[y] for x,y in seen)+100)],
            "legal_B_transition_grid_nodes": sum(not via_mask[y,x] and not masks[1,y,x] for x,y in seen),
            "touches_search_boundary": any(x in (0,len(xs)-1) or y in (0,len(ys)-1) for x,y in seen),
            "VCORE_pad_centers_on_reachable_grid": [
                name for name,pad in pads.items() if pad.GetNetname() == "VCORE" and node(pad) in seen],
        }
        results[seed]["legal_B_transition_grid_nodes"] = int(results[seed]["legal_B_transition_grid_nodes"])
    assert sha(PACKAGE / "handbell.kicad_pcb") == BASE
    report = {
        "status": "DIAGNOSTIC_ONLY_NO_BOARD_CHANGE",
        "input_pcb_sha256": BASE, "tool_sha256": sha(Path(__file__)),
        "mask_tool_sha256": sha(Path(__file__).with_name("route_core_distribution.py")),
        "search_tool_sha256": sha(Path(__file__).parents[1] / "route_printed_bell.py"),
        "grid_mm": GRID, "trace_width_mm": .2, "search_margin_mm": 4,
        "components": results,
        "qualification": "Grid reachability is not a native-clear route or proof of impossibility. Existing connected copper must be treated as a target group, not re-routed at the new trace width/grid.",
    }
    output.write_bytes((json.dumps(report, indent=2)+"\n").encode("utf-8"))
    print(json.dumps(report))


if __name__ == "__main__":
    main()
