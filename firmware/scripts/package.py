#!/usr/bin/env python3
"""Package a built CIRCUITPY tree as a reproducible release zip.

Contents of firmware/dist/digital-handbell-firmware-<version>.zip:

- ``CIRCUITPY/``  copy onto the board's CIRCUITPY drive
- ``uf2/``        the pinned CircuitPython UF2 for the board (MIT, unmodified)
- ``MANIFEST.json`` file hashes, toolchain pins and version
- ``INSTALL.txt``, ``LICENSE``

Entries are sorted with fixed timestamps (``SOURCE_DATE_EPOCH`` if set), so
identical inputs give an identical zip. A ``.sha256`` file is written beside it.

    python firmware/scripts/package.py [--build] [--offline] [--no-uf2]
"""

import argparse
import json
import os
import sys
import time
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402

INSTALL = """Digital handbell firmware {version}

Prototype firmware for owner testing. Follow the E09 bring-up gates before
powering a new board (current-limited supply first).

1. Install CircuitPython {cp} (once per board). A blank board appears as the
   RPI-RP2 drive; copy uf2/{uf2} onto it. To return to that drive later run
   `import microcontroller; microcontroller.on_next_reset(microcontroller.RunMode.UF2); microcontroller.reset()`
   in the REPL, or short the USBBOOT pad (TP3) while connecting USB.
2. Copy everything inside CIRCUITPY/ onto the CIRCUITPY drive. Keep a copy of
   your own bells.json first if you edited it. Eject the drive safely.
3. Open the serial console (115200 baud is ignored; any value works).
   Bring-up: `import bringup.info`, then the steps in bringup/__init__.py.
4. The instrument starts from code.py. Messages are HGP-shaped JSON lines.

Docs: https://github.com/dcuccia/digital-handbell/tree/main/firmware
"""


def zip_time():
    epoch = int(os.environ.get("SOURCE_DATE_EPOCH", "315532800"))
    return time.gmtime(max(epoch, 315532800))[:6]


def add_bytes(z, name, data, stamp):
    info = zipfile.ZipInfo(name, date_time=stamp)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    z.writestr(info, data)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--build", action="store_true", help="run build.py first")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--no-uf2", action="store_true", help="omit the CircuitPython UF2")
    ap.add_argument("--board", default="raspberry_pi_pico", help="UF2 key in toolchain.json")
    args = ap.parse_args(argv)

    if args.build:
        import build

        build.main(["--offline"] if args.offline else [])
    build_report = _common.REPORTS / "build.json"
    if not _common.CIRCUITPY.exists() or not build_report.exists():
        _common.fail("no build found; run python firmware/scripts/build.py first (or pass --build)")
    with open(build_report, encoding="utf-8") as f:
        built = json.load(f)
    if built.get("status") != "ok":
        _common.fail("build status is %r; refusing to package" % built.get("status"))
    if not built["build_info"].get("sounds", True):
        _common.fail("the build was made with --no-sounds and cannot start on a board; rebuild with sounds")

    tc = _common.toolchain()
    version = built["build_info"]["version"]
    stamp = zip_time()
    uf2_entry = tc["circuitpython"]["uf2"][args.board]
    uf2_name = uf2_entry["url"].rsplit("/", 1)[-1]
    _common.DIST.mkdir(parents=True, exist_ok=True)
    zip_path = _common.DIST / ("digital-handbell-firmware-%s.zip" % version)
    manifest = {
        "version": version,
        "circuitpython": tc["circuitpython"]["version"],
        "bundle": tc["bundle"],
        "uf2": None if args.no_uf2 else {"file": "uf2/" + uf2_name, "sha256": uf2_entry["sha256"], "url": uf2_entry["url"]},
        "space": built["space"],
        "files": built["files"],
    }
    with zipfile.ZipFile(zip_path, "w") as z:
        for path in sorted(p for p in _common.CIRCUITPY.rglob("*") if p.is_file()):
            rel = path.relative_to(_common.CIRCUITPY).as_posix()
            add_bytes(z, "CIRCUITPY/" + rel, path.read_bytes(), stamp)
        if not args.no_uf2:
            uf2 = _common.fetch(uf2_entry["url"], uf2_entry["sha256"], args.offline)
            add_bytes(z, "uf2/" + uf2_name, uf2.read_bytes(), stamp)
        add_bytes(
            z,
            "INSTALL.txt",
            INSTALL.format(version=version, cp=tc["circuitpython"]["version"], uf2=uf2_name).encode(),
            stamp,
        )
        add_bytes(z, "LICENSE", (_common.REPO / "LICENSE").read_bytes(), stamp)
        add_bytes(z, "MANIFEST.json", (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(), stamp)
    digest = _common.sha256_file(zip_path)
    (zip_path.parent / (zip_path.name + ".sha256")).write_text("%s  %s\n" % (digest, zip_path.name), encoding="utf-8")
    _common.write_report("package.json", {"zip": zip_path.name, "sha256": digest, "version": version})
    _common.log("packaged %s (%d bytes, sha256 %s)" % (zip_path, zip_path.stat().st_size, digest[:16]))
    return zip_path


if __name__ == "__main__":
    main()
