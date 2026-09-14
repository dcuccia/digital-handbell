# SPDX-License-Identifier: MIT
"""Refill the existing F/GND plan into a new file; never approve or overwrite it."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile

from kicad_sexpr import apply_edits, load


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if output.exists() or source == output:
        raise ValueError("Output must be a new working file")
    if source.with_suffix(".kicad_dru").exists():
        raise ValueError("Custom rules need explicit integration before this refill")
    project = json.loads(source.with_suffix(".kicad_pro").read_text(encoding="utf-8"))
    if os.name == "nt":
        native = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin"
        dll_handle = os.add_dll_directory(str(native))
        sys.path.insert(0, str(native / "Lib" / "site-packages"))
    import pcbnew as pcb

    if pcb.GetBuildVersion() != "10.0.6":
        raise ValueError("This refill recipe was exercised with KiCad 10.0.6")
    board = pcb.LoadBoard(str(source))
    zones = [z for z in board.Zones() if not z.GetIsRuleArea()]
    if (len(zones) != 1 or zones[0].GetNetname() != "GND"
            or list(zones[0].GetLayerSet().Seq()) != [pcb.F_Cu]):
        raise ValueError("Expected exactly the existing F/GND copper zone")
    zone = zones[0]
    if (zone.GetMinThickness() != pcb.FromMM(.25)
            or zone.GetPadConnection() != pcb.ZONE_CONNECTION_FULL
            or zone.GetIslandRemovalMode() != pcb.ISLAND_REMOVAL_MODE_ALWAYS):
        raise ValueError("Unexpected ground-plan settings; review rather than replace")
    rules = project["board"]["design_settings"]["rules"]
    clearances = [.2, rules["min_clearance"]]
    clearances.extend(c["clearance"] for c in project["net_settings"]["classes"])
    values = {
        "m_MinClearance": max(clearances),
        "m_CopperEdgeClearance": max(.25, rules["min_copper_edge_clearance"]),
        "m_HoleClearance": max(.25, rules["min_hole_clearance"]),
        "m_HoleToHoleMin": max(.25, rules["min_hole_to_hole"]),
        "m_MaxError": min(.001, rules["max_error"]),
    }
    if not all(math.isfinite(v) and v > 0 for v in [*clearances, *values.values()]):
        raise ValueError("Invalid project geometry limits")
    settings = board.GetDesignSettings()
    for name, value in values.items():
        setattr(settings, name, pcb.FromMM(value))
    board.BuildConnectivity()
    if not pcb.ZONE_FILLER(board).Fill(board.Zones()):
        raise RuntimeError("Native fill did not complete")
    with tempfile.TemporaryDirectory(prefix="handbell-fill-") as directory:
        staged = Path(directory) / "filled.kicad_pcb"
        if not pcb.SaveBoard(str(staged), board, True):
            raise RuntimeError("Native filled board could not be serialized")
        filled_text, filled = load(staged)
    text, original = load(source)
    by_uuid = {z.value("uuid"): z for z in filled.children("zone")}
    edits = []
    for original_zone in original.children("zone"):
        if original_zone.child("keepout") is not None:
            continue
        polygons = by_uuid[original_zone.value("uuid")].children("filled_polygon")
        if not polygons or any(p.value("layer") != "F.Cu" for p in polygons):
            raise ValueError("Missing or non-front filled copper")
        edits.extend((p.start, p.end, "") for p in original_zone.children("filled_polygon"))
        addition = "\n".join(filled_text[p.start:p.end] for p in polygons) + "\n"
        position = text.rfind("\n", original_zone.start, original_zone.end - 1) + 1
        if text[position:original_zone.end - 1].strip():
            position, addition = original_zone.end - 1, "\n" + addition
        edits.append((position, position, addition))
    # Keep source pad angles, declarations and all non-fill text out of native reserialization.
    output.write_bytes(apply_edits(text, edits).encode("utf-8"))
    print(json.dumps({
        "status": "WORKING_COPY_REQUIRES_CONNECTIVITY_DRC_AND_PROTECTION_REVIEW",
        "native_version": pcb.GetBuildVersion(),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "in_memory_settings_mm": values,
        "project_file_modified": False,
    }, indent=2))


if __name__ == "__main__":
    main()
