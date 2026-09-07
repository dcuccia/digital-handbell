# SPDX-License-Identifier: MIT
"""Read KiCad S-expressions without discarding source spans."""
from dataclasses import dataclass
import json
from pathlib import Path
import re

TOKEN = re.compile(r'\s+|"(?:\\.|[^"\\])*"|[()]|[^\s()]+')


@dataclass
class Atom:
    value: str
    start: int
    end: int


@dataclass
class Node:
    items: list
    start: int
    end: int

    @property
    def head(self):
        return self.items[0].value if self.items and isinstance(self.items[0], Atom) else None

    def children(self, head=None):
        return [item for item in self.items if isinstance(item, Node)
                and (head is None or item.head == head)]

    def child(self, head):
        values = self.children(head)
        if len(values) > 1:
            raise ValueError(f"Expected at most one {head} in {self.head}")
        return values[0] if values else None

    def atoms(self):
        return [item.value for item in self.items if isinstance(item, Atom)]

    def value(self, head):
        child = self.child(head)
        return child.atoms()[1] if child is not None else None

    def properties(self):
        return {child.atoms()[1]: child.atoms()[2] for child in self.children("property")}

    def walk(self):
        yield self
        for child in self.children():
            yield from child.walk()


def loads(text):
    tokens = [match for match in TOKEN.finditer(text) if not match.group().isspace()]
    cursor = 0

    def read():
        nonlocal cursor
        if cursor >= len(tokens):
            raise ValueError("Unexpected end of S-expression")
        token = tokens[cursor]
        cursor += 1
        raw = token.group()
        if raw == "(":
            items = []
            while cursor < len(tokens) and tokens[cursor].group() != ")":
                items.append(read())
            if cursor == len(tokens):
                raise ValueError("Unclosed S-expression")
            end = tokens[cursor].end()
            cursor += 1
            return Node(items, token.start(), end)
        if raw == ")":
            raise ValueError("Unexpected closing parenthesis")
        return Atom(json.loads(raw) if raw.startswith('"') else raw, token.start(), token.end())

    root = read()
    if cursor != len(tokens) or not isinstance(root, Node):
        raise ValueError("Expected exactly one root expression")
    return root


def load(path):
    text = Path(path).read_text(encoding="utf-8-sig")
    return text, loads(text)


def pcb_net_name(name):
    """Escape pin-name slashes in flat auto-nets, not hierarchical label paths."""
    if name and name.startswith(("unconnected-", "Net-")):
        return name.replace("/", "{slash}")
    return name


def apply_edits(text, edits):
    """Apply nonoverlapping source-span edits, then reject malformed output."""
    previous = len(text) + 1
    for start, end, replacement in sorted(edits, key=lambda edit: (edit[0], edit[1]), reverse=True):
        if not (0 <= start <= end <= len(text)) or end > previous:
            raise ValueError("Invalid or overlapping source edits")
        text = text[:start] + replacement + text[end:]
        previous = start
    loads(text)
    return text
