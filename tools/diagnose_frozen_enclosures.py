# SPDX-License-Identifier: MIT
"""Inventory frozen copper/pads/rule areas that enclose selected open endpoints.

This is a read-only diagnosis.  For each open item in a KiCad DRC report it
lists the nearest foreign-net primitives from the frozen board on every signal
layer, preserving UUIDs and positions.  Project-specific minimal-change and
risk dispositions are attached for engineering review; no change is applied.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from shapely.geometry import Point
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_routing_result as crr  # noqa: E402
from stitch_gnd_islands import item_shape, poly_set_to_shapely  # noqa: E402

LAYERS = ["F.Cu", "In2.Cu", "In3.Cu", "B.Cu"]

DISPOSITIONS = {
    "POWER": {
        "change": "Move the frozen ~ENABLE escape track nearest Q2.1 about 0.3 mm away from the pad.",
        "risk": "high",
        "why": "Power-selection control adjacent to the boost switch cell; requires loop/control review.",
    },
    "VO+": {
        "change": "Shift C22 about 0.5 mm toward J1 and replace its local VO+/GND fanout.",
        "risk": "high",
        "why": "BTL audio-output current path and return geometry; USB D- also passes behind C22.",
    },
    "GND:IC1": {
        "change": "Move the frozen XIN escape track beside IC1.19 about 0.3 mm and restore the crystal route.",
        "risk": "very high",
        "why": "Crystal/clock geometry and MCU return path are both sensitive.",
    },
    "GND:GAIN0": {
        "change": "Move the nearest frozen VBAT F.Cu segment about 0.3 mm away from GAIN0.1.",
        "risk": "high",
        "why": "High-current source copper next to amplifier gain/ground selection.",
    },
    "GND:POUR": {
        "change": "Revise the F.GND zone neck around frozen USB anchor X6.M3, then refill.",
        "risk": "medium-high",
        "why": "USB mechanical anchor/edge geometry and return continuity need review.",
    },
    "USBBOOT": {
        "change": "Move R18 about 0.3 mm away from D3.C and replace its short I2S_MOD/VAMP fanout.",
        "risk": "medium-high",
        "why": "Amplifier mode and supply-adjacent routing; MCU-side +3V3 fanout remains constrained.",
    },
    "SWDIO": {
        "change": "Reroute the frozen VCORE escape immediately beside IC1.25 by about 0.3 mm.",
        "risk": "very high",
        "why": "MCU core-supply/decoupling geometry competes with SWD recovery access.",
    },
    "I2S_LRCLK": {
        "change": "Move TP14 beyond the current 12 mm relocation domain rather than disturb USB D+ or U4 ground.",
        "risk": "medium",
        "why": "A test-point move is lower risk than changing the USB pair or amplifier thermal/return copper.",
    },
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def critical(net, ref):
    if net in {"USB_D+", "USB_D-"}:
        return "USB differential pair"
    if net in {"Net-(IC1-XIN)", "Net-(IC1-XOUT)"}:
        return "RP2040 crystal/clock"
    if net in {"VCORE", "+3V3"}:
        return "MCU core/supply distribution"
    if net in {"VBAT", "V+", "BOOST_FB"}:
        return "battery/boost power cell"
    if net in {"VAMP", "VO+", "VO-", "I2S_BCLK", "I2S_MOD"}:
        return "audio amplifier/signal group"
    if net in {"SWCLK", "SWDIO", "~{RESET}"}:
        return "debug/recovery"
    if net in {"CC1", "CC2"} or (ref and ref.startswith("X6.")):
        return "USB connector/CC interface"
    if net == "GND":
        return "protected return"
    return None


def link_key(net, descriptions):
    text = " ".join(descriptions)
    if net == "GND":
        if "IC1" in text:
            return "GND:IC1"
        if "GAIN0" in text:
            return "GND:GAIN0"
        return "GND:POUR"
    return net


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True, help="current best board")
    ap.add_argument("--frozen", required=True)
    ap.add_argument("--drc", required=True)
    ap.add_argument("--radius", type=float, default=2.0)
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    pcbnew, _handle = crr.load_pcbnew()
    frozen = pcbnew.LoadBoard(args.frozen)
    mm = pcbnew.ToMM
    layer_ids = {name: frozen.GetLayerID(name) for name in LAYERS}
    primitives = []
    for item in frozen.GetTracks():
        q = item.GetPosition()
        pos = [round(mm(q.x), 4), round(mm(q.y), 4)]
        for name, layer in layer_ids.items():
            if item.IsOnLayer(layer):
                primitives.append({
                    "net": item.GetNetname(), "layer": name, "type": item.GetClass(),
                    "uuid": item.m_Uuid.AsString(), "position": pos,
                    "shape": item_shape(pcbnew, item, layer), "ref": None,
                })
    for fp in frozen.GetFootprints():
        for pad in fp.Pads():
            q = pad.GetPosition()
            ref = f"{fp.GetReference()}.{pad.GetNumber()}"
            for name, layer in layer_ids.items():
                if pad.IsOnLayer(layer):
                    primitives.append({
                        "net": pad.GetNetname(), "layer": name, "type": "PAD",
                        "uuid": pad.m_Uuid.AsString(),
                        "position": [round(mm(q.x), 4), round(mm(q.y), 4)],
                        "shape": item_shape(pcbnew, pad, layer), "ref": ref,
                    })
    for zone in frozen.Zones():
        if not zone.GetIsRuleArea():
            continue
        shape = unary_union(poly_set_to_shapely(pcbnew, zone.Outline()))
        for name, layer in layer_ids.items():
            if zone.IsOnLayer(layer):
                primitives.append({
                    "net": zone.GetNetname(), "layer": name, "type": "RULE_AREA",
                    "uuid": zone.m_Uuid.AsString(), "position": None, "shape": shape,
                    "ref": zone.GetZoneName() or None,
                })

    report = json.loads(Path(args.drc).read_text(encoding="utf-8"))
    links = []
    for violation in report.get("unconnected_items", []):
        endpoints = violation["items"][:2]
        net = crr.drc_net(endpoints[0]["description"])
        descriptions = [item["description"] for item in endpoints]
        key = link_key(net, descriptions)
        endpoint_rows = []
        for endpoint in endpoints:
            point = Point(endpoint["pos"]["x"], endpoint["pos"]["y"])
            rows = []
            seen = set()
            for primitive in primitives:
                if primitive["net"] == net:
                    continue
                distance = primitive["shape"].distance(point)
                if distance > args.radius:
                    continue
                token = (primitive["uuid"], primitive["layer"])
                if token in seen:
                    continue
                seen.add(token)
                row = {k: v for k, v in primitive.items() if k != "shape"}
                row["distance_mm"] = round(distance, 4)
                row["critical_circuit"] = critical(row["net"], row["ref"])
                rows.append(row)
            rows.sort(key=lambda row: (row["distance_mm"], row["layer"], row["uuid"]))
            endpoint_rows.append({
                "description": endpoint["description"], "uuid": endpoint["uuid"],
                "position": endpoint["pos"], "frozen_bounds": rows[:args.limit],
            })
        disposition = DISPOSITIONS.get(key, {
            "change": "Requires engineering review.", "risk": "unranked", "why": "",
        })
        links.append({"key": key, "net": net, "endpoints": endpoint_rows,
                      "smallest_single_change": disposition})

    output = {
        "status": "DIAGNOSIS_ONLY", "board_sha256": sha256(args.board),
        "frozen_sha256": sha256(args.frozen), "radius_mm": args.radius,
        "links": links,
    }
    Path(args.out).write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"links": len(links), "out": str(Path(args.out).resolve())}, indent=2))


if __name__ == "__main__":
    main()
