# Sound masters

Uncompressed masters for the bell sound library: one mono 16-bit
22,050 Hz `<NOTE>.wav` per note, C5 to C6. They are tracked with
**Git LFS**, so run `git lfs pull` after cloning; a build that finds an LFS
pointer instead of audio stops with that instruction.

`bells.json` chooses which notes reach the device (C5 and G5 by default).
`firmware/scripts/build.py` renders each chosen sound from its master: a
byte-identical WAV, or an MP3 encode for a bell that asks for MP3.

The current masters are original sounds synthesized from
`handbell.core.bell_model` and released under the project's MIT license.
`provenance.json` lists each file's hash, source and license. Regenerate
them with:

    python firmware/scripts/make_sounds.py --write-masters

To use a recording instead, replace the note's master and its provenance
entry, following [ATTRIBUTION.md](../../ATTRIBUTION.md) and
[audio assets](../../docs/firmware/audio-assets.md#adding-your-own-recordings).
