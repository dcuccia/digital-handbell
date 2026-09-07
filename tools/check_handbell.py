# SPDX-License-Identifier: MIT
"""Check schematic connectivity and SOX pad mapping; not a hardware signoff."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from kicad_sexpr import load

ROOT = Path(__file__).resolve().parents[1]
HARDWARE = ROOT / "hardware"
DRAFT = HARDWARE / "handbell"
BASE = HARDWARE / "reference" / "adafruit-5768"
SOX = HARDWARE / "reference" / "adafruit-4438"
BASE_STEM = "Adafruit Feather RP2040 Prop-Maker"
ALIASES = {"CHG": "CHG0", "CHG_EN": "CHG_EN0", "GAIN": "GAIN0",
           "L": "L0", "OUTPUTS": "OUTPUTS0", "SERVO": "SERVO0"}
ADDED = {"C23", "C24", "TP4", "TP5", "TP6"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nets(tree):
    return {n.get("name"): frozenset((p.get("ref"), p.get("pin")) for p in n.findall("node"))
            for n in tree.findall("nets/net")}


def projected(groups, omit):
    return {remaining for members in groups.values()
            if (remaining := frozenset(p for p in members if p[0] not in omit))}


def check_import(board, imported, aliases):
    source = ET.parse(board).getroot()
    expected = {
        frozenset((aliases.get(p.get("element"), p.get("element")), p.get("pad"))
                  for p in signal.findall("contactref"))
        for signal in source.findall("drawing/board/signals/signal")
        if signal.findall("contactref")
    }
    actual = {group for name, group in nets(imported).items()
              if group and not name.startswith("unconnected-")}
    require(expected == actual,
            f"{board.name}: source/native connected-net mismatch: missing={expected-actual}, extra={actual-expected}")
    return len(expected)


def check_footprint():
    source = ET.parse(SOX / "upstream" / "Adafruit_LSM6DSOX.sch").getroot()
    packages = source.findall("drawing/schematic/libraries/library/packages/package")
    package = next(p for p in packages if p.get("name") == "LGA-14L")
    _, fp = load(SOX / "kicad" / "Adafruit_LSM6DSOX-import-fps.pretty" / "LGA-14L.kicad_mod")
    pads = {p.atoms()[1]: p for p in fp.children("pad")}
    require(set(pads) == {str(p) for p in range(1, 15)}, "Expected exactly physical pads 1..14.")
    details = []
    for smd in package.findall("smd"):
        number = smd.get("name")
        pad = pads[number]
        at = list(map(float, pad.child("at").atoms()[1:]))
        size = list(map(float, pad.child("size").atoms()[1:]))
        expected = [float(smd.get("x")), -float(smd.get("y"))]
        require(all(math.isclose(a, b, abs_tol=1e-6) for a, b in zip(at[:2], expected)),
                f"Pad {number}: position differs from EAGLE.")
        require(all(math.isclose(a, b, abs_tol=1e-6)
                    for a, b in zip(size, [float(smd.get("dx")), float(smd.get("dy"))])),
                f"Pad {number}: size differs from EAGLE.")
        angle = at[2] if len(at) == 3 else 0
        eagle_angle = float(smd.get("rot", "R0").removeprefix("R"))
        require(math.isclose(angle % 180, eagle_angle % 180, abs_tol=1e-6),
                f"Pad {number}: rectangular-pad axis differs from EAGLE.")
        require(pad.atoms()[2] == "smd", f"Pad {number} must be surface-mount.")
        require(set(pad.child("layers").atoms()[1:]) == {"F.Cu", "F.Paste", "F.Mask"},
                f"Pad {number}: unexpected copper/paste/mask layers.")
        details.append({"pad": number, "position_mm": at[:2], "size_mm": size, "rotation_deg": angle})
    require(len(details) == 14, "Source package did not define exactly 14 SMD lands.")
    return details


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kicad-cli", default="kicad-cli")
    args = parser.parse_args()
    paths = {
        "baseline": BASE / "kicad" / f"{BASE_STEM}.kicad_sch",
        "sox": SOX / "kicad" / "Adafruit_LSM6DSOX.kicad_sch",
        "handbell": DRAFT / "handbell.kicad_sch",
    }
    with tempfile.TemporaryDirectory(prefix="handbell-check-") as directory:
        trees = {}
        for name, schematic in paths.items():
            output = Path(directory) / f"{name}.xml"
            subprocess.run([args.kicad_cli, "sch", "export", "netlist", "--format", "kicadxml",
                            "--output", str(output), str(schematic)], check=True)
            trees[name] = ET.parse(output).getroot()
        erc_path = Path(directory) / "erc.json"
        subprocess.run([args.kicad_cli, "sch", "erc", "--exit-code-violations", "--format", "json",
                        "--output", str(erc_path), str(paths["handbell"])], check=True)
        erc = json.loads(erc_path.read_text())

    import_counts = {
        "adafruit_5768": check_import(BASE / "upstream" / f"{BASE_STEM}.brd", trees["baseline"], ALIASES),
        "adafruit_4438": check_import(SOX / "upstream" / "Adafruit_LSM6DSOX.brd", trees["sox"], {}),
    }
    base_nets, draft_nets = nets(trees["baseline"]), nets(trees["handbell"])
    baseline_projection = projected(base_nets, {"IC4"})
    draft_projection = projected(draft_nets, {"IC4"} | ADDED)
    require(baseline_projection == draft_projection,
            f"Retained connections changed: missing={baseline_projection-draft_projection}, extra={draft_projection-baseline_projection}")
    baseline_components = {c.get("ref"): c for c in trees["baseline"].findall("components/comp")}
    draft_components = {c.get("ref"): c for c in trees["handbell"].findall("components/comp")}
    require(set(draft_components) == set(baseline_components) | ADDED, "Unexpected added/removed components.")
    for ref, component in baseline_components.items():
        if ref == "IC4":
            continue
        for field in ["value", "footprint"]:
            require(component.findtext(field) == draft_components[ref].findtext(field),
                    f"Retained {ref} {field} changed.")

    pin_nets = {pin: name for name, members in draft_nets.items() for pin in members}
    expected_sensor = {"1": "GND", "2": "GND", "3": "GND", "4": "INT", "5": "+3V3",
                       "6": "GND", "7": "GND", "8": "+3V3", "9": "/IMU_INT2",
                       "12": "+3V3", "13": "SCL", "14": "SDA"}
    for pin, net in expected_sensor.items():
        require(pin_nets.get(("IC4", pin)) == net, f"IC4 pad {pin} must connect to {net}.")
    for pin in ["10", "11"]:
        name = pin_nets[("IC4", pin)]
        require(name.startswith("unconnected-") and draft_nets[name] == {("IC4", pin)},
                f"IC4 auxiliary pad {pin} must be explicitly unconnected.")
    require({p for r, p in pin_nets if r == "IC4"} == {str(i) for i in range(1, 15)}, "Sensor pin set is not 1..14.")
    for ref, pin, net in [
        ("IC1", "4", "SDA"), ("IC1", "5", "SCL"), ("IC1", "34", "INT"),
        ("IC1", "27", "I2S_DIN"), ("IC1", "28", "I2S_BCLK"), ("IC1", "29", "I2S_LRCLK"),
        ("IC1", "35", "POWER"), ("TP4", "P$1", "SWCLK"), ("TP5", "P$1", "SWDIO"),
        ("IC1", "45", "VCORE"),
        ("TP6", "P$1", "/IMU_INT2"), ("R14", "2", "SCL"), ("R15", "2", "SDA"),
    ]:
        require(pin_nets.get((ref, pin)) == net, f"{ref}.{pin} must connect to {net}.")
    for ref in ["C23", "C24"]:
        require(pin_nets[(ref, "1")] == "+3V3" and pin_nets[(ref, "2")] == "GND", f"{ref} bypass rail mismatch.")
        require(draft_components[ref].findtext("value") == "0.1uF", f"{ref} must be 100 nF.")
    require(draft_components["IC4"].findtext("value") == "LSM6DSOXTR", "Incorrect sensor ordering code.")
    require(draft_components["IC4"].findtext("footprint") == "Adafruit_LSM6DSOX-import-fps:LGA-14L",
            "Sensor must use the reviewed imported footprint.")
    pads = check_footprint()
    base_project = json.loads(paths["baseline"].with_suffix(".kicad_pro").read_text())
    draft_project = json.loads(paths["handbell"].with_suffix(".kicad_pro").read_text())
    require(base_project["erc"] == draft_project["erc"], "ERC severity/pin matrix/exclusions changed.")
    require(not draft_project["erc"]["erc_exclusions"], "ERC exclusions must remain empty.")
    require(all(not s["violations"] for s in erc["sheets"]), "ERC violations remain.")
    published = ET.parse(DRAFT / "reports" / "handbell-netlist.xml").getroot()
    require(nets(published) == draft_nets, "Published netlist is stale; regenerate exports.")

    report = {
        "kicad_version": erc["kicad_version"],
        "scope": "Net topology, preserved component values/footprints, sensor pads, GPIO contract and ERC; not layout/function/safety approval.",
        "hash_normalization": "Review hashes use UTF-8 text with CRLF/CR normalized to LF; upstream source-byte hashes are recorded separately.",
        "source_schematic_sha256_lf": {
            name: hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
            for name, path in paths.items()
        },
        "source_connected_groups_matching_native": import_counts,
        "retained_components": len(baseline_components)-1,
        "retained_connection_groups": len(baseline_projection),
        "added_components_or_copper_features": sorted(ADDED),
        "sensor_pin_nets": {str(i): pin_nets[("IC4", str(i))] for i in range(1, 15)},
        "sensor_footprint_pads": pads,
        "erc_configuration_unchanged": True,
        "erc_exclusions": [],
        "erc_errors": 0,
        "erc_warnings": 0,
    }
    (DRAFT / "reports" / "connectivity-review.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    with (DRAFT / "reports" / "bom-draft.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["Reference", "Value", "Footprint", "MPN", "Review status"])
        for ref in sorted(draft_components):
            c = draft_components[ref]
            status = "Inherited reference; exact MPN, assembly SKU and fit review pending"
            if ref in {"TP4", "TP5", "TP6"}:
                status = "PCB copper test pad; no fitted component"
            elif ref in {"C23", "C24"}:
                status = "100 nF local IMU bypass; dielectric, voltage, tolerance and MPN pending"
            elif ref == "IC4":
                status = "Owner-approved sensor; footprint mapping reviewed, assembly quote pending"
            writer.writerow([ref, c.findtext("value"), c.findtext("footprint"),
                             "LSM6DSOXTR" if ref == "IC4" else "", status])
    print(f"PASS: source groups {import_counts}; {len(baseline_components)-1} retained components; "
          f"{len(baseline_projection)} retained net groups; all 14 sensor pads; ERC 0 errors / 0 warnings.")


if __name__ == "__main__":
    main()
