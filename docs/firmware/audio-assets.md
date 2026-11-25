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
| 2 resident WAV bells, C5 and G5, 4 s, 16-bit 22.05 kHz mono | 2 × 176,444 |
| Bring-up comparison files `sounds/test/A5.wav` and `A5.mp3` | 176,444 + 32,600 |
| **Allocated (with clusters and directories)** | **673,792 of 983,040** |

That leaves about **309 KB** of headroom, enough for one more 4-second WAV
bell. Drop the test files (`--test-wav "" --test-mp3 ""`) to make room for
two. `firmware/build/reports/build.json` has the current figures for every
build. Confirm real free space with `bringup.info`; the budget is an
estimate.

| Format (4 s mono note) | Bytes | Notes in ~850 KB | Start delay |
|---|---:|---:|---|
| WAV 44.1 kHz 16-bit | 352,800 | 2 | none |
| WAV 22.05 kHz 16-bit | 176,400 | 4 | none |
| MP3 64 kbit/s, 22.05 kHz | 32,600 | ~26 | ~50 ms (measured on host) |
| MP3 32 kbit/s, 22.05 kHz | ~16,300 | ~50 | ~50 ms |
| `synthio` modelled bell (`"sound": "synth"`) | 0 | any pitch | none in the file; synthesis CPU on device |

## Why the instrument bells are WAV

On the first-article board (stock CircuitPython 10.3.2, RP2040 at 125 MHz),
an MP3 decoded while the app runs drops out audibly. Phone recordings of the
same C5 note with the main loop busy (IMU reads plus a collection every
0.5 s) showed 6-7 short dropouts (6-11 dB, about 10 ms) per three notes for
MP3. The same note as a 16-bit WAV showed none, and the source MP3 decoded
on the host is clean. The cause is decode starvation on the single core
that also runs Python, not level or wiring. Details are in
[#21](https://github.com/dcuccia/digital-handbell/issues/21).

The shipped `bells.json` therefore has **two resident WAV bells, C5 and
G5**; a click on the button switches between them. Staging MP3 or ADPCM to
WAV on the device was measured as too slow on stock firmware (25 s and
about 6 s per 4-second note). A custom CircuitPython build that decodes on
the second core is being designed in
[#29](https://github.com/dcuccia/digital-handbell/issues/29). `synthio`
bells synthesize in C with no file or decoder work, but have not yet been
measured under app load on the board.

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

The firmware creates `audio.mp3_decoders` decoders (default 1) once at
startup, after a collection, **only if a configured bell uses MP3**, and
reuses them for every strike. With the shipped all-WAV bells no decoder is
allocated, which leaves about 37 KB more heap.

- With one decoder, an MP3 strike restarts the sounding MP3 rather than
  overlapping it. WAV and `synth` voices still overlap freely.
- A WAV voice gets its own preallocated 1 KB read buffer.
- Raise `mp3_decoders` (up to `voices`) only if `memFree` in the status
  line stays healthy. Each extra decoder costs about 37 KB.

With eight MP3 bells and one decoder, the running app reported about 24 KB
of `memFree`. A 24-strike stress test across all eight MP3 bells, with
other allocations churning the heap, completed without a MemoryError. It
did not test for audible dropouts, which the section above covers.

## Rules for sounds

- Every sound must be mono, 16-bit and at `audio.sample_rate` (22,050 Hz by
  default). `audiomixer` refuses mismatched sources, including 8-bit WAV.
- MP3s must be **CBR** (constant bit rate), as CircuitPython requires.
  `audiocore.WaveFile` reads plain PCM only, not ADPCM.
- Paths in `bells.json` are relative to the drive root (`sounds/C5.wav`).
  The firmware refuses to start, with a clear message, if a file is missing.

## Where the sounds come from

The uncompressed **masters** live in [`firmware/sounds/`](../../firmware/sounds/README.md),
one 16-bit mono 22.05 kHz `<NOTE>.wav` per note from C5 to C6, tracked with
Git LFS. Run `git lfs pull` after cloning. `build.py` calls
[`make_sounds.py`](../../firmware/scripts/make_sounds.py), which renders
each sound in `bells.json` from its master: a byte-identical copy for WAV,
or an encode for MP3. Without a master it synthesizes the note.

The current masters are **original** sounds from the modal model in
[`bell_model.py`](../../firmware/src/handbell/core/bell_model.py): the
strike note, a slightly detuned copy, the twelfth (3x) and two higher
partials, each decaying exponentially. The `synth` voice uses the same
partials with `synthio` envelopes. The model is a starting point for
listening comparisons, not a measured handbell. Regenerate the masters with
`python firmware/scripts/make_sounds.py --write-masters`. Their
`provenance.json`, and `sounds/provenance.json` on the device, list each
file's hash, source and license (MIT, project-generated).

## Adding your own recordings

Follow [ATTRIBUTION.md](../../ATTRIBUTION.md). Every distributed sound
needs a documented source, author, license and permitted modifications.
Code licenses do not cover recordings. To add one:

1. Convert to mono 16-bit 22.05 kHz WAV (for example
   `ffmpeg -i in.wav -ac 1 -ar 22050 -c:a pcm_s16le C5.wav`).
2. Trim leading silence so the attack starts at sample 0.
3. Replace the master `firmware/sounds/<NOTE>.wav`, update its entry in
   `firmware/sounds/provenance.json`, and list the note in `bells.json`. Do
   not commit recordings you lack the rights to redistribute.

A file placed at the same path under `firmware/src/sounds/` (create it) is
copied as a source file instead, and always wins over a rendered sound.
