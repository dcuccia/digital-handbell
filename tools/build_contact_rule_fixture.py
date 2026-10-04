# SPDX-License-Identifier: MIT
"""Build a source-bound contact-rule control fixture without importing KiCad."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import uuid

from kicad_sexpr import loads


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "hardware" / "handbell" / "iterations" / "printed-bell-four-layer" / "handbell.kicad_pcb"
MASK = REPO / "docs" / "measurements" / "2026-09-27-router-bakeoff" / "quilter-contact-via-mask-2026-10-03.json"
MASK_SHA256 = "489503349d1f05968ea165237a99bbd01e4381983b1f40273a9ab98fdef17fda"
FEED = MASK.with_name("quilter-contact-feed-candidate-2026-10-03.json")
FEED_SHA256 = "ff166d733bdd06966e7f549e36e232784d11174ef80cbd2370f9ce9b170f675e"
NAMESPACE = uuid.UUID("5e5f6ef1-e88f-4e09-a6e9-f61724ebba16")
FLAGS = {
    "tracks": "not_allowed",
    "vias": "not_allowed",
    "pads": "allowed",
    "copperpour": "not_allowed",
    "footprints": "allowed",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identifier(name):
    return str(uuid.uuid5(NAMESPACE, name))


def quoted(value):
    return json.dumps(value, ensure_ascii=True)


def net_name(node):
    net = node.child("net")
    if net is None or len(net.atoms()) != 2:
        raise ValueError("Expected the observed KiCad 10 name-only net syntax")
    return net.atoms()[1]


def build_fixture(source, mask):
    root = loads(source)
    if root.head != "kicad_pcb" or root.value("version") != "20260206":
        raise ValueError("Only the source-qualified KiCad 10 version 20260206 is supported")
    if root.children("net"):
        raise ValueError("Unexpected numeric root net table")
    footprints = [
        item for item in root.children("footprint")
        if item.properties().get("Reference") in {"BT1", "BT2"}
    ]
    if sorted(item.properties()["Reference"] for item in footprints) != ["BT1", "BT2"]:
        raise ValueError("Expected exactly one BT1 and one BT2")
    pads = [pad for footprint in footprints for pad in footprint.children("pad")]
    if len(pads) != 4:
        raise ValueError("Expected four physical contact pads")
    contacts = {}
    for footprint in footprints:
        names = {net_name(pad) for pad in footprint.children("pad")}
        if len(names) != 1:
            raise ValueError("Each contact must have one net")
        contacts[footprint.properties()["Reference"]] = names.pop()
    if contacts != {"BT1": "VBAT", "BT2": "/CELL_NEG"}:
        raise ValueError("Unexpected contact net identity")

    seed_rows = mask["protected_process_vias"]
    seed_ids = {row["uuid"] for row in seed_rows}
    if len(seed_rows) != 5 or len(seed_ids) != 5:
        raise ValueError("Expected five unique reviewed process vias")
    vias = [item for item in root.children("via") if item.value("uuid") in seed_ids]
    if len(vias) != 5 or {item.value("uuid") for item in vias} != seed_ids:
        raise ValueError("Reviewed process-via UUIDs do not match source")
    by_id = {item.value("uuid"): item for item in vias}
    for row in seed_rows:
        item = by_id[row["uuid"]]
        position = [float(value) for value in item.child("at").atoms()[1:]]
        expected = [value + 100 for value in row["common_xy_mm"]]
        actual = position + [float(item.value("size")), float(item.value("drill"))]
        expected += [row["diameter_mm"], row["drill_mm"]]
        if len(actual) != 4 or not all(
            math.isclose(a, b, rel_tol=0, abs_tol=1e-9) for a, b in zip(actual, expected)
        ):
            raise ValueError("Reviewed process-via geometry does not match source")
        if net_name(item) != "GND" or item.child("layers").atoms()[1:] != ["F.Cu", "B.Cu"]:
            raise ValueError("Unexpected process-via net or layer span")

    metadata = {"version", "generator", "generator_version", "general", "paper", "layers", "setup"}
    parts = [source[item.start:item.end] for item in root.children() if item.head in metadata]
    parts.append(
        '(title_block (title "CONTACT RULE CONTROL FIXTURE - NOT A PRODUCT BOARD") '
        '(comment 1 "Adafruit-derived CC BY-SA 3.0; see ATTRIBUTION.md"))'
    )
    retained = footprints + vias
    parts.extend(source[item.start:item.end] for item in retained)
    areas = mask["domains"]["native_via_only_rule_areas_expanded_each_edge_0_25_mm"]
    if len(areas) != 8 or len({area["name"] for area in areas}) != 8:
        raise ValueError("Expected eight unique reviewed contact guards")
    for area in areas:
        x0, x1 = area["x_min_mm"] + 100, area["x_max_mm"] + 100
        y0, y1 = area["y_min_mm"] + 100, area["y_max_mm"] + 100
        if not all(math.isfinite(v) for v in (x0, x1, y0, y1)) or not (x0 < x1 and y0 < y1):
            raise ValueError("Invalid contact guard rectangle")
        restrictions = " ".join(f"({key} {value})" for key, value in FLAGS.items())
        parts.append(
            f'(zone (layer "B.Cu") (uuid "{identifier("area/" + area["name"])}") '
            f'(name {quoted("CONTACT_METAL_GUARD_" + area["name"])}) '
            f'(hatch edge 0.5) (connect_pads (clearance 0)) (min_thickness 0.25) '
            f'(keepout {restrictions}) '
            f'(polygon (pts (xy {x0:.6f} {y0:.6f}) (xy {x1:.6f} {y0:.6f}) '
            f'(xy {x1:.6f} {y1:.6f}) (xy {x0:.6f} {y1:.6f}))))'
        )

    controls = []
    for name, y, disallowed in (
        ("inside", 100, True),
        ("threshold_inside", 106.107, True),
        ("threshold_outside", 106.127, False),
    ):
        item_id = identifier("probe/" + name)
        parts.append(
            f'(via (at 110 {y}) (size 0.604) (drill 0.35) '
            f'(layers "F.Cu" "B.Cu") (net "GND") (uuid "{item_id}"))'
        )
        controls.append({"name": name, "uuid": item_id, "expected_items_not_allowed": disallowed})
    for name, net, start, end, disallowed in (
        ("foreign_cross", "GND", (107, 100), (115, 100), True),
        ("same_cross", contacts["BT1"], (103.62, 100), (106.5, 100), True),
        ("outside", "GND", (107, 108), (115, 108), False),
    ):
        item_id = identifier("track/" + name)
        parts.append(
            f'(segment (start {start[0]} {start[1]}) (end {end[0]} {end[1]}) '
            f'(width 0.1778) (layer "B.Cu") (net {quoted(net)}) (uuid "{item_id}"))'
        )
        controls.append({"name": name, "uuid": item_id, "expected_items_not_allowed": disallowed})
    parts.append(
        f'(zone (net "GND") (layer "B.Cu") (uuid "{identifier("zone/foreign")}") '
        '(name "FOREIGN_POUR_CONTROL") (hatch edge 0.5) (connect_pads (clearance 0.2)) '
        '(min_thickness 0.2) (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3)) '
        '(polygon (pts (xy 104 93) (xy 120 93) (xy 120 107) (xy 104 107))))'
    )
    for index, (x0, y0, x1, y1) in enumerate((
        (70, 85, 130, 85), (130, 85, 130, 115),
        (130, 115, 70, 115), (70, 115, 70, 85),
    )):
        parts.append(
            f'(gr_line (start {x0} {y0}) (end {x1} {y1}) '
            f'(stroke (width 0.05) (type default)) (layer "Edge.Cuts") '
            f'(uuid "{identifier("edge/" + str(index))}"))'
        )
    result = "(kicad_pcb\n" + "\n".join(parts) + "\n)\n"
    parsed = loads(result)
    all_ids = [item.value("uuid") for item in parsed.walk() if item.child("uuid")]
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("Duplicate fixture UUID")
    report = {
        "status": "STATIC_FIXTURE_ONLY_NATIVE_BEHAVIOR_NOT_ESTABLISHED",
        "source_native_loads": 0,
        "fixture_native_loads": 0,
        "contact_nets": contacts,
        "physical_contact_pads": len(pads),
        "protected_via_uuids": sorted(seed_ids),
        "retained_subtree_sha256": {
            item.value("uuid"): digest(source[item.start:item.end].encode("utf-8"))
            for item in retained
        },
        "guard_coordinate_transform": "common XY +100/+100 exactly once",
        "guard_flags": FLAGS,
        "controls": controls,
        "legitimate_feed": "NOT_ESTABLISHED",
        "native_drc_or_reload": "NOT_RUN",
        "fixture_sha256": digest(result.encode("utf-8")),
    }
    return result, report


def build_feed_fixture(source, mask, ledger):
    base, report = build_fixture(source, mask)
    original, fixture = loads(source), loads(base)
    seeds = set(report["protected_via_uuids"])
    segments, ordinary_vias = [], []
    blocks = ledger["blocks"]
    if len(blocks) != 2 or {b["net"] for b in blocks} != {"VBAT", "/CELL_NEG"}:
        raise ValueError("Expected the two reviewed contact-feed blocks")
    for block in blocks:
        ids = block["segment_uuids"]
        selected = [s for s in original.children("segment") if s.value("uuid") in ids]
        if len(ids) != len(set(ids)) or len(selected) != block["selected_segment_count"] or len(selected) != len(ids):
            raise ValueError("Contact-feed segment UUIDs do not match source")
        if block["layer"] != "B.Cu" or any(
            s.value("layer") != "B.Cu" or net_name(s) != block["net"] for s in selected
        ):
            raise ValueError("Unexpected contact-feed segment net or layer")
        records = sorted([
            {"uuid":s.value("uuid"), "start":s.child("start").atoms()[1:],
             "end":s.child("end").atoms()[1:], "width":s.value("width")}
            for s in selected
        ], key=lambda row: row["uuid"])
        if digest(json.dumps(records, sort_keys=True, separators=(",", ":")).encode()) != block["records_sha256"]:
            raise ValueError("Contact-feed segment geometry does not match reviewed records")
        segments.extend(selected)
        for row in block["existing_via_candidates"]:
            matches = [v for v in original.children("via") if v.value("uuid") == row["uuid"]]
            if len(matches) != 1 or row["uuid"] in seeds:
                raise ValueError("Ordinary contact-via UUID does not match source")
            via = matches[0]
            observed = [float(v) for v in via.child("at").atoms()[1:]]
            observed += [float(via.value("size")), float(via.value("drill"))]
            expected = row["xy_mm"] + [row["diameter_mm"], row["drill_mm"]]
            if observed != expected or net_name(via) != block["net"] or via.child("layers").atoms()[1:] != ["F.Cu", "B.Cu"]:
                raise ValueError("Ordinary contact-via geometry/net/span does not match source")
            ordinary_vias.append(via)
    if len(segments) != 30 or len(ordinary_vias) != 5:
        raise ValueError("Expected 30 contact-feed segments and five ordinary vias")

    parts = []
    for item in fixture.children():
        if item.head == "segment" or (item.head == "via" and item.value("uuid") not in seeds):
            continue
        if item.head == "zone" and item.child("keepout") is None:
            continue
        if item.head == "title_block":
            parts.append(
                '(title_block (title "CONTACT FEED IMPORT ONLY - NOT FOR FABRICATION") '
                '(comment 1 "Adafruit-derived CC BY-SA 3.0; see ATTRIBUTION.md"))'
            )
        else:
            parts.append(base[item.start:item.end])
    retained = segments + ordinary_vias
    parts.extend(source[item.start:item.end] for item in retained)
    result = "(kicad_pcb\n" + "\n".join(parts) + "\n)\n"
    parsed = loads(result)
    ids = [n.value("uuid") for n in parsed.walk() if n.child("uuid")]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate fixture UUID")
    report["retained_subtree_sha256"].update({
        n.value("uuid"): digest(source[n.start:n.end].encode()) for n in retained
    })
    report.update({
        "status": "STATIC_CONTACT_FEED_IMPORT_ONLY_NATIVE_NOT_RUN",
        "import_only": True,
        "controls": [],
        "contact_feed_segment_uuids": sorted(n.value("uuid") for n in segments),
        "ordinary_via_uuids": sorted(n.value("uuid") for n in ordinary_vias),
        "copper_pours": 0,
        "intentional_limitations": [
            "Retained same-net feeds overlap all-track guards; this is not a legal product-board feed solution.",
            "Five inherited ordinary vias remain 0.600/0.300 mm; no manufacturing exception or resizing.",
            "No unrouted probe terminals: import recognition only, not routing-enforcement proof.",
        ],
        "fixture_sha256": digest(result.encode()),
    })
    return result, report


def write_fixture(output, source_bytes, mask_bytes, feed_bytes=None):
    if digest(mask_bytes) != MASK_SHA256:
        raise ValueError("Mask evidence hash does not match the reviewed report")
    mask = json.loads(mask_bytes)
    if digest(source_bytes) != mask["source_hashes_after"]["handbell.kicad_pcb"]:
        raise ValueError("PCB bytes do not match the reviewed source")
    if feed_bytes is None:
        fixture, report = build_fixture(source_bytes.decode("utf-8-sig"), mask)
    else:
        if digest(feed_bytes) != FEED_SHA256:
            raise ValueError("Feed evidence hash does not match the reviewed report")
        ledger = json.loads(feed_bytes)
        if ledger["source_pcb_sha256"] != digest(source_bytes) or ledger["contact_mask_sha256"] != digest(mask_bytes):
            raise ValueError("Feed evidence source binding does not match inputs")
        fixture, report = build_feed_fixture(source_bytes.decode("utf-8-sig"), mask, ledger)
    report["input_sha256"] = {"pcb": digest(source_bytes), "mask": digest(mask_bytes)}
    if feed_bytes is not None:
        report["input_sha256"]["feed_candidate"] = digest(feed_bytes)
    output.mkdir(parents=True, exist_ok=False)
    (output / "contact-rule-fixture.kicad_pcb").write_bytes(fixture.encode("utf-8"))
    (output / "contact-rule-fixture.kicad_pro").write_bytes(b"{}\n")
    (output / "static-fixture-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--mask", type=Path, default=MASK)
    parser.add_argument("--feed-candidate", type=Path, help="Reviewed ledger for the import-only variant; omitting it preserves the original rule-control fixture")
    parser.add_argument("--output", type=Path, required=True, help="New, non-existing output directory")
    args = parser.parse_args()
    report = write_fixture(
        args.output, args.source.read_bytes(), args.mask.read_bytes(),
        None if args.feed_candidate is None else args.feed_candidate.read_bytes(),
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
