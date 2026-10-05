import unittest

from private_plane_control import PRIVATE, build_profile
from kicad_sexpr import loads


BASE = """(kicad_pcb
 (version 20260206)
 (generator "pcbnew")
 (generator_version "10.0")
 (general (thickness 1.6))
 (paper "A4")
 (layers
\t\t(0 "F.Cu" signal)
\t\t(4 "In1.Cu" signal)
\t\t(6 "In2.Cu" signal)
\t\t(2 "B.Cu" signal))
 (setup)
 %s
)"""


def fixture_items():
    fps = []
    for i in range(8):
        pads = "".join(
            f'(pad "{j}" smd rect (at 0 0) (size 1 1) (layers "F.Cu") (uuid "00000000-0000-4000-8000-{i:06d}{j:06d}"))'
            for j in range(1 if i >= 4 else 2)
        )
        fps.append(
            f'(footprint "x" (layer "F.Cu") (uuid "10000000-0000-4000-8000-{i:012d}") '
            f'(at {i} 0) {pads})'
        )
    segs = [
        f'(segment (start 0 {i}) (end 1 {i}) (width .2) (layer "F.Cu") (net "GND") '
        f'(uuid "20000000-0000-4000-8000-{i:012d}"))' for i in range(10)
    ]
    vias = [
        f'(via (at {i} 0) (size .6) (drill .3) (layers "F.Cu" "B.Cu") '
        f'(net "GND") (uuid "30000000-0000-4000-8000-{i:012d}"))' for i in range(4)
    ]
    areas = [
        f'(zone (layer "F.Cu") (uuid "40000000-0000-4000-8000-{i:012d}") '
        f'(name "K{i}") (hatch edge .5) (keepout (tracks not_allowed)) '
        f'(polygon (pts (xy 0 0)(xy 1 0)(xy 1 1)(xy 0 1))))' for i in range(23)
    ]
    return "\n".join(fps + segs + vias + areas)


class TestBuild(unittest.TestCase):
    def test_profiles(self):
        base = BASE % fixture_items()
        expected = {
            "four-positive": (2, 23),
            "six-positive": (4, 27),
            "six-negative": (4, 26),
        }
        for name, (inners, rules) in expected.items():
            text, layers = build_profile(base, name)
            root = loads(text)
            self.assertEqual(len(layers), inners)
            self.assertEqual(sum(z.child("keepout") is not None for z in root.children("zone")), rules)
            self.assertEqual(len(root.children("via")), 5)
            self.assertEqual(sum(z.child("keepout") is None for z in root.children("zone")), inners)
        negative, _ = build_profile(base, "six-negative")
        self.assertNotIn(f"PRIVATE_VIA_{next(iter(PRIVATE))}_In3.Cu", negative)


if __name__ == "__main__":
    unittest.main()
