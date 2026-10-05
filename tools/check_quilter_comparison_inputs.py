#!/usr/bin/env python3
"""Independent static checker for the October 5 paired Quilter inputs.

This module never imports pcbnew.  It compares parsed PCB/project/schematic
bytes with the authoritative source, the saved native geometry inventory and
the independent selection, envelope, guard, role and supplier ledgers.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import math
import uuid
from dataclasses import dataclass
from pathlib import Path

from kicad_sexpr import Node, load, loads


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "hardware/handbell/iterations/printed-bell-four-layer"
REPORTS = REPO / "docs/measurements/2026-09-27-router-bakeoff"
WORKFLOW = REPO / "docs/design-inputs/2026-10-02-quilter-workflow.json"
INVENTORY = Path(
    r"C:\Projects\dcuccia\digital-handbell-routing-bakeoff-20260927\quilter"
    r"\outputs\inventory-final-recovery-20261002T142910-sol"
    r"\native-constraint-inventory.json"
)
R2 = Path(
    r"C:\Projects\dcuccia\digital-handbell-routing-bakeoff-20260927\quilter"
    r"\inputs\comparison-inputs-20261005T0746-sol-r2"
)

SOURCE_HASHES = {
    "handbell.kicad_pcb": "adc262b3e7056cb9031387c55262b5cf99e599ae6e28970f9784f5237e662314",
    "handbell.kicad_pro": "8213261803c4a032c6351311ed43db6249720a8cb334ebd15e3daca210899990",
    "handbell.kicad_sch": "ec93cc6f6f03bb91dd05199d2e0b4cab6b542567031e484fe8098056992ab69e",
    "placement-manifest.json": "b849b5defb95f010f555d43b6d261fdea3ef37e240aee0190a607fb519c642f8",
    "battery-contact-interface.json": "f96133d9f044600167477bcddbf67c43311ed0897066db9fa63d8e7f8118467b",
}
LEDGER_HASHES = {
    "quilter-prot-cout-release-contract-2026-10-04.json":
        "cc23592a8060db8a2732ff91954ff55e3177fbf733b22173b74062b7d4e5f896",
    "quilter-preserved-clock-qualification-2026-10-04.json":
        "e5e407129d1d7983c26921d09541ada6c623494adc6e32e356443ddd9d59ecc9",
    "quilter-trial-envelope-2026-10-03.json":
        "4178978d8e52db4d0b498e9e12aafdca5e43f098e43a7d084877ece1ed0da655",
    "quilter-native-guard-encoding-2026-10-04.json":
        "933a6ede3c9a47dbd7e8f77f3d3159b1303344e0fa0c3253448eaedd6d402cac",
    "quilter-contact-via-mask-2026-10-03.json":
        "489503349d1f05968ea165237a99bbd01e4381983b1f40273a9ab98fdef17fda",
    "quilter-four-six-role-selection-2026-10-04.json":
        "724b755b3f500250e3990cd77e8177d6da8db7c68070dc7f335ee143b9e65c1e",
    "quilter-four-six-stackup-source-screen-2026-10-04.json":
        "ef0a395804060313d207195cb9d19c19323936d9bb92ec2a1897d25f2e8e914e",
}
INVENTORY_HASH = "edba323c00da212fd881be71cc98f5d1afd8d8ca15ac4545c4b79bf609a7b7ba"
R2_HASHES = {
    "four-3313": "7695b88eef1b7a249e9f930c1d735fc4a527d152bce8c17c9a14517226f969db",
    "six-3313": "97d99b4d2c906f5a8a7bc377f8762fff383c2dc9a2591a7fb24d9a0fa47876d2",
}
R2_MANIFEST_HASHES = {
    "four-3313": "e5f4f63892288272347debb7210eb2e53e41f3fc1092b6429a099ab67f3ecddd",
    "six-3313": "31332bd457e1d33c3f8a9649c31c81c68d9d757a978467b9faf7e3ff03921521",
}
RESERVATION_REFS = {"J1", "J2", "MH1", "MH2", "X6"}
NS = uuid.UUID("cc59ed69-b83e-4553-93eb-1d497151a26e")
ALL_ALLOWED = {
    "tracks": "allowed", "vias": "allowed", "pads": "allowed",
    "copperpour": "allowed", "footprints": "allowed",
}
RESERVATION_FLAGS = {**ALL_ALLOWED, "footprints": "not_allowed"}
CONTACT_FLAGS = {
    "tracks": "not_allowed", "vias": "not_allowed", "pads": "allowed",
    "copperpour": "not_allowed", "footprints": "allowed",
}
ALL_PROHIBITED = {key: "not_allowed" for key in ALL_ALLOWED}
MINIMA = {
    "min_clearance": .2, "min_copper_edge_clearance": .25,
    "min_track_width": .1778, "min_via_diameter": .65,
    "min_through_hole_diameter": .35, "min_via_annular_width": .15,
}
DEFAULT_CLASS = {
    "clearance": .2, "track_width": .1778, "via_diameter": .65, "via_drill": .35,
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def ident(name: str) -> str:
    return str(uuid.uuid5(NS, name))


NUMERIC_HEADS = {
    "at", "start", "end", "mid", "center", "xy", "size", "drill", "width",
    "thickness", "epsilon_r", "loss_tangent", "clearance", "min_thickness",
    "thermal_gap", "thermal_bridge_width", "thermal_bridge_angle", "offset",
    "roundrect_rratio", "rect_delta", "solder_mask_margin",
    "solder_paste_margin", "solder_paste_margin_ratio", "zone_connect",
}
ORDERED_CHILD_HEADS = {"pts"}


def number(value):
    try:
        return round(float(value), 9)
    except (TypeError, ValueError):
        return value


def canon(node: Node, *, unordered_children: bool = False, omit=frozenset()):
    children = [canon(x, unordered_children=False) for x in node.children()
                if x.head not in omit]
    if unordered_children:
        children.sort(key=lambda x: json.dumps(x, separators=(",", ":")))
    raw_atoms = node.atoms()[1:]
    # Numeric normalization is deliberately field-typed.  Identifiers such as
    # pad "01", net names and library strings must never collapse to numbers.
    normalized = [number(x) for x in raw_atoms] if node.head in NUMERIC_HEADS else raw_atoms
    return [node.head, *normalized, *children]


def semantic(node: Node, *, angle_offset=0.0):
    raw = node.atoms()[1:]
    normalized = [number(x) for x in raw] if node.head in NUMERIC_HEADS else list(raw)
    if node.head == "hatch" and len(normalized) >= 2:
        normalized[-1] = number(normalized[-1])
    if node.head == "fill" and normalized[:1] == ["none"]:
        normalized[0] = "no"
    if node.head == "fill" and normalized[:1] == ["solid"]:
        normalized[0] = "yes"
    children = [semantic(x, angle_offset=angle_offset) for x in node.children()]
    if node.head not in ORDERED_CHILD_HEADS:
        children.sort(key=lambda x: json.dumps(x, separators=(",", ":")))
    return [node.head, *normalized, *children]


def semantic_optional(node: Node | None):
    return None if node is None else semantic(node)


def atoms(node: Node | None):
    return None if node is None else canon(node)[1:len(node.atoms())]


def close_seq(actual, expected, tolerance=1e-6):
    return len(actual) == len(expected) and all(
        abs(float(a) - float(b)) <= tolerance for a, b in zip(actual, expected)
    )


def child_last(node: Node, name: str):
    item = node.child(name)
    return None if item is None else item.atoms()[-1]


def single_value(node: Node, name: str):
    children = node.children(name)
    return children[0].atoms()[-1] if len(children) == 1 else None


def points(node: Node) -> list[list[float]]:
    polygon = node.child("polygon")
    if polygon is None or polygon.child("pts") is None:
        return []
    return [[float(x) for x in p.atoms()[1:3]]
            for p in polygon.child("pts").children("xy")]


def single_zone_geometry(node: Node) -> bool:
    """Generated zones have one layer declaration and one ordered polygon."""
    polygons = node.children("polygon")
    layers = node.children("layer")
    return (
        len(polygons) == 1 and len(layers) == 1 and
        polygons[0].child("pts") is not None and
        len(polygons[0].children("pts")) == 1
    )


def flags(node: Node):
    keepout = node.child("keepout")
    return {} if keepout is None else {
        key: child_last(keepout, key) for key in ALL_ALLOWED
    }


def net_name(node: Node):
    named = node.child("net_name")
    if named is not None:
        return named.atoms()[-1]
    net = node.child("net")
    return None if net is None else net.atoms()[-1]


def unique_map(items, key, errors, label):
    result = {}
    for item in items:
        value = key(item)
        if value is None or value in result:
            errors.append(f"{label}:duplicate_or_missing:{value}")
        else:
            result[value] = item
    return result


@functools.lru_cache(maxsize=1)
def selected_ids():
    retained = set(read_json(REPORTS / next(iter(LEDGER_HASHES)))["selection"]["retained_uuids"])
    clock = read_json(REPORTS / "quilter-preserved-clock-qualification-2026-10-04.json")
    retained.update(clock["union_with_original177"]["addition_uuids"])
    return retained


@functools.lru_cache(maxsize=1)
def room_polygon():
    result = []
    for i in range(49):
        a = math.pi - math.pi * i / 48
        result.append([100 + 22.5 * math.cos(a), 100 + 22.5 * math.sin(a)])
    edge = math.asin(5.75 / 22.5)
    for i in range(1, 25):
        a = -math.pi * i / 48
        if a <= -math.pi / 2 + edge:
            break
        result.append([100 + 22.5 * math.cos(a), 100 + 22.5 * math.sin(a)])
    result.extend([[105.75, 78.247127], [105.75, 73.15],
                   [94.25, 73.15], [94.25, 78.247127]])
    for i in range(24, 0, -1):
        a = -math.pi + math.pi * i / 48
        if a < -math.pi / 2 - edge:
            result.append([100 + 22.5 * math.cos(a), 100 + 22.5 * math.sin(a)])
    return result


@functools.lru_cache(maxsize=1)
def reservation_spec():
    rows = read_json(REPORTS / "quilter-trial-envelope-2026-10-03.json")[
        "reservation_layer"]["fixed_proxy_bodies_or_domains"]
    by_ref = {x["reference"]: x for x in rows if x["reference"] in RESERVATION_REFS}
    if set(by_ref) != RESERVATION_REFS:
        raise ValueError("reservation ledger population")
    result = {}
    for ref, row in by_ref.items():
        if ref.startswith("MH"):
            cx, cy = row["center_common_xy_mm"]
            # 0.0000005 mm radial serialization error still leaves containment.
            radius = row["radius_mm"] / math.cos(math.pi / 96) + 0.000001
            result[ref] = [[100 + cx + radius * math.cos(2 * math.pi * i / 96),
                            100 + cy + radius * math.sin(2 * math.pi * i / 96)]
                           for i in range(96)]
        else:
            result[ref] = [[100 + x, 100 + y] for x, y in row["polygon_common_xy_mm"]]
    return result


@functools.lru_cache(maxsize=None)
def profile_spec(profile):
    roles = read_json(REPORTS / "quilter-four-six-role-selection-2026-10-04.json")
    role_id = "four-3313" if profile == "four-3313" else "six-3313-reference-rich"
    role = next(x for x in roles["profiles"] if x["id"] == role_id)
    supplier = read_json(
        REPORTS / "quilter-four-six-stackup-source-screen-2026-10-04.json")
    construction = next(
        x for x in supplier["constructions"]
        if x["name"] == role["supplier_construction"]
    )
    dk = supplier["material_model"]
    layers, stack, planes = [], [], []
    copper_names = ["F.Cu", *[f"In{i}.Cu" for i in range(
        1, construction["copper_layers"] - 1)], "B.Cu"]
    copper_index = 0
    dielectric_index = 0
    for row in construction["ordered_layers"]:
        if row["role"] == "copper":
            name = copper_names[copper_index]
            selected = role["layer_roles_in_physical_order"][copper_index]
            token = "power" if selected["role"] == "ground" else "signal"
            layers.append((name, token))
            stack.append((name, "copper", row["thickness_mm"], None, None))
            if selected["role"] == "ground":
                planes.append(name)
            copper_index += 1
        else:
            dielectric_index += 1
            material = row["material"]
            dtype = "core" if material == "core" else "prepreg"
            if material == "core":
                epsilon = dk["published_core_Dk"]
            elif material.startswith("3313"):
                epsilon = dk["published_prepreg_Dk"]["3313"]
            else:
                epsilon = dk["published_prepreg_Dk"]["2116"]
            stack.append((f"dielectric {dielectric_index}", dtype,
                          row["thickness_mm"], material, epsilon))
    return layers, stack, planes


@dataclass
class Result:
    errors: list[str]
    observations: dict

    @property
    def passed(self):
        return not self.errors

    def as_dict(self):
        return {"passed": self.passed, "errors": self.errors,
                "observations": self.observations}


@functools.lru_cache(maxsize=1)
def binding_errors():
    errors = []
    for name, expected in SOURCE_HASHES.items():
        if sha(SOURCE / name) != expected:
            errors.append(f"binding:source:{name}")
    for name, expected in LEDGER_HASHES.items():
        if sha(REPORTS / name) != expected:
            errors.append(f"binding:ledger:{name}")
    if sha(INVENTORY) != INVENTORY_HASH:
        errors.append("binding:native_inventory")
    for profile, expected in R2_HASHES.items():
        if sha(R2 / profile / "handbell.kicad_pcb") != expected:
            errors.append(f"binding:r2_pcb:{profile}")
        if sha(R2 / profile / "input-manifest.json") != R2_MANIFEST_HASHES[profile]:
            errors.append(f"binding:r2_manifest:{profile}")
    return tuple(errors)


def verify_bindings(errors):
    errors.extend(binding_errors())


def pad_semantics(pad: Node):
    ignored = {"at", "layers", "net", "uuid"}
    fields = [semantic(x) for x in pad.children() if x.head not in ignored]
    fields.sort(key=lambda x: json.dumps(x, separators=(",", ":")))
    return {
        "atoms": pad.atoms()[1:],
        "size": atoms(pad.child("size")),
        "drill": None if pad.child("drill") is None else canon(pad.child("drill")),
        "layers": sorted(pad.child("layers").atoms()[1:]),
        "net": net_name(pad),
        "uuid": pad.value("uuid"),
        "fields": fields,
    }


def footprint_semantics(fp: Node, *, source_side=False, ignore_text_angles=False):
    omitted = {"at", "uuid", "pad"}
    fp_at = fp.child("at")
    fp_angle = 0.0 if fp_at is None or len(fp_at.atoms()) < 4 else float(fp_at.atoms()[3])
    fields = []
    for child in fp.children():
        if child.head in omitted:
            continue
        if child.head == "embedded_fonts" and child.atoms()[1:] == ["no"]:
            continue
        if child.head == "duplicate_pad_numbers_are_jumpers" and \
                child.atoms()[1:] == ["no"]:
            continue
        if child.head == "property" and child.atoms()[1] in {
                "Datasheet", "Description"} and child.atoms()[2] == "":
            continue
        record = semantic(child)
        if child.head == "attr":
            record = ["attr", *sorted(record[1:])]
        if child.head in {"property", "fp_text", "fp_text_box"}:
            for nested in record:
                if isinstance(nested, list) and nested[:1] == ["at"]:
                    # KiCad writes an omitted text angle as an explicit zero or
                    # as the footprint-relative physical angle.  Make the
                    # typed default explicit on both sides; apply the saved
                    # footprint transform only to source text.
                    while len(nested) < 4:
                        nested.append(0.0)
                    source_at = child.child("at")
                    transform = source_side and (
                        child.head != "property" or
                        source_at is not None and len(source_at.atoms()) < 4
                    )
                    angle = float(nested[3]) + (fp_angle if transform else 0.0)
                    nested[3] = 0.0 if ignore_text_angles else number(angle % 360)
            if child.head == "property":
                # A property UUID absent in source text is writer-generated.
                # Existing source UUIDs are checked separately below.
                record = [x for x in record
                          if not (isinstance(x, list) and x[:1] == ["uuid"])]
                for nested in record:
                    if isinstance(nested, list) and nested[:1] == ["effects"]:
                        for font in nested[1:]:
                            if isinstance(font, list) and font[:1] == ["font"] and \
                                    not any(isinstance(x, list) and
                                            x[:1] == ["thickness"] for x in font[1:]):
                                font.append(["thickness", .15])
                                font[1:] = sorted(
                                    font[1:],
                                    key=lambda x: json.dumps(x, separators=(",", ":")))
        if child.head.startswith("fp_"):
            record = [x for x in record
                      if not (isinstance(x, list) and x[:1] == ["uuid"])]
        fields.append(record)
    fields.sort(key=lambda x: json.dumps(x, separators=(",", ":")))
    return {"library": fp.atoms()[1], "layer": fp.value("layer"), "fields": fields}


def compare_footprints(source, board, baseline, inventory, fixed, baseline_manifest, errors):
    src = unique_map(source.children("footprint"),
                     lambda x: x.properties().get("Reference"), errors, "source_footprint")
    out = unique_map(board.children("footprint"),
                     lambda x: x.properties().get("Reference"), errors, "footprint")
    base = unique_map(baseline.children("footprint"),
                      lambda x: x.properties().get("Reference"), errors,
                      "baseline_footprint")
    if set(out) != set(src) or len(out) != 104:
        errors.append(f"footprint_population:{len(out)}")
    if set(inventory) != set(src):
        errors.append("inventory_footprint_population")
    move_map = baseline_manifest["move_map"]
    pad_count = 0
    seen_pads = set()
    for ref in sorted(set(src) & set(out) & set(inventory)):
        expected_native = inventory[ref]
        actual = out[ref]
        if actual.value("uuid") != expected_native["uuid"]:
            errors.append(f"footprint_uuid:{ref}")
        if actual.atoms()[1] != expected_native["library_id"]:
            errors.append(f"footprint_library:{ref}")
        if actual.properties().get("Value") != expected_native["value"]:
            errors.append(f"footprint_value:{ref}")
        if footprint_semantics(actual, ignore_text_angles=True) != footprint_semantics(
                src[ref], source_side=True, ignore_text_angles=True):
            errors.append(f"footprint_source_definition:{ref}")
        source_properties = {
            x.atoms()[1]: x for x in src[ref].children("property")
            if x.child("uuid") is not None
        }
        actual_properties = {
            x.atoms()[1]: x for x in actual.children("property")
        }
        for name, source_property in source_properties.items():
            if name not in actual_properties or \
                    actual_properties[name].value("uuid") != source_property.value("uuid"):
                errors.append(f"footprint_source_property_uuid:{ref}:{name}")
        source_child_uuids = {
            x.value("uuid") for x in src[ref].children()
            if x.head != "pad" and x.child("uuid") is not None
        }
        actual_child_uuids = {
            x.value("uuid") for x in actual.children()
            if x.head != "pad" and x.child("uuid") is not None
        }
        if not source_child_uuids <= actual_child_uuids:
            errors.append(f"footprint_source_child_uuid:{ref}")
        if footprint_semantics(actual) != footprint_semantics(base[ref]):
            errors.append(f"footprint_r2_surgical:{ref}")
        baseline_child_uuids = {
            x.value("uuid") for x in base[ref].children()
            if x.head != "pad" and x.child("uuid") is not None
        }
        if actual_child_uuids != baseline_child_uuids:
            errors.append(f"footprint_r2_child_uuid:{ref}")
        actual_at = [float(x) for x in actual.child("at").atoms()[1:]]
        actual_pose = actual_at[:2] + [actual_at[2] if len(actual_at) > 2 else 0.0]
        if ref in fixed:
            expected_pose = expected_native["position_mm"] + [expected_native["orientation_deg"]]
        else:
            expected_pose = move_map[ref]["to_native_xy_mm"] + [expected_native["orientation_deg"]]
        if not close_seq(actual_pose, expected_pose):
            errors.append(f"footprint_pose:{ref}:{actual_pose}")
        src_pads = {x.value("uuid"): x for x in src[ref].children("pad")}
        out_pads = unique_map(actual.children("pad"), lambda x: x.value("uuid"),
                              errors, f"pad:{ref}")
        inv_pads = {x["uuid"]: x for x in expected_native["pads"]}
        if set(out_pads) != set(src_pads) or set(out_pads) != set(inv_pads):
            errors.append(f"pad_population:{ref}")
        for uid in sorted(set(out_pads) & set(src_pads) & set(inv_pads)):
            pad_count += 1
            if uid in seen_pads:
                errors.append(f"pad_uuid_duplicate:{uid}")
            seen_pads.add(uid)
            candidate = out_pads[uid]
            expected = src_pads[uid]
            native_pad = inv_pads[uid]
            if pad_semantics(candidate) != pad_semantics(expected):
                errors.append(f"pad_definition:{ref}:{uid}")
            if candidate.atoms()[1] != native_pad["number"]:
                errors.append(f"pad_number:{ref}:{uid}")
            ca = [float(x) for x in candidate.child("at").atoms()[1:]]
            ea = [float(x) for x in expected.child("at").atoms()[1:]]
            if not close_seq(ca[:2], ea[:2]):
                errors.append(f"pad_local_xy:{ref}:{uid}")
            candidate_angle = ca[2] if len(ca) > 2 else 0.0
            if abs((candidate_angle - native_pad["orientation_deg"] + 180) % 360 - 180) > 1e-6:
                errors.append(f"pad_native_angle:{ref}:{uid}")
            theta = math.radians(actual_pose[2])
            global_xy = [
                actual_pose[0] + math.cos(theta) * ca[0] + math.sin(theta) * ca[1],
                actual_pose[1] - math.sin(theta) * ca[0] + math.cos(theta) * ca[1],
            ]
            expected_global = list(native_pad["position_mm"])
            if ref not in fixed:
                expected_global = [
                    expected_global[i] + expected_pose[i] - expected_native["position_mm"][i]
                    for i in range(2)
                ]
            if not close_seq(global_xy, expected_global, 1.1e-6):
                errors.append(
                    f"pad_native_position:{ref}:{uid}:{global_xy}:{expected_global}")
    if pad_count != 325 or len(seen_pads) != 325:
        errors.append(f"pad_total:{pad_count}:{len(seen_pads)}")


def copper_record(item):
    names = ("start", "end", "width", "layer", "net", "at", "size", "drill",
             "layers", "remove_unused_layers", "keep_end_layers")
    return [item.head, item.value("uuid"), *[
        None if item.child(name) is None else canon(item.child(name)) for name in names
    ]]


def zone_record(zone):
    return semantic(zone)


def compare_outline(board, errors):
    expected = read_json(REPORTS / "quilter-trial-envelope-2026-10-03.json")[
        "analytic_outline"]["ordered_closed_clockwise_records"]
    edge_items = [x for x in board.children()
                  if x.head.startswith("gr_") and
                  single_value(x, "layer") == "Edge.Cuts"]
    actual = unique_map(edge_items, lambda x: x.value("uuid"), errors, "outline")
    expected_ids = {ident("edge/" + str(i)): (i, row)
                    for i, row in enumerate(expected)}
    if set(actual) != set(expected_ids) or len(edge_items) != 6:
        errors.append(f"outline_population_or_identity:{len(edge_items)}")
    for uid in sorted(set(actual) & set(expected_ids)):
        index, spec = expected_ids[uid]
        item = actual[uid]
        if item.head != f"gr_{spec['type']}":
            errors.append(f"outline_type:{index}")
        stroke = item.child("stroke")
        if stroke is None or canon(stroke) != [
                "stroke", ["width", .05], ["type", "default"]]:
            errors.append(f"outline_stroke:{index}")
        reversed_geometry = (
            close_seq([float(x) for x in item.child("start").atoms()[1:3]],
                      spec["end_native_xy_mm"], 1.1e-6) and
            close_seq([float(x) for x in item.child("end").atoms()[1:3]],
                      spec["start_native_xy_mm"], 1.1e-6))
        for field in ("start", "end", "mid"):
            key = f"{field}_native_xy_mm"
            if key in spec and not (
                    field in {"start", "end"} and reversed_geometry) and not close_seq(
                    [float(x) for x in item.child(field).atoms()[1:3]],
                    spec[key], 1.1e-6):
                errors.append(f"outline_geometry:{index}:{field}")
        if item.value("layer") != "Edge.Cuts":
            errors.append(f"outline_layer:{index}")


def compare_zones(profile, source, board, mode, errors):
    source_rules = {z.value("uuid"): z for z in source.children("zone")
                    if z.child("keepout") is not None}
    if len(source_rules) != 19:
        errors.append(f"source_rule_spec_population:{len(source_rules)}")
    zones = unique_map(board.children("zone"), lambda z: single_value(z, "uuid"),
                       errors, "zone")
    for zone in zones.values():
        for field in ("uuid", "name", "layer"):
            if len(zone.children(field)) > 1:
                errors.append(f"zone_structure:{field}:{single_value(zone, 'uuid')}")
    for uid, expected in source_rules.items():
        if uid not in zones or zone_record(zones[uid]) != zone_record(expected):
            errors.append(f"source_rule:{uid}")

    room = room_polygon()
    named = unique_map(board.children("zone"), lambda z: single_value(z, "name"),
                       errors, "zone_name")
    placement = named.get("QUILTER_F_PLACEMENT_ROOM")
    if placement is None or placement.value("uuid") != ident(f"{profile}/placement-room") or \
            single_value(placement, "layer") != "F.Cu" or \
            not single_zone_geometry(placement) or \
            flags(placement) != ALL_ALLOWED or not polygon_equal(points(placement), room):
        errors.append("placement_room")

    contact_rows = read_json(REPORTS / "quilter-contact-via-mask-2026-10-03.json")[
        "domains"]["native_via_only_rule_areas_expanded_each_edge_0_25_mm"]
    for row in contact_rows:
        name = "CONTACT_METAL_GUARD_" + row["name"]
        expected_points = [
            [100 + row["x_min_mm"], 100 + row["y_min_mm"]],
            [100 + row["x_max_mm"], 100 + row["y_min_mm"]],
            [100 + row["x_max_mm"], 100 + row["y_max_mm"]],
            [100 + row["x_min_mm"], 100 + row["y_max_mm"]],
        ]
        zone = named.get(name)
        if zone is None or zone.value("uuid") != ident(f"{profile}/contact/{row['name']}") or \
                single_value(zone, "layer") != "B.Cu" or \
                not single_zone_geometry(zone) or \
                flags(zone) != CONTACT_FLAGS or not polygon_equal(points(zone), expected_points):
            errors.append(f"contact_guard:{name}")

    guard = read_json(REPORTS / "quilter-native-guard-encoding-2026-10-04.json")[
        "native_encoding"]
    private_rows = list(guard["source_obligation_mapping"])
    if profile == "six-3313":
        private_rows += [{
            "native_name": x["name"], "layer": x["layer"],
            "native_guard_uuid": x["native_guard_uuid"],
            "native_polygon_points_mm": [
                [x["native_bounds_mm"][0], x["native_bounds_mm"][1]],
                [x["native_bounds_mm"][2], x["native_bounds_mm"][1]],
                [x["native_bounds_mm"][2], x["native_bounds_mm"][3]],
                [x["native_bounds_mm"][0], x["native_bounds_mm"][3]],
            ],
        } for x in guard["six_extra_via_guards"]]
    for row in private_rows:
        zone = named.get(row["native_name"])
        expected_uuid = ident(f"{profile}/private/{row.get('native_guard_uuid', row['native_name'])}")
        if zone is None or zone.value("uuid") != expected_uuid or \
                single_value(zone, "layer") != row["layer"] or \
                not single_zone_geometry(zone) or \
                flags(zone) != ALL_PROHIBITED or not polygon_equal(
                    points(zone), row["native_polygon_points_mm"]):
            errors.append(f"private_guard:{row['native_name']}")

    reservations = reservation_spec()
    for ref, expected_points in reservations.items():
        zone = named.get("FOOTPRINT_RESERVATION_" + ref)
        if mode == "r2":
            if zone is not None:
                errors.append(f"unexpected_reservation:{ref}")
            continue
        if zone is None or zone.value("uuid") != ident(
                f"{profile}/footprint-reservation/{ref}") or \
                single_value(zone, "layer") != "F.Cu" or \
                not single_zone_geometry(zone) or \
                flags(zone) != RESERVATION_FLAGS or not polygon_equal(
                    points(zone), expected_points, 2e-6):
            errors.append(f"reservation:{ref}")
            continue
        if ref.startswith("MH"):
            center = [110, 115.7] if ref == "MH1" else [90, 84.3]
            radii = [math.dist(p, center) for p in points(zone)]
            edge_min = min(
                point_segment_distance(center, a, b)
                for a, b in zip(points(zone), points(zone)[1:] + points(zone)[:1])
            )
            if edge_min < 3.2 or max(radii) - 3.2 > .00172:
                errors.append(f"reservation_circle_margin:{ref}:{edge_min}:{max(radii)}")

    layers, _, planes = profile_spec(profile)
    for layer in planes:
        name = "PROTECTED_GND_" + layer
        zone = named.get(name)
        if zone is None:
            errors.append(f"plane_missing:{layer}")
            continue
        expected_fields = {
            "uuid": ident(f"{profile}/plane/{layer}"),
            "name": name, "net": "GND", "layer": layer,
            "hatch": ["hatch", "edge", .5],
            "connect_pads": ["connect_pads", ["clearance", .2]],
            "min_thickness": ["min_thickness", .1778],
            "fill": ["fill", "yes", ["thermal_gap", .3],
                     ["thermal_bridge_width", .3]],
        }
        observed = {
            "uuid": zone.value("uuid"),
            "name": zone.value("name"), "net": net_name(zone),
            "layer": single_value(zone, "layer"),
            "hatch": semantic(zone.child("hatch")),
            "connect_pads": semantic(zone.child("connect_pads")),
            "min_thickness": semantic(zone.child("min_thickness")),
            "fill": semantic(zone.child("fill")),
        }
        expected_fields["fill"] = [
            "fill", "yes", ["island_removal_mode", "0"],
            ["thermal_bridge_width", .3], ["thermal_gap", .3]]
        if observed != expected_fields:
            errors.append(f"plane_definition:{layer}:fields:{observed!r}:{expected_fields!r}")
        if not single_zone_geometry(zone) or not polygon_equal(points(zone), room):
            errors.append(f"plane_definition:{layer}:polygon")
        if zone.children("filled_polygon") or zone.children("fill_segments"):
            errors.append(f"plane_unfilled:{layer}")

    expected_count = 19 + 1 + 8 + len(private_rows) + len(planes)
    if mode == "final":
        expected_count += 5
    if len(zones) != expected_count:
        errors.append(f"unexpected_zone_population:{len(zones)}:{expected_count}")
    if any((z.value("name") or "").startswith("DIAG_") for z in zones.values()):
        errors.append("diagnostic_zone")


def polygon_equal(actual, expected, tolerance=1e-6):
    return len(actual) == len(expected) and all(
        close_seq(a, b, tolerance) for a, b in zip(actual, expected)
    )


def point_segment_distance(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.dist(p, [a[0] + t * dx, a[1] + t * dy])


def compare_profile(profile, board, project, errors):
    expected_layers, expected_stack, _ = profile_spec(profile)
    actual_layers = [(int(x.atoms()[0]), x.atoms()[1], x.atoms()[2])
                     for x in board.child("layers").children()
                     if x.atoms()[1].endswith(".Cu")]
    ids = {"F.Cu": 0, "B.Cu": 2, "In1.Cu": 4, "In2.Cu": 6,
           "In3.Cu": 8, "In4.Cu": 10}
    expected_layer_rows = [(ids[name], name, role) for name, role in expected_layers]
    if actual_layers != expected_layer_rows:
        errors.append(f"physical_layers:{actual_layers}")
    stack = board.child("setup").child("stackup").children("layer")
    actual_stack = []
    for row in stack:
        material = child_last(row, "material")
        epsilon = child_last(row, "epsilon_r")
        actual_stack.append((
            row.atoms()[1], child_last(row, "type"),
            float(child_last(row, "thickness")),
            material, None if epsilon is None else float(epsilon),
        ))
    if len(actual_stack) != len(expected_stack):
        errors.append(f"stackup_population:{len(actual_stack)}")
    else:
        for index, (actual, expected) in enumerate(zip(actual_stack, expected_stack)):
            if actual[:2] != expected[:2] or not close_seq([actual[2]], [expected[2]]) or \
                    actual[3] != expected[3] or (
                        expected[4] is not None and not close_seq([actual[4]], [expected[4]])):
                errors.append(f"stackup_row:{index}:{actual}:{expected}")
    rules = project["board"]["design_settings"]["rules"]
    observed_minima = {key: rules.get(key) for key in MINIMA}
    if observed_minima != MINIMA:
        errors.append(f"project_minima:{observed_minima}")
    defaults = project["net_settings"]["classes"][0]
    observed_defaults = {key: defaults.get(key) for key in DEFAULT_CLASS}
    if observed_defaults != DEFAULT_CLASS:
        errors.append(f"default_class:{observed_defaults}")


@functools.lru_cache(maxsize=None)
def baseline_context(profile):
    _, board = load(R2 / profile / "handbell.kicad_pcb")
    return (
        board,
        read_json(R2 / profile / "handbell.kicad_pro"),
        read_json(R2 / profile / "input-manifest.json"),
    )


@functools.lru_cache(maxsize=1)
def source_context():
    _, board = load(SOURCE / "handbell.kicad_pcb")
    return (
        board,
        read_json(WORKFLOW)["selected_comparison_retention"],
        read_json(INVENTORY)["all_native_footprints_and_serialized_geometry"],
    )


def compare_r2_surgical_baseline(profile, board, project, errors):
    baseline, baseline_project, _ = baseline_context(profile)
    excluded = {
        "footprint", "segment", "via", "zone", "gr_line", "gr_arc", "layers", "setup",
    }
    actual = [canon(x) for x in board.children() if x.head not in excluded]
    expected = [canon(x) for x in baseline.children() if x.head not in excluded]
    if actual != expected:
        errors.append("unexpected_top_level_change_from_r2")
    if project != baseline_project:
        errors.append("unexpected_project_change_from_r2")


def check_text(profile: str, pcb_text: str, project, schematic_bytes: bytes,
               *, mode="r2", baseline_manifest=None, verify_hashes=True) -> Result:
    errors = []
    if profile not in R2_HASHES:
        return Result([f"unknown_profile:{profile}"], {})
    if mode not in {"r2", "final"}:
        return Result([f"unknown_mode:{mode}"], {})
    if verify_hashes:
        verify_bindings(errors)
    source, workflow, inventory = source_context()
    board = loads(pcb_text)
    if workflow["retained_primitives"] != 209 or workflow["fixed_pad_count"] != 164:
        errors.append("workflow_selected_contract")
    fixed = set(workflow["fixed_references"])
    clock_contract = read_json(
        REPORTS / "quilter-preserved-clock-qualification-2026-10-04.json")
    independent_fixed = set(
        clock_contract["prospective_fixed_population"]["references"])
    if len(fixed) != 32 or fixed != independent_fixed or \
            workflow.get("report_sha256") != (
                "f436c0811eca7ec0e6893256c0ddd72444ee2c70cd012c83912695db42a000e1"):
        errors.append("fixed_contract_population")
    if baseline_manifest is None:
        baseline_manifest = baseline_context(profile)[2]
    baseline_board = baseline_context(profile)[0]
    compare_footprints(source, board, baseline_board, inventory, fixed,
                       baseline_manifest, errors)

    expected_ids = selected_ids()
    source_copper = {x.value("uuid"): x for x in source.children()
                     if x.head in {"segment", "via"}}
    copper_items = [x for x in board.children()
                    if x.head in {"segment", "via", "arc"}]
    copper = unique_map(copper_items, lambda x: x.value("uuid"), errors, "copper")
    if set(copper) != expected_ids or len(copper) != 209:
        errors.append(f"retained_membership:{len(copper)}")
    for uid in sorted(set(copper) & expected_ids):
        if uid not in source_copper or copper_record(copper[uid]) != copper_record(source_copper[uid]):
            errors.append(f"retained_record:{uid}")
    cout = {uid for uid, item in source_copper.items() if net_name(item) == "/PROT_COUT"}
    if len(cout) != 35 or cout & set(copper):
        errors.append(f"COUT35:{len(cout)}:{len(cout & set(copper))}")

    compare_outline(board, errors)
    compare_zones(profile, source, board, mode, errors)
    compare_profile(profile, board, project, errors)
    compare_r2_surgical_baseline(profile, board, project, errors)
    if hashlib.sha256(schematic_bytes).hexdigest() != SOURCE_HASHES["handbell.kicad_sch"]:
        errors.append("schematic_hash")
    all_ids = [x.value("uuid") for x in board.walk() if x.child("uuid") is not None]
    if None in all_ids or len(all_ids) != len(set(all_ids)):
        errors.append("global_uuid_uniqueness")
    observations = {
        "profile": profile, "mode": mode, "references": len(board.children("footprint")),
        "pads": sum(len(x.children("pad")) for x in board.children("footprint")),
        "tracks": sum(x.head == "segment" for x in copper_items),
        "vias": sum(x.head == "via" for x in copper_items),
        "zones": len(board.children("zone")), "all_failures_reported": True,
    }
    return Result(errors, observations)


def check_package(profile: str, package: Path, *, mode="r2") -> Result:
    pcb = package / "handbell.kicad_pcb"
    if not pcb.is_file():
        return Result([f"missing_pcb:{pcb}"], {})
    return check_text(
        profile, pcb.read_text(encoding="utf-8-sig"),
        read_json(package / "handbell.kicad_pro"),
        (package / "handbell.kicad_sch").read_bytes(), mode=mode,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, choices=sorted(R2_HASHES))
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--mode", choices=("r2", "final"), required=True)
    args = parser.parse_args()
    result = check_package(args.profile, args.package, mode=args.mode)
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
