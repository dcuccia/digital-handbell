"""Real positive and mutation controls for check_quilter_comparison_inputs."""

from __future__ import annotations

import copy
import os
import unittest

import check_quilter_comparison_inputs as checker
from kicad_sexpr import apply_edits, loads


class QuilterCheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = os.environ.get("QUILTER_TEST_PROFILE", "four-3313")
        if cls.profile not in checker.R2_HASHES:
            raise ValueError(f"unknown QUILTER_TEST_PROFILE: {cls.profile}")
        cls.package = checker.R2 / cls.profile
        cls.text = (cls.package / "handbell.kicad_pcb").read_text(encoding="utf-8-sig")
        cls.project = checker.read_json(cls.package / "handbell.kicad_pro")
        cls.sch = (cls.package / "handbell.kicad_sch").read_bytes()

    def check(self, text=None, project=None, mode="r2"):
        return checker.check_text(
            self.profile, self.text if text is None else text,
            self.project if project is None else project, self.sch, mode=mode,
            verify_hashes=True,
        )

    def assert_rejected(self, changed, category):
        self.assertNotEqual(changed, self.text, "mutation must change input")
        result = self.check(changed)
        self.assertFalse(result.passed, result.as_dict())
        self.assertTrue(any(category in error for error in result.errors), result.errors)

    def replace_node(self, predicate, replacement):
        root = loads(self.text)
        node = next(x for x in root.walk() if predicate(x))
        return apply_edits(self.text, [(node.start, node.end, replacement(self.text[node.start:node.end]))])

    def test_positive_r2_baseline(self):
        result = self.check()
        self.assertTrue(result.passed, result.as_dict())

    def test_positive_ordering_and_parked_translation(self):
        root = loads(self.text)
        fp = next(x for x in root.children("footprint")
                  if x.properties()["Reference"] not in
                  checker.read_json(checker.WORKFLOW)["selected_comparison_retention"]["fixed_references"])
        at = fp.child("at")
        old = at.atoms()
        moved = f"(at {float(old[1]) + 1} {float(old[2]) + 2}" + (
            f" {old[3]}" if len(old) > 3 else "") + ")"
        text = apply_edits(self.text, [(at.start, at.end, moved)])
        manifest = checker.read_json(self.package / "input-manifest.json")
        manifest = copy.deepcopy(manifest)
        ref = fp.properties()["Reference"]
        manifest["move_map"][ref]["to_native_xy_mm"] = [
            float(old[1]) + 1, float(old[2]) + 2]
        # Layer child ordering is explicitly set-valued.
        text = text.replace('(layers "B.Cu" "B.Mask" "B.Paste")',
                            '(layers "B.Paste" "B.Cu" "B.Mask")', 1)
        ordered = loads(text)
        order_pad = next(
            p for f in ordered.children("footprint") for p in f.children("pad")
            if p.child("pintype") is not None and p.child("pinfunction") is not None)
        first, second = order_pad.child("pintype"), order_pad.child("pinfunction")
        lo, hi = min(first.start, second.start), max(first.end, second.end)
        text = apply_edits(text, [(lo, hi,
            text[second.start:second.end] + "\n" + text[first.start:first.end])])
        result = checker.check_text(
            self.profile, text, self.project, self.sch, mode="r2",
            baseline_manifest=manifest, verify_hashes=True)
        self.assertTrue(result.passed, result.as_dict())

    def test_drop_retained(self):
        root = loads(self.text)
        item = next(x for x in root.children() if x.head in {"segment", "via"})
        self.assert_rejected(apply_edits(self.text, [(item.start, item.end, "")]),
                             "retained_membership")

    def test_pad_net_edit(self):
        changed = self.replace_node(
            lambda x: x.head == "pad" and x.child("net") is not None,
            lambda s: apply_edits(
                s,
                [(loads(s).child("net").start, loads(s).child("net").end,
                  '(net 999 "MUTATED_NET")')]))
        self.assert_rejected(changed, "pad_definition")

    def test_pad_number_01_is_lexical_identity(self):
        root = loads(self.text)
        pad = next(p for f in root.children("footprint") for p in f.children("pad")
                   if p.atoms()[1] == "1")
        original = self.text[pad.start:pad.end]
        mutated = original.replace('(pad "1"', '(pad "01"', 1)
        self.assertNotEqual(mutated, original)
        changed = apply_edits(self.text, [(pad.start, pad.end, mutated)])
        self.assert_rejected(changed, "pad_definition")

    def test_fixed_pose_shift(self):
        fixed = set(checker.read_json(checker.WORKFLOW)[
            "selected_comparison_retention"]["fixed_references"])
        root = loads(self.text)
        fp = next(x for x in root.children("footprint")
                  if x.properties()["Reference"] in fixed)
        at = fp.child("at")
        values = at.atoms()
        replacement = f"(at {float(values[1]) + .1} {values[2]}" + (
            f" {values[3]}" if len(values) > 3 else "") + ")"
        self.assert_rejected(
            apply_edits(self.text, [(at.start, at.end, replacement)]), "footprint_pose")

    def test_source_footprint_nonpad_semantics(self):
        root = loads(self.text)
        fp = next(f for f in root.children("footprint")
                  if f.child("attr") is not None and
                  "exclude_from_bom" in f.child("attr").atoms())
        attr = fp.child("attr")
        changed = apply_edits(
            self.text,
            [(attr.start, attr.end,
              self.text[attr.start:attr.end].replace("exclude_from_bom", "", 1))])
        self.assert_rejected(changed, "footprint_source_definition")

        fp = next(f for f in root.children("footprint")
                  if any(x.child("start") is not None
                         for x in f.children() if x.head.startswith("fp_")))
        graphic = next(x for x in fp.children()
                       if x.head.startswith("fp_") and x.child("start") is not None)
        start = graphic.child("start")
        values = start.atoms()
        changed = apply_edits(
            self.text,
            [(start.start, start.end,
              f"(start {float(values[1]) + .01} {values[2]})")])
        self.assert_rejected(changed, "footprint_source_definition")

    def test_copper_layer_and_geometry(self):
        root = loads(self.text)
        segment = next(x for x in root.children("segment"))
        layer = segment.child("layer")
        old_layer = layer.atoms()[1]
        new_layer = "B.Cu" if old_layer != "B.Cu" else "F.Cu"
        changed = apply_edits(
            self.text, [(layer.start, layer.end, f'(layer "{new_layer}")')])
        self.assert_rejected(changed, "retained_record")
        start = segment.child("start")
        xy = start.atoms()
        changed = apply_edits(
            self.text, [(start.start, start.end,
                         f"(start {float(xy[1]) + .01} {xy[2]})")])
        self.assert_rejected(changed, "retained_record")

    def test_guard_flag_and_polygon(self):
        root = loads(self.text)
        zone = next(z for z in root.children("zone")
                    if (z.value("name") or "").startswith("CONTACT_METAL_GUARD_"))
        keepout = zone.child("keepout")
        changed = apply_edits(
            self.text, [(keepout.start, keepout.end,
                         self.text[keepout.start:keepout.end].replace(
                             "(vias not_allowed)", "(vias allowed)", 1))])
        self.assert_rejected(changed, "contact_guard")
        pt = zone.child("polygon").child("pts").children("xy")[0]
        xy = pt.atoms()
        changed = apply_edits(
            self.text, [(pt.start, pt.end, f"(xy {float(xy[1]) + .01} {xy[2]})")])
        self.assert_rejected(changed, "contact_guard")

    def test_same_count_outline_coordinate(self):
        root = loads(self.text)
        edge = next(x for x in root.children() if x.head in {"gr_line", "gr_arc"}
                    and x.value("layer") == "Edge.Cuts")
        start = edge.child("start")
        xy = start.atoms()
        changed = apply_edits(
            self.text, [(start.start, start.end,
                         f"(start {float(xy[1]) + .01} {xy[2]})")])
        self.assert_rejected(changed, "outline_geometry")

    def final_text(self):
        root = loads(self.text)
        additions = []
        for ref, polygon in checker.reservation_spec().items():
            points = " ".join(f"(xy {x:.6f} {y:.6f})" for x, y in polygon)
            flags = " ".join(
                f"({key} {checker.RESERVATION_FLAGS[key]})"
                for key in ("tracks", "vias", "pads", "copperpour", "footprints"))
            additions.append(
                f'(zone (layer "F.Cu") '
                f'(uuid "{checker.ident(self.profile + "/footprint-reservation/" + ref)}") '
                f'(name "FOOTPRINT_RESERVATION_{ref}") (hatch edge 0.5) '
                f'(connect_pads (clearance 0)) (min_thickness 0.25) '
                f'(keepout {flags}) (polygon (pts {points})))')
        return self.text[:root.end - 1] + "\n" + "\n".join(additions) + "\n)\n"

    def test_positive_final_in_memory_fixture(self):
        result = self.check(self.final_text(), mode="final")
        self.assertTrue(result.passed, result.as_dict())

    def test_reservation_layer_and_polygon(self):
        good = self.final_text()
        root = loads(good)
        zone = next(z for z in root.children("zone")
                    if (z.value("name") or "") == "FOOTPRINT_RESERVATION_MH1")
        layer = zone.child("layer")
        changed = apply_edits(good, [(layer.start, layer.end, '(layer "B.Cu")')])
        result = checker.check_text(
            self.profile, changed, self.project, self.sch, mode="final")
        self.assertFalse(result.passed)
        self.assertTrue(any("reservation:MH1" in x for x in result.errors), result.errors)
        pt = zone.child("polygon").child("pts").children("xy")[0]
        xy = pt.atoms()
        changed = apply_edits(good, [(pt.start, pt.end,
                                     f"(xy {float(xy[1]) - .01} {xy[2]})")])
        result = checker.check_text(
            self.profile, changed, self.project, self.sch, mode="final")
        self.assertFalse(result.passed)
        self.assertTrue(any("reservation:MH1" in x for x in result.errors), result.errors)

    def test_dielectric_fields(self):
        for field, replacement in (
                ("thickness", "(thickness 0.2)"),
                ("material", '(material "wrong")'),
                ("epsilon_r", "(epsilon_r 9.9)"),
                ("type", '(type "core")')):
            root = loads(self.text)
            dielectric = next(x for x in root.child("setup").child("stackup").children("layer")
                              if x.atoms()[1] == "dielectric 1")
            node = dielectric.child(field)
            changed = apply_edits(self.text, [(node.start, node.end, replacement)])
            self.assert_rejected(changed, "stackup_row")

    def test_plane_net_and_layer(self):
        root = loads(self.text)
        plane = next(z for z in root.children("zone")
                     if (z.value("name") or "").startswith("PROTECTED_GND_"))
        net = plane.child("net")
        changed = apply_edits(self.text, [(net.start, net.end, '(net "CELL_NEG")')])
        self.assert_rejected(changed, "plane_definition")
        layer = plane.child("layer")
        changed = apply_edits(self.text, [(layer.start, layer.end, '(layer "In2.Cu")')])
        self.assert_rejected(changed, "plane_definition")

    def test_missing_extra_footprint_pad_zone(self):
        root = loads(self.text)
        fp = root.children("footprint")[0]
        self.assert_rejected(apply_edits(self.text, [(fp.start, fp.end, "")]),
                             "footprint_population")
        root = loads(self.text)
        fp = root.children("footprint")[0]
        pad = fp.children("pad")[0]
        self.assert_rejected(apply_edits(self.text, [(pad.start, pad.end, "")]),
                             "pad_population")
        extra_pad = self.text[pad.start:pad.end].replace(
            pad.value("uuid"), "00000000-0000-0000-0000-000000000003", 1)
        changed = apply_edits(self.text, [(fp.end - 1, fp.end - 1, extra_pad)])
        self.assert_rejected(changed, "pad_population")
        source, _, _ = checker.source_context()
        source_rule_ids = {
            z.value("uuid") for z in source.children("zone")
            if z.child("keepout") is not None
        }
        root = loads(self.text)
        zone = next(z for z in root.children("zone")
                    if z.value("uuid") in source_rule_ids)
        self.assert_rejected(apply_edits(self.text, [(zone.start, zone.end, "")]),
                             "source_rule")
        extra_zone = (
            '(zone (layer "F.Cu") '
            '(uuid "00000000-0000-0000-0000-000000000002") '
            '(name "UNEXPECTED_ZONE") (hatch edge 0.5) '
            '(polygon (pts (xy 1 1) (xy 2 1) (xy 2 2))))')
        root = loads(self.text)
        changed = self.text[:root.end - 1] + extra_zone + "\n)"
        self.assert_rejected(changed, "unexpected_zone_population")
        root = loads(self.text)
        extra = self.text[root.children("footprint")[0].start:
                          root.children("footprint")[0].end].replace(
                              root.children("footprint")[0].value("uuid"),
                              "00000000-0000-0000-0000-000000000001", 1)
        changed = self.text[:root.end - 1] + extra + "\n)"
        self.assert_rejected(changed, "footprint:duplicate_or_missing")

    def test_unexpected_copper_arc_and_edge_shape(self):
        root = loads(self.text)
        arc = (
            '(arc (start 1 1) (mid 2 2) (end 3 1) (width 0.2) '
            '(layer "F.Cu") (net 1 "GND") '
            '(uuid "00000000-0000-0000-0000-000000000004"))')
        changed = self.text[:root.end - 1] + arc + "\n)"
        self.assert_rejected(changed, "retained_membership")
        shape = (
            '(gr_circle (center 1 1) (end 2 1) '
            '(stroke (width 0.05) (type default)) (fill no) '
            '(layer "Edge.Cuts") '
            '(uuid "00000000-0000-0000-0000-000000000005"))')
        changed = self.text[:root.end - 1] + shape + "\n)"
        self.assert_rejected(changed, "outline_population_or_identity")

    def test_plane_rejects_extra_polygon_and_layer(self):
        root = loads(self.text)
        plane = next(z for z in root.children("zone")
                     if (z.value("name") or "").startswith("PROTECTED_GND_"))
        insert = plane.end - 1
        extra_polygon = "(polygon (pts (xy 1 1) (xy 2 1) (xy 2 2)))"
        changed = apply_edits(self.text, [(insert, insert, extra_polygon)])
        self.assert_rejected(changed, "plane_definition")
        changed = apply_edits(self.text, [(insert, insert, '(layer "F.Cu")')])
        self.assert_rejected(changed, "plane_definition")

if __name__ == "__main__":
    unittest.main()
