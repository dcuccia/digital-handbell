# SPDX-License-Identifier: MIT
"""Render a front-copper clock detail from native KiCad shapes; not a rule check."""
import argparse
import os
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont
from route_clock_local import PACKAGE


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    folder = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin"
    dll_handle = os.add_dll_directory(str(folder))
    sys.path.insert(0, str(folder / "Lib" / "site-packages"))
    import pcbnew as pcb
    if pcb.GetBuildVersion() != "10.0.6":
        raise ValueError("KiCad 10.0.6 required")
    board = pcb.LoadBoard(str(PACKAGE / "handbell.kicad_pcb"))
    image = Image.new("RGB", (1200, 1020), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(Path(os.environ["WINDIR"]) / "Fonts" / "arial.ttf"), 15)
    items = [pad for fp in board.GetFootprints() for pad in fp.Pads()] + list(board.GetTracks())
    clock = {"Net-(IC1-XIN)", "Net-(IC1-XOUT)", "Net-(C3-Pad2)"}
    for item in items:
        if not item.IsOnLayer(pcb.F_Cu):
            continue
        box = item.GetEffectiveShape(pcb.F_Cu).BBox()
        x0, y0, x1, y1 = [pcb.ToMM(v) for v in
                          (box.GetLeft(), box.GetTop(), box.GetRight(), box.GetBottom())]
        if x1 < 89.5 or x0 > 99.5 or y1 < 95.2 or y0 > 103:
            continue
        polygon = pcb.SHAPE_POLY_SET()
        item.TransformShapeToPolygon(polygon, pcb.F_Cu, 0, pcb.FromMM(.005), pcb.ERROR_OUTSIDE)
        color = "#438a52" if item.GetNetname() == "GND" else (
            "#d05e4b" if item.GetNetname() in clock else "#cccccc")
        for index in range(polygon.OutlineCount()):
            line = polygon.COutline(index)
            draw.polygon([((pcb.ToMM(line.CPoint(j).x)-89.5)*120,
                           (pcb.ToMM(line.CPoint(j).y)-95.2)*120)
                          for j in range(line.PointCount())], fill=color, outline="black")
        if isinstance(item, pcb.PAD):
            x, y = [pcb.ToMM(v) for v in item.GetPosition()]
            draw.text(((x-89.5)*120+3, (y-95.2)*120+3),
                      item.GetParentFootprint().GetReference()+"."+item.GetNumber(),
                      font=font, fill="black")
    draw.rectangle((0, 940, 1200, 1020), fill="white")
    draw.text((12, 948), "Native F.Cu primitives; unfilled zones. Red: clock / green: GND / grey: other nets.",
              font=font, fill="black")
    draw.text((12, 974), "Rendering only, not functional, mechanical or manufacturing approval.",
              font=font, fill="black")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    dll_handle.close()


if __name__ == "__main__":
    main()
