"""Shared helpers for firmware scripts (paths, pinned downloads, reports).

Standard library only, so every script runs before dev dependencies exist.
"""

import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

FIRMWARE = Path(__file__).resolve().parents[1]
REPO = FIRMWARE.parent
SRC = FIRMWARE / "src"
BUILD = FIRMWARE / "build"
CIRCUITPY = BUILD / "CIRCUITPY"
REPORTS = BUILD / "reports"
CACHE = FIRMWARE / ".cache"
DIST = FIRMWARE / "dist"
TOOLCHAIN = FIRMWARE / "toolchain.json"

# Files under src/ that never go to the device.
HOST_ONLY = {"handbell/platforms/desktop.py"}


def log(msg):
    print("[firmware] " + msg, flush=True)


def fail(msg, code=1):
    print("[firmware] ERROR: " + msg, file=sys.stderr, flush=True)
    sys.exit(code)


def toolchain():
    with open(TOOLCHAIN, encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url, sha256, offline=False):
    """Download ``url`` into the cache once and verify its SHA-256."""
    CACHE.mkdir(parents=True, exist_ok=True)
    target = CACHE / url.rsplit("/", 1)[-1]
    if target.exists() and sha256_file(target) == sha256:
        return target
    if offline:
        fail("%s is not cached and --offline was given" % target.name)
    log("downloading %s" % url)
    fd, tmp = tempfile.mkstemp(dir=CACHE, suffix=".part")
    os.close(fd)
    try:
        for attempt in range(3):
            try:
                with urllib.request.urlopen(url, timeout=120) as resp, open(tmp, "wb") as out:
                    shutil.copyfileobj(resp, out)
                break
            except OSError as e:
                if attempt == 2:
                    raise
                log("retrying after %s" % e)
                time.sleep(2 * (attempt + 1))
        got = sha256_file(tmp)
        if got != sha256:
            fail("SHA-256 mismatch for %s: got %s, pinned %s" % (url, got, sha256))
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return target


def host_key():
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "windows":
        return "windows-amd64"
    if system == "linux":
        return "linux-aarch64" if machine in ("aarch64", "arm64") else "linux-amd64"
    if system == "darwin":
        return "macos-arm64"
    fail("no pinned mpy-cross for %s/%s" % (system, machine))


def mpy_cross(offline=False):
    entry = toolchain()["mpy_cross"][host_key()]
    path = fetch(entry["url"], entry["sha256"], offline)
    if os.name != "nt":
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def git_version():
    try:
        out = subprocess.run(
            ["git", "describe", "--always", "--dirty", "--tags"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def write_report(name, data):
    REPORTS.mkdir(parents=True, exist_ok=True)
    path = REPORTS / name
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
    return path


def device_sources():
    """Relative POSIX paths of every file under src/ destined for the device."""
    out = []
    for path in sorted(SRC.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            rel = path.relative_to(SRC).as_posix()
            if rel not in HOST_ONLY:
                out.append(rel)
    return out


def add_src_to_path():
    # Append so src/code.py cannot shadow the stdlib ``code`` module.
    if str(SRC) not in sys.path:
        sys.path.append(str(SRC))
