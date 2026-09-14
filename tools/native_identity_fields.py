# SPDX-License-Identifier: MIT
"""Shared metadata-only edits; historical hash-bound one-shot writers stay intact."""
import json

from apply_clock_definition_revision import prop_edits
from kicad_sexpr import apply_edits


def prepare_fields(text, tree, kind, specifications):
    """Return edited text and per-reference evidence without writing design files."""
    edits, details = [], {}
    for item in tree.children(kind):
        props = item.properties()
        ref = props.get("Reference")
        if ref not in specifications:
            continue
        if ref in details:
            raise ValueError("Duplicate selected reference: "+ref)
        spec = specifications[ref]
        if props["Value"] not in spec["expected_values"]:
            raise ValueError("Unexpected nominal value: "+ref)
        values = dict(spec["properties"])
        for key in ("MPN", "Manufacturer"):
            if props.get(key) and props[key] != values[key]:
                raise ValueError("Conflicting identity: "+ref+"/"+key)
        old_sheet = props.get("Datasheet", "")
        if old_sheet and old_sheet != values["Datasheet"]:
            if props.get("CircuitReference") not in (None, "", old_sheet):
                raise ValueError("Conflicting circuit reference: "+ref)
            values["CircuitReference"] = old_sheet
        if kind == "footprint":
            if item.atoms()[1] not in spec["expected_footprints"]:
                raise ValueError("Unexpected footprint: "+ref)
            xy, layer = "0 0", '(layer "F.Fab")'
        else:
            if props["Footprint"] not in spec["expected_footprints"]:
                raise ValueError("Unexpected schematic footprint: "+ref)
            xy, layer = " ".join(item.child("at").atoms()[1:3]), ""
        details[ref] = {"value": props["Value"], "previous_mpn": props.get("MPN", ""),
                        **values}
        edits += prop_edits(item, values)
        fields = "".join(
            f'\n(property {json.dumps(key)} {json.dumps(value)} (at {xy} 0) {layer} '
            '(hide yes) (effects (font (size 1 1))))'
            for key, value in values.items() if key not in props)
        if fields:
            start = text.rfind("\n", item.start, item.end-1)+1
            insertion = item.end-1
            if not text[start:insertion].strip():
                insertion, fields = start, fields.lstrip("\n")+"\n"
            edits.append((insertion, insertion, fields))
    if details.keys() != specifications.keys():
        raise ValueError("Selected reference inventory differs: "+kind)
    return apply_edits(text, edits), details


def apply_manifest_fields(manifest, specifications):
    seen = set()
    for component in manifest["components"]:
        ref = component["reference"]
        if ref not in specifications:
            continue
        if ref in seen:
            raise ValueError("Duplicate manifest reference: "+ref)
        seen.add(ref)
        spec = specifications[ref]
        if (component["value"] not in spec["expected_values"]
                or component["footprint"] not in spec["expected_footprints"]
                or component.get("mpn") not in ("", spec["properties"]["MPN"])):
            raise ValueError("Manifest identity/footprint mismatch: "+ref)
        component.update(mpn=spec["properties"]["MPN"],
                         manufacturer=spec["properties"]["Manufacturer"])
    if seen != specifications.keys():
        raise ValueError("Selected manifest inventory differs")
