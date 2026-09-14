# SPDX-License-Identifier: MIT
"""Retain native local geometry when deriving a library from a board instance."""
import json

from apply_clock_definition_revision import prop_edits
from kicad_sexpr import apply_edits, loads


def library_from_instance(text, footprint, name):
    module = text[footprint.start:footprint.end]
    node = loads(module)
    edits = [(node.items[1].start, node.items[1].end, json.dumps(name))]
    edits += prop_edits(node, {"Reference": "REF**"})
    edits += [(n.start, n.end, "") for n in node.children() if n.head in ("at", "uuid", "path")]
    for pad in node.children("pad"):
        edits += [(n.start, n.end, "") for n in pad.children()
                  if n.head in ("net", "pintype", "pinfunction")]
    return apply_edits(module, edits)
