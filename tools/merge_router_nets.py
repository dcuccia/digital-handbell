# SPDX-License-Identifier: MIT
"""Merge only router-added copper on selected nets back onto a protected baseline.

Used when an external router improves unfinished nets but also disturbs copper
it was told to keep. Every baseline item is kept unchanged; router copper is
added only for the listed nets, and nets can be excluded after DRC review.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_routing_result as crr  # noqa: E402


def open_nets_from_drc(path):
    report = json.loads(Path(path).read_text(encoding="utf-8"))
    nets = set()
    for item in report.get("unconnected_items", []):
        for obj in item.get("items", []):
            desc = obj.get("description", "")
            if "[" in desc:
                nets.add(crr.drc_net(desc))
    return nets


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", required=True)
    ap.add_argument("--router", required=True)
    ap.add_argument("--base-drc", required=True, help="DRC report whose unconnected nets are eligible")
    ap.add_argument("--extra-nets", nargs="*", default=[], help="additional eligible nets (e.g. ripped-up nets)")
    ap.add_argument("--exclude-net", nargs="*", default=[])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    pcbnew, _handle = crr.load_pcbnew()
    base = pcbnew.LoadBoard(args.base)
    router = pcbnew.LoadBoard(args.router)
    _, new = crr.compare_copper(crr.copper_items(pcbnew, base), crr.copper_items(pcbnew, router))
    base_vias = [(t.GetNetname(), t.GetPosition()) for t in base.GetTracks() if t.GetClass() == "PCB_VIA"]

    def duplicate_via(src):
        p = src.GetPosition()
        return any(n == src.GetNetname() and abs(q.x - p.x) < 20000 and abs(q.y - p.y) < 20000
                   for n, q in base_vias)
    eligible = (open_nets_from_drc(args.base_drc) | set(args.extra_nets)) - set(args.exclude_net) - crr.ISOLATED_NETS
    added = {}
    for key, item in new:
        net = key[0] if isinstance(key, tuple) else key
        if net not in eligible:
            continue
        src = item[-1]
        if src.GetClass() == "PCB_VIA" and duplicate_via(src):
            continue
        if src.GetClass() == "PCB_VIA":
            dst = pcbnew.PCB_VIA(base)
            dst.SetPosition(src.GetPosition())
            dst.SetWidth(src.GetWidth(pcbnew.F_Cu))
            dst.SetDrill(src.GetDrillValue())
            dst.SetViaType(src.GetViaType())
            dst.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        else:
            dst = pcbnew.PCB_TRACK(base)
            dst.SetStart(src.GetStart())
            dst.SetEnd(src.GetEnd())
            dst.SetWidth(src.GetWidth())
            dst.SetLayer(src.GetLayer())
        dst.SetNet(base.FindNet(net))
        base.Add(dst)
        added[net] = added.get(net, 0) + 1
    pcbnew.SaveBoard(args.out, base)
    print(json.dumps({"eligible_nets": sorted(eligible), "added_by_net": added,
                      "skipped_router_items": len(new) - sum(added.values())}, indent=2))


if __name__ == "__main__":
    main()
