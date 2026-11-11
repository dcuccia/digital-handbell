# SPDX-License-Identifier: MIT
"""Build and measure the isolated four/six-layer private-plane controls."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import time
import uuid
from pathlib import Path

from kicad_sexpr import loads

FIXTURE_SHA = "0caf804fdd8afb18b20cdce78db05898479fafebaea6a29ee215ec22204e0148"
PROJECT_SHA = "ada159b721f8667449437318b30bab1a5be3881a707d9e39859658784b0730d4"
PRIVATE = {
    "eafa404c-be47-5f5c-8167-d39a967ba2e5": (100.2, 111.9),
    "6623be95-c657-5a8e-bedb-c5a73d42d40b": (103.7, 117.5),
}
SOURCE_HASHES = {
    "handbell.kicad_pcb": "adc262b3e7056cb9031387c55262b5cf99e599ae6e28970f9784f5237e662314",
    "handbell.kicad_sch": "ec93cc6f6f03bb91dd05199d2e0b4cab6b542567031e484fe8098056992ab69e",
    "handbell.kicad_pro": "8213261803c4a032c6351311ed43db6249720a8cb334ebd15e3daca210899990",
    "placement-manifest.json": "b849b5defb95f010f555d43b6d261fdea3ef37e240aee0190a607fb519c642f8",
    "battery-contact-interface.json": "f96133d9f044600167477bcddbf67c43311ed0897066db9fa63d8e7f8118467b",
}
NS = uuid.UUID("222b7253-9f55-502d-9c35-e054009a76d1")
ANCHOR_UUID = str(uuid.uuid5(NS, "diagnostic-gnd-anchor"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable(name: str) -> str:
    return str(uuid.uuid5(NS, name))


def zone(layer: str) -> str:
    return (
        f'(zone (net "GND") (layer "{layer}") (uuid "{stable("fill/" + layer)}") '
        f'(name "DIAGNOSTIC_GND_{layer}") (hatch edge 0.5) '
        f'(connect_pads (clearance 0)) (min_thickness 0.05) '
        f'(fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3) '
        f'(island_removal_mode 0)) '
        f'(polygon (pts (xy 70.5 85.5) (xy 164.5 85.5) '
        f'(xy 164.5 139.5) (xy 70.5 139.5))))'
    )


def guard(via_id: str, layer: str, xy: tuple[float, float]) -> str:
    x, y = xy
    x0, y0, x1, y1 = x - .55, y - .55, x + .55, y + .55
    flags = " ".join(
        f"({name} not_allowed)"
        for name in ("tracks", "vias", "pads", "copperpour", "footprints")
    )
    return (
        f'(zone (layer "{layer}") (uuid "{stable("guard/" + via_id + "/" + layer)}") '
        f'(name "PRIVATE_VIA_{via_id}_{layer}") (hatch edge 0.5) '
        f'(connect_pads (clearance 0)) (min_thickness 0.05) '
        f'(keepout {flags}) (polygon (pts (xy {x0:.6f} {y0:.6f}) '
        f'(xy {x1:.6f} {y0:.6f}) (xy {x1:.6f} {y1:.6f}) '
        f'(xy {x0:.6f} {y1:.6f}))))'
    )


def build_profile(base: str, profile: str) -> tuple[str, list[str]]:
    if profile not in {"four-positive", "six-positive", "six-negative"}:
        raise ValueError(profile)
    root = loads(base)
    if len(root.children("footprint")) != 8:
        raise RuntimeError("base footprint count differs")
    if sum(len(f.children("pad")) for f in root.children("footprint")) != 12:
        raise RuntimeError("base pad count differs")
    if len(root.children("segment")) != 10 or len(root.children("via")) != 4:
        raise RuntimeError("base track/via count differs")
    if len([z for z in root.children("zone") if z.child("keepout")]) != 23:
        raise RuntimeError("base rule-area count differs")
    layers = ["In1.Cu", "In2.Cu"]
    text = base.rstrip()
    if profile.startswith("six"):
        old = '\t\t(6 "In2.Cu" signal)\n\t\t(2 "B.Cu" signal)'
        new = (
            '\t\t(6 "In2.Cu" signal)\n\t\t(8 "In3.Cu" signal)\n'
            '\t\t(10 "In4.Cu" signal)\n\t\t(2 "B.Cu" signal)'
        )
        if text.count(old) != 1:
            raise RuntimeError("four-layer declaration was not unique")
        text = text.replace(old, new)
        layers += ["In3.Cu", "In4.Cu"]
    if not text.endswith(")"):
        raise RuntimeError("invalid fixture ending")
    additions = [
        f'(via (at 120 120) (size 0.6) (drill 0.3) '
        f'(layers "F.Cu" "B.Cu") (net "GND") (uuid "{ANCHOR_UUID}"))'
    ]
    if profile.startswith("six"):
        for via_id, xy in PRIVATE.items():
            for layer in ("In3.Cu", "In4.Cu"):
                if profile == "six-negative" and via_id.startswith("eafa") and layer == "In3.Cu":
                    continue
                additions.append(guard(via_id, layer, xy))
    additions.extend(zone(layer) for layer in layers)
    return text[:-1] + "\n" + "\n".join(additions) + "\n)\n", layers


def rectangle(pcb, x0: float, y0: float, x1: float, y1: float):
    chain = pcb.SHAPE_LINE_CHAIN()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        chain.Append(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y)))
    chain.SetClosed(True)
    poly = pcb.SHAPE_POLY_SET()
    poly.AddOutline(chain)
    return poly


def clearance_mm(pcb, poly, shape) -> float:
    if poly.Collide(shape, 0):
        return 0.0
    low, high = 0, pcb.FromMM(1)
    while not poly.Collide(shape, high):
        high *= 2
        if high > pcb.FromMM(100):
            raise RuntimeError("non-finite clearance")
    while high - low > 1:
        mid = (low + high) // 2
        if poly.Collide(shape, mid):
            high = mid
        else:
            low = mid
    return pcb.ToMM(low)


def uid(item) -> str:
    return item.m_Uuid.AsString()


def profile_counts(board) -> dict:
    classes = [type(x).__name__ for x in board.GetTracks()]
    return {
        "footprints": len(board.GetFootprints()),
        "pads": sum(1 for f in board.GetFootprints() for _ in f.Pads()),
        "tracks": classes.count("PCB_TRACK"),
        "vias": classes.count("PCB_VIA"),
        "rule_areas": sum(1 for z in board.Zones() if z.GetIsRuleArea()),
        "fill_zones": sum(1 for z in board.Zones() if not z.GetIsRuleArea()),
    }


def inspect_profile(pcb, board, profile: str, layers: list[str]) -> dict:
    by_name = {board.GetLayerName(i): i for i in board.GetEnabledLayers().Seq()}
    if list(name for name in ("F.Cu", *layers, "B.Cu") if name in by_name) != [
        "F.Cu", *layers, "B.Cu"
    ]:
        raise RuntimeError("logical copper names unavailable")
    vias = {uid(x): x for x in board.GetTracks() if x.Type() == pcb.PCB_VIA_T}
    anchor = vias[ANCHOR_UUID]
    zones = {z.GetZoneName(): z for z in board.Zones() if not z.GetIsRuleArea()}
    checks, anchors, witnesses = [], [], []
    for layer_name in layers:
        layer = by_name[layer_name]
        z = zones["DIAGNOSTIC_GND_" + layer_name]
        filled = z.GetFilledPolysList(layer)
        if filled is None or filled.IsEmpty():
            raise RuntimeError("empty native fill: " + layer_name)
        poly = filled.CloneDropTriangulation()
        ashape = anchor.GetEffectiveShape(layer)
        anchors.append({
            "layer": layer_name,
            "attached": bool(poly.Collide(ashape, 0)),
            "islands": poly.OutlineCount(),
            "area_mm2": round(poly.Area() / pcb.FromMM(1) ** 2, 6),
        })
        witness = rectangle(pcb, 86.39, 111.182, 86.41, 111.202)
        witnesses.append({
            "layer": layer_name,
            "R26_2_F_only_projection_filled": bool(poly.Collide(witness, 0)),
        })
        for via_id in PRIVATE:
            shape = vias[via_id].GetEffectiveShape(layer)
            distance = clearance_mm(pcb, poly, shape)
            checks.append({
                "via_uuid": via_id, "layer": layer_name,
                "intersects_fill": bool(poly.Collide(shape, 0)),
                "clearance_mm_lower_bound_1nm": round(distance, 6),
                "passes_0_25mm_minus_1nm": not poly.Collide(
                    shape, pcb.FromMM(.25) - 1
                ),
            })
    expected_negative = profile == "six-negative"
    negative = next(
        x for x in checks
        if x["via_uuid"].startswith("eafa") and x["layer"] == "In3.Cu"
    ) if expected_negative else None
    positives = [
        x for x in checks
        if not (expected_negative and x is negative)
    ]
    result = {
        "profile": profile,
        "enabled_copper_physical_order": ["F.Cu", *layers, "B.Cu"],
        "native_copper_layer_count": board.GetCopperLayerCount(),
        "counts": profile_counts(board),
        "private_via_fill_checks": checks,
        "anchor_attachments": anchors,
        "F_only_nonprojection_witnesses": witnesses,
        "minimum_positive_clearance_mm": min(x["clearance_mm_lower_bound_1nm"] for x in positives),
        "positive_pass": (
            all(x["passes_0_25mm_minus_1nm"] and not x["intersects_fill"] for x in positives)
            and all(x["attached"] for x in anchors)
            and all(x["R26_2_F_only_projection_filled"] for x in witnesses)
        ),
        "negative_missing_guard": negative,
        "negative_pass": (
            expected_negative and negative["intersects_fill"]
            and negative["clearance_mm_lower_bound_1nm"] == 0
        ) if expected_negative else None,
    }
    return result


def load_inspector_helper(path: Path):
    spec = importlib.util.spec_from_file_location("accepted_inspector", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", type=Path, required=True)
    ap.add_argument("--project", type=Path, required=True)
    ap.add_argument("--private-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--kicad-bin", type=Path, required=True)
    ap.add_argument("--accepted-inspector", type=Path, required=True)
    args = ap.parse_args()
    if "SUPERVISED_PROCESS_RECEIPT" not in os.environ:
        raise RuntimeError("must run under accepted supervisor")
    if args.output.exists():
        raise RuntimeError("output exists")
    if sha(args.fixture) != FIXTURE_SHA or sha(args.project) != PROJECT_SHA:
        raise RuntimeError("bound fixture/project hash mismatch")
    source_hashes = {
        name: sha(args.private_root / name) for name in SOURCE_HASHES
    }
    if source_hashes != SOURCE_HASHES:
        raise RuntimeError("authoritative source hash changed")
    args.output.mkdir(parents=True)
    base = args.fixture.read_text(encoding="utf-8")
    preflight = {}
    for profile in ("four-positive", "six-positive", "six-negative"):
        text, layers = build_profile(base, profile)
        parsed = loads(text)
        expected_rules = 23 if profile == "four-positive" else (
            26 if profile == "six-negative" else 27
        )
        actual_rules = len([z for z in parsed.children("zone") if z.child("keepout")])
        if actual_rules != expected_rules:
            raise RuntimeError(f"{profile} rule count {actual_rules}")
        path = args.output / f"{profile}-unfilled.kicad_pcb"
        path.write_text(text, encoding="utf-8")
        shutil.copyfile(args.project, path.with_suffix(".kicad_pro"))
        preflight[profile] = {
            "unfilled_sha256": sha(path), "logical_inner_layers": layers,
            "rule_areas": actual_rules,
            "private_guard_obligations": actual_rules - 5,
            "diagnostic_rule_areas": 5,
        }

    dll_handle = os.add_dll_directory(str(args.kicad_bin))
    try:
        sys.path.insert(0, str(args.kicad_bin / "Lib" / "site-packages"))
        pcb = __import__("pcbnew")
        accepted = load_inspector_helper(args.accepted_inspector)
        if accepted.ROUNDTRIP_SHA != FIXTURE_SHA or accepted.PROJECT_SHA != PROJECT_SHA:
            raise RuntimeError("accepted inspector bindings differ")
        profiles = {}
        for profile, row in preflight.items():
            started = time.monotonic()
            source = args.output / f"{profile}-unfilled.kicad_pcb"
            saved = args.output / f"{profile}-filled.kicad_pcb"
            board = pcb.LoadBoard(str(source))
            before = profile_counts(board)
            if before["footprints"] != 8 or before["pads"] != 12 or before["tracks"] != 10:
                raise RuntimeError("retained object count changed before fill")
            expected_vias = 5
            if before["vias"] != expected_vias:
                raise RuntimeError("diagnostic anchor via missing")
            board.BuildConnectivity()
            if not pcb.ZONE_FILLER(board).Fill(board.Zones()):
                raise RuntimeError("native fill failed")
            if not pcb.SaveBoard(str(saved), board, True):
                raise RuntimeError("native save failed")
            shutil.copyfile(args.project, saved.with_suffix(".kicad_pro"))
            del board
            reloaded = pcb.LoadBoard(str(saved))
            result = inspect_profile(
                pcb, reloaded, profile, row["logical_inner_layers"]
            )
            result.update({
                "native_loads": 2, "native_fills": 1, "native_saves": 1,
                "elapsed_seconds": round(time.monotonic() - started, 6),
                "filled_pcb_sha256": sha(saved),
                "project_sha256": sha(saved.with_suffix(".kicad_pro")),
                "retained_counts_before_fill": before,
                "retained_counts_after_reload": profile_counts(reloaded),
            })
            profiles[profile] = result
            del reloaded
    finally:
        dll_handle.close()
    if not profiles["four-positive"]["positive_pass"]:
        raise RuntimeError("four-layer positive failed")
    if not profiles["six-positive"]["positive_pass"]:
        raise RuntimeError("six-layer positive failed")
    if not profiles["six-negative"]["positive_pass"] or not profiles["six-negative"]["negative_pass"]:
        raise RuntimeError("six-layer negative control failed")
    output = {
        "schema_version": 1, "status": "PASS_ISOLATED_NATIVE_FILL_CONTROL",
        "pcbnew_version": pcb.GetBuildVersion(),
        "fixture_sha256": FIXTURE_SHA, "project_sha256": PROJECT_SHA,
        "source_native_loads": 0, "profile_operations": 3,
        "native_loads": 6, "native_fills": 3, "native_saves": 3,
        "preflight": preflight, "profiles": profiles,
        "source_hashes": source_hashes,
        "metric": {
            "fill": "ZONE.GetFilledPolysList(layer).CloneDropTriangulation(), including native holes",
            "private_object": "PCB_VIA.GetEffectiveShape(layer), complete 0.600 mm copper annulus/disk",
            "clearance": "native SHAPE_POLY_SET.Collide monotonic 1 nm lower-bound search",
            "threshold": "0.25 mm minus one internal unit (1 nm); numeric control tolerance only",
        },
        "drc_run": False,
        "limits": [
            "Conservative rectangular rule areas, not exact curved guards.",
            "Synthetic fixture control only; not full input, product routing, Quilter, stackup, supplier, or manufacturing qualification.",
            "Known retained same-net source objects remain inside all-object guards; no product-clean claim.",
        ],
    }
    result_path = args.output / "result.json"
    result_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "result": str(result_path), "sha256": sha(result_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
