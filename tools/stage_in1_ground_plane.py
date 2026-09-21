# SPDX-License-Identifier: MIT
"""Stage the first source-backed In1 protected-GND plane candidate."""
import argparse, hashlib, json, os, shutil, subprocess, sys, time, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "hardware/handbell/iterations/printed-bell-four-layer"
PCB_HASH = "d91837ed9f5cff10d709521e448f6deae3aac3a52abed88c34271ee809e25418"
MANIFEST_HASH = "ed64e9c92bd2cc7dc90a00cd98689f511517151c909052e7b23b3840d101f381"
INVENTORY = SOURCE / "reports/in1-exclusion-inventory.json"
REPORT = SOURCE / "reports/in1-plane-first-stage.json"
CLI = Path(os.environ["LOCALAPPDATA"]) / "Programs/KiCad/10.0/bin/kicad-cli.exe"
NS = uuid.UUID("26fe36fd-98d1-474d-aa7f-e54d62502e77")

sys.path.insert(0, str(ROOT / "tools"))
from kicad_sexpr import load, loads, apply_edits


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(value, message):
    if not value: raise AssertionError(message)
def stable(name): return str(uuid.uuid5(NS, name))


def replace_child(text, node, head, value):
    child = node.child(head)
    return apply_edits(text, [(child.start-node.start, child.end-node.start, value)])


def strip_fills(text):
    node = loads(text)
    return apply_edits(text, [(x.start, x.end, "") for x in node.children("filled_polygon")])


def keepout(name, bounds):
    x0, y0, x1, y1 = [value / 1_000_000 for value in bounds]
    return f'''(zone
        (layer "In1.Cu")
        (uuid "{stable(name)}")
        (name "{name}")
        (hatch edge 0.5)
        (connect_pads (clearance 0))
        (min_thickness 0.25)
        (keepout (tracks allowed) (vias allowed) (pads allowed) (copperpour not_allowed) (footprints allowed))
        (placement (enabled no) (sheetname ""))
        (fill (thermal_gap 0.5) (thermal_bridge_width 0.5) (island_removal_mode 0))
        (polygon (pts (xy {x0:g} {y0:g}) (xy {x1:g} {y0:g}) (xy {x1:g} {y1:g}) (xy {x0:g} {y1:g})))
    )'''


def run(command, timeout, work, name, stages):
    out, err = work/f"{name}.stdout.txt", work/f"{name}.stderr.txt"
    started = time.monotonic()
    with out.open("w") as stdout, err.open("w") as stderr:
        result = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=timeout)
    row = {"name": name, "seconds": time.monotonic()-started, "exit_code": result.returncode,
           "command": ["<kicad-cli>" if x == str(CLI) else
                       x.replace(str(work), "<work>").replace(str(ROOT), "<repo>") for x in command],
           "stdout": out.name, "stderr": err.name}
    stages.append(row)
    (work/"stages.json").write_bytes((json.dumps(stages, indent=2)+"\n").encode())
    require(result.returncode == 0, name + " failed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(
        "diagnostic-only; incomplete per-layer/source invariant gates, geometry attempt budget exhausted")
    work = args.work_dir.resolve()
    require(not work.exists(), "Work directory must be new")
    require(sha(SOURCE/"handbell.kicad_pcb") == PCB_HASH, "Source PCB changed")
    require(sha(SOURCE/"placement-manifest.json") == MANIFEST_HASH, "Manifest changed")
    work.mkdir(parents=True)
    package = work/"package"; package.mkdir()
    for name in ("handbell.kicad_sch", "handbell.kicad_pro", "fp-lib-table", "sym-lib-table",
                 "Handbell.kicad_sym", "T8.kicad_sym", "Clock.kicad_sym",
                 "battery-contact-interface.json", "LICENSE.txt"):
        shutil.copy2(SOURCE/name, package/name)
    shutil.copytree(SOURCE/"libraries", package/"libraries")

    source_text, source = load(SOURCE/"handbell.kicad_pcb")
    inventory = json.loads(INVENTORY.read_text())
    fzone = next(z for z in source.children("zone") if z.value("name") == "quote-native-F-GND-v1")
    fzone_text = source_text[fzone.start:fzone.end]
    in1 = strip_fills(fzone_text)
    inode = loads(in1)
    in1 = replace_child(in1, inode, "layer", '(layer "In1.Cu")')
    inode = loads(in1)
    in1 = replace_child(in1, inode, "uuid", f'(uuid "{stable("in1-protected-gnd-v1")}")')
    inode = loads(in1)
    in1 = replace_child(in1, inode, "name", '(name "in1-protected-gnd-v1")')

    exclusions = inventory["existing_pour_only_exclusions"]
    private = [row for row in exclusions if row["protected_item_uuid"] in {
        "6623be95-c657-5a8e-bedb-c5a73d42d40b", "eafa404c-be47-5f5c-8167-d39a967ba2e5"}]
    guards = [keepout("in1-private/"+row["protected_item_uuid"], row["bounds_absolute_iu"])
              for row in private]
    for row in inventory["sensitive_regions"]["BOOST_SW"]["items"]:
        bounds = [row["bounds_iu"][0]-250000, row["bounds_iu"][1]-250000,
                  row["bounds_iu"][2]+250000, row["bounds_iu"][3]+250000]
        guards.append(keepout("in1-boost-sw/"+row["uuid"], bounds))
    clock = [90103600, 96152596, 97237500, 100263901]
    guards.append(keepout("in1-clock-region", clock))
    addition = "\n" + in1 + "\n" + "\n".join(guards) + "\n"
    unfilled_text = source_text.rstrip()[:-1] + addition + ")\n"
    unfilled = package/"handbell-unfilled.kicad_pcb"
    unfilled.write_bytes(unfilled_text.encode())
    native = package/"handbell-native-filled.kicad_pcb"
    native.write_bytes(unfilled.read_bytes())
    stages = []
    run([str(CLI), "pcb", "drc", "--format", "json", "--severity-all", "--refill-zones",
         "--save-board", "--output", str(work/"native-refill-drc.json"), str(native)],
        120, work, "native-refill", stages)

    native_text, native_root = load(native)
    candidate_text = unfilled_text
    candidate_root = loads(candidate_text)
    edits = []
    for zone_name in ("quote-native-F-GND-v1", "in1-protected-gnd-v1"):
        nz = next(z for z in native_root.children("zone") if z.value("name") == zone_name)
        fills = nz.children("filled_polygon")
        require(fills, "Native refill omitted " + zone_name)
        cz = next(z for z in candidate_root.children("zone") if z.value("name") == zone_name)
        old = cz.children("filled_polygon")
        edits.extend((x.start, x.end, "") for x in old)
        insert = "\n".join(native_text[x.start:x.end] for x in fills) + "\n"
        edits.append((cz.end-1, cz.end-1, insert))
    candidate_text = apply_edits(candidate_text, edits)
    candidate = package/"handbell.kicad_pcb"
    candidate.write_bytes(candidate_text.encode())
    run([str(CLI), "pcb", "drc", "--format", "json", "--severity-all",
         "--output", str(work/"candidate-drc.json"), str(candidate)],
        120, work, "candidate-drc", stages)

    native_dir = CLI.parent
    dll_handle = os.add_dll_directory(str(native_dir))
    sys.path.insert(0, str(native_dir/"Lib/site-packages"))
    import pcbnew as pcb
    from zone_graph import CopperGraph
    from check_front_ground import compare_components
    before, after = CopperGraph(pcb, SOURCE/"handbell.kicad_pcb"), CopperGraph(pcb, candidate)
    preserved = compare_components(before, after)
    pickoffs = [after.pickoff("R26", "2", "R27", "2"), after.pickoff("R24", "2", "C28", "2")]
    require(all(x["independent_until_terminal"] for x in pickoffs), "Private pickoff bypass")
    require(not after.shorts and not after.floating_copper(), "Filled graph short/floating copper")
    new_zone_uuid = stable("in1-protected-gnd-v1")
    islands = [x for x in after.zone_islands if x["zone_uuid"] == new_zone_uuid]
    require(islands, "No In1 filled islands")

    old_drc = json.loads((SOURCE/"reports/four-layer-baseline-drc.json").read_text())
    drc = json.loads((work/"candidate-drc.json").read_text())
    old_nonopens = {(x["type"], x["description"]) for x in old_drc["violations"]}
    new_nonopens = [(x["type"], x["description"]) for x in drc["violations"]
                    if (x["type"], x["description"]) not in old_nonopens]
    require(not new_nonopens, "New non-unconnected DRC findings")
    require(len(drc["unconnected_items"]) <= 51, "Open count increased")
    zones = loads(candidate_text).children("zone")
    require(len(zones) == 21, "Expected F1+F10+In1 new1+9 In1 guards")
    report = {
        "status": "STAGED_IN1_PROTECTED_GROUND_CANDIDATE_NOT_ACCEPTED",
        "input_pcb_sha256": PCB_HASH, "output_pcb_sha256": sha(candidate),
        "accepted_manifest_sha256": MANIFEST_HASH, "accepted_manifest_modified": False,
        "source_plan_sha256": sha(SOURCE.parent/"printed-bell-clock-draft/reports/front-ground-plan.json"),
        "inventory_sha256": sha(INVENTORY), "tool_sha256": sha(__file__),
        "workspace_name": work.name, "zones_total": len(zones),
        "zones_added": {"ground": 1, "private_via_guards": 2, "boost_guards": 6, "clock_guards": 1},
        "in1_islands": islands, "in1_total_area_mm2": sum(x["filled_area_mm2"] for x in islands),
        "private_pickoffs": pickoffs, "existing_pad_groups_preserved": preserved,
        "shorts": after.shorts, "floating_copper": after.floating_copper(),
        "native_drc": {"opens": len(drc["unconnected_items"]),
                       "warnings": sum(x["severity"] == "warning" for x in drc["violations"]),
                       "new_non_unconnected_findings": new_nonopens},
        "source_invariants": "Candidate is source text plus ten new In1 zone definitions and native F/In1 filled_polygon caches; footprints/tracks/vias/pads/rules/layers remain source bytes.",
        "stages": stages,
        "remaining_gates": ["Astra engineering review", "physical stackup", "return-path/plane continuity review",
                            "full CAD rebind", "manufacturing and assembly qualification"]
    }
    REPORT.write_bytes((json.dumps(report, indent=2)+"\n").encode())
    print(json.dumps({"candidate": str(candidate), "candidate_sha256": sha(candidate),
                      "opens": len(drc["unconnected_items"]), "warnings": report["native_drc"]["warnings"],
                      "in1_islands": len(islands), "in1_area_mm2": report["in1_total_area_mm2"],
                      "report_sha256": sha(REPORT)}, indent=2))


if __name__ == "__main__":
    main()
