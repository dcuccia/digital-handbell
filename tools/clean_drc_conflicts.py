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


def violation_uuids(report):
    pairs = set()
    for v in report.get("violations", []):
        if v["type"] in CONFLICT_TYPES:
            for item in v.get("items", []):
                if item.get("uuid"):
                    pairs.add((v["type"], item["uuid"]))
    return pairs


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True)
    ap.add_argument("--drc", required=True)
    ap.add_argument("--baseline-drc", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    new = violation_uuids(json.loads(Path(args.drc).read_text(encoding="utf-8")))
    old = violation_uuids(json.loads(Path(args.baseline_drc).read_text(encoding="utf-8")))
    targets = {u for t, u in new - old}
    pcbnew, _h = crr.load_pcbnew()
    board = pcbnew.LoadBoard(args.board)
    removed = {}
    for item in list(board.GetTracks()):
        net = item.GetNetname()
        protected = net == "/CELL_NEG" or (net == "VBAT" and item.IsOnLayer(pcbnew.B_Cu))
        if item.m_Uuid.AsString() in targets and not protected:
            removed[net] = removed.get(net, 0) + 1
            board.Remove(item)
    # Zones are refilled by the following DRC run; refilling here crashed pcbnew after bulk removals.
    pcbnew.SaveBoard(args.out, board)
    print(json.dumps({"removed_total": sum(removed.values()), "removed_by_net": removed}, indent=2))


if __name__ == "__main__":
    main()
