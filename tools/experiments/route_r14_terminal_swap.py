# SPDX-License-Identifier: MIT
"""Read-only diagnostic reproduction of the last R14 terminal-swap search."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "experiments"))
import route_core_distribution as routing

PACKAGE = ROOT / "hardware" / "handbell" / "iterations" / "printed-bell-clock-draft"
BASE = "a83cc417c96b05dd15c187e648b9fd2a35ba857c3a66f7d13aaaa42ae3bd9fff"
REMOVE = (
    "548c8552-ff4c-56b3-83d9-9d0a5389e3e2",
    "76a37864-74d8-5963-bcc4-18eb043accfd",
    "8b67bfa8-9f2d-5d11-b459-76494e6f41ef",
)
DIAGNOSTIC_NAME = "r14-terminal-swap-diagnostic.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mm(pcb, point):
    return [round(pcb.ToMM(value), 6) for value in point]


def persist(path, diagnostic):
    path.write_text(
        json.dumps(diagnostic, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="new directory for diagnostic JSON only")
    args = parser.parse_args()
    out = args.output.resolve()
    board_path = PACKAGE / "handbell.kicad_pcb"
    if out.exists() or sha(board_path) != BASE:
        raise ValueError("Require pinned source and a new output directory")
    out.mkdir(parents=True)
    diagnostic_path = out / DIAGNOSTIC_NAME

    native = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin"
    dll_directory_handle = os.add_dll_directory(str(native))
    sys.path.insert(0, str(native / "Lib" / "site-packages"))
    import pcbnew as pcb

    if pcb.GetBuildVersion() != "10.0.6":
        raise ValueError("KiCad 10.0.6 required")

    board = pcb.LoadBoard(str(board_path))
    footprints = {footprint.GetReference(): footprint for footprint in board.GetFootprints()}
    r14 = footprints["R14"]
    assert mm(pcb, r14.GetPosition()) == [87.094469, 94.71803]
    assert round(r14.GetOrientationDegrees(), 6) == 90
    pads = {
        footprint.GetReference() + "." + pad.GetNumber(): pad
        for footprint in board.GetFootprints()
        for pad in footprint.Pads()
    }
    assert pads["R14.1"].GetNetname() == "+3V3"
    assert pads["R14.2"].GetNetname() == "SCL"

    r14.SetOrientationDegrees(270)
    transform = {
        "center_mm": mm(pcb, r14.GetPosition()),
        "rotation_deg": round(r14.GetOrientationDegrees(), 6),
        "pad1_mm": mm(pcb, pads["R14.1"].GetPosition()),
        "pad2_mm": mm(pcb, pads["R14.2"].GetPosition()),
    }
    assert transform == {
        "center_mm": [87.094469, 94.71803],
        "rotation_deg": 270.0,
        "pad1_mm": [87.094469, 94.21003],
        "pad2_mm": [87.094469, 95.22603],
    }

    expected = {
        REMOVE[0]: ([87.8697, 93.4927], [87.8697, 94.9461]),
        REMOVE[1]: ([87.8697, 94.9461], [87.5898, 95.226]),
        REMOVE[2]: ([87.0945, 95.226], [87.5898, 95.226]),
    }
    by_id = {track.m_Uuid.AsString(): track for track in board.GetTracks()}
    removed = []
    for uid in REMOVE:
        track = by_id[uid]
        endpoints = (mm(pcb, track.GetStart()), mm(pcb, track.GetEnd()))
        assert track.GetNetname() == "+3V3"
        assert pcb.ToMM(track.GetWidth()) == 0.1778
        assert endpoints == expected[uid]
        removed.append({"uuid": uid, "start_mm": endpoints[0], "end_mm": endpoints[1]})
        board.Remove(track)

    routing.ROUTING_BOUNDS = (-14.5, -9.0, -6.5, -2.0)
    routing.SEARCH_LIMIT = 80000
    router = routing.NativeRouter(board, pcb)
    diagnostic = {
        "status": "READ_ONLY_DIAGNOSTIC_NOT_RUN",
        "input_pcb_sha256": BASE,
        "output_pcb_written": False,
        "candidate_accepted": False,
        "native_transform_verified_in_memory": transform,
        "removed_tracks_verified_and_removed_in_memory_only": removed,
        "search_bounds_native_mm": [85.5, 91.0, 93.5, 98.0],
        "grid_mm": 0.05,
        "clearance_mm": 0.2,
        "front_only": True,
        "searches": [],
        "note": (
            "Any returned proposal is an in-memory path pending native/filled "
            "acceptance; this diagnostic emits no PCB."
        ),
    }

    def search(label, start, end, net):
        path = router.search(
            [value - 100 for value in start],
            [value - 100 for value in end],
            net,
            0.2,
            False,
            6,
            expansion_limit=80000,
        )
        diagnostic["searches"].append(
            {
                "connection": label,
                "result": (
                    "SEARCH_RETURNED_NO_PATH"
                    if path is None
                    else "IN_MEMORY_PATH_ONLY_PENDING_ACCEPTANCE"
                ),
                "statistics": router.last_search_statistics,
            }
        )
        diagnostic["status"] = (
            "UNSUCCESSFUL_SEARCH_RETURNED_NO_PATH"
            if path is None
            else "IN_MEMORY_PATH_ONLY_PENDING_ACCEPTANCE"
        )
        persist(diagnostic_path, diagnostic)
        return path

    supply_path = search(
        "R14.1 to +3V3 via 1c15a7a2",
        [87.094469, 94.21003],
        [87.9, 93.6],
        "+3V3",
    )
    if supply_path is None:
        print("Unsuccessful: +3V3 search returned no path.", file=sys.stderr)
        return 1
    router.add_path(supply_path, "+3V3", 0.2, "R14.1 supply proposal")
    for track in router.tracks:
        item = pcb.PCB_TRACK(board)
        item.SetLayer(pcb.F_Cu)
        item.SetWidth(pcb.FromMM(track["width"]))
        item.SetNetCode(pads["R14.1"].GetNetCode())
        item.SetStart(pcb.VECTOR2I(*(pcb.FromMM(v + 100) for v in track["a"])))
        item.SetEnd(pcb.VECTOR2I(*(pcb.FromMM(v + 100) for v in track["b"])))
        board.Add(item)
        router.obstacles.append(item)

    anchor = mm(pcb, pads["IC4.13"].GetPosition())
    assert anchor == [90.412306, 93.992711]
    scl_path = search(
        "historical last attempt: R14.2 to closer IC4.13 SCL terminal",
        [87.094469, 95.22603],
        anchor,
        "SCL",
    )
    if scl_path is None:
        print("Unsuccessful: closer SCL target search returned no path.", file=sys.stderr)
        return 1

    # Keep the DLL search path registration alive through all native operations.
    assert dll_directory_handle is not None
    print(
        "Diagnostic found an in-memory path pending native/filled acceptance; no PCB written."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
