#!/usr/bin/env python3
"""Resolve saved private-guard AABB candidates with exact primitive geometry.

This is deliberately static: it consumes only source-bound JSON evidence and
uses no pcbnew, KiCad file parser, board load, or third-party geometry package.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

EPS = 1e-9
BOUNDARY = {
    "8b095e6c-ce66-5915-a589-2b1a247f9129": "C28.2 reviewed ordinary-GND boundary join",
    "665297da-57ea-5e05-aa18-5a3aa335eedd": "R27.2 reviewed ordinary-GND boundary join",
}
EXPECTED_INPUTS = {
    "repair": "f15a7743c8f5bcc205f2fabac34dd44d1901ce5c07a6204ad3b34c5085120d94",
    "inventory": "edba323c00da212fd881be71cc98f5d1afd8d8ca15ac4545c4b79bf609a7b7ba",
    "connectivity": "079b47d115db668be0fd8af196b20bfea316193426eca36398dbc98dae0ee23d",
    "retained": "639a7f81136e9e38319a55ac5d84dff42dfaaa08fe909ac87a68053fbefe23a9",
}
EXPECTED_FULL_GEOMETRY_SUPPLEMENT = (
    "4f5d16f9b631b2d01e3af7e1039dad2638462e76850bdbe6a45e4dea7ae9c72e"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def point_segment_distance(p, a, b):
    ab = sub(b, a)
    den = dot(ab, ab)
    if den <= EPS:
        return math.dist(p, a)
    t = max(0.0, min(1.0, dot(sub(p, a), ab) / den))
    return math.dist(p, (a[0] + t * ab[0], a[1] + t * ab[1]))


def on_segment(p, a, b):
    return abs(cross(sub(p, a), sub(b, a))) <= EPS and (
        min(a[0], b[0]) - EPS <= p[0] <= max(a[0], b[0]) + EPS
        and min(a[1], b[1]) - EPS <= p[1] <= max(a[1], b[1]) + EPS
    )


def segments_intersect(a, b, c, d):
    ab, ac, ad = sub(b, a), sub(c, a), sub(d, a)
    cd, ca, cb = sub(d, c), sub(a, c), sub(b, c)
    c1, c2, c3, c4 = cross(ab, ac), cross(ab, ad), cross(cd, ca), cross(cd, cb)
    if ((c1 > EPS and c2 < -EPS) or (c1 < -EPS and c2 > EPS)) and (
        (c3 > EPS and c4 < -EPS) or (c3 < -EPS and c4 > EPS)
    ):
        return True
    return (
        (abs(c1) <= EPS and on_segment(c, a, b))
        or (abs(c2) <= EPS and on_segment(d, a, b))
        or (abs(c3) <= EPS and on_segment(a, c, d))
        or (abs(c4) <= EPS and on_segment(b, c, d))
    )


def segment_segment_distance(a, b, c, d):
    if segments_intersect(a, b, c, d):
        return 0.0
    return min(
        point_segment_distance(a, c, d),
        point_segment_distance(b, c, d),
        point_segment_distance(c, a, b),
        point_segment_distance(d, a, b),
    )


def rect_corners(center, size, rotation_deg):
    hx, hy = size[0] / 2.0, size[1] / 2.0
    angle = math.radians(rotation_deg)
    ca, sa = math.cos(angle), math.sin(angle)
    return [
        (center[0] + x * ca - y * sa, center[1] + x * sa + y * ca)
        for x, y in [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
    ]


def point_in_convex(p, poly):
    signs = []
    for i, a in enumerate(poly):
        value = cross(sub(poly[(i + 1) % len(poly)], a), sub(p, a))
        if abs(value) > EPS:
            signs.append(value > 0)
    return not signs or all(x == signs[0] for x in signs)


def segment_rect_distance(a, b, rect):
    if point_in_convex(a, rect) or point_in_convex(b, rect):
        return 0.0
    edges = [(rect[i], rect[(i + 1) % 4]) for i in range(4)]
    return min(segment_segment_distance(a, b, c, d) for c, d in edges)


def rect_rect_distance(a, b):
    if any(point_in_convex(p, b) for p in a) or any(point_in_convex(p, a) for p in b):
        return 0.0
    ea = [(a[i], a[(i + 1) % 4]) for i in range(4)]
    eb = [(b[i], b[(i + 1) % 4]) for i in range(4)]
    return min(segment_segment_distance(*x, *y) for x in ea for y in eb)


def core_distance(a, b):
    if a["core"] == "segment" and b["core"] == "segment":
        return segment_segment_distance(a["a"], a["b"], b["a"], b["b"])
    if a["core"] == "rect" and b["core"] == "segment":
        return segment_rect_distance(b["a"], b["b"], a["corners"])
    if a["core"] == "segment" and b["core"] == "rect":
        return segment_rect_distance(a["a"], a["b"], b["corners"])
    if a["core"] == "rect" and b["core"] == "rect":
        return rect_rect_distance(a["corners"], b["corners"])
    raise AssertionError((a["core"], b["core"]))


def clearance(a, b):
    signed = core_distance(a, b) - a["radius"] - b["radius"]
    return {
        "edge_clearance_mm": round(max(0.0, signed), 9),
        "touch_or_overlap": signed <= EPS,
        "signed_core_offset_mm": round(signed, 9),
    }


def shape_from_guard(guard, halo):
    shape = guard["shape"]
    if shape["type"] == "capsule":
        return {
            "core": "segment", "a": tuple(shape["start_mm"]), "b": tuple(shape["end_mm"]),
            "radius": float(shape["radius_mm"]),
        }
    if shape["type"] == "circle":
        p = tuple(shape["center_mm"])
        return {"core": "segment", "a": p, "b": p, "radius": float(shape["radius_mm"])}
    if shape["type"] == "oriented_rect":
        return {
            "core": "rect",
            "corners": rect_corners(shape["center_mm"], shape["source_size_mm"], shape["rotation_deg"]),
            "radius": float(halo),
        }
    raise ValueError("unsupported guard shape: " + shape["type"])


def copper_shape_from_guard(guard, halo):
    result = shape_from_guard(guard, halo)
    result["radius"] = max(0.0, result["radius"] - halo)
    return result


def parse_native_pad(reference, pad):
    literal = pad["serialized_definition"]
    header = re.search(r'^\(pad\s+"[^"]+"\s+\S+\s+(\S+)', literal)
    size = re.search(r"\(size\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\)", literal)
    if not header or not size:
        raise ValueError("unsupported pad serialization: " + pad["uuid"])
    shape = header.group(1)
    if shape != "rect":
        raise ValueError("unsupported candidate pad shape: " + pad["uuid"] + ":" + shape)
    layers = [x["name"] for x in pad["layer_ids_names"] if x["name"].endswith(".Cu")]
    return {
        "uuid": pad["uuid"], "kind": "pad", "reference": reference, "number": pad["number"],
        "net": pad["net_name"], "layers": layers, "center_mm": pad["position_mm"],
        "orientation_deg": float(pad["orientation_deg"]),
        "size_mm": [float(size.group(1)), float(size.group(2))],
        "shape": shape, "serialized_definition_sha256": pad["serialized_definition_sha256"],
    }


def parse_native_pad_full(reference, pad, enabled_layers):
    """Parse saved-native global pad geometry without recomputing footprint poses."""
    literal = pad["serialized_definition"]
    header = re.search(r'^\(pad\s+"[^"]*"\s+(\S+)\s+(\S+)', literal)
    size = re.search(r"\(size\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\)", literal)
    if not header or not size:
        raise ValueError("unsupported pad serialization: " + pad["uuid"])
    pad_type, shape = header.groups()
    if shape not in {"rect", "circle", "oval", "roundrect"}:
        raise ValueError("unsupported full-population pad shape: " + pad["uuid"] + ":" + shape)
    angle = float(pad["orientation_deg"]) % 360.0
    if min(abs(angle - x) for x in (0.0, 90.0, 180.0, 270.0, 360.0)) > EPS:
        raise ValueError("unqualified nonorthogonal native population pad: " + pad["uuid"])
    native_layer_names = [x["name"] for x in pad["layer_ids_names"]]
    layers = [x for x in enabled_layers if x in native_layer_names]
    if not layers:
        raise ValueError("pad has no enabled conductive/physical layer: " + pad["uuid"])
    result = {
        "uuid": pad["uuid"], "kind": "pad", "reference": reference, "number": pad["number"],
        "net": pad["net_name"], "layers": layers, "center_mm": pad["position_mm"],
        "orientation_deg": float(pad["orientation_deg"]),
        "size_mm": [float(size.group(1)), float(size.group(2))],
        "shape": shape, "pad_type": pad_type,
        "conductive": pad_type != "np_thru_hole",
        "serialized_definition_sha256": pad["serialized_definition_sha256"],
        "layer_expansion": (
            "saved-native layer IDs intersected with source-enabled copper layers"
            + ("; wildcard/all-copper span" if '"*.Cu"' in literal else "")
        ),
    }
    if shape == "roundrect":
        ratio = re.search(r"\(roundrect_rratio\s+([-+0-9.eE]+)\)", literal)
        if not ratio:
            raise ValueError("roundrect missing radius ratio: " + pad["uuid"])
        result["roundrect_rratio"] = float(ratio.group(1))
    if pad_type == "np_thru_hole":
        drill = re.search(r"\(drill\s+([-+0-9.eE]+)\)", literal)
        if not drill:
            raise ValueError("NPTH missing circular drill: " + pad["uuid"])
        result["drill_mm"] = float(drill.group(1))
    return result


def expand_copper_layers(record, enabled_layers):
    """Expand a track/via onto actual enabled conductive layers."""
    result = normalized_geometry(record)
    listed = list(result["layers"])
    unknown = set(listed) - set(enabled_layers)
    if unknown:
        raise ValueError(f"copper uses non-enabled layer(s) {sorted(unknown)}: {result['uuid']}")
    if result["kind"] == "track":
        if len(listed) != 1:
            raise ValueError("track layer count is not one: " + result["uuid"])
        return result
    if result["kind"] != "via" or len(listed) < 2:
        raise ValueError("unsupported via layer span: " + result["uuid"])
    indices = [enabled_layers.index(x) for x in listed]
    lo, hi = min(indices), max(indices)
    result["layers"] = enabled_layers[lo:hi + 1]
    result["layer_expansion"] = {
        "saved_span_endpoints": listed,
        "actual_enabled_layers_in_span": result["layers"],
    }
    return result


def rounded_rect_shape(center, size, rotation_deg, ratio):
    radius = min(size) * ratio
    core_size = [max(0.0, size[0] - 2 * radius), max(0.0, size[1] - 2 * radius)]
    return {
        "core": "rect", "corners": rect_corners(center, core_size, rotation_deg),
        "radius": radius,
    }


def oval_shape(center, size, rotation_deg):
    w, h = size
    radius = min(w, h) / 2.0
    half_core = abs(w - h) / 2.0
    angle = math.radians(rotation_deg + (0.0 if w >= h else 90.0))
    dx, dy = half_core * math.cos(angle), half_core * math.sin(angle)
    return {
        "core": "segment",
        "a": (center[0] - dx, center[1] - dy),
        "b": (center[0] + dx, center[1] + dy),
        "radius": radius,
    }


def candidate_shape(record):
    if record["kind"] == "track":
        return {
            "core": "segment", "a": tuple(record["start_mm"]), "b": tuple(record["end_mm"]),
            "radius": float(record["width_mm"]) / 2.0,
        }
    if record["kind"] == "via":
        p = tuple(record.get("position_mm", record.get("at_mm")))
        diameter = record.get("diameter_mm", record.get("size_mm"))
        return {"core": "segment", "a": p, "b": p, "radius": float(diameter) / 2.0}
    if record["kind"] == "pad":
        if record["shape"] == "circle":
            p = tuple(record["center_mm"])
            return {"core": "segment", "a": p, "b": p, "radius": record["size_mm"][0] / 2.0}
        if record["shape"] == "oval":
            return oval_shape(record["center_mm"], record["size_mm"], record["orientation_deg"])
        if record["shape"] == "roundrect":
            return rounded_rect_shape(
                record["center_mm"], record["size_mm"], record["orientation_deg"],
                record["roundrect_rratio"],
            )
        if record["shape"] != "rect":
            raise ValueError("unsupported candidate pad shape: " + record["uuid"] + ":" + record["shape"])
        return {
            "core": "rect",
            "corners": rect_corners(record["center_mm"], record["size_mm"], record["orientation_deg"]),
            "radius": 0.0,
        }
    raise ValueError("unsupported candidate kind: " + record["kind"])


def shape_bounds(shape):
    if shape["core"] == "segment":
        xs = (shape["a"][0], shape["b"][0])
        ys = (shape["a"][1], shape["b"][1])
    elif shape["core"] == "rect":
        xs = [p[0] for p in shape["corners"]]
        ys = [p[1] for p in shape["corners"]]
    else:
        raise ValueError("unsupported bounds core: " + shape["core"])
    r = shape["radius"]
    return [min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r]


def bounds_overlap(a, b):
    return not (a[2] < b[0] - EPS or b[2] < a[0] - EPS
                or a[3] < b[1] - EPS or b[3] < a[1] - EPS)


def normalized_geometry(record):
    """Canonicalize accepted aliases and reject contradictory duplicate fields."""
    result = dict(record)
    if record.get("kind") == "via":
        positions = [record[k] for k in ("position_mm", "at_mm") if k in record]
        diameters = [record[k] for k in ("diameter_mm", "size_mm") if k in record]
        if not positions or not diameters:
            raise ValueError("incomplete via geometry: " + record.get("uuid", "<unknown>"))
        if any(list(x) != list(positions[0]) for x in positions[1:]):
            raise ValueError("conflicting via position aliases: " + record.get("uuid", "<unknown>"))
        if any(float(x) != float(diameters[0]) for x in diameters[1:]):
            raise ValueError("conflicting via diameter aliases: " + record.get("uuid", "<unknown>"))
        result["position_mm"] = list(positions[0])
        result["diameter_mm"] = float(diameters[0])
        result.pop("at_mm", None)
        result.pop("size_mm", None)
    return result


def geometry_signature(record):
    record = normalized_geometry(record)
    keys = ("uuid", "kind", "net", "layers", "start_mm", "end_mm", "width_mm",
            "position_mm", "diameter_mm", "drill_mm")
    return json.dumps({k: record[k] for k in keys if k in record}, sort_keys=True)


def collect_geometry(value, wanted, found):
    if isinstance(value, dict):
        uid = value.get("uuid")
        kind = value.get("kind")
        complete = (
            kind == "track" and all(k in value for k in ("start_mm", "end_mm", "width_mm", "net", "layers"))
        ) or (
            kind == "via" and ("position_mm" in value or "at_mm" in value)
            and ("diameter_mm" in value or "size_mm" in value) and "net" in value and "layers" in value
        )
        if uid in wanted and complete:
            normalized = normalized_geometry(value)
            found[uid][geometry_signature(normalized)] = {
                k: v for k, v in normalized.items() if k != "copper"
            }
        for child in value.values():
            collect_geometry(child, wanted, found)
    elif isinstance(value, list):
        for child in value:
            collect_geometry(child, wanted, found)


def run_controls():
    controls = []

    def check(name, actual, expected, tol=1e-9):
        passed = abs(actual - expected) <= tol
        controls.append({"name": name, "actual": actual, "expected": expected, "passed": passed})
        if not passed:
            raise AssertionError(name)

    # Independent known-coordinate boundaries.
    check("parallel_capsules_0.25_gap", clearance(
        {"core": "segment", "a": (0, 0), "b": (2, 0), "radius": 0.1},
        {"core": "segment", "a": (0, 0.45), "b": (2, 0.45), "radius": 0.1},
    )["edge_clearance_mm"], 0.25)
    check("circle_tangent_to_axis_rect", clearance(
        {"core": "segment", "a": (2, 0), "b": (2, 0), "radius": 0.5},
        {"core": "rect", "corners": rect_corners((0, 0), (3, 2), 0), "radius": 0},
    )["edge_clearance_mm"], 0.0)
    check("rotated_rect_90_clearance", clearance(
        {"core": "rect", "corners": rect_corners((0, 0), (2, 1), 90), "radius": 0},
        {"core": "segment", "a": (1, 0), "b": (1, 0), "radius": 0.25},
    )["edge_clearance_mm"], 0.25)
    check("segment_to_45deg_rect_contact", clearance(
        {"core": "segment", "a": (-2, 0), "b": (2, 0), "radius": 0},
        {"core": "rect", "corners": rect_corners((0, 0), (1, 1), 45), "radius": 0},
    )["edge_clearance_mm"], 0.0)
    states = [
        clearance(
            {"core": "segment", "a": (0, 0), "b": (0, 0), "radius": 1},
            {"core": "segment", "a": (1.5, 0), "b": (1.5, 0), "radius": 1},
        )["touch_or_overlap"],
        clearance(
            {"core": "segment", "a": (0, 0), "b": (0, 0), "radius": 1},
            {"core": "segment", "a": (2, 0), "b": (2, 0), "radius": 1},
        )["touch_or_overlap"],
        clearance(
            {"core": "segment", "a": (0, 0), "b": (0, 0), "radius": 1},
            {"core": "segment", "a": (2.000001, 0), "b": (2.000001, 0), "radius": 1},
        )["touch_or_overlap"],
    ]
    expected_states = [True, True, False]
    controls.append({
        "name": "boolean_overlap_tangent_small_positive_gap",
        "actual": states, "expected": expected_states, "passed": states == expected_states,
    })
    try:
        normalized_geometry({
            "uuid": "alias-control", "kind": "via", "position_mm": [0, 0], "at_mm": [0.1, 0],
            "diameter_mm": 0.6, "size_mm": 0.6,
        })
        alias_rejected = False
    except ValueError:
        alias_rejected = True
    controls.append({
        "name": "conflicting_via_alias_rejected",
        "actual": alias_rejected, "expected": True, "passed": alias_rejected,
    })
    if not all(x["passed"] for x in controls):
        raise AssertionError("geometry control failed")
    return controls


def expect_validation_failure(name, action, controls):
    try:
        action()
        detected = False
    except (AssertionError, ValueError):
        detected = True
    controls.append({"name": name, "actual": detected, "expected": True, "passed": detected})
    if not detected:
        raise AssertionError(name)


def validate_exact_ids(name, actual, expected):
    if len(actual) != len(set(actual)):
        raise ValueError(name + " contains duplicate identities")
    if set(actual) != set(expected):
        raise ValueError(name + " identity set mismatch")


def run_full_population(args, paths, actual_hashes):
    controls = run_controls()
    repair, inventory = load(args.repair), load(args.inventory)
    connectivity, retained = load(args.connectivity), load(args.retained)
    enabled_layers = list(connectivity["enabled_copper_layers"])
    if enabled_layers != ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]:
        raise ValueError("unexpected source-enabled copper layers: " + repr(enabled_layers))
    guards = {x["proposal_uuid"]: x for x in repair["guard_definitions"]}
    if len(guards) != 18 or len(guards) != len(repair["guard_definitions"]):
        raise ValueError("guard identity/count mismatch")
    fixed_refs = set(retained["identity_baseline"]["retained27_references"])
    if len(fixed_refs) != 27:
        raise ValueError("fixed reference count mismatch")
    retained_ids = list(retained["retained177"]["uuids"])
    if len(retained_ids) != 177:
        raise ValueError("retained copper count mismatch")

    if args.geometry_supplement is None:
        raise ValueError("--full-population requires --geometry-supplement")
    supplement_hash = sha256(args.geometry_supplement)
    if supplement_hash != EXPECTED_FULL_GEOMETRY_SUPPLEMENT:
        raise ValueError("unexpected geometry supplement hash: " + supplement_hash)
    found = defaultdict(dict)
    collect_geometry(connectivity, set(retained_ids), found)
    primary_missing = sorted(uid for uid in retained_ids if not found[uid])
    if primary_missing != ["898341e7-3649-568b-a9f2-8843ec69658c"]:
        raise ValueError("unexpected primary saved-geometry gap: " + repr(primary_missing))
    collect_geometry(load(args.geometry_supplement), set(retained_ids), found)
    copper = {}
    for uid in retained_ids:
        if not found[uid]:
            raise ValueError("missing saved retained copper geometry: " + uid)
        if len(found[uid]) != 1:
            raise ValueError("non-unique saved retained copper geometry: " + uid)
        copper[uid] = expand_copper_layers(next(iter(found[uid].values())), enabled_layers)
    validate_exact_ids("retained copper", list(copper), retained_ids)

    pads = {}
    pad_refs = {}
    for ref, footprint in inventory["all_native_footprints_and_serialized_geometry"].items():
        if ref not in fixed_refs:
            continue
        pad_refs[ref] = 0
        for pad in footprint["pads"]:
            uid = pad["uuid"]
            if uid in pads:
                raise ValueError("duplicate saved-native fixed pad: " + uid)
            pads[uid] = parse_native_pad_full(ref, pad, enabled_layers)
            pad_refs[ref] += 1
    expected_pad_count = retained["identity_baseline"]["retained27_pad_count"]
    if len(pads) != expected_pad_count or expected_pad_count != 97:
        raise ValueError(f"fixed pad count mismatch: {len(pads)} != {expected_pad_count}")
    if set(pad_refs) != fixed_refs or any(x <= 0 for x in pad_refs.values()):
        raise ValueError("fixed reference pad coverage mismatch")

    # Explicit completeness and regression controls.
    controls.append({
        "name": "all_97_saved_native_fixed_pads_covered",
        "actual": len(pads), "expected": 97, "passed": len(pads) == 97,
    })
    controls.append({
        "name": "all_177_retained_copper_resolved_uniquely",
        "actual": len(copper), "expected": 177, "passed": len(copper) == 177,
    })
    pose_witness = {
        "e5faefdc-06ab-5b87-9fc1-47bbda0e766a": [86.4, 112.208],  # R26.1
        "bf411126-e0c1-5e14-b531-dc4dd157714a": [102.2, 114.25],  # C28.1
    }
    wrong_pose = {
        "e5faefdc-06ab-5b87-9fc1-47bbda0e766a": [86.4, 111.192],
        "bf411126-e0c1-5e14-b531-dc4dd157714a": [102.2, 116.15],
    }
    pose_pass = all(
        list(pads[uid]["center_mm"]) == expected and list(pads[uid]["center_mm"]) != wrong_pose[uid]
        for uid, expected in pose_witness.items()
    )
    controls.append({
        "name": "wrong_R26.1_C28.1_opposite_pad_poses_rejected",
        "actual": pose_pass, "expected": True, "passed": pose_pass,
        "saved_native_centers_mm": {uid: pads[uid]["center_mm"] for uid in pose_witness},
    })
    if not pose_pass:
        raise AssertionError("saved-native pose witness failed")
    expect_validation_failure(
        "omitted_fixed_pad_is_detected",
        lambda: validate_exact_ids("fixed pads", list(pads)[:-1], pads.keys()), controls,
    )
    expect_validation_failure(
        "omitted_retained_copper_is_detected",
        lambda: validate_exact_ids("retained copper", list(copper)[:-1], retained_ids), controls,
    )
    wildcard_pad = next(x for x in pads.values() if "wildcard/all-copper span" in x["layer_expansion"])
    expect_validation_failure(
        "omitted_actual_copper_layer_is_detected",
        lambda: validate_exact_ids(
            "wildcard pad layers", wildcard_pad["layers"][:-1], enabled_layers
        ), controls,
    )

    candidates = {**copper, **pads}
    if len(candidates) != 274:
        raise ValueError("combined population identity collision/count mismatch")
    candidate_shapes = {uid: candidate_shape(x) for uid, x in candidates.items()}
    candidate_bounds = {uid: shape_bounds(x) for uid, x in candidate_shapes.items()}
    private_ids = set(repair["private_objects"])
    old = load(args.compare) if args.compare else None
    old_by_pair = {}
    if old is not None:
        old_by_pair = {
            (x["guard_uuid"], x["candidate_uuid"], x["layer"]): x
            for x in old["relationships"]
        }
        if len(old_by_pair) != len(old["relationships"]):
            raise ValueError("prior relationship pair keys are not unique")

    relationships = []
    broad_pairs = []
    self_pairs = []
    halo = 0.25
    for guard in sorted(guards.values(), key=lambda x: x["proposal_uuid"]):
        layer = guard["layer"]
        if layer not in enabled_layers:
            raise ValueError("guard on non-enabled layer: " + layer)
        guard_shape = shape_from_guard(guard, halo)
        private_shape = copper_shape_from_guard(guard, halo)
        guard_bounds = shape_bounds(guard_shape)
        for uid in sorted(candidates):
            item = candidates[uid]
            if layer not in item["layers"] or not bounds_overlap(guard_bounds, candidate_bounds[uid]):
                continue
            pair = (guard["proposal_uuid"], uid, layer)
            broad_pairs.append(pair)
            cshape = candidate_shapes[uid]
            guard_result = clearance(cshape, guard_shape)
            copper_result = clearance(cshape, private_shape)
            if uid == guard["source_uuid"]:
                category = "protected_object_self"
                self_pairs.append(pair)
            elif item["kind"] == "pad" and not item["conductive"]:
                category = "NPTH_physical_hole_candidate"
            elif not guard_result["touch_or_overlap"]:
                category = "broad_phase_false_positive"
            elif uid in private_ids:
                category = "protected_branch_join"
            elif uid in BOUNDARY:
                category = "reviewed_ordinary_GND_boundary_join"
            elif item["net"] == "GND":
                category = "other_retained_same_net_intrusion"
            else:
                category = "foreign_net_intrusion"
            relationships.append({
                "guard_uuid": guard["proposal_uuid"],
                "guard_source_uuid": guard["source_uuid"],
                "guard_branch": guard["branch"],
                "candidate_uuid": uid,
                "candidate_reference": item.get("reference"),
                "candidate_number": item.get("number"),
                "candidate_net": item["net"],
                "candidate_kind": item["kind"],
                "candidate_shape": item.get("shape"),
                "candidate_conductive": item.get("conductive", True),
                "layer": layer,
                "guard_clearance": guard_result,
                "private_copper_clearance": copper_result,
                "contact_class": (
                    "physical_hole_candidate" if item.get("conductive") is False
                    else "actual_copper_contact" if copper_result["touch_or_overlap"]
                    else "guard_halo_only" if guard_result["touch_or_overlap"]
                    else "clear_of_guard"
                ),
                "category": category,
                "review_note": BOUNDARY.get(uid),
            })

    if len(self_pairs) != 18 or len(set(self_pairs)) != 18:
        raise ValueError(f"self exclusion count mismatch: {len(self_pairs)}")
    relation_by_pair = {
        (x["guard_uuid"], x["candidate_uuid"], x["layer"]): x for x in relationships
    }
    if len(relation_by_pair) != len(relationships):
        raise ValueError("generated relationship pair keys are not unique")
    old_keys, new_keys = set(old_by_pair), set(relation_by_pair)
    common = sorted(old_keys & new_keys)
    added = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)
    comparable_fields = (
        "guard_uuid", "guard_source_uuid", "guard_branch", "candidate_uuid", "candidate_net",
        "candidate_kind", "layer", "guard_clearance", "private_copper_clearance",
        "contact_class", "category", "review_note",
    )
    changed_common = []
    for key in common:
        before, after = old_by_pair[key], relation_by_pair[key]
        delta = {
            field: {"prior": before.get(field), "current": after.get(field)}
            for field in comparable_fields if before.get(field) != after.get(field)
        }
        if delta:
            changed_common.append({"pair": list(key), "fields": delta})
    if changed_common:
        raise AssertionError("shared prior relationship changed")

    categories = Counter(x["category"] for x in relationships)
    contacts = Counter(x["contact_class"] for x in relationships)
    exact_shapes = Counter(
        (x["kind"], x.get("shape", "capsule_or_circle")) for x in candidates.values()
    )
    result = {
        "schema_version": 2,
        "status": "STATIC_FULL_POPULATION_CANDIDATE_COVERAGE",
        "runtime": {"python": sys.version, "native_loads": 0, "third_party_dependencies": 0},
        "input_sha256": {
            "repair_raw": actual_hashes["repair"],
            "native_inventory": actual_hashes["inventory"],
            "saved_connectivity": actual_hashes["connectivity"],
            "retained177": actual_hashes["retained"],
            "prior_corrected_raw": sha256(args.compare) if args.compare else None,
            "saved_native_geometry_supplement": supplement_hash,
        },
        "scope": {
            "guard_definitions_unchanged": 18,
            "enabled_copper_layers": enabled_layers,
            "retained_copper": len(copper),
            "saved_native_fixed_references": len(fixed_refs),
            "saved_native_fixed_pads": len(pads),
            "combined_obstacle_population": len(candidates),
            "broad_phase_relationships": len(broad_pairs),
            "narrow_phase_relationships": len(relationships),
            "explicit_self_exclusions": len(self_pairs),
            "source_or_pcb_changes": 0,
        },
        "population_proof": {
            "primary_geometry_gap_filled_from_pinned_saved_native_supplement": primary_missing,
            "retained_copper_expected_uuids": sorted(retained_ids),
            "retained_copper_resolved_uuids": sorted(copper),
            "fixed_reference_expected": sorted(fixed_refs),
            "fixed_reference_pad_counts": dict(sorted(pad_refs.items())),
            "fixed_pad_uuids": sorted(pads),
            "unsupported_or_unresolved_records": [],
            "silent_exclusions_or_deduplication": 0,
            "shape_counts": {
                f"{kind}:{shape}": count for (kind, shape), count in sorted(exact_shapes.items())
            },
        },
        "layer_population_counts": {
            layer: {
                "retained_copper": sum(layer in x["layers"] for x in copper.values()),
                "fixed_pads": sum(layer in x["layers"] for x in pads.values()),
            } for layer in enabled_layers
        },
        "geometry_contract": {
            "broad_phase": "Conservative AABBs enclosing exact saved-global primitive shapes.",
            "narrow_phase": (
                "Exact Euclidean core distance for tracks/vias/circles/ovals/rectangles/"
                "roundrects against unchanged circle/capsule/oriented-rectangle guards."
            ),
            "pad_pose": "Saved-native global center/orientation only; no footprint-local transform.",
            "through_layer_policy": "Span endpoints expanded across all source-enabled copper layers.",
            "NPTH_policy": "Reported as physical-hole candidates, never as copper contact.",
        },
        "controls": controls,
        "relationship_counts": dict(sorted(categories.items())),
        "contact_counts": dict(sorted(contacts.items())),
        "relationships": relationships,
        "broad_phase_pair_keys": [list(x) for x in broad_pairs],
        "self_exclusion_pair_keys": [list(x) for x in self_pairs],
        "prior_corrected_comparison": {
            "prior_relationships": len(old_keys),
            "common_relationships": len(common),
            "common_relationships_unchanged": len(changed_common) == 0,
            "added_relationships": len(added),
            "removed_relationships": len(removed),
            "added_pair_keys": [list(x) for x in added],
            "removed_pair_keys": [list(x) for x in removed],
            "changed_common": changed_common,
        },
        "limits": [
            "Static population/geometry evidence only; no native rule enforcement or product keepout approval.",
            "Existing intended-terminal joins are enumerated but not reinterpreted.",
            "The DOUT halo conflict is not an electrical-clearance failure and its route is unchanged.",
            "No functional grounding, routing, fill, source edit, cloud, manufacturing, or safety claim.",
        ],
    }
    if not all(x["passed"] for x in controls):
        raise AssertionError("full-population control failed")
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"], "population": len(candidates),
        "broad_relationships": len(broad_pairs), "self": len(self_pairs),
        "common": len(common), "added": len(added), "removed": len(removed),
        "categories": result["relationship_counts"], "contacts": result["contact_counts"],
    }, sort_keys=True))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repair", required=True, type=Path)
    ap.add_argument("--inventory", required=True, type=Path)
    ap.add_argument("--connectivity", required=True, type=Path)
    ap.add_argument("--retained", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--compare", type=Path)
    ap.add_argument("--geometry-supplement", type=Path)
    ap.add_argument("--full-population", action="store_true")
    args = ap.parse_args()

    if args.output.exists():
        raise FileExistsError("output already exists: " + str(args.output))
    paths = {
        "repair": args.repair, "inventory": args.inventory,
        "connectivity": args.connectivity, "retained": args.retained,
    }
    actual_hashes = {name: sha256(path) for name, path in paths.items()}
    if actual_hashes != EXPECTED_INPUTS:
        raise ValueError("unexpected bound input hashes: " + json.dumps(actual_hashes, sort_keys=True))
    if args.full_population:
        if args.compare is None:
            raise ValueError("--full-population requires --compare")
        return run_full_population(args, paths, actual_hashes)
    controls = run_controls()
    repair, inventory = load(args.repair), load(args.inventory)
    connectivity, retained = load(args.connectivity), load(args.retained)
    rows = repair["collateral_AABB_candidates"]
    guards = {x["proposal_uuid"]: x for x in repair["guard_definitions"]}
    private_ids = set(repair["private_objects"])
    retained_ids = set(retained["retained177"]["uuids"])
    fixed_refs = set(retained["identity_baseline"]["retained27_references"])
    candidate_ids = sorted({uid for row in rows for uid in row["AABB_candidates"]})
    relationship_count = sum(len(row["AABB_candidates"]) for row in rows)

    native_pads = {}
    for ref, footprint in inventory["all_native_footprints_and_serialized_geometry"].items():
        for pad in footprint["pads"]:
            if pad["uuid"] in candidate_ids:
                if pad["uuid"] in native_pads:
                    raise ValueError("duplicate candidate native pad: " + pad["uuid"])
                native_pads[pad["uuid"]] = parse_native_pad(ref, pad)
                angle = native_pads[pad["uuid"]]["orientation_deg"] % 360.0
                if min(abs(angle - x) for x in (0.0, 90.0, 180.0, 270.0, 360.0)) > EPS:
                    raise ValueError("unqualified nonorthogonal native candidate pad: " + pad["uuid"])

    wanted_copper = set(candidate_ids) - set(native_pads)
    found = defaultdict(dict)
    collect_geometry(connectivity, wanted_copper, found)
    copper = {}
    for uid in wanted_copper:
        if not found[uid]:
            raise ValueError("missing saved copper geometry: " + uid)
        if len(found[uid]) != 1:
            raise ValueError("conflicting saved copper geometry: " + uid)
        copper[uid] = next(iter(found[uid].values()))

    candidates = {**copper, **native_pads}
    for uid, item in candidates.items():
        if item["kind"] == "pad":
            if item["reference"] not in fixed_refs:
                raise ValueError("candidate pad not in retained fixed references: " + uid)
        elif uid not in retained_ids:
            raise ValueError("candidate copper not in retained177: " + uid)

    relationships = []
    halo = 0.25
    for row in rows:
        guard = guards[row["guard"]]
        guard_shape = shape_from_guard(guard, halo)
        private_shape = copper_shape_from_guard(guard, halo)
        for uid in row["AABB_candidates"]:
            item = candidates[uid]
            if row["layer"] not in item["layers"]:
                raise ValueError(f"candidate layer mismatch: {uid}:{row['layer']}")
            cshape = candidate_shape(item)
            guard_result = clearance(cshape, guard_shape)
            copper_result = clearance(cshape, private_shape)
            if not guard_result["touch_or_overlap"]:
                category = "broad_phase_false_positive"
            elif uid == guard["source_uuid"]:
                category = "protected_object_self"
            elif uid in private_ids:
                category = "protected_branch_join"
            elif uid in BOUNDARY:
                category = "reviewed_ordinary_GND_boundary_join"
            elif item["net"] == "GND":
                category = "other_retained_same_net_intrusion"
            else:
                category = "foreign_net_intrusion"
            relationships.append({
                "guard_uuid": guard["proposal_uuid"],
                "guard_source_uuid": guard["source_uuid"],
                "guard_branch": guard["branch"],
                "candidate_uuid": uid,
                "candidate_net": item["net"],
                "candidate_kind": item["kind"],
                "layer": row["layer"],
                "guard_clearance": guard_result,
                "private_copper_clearance": copper_result,
                "contact_class": (
                    "actual_copper_contact" if copper_result["touch_or_overlap"]
                    else "guard_halo_only" if guard_result["touch_or_overlap"]
                    else "clear_of_guard"
                ),
                "category": category,
                "review_note": BOUNDARY.get(uid),
            })

    categories = Counter(x["category"] for x in relationships)
    contacts = Counter(x["contact_class"] for x in relationships)
    object_categories = {}
    for uid in candidate_ids:
        rs = [x for x in relationships if x["candidate_uuid"] == uid]
        object_categories[uid] = sorted(set(x["category"] for x in rs))
    nearest_clear = sorted(
        (x for x in relationships if not x["guard_clearance"]["touch_or_overlap"]),
        key=lambda x: (x["guard_clearance"]["edge_clearance_mm"], x["guard_uuid"], x["candidate_uuid"]),
    )[:5]
    overlaps = sorted(
        (x for x in relationships if x["guard_clearance"]["touch_or_overlap"]),
        key=lambda x: (x["guard_clearance"]["signed_core_offset_mm"], x["guard_uuid"], x["candidate_uuid"]),
    )
    comparison = {
        "requested": args.compare is not None,
        "relationship_array_identical": None,
        "difference": None,
    }
    if args.compare is not None:
        prior = load(args.compare)
        comparison["relationship_array_identical"] = prior["relationships"] == relationships
        if not comparison["relationship_array_identical"]:
            comparison["difference"] = {
                "prior_count": len(prior["relationships"]), "current_count": len(relationships)
            }

    result = {
        "schema_version": 1,
        "status": "STATIC_ANALYTIC_DISPOSITION_ONLY",
        "runtime": {"python": sys.version, "native_loads": 0, "third_party_dependencies": 0},
        "input_sha256": {
            "repair_raw": sha256(args.repair),
            "native_inventory": sha256(args.inventory),
            "saved_connectivity": sha256(args.connectivity),
            "retained177": sha256(args.retained),
        },
        "scope": {
            "guard_root_objects": repair["guard_root_object_count"],
            "guard_layer_obligations": repair["guard_layer_obligation_count"],
            "broad_phase_rows": len(rows),
            "unique_candidate_objects": len(candidate_ids),
            "relationships": relationship_count,
            "population": "corrected retained177 copper plus pads of retained27 fixed refs",
            "population_limit": "Not all 325 pads, future movers, footprint bodies, or future copper.",
            "source_or_pcb_changes": 0,
        },
        "candidate_evidence": {
            "retained_copper_objects": len(copper),
            "saved_native_global_pad_records": len(native_pads),
            "all_candidate_pads_rect_and_supported": True,
            "candidate_pad_angles_deg": {
                uid: item["orientation_deg"] for uid, item in sorted(native_pads.items())
            },
            "fixed_pad_baseline_count": retained["identity_baseline"]["retained27_pad_count"],
        },
        "candidate_copper_records_used": [copper[uid] for uid in sorted(copper)],
        "candidate_native_pad_records_used": [native_pads[uid] for uid in sorted(native_pads)],
        "geometry_contract": {
            "method": "exact Euclidean core distance for circles/capsules/oriented rectangles; 0.25 mm Minkowski halo",
            "edge_clearance_definition": "nonnegative edge gap; zero means touch or overlap",
            "signed_core_offset_definition": "core distance minus shape radii; <=0 means touch/overlap",
            "actual_contact_definition": "candidate copper touches/overlaps unexpanded private source copper",
            "halo_only_definition": "candidate misses private copper but touches/overlaps its 0.25 mm guard",
        },
        "controls": controls,
        "relationship_counts": dict(sorted(categories.items())),
        "contact_counts": dict(sorted(contacts.items())),
        "unique_object_category_counts": dict(sorted(Counter(
            category for values in object_categories.values() for category in set(values)
        ).items())),
        "relationships": relationships,
        "nearest_clear_relationships": nearest_clear,
        "guard_overlap_relationships": overlaps,
        "object_categories": object_categories,
        "attempt1_comparison": comparison,
        "limits": [
            "Analytic static evidence does not qualify native KiCad or Quilter guard representation/enforcement.",
            "Reviewed joins and same-net intrusions are reported, not waived or carved out.",
            "No acceptance, routing, PCB generation, fill, save, DRC, cloud action, or COUT duty change is made.",
        ],
    }
    if result["scope"]["unique_candidate_objects"] != 25 or result["scope"]["broad_phase_rows"] != 14:
        raise AssertionError("candidate population changed")
    if not all(x["passed"] for x in controls):
        raise AssertionError("geometry controls failed")
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"], "objects": len(candidate_ids), "relationships": relationship_count,
        "categories": result["relationship_counts"], "contacts": result["contact_counts"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
