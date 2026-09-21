# SPDX-License-Identifier: MIT
"""Stage the first source-backed In1 protected-GND plane candidate."""
import argparse, hashlib, json, os, shutil, subprocess, sys, time, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "hardware/handbell/iterations/printed-bell-four-layer"
PCB_HASH = "d91837ed9f5cff10d709521e448f6deae3aac3a52abed88c34271ee809e25418"
MANIFEST_HASH = "ed64e9c92bd2cc7dc90a00cd98689f511517151c909052e7b23b3840d101f381"
INVENTORY = SOURCE / "reports/in1-exclusion-inventory.json"
REPORT = SOURCE / "reports/in1-plane-settings-replay.json"
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
    x0, y0, x1, y1 = [f"{value / 1_000_000:.6f}" for value in bounds]
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
        (polygon (pts (xy {x0} {y0}) (xy {x1} {y0}) (xy {x1} {y1}) (xy {x0} {y1})))
    )'''


def fill_worker(source, output, report):
    native_dir = CLI.parent
    dll_handle = os.add_dll_directory(str(native_dir))
    sys.path.insert(0, str(native_dir/"Lib/site-packages"))
    import pcbnew as pcb
    require(pcb.GetBuildVersion() == "10.0.6", "KiCad 10.0.6 required")
    board = pcb.LoadBoard(str(source))
    settings = board.GetDesignSettings()
    values = {"m_MinClearance": .2, "m_CopperEdgeClearance": .25,
              "m_HoleClearance": .25, "m_HoleToHoleMin": .25, "m_MaxError": .001}
    for name, value in values.items():
        setattr(settings, name, pcb.FromMM(value))
    board.BuildConnectivity()
    started = time.monotonic()
    require(pcb.ZONE_FILLER(board).Fill(board.Zones()), "Native fill failed")
    require(pcb.SaveBoard(str(output), board, True), "Native save failed")
    Path(report).write_bytes((json.dumps({"kicad_version": pcb.GetBuildVersion(),
        "settings_mm": values, "fill_seconds": time.monotonic()-started,
        "output_sha256": sha(output)}, indent=2)+"\n").encode())


def run(command, timeout, work, name, stages):
    out, err = work/f"{name}.stdout.txt", work/f"{name}.stderr.txt"
    started = time.monotonic()
    stages.append({"name": name, "status": "started", "command": [
        "<kicad-cli>" if x == str(CLI) else "<python>" if x == sys.executable else
        x.replace(str(work), "<work>").replace(str(ROOT), "<repo>") for x in command]})
    (work/"stages.json").write_bytes((json.dumps(stages, indent=2)+"\n").encode())
    with out.open("w") as stdout, err.open("w") as stderr:
        result = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=timeout)
    row = {"name": name, "seconds": time.monotonic()-started, "exit_code": result.returncode,
           "command": ["<kicad-cli>" if x == str(CLI) else "<python>" if x == sys.executable else
                       x.replace(str(work), "<work>").replace(str(ROOT), "<repo>") for x in command],
           "stdout": out.name, "stderr": err.name}
    stages[-1] = row
    (work/"stages.json").write_bytes((json.dumps(stages, indent=2)+"\n").encode())
    require(result.returncode == 0, name + " failed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--settings-replay", action="store_true")
    args = parser.parse_args()
    require(args.settings_replay,
            "diagnostic-only; use --settings-replay only for the authorized complete replay")
    work = args.work_dir.resolve()
    require(not work.exists(), "Work directory must be new")
    require(sha(SOURCE/"handbell.kicad_pcb") == PCB_HASH, "Source PCB changed")
    require(sha(SOURCE/"placement-manifest.json") == MANIFEST_HASH, "Manifest changed")
    work.mkdir(parents=True)
    directories = {name: work/name for name in ("unfilled", "canonical", "final")}
    for directory in directories.values():
        directory.mkdir()
        for name in ("handbell.kicad_sch", "handbell.kicad_pro", "fp-lib-table", "sym-lib-table",
                     "Handbell.kicad_sym", "T8.kicad_sym", "Clock.kicad_sym",
                     "battery-contact-interface.json", "LICENSE.txt"):
            shutil.copy2(SOURCE/name, directory/name)
        shutil.copytree(SOURCE/"libraries", directory/"libraries")

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
    unfilled = directories["unfilled"]/"handbell.kicad_pcb"
    unfilled.write_bytes(unfilled_text.encode())
    parsed = loads(unfilled_text)
    expected_guard_bounds = {}
    for row in private:
        expected_guard_bounds["in1-private/"+row["protected_item_uuid"]] = row["bounds_absolute_iu"]
    for row in inventory["sensitive_regions"]["BOOST_SW"]["items"]:
        expected_guard_bounds["in1-boost-sw/"+row["uuid"]] = [
            row["bounds_iu"][0]-250000, row["bounds_iu"][1]-250000,
            row["bounds_iu"][2]+250000, row["bounds_iu"][3]+250000]
    expected_guard_bounds["in1-clock-region"] = clock
    for name, expected in expected_guard_bounds.items():
        zone = next(z for z in parsed.children("zone") if z.value("name") == name)
        points = zone.child("polygon").child("pts").children("xy")
        xs = [round(float(p.atoms()[1])*1_000_000) for p in points]
        ys = [round(float(p.atoms()[2])*1_000_000) for p in points]
        require([min(xs), min(ys), max(xs), max(ys)] == expected,
                "Serialized guard geometry differs: " + name)
        require(zone.value("layer") == "In1.Cu" and zone.child("keepout") is not None,
                "Serialized guard role differs: " + name)
        keepout_values = {child.head: child.atoms()[1] for child in zone.child("keepout").children()}
        require(keepout_values == {"tracks": "allowed", "vias": "allowed", "pads": "allowed",
                                   "copperpour": "not_allowed", "footprints": "allowed"},
                "Serialized guard permissions differ: " + name)
    native = directories["canonical"]/"handbell.kicad_pcb"
    stages = []
    run([sys.executable, str(Path(__file__)), "--fill-worker", str(unfilled), str(native),
         str(work/"fill-worker.json")], 120, work, "native-fill", stages)

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
    candidate = directories["final"]/"handbell.kicad_pcb"
    candidate.write_bytes(candidate_text.encode())
    run([str(CLI), "pcb", "drc", "--format", "json", "--severity-all",
         "--output", str(work/"candidate-drc.json"), str(candidate)],
        120, work, "candidate-drc", stages)

    native_dir = CLI.parent
    dll_handle = os.add_dll_directory(str(native_dir))
    sys.path.insert(0, str(native_dir/"Lib/site-packages"))
    import pcbnew as pcb
    from zone_graph import CopperGraph, IslandItem
    from check_front_ground import compare_components, board_polygon, bounds_polygon
    before, after = CopperGraph(pcb, SOURCE/"handbell.kicad_pcb"), CopperGraph(pcb, candidate)
    preserved = compare_components(before, after)
    pickoffs = [after.pickoff("R26", "2", "R27", "2"), after.pickoff("R24", "2", "C28", "2")]
    require(all(x["independent_until_terminal"] for x in pickoffs), "Private pickoff bypass")
    require(not after.shorts and not after.floating_copper(), "Filled graph short/floating copper")
    new_zone_uuid = stable("in1-protected-gnd-v1")
    islands = [x for x in after.zone_islands if x["zone_uuid"] == new_zone_uuid]
    require(islands, "No In1 filled islands")
    manifest = json.loads((SOURCE/"placement-manifest.json").read_text())
    plan = json.loads((SOURCE.parent/"printed-bell-clock-draft/reports/front-ground-plan.json").read_text())
    by_zone = {z.m_Uuid.AsString(): z for z in after.board.Zones()}
    expected_zone_ids = {z.value("uuid") for z in source.children("zone")}
    expected_zone_ids |= {new_zone_uuid} | {stable(name) for name in expected_guard_bounds}
    require(set(by_zone) == expected_zone_ids and len(by_zone) == 21, "Unexpected zone UUID inventory")
    for zone_id in ("42e3abc5-2c92-5943-8944-bee0da8523c3", new_zone_uuid):
        zone = by_zone[zone_id]
        expected_layer = pcb.F_Cu if zone_id.startswith("42e3") else pcb.In1_Cu
        require(list(zone.GetLayerSet().Seq()) == [expected_layer]
                and zone.GetLocalClearance() == pcb.FromMM(.2)
                and zone.GetMinThickness() == pcb.FromMM(.25)
                and zone.GetPadConnection() == pcb.ZONE_CONNECTION_FULL
                and zone.GetIslandRemovalMode() == pcb.ISLAND_REMOVAL_MODE_ALWAYS,
                "Ground zone settings/layer differ")
    boundary = board_polygon(pcb, manifest, .25)
    guard_records = [(record["bounds_absolute_iu"], pcb.F_Cu)
                     for record in plan["protection"]["pour_only_F_keepouts"]]
    guard_records += [(bounds, pcb.In1_Cu) for bounds in expected_guard_bounds.values()]
    private_ids = {"6623be95-c657-5a8e-bedb-c5a73d42d40b", "eafa404c-be47-5f5c-8167-d39a967ba2e5"}
    for item in after.items.values():
        if not isinstance(item, IslandItem):
            continue
        require(item.layer in (pcb.F_Cu, pcb.In1_Cu), "Unexpected filled copper layer")
        outside = item.polygon.CloneDropTriangulation()
        outside.BooleanSubtract(boundary)
        require(outside.IsEmpty(), "Filled copper violates 0.25 mm edge boundary")
        for bounds, layer in guard_records:
            if layer != item.layer:
                continue
            record = {"bounds_absolute_iu": bounds}
            overlap = item.polygon.CloneDropTriangulation()
            overlap.BooleanIntersection(bounds_polygon(pcb, record))
            require(overlap.IsEmpty(), "Filled copper enters an exact pour-only guard")
        for other in after.items.values():
            if isinstance(other, IslandItem) or not other.IsOnLayer(item.layer) or other.GetNetname() == "GND":
                continue
            require(not item.polygon.Collide(other.GetEffectiveShape(item.layer), pcb.FromMM(.2)-1),
                    "Filled copper violates foreign-net clearance: " + other.GetNetname())
        if item.layer == pcb.In1_Cu:
            for protected in private_ids:
                require(not item.polygon.Collide(after.items[protected].GetEffectiveShape(pcb.In1_Cu),
                                                pcb.FromMM(.25)-1),
                        "In1 fill approaches a private via within 0.25 mm")
    source_root = loads(source_text)
    final_text, final_root = load(candidate)
    for head in ("general", "layers", "setup", "net", "footprint", "segment", "via"):
        original = [source_text[x.start:x.end] for x in source_root.children(head)]
        staged = [final_text[x.start:x.end] for x in final_root.children(head)]
        require(original == staged, "Unauthorized source node changed: " + head)
    source_zones = {z.value("uuid"): z for z in source_root.children("zone")}
    final_zones = {z.value("uuid"): z for z in final_root.children("zone")}
    for zone_id, zone in source_zones.items():
        original_children = [source_text[x.start:x.end] for x in zone.items
                             if getattr(x, "head", None) != "filled_polygon"]
        staged_zone = final_zones[zone_id]
        staged_children = [final_text[x.start:x.end] for x in staged_zone.items
                           if getattr(x, "head", None) != "filled_polygon"]
        require(original_children == staged_children,
                "Existing zone definition changed: " + zone_id)
    merges = []
    before_group = {uid: before.components[before.by_uuid[uid][0]]
                    for uid, pad in before.pads.items() if pad.GetNetname() == "GND" and before.by_uuid[uid]}
    after_groups = {}
    for uid, old_group in before_group.items():
        new_group = after.components[after.by_uuid[uid][0]]
        after_groups.setdefault(new_group, {}).setdefault(old_group, []).append(uid)
    for old_parts in after_groups.values():
        if len(old_parts) > 1:
            refs = sorted({f"{after.pads[u].GetParentFootprint().GetReference()}.{after.pads[u].GetNumber()}"
                           for values in old_parts.values() for u in values})
            merges.append({"previous_group_count": len(old_parts), "joined_pad_refs": refs})

    old_drc = json.loads((SOURCE/"reports/four-layer-baseline-drc.json").read_text())
    drc = json.loads((work/"candidate-drc.json").read_text())
    signature = lambda x: (x["type"], tuple(sorted(i.get("uuid", "") for i in x.get("items", []))))
    old_nonopens = {signature(x) for x in old_drc["violations"]}
    new_nonopens = [x for x in drc["violations"] if signature(x) not in old_nonopens]
    require(not new_nonopens, "New non-unconnected DRC findings")
    require(len(drc["unconnected_items"]) <= 51, "Open count increased")
    projection_crossings = []
    projection_regions = {name: bounds for name, bounds in expected_guard_bounds.items()
                          if name.startswith("in1-boost-sw/") or name == "in1-clock-region"}
    for uid, item in after.items.items():
        if (isinstance(item, IslandItem) or not hasattr(item, "GetClass")
                or item.GetClass() != "PCB_TRACK" or not item.IsOnLayer(pcb.F_Cu)
                or item.GetNetname() == "GND"):
            continue
        for name, bounds in projection_regions.items():
            if bounds_polygon(pcb, {"bounds_absolute_iu": bounds}).Collide(
                    item.GetEffectiveShape(pcb.F_Cu), 0):
                projection_crossings.append({
                    "uuid": uid, "net": item.GetNetname(), "region": name,
                    "start_mm": [item.GetStart().x/1e6, item.GetStart().y/1e6],
                    "end_mm": [item.GetEnd().x/1e6, item.GetEnd().y/1e6],
                    "intended_sensitive_net": (
                        item.GetNetname() in ("BOOST_SW", "/BOOST_SW")
                        or (name == "in1-clock-region"
                            and any(token in item.GetNetname() for token in ("XIN", "XOUT", "C3-Pad2")))),
                })
    zones = final_root.children("zone")
    report = {
        "status": "STAGED_IN1_PROTECTED_GROUND_CANDIDATE_NOT_ACCEPTED",
        "input_pcb_sha256": PCB_HASH, "output_pcb_sha256": sha(candidate),
        "accepted_manifest_sha256": MANIFEST_HASH, "accepted_manifest_modified": False,
        "source_plan_sha256": sha(SOURCE.parent/"printed-bell-clock-draft/reports/front-ground-plan.json"),
        "inventory_sha256": sha(INVENTORY), "tool_sha256": sha(__file__),
        "previous_rejected_tool_sha256": "f645682a982ead3b558ccb8c022f36f263ce92d222da3b80ee073da9041d7ded",
        "workspace_name": work.name, "zones_total": len(zones),
        "zones_added": {"ground": 1, "private_via_guards": 2, "boost_guards": 6, "clock_guards": 1},
        "in1_islands": islands, "in1_total_area_mm2": sum(x["filled_area_mm2"] for x in islands),
        "private_pickoffs": pickoffs, "existing_pad_groups_preserved": preserved,
        "newly_joined_ground_groups": merges,
        "shorts": after.shorts, "floating_copper": after.floating_copper(),
        "native_drc": {"opens": len(drc["unconnected_items"]),
                       "warnings": sum(x["severity"] == "warning" for x in drc["violations"]),
                       "new_non_unconnected_findings": new_nonopens,
                       "schematic_parity": "Not rerun; historical gate remains 46 notices."},
        "projected_f_trace_crossings_of_in1_sensitive_voids": projection_crossings,
        "acceptance_gates": {
            "zone_inventory_and_settings": True, "exact_guard_geometry": True,
            "edge_and_guard_clearance": True, "foreign_net_clearance_F_In1": True,
            "private_via_clearance": True, "full_graph_pickoffs_no_shorts_no_floating": True,
            "existing_pad_groups_and_C25_2_preserved": True,
            "source_nodes_and_existing_zone_definitions_preserved": True,
            "native_drc_without_refill": True, "missing": []},
        "source_invariants": {"exact_source_nodes_preserved": ["general", "layers", "setup", "net", "footprint", "segment", "via"],
                              "all_11_existing_zone_definitions_preserved_excluding_fill_cache": True,
                              "project_sha256": sha(SOURCE/"handbell.kicad_pro"),
                              "manifest_sha256": sha(SOURCE/"placement-manifest.json")},
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
    if len(sys.argv) > 1 and sys.argv[1] == "--fill-worker":
        fill_worker(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
    else:
        main()
