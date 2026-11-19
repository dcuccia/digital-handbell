#!/usr/bin/env python3
"""Publish a packaged firmware zip as a GitHub release (uses the gh CLI).

Requires a tag named ``firmware-v<version>`` where <version> equals
``handbell.__version__``, so a release can only come from a deliberate
version bump. Idempotent: re-running uploads with --clobber to the same
release. Releases are created as prereleases while the version contains a
pre-release marker such as "-dev" or "-rc".

    python firmware/scripts/publish.py --tag firmware-v0.1.0 [--dry-run]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402

_common.add_src_to_path()
from handbell import __version__  # noqa: E402


def gh(args, check=True):
    return subprocess.run(["gh"] + args, cwd=_common.REPO, capture_output=True, text=True, check=check)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--tag", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    expected = "firmware-v" + __version__
    if args.tag != expected:
        _common.fail("tag %s does not match handbell.__version__ (expected %s)" % (args.tag, expected))
    report = _common.REPORTS / "package.json"
    if not report.exists():
        _common.fail("no package found; run python firmware/scripts/package.py first")
    with open(report, encoding="utf-8") as f:
        pkg = json.load(f)
    zip_path = _common.DIST / pkg["zip"]
    sha_path = _common.DIST / (pkg["zip"] + ".sha256")
    assets = [str(zip_path), str(sha_path)]
    prerelease = "-" in __version__
    notes = (
        "Digital handbell firmware %s for CircuitPython %s.\n\n"
        "Prototype firmware for owner testing; not a released kit. See INSTALL.txt in the zip "
        "and docs/firmware/bring-up.md. SHA-256: %s"
        % (__version__, _common.toolchain()["circuitpython"]["version"], pkg["sha256"])
    )
    if args.dry_run:
        _common.log("would publish %s to release %s (prerelease=%s)" % (", ".join(assets), args.tag, prerelease))
        return 0
    exists = gh(["release", "view", args.tag], check=False).returncode == 0
    if exists:
        gh(["release", "upload", args.tag, "--clobber"] + assets)
    else:
        cmd = ["release", "create", args.tag, "--title", "Firmware " + __version__, "--notes", notes, "--verify-tag"]
        if prerelease:
            cmd.append("--prerelease")
        gh(cmd + assets)
    _common.log("published %s" % args.tag)
    return 0


if __name__ == "__main__":
    sys.exit(main())
