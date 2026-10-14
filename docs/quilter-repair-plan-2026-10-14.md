# Bounded repair plan: saved Quilter standard 1.1

## Decision and authorization

Plan the finish of **one saved candidate**, not another placement/layer search.
The owner authorized this plan on October 14. **No PCB repair, native rerun,
new cloud job, source replacement or fabrication is authorized by this document.**
The authoritative four-layer 37-open board remains unchanged.

Recommend a **four-item, at most 60-minute viability pilot** before committing
to full manual closure. Test the constrained core-power, USB and power-trunk
work first, not easy test-pad connections that can improve an open count while
leaving the difficult work untouched. Each future item has a 15-minute total
cap, including preparation and review, and at most an initial attempt plus two
corrections. A timeout or exhausted item stops that scope; it does not reset
its budget under a new name. These are proposed effort caps, not completion
estimates or current permission to start.

## Exact starting point

Private evidence root, abbreviated `REC` below:

```text
C:\Projects\dcuccia\digital-handbell-routing-bakeoff-20260927\quilter\outputs\placement-first-results-20261013T1904\setup-fill-recovery-20261013T2243
```

| Input | SHA-256 |
|---|---|
| `REC\filled\candidate-1.1\handbell.kicad_pcb` | `05857d580f37294177d7b4be91b5edb958c82806cb7b414749960f63cf70062c` |
| Same-stem intended project | `917b3f1643449f86db43e6b7c987837d1b49aa1c243c7896e765510080b1971c` |
| Same-stem schematic | `ec93cc6f6f03bb91dd05199d2e0b4cab6b542567031e484fe8098056992ab69e` |
| Same-directory `drc.json` | `64c59ec14915af8ecf5f3f3c24bc8f8444c82cc97426097b40e810c156fa9bcb` |
| `REC\witness-1.1-attempt-1\report.json` | `8f288b0e40b401f93bf1d4facdc316b6e6fe5df4e5621c6e068cc63b4750ee2e` |
| `REC\width-screen-saved-1.1\attempt-2\report.json` | `600151ca7bf834ee8ecbf601282fc8ca6d8e5151ee2320af9c38e2dcf86091d8` |

The [October 13 ledger](measurements/2026-09-27-router-bakeoff/quilter-eight-candidate-review-2026-10-06.json)
binds the raw archives, retained-object definition and native/composite
preservation proof. Keep its original strict serialized HELD report alongside
the accepted source-specific supplement. Do not rebuild the input or repeat
the missing mask-only control just to begin repair planning.

The saved board has 104 footprints, 325 pads and 1,563 routing objects.
Its intended-project DRC has **34 open records / 30 non-GND nets, 405 other
findings and 46 parity records**. All six QSPI nets remain open. No native
short/copper-clearance finding was reported in the exercised default
first-error-per-track mode; this is not an exhaustive per-rule clearance proof.

## Fixed contract for any later implementation

Use a new isolated derivative of the saved PCB and the same intended project
and schematic, never the returned project's weaker/different defaults.
Keep all 104 component poses, pad/net identities, outline, eight-layer physical
stack, 63 zone definitions and the retained 209 copper objects unchanged.
Only an explicitly enumerated subset of **new Quilter copper** may be replaced;
record old/new UUIDs and every preserved branch connection. Do not freeze
replaceable generated stubs merely because they exist, or remove them merely
because DRC calls them dangling.

Keep the actual signal/ground roles **S/G/S/G/G/S/G/S**:
F, In2, In5 and B are signal layers; In1, In3, In4 and In6 are protected GND.
B routing and every through-via remain constrained by contact metal, slots,
holes and all-layer rules. Preserve all five mandatory filled/planarized/capped
process vias and the two private-return via exclusions. Do not replace
CELL_NEG isolation with a common GND connection or bypass either
R24.2-to-C28.2 or R26.2-to-R27.2 private pickoff.

Maintain the 0.1778 mm new-track floor, 0.20 mm copper clearance and intended
hole/edge rules; new ordinary vias start at 0.650/0.350 mm with a 0.150 mm ring.
These are minima, not USB widths, current ratings or approval to resize
retained process vias. No smaller-rule, placement, footprint, layer-role or
mechanical exception is selected.

## Complete remaining-connection inventory

The saved graph has 26 two-group nets and four three-group nets. On **every
net**, DRC multiplicity equals the number of pad groups minus one: 34 required
group merges in total. This consistency check does not turn 34 witnesses
into 34 route operations or prove an unobstructed path. A branched connection
may join several groups, while one connection can require several changes.
All groups below are required; service connections are deferred, not deleted.

`/` separates disconnected groups; commas and semicolons within a group do
not. References retain their native pad numbers. The complete large +3V3
group remains in the bound graph rather than being reprinted here.

| Work package | Exact net | Saved terminal groups | Open records |
|---|---|---|---:|
| IMU mode strap | `+3V3` | Existing 32-terminal group, including IC4.5/.8 / IC4.12 (CS) | 1 |
| MCU core | `VCORE` | C8.1, C18.2, C7.2, IC1.23/.45 / C6.2, IC1.50 | 1 |
| Flash | `QSPI_CS` | U1.1, R5.1, R11.1 / IC1.56 | 1 |
| Flash | `QSPI_DATA[1]` | IC1.55 / U1.2 | 1 |
| Flash | `QSPI_DATA[2]` | IC1.54 / U1.3 | 1 |
| Flash | `QSPI_DATA[0]` | IC1.53 / U1.5 | 1 |
| Flash | `QSPI_SCK` | IC1.52 / U1.6 | 1 |
| Flash | `QSPI_DATA[3]` | IC1.51 / U1.7 | 1 |
| Flash-associated branch | `Net-(D3-PadA)` | D3.A / R11.2; R11.1 is on QSPI_CS | 1 |
| USB | `D-` | IC1.46 / R9.2 | 1 |
| Source power | `VBUS` | U3.4, X6.A4B9/.B4A9, Q3.1, R4.2 / D4.A, CHG0.A | 1 |
| Battery branch | `VBAT` | CHG_EN0.2, C20.1, both BT1.1 lands, TP11.P$1, Q3.3 / R25.1 | 1 |
| Source power | `VHI` | R16.2, Q3.2, D4.C, Q1.2 / C1.1, U2.1 / R3.2 | 2 |
| Power control | `~{ENABLE}` | R16.1, Q2.3 / Q1.1 | 1 |
| Power control | `EN` | U2.3 / R3.1 | 1 |
| Power control | `POWER` | Q2.1, TP16.P$1, R17.1 / IC1.35 / U5.2 | 2 |
| Motion/I2C | `SCL` | IC1.5, R14.2 / IC4.13 | 1 |
| Motion/I2C | `SDA` | IC4.14 / R15.2 / IC1.4 | 2 |
| Motion interrupt | `INT` | IC4.4 / IC1.34 | 1 |
| Audio data | `I2S_DIN` | TP12.P$1, U4.1 / IC1.27 | 1 |
| Audio clock | `I2S_LRCLK` | TP14.P$1, U4.14 / IC1.29 | 1 |
| Audio control | `AMP_MUTE` | TP15.P$1, R20.2, Q4.1 / IC1.31 | 1 |
| Audio configuration | `GAIN` | GAIN0.2 / U4.2 | 1 |
| User input | `BUTTON` | R21.2, R22.1 / C25.1, IC1.30 | 1 |
| Indication/control | `D13` | R7.1 / IC1.16 | 1 |
| Charge indication | `Net-(CHG0-PadC)` | CHG0.C / R2.1 | 1 |
| Reset and service | `~{RESET}` | TP7.P$1 / IC1.26 / R1.2 | 2 |
| Debug service | `SWDIO` | TP5.P$1 / IC1.25 | 1 |
| Debug service | `SWCLK` | TP4.P$1 / IC1.24 | 1 |
| IMU test service | `/IMU_INT2` | TP6.P$1 / IC4.9 | 1 |
| **Total** | **30 nets** | **64 existing pad groups** | **34** |

Only SWDIO, SWCLK, /IMU_INT2 and the TP7 branch of RESET are plainly
service-only group joins. A test pad in I2S_DIN, I2S_LRCLK or AMP_MUTE does
**not** make that open optional: its group also contains the functional
amplifier terminal. RESET's MCU-to-pullup join remains functionally important.
Do not remove test lands, boot paths, pullups or controls to improve counts.

Three source-function corrections matter to the repair order. IC4.12 is
`CS_12`, an input tied high for the selected IMU interface, **not a missing
VDD connection**. POWER joins IC1.35/GPIO23, U5.2/EN and Q2.1/gate;
it is **enable control, not a high-current supply trunk**. R25 is the
330-ohm VBAT-to-PROT_BAT link; retain it rather than treating isolated R25.1
as a disposable test branch.

The diode branch is also mandatory boot circuitry:
QSPI_CS -> R11 (1 kohm) -> D3.A, with D3.C on the already connected
USBBOOT group `{IC1.9, TP3.P$1, D3.C}`. Native diode pad spelling is
`C`, not `K`. This open belongs with flash/boot closure, not LED cleanup.

## Width work is eight packages, not 76 independent repairs

All selected segments are new F.Cu copper at 0.162 mm. The 15 endpoint runs
below describe segmentation only, not full electrical connected components.

| Net | Segments | Endpoint runs | Drawn length (mm) | Disposition |
|---|---:|---:|---:|---|
| +3V3 | 41 | 6 | 6.736810 | With supply/strap closure and current-path review |
| VCORE | 12 | 3 | 2.043858 | With MCU regulator/core and C18 bypass work |
| D+ | 4 | 1 | 0.643835 | With complete USB pair, not minimum-width-only correction |
| GND | 4 | 1 | 1.590409 | Preserve local-return topology and all filled-island duties |
| BUTTON | 3 | 1 | 1.454430 | Local rule correction; retain filter function |
| I2S_BCLK | 4 | 1 | 2.047365 | With audio routing/reference review |
| SCL | 4 | 1 | 1.071451 | With I2C connections; preserve pullups |
| USBBOOT | 4 | 1 | 1.457097 | Recovery control, not a USB differential conductor |
| **Total** | **76** | **15** | **17.045255** | **53 segments on +3V3/VCORE** |

The saved prospective screen added 7.9 um per selected boundary, or 15.8 um
when both members widen. It found no foreign-copper obstacle in its limited
F.Cu screen, but nine new same-net contact pairs involving 11 selected tracks:
five pairs on +3V3, two on VCORE and two on D+. They are **topology-review
locations**, not nine proven defects or nine guaranteed repairs. The exact
UUIDs/coordinates remain in the bound width report. No GND contact pair was
reported, but that does not waive its private-return proof after changes.

One bounded static parse of the exact saved board adds useful discrimination:
**seven of the nine pairs already have literal same-net F segment paths
between their members**. Four have a direct intervening segment; three have
a multi-segment chain. The two unresolved pairs share one local +3V3 area.
This reduces the unknown topology questions; it does not prove widening
harmless or replace current/impedance/clearance checks.

| Pair(s), in width-report order | Local area (mm) | Existing static path evidence |
|---|---|---|
| W1, +3V3 | x=99, y=96.55-97.183114 | Direct bridge `79474f75-ec2b-4fdf-9e4b-b135b6591add` |
| W2/W3, +3V3 | x=102.930105-103.450643, y=102.6-103.053948 | Unknown connection from selected `7b9ecb44-46de-4045-bf08-bc653d87b57a` to `b7701ba0-84bb-4da1-8b23-ed33397a41ca` / `e73c635a-325a-4b3e-9e26-9fb7f276a98d`; the latter two share an endpoint |
| W4, +3V3 | Same local area toward x=103.703936 | Two-segment bridge via `89c50dab-ea8d-4345-bf98-2daaf1903fd9` and `01e7bbee-0ab2-4517-8e28-b104e4bfc013` |
| W5, +3V3 | x=95.908327-96.55, y about 100.2 | Direct bridge `ab6b4385-4eb0-463d-89d2-6e07090b7cf0` |
| W6, VCORE | x=96.55-97.172887, y=100.6 | Direct bridge `2a42b920-d832-4965-9e16-75461b8692cb` |
| W7, VCORE | x=103.8875-104.327108, y about 101.8 | Four-segment same-net path between reported members |
| W8/W9, D+ | x=103.45-104.22689, y about 101 | W8 direct bridge `15f417ca-96f4-48f7-9472-ddddc2f50e11`; W9 continues through `128f1901-b108-479d-97c4-fed2cdce0a2a` and `eeadea9d-2641-4ff8-b97f-b1eca1531a56` |

Two X6 NPTH holes, full edge/keepout/fill legality, current capacity and
impedance were outside that screen. Blanket `SetWidth` is not the plan.
CC2's separate In2 hole-clearance finding is not one of these 76 segments.

### CC2: one separate local obstacle, no rule relaxation

Track `689b9c2a-470e-4d4c-b020-482207c32a05`, In2.Cu, is
`(97.767685,76.971614)` to `(97.767685,80.641492)`, width 0.177978 mm.
It misses the 0.2500 mm copper-to-hole rule at X6 NPTH
`8e659786-985c-5a3b-8d6a-fd715282132b`, centre `(97.11,78.38)`;
DRC reports 0.2437 mm, a 6.3 um deficit at its displayed precision.
Plan a local track detour with margin and full neighboring-copper checks,
not a guessed 6.3 um translation, smaller hole or relaxed rule. Retain
its full connected CC2 group and both existing segment-end obligations.

## Proposed first authorization: four stop/go items

| Item | Exact objective | Deliverable and success gate | Stop condition |
|---|---|---|---|
| P1: core supply/escape viability, 15 min | VCORE, C8/C6/C7/C18 and associated IC1 terminals; the 12 VCORE width segments and +3V3 escape interfaces that constrain the same area | One complete native net/obstacle snapshot, one finite route/width candidate batch, and an exact replacement/branch-restoration contract. Demonstrate a short local C18 supply/return option or explicitly justify the existing detour; account for all VCORE terminal groups. Show legal whole-span transition sites if needed. No tiny-grid retries or automatic placement change. | No simultaneous legal supply/return access, unresolved branch membership, contact/guard conflict, or a required retained-copper/pose change. A shorter airwire alone is not success. |
| P2: flash/boot corridor viability, 15 min | All six QSPI nets between IC1 and U1, R5/R11/D3 branch and USBBOOT width package | One simultaneous six-net corridor/transition allocation, preserving flash pullup and boot behavior. Inspect fast-edge reference continuity, clock/data topology and competing USB/core escapes. Existing R11/U1 connections stay; use reachable connected copper, not six independent straight pad routes. | A single-net success strands another member, return continuity is missing, or resolving the corridor needs an unapproved placement/retained-clock change. Do not call five of six a bootable flash interface. |
| P3: USB and CC2 viability, 15 min | D+/D-, USB_D+/USB_D-, series-resistor boundaries, X6 holes and the four D+ width segments | One bounded pair/corridor proposal preserving the complete connector-to-MCU chain and service lands, with references, pair separation/length/skew and transition-return treatment. Give CC2 an exact local detour contract around the actual NPTH, preserving its terminals. | No legal pair/reference corridor at retained placement, unclear pair topology, or need to change X6/holes/retained copper. Do not fix an impedance problem by merely reaching 0.1778 mm. |
| P4: source/audio power viability, 15 min | VBAT/VBUS/VHI/V+, protected return, VAMP and amplifier output paths; +3V3 supply branches | Map source/load/return paths and exposed necks, reconcile the existing V+ service failure, and issue bounded trunk/branch replacements under existing current/drop screens. Preserve the retained boost loop and quiet pickoffs. | Required current geometry cannot fit without structural change, or budgets remain too uncertain to select a defensible conductor. Report the uncertainty instead of treating a DRC pass as ampacity. |

These are **future bounded engineering items**, not a request for another
full-board baseline inventory. With separate implementation authorization,
an exact root-reviewed proposal may be applied and checked on the derivative
inside that same item's cap; otherwise retain its geometry contract and stop.
Do not spend the entire pilot building another general-purpose checker.
Reuse one complete snapshot across compatible
items; query whole connected groups and relevant obstacles, not only the DRC
representative endpoints. Use already exercised tools with hard 30-second
static / 90-second native subprocess limits and persistent receipts. Check
argument lists before running. No child starts if its hard limit would cross
the item's execution cutoff; reserve time for root review. A native timeout
stops dependent work immediately.

The pilot intentionally precedes any paid/unbounded manual finish. If all
four contracts are credible within the cap, release their exact isolated
repair batches separately. If one needs relocation, relaxed minima, protected
copper changes or a new router job, retain the candidate and bring that single
design decision back; do not start an automatic additional experiment.

## Conditional implementation sequence and measurable exits

Only after the critical geometry fits, work on one derivative in this order.
Each row is a named work package, not a promise it fits a single execution.
Cap any execution item at 15 minutes and split at a reviewed checkpoint rather
than silently extending it. Do not accumulate a new cap for an exhausted
failure. Routine packages do not start while a critical route remains blocked.

| Order | Required work | Baseline opens covered | Completion evidence |
|---|---|---:|---|
| R1: core/rail | VCORE groups and C18 loop; IC4.12 +3V3 connection; all 53 +3V3/VCORE width subjects | 2 | Both terminal groups close, two formerly open nets complete; full width/contact and supply/return review, not just two fewer airwires |
| R2: flash/boot/reset | Six QSPI nets, R11/D3 branch, USBBOOT widths, functional reset and its TP7 branch | 9 | All flash/boot/reset terminals connected; coherent fast-edge routing/reference review; preserve clock block and access |
| R3: USB | D- closure, complete two-sided D+/D- chain, D+ width/shape, CC2 detour | 1 | All USB terminals connected, CC2 finding absent, pair/return/impedance disposition complete |
| R4: source and enable | VBAT, VBUS, VHI, ~{ENABLE}, EN, POWER; V+/VAMP/BTL quality even where already connected | 8 | Source and control groups close without private bypass; current/return/drop and local-decoupling evidence |
| R5: motion/audio | SCL/SDA/INT; I2S_DIN/LRCLK, AMP_MUTE, GAIN; SCL/BCLK widths | 8 | IMU and amplifier interfaces complete, pullups/filter/control functions preserved, clocks/references reviewed |
| R6: user/indicator/service | BUTTON/D13/charge-indicator; SWCLK/SWDIO/IMU_INT2; BUTTON widths | 6 | All remaining required terminals and recovery/test lands connected; no service deletion |
| Cross-cutting return | Four GND width subjects and all return effects of R1-R6 | 0 | Preserve GND terminal groups, every actual grounded island and both private cuts after changes |
| **Total** | **Every open net assigned exactly once** | **34** | **No inference of 34 separate physical repairs** |

The five saved dangling records are not a cleanup order. In particular,
retained GND feeder `3598d04b-1396-5df4-953b-9f195d966b71` must not be deleted.
The two VBAT vias (`0ba3129d-4c2f-51a5-b83d-47c5c587ae79`,
`bad9068e-b03b-5869-a449-cdb7731eb117`) and VBAT stub
`fde83bd5-48d4-47da-9eff-645e2cadc90e` need R4 membership/process disposition;
the V+ track `55860106-e61a-595b-bf7a-228abb7de8f5` needs its load-path context.
Neither a dangling report nor a same-net overlap proves expendable copper.

## Electrical quality beyond the open count

For this exact standard 1.1 lineage, the saved service review reports C18 to
IC1.23 at **12.041860 mm / two layer switches**, versus short zero-switch
C23/IC4.5 and C24/IC4.8 paths at 1.677271/1.759681 mm. Preserve those IMU gains,
but a connected GND net is not proof of a small local high-frequency loop.
The service's generic 10 mm bypass threshold is not a component requirement.
P1 must inspect actual native current/return topology, not call 12 mm either
automatically acceptable or automatically a placement defect.

The exact service review also reports USB_D pair length mismatch
17.152565 mm and uncoupled length 20.682254 mm, with D+/D- check errors.
These are source-bound screening results, not measurements on repaired copper.
Keep both sides of the series resistors in P3 even if one side is graph-complete:
device-side D+ is IC1.47-to-R10.2, D- is IC1.46-to-R9.2; connector-side
USB_D+ is R10.1/X6.A6/.B6/D+1.TP and USB_D- is R9.1/X6.A7/.B7/D-1.TP.
The saved 90-ohm model gives F/B width about 0.22735 mm at 0.210 mm gap,
In2 about 0.18669/0.21648 mm, and In5 about 0.18735/0.210 mm.
Use those as existing model evidence, not supplier-qualified finished
dimensions or permission to transplant one layer's geometry to another.
Preserve an uninterrupted appropriate ground reference and handle return
transitions explicitly; do not tune a long detour just to match another one.

P4 uses the [existing power assumptions](../hardware/handbell/iterations/printed-bell-routing/reports/power-routing-review.md#working-review-assumptions-for-the-next-candidate):
2 A source/return screen with a 3 A sensitivity case, 1 A boosted/audio
distribution, copper-only round-trip drop targets of 50 mV at 2 A and
100 mV at 1 A respectively, and a provisional 10 C conductor-rise target.
Use the exact eight-layer copper construction, exposed necks, vias and
parallel paths, not old two-layer route lengths or a net-name-wide current.
The service's 600 mA logic/core setting is a conservative screen based on
the upstream regulator, **not an RP2040 core-load rating**. Its VBUS 2 A
setting is not USB draw permission; 20 C IPC-2221 results do not close the
10 C/IPC-2152, transient, actual-load or enclosure gates.

## Acceptance after any future edit batch

Require the declared geometric delta and unchanged source/project bindings;
do not demand whole-board copper equality after an authorized route change.
Every previously connected terminal group must remain connected, every
targeted functional group must close, and no new foreign-net contact,
floating island, private bypass or CELL_NEG/GND join may appear. A changed
DRC airwire representative is not itself a lost connection.

Use scoped checks during candidate screening. At a coherent saved milestone,
run intended-project DRC with parity, all severities and **all track errors**;
refill/save only the authorized derivative, then compare connected groups,
guard/island/private-return evidence and all non-edit invariants. Use a fresh
report rather than overwriting baseline evidence. Any additional findings
exposed by all-track-errors mode need attribution against a same-mode
baseline; do not silently compare its count with the older default-mode 405.
Run that baseline once if required, not once per net.

For final electrical closure the targets are zero opens on every required
terminal, zero remaining below-floor new tracks, zero CC2 hole deficit, no
short/clearance/contact/guard regressions, and explicit USB/power acceptance.
The remaining process, library, silkscreen and 46 parity records still need
their own disposition. Matching 50 baseline mask records is attribution,
not manufacturing approval. Rebind final mechanical/assembly assets only
after selecting a stable electrical candidate.

Track accepted functional groups and geometry-quality defects closed per
item, actual active time and unsuccessful attempts. Do not quote an unmeasured
remaining dollar cost or use this board's 34 versus the source's 37 as proof
of cheaper completion. A completed plan is not a completed board.

## Planning evidence and execution limit

This plan uses saved reports plus read-only serialized-board extraction by
runtime-verified GPT-5.6 Sol/medium, with Astra's prioritization and source-role
corrections. There were nine executor shell/static invocations: eight exited
0 and one failed a legacy numeric-net assumption before the corrected parse.
No native operation, board/file write or cloud action occurred in extraction.
The original eight invocations completed promptly but **did not enforce the
requested hard timeout**; `initial_wait` is not a process limit. The last
boot-role read used an explicit 30-second job wait/stop handler. Preserve that
procedural limitation, not a claim of nine supervised native validations.
Do not rerun the completed static evidence to improve its accounting.

The new seven-chain result is a literal segment-connectivity observation,
not an independent pad/zone graph or a general checker qualification.
The two unresolved +3V3 relationships and all full-rule/electrical limits
remain in the future repair contract. The plan adds no native acceptance.
