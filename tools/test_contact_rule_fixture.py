# SPDX-License-Identifier: MIT
import copy
import json
from pathlib import Path
import tempfile
import unittest

from build_contact_rule_fixture import MASK, SOURCE, build_fixture, write_fixture
from kicad_sexpr import loads


class ContactRuleFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_bytes = SOURCE.read_bytes()
        cls.mask_bytes = MASK.read_bytes()
        cls.source = cls.source_bytes.decode("utf-8-sig")
        cls.mask = json.loads(cls.mask_bytes)

    def test_exact_source_subtrees_and_name_only_nets(self):
        text, report = build_fixture(self.source, self.mask)
        original, fixture = loads(self.source), loads(text)
        self.assertEqual(2, len(fixture.children("footprint")))
        self.assertEqual(8, len(fixture.children("via")))
        self.assertEqual(7, len(report["retained_subtree_sha256"]))
        self.assertTrue(
            {row["uuid"] for row in self.mask["protected_process_vias"]}
            <= {item.value("uuid") for item in fixture.children("via")}
        )
        for item_id in report["retained_subtree_sha256"]:
            before = next(n for n in original.children() if n.value("uuid") == item_id)
            after = next(n for n in fixture.children() if n.value("uuid") == item_id)
            self.assertEqual(self.source[before.start:before.end], text[after.start:after.end])
        nets = [n.atoms() for n in fixture.walk() if n.head == "net"]
        self.assertTrue(nets)
        self.assertTrue(all(len(n) == 2 for n in nets))
        self.assertEqual({"VBAT", "/CELL_NEG", "GND"}, {n[1] for n in nets})

    def test_every_guard_flag_and_single_coordinate_translation(self):
        text, _ = build_fixture(self.source, self.mask)
        zones = [z for z in loads(text).children("zone") if z.child("keepout")]
        areas = self.mask["domains"]["native_via_only_rule_areas_expanded_each_edge_0_25_mm"]
        self.assertEqual(8, len(zones))
        for zone, area in zip(zones, areas):
            self.assertEqual("B.Cu", zone.value("layer"))
            self.assertEqual("CONTACT_METAL_GUARD_" + area["name"], zone.value("name"))
            self.assertEqual(
                {"tracks": "not_allowed", "vias": "not_allowed", "pads": "allowed",
                 "copperpour": "not_allowed", "footprints": "allowed"},
                {n.head: n.atoms()[1] for n in zone.child("keepout").children()},
            )
            pts = zone.child("polygon").child("pts").children("xy")
            actual = [[float(v) for v in point.atoms()[1:]] for point in pts]
            x0, x1 = area["x_min_mm"] + 100, area["x_max_mm"] + 100
            y0, y1 = area["y_min_mm"] + 100, area["y_max_mm"] + 100
            for observed, expected in zip(actual, [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]):
                for a, b in zip(observed, expected):
                    self.assertAlmostEqual(a, b, places=6)

    def test_missing_seed_rejected(self):
        mask = copy.deepcopy(self.mask)
        mask["protected_process_vias"][0]["uuid"] = "not-a-source-uuid"
        with self.assertRaisesRegex(ValueError, "UUIDs"):
            build_fixture(self.source, mask)

    def test_changed_seed_geometry_rejected(self):
        mask = copy.deepcopy(self.mask)
        mask["protected_process_vias"][0]["diameter_mm"] += 0.1
        with self.assertRaisesRegex(ValueError, "geometry"):
            build_fixture(self.source, mask)

    def test_unsupported_version_rejected(self):
        with self.assertRaisesRegex(ValueError, "version"):
            build_fixture(self.source.replace("20260206", "20241229", 1), self.mask)

    def test_unreviewed_input_rejected_before_directory_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "new-fixture"
            with self.assertRaisesRegex(ValueError, "PCB bytes"):
                write_fixture(output, self.source_bytes + b"\n", self.mask_bytes)
            self.assertFalse(output.exists())
            with self.assertRaisesRegex(ValueError, "Mask evidence"):
                write_fixture(output, self.source_bytes, self.mask_bytes + b"\n")
            self.assertFalse(output.exists())

    def test_writes_only_static_fixture_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "new-fixture"
            report = write_fixture(output, self.source_bytes, self.mask_bytes)
            self.assertEqual(0, report["fixture_native_loads"])
            self.assertEqual("NOT_RUN", report["native_drc_or_reload"])
            self.assertEqual(
                {"contact-rule-fixture.kicad_pcb", "contact-rule-fixture.kicad_pro", "static-fixture-report.json"},
                {path.name for path in output.iterdir()},
            )
            before = (output / "contact-rule-fixture.kicad_pcb").read_bytes()
            with self.assertRaises(FileExistsError):
                write_fixture(output, self.source_bytes, self.mask_bytes)
            self.assertEqual(before, (output / "contact-rule-fixture.kicad_pcb").read_bytes())


if __name__ == "__main__":
    unittest.main()
