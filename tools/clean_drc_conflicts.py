# SPDX-License-Identifier: MIT
"""Remove tracks/vias that take part in new DRC conflicts, so a router can redo them.

Compares a DRC report with a baseline report and deletes only track/via items
(never pads or zones) that appear in conflict violations absent from the
baseline. Protected nets are never touched.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_routing_result as crr  # noqa: E402

CONFLICT_TYPES = {"clearance", "shorting_items", "tracks_crossing", "hole_clearance", "hole_to_hole",
                  "items_not_allowed", "copper_edge_clearance", "track_dangling", "via_dangling"}
PROTECTED_NETS = {"/CELL_NEG", "VBAT"}


def violation_items(report):
    pairs = set()
    for v in report.get("violations", []):
        if v["type"] in CONFLICT_TYPES:
            for item in v.get("items", []):
                desc = item.get("description", "")
                net = desc.split("[", 1)[1].split("]", 1)[0] if "[" in desc else ""
                kind = "via" if desc.startswith("Via") else ("track" if desc.startswith("Track") else "")
                pairs.add((v["type"], item.get("uuid", ""), kind, net,
                           round(item["pos"]["x"], 3), round(item["pos"]["y"], 3)))
    return pairs


def violation_uuids(report):
    return {(t, u) for t, u, *_ in violation_items(report)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True)
    ap.add_argument("--drc", required=True)
    ap.add_argument("--baseline-drc", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--base-board", help="if given, only copper absent from this board may be removed")
    args = ap.parse_args()

    new = violation_items(json.loads(Path(args.drc).read_text(encoding="utf-8")))
    old = violation_items(json.loads(Path(args.baseline_drc).read_text(encoding="utf-8")))
    old_keys = {(t, k, n, x, y) for t, _u, k, n, x, y in old}
    fresh = [(t, u, k, n, x, y) for t, u, k, n, x, y in new if (t, k, n, x, y) not in old_keys]
    targets = {u for _t, u, *_ in fresh}
    located = [(k, n, x, y) for _t, _u, k, n, x, y in fresh if k]
    pcbnew, _h = crr.load_pcbnew()
    board = pcbnew.LoadBoard(args.board)
    mm = pcbnew.ToMM
    for item in board.GetTracks():
        kind = "via" if item.GetClass() == "PCB_VIA" else "track"
        points = [item.GetPosition()] if kind == "via" else [item.GetStart(), item.GetEnd()]
        for k, n, x, y in located:
            if k == kind and n == item.GetNetname() and any(
                    abs(mm(p.x) - x) < 0.002 and abs(mm(p.y) - y) < 0.002 for p in points):
                targets.add(item.m_Uuid.AsString())
                break
    if args.base_board:
        base = pcbnew.LoadBoard(args.base_board)
        _, added = crr.compare_copper(crr.copper_items(pcbnew, base), crr.copper_items(pcbnew, board))
        removable = {item[-1].m_Uuid.AsString() for _, item in added}
        targets &= removable
    removed = {}
    for item in list(board.GetTracks()):
        net = item.GetNetname()
        # With a base board, only new copper is removable, so new VBAT copper may go too.
        protected = net == "/CELL_NEG" or (not args.base_board and net == "VBAT" and item.IsOnLayer(pcbnew.B_Cu))
        if item.m_Uuid.AsString() in targets and not protected:
            removed[net] = removed.get(net, 0) + 1
            board.Remove(item)
    # Zones are refilled by the following DRC run; refilling here crashed pcbnew after bulk removals.
    pcbnew.SaveBoard(args.out, board)
    print(json.dumps({"removed_total": sum(removed.values()), "removed_by_net": removed}, indent=2))


if __name__ == "__main__":
    main()
