# SPDX-License-Identifier: MIT
"""Render native copper primitives; default to the clock detail, not a rule check."""
import argparse
import hashlib
import math
import os
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont
from route_clock_local import PACKAGE


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pcb", type=Path, default=PACKAGE / "handbell.kicad_pcb")
    parser.add_argument("--layer", choices=("F.Cu", "In1.Cu", "In2.Cu", "B.Cu"), default="F.Cu")
    parser.add_argument("--bounds", type=float, nargs=4, metavar=("XMIN", "YMIN", "XMAX", "YMAX"),
                        default=(89.5, 95.2, 99.5, 103.0))
    parser.add_argument("--highlight-net", action="append")
    args = parser.parse_args()
    xmin, ymin, xmax, ymax = args.bounds
    if not all(math.isfinite(v) for v in args.bounds) or xmin >= xmax or ymin >= ymax:
        parser.error("--bounds must be finite and ordered XMIN YMIN XMAX YMAX")
    folder = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin"
    dll_handle = os.add_dll_directory(str(folder))
    sys.path.insert(0, str(folder / "Lib" / "site-packages"))
    import pcbnew as pcb
    if pcb.GetBuildVersion() != "10.0.6":
        raise ValueError("KiCad 10.0.6 required")
    source_hash = hashlib.sha256(args.pcb.read_bytes()).hexdigest()
    board = pcb.LoadBoard(str(args.pcb))
    layer = {"F.Cu": pcb.F_Cu, "In1.Cu": pcb.In1_Cu,
             "In2.Cu": pcb.In2_Cu, "B.Cu": pcb.B_Cu}[args.layer]
    if layer not in board.GetEnabledLayers().Seq():
        parser.error(f"{args.layer} is not enabled on the supplied PCB")
    scale = 1200 / (xmax - xmin)
    drawing_height = math.ceil((ymax - ymin) * scale) + 4
    image = Image.new("RGB", (1200, drawing_height + 80), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(Path(os.environ["WINDIR"]) / "Fonts" / "arial.ttf"), 15)
    items = [pad for fp in board.GetFootprints() for pad in fp.Pads()] + list(board.GetTracks())
    highlighted = set(args.highlight_net) if args.highlight_net else {
        "Net-(IC1-XIN)", "Net-(IC1-XOUT)", "Net-(C3-Pad2)"}
    for item in items:
        if not item.IsOnLayer(layer):
            continue
        box = item.GetEffectiveShape(layer).BBox()
        x0, y0, x1, y1 = [pcb.ToMM(v) for v in
                          (box.GetLeft(), box.GetTop(), box.GetRight(), box.GetBottom())]
        if x1 < xmin or x0 > xmax or y1 < ymin or y0 > ymax:
            continue
        polygon = pcb.SHAPE_POLY_SET()
        item.TransformShapeToPolygon(polygon, layer, 0, pcb.FromMM(.005), pcb.ERROR_OUTSIDE)
        color = "#438a52" if item.GetNetname() == "GND" else (
            "#d05e4b" if item.GetNetname() in highlighted else "#cccccc")
        for index in range(polygon.OutlineCount()):
            line = polygon.COutline(index)
            draw.polygon([((pcb.ToMM(line.CPoint(j).x)-xmin)*scale,
                           (pcb.ToMM(line.CPoint(j).y)-ymin)*scale)
                          for j in range(line.PointCount())], fill=color, outline="black")
        if isinstance(item, pcb.PAD):
            x, y = [pcb.ToMM(v) for v in item.GetPosition()]
            draw.text(((x-xmin)*scale+3, (y-ymin)*scale+3),
                      item.GetParentFootprint().GetReference()+"."+item.GetNumber(),
                      font=font, fill="black")
    draw.rectangle((0, drawing_height, 1200, drawing_height + 80), fill="white")
    draw.text((12, drawing_height + 8),
              f"Native {args.layer} primitives; zone fills omitted. Red: highlighted / green: GND / grey: other nets.",
              font=font, fill="black")
    draw.text((12, drawing_height + 34), f"{args.pcb.name} / SHA256 {source_hash}",
              font=font, fill="black")
    draw.text((12, drawing_height + 60), "Rendering only, not functional, mechanical or manufacturing approval.",
              font=font, fill="black")
    if hashlib.sha256(args.pcb.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("PCB changed during rendering; output was not saved")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    dll_handle.close()


if __name__ == "__main__":
    main()
