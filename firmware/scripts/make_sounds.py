#!/usr/bin/env python3
"""Generate the device's bell sounds from the uncompressed masters.

Each device sound is rendered from its master ``firmware/sounds/<NOTE>.wav``
(16-bit mono, tracked with Git LFS) when one exists, otherwise synthesized
from the modal model in ``handbell.core.bell_model``. Deterministic: the same
inputs produce the same WAV bytes (MP3 bytes depend on the pinned LAME build
in ``lameenc``). The generated sounds are original and released under the
project's MIT license (see ATTRIBUTION.md).

    python firmware/scripts/make_sounds.py --out firmware/build/assets
    python firmware/scripts/make_sounds.py --write-masters   # regenerate masters
"""

import argparse
import json
import math
import struct
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402

_common.add_src_to_path()
from handbell.core import bell_model, pitch  # noqa: E402
from handbell.core import config as hb_config  # noqa: E402

PEAK = 0.89  # about -1 dBFS for a full-level strike
FADE_SECONDS = 0.25
# LAME (encoder) + standard decoder priming, measured with dr_mp3 on a 22.05 kHz
# 64 kbit/s file: first audible sample at 1106 samples (50.2 ms).
MP3_PRIMING_SAMPLES = 1105
MASTERS = _common.FIRMWARE / "sounds"
# The sound library kept as masters; bells.json chooses which reach the device.
LIBRARY = ("C5", "D5", "E5", "F5", "G5", "A5", "B5", "C6")
LFS_POINTER = b"version https://git-lfs"


def synthesize(midi, sample_rate, seconds):
    f0 = pitch.midi_to_hz(midi)
    partials = bell_model.audible_partials(f0, sample_rate)
    n = int(seconds * sample_rate)
    attack = max(1, int(bell_model.ATTACK_SECONDS * sample_rate))
    fade = int(FADE_SECONDS * sample_rate)
    two_pi = 2.0 * math.pi
    data = bytearray()
    for i in range(n):
        t = i / sample_rate
        v = 0.0
        for f, amp, decay in partials:
            v += amp * math.exp(-t / decay) * math.sin(two_pi * f * t)
        if i < attack:
            v *= 0.5 - 0.5 * math.cos(math.pi * i / attack)
        if i >= n - fade:
            v *= 0.5 + 0.5 * math.cos(math.pi * (i - (n - fade)) / fade)
        data += struct.pack("<h", int(max(-1.0, min(1.0, v * PEAK)) * 32767))
    return bytes(data)


def write_wav(path, pcm, sample_rate):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm)


def master_path(midi, masters=MASTERS):
    return Path(masters) / ("%s.wav" % pitch.midi_to_name(midi))


def read_master(path, sample_rate):
    """PCM bytes of a master, which must be mono 16-bit at ``sample_rate``."""
    with open(path, "rb") as f:
        if f.read(len(LFS_POINTER)) == LFS_POINTER:
            _common.fail("%s is a Git LFS pointer; run: git lfs pull" % path)
    with wave.open(str(path), "rb") as w:
        fmt = (w.getnchannels(), w.getsampwidth(), w.getframerate())
        if fmt != (1, 2, sample_rate):
            _common.fail("%s must be mono 16-bit at %d Hz, got %r" % (path, sample_rate, fmt))
        return w.readframes(w.getnframes())


def write_mp3(path, pcm, sample_rate, kbps):
    try:
        import lameenc
    except ImportError:
        _common.fail("MP3 output needs lameenc: python firmware/scripts/setup_dev.py")
    enc = lameenc.Encoder()
    enc.set_bit_rate(kbps)
    enc.set_in_sample_rate(sample_rate)
    enc.set_channels(1)
    enc.set_quality(2)
    data = enc.encode(pcm) + enc.flush()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def plan_from_config(config_path, sample_rate, user_root=None):
    """Bells whose file sounds need generating; files under ``user_root`` win."""
    with open(config_path, encoding="utf-8") as f:
        cfg = hb_config.parse(json.load(f))
    if cfg.audio["sample_rate"] != sample_rate:
        _common.fail("bells.json audio.sample_rate %d differs from --rate %d" % (cfg.audio["sample_rate"], sample_rate))
    items = []
    for b in cfg.bells:
        if b.kind not in ("mp3", "wav"):
            continue
        if user_root is not None and (Path(user_root) / b.sound).exists():
            _common.log("using provided %s (not generated)" % b.sound)
            continue
        items.append((b.id, b.midi, b.sound))
    return items


def generate(out_root, items, sample_rate, seconds, kbps, masters=MASTERS):
    """``items`` are (bell_id, midi, relative_path). Returns provenance records.

    A master in ``masters`` is used as the source for its note; ``masters=None``
    always synthesizes.
    """
    records = []
    cache = {}
    for bell_id, midi, rel in items:
        if midi not in cache:
            mpath = master_path(midi, masters) if masters is not None else None
            if mpath is not None and mpath.exists():
                pcm = read_master(mpath, sample_rate)
                source = "master %s (sha256 %s)" % (
                    mpath.relative_to(_common.REPO).as_posix() if mpath.is_relative_to(_common.REPO) else mpath.name,
                    _common.sha256_file(mpath),
                )
            else:
                pcm = synthesize(midi, sample_rate, seconds)
                source = "original synthesis (handbell.core.bell_model), digital-handbell project"
            cache[midi] = (pcm, source)
        pcm, source = cache[midi]
        path = out_root / rel
        if rel.lower().endswith(".mp3"):
            write_mp3(path, pcm, sample_rate, kbps)
            fmt = "mp3 %d kbit/s CBR mono" % kbps
        else:
            write_wav(path, pcm, sample_rate)
            fmt = "wav 16-bit mono"
        records.append(
            {
                "file": rel,
                "bell": bell_id,
                "midi": midi,
                "format": fmt,
                "sample_rate": sample_rate,
                "seconds": round(len(pcm) / 2.0 / sample_rate, 3),
                "bytes": path.stat().st_size,
                "sha256": _common.sha256_file(path),
                "source": source,
                "license": "MIT",
            }
        )
    return records


def write_masters(masters, notes, sample_rate, seconds):
    """Synthesize ``notes`` as uncompressed masters plus their provenance."""
    masters = Path(masters)
    records = generate(masters, [(n, pitch.name_to_midi(n), "%s.wav" % n) for n in notes], sample_rate, seconds, 0, None)
    with open(masters / "provenance.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump({"generator": "firmware/scripts/make_sounds.py --write-masters", "model": "handbell.core.bell_model.PARTIALS", "files": records}, f, indent=1, sort_keys=True)
        f.write("\n")
    _common.log("wrote %d masters to %s" % (len(records), masters))
    return records


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", default=str(_common.SRC / "bells.json"))
    ap.add_argument("--out", default=str(_common.BUILD / "assets"), help="root; files land at <out>/<bell sound path>")
    ap.add_argument("--rate", type=int, default=22050)
    ap.add_argument("--seconds", type=float, default=4.0)
    ap.add_argument("--kbps", type=int, default=64)
    ap.add_argument("--test-wav", default="A5", help="also write sounds/test/<NOTE>.wav for bring-up comparison ('' to skip)")
    ap.add_argument("--test-mp3", default="A5", help="also write sounds/test/<NOTE>.mp3 for bring-up comparison ('' to skip)")
    ap.add_argument("--masters", default=str(MASTERS), help="directory of uncompressed <NOTE>.wav masters")
    ap.add_argument("--write-masters", action="store_true", help="synthesize the library masters into --masters and exit")
    args = ap.parse_args(argv)

    if args.write_masters:
        return write_masters(args.masters, LIBRARY, args.rate, args.seconds)

    out_root = Path(args.out)
    items = plan_from_config(args.config, args.rate, user_root=_common.SRC)
    if args.test_wav:
        items.append((args.test_wav, pitch.name_to_midi(args.test_wav), "sounds/test/%s.wav" % args.test_wav))
    if args.test_mp3:
        items.append((args.test_mp3, pitch.name_to_midi(args.test_mp3), "sounds/test/%s.mp3" % args.test_mp3))
    records = generate(out_root, items, args.rate, args.seconds, args.kbps, Path(args.masters))
    provenance = {
        "generator": "firmware/scripts/make_sounds.py",
        "model": "handbell.core.bell_model.PARTIALS",
        "mp3_priming_ms": round(MP3_PRIMING_SAMPLES * 1000.0 / args.rate, 1),
        "files": records,
    }
    prov_path = out_root / "sounds" / "provenance.json"
    prov_path.parent.mkdir(parents=True, exist_ok=True)
    with open(prov_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(provenance, f, indent=1, sort_keys=True)
        f.write("\n")
    total = sum(r["bytes"] for r in records)
    _common.log("generated %d sound files, %d bytes, in %s" % (len(records), total, out_root / "sounds"))
    return provenance


if __name__ == "__main__":
    main()
