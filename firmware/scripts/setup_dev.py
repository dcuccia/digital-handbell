#!/usr/bin/env python3
"""Install the CPython tools the firmware scripts need (idempotent).

Skips installation when every requirement is already importable.

    python firmware/scripts/setup_dev.py [--force]
"""

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402

MODULES = {"pytest": "pytest", "lameenc": "lameenc", "serial": "pyserial"}


def missing():
    return [pkg for mod, pkg in MODULES.items() if importlib.util.find_spec(mod) is None]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--force", action="store_true", help="reinstall even if present")
    args = ap.parse_args(argv)
    need = missing()
    if not need and not args.force:
        _common.log("dev requirements already installed")
        return 0
    req = _common.FIRMWARE / "requirements-dev.txt"
    _common.log("installing %s" % (", ".join(need) if need else "requirements (forced)"))
    result = subprocess.run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-r", str(req)])
    if result.returncode != 0:
        _common.fail("pip install failed")
    still = missing()
    if still:
        _common.fail("still missing after install: %s" % ", ".join(still))
    return 0


if __name__ == "__main__":
    sys.exit(main())
