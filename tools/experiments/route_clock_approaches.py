# SPDX-License-Identifier: MIT
"""Blocked all-front clock proposal; C3 clearance gate rejects it before writing."""
import hashlib
import faulthandler
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kicad_sexpr import apply_edits, load
from route_clock_local import PACKAGE

INPUT_SHA = "9472e9887da88826fe8cfa1145ab53afb8adba2a0a5fbf20d6fc45d90f85acc6"
POSES = {
    "Y1": (92.574801, 98.002596, 90),
    "C2": (90.603600, 96.952450, 90),
    "C3": (90.599181, 99.199331, 270),
    "R6": (94.825414, 99.205901, 270),
}
# Endpoints are taken from the moved native pads, not duplicated coordinates.
ROUTES = [
    ("C2.2", "Y1.3", .1778, [(91.399655, 96.552450)]),
    ("C3.2", "Y1.1", .1778,
     [(90.599181, 100.1), (92.7, 100.1), (93.449801, 99.350199)]),
    ("Y1.1", "R6.1", .1778,
     [(94.30, 99.152596), (94.754695, 98.697901)]),
    ("C2.1", "C3.1", .2, [(90.603600, 98.794912)]),
    ("C3.1", "Y1.4", .2, [(91.346536, 98.799331)]),
    ("Y1.3", "IC1.20", .1778,
     [(91.699801, 97.9), (95.42, 97.9), (95.42, 99.4)]),
    ("IC1.21", "R6.2", .1778, [(94.911513, 99.8)]),
    ("C2.1", "Y1.2", .2,
     [(89.95, 97.352450), (89.95, 95.90), (90.25, 95.60), (93.449801, 95.60)]),
    ("Y1.2", "IC1.19", .1778,
     [(95.3, 96.852596), (95.81, 97.362596), (95.81, 99.0)]),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, value):
    path.write_bytes((json.dumps(value, indent=2) + "\n").encode("utf-8"))


def bounds(c):
    angle = math.radians(c["rotation_deg"])
    w = abs(c["width_mm"] * math.cos(angle)) + abs(c["depth_mm"] * math.sin(angle))
    d = abs(c["width_mm"] * math.sin(angle)) + abs(c["depth_mm"] * math.cos(angle))
    return c["x_mm"] - w/2, c["x_mm"] + w/2, c["y_mm"] - d/2, c["y_mm"] + d/2


def main():
    faulthandler.enable()
    path = PACKAGE / "handbell.kicad_pcb"
    report_path = PACKAGE / "reports" / "clock-approaches.json"
    if sha(path) != INPUT_SHA or report_path.exists():
        raise ValueError("Pinned input changed or output exists; refusing overwrite")
    text, tree = load(path)
    manifest_path = PACKAGE / "placement-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    prior = json.loads((PACKAGE / "reports" / "clock-local-routing.json").read_text(encoding="utf-8"))
    removed_ids = {t["uuid"] for t in prior["added_tracks"] if t["from"] != "IC1.19"}
    edits, movements = [], []
    for fp in tree.children("footprint"):
        ref = fp.properties()["Reference"]
        if ref not in POSES:
            continue
        node = fp.child("at")
        old = list(map(float, node.atoms()[1:]))
        new = POSES[ref]
        edits.append((node.start, node.end, f"(at {new[0]} {new[1]} {new[2]})"))
        c = next(c for c in manifest["components"] if c["reference"] == ref)
        dx, dy = c["x_mm"] - (old[0]-100), c["y_mm"] - (old[1]-100)
        a = math.radians(old[2]-new[2])
        c.update(x_mm=new[0]-100+dx*math.cos(a)-dy*math.sin(a),
                 y_mm=new[1]-100+dx*math.sin(a)+dy*math.cos(a),
                 rotation_deg=-new[2], native_origin_common_xy_mm=[new[0]-100, new[1]-100])
        manifest["electrical_landmarks"]["core"][ref] = [new[0]-100, new[1]-100, new[2]]
        movements.append({"reference": ref, "old_native_pose": old, "new_native_pose": new})
    for c in manifest["components"]:
        if c["reference"] not in POSES:
            continue
        a = bounds(c)
        if any(math.hypot(x, y) >= 21.5 for x in a[:2] for y in a[2:]):
            raise ValueError("Moved clock envelope leaves D43")
        for other in manifest["components"]:
            if other["side"] != c["side"] or other["reference"] == c["reference"]:
                continue
            b = bounds(other)
            if max(a[0], b[0]) < min(a[1], b[1]) and max(a[2], b[2]) < min(a[3], b[3]):
                raise ValueError(f"Screening envelope overlap: {c['reference']}/{other['reference']}")

    folder = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin"
    dll_handle = os.add_dll_directory(str(folder))
    sys.path.insert(0, str(folder / "Lib" / "site-packages"))
    import pcbnew as pcb
    from check_printed_bell_power_rework import CopperGraph
    if pcb.GetBuildVersion() != "10.0.6":
        raise ValueError("KiCad 10.0.6 required")
    found = set()
    for n in tree.children("segment"):
        if n.value("uuid") in removed_ids:
            found.add(n.value("uuid"))
            edits.append((n.start, n.end, ""))
    if found != removed_ids:
        raise ValueError("Old local-clock segment inventory differs")
    # Reload the staged text instead of mutating SWIG-owned board collections.
    with tempfile.TemporaryDirectory(prefix="handbell-clock-") as temporary:
        staged = Path(temporary) / "clock.kicad_pcb"
        staged.write_bytes(apply_edits(text, edits).encode("utf-8"))
        board = pcb.LoadBoard(str(staged))
    pads = {f.GetReference()+"."+p.GetNumber(): p
            for f in board.GetFootprints() for p in f.Pads()
            if f.GetReference() in set(POSES) | {"IC1"}}
    obstacles = [p for f in board.GetFootprints() for p in f.Pads()] + list(board.GetTracks())
    # Screen moved pads as well as tracks, including unassigned metal.
    for name, pad in pads.items():
        if name.split(".")[0] not in POSES:
            continue
        for other in obstacles:
            if not other.IsOnLayer(pcb.F_Cu) or other.GetNetname() == pad.GetNetname():
                continue
            if pad.GetEffectiveShape(pcb.F_Cu).Collide(other.GetEffectiveShape(pcb.F_Cu),
                                                     pcb.FromMM(.2)):
                raise ValueError("Moved-pad copper clearance: "+name+" / "+other.m_Uuid.AsString())
    additions, records = [], []
    for route_index, (start, end, width, middle) in enumerate(ROUTES):
        a, b = pads[start], pads[end]
        if not a.GetNetname() or a.GetNetname() != b.GetNetname():
            raise ValueError("Route endpoints have different nets")
        points = [tuple(round(pcb.ToMM(v), 6) for v in a.GetPosition()),
                  *middle, tuple(round(pcb.ToMM(v), 6) for v in b.GetPosition())]
        for index, (p, q) in enumerate(zip(points, points[1:])):
            track = pcb.PCB_TRACK(board)
            track.SetLayer(pcb.F_Cu)
            track.SetWidth(pcb.FromMM(width))
            track.SetStart(pcb.VECTOR2I(*(pcb.FromMM(v) for v in p)))
            track.SetEnd(pcb.VECTOR2I(*(pcb.FromMM(v) for v in q)))
            track.SetNetCode(a.GetNetCode())
            identifier = str(uuid.uuid5(uuid.NAMESPACE_URL,
                                       f"digital-handbell/clock-approaches/{route_index}/{index}"))
            for other in obstacles:
                if not other.IsOnLayer(pcb.F_Cu) or other.GetNetname() == a.GetNetname():
                    continue
                if track.GetEffectiveShape(pcb.F_Cu).Collide(other.GetEffectiveShape(pcb.F_Cu),
                                                           pcb.FromMM(.2)):
                    raise ValueError(f"Track clearance: {start}/{end} segment {index} / "
                                     + other.m_Uuid.AsString())
            obstacles.append(track)
            board.Add(track)
            additions.append(f'\n(segment (start {p[0]} {p[1]}) (end {q[0]} {q[1]}) '
                             f'(width {width}) (layer "F.Cu") (net {json.dumps(a.GetNetname())}) '
                             f'(uuid "{identifier}"))')
            records.append({"uuid": identifier, "from": start, "to": end, "start_mm": p,
                            "end_mm": q, "net": a.GetNetname(), "width_mm": width, "layer": "F.Cu"})

    class MemoryApi:
        def __getattr__(self, name):
            return getattr(pcb, name)

        def LoadBoard(self, unused):
            return board

    graph = CopperGraph(MemoryApi(), "<clock-approaches-memory>")
    pairs = [(a, b) for a, b, _, _ in ROUTES]
    pairs += [(ref, "IC1.P$1") for ref in ("Y1.2", "Y1.4", "C2.1", "C3.1")]
    for a, b in pairs:
        if not graph.connected(graph.pad_uuid(*a.split(".")), graph.pad_uuid(*b.split("."))):
            raise ValueError("Missing physical route: "+a+"/"+b)
        if not graph.path(graph.pad_uuid(*a.split(".")), graph.pad_uuid(*b.split(".")), pcb.F_Cu):
            raise ValueError("Connection depends on rear copper: "+a+"/"+b)
    if sha(path) != INPUT_SHA:
        raise ValueError("Input changed during operation")
    edits.append((tree.end-1, tree.end-1, "".join(additions)))
    path.write_bytes(apply_edits(text, edits).encode("utf-8"))
    manifest.update(generated_pcb_sha256=sha(path), status="CLOCK_CLUSTER_ROUTED_GLOBAL_GATES_OPEN",
                    current_stage_report="reports/clock-approaches.json", mechanical_rebind_required=True)
    save_json(manifest_path, manifest)
    report = {"input_commit": "1a83d8c", "input_pcb_sha256": INPUT_SHA,
              "output_pcb_sha256": sha(path), "placement_manifest_sha256": sha(manifest_path),
              "generator_sha256": sha(Path(__file__)), "kicad_version": pcb.GetBuildVersion(),
              "movements": movements, "removed_local_segment_uuids": sorted(removed_ids),
              "added_segments": records, "new_vias": [], "native_all_front_connected_pairs": pairs,
              "native_foreign_copper_screen_mm": .2, "component_envelope_screen": "No same-face AABB overlaps; moved envelopes within D43",
              "limits": ["Nominal screening geometry, not full mechanical rebinding or assembly acceptance.",
                         "No B copper or vias added because the negative contact/base lies behind the cluster.",
                         "Zone refill/global routing/USB and other part revisions remain incomplete.",
                         "Clock startup/drive/frequency and low-cell behavior still require powered evaluation."]}
    save_json(report_path, report)
    print(json.dumps({"pcb_sha256": sha(path), "added_tracks": len(records),
                      "removed_local_tracks": len(removed_ids), "new_vias": 0}, indent=2))
    dll_handle.close()


if __name__ == "__main__":
    main()
