# SPDX-License-Identifier: MIT
"""Read-only bounded numerical screen for possible R14 relocation poses."""
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "hardware" / "handbell" / "iterations" / "printed-bell-clock-draft"
PCB_PATH = PACKAGE / "handbell.kicad_pcb"
MANIFEST_PATH = PACKAGE / "placement-manifest.json"
OUTPUT = ROOT / "docs" / "measurements" / "2026-09-21-r14-relocation-screen.json"
PCB_SHA = "a83cc417c96b05dd15c187e648b9fd2a35ba857c3a66f7d13aaaa42ae3bd9fff"
MANIFEST_SHA = "2b9ea13a6ae85d0f8d2ae09c74161e3122349e4ecb56c9aa760823cd88d9bb55"
EXCLUDED_UUID = "8b67bfa8-9f2d-5d11-b459-76494e6f41ef"
CLEARANCE_MM = 0.20


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mm(pcb, point):
    return [round(pcb.ToMM(v), 6) for v in point]


def rect(component, native_x=None, native_y=None, native_rotation=None):
    x = component["x_mm"] + 100 if native_x is None else native_x
    y = component["y_mm"] + 100 if native_y is None else native_y
    rotation = component["rotation_deg"] if native_rotation is None else -native_rotation
    angle = math.radians(rotation)
    w = abs(component["width_mm"] * math.cos(angle)) + abs(component["depth_mm"] * math.sin(angle))
    h = abs(component["width_mm"] * math.sin(angle)) + abs(component["depth_mm"] * math.cos(angle))
    return [x-w/2, y-h/2, x+w/2, y+h/2]


def overlaps(a, b):
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])


def nearest_point(pcb, item, point):
    if isinstance(item, pcb.PCB_TRACK) and not isinstance(item, pcb.PCB_VIA):
        a, b = mm(pcb, item.GetStart()), mm(pcb, item.GetEnd())
        vx, vy = b[0]-a[0], b[1]-a[1]
        d2 = vx*vx + vy*vy
        t = 0 if d2 == 0 else max(0, min(1, ((point[0]-a[0])*vx + (point[1]-a[1])*vy)/d2))
        q = [a[0]+t*vx, a[1]+t*vy]
    else:
        q = mm(pcb, item.GetPosition())
    return [round(q[0], 6), round(q[1], 6)], math.hypot(point[0]-q[0], point[1]-q[1])


def identity(item):
    if hasattr(item, "GetParentFootprint") and item.GetParentFootprint():
        fp = item.GetParentFootprint()
        return f"{fp.GetReference()}.{item.GetNumber()}"
    return item.m_Uuid.AsString()


def main():
    started = time.perf_counter()
    if sha(PCB_PATH) != PCB_SHA or sha(MANIFEST_PATH) != MANIFEST_SHA or OUTPUT.exists():
        raise ValueError("Pinned inputs changed or output already exists")
    native = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin"
    dll_handle = os.add_dll_directory(str(native))
    sys.path.insert(0, str(native / "Lib" / "site-packages"))
    import pcbnew as pcb
    if pcb.GetBuildVersion() != "10.0.6":
        raise ValueError("KiCad 10.0.6 required")

    board = pcb.LoadBoard(str(PCB_PATH))
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    r14 = fps["R14"]
    pads = {p.GetNumber(): p for p in r14.Pads()}
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    components = {c["reference"]: c for c in manifest["components"]}
    front_components = [c for c in manifest["components"] if c["side"] == "F" and c["reference"] != "R14"]

    obstacles = []
    for footprint in board.GetFootprints():
        if footprint.GetReference() == "R14":
            continue
        obstacles.extend(p for p in footprint.Pads() if p.IsOnLayer(pcb.F_Cu))
    obstacles.extend(t for t in board.GetTracks()
                     if t.IsOnLayer(pcb.F_Cu) and t.m_Uuid.AsString() != EXCLUDED_UUID)

    courtyard_shapes = {}
    courtyard_missing = []
    for ref, footprint in fps.items():
        if ref == "R14" or footprint.GetLayer() != pcb.F_Cu:
            continue
        footprint.BuildCourtyardCaches()
        shape = footprint.GetCourtyard(pcb.F_CrtYd)
        if shape.OutlineCount():
            courtyard_shapes[ref] = shape
        else:
            courtyard_missing.append(ref)

    same_net = {net: [o for o in obstacles if o.GetNetname() == net]
                for net in ("SCL", "+3V3")}
    scanned = pad_pass = body_pass = 0
    viable = []
    pad_rejects = {}
    body_rejects = {}
    xs = [90.8 + .25*i for i in range(13)]
    ys = [90.8 + .25*i for i in range(18)]
    for x in xs:
        for y in ys:
            for rotation in (0, 90, 180, 270):
                scanned += 1
                r14.SetPosition(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y)))
                r14.SetOrientationDegrees(rotation)
                collision = None
                for number, pad in pads.items():
                    for obstacle in obstacles:
                        if obstacle.GetNetname() == pad.GetNetname():
                            continue
                        if pad.GetEffectiveShape(pcb.F_Cu).Collide(
                                obstacle.GetEffectiveShape(pcb.F_Cu), pcb.FromMM(CLEARANCE_MM)):
                            collision = f"R14.{number}/{identity(obstacle)}"
                            break
                    if collision:
                        break
                if collision:
                    pad_rejects[collision] = pad_rejects.get(collision, 0) + 1
                    continue
                pad_pass += 1

                proxy = rect(components["R14"], x, y, rotation)
                proxy_hit = next((c["reference"] for c in front_components
                                  if overlaps(proxy, rect(c))), None)
                if proxy_hit:
                    body_rejects["proxy/"+proxy_hit] = body_rejects.get("proxy/"+proxy_hit, 0) + 1
                    continue
                r14.BuildCourtyardCaches()
                candidate_courtyard = r14.GetCourtyard(pcb.F_CrtYd)
                native_hit = next((ref for ref, shape in courtyard_shapes.items()
                                   if candidate_courtyard.Collide(shape, 0)), None)
                if native_hit:
                    body_rejects["courtyard/"+native_hit] = body_rejects.get("courtyard/"+native_hit, 0) + 1
                    continue
                body_pass += 1

                links = {}
                total = 0.0
                for number, net in (("2", "SCL"), ("1", "+3V3")):
                    point = mm(pcb, pads[number].GetPosition())
                    choices = []
                    for primitive in same_net[net]:
                        q, distance = nearest_point(pcb, primitive, point)
                        choices.append((distance, primitive, q))
                    distance, primitive, q = min(choices, key=lambda value: value[0])
                    total += distance
                    direct = pcb.PCB_TRACK(board)
                    direct.SetLayer(pcb.F_Cu)
                    direct.SetWidth(pcb.FromMM(.20))
                    direct.SetStart(pads[number].GetPosition())
                    direct.SetEnd(pcb.VECTOR2I(pcb.FromMM(q[0]), pcb.FromMM(q[1])))
                    direct.SetNetCode(pads[number].GetNetCode())
                    crossings = []
                    for obstacle in obstacles:
                        if obstacle.GetNetname() == net or obstacle is primitive:
                            continue
                        if direct.GetEffectiveShape(pcb.F_Cu).Collide(
                                obstacle.GetEffectiveShape(pcb.F_Cu), pcb.FromMM(CLEARANCE_MM)):
                            crossings.append({
                                "uuid": obstacle.m_Uuid.AsString(),
                                "identity": identity(obstacle),
                                "net": obstacle.GetNetname(),
                            })
                    links[net] = {
                        "candidate_pad": f"R14.{number}",
                        "pad_center_mm": point,
                        "nearest_primitive_uuid": primitive.m_Uuid.AsString(),
                        "nearest_primitive_identity": identity(primitive),
                        "nearest_point_mm": q,
                        "raw_centerline_distance_mm": distance,
                        "direct_f_segment_width_mm": .20,
                        "direct_f_segment_other_net_collisions": crossings,
                    }
                viable.append({
                    "center_mm": [round(x, 6), round(y, 6)],
                    "rotation_deg": rotation,
                    "pad_positions_mm": {"R14.1_+3V3": mm(pcb, pads["1"].GetPosition()),
                                         "R14.2_SCL": mm(pcb, pads["2"].GetPosition())},
                    "rank_sum_raw_distance_mm": total,
                    "links": links,
                })

    viable.sort(key=lambda value: value["rank_sum_raw_distance_mm"])
    report = {
        "status": "READ_ONLY_NUMERICAL_PLACEMENT_SCREEN",
        "input_pcb_sha256": PCB_SHA,
        "input_manifest_sha256": MANIFEST_SHA,
        "native_version": pcb.GetBuildVersion(),
        "accepted_board_modified": False,
        "candidate_pcb_written": False,
        "screen": {
            "bounds_native_mm": [90.8, 90.8, 94.0, 95.2],
            "lattice_mm": .25,
            "rotations_deg": [0, 90, 180, 270],
            "maximum_poses": 1000,
            "total_scanned": scanned,
            "pad_pass": pad_pass,
            "body_courtyard_pass": body_pass,
            "foreign_copper_clearance_mm": CLEARANCE_MM,
            "excluded_old_immediate_supply_spur_uuid": EXCLUDED_UUID,
        },
        "filters": {
            "pad": "Native effective F.Cu pad shapes against all non-R14 F.Cu pads/tracks of other or blank nets; same-net copper permitted.",
            "body": "Existing placement-manifest component-envelope proxy plus native F.Courtyard polygon collision where available; reference/value text excluded.",
            "ranking": "Sum of Euclidean pad-center distance to nearest centerline/center point of existing same-net F.Cu pad/track/via primitive.",
            "direct_segment": "0.20 mm F.Cu segment tested at 0.20 mm native effective-shape clearance against other/blank-net pads and tracks; no path search.",
        },
        "incomplete_evidence": {
            "body_proxy_screening_only": True,
            "native_courtyard_missing_for_front_references": sorted(courtyard_missing),
            "filled_zone_GND_implications": "INCOMPLETE: filled-zone shapes were not included; local GND groups must not be assumed continuous.",
            "qualification": "Pad/body screening only; no placement is approved, usable, routed, or DRC-clean.",
        },
        "top3": viable[:3],
        "viable_pose_count": len(viable),
        "leading_pad_rejections": sorted(pad_rejects.items(), key=lambda x: -x[1])[:8],
        "leading_body_rejections": sorted(body_rejects.items(), key=lambda x: -x[1])[:8],
        "timing_seconds": round(time.perf_counter()-started, 3),
        "tool": "tools/experiments/screen_r14_relocation.py",
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    assert dll_handle is not None
    print(json.dumps({"scanned": scanned, "pad_pass": pad_pass, "body_pass": body_pass,
                      "viable": len(viable), "top3": viable[:3],
                      "seconds": report["timing_seconds"]}, separators=(",", ":")))


if __name__ == "__main__":
    main()
