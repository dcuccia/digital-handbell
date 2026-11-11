# Printed-bell six-layer zero-open review snapshot

**Current public electronics review target, November 2026.** This is a
provenance-cleared snapshot, not a fabrication, CAD-fit, functional, safety
or child-use release. The older 37-open four-layer board is preserved
separately; do not use it as the current quote source.

[Project home](../../../../README.md) ·
[Review and risks](../../../../docs/pcb-review-2026-11.md) ·
[Gallery](../../../../docs/design-gallery.md) ·
[Revision guide](../README.md)

## Open and inspect

| Artifact | Purpose |
|---|---|
| [handbell.kicad_pro](handbell.kicad_pro) | Open this project in KiCad 10.0.6; retain the whole checkout for libraries |
| [handbell.kicad_sch](handbell.kicad_sch) | Native schematic with embedded symbols |
| [handbell.kicad_pcb](handbell.kicad_pcb) | Six-layer board `2f738ccb`; 104 footprints, 83 fitted parts |
| [MANIFEST.sha256](MANIFEST.sha256) | Packaged source hashes |
| [Native DRC](reports/native-drc.json) | Zero opens, 291 non-open findings, 46 parity findings; not a clean-board claim |
| [Publication validation](reports/publication-validation.json) | Exact source/delta, library and publication checks |
| [Quote package](../../quote-prep/2026-11-09-six-layer/README.md) | Matching BOM/CPL, quote history and remaining order gates |

The [most recent completed mechanical assembly](../../../../mechanical/README.md)
still binds an older board. There is no six-layer fit-qualified assembly
or populated STEP here.

## Source and provenance

The PCB is a publication derivative of private routing milestone
`0051b2e32c78533f102f3e20cb1bdac3c23377ec9d53b594b4ae5deda663a6bd`.
Only J1's footprint expression was replaced. Its copper lands are independently
derived from the JST ACHL dimensional drawing and retain the accepted pose,
pad numbers, nets, and copper geometry. All non-J1 native objects and saved
fills are preserved by exact-complement proof.

The source project retains the harmless historical internal
`meta.filename = routed-c1.kicad_pro`. The schematic is self-contained for
review, but blanket “Update Footprints from Library” is unsupported for three
legacy schematic alias names; do not use that command as a review step.

See `reports/publication-validation.json` for hashes, geometry, DRC results,
dependency checks, privacy checks, and limits.
