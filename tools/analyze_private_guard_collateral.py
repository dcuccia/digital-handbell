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
        return {
            "core": "rect",
            "corners": rect_corners(record["center_mm"], record["size_mm"], record["orientation_deg"]),
            "radius": 0.0,
        }
    raise ValueError("unsupported candidate kind: " + record["kind"])


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repair", required=True, type=Path)
    ap.add_argument("--inventory", required=True, type=Path)
    ap.add_argument("--connectivity", required=True, type=Path)
    ap.add_argument("--retained", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--compare", type=Path)
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
