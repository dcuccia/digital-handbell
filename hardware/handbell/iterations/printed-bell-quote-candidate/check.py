# SPDX-License-Identifier: MIT
"""Check this completion candidate, never generate or rewrite its design inputs.

Use KiCad's bundled Python: python.exe check.py --run-native. Without that
option, every explicitly bound native input/output must still match the cache.
Exit 1 means failed/stale evidence; exit 2 means checked but incomplete/blocked,
including the inherited USB/parity errors and mandatory full mechanical rebind.
No successful fabrication/quotation release is implemented by this checker.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
import copy
from datetime import datetime, timezone
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = HERE.parent / "printed-bell-power-rework"
REPORTS = HERE / "reports"
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
from kicad_sexpr import load, loads
from zone_graph import CopperGraph, bbox, native_polygon, rectangle
from fill_ground import BASELINE, ZONE_INPUTS, protection_plan, validate_zone_nodes, validate_filled_graph

PINNED = {
    "handbell.kicad_pcb": "6132f8d3ec508f8ae023888052cc2a1f8b2c24f2c38d9d12dca3234ba887dcc1",
    "placement-manifest.json": "60e394c41bcfd7734b41c7713100360253164381f0217eed325386bd49977799",
}
STATIC = (
    "handbell.kicad_sch", "handbell.kicad_pro", "battery-contact-interface.json",
    "fp-lib-table", "sym-lib-table", "Handbell.kicad_sym", "T8.kicad_sym",
    "source-evidence.json", "design-input-snapshot.json", "LICENSE.txt",
)
NOTICES = ("adafruit-5768-README.md", "adafruit-4438-README.md", "adafruit-4654-README.md")
NATIVE_REPORTS = (
    "erc.json", "drc.json", "handbell-netlist.xml", "handbell-schematic.pdf",
    "schematic-svg/handbell.svg", "front-native.pdf", "rear-native.pdf",
    "front-native.svg", "rear-native.svg", "source-erc.json", "source-drc.json",
    "source-netlist.xml", "native-command-log.json",
)
SILK_TYPES = frozenset(("silk_overlap", "silk_over_copper", "silk_edge_clearance",
                        "text_height", "text_thickness"))
LABELS = {
    "+ POS": (15.7, 11, 4.4, 1.4),
    "- NEG": (-15.7, 11, 4.4, 1.4),
    "< T8 BUTTON END": (0, 10.5, 12, 1.4),
    "1S Li-ion": (0, -15.6, None, None),
    "4.2V ONLY": (0, -14, None, None),
    "NO PRIMARY": (0, -12.1, None, None),
    "CR123A": (0, -10.5, None, None),
}
TOL = .000002
_DLL_HANDLES = []


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    def invalid_number(value):
        raise ValueError("Non-finite JSON number: " + value)
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), parse_constant=invalid_number)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value, indent=2) + "\n",
                    encoding="utf-8")


def relative(path):
    return str(Path(path).resolve().relative_to(ROOT))


def contained(folder, name):
    require(isinstance(name, str) and name and not Path(name).is_absolute(),
            "Expected a relative explicit input name")
    path = folder / name
    require(path.resolve().is_relative_to(folder.resolve()), "Input escapes its declared package")
    return path


def literal(text, node):
    return text[node.start:node.end]


def literal_board(path):
    text = path.read_bytes().decode("utf-8-sig")
    return text, loads(text)


def pose(fp):
    values = list(map(float, fp.child("at").atoms()[1:]))
    require(len(values) in (2, 3) and all(math.isfinite(v) for v in values), "Invalid root pose")
    return values if len(values) == 3 else values + [0.]


def same_pose(a, b):
    return (len(a) == len(b) == 3 and math.dist(a[:2], b[:2]) < TOL
            and abs((a[2] - b[2] + 180) % 360 - 180) < TOL)


def transform(point, old, new):
    angle = math.radians(old[2] - new[2])
    x, y = point[0] - old[0], point[1] - old[1]
    return [new[0] + x * math.cos(angle) - y * math.sin(angle),
            new[1] + x * math.sin(angle) + y * math.cos(angle)]


def source_files():
    """Same explicit authoritative scope as route.py; no directory/report snapshot."""
    names = set(STATIC) | set(PINNED) | {"routing-data.json"}
    _, board = load(SOURCE / "handbell.kicad_pcb")
    _, table = load(SOURCE / "fp-lib-table")
    libraries = {item.value("name"): item.value("uri") for item in table.children("lib")}
    require(len(libraries) == len(table.children("lib")), "Duplicate library table name")
    for fp in board.children("footprint"):
        library, name = fp.atoms()[1].split(":", 1)
        uri = libraries[library]
        require(uri.startswith("${KIPRJMOD}/libraries/"), "Nonlocal authoritative footprint library")
        name = uri.replace("${KIPRJMOD}/", "", 1) + "/" + name + ".kicad_mod"
        contained(SOURCE, name)
        names.add(name)
    names.update("notices/" + name for name in NOTICES)
    return sorted(names)


def declared_moves():
    """Read literal declarations, without importing or invoking the generator."""
    tree = ast.parse((HERE / "route.py").read_text(encoding="utf-8-sig"))
    declarations = {}
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name) and target.id in {"POSES", "REASONS"}:
                    require(target.id not in declarations, "Ambiguous generator move declaration")
                    declarations[target.id] = ast.literal_eval(statement.value)
    poses, reasons = declarations["POSES"], declarations["REASONS"]
    require(isinstance(poses, dict) and poses.keys() == reasons.keys(), "Move/rationale inventory differs")
    require(not set(poses) & {"X6", "BT1", "BT2", "MH1", "MH2"},
            "USB, actual contacts and mounting interfaces are immovable")
    for ref, target in poses.items():
        require(len(target) == 3 and all(math.isfinite(v) for v in target)
                and isinstance(reasons[ref], str) and reasons[ref].strip(),
                "Every declared root move needs a finite pose and rationale: " + ref)
    return poses, reasons


def provenance():
    for name, digest in PINNED.items():
        require(sha(SOURCE / name) == digest, "Accepted source changed: " + name)
    names = source_files()
    sources = {name: sha(contained(SOURCE, name)) for name in names}
    state = read(HERE / "completion-build.json")
    require(state["source_pcb_sha256"] == PINNED["handbell.kicad_pcb"]
            and state["source_manifest_sha256"] == PINNED["placement-manifest.json"],
            "Completion build names a different delivered source")
    require(state["source_inputs"] == sources, "Completion source allowlist/hash binding is stale")
    expected = set(STATIC) | {
        "handbell.kicad_pcb", "placement-manifest.json", "routing-data.json",
        "reports/footprint-movements.json",
    } | {name for name in names if name.startswith(("libraries/", "notices/"))}
    require(set(state["protected_files"]) == expected, "Incomplete or excessive protected-file allowlist")
    for name in sorted(expected):
        require(sha(contained(HERE, name)) == state["protected_files"][name],
                "Completion protected input changed: " + name)
    require(state["generator_sha256"] == sha(HERE / "route.py"), "Completion generator binding is stale")
    allowed_interchange = {
        "routing/" + name for name in (
            "completion-input.dsn", "power-seed.kicad_pcb", "power-seed-manifest.json",
            "power-seed-data.json", "router-input-binding.json", "completion-output.ses",
            "local-router-binding.json", "fixed-copper-restoration.json")
    } | set(ZONE_INPUTS)
    require(set(state["interchange_bindings"]) <= allowed_interchange, "Unknown interchange artifact binding")
    for name, digest in state["interchange_bindings"].items():
        require(sha(contained(HERE, name)) == digest, "Interchange artifact changed: " + name)
    require(state["mechanical_rebind_required"] is True, "Full mechanical rebind cannot be waived")
    for name in names:
        if name in PINNED or name == "routing-data.json":
            continue
        require((HERE / name).read_bytes() == (SOURCE / name).read_bytes(),
                "Authoritative schematic/project/library/provenance bytes changed: " + name)
    return sources, expected


def input_bindings():
    sources, protected = provenance()
    paths = {SOURCE / name for name in sources} | {HERE / name for name in protected}
    paths.update((
        HERE / "completion-build.json", HERE / "route.py", Path(__file__),
        HERE / "zone_graph.py", HERE / "fill_ground.py", HERE / "complete.py",
        HERE / "run_local_router.py",
        ROOT / "tools" / "kicad_sexpr.py", ROOT / "tools" / "check_printed_bell_power_rework.py",
        ROOT / "tools" / "route_printed_bell_power_rework.py",
        ROOT / "tools" / "route_printed_bell.py",
        HERE.parent / "printed-bell-front" / "routing" / "prepare.py",
    ))
    paths.update(HERE / name for name in read(HERE / "completion-build.json")["interchange_bindings"])
    if (HERE / "reports" / "ground-fill.json").exists():
        paths.update(HERE / name for name in ZONE_INPUTS)
    return {relative(path): sha(path) for path in sorted(paths)}


def validate_geometry():
    provenance()
    old_text, old = literal_board(SOURCE / "handbell.kicad_pcb")
    text, board = literal_board(HERE / "handbell.kicad_pcb")
    previous = {fp.properties()["Reference"]: fp for fp in old.children("footprint")}
    current = {fp.properties()["Reference"]: fp for fp in board.children("footprint")}
    require(len(previous) == len(old.children("footprint"))
            and len(current) == len(board.children("footprint")), "Duplicate footprint reference")
    require(current.keys() == previous.keys(), "Footprint inventory changed")
    targets, reasons = declared_moves()
    movements = read(REPORTS / "footprint-movements.json")
    require(isinstance(movements, list), "Movement report must be a list")
    declared = {record["reference"]: record for record in movements}
    require(len(declared) == len(movements) and declared.keys() == targets.keys(),
            "Movement records differ from explicit route.py declarations")
    changed, proofs, owners, pad_ids = {}, {}, {}, {}
    for ref, fp in current.items():
        before = previous[ref]
        a, b = pose(before), pose(fp)
        old_literal, new_literal = literal(old_text, before), literal(text, fp)
        if old_literal != new_literal:
            require(ref in declared, "Undeclared footprint change: " + ref)
            require(not any(pad.child("drill") for pad in before.children("pad")),
                    "A root move would relocate a fixed drill: " + ref)
            old_at, new_at = before.child("at"), fp.child("at")
            old_rest = old_literal[:old_at.start-before.start] + "<POSE>" + old_literal[old_at.end-before.start:]
            new_rest = new_literal[:new_at.start-fp.start] + "<POSE>" + new_literal[new_at.end-fp.start:]
            require(old_rest == new_rest and not same_pose(a, b), "Change beyond root pose: " + ref)
            changed[ref] = {"old_native_pose": a, "new_native_pose": b}
        old_pads = [literal(old_text, p) for p in before.children("pad")]
        new_pads = [literal(text, p) for p in fp.children("pad")]
        require(old_pads == new_pads, "Complete local pad/net/primitive/angle/UUID changed: " + ref)
        for index, pad in enumerate(fp.children("pad")):
            uid = pad.value("uuid")
            require(uid and uid not in owners, "Missing/duplicate physical pad UUID")
            owners[uid] = ref
            pad_ids[uid] = f'{ref}.{pad.atoms()[1]}#{index}'
        proofs[ref] = {
            "root_pose_changed": ref in changed, "pad_count": len(new_pads),
            "footprint_literal_sha256": hashlib.sha256(new_literal.encode()).hexdigest(),
            "local_pad_literals_sha256": hashlib.sha256("\n".join(new_pads).encode()).hexdigest(),
        }
    require(len(owners) == 325, "Expected all 325 physical pad records")
    require(changed.keys() == declared.keys(), "Declared and actual root changes differ")
    for ref, change in changed.items():
        a, b = change["old_native_pose"], change["new_native_pose"]
        require(same_pose(declared[ref]["old_native_pose"], [a[0]-100, a[1]-100, a[2]])
                and same_pose(declared[ref]["new_native_pose"], [b[0]-100, b[1]-100, b[2]])
                and same_pose(declared[ref]["new_native_pose"], targets[ref])
                and declared[ref]["rationale"] == reasons[ref], "Incorrect declared move: " + ref)
    for kind in {n.head for n in old.children()} | {n.head for n in board.children()}:
        if kind in {"footprint", "segment", "via", "zone"}:
            continue
        require([literal(old_text, n) for n in old.children(kind)] ==
                [literal(text, n) for n in board.children(kind)], "Fixed native object changed: " + kind)
    require(not old.children("zone"), "The authoritative source must remain zone-free")
    zone_proof = validate_zone_nodes(HERE, text, board)
    for candidate in (old, board):
        require(not any(candidate.children(kind) for kind in ("arc", "group")),
                "Track arcs and groups are unsupported")
        require(not any(fp.children("zone") for fp in candidate.children("footprint")),
                "Footprint zones are unsupported")
        require(not any((n.value("layer") or "").endswith(".Cu")
                        for n in candidate.children() if n.head.startswith("gr_")),
                "Board-level graphical copper needs an explicit native island implementation")
        for fp in candidate.children("footprint"):
            copper_graphics = [n for n in fp.children() if n.head.startswith("fp_")
                               and (n.value("layer") or "").endswith(".Cu")]
            require(not copper_graphics or
                    (fp.properties()["Reference"] == "CHG_EN0" and len(copper_graphics) == 1
                     and copper_graphics[0].head == "fp_poly"
                     and fp.child("net_tie_pad_groups").atoms()[1:] == ["1, 2"]),
                    "Unsupported footprint copper graphic; explicit shape/net-tie review required")
    manifest, baseline = read(HERE / "placement-manifest.json"), read(SOURCE / "placement-manifest.json")
    require(manifest["schema_version"] == baseline["schema_version"] == 2, "Expected schema-2 manifest")
    variable = {
        "components", "electrical_landmarks", "status", "generated_pcb_sha256",
        "baseline_pcb_sha256", "source_baseline", "mechanical_rebind_required", "routing_report", "planning",
        "proxy_envelope_adjustments",
    }
    require({k: v for k, v in manifest.items() if k not in variable} ==
            {k: v for k, v in baseline.items() if k not in variable},
            "Fixed manifest interfaces, full-height proxies or other undeclared metadata changed")
    require(manifest["board"]["diameter_mm"] == 43 and manifest["board"]["front_z_mm"] == 25
            and manifest["board"]["back_z_mm"] == 26.6, "D43 / F25 / B26.6 changed")
    components = {c["reference"]: c for c in manifest["components"]}
    prior = {c["reference"]: c for c in baseline["components"]}
    envelope_adjustments = copy.deepcopy(baseline["proxy_envelope_adjustments"])
    for adjustment in envelope_adjustments["changes"]:
        angle = math.radians(components[adjustment["reference"]]["rotation_deg"])
        adjustment["rotation_deg"] = components[adjustment["reference"]]["rotation_deg"]
        adjustment["local_depth_axis_board_xy_unit"] = [round(-math.sin(angle), 12), round(math.cos(angle), 12)]
    require(manifest["proxy_envelope_adjustments"] == envelope_adjustments,
            "Maximum-envelope provenance or actual rotated depth axis differs")
    require(len(components) == len(manifest["components"]) == 83 and components.keys() == prior.keys(),
            "Fitted inventory differs from 83 source parts")
    require(Counter(c["side"] for c in components.values()) == {"F": 81, "B": 2}
            and {r for r, c in components.items() if c["side"] == "B"} == {"BT1", "BT2"},
            "81 front electronics plus two fitted back contacts changed")
    require(set(changed) <= {ref for ref, c in components.items() if c["side"] == "F"},
            "Moves must belong to fitted F electronics, not DNP/contact/copper-only interfaces")
    require(components["U1"]["depth_mm"] == 2.1 and components["U6"]["depth_mm"] == 1.55,
            "Qualified proxy-depth corrections lost")
    pose_fields = {"x_mm", "y_mm", "rotation_deg", "native_origin_common_xy_mm"}
    for ref, component in components.items():
        if ref not in changed:
            require(component == prior[ref], "Unmoved full proxy changed: " + ref)
        else:
            require({k: v for k, v in component.items() if k not in pose_fields} ==
                    {k: v for k, v in prior[ref].items() if k not in pose_fields},
                    "Moved proxy dimensions, height, Z, face, value or semantics changed: " + ref)
        a, b = pose(previous[ref]), pose(current[ref])
        expected = transform([prior[ref]["x_mm"]+100, prior[ref]["y_mm"]+100], a, b)
        require(math.dist(expected, [component["x_mm"]+100, component["y_mm"]+100]) < TOL,
                "Body centre does not follow actual root pose: " + ref)
        require(math.dist(component["native_origin_common_xy_mm"], [b[0]-100, b[1]-100]) < TOL
                and abs((component["rotation_deg"] + b[2] + 180) % 360 - 180) < TOL,
                "Manifest native root/angle differs: " + ref)
        require(abs(component["z_max_mm"]-component["z_min_mm"]-component["height_mm"]) < TOL,
                "Full-height proxy Z interval is inconsistent: " + ref)
    landmarks = copy.deepcopy(baseline["electrical_landmarks"])
    for cluster in landmarks.values():
        for ref in cluster:
            if ref in changed:
                b = changed[ref]["new_native_pose"]
                cluster[ref] = [b[0]-100, b[1]-100, b[2]]
    require(manifest["electrical_landmarks"].keys() == landmarks.keys(), "Landmark clusters changed")
    for group, values in landmarks.items():
        require(manifest["electrical_landmarks"][group].keys() == values.keys(), "Landmark inventory changed")
        for ref, target in values.items():
            require(same_pose(manifest["electrical_landmarks"][group][ref], target), "Stale landmark: " + ref)
    for key, name in (("generated_pcb_sha256", "handbell.kicad_pcb"),
                      ("schematic_sha256", "handbell.kicad_sch"),
                      ("battery_contact_interface_sha256", "battery-contact-interface.json")):
        require(manifest[key] == sha(HERE / name), "Stale manifest binding: " + key)
    require(manifest["baseline_pcb_sha256"] == PINNED["handbell.kicad_pcb"]
            and (ROOT / manifest["source_baseline"]).resolve() == SOURCE, "Manifest source baseline changed")
    require(manifest["mechanical_rebind_required"] is True
            and manifest["planning"].get("mechanical_fit_approval") is False, "Mechanical approval cannot transfer")
    return {"changed_footprints": changed, "physical_pad_records_preserved": len(owners),
            "footprint_proofs": proofs, "pose_coordinates": "Absolute native XY; movement records use XY minus 100",
            "all_other_native_objects_and_authoritative_circuit_files_unchanged": True,
            "front_ground_fill": zone_proof}, board, owners, pad_ids


def validate_route_data(board, pad_ids):
    data = read(HERE / "routing-data.json")
    tracks, vias = board.children("segment"), board.children("via")
    require(len(tracks) == len(data["tracks"]) and len(vias) == len(data["vias"]),
            "Native/route metadata inventories differ")
    identities = set(pad_ids)
    for node, item in zip(tracks, data["tracks"]):
        for key, point in (("start", item["a"]), ("end", item["b"])):
            require(len(point) == 2 and all(math.isfinite(v) for v in point)
                    and math.dist(list(map(float, node.child(key).atoms()[1:3])), [v+100 for v in point]) < TOL,
                    "Native track geometry differs from route metadata")
        require(item["layer"] in {"F.Cu", "B.Cu"} and item["net"]
                and item["width"] > 0 and math.isfinite(item["width"])
                and math.dist(item["a"], item["b"]) > .000001
                and node.value("net") == item["net"] and node.value("layer") == item["layer"]
                and abs(float(node.value("width"))-item["width"]) < TOL,
                "Track net/layer/width differs or is invalid")
    for node, item in zip(vias, data["vias"]):
        require(len(item["xy"]) == 2 and all(math.isfinite(v) for v in item["xy"])
                and math.dist(list(map(float, node.child("at").atoms()[1:3])), [v+100 for v in item["xy"]]) < TOL
                and node.value("net") == item["net"] and item["net"]
                and abs(float(node.value("size"))-item["diameter"]) < TOL
                and abs(float(node.value("drill"))-item["drill"]) < TOL
                and node.child("layers").atoms()[1:] == ["F.Cu", "B.Cu"]
                and item["diameter"] > item["drill"] > 0, "Via geometry/net differs or unsupported layer pair")
    for node in tracks + vias:
        uid = node.value("uuid")
        require(uid and uid not in identities, "Missing/duplicate native copper UUID")
        identities.add(uid)
    for intent in data["connections"]:
        for endpoint in ("from", "to"):
            uid = intent[endpoint+"_uuid"]
            require(uid in pad_ids and pad_ids[uid] == intent[endpoint], "Route intent physical endpoint differs")
    return data


def cli_path():
    return Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin" / "kicad-cli.exe"


def sanitize(text):
    for key in ("USERPROFILE", "LOCALAPPDATA", "APPDATA", "HOME"):
        value = os.environ.get(key)
        if value:
            text = re.sub(re.escape(value), "<local-user>", text, flags=re.IGNORECASE)
            text = re.sub(re.escape(value.replace("\\", "/")), "<local-user>", text, flags=re.IGNORECASE)
    return re.sub(r"[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/][^\s\"'<>]+",
                  "<local-user-path>", text, flags=re.IGNORECASE)


def tool_identity():
    cli = cli_path()
    result = subprocess.run([str(cli), "--version"], capture_output=True, text=True, timeout=30, cwd=ROOT)
    require(result.returncode == 0 and result.stdout.strip() == "10.0.6", "KiCad CLI 10.0.6 required")
    symbols = cli.parent.parent / "share" / "kicad" / "symbols" / "power.kicad_sym"
    return {"executable": cli.name, "binary_sha256": sha(cli), "version": "10.0.6",
            "standard_power_symbol_library_sha256": sha(symbols),
            "version_sha256": hashlib.sha256(b"10.0.6").hexdigest()}


def native_api():
    folder = cli_path().parent
    _DLL_HANDLES.append(os.add_dll_directory(str(folder)))
    package = folder / "Lib" / "site-packages"
    sys.path.insert(0, str(package))
    pcb = importlib.import_module("pcbnew")
    extension = importlib.import_module("_pcbnew")
    require(pcb.GetBuildVersion() == "10.0.6"
            and Path(pcb.__file__).resolve().is_relative_to(folder)
            and Path(extension.__file__).resolve().is_relative_to(folder),
            "Native KiCad 10.0.6 API must come from the explicitly selected installation")
    identity = {"version": pcb.GetBuildVersion(),
                "files": {Path(module.__file__).name: sha(module.__file__) for module in (pcb, extension)}}
    return pcb, identity


def run_native():
    validate_geometry()
    inputs, identity = input_bindings(), tool_identity()
    work = REPORTS / ".native-check-work"
    require(not work.exists(), "Inspect/remove interrupted candidate reports/.native-check-work before retrying")
    work.mkdir(parents=True)
    commands = []
    for prefix, package in (("", HERE), ("source-", SOURCE)):
        sch, board = relative(package / "handbell.kicad_sch"), relative(package / "handbell.kicad_pcb")
        commands.extend((
            ["sch", "erc", "--format", "json", "--severity-all",
             "--output", relative(work / (prefix+"erc.json")), sch],
            ["pcb", "drc", "--format", "json", "--schematic-parity", "--severity-all",
             "--output", relative(work / (prefix+"drc.json")), board],
            ["sch", "export", "netlist", "--format", "kicadxml",
             "--output", relative(work / ("source-netlist.xml" if prefix else "handbell-netlist.xml")), sch],
        ))
    sch, board = relative(HERE / "handbell.kicad_sch"), relative(HERE / "handbell.kicad_pcb")
    commands.extend((
        ["sch", "export", "pdf", "--exclude-pdf-metadata",
         "--output", relative(work / "handbell-schematic.pdf"), sch],
        ["sch", "export", "svg", "--output", relative(work / "schematic-svg"), sch],
    ))
    for side, name in (("F", "front"), ("B", "rear")):
        layers = f"{side}.Cu,{side}.Fab,{side}.SilkS,Edge.Cuts"
        mirror = ["--mirror"] if side == "B" else []
        commands.extend((
            ["pcb", "export", "pdf", "--mode-single", "--layers", layers, "--scale", "3", "--exclude-value",
             *mirror, "--output", relative(work / (name+"-native.pdf")), board],
            ["pcb", "export", "svg", "--mode-single", "--layers", layers, "--fit-page-to-board",
             "--exclude-drawing-sheet", *mirror, "--output", relative(work / (name+"-native.svg")), board],
        ))
    logs = []
    config = HERE / "routing" / "native-config"
    config.mkdir(parents=True, exist_ok=True)
    write(config / "10.0" / "sym-lib-table",
          '(sym_lib_table (version 7) (lib (name "power") (type "KiCad") '
          '(uri "${KICAD10_SYMBOL_DIR}/power.kicad_sym") (options "") (descr "Explicit installed KiCad power symbols")))\n')
    environment = dict(os.environ, KICAD_CONFIG_HOME=str(config),
                       KICAD10_SYMBOL_DIR=str(cli_path().parent.parent / "share" / "kicad" / "symbols"))
    try:
        for command in commands:
            result = subprocess.run([str(cli_path()), *command], cwd=ROOT, capture_output=True,
                                    encoding="utf-8", errors="replace", timeout=180, env=environment)
            logs.append({"command": [cli_path().name, *command], "exit": result.returncode,
                         "stdout": sanitize(result.stdout), "stderr": sanitize(result.stderr)})
            require(result.returncode == 0, "Native command failed: " + sanitize(result.stdout+result.stderr))
        require(input_bindings() == inputs and tool_identity() == identity,
                "Inputs/tool changed during native export; no evidence accepted")
        write(work / "native-command-log.json", {"tool": identity, "commands": logs})
        for name in NATIVE_REPORTS:
            source, target = work / name, REPORTS / name
            require(source.is_file() and source.stat().st_size > 0, "Native report missing/empty: " + name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        write(REPORTS / "native-input-bindings.json", {
            "schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(),
            "tool": identity, "inputs": inputs, "reports": {name: sha(REPORTS / name) for name in NATIVE_REPORTS},
            "source_report_basis": "Fresh local exports of explicitly pinned source inputs; source reports never read",
            "native_configuration_scope": "Isolated candidate-local default configuration; shared user settings caused a reproducible DRC stall even on the accepted source",
        })
    finally:
        shutil.rmtree(work)


def validate_cache():
    cache = read(REPORTS / "native-input-bindings.json")
    require(cache["schema_version"] == 1 and cache["tool"] == tool_identity(), "Native binary/version binding is stale")
    inputs = input_bindings()
    require(cache["inputs"] == inputs, "Native input bindings are stale; use --run-native")
    require(cache["reports"] == {name: sha(REPORTS / name) for name in NATIVE_REPORTS},
            "Native report/export inventory or bytes changed; use --run-native")
    return inputs, cache


def normalize_finding(finding, owners, moves):
    result = copy.deepcopy(finding)
    for item in result.get("items", []):
        position = item.get("pos")
        if position is None:
            continue
        ref = owners.get(item.get("uuid"))
        xy = [position["x"], position["y"]]
        if ref in moves:
            change = moves[ref]
            xy = transform(xy, change["new_native_pose"], change["old_native_pose"])
        item["pos"] = {"x": round(xy[0], 6), "y": round(xy[1], 6)}
    result["items"] = sorted(result.get("items", []), key=lambda item: json.dumps(item, sort_keys=True))
    return json.dumps(result, sort_keys=True)


def native_rules(owners, moves, errors):
    erc, source_erc = read(REPORTS / "erc.json"), read(REPORTS / "source-erc.json")
    violations = [v for sheet in erc["sheets"] for v in sheet["violations"]]
    source_violations = [v for sheet in source_erc["sheets"] for v in sheet["violations"]]
    if violations or source_violations:
        errors.append("Native candidate/source ERC is not clean")

    def pins(path):
        root = ET.parse(path).getroot()
        return Counter((net.get("name"), tuple(sorted(pin.attrib.items())))
                       for net in root.findall("nets/net") for pin in net.findall("node"))

    require(pins(REPORTS / "handbell-netlist.xml") == pins(REPORTS / "source-netlist.xml"),
            "Fresh exported schematic connectivity differs")
    drc, baseline = read(REPORTS / "drc.json"), read(REPORTS / "source-drc.json")
    types = Counter(finding["type"] for finding in drc["violations"])
    inherited_silk = {finding["type"] for finding in baseline["violations"]} & SILK_TYPES
    forbidden = [finding for finding in drc["violations"]
                 if finding["type"] not in inherited_silk | {"hole_clearance"}
                 or (finding["type"] in inherited_silk and finding.get("severity") != "warning")
                 or finding.get("excluded") is True]
    if forbidden:
        errors.append("New/unpermitted copper, hole, mask, dangling, excluded or other physical DRC findings")
    holes = lambda report: Counter(normalize_finding(f, {}, {}) for f in report["violations"]
                                   if f["type"] == "hole_clearance")
    require(holes(drc) == holes(baseline) and types["hole_clearance"] == 4,
            "The four original USB hole-clearance findings must persist unchanged, never waived")
    require(all(f.get("severity") == "error" for f in drc["violations"] if f["type"] == "hole_clearance"),
            "Inherited USB errors were downgraded")
    require(len(drc["schematic_parity"]) == len(baseline["schematic_parity"]) == 46
            and Counter(normalize_finding(f, owners, moves) for f in drc["schematic_parity"]) ==
            Counter(normalize_finding(f, owners, {}) for f in baseline["schematic_parity"]),
            "The 46 original CLI parity findings differ beyond inverse-transformed declared pad poses")
    return {
        "erc_violations": violations, "source_erc_violations": source_violations,
        "physical_findings_by_type": dict(types),
        "physical_findings_by_severity": dict(Counter(f["severity"] for f in drc["violations"])),
        "forbidden_physical_findings": forbidden,
        "inherited_silk_warning_types": sorted(inherited_silk),
        "inherited_usb_hole_errors": [f for f in drc["violations"] if f["type"] == "hole_clearance"],
        "cli_parity_findings": len(drc["schematic_parity"]),
        "cli_parity_comparison": "Full finding multiset, only declared pad poses inverse-transformed",
        "baseline_unconnected_items": len(baseline["unconnected_items"]),
        "unconnected_items": len(drc["unconnected_items"]),
        "unconnected_findings": drc["unconnected_items"],
        "inherited_findings_are_release_blockers_not_waivers": True,
    }


def build_graph(pcb, package):
    """Physical primitives plus separately identified native filled-zone islands."""
    graph = CopperGraph(pcb, package / "handbell.kicad_pcb")
    if graph.board.GetAreaCount():
        require(package == HERE, "Native source unexpectedly contains zones")
        text, board = literal_board(package / "handbell.kicad_pcb")
        report = validate_zone_nodes(package, text, board)
        prefill = CopperGraph(pcb, package / BASELINE)
        expected = protection_plan(prefill, read(package / "routing-data.json"),
                                   read(package / "battery-contact-interface.json"))
        def canonical_protection(plan):
            value = copy.deepcopy(plan)
            for witness in value["private_pickoffs_before"]:
                witness["joins_cut_wholly_inside_terminal"] = sorted(
                    ({"a_uuid": min(edge["a_uuid"], edge["b_uuid"]),
                      "b_uuid": max(edge["a_uuid"], edge["b_uuid"]), "layer": edge["layer"]}
                     for edge in witness["joins_cut_wholly_inside_terminal"]),
                    key=lambda edge: (edge["layer"], edge["a_uuid"], edge["b_uuid"]))
            return value
        require(canonical_protection(report["protection"]) == canonical_protection(expected),
                "Zone protection does not cover the exact prefill private paths/annuli")
        validate_filled_graph(graph, report, read(package / "placement-manifest.json"))
    require(len(graph.pads) == 325, "Native pad UUID inventory lost a physical item")
    return graph


def net_tie_screen(graph, errors):
    """Keep logical schematic nets separate at the explicit CHG_EN0 component."""
    pcb = graph.pcb
    footprint = next(f for f in graph.board.GetFootprints() if f.GetReference() == "CHG_EN0")
    graphics = [g for g in footprint.GraphicalItems() if g.IsOnLayer(pcb.F_Cu)]
    require(len(graphics) == 1, "Expected the one retained CHG_EN0 native copper bridge")
    graphic = graphics[0]
    shape = graphic.GetEffectiveShape(pcb.F_Cu)
    lands = [graph.pad_uuid("CHG_EN0", pin) for pin in ("1", "2")]
    require(all(shape.Collide(graph.pads[uid].GetEffectiveShape(pcb.F_Cu), 0) for uid in lands),
            "CHG_EN0 graphic does not actually touch both declared jumper lands")
    conflicts = []
    for uid, item in graph.items.items():
        if uid in lands or not item.IsOnLayer(pcb.F_Cu) or not shape.Collide(item.GetEffectiveShape(pcb.F_Cu), 0):
            continue
        overlap = native_polygon(pcb, item, pcb.F_Cu)
        overlap.BooleanIntersection(native_polygon(pcb, graphic, pcb.F_Cu))
        for land in lands:
            if item.GetNetname() == graph.pads[land].GetNetname():
                overlap.BooleanSubtract(native_polygon(pcb, graph.pads[land], pcb.F_Cu, outside=False))
        if not overlap.IsEmpty():
            conflicts.append(uid)
    if conflicts:
        errors.append("Copper touches CHG_EN0 bridge outside its own declared same-net terminal")
    return {"reference": "CHG_EN0", "graphic_uuid": graphic.m_Uuid.AsString(),
            "actual_shape_touches_both_lands": True, "lands": [graph.describe_pad(uid) for uid in lands],
            "nets": [graph.pads[uid].GetNetname() for uid in lands], "unexpected_contacts": conflicts,
            "semantics": "Intentional net-tie component; logical net islands remain separate across its internal bridge"}


def connectivity_report(before, after, data, errors):
    previous, current = before.nets(), after.nets()
    old_nets, new_nets = {n["net"]: n for n in previous}, {n["net"]: n for n in current}
    require(old_nets.keys() == new_nets.keys(), "Native net inventory changed")
    regressions = []
    for net in previous:
        for island in net["islands"]:
            ids = sorted(pad["uuid"] for pad in island)
            for index, a in enumerate(ids):
                for b in ids[index+1:]:
                    if not after.connected(a, b):
                        regressions.append({"net": net["net"], "from": after.describe_pad(a), "to": after.describe_pad(b)})
    if regressions:
        errors.append(f"{len(regressions)} source-connected physical-pad pairs regressed; no net/regression policy waiver")
    pairs = []
    for intent in data["connections"]:
        a, b = intent["from_uuid"], intent["to_uuid"]
        require(after.pads[a].GetNetname() == after.pads[b].GetNetname() == intent["net"],
                "Route intent net differs from native physical pads")
        connected = after.connected(a, b)
        if intent["status"].startswith("routed") and not connected:
            errors.append("Claimed route is not shape-connected: " + intent["from"] + " -> " + intent["to"])
        pairs.append({"from": intent["from"], "to": intent["to"], "net": intent["net"],
                      "declared_status": intent["status"], "before_connected": before.connected(a, b),
                      "after_connected": connected, "native_shape_path": after.path(a, b) if connected else []})
    floats = after.floating_copper()
    if floats:
        errors.append(f"{len(floats)} floating/unassigned copper items have no connected physical pad")
    if after.shorts:
        errors.append("Native effective copper shapes short different nets")
    transitions = [
        {"net": net["net"], "before_status": old_nets[net["net"]]["status"], "after_status": net["status"],
         "before_islands": len(old_nets[net["net"]]["islands"]), "after_islands": len(net["islands"])}
        for net in current
    ]
    minimum_joins = sum(len(n["islands"])-1 for n in current)
    if after.zone_islands and minimum_joins != int(after.board.GetConnectivity().GetUnconnectedCount(False)):
        errors.append("Filled-island physical graph and native connectivity-engine unconnected counts differ")
    return {"source_native_net_islands": previous, "candidate_native_net_islands": current,
            "net_transitions": transitions, "regressed_physical_pad_pairs": regressions,
            "declared_endpoint_checks": pairs, "floating_copper_uuids": floats, "native_shape_shorts": after.shorts,
            "residual_open_nodes": [n for n in current if len(n["islands"]) > 1],
            "minimum_remaining_logical_island_joins": minimum_joins,
            "filled_zone_islands": after.zone_islands,
            "method": "Actual per-layer effective shapes, plated barrels and individual filled-zone islands with holes; no parent-zone UUID, outline, route group or ratsnest joins"}


def power_topology(before, after, errors):
    paths = []

    def witness(a_ref, a_pin, b_ref, b_pin, all_front=False):
        a, b = after.pad_uuid(a_ref, a_pin), after.pad_uuid(b_ref, b_pin)
        require(after.pads[a].GetNetname() == after.pads[b].GetNetname(), "Required power pair has different nets")
        layer = after.pcb.F_Cu if all_front else None
        old_path, new_path = before.path(a, b, layer), after.path(a, b, layer)
        if not new_path:
            errors.append(f"Mandatory {'all-F ' if all_front else ''}power path missing: {a_ref}.{a_pin} -> {b_ref}.{b_pin}")
        paths.append({"from": f"{a_ref}.{a_pin}", "to": f"{b_ref}.{b_pin}",
                      "net": after.pads[a].GetNetname(), "all_F_required": all_front,
                      "before_path": old_path, "after_path": new_path})

    for cap in ("C27", "C28"):
        witness("U5", "6", cap, "1", True)
        witness("U5", "4", cap, "2", True)
    witness("U5", "5", "L1", "P$2", True)
    for args in (
        ("U6", "3", "Q5", "B1"), ("U6", "2", "Q5", "B2"),
        ("R28", "1", "U6", "3"), ("R28", "2", "U6", "4"),
        ("R29", "1", "Q5", "B2"), ("R29", "2", "Q5", "A2"),
        ("Q1", "3", "C26", "1"), ("Q3", "2", "Q1", "2"),
    ):
        witness(*args)
    pickoffs = []
    for a, b in (("R26", "R27"), ("R24", "C28")):
        require(after.pads[after.pad_uuid(a, "2")].GetNetname() == "GND"
                and after.pads[after.pad_uuid(b, "2")].GetNetname() == "GND", "Quiet pickoff must remain on GND")
        result = after.pickoff(a, "2", b, "2")
        if not result["independent_until_terminal"]:
            errors.append(f"{a}.2 merges with another GND land before actual {b}.2 terminal copper")
        pickoffs.append({"before": before.pickoff(a, "2", b, "2"), "after": result})
    return {"mandatory_power_paths": paths, "terminal_cut_pickoffs": pickoffs,
            "source_local_supply_clock_preservation": "Every source-connected physical-pad pair checked, on every net",
            "limitations": "Shape paths prove contacts, not short loop area, impedance, exposed width, current or fault ratings"}


def service_contact_screen(before, after, errors):
    pcb = after.pcb
    marks = lambda graph: {mark.GetText(): mark for mark in graph.board.GetDrawings()
                           if isinstance(mark, pcb.PCB_TEXT) and mark.GetLayer() == pcb.B_SilkS}
    old_marks, new_marks = marks(before), marks(after)
    require(old_marks.keys() == new_marks.keys() == LABELS.keys(), "Expected seven unchanged B-side service labels")
    rear = {uid: item for uid, item in after.items.items() if item.IsOnLayer(pcb.B_Cu)}
    labels = []
    for text, mark in sorted(new_marks.items()):
        require(mark.IsMirrored(), "Rear service label is not mirrored")
        shape = mark.GetEffectiveTextShape()
        bounds = [pcb.ToMM(v)-100 for v in bbox(shape)]
        old_bounds = [pcb.ToMM(v)-100 for v in bbox(old_marks[text].GetEffectiveTextShape())]
        require(max(abs(a-b) for a, b in zip(bounds, old_bounds)) < TOL, "Source native glyph bounds changed")
        x, y, width, height = LABELS[text]
        position = mark.GetPosition()
        require(math.dist([pcb.ToMM(position.x)-100, pcb.ToMM(position.y)-100], [x, y]) < TOL,
                "Service label centre changed")
        if width is None:
            require(abs(pcb.ToMM(mark.GetTextHeight())-1) < TOL, "Chemistry text must remain 1 mm")
        reserve = [bounds[0]-.2, bounds[1]-.2, bounds[2]+.2, bounds[3]+.2]
        if width is not None:
            box = [x-width/2, y-height/2, x+width/2, y+height/2]
            require(bounds[0] >= box[0]-TOL and bounds[1] >= box[1]-TOL
                    and bounds[2] <= box[2]+TOL and bounds[3] <= box[3]+TOL,
                    "Glyph exceeds full mechanical reservation: " + text)
            reserve = [min(reserve[0], box[0]), min(reserve[1], box[1]),
                       max(reserve[2], box[2]), max(reserve[3], box[3])]
        rect = rectangle(pcb, [v+100 for v in reserve])
        rect_hits = [uid for uid, item in rear.items() if rect.Collide(item.GetEffectiveShape(pcb.B_Cu), 0)]
        glyph_hits = [uid for uid, item in rear.items()
                      if shape.Collide(item.GetEffectiveShape(pcb.B_Cu), pcb.FromMM(.25))]
        if rect_hits or glyph_hits:
            errors.append("Rear copper enters full service rectangle/glyph clearance: " + text)
        labels.append({"text": text, "native_glyph_bounds_xy_mm": bounds,
                       "full_service_rectangle_xy_mm": reserve, "rectangle_conflicts": rect_hits,
                       "glyph_clearance_mm": .25, "glyph_conflicts": glyph_hits})
    contact = read(HERE / "battery-contact-interface.json")
    require({c["reference"] for c in contact["contacts"]} == {"BT1", "BT2"}, "Actual contact inventory changed")
    regions, conflicts = [], []
    primitives = contact["right_contact_original_primitives"]
    for ref, sign in (("BT1", 1), ("BT2", -1)):
        lands = [uid for uid, p in after.pads.items() if p.GetParentFootprint().GetReference() == ref]
        nets = {after.pads[uid].GetNetname() for uid in lands}
        require(len(nets) == 1 and nets == ({"VBAT"} if ref == "BT1" else {"/CELL_NEG"}),
                "Actual raw contact net changed")
        net = next(iter(nets))
        for index, item in enumerate([*primitives["base_tabs"], primitives["under_cell_base"]]):
            xmin, xmax = sorted((sign*item["x_min"], sign*item["x_max"]))
            bounds = [xmin, -item["y_width"]/2, xmax, item["y_width"]/2]
            regions.append((f"{ref}.base-{index}", net, rectangle(pcb, [v+100 for v in bounds]), bounds))
        for uid in lands:
            regions.append((f"{ref}.native-pad-{uid}", net, native_polygon(pcb, after.pads[uid], pcb.B_Cu), None))
    for name, net, polygon, bounds in regions:
        for uid, item in rear.items():
            if item.GetNetname() != net and polygon.Collide(item.GetEffectiveShape(pcb.B_Cu), pcb.FromMM(.2)):
                conflicts.append({"region": name, "uuid": uid, "foreign_net": item.GetNetname()})
    if conflicts:
        errors.append("Foreign B copper/vias enter actual raw-contact lands or conductive base projection")
    lane = rectangle(pcb, [98.7, 93, 101.3, 107])
    thermal = native_polygon(pcb, after.pads[after.pad_uuid("IC1", "P$1")], pcb.F_Cu, outside=False)
    lane_hits, local_thermal = [], []
    for uid, item in rear.items():
        if item.GetNetname() != "GND" or not lane.Collide(item.GetEffectiveShape(pcb.B_Cu), 0):
            continue
        remainder = native_polygon(pcb, item, pcb.B_Cu)
        remainder.BooleanSubtract(thermal)
        if remainder.IsEmpty():
            local_thermal.append(uid)
        else:
            lane_hits.append(uid)
    if lane_hits:
        errors.append("GND copper enters central B neck outside the actual IC1 thermal-land projection")
    return {"labels": labels, "glyph_bounds_basis": "Native source PCB, not mutable source reports",
            "contact_clearance_mm": .2, "foreign_contact_conflicts": conflicts,
            "contact_regions": [{"id": name, "net": net, "base_bounds_xy_mm": bounds}
                                for name, net, _, bounds in regions],
            "central_B_lane_bounds_xy_mm": [-1.3, -7, 1.3, 7],
            "central_B_lane_GND_conflicts": lane_hits, "local_IC1_thermal_items": local_thermal,
            "central_lane_policy": "No shared return, irrespective of width/group; only native local thermal footprint projection",
            "mechanical_visibility": "Not approved; full mechanical assembly/service rebind remains mandatory"}


def corners(component):
    angle = math.radians(component["rotation_deg"])
    return [(component["x_mm"] + x*math.cos(angle) - y*math.sin(angle),
             component["y_mm"] + x*math.sin(angle) + y*math.cos(angle))
            for x, y in ((-component["width_mm"]/2, -component["depth_mm"]/2),
                         (component["width_mm"]/2, -component["depth_mm"]/2),
                         (component["width_mm"]/2, component["depth_mm"]/2),
                         (-component["width_mm"]/2, component["depth_mm"]/2))]


def segment_distance(point, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    fraction = min(1, max(0, ((point[0]-a[0])*dx+(point[1]-a[1])*dy)/(dx*dx+dy*dy))) if dx or dy else 0
    return math.dist(point, [a[0]+fraction*dx, a[1]+fraction*dy])


def polygon_distance(point, polygon):
    inside = False
    edges = list(zip(polygon, polygon[1:]+polygon[:1]))
    for a, b in edges:
        if (a[1] > point[1]) != (b[1] > point[1]) and point[0] < (b[0]-a[0])*(point[1]-a[1])/(b[1]-a[1])+a[0]:
            inside = not inside
    return 0 if inside else min(segment_distance(point, a, b) for a, b in edges)


def outline_contains(polygon, outline):
    if any(polygon_distance(point, outline) > TOL for point in polygon):
        return False
    cross = lambda a, b, p: (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
    for a, b in zip(polygon, polygon[1:]+polygon[:1]):
        for c, d in zip(outline, outline[1:]+outline[:1]):
            if cross(a, b, c)*cross(a, b, d) < -TOL*TOL and cross(c, d, a)*cross(c, d, b) < -TOL*TOL:
                return False
    return True


def overlaps(components):
    result = set()
    for index, a in enumerate(components):
        for b in components[index+1:]:
            if min(a["z_max_mm"], b["z_max_mm"])-max(a["z_min_mm"], b["z_min_mm"]) <= TOL:
                continue
            ac, bc = corners(a), corners(b)
            axes = []
            for component in (a, b):
                angle = math.radians(component["rotation_deg"])
                axes.extend(((math.cos(angle), math.sin(angle)), (-math.sin(angle), math.cos(angle))))
            for axis in axes:
                ap = [p[0]*axis[0]+p[1]*axis[1] for p in ac]
                bp = [p[0]*axis[0]+p[1]*axis[1] for p in bc]
                if min(max(ap), max(bp))-max(min(ap), min(bp)) <= TOL:
                    break
            else:
                result.add(tuple(sorted((a["reference"], b["reference"]))))
    return result


def placement_screen(changed, errors):
    source, current = read(SOURCE / "placement-manifest.json"), read(HERE / "placement-manifest.json")
    old, new = overlaps(source["components"]), overlaps(current["components"])
    introduced = sorted(new-old)
    if introduced:
        errors.append("New full-height same-Z component proxy SAT overlaps")
    outside = lambda manifest: {c["reference"] for c in manifest["components"]
                                if not outline_contains(corners(c), manifest["board"]["outline_common_xy_mm"])}
    old_outside, new_outside = outside(source), outside(current)
    forbidden = (new_outside-old_outside) | (new_outside & set(changed))
    if forbidden:
        errors.append("New/moved full component proxy extends beyond the fixed outline")
    bands = ((current["speaker_front_z_mm"], current["speaker_basket_rear_z_mm"],
              current["speaker_dimensions_mm"]["overall_diameter"]/2),
             (current["speaker_basket_rear_z_mm"], current["speaker_magnet_rear_z_mm"],
              current["speaker_dimensions_mm"]["magnet_diameter"]/2))
    clearances = []
    for component in current["components"]:
        for zmin, zmax, radius in bands:
            if component["side"] != "F" or min(component["z_max_mm"], zmax)-max(component["z_min_mm"], zmin) <= TOL:
                continue
            clearance = polygon_distance((0, 0), corners(component))-radius
            clearances.append({"reference": component["reference"], "speaker_band_z_mm": [zmin, zmax],
                               "radial_clearance_mm": clearance})
            if clearance < current["speaker_screen"]["radial_planning_margin_mm"]-TOL:
                errors.append("Full component proxy violates stepped speaker reserve: " + component["reference"])
    inductor = next(c for c in current["components"] if c["reference"] == "L1")
    gap = inductor["z_min_mm"]-current["speaker_screen"]["yoke_top_z_mm"]
    require(inductor["height_mm"] == 5 and gap >= .7-TOL, "Full-height L1/yoke gap reduced")
    return {"new_proxy_overlap_pairs": introduced, "inherited_proxy_overlap_pairs": sorted(new & old),
            "new_or_moved_outside_outline": sorted(forbidden),
            "inherited_outside_outline_proxies": sorted(new_outside & old_outside),
            "conservative_speaker_clearances": clearances, "L1_yoke_axial_gap_mm": gap,
            "method": "Oriented XY SAT with actual Z intervals, outline crossings and conservative stepped speaker",
            "mechanical_rebind_required": True,
            "limitations": "Full-size screening proxies, not part tolerance, loaded contacts, service visibility or assembled fit"}


def markdown(report):
    rules = report.get("native_rules", {})
    graph = report.get("connectivity", {})
    lines = ["# Printed-bell quotation-candidate check", "", "**" + report["status"] + "**", "",
             "Not a quotation/fabrication release, functional/safety qualification or mechanical-fit approval.", "",
             f"- Native tracks / vias: {report.get('tracks', 'not evaluated')} / {report.get('vias', 'not evaluated')}.",
             f"- Native unconnected items: {rules.get('baseline_unconnected_items', 'not evaluated')} source -> "
             f"{rules.get('unconnected_items', 'not evaluated')} candidate.",
             f"- ERC findings: {len(rules['erc_violations']) if 'erc_violations' in rules else 'not evaluated'}.",
             f"- Physical DRC types: `{json.dumps(rules.get('physical_findings_by_type', {}), sort_keys=True)}`.",
             f"- CLI parity findings: {rules.get('cli_parity_findings', 'not evaluated')} (not waived).",
             f"- Source-connected pair regressions: {len(graph.get('regressed_physical_pad_pairs', [])) if graph else 'not evaluated'}.",
             "- Exact hashes, native findings, pad islands and endpoint witnesses are in completion-review.json.", "",
             "## Input hashes", ""]
    lines.extend(f"- `{name}`: `{digest}`" for name, digest in report.get("hashes", {}).items())
    lines.extend(["", "## Residual native net islands", "", "| Net | Source islands | Candidate islands | Status |",
                  "|---|---:|---:|---|"])
    for item in graph.get("net_transitions", []):
        if item["after_islands"] > 1 or item["before_islands"] != item["after_islands"]:
            lines.append(f"| {item['net']} | {item['before_islands']} | {item['after_islands']} | {item['after_status']} |")
    lines.extend(["", "Physical pad UUIDs for every open island are retained in the JSON, not replaced with zero claims.",
                  "", "## Failed checks", ""])
    lines.extend("- " + error for error in report["errors"])
    if not report["errors"]:
        lines.append("No failure of the implemented screens; this is still an incomplete/blocked engineering candidate.")
    lines.extend(["", "## Mandatory remaining gates", ""])
    lines.extend("- " + gate for gate in report["release_blockers"])
    lines.extend(["", "Native exports: [schematic](handbell-schematic.pdf), [front](front-native.pdf), "
                  "[mirrored rear](rear-native.pdf), [front SVG](front-native.svg), [rear SVG](rear-native.svg).", ""])
    return "\n".join(lines)


def check():
    geometry, board, owners, pad_ids = validate_geometry()
    data = validate_route_data(board, pad_ids)
    inputs, cache = validate_cache()
    errors = []
    rules = native_rules(owners, geometry["changed_footprints"], errors)
    pcb, api_identity = native_api()
    before, after = build_graph(pcb, SOURCE), build_graph(pcb, HERE)
    source_count = int(before.board.GetConnectivity().GetUnconnectedCount(False))
    current_count = int(after.board.GetConnectivity().GetUnconnectedCount(False))
    if source_count != rules["baseline_unconnected_items"] or current_count != rules["unconnected_items"]:
        errors.append("Native connectivity-engine and DRC unconnected counts differ")
    ties = {"source": net_tie_screen(before, errors), "candidate": net_tie_screen(after, errors)}
    graph = connectivity_report(before, after, data, errors)
    power = power_topology(before, after, errors)
    service = service_contact_screen(before, after, errors)
    proxies = placement_screen(geometry["changed_footprints"], errors)
    require(input_bindings() == inputs, "Explicit design/checker inputs changed during native shape checks")
    require(cache["reports"] == {name: sha(REPORTS / name) for name in NATIVE_REPORTS},
            "Native evidence changed during checks")
    incomplete = bool(current_count or graph["residual_open_nodes"])
    status = ("FAILED candidate checks" if errors else
              "INCOMPLETE routing; quotation/fabrication BLOCKED" if incomplete else
              "ROUTING CONNECTED; quotation/fabrication BLOCKED by inherited findings and mechanical rebind")
    return {
        "schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(), "status": status,
        "exit_code": 1 if errors else 2, "routing_complete": not incomplete,
        "quotation_ready": False, "fabrication_ready": False, "errors": errors,
        "kicad_cli": cache["tool"], "native_api": api_identity,
        "hashes": {name: sha(HERE / name) for name in (
            "handbell.kicad_pcb", "handbell.kicad_sch", "handbell.kicad_pro",
            "placement-manifest.json", "battery-contact-interface.json", "routing-data.json", "completion-build.json")},
        "explicit_input_hashes": inputs, "explicit_native_report_hashes": cache["reports"],
        "native_binding_sha256": sha(REPORTS / "native-input-bindings.json"),
        "tracks": len(data["tracks"]), "vias": len(data["vias"]),
        "zones": len({island["zone_uuid"] for island in after.zone_islands}),
        "filled_zone_islands": len(after.zone_islands),
        "pour_only_rule_areas": sum(zone.GetIsRuleArea() for zone in after.board.Zones()),
        "geometry": geometry, "native_rules": rules, "connectivity": graph, "intentional_net_tie": ties,
        "native_engine_unconnected_items": {"source": source_count, "candidate": current_count},
        "power_topology": power, "service_contact_screen": service, "placement_proxy_screen": proxies,
        "mechanical_rebind_required": True,
        "release_blockers": [
            "All residual native net islands/unconnected items must be routed; every source-connected pair must remain connected.",
            "Four original USB hole-clearance errors and 46 original CLI parity findings persist; none is a waiver.",
            "Inherited silk warnings remain visible engineering review work.",
            "Full mechanical assembly and service-visibility rebind to this exact PCB/manifest is always required.",
            "No current, thermal, noise, charging/fault, contact insulation/retention or child-use qualification.",
            "No supplier upload, purchase, fabrication/assembly order or operational approval.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-native", action="store_true", help="Refresh explicit KiCad ERC/DRC/netlist/PDF/SVG evidence")
    args = parser.parse_args()
    try:
        if args.run_native:
            run_native()
        report = check()
    except (ValueError, KeyError, TypeError, OSError, RuntimeError, AttributeError,
            subprocess.SubprocessError, ET.ParseError, ImportError) as error:
        report = {
            "schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(),
            "status": "FAILED or STALE candidate evidence; completion not evaluated",
            "exit_code": 1, "routing_complete": None, "quotation_ready": False, "fabrication_ready": False,
            "errors": [sanitize(str(error))], "mechanical_rebind_required": True,
            "release_blockers": ["Resolve failed/stale evidence, rerun --run-native, then all native/physical/mechanical gates.",
                                 "No prior approval or zero-unconnected claim transfers to this candidate."],
        }
    write(REPORTS / "completion-review.json", report)
    write(REPORTS / "completion-review.md", markdown(report))
    print(json.dumps({"status": report["status"], "exit_code": report["exit_code"],
                      "tracks": report.get("tracks"), "vias": report.get("vias"),
                      "unconnected_items": report.get("native_rules", {}).get("unconnected_items"),
                      "errors": report["errors"]}, indent=2))
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
