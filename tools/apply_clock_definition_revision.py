# SPDX-License-Identifier: MIT
"""Create an isolated clock-definition draft; never route or overwrite a draft."""
import hashlib
import json
import math
from pathlib import Path
import shutil
import uuid

from kicad_sexpr import apply_edits, loads

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "hardware" / "handbell" / "iterations" / "printed-bell-clock-draft"
RECOVERED = HERE.parent / "printed-bell-quote-candidate"
FROZEN = HERE.parent / "printed-bell-power-rework"
PINNED = {
    "handbell.kicad_pcb": "2d88301f48ad05dc01384b90111f16615f176a7f4704eab82a1e3560ef5c8bc0",
    "handbell.kicad_sch": "e131a8d093795df7285bcae4a8886ffe01106c6513a19bd588ee7c29c6993b4f",
    "placement-manifest.json": "404a8c53dc0ce28f8769ec4a1926452564cbd3cd5f8c27d95b7ac2ebee1b55de",
}
NAMES = {"Y1": "ABM8_272_T3", "C2": "GRM1555C1H150JA01D", "C3": "GRM1555C1H150JA01D"}
MPNS = {"Y1": "ABM8-272-T3", "C2": "GRM1555C1H150JA01D", "C3": "GRM1555C1H150JA01D"}
CLOCK_NETS = {"Net-(IC1-XIN)", "Net-(IC1-XOUT)", "Net-(C3-Pad2)"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "digital-handbell/clock-definition/" + name))


def prop_edits(node, values):
    return [(p.items[2].start, p.items[2].end, json.dumps(values[p.atoms()[1]]))
            for p in node.children("property") if p.atoms()[1] in values]


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def metadata(reference, schematic=False):
    layer = "" if schematic else '(layer "F.Fab")'
    return "".join(f'\n(property "{key}" "{value}" (at 0 0 0) {layer} (hide yes) '
                   '(effects (font (size 1 1))))'
                   for key, value in (("MPN", MPNS[reference]),
                                      ("Manufacturer", "Abracon" if reference == "Y1" else "Murata")))


def main():
    if (HERE / "handbell.kicad_pcb").exists():
        raise ValueError("Existing draft refused; preserve edits and use a separate next step")
    source = HERE / "input-checkpoint"
    source.mkdir(parents=True, exist_ok=True)
    for name, digest in PINNED.items():
        if not (source / name).exists():
            if sha(RECOVERED / name) != digest:
                raise ValueError("Recovered input changed: " + name)
            shutil.copyfile(RECOVERED / name, source / name)
        if sha(source / name) != digest:
            raise ValueError("Pinned checkpoint changed: " + name)
    for name in ("handbell.kicad_pro", "battery-contact-interface.json", "fp-lib-table",
                 "sym-lib-table", "Handbell.kicad_sym", "T8.kicad_sym", "LICENSE.txt"):
        shutil.copyfile(FROZEN / name, HERE / name)
    for folder in ("libraries", "notices"):
        shutil.copytree(FROZEN / folder, HERE / folder, dirs_exist_ok=True)

    manifest = json.loads((source / "placement-manifest.json").read_text(encoding="utf-8-sig"))
    crystal = next(c for c in manifest["components"] if c["reference"] == "Y1")
    crystal["width_mm"], crystal["depth_mm"] = 3.6, 2.8
    gaps = []
    def bounds(c):
        angle = math.radians(c["rotation_deg"])
        w = abs(c["width_mm"] * math.cos(angle)) + abs(c["depth_mm"] * math.sin(angle))
        d = abs(c["width_mm"] * math.sin(angle)) + abs(c["depth_mm"] * math.cos(angle))
        return c["x_mm"] - w/2, c["x_mm"] + w/2, c["y_mm"] - d/2, c["y_mm"] + d/2
    a = bounds(crystal)
    for c in manifest["components"]:
        if c["side"] != "F" or c["reference"] == "Y1":
            continue
        b = bounds(c)
        dx, dy = max(a[0]-b[1], b[0]-a[1], 0), max(a[2]-b[3], b[2]-a[3], 0)
        if dx == 0 and dy == 0:
            raise ValueError("New Y1 screening envelope overlaps " + c["reference"])
        gaps.append({"reference": c["reference"], "screen_gap_mm": math.hypot(dx, dy)})
    if any(math.hypot(x, y) >= 21.5 for x in a[:2] for y in a[2:]):
        raise ValueError("Clock envelope leaves D43")

    text = (source / "handbell.kicad_pcb").read_text(encoding="utf-8-sig")
    board = loads(text)
    edits, removed = [], []
    for fp in board.children("footprint"):
        ref = fp.properties().get("Reference")
        if ref not in NAMES:
            continue
        block = text[fp.start:fp.end]
        f = loads(block)
        changes = [(f.items[1].start, f.items[1].end, json.dumps("Clock:" + NAMES[ref]))]
        changes += prop_edits(f, {"Value": "12MHz/CL10pF" if ref == "Y1" else "15pF"})
        changes.append((f.end-1, f.end-1, metadata(ref)))
        for pad in f.children("pad"):
            number = pad.atoms()[1]
            x, y = ((-1.15 if number in ("1", "4") else 1.15),
                    (.875 if number in ("1", "2") else -.875)) if ref == "Y1" else (
                        -.4 if number == "1" else .4, 0)
            for key, replacement in (("at", f"(at {x} {y})"),
                                     ("size", "(size 1.3 1.05)" if ref == "Y1" else "(size .4 .5)")):
                n = pad.child(key)
                changes.append((n.start, n.end, replacement))
            if ref == "Y1" and number in ("2", "4"):
                changes.append((pad.end-1, pad.end-1, '\n(net "GND") (pintype "passive") (pinfunction "CASE")'))
        if ref == "Y1":
            changes += [(n.start, n.end, "") for n in f.children("fp_line")]
            changes.append((f.end-1, f.end-1,
                            '\n(fp_rect (start -1.6 -1.25) (end 1.6 1.25) '
                            '(stroke (width .1) (type solid)) (fill none) (layer "F.Fab"))'))
        changed = apply_edits(block, changes)
        edits.append((fp.start, fp.end, changed))
        module = loads(changed)
        module_edits = [(module.items[1].start, module.items[1].end, json.dumps(NAMES[ref]))]
        module_edits += prop_edits(module, {"Reference": "REF**"})
        module_edits += [(n.start, n.end, "") for n in module.children()
                         if n.head in ("at", "uuid", "path")]
        for pad in module.children("pad"):
            module_edits += [(n.start, n.end, "") for n in pad.children()
                             if n.head in ("net", "pintype", "pinfunction")]
        write(HERE / "libraries" / "Clock.pretty" / (NAMES[ref] + ".kicad_mod"),
              apply_edits(changed, module_edits))
    for kind in ("segment", "via"):
        for n in board.children(kind):
            if n.value("net") in CLOCK_NETS:
                removed.append({"kind": kind, "uuid": n.value("uuid"), "net": n.value("net")})
                edits.append((n.start, n.end, ""))
    for zone in board.children("zone"):
        edits += [(n.start, n.end, "") for n in zone.children("filled_polygon")]
    pcb = apply_edits(text, edits)

    text = (source / "handbell.kicad_sch").read_text(encoding="utf-8-sig")
    schematic = loads(text)
    old = next(s for s in schematic.child("lib_symbols").children("symbol")
               if s.atoms()[1] == "Handbell:CRYSTAL2.5X2.0")
    symbol = text[old.start:old.end].replace("Handbell:CRYSTAL2.5X2.0", "Clock:ABM8_272_T3").replace(
        "CRYSTAL2.5X2.0_", "ABM8_272_T3_")
    sym = loads(symbol)
    changes = prop_edits(sym, {"Footprint": "Clock:ABM8_272_T3",
                              "Description": "12MHz CL10pF ABM8-272-T3; pins2/4 case ground."})
    body = next(n for n in sym.children("symbol") if n.children("pin"))
    pins = "".join(f'\n(pin passive line (at {x} -3.81 90) (length 1.27) '
                   f'(name "CASE" (effects (font (size .8 .8)))) '
                   f'(number "{number}" (effects (font (size .8 .8)))))'
                   for number, x in (("2", -1.27), ("4", 1.27)))
    changes.append((body.end-1, body.end-1, pins))
    symbol = apply_edits(symbol, changes)
    write(HERE / "Clock.kicad_sym", '(kicad_symbol_lib (version 20250114) (generator "handbell")\n' +
          symbol.replace('"Clock:ABM8_272_T3"', '"ABM8_272_T3"', 1) + '\n)')
    edits = [(schematic.child("lib_symbols").end-1, schematic.child("lib_symbols").end-1, "\n" + symbol)]
    for instance in schematic.children("symbol"):
        ref = instance.properties().get("Reference")
        if ref not in NAMES:
            continue
        edits += prop_edits(instance, {"Value": "12MHz/CL10pF" if ref == "Y1" else "15pF",
                                      "Footprint": "Clock:" + NAMES[ref]})
        edits.append((instance.end-1, instance.end-1, metadata(ref, True)))
        if ref == "Y1":
            n = instance.child("lib_id")
            edits.append((n.start, n.end, '(lib_id "Clock:ABM8_272_T3")'))
            edits.append((instance.end-1, instance.end-1, "".join(
                f'\n(pin "{number}" (uuid "{uid("pin"+number)}"))' for number in ("2", "4"))))
    labels = "".join(f'\n(global_label "GND" (shape input) (at 49.53 {y} 0) '
                     '(effects (font (size .8 .8)) (justify left)) '
                     f'(uuid "{uid("label"+str(y))}"))' for y in (186.69, 184.15))
    edits.append((schematic.end-1, schematic.end-1, labels))
    sch = apply_edits(text, edits)
    for filename, addition in (
        ("fp-lib-table", '(lib (name "Clock") (type "KiCad") (uri "${KIPRJMOD}/libraries/Clock.pretty") (options "") (descr "Clock reference lands"))'),
        ("sym-lib-table", '(lib (name "Clock") (type "KiCad") (uri "${KIPRJMOD}/Clock.kicad_sym") (options "") (descr "Four-terminal clock reference"))')):
        original = (HERE / filename).read_text(encoding="utf-8-sig")
        node = loads(original)
        write(HERE / filename, apply_edits(original, [(node.end-1, node.end-1, "\n" + addition)]))
    write(HERE / "handbell.kicad_pcb", pcb)
    write(HERE / "handbell.kicad_sch", sch)
    for c in manifest["components"]:
        if c["reference"] in NAMES:
            ref = c["reference"]
            c.update(mpn=MPNS[ref], value="12MHz/CL10pF" if ref == "Y1" else "15pF",
                     footprint="Clock:" + NAMES[ref])
    manifest.update(generated_pcb_sha256=sha(HERE / "handbell.kicad_pcb"),
                    schematic_sha256=sha(HERE / "handbell.kicad_sch"),
                    status="CLOCK_DEFINITIONS_ONLY_ROUTING_AND_ZONE_REFILL_PENDING")
    write(HERE / "placement-manifest.json", json.dumps(manifest, indent=2) + "\n")
    report = {"status": manifest["status"], "input_sha256": PINNED,
              "output_pcb_sha256": manifest["generated_pcb_sha256"],
              "output_schematic_sha256": manifest["schematic_sha256"],
              "changed_references": ["Y1", "C2", "C3"], "moved_references": [],
              "new_tracks": 0, "removed_clock_copper": removed,
              "cached_zone_fills_cleared": True,
              "nearest_screen_gaps": sorted(gaps, key=lambda g: g["screen_gap_mm"])[:6],
              "scope": "Nominal 2D proxy screen only, not full mechanical/assembly qualification"}
    write(HERE / "reports" / "clock-definition.json", json.dumps(report, indent=2) + "\n")
    write(HERE / ".gitattributes", "* -text\n")
    print(json.dumps({k: v for k, v in report.items() if k != "removed_clock_copper"}, indent=2))


if __name__ == "__main__":
    main()
