# Project guidance

## Bounded engineering work

- **September 23 coordinated IMU re-layout approved:** after the blocked
  twelve-plan fixed-placement trial, the owner explicitly authorized
  coordinated local re-layout. The bounded release covers IC4, C23/C24,
  R14/R15, two named local routing vias and necessary internal boundary
  routing; exact limits are in
  `docs/pcb-closure-plan.md#owner-pause-and-next-item`. Stage separately,
  prove both IMU returns and compatible supply/signal escapes together,
  and preserve all prior connections. No rule reductions, outside-interface
  changes or wholesale 69-track removal. The accepted 41-open board stays
  authoritative until electrical and required mechanical reviews pass.
  Follow the bottleneck-first sequence in `docs/routing-agent-policy.md`.
- **September 21 four-layer migration approved:** preserve the accepted
  two-layer `printed-bell-clock-draft` as evidence and establish one separate
  `printed-bell-four-layer` working candidate. Follow the four-layer batch,
  layer-role, all-layer-tooling and portable-process contract in
  `docs/routing-agent-policy.md`. Necessary special processes are permitted;
  simpler alternatives require equivalent electrical/thermal/assembly
  evidence, not silent removal of filled/capped-via requirements.
  Astra retains engineering judgment;
  routine routing/tool execution goes to explicitly pinned GPT-5.6 Sol at
  medium effort. Follow `docs/routing-agent-policy.md`, including its
  fail-closed invocation and runtime-verification gate. Never substitute Astra
  for an unavailable Sol executor. This supersedes the September 16 pause.
  The exact artifacts and next
  scope are in `docs/pcb-closure-plan.md#owner-pause-and-next-item`.
- Apply the [cost-aware closure plan](docs/pcb-closure-plan.md). Optimize for
  closing a stable candidate, not the number of microtasks or reports produced.
  Keep one active candidate and preserve older work as evidence.
- Divide potentially long work (schematics, sourcing, placement, PCB routing,
  CAD, exports and validation) into bite-sized, independently reviewable items.
  Name the exact references, nets, files or mechanical interface, expected
  output and stopping condition before starting. "Finish the board" is not
  a bounded item.
- Default to one foreground item per turn. Target 10-15 minutes total,
  including reasoning, research, generation and validation. Use explicit
  process timeouts; a tool's initial output wait is not a termination timeout.
  If the work will exceed the budget, checkpoint and split it rather than
  silently extending the task.
- The owner explicitly authorizes sequential bounded items as of September 14:
  after publishing a successful checkpoint, announce and start the next ready
  item without waiting for another prompt. Keep the per-item budget and retry
  limit; a blocker or pause request still stops the affected work promptly.
- The owner permits at most two corrective retries within that budget (an
  initial attempt plus up to two corrections). Do not turn a failed
  attempt into an open-ended search, optimization, routing or check/fix loop.
  Return a concrete blocker and preserve the usable work when the budget ends.
- For routine PCB execution use the verified Sol executor, even for small
  mechanical tasks; Astra handles engineering judgment and acceptance.
  Do not launch background engineering
  agents by default. If delegation is explicitly appropriate, give one small
  deliverable and the same budget/stop rules; do not queue additional scope
  onto an already-running agent. Its next job starts only after its current
  result has been reviewed.
- Separate source selection, native definitions/local placement, routing and
  whole-assembly integration when they cannot fit one bounded item. Reuse
  already-reviewed evidence; do not reopen sourcing without a specific new
  conflict. Distinguish required connectivity/clearance corrections from
  optional manufacturer-example footprint refinements.
- End each item with an honest status, changed artifacts, remaining work and
  a durable checkpoint. Commit/push accepted coherent changes under the
  owner's standing authorization; preserve incomplete experiments separately.
  Do not fabricate a successful result to meet the time budget.
- A request to pause, relocate or stop suspends further engineering work.
  Preserve saved files, report partial/stale state and return promptly; do
  not first try to finish routing or get a clean report. A queued message is
  not confirmation that a running agent paused. State that limitation and
  use the available task-cancellation controls when a forced stop is needed.
- Keep the handoff sufficient for a fresh session to resume: exact starting
  artifact, relevant decision, applied/unapplied changes and one next item.
  Automatic continuation requires the owner's explicit authorization above;
  it does not authorize an unbounded task or skipping dependency gates.

### General agent efficiency principles

These principles also apply to software work; hardware-specific gates remain
in the linked closure plan.

- Freeze settled requirements and dependencies before expensive downstream
  work. Reopen them only for a concrete conflict, not speculative improvement.
- Keep a promising candidate with a finite repair list. A local regression
  calls for a local repair attempt, not automatic abandonment or acceptance.
- Count root defects, not repeated diagnostic witnesses. Preserve the
  evidence, but group findings by the actual connection or behavior to repair.
- Batch related bookkeeping. Use cheap scoped checks during iteration and
  complete checks at coherent milestones; never substitute scoped evidence
  for a release gate. Reuse unchanged evidence only when its inputs/invariants
  are demonstrably unchanged.
- Prefer existing deterministic tools to repeated model reasoning or new
  one-off frameworks. Time slow stages once before optimizing; a timeout
  indicates incomplete evidence, not necessarily a defective design.
- For routing, query complete relevant nets and obstacles through the native
  API, then screen a bounded numerical candidate batch. Read the exercised
  [tooling lessons](docs/routing-tooling.md) before repeating autorouter trials.
  Include a no-routing exchange control; requested scope/settings are not
  qualified until demonstrated. Never count exchange-only changes as routing.
- Generate connections between existing connected copper groups. A fixed-pad
  grid failure can miss another reachable terminal on the same group; inspect
  those terminals before moving parts, refining the grid or expanding search.
- Make each bounded item a coherent closure pass, not a single field edit.
  Keep reports concise and source-bound; regenerate large exports only when
  needed for review or milestone handoff.
- Preserve functional, safety, recovery and provenance requirements.
  Optional simplifications need explicit dispositions, not hidden exclusions.
- Escalate structural redesign, exhausted corrective attempts or repeated
  lack of measurable progress. Do not broaden the task or promise a remaining
  dollar cost without evidence.

## Design and provenance

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
- The original 0.2 43 mm placement has no routing. Do not overwrite it with the generator
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
- The separate T8 cartridge uses the exact 83-part T8 manifest, four printed
  pieces and M2x6 captive-nut joints. Its 6.25 mm mouthward stack shift and
  10.75 mm grille projection are review alternatives, not an approved exterior.
  Use `build_t8_cartridge.py` / `check_t8_cartridge.py`; preserve the fixed-stack
  evidence. Full contacts stay in native/STEP; the inert PCBA STL explicitly
  omits BT1/BT2. The owner's approximate 1 mm spacing observation is not a
  measured clearance or permission to reduce component heights.
- September 13 authorizes a separate single-piece printed bell, flush removable
  cartridge and black handle, plus an all-front electronic SMT study with
  explicit battery-contact exceptions. Read `docs/printed-bell-revision.md`
  and its dated design-input contract. Preserve the successful T8 fit snapshot.
  The owner now permits routing after coordinated engineering review establishes
  stable PCB mounts, USB/service and contact interfaces; this is not fabrication
  approval. Silk-PLA appearance is not strength/thermal qualification. Do not
  trace or redistribute the supplied reference photographs.
- The printed-bell front placement achieves D43 with 81F electronic parts and
  two B SMT contacts. Preserve its immutable stage-1 checkpoint when routing
  a separate candidate, then rebind mechanical inputs exactly. The D70/H55.8
  shell has an 80 mm keyed M4x16 handle and three internal front-retention
  joints; preserve their closed exterior skin and real USB front lip. A
  nose-approach screen is not actual USB mating or sealing qualification.
- The first `printed-bell-routing` candidate contains partial copper, not a
  power-layout approval. Read its `reports/power-routing-review.md`: the boost
  output-capacitor loop and shared protector-sense pickup required rework in a
  separate candidate. Keep actual load/ripple/sense paths distinct, account
  for pad/parallel-copper overlaps when evaluating necks, and do not infer
  ampacity from DRC. Current/copper/drop/temperature targets are provisional.
  Prioritize paired power/return routing and local switching loops over
  preserving an initial local floorplan; rebind moved parts into the full
  mechanical model. Preserve contact-base exclusions and CELL_NEG isolation.
- The separate `printed-bell-power-rework` implements those two topology
  corrections and has a matching complete CAD assembly, but retains 155
  unconnected items and open power budgets. Preserve this milestone while
  completing routing. Bind authoritative source bytes, not ignored KiCad
  `.kicad_prl` preferences or other ambient personal state.
- Read `docs/usb-connector-qualification.md`: the import lost four elongated
  USB anchor openings, leaving round drills. Restoring slots without reviewing
  annular rings is insufficient. Qualify the complete manufacturer pattern,
  paste, pickup datum and tail/body geometry; do not waive global clearances
  or edit the archived reference. SMD-only CPL export can omit fitted X6.
- The owner expects full PCB+PCBA quotation assets for JLCPCB and PCBWay.
  Follow `docs/pcba-quotation-plan.md`; include both fitted rear contacts and
  verify actual placement centres/rotations. Do not label unrouted exports
  quote-ready, confuse quotation with safety qualification, or upload/order
  on the owner's behalf without approval.
- Track design changes, decisions, dependencies, and supporting artifacts in
  linked epic issues. A rule-check pass is not functional or safety signoff.
- Do not purchase parts, place fabrication orders, or distribute a child-use
  kit without explicit owner approval. Do not publish personal participant data.
- Use accessible explanations and exported schematic views for novice review.
  Record real tool versions and reproducible export steps once exercised.
