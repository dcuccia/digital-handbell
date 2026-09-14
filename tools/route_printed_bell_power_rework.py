# SPDX-License-Identifier: MIT
"""Independent power-first rework; never writes either published electrical package."""
from __future__ import annotations

import argparse
from collections import Counter
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

sys.dont_write_bytecode = True
import numpy as np
import route_printed_bell as frozen
from kicad_sexpr import apply_edits, load, loads

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "hardware" / "handbell" / "iterations" / "printed-bell-routing"
OUTPUT = SOURCE.parent / "printed-bell-power-rework"
CLI, prep = frozen.CLI, frozen.prep
REVIEW_COMMIT = "eb9041a6c0d4cd5b43adfb33383449f4a8ada6fc"
POSES = {
    "U5": (-2.7, 15.2, 0), "L1": (-7, 14.8, 0),
    "C26": (-9.5, 10.9, 180), "C27": (.1, 15.2, 270), "C28": (2.2, 15.2, 270),
    "R23": (-1.8, 12.7, 180), "R24": (-2.1, 11.4, 0), "C29": (-5.7, 11, 0),
    "R26": (-13.6, 11.7, 90), "R25": (-9.2, 8.3, 0),
}
REASONS = {
    "U5": "Face both output-capacitor rows; SW escapes under the package toward the inductor behind it, per SLVAES4.",
    "L1": "Move full-height inductor behind U5, not between VOUT/GND and output capacitors; retain annular magnet clearance.",
    "C26": "Face V+ directly toward the inductor input, with GND facing the shunt-return approach; avoid crossing its opposite-polarity land.",
    "C27": "First output capacitor directly faces U5 VOUT/GND with both connections on F.",
    "C28": "Parallel second output capacitor on the same broad F positive/ground buses.",
    "R23": "Keep feedback divider adjacent to FB and take voltage from the output capacitor, away from SW.",
    "R24": "Keep FB node short; use a separately reserved quiet capacitor-ground reference, not the switching-return maze.",
    "C29": "Keep the DNP snubber/service reservation clear of the relocated full-size inductor; do not fit or change circuit.",
    "R26": "Put sense resistor beside R27 system-side land for an independent direct pickoff.",
    "R25": "Clear the R27 load-return approach formerly obstructed by this bias resistor; retain local U6 filtered supply.",
}
PROXY_DEPTH_UPDATES = {
    "U1": {
        "old_depth_mm": 2.0, "new_depth_mm": 2.1,
        "dimension_basis": "Winbond UX E=2.0 +/-0.1mm; width envelope already covers D=3.0 +/-0.1mm.",
        "manufacturer_document": {
            "url": "https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/6661/W25Q16JV.pdf",
            "revision": "Winbond Revision I December24,2024; section11.3 printedp67",
            "previously_inspected_pdf_sha256": "a1e966f4a80bfb3786a3f781cfeff28c774b824ec92e10090038f9dec823e5f3",
        },
    },
    "U6": {
        "old_depth_mm": 1.5, "new_depth_mm": 1.55,
        "dimension_basis": "TI DSE0006A permits 1.55mm maximum body depth; width envelope is already larger.",
        "manufacturer_document": {
            "url": "https://www.ti.com/lit/ds/symlink/bq2970.pdf",
            "revision": "TI SLUSBU9I August2024; DSE0006A drawing4220552/B January2024",
            "previously_inspected_pdf_sha256": "33ecbecf2eca2276a7afa6cf41aa6f8016ef4a71572a52d6941dfba8f3def126",
        },
    },
}
sha = frozen.sha
write = frozen.write


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "digital-handbell/power-rework/"+name))


def bindings():
    paths = [p for p in SOURCE.rglob("*") if p.is_file() and "__pycache__" not in p.parts
             and not p.name.endswith((".lck", ".bak", ".pyc", ".kicad_prl"))]
    paths += [Path(frozen.__file__), Path(prep.__file__), ROOT / "tools" / "kicad_sexpr.py"]
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}


def guard():
    report = OUTPUT / "routing-build.json"
    if report.exists():
        previous = json.loads(report.read_text())
        prep.require(sha(OUTPUT / "handbell.kicad_pcb") == previous["pcb_sha256"],
                     "Edited power-rework board: refusing overwrite")
        for name, digest in previous["protected_files"].items():
            prep.require(sha(OUTPUT / name) == digest, "Edited power-rework dependency: "+name)
    else:
        prep.require(not (OUTPUT / "handbell.kicad_pcb").exists(), "Unbound existing power-rework PCB")


def moved_board():
    text, board = load(SOURCE / "handbell.kicad_pcb")
    edits, moves = [], []
    for fp in board.children("footprint"):
        ref = fp.properties()["Reference"]
        if ref in POSES:
            at = fp.child("at")
            old = list(map(float, at.atoms()[1:]))
            x, y, angle = POSES[ref]
            edits.append((at.start, at.end, f"(at {100+x:.6f} {100+y:.6f} {angle:g})"))
            moves.append({"reference": ref, "old_native_pose": [old[0]-100, old[1]-100, old[2]],
                          "new_native_pose": [x, y, angle], "rationale": REASONS[ref]})
    for kind in ("segment", "via"):
        edits.extend((n.start, n.end, "") for n in board.children(kind))
    return apply_edits(text, edits), moves


def updated_manifest(moves):
    manifest = json.loads((SOURCE / "placement-manifest.json").read_text())
    for movement in moves:
        ref, old, new = movement["reference"], movement["old_native_pose"], movement["new_native_pose"]
        for part in manifest["components"]:
            if part["reference"] == ref:
                dx, dy = prep.rotate(part["x_mm"]-old[0], part["y_mm"]-old[1], new[2]-old[2])
                part.update(x_mm=new[0]+dx, y_mm=new[1]+dy, rotation_deg=-new[2],
                            native_origin_common_xy_mm=list(new[:2]))
        for cluster in manifest["electrical_landmarks"].values():
            if ref in cluster:
                cluster[ref] = list(new)
    envelope_changes = []
    for part in manifest["components"]:
        if part["reference"] not in PROXY_DEPTH_UPDATES:
            continue
        update = PROXY_DEPTH_UPDATES[part["reference"]]
        prep.require(part["depth_mm"] == update["old_depth_mm"], "Unexpected source proxy depth")
        angle = math.radians(part["rotation_deg"])
        # Depth is the local Y axis, not an unrotated board-Y bounding-box dimension.
        axis = [round(-math.sin(angle), 12), round(math.cos(angle), 12)]
        envelope_changes.append({
            "reference": part["reference"], **copy.deepcopy(update),
            "rotation_deg": part["rotation_deg"], "local_depth_axis_board_xy_unit": axis,
            "unchanged_width_height_mm": [part["width_mm"], part["height_mm"]],
            "native_geometry_changed_by_envelope_adjustment": False,
        })
        part["depth_mm"] = update["new_depth_mm"]
    manifest["proxy_envelope_adjustments"] = {
        "authorization": "Parent-authorized conservative U1/U6 body-depth corrections, September14,2026",
        "evidence_scope": "Manufacturer maxima carried forward from the read-only BOM audit and T8 source evidence; no new physical measurement or PDF redistribution",
        "audit_reference": "docs/pcba-bom-readiness.md",
        "changes": envelope_changes,
    }
    manifest.update(status="Power-first rework, partial and not mechanically rebound or approved for operation",
                    source_baseline=str(SOURCE.relative_to(ROOT)),
                    baseline_pcb_sha256=sha(SOURCE / "handbell.kicad_pcb"),
                    baseline_schematic_sha256=sha(SOURCE / "handbell.kicad_sch"),
                    mechanical_rebind_required=True,
                    routing_report="reports/routing-review.json",
                    placement_method="Authorized local boost/protection pose rework for real current loops and independent pickoffs")
    manifest["planning"] = {
        "scope": "Current native pad/courtyard and component-envelope screens are in the new routing report",
        "report": "reports/routing-review.json",
        "source_planning_assessment_not_transferred": True,
        "mechanical_fit_approval": False,
    }
    manifest["limits"] = [s for s in manifest["limits"] if not s.startswith(
        ("Exact geometry retained", "Thermal via-in-pad fill/cap"))]
    manifest["limits"] += ["Changed F poses require exact new mechanical rebind; prior model does not approve these poses.",
                           "U1/U6 maximum-depth envelopes are enlarged; old nominal clearances do not include these component tolerances or approve the new fit.",
                           "2A cell/1A5V screens and copper-drop targets are provisional, not current or thermal ratings.",
                           "Thermal-pad and under-body via assembly process is unresolved; no fill/cap mandate or standard-via qualification."]
    return manifest


class PowerRouter(frozen.Router):
    def __init__(self, manifest, board):
        super().__init__(manifest, board)
        # The inherited engine reads only unchanged contact bytes from stage1.
        self.quiet = []
        self.ignore_quiet = None
        report = json.loads((SOURCE / "reports" / "service-label-review.json").read_text())
        self.label_boxes = [p["glyph_bounds_xy_mm"] for p in report["labels"]]
        self.manual_records = []

    def search(self, a, b, net, width, allow_vias=False, margin=3, expansion_limit=220000, endpoint_layers=(0, 0)):
        for xy, layer in zip((a, b), endpoint_layers):
            masks, _ = self.masks(net, width, np.array([xy[0]]), np.array([xy[1]]), False)
            if masks[layer, 0, 0]:
                return None
        return super().search(a, b, net, width, allow_vias, margin, expansion_limit, endpoint_layers)

    def masks(self, net, width, xs, ys, allow_vias):
        masks, via_mask = super().masks(net, width, xs, ys, allow_vias)
        X, Y = np.meshgrid(xs, ys)
        for xmin, ymin, xmax, ymax in self.label_boxes:
            masks[1] |= ((X >= xmin-width/2-.25) & (X <= xmax+width/2+.25) &
                         (Y >= ymin-width/2-.25) & (Y <= ymax+width/2+.25))
            via_mask |= ((X >= xmin-.55) & (X <= xmax+.55) & (Y >= ymin-.55) & (Y <= ymax+.55))
        for item in self.quiet:
            if item["group"] == self.ignore_quiet:
                continue
            a, b = item["a"], item["b"]
            dx, dy = b[0]-a[0], b[1]-a[1]
            fraction = np.clip(((X-a[0])*dx+(Y-a[1])*dy)/(dx*dx+dy*dy), 0, 1)
            distance2 = (X-a[0]-fraction*dx)**2+(Y-a[1]-fraction*dy)**2
            terminal = item["terminal"]
            tx, ty = terminal["center"]
            angle = math.radians(terminal["angle_deg"])
            lx = (X-tx)*math.cos(angle)-(Y-ty)*math.sin(angle)
            ly = (X-tx)*math.sin(angle)+(Y-ty)*math.cos(angle)
            inside = (abs(lx) <= terminal["size"][0]/2) & (abs(ly) <= terminal["size"][1]/2)
            masks[0 if item["layer"] == "F.Cu" else 1] |= (
                distance2 <= (width/2+item["width"]/2+.205)**2) & ~inside
            via_mask |= (distance2 <= (.3+item["width"]/2+.205)**2) & ~inside
        return masks, via_mask

    def wire(self, points, net, width, group, layer="F.Cu"):
        for a, b in zip(points, points[1:]):
            self.add_segment(a, b, net, layer, width, group)

    def mark_pair(self, ar, ap, br, bp, group):
        a, b = self.pad(ar, ap), self.pad(br, bp)
        prep.require(a["net"] == b["net"], "Wrong-net endpoint claim")
        self.results.append({"from": a["id"], "to": b["id"], "from_uuid": a["uuid"], "to_uuid": b["uuid"],
                             "net": a["net"], "group": group,
                             "status": "routed_endpoint_pair_pending_native_validation"})

    def reserve_quiet(self, start, terminal, group, width=.1778, layer="F.Cu"):
        self.quiet.append({"a": start, "b": terminal["center"], "width": width, "layer": layer,
                           "group": group, "terminal": terminal})

    def link(self, ar, ap, br, bp, group, width=.8, vias=True):
        a, b = self.pad(ar, ap), self.pad(br, bp)
        prep.require(a["net"] == b["net"], "Wrong-net power connection")
        layers = tuple(0 if "F.Cu" in p["layers"] else 1 for p in (a, b))
        for margin in (3, 7):
            path = self.search(a["center"], b["center"], a["net"], width, vias, margin,
                               expansion_limit=140000, endpoint_layers=layers)
            if path:
                self.add_path(path, a["net"], width, group)
                self.mark_pair(ar, ap, br, bp, group)
                print("connected", group, width, flush=True)
                return True
        choices = []
        for pad, other, layer in ((a, b, layers[0]), (b, a, layers[1])):
            options = []
            neck_width = min(width, .6 if pad["shape"] == "custom" or min(pad["size"]) >= .6 else .3)
            for radius in (.7, 1.0, 1.3):
                angles = sorted(range(0, 360, 45), key=lambda angle: math.dist(
                    [pad["center"][0]+radius*math.cos(math.radians(angle)),
                     pad["center"][1]+radius*math.sin(math.radians(angle))], other["center"]))
                for angle in angles:
                    xy = [pad["center"][0]+radius*math.cos(math.radians(angle)),
                          pad["center"][1]+radius*math.sin(math.radians(angle))]
                    masks, _ = self.masks(a["net"], width, np.array([xy[0]]), np.array([xy[1]]), False)
                    if masks[layer, 0, 0]:
                        continue
                    neck = self.search(pad["center"], xy, a["net"], neck_width, False, 1, 12000, (layer, layer))
                    if neck and sum(math.dist(p[:2], q[:2]) for p, q in zip(neck, neck[1:])) <= 1.6:
                        options.append((xy, neck, neck_width))
                    if len(options) >= 3:
                        break
                if len(options) >= 3:
                    break
            # Large endpoint lands do not need an artificial narrow escape.
            mask, _ = self.masks(a["net"], width, np.array([pad["center"][0]]), np.array([pad["center"][1]]), False)
            if not mask[layer, 0, 0]:
                options.insert(0, (pad["center"], [[*pad["center"], layer]], width))
            choices.append(options[:3])
        for ax, an, aw in choices[0]:
            for bx, bn, bw in choices[1]:
                middle = self.search(ax, bx, a["net"], width, vias, 7, 160000, layers)
                if middle:
                    self.add_path(an, a["net"], aw, group+" package escape")
                    self.add_path(middle, a["net"], width, group)
                    self.add_path(bn, a["net"], bw, group+" package escape")
                    self.mark_pair(ar, ap, br, bp, group)
                    print("connected with bounded package escapes", group, flush=True)
                    return True
        self.results.append({"from": a["id"], "to": b["id"], "from_uuid": a["uuid"], "to_uuid": b["uuid"],
                             "net": a["net"], "group": group, "status": "unrouted_no_safe_power_path", "width_mm": width})
        print("OPEN", group, flush=True)
        return False


def local_power(router):
    p = lambda r, n: router.pad(r, n)["center"]
    # Preserve the actual outside Q5 fanouts, separate source buses and thermal banks.
    prior = json.loads((SOURCE / "routing-data.json").read_text())
    router.tracks = [copy.deepcopy(t) for t in prior["tracks"] if t["group"].startswith(
        ("Q5 ", "IC1 local thermal", "U4 local thermal"))]
    router.vias = [copy.deepcopy(v) for v in prior["vias"] if "Q5" in v["group"] or "thermal via" in v["group"]]
    for via in router.vias:
        if "thermal via" in via["group"]:
            via["group"] = via["group"].split()[0]+" retained thermal-pad via; assembly process unresolved"

    sense = "quiet R26 shunt pickoff"
    router.wire([p("R26", "2"), p("R27", "2")], "GND", .1778, sense)
    router.reserve_quiet(p("R26", "2"), router.pad("R27", "2"), sense)
    router.mark_pair("R26", "2", "R27", "2", sense)

    # TI SLVAES4: SW runs under the package, not through the output-capacitor side.
    router.wire([p("U5", "5"), [-2.7, 15.2], [-2.7, 16.7]], "BOOST_SW", .20, "bounded under-U5 SW escape")
    router.wire([[-2.7, 16.7], [-5.4, 16.7], p("L1", "P$2")], "BOOST_SW", 1.2, "inductor SW link behind U5")
    router.mark_pair("U5", "5", "L1", "P$2", "SW under device, no output-loop crossing")
    for pin, cap_pin, y, net in (("6", "1", 14.25, "VAMP"), ("4", "2", 16.15, "GND")):
        source = p("U5", pin)
        router.wire([source, [-1.25, source[1]]], net, .30, "output-loop bounded SOT563 escape")
        router.wire([[-1.25, source[1]], [-.6, y], p("C27", cap_pin), p("C28", cap_pin)],
                    net, .8, "direct all-F output capacitor bus")
        for cap in ("C27", "C28"):
            router.mark_pair("U5", pin, cap, cap_pin, "all-F output hot loop")

    router.wire([p("U5", "1"), [-3.335, 12.7], p("R23", "2"), p("R24", "1")],
                "BOOST_FB", .1778, "quiet FB node")
    router.wire([p("R23", "1"), [-.2, 12.7], p("C27", "1")], "VAMP", .1778, "feedback voltage capacitor pickoff")
    router.mark_pair("U5", "1", "R23", "2", "quiet FB node")
    router.mark_pair("U5", "1", "R24", "1", "quiet FB node")
    router.mark_pair("R23", "1", "C27", "1", "feedback voltage capacitor pickoff")
    quiet = "quiet R24 capacitor-ground reference"
    points = [p("R24", "2"), [-.2, 11.4], [.2, 11.9]]
    router.wire(points, "GND", .1778, quiet)
    router.add_via([.2, 11.9], "GND", group=quiet)
    back = [[.2, 11.9], [3.7, 13.1], [3.7, 17.5]]
    router.wire(back, "GND", .1778, quiet, "B.Cu")
    router.add_via([3.7, 17.5], "GND", group=quiet)
    router.wire([[3.7, 17.5], p("C28", "2")], "GND", .1778, quiet)
    for t in router.tracks:
        if t["group"] == quiet:
            router.quiet.append({**t, "terminal": router.pad("C28", "2")})
    router.mark_pair("R24", "2", "C28", "2", quiet)
    for pin in ("3", "11", "15"):
        start, end = p("U4", "THERMAL"), p("U4", pin)
        corner = [end[0], start[1]] if pin == "15" else [start[0], end[1]]
        router.wire([start, corner, end], "GND", .3, "amplifier local ground land")
        router.mark_pair("U4", "THERMAL", "U4", pin, "amplifier local ground land")
    thermal = [v["xy"] for v in router.vias if v["group"].startswith("U4")]
    for ref, via in (("C16", [12, -6.2]), ("C19", [15.15, -8.2])):
        router.wire([p(ref, "2"), via], "GND", .6, "amplifier bypass ground off-pad escape")
        router.add_via(via, "GND", group="amplifier bypass return off-pad transition")
        router.wire([via, min(thermal, key=lambda xy: math.dist(xy, via))], "GND", .8,
                    "amplifier bypass B return outside raw contact base", "B.Cu")
        router.mark_pair(ref, "2", "U4", "THERMAL", "completed amplifier local bypass return")
    router.wire([p("U4", "7"), p("U4", "8")], "VAMP", .3, "paired amplifier supply lands")
    router.mark_pair("U4", "7", "U4", "8", "paired amplifier supply lands")
    router.wire([p("C27", "2"), [-.6, 17.5]], "GND", .8, "boost return F takeoff, outside hot loop")
    router.add_via([-.6, 17.5], "GND", group="boost load return off-pad transition")
    router.wire([[-.6, 17.5], [-12.1, 10.3]], "GND", 1.2, "boost load return upper B bank", "B.Cu")
    router.add_via([-12.1, 10.3], "GND", group="boost load return off-pad transition")
    router.wire([[-12.1, 10.3], [-12.1, 9.500966], p("R27", "2")], "GND", .8,
                "load return enters R27 from right; sense enters from below")
    router.mark_pair("C27", "2", "R27", "2", "boost main protected return")
    router.wire([p("C26", "2"), [-12.1, 10.3]], "GND", .8, "input capacitor local return to load-return node")
    router.mark_pair("C26", "2", "R27", "2", "input capacitor protected return")
    router.wire([p("C30", "2"), [-10, 6.2]], "/CELL_NEG", .1778, "VSS local bypass off-pad escape")
    router.wire([[-11.5, 8.75], p("U6", "4")], "/CELL_NEG", .1778, "VSS local bypass off-pad escape")
    for xy in ([-10, 6.2], [-11.5, 8.75]):
        router.add_via(xy, "/CELL_NEG", group="VSS local bypass off-pad transition")
    router.wire([[-10, 6.2], [-11.5, 8.75]], "/CELL_NEG", .1778, "VSS local bypass B link", "B.Cu")
    router.mark_pair("U6", "4", "C30", "2", "VSS local decoupling")
    router.add_via([-16.6, 8.1], "/PROT_FET_RETURN", group="parallel common return off-pad transition")
    router.wire([[-16.6, 8.1], p("R27", "1")], "/PROT_FET_RETURN", .6,
                "parallel common return F branch")
    router.wire([[-16.6, 8.1], [-16.7, 6.70048], [-15.750825, 6.70048]], "/PROT_FET_RETURN", .6,
                "parallel common return B branch outside Source1 bus", "B.Cu")
    router.wire([p("Q5", "B1"), [-14.400825, 8.5], [-12.102673, 8.5], p("U6", "3")],
                "/PROT_DOUT", .1778, "DOUT outside Source1 pad row")
    router.mark_pair("U6", "3", "Q5", "B1", "DOUT outside Source1 pad row")


def power_corridors(router):
    # These are requested widths, never current ratings. Unfound paths remain explicit.
    raw_source = router.pad("BT2", "1")
    source_bus = [-13.050825, 7.75048]
    path = router.search(raw_source["center"], source_bus, "/CELL_NEG", 1.0, False, 8,
                         endpoint_layers=(1, 1))
    prep.require(path is not None, "Raw return must reach the existing outside Source1 bus, not obstruct Q5 gates")
    router.add_path(path, "/CELL_NEG", 1.0, "raw cell return to existing outside Q5 Source1 bus")
    router.mark_pair("BT2", "1", "Q5", "A1", "raw cell return via preserved outside source escapes")
    for args in (
        ("C26", "1", "L1", "P$1", "inductor input-current feed", 1.2, False),
        ("BT1", "1", "Q3", "3", "cell positive to selector", 1.2, True),
        ("Q3", "2", "Q1", "2", "VHI cell selector to audio switch", 1.0, True),
        ("Q1", "3", "C26", "1", "switched cell feed to boost input", 1.2, True),
        ("C28", "1", "C19", "1", "5V amplifier supply trunk", 1.0, True),
        ("C19", "2", "C27", "2", "amplifier protected return trunk", 1.0, True),
    ):
        router.link(*args)
    for ref in ("BT1", "BT2"):
        a, b = router.lookup[(ref, "1")]
        router.wire([a["center"], b["center"]], a["net"], 1.5, "paired physical contact lands", "B.Cu")
        router.results.append({"from": a["id"], "to": b["id"], "from_uuid": a["uuid"], "to_uuid": b["uuid"],
                               "net": a["net"], "group": "paired physical contact lands",
                               "status": "routed_endpoint_pair_pending_native_validation"})
    for args in (
        ("U5", "3", "C26", "1", "VIN bias decoupling spur, not inductor current", .1778, True),
        ("U6", "5", "R25", "2", "protector filtered supply", .1778, True),
        ("U6", "5", "C30", "1", "protector local bypass", .1778, True),
        ("U6", "6", "R26", "1", "VM sense resistor to protector", .1778, True),
        ("U6", "4", "Q5", "A1", "VSS deliberate raw source reference", .1778, True),
        ("U6", "2", "Q5", "B2", "protector COUT", .1778, True),
        ("R28", "1", "Q5", "B1", "DOUT discharge gate connection", .1778, True),
        ("R28", "2", "Q5", "A1", "DOUT discharge raw source connection", .1778, True),
        ("R29", "2", "Q5", "A2", "COUT low-current discharge source connection", .1778, True),
        ("R25", "1", "BT1", "1", "protector VBAT bias feed, not load current", .1778, True),
        ("U4", "7", "C16", "1", "amplifier ceramic positive", .3, True),
        ("U4", "8", "C19", "1", "amplifier bulk positive", .3, True),
    ):
        router.link(*args)


def retain_compatible(router):
    data = json.loads((SOURCE / "routing-data.json").read_text())
    nets = sorted({t["net"] for t in data["tracks"]} -
                  {"GND", "VAMP", "V+", "BOOST_SW", "BOOST_FB", "/PROT_VM", "/PROT_BAT", "/CELL_NEG", "/PROT_FET_RETURN"})
    dropped = []
    for net in nets:
        tracks = [t for t in data["tracks"] if t["net"] == net]
        vias = [v for v in data["vias"] if v["net"] == net]
        accepted = True
        for t in tracks:
            _, _, xs, ys = router.local_grid(t["a"], t["b"], .2)
            masks, _ = router.masks(net, t["width"], xs, ys, False)
            for i in range(max(2, math.ceil(math.dist(t["a"], t["b"])/.025))+1):
                count = max(2, math.ceil(math.dist(t["a"], t["b"])/.025))
                xy = [t["a"][j]+(t["b"][j]-t["a"][j])*i/count for j in (0, 1)]
                x, y = round((xy[0]-xs[0])/.05), round((xy[1]-ys[0])/.05)
                if masks[0 if t["layer"] == "F.Cu" else 1, y, x]:
                    accepted = False
                    break
            if not accepted:
                break
        if accepted:
            for v in vias:
                if prep.via_rejections(v["xy"], net, router.pads, router.holes, router.metal,
                                       router.outline, v["diameter"], v["drill"], .2, .25, True):
                    accepted = False
                    break
        if accepted:
            router.tracks += copy.deepcopy(tracks)
            router.vias += copy.deepcopy(vias)
            router.results += [copy.deepcopy(r) for r in data["connections"] if r["net"] == net and r["status"].startswith("routed")]
        else:
            dropped.append({"net": net, "reason": "Previous signal copper conflicts with power-first geometry or reserved quiet/service regions"})
    return dropped


def emit(text, moves, manifest, router, before, dropped):
    additions = []
    for i, t in enumerate(router.tracks):
        additions.append(f'(segment (start {100+t["a"][0]:.6f} {100+t["a"][1]:.6f}) '
                         f'(end {100+t["b"][0]:.6f} {100+t["b"][1]:.6f}) (width {t["width"]:g}) '
                         f'(layer "{t["layer"]}") (net {json.dumps(t["net"])}) (uuid "{uid("track/"+str(i))}"))')
    for i, v in enumerate(router.vias):
        additions.append(f'(via (at {100+v["xy"][0]:.6f} {100+v["xy"][1]:.6f}) (size {v["diameter"]:g}) '
                         f'(drill {v["drill"]:g}) (layers "F.Cu" "B.Cu") (net {json.dumps(v["net"])}) '
                         f'(uuid "{uid("via/"+str(i))}"))')
    board = loads(text)
    title = board.child("title_block")
    pcb = apply_edits(text, [(board.end-1, board.end-1, "\n"+"\n".join(additions)+"\n"),
                            (title.start, title.end, '(title_block (title "Printed bell power rework - PARTIAL") '
                             '(rev "0.7-power-rework") (comment 1 "Adafruit-derived CC BY-SA3.0; not fabrication approval"))')])
    write(OUTPUT / "handbell.kicad_pcb", pcb)
    manifest["generated_pcb_sha256"] = sha(OUTPUT / "handbell.kicad_pcb")
    write(OUTPUT / "placement-manifest.json", manifest)
    write(OUTPUT / "routing-data.json", {
        "tracks": router.tracks, "vias": router.vias, "connections": router.results,
        "regression_policy": "Explicit partial power-first reallocation; report every lost physical-pad pair and never waive copper errors"})
    write(OUTPUT / "reports" / "footprint-movements.json", moves)
    write(OUTPUT / "reports" / "proxy-envelope-adjustments.json", manifest["proxy_envelope_adjustments"])
    write(OUTPUT / "reports" / "reserved-paths.json", {
        "quiet_paths": router.quiet, "retained_signal_rejections": dropped,
        "planning_basis": {"cell_A": 2, "cell_sensitivity_A": 3, "V5_A": 1, "nominal_copper_um": 35,
                          "resistance_30um_60C_factor": 1.35, "cell_roundtrip_drop_target_mV": 50,
                          "V5_roundtrip_drop_target_mV": 100, "future_conductor_rise_target_C": 10,
                          "ripple_case": "UNQUALIFIED 1uH/1MHz, 2.8->5V: 1.23App, ~2.6A peak at2A mean"},
        "not_qualified": ["Copper, plating, widths, thermal rise, contacts, FET/SOA, charge/reversal, via/stencil process",
                          "No current rating or operating/temperature permission follows from these planning cases"]})
    protected = ["handbell.kicad_sch", "handbell.kicad_pro", "placement-manifest.json", "routing-data.json",
                 "battery-contact-interface.json", "fp-lib-table", "sym-lib-table", "Handbell.kicad_sym", "T8.kicad_sym",
                 "reports/proxy-envelope-adjustments.json"]
    protected += [str(p.relative_to(OUTPUT)) for p in (OUTPUT / "libraries").rglob("*") if p.is_file()]
    write(OUTPUT / "routing-build.json", {
        "pcb_sha256": sha(OUTPUT / "handbell.kicad_pcb"), "script_sha256": sha(__file__),
        "source_bindings": before, "protected_files": {name: sha(OUTPUT / name) for name in protected},
        "tracks": len(router.tracks), "vias": len(router.vias),
        "review_commit": REVIEW_COMMIT, "mechanical_rebind_required": True,
        "connection_results": dict(Counter(r["status"] for r in router.results))})
    prep.require(bindings() == before, "Frozen source bytes changed during power rework")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("local", "power", "retain"), default="retain")
    args = parser.parse_args()
    prep.require(sha(SOURCE / "handbell.kicad_pcb") == "075c7b7cb0a98e302af29f5985bbf020111df5b1be385e5ebfa61be236b04250",
                 "Wrong reviewed PCB baseline")
    prep.require(sha(SOURCE / "placement-manifest.json") == "cc935ef468e8fb8d0fda5d55010e8883eab1f8b578078f2dcc4f77fe456fe69f",
                 "Wrong reviewed placement baseline")
    frozen.verify_release()
    before = bindings()
    guard()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "reports").mkdir(exist_ok=True)
    for name in ("handbell.kicad_sch", "handbell.kicad_pro", "Handbell.kicad_sym", "T8.kicad_sym", "fp-lib-table",
                 "sym-lib-table", "LICENSE.txt", "battery-contact-interface.json", "source-evidence.json",
                 "design-input-snapshot.json"):
        shutil.copyfile(SOURCE / name, OUTPUT / name)
    for name in ("libraries", "notices"):
        shutil.copytree(SOURCE / name, OUTPUT / name, dirs_exist_ok=True)
    shutil.copyfile(SOURCE / "reports" / "bom-draft.csv", OUTPUT / "reports" / "bom-draft.csv")
    text, moves = moved_board()
    manifest = updated_manifest(moves)
    router = PowerRouter(manifest, loads(text))
    local_power(router)
    if args.stage != "local":
        power_corridors(router)
    dropped = retain_compatible(router) if args.stage == "retain" else []
    emit(text, moves, manifest, router, before, dropped)
    removed = []
    for _ in range(4):
        drc_path = OUTPUT / "reports" / "drc-routing-step.json"
        subprocess.run([str(CLI), "pcb", "drc", "--format", "json", "--severity-all",
                        "--output", str(drc_path), str(OUTPUT / "handbell.kicad_pcb")],
                       check=True, capture_output=True, timeout=180)
        drc = json.loads(drc_path.read_text())
        ids = {item["uuid"] for v in drc["violations"] if v["type"] == "track_dangling" for item in v["items"]}
        if not ids:
            break
        doomed = [i for i, track in enumerate(router.tracks) if uid("track/"+str(i)) in ids]
        prep.require(doomed and all(math.dist(router.tracks[i]["a"], router.tracks[i]["b"]) < .01 for i in doomed),
                     "Non-microscopic dangling copper requires an explicit routing repair")
        removed += [router.tracks[i] for i in doomed]
        router.tracks = [t for i, t in enumerate(router.tracks) if i not in doomed]
        emit(text, moves, manifest, router, before, dropped)
    else:
        raise ValueError("Microscopic native spur cleanup did not converge")
    write(OUTPUT / "reports" / "removed-native-spurs.json",
          {"scope": "Native-reported sub0.01mm endpoint/grid overshoots physically removed; not a waiver",
           "removed": removed})
    drc_path.unlink()
    print(json.dumps({"pcb_sha256": sha(OUTPUT / "handbell.kicad_pcb"), "tracks": len(router.tracks),
                      "vias": len(router.vias), "stage": args.stage}, indent=2))


if __name__ == "__main__":
    main()
