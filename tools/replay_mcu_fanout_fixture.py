# SPDX-License-Identifier: MIT
"""Recreate the source-bound MCU fanout clipping fixture from its public report."""
import argparse
import hashlib
import json
from pathlib import Path

from kicad_sexpr import apply_edits, load


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Fixture output must be a new private file")
    report = json.loads(args.report.read_text(encoding="utf-8"))
    expected = report["source_bindings"]["pcb_sha256"]
    if sha(args.source) != expected:
        raise RuntimeError("Source PCB hash differs from report")

    text, root = load(args.source)
    segments = {node.value("uuid"): node for node in root.children("segment")}
    edits = []
    for row in report["clipping"]["removed_fragments"]:
        node = segments[row["parent_uuid"]]
        edits.append((node.start, node.end, ""))
    for row in report["clipping"]["clipped_parents"]:
        node = segments[row["parent_uuid"]]
        fragments = []
        for item in row["retained_exteriors"]:
            fragments.append(
                f'(segment (start {item["start"][0]:.6f} {item["start"][1]:.6f}) '
                f'(end {item["end"][0]:.6f} {item["end"][1]:.6f}) '
                f'(width {item["width_mm"]:.6f}) (layer "F.Cu") '
                f'(net "{item["net"]}") (uuid "{item["uuid"]}"))'
            )
        edits.append((node.start, node.end, "\n".join(fragments)))

    f_zone = next(
        zone for zone in root.children("zone")
        if zone.value("name") == "quote-native-F-GND-v1"
    )
    edits.extend((node.start, node.end, "")
                 for node in f_zone.children("filled_polygon"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        output.write(apply_edits(text, edits))
    print(json.dumps({"output_sha256": sha(args.output)}, indent=2))


if __name__ == "__main__":
    main()
