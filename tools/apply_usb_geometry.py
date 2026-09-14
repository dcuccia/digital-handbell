# SPDX-License-Identifier: MIT
"""Stage the approved X6-only drawing-based correction; never overwrite a package."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import uuid

from apply_clock_definition_revision import prop_edits
from kicad_sexpr import apply_edits, load, loads
from native_identity_fields import prepare_fields, apply_manifest_fields
from native_footprint_fields import library_from_instance
from route_clock_local import PACKAGE, ROOT

OLD = "Adafruit Feather RP2040 Prop-Maker-import-fps:USB_C_CUSB31-CFM2AX-01-X"
NAME = "USB_C_HRO_TYPE_C_31_M_12_Handbell"
NEW = "Handbell:" + NAME
BASE = "307122d6838df5dda24331091c463930889a2185fb01b57ae95cab107337c408"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repair_approaches(text):
    tree = loads(text)
    removed = {
        "318437f4-fa67-5d9e-b35a-e2a02e3e0d6c", "e5368300-6b5a-522b-90b9-da09b595dd23",
        "862e2b2a-46b1-522c-b1dc-8272d2a634f5", "5219b022-f6e8-50c8-85ab-96851214bb2c",
        "3d626e95-efbf-5c3f-85f6-ee7a5b77c29d",
    }
    maps = {
        "CC1": {(95.4094, 77.4914): (95.2, 77.4914), (94.6483, 78.2525): (94.6483, 78.0431)},
        "CC2": {(98.25, 80.5426): (98.35, 80.5426), (98.5194, 80.2732): (98.6194, 80.2732)},
        "VBUS": {(105.1444, 77.4368): (101.9, 78.23)},
    }
    edits, changed, deleted = [], [], set()
    for item in tree.children():
        if item.head not in ("segment", "via"):
            continue
        uid, net = item.value("uuid"), item.value("net")
        if uid in removed:
            assert net == "VBUS" and item.value("layer") == "F.Cu"
            edits.append((item.start, item.end, ""))
            deleted.add(uid)
            continue
        for key in ("start", "end", "at"):
            point = item.child(key)
            if point is None:
                continue
            original = tuple(map(float, point.atoms()[1:3]))
            replacement = maps.get(net, {}).get(original)
            if replacement is None:
                continue
            if uid == "035a896c-b52b-533c-a74f-f165f4d21113":
                replacement = (98.25, 80.4426)
            if uid == "4cc36db8-8b94-54c6-b930-2cae03aec8be":
                replacement = (101.9, 77.4368)
            edits.append((point.start, point.end, f"({key} {replacement[0]:.6f} {replacement[1]:.6f})"))
            changed.append(uid)
    assert deleted == removed
    routes = [
        ("VBUS", "F.Cu", (102.4, 79.655), (102.25, 79.505)),
        ("VBUS", "F.Cu", (102.25, 79.505), (102.25, 78.58)),
        ("VBUS", "F.Cu", (102.25, 78.58), (101.9, 78.23)),
        ("VBUS", "B.Cu", (101.9, 77.4368), (101.9, 78.23)),
        ("CC2", "F.Cu", (98.25, 80.4426), (98.35, 80.5426)),
    ]
    added, lines = [], []
    for index, (net, layer, start, end) in enumerate(routes):
        uid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"digital-handbell/usb-closure/{index}"))
        assert not any(n.value("uuid") == uid for n in tree.children())
        added.append(uid)
        lines.append(f'(segment (start {start[0]} {start[1]}) (end {end[0]} {end[1]}) '
                     f'(width 0.1778) (layer "{layer}") (net "{net}") (uuid "{uid}"))')
    edits.append((tree.end - 1, tree.end - 1, "\n" + "\n".join(lines) + "\n"))
    return apply_edits(text, edits), {
        "nets": ["CC1", "CC2", "VBUS"], "removed_track_uuids": sorted(removed),
        "changed_copper_uuids": sorted(set(changed)), "added_track_uuids": added,
        "new_vias": 0, "relocated_existing_vias": 2,
        "rationale": "Clear enlarged anchors and moved outer lands. Shorten the VBUS wrap using its existing via on a clear rearward escape; retain widths and all endpoints.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or sha(PACKAGE / "handbell.kicad_pcb") != BASE:
        raise ValueError("Require the pinned input and a new staging directory")
    register_path = ROOT / "hardware" / "handbell" / "parts" / "hro-usb-candidate.json"
    register = json.loads(register_path.read_text(encoding="utf-8"))
    spec = register["authorized_engineering_variant"]
    if register["mpn"] != "TYPE-C-31-M-12" or spec["outer_pad_center_local_y_mm"] != -2.475:
        raise ValueError("USB decision changed; review before generation")
    properties = {
        "MPN": register["mpn"], "Manufacturer": register["manufacturer"],
        "Datasheet": register["source"]["product_url"],
        "Description": "HRO TYPE-C-31-M-12; modified slots/outer lands; secondary solder all four anchors.",
    }
    specifications = {"X6": {
        "expected_values": ["USB Type C"], "expected_footprints": [OLD],
        "properties": properties,
    }}
    text, tree = load(PACKAGE / "handbell.kicad_pcb")
    text, _ = prepare_fields(text, tree, "footprint", specifications)
    tree = loads(text)
    fp = next(f for f in tree.children("footprint") if f.properties().get("Reference") == "X6")
    assert fp.atoms()[1] == OLD and fp.child("at").atoms()[1:] == ["100.000000", "77.180000", "180"]
    changes = [(fp.items[1].start, fp.items[1].end, json.dumps(NEW))]
    assert fp.child("attr") is None
    changes.append((fp.end - 1, fp.end - 1, '\n(attr through_hole)\n'))
    before_nets = {p.value("uuid"): p.value("net") for p in fp.children("pad")}
    for pad in fp.children("pad"):
        number = pad.atoms()[1]
        at = pad.child("at")
        if number in spec["outer_pads_to_shift"]:
            assert at.atoms()[2] == "-2.275"
            changes.append((at.start, at.end, f'(at {at.atoms()[1]} -2.475)'))
        elif number in ("M1", "M2", "M3", "M4"):
            assert at.atoms()[3] == "90" and pad.child("drill").atoms()[1:] == ["0.6"]
            x = -4.325 if number in ("M1", "M3") else 4.325
            rear = number in ("M1", "M2")
            # Preserve the local 90-degree pad angle: size/drill X becomes footprint-local Y.
            replacements = {
                "at": f'(at {x} {at.atoms()[2]} 90)',
                "size": "(size 2.2 1.1)" if rear else "(size 1.9 1.1)",
                "drill": "(drill oval 1.7 0.6)" if rear else "(drill oval 1.4 0.6)",
            }
            for key, value in replacements.items():
                node = pad.child(key)
                changes.append((node.start, node.end, value))
    moved_paste, removed_paste = [], []
    for poly in fp.children("fp_poly"):
        if poly.value("layer") != "F.Paste":
            continue
        points = poly.child("pts").children("xy")
        if max(abs(float(p.atoms()[1])) for p in points) > 3.8:
            changes.append((poly.start, poly.end, ""))
            removed_paste.append(poly.value("uuid"))
        else:
            for point in points:
                x, y = map(float, point.atoms()[1:])
                changes.append((point.start, point.end, f"(xy {x:.6f} {y - .2:.6f})"))
            moved_paste.append(poly.value("uuid"))
    assert len(moved_paste) == len(removed_paste) == 4
    for zone in tree.children("zone"):
        changes.extend((p.start, p.end, "") for p in zone.children("filled_polygon"))
    pcb_text, repairs = repair_approaches(apply_edits(text, changes))
    new_fp = next(f for f in loads(pcb_text).children("footprint") if f.properties().get("Reference") == "X6")
    assert before_nets == {p.value("uuid"): p.value("net") for p in new_fp.children("pad")}
    module = library_from_instance(pcb_text, new_fp, NAME)
    sch_text, sch = load(PACKAGE / "handbell.kicad_sch")
    sch_text, _ = prepare_fields(sch_text, sch, "symbol", specifications)
    instance = next(s for s in loads(sch_text).children("symbol") if s.properties().get("Reference") == "X6")
    sch_text = apply_edits(sch_text, prop_edits(instance, {"Footprint": NEW}))
    manifest = json.loads((PACKAGE / "placement-manifest.json").read_text(encoding="utf-8"))
    assert manifest["generated_pcb_sha256"] == BASE
    assert manifest["schematic_sha256"] == sha(PACKAGE / "handbell.kicad_sch")
    apply_manifest_fields(manifest, specifications)
    component = next(c for c in manifest["components"] if c["reference"] == "X6")
    component.update(footprint=NEW, y_mm=-24.01, depth_mm=8.08)
    reservation = manifest["cross_face_keepouts"][0]
    assert reservation["source"].startswith("X6") and reservation["plan_h"] == 8.93
    reservation.update(y=-24.01, plan_h=9.08,
                       source="X6 conservative body/drill projection plus 0.5 mm per edge; secondary-anchor solder remains unqualified")
    manifest["usb_interface"].update(
        selected_mpn=register["mpn"], component_front_bound_common_y_mm=-28.05,
        anchor_assembly="Secondary solder all four plated anchors; supplier acceptance pending")
    shutil.copytree(PACKAGE, output, ignore=shutil.ignore_patterns(
        "reports", "input-checkpoint", "*.kicad_prl", "*.lck", "*-backups"))
    for name, content in (("handbell.kicad_pcb", pcb_text), ("handbell.kicad_sch", sch_text),
                          (str(Path("libraries") / "Handbell.pretty" / (NAME + ".kicad_mod")), module)):
        (output / name).write_bytes(content.encode("utf-8"))
    manifest.update(generated_pcb_sha256=sha(output / "handbell.kicad_pcb"),
                    schematic_sha256=sha(output / "handbell.kicad_sch"),
                    current_stage_report="reports/usb-geometry.json", mechanical_rebind_required=True)
    (output / "placement-manifest.json").write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    (output / "reports").mkdir()
    report = {
        "status": "STAGED_NOT_ACCEPTED", "input_pcb_sha256": BASE,
        "register_sha256": sha(register_path), "generator_sha256": sha(Path(__file__)),
        "output_pcb_sha256": sha(output / "handbell.kicad_pcb"),
        "output_schematic_sha256": sha(output / "handbell.kicad_sch"),
        "pad_uuid_to_net_unchanged": True, "removed_anchor_paste_uuids": removed_paste,
        "shifted_outer_paste_uuids": moved_paste, "ground_fill_invalidated": True,
        "fixed_connector_origin_unchanged": True, "selected_variant": spec,
        "local_copper_repairs": repairs,
        "remaining": "Native geometry/DRC, connectivity, refill, manufacturing and full mechanical bind required.",
    }
    (output / "reports" / "usb-geometry.json").write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"status": report["status"], "pcb_sha256": report["output_pcb_sha256"]}))


if __name__ == "__main__":
    main()
