# SPDX-License-Identifier: MIT
"""Static quote-package builder and independent export verifier for a KiCad board.

build   Write JLC, PCBWay and sourcing BOMs, a CPL and an inventory from a
        .kicad_pcb and an LCSC register. No KiCad, network or refill is used.
verify  Recompute drill, outline, via, position and ZIP expectations from the
        .kicad_pcb text and compare them with natively exported files.
hashlist Write or --check a sha256sum-format manifest: relative POSIX names,
        LF line endings, so `sha256sum -c` works on any platform.

Gerber parsing (--gerbers) needs the optional gerbonara package. Nothing here
uploads, orders or edits a board; outputs are quote preparation only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
import zipfile
from collections import Counter, defaultdict, namedtuple
from dataclasses import dataclass
from pathlib import Path

from kicad_sexpr import Node, loads

REGISTER_SCHEMA = "handbell-lcsc-register-v1"
REPORT_SCHEMA = "handbell-quote-verification-v1"
EXPECT_SCHEMA = "handbell-quote-expectations-v1"
INVENTORY_SCHEMA = "handbell-quote-inventory-v1"
LCSC_RE = re.compile(r"^C\d{3,9}$")
HINT_PROPS = ("ROT", "JLC_ROTATION", "JLC_ROTATION_1")
DRILL_TOL = 1.1e-3
POS_TOL = 1e-4
GERBER_NO_NET = "N/C"  # KiCad's X2 .N value for a pad with no net
JLC_HEADER =  ["Comment", "Designator", "Footprint", "LCSC Part #"]
SOURCING_HEADER = ["Designators", "Qty", "Value", "Footprint", "MPN", "Manufacturer",
                   "LCSC", "LCSC provenance", "Status", "Notes"]
PCBWAY_HEADER = ["Item #", "Designator", "Qty", "Manufacturer", "Mfg Part #",
                 "Description / Value", "Package/Footprint", "Type", "Your Instructions / Notes"]
CPL_HEADER = ["Designator", "Mid X", "Mid Y", "Layer", "Rotation"]
NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)"
RE_TOOLDEF = re.compile(r"^T(\d+)C(\d+(?:\.\d+)?)$")
RE_TOOLSEL = re.compile(r"^T(\d+)$")
RE_HIT = re.compile(rf"^X({NUM})Y({NUM})$")
RE_SLOT = re.compile(rf"^X({NUM})Y({NUM})G85X({NUM})Y({NUM})$")
RE_HASH_LINE = re.compile(r"^([0-9a-fA-F]{64}) [ *](.+)$")


@dataclass
class Pad:
    index: int
    number: str
    kind: str
    shape: str
    x: float
    y: float
    angle: float
    w: float
    h: float
    layers: tuple
    net: str
    drill: tuple | None


@dataclass
class Footprint:
    ref: str
    value: str
    lib: str
    layer: str
    x: float
    y: float
    rot: float
    attrs: frozenset
    props: dict
    pads: list

    @property
    def name(self) -> str:
        return self.lib.split(":", 1)[-1]

    @property
    def side(self) -> str:
        return "bottom" if self.layer == "B.Cu" else "top"

    @property
    def dnp(self) -> bool:
        return "dnp" in self.attrs

    @property
    def board_only(self) -> bool:
        return "board_only" in self.attrs

    @property
    def in_pos_all(self) -> bool:
        return "exclude_from_pos_files" not in self.attrs

    @property
    def in_pos_fitted(self) -> bool:
        return self.in_pos_all and not self.dnp

    @property
    def in_bom(self) -> bool:
        return "exclude_from_bom" not in self.attrs and not self.dnp and not self.board_only

    @property
    def in_cpl(self) -> bool:
        return self.in_pos_fitted and not self.board_only

    @property
    def fitted(self) -> bool:
        return self.in_bom and self.in_cpl

    def exclusion_reasons(self) -> list:
        reasons = [a for a in ("exclude_from_bom", "exclude_from_pos_files") if a in self.attrs]
        if self.dnp:
            reasons.append("dnp")
        if self.board_only:
            reasons.append("board_only")
        return reasons


@dataclass
class Via:
    x: float
    y: float
    size: float
    drill: float
    layers: tuple
    net: str
    uuid: str
    kind: str
    capping: str
    filling: str


@dataclass
class Hole:
    plated: bool
    dia: float
    x: float
    y: float
    x2: float | None = None
    y2: float | None = None
    source: str = ""


@dataclass
class ExcellonFile:
    tools: dict
    hits: list
    slots: list
    plated: bool | None = None


@dataclass
class Board:
    root: Node
    footprints: list
    vias: list
    sha256: str = ""


Row = namedtuple("Row", "ref x y rot side val pkg")


class Report:
    def __init__(self) -> None:
        self.checks: list = []
        self.metrics: dict = {}
        self.files: dict = {}

    def add(self, name: str, status: str, detail: str = "") -> None:
        self.checks.append({"name": name, "status": status, "detail": detail})

    def overall(self) -> str:
        statuses = {c["status"] for c in self.checks}
        if "FAIL" in statuses:
            return "FAIL"
        return "WARN" if "WARN" in statuses else "PASS"

    def to_dict(self) -> dict:
        counts = Counter(c["status"] for c in self.checks)
        return {"schema": REPORT_SCHEMA, "overall": self.overall(), "counts": dict(sorted(counts.items())),
                "checks": self.checks, "metrics": self.metrics, "files": self.files}


def natural_key(ref: str) -> list:
    parts = re.split(r"([0-9]+)", ref)
    return [int(p) if i % 2 else p for i, p in enumerate(parts)]


def cos_sin(deg: float) -> tuple:
    d = deg % 360.0
    if d < 1e-9 or d > 360.0 - 1e-9:
        return 1.0, 0.0
    for k, cs in ((90.0, (0.0, 1.0)), (180.0, (-1.0, 0.0)), (270.0, (0.0, -1.0))):
        if abs(d - k) < 1e-9:
            return cs
    r = math.radians(d)
    return math.cos(r), math.sin(r)


def rotate_local(x: float, y: float, deg: float) -> tuple:
    c, s = cos_sin(deg)
    return x * c + y * s, y * c - x * s


def board_point(fp: Footprint, x: float, y: float) -> tuple:
    rx, ry = rotate_local(x, y, fp.rot)
    return fp.x + rx, fp.y + ry


def fmt_num(v: float) -> str:
    s = f"{v:.6f}".rstrip("0")
    if s.endswith("."):
        s += "0"
    return "0.0" if s == "-0.0" else s


def norm_rot(deg: float) -> float:
    r = round(deg % 360.0, 6)
    return 0.0 if r >= 360.0 else r


def circ_diff(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def values_equal(a, b, tol: float = 1e-6) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= tol
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(values_equal(a[k], b[k], tol) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(values_equal(x, y, tol) for x, y in zip(a, b))
    return a == b


def sha256_file(path: Path) -> tuple:
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
            n += len(chunk)
    return h.hexdigest(), n


def write_json(path: Path, data) -> None:
    with open(path, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(json.dumps(data, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, header: list, rows: list) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def parse_pad(index: int, node: Node) -> Pad:
    atoms = node.atoms()
    at = node.child("at")
    a = at.atoms() if at is not None else ["at", "0", "0"]
    size = node.child("size")
    s = size.atoms() if size is not None else ["size", "0", "0"]
    layers = node.child("layers")
    net = node.child("net")
    drill = None
    d = node.child("drill")
    if d is not None:
        off = d.child("offset")
        if off is not None and any(abs(float(v)) > 1e-9 for v in off.atoms()[1:]):
            raise ValueError("non-zero pad drill offset is not supported")
        da = d.atoms()[1:]
        if da and da[0] == "oval":
            drill = (float(da[1]), float(da[2]))
        elif da:
            drill = (float(da[0]), float(da[0]))
    return Pad(index, atoms[1], atoms[2], atoms[3], float(a[1]), float(a[2]),
               float(a[3]) if len(a) > 3 else 0.0, float(s[1]), float(s[2]),
               tuple(layers.atoms()[1:]) if layers is not None else (),
               net.atoms()[-1] if net is not None else "", drill)


def parse_footprint(node: Node) -> Footprint:
    props = node.properties()
    ref = props.get("Reference")
    if not ref:
        raise ValueError("footprint without a Reference property")
    at = node.child("at").atoms()
    attr = node.child("attr")
    pads = [parse_pad(i, p) for i, p in enumerate(node.children("pad"))]
    return Footprint(ref, props.get("Value", ""), node.atoms()[1], node.child("layer").atoms()[1],
                     float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0,
                     frozenset(attr.atoms()[1:]) if attr is not None else frozenset(), props, pads)


def parse_via(node: Node) -> Via:
    kind = "through"
    for a in node.atoms()[1:]:
        if a in ("blind", "micro", "buried"):
            kind = a
    at = node.child("at").atoms()
    net = node.child("net")
    uuid = node.child("uuid")
    return Via(float(at[1]), float(at[2]), float(node.child("size").atoms()[1]),
               float(node.child("drill").atoms()[1]), tuple(node.child("layers").atoms()[1:]),
               net.atoms()[-1] if net is not None else "", uuid.atoms()[1] if uuid is not None else "",
               kind, node.value("capping") or "", node.value("filling") or "")


def parse_board_text(text: str) -> Board:
    root = loads(text)
    if root.head != "kicad_pcb":
        raise ValueError("not a kicad_pcb file")
    setup = root.child("setup")
    if setup is not None and setup.child("aux_axis_origin") is not None:
        raise ValueError("aux_axis_origin is set; the checks assume the absolute origin")
    fps = [parse_footprint(n) for n in root.children("footprint")]
    refs = Counter(f.ref for f in fps)
    dup = sorted(r for r, n in refs.items() if n > 1)
    if dup:
        raise ValueError("duplicate references: " + ", ".join(dup))
    for fp in fps:
        if fp.layer == "B.Cu" and any(p.drill for p in fp.pads):
            raise ValueError(f"{fp.ref}: hole pads on a bottom footprint are not supported")
    return Board(root, fps, [parse_via(n) for n in root.children("via")])


def parse_board(path: Path) -> Board:
    data = Path(path).read_bytes()
    board = parse_board_text(data.decode("utf-8-sig"))
    board.sha256 = hashlib.sha256(data).hexdigest()
    return board


def pad_holes(fp: Footprint) -> list:
    holes = []
    for pad in fp.pads:
        if pad.drill is None or pad.kind not in ("thru_hole", "np_thru_hole"):
            continue
        a, b = pad.drill
        if a <= 0 or b <= 0:
            continue
        bx, by = board_point(fp, pad.x, pad.y)
        plated = pad.kind == "thru_hole"
        source = f"{fp.ref}.{pad.number or pad.index}"
        if abs(a - b) < 1e-9:
            holes.append(Hole(plated, a, bx, by, source=source))
            continue
        c, s = cos_sin(pad.angle)
        dx, dy = (c, -s) if a >= b else (s, c)
        half = (max(a, b) - min(a, b)) / 2.0
        holes.append(Hole(plated, min(a, b), bx - dx * half, by - dy * half,
                          bx + dx * half, by + dy * half, source))
    return holes


def expected_holes(board: Board) -> list:
    holes = [Hole(True, v.drill, v.x, v.y, source="via " + v.uuid[:8]) for v in board.vias]
    for fp in board.footprints:
        holes.extend(pad_holes(fp))
    return holes


def tool_table(holes: list, plated: bool) -> dict:
    t = Counter(f"{h.dia:.3f} {'slot' if h.x2 is not None else 'round'}" for h in holes if h.plated == plated)
    return dict(sorted(t.items()))


def parse_excellon(text: str) -> ExcellonFile:
    tools: dict = {}
    hits: list = []
    slots: list = []
    plated = None
    decimal = None
    current = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(";"):
            low = line.lower()
            if "format=" in low:
                decimal = "decimal" in low
            m = re.search(r"TF\.FileFunction,(\w+)", line)
            if m:
                plated = m.group(1).lower() == "plated"
            continue
        if line in ("M48", "%", "G90", "G05", "M30", "FMAT,2") or line.startswith("METRIC"):
            continue
        if line.startswith("INCH"):
            raise ValueError("inch Excellon files are not supported")
        m = RE_TOOLDEF.match(line)
        if m:
            tools[int(m.group(1))] = float(m.group(2))
            continue
        m = RE_TOOLSEL.match(line)
        if m:
            n = int(m.group(1))
            if n not in tools:
                raise ValueError(f"tool T{n} selected before definition")
            current = tools[n]
            continue
        m = RE_SLOT.match(line)
        if m and current is not None:
            x1, y1, x2, y2 = (float(v) for v in m.groups())
            slots.append((current, x1, -y1, x2, -y2))
            continue
        m = RE_HIT.match(line)
        if m and current is not None:
            hits.append((current, float(m.group(1)), -float(m.group(2))))
            continue
        raise ValueError(f"unsupported Excellon statement: {line!r}")
    if decimal is False:
        raise ValueError("Excellon coordinates are not decimal")
    return ExcellonFile(tools, hits, slots, plated)


def match_points(expected: list, actual: list, tol: float, dist) -> tuple:
    pairs = sorted((dist(e, a), i, j) for i, e in enumerate(expected) for j, a in enumerate(actual))
    used_e: set = set()
    used_a: set = set()
    matched = 0
    worst = 0.0
    for d, i, j in pairs:
        if d > tol:
            break
        if i in used_e or j in used_a:
            continue
        used_e.add(i)
        used_a.add(j)
        matched += 1
        worst = max(worst, d)
    return (matched, worst, [e for i, e in enumerate(expected) if i not in used_e],
            [a for j, a in enumerate(actual) if j not in used_a])


def _round_dist(e, a) -> float:
    return max(abs(e[0] - a[0]), abs(e[1] - a[1]))


def _slot_dist(e, a) -> float:
    d1 = max(abs(e[0] - a[0]), abs(e[1] - a[1]), abs(e[2] - a[2]), abs(e[3] - a[3]))
    d2 = max(abs(e[0] - a[2]), abs(e[1] - a[3]), abs(e[2] - a[0]), abs(e[3] - a[1]))
    return min(d1, d2)


def compare_drill(report: Report, label: str, expected: list, parsed: ExcellonFile, plated: bool) -> None:
    exp: dict = defaultdict(list)
    act: dict = defaultdict(list)
    for h in expected:
        if h.plated == plated:
            key = ("slot" if h.x2 is not None else "round", round(h.dia, 3))
            exp[key].append((h.x, h.y) if h.x2 is None else (h.x, h.y, h.x2, h.y2))
    for dia, x, y in parsed.hits:
        act[("round", round(dia, 3))].append((x, y))
    for dia, x1, y1, x2, y2 in parsed.slots:
        act[("slot", round(dia, 3))].append((x1, y1, x2, y2))
    if parsed.plated is not None and parsed.plated != plated:
        report.add(f"drill:{label}:function", "FAIL", f"file declares plated={parsed.plated}, expected {plated}")
    for key in sorted(set(exp) | set(act)):
        kind, dia = key
        matched, worst, missing, extra = match_points(
            exp.get(key, []), act.get(key, []), DRILL_TOL, _slot_dist if kind == "slot" else _round_dist)
        ok = not missing and not extra
        detail = f"expected {len(exp.get(key, []))}, file {len(act.get(key, []))}, matched {matched}, max error {worst:.6f} mm"
        if missing:
            detail += f"; missing {missing[:3]}"
        if extra:
            detail += f"; extra {extra[:3]}"
        report.add(f"drill:{label}:{kind} {dia:.3f}", "PASS" if ok else "FAIL", detail)


def line_width(node: Node) -> float:
    stroke = node.child("stroke")
    if stroke is not None and stroke.value("width") is not None:
        return float(stroke.value("width"))
    w = node.value("width")
    return float(w) if w is not None else 0.0


def _orient(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _point_seg(p, a, b) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    if l2 == 0:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def seg_distance(p, q, r, s) -> float:
    o1, o2, o3, o4 = _orient(p, q, r), _orient(p, q, s), _orient(r, s, p), _orient(r, s, q)
    if o1 * o2 < 0 and o3 * o4 < 0:
        return 0.0
    return min(_point_seg(p, r, s), _point_seg(q, r, s), _point_seg(r, p, q), _point_seg(s, p, q))


def analyze_outline(root: Node, tol: float = 1e-4) -> dict:
    segs: list = []
    unsupported: list = []
    for node in root.children():
        head = node.head or ""
        if head.startswith("gr_"):
            layer = node.child("layer")
            if layer is None or layer.atoms()[1] != "Edge.Cuts":
                continue
            if head != "gr_line":
                unsupported.append(head)
                continue
            s, e = node.child("start").atoms(), node.child("end").atoms()
            segs.append((float(s[1]), float(s[2]), float(e[1]), float(e[2]), line_width(node)))
        elif head == "footprint":
            for sub in node.children():
                if (sub.head or "").startswith("fp_"):
                    layer = sub.child("layer")
                    if layer is not None and layer.atoms()[1] == "Edge.Cuts":
                        unsupported.append("footprint " + sub.head)
    pts: list = []

    def node_id(x: float, y: float) -> int:
        for i, (px, py) in enumerate(pts):
            if abs(px - x) <= tol and abs(py - y) <= tol:
                return i
        pts.append((x, y))
        return len(pts) - 1

    edges = [(node_id(x1, y1), node_id(x2, y2)) for x1, y1, x2, y2, _ in segs]
    deg = [0] * len(pts)
    adj: list = [[] for _ in pts]
    zero = 0
    for i, (a, b) in enumerate(edges):
        zero += a == b
        deg[a] += 1
        deg[b] += 1
        adj[a].append((i, b))
        adj[b].append((i, a))
    seen: set = set()
    components = 0
    for start in range(len(pts)):
        if start in seen:
            continue
        components += 1
        stack = [start]
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            stack.extend(o for _, o in adj[n])
    bad_degree = sum(1 for d in deg if d != 2)
    crossings = []
    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            if set(edges[i]) & set(edges[j]):
                continue
            p, q = (segs[i][0], segs[i][1]), (segs[i][2], segs[i][3])
            r, s = (segs[j][0], segs[j][1]), (segs[j][2], segs[j][3])
            if seg_distance(p, q, r, s) <= tol:
                crossings.append((i, j))
    closed = bool(segs) and bad_degree == 0 and components == 1 and zero == 0
    area = None
    if closed:
        order, cur, prev = [], 0, None
        while len(order) <= len(segs):
            order.append(cur)
            ei, cur = next((e, o) for e, o in adj[cur] if e != prev)
            prev = ei
            if cur == 0:
                break
        ring = [pts[i] for i in order]
        area = abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]))) / 2.0
    xs = [v for s in segs for v in (s[0], s[2])]
    ys = [v for s in segs for v in (s[1], s[3])]
    return {"segments": len(segs), "unsupported": sorted(set(unsupported)), "nodes": len(pts),
            "components": components, "bad_degree_nodes": bad_degree, "zero_length": zero,
            "crossings": crossings, "closed": closed, "widths": sorted({s[4] for s in segs}),
            "bbox": [min(xs), min(ys), max(xs), max(ys)] if segs else [0.0] * 4,
            "perimeter": sum(math.hypot(s[2] - s[0], s[3] - s[1]) for s in segs), "area": area}


def via_census(vias: list) -> dict:
    by = Counter(f"{v.size:g}/{v.drill:g}" for v in vias)
    through = sum(1 for v in vias if v.kind == "through" and set(v.layers) == {"F.Cu", "B.Cu"})
    flags = sum(1 for v in vias if v.capping == "yes" or v.filling == "yes")
    return {"total": len(vias), "through_FB": through, "by_size_drill": dict(sorted(by.items())),
            "capped_filled_flags": flags}


def via_in_pad(board: Board) -> list:
    out = []
    for v in board.vias:
        for fp in board.footprints:
            for pad in fp.pads:
                if pad.w <= 0 or pad.h <= 0 or not any(layer.endswith(".Cu") for layer in pad.layers):
                    continue
                px, py = board_point(fp, pad.x, pad.y)
                dx, dy = v.x - px, v.y - py
                c, s = cos_sin(pad.angle)
                lx, ly = dx * c - dy * s, dx * s + dy * c
                r = v.size / 2.0
                if pad.shape == "circle":
                    d = math.hypot(lx, ly)
                    inside, full = d <= pad.w / 2, d + r <= pad.w / 2
                else:
                    inside = abs(lx) <= pad.w / 2 and abs(ly) <= pad.h / 2
                    full = abs(lx) + r <= pad.w / 2 and abs(ly) + r <= pad.h / 2
                if inside:
                    out.append({"via": v.uuid[:8], "via_at": [round(v.x, 6), round(v.y, 6)], "via_net": v.net,
                                "pad": f"{fp.ref}.{pad.number}", "pad_net": pad.net, "pad_shape": pad.shape,
                                "fully_inside": full, "fitted": fp.fitted,
                                "capping": v.capping, "filling": v.filling})
    return out


def stackup_summary(root: Node) -> dict | None:
    setup = root.child("setup")
    stack = setup.child("stackup") if setup is not None else None
    if stack is None:
        return None
    totals = {"copper": 0.0, "dielectric": 0.0, "other": 0.0}
    layers = []
    for layer in stack.children("layer"):
        types = [t.atoms()[1] for t in layer.children("type") if len(t.atoms()) > 1]
        thickness = sum(float(t.atoms()[1]) for t in layer.children("thickness") if len(t.atoms()) > 1)
        kind = (types[0] if types else "").lower()
        bucket = "copper" if kind == "copper" else "dielectric" if kind in ("core", "prepreg") else "other"
        totals[bucket] += thickness
        layers.append({"name": layer.atoms()[1], "type": types[0] if types else "", "thickness_mm": round(thickness, 6)})
    general = root.child("general")
    gt = general.value("thickness") if general is not None else None
    return {"copper_mm": round(totals["copper"], 6), "dielectric_mm": round(totals["dielectric"], 6),
            "other_mm": round(totals["other"], 6), "total_mm": round(totals["copper"] + totals["dielectric"], 6),
            "general_thickness_mm": float(gt) if gt is not None else None, "layers": layers}


def board_metrics(board: Board) -> dict:
    fps = board.footprints
    fitted = [f for f in fps if f.fitted]
    holes = expected_holes(board)
    outline = analyze_outline(board.root)
    census = via_census(board.vias)
    vip = via_in_pad(board)
    stack = stackup_summary(board.root)
    m = {
        "pcb.sha256": board.sha256,
        "pcb.footprints": len(fps),
        "pcb.pos_all": sum(f.in_pos_all for f in fps),
        "pcb.pos_fitted": sum(f.in_pos_fitted for f in fps),
        "pcb.bom_refs": sum(f.in_bom for f in fps),
        "pcb.cpl_refs": sum(f.in_cpl for f in fps),
        "pcb.fitted": len(fitted),
        "pcb.fitted_side": {"top": sum(f.side == "top" for f in fitted), "bottom": sum(f.side == "bottom" for f in fitted)},
        "pcb.excluded_refs": sorted((f.ref for f in fps if not f.fitted), key=natural_key),
        "pcb.dnp_refs": sorted((f.ref for f in fps if f.dnp), key=natural_key),
        "pcb.board_only_refs": sorted((f.ref for f in fps if f.board_only), key=natural_key),
        "edge.segments": outline["segments"],
        "edge.closed": outline["closed"],
        "edge.bbox": [round(v, 6) for v in outline["bbox"]],
        "edge.perimeter_mm": round(outline["perimeter"], 6),
        "edge.area_mm2": round(outline["area"], 6) if outline["area"] is not None else None,
        "edge.stroke_widths": outline["widths"],
        "vias.total": census["total"],
        "vias.through_FB": census["through_FB"],
        "vias.by_size_drill": census["by_size_drill"],
        "vias.capped_filled_flags": census["capped_filled_flags"],
        "via_in_pad.pairs": len(vip),
        "via_in_pad.centre_inside": len(vip),
        "via_in_pad.fully_inside": sum(1 for v in vip if v["fully_inside"]),
        "holes.PTH.total": sum(1 for h in holes if h.plated),
        "holes.PTH.by_tool": tool_table(holes, True),
        "holes.NPTH.total": sum(1 for h in holes if not h.plated),
        "holes.NPTH.by_tool": tool_table(holes, False),
    }
    if stack is not None:
        m["stackup.total_mm"] = stack["total_mm"]
        m["stackup.copper_mm"] = stack["copper_mm"]
        m["stackup.dielectric_mm"] = stack["dielectric_mm"]
    return m


def load_register(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != REGISTER_SCHEMA:
        raise ValueError(f"register schema must be {REGISTER_SCHEMA}")
    entries: dict = {}
    for e in data["entries"]:
        key = e["mpn"].strip().lower()
        if key in entries:
            raise ValueError("duplicate register MPN " + e["mpn"])
        if not LCSC_RE.match(e["lcsc"]):
            raise ValueError(f"invalid LCSC code {e['lcsc']!r} for {e['mpn']}")
        entries[key] = e
    return entries


def resolve_lcsc(fp: Footprint, register: dict) -> tuple:
    pcb_code = fp.props.get("LCSC", "").strip()
    mpn = fp.props.get("MPN", "").strip()
    reg = register.get(mpn.lower()) if mpn else None
    notes = [reg["note"]] if reg and reg.get("note") else []
    if pcb_code:
        if not LCSC_RE.match(pcb_code):
            return "", "invalid-pcb-property", notes + [f"invalid LCSC property {pcb_code!r}"]
        if reg and reg["lcsc"] != pcb_code:
            notes.append(f"register-conflict: register has {reg['lcsc']}")
        elif reg:
            notes.append("register agrees")
        return pcb_code, "pcb-property", notes
    if reg:
        return reg["lcsc"], "register", notes
    return "", "unresolved", notes


def pcbway_type(fps: list) -> str:
    smd = any(p.kind == "smd" for f in fps for p in f.pads)
    tht = any(p.kind == "thru_hole" for f in fps for p in f.pads)
    return "SMD+THT" if smd and tht else "THT" if tht else "SMD" if smd else "OTHER"


def jlc_comment(value: str, mpn: str) -> str:
    return value if not mpn or mpn == value else f"{value} {mpn}"


def bom_groups(board: Board, register: dict) -> tuple:
    groups: dict = {}
    disagreements: dict = defaultdict(list)
    for fp in sorted((f for f in board.footprints if f.fitted), key=lambda f: natural_key(f.ref)):
        code, prov, notes = resolve_lcsc(fp, register)
        mpn = fp.props.get("MPN", "").strip()
        reg = register.get(mpn.lower()) if mpn else None
        if prov == "pcb-property" and reg and reg["lcsc"] != code:
            disagreements[(mpn, code, reg["lcsc"])].append(fp.ref)
        g = groups.setdefault((fp.value, fp.name, mpn, code), {
            "value": fp.value, "footprint": fp.name, "mpn": mpn, "lcsc": code, "provenance": [],
            "refs": [], "fps": [], "manufacturer": "", "notes": []})
        g["refs"].append(fp.ref)
        g["fps"].append(fp)
        if prov not in g["provenance"]:
            g["provenance"].append(prov)
        if not g["manufacturer"]:
            g["manufacturer"] = fp.props.get("Manufacturer", "").strip()
        g["notes"].extend(n for n in notes if n not in g["notes"])
    out = sorted(groups.values(), key=lambda g: natural_key(g["refs"][0]))
    by_vfm: dict = defaultdict(set)
    for g in out:
        by_vfm[(g["value"], g["footprint"], g["mpn"])].add(g["lcsc"])
    conflicts = [{"kind": "multiple-codes", "value": k[0], "footprint": k[1], "mpn": k[2], "lcsc": sorted(v)}
                 for k, v in sorted(by_vfm.items()) if len(v) > 1]
    conflicts += [{"kind": "pcb-vs-register", "mpn": k[0], "pcb_property": k[1], "register": k[2],
                   "designators": refs}
                  for k, refs in sorted(disagreements.items())]
    return out, conflicts


def cpl_rows(board: Board) -> list:
    return [[f.ref, fmt_num(f.x), fmt_num(-f.y), "Bottom" if f.side == "bottom" else "Top", fmt_num(norm_rot(f.rot))]
            for f in sorted((f for f in board.footprints if f.in_cpl), key=lambda f: natural_key(f.ref))]


def build_outputs(board: Board, register: dict) -> dict:
    groups, conflicts = bom_groups(board, register)
    jlc, sourcing, pcbway = [], [], []
    warnings = []
    for i, g in enumerate(groups, 1):
        refs = ",".join(g["refs"])
        comment = jlc_comment(g["value"], g["mpn"])
        jlc.append([comment, refs, g["footprint"], g["lcsc"]])
        if any(ord(ch) > 127 for ch in comment + g["footprint"]):
            warnings.append(f"non-ASCII text in BOM row for {refs}")
        status = "VERIFY LIVE" if g["lcsc"] else "NEEDS LCSC CODE"
        notes = "; ".join(g["notes"] + ([] if g["lcsc"] else ["unresolved"]))
        sourcing.append([refs, len(g["refs"]), g["value"], g["footprint"], g["mpn"], g["manufacturer"],
                         g["lcsc"], "+".join(g["provenance"]), status, notes])
        pcbway.append([i, refs, len(g["refs"]), g["manufacturer"], g["mpn"], g["value"], g["footprint"],
                       pcbway_type(g["fps"]), "; ".join(g["notes"])])
    inventory = {
        "schema": INVENTORY_SCHEMA, "pcb_sha256": board.sha256,
        "counts": {"footprints": len(board.footprints), "fitted": sum(f.fitted for f in board.footprints),
                   "bom_rows": len(groups), "lcsc_resolved_rows": sum(1 for g in groups if g["lcsc"]),
                   "lcsc_unresolved_rows": sum(1 for g in groups if not g["lcsc"])},
        "fitted": [{"ref": f.ref, "value": f.value, "footprint": f.name, "mpn": f.props.get("MPN", ""),
                    "manufacturer": f.props.get("Manufacturer", ""), "side": f.side,
                    "x": round(f.x, 6), "y": round(f.y, 6), "rot": round(f.rot, 6),
                    "hints": {k: f.props[k] for k in HINT_PROPS if k in f.props}}
                   for f in sorted((f for f in board.footprints if f.fitted), key=lambda f: natural_key(f.ref))],
        "excluded": [{"ref": f.ref, "reasons": f.exclusion_reasons()}
                     for f in sorted((f for f in board.footprints if not f.fitted), key=lambda f: natural_key(f.ref))],
        "unresolved_lcsc": [{"designators": g["refs"], "value": g["value"], "footprint": g["footprint"], "mpn": g["mpn"]}
                            for g in groups if not g["lcsc"]],
        "lcsc_conflicts": conflicts, "warnings": warnings,
    }
    return {"jlc": jlc, "sourcing": sourcing, "pcbway": pcbway, "cpl": cpl_rows(board), "inventory": inventory}


def cmd_build(args: argparse.Namespace) -> int:
    board = parse_board(args.pcb)
    out = build_outputs(board, load_register(args.register))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "jlc-bom.csv", JLC_HEADER, out["jlc"])
    write_csv(args.out_dir / "sourcing-bom.csv", SOURCING_HEADER, out["sourcing"])
    write_csv(args.out_dir / "pcbway-bom.csv", PCBWAY_HEADER, out["pcbway"])
    write_csv(args.out_dir / "cpl.csv", CPL_HEADER, out["cpl"])
    write_json(args.out_dir / "inventory.json", out["inventory"])
    c = out["inventory"]["counts"]
    print(f"fitted {c['fitted']}; BOM rows {c['bom_rows']} (LCSC resolved {c['lcsc_resolved_rows']}, "
          f"unresolved {c['lcsc_unresolved_rows']}); CPL rows {len(out['cpl'])}; "
          f"conflicts {len(out['inventory']['lcsc_conflicts'])}; warnings {len(out['inventory']['warnings'])}")
    return 0


def read_pos_csv(path: Path) -> list:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return [Row(r["Ref"], float(r["PosX"]), float(r["PosY"]), float(r["Rot"]), r["Side"].strip().lower(),
                    r["Val"], r["Package"]) for r in csv.DictReader(fh)]


def read_cpl_csv(path: Path) -> list:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return [Row(r["Designator"], float(r["Mid X"]), float(r["Mid Y"]), float(r["Rotation"]),
                    r["Layer"].strip().lower(), None, None) for r in csv.DictReader(fh)]


def compare_rows(report: Report, label: str, rows: list, expected: dict) -> None:
    seen: dict = {}
    dups = []
    for r in rows:
        if r.ref in seen:
            dups.append(r.ref)
        seen[r.ref] = r
    missing = sorted(set(expected) - set(seen), key=natural_key)
    extra = sorted(set(seen) - set(expected), key=natural_key)
    bad, text = [], []
    for ref, fp in expected.items():
        r = seen.get(ref)
        if r is None:
            continue
        if not (abs(r.x - fp.x) <= POS_TOL and abs(r.y + fp.y) <= POS_TOL
                and circ_diff(r.rot, fp.rot) <= POS_TOL and r.side == fp.side):
            bad.append(f"{ref}: file ({r.x}, {r.y}, {r.rot}, {r.side}) vs board ({fp.x}, {-fp.y}, {fp.rot % 360.0}, {fp.side})")
        if r.val is not None and (r.val != fp.value or r.pkg != fp.name):
            text.append(ref)
    ok = not (missing or extra or dups or bad)
    detail = f"{len(rows)} rows, {len(expected)} expected"
    for name, items in (("missing", missing), ("extra", extra), ("duplicate", dups), ("mismatch", bad)):
        if items:
            detail += f"; {name} {items[:5]}"
    report.add(f"{label}:rows", "PASS" if ok else "FAIL", detail)
    if text:
        report.add(f"{label}:text", "WARN", f"Val/Package text differs for {len(text)} rows: {text[:10]}")


def function_norm(s: str) -> str:
    s = s.strip().lower().replace(" ", "")
    return s[len("solder"):] if s.startswith("solder") else s


def function_matches(a: str, b: str) -> bool:
    na, nb = function_norm(a), function_norm(b)
    return na == nb or na.startswith(nb + ",") or nb.startswith(na + ",")


def pad_on_layer(pad: Pad, layer: str) -> bool:
    return layer in pad.layers or "*.Cu" in pad.layers


def compare_flashes(footprints: list, flashes: list, layer: str, tol: float = 1e-3) -> dict:
    by_ref = {f.ref: f for f in footprints}
    found: dict = defaultdict(list)
    result = {"flashes": len(flashes), "position_mismatch": [], "net_mismatch": [], "unknown_ref": [],
              "missing_flash": []}
    for gx, gy, ref, number, net in flashes:
        fp = by_ref.get(ref)
        if fp is None:
            result["unknown_ref"].append(ref)
            continue
        hit = None
        for p in fp.pads:
            if p.number == number and pad_on_layer(p, layer):
                bx, by = board_point(fp, p.x, p.y)
                if abs(bx - gx) <= tol and abs(by + gy) <= tol:
                    hit = p
                    break
        if hit is None:
            result["position_mismatch"].append(f"{ref}.{number} at ({gx:.4f}, {-gy:.4f})")
            continue
        found[ref].append(hit.index)
        if net is not None and hit.net != net and not (net == GERBER_NO_NET and not hit.net):
            result["net_mismatch"].append(f"{ref}.{number}: gerber {net!r} vs board {hit.net!r}")
    for fp in footprints:
        for p in fp.pads:
            if p.number and p.shape != "custom" and p.w > 0 and p.h > 0 and pad_on_layer(p, layer) \
                    and p.index not in found.get(fp.ref, []):
                result["missing_flash"].append(f"{fp.ref}.{p.number}")
    return result


def flashes_from_gerber(gf) -> list:
    out = []
    for o in gf.objects:
        if type(o).__name__ != "Flash":
            continue
        attrs = o.attrs or {}
        p = attrs.get(".P")
        if p:
            n = attrs.get(".N")
            out.append((o.x, o.y, p[0], p[1], n[0] if n else None))
    return out


def check_static(report: Report, board: Board) -> None:
    report.metrics.update(board_metrics(board))
    m = report.metrics
    bom = {f.ref for f in board.footprints if f.in_bom}
    cpl = {f.ref for f in board.footprints if f.in_cpl}
    report.add("fitted:bom-vs-cpl", "PASS" if bom == cpl else "WARN",
               f"BOM {len(bom)} refs, CPL {len(cpl)} refs, difference {sorted(bom ^ cpl, key=natural_key)}")
    outline = analyze_outline(board.root)
    problems = []
    if outline["unsupported"]:
        problems.append(f"unsupported Edge.Cuts items {outline['unsupported']}")
    if not outline["closed"]:
        problems.append(f"not one closed loop (components {outline['components']}, "
                        f"bad-degree nodes {outline['bad_degree_nodes']}, zero-length {outline['zero_length']})")
    if outline["crossings"]:
        problems.append(f"{len(outline['crossings'])} crossing or touching non-adjacent segment pairs")
    report.add("edge:closed-loop", "FAIL" if problems else "PASS",
               "; ".join(problems) or f"{outline['segments']} segments, bbox {m['edge.bbox']}, "
               f"perimeter {m['edge.perimeter_mm']} mm, area {m['edge.area_mm2']} mm2")
    non_through = m["vias.total"] - m["vias.through_FB"]
    report.add("vias:through-only", "FAIL" if non_through else "PASS",
               f"{m['vias.total']} vias, {non_through} not F.Cu-B.Cu through vias; {m['vias.by_size_drill']}")
    report.add("vias:in-pad-screen", "INFO",
               f"{m['via_in_pad.pairs']} via-pad pairs with the via centre inside a pad bbox, "
               f"{m['via_in_pad.fully_inside']} fully inside; screen only, not a process decision")
    stack = stackup_summary(board.root)
    if stack is None:
        report.add("stackup:summary", "WARN", "no stackup in the board file")
    else:
        gt = stack["general_thickness_mm"]
        report.add("stackup:summary", "INFO",
                   f"copper {stack['copper_mm']} + dielectric {stack['dielectric_mm']} = {stack['total_mm']} mm "
                   f"(other {stack['other_mm']}); general.thickness {gt}")


def check_drill(report: Report, board: Board, ddir: Path, basename: str) -> None:
    holes = expected_holes(board)
    for label, name, plated in (("PTH", f"{basename}-PTH.drl", True), ("NPTH", f"{basename}-NPTH.drl", False)):
        path = ddir / name
        if not path.is_file():
            report.add(f"drill:{label}:file", "FAIL", f"missing {name}")
            continue
        try:
            parsed = parse_excellon(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            report.add(f"drill:{label}:parse", "FAIL", str(exc))
            continue
        report.add(f"drill:{label}:parse", "PASS",
                   f"{len(parsed.hits)} hits, {len(parsed.slots)} slots, tools {dict(sorted(parsed.tools.items()))}")
        compare_drill(report, label, holes, parsed, plated)


def check_pos(report: Report, board: Board, pdir: Path, cpl: Path | None) -> None:
    sets = {"pos-all.csv": {f.ref: f for f in board.footprints if f.in_pos_all},
            "pos-fitted.csv": {f.ref: f for f in board.footprints if f.in_pos_fitted}}
    for name, expected in sets.items():
        path = pdir / name
        if not path.is_file():
            report.add(f"pos:{name}", "FAIL", "missing file")
            continue
        compare_rows(report, f"pos:{name}", read_pos_csv(path), expected)
    if cpl is not None:
        compare_rows(report, "cpl", read_cpl_csv(cpl), {f.ref: f for f in board.footprints if f.in_cpl})


def check_bom(report: Report, board: Board, bom: Path) -> None:
    with open(bom, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        header_ok = reader.fieldnames == JLC_HEADER
        refs = [r.strip() for row in reader for r in row["Designator"].split(",") if r.strip()]
    expected = {f.ref for f in board.footprints if f.fitted}
    dups = sorted({r for r in refs if refs.count(r) > 1}, key=natural_key)
    ok = header_ok and set(refs) == expected and not dups
    report.add("bom:designators", "PASS" if ok else "FAIL",
               f"{len(refs)} designators, expected {len(expected)}, header ok {header_ok}, duplicates {dups}, "
               f"missing {sorted(expected - set(refs), key=natural_key)}, extra {sorted(set(refs) - expected, key=natural_key)}")


def check_zip(report: Report, gdir: Path, ddir: Path, zpath: Path, job: dict, basename: str) -> None:
    members = [e["Path"] for e in job["FilesAttributes"]] + [f"{basename}-PTH.drl", f"{basename}-NPTH.drl"]
    with zipfile.ZipFile(zpath) as z:
        names = z.namelist()
        flat = all("/" not in n and "\\" not in n for n in names)
        bad = z.testzip()
        diffs = []
        for n in names:
            src = gdir / n if (gdir / n).is_file() else ddir / n
            if not src.is_file() or src.read_bytes() != z.read(n):
                diffs.append(n)
    exact = sorted(names) == sorted(members)
    ok = flat and bad is None and exact and not diffs
    report.add("zip:members", "PASS" if ok else "FAIL",
               f"{len(names)} entries, flat {flat}, crc {bad}, exact set {exact}, differing from source {diffs}; "
               f"missing {sorted(set(members) - set(names))}, extra {sorted(set(names) - set(members))}")


def check_receipt(report: Report, receipt: Path, root: Path) -> None:
    data = json.loads(receipt.read_text(encoding="utf-8"))
    bad = []
    for e in data["files"]:
        p = root / e["path"].replace("\\", "/")
        if not p.is_file():
            bad.append(f"{e['path']}: missing")
            continue
        digest, size = sha256_file(p)
        if digest != e["sha256"] or size != e["bytes"]:
            bad.append(f"{e['path']}: hash or size differs")
    report.add("receipt:rehash", "FAIL" if bad else "PASS", f"{len(data['files'])} entries; {bad[:5]}")


def check_gerbers(report: Report, board: Board, gdir: Path, job: dict) -> None:
    from gerbonara import GerberFile
    from gerbonara.utils import MM

    outline = analyze_outline(board.root)
    x0, y0, x1, y1 = outline["bbox"]
    hw = max(outline["widths"] or [0.0]) / 2.0
    size = job.get("GeneralSpecs", {}).get("Size", {})
    if size:
        ok = abs(size["X"] - (x1 - x0 + 2 * hw)) <= 1e-3 and abs(size["Y"] - (y1 - y0 + 2 * hw)) <= 1e-3
        report.add("gbrjob:size", "PASS" if ok else "FAIL",
                   f"job {size['X']} x {size['Y']} vs outline {x1 - x0 + 2 * hw:.4f} x {y1 - y0 + 2 * hw:.4f}")
    for entry in job["FilesAttributes"]:
        name = entry["Path"]
        path = gdir / name
        if not path.is_file():
            report.add(f"gerber:{name}", "FAIL", "listed in the job file but missing")
            continue
        gf = GerberFile.open(str(path))
        func = ",".join(gf.file_attrs.get(".FileFunction", ()))
        report.add(f"gerber:{name}:function", "PASS" if function_matches(func, entry["FileFunction"]) else "FAIL",
                   f"header {func!r}, job {entry['FileFunction']!r}")
        (bx0, by0), (bx1, by1) = gf.bounding_box(MM)
        if None in (bx0, by0, bx1, by1) or not gf.objects:
            report.add(f"gerber:{name}:content", "WARN", "no drawable objects")
            continue
        gb = (bx0, -by1, bx1, -by0)
        kind = function_norm(func).split(",")[0]
        if kind == "profile":
            exp = (x0 - hw, y0 - hw, x1 + hw, y1 + hw)
            ok = all(abs(a - b) <= 1e-3 for a, b in zip(gb, exp)) and len(gf.objects) == outline["segments"]
            report.add(f"gerber:{name}:outline", "PASS" if ok else "FAIL",
                       f"{len(gf.objects)} objects, bbox {[round(v, 4) for v in gb]} vs {[round(v, 4) for v in exp]}")
        elif kind in ("copper", "mask", "paste"):
            t = hw + 1e-3
            ok = gb[0] >= x0 - t and gb[1] >= y0 - t and gb[2] <= x1 + t and gb[3] <= y1 + t
            report.add(f"gerber:{name}:inside-outline", "PASS" if ok else "FAIL",
                       f"{len(gf.objects)} objects, bbox {[round(v, 4) for v in gb]}")
        else:
            report.add(f"gerber:{name}:content", "INFO", f"{len(gf.objects)} objects, bbox {[round(v, 4) for v in gb]}")
        parts = func.split(",")
        if parts[0] == "Copper" and parts[-1] in ("Top", "Bot"):
            if str(gf.unit) != str(MM):
                report.add(f"gerber:{name}:pads", "WARN", f"unit {gf.unit}; pad cross-check skipped")
                continue
            layer = "F.Cu" if parts[-1] == "Top" else "B.Cu"
            res = compare_flashes(board.footprints, flashes_from_gerber(gf), layer)
            bad = res["position_mismatch"] or res["unknown_ref"]
            report.add(f"gerber:{name}:pad-positions", "FAIL" if bad else "PASS",
                       f"{res['flashes']} pad flashes with identity; mismatched {res['position_mismatch'][:5]}; "
                       f"unknown refs {res['unknown_ref'][:5]}")
            report.add(f"gerber:{name}:pad-nets", "WARN" if res["net_mismatch"] else "PASS",
                       f"net mismatches {len(res['net_mismatch'])}: {res['net_mismatch'][:5]}")
            report.add(f"gerber:{name}:pad-coverage", "WARN" if res["missing_flash"] else "PASS",
                       f"board pads without a matching flash {len(res['missing_flash'])}: {res['missing_flash'][:10]}")


def cmd_verify(args: argparse.Namespace) -> int:
    if args.gerbers:
        try:
            import gerbonara  # noqa: F401
        except ImportError:
            print("gerbonara is required for --gerbers", file=sys.stderr)
            return 2
    board = parse_board(args.pcb)
    report = Report()
    root = args.export_root
    gdir, ddir, pdir, udir = root / "gerbers", root / "drill", root / "pos", root / "upload"
    check_static(report, board)
    check_drill(report, board, ddir, args.basename)
    check_pos(report, board, pdir, args.cpl)
    if args.bom is not None:
        check_bom(report, board, args.bom)
    zpath = args.zip
    if zpath is None:
        zips = sorted(udir.glob("*.zip")) if udir.is_dir() else []
        zpath = zips[0] if len(zips) == 1 else None
        if len(zips) != 1:
            report.add("zip:found", "WARN", f"{len(zips)} ZIP files under upload/")
    jobs = sorted(gdir.glob("*.gbrjob")) if gdir.is_dir() else []
    job = json.loads(jobs[0].read_text(encoding="utf-8")) if len(jobs) == 1 else None
    if job is None:
        report.add("gbrjob:found", "WARN", f"{len(jobs)} job files under gerbers/")
    elif zpath is not None:
        check_zip(report, gdir, ddir, zpath, job, args.basename)
    if args.gerbers and job is not None:
        check_gerbers(report, board, gdir, job)
    if args.receipt is not None:
        check_receipt(report, args.receipt, root)
    checked = [args.pcb] + sorted(ddir.glob("*")) + sorted(pdir.glob("*")) + sorted(gdir.glob("*"))
    if zpath is not None:
        checked.append(zpath)
    for p in checked:
        if p.is_file():
            digest, size = sha256_file(p)
            key = p.name if p == args.pcb else p.relative_to(root).as_posix()
            report.files[key] = {"sha256": digest, "bytes": size}
    if args.expect is not None:
        spec = json.loads(args.expect.read_text(encoding="utf-8"))
        if spec.get("schema") != EXPECT_SCHEMA:
            raise ValueError(f"expectation schema must be {EXPECT_SCHEMA}")
        for name, want in sorted(spec["expect"].items()):
            got = report.metrics.get(name, "<absent>")
            report.add(f"expect:{name}", "PASS" if values_equal(got, want) else "FAIL", f"got {got!r}, want {want!r}")
    result = report.to_dict()
    if args.out is not None:
        write_json(args.out, result)
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    for c in report.checks:
        if c["status"] in ("FAIL", "WARN"):
            print(f"{c['status']}: {c['name']}: {c['detail']}", file=sys.stderr)
    print(f"overall {result['overall']} {result['counts']}", file=sys.stderr)
    return 1 if result["overall"] == "FAIL" else 0


def manifest_name_problem(name: str) -> str:
    """Why a manifest name is unusable, or "" for a plain relative POSIX path."""
    if not name:
        return "empty name"
    if "\\" in name or name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        return "not a relative POSIX path"
    if any(part in ("", ".", "..") for part in name.split("/")):
        return "has an empty, '.' or '..' segment"
    return ""


def hashlist_write(root: Path, out: Path, names: list) -> int:
    lines = []
    seen = set()
    for name in names:
        problem = manifest_name_problem(name)
        if problem:
            raise ValueError(f"{name!r}: {problem}")
        if name in seen:
            raise ValueError(f"{name!r}: listed twice")
        seen.add(name)
        path = root.joinpath(*name.split("/"))
        if not path.is_file():
            raise ValueError(f"{name!r}: no such file under the root")
        if path.resolve() == out.resolve():
            raise ValueError(f"{name!r}: a manifest cannot list itself")
        lines.append(f"{sha256_file(path)[0]}  {name}")
    with open(out, "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return len(lines)


def hashlist_check(root: Path, manifest: Path) -> tuple:
    """Return (ok_count, problems) for a sha256sum-format file; CRLF is tolerated."""
    try:
        text = manifest.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return 0, ["manifest is not valid UTF-8"]
    ok = 0
    entries = 0
    problems = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        m = RE_HASH_LINE.match(line)
        if m is None:
            problems.append(f"line {lineno}: not a '<sha256>  <name>' line")
            continue
        entries += 1
        want, name = m.group(1).lower(), m.group(2)
        problem = manifest_name_problem(name)
        if problem:
            problems.append(f"line {lineno}: {name!r}: {problem}")
            continue
        path = root.joinpath(*name.split("/"))
        if not path.is_file():
            problems.append(f"{name}: missing")
            continue
        got = sha256_file(path)[0]
        if got != want:
            problems.append(f"{name}: sha256 mismatch (file {got[:12]}, manifest {want[:12]})")
            continue
        ok += 1
    if entries == 0:
        problems.append("no checksum lines found")
    return ok, problems


def cmd_hashlist(args: argparse.Namespace) -> int:
    if not args.root.is_dir():
        print(f"hashlist: root is not a directory: {args.root.name}", file=sys.stderr)
        return 2
    if args.check is not None:
        if args.names:
            print("hashlist: NAME arguments are only used with --out", file=sys.stderr)
            return 2
        if not args.check.is_file():
            print(f"hashlist: manifest not found: {args.check.name}", file=sys.stderr)
            return 2
        ok, problems = hashlist_check(args.root, args.check)
        for problem in problems:
            print(f"FAIL: {problem}", file=sys.stderr)
        print(f"hashlist check {args.check.name}: {ok} ok, {len(problems)} problem(s)")
        return 1 if problems else 0
    if not args.names:
        print("hashlist: at least one NAME is required with --out", file=sys.stderr)
        return 2
    try:
        count = hashlist_write(args.root, args.out, args.names)
    except ValueError as exc:
        print(f"hashlist: {exc}", file=sys.stderr)
        return 2
    print(f"hashlist wrote {count} entries to {args.out.name}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="write BOM/CPL/inventory files from the board text")
    b.add_argument("--pcb", type=Path, required=True)
    b.add_argument("--register", type=Path, required=True)
    b.add_argument("--out-dir", type=Path, required=True)
    v = sub.add_parser("verify", help="compare native exports with the board text")
    v.add_argument("--pcb", type=Path, required=True)
    v.add_argument("--export-root", type=Path, required=True)
    v.add_argument("--basename", default="handbell")
    v.add_argument("--cpl", type=Path)
    v.add_argument("--bom", type=Path)
    v.add_argument("--zip", type=Path)
    v.add_argument("--receipt", type=Path)
    v.add_argument("--expect", type=Path)
    v.add_argument("--out", type=Path)
    v.add_argument("--gerbers", action="store_true")
    h = sub.add_parser("hashlist", help="write or check a sha256sum-format manifest (LF, relative names)")
    h.add_argument("--root", type=Path, required=True)
    mode = h.add_mutually_exclusive_group(required=True)
    mode.add_argument("--out", type=Path)
    mode.add_argument("--check", type=Path)
    h.add_argument("names", nargs="*", help="files under --root as relative POSIX names (with --out)")
    args = parser.parse_args()
    handlers = {"build": cmd_build, "verify": cmd_verify, "hashlist": cmd_hashlist}
    return handlers[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
