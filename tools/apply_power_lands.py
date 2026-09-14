# SPDX-License-Identifier: MIT
"""Stage the selected eleven power/passive land patterns without moving parts."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import uuid

from apply_clock_definition_revision import prop_edits
from kicad_sexpr import apply_edits, load, loads
from native_footprint_fields import library_from_instance
from route_clock_local import PACKAGE, ROOT

BASE = "7f2abd76c716364b77356bb251e889ea2dfcc1efe9eaa3e33e55b59a7cd8ba16"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    output = parser.parse_args().output.resolve()
    if output.exists() or sha(PACKAGE / "handbell.kicad_pcb") != BASE:
        raise ValueError("Require pinned complete-identity input and a new staging directory")
    register_path = ROOT / "hardware" / "handbell" / "parts" / "power-component-candidates.json"
    register = json.loads(register_path.read_text(encoding="utf-8"))
    groups = [*register["groups"], register["closely_coupled_standard_capacitor_land_update"]]
    names = ["TDK_VLS5045EX_Reflow", "Murata_GRM21_22uF_Reflow",
             "Murata_BLM18SG121_WideCopper", "Murata_GRM21_10uF_Reflow"]
    specs = {ref: (name, group) for name, group in zip(names, groups, strict=True) for ref in group["references"]}
    assert set(specs) == {"L1", "C26", "C27", "C28", "FB1", "FB2", "C1", "C4", "C5", "C19", "C20"}
    text, tree = load(PACKAGE / "handbell.kicad_pcb")
    edits, details = [], {}
    for fp in tree.children("footprint"):
        ref = fp.properties().get("Reference")
        if ref not in specs:
            continue
        name, spec = specs[ref]
        mpn = spec.get("mpn") or spec["unchanged_selected_mpn"]
        assert fp.properties()["MPN"] == mpn
        pads = fp.children("pad")
        assert len(pads) == 2 and fp.child("attr") is None
        edits.append((fp.items[1].start, fp.items[1].end, json.dumps("Handbell:" + name)))
        additions = "\n(attr smd)\n"
        pad_changes = []
        for pad in pads:
            at, size = pad.child("at"), pad.child("size")
            x, y = map(float, at.atoms()[1:3])
            assert y == 0 and (len(at.atoms()) == 3 or float(at.atoms()[3]) == 0)
            assert pad.atoms()[2:] == ["smd", "rect"]
            new_x = spec["new_copper_pad_centers_local_x_mm"][0 if x < 0 else 1]
            sx, sy = spec["new_copper_pad_size_mm"]
            edits += [(at.start, at.end, f"(at {new_x} 0)"),
                      (size.start, size.end, f"(size {sx} {sy})")]
            if spec.get("remove_automatic_pad_mask_and_paste"):
                layers = pad.child("layers")
                edits.append((layers.start, layers.end, '(layers "F.Cu")'))
                edits += [(n.start, n.end, "") for n in pad.children()
                          if n.head in ("solder_mask_margin", "solder_paste_margin")]
                wx, wy = spec["explicit_mask_and_paste_window_size_mm"]
                for layer in ("F.Mask", "F.Paste"):
                    uid = uuid.uuid5(uuid.NAMESPACE_URL, f"digital-handbell/{ref}/{pad.atoms()[1]}/{layer}/window")
                    additions += (
                        f'(fp_rect (start {new_x-wx/2:.6f} {-wy/2:.6f}) '
                        f'(end {new_x+wx/2:.6f} {wy/2:.6f}) '
                        f'(stroke (width 0) (type solid)) (fill solid) (layer "{layer}") (uuid "{uid}"))\n')
            pad_changes.append({"number": pad.atoms()[1], "uuid": pad.value("uuid"),
                                "old_at": at.atoms()[1:], "new_local_xy_mm": [new_x, 0],
                                "old_size_mm": list(map(float, size.atoms()[1:])),
                                "new_size_mm": [sx, sy], "net": pad.value("net")})
        edits.append((fp.end - 1, fp.end - 1, additions))
        details[ref] = {"old_footprint": fp.atoms()[1], "new_footprint": "Handbell:" + name,
                        "pads": pad_changes, "unchanged_native_pose": fp.child("at").atoms()[1:]}
    assert details.keys() == specs.keys()
    for zone in tree.children("zone"):
        edits += [(p.start, p.end, "") for p in zone.children("filled_polygon")]
    pcb_text = apply_edits(text, edits)
    modules = {}
    for fp in loads(pcb_text).children("footprint"):
        ref = fp.properties().get("Reference")
        if ref in specs:
            name = specs[ref][0]
            if name not in modules:
                modules[name] = library_from_instance(pcb_text, fp, name)
    sch_text, sch = load(PACKAGE / "handbell.kicad_sch")
    changes = []
    for symbol in sch.children("symbol"):
        ref = symbol.properties().get("Reference")
        if ref in specs:
            assert symbol.properties()["Footprint"] == details[ref]["old_footprint"]
            changes += prop_edits(symbol, {"Footprint": details[ref]["new_footprint"]})
    sch_text = apply_edits(sch_text, changes)
    manifest = json.loads((PACKAGE / "placement-manifest.json").read_text(encoding="utf-8"))
    assert manifest["generated_pcb_sha256"] == BASE and manifest["schematic_sha256"] == sha(PACKAGE / "handbell.kicad_sch")
    for component in manifest["components"]:
        if component["reference"] in details:
            component["footprint"] = details[component["reference"]]["new_footprint"]
    shutil.copytree(PACKAGE, output, ignore=shutil.ignore_patterns(
        "reports", "input-checkpoint", "*.kicad_prl", "*.lck", "*-backups"))
    for name, contents in (("handbell.kicad_pcb", pcb_text), ("handbell.kicad_sch", sch_text)):
        (output / name).write_bytes(contents.encode("utf-8"))
    for name, contents in modules.items():
        (output / "libraries" / "Handbell.pretty" / (name + ".kicad_mod")).write_bytes(contents.encode("utf-8"))
    manifest.update(generated_pcb_sha256=sha(output / "handbell.kicad_pcb"),
                    schematic_sha256=sha(output / "handbell.kicad_sch"),
                    current_stage_report="reports/power-lands.json", mechanical_rebind_required=True)
    (output / "placement-manifest.json").write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    (output / "reports").mkdir()
    report = {
        "status": "STAGED_NOT_ACCEPTED", "input_pcb_sha256": BASE,
        "register_sha256": sha(register_path), "generator_sha256": sha(Path(__file__)),
        "output_pcb_sha256": sha(output / "handbell.kicad_pcb"),
        "output_schematic_sha256": sha(output / "handbell.kicad_sch"),
        "changes": details, "component_moves": [], "copper_primitive_changes": [],
        "ground_fill_invalidated": True,
        "remaining": "Native geometry/library/mask/paste, continuity, quiet pickoffs, uncovered current paths, refill and manufacturing review required.",
    }
    (output / "reports" / "power-lands.json").write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"status": report["status"], "references": sorted(details), "pcb_sha256": report["output_pcb_sha256"]}))


if __name__ == "__main__":
    main()
