#!/usr/bin/env python3
"""Read back the isolated guard fixture, then run bounded KiCad CLI diagnostics."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROUNDTRIP_SHA = "0caf804fdd8afb18b20cdce78db05898479fafebaea6a29ee215ec22204e0148"
PROJECT_SHA = "ada159b721f8667449437318b30bab1a5be3881a707d9e39859658784b0730d4"
ORACLE = {
    "3ed47a01-14b9-59e7-bdfe-95561c7f1435": ("R26", "2", [86.4, 111.192], 90.0),
    "933e95b2-4ef8-5095-ab3d-4759e7fa0826": ("R27", "2", [86.424019, 109.500966], 0.0),
    "1ba917bc-32e2-5176-954f-c3d06c7f6040": ("R24", "2", [98.408, 111.4], 0.0),
    "bcb9e722-fe71-5b16-8387-e04b4bcd0520": ("C28", "2", [102.2, 116.15], 270.0),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def mm(pcb, value) -> float:
    return round(pcb.ToMM(value), 6)


def uuid(item) -> str:
    return item.m_Uuid.AsString()


def read_native(pcb, pcb_path: Path) -> dict:
    board = pcb.LoadBoard(str(pcb_path))
    try:
        records, seen = [], set()
        for footprint in board.GetFootprints():
            if footprint.GetReference() not in {"R24", "R26", "R27", "C28"}:
                continue
            for pad in footprint.Pads():
                ident = uuid(pad)
                if ident in seen:
                    raise RuntimeError(f"duplicate native pad UUID: {ident}")
                seen.add(ident)
                pos = pad.GetPosition()
                records.append({
                    "reference": footprint.GetReference(), "number": pad.GetNumber(),
                    "uuid": ident, "position_mm": [mm(pcb, pos.x), mm(pcb, pos.y)],
                    "orientation_deg": round(pad.GetOrientationDegrees(), 6),
                    "layers": [board.GetLayerName(i) for i in pad.GetLayerSet().Seq()],
                })
        if len(records) != 8:
            raise RuntimeError(f"expected 8 source pads, got {len(records)}")
        by_uuid = {item["uuid"]: item for item in records}
        oracle_checks = {}
        for ident, (ref, number, xy, angle) in ORACLE.items():
            item = by_uuid.get(ident)
            if item is None:
                raise RuntimeError(f"missing oracle UUID: {ident}")
            passed = (
                item["reference"] == ref and item["number"] == number
                and item["position_mm"] == xy and item["orientation_deg"] == angle
            )
            oracle_checks[f"{ref}.{number}"] = passed
            if not passed:
                raise RuntimeError(f"oracle mismatch for {ref}.{number}: {item}")
        restrictions = []
        for zone in board.Zones():
            if zone.GetIsRuleArea():
                restrictions.append({
                    "uuid": uuid(zone), "name": zone.GetZoneName(),
                    "layers": [board.GetLayerName(i) for i in zone.GetLayerSet().Seq()],
                    "tracks_not_allowed": bool(zone.GetDoNotAllowTracks()),
                    "vias_not_allowed": bool(zone.GetDoNotAllowVias()),
                    "pads_not_allowed": bool(zone.GetDoNotAllowPads()),
                    "copperpour_not_allowed": bool(zone.GetDoNotAllowZoneFills()),
                    "footprints_not_allowed": bool(zone.GetDoNotAllowFootprints()),
                })
        return {
            "pcbnew_version": pcb.GetBuildVersion(), "fixture_sha256": sha256(pcb_path),
            "source_pads": sorted(records, key=lambda x: (x["reference"], x["number"])),
            "oracle_checks": oracle_checks, "rule_area_count": len(restrictions),
            "rule_areas": restrictions,
        }
    finally:
        del board


def run_child(command, cwd: Path, limit: float, stem: str) -> dict:
    stdout = cwd / f"{stem}-stdout.bin"
    stderr = cwd / f"{stem}-stderr.bin"
    receipt_path = cwd / f"{stem}-receipt.json"
    if any(p.exists() for p in (stdout, stderr, receipt_path)):
        raise RuntimeError(f"refusing stale {stem} output")
    started = time.monotonic()
    with stdout.open("wb", buffering=0) as out, stderr.open("wb", buffering=0) as err:
        process = subprocess.Popen(
            command, cwd=cwd, stdin=subprocess.DEVNULL, stdout=out, stderr=err
        )
        receipt = {
            "state": "running", "command": command, "pid": process.pid,
            "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "limit_seconds": limit,
        }
        write_json(receipt_path, receipt)
        timed_out = False
        try:
            code = process.wait(timeout=limit)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            code = process.wait(timeout=5)
    receipt.update({
        "state": "completed",
        "command": command, "pid": process.pid, "limit_seconds": limit,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "timed_out": timed_out, "numeric_child_returncode": code,
        "child_confirmed_exited": process.poll() is not None,
        "stdout_bytes": stdout.stat().st_size, "stderr_bytes": stderr.stat().st_size,
        "stdout_sha256": sha256(stdout), "stderr_sha256": sha256(stderr),
    })
    write_json(receipt_path, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--kicad-bin", required=True, type=Path)
    args = parser.parse_args()
    if "SUPERVISED_PROCESS_RECEIPT" not in os.environ:
        raise RuntimeError("direct execution is forbidden; use supervise_process.py")
    if args.output.exists():
        raise RuntimeError("output directory already exists")
    if sha256(args.fixture) != ROUNDTRIP_SHA:
        raise RuntimeError("fixture is not the authorized exact roundtrip bytes")
    if sha256(args.project) != PROJECT_SHA:
        raise RuntimeError("project is not the bound private fixture project")
    args.output.mkdir(parents=True)

    pcb_path = args.output / "fixture-4layer-roundtrip.kicad_pcb"
    pro_path = args.output / "fixture-4layer-roundtrip.kicad_pro"
    shutil.copyfile(args.fixture, pcb_path)
    shutil.copyfile(args.project, pro_path)

    dll_handle = os.add_dll_directory(str(args.kicad_bin))
    try:
        sys.path.insert(0, str(args.kicad_bin / "Lib" / "site-packages"))
        import pcbnew as pcb
        readback = read_native(pcb, pcb_path)
    finally:
        dll_handle.close()
    write_json(args.output / "native-readback.json", readback)

    cli = args.kicad_bin / "kicad-cli.exe"
    version = run_child([str(cli), "--version"], args.output, 8, "cli-version")
    if version["timed_out"] or version["numeric_child_returncode"] != 0:
        raise RuntimeError("kicad-cli version probe failed")
    drc_output = args.output / "drc.json"
    drc = run_child([
        str(cli), "pcb", "drc", "--format", "json", "--output",
        str(drc_output), str(pcb_path)
    ], args.output, 60, "cli-drc")
    if drc["timed_out"] or drc["numeric_child_returncode"] != 0:
        raise RuntimeError("kicad-cli DRC failed")
    if not drc_output.is_file():
        raise RuntimeError("fresh DRC report absent")
    parsed = json.loads(drc_output.read_text(encoding="utf-8"))
    for key in ("violations", "unconnected_items", "schematic_parity"):
        if not isinstance(parsed.get(key), list):
            raise RuntimeError(f"DRC report missing array: {key}")
    drc.update(
        executable_sha256=sha256(cli), input_sha256=sha256(pcb_path),
        project_sha256=sha256(pro_path), output_exists=drc_output.is_file(),
        output_bytes=drc_output.stat().st_size if drc_output.is_file() else None,
        output_sha256=sha256(drc_output) if drc_output.is_file() else None,
    )
    result = {
        "completed_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "native_loads": 1, "native_saves": 0, "source_native_loads": 0,
        "readback": readback, "cli_version": version, "drc": drc,
    }
    write_json(args.output / "pipeline-result.json", result)
    return 0 if not drc["timed_out"] and drc["output_exists"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
