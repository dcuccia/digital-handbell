#!/usr/bin/env python3
"""Generate original synthesized bell sounds for the device.

Deterministic: the same inputs produce the same WAV bytes (MP3 bytes depend
on the pinned LAME build in ``lameenc``). Sounds come from the modal model
in ``handbell.core.bell_model``, so no third-party recordings are involved.
They are released under the project's MIT license (see ATTRIBUTION.md).

    python firmware/scripts/make_sounds.py --out firmware/build/assets
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


def generate(out_root, items, sample_rate, seconds, kbps):
    """``items`` are (bell_id, midi, relative_path). Returns provenance records."""
    records = []
    cache = {}
    for bell_id, midi, rel in items:
        pcm = cache.get(midi)
        if pcm is None:
            pcm = synthesize(midi, sample_rate, seconds)
            cache[midi] = pcm
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
                "seconds": seconds,
                "bytes": path.stat().st_size,
                "sha256": _common.sha256_file(path),
                "source": "original synthesis (handbell.core.bell_model), digital-handbell project",
                "license": "MIT",
            }
        )
    return records


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", default=str(_common.SRC / "bells.json"))
    ap.add_argument("--out", default=str(_common.BUILD / "assets"), help="root; files land at <out>/<bell sound path>")
    ap.add_argument("--rate", type=int, default=22050)
    ap.add_argument("--seconds", type=float, default=4.0)
    ap.add_argument("--kbps", type=int, default=64)
    ap.add_argument("--test-wav", default="A5", help="also write sounds/test/<NOTE>.wav for bring-up comparison ('' to skip)")
    args = ap.parse_args(argv)

    out_root = Path(args.out)
    items = plan_from_config(args.config, args.rate, user_root=_common.SRC)
    if args.test_wav:
        items.append((args.test_wav, pitch.name_to_midi(args.test_wav), "sounds/test/%s.wav" % args.test_wav))
    records = generate(out_root, items, args.rate, args.seconds, args.kbps)
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
