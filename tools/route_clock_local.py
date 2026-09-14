# SPDX-License-Identifier: MIT
"""Add only the first local clock connections to the pinned definition stage."""
import hashlib
import json
import os
from pathlib import Path
import sys
import uuid

from kicad_sexpr import apply_edits, load

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "hardware" / "handbell" / "iterations" / "printed-bell-clock-draft"
INPUT_SHA = "6b26bcc4a43f4af0e1a5c507c8dfc987c025bd45b4dec51748df75bb5bc99192"
SCHEMATIC_SHA = "51fec9d33a95ea712f26df13689ce1321f0c6084110fef97cd927fdc0ea4f865"
ROUTES = [
    ("C2.2", "Y1.3", .1778,
     [(90.9036, 96.55245), (91.899655, 96.55245), (92.199801, 96.852596)]),
    ("C3.2", "Y1.1", .1778,
     [(90.899181, 99.599331), (90.899181, 100.1), (93.2, 100.1),
      (93.949801, 99.350199), (93.949801, 99.152596)]),
    ("Y1.1", "R6.1", .1778,
     [(93.949801, 99.152596), (94.6, 99.152596),
      (95.161305, 99.713901), (95.175414, 99.713901)]),
    ("C2.1", "C3.1", .2,
     [(90.9036, 97.35245), (90.9036, 98.794912), (90.899181, 98.799331)]),
    ("C3.1", "Y1.4", .2,
     [(90.899181, 98.799331), (91.846536, 98.799331), (92.199801, 99.152596)]),
    ("IC1.19", "IC1.P$1", .1778,
     [(96.55, 99.0), (100.0, 99.0), (100.0, 100.0)]),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    path = PACKAGE / "handbell.kicad_pcb"
    if sha(path) != INPUT_SHA or sha(PACKAGE / "handbell.kicad_sch") != SCHEMATIC_SHA:
        raise ValueError("Pinned clock inputs changed; no overwrite permitted")
    report_path = PACKAGE / "reports" / "clock-local-routing.json"
    if report_path.exists():
        raise ValueError("Existing routing report refused")
    folder = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin"
    dll_handle = os.add_dll_directory(str(folder))
    sys.path.insert(0, str(folder / "Lib" / "site-packages"))
    import pcbnew as pcb
    from check_printed_bell_power_rework import CopperGraph

    if pcb.GetBuildVersion() != "10.0.6":
        raise ValueError("KiCad 10.0.6 required")
    board = pcb.LoadBoard(str(path))
    pads = {f.GetReference() + "." + p.GetNumber(): p
            for f in board.GetFootprints() for p in f.Pads()
            if f.GetReference() in ("Y1", "C2", "C3", "R6", "IC1")}
    obstacles = [p for f in board.GetFootprints() for p in f.Pads()]
    obstacles += list(board.GetTracks())
    additions, records, inserted = [], [], []
    for route_index, (start, end, width, points) in enumerate(ROUTES):
        a, b = pads[start], pads[end]
        if not a.GetNetname() or a.GetNetname() != b.GetNetname():
            raise ValueError("Different endpoint nets: " + start + " / " + end)
        for pad, point in ((a, points[0]), (b, points[-1])):
            actual = tuple(round(pcb.ToMM(v), 6) for v in pad.GetPosition())
            if actual != point:
                raise ValueError("Endpoint moved: " + start + " / " + end)
        for index, (p, q) in enumerate(zip(points, points[1:])):
            track = pcb.PCB_TRACK(board)
            track.SetLayer(pcb.F_Cu)
            track.SetWidth(pcb.FromMM(width))
            track.SetStart(pcb.VECTOR2I(*(pcb.FromMM(v) for v in p)))
            track.SetEnd(pcb.VECTOR2I(*(pcb.FromMM(v) for v in q)))
            track.SetNetCode(a.GetNetCode())
            identifier = str(uuid.uuid5(uuid.NAMESPACE_URL,
                                       f"digital-handbell/clock-local/{route_index}/{index}"))
            shape = track.GetEffectiveShape(pcb.F_Cu)
            for obstacle in obstacles:
                if (not obstacle.IsOnLayer(pcb.F_Cu)
                        or obstacle.GetNetname() == a.GetNetname()):
                    continue
                if shape.Collide(obstacle.GetEffectiveShape(pcb.F_Cu), pcb.FromMM(.2)):
                    raise ValueError(f"Conservative 0.20 mm copper screen failed: {start}/{end} "
                                     f"segment {index} vs {obstacle.m_Uuid.AsString()}")
            obstacles.append(track)
            inserted.append(track)
            additions.append(
                f'\n(segment (start {p[0]} {p[1]}) (end {q[0]} {q[1]}) '
                f'(width {width}) (layer "F.Cu") (net {json.dumps(a.GetNetname())}) '
                f'(uuid "{identifier}"))')
            records.append({"uuid": identifier, "from": start, "to": end,
                            "net": a.GetNetname(), "start_mm": p, "end_mm": q,
                            "width_mm": width, "layer": "F.Cu"})

    # Native in-memory connectivity proof without saving/reformatting existing copper.
    for track in inserted:
        board.Add(track)

    class MemoryApi:
        def __getattr__(self, name):
            return getattr(pcb, name)

        def LoadBoard(self, unused):
            return board

    graph = CopperGraph(MemoryApi(), "<clock-local-memory>")
    for start, end, _, _ in ROUTES:
        a, b = start.split("."), end.split(".")
        if not graph.connected(graph.pad_uuid(*a), graph.pad_uuid(*b)):
            raise ValueError("Native physical connection absent: " + start + " / " + end)
    text, tree = load(path)
    output = apply_edits(text, [(tree.end - 1, tree.end - 1, "".join(additions))])
    if sha(path) != INPUT_SHA:
        raise ValueError("Source changed during inspection")
    path.write_bytes(output.encode("utf-8"))
    manifest_path = PACKAGE / "placement-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    manifest.update(generated_pcb_sha256=sha(path),
                    status="CLOCK_LOCAL_CONNECTIONS_PARTIAL_NO_ZONE_REFILL",
                    routing_report="reports/clock-local-routing.json",
                    mechanical_rebind_required=True)
    manifest_path.write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    report = {
        "status": manifest["status"], "kicad_version": pcb.GetBuildVersion(),
        "input_pcb_sha256": INPUT_SHA, "input_commit": "702f53b",
        "output_pcb_sha256": sha(path), "schematic_sha256": SCHEMATIC_SHA,
        "generator_sha256": sha(Path(__file__)),
        "changed_footprints": [], "removed_tracks": [], "new_vias": [],
        "added_tracks": records, "new_track_foreign_copper_screen_mm": .2,
        "native_connected_pairs": [[a, b] for a, b, _, _ in ROUTES],
        "limitations": [
            "Local primitive copper screen and physical connectivity, not full DRC/DFM approval.",
            "No zone refill; zone outlines are not counted as connected copper.",
            "XIN and XOUT MCU approaches remain unrouted.",
            "Y1.2 and the C2/C3/Y1.4 return island still need protected-ground connections.",
            "Three Clock library footprint mismatch warnings need separate resolution.",
            "No finished mechanical rebinding, fabrication or quotation package."
        ],
    }
    report_path.write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"tracks_added": len(records), "pcb_sha256": sha(path),
                      "status": report["status"]}, indent=2))
    dll_handle.close()


if __name__ == "__main__":
    main()
