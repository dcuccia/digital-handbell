# SPDX-License-Identifier: MIT
"""Remove router-added B.Cu copper that intersects battery-contact metal guards.

DeepPCB was observed to place B.Cu copper inside CONTACT_METAL_GUARD rule areas.
Only copper absent from the frozen base board is removed.
"""
import argparse
import json
import sys
from pathlib import Path

from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_routing_result as crr  # noqa: E402
from stitch_gnd_islands import item_shape, poly_set_to_shapely  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", required=True)
    ap.add_argument("--board", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    pcbnew, _h = crr.load_pcbnew()
    base = pcbnew.LoadBoard(args.base)
    board = pcbnew.LoadBoard(args.board)
    _, new = crr.compare_copper(crr.copper_items(pcbnew, base), crr.copper_items(pcbnew, board))
    new_ids = {item[-1].m_Uuid.AsString() for _, item in new}
    guards = unary_union([unary_union(poly_set_to_shapely(pcbnew, z.Outline())) for z in board.Zones()
                          if z.GetIsRuleArea() and z.GetZoneName().startswith("CONTACT_METAL_GUARD")])
    removed = [t for t in board.GetTracks() if t.m_Uuid.AsString() in new_ids and t.IsOnLayer(pcbnew.B_Cu)
               and item_shape(pcbnew, t, pcbnew.B_Cu).intersects(guards)]
    summary = [(t.GetNetname(), t.GetClass()) for t in removed]
    for t in removed:
        board.Remove(t)
    pcbnew.SaveBoard(args.out, board)
    print(json.dumps({"removed": summary}))


if __name__ == "__main__":
    main()
