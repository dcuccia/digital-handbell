# SPDX-License-Identifier: MIT
"""Unit tests for build_quote_package.py using synthetic boards and exports."""
from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import build_quote_package as bq
from kicad_sexpr import loads

try:
    import gerbonara  # noqa: F401

    HAVE_GERBONARA = True
except ImportError:
    HAVE_GERBONARA = False

TOP = '"F.Cu" "F.Mask" "F.Paste"'
BOT = '"B.Cu" "B.Mask" "B.Paste"'
THT = '"*.Cu" "*.Mask"'
STACKUP = (
    '(setup (stackup (layer "F.Cu" (type "copper") (thickness 0.035)) '
    '(layer "dielectric 1" (type "prepreg") (thickness 0.1)) '
    '(layer "B.Cu" (type "copper") (thickness 0.035))))'
)
_serial = [0]


def uid() -> str:
    _serial[0] += 1
    return f"{_serial[0]:08x}-0000-0000-0000-000000000000"


def count(value):
    return len(value) if isinstance(value, (list, tuple, set, dict)) else value


def put(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return path


def pad(num, kind="smd", shape="rect", x=0.0, y=0.0, ang=None, w=1.0, h=1.0,
        layers=None, drill=None, net=None, extra=""):
    if layers is None:
        layers = THT if kind in ("thru_hole", "np_thru_hole") else TOP
    at = f"(at {x} {y} {ang})" if ang is not None else f"(at {x} {y})"
    parts = [f'(pad "{num}" {kind} {shape} {at} (size {w} {h})']
    if drill is not None:
        parts.append(f"(drill {drill})")
    parts.append(f"(layers {layers})")
    if net is not None:
        parts.append(f'(net "{net}")')
    if extra:
        parts.append(extra)
    parts.append(f'(uuid "{uid()}"))')
    return " ".join(parts)


def footprint(ref, x, y, rot=None, layer="F.Cu", attrs="smd", value="X", lib="Lib:X",
              props=None, pads=()):
    at = f"(at {x} {y} {rot})" if rot is not None else f"(at {x} {y})"
    items = [f'(footprint "{lib}"', f'(layer "{layer}")', f'(uuid "{uid()}")', at,
             f'(property "Reference" "{ref}")', f'(property "Value" "{value}")']
    items += [f'(property "{k}" "{v}")' for k, v in (props or {}).items()]
    if attrs:
        items.append(f"(attr {attrs})")
    items += list(pads)
    return " ".join(items) + ")"


def edge(x1, y1, x2, y2, w=0.05, layer="Edge.Cuts"):
    return (f"(gr_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type default)) "
            f'(layer "{layer}") (uuid "{uid()}"))')


def rect(x1, y1, x2, y2, w=0.05):
    return [edge(x1, y1, x2, y1, w), edge(x2, y1, x2, y2, w),
            edge(x2, y2, x1, y2, w), edge(x1, y2, x1, y1, w)]


def via(x, y, size, drill, net="", extra="", uuid=None):
    return (f'(via (at {x} {y}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") '
            f'(net "{net}") {extra} (uuid "{uuid or uid()}"))')


def make_board(parts=(), vias=(), edges=(), setup="(setup)"):
    body = "\n".join([setup, *parts, *vias, *edges])
    return ('(kicad_pcb (version 20260206) (generator "pcbnew") (generator_version "10.0") '
            '(general (thickness 1.6)) (paper "A4") (layers (0 "F.Cu" signal) (2 "B.Cu" signal)) '
            + body + ")")


def parse(text: str) -> "bq.Board":
    return bq.parse_board_text(text)


def one_footprint(props):
    return parse(make_board([footprint("D4", 0, 0, props=props)])).footprints[0]


def board_a() -> str:
    resistor = {"MPN": "RC0402FR-0710KL", "Manufacturer": "Yageo"}

    def two_pads(net2=None):
        return [pad(1, x=-0.5), pad(2, x=0.5, net=net2)]

    parts = [
        footprint("R10", 6, 2, value="10k", lib="Lib:R_0402", props=resistor, pads=two_pads()),
        footprint("R1", 2, 2, value="10k", lib="Lib:R_0402", props=resistor, pads=two_pads("N1")),
        footprint("R2", 4, 2, value="10k", lib="Lib:R_0402", props=resistor, pads=two_pads()),
        footprint("C1", 8, 2, rot=-90, value="10uF", lib="Lib:C_0805",
                  props={"MPN": "GRM21BR61C106KE15L", "Manufacturer": "Murata", "ROT": "270"},
                  pads=[pad(1, x=-0.9, ang=-90), pad(2, x=0.9, ang=-90)]),
        footprint("BT1", 15, 5, rot=180, layer="B.Cu", value="BAT", lib="Lib:Keystone_254",
                  props={"MPN": "254"}, pads=[pad(1, x=-1, layers=BOT), pad(2, x=1, layers=BOT)]),
        footprint("C29", 10, 8, attrs="smd dnp", value="1u", lib="Lib:C_0402", pads=two_pads()),
        footprint("TP1", 12, 8, attrs="smd exclude_from_pos_files exclude_from_bom", value="TP",
                  lib="Lib:TP_1mm", pads=[pad(1)]),
        footprint("MH1", 1, 9, attrs="board_only exclude_from_pos_files exclude_from_bom", value="MH",
                  lib="Lib:MountingHole_2.2mm",
                  pads=[pad("", "thru_hole", "circle", w=4.4, h=4.4, drill="2.2")]),
        footprint("H1", 18, 2, rot=90, attrs="exclude_from_pos_files exclude_from_bom", value="H",
                  lib="Lib:Hole_0.65",
                  pads=[pad("", "np_thru_hole", "circle", x=0.5, w=0.65, h=0.65, drill="0.65")]),
    ]
    vias = [via(2.6, 2.0, 0.5, 0.3, "N1"), via(7, 5, 0.6, 0.3, "GND", "(capping yes) (filling yes)")]
    return make_board(parts, vias, rect(0, 0, 20, 10), STACKUP)


PTH_TEXT = """M48
; DRILL file KiCad 10.0.6 date 2026-11-09T17:43:27
; FORMAT={-:-/ absolute / metric / decimal}
; #@! TF.CreationDate,2026-11-09T17:43:27-08:00
; #@! TF.GenerationSoftware,Kicad,Pcbnew,10.0.6
; #@! TF.FileFunction,Plated,1,6,PTH
FMAT,2
METRIC
; #@! TA.AperFunction,Plated,PTH,ViaDrill
T1C0.300
; #@! TA.AperFunction,Plated,PTH,ComponentDrill
T2C2.200
T3C0.600
%
G90
G05
T1
X2.6Y-2
X7Y-5
T2
X1Y-9
T3
X95.675Y-74.3G85X95.675Y-75.1
G05
M30
"""

NPTH_TEXT = """M48
; DRILL file KiCad 10.0.6 date 2026-11-09T17:43:27
; FORMAT={-:-/ absolute / metric / decimal}
; #@! TF.FileFunction,NonPlated,1,6,NPTH
FMAT,2
METRIC
; #@! TA.AperFunction,NonPlated,NPTH,ComponentDrill
T1C0.650
%
G90
G05
T1
X18Y-1.5
M30
"""

PTH_A = PTH_TEXT.replace("T3C0.600\n", "").replace("T3\nX95.675Y-74.3G85X95.675Y-75.1\nG05\n", "")


def pos_text(rows) -> str:
    lines = ["Ref,Val,Package,PosX,PosY,Rot,Side"]
    for ref, val, pkg, x, y, rot, side in rows:
        lines.append(f'"{ref}","{val}","{pkg}",{x:.6f},{y:.6f},{rot:.6f},{side}')
    return "\n".join(lines) + "\n"


POS_FITTED = [
    ("R10", "10k", "R_0402", 6, -2, 0, "top"),
    ("R1", "10k", "R_0402", 2, -2, 0, "top"),
    ("R2", "10k", "R_0402", 4, -2, 0, "top"),
    ("C1", "10uF", "C_0805", 8, -2, -90, "top"),
    ("BT1", "BAT", "Keystone_254", 15, -5, 180, "bottom"),
]
POS_ALL = POS_FITTED + [("C29", "1u", "C_0402", 10, -8, 0, "top")]


class FormatTests(unittest.TestCase):
    def test_fmt_num(self):
        self.assertEqual(bq.fmt_num(-0.0), "0.0")
        self.assertEqual(bq.fmt_num(-1e-9), "0.0")
        self.assertEqual(bq.fmt_num(2), "2.0")
        self.assertEqual(bq.fmt_num(-5), "-5.0")
        self.assertEqual(bq.fmt_num(100), "100.0")
        self.assertEqual(bq.fmt_num(10.5), "10.5")
        self.assertEqual(bq.fmt_num(1.2345678), "1.234568")

    def test_angles(self):
        self.assertEqual(bq.norm_rot(-90), 270.0)
        self.assertEqual(bq.norm_rot(360), 0.0)
        self.assertEqual(bq.norm_rot(-1e-9), 0.0)
        self.assertEqual(bq.norm_rot(450), 90.0)
        self.assertAlmostEqual(bq.circ_diff(10, 350), 20.0)
        self.assertAlmostEqual(bq.circ_diff(0, 360), 0.0)
        self.assertAlmostEqual(bq.circ_diff(-90, 270), 0.0)

    def test_natural_key(self):
        refs = ["R10", "R2", "C29", "R1", "C3"]
        self.assertEqual(sorted(refs, key=bq.natural_key), ["C3", "C29", "R1", "R2", "R10"])

    def test_rotation_convention_matches_kicad(self):
        x, y = bq.rotate_local(1, 0, 90)
        self.assertAlmostEqual(x, 0.0)
        self.assertAlmostEqual(y, -1.0)
        x, y = bq.rotate_local(0, 1, 90)
        self.assertAlmostEqual(x, 1.0)
        self.assertAlmostEqual(y, 0.0)
        x, y = bq.rotate_local(1, 0, 180)
        self.assertAlmostEqual(x, -1.0)
        self.assertAlmostEqual(y, 0.0)
        fp = one_footprint({})
        fp = parse(make_board([footprint("X1", 10, 20, rot=90)])).footprints[0]
        x, y = bq.board_point(fp, 1, 0)
        self.assertAlmostEqual(x, 10.0)
        self.assertAlmostEqual(y, 19.0)

    def test_values_equal(self):
        self.assertTrue(bq.values_equal(1.0, 1.0000001))
        self.assertFalse(bq.values_equal(1.0, 1.1))
        self.assertTrue(bq.values_equal({"a": [1, 2.0]}, {"a": [1.0, 2]}))
        self.assertFalse(bq.values_equal({"a": 1}, {"b": 1}))
        self.assertFalse(bq.values_equal([1, 2], [1, 2, 3]))
        self.assertTrue(bq.values_equal("x", "x"))
        self.assertFalse(bq.values_equal("<absent>", 5))

    def test_write_json_is_sorted_with_trailing_newline(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.json"
            bq.write_json(path, {"b": 1, "a": [1, 2]})
            text = path.read_text(encoding="utf-8")
        self.assertTrue(text.endswith("}\n"))
        self.assertLess(text.index('"a"'), text.index('"b"'))
        self.assertIn("\n  ", text)

    def test_write_csv_uses_lf_and_no_bom(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.csv"
            bq.write_csv(path, ["A", "B"], [["x", 1], ["y,z", "\u00e9"]])
            data = path.read_bytes()
        self.assertEqual(data, 'A,B\nx,1\n"y,z",\u00e9\n'.encode("utf-8"))

    def test_sha256_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = put(Path(tmp) / "x.bin", "abc")
            self.assertEqual(tuple(bq.sha256_file(path)), (hashlib.sha256(b"abc").hexdigest(), 3))

    def test_report_overall_precedence(self):
        report = bq.Report()
        self.assertEqual(report.overall(), "PASS")
        report.add("a", "PASS")
        report.add("b", "INFO")
        self.assertEqual(report.overall(), "PASS")
        report.add("c", "WARN", "careful")
        self.assertEqual(report.overall(), "WARN")
        report.add("d", "FAIL", "broken")
        self.assertEqual(report.overall(), "FAIL")
        data = report.to_dict()
        self.assertEqual(data["schema"], bq.REPORT_SCHEMA)
        self.assertEqual(data["overall"], "FAIL")
        self.assertEqual(data["counts"], {"FAIL": 1, "INFO": 1, "PASS": 1, "WARN": 1})
        self.assertEqual([c["name"] for c in data["checks"]], ["a", "b", "c", "d"])
        self.assertEqual(data["checks"][3], {"name": "d", "status": "FAIL", "detail": "broken"})


class BoardAParseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = parse(board_a())
        cls.by_ref = {f.ref: f for f in cls.board.footprints}

    def test_footprint_flags(self):
        b = self.by_ref
        self.assertEqual(b["R1"].name, "R_0402")
        self.assertEqual(b["R1"].side, "top")
        self.assertEqual(b["BT1"].side, "bottom")
        self.assertTrue(b["C29"].dnp)
        self.assertTrue(b["C29"].in_pos_all)
        self.assertFalse(b["C29"].in_pos_fitted)
        self.assertFalse(b["C29"].in_bom)
        self.assertFalse(b["C29"].fitted)
        self.assertTrue(b["MH1"].board_only)
        self.assertFalse(b["MH1"].in_pos_all)
        self.assertFalse(b["TP1"].fitted)
        self.assertTrue(b["BT1"].fitted)
        self.assertTrue(b["R10"].fitted)

    def test_exclusion_reasons(self):
        b = self.by_ref
        self.assertEqual(list(b["R1"].exclusion_reasons()), [])
        self.assertEqual(list(b["C29"].exclusion_reasons()), ["dnp"])
        self.assertEqual(list(b["TP1"].exclusion_reasons()), ["exclude_from_bom", "exclude_from_pos_files"])
        self.assertEqual(list(b["MH1"].exclusion_reasons()),
                         ["exclude_from_bom", "exclude_from_pos_files", "board_only"])

    def test_pad_indices_are_zero_based(self):
        self.assertEqual([p.index for p in self.by_ref["R1"].pads], [0, 1])
        self.assertEqual(self.by_ref["R1"].pads[1].net, "N1")
        self.assertEqual(self.by_ref["C1"].pads[0].angle, -90.0)

    def test_metrics(self):
        m = bq.board_metrics(self.board)
        self.assertEqual(m["pcb.footprints"], 9)
        self.assertEqual(m["pcb.pos_all"], 6)
        self.assertEqual(m["pcb.pos_fitted"], 5)
        self.assertEqual(m["pcb.bom_refs"], 5)
        self.assertEqual(m["pcb.cpl_refs"], 5)
        self.assertEqual(m["pcb.fitted"], 5)
        self.assertEqual(m["pcb.fitted_side"], {"top": 4, "bottom": 1})
        self.assertEqual(list(m["pcb.excluded_refs"]), ["C29", "H1", "MH1", "TP1"])
        self.assertEqual(list(m["pcb.dnp_refs"]), ["C29"])
        self.assertEqual(list(m["pcb.board_only_refs"]), ["MH1"])
        self.assertEqual(m["edge.segments"], 4)
        self.assertTrue(m["edge.closed"])
        for got, want in zip(m["edge.bbox"], [0, 0, 20, 10]):
            self.assertAlmostEqual(got, want)
        self.assertAlmostEqual(m["edge.perimeter_mm"], 60.0)
        self.assertAlmostEqual(m["edge.area_mm2"], 200.0)
        self.assertEqual(m["vias.total"], 2)
        self.assertEqual(m["vias.through_FB"], 2)
        self.assertEqual(m["vias.by_size_drill"], {"0.5/0.3": 1, "0.6/0.3": 1})
        self.assertEqual(m["vias.capped_filled_flags"], 1)
        self.assertEqual(m["holes.PTH.total"], 3)
        self.assertEqual(m["holes.PTH.by_tool"], {"0.300 round": 2, "2.200 round": 1})
        self.assertEqual(m["holes.NPTH.total"], 1)
        self.assertEqual(m["holes.NPTH.by_tool"], {"0.650 round": 1})
        self.assertAlmostEqual(m["stackup.copper_mm"], 0.07)
        self.assertAlmostEqual(m["stackup.dielectric_mm"], 0.1)
        self.assertAlmostEqual(m["stackup.total_mm"], 0.17)
        self.assertEqual(m["via_in_pad.pairs"], 1)
        self.assertEqual(m["via_in_pad.fully_inside"], 1)

    def test_via_in_pad_pair(self):
        (pair,) = bq.via_in_pad(self.board)
        self.assertEqual(pair["pad"], "R1.2")
        self.assertEqual(pair["via_net"], "N1")
        self.assertEqual(pair["pad_net"], "N1")
        self.assertTrue(pair["fully_inside"])
        self.assertTrue(pair["fitted"])

    def test_via_census(self):
        census = bq.via_census(self.board.vias)
        self.assertEqual(census["total"], 2)
        self.assertEqual(census["capped_filled_flags"], 1)

    def test_expected_holes(self):
        holes = bq.expected_holes(self.board)
        self.assertEqual(bq.tool_table(holes, True), {"0.300 round": 2, "2.200 round": 1})
        self.assertEqual(bq.tool_table(holes, False), {"0.650 round": 1})
        h1 = next(h for h in holes if h.source == "H1.0")
        self.assertFalse(h1.plated)
        self.assertAlmostEqual(h1.x, 18.0)
        self.assertAlmostEqual(h1.y, 1.5)

    def test_parse_board_sets_sha256(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = put(Path(tmp) / "b.kicad_pcb", board_a())
            board = bq.parse_board(path)
            self.assertEqual(board.sha256, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_stackup_sums_sublayers(self):
        text = make_board(setup=(
            '(setup (stackup (layer "F.Cu" (type "copper") (thickness 0.035)) '
            '(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01)) '
            '(layer "dielectric 1" (type "core") (thickness 0.2) addsublayer (thickness 0.7) '
            'addsublayer (thickness 0.2)) '
            '(layer "B.Cu" (type "copper") (thickness 0.035))))'))
        summary = bq.stackup_summary(loads(text))
        self.assertAlmostEqual(summary["copper_mm"], 0.07)
        self.assertAlmostEqual(summary["dielectric_mm"], 1.1)
        self.assertAlmostEqual(summary["other_mm"], 0.01)
        self.assertAlmostEqual(summary["total_mm"], 1.17)
        self.assertAlmostEqual(summary["general_thickness_mm"], 1.6)
        self.assertIsNone(bq.stackup_summary(loads(make_board())))


class ParseErrorTests(unittest.TestCase):
    def test_rejects_non_pcb(self):
        with self.assertRaises(ValueError):
            parse("(kicad_sch (version 1))")

    def test_rejects_aux_axis_origin(self):
        with self.assertRaises(ValueError):
            parse(make_board(setup="(setup (aux_axis_origin 10 10))"))

    def test_rejects_duplicate_references(self):
        with self.assertRaises(ValueError):
            parse(make_board([footprint("R1", 0, 0), footprint("R1", 5, 5)]))

    def test_rejects_missing_reference(self):
        text = make_board(['(footprint "Lib:X" (layer "F.Cu") (at 0 0))'])
        with self.assertRaises(ValueError):
            parse(text)

    def test_rejects_hole_pad_on_bottom_footprint(self):
        pads = [pad(1, "thru_hole", "circle", w=1.5, h=1.5, drill="0.8")]
        with self.assertRaises(ValueError):
            parse(make_board([footprint("J9", 0, 0, layer="B.Cu", attrs="through_hole", pads=pads)]))

    def test_rejects_drill_offset_only_when_nonzero(self):
        def board_with(drill):
            pads = [pad(1, "thru_hole", "circle", w=1.5, h=1.5, drill=drill)]
            return make_board([footprint("J9", 0, 0, attrs="through_hole", pads=pads)])

        parsed = parse(board_with("0.8 (offset 0 0)"))
        self.assertEqual(parsed.footprints[0].pads[0].drill, (0.8, 0.8))
        for drill in ("0.8 (offset 0.1 0)", "oval 1.7 0.6 (offset 0 0.2)"):
            with self.subTest(drill=drill), self.assertRaises(ValueError):
                parse(board_with(drill))

    def test_pcbway_type_from_pad_kinds(self):
        smd = footprint("U1", 0, 0, pads=[pad(1)])
        tht = footprint("U2", 5, 0, attrs="through_hole",
                        pads=[pad(1, "thru_hole", "circle", w=1.5, h=1.5, drill="0.8")])
        both = footprint("U3", 10, 0, attrs="through_hole", pads=[
            pad(1), pad(2, "thru_hole", "circle", w=1.5, h=1.5, drill="0.8")])
        board = parse(make_board([smd, tht, both]))
        kinds = {f.ref: bq.pcbway_type([f]) for f in board.footprints}
        self.assertEqual(kinds, {"U1": "SMD", "U2": "THT", "U3": "SMD+THT"})


class HoleTests(unittest.TestCase):
    def holes_of(self, *pads, rot=90, attrs="through_hole"):
        board = parse(make_board([footprint("R1", 10, 20, rot=rot, attrs=attrs, pads=list(pads))]))
        return bq.pad_holes(board.footprints[0])

    def ends(self, hole):
        return sorted([(round(hole.x, 4), round(hole.y, 4)), (round(hole.x2, 4), round(hole.y2, 4))])

    def test_round_hole_follows_footprint_rotation(self):
        (h,) = self.holes_of(pad(1, "thru_hole", "circle", x=1, w=1.5, h=1.5, drill="0.8"))
        self.assertTrue(h.plated)
        self.assertAlmostEqual(h.dia, 0.8)
        self.assertAlmostEqual(h.x, 10.0)
        self.assertAlmostEqual(h.y, 19.0)
        self.assertIsNone(h.x2)
        self.assertEqual(h.source, "R1.1")

    def test_slot_uses_absolute_pad_angle(self):
        (h,) = self.holes_of(pad(1, "thru_hole", "oval", x=1, ang=270, w=2.2, h=1.1, drill="oval 1.7 0.6"))
        self.assertAlmostEqual(h.dia, 0.6)
        self.assertEqual(self.ends(h), [(10.0, 18.45), (10.0, 19.55)])

    def test_slot_without_angle_is_horizontal(self):
        (h,) = self.holes_of(pad(1, "thru_hole", "oval", x=1, w=2.2, h=1.1, drill="oval 1.7 0.6"))
        self.assertEqual(self.ends(h), [(9.45, 19.0), (10.55, 19.0)])

    def test_slot_with_tall_drill_turns_with_angle(self):
        (v,) = self.holes_of(pad(1, "thru_hole", "oval", x=1, w=1.1, h=2.2, drill="oval 0.6 1.7"))
        self.assertEqual(self.ends(v), [(10.0, 18.45), (10.0, 19.55)])
        (z,) = self.holes_of(pad(1, "thru_hole", "oval", x=1, ang=90, w=1.1, h=2.2, drill="oval 0.6 1.7"))
        self.assertEqual(self.ends(z), [(9.45, 19.0), (10.55, 19.0)])

    def test_unplated_and_unnumbered_pads(self):
        holes = self.holes_of(
            pad("", "thru_hole", "circle", w=1.5, h=1.5, drill="0.8"),
            pad(2, "np_thru_hole", "circle", x=3, w=0.65, h=0.65, drill="0.65"),
        )
        self.assertEqual([(h.plated, h.source) for h in holes], [(True, "R1.0"), (False, "R1.2")])

    def test_tool_table_labels_slots(self):
        holes = [bq.Hole(True, 0.3, 0, 0), bq.Hole(True, 0.3, 1, 1), bq.Hole(True, 0.6, 0, 0, 0, 1),
                 bq.Hole(False, 0.65, 5, 5)]
        self.assertEqual(bq.tool_table(holes, True), {"0.300 round": 2, "0.600 slot": 1})
        self.assertEqual(bq.tool_table(holes, False), {"0.650 round": 1})


class ExcellonTests(unittest.TestCase):
    def test_parses_hits_slots_and_function(self):
        parsed = bq.parse_excellon(PTH_TEXT)
        self.assertEqual(parsed.tools, {1: 0.3, 2: 2.2, 3: 0.6})
        self.assertEqual([tuple(round(v, 6) for v in h) for h in parsed.hits],
                         [(0.3, 2.6, 2.0), (0.3, 7.0, 5.0), (2.2, 1.0, 9.0)])
        self.assertEqual([tuple(round(v, 6) for v in s) for s in parsed.slots],
                         [(0.6, 95.675, 74.3, 95.675, 75.1)])
        self.assertTrue(parsed.plated)
        self.assertFalse(bq.parse_excellon(NPTH_TEXT).plated)

    def test_crlf_text_parses_identically(self):
        lf = bq.parse_excellon(PTH_TEXT)
        crlf = bq.parse_excellon(PTH_TEXT.replace("\n", "\r\n"))
        self.assertEqual((lf.tools, lf.hits, lf.slots, lf.plated), (crlf.tools, crlf.hits, crlf.slots, crlf.plated))

    def test_rejects_unsupported_input(self):
        with self.assertRaisesRegex(ValueError, "selected before definition"):
            bq.parse_excellon(PTH_TEXT.replace("T2\nX1Y-9", "T9\nX1Y-9"))
        with self.assertRaises(ValueError):
            bq.parse_excellon(PTH_TEXT.replace("METRIC", "INCH"))
        with self.assertRaisesRegex(ValueError, "unsupported Excellon statement"):
            bq.parse_excellon(PTH_TEXT.replace("G05\nM30", "G05\nM71\nM30"))
        with self.assertRaises(ValueError):
            bq.parse_excellon(PTH_TEXT.replace("decimal", "trailing"))


class DrillCompareTests(unittest.TestCase):
    def setUp(self):
        self.parsed = bq.parse_excellon(PTH_TEXT)
        self.expected = [
            bq.Hole(True, 0.3, 2.6, 2.0, source="v1"),
            bq.Hole(True, 0.3, 7.0, 5.0, source="v2"),
            bq.Hole(True, 2.2, 1.0, 9.0, source="MH1.1"),
            bq.Hole(True, 0.6, 95.675, 74.3, 95.675, 75.1, source="X6.M1"),
            bq.Hole(False, 0.65, 18.0, 1.5, source="H1.1"),
        ]

    def compare(self, expected, parsed=None, plated=True, label="PTH"):
        report = bq.Report()
        bq.compare_drill(report, label, expected, parsed or self.parsed, plated)
        return report, {c["name"]: c for c in report.checks}

    def test_exact_match_passes(self):
        report, checks = self.compare(self.expected)
        self.assertEqual(report.overall(), "PASS")
        for name in ("drill:PTH:round 0.300", "drill:PTH:round 2.200", "drill:PTH:slot 0.600"):
            self.assertEqual(checks[name]["status"], "PASS", name)

    def test_unplated_holes_are_compared_separately(self):
        report, checks = self.compare(self.expected, bq.parse_excellon(NPTH_TEXT), plated=False, label="NPTH")
        self.assertEqual(report.overall(), "PASS")
        self.assertEqual(checks["drill:NPTH:round 0.650"]["status"], "PASS")

    def test_missing_hole_fails(self):
        _, checks = self.compare(self.expected + [bq.Hole(True, 0.3, 50.0, 50.0, source="v3")])
        self.assertEqual(checks["drill:PTH:round 0.300"]["status"], "FAIL")
        self.assertIn("missing", checks["drill:PTH:round 0.300"]["detail"])

    def test_offset_beyond_tolerance_fails_and_within_passes(self):
        far = [bq.Hole(True, 0.3, 2.61, 2.0)] + self.expected[1:]
        _, checks = self.compare(far)
        self.assertEqual(checks["drill:PTH:round 0.300"]["status"], "FAIL")
        near = [bq.Hole(True, 0.3, 2.601, 2.0)] + self.expected[1:]
        _, checks = self.compare(near)
        self.assertEqual(checks["drill:PTH:round 0.300"]["status"], "PASS")

    def test_slot_endpoint_order_is_irrelevant(self):
        flipped = self.expected[:3] + [bq.Hole(True, 0.6, 95.675, 75.1, 95.675, 74.3)]
        _, checks = self.compare(flipped)
        self.assertEqual(checks["drill:PTH:slot 0.600"]["status"], "PASS")

    def test_function_mismatch_fails(self):
        _, checks = self.compare(self.expected, bq.parse_excellon(NPTH_TEXT))
        self.assertEqual(checks["drill:PTH:function"]["status"], "FAIL")


class OutlineTests(unittest.TestCase):
    def analyze(self, edges, parts=()):
        return bq.analyze_outline(loads(make_board(parts, (), edges)))

    def test_closed_rectangle(self):
        r = self.analyze(rect(0, 0, 20, 10))
        self.assertEqual(count(r["segments"]), 4)
        self.assertEqual(count(r["components"]), 1)
        self.assertEqual(count(r["bad_degree_nodes"]), 0)
        self.assertEqual(count(r["crossings"]), 0)
        self.assertEqual(count(r["unsupported"]), 0)
        self.assertTrue(r["closed"])
        for got, want in zip(r["bbox"], [0, 0, 20, 10]):
            self.assertAlmostEqual(got, want)
        self.assertAlmostEqual(r["perimeter"], 60.0)
        self.assertAlmostEqual(r["area"], 200.0)
        self.assertEqual(sorted(r["widths"]), [0.05])

    def test_open_outline_is_not_closed(self):
        r = self.analyze(rect(0, 0, 20, 10)[:3])
        self.assertFalse(r["closed"])
        self.assertEqual(count(r["bad_degree_nodes"]), 2)

    def test_disjoint_loops_are_not_one_outline(self):
        r = self.analyze(rect(0, 0, 5, 5) + rect(10, 0, 15, 5))
        self.assertEqual(count(r["components"]), 2)
        self.assertFalse(r["closed"])

    def test_self_crossing_loop_is_flagged(self):
        r = self.analyze([edge(0, 0, 10, 10), edge(10, 10, 10, 0), edge(10, 0, 0, 10), edge(0, 10, 0, 0)])
        self.assertTrue(r["closed"])
        self.assertTrue(count(r["crossings"]))

    def test_unsupported_edge_items_are_reported(self):
        arc = (f'(gr_arc (start 0 0) (mid 1 1) (end 2 0) (stroke (width 0.05) (type default)) '
               f'(layer "Edge.Cuts") (uuid "{uid()}"))')
        self.assertEqual(list(self.analyze(rect(0, 0, 20, 10) + [arc])["unsupported"]), ["gr_arc"])
        fp_line = (f'(footprint "Lib:X" (layer "F.Cu") (uuid "{uid()}") (at 0 0) '
                   f'(property "Reference" "U1") (property "Value" "X") '
                   f'(fp_line (start 0 0) (end 1 0) (stroke (width 0.05) (type default)) '
                   f'(layer "Edge.Cuts") (uuid "{uid()}")))')
        r = self.analyze(rect(0, 0, 20, 10), [fp_line])
        self.assertTrue(any("fp_line" in item for item in r["unsupported"]))

    def test_non_edge_lines_are_ignored(self):
        r = self.analyze(rect(0, 0, 20, 10) + [edge(0, 0, 5, 5, layer="F.SilkS")])
        self.assertEqual(count(r["segments"]), 4)
        self.assertTrue(r["closed"])


class ViaInPadTests(unittest.TestCase):
    def test_pad_shapes_and_rotation(self):
        parts = [
            footprint("U1", 5, 5, pads=[pad(1, w=1, h=1)]),
            footprint("U2", 20, 5, pads=[pad(1, shape="circle", w=1, h=1)]),
            footprint("U3", 30, 5, pads=[pad(1, ang=90, w=2, h=1)]),
        ]
        ids = {name: f"{name * 8}-0000-0000-0000-000000000000" for name in "abcdefg"}
        vias = [
            via(5.1, 5.0, 0.6, 0.3, "A", uuid=ids["a"]),
            via(5.45, 5.0, 0.6, 0.3, "A", uuid=ids["b"]),
            via(7, 7, 0.6, 0.3, "A", uuid=ids["c"]),
            via(20.2, 5, 0.3, 0.2, "A", uuid=ids["d"]),
            via(20.45, 5, 0.3, 0.2, "A", uuid=ids["e"]),
            via(30, 5.8, 0.3, 0.2, "A", uuid=ids["f"]),
            via(30.8, 5, 0.3, 0.2, "A", uuid=ids["g"]),
        ]
        board = parse(make_board(parts, vias))
        found = {p["via"]: p for p in bq.via_in_pad(board)}
        self.assertEqual(sorted(found), ["aaaaaaaa", "bbbbbbbb", "dddddddd", "eeeeeeee", "ffffffff"])
        self.assertEqual({k: v["fully_inside"] for k, v in found.items()},
                         {"aaaaaaaa": True, "bbbbbbbb": False, "dddddddd": True,
                          "eeeeeeee": False, "ffffffff": True})
        self.assertEqual(found["aaaaaaaa"]["pad"], "U1.1")
        self.assertEqual(found["dddddddd"]["pad"], "U2.1")
        self.assertEqual(found["ffffffff"]["pad"], "U3.1")


class RegisterTests(unittest.TestCase):
    GOOD = {"schema": bq.REGISTER_SCHEMA, "entries": [
        {"mpn": " PMEG2020AEA,115 ", "lcsc": "C389354", "note": "n1"},
        {"mpn": "AO3400A", "lcsc": "C20917"},
    ]}

    def load(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            return bq.load_register(put(Path(tmp) / "register.json", json.dumps(data)))

    def test_load_keys_are_normalised(self):
        register = self.load(self.GOOD)
        self.assertEqual(sorted(register), ["ao3400a", "pmeg2020aea,115"])
        self.assertEqual(register["ao3400a"]["lcsc"], "C20917")

    def test_load_rejects_bad_registers(self):
        bad_schema = dict(self.GOOD, schema="other")
        duplicate = dict(self.GOOD, entries=self.GOOD["entries"] + [{"mpn": "ao3400a", "lcsc": "C1111"}])
        bad_code = dict(self.GOOD, entries=[{"mpn": "X", "lcsc": "20917"}])
        for data in (bad_schema, duplicate, bad_code):
            with self.assertRaises(ValueError):
                self.load(data)

    def test_resolution_order(self):
        register = self.load(self.GOOD)
        code, provenance, notes = bq.resolve_lcsc(
            one_footprint({"MPN": "PMEG2020AEA,115", "LCSC": "C389354"}), register)
        self.assertEqual((code, provenance), ("C389354", "pcb-property"))
        self.assertIn("register agrees", notes)

        code, provenance, notes = bq.resolve_lcsc(
            one_footprint({"MPN": "PMEG2020AEA,115", "LCSC": "C111111"}), register)
        self.assertEqual((code, provenance), ("C111111", "pcb-property"))
        self.assertTrue(any(n.startswith("register-conflict") and "C389354" in n for n in notes))

        code, provenance, notes = bq.resolve_lcsc(
            one_footprint({"MPN": "PMEG2020AEA,115", "LCSC": "ABC"}), register)
        self.assertEqual((code, provenance), ("", "invalid-pcb-property"))
        self.assertTrue(any("invalid LCSC property" in n for n in notes))

        code, provenance, notes = bq.resolve_lcsc(one_footprint({"MPN": "pmeg2020aea,115"}), register)
        self.assertEqual((code, provenance), ("C389354", "register"))
        self.assertIn("n1", notes)

        self.assertEqual(bq.resolve_lcsc(one_footprint({"MPN": "UNKNOWN"}), register), ("", "unresolved", []))


class RowCompareTests(unittest.TestCase):
    def setUp(self):
        board = parse(board_a())
        fitted = [f for f in board.footprints if f.in_pos_fitted]
        self.expected = {f.ref: f for f in fitted}
        self.rows = [bq.Row(f.ref, f.x, -f.y, f.rot, f.side, f.value, f.name) for f in fitted]

    def compare(self, rows):
        report = bq.Report()
        bq.compare_rows(report, "pos", rows, self.expected)
        return {c["name"]: c for c in report.checks}

    def replaced(self, index, **changes):
        rows = list(self.rows)
        rows[index] = rows[index]._replace(**changes)
        return rows

    def test_exact_rows_pass(self):
        checks = self.compare(self.rows)
        self.assertEqual(checks["pos:rows"]["status"], "PASS")

    def test_rotation_is_compared_modulo_360(self):
        self.assertEqual(self.compare(self.replaced(0, rot=self.rows[0].rot + 360))["pos:rows"]["status"], "PASS")
        self.assertEqual(self.compare(self.replaced(0, rot=self.rows[0].rot + 90))["pos:rows"]["status"], "FAIL")

    def test_position_and_side_mismatches_fail(self):
        self.assertEqual(self.compare(self.replaced(1, x=self.rows[1].x + 0.01))["pos:rows"]["status"], "FAIL")
        self.assertEqual(self.compare(self.replaced(1, y=self.rows[1].y + 0.01))["pos:rows"]["status"], "FAIL")
        self.assertEqual(self.compare(self.replaced(1, side="bottom"))["pos:rows"]["status"], "FAIL")

    def test_missing_extra_and_duplicate_rows_fail(self):
        missing = self.compare(self.rows[1:])["pos:rows"]
        self.assertEqual(missing["status"], "FAIL")
        self.assertIn("missing", missing["detail"])
        extra = self.compare(self.rows + [bq.Row("Z9", 0, 0, 0, "top", "v", "p")])["pos:rows"]
        self.assertEqual(extra["status"], "FAIL")
        self.assertIn("extra", extra["detail"])
        duplicate = self.compare(self.rows + [self.rows[0]])["pos:rows"]
        self.assertEqual(duplicate["status"], "FAIL")
        self.assertIn("duplicate", duplicate["detail"])

    def test_text_difference_only_warns(self):
        checks = self.compare(self.replaced(0, pkg="WRONG"))
        self.assertEqual(checks["pos:rows"]["status"], "PASS")
        self.assertEqual(checks["pos:text"]["status"], "WARN")


class FlashTests(unittest.TestCase):
    def setUp(self):
        self.board = parse(make_board([
            footprint("BT2", 88.375, 100, rot=180, layer="B.Cu", value="BAT", lib="Lib:Keystone", pads=[
                pad(1, x=-3, layers=BOT, net="VBAT"), pad(1, x=3, layers=BOT, net="VBAT")]),
            footprint("R1", 10, 10, value="R", lib="Lib:R", pads=[pad(1, x=-0.5, net="GND"), pad(2, x=0.5, net="N1")]),
        ]))
        self.bottom = [(91.375, -100.0, "BT2", "1", "VBAT"), (85.375, -100.0, "BT2", "1", "VBAT")]
        self.top = [(9.5, -10.0, "R1", "1", "GND"), (10.5, -10.0, "R1", "2", "N1")]

    def compare(self, flashes, layer):
        return bq.compare_flashes(self.board.footprints, flashes, layer)

    def assert_only(self, result, *keys):
        for key in ("position_mismatch", "net_mismatch", "unknown_ref", "missing_flash"):
            self.assertEqual(bool(count(result[key])), key in keys, key)

    def test_duplicate_pad_numbers_are_matched_by_position(self):
        result = self.compare(self.bottom, "B.Cu")
        self.assertEqual(count(result["flashes"]), 2)
        self.assert_only(result)
        self.assert_only(self.compare(self.top, "F.Cu"))

    def test_missing_flash_is_reported(self):
        self.assert_only(self.compare(self.bottom[:1], "B.Cu"), "missing_flash")

    def test_position_mismatch_is_reported(self):
        shifted = [(91.385, -100.0, "BT2", "1", "VBAT"), self.bottom[1]]
        result = self.compare(shifted, "B.Cu")
        self.assertIn("position_mismatch", [k for k in result if count(result[k])])
        self.assertTrue(any("BT2.1" in item for item in result["position_mismatch"]))

    def test_net_mismatch_is_reported(self):
        result = self.compare([(91.375, -100.0, "BT2", "1", "OTHER"), self.bottom[1]], "B.Cu")
        self.assert_only(result, "net_mismatch")
        self.assertTrue(any("gerber 'OTHER' vs board 'VBAT'" in item for item in result["net_mismatch"]))

    def test_gerber_no_connect_marker_matches_a_pad_without_a_net(self):
        board = parse(make_board([
            footprint("X6", 20, 20, value="USB", lib="Lib:USB", attrs="through_hole", pads=[
                pad("M1", kind="thru_hole", shape="oval", x=-2, w=1, h=2, drill="oval 0.6 1.4"),
                pad("S1", x=2, net="GND")]),
        ]))
        no_net = (18.0, -20.0, "X6", "M1", "N/C")
        grounded = (22.0, -20.0, "X6", "S1", "GND")
        clean = bq.compare_flashes(board.footprints, [no_net, grounded], "F.Cu")
        self.assertEqual(clean["net_mismatch"], [])
        self.assertEqual(clean["position_mismatch"], [])

    def test_gerber_no_connect_marker_does_not_hide_a_real_board_net(self):
        board = parse(make_board([
            footprint("R1", 10, 10, value="R", lib="Lib:R", pads=[pad(1, x=-0.5, net="GND"), pad(2, x=0.5)]),
        ]))
        result = bq.compare_flashes(board.footprints, [(9.5, -10.0, "R1", "1", "N/C"),
                                                       (10.5, -10.0, "R1", "2", "GND")], "F.Cu")
        self.assertEqual(len(result["net_mismatch"]), 2)
        self.assertTrue(any("gerber 'N/C' vs board 'GND'" in item for item in result["net_mismatch"]))
        self.assertTrue(any("gerber 'GND' vs board ''" in item for item in result["net_mismatch"]))

    def test_unknown_reference_is_reported(self):
        result = self.compare(self.top + [(50.0, -50.0, "ZZ9", "1", "GND")], "F.Cu")
        self.assert_only(result, "unknown_ref")

    def test_function_matching_tolerates_job_file_spelling(self):
        self.assertTrue(bq.function_matches("Copper,L1,Top", "Copper,L1,Top"))
        self.assertTrue(bq.function_matches("SolderMask,Top", "Soldermask,Top"))
        self.assertTrue(bq.function_matches("Profile", "Profile,NP"))
        self.assertTrue(bq.function_matches("Paste,Top", "SolderPaste,Top"))
        self.assertFalse(bq.function_matches("Copper,L1,Top", "Copper,L2,Inr"))
        self.assertFalse(bq.function_matches("Profile", "Profile2"))

    def test_flashes_from_stand_in_objects(self):
        class Flash:
            def __init__(self, x, y, attrs):
                self.x, self.y, self.attrs = x, y, attrs

        class Line:
            attrs = {}

        gf = SimpleNamespace(objects=[
            Flash(1.0, -2.0, {".P": ("R1", "1", "Pad1"), ".N": ("GND",)}),
            Flash(3.0, -4.0, {".P": ("R2", "2", "Pad2")}),
            Flash(5.0, -6.0, {}),
            Line(),
        ])
        self.assertEqual(bq.flashes_from_gerber(gf),
                         [(1.0, -2.0, "R1", "1", "GND"), (3.0, -4.0, "R2", "2", None)])

    @unittest.skipUnless(HAVE_GERBONARA, "gerbonara is not installed")
    def test_flashes_from_real_gerber_file(self):
        text = "\n".join([
            "%FSLAX46Y46*%", "%MOMM*%", "%TF.FileFunction,Copper,L1,Top*%", "%ADD10C,1.000000*%",
            "G01*", "%LPD*%", "D10*", "%TO.P,R1,1,Pad1*%", "%TO.N,GND*%", "X1000000Y2000000D03*",
            "%TD*%", "M02*", ""])
        from gerbonara import GerberFile

        with tempfile.TemporaryDirectory() as tmp:
            gf = GerberFile.open(put(Path(tmp) / "t.gtl", text))
            flashes = bq.flashes_from_gerber(gf)
        self.assertEqual([(round(x, 6), round(y, 6), r, n, net) for x, y, r, n, net in flashes],
                         [(1.0, 2.0, "R1", "1", "GND")])


def read_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.reader(fh))


class BuildTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.pcb = put(self.root / "board.kicad_pcb", board_a())
        self.register = put(self.root / "register.json", json.dumps({
            "schema": bq.REGISTER_SCHEMA,
            "entries": [{"mpn": "RC0402FR-0710KL", "lcsc": "C123456", "note": "test"}]}))

    def build(self, out_name="out"):
        out = self.root / out_name
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            rc = bq.cmd_build(Namespace(pcb=self.pcb, register=self.register, out_dir=out))
        return rc, buffer.getvalue(), out

    def test_summary_line_and_outputs(self):
        rc, printed, out = self.build()
        self.assertEqual(rc, 0)
        self.assertEqual(printed, "fitted 5; BOM rows 3 (LCSC resolved 1, unresolved 2); "
                                  "CPL rows 5; conflicts 0; warnings 0\n")
        self.assertEqual(sorted(p.name for p in out.iterdir()),
                         ["cpl.csv", "inventory.json", "jlc-bom.csv", "pcbway-bom.csv", "sourcing-bom.csv"])

    def test_jlc_bom(self):
        _, _, out = self.build()
        rows = read_rows(out / "jlc-bom.csv")
        self.assertEqual(rows[0], bq.JLC_HEADER)
        self.assertEqual(rows[1:], [
            ["BAT 254", "BT1", "Keystone_254", ""],
            ["10uF GRM21BR61C106KE15L", "C1", "C_0805", ""],
            ["10k RC0402FR-0710KL", "R1,R2,R10", "R_0402", "C123456"],
        ])

    def test_sourcing_bom_marks_unresolved_rows(self):
        _, _, out = self.build()
        rows = read_rows(out / "sourcing-bom.csv")
        self.assertEqual(rows[0], bq.SOURCING_HEADER)
        by_designators = {r[0]: dict(zip(bq.SOURCING_HEADER, r)) for r in rows[1:]}
        resolved = by_designators["R1,R2,R10"]
        self.assertEqual((resolved["Qty"], resolved["LCSC"], resolved["Status"]), ("3", "C123456", "VERIFY LIVE"))
        self.assertIn("register", resolved["LCSC provenance"])
        self.assertIn("test", resolved["Notes"])
        for ref in ("BT1", "C1"):
            row = by_designators[ref]
            self.assertEqual((row["LCSC"], row["Status"], row["Notes"]), ("", "NEEDS LCSC CODE", "unresolved"))
            self.assertEqual(row["LCSC provenance"], "unresolved")

    def test_pcbway_bom(self):
        _, _, out = self.build()
        rows = read_rows(out / "pcbway-bom.csv")
        self.assertEqual(rows[0], bq.PCBWAY_HEADER)
        self.assertEqual([r[:3] for r in rows[1:]], [["1", "BT1", "1"], ["2", "C1", "1"], ["3", "R1,R2,R10", "3"]])
        by_designators = {r[1]: dict(zip(bq.PCBWAY_HEADER, r)) for r in rows[1:]}
        self.assertEqual(by_designators["R1,R2,R10"]["Manufacturer"], "Yageo")
        self.assertEqual(by_designators["R1,R2,R10"]["Type"], "SMD")
        self.assertEqual(by_designators["BT1"]["Manufacturer"], "")

    def test_cpl(self):
        _, _, out = self.build()
        rows = read_rows(out / "cpl.csv")
        self.assertEqual(rows[0], bq.CPL_HEADER)
        self.assertEqual(rows[1:], [
            ["BT1", "15.0", "-5.0", "Bottom", "180.0"],
            ["C1", "8.0", "-2.0", "Top", "270.0"],
            ["R1", "2.0", "-2.0", "Top", "0.0"],
            ["R2", "4.0", "-2.0", "Top", "0.0"],
            ["R10", "6.0", "-2.0", "Top", "0.0"],
        ])

    def test_inventory(self):
        _, _, out = self.build()
        inventory = json.loads((out / "inventory.json").read_text(encoding="utf-8"))
        self.assertEqual(inventory["schema"], bq.INVENTORY_SCHEMA)
        self.assertEqual(inventory["counts"], {
            "footprints": 9, "fitted": 5, "bom_rows": 3, "lcsc_resolved_rows": 1, "lcsc_unresolved_rows": 2})
        self.assertEqual([f["ref"] for f in inventory["fitted"]], ["BT1", "C1", "R1", "R2", "R10"])
        c1 = next(f for f in inventory["fitted"] if f["ref"] == "C1")
        self.assertEqual((c1["hints"], c1["side"], c1["rot"]), ({"ROT": "270"}, "top", -90.0))
        self.assertEqual(inventory["excluded"], [
            {"ref": "C29", "reasons": ["dnp"]},
            {"ref": "H1", "reasons": ["exclude_from_bom", "exclude_from_pos_files"]},
            {"ref": "MH1", "reasons": ["exclude_from_bom", "exclude_from_pos_files", "board_only"]},
            {"ref": "TP1", "reasons": ["exclude_from_bom", "exclude_from_pos_files"]},
        ])
        self.assertEqual([u["designators"] for u in inventory["unresolved_lcsc"]], [["BT1"], ["C1"]])
        self.assertEqual(inventory["lcsc_conflicts"], [])

    def test_outputs_are_deterministic(self):
        _, _, first = self.build("first")
        _, _, second = self.build("second")
        for name in ("cpl.csv", "inventory.json", "jlc-bom.csv", "pcbway-bom.csv", "sourcing-bom.csv"):
            self.assertEqual((first / name).read_bytes(), (second / name).read_bytes(), name)
            self.assertNotIn(b"\r\n", (first / name).read_bytes())
            self.assertFalse((first / name).read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_property_register_conflict_is_reported(self):
        parts = [footprint("D4", 0, 0, props={"MPN": "RC0402FR-0710KL", "LCSC": "C999999"}),
                 footprint("D5", 5, 0, props={"MPN": "RC0402FR-0710KL", "LCSC": "C999999"})]
        board = parse(make_board(parts))
        register = bq.load_register(self.register)
        outputs = bq.build_outputs(board, register)
        self.assertEqual([row[3] for row in outputs["jlc"]], ["C999999"])
        self.assertEqual(outputs["inventory"]["lcsc_conflicts"], [
            {"kind": "pcb-vs-register", "mpn": "RC0402FR-0710KL", "pcb_property": "C999999",
             "register": "C123456", "designators": ["D4", "D5"]}])
        self.assertIn("register-conflict: register has C123456", outputs["sourcing"][0][9])

    def test_agreeing_property_is_not_a_conflict(self):
        parts = [footprint("D6", 9, 0, props={"MPN": "RC0402FR-0710KL", "LCSC": "C123456"})]
        outputs = bq.build_outputs(parse(make_board(parts)), bq.load_register(self.register))
        self.assertEqual(outputs["inventory"]["lcsc_conflicts"], [])
        self.assertEqual(outputs["jlc"][0][3], "C123456")

    def test_same_part_with_two_codes_is_reported(self):
        parts = [footprint("R1", 0, 0, value="10k", lib="Lib:R_0402", props={"MPN": "RX", "LCSC": "C111111"}),
                 footprint("R2", 3, 0, value="10k", lib="Lib:R_0402", props={"MPN": "RX", "LCSC": "C222222"})]
        outputs = bq.build_outputs(parse(make_board(parts)), {})
        self.assertEqual(len(outputs["jlc"]), 2)
        self.assertEqual(outputs["inventory"]["lcsc_conflicts"], [
            {"kind": "multiple-codes", "value": "10k", "footprint": "R_0402", "mpn": "RX",
             "lcsc": ["C111111", "C222222"]}])

    def test_summary_counts_property_register_conflicts(self):
        pcb = put(self.root / "conflict.kicad_pcb", make_board(
            [footprint("D4", 0, 0, props={"MPN": "RC0402FR-0710KL", "LCSC": "C999999"})]))
        out = self.root / "conflict-out"
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            rc = bq.cmd_build(Namespace(pcb=pcb, register=self.register, out_dir=out))
        self.assertEqual(rc, 0)
        self.assertIn("conflicts 1;", buffer.getvalue())

    def test_non_ascii_bom_text_is_flagged(self):
        board = parse(make_board([footprint("C1", 0, 0, value="10\u00b5F", lib="Lib:C_0805", props={"MPN": "X1"})]))
        warnings = bq.build_outputs(board, {})["inventory"]["warnings"]
        self.assertEqual(warnings, ["non-ASCII text in BOM row for C1"])


class VerifyTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.pcb = put(self.root / "board.kicad_pcb", board_a())
        register = put(self.root / "register.json", json.dumps({"schema": bq.REGISTER_SCHEMA, "entries": []}))
        self.built = self.root / "built"
        with contextlib.redirect_stdout(io.StringIO()):
            bq.cmd_build(Namespace(pcb=self.pcb, register=register, out_dir=self.built))
        self.export = self.root / "export"
        put(self.export / "drill" / "handbell-PTH.drl", PTH_A)
        put(self.export / "drill" / "handbell-NPTH.drl", NPTH_TEXT)
        put(self.export / "pos" / "pos-all.csv", pos_text(POS_ALL))
        put(self.export / "pos" / "pos-fitted.csv", pos_text(POS_FITTED))

    def verify(self, expect=None, bom=True, cpl=True):
        out = self.root / "verification.json"
        args = Namespace(
            pcb=self.pcb, export_root=self.export, basename="handbell",
            cpl=self.built / "cpl.csv" if cpl else None,
            bom=self.built / "jlc-bom.csv" if bom else None,
            zip=None, receipt=None, expect=expect, out=out, gerbers=False)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = bq.cmd_verify(args)
        return rc, json.loads(out.read_text(encoding="utf-8")), err.getvalue()

    @staticmethod
    def statuses(result, status):
        return sorted(c["name"] for c in result["checks"] if c["status"] == status)

    def test_consistent_export_has_only_package_warnings(self):
        rc, result, err = self.verify()
        self.assertEqual(rc, 0)
        self.assertEqual(result["schema"], bq.REPORT_SCHEMA)
        self.assertEqual(result["overall"], "WARN")
        self.assertEqual(self.statuses(result, "FAIL"), [])
        self.assertIn("gbrjob:found", self.statuses(result, "WARN"))
        self.assertIn("zip:found", self.statuses(result, "WARN"))
        self.assertIn("overall WARN", err)

    def test_records_hashes_with_relative_names(self):
        _, result, _ = self.verify()
        for key, path in (("board.kicad_pcb", self.pcb),
                          ("drill/handbell-PTH.drl", self.export / "drill" / "handbell-PTH.drl"),
                          ("pos/pos-all.csv", self.export / "pos" / "pos-all.csv")):
            data = path.read_bytes()
            self.assertEqual(result["files"][key], {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
        self.assertFalse(any(str(self.root) in key for key in result["files"]))

    def test_expectations_pass_and_fail(self):
        spec = {"schema": bq.EXPECT_SCHEMA, "expect": {
            "pcb.footprints": 9, "pcb.fitted": 5, "pcb.fitted_side": {"top": 4, "bottom": 1},
            "holes.PTH.total": 3, "edge.closed": True, "stackup.total_mm": 0.17}}
        rc, result, _ = self.verify(expect=put(self.root / "expect.json", json.dumps(spec)))
        self.assertEqual(rc, 0)
        self.assertEqual(self.statuses(result, "FAIL"), [])
        self.assertIn("expect:pcb.fitted_side", [c["name"] for c in result["checks"]])
        spec["expect"]["vias.total"] = 3
        rc, result, _ = self.verify(expect=put(self.root / "expect.json", json.dumps(spec)))
        self.assertEqual(rc, 1)
        self.assertEqual(self.statuses(result, "FAIL"), ["expect:vias.total"])

    def test_expectation_schema_is_enforced(self):
        bad = put(self.root / "expect.json", json.dumps({"schema": "other", "expect": {}}))
        with self.assertRaises(ValueError):
            self.verify(expect=bad)

    def test_tampered_position_row_fails(self):
        path = self.export / "pos" / "pos-fitted.csv"
        text = path.read_text(encoding="utf-8")
        put(path, text.replace('"R1","10k","R_0402",2.000000', '"R1","10k","R_0402",2.500000'))
        rc, result, _ = self.verify()
        self.assertEqual(rc, 1)
        self.assertTrue(any(name.endswith(":rows") for name in self.statuses(result, "FAIL")))

    def test_missing_and_moved_drill_data_fail(self):
        (self.export / "drill" / "handbell-NPTH.drl").unlink()
        rc, result, _ = self.verify()
        self.assertEqual(rc, 1)
        self.assertIn("drill:NPTH:file", self.statuses(result, "FAIL"))
        put(self.export / "drill" / "handbell-NPTH.drl", NPTH_TEXT)
        path = self.export / "drill" / "handbell-PTH.drl"
        put(path, path.read_text(encoding="utf-8").replace("X7Y-5", "X7.5Y-5"))
        rc, result, _ = self.verify()
        self.assertEqual(rc, 1)
        self.assertIn("drill:PTH:round 0.300", self.statuses(result, "FAIL"))

    def test_bom_designator_and_header_checks(self):
        path = self.built / "jlc-bom.csv"
        text = path.read_text(encoding="utf-8")
        put(path, text.replace("R1,R2,R10", "R1,R2"))
        rc, result, _ = self.verify()
        self.assertEqual(rc, 1)
        self.assertIn("bom:designators", self.statuses(result, "FAIL"))
        put(path, text.replace("Comment,", "Name,", 1))
        rc, _, _ = self.verify()
        self.assertEqual(rc, 1)


class PackageCheckTests(unittest.TestCase):
    FILES = {"x-F_Cu.gtl": b"top\r\n", "x-B_Cu.gbl": b"bottom\r\n", "x-PTH.drl": b"pth\n", "x-NPTH.drl": b"npth\n"}

    def run_zip(self, mutate):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gdir, ddir = root / "gerbers", root / "drill"
            gdir.mkdir()
            ddir.mkdir()
            for name, data in self.FILES.items():
                (ddir if name.endswith(".drl") else gdir).joinpath(name).write_bytes(data)
            job = {"FilesAttributes": [{"Path": "x-F_Cu.gtl"}, {"Path": "x-B_Cu.gbl"}]}
            zpath = root / "pkg.zip"
            with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
                for name, data in mutate(dict(self.FILES)).items():
                    zf.writestr(name, data)
            report = bq.Report()
            bq.check_zip(report, gdir, ddir, zpath, job, "x")
            return report

    def test_matching_zip_passes(self):
        self.assertEqual(self.run_zip(lambda m: m).overall(), "PASS")

    def test_changed_missing_extra_and_nested_members_fail(self):
        cases = {
            "changed": lambda m: {**m, "x-F_Cu.gtl": b"other"},
            "missing": lambda m: {k: v for k, v in m.items() if k != "x-PTH.drl"},
            "extra": lambda m: {**m, "notes.txt": b"hi"},
            "nested": lambda m: {("sub/" + k if k == "x-B_Cu.gbl" else k): v for k, v in m.items()},
        }
        for label, mutate in cases.items():
            self.assertEqual(self.run_zip(mutate).overall(), "FAIL", label)

    def test_receipt_rehash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = put(root / "drill" / "a.txt", "abc")
            entry = {"path": "drill\\a.txt", "name": "a.txt", "bytes": 3,
                     "sha256": hashlib.sha256(b"abc").hexdigest()}
            receipt = put(root / "receipt.json", json.dumps({"files": [entry]}))
            good = bq.Report()
            bq.check_receipt(good, receipt, root)
            put(target, "abd")
            bad = bq.Report()
            bq.check_receipt(bad, receipt, root)
        self.assertEqual(good.overall(), "PASS")
        self.assertEqual(bad.overall(), "FAIL")


class HashlistTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.root = self.base / "root"
        self.a = put(self.root / "a.csv", "one,two\r\n")
        self.b = put(self.root / "sub" / "b.bin", "bytes")
        self.out = self.base / "MANIFEST.sha256"

    @staticmethod
    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def run_cmd(self, out=None, check=None, names=()):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = bq.cmd_hashlist(Namespace(root=self.root, out=out, check=check, names=list(names)))
        return rc, stdout.getvalue(), stderr.getvalue()

    def write_manifest(self, names=("a.csv", "sub/b.bin")):
        rc, _, err = self.run_cmd(out=self.out, names=names)
        self.assertEqual((rc, err), (0, ""))

    def test_write_emits_lf_only_sha256sum_lines_in_order(self):
        self.write_manifest(["sub/b.bin", "a.csv"])
        raw = self.out.read_bytes()
        self.assertNotIn(b"\r", raw)
        self.assertTrue(raw.endswith(b"\n"))
        self.assertEqual(
            raw.decode("utf-8").splitlines(),
            [f"{self.digest(self.b)}  sub/b.bin", f"{self.digest(self.a)}  a.csv"],
        )

    def test_round_trip_check_passes_and_reports_count(self):
        self.write_manifest()
        rc, stdout, stderr = self.run_cmd(check=self.out)
        self.assertEqual((rc, stderr), (0, ""))
        self.assertIn("2 ok, 0 problem(s)", stdout)

    def test_changed_byte_is_reported_as_mismatch(self):
        self.write_manifest()
        put(self.a, "one,twX\r\n")
        rc, stdout, stderr = self.run_cmd(check=self.out)
        self.assertEqual(rc, 1)
        self.assertIn("a.csv: sha256 mismatch", stderr)
        self.assertIn("1 ok, 1 problem(s)", stdout)

    def test_missing_file_fails_check(self):
        self.write_manifest()
        self.b.unlink()
        rc, _, stderr = self.run_cmd(check=self.out)
        self.assertEqual(rc, 1)
        self.assertIn("sub/b.bin: missing", stderr)

    def test_check_tolerates_crlf_binary_marker_and_uppercase_hash(self):
        lines = [f"{self.digest(self.a)}  a.csv", f"{self.digest(self.b).upper()} *sub/b.bin"]
        put(self.out, "\r\n".join(lines) + "\r\n")
        rc, stdout, stderr = self.run_cmd(check=self.out)
        self.assertEqual((rc, stderr), (0, ""))
        self.assertIn("2 ok", stdout)

    def test_write_rejects_unusable_names_and_writes_nothing(self):
        for names in (["a.csv", "absent.txt"], ["../a.csv"], ["/etc/hosts"], ["C:/a.csv"],
                      ["sub\\b.bin"], ["sub//b.bin"], ["./a.csv"], ["a.csv", "a.csv"], [""]):
            with self.subTest(names=names):
                rc, stdout, stderr = self.run_cmd(out=self.out, names=names)
                self.assertEqual((rc, stdout), (2, ""))
                self.assertIn("hashlist:", stderr)
                self.assertFalse(self.out.exists())

    def test_write_refuses_to_list_itself_and_keeps_the_old_file(self):
        manifest = put(self.root / "MANIFEST.sha256", "old")
        rc, _, stderr = self.run_cmd(out=manifest, names=["a.csv", "MANIFEST.sha256"])
        self.assertEqual(rc, 2)
        self.assertIn("cannot list itself", stderr)
        self.assertEqual(manifest.read_bytes(), b"old")

    def test_name_arguments_are_required_for_out_and_rejected_for_check(self):
        self.assertEqual(self.run_cmd(out=self.out, names=[])[0], 2)
        self.assertFalse(self.out.exists())
        self.write_manifest()
        self.assertEqual(self.run_cmd(check=self.out, names=["a.csv"])[0], 2)

    def test_check_rejects_malformed_empty_and_escaping_manifests(self):
        good = f"{self.digest(self.a)}  a.csv"
        cases = {
            "malformed": (good + "\nnot a hash line\n", "not a '<sha256>  <name>' line"),
            "empty": ("\n\n", "no checksum lines found"),
            "escape": (f"{self.digest(self.a)}  ../root/a.csv\n", "'..' segment"),
            "absolute": (f"{self.digest(self.a)}  /a.csv\n", "not a relative POSIX path"),
        }
        for label, (text, expected) in cases.items():
            with self.subTest(label):
                put(self.out, text)
                rc, _, stderr = self.run_cmd(check=self.out)
                self.assertEqual(rc, 1)
                self.assertIn(expected, stderr)

    def test_missing_manifest_or_root_is_a_usage_error(self):
        self.assertEqual(self.run_cmd(check=self.base / "absent.sha256")[0], 2)
        self.root = self.base / "no-such-root"
        self.assertEqual(self.run_cmd(out=self.out, names=["a.csv"])[0], 2)

    def test_command_line_wiring(self):
        def main(*argv):
            stderr = io.StringIO()
            with mock.patch.object(sys, "argv", ["build_quote_package.py", *argv]), \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
                try:
                    return bq.main(), stderr.getvalue()
                except SystemExit as exc:
                    return exc.code, stderr.getvalue()

        root = str(self.root)
        self.assertEqual(main("hashlist", "--root", root, "--out", str(self.out), "a.csv", "sub/b.bin"), (0, ""))
        self.assertEqual(main("hashlist", "--root", root, "--check", str(self.out)), (0, ""))
        self.assertEqual(main("hashlist", "--root", root)[0], 2)
        self.assertEqual(main("hashlist", "--root", root, "--out", str(self.out), "--check", str(self.out), "a.csv")[0], 2)


if __name__ == "__main__":
    unittest.main()
