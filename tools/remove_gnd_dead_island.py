# SPDX-License-Identifier: MIT
"""Remove only small filled islands from the named F.Cu GND zone and refill.

The zone outline and every other setting remain unchanged.  Native KiCad fill
is authoritative; the report records before/after island areas so a candidate
is accepted only when the intended dead island disappears without collateral
connectivity changes.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_routing_result as crr  # noqa: E402
from stitch_gnd_islands import poly_set_to_shapely  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True)
    ap.add_argument("--zone", default="quote-native-F-GND-v1")
    ap.add_argument("--minimum-area", type=float, default=3.0, help="remove islands below this area (mm^2)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    pcbnew, _handle = crr.load_pcbnew()
    board = pcbnew.LoadBoard(args.board)
    zone = next((z for z in board.Zones() if z.GetZoneName() == args.zone
                 and z.IsOnLayer(pcbnew.F_Cu)), None)
    if zone is None:
        raise SystemExit(f"zone not found: {args.zone}")

    def areas():
        return sorted(round(poly.area, 6)
                      for poly in poly_set_to_shapely(
                          pcbnew, zone.GetFilledPolysList(pcbnew.F_Cu)))

    before = areas()
    prior = {"mode": int(zone.GetIslandRemovalMode()),
             "minimum_area_raw": int(zone.GetMinIslandArea())}
    zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_AREA)
    # KiCad stores zone island area in squared internal units.
    zone.SetMinIslandArea(int(args.minimum_area * pcbnew.FromMM(1.0) ** 2))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    after = areas()
    pcbnew.SaveBoard(args.out, board)
    report = {
        "zone": args.zone, "zone_uuid": zone.m_Uuid.AsString(),
        "prior": prior, "mode": int(zone.GetIslandRemovalMode()),
        "minimum_area_mm2": args.minimum_area,
        "before_island_areas_mm2": before, "after_island_areas_mm2": after,
        "removed_areas_mm2": [area for area in before if area not in after],
    }
    Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"before": len(before), "after": len(after),
                      "removed": report["removed_areas_mm2"]}, indent=2))


if __name__ == "__main__":
    main()
