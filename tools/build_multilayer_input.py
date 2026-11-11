# SPDX-License-Identifier: MIT
"""Build a six-layer routing baseline from the authoritative board and a placement.

Private-copy preparation step for the multilayer plan:
- footprints take their poses from a placement board (e.g. the moved-MCU copy);
- authoritative copper is kept per connected island: islands touching only
  unmoved parts stay; islands touching only parts that moved by one common
  offset move with them; all other islands are dropped for re-routing;
- the copper layer table and physical stackup come from a stackup board;
- In1 rule areas and the In1 GND plane are mirrored onto the new GND plane
  layer, and listed rule areas are translated with their parts.
"""
import argparse
import json
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_routing_result as crr  # noqa: E402
from stitch_gnd_islands import item_shape  # noqa: E402


def block_at(text, start):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return start, i + 1
    raise ValueError("unbalanced")


def find_block(text, head, after=0):
    i = text.find(head, after)
    if i < 0:
        raise SystemExit(f"{head} not found")
    return block_at(text, i)


def islands(pcbnew, board):
    """Group track/via items into connected islands per net; return list of (items, pads)."""
    mm = pcbnew.ToMM
    lay = {"F.Cu": pcbnew.F_Cu, "In1.Cu": pcbnew.In1_Cu, "In2.Cu": pcbnew.In2_Cu, "B.Cu": pcbnew.B_Cu}
    by_net = {}
    for item in board.GetTracks():
        shapes = {n: item_shape(pcbnew, item, l) for n, l in lay.items() if item.IsOnLayer(l)}
        by_net.setdefault(item.GetNetname(), []).append((item, shapes))
    pads_by_net = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            shapes = {n: item_shape(pcbnew, pad, l) for n, l in lay.items() if pad.IsOnLayer(l)}
            pads_by_net.setdefault(pad.GetNetname(), []).append((fp.GetReference(), shapes))
    result = []
    for net, items in by_net.items():
        parent = list(range(len(items)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if any(lname in items[j][1] and s.intersects(items[j][1][lname])
                       for lname, s in items[i][1].items()):
                    parent[find(i)] = find(j)
        groups = {}
        for i in range(len(items)):
            groups.setdefault(find(i), []).append(i)
        for members in groups.values():
            refs = set()
            for ref, pshapes in pads_by_net.get(net, []):
                if any(lname in items[m][1] and s.intersects(items[m][1][lname])
                       for m in members for lname, s in pshapes.items()):
                    refs.add(ref)
            result.append((net, [items[m][0] for m in members], refs))
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True, help="authoritative-derived 4-layer board with guards")
    ap.add_argument("--placement", required=True, help="board whose footprint poses are used")
    ap.add_argument("--stackup", required=True, help="board providing (layers ...) and (stackup ...)")
    ap.add_argument("--plane-layer", default="In4.Cu", help="new GND plane layer mirroring In1")
    ap.add_argument("--translate-areas", nargs="*", default=["in1-clock-region"],
                    help="rule-area name prefixes moved with the parts they sit under")
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    pcbnew, _h = crr.load_pcbnew()
    mm = pcbnew.ToMM
    board = pcbnew.LoadBoard(args.source)
    place = pcbnew.LoadBoard(args.placement)
    poses = {f.GetReference(): (f.GetPosition(), f.GetOrientationDegrees(), f.GetLayer()) for f in place.GetFootprints()}
    deltas = {}
    for fp in board.GetFootprints():
        pos, ang, layer = poses[fp.GetReference()]
        old = fp.GetPosition()
        d = (round(mm(pos.x - old.x), 4), round(mm(pos.y - old.y), 4))
        if abs(ang - fp.GetOrientationDegrees()) > 1e-3 or layer != fp.GetLayer():
            raise SystemExit(f"{fp.GetReference()} rotation/side change is not supported")
        deltas[fp.GetReference()] = d

    plan = []
    for net, items, refs in islands(pcbnew, board):
        moved = {r for r in refs if deltas[r] != (0.0, 0.0)}
        offsets = {deltas[r] for r in refs}
        if not moved:
            plan.append((net, items, "keep", None))
        elif refs and moved == refs and len(offsets) == 1:
            plan.append((net, items, "shift", offsets.pop()))
        else:
            plan.append((net, items, "drop", None))

    # Rule areas sitting under moved parts move with the most common offset of the parts they cover.
    for zone in list(board.Zones()):
        if not any(zone.GetZoneName().startswith(p) for p in args.translate_areas):
            continue
        outline = zone.Outline()
        covered = [deltas[f.GetReference()] for f in board.GetFootprints()
                   if outline.Contains(f.GetPosition()) and deltas[f.GetReference()] != (0.0, 0.0)]
        if covered:
            dx, dy = max(set(covered), key=covered.count)
            zone.Move(pcbnew.VECTOR2I(pcbnew.FromMM(dx), pcbnew.FromMM(dy)))
    for fp in list(board.GetFootprints()):
        dx, dy = deltas[fp.GetReference()]
        if (dx, dy) != (0.0, 0.0):
            fp.Move(pcbnew.VECTOR2I(pcbnew.FromMM(dx), pcbnew.FromMM(dy)))

    kept = dropped = shifted = 0
    summary = {}
    for net, items, action, offset in plan:
        if action == "shift":
            vec = pcbnew.VECTOR2I(pcbnew.FromMM(offset[0]), pcbnew.FromMM(offset[1]))
            for item in items:
                item.Move(vec)
            shifted += len(items)
        elif action == "drop":
            for item in items:
                board.Remove(item)
            dropped += len(items)
        else:
            kept += len(items)
        summary.setdefault(net, {"keep": 0, "shift": 0, "drop": 0})[action] += len(items)
    tmp = args.out + ".tmp"
    pcbnew.SaveBoard(tmp, board)

    text = Path(tmp).read_text(encoding="utf-8")
    Path(tmp).unlink()
    stack_text = Path(args.stackup).read_text(encoding="utf-8")
    for head in ("(layers", "(stackup"):
        s0, s1 = find_block(stack_text, head)
        if text.find(head) < 0 and head == "(stackup":
            insert_at = text.find("(setup") + len("(setup")
            text = text[:insert_at] + "\n\t\t" + stack_text[s0:s1] + text[insert_at:]
            continue
        t0, t1 = find_block(text, head)
        text = text[:t0] + stack_text[s0:s1] + text[t1:]
    # Mirror In1 zones (GND plane and In1 rule areas) onto the new plane layer.
    mirrored = []
    for m in re.finditer(r'\(zone\b', text):
        z0, z1 = block_at(text, m.start())
        z = text[z0:z1]
        if '(layer "In1.Cu")' in z:
            copy = z.replace('(layer "In1.Cu")', f'(layer "{args.plane_layer}")')
            copy = re.sub(r'\(uuid "[^"]+"\)', lambda _m: f'(uuid "{uuid.uuid4()}")', copy, count=1)
            copy = re.sub(r'\(name "([^"]*)"\)', lambda mm_: f'(name "{mm_.group(1)}-{args.plane_layer[:3].lower()}")',
                          copy, count=1)
            copy = re.sub(r'\(filled_polygon[\s\S]*?\n\t\t\)', '', copy)
            mirrored.append(copy)
    end = text.rstrip().rfind(")")
    text = text[:end] + "\n".join(mirrored) + "\n" + text[end:]
    Path(args.out).write_text(text, encoding="utf-8", newline="")

    report = {"kept_items": kept, "shifted_items": shifted, "dropped_items": dropped,
              "moved_parts": sorted(r for r, d in deltas.items() if d != (0.0, 0.0)),
              "mirrored_zones": len(mirrored), "per_net": summary}
    Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "per_net"}, indent=2))


if __name__ == "__main__":
    main()
