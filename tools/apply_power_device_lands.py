# SPDX-License-Identifier: MIT
"""Stage the recorded U5/R27 manufacturer land examples without moving parts."""
import argparse
import copy
import json
from pathlib import Path
import shutil

from apply_clock_definition_revision import prop_edits
from apply_power_lands import sha
import check_printed_bell_power_rework as check
from kicad_sexpr import apply_edits, load, loads
from native_footprint_fields import library_from_instance
from route_clock_local import PACKAGE, ROOT

BASE = "f6a9d31192c7e59c4b81b7bcb281e23fd06cdc201e8a7a1f180ae7a8f860e3e4"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--repair-u5-escapes", action="store_true")
    parser.add_argument("--expand-r27-exclusion", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or sha(PACKAGE / "handbell.kicad_pcb") != BASE:
        raise ValueError("Require the pinned power-land board and a new output directory")
    if args.expand_r27_exclusion and not args.repair_u5_escapes:
        raise ValueError("The exclusion correction builds on the U5 escape correction")
    register_path = ROOT / "hardware" / "handbell" / "parts" / "existing-part-review.json"
    register = json.loads(register_path.read_text(encoding="utf-8"))
    specs = {ref: group for group in register["parts"] for ref in group["references"]
             if ref in ("U5", "R27")}
    names = {"U5": "TPS61023_DRL_TI_Example", "R27": "ERJ6BW_0805_Panasonic_Example"}
    text, tree = load(PACKAGE / "handbell.kicad_pcb")
    edits, details = [], {}
    for fp in tree.children("footprint"):
        ref = fp.properties().get("Reference")
        if ref not in names:
            continue
        spec = specs[ref]
        assert fp.properties()["MPN"] == spec["quote_mpn"]
        geometry = spec["manufacturer_example_lands" if ref == "U5" else "proposed_minimum_span_lands"]
        centers = geometry["column_centers_x_mm" if ref == "U5" else "centers_x_mm"]
        sx, sy = geometry["size_mm"]
        edits.append((fp.items[1].start, fp.items[1].end, json.dumps("Handbell:" + names[ref])))
        if fp.child("attr") is None:
            edits.append((fp.end - 1, fp.end - 1, "\n(attr smd)\n"))
        pads = fp.children("pad")
        assert len(pads) == (6 if ref == "U5" else 2)
        changes = []
        for pad in pads:
            assert pad.atoms()[2:] == ["smd", "rect"]
            at, size = pad.child("at"), pad.child("size")
            x, y = map(float, at.atoms()[1:3])
            assert len(at.atoms()) == 3 or float(at.atoms()[3]) == 0
            old_centers = spec["native_lands"].get("column_centers_x_mm", spec["native_lands"].get("centers_x_mm"))
            assert x in old_centers and list(map(float, size.atoms()[1:])) == spec["native_lands"]["size_mm"]
            nx = centers[0 if x < 0 else 1]
            edits.extend(((at.start, at.end, f"(at {nx} {y})"),
                          (size.start, size.end, f"(size {sx} {sy})")))
            if ref == "U5":
                edits.append((pad.items[3].start, pad.items[3].end, "roundrect"))
                ratio = geometry["corner_radius_mm"] / min(sx, sy)
                edits.append((pad.end - 1, pad.end - 1, f"\n(roundrect_rratio {ratio})\n"))
                margin = pad.child("solder_mask_margin")
                edits.append((margin.start, margin.end,
                              f'(solder_mask_margin {geometry["nsmd_expansion_max_mm"]})'))
            changes.append({"number": pad.atoms()[1], "uuid": pad.value("uuid"),
                            "net": pad.value("net"), "old_xy_mm": [x, y],
                            "new_xy_mm": [nx, y], "old_size_mm": spec["native_lands"]["size_mm"],
                            "new_size_mm": [sx, sy]})
        details[ref] = {"old_footprint": fp.atoms()[1], "new_footprint": "Handbell:" + names[ref],
                        "native_pose_unchanged": fp.child("at").atoms()[1:],
                        "source_ids": spec["source_ids"], "pads": changes}
    assert details.keys() == names.keys()
    primitive_changes = []
    if args.repair_u5_escapes:
        # Keep the neck widths; move the adjacent widening/turns clear of the new lands.
        endpoints = {
            "745fcd9e-40cc-5272-833c-e3bc67e2894e": {"end": [98.9, 114.7]},
            "5f740232-0ad1-5df6-a1d0-daa1b956e7bf": {"start": [98.9, 114.7]},
            "088bee53-2413-5430-8acc-32a9f7f281d8": {"end": [98.9, 115.7]},
            "1882384a-8437-51aa-84e0-67f4c472cc46": {"start": [98.9, 115.7]},
            "7bce90b0-8c1e-5e58-a24c-60bfac93897d": {"end": [96.15, 115.7]},
            "96b369f0-8c8f-57ec-a828-7f759b9a8469": {"start": [96.15, 115.7], "end": [96.05, 115.6]},
            "777c69a3-6d88-54c4-b0c4-f5a0ae8bfdcf": {"start": [96.05, 115.6], "end": [96.0, 115.6]},
            "65d4fb9f-c79e-5bdb-96a9-94febf71ebbf": {"start": [96.0, 115.6], "end": [95.95, 115.55]},
            "24231eab-ec5d-52e1-a01c-10bb12a1db85": {"start": [95.95, 115.55], "end": [95.95, 115.5]},
            "70b2d1e0-eca8-52fc-bb62-caede28fc13b": {"start": [95.95, 115.5], "end": [95.85, 115.4]},
            "40ebf67d-4eef-5e66-9e9c-baf5cef87305": {"start": [95.85, 115.4], "end": [95.85, 113.1]},
            "47285eb4-b602-55dd-92e4-01c622054d09": {"start": [95.85, 113.1]},
        }
        for segment in tree.children("segment"):
            uid = segment.value("uuid")
            if uid not in endpoints:
                continue
            old = {key: list(map(float, segment.child(key).atoms()[1:])) for key in ("start", "end")}
            new = {**old, **endpoints[uid]}
            for key, (x, y) in endpoints[uid].items():
                node = segment.child(key)
                edits.append((node.start, node.end, f"({key} {x} {y})"))
            primitive_changes.append({"uuid": uid, "net": segment.value("net"),
                                      "width_mm_unchanged": float(segment.value("width")),
                                      "before": old, "after": new})
        assert len(primitive_changes) == len(endpoints)
    plan_path = PACKAGE / "reports" / "front-ground-plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    exclusion_changes = []
    for zone in tree.children("zone"):
        if args.expand_r27_exclusion and zone.value("uuid") == "f3661a20-0fd3-5f50-ab1e-e8bef7117484":
            record = next(r for r in plan["protection"]["pour_only_F_keepouts"]
                          if r["uuid"] == zone.value("uuid"))
            old = record["bounds_absolute_iu"]
            assert old == [85648019, 108549966, 87150019, 110451966]
            new = [old[0] - 50000, old[1], old[2] + 100000, old[3]]
            points = zone.child("polygon").child("pts").children("xy")
            assert len(points) == 4
            for point in points:
                x, y = [round(float(v) * 1e6) for v in point.atoms()[1:]]
                assert x in (old[0], old[2]) and y in (old[1], old[3])
                x = new[0] if x == old[0] else new[2]
                edits.append((point.start, point.end, f"(xy {x/1e6:.6f} {y/1e6:.6f})"))
            record["bounds_absolute_iu"] = new
            exclusion_changes.append({"uuid": record["uuid"], "before_bounds_iu": old,
                                      "after_bounds_iu": new,
                                      "reason": "Follow R27.2 land growth, retaining the original 0.251 mm bounding margin; do not weaken the 0.25 mm private-copper guard."})
        edits.extend((p.start, p.end, "") for p in zone.children("filled_polygon"))
    assert len(exclusion_changes) == int(args.expand_r27_exclusion)
    if exclusion_changes:
        plan["revision"] = {"input_plan_sha256": sha(plan_path), "changes": exclusion_changes}
    pcb_text = apply_edits(text, edits)
    sch_text, sch = load(PACKAGE / "handbell.kicad_sch")
    sch_edits = []
    for symbol in sch.children("symbol"):
        ref = symbol.properties().get("Reference")
        if ref in names:
            assert symbol.properties()["Footprint"] == details[ref]["old_footprint"]
            sch_edits.extend(prop_edits(symbol, {"Footprint": details[ref]["new_footprint"]}))
    sch_text = apply_edits(sch_text, sch_edits)
    manifest_path = PACKAGE / "placement-manifest.json"
    baseline = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert baseline["generated_pcb_sha256"] == BASE
    assert baseline["schematic_sha256"] == sha(PACKAGE / "handbell.kicad_sch")
    manifest = copy.deepcopy(baseline)
    for component in manifest["components"]:
        ref = component["reference"]
        if ref not in names:
            continue
        old = {key: component[key] for key in ("width_mm", "depth_mm", "height_mm")}
        assert list(old.values()) == specs[ref]["frozen_proxy_mm"]
        dimensions = (2.15, 2.0, .65) if ref == "U5" else (3.2, 1.45, .75)
        for key, value in zip(old, dimensions, strict=True):
            assert value >= component[key]
            component[key] = value
        assert component["side"] == "F" and component["z_max_mm"] == manifest["board"]["front_z_mm"]
        component["z_min_mm"] = component["z_max_mm"] - component["height_mm"]
        component["footprint"] = details[ref]["new_footprint"]
        component["height_source"] = "Conservative manufacturer/land envelope; not measured mounted height. See reports/power-device-lands.json."
        details[ref]["envelope"] = {"old_mm": list(old.values()), "new_mm": list(dimensions)}
    errors = []
    screen = check.placement_proxy_screen(check.generator(), set(), errors,
                                         baseline=baseline, manifest=manifest, resized=set(names))
    if errors:
        raise ValueError("Local envelope repair required: " + json.dumps({"errors": errors, "screen": screen}))
    shutil.copytree(PACKAGE, output, ignore=shutil.ignore_patterns(
        "reports", "input-checkpoint", "*.kicad_prl", "*.lck", "*-backups"))
    (output / "handbell.kicad_pcb").write_bytes(pcb_text.encode("utf-8"))
    (output / "handbell.kicad_sch").write_bytes(sch_text.encode("utf-8"))
    for fp in loads(pcb_text).children("footprint"):
        ref = fp.properties().get("Reference")
        if ref in names:
            module = library_from_instance(pcb_text, fp, names[ref])
            (output / "libraries" / "Handbell.pretty" / (names[ref] + ".kicad_mod")).write_bytes(module.encode("utf-8"))
    manifest.update(generated_pcb_sha256=sha(output / "handbell.kicad_pcb"),
                    schematic_sha256=sha(output / "handbell.kicad_sch"),
                    current_stage_report="reports/power-device-lands.json", mechanical_rebind_required=True)
    (output / "placement-manifest.json").write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    report = {"status": "STAGED_NOT_ACCEPTED", "input_pcb_sha256": BASE,
              "input_manifest_sha256": sha(manifest_path), "register_sha256": sha(register_path),
              "generator_sha256": sha(Path(__file__)), "changes": details, "screen": screen,
              "output_pcb_sha256": sha(output / "handbell.kicad_pcb"),
              "output_schematic_sha256": sha(output / "handbell.kicad_sch"),
              "output_manifest_sha256": sha(output / "placement-manifest.json"),
              "component_moves": [], "copper_primitive_changes": primitive_changes,
              "private_exclusion_changes": exclusion_changes,
              "corrective_u5_escape_pass": args.repair_u5_escapes, "ground_fill_invalidated": True,
              "remaining": "Local geometry, continuity, private pickoffs, refill, DRC/ERC, library agreement and assembly review."}
    (output / "reports").mkdir()
    (output / "reports" / "front-ground-plan.json").write_bytes((json.dumps(plan, indent=2) + "\n").encode("utf-8"))
    (output / "reports" / "power-device-lands.json").write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"status": report["status"], "screen": screen}))


if __name__ == "__main__":
    main()
