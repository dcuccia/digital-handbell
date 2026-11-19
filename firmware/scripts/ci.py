#!/usr/bin/env python3
"""Run the whole firmware pipeline the way CI does: setup -> test -> build -> package.

CI workflows call only this script, so a local run reproduces CI exactly.

    python firmware/scripts/ci.py [--offline] [--skip-setup]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--skip-setup", action="store_true")
    args = ap.parse_args(argv)
    offline = ["--offline"] if args.offline else []

    if not args.skip_setup:
        import setup_dev

        setup_dev.main([])
    import build
    import package
    import test

    _common.log("== test ==")
    test.main(offline)
    _common.log("== build ==")
    build.main(offline)
    _common.log("== package ==")
    package.main(offline)
    _common.log("ci pipeline passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
