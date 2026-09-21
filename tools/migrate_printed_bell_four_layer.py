# SPDX-License-Identifier: MIT
"""Create the logical four-copper-layer printed-bell baseline without geometry edits."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

from kicad_sexpr import apply_edits, loads

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "hardware/handbell/iterations/printed-bell-clock-draft"
OUTPUT = ROOT / "hardware/handbell/iterations/printed-bell-four-layer"
KICAD_BIN = Path(os.environ.get(
    "KICAD10_BIN",
    Path(os.environ["LOCALAPPDATA"]) / "Programs/KiCad/10.0/bin"))
EXPECTED_PCB = "a83cc417c96b05dd15c187e648b9fd2a35ba857c3a66f7d13aaaa42ae3bd9fff"
EXPECTED_MANIFEST = "2b9ea13a6ae85d0f8d2ae09c74161e3122349e4ecb56c9aa760823cd88d9bb55"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit(f"Refusing existing target: {OUTPUT}")
    if sha(SOURCE / "handbell.kicad_pcb") != EXPECTED_PCB:
        raise SystemExit("Source PCB hash mismatch")
    if sha(SOURCE / "placement-manifest.json") != EXPECTED_MANIFEST:
        raise SystemExit("Source manifest hash mismatch")

    OUTPUT.mkdir(parents=True)
    (OUTPUT / "reports").mkdir()
    for name in (
        "handbell.kicad_pcb", "handbell.kicad_sch", "handbell.kicad_pro",
        "fp-lib-table", "sym-lib-table", "Handbell.kicad_sym", "T8.kicad_sym",
        "Clock.kicad_sym", "battery-contact-interface.json", "LICENSE.txt",
    ):
        shutil.copy2(SOURCE / name, OUTPUT / name)
    shutil.copytree(SOURCE / "libraries", OUTPUT / "libraries", copy_function=shutil.copy2)

    dll_handle = os.add_dll_directory(str(KICAD_BIN))
    sys.path.insert(0, str(KICAD_BIN / "Lib/site-packages"))
    import pcbnew as pcb
    if pcb.GetBuildVersion() != "10.0.6":
        raise SystemExit(f"Expected KiCad 10.0.6, got {pcb.GetBuildVersion()}")

    board_path = OUTPUT / "handbell.kicad_pcb"
    source_text = board_path.read_bytes().decode("utf-8-sig")
    board = pcb.LoadBoard(str(board_path))
    board.SetCopperLayerCount(4)
    board.GetDesignSettings().SetCopperLayerCount(4)
    pcb.SaveBoard(str(board_path), board)
    native_text = board_path.read_bytes().decode("utf-8-sig")
    source_layers = loads(source_text).child("layers")
    native_layers = loads(native_text).child("layers")
    board_path.write_bytes(apply_edits(
        source_text,
        [(source_layers.start, source_layers.end,
          native_text[native_layers.start:native_layers.end])]).encode("utf-8"))
    reloaded = pcb.LoadBoard(str(board_path))
    actual = [
        reloaded.GetLayerName(layer)
        for layer in reloaded.GetEnabledLayers().Seq()
        if pcb.IsCopperLayer(layer)
    ]
    if set(actual) != {"F.Cu", "In1.Cu", "In2.Cu", "B.Cu"} or len(actual) != 4:
        raise SystemExit(f"Unexpected enabled copper layers: {actual}")
    manifest_path = OUTPUT / "placement-manifest.json"
    manifest = json.loads((SOURCE / "placement-manifest.json").read_text(encoding="utf-8-sig"))
    manifest["status"] = "LOGICAL_FOUR_LAYER_PARTIAL_MIGRATION_BASELINE"
    manifest["generated_pcb_sha256"] = sha(board_path)
    manifest["source_two_layer_pcb_sha256"] = EXPECTED_PCB
    manifest["current_stage_report"] = "reports/four-layer-baseline.json"
    manifest["logical_copper_layers"] = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]
    manifest["physical_stackup_status"] = "pending; nominal total board thickness remains 1.6 mm"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "output": str(OUTPUT.relative_to(ROOT)),
        "pcb_sha256": sha(board_path),
        "manifest_sha256": sha(manifest_path),
        "enabled_copper_layers": actual,
    }, indent=2))


if __name__ == "__main__":
    main()
