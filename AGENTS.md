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
- The imported reference retains LIS3DH. The owner-approved LSM6DSOX is
  integrated in `hardware/handbell`; read its README and `docs/motion-sensing.md`.
  It uses ST Mode 1: SDx/SCx grounded, OCS_Aux/SDO_Aux NC, both GND pads connected.
  Keep the documented CircuitPython CTRL9_XL initialization gate before bring-up.
  Neither an IMU nor a pose classifier proves physical chest contact.
- KiCad 10.0.6 has been exercised. The native reference package under
  `hardware/reference/adafruit-5768` is CC BY-SA 3.0, not root MIT, and has
  unchanged initial ERC findings. Their individual dispositions and the
  derivative's clean ERC are in `hardware/handbell/reports`; the reference
  itself must not be edited as if it were the derivative.
- Preserve shared power-selection/switching circuitry, pullups, decoupling,
  protection, and recovery access when removing peripheral branches.
- Separate components-on-one-face from two copper layers. Do not promise board
  diameter, runtime, price, or child suitability without the relevant evidence.
- Read `docs/electrical-reduction-and-placement.md` for the implemented 0.2
  revision and its explicit remaining gates. MiniBoost's pinned
  divider is approximately 5 V despite 5.2 V prose; the 40 mm speaker has
  conflicting seller power ratings. Do not treat either as resolved by a title.
- Keep measured geometry separate from assumptions. For new work use
  `docs/measurements/2026-09-11-shell-speaker-inputs.json`: ID71.68 at z0,
  ID69.75 at z4.9, ID50 at confirmed z14.9; OD38.42 at approximate z41.75.
  Owner assumes a uniform 1.15 mm wall; upper ID36.12 is inferred, raw OD/ID
  discrepancies remain unresolved, and curve/final-closure shapes are not
  measured. The old z13/D50 to z43/D34 profile belongs to preserved studies.
  GPIO19 is stock EXTERNAL_BUTTON; stock board.BUTTON is GPIO7.
  GPIO20 is active-high AMP_MUTE.
- The 43 mm placement has no routing. Do not overwrite it with the generator
  after manual changes. Preserve local KiCad 10 pad angles, source libraries
  and documented Q3/jumper corrections; do not silence USB clearance findings.
- Mechanical component heights and battery blocks are screening placeholders,
  not qualified parts. Follow the FreeCAD handoff before changing shared geometry.
- Preserve the 0.2 print snapshot while investigating the owner's preferred
  speaker-facing electronics/handle-side cell alternative. PCB battery contacts
  may be through-hole or SMT with a capture cradle; no cell/holder is selected.
  Do not treat flipping the board as resolution of its speaker conflicts.
- Owner speaker measurements supersede the old gauge for new work:
  D40/H19 overall, D32 basket rear at z12, magnet H7 and September 11 D21.70
  (superseding D22). Keep the original print
  files intact; use the separate measured-speaker study. The good PCBA print
  has no measured insertion depth, and unspecified flimsy parts are not yet
  identified failures. Do not invent tolerances, reinforced parts or holder fit.
- The separate `hardware/handbell/iterations/wing-draft` uses schema-2 mixed-face
  proxies, explicit z bounds and M2 mounting interfaces. Use its dedicated
  generation/checking tools, not the original placement generator. Reserve
  USB through-board anchors on B; X1 is DNP across all three schematic units.
  Do not transfer the old GUI parity approval to this variant or count B-side
  fitted parts as copper-only BOM exclusions.
- The integrated-cartridge study consumes that exact manifest. Its two printed
  pieces do not include battery retention or shell attachment; D72 is an
  external flange, not a diameter to shrink to the D70 mouth. Preserve the
  required speaker-before-yoke-before-PCB sequence and recorded small gaps.
- The September 11 T8 revision must remain separate from the wing/print
  snapshots and consume its own exact placement manifest. Whole-cell
  protection cannot be replaced by TPS61023-only protection. Distinguish raw
  cell negative from protected GND for a low-side cutoff; insulate the cell
  can, both contacts and hardware from the metal bell and avoid ground bypasses.
  The 1-1.5 mm proud-plastic request is a design target, not qualified insulation.
  New hardware, USB access and reversible service paths must appear together
  in FreeCAD for owner review before routing. Read `docs/t8-integration-plan.md`.
- Track design changes, decisions, dependencies, and supporting artifacts in
  linked epic issues. A rule-check pass is not functional or safety signoff.
- Do not purchase parts, place fabrication orders, or distribute a child-use
  kit without explicit owner approval. Do not publish personal participant data.
- Use accessible explanations and exported schematic views for novice review.
  Record real tool versions and reproducible export steps once exercised.
