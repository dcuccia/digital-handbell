# SPDX-License-Identifier: MIT
"""Conservative footprint drawing bounds; these are not qualified part bodies."""
import math


def point(node):
    return tuple(map(float, node.atoms()[1:3]))


def drawing_points(item):
    if item.head in {"fp_line", "fp_rect"}:
        return [point(item.child("start")), point(item.child("end"))]
    if item.head == "fp_poly":
        return [point(p) for p in item.child("pts").children("xy")]
    if item.head == "fp_circle":
        x, y = point(item.child("center"))
        ex, ey = point(item.child("end"))
        radius = math.hypot(ex-x, ey-y)
        return [(x-radius, y-radius), (x+radius, y+radius)]
    if item.head == "fp_arc":
        a, b, c = [point(item.child(key)) for key in ["start", "mid", "end"]]
        ax, ay = a
        bx, by = b
        cx, cy = c
        d = 2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
        if abs(d) < 1e-10:
            return [a, b, c]
        ux = ((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/d
        uy = ((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/d
        radius = math.hypot(ax-ux, ay-uy)
        return [(ux-radius, uy-radius), (ux+radius, uy+radius)]
    raise ValueError(f"Unsupported selected drawing: {item.head}")


def bounds(points):
    if not points:
        raise ValueError("Cannot bound an empty footprint")
    return [min(p[0] for p in points), min(p[1] for p in points),
            max(p[0] for p in points), max(p[1] for p in points)]


def footprint_bounds(footprint):
    envelope, courtyard = [], []
    for pad in footprint.children("pad"):
        at = list(map(float, pad.child("at").atoms()[1:]))
        x, y = at[:2]
        angle = math.radians(at[2] if len(at) > 2 else 0)
        w, h = point(pad.child("size"))
        half_w = (abs(math.cos(angle))*w+abs(math.sin(angle))*h)/2
        half_h = (abs(math.sin(angle))*w+abs(math.cos(angle))*h)/2
        envelope.extend([(x-half_w, y-half_h), (x+half_w, y+half_h)])
        primitives = pad.child("primitives")
        if primitives:
            for primitive in primitives.children():
                if primitive.head != "gr_poly":
                    raise ValueError(f"Unsupported custom pad primitive: {primitive.head}")
                for p in primitive.child("pts").children("xy"):
                    px, py = point(p)
                    envelope.append((x+px*math.cos(angle)+py*math.sin(angle),
                                     y-px*math.sin(angle)+py*math.cos(angle)))
    for item in footprint.children():
        if item.head.startswith("fp_") and item.value("layer") in {"F.Fab", "F.SilkS", "F.CrtYd"}:
            if item.head in {"fp_text", "fp_text_box"}:
                continue
            points = drawing_points(item)
            if item.value("layer") == "F.CrtYd":
                courtyard.extend(points)
            else:
                envelope.extend(points)
    raw = bounds(envelope)
    planning = [raw[0]-.25, raw[1]-.25, raw[2]+.25, raw[3]+.25]
    if courtyard:
        c = bounds(courtyard)
        planning = [min(planning[0], c[0]), min(planning[1], c[1]),
                    max(planning[2], c[2]), max(planning[3], c[3])]
    return raw, planning, bool(courtyard)
