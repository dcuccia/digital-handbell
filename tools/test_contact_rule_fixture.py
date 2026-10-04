# SPDX-License-Identifier: MIT
import copy
import json
from pathlib import Path
import tempfile
import unittest

from build_contact_rule_fixture import FEED, MASK, SOURCE, build_feed_fixture, build_fixture, digest, write_fixture
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

    def test_feed_import_preserves_every_selected_subtree_without_synthetic_controls(self):
        ledger = json.loads(FEED.read_bytes())
        text, report = build_feed_fixture(self.source, self.mask, ledger)
        original, fixture = loads(self.source), loads(text)
        self.assertEqual(2, len(fixture.children("footprint")))
        self.assertEqual(10, len(fixture.children("via")))
        self.assertEqual(30, len(fixture.children("segment")))
        self.assertEqual(8, len(fixture.children("zone")))
        self.assertTrue(all(z.child("keepout") is not None for z in fixture.children("zone")))
        self.assertEqual(42, len(report["retained_subtree_sha256"]))
        self.assertEqual([], report["controls"])
        self.assertTrue(report["import_only"])
        self.assertEqual(
            {u for b in ledger["blocks"] for u in b["segment_uuids"]},
            {s.value("uuid") for s in fixture.children("segment")},
        )
        for item_id in report["retained_subtree_sha256"]:
            before = next(n for n in original.children() if n.value("uuid") == item_id)
            after = next(n for n in fixture.children() if n.value("uuid") == item_id)
            self.assertEqual(self.source[before.start:before.end], text[after.start:after.end])
        baseline, _ = build_fixture(self.source, self.mask)
        for head in ("layers", "gr_line"):
            self.assertEqual(
                [baseline[n.start:n.end] for n in loads(baseline).children(head)],
                [text[n.start:n.end] for n in fixture.children(head)],
            )
        base_guards = [z for z in loads(baseline).children("zone") if z.child("keepout")]
        self.assertEqual(
            [baseline[z.start:z.end] for z in base_guards],
            [text[z.start:z.end] for z in fixture.children("zone")],
        )

    def test_feed_import_rejects_wrong_segments_and_via_geometry(self):
        ledger = json.loads(FEED.read_bytes())
        ledger["blocks"][0]["segment_uuids"][0] = "not-a-source-uuid"
        with self.assertRaisesRegex(ValueError, "segment UUIDs"):
            build_feed_fixture(self.source, self.mask, ledger)
        ledger = json.loads(FEED.read_bytes())
        ledger["blocks"][0]["records_sha256"] = "wrong-record-hash"
        with self.assertRaisesRegex(ValueError, "segment geometry"):
            build_feed_fixture(self.source, self.mask, ledger)
        ledger = json.loads(FEED.read_bytes())
        ledger["blocks"][0]["existing_via_candidates"][0]["drill_mm"] = 0.35
        with self.assertRaisesRegex(ValueError, "via geometry"):
            build_feed_fixture(self.source, self.mask, ledger)

    def test_feed_import_write_hash_gate_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "import-fixture"
            feed = FEED.read_bytes()
            with self.assertRaisesRegex(ValueError, "Feed evidence hash"):
                write_fixture(output, self.source_bytes, self.mask_bytes, feed + b"\n")
            self.assertFalse(output.exists())
            report = write_fixture(output, self.source_bytes, self.mask_bytes, feed)
            self.assertEqual(digest(feed), report["input_sha256"]["feed_candidate"])
            board = output / "contact-rule-fixture.kicad_pcb"
            before = board.read_bytes()
            with self.assertRaises(FileExistsError):
                write_fixture(output, self.source_bytes, self.mask_bytes, feed)
            self.assertEqual(before, board.read_bytes())

    def test_original_fixture_bytes_remain_unchanged(self):
        text, _ = build_fixture(self.source, self.mask)
        self.assertEqual(
            "a54f71f8db307cabe0f88d7964e20533e64ce374d0e072c1ab24b51a3cf1a892",
            digest(text.encode()),
        )


if __name__ == "__main__":
    unittest.main()
