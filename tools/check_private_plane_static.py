# SPDX-License-Identifier: MIT
"""Static saved-file reconciliation for the private-plane native control."""
from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from pathlib import Path

from kicad_sexpr import Atom, Node, loads

NS = uuid.UUID("222b7253-9f55-502d-9c35-e054009a76d1")
ANCHOR = str(uuid.uuid5(NS, "diagnostic-gnd-anchor"))
PRIVATE = {
    "eafa404c-be47-5f5c-8167-d39a967ba2e5": [100.2, 111.9],
    "6623be95-c657-5a8e-bedb-c5a73d42d40b": [103.7, 117.5],
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(item):
    if isinstance(item, Atom):
        return item.value
    return [canonical(child) for child in item.items]


def object_maps(root):
    footprints = {n.value("uuid"): canonical(n) for n in root.children("footprint")}
    pads = {
        p.value("uuid"): canonical(p)
        for f in root.children("footprint") for p in f.children("pad")
    }
    tracks = {n.value("uuid"): canonical(n) for n in root.children("segment")}
    vias = {n.value("uuid"): canonical(n) for n in root.children("via")}
    return {"footprints": footprints, "pads": pads, "tracks": tracks, "vias": vias}


def layer_records(root):
    return [
        {"serialized_id": int(n.atoms()[0]), "name": n.atoms()[1], "type": n.atoms()[2]}
        for n in root.child("layers").children()
        if n.atoms() and n.atoms()[1].endswith(".Cu")
    ]


def keepout_record(zone):
    keepout = zone.child("keepout")
    return {
        "uuid": zone.value("uuid"),
        "name": zone.value("name"),
        "layers": (
            zone.child("layers").atoms()[1:]
            if zone.child("layers") else [zone.value("layer")]
        ),
        "flags": {n.head: n.atoms()[1] for n in keepout.children()},
        "polygon": canonical(zone.child("polygon")),
    }


def via_record(node):
    size = float(node.value("size"))
    return {
        "uuid": node.value("uuid"),
        "center_mm": [float(x) for x in node.child("at").atoms()[1:3]],
        "diameter_mm": size,
        "outer_radius_mm": size / 2,
        "drill_mm": float(node.value("drill")),
        "layers": node.child("layers").atoms()[1:],
        "net": node.child("net").atoms()[1],
    }


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--four", type=Path, required=True)
    ap.add_argument("--six-positive", type=Path, required=True)
    ap.add_argument("--six-negative", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    paths = {
        "base": args.base, "four_positive": args.four,
        "six_positive": args.six_positive, "six_negative": args.six_negative,
    }
    roots = {
        name: loads(path.read_text(encoding="utf-8-sig"))
        for name, path in paths.items()
    }
    maps = {name: object_maps(root) for name, root in roots.items()}
    base = maps["base"]
    preservation = {}
    for profile in ("four_positive", "six_positive", "six_negative"):
        current = maps[profile]
        rows = {}
        for kind in ("footprints", "pads", "tracks", "vias"):
            expected = set(base[kind])
            observed = set(current[kind])
            additions = observed - expected
            expected_additions = {ANCHOR} if kind == "vias" else set()
            require(additions == expected_additions, f"{profile} unexpected {kind} additions")
            require(not expected - observed, f"{profile} missing retained {kind}")
            mismatches = [
                ident for ident in sorted(expected)
                if base[kind][ident] != current[kind][ident]
            ]
            require(not mismatches, f"{profile} changed retained {kind}: {mismatches}")
            rows[kind] = {
                "retained_uuid_count": len(expected),
                "exact_canonical_records_equal": True,
                "added_uuids": sorted(additions),
            }
        preservation[profile] = rows

    expected_layers = {
        "base": [(0, "F.Cu"), (4, "In1.Cu"), (6, "In2.Cu"), (2, "B.Cu")],
        "four_positive": [(0, "F.Cu"), (4, "In1.Cu"), (6, "In2.Cu"), (2, "B.Cu")],
        "six_positive": [
            (0, "F.Cu"), (4, "In1.Cu"), (6, "In2.Cu"),
            (8, "In3.Cu"), (10, "In4.Cu"), (2, "B.Cu"),
        ],
        "six_negative": [
            (0, "F.Cu"), (4, "In1.Cu"), (6, "In2.Cu"),
            (8, "In3.Cu"), (10, "In4.Cu"), (2, "B.Cu"),
        ],
    }
    layers = {name: layer_records(root) for name, root in roots.items()}
    for name, rows in layers.items():
        require(
            [(r["serialized_id"], r["name"]) for r in rows] == expected_layers[name],
            name + " serialized layer order/IDs differ",
        )

    anchor_rows, private_rows = {}, {}
    for profile in ("four_positive", "six_positive", "six_negative"):
        vias = {n.value("uuid"): n for n in roots[profile].children("via")}
        anchor_rows[profile] = via_record(vias[ANCHOR])
        require(
            anchor_rows[profile] == {
                "uuid": ANCHOR, "center_mm": [120.0, 120.0],
                "diameter_mm": 0.6, "outer_radius_mm": 0.3,
                "drill_mm": 0.3, "layers": ["F.Cu", "B.Cu"], "net": "GND",
            },
            profile + " anchor binding differs",
        )
        private_rows[profile] = [via_record(vias[ident]) for ident in PRIVATE]
        for row in private_rows[profile]:
            require(row["center_mm"] == PRIVATE[row["uuid"]], "private center differs")
            require(
                row["diameter_mm"] == .6 and row["outer_radius_mm"] == .3
                and row["drill_mm"] == .3 and row["layers"] == ["F.Cu", "B.Cu"]
                and row["net"] == "GND",
                "private via serialized shape/net/span differs",
            )

    rules = {
        name: {
            row["uuid"]: row
            for row in (keepout_record(z) for z in root.children("zone") if z.child("keepout"))
        }
        for name, root in roots.items()
    }
    positive, negative = rules["six_positive"], rules["six_negative"]
    missing = set(positive) - set(negative)
    added = set(negative) - set(positive)
    changed = [
        ident for ident in sorted(set(positive) & set(negative))
        if positive[ident] != negative[ident]
    ]
    require(len(missing) == 1 and not added and not changed, "negative rule delta differs")
    missing_record = positive[next(iter(missing))]
    require(
        missing_record["name"] ==
        "PRIVATE_VIA_eafa404c-be47-5f5c-8167-d39a967ba2e5_In3.Cu",
        "wrong negative guard omitted",
    )
    flag_groups = {}
    for profile in ("four_positive", "six_positive", "six_negative"):
        groups = {}
        for row in rules[profile].values():
            key = json.dumps(row["flags"], sort_keys=True)
            groups.setdefault(key, {"flags": row["flags"], "count": 0, "layers": set(), "names": []})
            groups[key]["count"] += 1
            groups[key]["layers"].update(row["layers"])
            groups[key]["names"].append(row["name"])
        flag_groups[profile] = [
            {
                "flags": group["flags"], "count": group["count"],
                "layers": sorted(group["layers"]),
                "names": sorted(group["names"]),
            }
            for group in groups.values()
        ]
    diag_via = [
        row for row in rules["six_positive"].values() if row["name"] == "DIAG_VIA_ALL"
    ]
    require(len(diag_via) == 1 and diag_via[0]["layers"] == ["F.Cu"], "DIAG_VIA_ALL changed")

    result = {
        "schema_version": 1, "status": "PASS_SAVED_STATIC_RECONCILIATION",
        "inputs": {name: {"path": str(path), "sha256": sha(path)} for name, path in paths.items()},
        "retained_object_comparison": preservation,
        "serialized_copper_layer_records": layers,
        "serialized_anchor_bindings": anchor_rows,
        "serialized_private_via_bindings": private_rows,
        "rule_flag_groups": flag_groups,
        "six_positive_vs_negative": {
            "missing_only": missing_record, "added_rule_areas": [],
            "changed_common_rule_areas": [],
        },
        "diagnostic_via_area": {
            "name": "DIAG_VIA_ALL", "layers": ["F.Cu"],
            "expanded_to_new_inner_layers": False,
            "flags": diag_via[0]["flags"],
        },
        "limits": [
            "Static saved-file comparison only; no pcbnew import, native load, fill, save, or DRC.",
            "Canonical S-expression identity proves retained serialized records, not functional grounding.",
        ],
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "output_sha256": sha(args.output)}))


if __name__ == "__main__":
    main()
