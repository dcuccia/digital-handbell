# SPDX-License-Identifier: MIT
"""Guarded completion candidate; explicit source inputs, no old writer invocation."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = HERE.parent / "printed-bell-power-rework"
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
import route_printed_bell_power_rework as power
from kicad_sexpr import apply_edits, load, loads

PINNED = {
    "handbell.kicad_pcb": "6132f8d3ec508f8ae023888052cc2a1f8b2c24f2c38d9d12dca3234ba887dcc1",
    "placement-manifest.json": "60e394c41bcfd7734b41c7713100360253164381f0217eed325386bd49977799",
}
STATIC = ("handbell.kicad_sch", "handbell.kicad_pro", "battery-contact-interface.json",
          "fp-lib-table", "sym-lib-table", "Handbell.kicad_sym", "T8.kicad_sym",
          "source-evidence.json", "design-input-snapshot.json", "LICENSE.txt")
POSES = {
    "Q1": (-6.4, 8, 90),
    "Q3": (-2.5, 7.45, 0),
    "L0": (-2, -11.23, 0),
    "R7": (-3, 10, 0),
    "U6": (-10.8, 6.6, 0),
    "C30": (-8.9, 7.1, 270),
    "R25": (-7.5, 5.3, 0),
    "R28": (-11.6, 8.55, 0),
    "U1": (6.301448, -3.159246, 270),
    "C10": (8.6, -2.2, 0),
    "R5": (6.901181, -6.701464, 90),
    "R9": (8.105371, .642334, 180),
    "R10": (8.109565, -.559133, 180),
}
REASONS = {
    "Q1": "Colocate with the cell selector and boost; source faces Q3 and drain faces C26, avoiding a board-perimeter 2A detour.",
    "Q3": "Bring the corrected selector drain close to the positive-contact upper exit; preserve every custom land and shorten VBAT/VHI.",
    "L0": "Move the indicator into the vacated selector envelope; clear compact power and local protector decoupling.",
    "R7": "Clear the source-selector body and retain this control resistor beside the relocated switch.",
    "U6": "Move right/up to expose COUT beyond the outside Q5 source-via barrier without narrowing source copper or entering NC copper.",
    "C30": "Face the adjacent U6 supply/VSS pins with vertical local decoupling, leaving VM's upper escape unobstructed.",
    "R25": "Keep the protector input filter above its local capacitor instead of blocking the capacitor or switched-power corridor.",
    "R28": "Move the bias-only gate discharge resistor beside U6 so DOUT need not cross the outside Q5 source vias.",
    "U1": "Reverse the flash banks and shift 0.2mm to make all six QSPI signals planar on F despite the B contact lands; retain the maximum UX envelope.",
    "C10": "Keep flash VCC bypass beside the reoriented VCC land rather than across the signal fanout.",
    "R5": "Clear the outer CS lane while retaining the actual CS pullup beside the flash.",
    "R9": "Shift the USB series pair together to clear the rotated flash courtyard without changing pair spacing or values.",
    "R10": "Shift the USB series pair together to clear the rotated flash courtyard without changing pair spacing or values.",
}
_DLLS = []


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data, indent=2)+"\n", encoding="utf-8")


def native():
    folder = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin"
    _DLLS.append(os.add_dll_directory(str(folder)))
    sys.path.insert(0, str(folder / "Lib" / "site-packages"))
    import pcbnew
    require(pcbnew.GetBuildVersion() == "10.0.6", "KiCad 10.0.6 required")
    return pcbnew


def source_files():
    """Only actual design inputs and used library files; never ambient reports/preferences."""
    names = set(STATIC) | set(PINNED) | {"routing-data.json"}
    _, board = load(SOURCE / "handbell.kicad_pcb")
    _, table = load(SOURCE / "fp-lib-table")
    libraries = {item.value("name"): item.value("uri") for item in table.children("lib")}
    for footprint in board.children("footprint"):
        library, name = footprint.atoms()[1].split(":", 1)
        uri = libraries[library]
        require(uri.startswith("${KIPRJMOD}/libraries/"), "External footprint lookup refused")
        names.add(uri.replace("${KIPRJMOD}/", "")+"/"+name+".kicad_mod")
    names.update("notices/"+name for name in (
        "adafruit-5768-README.md", "adafruit-4438-README.md", "adafruit-4654-README.md"))
    return sorted(names)


def source_bindings():
    for name, digest in PINNED.items():
        require(sha(SOURCE / name) == digest, "Accepted source changed: "+name)
    return {name: sha(SOURCE / name) for name in source_files()}


def guard():
    state = HERE / "completion-build.json"
    if state.exists():
        previous = read(state)
        for name, digest in {**previous["protected_files"], **previous.get("interchange_bindings",{})}.items():
            require(sha(HERE / name) == digest, "Edited completion candidate; refusing overwrite: "+name)
    else:
        require(not (HERE / "handbell.kicad_pcb").exists(), "Existing unbound candidate refused")


def require_unfilled():
    if (HERE / "handbell.kicad_pcb").exists():
        _, board = load(HERE / "handbell.kicad_pcb")
        require(not board.children("zone"), "Filled candidate is immutable to routing operations; use a separately guarded new revision, not stale fills")


def save_state(bindings):
    names = set(STATIC) | {"handbell.kicad_pcb", "placement-manifest.json", "routing-data.json",
                          "reports/footprint-movements.json"}
    names.update(name for name in bindings if name.startswith(("libraries/", "notices/")))
    old_state = read(HERE/"completion-build.json") if (HERE/"completion-build.json").exists() else {}
    write(HERE / "completion-build.json", {
        "source_pcb_sha256": PINNED["handbell.kicad_pcb"],
        "source_manifest_sha256": PINNED["placement-manifest.json"],
        "source_inputs": bindings,
        "source_scope": "Explicit authoritative files and used local libraries; no PRL/locks/caches or report-folder snapshot",
        "generator_sha256": sha(__file__),
        "protected_files": {name: sha(HERE / name) for name in sorted(names)},
        "mechanical_rebind_required": True,
        "interchange_bindings": old_state.get("interchange_bindings",{}),
    })
    require(source_bindings() == bindings, "Source changed during operation")


def moved_source():
    text, board = load(SOURCE / "handbell.kicad_pcb")
    manifest = read(SOURCE / "placement-manifest.json")
    edits, moves = [], []
    for fp in board.children("footprint"):
        ref = fp.properties()["Reference"]
        if ref not in POSES:
            continue
        node = fp.child("at")
        old = list(map(float, node.atoms()[1:]))
        if len(old) == 2:
            old.append(0.)
        old[:2] = [v-100 for v in old[:2]]
        new = POSES[ref]
        edits.append((node.start, node.end, f"(at {new[0]+100:.6f} {new[1]+100:.6f} {new[2]:g})"))
        moves.append({"reference": ref, "old_native_pose": old, "new_native_pose": new, "rationale": REASONS[ref]})
        for component in manifest["components"]:
            if component["reference"] == ref:
                x, y = power.prep.rotate(component["x_mm"]-old[0], component["y_mm"]-old[1], new[2]-old[2])
                component.update(x_mm=new[0]+x, y_mm=new[1]+y, rotation_deg=-new[2],
                                 native_origin_common_xy_mm=list(new[:2]))
        for group in manifest["electrical_landmarks"].values():
            if ref in group:
                group[ref] = list(new)
    for kind in ("segment", "via"):
        edits.extend((node.start, node.end, "") for node in board.children(kind))
    manifest.update(status="Completion routing in progress; not quotation or fabrication release",
                    baseline_pcb_sha256=PINNED["handbell.kicad_pcb"],
                    source_baseline=str(SOURCE.relative_to(ROOT)),
                    mechanical_rebind_required=True,
                    routing_report="reports/completion-review.json")
    manifest["planning"] = {"scope": "Completion-candidate native/envelope screens; new poses require exact mechanical rebind",
                            "mechanical_fit_approval": False}
    return apply_edits(text, edits), manifest, moves


class Router(power.PowerRouter):
    def __init__(self, manifest, board):
        self.pads, self.holes = power.prep.read_pads(board)
        for fp in board.children("footprint"):
            for index, node in enumerate(fp.children("pad")):
                key = f'{fp.properties()["Reference"]}.{node.atoms()[1]}#{index}'
                pad = next((p for p in self.pads if p["id"] == key), None)
                if pad:
                    pad["uuid"] = node.value("uuid")
        self.lookup = {}
        for pad in self.pads:
            self.lookup.setdefault((pad["reference"], pad["number"]), []).append(pad)
        self.outline = manifest["board"]["outline_common_xy_mm"]
        self.metal = power.prep.contact_metal_reservations(read(HERE / "battery-contact-interface.json"))
        self.tracks, self.vias, self.results = [], [], []
        self.quiet, self.ignore_quiet, self.manual_records = [], None, []
        self.label_boxes = [[13.5, 10.3, 17.9, 11.7], [-17.9, 10.3, -13.5, 11.7],
                            [-6, 9.8, 6, 11.2]]
        self.label_boxes += [[-5.5, y-.7, 5.5, y+.7] for y in (-15.6, -14, -12.1, -10.5)]


def emit(text, manifest, moves, router, bindings):
    board = loads(text)
    additions = []
    for index, track in enumerate(router.tracks):
        token = str(uuid.uuid5(uuid.NAMESPACE_URL, "handbell/quote/track/"+str(index)))
        a, b = track["a"], track["b"]
        additions.append(f'(segment (start {a[0]+100:.6f} {a[1]+100:.6f}) '
                         f'(end {b[0]+100:.6f} {b[1]+100:.6f}) (width {track["width"]:g}) '
                         f'(layer "{track["layer"]}") (net {json.dumps(track["net"])}) (uuid "{token}"))')
    for index, via in enumerate(router.vias):
        token = str(uuid.uuid5(uuid.NAMESPACE_URL, "handbell/quote/via/"+str(index)))
        x, y = via["xy"]
        additions.append(f'(via (at {x+100:.6f} {y+100:.6f}) (size {via["diameter"]:g}) '
                         f'(drill {via["drill"]:g}) (layers "F.Cu" "B.Cu") '
                         f'(net {json.dumps(via["net"])}) (uuid "{token}"))')
    write(HERE / "handbell.kicad_pcb", apply_edits(text, [(board.end-1, board.end-1, "\n"+"\n".join(additions)+"\n")]))
    components = {item["reference"]:item for item in manifest["components"]}
    for adjustment in manifest.get("proxy_envelope_adjustments",{}).get("changes",[]):
        component = components[adjustment["reference"]]
        angle = math.radians(component["rotation_deg"])
        adjustment["rotation_deg"] = component["rotation_deg"]
        adjustment["local_depth_axis_board_xy_unit"] = [round(-math.sin(angle),12),round(math.cos(angle),12)]
    manifest["generated_pcb_sha256"] = sha(HERE / "handbell.kicad_pcb")
    write(HERE / "placement-manifest.json", manifest)
    write(HERE / "reports" / "footprint-movements.json", moves)
    write(HERE / "routing-data.json", {"tracks": router.tracks, "vias": router.vias,
                                     "connections": router.results, "quiet_paths": router.quiet})
    save_state(bindings)


def build_power():
    guard()
    require_unfilled()
    bindings = source_bindings()
    for name in source_files():
        if name in PINNED or name == "routing-data.json":
            continue
        (HERE / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE / name, HERE / name)
    text, manifest, moves = moved_source()
    router = Router(manifest, loads(text))
    prior = read(SOURCE / "routing-data.json")
    def removed(item):
        if item["net"].startswith("QSPI"):
            return True
        if item["net"] == "+3V3" and "a" in item and all(
                4.4 < point[0] < 6.2 and -6.15 < point[1] < -4.1 for point in (item["a"],item["b"])):
            return True
        if item["net"] in ("/PROT_BAT", "/PROT_VM", "/PROT_DOUT", "VHI"):
            return True
        if item["group"].startswith(("DOUT discharge raw source connection", "VSS local", "VSS deliberate",
                                     "Q5 main protected-return", "Q5 main return", "COUT low-current discharge",
                                     "cell positive to selector", "protector VBAT bias feed")):
            return True
        return False
    router.tracks = [copy.deepcopy(t) for t in prior["tracks"] if not removed(t)]
    router.vias = [copy.deepcopy(v) for v in prior["vias"] if not removed(v)]
    router.results = [copy.deepcopy(r) for r in prior["connections"]
                      if not any(r.get(endpoint, "").split(".")[0] in POSES for endpoint in ("from", "to"))]
    sense = router.pad("R26", "2")
    router.reserve_quiet(sense["center"], router.pad("R27", "2"), "quiet R26 shunt pickoff")
    for track in router.tracks:
        if track["group"] == "quiet R24 capacitor-ground reference":
            router.quiet.append({**track, "terminal": router.pad("C28", "2")})
    p = lambda r, n: router.pad(r, n)["center"]
    qspi = [
        ("56","1",[[4.2,-2.6],[4.2,-4.25],[3.8,-4.65],[3.8,-8.65],[6.7,-8.65],[6.7,-7.86],[7.5,-7.86],[7.5,-4.409246]]),
        ("55","2",[[4.6,-2.2],[4.6,-5.5],[6.551448,-5.5]]),
        ("54","3",[[5,-1.8],[5,-5.05],[6.051448,-5.05]]),
        ("53","5",[[5.551448,-1.4]]),
        ("52","6",[[6.051448,-1]]),
        ("51","7",[[4.2,-.6],[4.2,.205],[6.95,.205],[6.95,-1.25],[6.551448,-1.25]]),
    ]
    for mcu_pin,flash_pin,corners in qspi:
        net=router.pad("IC1",mcu_pin)["net"]
        router.wire([p("IC1",mcu_pin),*corners,p("U1",flash_pin)],net,.1778,"QSPI planar bank fanout")
        router.mark_pair("IC1",mcu_pin,"U1",flash_pin,"QSPI all-F completion")
    router.wire([p("R5","1"),[7.5,p("R5","1")[1]]],"QSPI_CS",.1778,"QSPI CS pullup")
    router.mark_pair("R5","1","U1","1","QSPI CS pullup completion")
    router.wire([p("U1","8"),p("C10","1")],"+3V3",.25,"QSPI local supply bypass")
    router.mark_pair("U1","8","C10","1","QSPI local bypass")
    router.add_via([-16.6, 7.2], "/PROT_FET_RETURN", group="second common return off-pad transition")
    router.wire([[-16.6, 8.1], [-16.6, 7.2]], "/PROT_FET_RETURN", .6, "parallel common return barrel pair", "B.Cu")
    router.wire([[-16.6, 7.2], [-16.6,8.5], p("R27", "1")], "/PROT_FET_RETURN", .6, "second common return F branch")
    router.wire([p("R29", "2"), [-16.6, 8.1]], "/PROT_FET_RETURN", .1778, "local COUT discharge source")
    router.wire([p("Q5", "B2"), [-14.400825, 5.45], [-17.6, 5.45], [-17.6, 6.2]],
                "/PROT_COUT", .1778, "COUT outside source row")
    router.add_via([-17.6, 6.2], "/PROT_COUT", group="COUT off-pad escape")
    router.add_via([-12.5, 6.09], "/PROT_COUT", group="COUT off-pad escape")
    router.wire([[-17.6, 6.2], [-17.6, 6.05], [-12.5, 6.05], [-12.5, 6.09]],
                "/PROT_COUT", .1778, "bias-only COUT between raw base and source bus", "B.Cu")
    router.wire([[-12.5, 6.09], [-12.2, 6.09], [-12.2, 6.6], p("U6", "2")],
                "/PROT_COUT", .1778, "COUT exposed controller approach")
    router.mark_pair("Q5", "B2", "U6", "2", "protector gate completion")
    router.wire([p("Q5", "B1"), [-14.400825, 8.5], [-12.108, 8.5], p("R28", "1")],
                "/PROT_DOUT", .1778, "DOUT direct outside-source connection")
    router.wire([[-12.108, 8.5], [-12.108, 7.1], p("U6", "3")],
                "/PROT_DOUT", .1778, "DOUT controller connection")
    router.mark_pair("Q5", "B1", "U6", "3", "DOUT completion")
    router.mark_pair("R28", "1", "U6", "3", "DOUT bias connection")
    for xy in ([-1.4,7.45],[-1.4,8.35]):
        router.add_via(xy,"VBAT",group="parallel selector drain off-pad transition")
    router.wire([p("Q3","3"),[-1.7,7.45]],"VBAT",.6,"bounded selector drain package escape")
    router.wire([[-1.7,7.45],[-1.4,7.45],[-1.4,8.35]],"VBAT",1.2,"selector drain F landing")
    router.wire([[-1.4,7.45],[-1.4,8.35]],"VBAT",1.5,"parallel selector entry B connection","B.Cu")
    router.wire([p("BT1","1"),[3.685,5.4],[-1.4,7.45]],"VBAT",1.5,
                "broad positive feeder kept clear of the USB-supply exit","B.Cu")
    router.mark_pair("BT1","1","Q3","3","compact cell positive feeder")
    router.wire([p("Q3","2"),[-4.3,7.95]],"VHI",.3,"bounded selector source package escape")
    router.wire([[-4.3,7.95],p("Q1","2")],"VHI",1.0,"short selector-to-switch trunk")
    router.mark_pair("Q3","2","Q1","2","compact VHI trunk")
    router.wire([p("Q1","3"),[-7.4,9.3],p("C26","1")],"V+",1.2,"short all-F switched boost feeder")
    router.mark_pair("Q1","3","C26","1","compact full-width switched input")
    router.add_via([-8.9,8.7], "/CELL_NEG", group="raw VSS reference off-pad transition")
    router.wire([p("C30","2"),[-8.9,8.7]],"/CELL_NEG",.1778,"raw VSS reference F approach")
    router.wire([p("R25","1"),[-8.008,4.2],[-2.5,4.2],p("Q3","3")],
                "VBAT",.1778,"protector bias pickup above the switch and MCU perimeter")
    router.mark_pair("R25","1","Q3","3","protector filtered-input supply")
    for xy in ([0,-7.5],[0,-2.3],[0,2.3],[-4.9,6.0]):
        router.add_via(xy,"VHI",group="USB supply off-pad layer transition")
    router.wire([[0,-2.3],[2.3,-2.3],[2.3,2.3],[0,2.3]],"VHI",.8,
                "USB supply passage outside the unchanged MCU thermal land")
    router.wire([[-4.9,6.0],p("Q1","2")],"VHI",.8,"USB supply F approach to source switch")
    router.wire([p("D4","C"),[0,-7.5]],"VHI",.8,"USB diode off-pad entry")
    router.wire([[0,-7.5],[0,-2.3]],"VHI",.8,"USB supply central B entry","B.Cu")
    router.wire([[0,2.3],[-4.9,6.0]],"VHI",.8,"USB supply upper B exit","B.Cu")
    router.mark_pair("D4","C","Q1","2","complete USB diode supply branch")
    for args in (
        ("R28", "2", "U6", "4", "relocated DOUT discharge source branch", .1778, True),
        ("R29", "1", "Q5", "B2", "COUT discharge gate branch", .1778, True),
        ("U6", "5", "R25", "2", "protector filtered supply", .1778, True),
        ("U6", "5", "C30", "1", "protector bypass supply", .1778, True),
        ("U6", "4", "C30", "2", "protector raw-negative bypass", .1778, True),
        ("U6", "6", "R26", "1", "protector VM input", .1778, True),
    ):
        router.link(*args)
    path = router.search([-8.9,8.7], [-13.050825, 7.75048], "/CELL_NEG", .1778, False, 5, 140000, (1, 1))
    require(path, "Raw VSS reference must reach Source1 without protected-GND joins")
    router.add_path(path, "/CELL_NEG", .1778, "raw VSS reference B approach")
    router.mark_pair("U6", "4", "Q5", "C1", "intentional raw-negative VSS reference")
    emit(text, manifest, moves, router, bindings)
    print(json.dumps({"pcb_sha256": sha(HERE / "handbell.kicad_pcb"),
                      "tracks": len(router.tracks), "vias": len(router.vias)}, indent=2))


def export_dsn():
    guard()
    require_unfilled()
    pcb = native()
    board = pcb.LoadBoard(str(HERE / "handbell.kicad_pcb"))
    data = read(HERE / "routing-data.json")
    groups = {str(uuid.uuid5(uuid.NAMESPACE_URL, "handbell/quote/"+kind+"/"+str(index))): item["group"]
              for kind, items in (("track",data["tracks"]),("via",data["vias"]))
              for index,item in enumerate(items)}
    for track in board.GetTracks():
        group = groups[track.m_Uuid.AsString()]
        net = track.GetNetname()
        width = pcb.ToMM(track.GetWidth(pcb.F_Cu) if isinstance(track,pcb.PCB_VIA) else track.GetWidth())
        fixed = (net in ("GND","V+","VHI","VAMP","BOOST_SW","BOOST_FB","/PROT_FET_RETURN")
                 or net in ("VBAT","/CELL_NEG") and width >= .6
                 or group.startswith(("QSPI", "native fixed seed copper", "Q5 ", "COUT outside", "COUT off-pad", "bias-only COUT",
                                      "COUT exposed", "quiet ")))
        track.SetLocked(fixed)
    path = HERE / "routing" / "completion-input.dsn"
    path.parent.mkdir(exist_ok=True)
    require(pcb.ExportSpecctraDSN(board, str(path)), "Native DSN export failed")
    text = path.read_text().replace('(string_quote ")', "(string_quote quote)")
    header, body = text.split("\n", 1)
    require(header.startswith('(pcb "'), "Unexpected DSN document header")
    text = '(pcb "completion-input"\n'+body
    tree = loads(text)
    structure = tree.child("structure")
    manifest = read(HERE / "placement-manifest.json")
    router = Router(manifest, load(HERE / "handbell.kicad_pcb")[1])
    data = read(HERE / "routing-data.json")
    keepouts = []

    def reserve(bounds, layer):
        x0, y0, x1, y1 = bounds
        coords = " ".join(f"{1000*(x+100):.6f} {-1000*(y+100):.6f}"
                         for x, y in ((x0,y0), (x1,y0), (x1,y1), (x0,y1)))
        keepouts.append(f'(keepout "completion-reservation-{len(keepouts)}" (polygon {layer} 0 {coords}))')

    for metal in router.metal:
        x, y = metal["center"]
        w, h = metal["size"]
        reserve([x-w/2-.02, y-h/2-.02, x+w/2+.02, y+h/2+.02], "B.Cu")
    for bounds in router.label_boxes:
        reserve(bounds, "B.Cu")
    for quiet in data["quiet_paths"]:
        a, b = quiet["a"], quiet["b"]
        reserve([min(a[0],b[0])-.35, min(a[1],b[1])-.35,
                 max(a[0],b[0])+.35, max(a[1],b[1])+.35], quiet.get("layer", "F.Cu"))
    edits = [(structure.end-1, structure.end-1, "\n"+"\n".join(keepouts)+"\n")]
    network = tree.child("network")
    for netclass in network.children("class"):
        atoms = netclass.atoms()
        names = [net for net in atoms[2:] if net not in ("V+","GND")]
        rest = "\n".join(text[n.start:n.end] for n in netclass.children())
        rest = rest.replace("(width 200)", "(width 177.8)")
        edits.append((netclass.start, netclass.end,
                      "(class "+json.dumps(atoms[1])+" "+" ".join(map(json.dumps,names))+"\n"+rest+")"))
    edits.append((network.end-1, network.end-1,
                  '\n(class "SwitchedCellPower" "V+" (rule (width 1000) (clearance 205)))'
                  '\n(class "GroundFill" "GND" (rule (width 177.8) (clearance 205)))\n'))
    write(path, apply_edits(text, edits).replace("(string_quote quote)", '(string_quote ")'))
    shutil.copyfile(HERE / "handbell.kicad_pcb", HERE / "routing" / "power-seed.kicad_pcb")
    shutil.copyfile(HERE / "placement-manifest.json", HERE / "routing" / "power-seed-manifest.json")
    shutil.copyfile(HERE / "routing-data.json", HERE / "routing" / "power-seed-data.json")
    write(HERE / "routing" / "router-input-binding.json", {
        "pcb_sha256": sha(HERE / "handbell.kicad_pcb"), "dsn_sha256": sha(path),
        "manifest_sha256": sha(HERE / "placement-manifest.json"),
        "scope": "Local constrained routing; power/local loops/quiet paths/source fanouts locked; other signal copper may be rerouted; no upload",
        "keepout_count": len(keepouts),
        "fixed_seed_uuids": sorted(track.m_Uuid.AsString() for track in board.GetTracks() if track.IsLocked()),
        "requested_Vplus_body_width_mm": 1.0,
        "width_scope": "Alternate broad routing screen; not ampacity or copper-drop approval",
    })
    state = read(HERE/"completion-build.json")
    state["interchange_bindings"] = {"routing/"+name:sha(HERE/"routing"/name) for name in (
        "completion-input.dsn","power-seed.kicad_pcb","power-seed-manifest.json","power-seed-data.json","router-input-binding.json")}
    state["generator_sha256"] = sha(__file__)
    write(HERE/"completion-build.json",state)
    print(path)


def import_session():
    guard()
    require_unfilled()
    binding = read(HERE / "routing" / "router-input-binding.json")
    run = read(HERE / "routing" / "local-router-binding.json")
    require(run["dsn_sha256"] == sha(HERE / "routing" / "completion-input.dsn")
            and run["ses_sha256"] == sha(HERE / "routing" / "completion-output.ses")
            and run["jar_sha256"] == "9084a4888937a7f31f857ecc12aa7a37407f51160e4d2892dff9c9bb47ae3102",
            "SES does not match the recorded local routing run")
    seed = HERE / "routing" / "power-seed.kicad_pcb"
    require(sha(seed) == binding["pcb_sha256"]
            and sha(HERE / "routing" / "completion-input.dsn") == binding["dsn_sha256"],
            "Routed session belongs to a different seed")
    pcb = native()
    board = pcb.LoadBoard(str(seed))
    fixed_ids = set(binding["fixed_seed_uuids"])
    protected, seed_ids = [], set()
    for track in board.GetTracks():
        seed_ids.add(track.m_Uuid.AsString())
        if isinstance(track,pcb.PCB_VIA):
            xy = [pcb.ToMM(track.GetPosition().x)-100,pcb.ToMM(track.GetPosition().y)-100]
            row = {"xy":xy,"net":track.GetNetname(),"diameter":pcb.ToMM(track.GetWidth(pcb.F_Cu)),
                   "drill":pcb.ToMM(track.GetDrillValue())}
        else:
            a,b = ([pcb.ToMM(point.x)-100,pcb.ToMM(point.y)-100] for point in (track.GetStart(),track.GetEnd()))
            width = pcb.ToMM(track.GetWidth())
            row = {"a":a,"b":b,"net":track.GetNetname(),"layer":track.GetLayerName(),"width":width}
        track.SetLocked(track.m_Uuid.AsString() in fixed_ids)
        if track.m_Uuid.AsString() in fixed_ids:
            protected.append(row)
    require(len(protected) == len(fixed_ids) and protected, "Fixed seed UUID inventory mismatch")
    # SES deliberately omits fixed wires. Keep their original native geometry, not an inferred reroute.
    require(pcb.ImportSpecctraSES(board, str(HERE / "routing" / "completion-output.ses")), "SES import failed")
    text, old = load(seed)
    text = apply_edits(text, [(n.start,n.end,"") for kind in ("segment","via") for n in old.children(kind)])
    manifest = read(HERE/"routing"/"power-seed-manifest.json")
    require(sha(HERE/"routing"/"power-seed-manifest.json") == binding["manifest_sha256"],
            "Only the PCB hash may have changed since the exported placement")
    router = Router(manifest, loads(text))
    prior = read(HERE / "routing" / "power-seed-data.json")
    router.results, router.quiet = prior["connections"], prior["quiet_paths"]
    contained_rounding_stubs = []
    for track in board.GetTracks():
        if track.m_Uuid.AsString() in seed_ids:
            continue
        if isinstance(track, pcb.PCB_VIA):
            router.add_via([pcb.ToMM(track.GetPosition().x)-100, pcb.ToMM(track.GetPosition().y)-100],
                           track.GetNetname(), pcb.ToMM(track.GetWidth(pcb.F_Cu)), pcb.ToMM(track.GetDrillValue()),
                           "local constrained routing session")
        else:
            require(not isinstance(track, pcb.PCB_ARC), "Unexpected session arc needs native support")
            a = [pcb.ToMM(track.GetStart().x)-100, pcb.ToMM(track.GetStart().y)-100]
            b = [pcb.ToMM(track.GetEnd().x)-100, pcb.ToMM(track.GetEnd().y)-100]
            if any(
                    "a" in item and item["net"] == track.GetNetname()
                    and item["layer"] == track.GetLayerName()
                    and all(power.prep.point_segment_distance(point, item["a"], item["b"])
                            + .000001 < item["width"]/2
                            for point in (a, b)) for item in protected):
                contained_rounding_stubs.append({"a": a, "b": b, "net": track.GetNetname(),
                                                  "reason": "Entire interchange segment centerline lies inside one restored same-net fixed copper capsule"})
                continue
            router.add_segment(a, b,
                               track.GetNetname(), track.GetLayerName(), pcb.ToMM(track.GetWidth()),
                               "local constrained routing session")
    for row in protected:
        if "xy" in row:
            router.add_via(row["xy"],row["net"],row["diameter"],row["drill"],"native fixed seed copper")
        else:
            router.add_segment(row["a"],row["b"],row["net"],row["layer"],row["width"],"native fixed seed copper")
    emit(text, manifest, read(HERE / "reports" / "footprint-movements.json"), router, source_bindings())
    write(HERE/"routing"/"fixed-copper-restoration.json",
          {"seed_pcb_sha256":binding["pcb_sha256"],"dsn_sha256":binding["dsn_sha256"],
           "ses_sha256":sha(HERE/"routing"/"completion-output.ses"),
           "scope":"Exact native fixed copper deliberately omitted by SES; restored once without altering pads",
           "fixed_items":protected, "contained_interchange_rounding_stubs_omitted": contained_rounding_stubs})
    state = read(HERE / "completion-build.json")
    state["interchange_bindings"].update({
        "routing/" + name: sha(HERE / "routing" / name)
        for name in ("completion-output.ses", "local-router-binding.json", "fixed-copper-restoration.json")})
    write(HERE / "completion-build.json", state)
    print(json.dumps({"tracks": len(router.tracks), "vias": len(router.vias),
                      "pcb_sha256": sha(HERE / "handbell.kicad_pcb")}, indent=2))


def repair_clearances():
    guard()
    require_unfilled()
    text, board = load(HERE / "handbell.kicad_pcb")
    text = apply_edits(text, [(n.start,n.end,"") for kind in ("segment","via") for n in board.children(kind)])
    manifest, data = read(HERE / "placement-manifest.json"), read(HERE / "routing-data.json")
    router = Router(manifest, loads(text))
    router.tracks, router.vias = copy.deepcopy(data["tracks"]), copy.deepcopy(data["vias"])
    router.results, router.quiet = data["connections"], data["quiet_paths"]
    repairs = []
    close = lambda a,b: math.dist(a,b)<.0002
    for via in router.vias:
        if via["net"] == "/PROT_COUT" and close(via["xy"], [-12.3,6.2]):
            via["xy"] = [-12.5,6.08]
            repairs.append({"net": "/PROT_COUT", "old_via_xy": [-12.3,6.2], "new_via_xy": via["xy"],
                            "reason": "Clear the existing broad raw-negative feed and retain both contact-base/source-via clearances"})
    require(repairs, "Expected uncorrected COUT transition absent; do not apply this repair twice")
    kept = []
    for track in router.tracks:
        if track["net"] == "/PROT_COUT":
            if track["layer"] == "F.Cu" and any(close(point, [-12.3,6.2]) or close(point, [-12.3,6.6])
                                               for point in (track["a"],track["b"])):
                continue
            if track["layer"] == "B.Cu":
                for name in ("a","b"):
                    if close(track[name],[-12.3,6.2]):
                        track[name] = [-12.5,6.08]
                    elif close(track[name],[-12.3,6.05]):
                        track[name] = [-12.5,6.05]
        kept.append(track)
    router.tracks = kept
    router.wire([[-12.5,6.08],[-12.2,6.08],[-12.2,6.6],router.pad("U6","2")["center"]],
                "/PROT_COUT", .1778, "corrected COUT controller approach")
    offenders = [t for t in router.tracks if t["net"] == "/PROT_VM" and t["layer"] == "B.Cu"
                 and power.prep.point_segment_distance([-10.45,9.0], t["a"], t["b"]) < .3+t["width"]/2+.203]
    require(offenders, "Expected VM-to-raw-VSS-via clearance conflict absent")
    for track in offenders:
        router.tracks.remove(track)
        path = router.search(track["a"],track["b"],track["net"],track["width"],False,3,180000,(1,1))
        require(path, "Cannot safely repair VM locally with completed copper; coordinated reroute needed")
        router.add_path(path,track["net"],track["width"],"VM detour around actual raw-VSS annulus")
        repairs.append({"net": track["net"], "replaced_track": track,
                        "reason": "Route the quiet VM input around the full raw-VSS via annulus, not just its entering track"})
    emit(text,manifest,read(HERE/"reports"/"footprint-movements.json"),router,source_bindings())
    write(HERE/"reports"/"clearance-repairs.json",repairs)


def finish_power():
    guard()
    require_unfilled()
    text, board = load(HERE/"handbell.kicad_pcb")
    text = apply_edits(text,[(n.start,n.end,"") for kind in ("segment","via") for n in board.children(kind)])
    manifest, data = read(HERE/"placement-manifest.json"), read(HERE/"routing-data.json")
    router = Router(manifest,loads(text))
    router.tracks, router.vias = copy.deepcopy(data["tracks"]), copy.deepcopy(data["vias"])
    router.results, router.quiet = data["connections"], data["quiet_paths"]
    require(router.link("Q1","3","L1","P$1","broad switched supply to full inductor input land",1.2,True),
            "Full-width source-to-inductor route still blocked; no stubs applied")
    emit(text,manifest,read(HERE/"reports"/"footprint-movements.json"),router,source_bindings())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("power", "export-dsn", "import-ses"))
    args = parser.parse_args()
    require_unfilled()
    if args.operation == "power":
        build_power()
    elif args.operation == "export-dsn":
        export_dsn()
    elif args.operation == "import-ses":
        import_session()


if __name__ == "__main__":
    main()
