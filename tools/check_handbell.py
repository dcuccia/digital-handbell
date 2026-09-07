# SPDX-License-Identifier: MIT
"""Check schematic connectivity and SOX pad mapping; not a hardware signoff."""
import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from kicad_sexpr import load, pcb_net_name

ROOT = Path(__file__).resolve().parents[1]
HARDWARE = ROOT / "hardware"
DRAFT = HARDWARE / "handbell"
BASE = HARDWARE / "reference" / "adafruit-5768"
SOX = HARDWARE / "reference" / "adafruit-4438"
BOOST = HARDWARE / "reference" / "adafruit-4654"
BASE_STEM = "Adafruit Feather RP2040 Prop-Maker"
ALIASES = {"CHG": "CHG0", "CHG_EN": "CHG_EN0", "GAIN": "GAIN0",
           "L": "L0", "OUTPUTS": "OUTPUTS0", "SERVO": "SERVO0"}
REMOVED = {"JP1", "JP3", "SERVO0", "OUTPUTS0", "LED1", "IC2", "R19", "CONN1",
           "SW1", "SW2", "U$31", "U$32", "U$34", "U$35"}
ADDED = {"C23", "C24", "C25", "C26", "C27", "C28", "C29", "U5", "L1", "Q4",
         "R20", "R21", "R22", "R23", "R24", "J1", "J2"} | {f"TP{i}" for i in range(4, 17)}
AMP_MOVED = {("C16", "1"), ("C19", "1"), ("GAIN0", "3"), ("R18", "2"), ("U4", "7"), ("U4", "8")}
CHANGED_FOOTPRINTS = {
    "Q3": "Handbell:DFN2015-3_DrainPad",
    "CHG_EN0": "Jumper:SolderJumper-2_P1.3mm_Bridged_Pad1.0x1.5mm",
    "GAIN0": "Jumper:SolderJumper-3_P1.3mm_Open_Pad1.0x1.5mm",
}
NEW_PIN_NETS = {
    "U5": {"1": "BOOST_FB", "2": "POWER", "3": "V+", "4": "GND", "5": "BOOST_SW", "6": "VAMP"},
    "L1": {"P$1": "V+", "P$2": "BOOST_SW"},
    "Q4": {"1": "AMP_MUTE", "2": "GND", "3": "I2S_MOD"},
    "R20": {"1": "+3V3", "2": "AMP_MUTE"},
    "R21": {"1": "+3V3", "2": "BUTTON"},
    "R22": {"1": "BUTTON", "2": "BUTTON_EXT"},
    "R23": {"1": "VAMP", "2": "BOOST_FB"},
    "R24": {"1": "BOOST_FB", "2": "GND"},
    "C25": {"1": "BUTTON", "2": "GND"},
    "C26": {"1": "V+", "2": "GND"},
    "C27": {"1": "VAMP", "2": "GND"},
    "C28": {"1": "VAMP", "2": "GND"},
    "C29": {"1": "VAMP", "2": "BOOST_FB"},
    "J1": {"1": "VO+", "2": "VO-"},
    "J2": {"1": "BUTTON_EXT", "2": "GND"},
    **{f"TP{i}": {"P$1": net} for i, net in enumerate(
        ["~{RESET}", "GND", "+3V3", "VAMP", "VBAT", "I2S_DIN", "I2S_BCLK", "I2S_LRCLK",
         "AMP_MUTE", "POWER"], 7)},
}
NEW_VALUES = {"U5": "TPS61023DRLR", "L1": "1uH (MPN pending)", "Q4": "AO3400A",
              "R20": "4.7K", "R21": "10K", "R22": "1K", "R23": "732K", "R24": "100K",
              "C25": "10nF", "C26": "22uF", "C27": "22uF", "C28": "22uF",
              "C29": "220pF (DNP)", "J1": "504050-0291", "J2": "SM02B-SRSS-TB"}


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


def check_footprint(source_path, package_name, footprint_path, expected_numbers):
    source = ET.parse(source_path).getroot()
    packages = source.findall("drawing/schematic/libraries/library/packages/package")
    package = next(p for p in packages if p.get("name") == package_name)
    _, fp = load(footprint_path)
    pads = {p.atoms()[1]: p for p in fp.children("pad")}
    require(set(pads) == set(expected_numbers), f"{package_name}: unexpected physical pad set.")
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
    require(len(details) == len(expected_numbers), f"{package_name}: source land count differs.")
    return details


def check_placement(cli, schematic, components, pin_nets, dnp, record_gui_review):
    path = DRAFT / "handbell.kicad_pcb"
    folder = DRAFT / "placement"
    manifest = json.loads((folder / "placement-manifest.json").read_text())
    _, pcb = load(path)
    require(manifest["generated_pcb_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest(),
            "Placement manifest refers to a different PCB.")
    require(manifest["schematic_sha256"] == hashlib.sha256((DRAFT / "handbell.kicad_sch").read_bytes()).hexdigest(),
            "Placement manifest refers to a different schematic.")
    require(not any(pcb.children(kind) for kind in ("segment", "via", "zone")),
            "This placement-only contract must not be used to approve routed copper.")
    footprints = {fp.properties()["Reference"]: fp for fp in pcb.children("footprint")}
    require(len(footprints) == len(pcb.children("footprint")) and set(footprints) == set(components),
            "PCB references do not exactly match schematic references.")
    instances = {s.properties()["Reference"]: s for s in schematic.children("symbol")
                 if s.value("unit") == "1"}
    checked_pads = 0
    for ref, fp in footprints.items():
        require(fp.atoms()[1] == components[ref].findtext("footprint"), f"{ref}: PCB footprint differs.")
        require(fp.properties()["Value"] == components[ref].findtext("value"), f"{ref}: PCB value differs.")
        require(fp.value("path") == f'/{schematic.value("uuid")}/{instances[ref].value("uuid")}',
                f"{ref}: PCB schematic link differs.")
        attrs = fp.child("attr")
        require(bool(attrs and "dnp" in attrs.atoms()) == (ref in dnp), f"{ref}: PCB DNP differs.")
        present = {p.atoms()[1] for p in fp.children("pad")}
        require({pin for r, pin in pin_nets if r == ref} <= present, f"{ref}: schematic pins lack physical pads.")
        for pad in fp.children("pad"):
            expected = pin_nets.get((ref, pad.atoms()[1]))
            require(pad.value("net") == pcb_net_name(expected), f"{ref}.{pad.atoms()[1]}: PCB pad net differs.")
            checked_pads += 1
    top = {p["reference"] for p in manifest["components"]}
    back = {p["reference"] for p in manifest["copper_only_back_features"]}
    require(top | back | dnp == set(components) and not top & back, "Manifest reference inventory differs.")
    for ref in top | dnp:
        require(footprints[ref].value("layer") == "F.Cu", f"{ref}: fitted/DNP part is not on front.")
    for ref in back:
        require(footprints[ref].value("layer") == "B.Cu", f"{ref}: copper-only feature is not on back.")
    require(not manifest["remaining_planning_envelope_overlaps_mm2"] and
            not manifest["remaining_conservative_boundary_violations"], "Placement envelope conflicts remain.")
    drc_path = folder / "placement-drc.json"
    subprocess.run([cli, "pcb", "drc", "--schematic-parity", "--format", "json",
                    "--output", str(drc_path), str(path)], check=True)
    drc = json.loads(drc_path.read_text())
    allowed = {"silk_over_copper", "silk_overlap", "silk_edge_clearance", "text_height",
               "text_thickness", "hole_clearance"}
    require(all(v["type"] in allowed for v in drc["violations"]),
            "New substantive DRC findings require review; do not expand allowances to hide them.")
    holes = [v for v in drc["violations"] if v["type"] == "hole_clearance"]
    require(all(all("of X6" in item["description"] for item in v["items"]) for v in holes),
            "Unreviewed hole clearance outside the USB footprint.")
    auto_pads = {p.value("uuid") for fp in footprints.values() for p in fp.children("pad")
                 if (p.value("net") or "").startswith(("Net-", "unconnected-"))}
    for finding in drc["schematic_parity"]:
        require(finding["type"] == "net_conflict" and
                finding["description"] == "No corresponding pin found in schematic" and
                len(finding["items"]) == 1 and finding["items"][0]["uuid"] in auto_pads,
                "Unexpected native parity discrepancy; review rather than suppress.")
    gui_report = folder / "placement-gui-drc.rpt"
    gui_record = folder / "placement-gui-review.json"
    require(gui_report.exists(), "Save a paired-editor GUI DRC report with schematic parity enabled.")
    gui_text = gui_report.read_text(encoding="utf-8-sig")
    require("** Found 0 Footprint errors **" in gui_text, "GUI schematic parity findings remain.")
    require(f'** Found {len(drc["violations"])} DRC violations **' in gui_text and
            f'** Found {len(drc["unconnected_items"])} unconnected pads **' in gui_text,
            "GUI and CLI physical DRC counts differ.")
    binding = {
        "pcb_sha256": manifest["generated_pcb_sha256"],
        "schematic_sha256": manifest["schematic_sha256"],
        "project_sha256": hashlib.sha256((DRAFT / "handbell.kicad_pro").read_bytes()).hexdigest(),
        "gui_report_sha256_lf": hashlib.sha256(gui_text.encode("utf-8")).hexdigest(),
        "kicad_version": drc["kicad_version"],
        "gui_schematic_parity_findings": 0,
        "scope": "Paired schematic/PCB editors, parity enabled; physical DRC/routing gates remain open.",
    }
    if record_gui_review:
        require(gui_report.stat().st_mtime >= path.stat().st_mtime,
                "GUI report predates the PCB; rerun the paired-editor check.")
        gui_record.write_text(json.dumps(binding, indent=2)+"\n", encoding="utf-8")
    require(gui_record.exists() and json.loads(gui_record.read_text()) == binding,
            "GUI evidence is missing/stale. Rerun it, then use --placement --record-gui-review.")
    report = {
        "scope": "Unrouted correspondence/placement screen, NOT DRC or fabrication approval",
        "pcb_sha256": manifest["generated_pcb_sha256"], "schematic_sha256": manifest["schematic_sha256"],
        "references": len(footprints), "physical_pads_checked": checked_pads,
        "fitted_front": len(top), "copper_only_back": len(back), "dnp": sorted(dnp),
        "native_drc_counts": dict(Counter(v["type"] for v in drc["violations"])),
        "native_schematic_parity_counts": dict(Counter(v["type"] for v in drc["schematic_parity"])),
        "cli_parity_limitation": "CLI fallback omits auto/NC pins. Full exported pin/net correspondence is checked above; paired-editor GUI parity must be recorded separately.",
        "gui_schematic_parity_findings": 0,
        "unconnected_items": len(drc["unconnected_items"]),
        "unresolved_gate": "X6 source footprint NPTH clearance and unfinished silk; all routing still absent.",
    }
    (folder / "placement-review.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kicad-cli", default="kicad-cli")
    parser.add_argument("--placement", action="store_true",
                        help="Also check the current unrouted PCB, manifest and native DRC.")
    parser.add_argument("--record-gui-review", action="store_true",
                        help="Bind a freshly saved paired-editor, parity-enabled GUI report to these CAD bytes.")
    args = parser.parse_args()
    if args.record_gui_review and not args.placement:
        parser.error("--record-gui-review requires --placement")
    paths = {
        "baseline": BASE / "kicad" / f"{BASE_STEM}.kicad_sch",
        "sox": SOX / "kicad" / "Adafruit_LSM6DSOX.kicad_sch",
        "boost": BOOST / "kicad" / "Adafruit TPS61023.kicad_sch",
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
        "adafruit_4654": check_import(BOOST / "upstream" / "Adafruit TPS61023.brd", trees["boost"], {}),
    }
    base_nets, draft_nets = nets(trees["baseline"]), nets(trees["handbell"])
    baseline_projection = projected(base_nets, {"IC4"} | REMOVED)
    old_amp_group = next(group for group in baseline_projection if ("Q1", "3") in group)
    require(AMP_MOVED <= old_amp_group, "Baseline amplifier source topology changed.")
    baseline_projection.remove(old_amp_group)
    baseline_projection.update({old_amp_group - AMP_MOVED, frozenset(AMP_MOVED)})
    draft_projection = projected(draft_nets, {"IC4"} | ADDED)
    require(baseline_projection == draft_projection,
            f"Retained connections changed: missing={baseline_projection-draft_projection}, extra={draft_projection-baseline_projection}")
    baseline_components = {c.get("ref"): c for c in trees["baseline"].findall("components/comp")}
    draft_components = {c.get("ref"): c for c in trees["handbell"].findall("components/comp")}
    require(set(draft_components) == (set(baseline_components) - REMOVED) | ADDED,
            "Unexpected added/removed components.")
    for ref, component in baseline_components.items():
        if ref == "IC4" or ref in REMOVED:
            continue
        for field in ["value", "footprint"]:
            expected = "10K" if ref == "R18" and field == "value" else component.findtext(field)
            if field == "footprint" and ref in CHANGED_FOOTPRINTS:
                expected = CHANGED_FOOTPRINTS[ref]
            require(expected == draft_components[ref].findtext(field),
                    f"Retained {ref} {field} changed.")

    pin_nets = {pin: name for name, members in draft_nets.items() for pin in members}
    for ref, pin_map in NEW_PIN_NETS.items():
        require({pin for r, pin in pin_nets if r == ref} == set(pin_map), f"{ref}: unexpected pin set.")
        for pin, name in pin_map.items():
            require(pin_nets.get((ref, pin)) == name, f"{ref}.{pin} must connect to {name}.")
    for pin in AMP_MOVED:
        require(pin_nets.get(pin) == "VAMP", f"{pin}: amplifier rail not moved to boost output.")
    for ref, value in NEW_VALUES.items():
        require(draft_components[ref].findtext("value") == value, f"{ref}: expected {value}.")
    require(pin_nets.get(("IC1", "30")) == "BUTTON", "User button must use GPIO19.")
    require(pin_nets.get(("IC1", "31")) == "AMP_MUTE", "Mute must use GPIO20.")
    _, native_schematic = load(paths["handbell"])
    dnp = {s.properties()["Reference"] for s in native_schematic.children("symbol") if s.value("dnp") == "yes"}
    require(dnp == {"C29"}, "Only the unresolved feed-forward option C29 should be DNP.")
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
    pads = check_footprint(SOX / "upstream" / "Adafruit_LSM6DSOX.sch", "LGA-14L",
                          SOX / "kicad" / "Adafruit_LSM6DSOX-import-fps.pretty" / "LGA-14L.kicad_mod",
                          {str(i) for i in range(1, 15)})
    boost_pads = {
        name: check_footprint(BOOST / "upstream" / "Adafruit TPS61023.sch", name,
                             BOOST / "kicad" / "Adafruit TPS61023-import-fps.pretty" / f"{name}.kicad_mod",
                             numbers)
        for name, numbers in [("SOT563", {str(i) for i in range(1, 7)}),
                              ("INDUCTOR_5X5MM_TDK_VLC5045", {"P$1", "P$2"})]
    }
    base_project = json.loads(paths["baseline"].with_suffix(".kicad_pro").read_text())
    draft_project = json.loads(paths["handbell"].with_suffix(".kicad_pro").read_text())
    require(base_project["erc"] == draft_project["erc"], "ERC severity/pin matrix/exclusions changed.")
    require(not draft_project["erc"]["erc_exclusions"], "ERC exclusions must remain empty.")
    require(all(not s["violations"] for s in erc["sheets"]), "ERC violations remain.")
    published = ET.parse(DRAFT / "reports" / "handbell-netlist.xml").getroot()
    require(nets(published) == draft_nets, "Published netlist is stale; regenerate exports.")
    if args.placement:
        check_placement(args.kicad_cli, native_schematic, draft_components, pin_nets, dnp, args.record_gui_review)

    report = {
        "kicad_version": erc["kicad_version"],
        "scope": "Net topology, preserved component values/footprints, sensor pads, GPIO contract and ERC; not layout/function/safety approval.",
        "hash_normalization": "Review hashes use UTF-8 text with CRLF/CR normalized to LF; upstream source-byte hashes are recorded separately.",
        "source_schematic_sha256_lf": {
            name: hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
            for name, path in paths.items()
        },
        "source_connected_groups_matching_native": import_counts,
        "revision": "0.2-draft",
        "retained_components": len(baseline_components)-1-len(REMOVED),
        "retained_connection_groups": len(baseline_projection),
        "added_components_or_copper_features": sorted(ADDED),
        "removed_components_or_features": sorted(REMOVED),
        "retained_amp_pins_moved_to_VAMP": sorted([list(p) for p in AMP_MOVED]),
        "intentional_footprint_changes": CHANGED_FOOTPRINTS,
        "new_pin_net_contract": NEW_PIN_NETS,
        "dnp_references": sorted(dnp),
        "sensor_pin_nets": {str(i): pin_nets[("IC4", str(i))] for i in range(1, 15)},
        "sensor_footprint_pads": pads,
        "boost_footprint_pads": boost_pads,
        "erc_configuration_unchanged": True,
        "erc_exclusions": [],
        "erc_errors": 0,
        "erc_warnings": 0,
    }
    (DRAFT / "reports" / "handbell-erc.json").write_text(json.dumps(erc, indent=2)+"\n", encoding="utf-8")
    (DRAFT / "reports" / "connectivity-review.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    with (DRAFT / "reports" / "bom-draft.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["Reference", "Value", "Footprint", "MPN", "DNP", "Review status"])
        for ref in sorted(draft_components):
            c = draft_components[ref]
            status = "Inherited reference; exact MPN, assembly SKU and fit review pending"
            if ref.startswith("TP") or ref in {"D+1", "D-1", "GAIN0", "CHG_EN0"}:
                status = "PCB copper test pad; no fitted component"
            elif ref in {"C23", "C24"}:
                status = "100 nF local IMU bypass; dielectric, voltage, tolerance and MPN pending"
            elif ref == "IC4":
                status = "Owner-approved sensor; footprint mapping reviewed, assembly quote pending"
            elif ref in {"U5", "Q4", "J1", "J2"}:
                status = "Prototype ordering code selected; assembly availability and full integration review pending"
            elif ref in {"L1", "C26", "C27", "C28", "C29", "R23", "R24"}:
                status = "Boost design candidate; exact MPN, effective values, compensation and thermal review pending"
            elif ref in {"R20", "R21", "R22", "C25"}:
                status = "New control/filter passive; voltage/tolerance/MPN and cable review pending"
            mpn = c.findtext("fields/field[@name='MPN']", default="")
            writer.writerow([ref, c.findtext("value"), c.findtext("footprint"),
                             "LSM6DSOXTR" if ref == "IC4" else mpn, "yes" if ref in dnp else "no", status])
    print(f"PASS: source groups {import_counts}; {len(baseline_components)-1-len(REMOVED)} retained components; "
          f"{len(baseline_projection)} retained net groups; all 14 sensor pads; ERC 0 errors / 0 warnings.")


if __name__ == "__main__":
    main()
