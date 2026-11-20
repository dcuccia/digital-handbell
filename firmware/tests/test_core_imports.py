"""Guard the architecture seams with static checks."""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
CORE = SRC / "handbell" / "core"
CIRCUITPYTHON_ONLY = {
    "board", "busio", "digitalio", "audiobusio", "audiocore", "audiomixer", "audiomp3",
    "synthio", "keypad", "microcontroller", "supervisor", "adafruit_lsm6ds", "adafruit_bus_device",
}
UNSUPPORTED_ON_CIRCUITPYTHON = {"typing", "dataclasses", "enum", "abc", "pathlib", "functools", "itertools"}


def imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            yield node.module or ""


def device_files():
    for path in SRC.rglob("*.py"):
        if path.name != "desktop.py":
            yield path


def test_core_imports_only_math_and_core():
    for path in CORE.glob("*.py"):
        for name in imports(path):
            assert name == "math" or name.startswith("handbell.core"), "%s imports %s" % (path.name, name)


def test_core_and_ports_never_touch_hardware_modules():
    for path in list(CORE.glob("*.py")) + [SRC / "handbell" / "ports.py"]:
        for name in imports(path):
            assert name.split(".")[0] not in CIRCUITPYTHON_ONLY, "%s imports %s" % (path.name, name)


def test_device_code_avoids_cpython_only_modules():
    for path in device_files():
        for name in imports(path):
            assert name.split(".")[0] not in UNSUPPORTED_ON_CIRCUITPYTHON, "%s imports %s" % (path, name)


def test_no_max_default_keyword_in_device_code():
    for path in device_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) in ("max", "min"):
                assert not node.keywords, "%s uses %s(..., keyword=) unsupported on CircuitPython" % (path, node.func.id)
