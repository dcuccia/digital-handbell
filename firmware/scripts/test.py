#!/usr/bin/env python3
"""Run the firmware tests and the CircuitPython compile check.

1. pytest on firmware/tests (CPython: core logic, detectors, controls,
   instrument behavior, config, scripts).
2. Compile every device .py with the pinned CircuitPython mpy-cross, which
   catches syntax CircuitPython does not accept.

Writes firmware/build/reports/test.json and junit.xml.

    python firmware/scripts/test.py [--offline] [--no-compile] [-- extra pytest args]
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402


def run_pytest(extra):
    _common.REPORTS.mkdir(parents=True, exist_ok=True)
    junit = _common.REPORTS / "junit.xml"
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(_common.FIRMWARE / "tests"),
        "-q",
        "-p",
        "no:cacheprovider",
        "--junitxml",
        str(junit),
    ] + list(extra)
    _common.log("running " + " ".join(cmd[2:4]) + " ...")
    return subprocess.run(cmd, cwd=_common.FIRMWARE).returncode


def compile_check(offline):
    mpy_cross = _common.mpy_cross(offline)
    failures = []
    count = 0
    with tempfile.TemporaryDirectory() as tmp:
        for rel in _common.device_sources():
            if not rel.endswith(".py"):
                continue
            out = Path(tmp) / (rel.replace("/", "_") + ".mpy")
            r = subprocess.run([str(mpy_cross), "-o", str(out), rel], cwd=_common.SRC, capture_output=True, text=True)
            count += 1
            if r.returncode != 0:
                failures.append({"file": rel, "error": (r.stdout + r.stderr).strip()})
    return count, failures


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--no-compile", action="store_true", help="skip the mpy-cross compile check")
    args, extra = ap.parse_known_args(argv)
    if extra and extra[0] == "--":
        extra = extra[1:]

    try:
        import pytest  # noqa: F401
    except ImportError:
        _common.fail("pytest is missing: python firmware/scripts/setup_dev.py")

    code = run_pytest(extra)
    report = {"pytest_exit_code": code}
    if not args.no_compile:
        count, failures = compile_check(args.offline)
        report["compiled"] = count
        report["compile_failures"] = failures
        for f in failures:
            print("mpy-cross: %s\n%s" % (f["file"], f["error"]), file=sys.stderr)
        _common.log("mpy-cross compiled %d device files, %d failures" % (count, len(failures)))
    ok = code == 0 and not report.get("compile_failures")
    report["status"] = "ok" if ok else "failed"
    _common.write_report("test.json", report)
    if not ok:
        _common.fail("tests failed")
    _common.log("tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
