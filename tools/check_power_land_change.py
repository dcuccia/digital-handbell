# SPDX-License-Identifier: MIT
"""Read-only local land-change proof using the existing primitive/power checks."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys

import numpy
import analyze_printed_bell_power_paths as measure
import check_printed_bell_power_rework as check
from check_front_ground import compare_components


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(graph, pcb):
    result = {}
    for track in graph.board.GetTracks():
        uid = track.m_Uuid.AsString()
        if isinstance(track, pcb.PCB_VIA):
            result[uid] = {"kind": "via", "net": track.GetNetname(),
                           "xy": [pcb.ToMM(v) for v in track.GetPosition()],
                           "width_by_layer": {graph.layer_name(layer): pcb.ToMM(track.GetWidth(layer))
                                              for layer in track.GetLayerSet().Seq()},
                           "drill": pcb.ToMM(track.GetDrillValue()),
                           "layers": list(track.GetLayerSet().Seq())}
        else:
            assert not isinstance(track, pcb.PCB_ARC), "Arc exposure needs a separate implementation"
            result[uid] = {"kind": "segment", "net": track.GetNetname(),
                           "width": pcb.ToMM(track.GetWidth()),
                           "layer": graph.layer_name(track.GetLayer()),
                           "a": [pcb.ToMM(v) - 100 for v in track.GetStart()],
                           "b": [pcb.ToMM(v) - 100 for v in track.GetEnd()]}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--stage-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Require a new report output")
    stage = json.loads(args.stage_report.read_text(encoding="utf-8"))
    assert sha(args.baseline) == stage["input_pcb_sha256"]
    assert sha(args.candidate) == stage["output_pcb_sha256"]
    native = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin"
    handle = os.add_dll_directory(str(native))
    sys.path.insert(0, str(native / "Lib" / "site-packages"))
    import pcbnew as pcb

    assert pcb.GetBuildVersion() == "10.0.6"
    before = check.CopperGraph(pcb, args.baseline)
    after = check.CopperGraph(pcb, args.candidate)
    continuity = compare_components(before, after)
    assert not after.shorts and not after.floating_copper()
    errors = []
    topology = check.power_topology(before, after, errors)
    assert not errors, errors
    changed = set(stage["changes"])
    poses = lambda graph: {fp.GetReference(): (tuple(fp.GetPosition()), fp.GetOrientationDegrees())
                           for fp in graph.board.GetFootprints()}
    assert poses(before) == poses(after), "Component poses changed"
    for fp in after.board.GetFootprints():
        if fp.GetReference() in changed:
            lib = pcb.FootprintLoad(str(args.candidate.parent / "libraries" / "Handbell.pretty"),
                                   fp.GetFPID().GetLibItemName())
            assert lib and not fp.FootprintNeedsUpdate(lib), fp.GetReference()
            assert fp.GetAttributes() == pcb.FP_SMD
    old, new = records(before, pcb), records(after, pcb)
    assert old.keys() == new.keys(), "Copper primitive inventory changed"
    changed_tracks = {uid for uid in old if old[uid] != new[uid]}
    declared = {row["uuid"]: row for row in stage["copper_primitive_changes"]}
    assert changed_tracks == declared.keys(), "Undeclared track/via changes"
    for uid in changed_tracks:
        a, b = old[uid], new[uid]
        assert a["kind"] == b["kind"] == "segment"
        assert all(a[k] == b[k] for k in ("net", "layer", "width"))
        for key, label in (("a", "start"), ("b", "end")):
            for row, state in ((a, "before"), (b, "after")):
                assert all(abs(x + 100 - y) < 1e-6
                           for x, y in zip(row[key], declared[uid][state][label], strict=True))
    measure.np = numpy
    models = [measure.NativeWalk(check, pcb, path.parent, rows)
              for path, rows in ((args.baseline, old), (args.candidate, new))]
    adjacent = {(uid, pcb.F_Cu) for uid in changed_tracks}
    for graph in (before, after):
        for uid, pad in graph.pads.items():
            if pad.GetParentFootprint().GetReference() in changed:
                for key in graph.by_uuid[uid]:
                    adjacent.update(other for other in graph.adj[key]
                                    if other[0] in new and new[other[0]]["kind"] == "segment")
    exposure = []
    for key in sorted(adjacent):
        lengths = []
        for model, rows in zip(models, (old, new), strict=True):
            row = rows[key[0]]
            a, b = [tuple(v + 100 for v in row[k]) for k in ("a", "b")]
            _, pieces, _ = model.exposed(key, a, b)
            lengths.append(sum(v - u for u, v in pieces) * math.dist(a, b))
        exposure.append({"uuid": key[0], "net": new[key[0]]["net"],
                         "width_mm": new[key[0]]["width"],
                         "before_uncovered_mm": lengths[0], "after_uncovered_mm": lengths[1],
                         "increase_mm": lengths[1] - lengths[0]})
    report = {
        "status": "LOCAL_PRIMITIVE_CHECK_PASSED", "baseline_sha256": sha(args.baseline),
        "candidate_sha256": sha(args.candidate), "tool_sha256": sha(Path(__file__)),
        "helper_sha256": sha(Path(check.__file__)), "continuity": continuity,
        "component_poses_unchanged": True, "changed_footprint_library_matches": sorted(changed),
        "unchanged_primitive_inventory_and_widths": True, "changed_tracks": sorted(changed_tracks),
        "power_topology": topology, "primitive_only_exposure": exposure,
        "exposure_method_sha256": sha(Path(measure.__file__)),
        "scope": "Existing primitive connectivity/power guards plus actual before/after centerline exposure. Excludes zones; not resistance, ampacity, full DRC or functional approval.",
    }
    args.output.write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"status": report["status"], "changed_tracks": len(changed_tracks),
                      "measured_tracks": len(exposure)}))


if __name__ == "__main__":
    main()
