# SPDX-License-Identifier: MIT
"""Bounded local Freerouting exchange/proposal pilot; never modifies the source PCB."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kicad_sexpr import apply_edits, loads
from route_clock_local import PACKAGE

JAR_SHA = "251101c3eeac22d7e7dfcf6796603279e5d1000283eb82d8f093780f7afc6aa9"
PCB_SHA = "57ae2c0b54e1313fb175ccdecdee07ebda07abed5151e776c9767511135d440f"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def geometry(board, pcb):
    parts = {f.GetReference(): (tuple(f.GetPosition()), f.GetOrientationDegrees(), f.GetLayer(),
                               tuple(sorted((p.GetNumber(), p.GetNetname(), tuple(p.GetPosition()),
                                             tuple(p.GetSize()), p.GetOrientationDegrees(),
                                             tuple(p.GetLayerSet().Seq())) for p in f.Pads())))
             for f in board.GetFootprints()}
    tracks = Counter()
    for t in board.GetTracks():
        if isinstance(t, pcb.PCB_VIA):
            key = ("via", t.GetNetname(), tuple(t.GetPosition()), t.GetDrillValue(),
                   tuple((layer, t.GetWidth(layer)) for layer in t.GetLayerSet().Seq()))
        else:
            if isinstance(t, pcb.PCB_ARC):
                raise ValueError("Arc comparison needs explicit implementation")
            a, b = sorted((tuple(t.GetStart()), tuple(t.GetEnd())))
            key = ("track", t.GetNetname(), t.GetLayer(), t.GetWidth(), a, b)
        tracks[key] += 1
    return parts, tracks


def prepare(raw, net):
    # DSN's quote declaration is not a KiCad string. Normalize only while parsing.
    text = raw.replace('(string_quote ")', "(string_quote dq)")
    text = '(pcb "handbell-pilot"\n' + text.split("\n", 1)[1]
    tree = loads(text)
    structure, network, wiring = (tree.child(k) for k in ("structure", "network", "wiring"))
    edits = [(n.start, n.end, "") for n in structure.children("plane")]
    classes, hits = [], 0
    for group in network.children("class"):
        classes.append(group.atoms()[1])
        for item in group.items[2:]:
            if getattr(item, "value", None) == net:
                edits.append((item.start, item.end, ""))
                hits += 1
    if hits != 1:
        raise ValueError("Target must belong to exactly one exported net class")
    edits.append((network.end-1, network.end-1,
                  f'\n(class pilot {json.dumps(net)} (rule (width 200) (clearance 210)))\n'))
    protected = 0
    for item in wiring.children():
        if item.head not in ("wire", "via"):
            raise ValueError("Unexpected wiring item: " + item.head)
        fixed = item.child("type")
        if fixed:
            edits.append((fixed.start, fixed.end, "(type protect)"))
        else:
            edits.append((item.end-1, item.end-1, "(type protect)"))
        protected += 1
    adjusted = []
    for rule in structure.children("rule"):
        for clearance in rule.children("clearance"):
            if float(clearance.atoms()[1]) < 200:
                value = clearance.items[1]
                adjusted.append(clearance.atoms()[1])
                edits.append((value.start, value.end, "200"))
    output = apply_edits(text, edits).replace("(string_quote dq)", '(string_quote ")')
    return output, {"ignored_classes": classes, "target_class": "pilot", "target_net": net,
                    "protected_wiring_items": protected,
                    "removed_outline_planes": len(structure.children("plane")),
                    "raised_clearance_values_um": adjusted,
                    "target_width_mm": .2, "target_clearance_mm": .21,
                    "scope": "F-only, no new vias; GND plane outline omitted intentionally. Existing pour-only exclusions export as conservative routing keepouts. Custom B metal is not qualified by this pilot."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java", type=Path, required=True)
    parser.add_argument("--jar", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--net", default="GAIN")
    parser.add_argument("--no-routing", action="store_true")
    parser.add_argument("--explicit-settings", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--legacy-engine", action="store_true")
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists() or sha(args.jar) != JAR_SHA or sha(PACKAGE / "handbell.kicad_pcb") != PCB_SHA:
        raise ValueError("Require new output and the pinned board/JAR")
    out.mkdir(parents=True)
    native = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin"
    dll_handle = os.add_dll_directory(str(native))
    sys.path.insert(0, str(native / "Lib" / "site-packages"))
    import pcbnew as pcb
    if pcb.GetBuildVersion() != "10.0.6":
        raise ValueError("KiCad 10.0.6 required")
    board = pcb.LoadBoard(str(PACKAGE / "handbell.kicad_pcb"))
    old_parts, old_tracks = geometry(board, pcb)
    started = time.monotonic()
    if not pcb.ExportSpecctraDSN(board, str(out / "raw.dsn")):
        raise RuntimeError("DSN export failed")
    export_seconds = time.monotonic() - started
    prepared, adjustments = prepare((out / "raw.dsn").read_text(encoding="utf-8"), args.net)
    (out / "pilot.dsn").write_bytes(prepared.encode("utf-8"))
    ignored = adjustments["ignored_classes"] + (["pilot"] if args.no_routing else [])
    options = [
        "-da", "--gui.enabled=false", "--api_server.enabled=false", "--mcp_server.enabled=false",
        "--feature_flags.save_jobs=false", "--router.optimizer.enabled=false",
        "--router.fanout.enabled=false", "--router.allowed_via_types=false",
        "--router.automatic_neckdown=false", "--router.layers.routable=true,false",
        "--router.max_passes=1", "--router.max_threads=1",
        "--router.ignore_net_classes="+",".join(ignored),
        "--router.enabled="+("false" if args.no_routing else "true"),
    ]
    if args.legacy_engine:
        options.append("--router.algorithm=freerouting-router-v19")
    command = [str(args.java), "-Xmx1g", "-XX:ActiveProcessorCount=2", "-jar", str(args.jar),
               *options, "--user_data_path="+str(out/"profile"),
               "--router.result_json="+str(out/"engine-result.json"),
               "-de", str(out/"pilot.dsn"), "-do", str(out/"result.ses")]
    version = subprocess.run([str(args.java), "-version"], capture_output=True, timeout=10, check=True)
    start = time.monotonic()
    try:
        process = subprocess.run(command, capture_output=True, timeout=60)
        status = "ENGINE_FINISHED" if process.returncode == 0 else "ENGINE_FAILED"
        stdout, stderr = process.stdout, process.stderr
        code = process.returncode
    except subprocess.TimeoutExpired as error:
        status, code = "ENGINE_TIMED_OUT", None
        stdout, stderr = error.stdout or b"", error.stderr or b""
    routing_seconds = time.monotonic() - start
    (out/"stdout.log").write_bytes(stdout)
    (out/"stderr.log").write_bytes(stderr)
    report = {
        "status": status, "source_pcb_sha256": PCB_SHA, "jar_sha256": JAR_SHA,
        "tool_sha256": sha(Path(__file__)), "kicad_version": pcb.GetBuildVersion(),
        "target_net": args.net, "no_routing_control": args.no_routing,
        "explicit_settings": True,
        "legacy_engine": args.legacy_engine,
        "java_version": (version.stdout+version.stderr).decode("utf-8", errors="replace").strip(),
        "routing_scope_qualification": "Requested restrictions; not qualified for production routing by this pilot.",
        "options": options, "external_deadline_seconds": 60,
        "export_seconds": export_seconds, "engine_seconds": routing_seconds,
        "engine_exit_code": code, "exchange_adjustments": adjustments,
        "raw_dsn_sha256": sha(out/"raw.dsn"), "pilot_dsn_sha256": sha(out/"pilot.dsn"),
        "source_modified": False, "proposal_only": True,
    }
    if code == 0 and (out/"result.ses").exists():
        before = time.monotonic()
        if not pcb.ImportSpecctraSES(board, str(out/"result.ses")):
            report["status"] = "SESSION_IMPORT_FAILED"
        else:
            new_parts, new_tracks = geometry(board, pcb)
            removed, added = old_tracks-new_tracks, new_tracks-old_tracks
            report.update(
                status="IMPORTED_PROPOSAL_REQUIRES_NATIVE_REVIEW",
                session_sha256=sha(out/"result.ses"),
                import_seconds=time.monotonic()-before,
                footprints_and_pads_identical=old_parts == new_parts,
                original_track_instances=sum(old_tracks.values()),
                imported_track_instances=sum(new_tracks.values()),
                exact_geometry_removed=sum(removed.values()), exact_geometry_added=sum(added.values()),
                removed_by_net=dict(Counter({net: sum(n for key,n in removed.items() if key[1] == net)
                                             for net in {k[1] for k in removed}})),
                added_by_net=dict(Counter({net: sum(n for key,n in added.items() if key[1] == net)
                                           for net in {k[1] for k in added}})),
                added_geometry=[{"geometry": key, "count": n} for key,n in added.items()],
            )
            if not pcb.SaveBoard(str(out/"imported.kicad_pcb"), board):
                raise RuntimeError("Could not save disposable imported board")
            shutil.copyfile(PACKAGE/"handbell.kicad_pro", out/"imported.kicad_pro")
            for name in ("fp-lib-table", "LICENSE.txt"):
                shutil.copyfile(PACKAGE/name, out/name)
            shutil.copytree(PACKAGE/"libraries", out/"libraries")
    elif code == 0:
        report["status"] = "NO_SESSION_OUTPUT"
    if sha(PACKAGE/"handbell.kicad_pcb") != PCB_SHA:
        raise RuntimeError("Source PCB changed during pilot")
    (out/"pilot-report.json").write_bytes((json.dumps(report,indent=2)+"\n").encode("utf-8"))
    print(json.dumps({k:v for k,v in report.items()
                      if k in ("status","engine_seconds","footprints_and_pads_identical",
                               "exact_geometry_removed","exact_geometry_added","added_by_net")}))
    return 0 if report["status"] == "IMPORTED_PROPOSAL_REQUIRES_NATIVE_REVIEW" else 2


if __name__ == "__main__":
    sys.exit(main())
