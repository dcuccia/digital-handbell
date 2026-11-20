#!/usr/bin/env python3
"""Assemble firmware/build/CIRCUITPY: the exact tree to copy onto the board.

Steps: validate bells.json -> compile handbell/ to .mpy with the pinned
CircuitPython mpy-cross -> extract pinned Adafruit libraries from the bundle
-> generate sounds -> write build_info.json -> check the flash budget.
Idempotent; downloads are cached and hash-checked in firmware/.cache.
Writes firmware/build/reports/build.json. Exit code 2 means over budget.

    python firmware/scripts/build.py [--offline] [--no-mpy] [--no-sounds]
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402
import make_sounds  # noqa: E402

_common.add_src_to_path()
from handbell import __version__  # noqa: E402
from handbell.core import config as hb_config  # noqa: E402

KEEP_AS_PY = {"code.py"}


def validate_config():
    with open(_common.SRC / "bells.json", encoding="utf-8") as f:
        cfg = hb_config.parse(json.load(f))
    _common.log("bells.json OK: %d bells, %s, %d Hz" % (len(cfg.bells), cfg.select, cfg.audio["sample_rate"]))
    return cfg


def compile_mpy(mpy_cross, rel, out_dir):
    target = out_dir / (rel[:-3] + ".mpy")
    target.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [str(mpy_cross), "-o", str(target), rel],
        cwd=_common.SRC,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        _common.fail("mpy-cross failed for %s:\n%s%s" % (rel, result.stdout, result.stderr))
    return target


def copy_sources(out_dir, use_mpy, offline):
    mpy_cross = _common.mpy_cross(offline) if use_mpy else None
    count = 0
    for rel in _common.device_sources():
        src = _common.SRC / rel
        if use_mpy and rel.startswith("handbell/") and rel.endswith(".py"):
            compile_mpy(mpy_cross, rel, out_dir)
        else:
            dst = out_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
        count += 1
    return count


def extract_libraries(out_dir, offline):
    pins = _common.toolchain()["bundle"]
    bundle = _common.fetch(pins["url"], pins["sha256"], offline)
    lib_dir = out_dir / "lib"
    lib_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    with zipfile.ZipFile(bundle) as z:
        names = z.namelist()
        root = names[0].split("/", 1)[0]
        for lib in pins["libraries"]:
            prefix = "%s/lib/%s/" % (root, lib)
            single = "%s/lib/%s.mpy" % (root, lib)
            members = [n for n in names if n.startswith(prefix) and not n.endswith("/")]
            if single in names:
                members.append(single)
            if not members:
                _common.fail("library %s not found in bundle %s" % (lib, pins["tag"]))
            for m in members:
                rel = m[len(root) + len("/lib/"):]
                dst = lib_dir / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                with z.open(m) as src, open(dst, "wb") as out:
                    shutil.copyfileobj(src, out)
            copied.append(lib)
    return copied


def sounds_key(args):
    h = hashlib.sha256()
    for path in (
        _common.SRC / "bells.json",
        _common.SRC / "handbell" / "core" / "bell_model.py",
        Path(make_sounds.__file__),
    ):
        h.update(path.read_bytes())
    h.update(repr((args.rate, args.seconds, args.kbps, args.test_wav)).encode())
    user_sounds = _common.SRC / "sounds"
    if user_sounds.exists():
        for p in sorted(user_sounds.rglob("*")):
            if p.is_file():
                h.update(p.relative_to(_common.SRC).as_posix().encode())
    try:
        import lameenc

        h.update(str(getattr(lameenc, "__version__", "lameenc")).encode())
    except ImportError:
        pass
    return h.hexdigest()


def build_sounds(out_dir, args):
    assets = _common.BUILD / "assets"
    key = sounds_key(args)
    key_file = assets / ".key"
    if not (key_file.exists() and key_file.read_text() == key):
        if assets.exists():
            shutil.rmtree(assets)
        make_sounds.main(
            [
                "--out", str(assets),
                "--rate", str(args.rate),
                "--seconds", str(args.seconds),
                "--kbps", str(args.kbps),
                "--test-wav", args.test_wav,
            ]
        )
        key_file.write_text(key)
    else:
        _common.log("sounds unchanged; reusing %s" % assets)
    shutil.copytree(assets / "sounds", out_dir / "sounds", dirs_exist_ok=True)
    with open(assets / "sounds" / "provenance.json", encoding="utf-8") as f:
        return json.load(f)


def budget(out_dir):
    pins = _common.toolchain()["circuitpy"]
    cluster = pins["cluster_bytes"]
    files = []
    used = 0
    for path in sorted(out_dir.rglob("*")):
        if path.is_dir():
            used += cluster
            continue
        size = path.stat().st_size
        used += max(1, -(-size // cluster)) * cluster
        files.append({"path": path.relative_to(out_dir).as_posix(), "bytes": size, "sha256": _common.sha256_file(path)})
    limit = pins["capacity_bytes"] - pins["reserve_bytes"]
    return {
        "allocated_bytes": used,
        "limit_bytes": limit,
        "capacity_bytes": pins["capacity_bytes"],
        "reserve_bytes": pins["reserve_bytes"],
        "headroom_bytes": limit - used,
        "note": "Estimate: FAT clusters of %d bytes. Verify on hardware with bringup.info." % cluster,
    }, files


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--offline", action="store_true", help="use only cached downloads")
    ap.add_argument("--no-mpy", action="store_true", help="copy handbell/ as .py instead of compiling")
    ap.add_argument("--no-sounds", action="store_true", help="skip sound generation")
    ap.add_argument("--rate", type=int, default=22050)
    ap.add_argument("--seconds", type=float, default=4.0)
    ap.add_argument("--kbps", type=int, default=64)
    ap.add_argument("--test-wav", default="A5")
    ap.add_argument("--allow-over-budget", action="store_true")
    args = ap.parse_args(argv)

    cfg = validate_config()
    out_dir = _common.CIRCUITPY
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    n_src = copy_sources(out_dir, not args.no_mpy, args.offline)
    libs = extract_libraries(out_dir, args.offline)
    provenance = None if args.no_sounds else build_sounds(out_dir, args)
    tc = _common.toolchain()
    info = {
        "version": "%s+%s" % (__version__, _common.git_version()),
        "circuitpython": tc["circuitpython"]["version"],
        "bundle": tc["bundle"]["tag"],
        "mpy": not args.no_mpy,
        "sounds": not args.no_sounds,
    }
    with open(out_dir / "build_info.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(info, f, sort_keys=True)
        f.write("\n")

    space, files = budget(out_dir)
    report = {
        "status": "ok" if space["headroom_bytes"] >= 0 else "over_budget",
        "build_info": info,
        "bells": [{"id": b.id, "sound": b.sound} for b in cfg.bells],
        "sources": n_src,
        "libraries": libs,
        "space": space,
        "mp3_priming_ms": provenance["mp3_priming_ms"] if provenance else None,
        "files": files,
    }
    path = _common.write_report("build.json", report)
    _common.log(
        "CIRCUITPY at %s: %d files, %d of %d bytes allocated (%d headroom). Report: %s"
        % (out_dir, len(files), space["allocated_bytes"], space["limit_bytes"], space["headroom_bytes"], path)
    )
    if space["headroom_bytes"] < 0 and not args.allow_over_budget:
        _common.fail("over the CIRCUITPY budget by %d bytes" % -space["headroom_bytes"], code=2)
    return report


if __name__ == "__main__":
    main()
