# Project guidance

- This is a public educational digital-handbell project in an early planning
  phase. Read `README.md`, `docs/roadmap.md`, and the relevant decision entries
  before implementing.
- Preserve the historical `Design Notes.md`, `System Diagram.pptx`, and existing
  MIT `LICENSE`. Record new decisions separately; do not silently overwrite
  the 2023 wireless/6-DOF concept.
- Prefer documented, code-supported open hardware. Pin the actual upstream
  source revision and distinguish vendor evidence from project measurements.
- Follow `ATTRIBUTION.md` before importing CAD, code, recordings, or models.
  Never apply the root MIT license to third-party CC BY-SA hardware by default.
- KiCad is the recommended target; upstream Adafruit CAD is EAGLE XML.
  Import fidelity and source-to-net equivalence must be reviewed before reuse.
- The working baseline is RP2040 Prop-Maker Feather 5768, not analog-audio
  FeatherWing 3988. LIS3DH is accelerometer-only; RP2040 I2S uses PIO.
- Preserve shared power-selection/switching circuitry, pullups, decoupling,
  protection, and recovery access when removing peripheral branches.
- Separate components-on-one-face from two copper layers. Do not promise board
  diameter, runtime, price, or child suitability without the relevant evidence.
- Track design changes, decisions, dependencies, and supporting artifacts in
  linked epic issues. A rule-check pass is not functional or safety signoff.
- Do not purchase parts, place fabrication orders, or distribute a child-use
  kit without explicit owner approval. Do not publish personal participant data.
- Use accessible explanations and exported schematic views for novice review.
  Record real tool versions and reproducible export steps once exercised.
