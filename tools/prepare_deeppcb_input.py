# SPDX-License-Identifier: MIT
"""Prepare an isolated routing-service input from the authoritative four-layer board.

The authoritative files are copied, never edited. The routing copy adds the
reviewed battery-contact metal guards as B.Cu keep-outs and tightens net classes
and edge clearance so an external router cannot use weaker defaults.
"""
import argparse
import hashlib
import json
import re
import shutil
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE_DIR = REPO / "hardware" / "handbell" / "iterations" / "printed-bell-four-layer"
SOURCE_HASHES = {
    "handbell.kicad_pcb": "adc262b3e7056cb9031387c55262b5cf99e599ae6e28970f9784f5237e662314",
    "handbell.kicad_pro": "8213261803c4a032c6351311ed43db6249720a8cb334ebd15e3daca210899990",
    "handbell.kicad_sch": "ec93cc6f6f03bb91dd05199d2e0b4cab6b542567031e484fe8098056992ab69e",
}
MASK = REPO / "docs" / "measurements" / "2026-09-27-router-bakeoff" / "quilter-contact-via-mask-2026-10-03.json"
MASK_SHA256 = "489503349d1f05968ea165237a99bbd01e4381983b1f40273a9ab98fdef17fda"
NAMESPACE = uuid.UUID("0d6f1f0e-5b7c-4c1e-9a43-2e0c8d2f6a11")
EDGE_CLEARANCE_MM = 0.3
NET_CLASSES = {
    "Default": {"track_width": 0.2, "clearance": 0.2, "via_diameter": 0.6, "via_drill": 0.3},
    "power": {"track_width": 0.3, "clearance": 0.2, "via_diameter": 0.6, "via_drill": 0.3},
}
POWER_NETS = ["VBUS", "VBAT", "VHI", "VAMP"]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def guard_zones(mask):
    areas = mask["domains"]["native_via_only_rule_areas_expanded_each_edge_0_25_mm"]
    if len(areas) != 8 or len({a["name"] for a in areas}) != 8:
        raise ValueError("Expected eight reviewed contact guards")
    zones = []
    for area in areas:
        # Mask coordinates are common-origin; board coordinates are offset +100/+100.
        x0, x1 = area["x_min_mm"] + 100, area["x_max_mm"] + 100
        y0, y1 = area["y_min_mm"] + 100, area["y_max_mm"] + 100
        if not (x0 < x1 and y0 < y1):
            raise ValueError(f"Invalid guard {area['name']}")
        zid = uuid.uuid5(NAMESPACE, area["name"])
        zones.append(
            f'(zone (layer "B.Cu") (uuid "{zid}") '
            f'(name "CONTACT_METAL_GUARD_{area["name"]}") '
            f'(hatch edge 0.5) (connect_pads (clearance 0)) (min_thickness 0.25) '
            f'(keepout (tracks not_allowed) (vias not_allowed) (pads allowed) '
            f'(copperpour not_allowed) (footprints allowed)) '
            f'(polygon (pts (xy {x0:.6f} {y0:.6f}) (xy {x1:.6f} {y0:.6f}) '
            f'(xy {x1:.6f} {y1:.6f}) (xy {x0:.6f} {y1:.6f}))))'
        )
    return zones


def tighten_project(project):
    settings = project["net_settings"]
    by_name = {c["name"]: c for c in settings["classes"]}
    for name, values in NET_CLASSES.items():
        by_name[name].update(values)
    patterns = [p for p in settings.get("netclass_patterns") or []
                if p["pattern"] not in ("GND", "N$10") and p["netclass"] != "power"]
    patterns += [{"netclass": "power", "pattern": net} for net in POWER_NETS]
    settings["netclass_patterns"] = patterns
    project["board"]["design_settings"]["rules"]["min_copper_edge_clearance"] = EDGE_CLEARANCE_MM
    project["board"]["design_settings"]["rules"]["min_clearance"] = 0.2
    return project


def tighten_board(text):
    """Restrict In1 to plane use and stop new copper in private-return guards."""
    text = text.replace('(4 "In1.Cu" signal)', '(4 "In1.Cu" power)', 1)
    if '(4 "In1.Cu" power)' not in text:
        raise SystemExit("Could not mark In1.Cu as a power plane")
    count = 0
    pattern = re.compile(r"\(keepout\s*\(tracks allowed\)\s*\(vias allowed\)\s*\(pads allowed\)"
                         r"\s*\(copperpour not_allowed\)\s*\(footprints allowed\)\s*\)")
    new = ("(keepout (tracks not_allowed) (vias not_allowed) (pads allowed) "
           "(copperpour not_allowed) (footprints allowed))")
    for marker in ('(name "private-', '(name "in1-private/'):
        start = 0
        while (i := text.find(marker, start)) >= 0:
            match = pattern.search(text, i)
            if not match or match.start() - i > 400:
                raise SystemExit("Unexpected private guard flags")
            text = text[:match.start()] + new + text[match.end():]
            count += 1
            start = match.start() + len(new)
    if count != 12:
        raise SystemExit(f"Expected 12 private guards, found {count}")
    zid = uuid.uuid5(NAMESPACE, "in1-no-tracks")
    in1 = (f'(zone (layer "In1.Cu") (uuid "{zid}") (name "IN1_PLANE_NO_TRACKS") '
           f'(hatch edge 0.5) (connect_pads (clearance 0)) (min_thickness 0.25) '
           f'(keepout (tracks not_allowed) (vias allowed) (pads allowed) '
           f'(copperpour allowed) (footprints allowed)) '
           f'(polygon (pts (xy 70 65) (xy 130 65) (xy 130 130) (xy 70 130))))')
    return text, count, in1


TRIAL_REMOVED_REFS = ("TP12", "TP13", "TP14", "TP15")


def remove_footprints(text, refs):
    """Remove whole footprint blocks for a free-trial probe copy only."""
    removed = []
    for ref in refs:
        marker = f'(property "Reference" "{ref}"'
        i = text.find(marker)
        if i < 0:
            raise SystemExit(f"{ref} not found")
        start = text.rfind("(footprint ", 0, i)
        depth = 0
        for end in range(start, len(text)):
            if text[end] == "(":
                depth += 1
            elif text[end] == ")":
                depth -= 1
                if depth == 0:
                    break
        text = text[:start] + text[end + 1:]
        removed.append(ref)
    return text, removed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workdir", type=Path)
    args = parser.parse_args()
    if sha256(MASK) != MASK_SHA256:
        raise SystemExit("Contact mask hash mismatch")
    base, routed_input = args.workdir / "base", args.workdir / "input"
    for folder in (base, routed_input):
        folder.mkdir(parents=True, exist_ok=True)
    for name, expected in SOURCE_HASHES.items():
        if sha256(SOURCE_DIR / name) != expected:
            raise SystemExit(f"Authoritative {name} hash mismatch")
        shutil.copy2(SOURCE_DIR / name, base / name)
        shutil.copy2(SOURCE_DIR / name, routed_input / name)

    pcb_path = routed_input / "handbell.kicad_pcb"
    text = pcb_path.read_text(encoding="utf-8")
    if "CONTACT_METAL_GUARD_" in text:
        raise SystemExit("Source unexpectedly already contains contact guards")
    end = text.rstrip().rfind(")")
    zones = guard_zones(json.loads(MASK.read_text(encoding="utf-8")))
    text, private_guards, in1_zone = tighten_board(text[:end])
    text = text + "\n" + "\n".join(zones + [in1_zone]) + "\n)\n"
    pcb_path.write_text(text, encoding="utf-8", newline="")

    pro_path = routed_input / "handbell.kicad_pro"
    project = tighten_project(json.loads(pro_path.read_text(encoding="utf-8")))
    pro_path.write_text(json.dumps(project, indent=2) + "\n", encoding="utf-8")

    probe = args.workdir / "trial-probe"
    probe.mkdir(exist_ok=True)
    probe_text, removed = remove_footprints(text, TRIAL_REMOVED_REFS)
    (probe / "handbell.kicad_pcb").write_text(probe_text, encoding="utf-8", newline="")
    shutil.copy2(pro_path, probe / "handbell.kicad_pro")
    shutil.copy2(routed_input / "handbell.kicad_sch", probe / "handbell.kicad_sch")

    manifest = {
        "source_hashes": SOURCE_HASHES,
        "contact_mask_sha256": MASK_SHA256,
        "added_contact_guards": len(zones),
        "private_guards_blocking_tracks_and_vias": private_guards,
        "in1": "power-plane layer type plus whole-board track keep-out (vias allowed)",
        "net_classes": NET_CLASSES,
        "power_nets": POWER_NETS,
        "min_copper_edge_clearance_mm": EDGE_CLEARANCE_MM,
        "input_hashes": {p.name: sha256(p) for p in sorted(routed_input.iterdir()) if p.is_file()},
        "trial_probe_removed_refs": removed,
        "trial_probe_hashes": {p.name: sha256(p) for p in sorted(probe.iterdir()) if p.is_file()},
    }
    (args.workdir / "input-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
