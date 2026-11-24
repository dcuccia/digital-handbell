# Audio assets and storage

[Firmware guide](../../firmware/README.md) · [Architecture](architecture.md) · [Bring-up](bring-up.md)

## Budget on the 2 MB board

The Pico CircuitPython build reserves 1020 KiB for firmware and 4 KiB for
settings, leaving a **1 MiB** filesystem on the W25Q16JV. `build.py` keeps a
64 KiB reserve for FAT overhead and files CircuitPython creates, then checks
everything against the remaining 960 KiB, counting 512-byte clusters. The
build at the time of writing measured:

| Item | Bytes |
|---|---:|
| `handbell/` compiled to `.mpy` | 37,413 |
| `bringup/` scripts (`.py`) | 18,235 |
| Adafruit libraries (lsm6ds, register, bus_device) | 20,417 |
| 8 MP3 bells, C5-C6, 4 s, 64 kbit/s mono | 8 × 32,600 |
| Test WAV `sounds/test/A5.wav`, 4 s, 22.05 kHz | 176,444 |
| **Allocated (with clusters and directories)** | **544,256 of 983,040** |

That leaves about **439 KB** of headroom: roughly 13 more 4-second MP3 bells,
or two more WAVs. `firmware/build/reports/build.json` has the current
figures for every build. Confirm real free space with `bringup.info`; the
budget is an estimate.

| Format (4 s mono note) | Bytes | Notes in ~850 KB | Start delay |
|---|---:|---:|---|
| WAV 44.1 kHz 16-bit | 352,800 | 2 | none |
| WAV 22.05 kHz 16-bit | 176,400 | 4 | none |
| MP3 64 kbit/s, 22.05 kHz | 32,600 | ~26 | ~50 ms (measured on host) |
| MP3 32 kbit/s, 22.05 kHz | ~16,300 | ~50 | ~50 ms |
| `synthio` modelled bell (`"sound": "synth"`) | 0 | any pitch | none in the file; synthesis CPU on device |

## MP3 start delay

MP3 encoders and decoders add priming samples before the audio. A LAME
22.05 kHz/64 kbit/s file decoded with dr_mp3 on the host first exceeds 10%
amplitude at **sample 1106 (50.2 ms)**. That is the standard 576-sample
encoder delay plus a 529-sample decoder delay, and it happens on every
strike. At 44.1 kHz the same sample count is about 25 ms, at twice the
storage. CircuitPython's Helix-based decoder was not measured; the bring-up
latency test does that.

Options, in increasing complexity:

1. Use MP3 for its storage advantage and judge whether 50 ms plus detection
   latency is acceptable musically. That is an owner decision once measured.
2. Use WAV or `synth` for latency-critical notes; the choice is per bell in
   `bells.json`.
3. A **PCM head + aligned MP3 tail**: a short WAV covers the first ~55 ms
   while an MP3, encoded from audio shifted by the priming length, takes
   over sample-aligned. Not implemented; it depends on a measured,
   constant decoder delay on the device.

## MP3 decoders and RAM

Flash is not the only budget. Each CircuitPython `audiomp3.MP3Decoder`
costs about **37 KB of RAM** (measured on the RP2040 board: decoder state
plus two 4,608-byte PCM buffers and the input buffer). The RP2040 heap is
fixed at about 150 KB and the app's imports use about 65 KB, so only one
decoder fits comfortably. The decoder allocates its buffers without first
running garbage collection, so creating one while the app is running can
fail with `MemoryError` even when memory would be available after a
collection. That was the fast red blink seen on the first board.

The firmware therefore creates `audio.mp3_decoders` decoders (default 1)
once at startup, after a collection, and reuses them for every strike:

- With one decoder, an MP3 strike restarts the sounding MP3 rather than
  overlapping it. WAV and `synth` voices still overlap freely.
- A WAV voice gets its own preallocated 1 KB read buffer.
- Raise `mp3_decoders` (up to `voices`) only if `memFree` in the status
  line stays healthy. Each extra decoder costs about 37 KB.

On the device with one decoder, the running app reports about 24 KB of
`memFree`. A 24-strike stress test across all eight MP3 bells, with other
allocations churning the heap, completed without error.

## Rules for sounds

- Every sound must be mono, 16-bit and at `audio.sample_rate` (22,050 Hz by
  default). `audiomixer` refuses mismatched sources.
- MP3s must be **CBR** (constant bit rate), as CircuitPython requires.
  `audiocore.WaveFile` reads plain PCM only, not ADPCM.
- Paths in `bells.json` are relative to the drive root (`sounds/C5.mp3`).
  The firmware refuses to start, with a clear message, if a file is missing.

## Where the sounds come from

`build.py` calls [`make_sounds.py`](../../firmware/scripts/make_sounds.py)
to synthesize **original** bell sounds from the modal model in
[`bell_model.py`](../../firmware/src/handbell/core/bell_model.py): the
strike note, a slightly detuned copy, the twelfth (3x) and two higher
partials, each decaying exponentially. The `synth` voice uses the same
partials with `synthio` envelopes. The model is a starting point for
listening comparisons, not a measured handbell. Generated WAVs are
byte-identical across runs. `sounds/provenance.json` on the device lists
each file's hash, source and license (MIT, project-generated).

## Adding your own recordings

Follow [ATTRIBUTION.md](../../ATTRIBUTION.md). Every distributed sound
needs a documented source, author, license and permitted modifications.
Code licenses do not cover recordings. To add one:

1. Convert to mono 22.05 kHz. For MP3, use CBR (for example
   `ffmpeg -i in.wav -ac 1 -ar 22050 -codec:a libmp3lame -b:a 64k out.mp3`).
2. Trim leading silence so the attack starts at sample 0. MP3 adds its own
   delay on top.
3. Put the file under `firmware/src/sounds/` (create it), add the bell to
   `bells.json` and record provenance beside it. Do not commit recordings
   you lack the rights to redistribute.

`build.py` copies `firmware/src/sounds/` as source files. The generator then
fills in only the bells whose files are not provided there, so your
recording always wins over a generated sound with the same path.
