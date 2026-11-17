"""Generate the speaker-plug (JST ACHL) build-guide illustrations.

The ACHLR-02V-S housing is modelled as a prism extruded from an outline
read off JST's published top-view dimensions (eACHL.pdf): 3.75 + 0.3 mm
long, 2.6 mm wide, 1.12 mm tall, 1.2 mm cavity pitch. The flat wire-entry
face carries the two holes; the opposite "rough" end carries the latch and
mating features. The triangle on the top face marks cavity 1. Shapes are
simplified documentation art, not a manufacturer model or a fit claim.

Coordinates (mm): X along the plug from the wire-entry face (0) toward the
rough end, Y toward cavity 1 (+0.6) / cavity 2 (-0.6), Z up out of the
triangle face. Looking into the holes with the triangle face up, cavity 1
is the LEFT hole.

Run from the repository root:  python tools/draw_achl_illustrations.py
"""

from __future__ import annotations

import math
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "docs" / "images" / "showcase"

OUTLINE = [
    (0.0, 1.316), (1.5, 1.316), (1.895, 1.732), (2.763, 1.732), (2.763, 1.316),
    (4.079, 1.316), (4.079, 0.932), (3.805, 0.932), (3.805, 0.221),
    (4.089, 0.221), (4.089, -0.200), (3.805, -0.200), (3.805, -1.547),
    (3.395, -1.547), (3.395, -1.305), (2.789, -1.305), (2.789, -1.716),
    (1.895, -1.716), (1.5, -1.305), (0.0, -1.305),
]
HEIGHT = 1.12
PITCH = 1.2
HOLE_Z = 0.60
HOLE_W, HOLE_H, HOLE_R = 0.74, 0.78, 0.28
WIRE_OD = 0.6

INK = "#193247"
BODY = {"top": "#f3eedf", "side": "#d9cfb6", "face": "#e6dcc4", "edge": "#6b5a3a"}
RED = "#d63a2f"

STYLE = """
    <style>
      text { font-family: Arial, sans-serif; fill: #193247; }
      .heading { font-size: 32px; font-weight: bold; }
      .label { font-size: 23px; font-weight: bold; }
      .body { font-size: 20px; }
      .note { font-size: 18px; }
      .small { font-size: 16px; }
      .call { font-size: 19px; fill: #8a3b12; font-weight: bold; }
      .warn { font-size: 20px; font-weight: bold; fill: #a3341a; }
    </style>
    <linearGradient id="gold" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#f6dd8f"/><stop offset="0.45" stop-color="#d9a945"/>
      <stop offset="1" stop-color="#9c7124"/>
    </linearGradient>
    <linearGradient id="wire" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffffff"/><stop offset="0.6" stop-color="#eef1f3"/>
      <stop offset="1" stop-color="#b7c0c7"/>
    </linearGradient>
    <linearGradient id="redwire" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#f08a80"/><stop offset="0.6" stop-color="#d63a2f"/>
      <stop offset="1" stop-color="#9b231b"/>
    </linearGradient>
    <linearGradient id="steel" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#9aa6b0"/><stop offset="1" stop-color="#3f4a53"/>
    </linearGradient>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto"><path d="M0 0 8 4 0 8" fill="#007f91"/></marker>
"""


def fmt(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


class View:
    """Orthographic camera looking mostly along +X (into the holes)."""

    def __init__(self, ox: float, oy: float, scale: float, az: float = 52.0, el: float = 30.0):
        a, e = math.radians(az), math.radians(el)
        self.d = (math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), -math.sin(e))
        r = (self.d[1], -self.d[0], 0.0)
        n = math.hypot(r[0], r[1])
        self.r = (r[0] / n, r[1] / n, 0.0)
        dx, dy, dz = self.d
        rx, ry, rz = self.r
        self.u = (ry * dz - rz * dy, rz * dx - rx * dz, rx * dy - ry * dx)
        self.ox, self.oy, self.s = ox, oy, scale

    def p(self, x: float, y: float, z: float) -> tuple[float, float]:
        sx = x * self.r[0] + y * self.r[1] + z * self.r[2]
        sy = x * self.u[0] + y * self.u[1] + z * self.u[2]
        return self.ox + sx * self.s, self.oy - sy * self.s

    def depth(self, x: float, y: float, z: float) -> float:
        return x * self.d[0] + y * self.d[1] + z * self.d[2]

    def poly(self, pts, **attrs) -> str:
        d = " ".join(f"{fmt(a)},{fmt(b)}" for a, b in (self.p(*q) for q in pts))
        extra = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
        return f'<polygon points="{d}" {extra}/>'


def hole_ring(cy: float, n: int = 24) -> list[tuple[float, float]]:
    """Rounded-rectangle hole outline in the X=0 face (Y, Z)."""
    hw, hh, r = HOLE_W / 2, HOLE_H / 2, HOLE_R
    pts = []
    for cx, cz, a0 in ((hw - r, hh - r, 0), (-hw + r, hh - r, 90), (-hw + r, -hh + r, 180), (hw - r, -hh + r, 270)):
        for i in range(n // 4 + 1):
            a = math.radians(a0 + 90 * i / (n // 4))
            pts.append((cy + cx + r * math.cos(a), HOLE_Z + cz + r * math.sin(a)))
    return pts


def housing(v: View, marks: bool = True, holes: bool = True) -> str:
    out = []
    n = len(OUTLINE)
    faces = []
    for i in range(n):
        (x0, y0), (x1, y1) = OUTLINE[i], OUTLINE[(i + 1) % n]
        nx, ny = -(y1 - y0), (x1 - x0)  # outward normal for this clockwise (Y-up) outline
        if nx * v.d[0] + ny * v.d[1] >= 0:
            continue
        quad = [(x0, y0, 0), (x1, y1, 0), (x1, y1, HEIGHT), (x0, y0, HEIGHT)]
        depth = v.depth((x0 + x1) / 2, (y0 + y1) / 2, HEIGHT / 2)
        fill = BODY["face"] if x0 == x1 == 0.0 else BODY["side"]
        faces.append((depth, quad, fill))
    for _, quad, fill in sorted(faces, key=lambda f: -f[0]):
        out.append(v.poly(quad, fill=fill, stroke=BODY["edge"], stroke_width="2", stroke_linejoin="round"))
    out.append(v.poly([(x, y, HEIGHT) for x, y in OUTLINE], fill=BODY["top"], stroke=BODY["edge"],
                      stroke_width="2.5", stroke_linejoin="round"))
    if holes:
        for cy in (PITCH / 2, -PITCH / 2):
            ring = [(0.0, y, z) for y, z in hole_ring(cy)]
            out.append(v.poly(ring, fill="#3b3226", stroke=BODY["edge"], stroke_width="1.5"))
            inner = [(0.0, cy + (y - cy) * 0.6, HOLE_Z + (z - HOLE_Z) * 0.6 - 0.05) for y, z in hole_ring(cy)]
            out.append(v.poly(inner, fill="#16120c"))
    if marks:
        tri = [(0.45, 0.85, HEIGHT), (0.45, 0.35, HEIGHT), (0.95, 0.6, HEIGHT)]
        out.append(v.poly(tri, fill="none", stroke=INK, stroke_width="2.5", stroke_linejoin="round"))
        box = [(3.0, -0.3, HEIGHT), (3.5, -0.3, HEIGHT), (3.5, -0.9, HEIGHT), (3.0, -0.9, HEIGHT)]
        out.append(v.poly(box, fill="none", stroke=INK, stroke_width="2"))
        cx, cy = v.p(3.25, -0.6, HEIGHT)
        out.append(f'<text x="{fmt(cx)}" y="{fmt(cy + 0.12 * v.s)}" text-anchor="middle" '
                   f'style="font-size:{fmt(0.34 * v.s)}px;font-weight:bold">2</text>')
    return "\n  ".join(out)


def wire_path(pts: list[tuple[float, float]], red: bool, width: float) -> str:
    d = "M" + " L".join(f"{fmt(a)} {fmt(b)}" for a, b in pts)
    colour = RED if red else "#ffffff"
    return (f'<path d="{d}" fill="none" stroke="#526878" stroke-width="{fmt(width + 4)}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="{fmt(width)}" stroke-linecap="round" stroke-linejoin="round"/>')


def wire_curve(d: str, red: bool, width: float) -> str:
    colour = RED if red else "#ffffff"
    return (f'<path d="{d}" fill="none" stroke="#526878" stroke-width="{fmt(width + 4)}" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="{fmt(width)}" stroke-linecap="round"/>')


def wire_pair(d1: str, d2: str, red1: bool, width: float) -> str:
    """Two joined wire segments: outlines first so the join has no seam."""
    out = [f'<path d="{d}" fill="none" stroke="#526878" stroke-width="{fmt(width + 4)}" stroke-linecap="round"/>' for d in (d1, d2)]
    out.append(f'<path d="{d1}" fill="none" stroke="{RED if red1 else "#ffffff"}" stroke-width="{fmt(width)}" stroke-linecap="butt"/>')
    out.append(f'<path d="{d2}" fill="none" stroke="#ffffff" stroke-width="{fmt(width)}" stroke-linecap="butt"/>')
    return "".join(out)


def contact_side(x: float, y: float, s: float, wire_len: float = 2.2, red: bool = False) -> str:
    """Realistic side view of a factory-crimped SACHL contact; wire to the left.

    (x, y) is the contact's wire-end at its centreline; s is px/mm.
    """
    def R(x0, w, h, **a):
        extra = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in a.items())
        return f'<rect x="{fmt(x + x0 * s)}" y="{fmt(y - h / 2 * s)}" width="{fmt(w * s)}" height="{fmt(h * s)}" {extra}/>'

    g = []
    wf = "url(#redwire)" if red else "url(#wire)"
    g.append(f'<rect x="{fmt(x - wire_len * s)}" y="{fmt(y - WIRE_OD / 2 * s)}" width="{fmt((wire_len + 0.3) * s)}" '
             f'height="{fmt(WIRE_OD * s)}" rx="{fmt(0.12 * s)}" fill="{wf}" stroke="#526878" stroke-width="2"/>')
    # Insulation crimp: two wrapped wings.
    g.append(R(0.0, 0.72, 0.86, rx=fmt(0.14 * s), fill="url(#gold)", stroke="#7a5418", stroke_width="2"))
    g.append(f'<path d="M{fmt(x + 0.12 * s)} {fmt(y - 0.43 * s)} Q{fmt(x + 0.42 * s)} {fmt(y)} {fmt(x + 0.18 * s)} {fmt(y + 0.43 * s)} '
             f'M{fmt(x + 0.40 * s)} {fmt(y - 0.43 * s)} Q{fmt(x + 0.70 * s)} {fmt(y)} {fmt(x + 0.46 * s)} {fmt(y + 0.43 * s)}" '
             f'fill="none" stroke="#7a5418" stroke-width="1.6"/>')
    g.append(R(0.72, 0.16, 0.42, fill="url(#gold)", stroke="#7a5418", stroke_width="1.5"))
    # Wire crimp with serrations.
    g.append(R(0.86, 0.6, 0.62, rx=fmt(0.08 * s), fill="url(#gold)", stroke="#7a5418", stroke_width="2"))
    for k in range(1, 5):
        xx = x + (0.86 + 0.12 * k) * s
        g.append(f'<path d="M{fmt(xx)} {fmt(y - 0.28 * s)} V{fmt(y + 0.28 * s)}" stroke="#a37a2c" stroke-width="1.2"/>')
    # Neck and receptacle box with spring nose.
    g.append(R(1.46, 0.6, 0.22, fill="url(#gold)", stroke="#7a5418", stroke_width="1.5"))
    g.append(f'<path d="M{fmt(x + 2.0 * s)} {fmt(y - 0.25 * s)} H{fmt(x + 2.95 * s)} '
             f'Q{fmt(x + 3.2 * s)} {fmt(y - 0.25 * s)} {fmt(x + 3.2 * s)} {fmt(y)} '
             f'Q{fmt(x + 3.2 * s)} {fmt(y + 0.25 * s)} {fmt(x + 2.95 * s)} {fmt(y + 0.25 * s)} H{fmt(x + 2.0 * s)} Z" '
             f'fill="url(#gold)" stroke="#7a5418" stroke-width="2"/>')
    g.append(R(2.35, 0.5, 0.18, fill="#8a6420", opacity="0.55"))
    g.append(f'<path d="M{fmt(x + 2.05 * s)} {fmt(y + 0.25 * s)} L{fmt(x + 2.35 * s)} {fmt(y + 0.42 * s)}" '
             f'stroke="#7a5418" stroke-width="3" stroke-linecap="round"/>')
    return "\n  ".join(g)


def contact_iso(v: View, cy: float, x_tip: float, red: bool = False, wire_to: float | None = None) -> str:
    """A contact on the cavity axis whose spring tip is at X=x_tip (negative = outside)."""
    out = []
    z = HOLE_Z
    tail = x_tip - 3.2
    if wire_to is not None:
        a, b = v.p(wire_to, cy, z), v.p(tail + 0.2, cy, z)
        out.append(wire_path([a, b], red, WIRE_OD * v.s))
    vis_tip = min(x_tip, 0.0)
    if vis_tip > tail:
        a, b = v.p(tail, cy, z), v.p(vis_tip, cy, z)
        out.append(f'<path d="M{fmt(a[0])} {fmt(a[1])} L{fmt(b[0])} {fmt(b[1])}" stroke="#7a5418" '
                   f'stroke-width="{fmt(0.62 * v.s + 3)}" stroke-linecap="butt"/>')
        out.append(f'<path d="M{fmt(a[0])} {fmt(a[1])} L{fmt(b[0])} {fmt(b[1])}" stroke="#ddb04f" '
                   f'stroke-width="{fmt(0.62 * v.s)}" stroke-linecap="butt"/>')
    return "\n  ".join(out)


def pliers(tip: tuple[float, float], angle_deg: float, length: float = 230, open_px: float = 10) -> str:
    """Needle-nose pliers in screen space; jaws end at tip, handles at angle."""
    a = math.radians(angle_deg)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    tx, ty = tip
    out = []
    for sgn in (1, -1):
        o = sgn * open_px / 2
        jaw = [
            (tx + nx * o, ty + ny * o),
            (tx + ux * 70 + nx * (o + sgn * 9), ty + uy * 70 + ny * (o + sgn * 9)),
            (tx + ux * 110 + nx * sgn * 14, ty + uy * 110 + ny * sgn * 14),
            (tx + ux * length + nx * sgn * 34, ty + uy * length + ny * sgn * 34),
            (tx + ux * length + nx * sgn * 18, ty + uy * length + ny * sgn * 18),
            (tx + ux * 110 + nx * sgn * 4, ty + uy * 110 + ny * sgn * 4),
            (tx + ux * 70 + nx * (o + sgn * 2), ty + uy * 70 + ny * (o + sgn * 2)),
            (tx + nx * o, ty + ny * o),
        ]
        out.append('<polygon points="' + " ".join(f"{fmt(p)},{fmt(q)}" for p, q in jaw)
                   + '" fill="url(#steel)" stroke="#2b333a" stroke-width="1.5"/>')
    px, py = tx + ux * 110, ty + uy * 110
    out.append(f'<circle cx="{fmt(px)}" cy="{fmt(py)}" r="7" fill="#5e6a73" stroke="#2b333a" stroke-width="1.5"/>')
    return "\n  ".join(out)


def finger(v: View, side: int) -> str:
    """A fingertip pressing on the +Y (side=1, behind) or -Y (side=-1, in front) wall."""
    c = v.p(2.3, side * 2.55, 0.55)
    tip = v.p(2.3, side * 1.75, 0.55)
    ang = math.degrees(math.atan2(c[1] - tip[1], c[0] - tip[0]))
    rx, ry = 1.0 * v.s, 0.62 * v.s
    cx, cy = tip[0] + (c[0] - tip[0]) * 1.25, tip[1] + (c[1] - tip[1]) * 1.25
    nail = (f'<ellipse cx="{fmt(cx - 0.25 * v.s * math.cos(math.radians(ang)))}" '
            f'cy="{fmt(cy - 0.25 * v.s * math.sin(math.radians(ang)) - 0.12 * v.s)}" rx="{fmt(0.42 * v.s)}" '
            f'ry="{fmt(0.26 * v.s)}" transform="rotate({fmt(ang)} {fmt(cx)} {fmt(cy)})" fill="#f7e1d5" '
            f'stroke="#c99a80" stroke-width="1.5"/>') if side < 0 else ""
    return (f'<ellipse cx="{fmt(cx)}" cy="{fmt(cy)}" rx="{fmt(rx)}" ry="{fmt(ry)}" '
            f'transform="rotate({fmt(ang)} {fmt(cx)} {fmt(cy)})" fill="#ecbd9e" stroke="#a8765a" stroke-width="2"/>' + nail)


def held_housing(v: View) -> str:
    return finger(v, 1) + "\n  " + housing(v) + "\n  " + finger(v, -1)


def axis_angle(v: View, cy: float) -> float:
    """Screen angle (degrees) pointing out of a hole along the wire axis."""
    a, b = v.p(0.0, cy, HOLE_Z), v.p(-1.0, cy, HOLE_Z)
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def panel(x, y, w, h, fill="#f4f7fa") -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{fill}"/>'


def text(x, y, s, cls="body", anchor=None, extra="") -> str:
    a = f' text-anchor="{anchor}"' if anchor else ""
    return f'<text x="{fmt(x)}" y="{fmt(y)}" class="{cls}"{a}{extra}>{s}</text>'


def leader(a, b) -> str:
    return (f'<path d="M{fmt(a[0])} {fmt(a[1])} L{fmt(b[0])} {fmt(b[1])}" stroke="#8a3b12" stroke-width="2"/>'
            f'<circle cx="{fmt(b[0])}" cy="{fmt(b[1])}" r="4" fill="#8a3b12"/>')


def svg(w, h, title, desc, body) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
            f'aria-labelledby="title desc">\n  <title id="title">{title}</title>\n  <desc id="desc">{desc}</desc>\n'
            f'  <defs>{STYLE}  </defs>\n  <rect width="{w}" height="{h}" fill="#fff"/>\n  ' + "\n  ".join(body) + "\n</svg>\n")


def face_on(x0: float, y0: float, s: float) -> list[str]:
    """Straight-on view into the wire-entry face, triangle face up."""
    b = []
    w, h = 2.62, HEIGHT
    left = x0 - 1.316 * s
    b.append(f'<rect x="{fmt(left)}" y="{fmt(y0 - h * s)}" width="{fmt(w * s)}" height="{fmt(h * s)}" rx="4" '
             f'fill="{BODY["face"]}" stroke="{BODY["edge"]}" stroke-width="3"/>')
    for cy in (PITCH / 2, -PITCH / 2):
        hx = x0 - cy * s  # +Y (cavity 1) is to the viewer's left
        b.append(f'<rect x="{fmt(hx - HOLE_W / 2 * s)}" y="{fmt(y0 - (HOLE_Z + HOLE_H / 2) * s)}" width="{fmt(HOLE_W * s)}" '
                 f'height="{fmt(HOLE_H * s)}" rx="{fmt(HOLE_R * s)}" fill="#3b3226" stroke="{BODY["edge"]}" stroke-width="2"/>')
    return b


def parts_svg() -> str:
    b = [text(40, 55, "Know the parts: which face is which", "heading"),
         text(40, 92, "Drawn from JST's published outline dimensions, simplified and magnified. No crimping is needed.")]
    # A: isometric housing
    b.append(panel(30, 115, 1140, 430))
    b.append(text(55, 153, "A. Plug housing ACHLR-02V-S: flat face in, rough end out", "label"))
    v = View(590, 405, 80, az=40)
    b.append(housing(v))
    tri = v.p(0.6, 0.6, HEIGHT)
    b.append(leader((330, 215), tri))
    b.append(text(55, 200, "Triangle on top = cavity 1", "call"))
    b.append(text(55, 226, "= VO+ (red lead)", "call"))
    hole = v.p(0, -PITCH / 2, HOLE_Z)
    b.append(leader((330, 470), hole))
    b.append(text(55, 465, "FLAT face, two holes:", "call"))
    b.append(text(55, 491, "contacts go in here", "call"))
    two = v.p(3.25, -0.9, HEIGHT)
    b.append(leader((880, 222), two))
    b.append(text(886, 228, '"2" = cavity 2 = VO-', "call"))
    rough = v.p(4.08, 0.0, HEIGHT * 0.5)
    b.append(leader((880, 380), rough))
    b.append(text(886, 375, "ROUGH end: latch and", "call"))
    b.append(text(886, 401, "mating features.", "call"))
    b.append(text(886, 427, "Never insert here.", "call"))
    b.append(text(55, 528, "Top face points AWAY from the board when plugged in; the wires then lie along the board.", "note"))
    # B: face-on
    b.append(panel(30, 565, 545, 300))
    b.append(text(55, 603, "B. Look into the holes, triangle face up", "label"))
    s = 95
    fx, fy = 300, 780
    b.append(f'<path d="M{fx - 0.6 * s - 14} {fy - HEIGHT * s - 38} l28 13 -28 13 Z" fill="none" stroke="{INK}" stroke-width="3"/>')
    b.append(text(fx - 0.6 * s + 26, fy - HEIGHT * s - 18, "on top", "small"))
    b.extend(face_on(fx, fy, s))
    b.append(text(fx - 0.6 * s, fy + 38, "1  +  red", "label", "middle"))
    b.append(text(fx + 0.6 * s, fy + 38, "2  -", "label", "middle"))
    b.append(text(55, 852, "Cavity 1 is the LEFT hole. 1.2 mm between centres.", "note"))
    # C: contact
    b.append(panel(595, 565, 575, 300))
    b.append(text(620, 603, "C. Pre-crimped contact (SACHL-003G-P0.2)", "label"))
    cs = 105
    cx, cy = 760, 730
    b.append(contact_side(cx, cy, cs, wire_len=1.2))
    b.append(leader((700, 650), (cx + 0.5 * cs, cy - 0.38 * cs)))
    b.append(text(640, 645, "Grip here: base of the metal", "call"))
    b.append(leader((1080, 660), (cx + 2.9 * cs, cy - 0.22 * cs)))
    b.append(text(1000, 650, "goes in first", "call"))
    b.append(text(620, 815, "3.2 mm long, 0.8 mm wide. Gold-plated. Don't squeeze", "note"))
    b.append(text(620, 840, "or bend the spring box at the front.", "note"))
    # D: tools
    b.append(panel(30, 885, 1140, 110, "#e2f1f2"))
    b.append(text(55, 922, "D. Tools", "label"))
    b.append(text(55, 955, "Fine needle-nose pliers, flush cutters, red permanent marker, bright lamp (a phone camera at 2-3x helps),", "note"))
    b.append(text(55, 980, "fine soldering tip, flux, small heat-shrink, multimeter and a sewing needle. No microscope or crimper.", "note"))
    desc = ("Panel A: a three-dimensional drawing of the ACHLR-02V-S plug housing. Its flat face has two holes where the "
            "contacts go in; the opposite rough end has the latch and mating features and is never used for insertion. "
            "A triangle on the top face marks cavity 1 (VO plus, red lead) and a 2 marks cavity 2 (VO minus). The top face "
            "points away from the board when plugged in. Panel B: looking straight into the holes with the triangle face up, "
            "cavity 1 is the left hole; the holes are 1.2 mm apart. Panel C: a factory-crimped SACHL contact, 3.2 mm long, "
            "gripped at the base of its metal crimp; the spring box at the front goes in first. Panel D: tools. Drawn from "
            "JST's published outline dimensions, simplified; not a manufacturer drawing.")
    return svg(1200, 1020, "Know the speaker-plug parts and which face is which", desc, b)


def insert_svg() -> str:
    b = [text(40, 55, "Insert the contacts: one jumper, one plug", "heading"),
         text(40, 92, "Both ends of ONE 12-inch jumper go into ONE housing; snip the loop afterwards. A spare is useful for practice.")]
    W, H = 555, 360
    cells = [(30, 115), (615, 115), (30, 495), (615, 495), (30, 875), (615, 875)]
    S = 46

    def captions(x, y, lines, last_warn=False):
        for i, line in enumerate(lines):
            cls = "warn" if (last_warn and i == len(lines) - 1) else "body"
            b.append(text(x + 25, y + 292 + 26 * i, line, cls))

    # 1 hold
    x, y = cells[0]
    b.append(panel(x, y, W, H))
    b.append(text(x + 25, y + 38, "1. Hold the housing", "label"))
    v = View(x + 250, y + 200, S)
    b.append(held_housing(v))
    captions(x, y, ["Pinch its sides between thumb and forefinger,",
                    "triangle face up, flat hole face toward the",
                    "pliers. The rough end points away."])

    # 2 grip
    x, y = cells[1]
    b.append(panel(x, y, W, H))
    b.append(text(x + 25, y + 38, "2. Grip the base of the metal", "label"))
    cs = 62
    cx0, cy0 = x + 250, y + 150
    b.append(contact_side(cx0, cy0, cs, wire_len=2.6))
    b.append(pliers((cx0 + 0.66 * cs, cy0), 188, length=210, open_px=0.9 * cs))
    captions(x, y, ["Needle-nose pliers on the crimp at the base of",
                    "the metal, contact roughly parallel to the jaws,",
                    "spring box pointing forward."])

    # 3 insert most of the way
    x, y = cells[2]
    b.append(panel(x, y, W, H))
    b.append(text(x + 25, y + 38, "3. Push it most of the way in", "label"))
    v = View(x + 300, y + 205, S)
    b.append(finger(v, 1))
    b.append(housing(v))
    b.append(contact_iso(v, PITCH / 2, 2.3, wire_to=-4.6))
    b.append(pliers(v.p(-0.35, PITCH / 2, HOLE_Z), axis_angle(v, PITCH / 2), length=165, open_px=0.85 * S))
    b.append(finger(v, -1))
    captions(x, y, ["Line it up with the LEFT hole (cavity 1) and push",
                    "until most of the metal is inside."])

    # 4 re-grip and seat
    x, y = cells[3]
    b.append(panel(x, y, W, H, "#e2f1f2"))
    b.append(text(x + 25, y + 38, "4. Re-grip on the wire, seat it gently", "label"))
    v = View(x + 300, y + 205, S)
    b.append(finger(v, 1))
    b.append(housing(v))
    b.append(contact_iso(v, PITCH / 2, 3.2, wire_to=-4.6))
    b.append(pliers(v.p(-0.9, PITCH / 2, HOLE_Z), axis_angle(v, PITCH / 2), length=165, open_px=0.62 * S))
    b.append(finger(v, -1))
    a, c = v.p(-2.4, PITCH / 2 + 1.3, HOLE_Z + 0.6), v.p(-1.0, PITCH / 2 + 1.3, HOLE_Z + 0.6)
    b.append(f'<path d="M{fmt(a[0])} {fmt(a[1])} L{fmt(c[0])} {fmt(c[1])}" stroke="#007f91" stroke-width="5" marker-end="url(#arrow)"/>')
    captions(x, y, ["Move the pliers back onto the wire and push",
                    "gently until it stops flush. Binds? Pull back,",
                    "roll it half a turn, retry. Never force it."], last_warn=True)

    # loop geometry shared by steps 5 and 6
    def loop_parts(v, y):
        p1, p2 = v.p(-0.3, PITCH / 2, HOLE_Z), v.p(-0.3, -PITCH / 2, HOLE_Z)
        mid = (p1[0] - 150, y + 250)
        h1 = (f"M{fmt(p1[0])} {fmt(p1[1])} C{fmt(p1[0] - 230)} {fmt(p1[1] - 5)} {fmt(mid[0] - 140)} {fmt(mid[1])} "
              f"{fmt(mid[0])} {fmt(mid[1])}")
        h2 = (f"M{fmt(mid[0])} {fmt(mid[1])} C{fmt(mid[0] + 110)} {fmt(mid[1])} {fmt(p2[0] - 70)} {fmt(p2[1] + 70)} "
              f"{fmt(p2[0])} {fmt(p2[1])}")
        return h1, h2, mid

    # 5 other end
    x, y = cells[4]
    b.append(panel(x, y, W, H))
    b.append(text(x + 25, y + 38, "5. Other end of the SAME jumper", "label"))
    v = View(x + 360, y + 160, 40)
    b.append(housing(v))
    h1, h2, mid = loop_parts(v, y)
    b.append(wire_pair(h1, h2, False, 0.6 * 40))
    captions(x, y, ["Steps 2-4 again, into the RIGHT hole (cavity 2).",
                    "Hold the housing and tug each wire gently:",
                    "neither may move."])

    # 6 mark and snip
    x, y = cells[5]
    b.append(panel(x, y, W, H))
    b.append(text(x + 25, y + 38, "6. Colour cavity 1's half red, snip", "label"))
    v = View(x + 360, y + 160, 40)
    b.append(housing(v))
    h1, h2, mid = loop_parts(v, y)
    b.append(wire_pair(h1, h2, True, 0.6 * 40))
    b.append(f'<path d="M{fmt(mid[0])} {fmt(mid[1] - 30)} V{fmt(mid[1] + 30)}" stroke="#c14d2b" stroke-width="3" stroke-dasharray="6 5"/>')
    b.append(text(mid[0] + 14, mid[1] - 20, "snip", "small"))
    captions(x, y, ["Marker from the LEFT (triangle) hole to the",
                    "middle of the loop; cut there. Two ~6-inch",
                    "leads: red = VO+, plain = VO-."])

    b.append(panel(30, 1255, 1140, 80, "#fff2df"))
    b.append(text(55, 1289, "Got them the other way round? Don't dig a contact out.", "label"))
    b.append(text(55, 1319, "Colour whichever lead is in the triangle (left) hole red instead. A single speaker works either way round.", "note"))
    desc = ("Six steps. One: pinch the plug housing between thumb and forefinger, triangle face up, flat hole face toward you. "
            "Two: grip the factory-crimped contact at the base of its metal with needle-nose pliers, spring box pointing forward. "
            "Three: push it straight into the left hole, cavity 1, until most of the metal is inside. Four: move the pliers back "
            "onto the wire and push gently until the contact stops flush; if it binds, pull back, roll it half a turn and retry, "
            "never force it. Five: put the other end of the same 12-inch jumper into the right hole, cavity 2, making a loop, "
            "and tug-test both. Six: colour the half from the triangle hole red as far as the middle of the loop, then cut "
            "there to make two six-inch leads: red is VO plus, plain is VO minus. Simplified drawing from JST outline "
            "dimensions.")
    return svg(1200, 1360, "Insert the contacts: one jumper, one plug", desc, b)


def finish_svg() -> str:
    b = [text(40, 55, "Solder and plug in", "heading")]
    # 1 solder
    x, y = 30, 80
    b.append(panel(x, y, 555, 400))
    b.append(text(x + 25, y + 38, "1. Solder to the speaker tabs", "label"))
    b.append('<circle cx="430" cy="270" r="115" fill="#3b4752"/><circle cx="430" cy="270" r="60" fill="#56636f"/>')
    for ty in (170, 348):
        b.append(f'<rect x="325" y="{ty}" width="44" height="22" rx="4" fill="#c0c7cc" stroke="#55606a" stroke-width="2"/>')
    b.append(f'<text x="347" y="164" text-anchor="middle" class="label" style="fill:{RED}">+</text>')
    b.append(wire_path([(70, 181), (300, 181)], True, 10))
    b.append(wire_path([(70, 359), (300, 359)], False, 10))
    for ty in (181, 359):
        b.append(f'<path d="M300 {ty} H330" stroke="#b87333" stroke-width="6"/>')
        b.append(f'<rect x="245" y="{ty - 11}" width="52" height="22" rx="4" fill="#1f2a33" opacity="0.85"/>')
    b.append(text(271, 218, "heat-shrink", "note", "middle"))
    b.append(text(x + 25, y + 182, "Heat-shrink on FIRST.", "body"))
    b.append(text(x + 25, y + 209, "Strip ~2 mm, twist, tin.", "body"))
    b.append(text(x + 25, y + 236, "Red to the + tab.", "body"))
    b.append(text(x + 25, y + 335, "About 3 s per joint, then shrink, keeping", "body"))
    b.append(text(x + 25, y + 362, "heat away from the paper cone.", "body"))
    # 2 strain relief
    x, y = 615, 80
    b.append(panel(x, y, 555, 400))
    b.append(text(x + 25, y + 38, "2. Slack and strain relief", "label"))
    d = "M660 220 C770 220 780 170 860 180 S960 260 1050 220"
    b.append(wire_curve(d, True, 10))
    b.append('<ellipse cx="1040" cy="223" rx="30" ry="20" fill="#f5e7a8" stroke="#b49a32" stroke-width="2"/>')
    b.append(text(1040, 270, "glue dot / tie", "note", "middle"))
    b.append(text(x + 25, y + 280, "Trim only after a dry fit; leave a gentle loop.", "body"))
    b.append(text(x + 25, y + 307, "Anchor the leads near the speaker so a pull", "body"))
    b.append(text(x + 25, y + 334, "never reaches the crimps or the plug.", "body"))
    # 3 plug in (full width)
    x, y = 30, 500
    b.append(panel(x, y, 1140, 400, "#e2f1f2"))
    b.append(text(x + 25, y + 38, "3. Plug in: triangle face up, on J1's pin-1 side", "label"))
    S = 55
    ox, oy = 330, 725

    def P(X, Y):
        return ox + X * S, oy - Y * S

    def rect(x0, x1, y0, y1, **a):
        (ax, ay), (bx, by) = P(x0, y1), P(x1, y0)
        extra = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in a.items())
        return f'<rect x="{fmt(ax)}" y="{fmt(ay)}" width="{fmt(bx - ax)}" height="{fmt(by - ay)}" {extra}/>'

    b.append(rect(-3.6, 5.6, -2.85, 2.85, rx="6", fill="#2d6a3e", stroke="#173a21", stroke_width="2"))
    b.append(rect(0.2, 4.6, -2.1, 2.1, fill="#262626", stroke="#000", stroke_width="1.5"))
    for a, c in (((4.85, 2.35), (4.85, 1.55)), ((4.85, 2.35), (4.05, 2.35))):
        pa, pc = P(*a), P(*c)
        b.append(f'<path d="M{fmt(pa[0])} {fmt(pa[1])} L{fmt(pc[0])} {fmt(pc[1])}" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>')
    for cy, red in ((PITCH / 2, True), (-PITCH / 2, False)):
        b.append(wire_path([P(-3.3, cy), P(0.1, cy)], red, WIRE_OD * S))
    pts = " ".join(f"{fmt(P(X, Y)[0])},{fmt(P(X, Y)[1])}" for X, Y in OUTLINE)
    b.append(f'<polygon points="{pts}" fill="{BODY["top"]}" stroke="{BODY["edge"]}" stroke-width="2.5" stroke-linejoin="round"/>')
    t = [P(0.45, 0.85), P(0.45, 0.35), P(0.95, 0.6)]
    b.append('<polygon points="' + " ".join(f"{fmt(a)},{fmt(c)}" for a, c in t) + f'" fill="none" stroke="{INK}" stroke-width="3"/>')
    bx0, by0 = P(3.0, -0.3)
    b.append(f'<rect x="{fmt(bx0)}" y="{fmt(by0)}" width="{fmt(0.5 * S)}" height="{fmt(0.6 * S)}" fill="none" stroke="{INK}" stroke-width="2"/>')
    b.append(text(P(3.25, -0.6)[0], P(3.25, -0.6)[1] + 8, "2", "label", "middle"))
    b.append(leader((700, 612), P(4.85, 2.35)))
    b.append(text(706, 608, "White corner mark on the board = J1 pin 1", "call"))
    b.append(text(706, 634, "(VO+). The triangle side of the plug goes here.", "note"))
    for cy, label in ((1.45, "red = VO+ (triangle side)"), (-1.75, "plain = VO-")):
        lx, ly = P(-3.3, cy)
        b.append(f'<text x="{fmt(lx)}" y="{fmt(ly)}" class="note" style="fill:#ffffff">{label}</text>')
    b.append(text(706, 760, "Seen from above, plug seated. Press straight", "body"))
    b.append(text(706, 787, "down until it sits flat; the wires lie along", "body"))
    b.append(text(706, 814, "the board. Unplug by lifting the housing,", "body"))
    b.append(text(706, 841, "never by pulling the wires.", "warn"))
    # footer
    b.append(panel(30, 920, 1140, 165, "#fff2df"))
    b.append(text(55, 958, "Neither speaker wire is ground. Don't connect either to the case or a battery clip.", "label"))
    b.append(text(55, 992, "J1 pin 1 is VO+ and pin 2 is VO- on PCB 2f738ccb; the amplifier drives both wires.", "body"))
    b.append(text(55, 1024, "Optional check: meter on continuity, one probe on a lead's free end, a needle on the other probe touching", "note"))
    b.append(text(55, 1048, "the metal in the plug's underside opening. Cable route and plug clearance in the six-layer cartridge", "note"))
    b.append(text(55, 1072, "are not yet fit-checked: dry-fit before trimming.", "note"))
    desc = ("Three steps. One: slide heat-shrink on, strip about 2 mm, tin, and solder the red lead to the speaker's plus "
            "tab and the plain lead to the other tab, about 3 seconds per joint. Two: dry-fit, leave slack and anchor the "
            "leads near the speaker. Three: with the triangle face up, put the plug on the J1 header with cavity 1 on the "
            "side of the pin-1 silkscreen corner mark and press straight down until flat; the wires lie along the board; "
            "unplug by lifting the housing. Neither wire is ground. J1 pin 1 is VO plus on PCB 2f738ccb. Schematic board "
            "and header; fit not verified.")
    return svg(1200, 1105, "Solder the speaker lead and plug it in", desc, b)


def main() -> None:
    for name, fn in (("build-connector-parts.svg", parts_svg), ("build-connector-insert.svg", insert_svg),
                     ("build-connector-finish.svg", finish_svg)):
        (OUT / name).write_text(fn(), encoding="utf-8", newline="\n")
        print("wrote", name)


if __name__ == "__main__":
    main()
