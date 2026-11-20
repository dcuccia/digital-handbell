#!/usr/bin/env python3
"""Copy firmware/build/CIRCUITPY onto a connected CIRCUITPY drive.

Only changed files are written; code.py is written last so CircuitPython
reloads once. Files the build manages (handbell/, bringup/, sounds/, managed
lib/ packages) that no longer exist in the build are removed. Other files on
the drive (settings.toml, your notes) are never touched. An existing
bells.json on the device is kept unless --config is given, because it may hold
your edits.

    python firmware/scripts/deploy.py [--drive E:\\] [--dry-run] [--config]
"""

import argparse
import json
import os
import shutil
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402

MANAGED_DIRS = ("handbell", "bringup", "sounds")
LAST = ("code.py",)


def find_drive():
    candidates = []
    if os.name == "nt":
        import ctypes

        for letter in string.ascii_uppercase:
            root = "%s:\\" % letter
            if not os.path.exists(root):
                continue
            name = ctypes.create_unicode_buffer(261)
            ok = ctypes.windll.kernel32.GetVolumeInformationW(root, name, 261, None, None, None, None, 0)
            if ok and name.value == "CIRCUITPY":
                candidates.append(Path(root))
    else:
        user = os.environ.get("USER", "")
        for base in ("/Volumes/CIRCUITPY", "/media/%s/CIRCUITPY" % user, "/run/media/%s/CIRCUITPY" % user, "/media/CIRCUITPY"):
            if os.path.isdir(base):
                candidates.append(Path(base))
    if not candidates:
        _common.fail("no CIRCUITPY drive found; connect the board or pass --drive")
    if len(candidates) > 1:
        _common.fail("several CIRCUITPY drives found (%s); pass --drive" % ", ".join(map(str, candidates)))
    return candidates[0]


def same(a, b):
    return b.exists() and a.stat().st_size == b.stat().st_size and a.read_bytes() == b.read_bytes()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--drive", help="CIRCUITPY mount point or drive root")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--config", action="store_true", help="overwrite bells.json on the device")
    args = ap.parse_args(argv)

    src_root = _common.CIRCUITPY
    if not src_root.exists():
        _common.fail("no build found; run python firmware/scripts/build.py first")
    drive = Path(args.drive) if args.drive else find_drive()
    if not (drive / "boot_out.txt").exists():
        _common.fail("%s does not look like a CIRCUITPY drive (no boot_out.txt)" % drive)

    managed_libs = _common.toolchain()["bundle"]["libraries"]
    managed_dirs = list(MANAGED_DIRS)
    try:
        with open(src_root / "build_info.json", encoding="utf-8") as f:
            build_info = json.load(f)
    except (OSError, ValueError):
        build_info = {}
    if build_info.get("sounds") is False:
        # A code-only build (--no-sounds) must not wipe the sounds on the device.
        managed_dirs.remove("sounds")
        _common.log("build has no sounds; leaving the device's sounds/ untouched")
    files = sorted(p.relative_to(src_root).as_posix() for p in src_root.rglob("*") if p.is_file())
    ordered = [f for f in files if f not in LAST] + [f for f in LAST if f in files]
    written = skipped = 0
    for rel in ordered:
        src = src_root / rel
        dst = drive / rel
        if rel == "bells.json" and dst.exists() and not args.config:
            if not same(src, dst):
                _common.log("keeping the device's bells.json (differs from build; use --config to overwrite)")
            continue
        if same(src, dst):
            skipped += 1
            continue
        _common.log("%s %s" % ("would write" if args.dry_run else "write", rel))
        if not args.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
        written += 1

    wanted = set(files)
    removed = 0
    roots = managed_dirs + ["lib/" + lib for lib in managed_libs]
    for root in roots:
        base = drive / root
        if not base.exists():
            continue
        for path in sorted(base.rglob("*"), reverse=True):
            rel = path.relative_to(drive).as_posix()
            if path.is_file() and rel not in wanted:
                _common.log("%s %s" % ("would remove" if args.dry_run else "remove", rel))
                if not args.dry_run:
                    path.unlink()
                removed += 1
            elif path.is_dir() and not args.dry_run and not any(path.iterdir()):
                path.rmdir()
    if hasattr(os, "sync") and not args.dry_run:
        os.sync()
    _common.log("%s: %d written, %d unchanged, %d removed" % (drive, written, skipped, removed))
    if written and not args.dry_run:
        _common.log("eject the drive before unplugging so the filesystem is not corrupted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
