# From fit mock-up to routed PCB

## September 14 all-front clock network completed locally

The [current clock revision](../hardware/handbell/iterations/printed-bell-clock-draft/README.md)
now routes the MCU XIN/XOUT network and both crystal-case/capacitor returns on
F, with no new vias or rear copper beneath the raw-negative contact base.
It applies only small Y1/C2/C3/R6 pose changes and replaces the prior local
clock segments. All nonclock copper and fixed mechanical interfaces remain.
The exact moves, native front-only paths and current hashes are in
`reports/clock-approaches.json`; the earlier rejected proposal remains history.

Matching unfilled-zone DRC changes from 86 to 82 opens, without new physical
findings. This is local routing completion, not powered clock qualification,
whole-board completion or a fresh full mechanical bind. The owner now permits
an initial attempt plus up to two corrective retries within each bounded item,
and sequential continuation after successful checkpoints.

## September 14 first local clock copper

The [isolated clock draft](../hardware/handbell/iterations/printed-bell-clock-draft/README.md)
now contains the selected crystal/capacitor definitions and a first increment of
15 F-side tracks. It connects the crystal, load capacitors and R6 locally, plus
initial ground links, without moving components, adding vias or changing any
existing copper. MCU XIN/XOUT approaches and final case/capacitor returns remain
unfinished. The native detail image and exact track inventory accompany the draft.

The resumed DRC works with an initialized isolated KiCad configuration; the
normal user configuration still timed out. Matching **unfilled-zone** checks
show 92 to 86 unconnected items, not a comparison with the older 59-item
filled-zone recovery. Four inherited USB clearance errors and three newly
identified Clock footprint/library mismatch warnings remain, alongside
silkscreen/text findings. The routing increment adds no new physical findings.
The subsequent bounded definition item resolves those three warnings by
explicitly marking the two libraries and three instances as SMD. Their implicit
assembly classifications differed; no pad geometry or copper changed. All other
findings and the 86-item count persist. MCU approaches/returns are next.

The first all-front MCU/return proposal was then **blocked before writing**:
its C3 move leaves approximately 0.1764 mm to an existing `+3V3` track, below
the 0.1778 mm minimum. The experiment and exact obstacle are preserved in the
clock draft's `reports/clock-approaches-blocked.json`. The accepted board is
unchanged; later proposed routes are not proven. Stop this exhausted-retry
item rather than broadening the move/routing search.

The owner now explicitly authorizes starting the next ready bounded item after
each successful published checkpoint. Retain the per-item time/retry limits
below; stop promptly on a pause request or concrete blocker.

This is not a manufacturing release or an updated full mechanical binding.
The definition-only `702f53b` stage and original recovered copper remain
preserved. No background routing task is running.

## September 14 bounded restart

The owner cancelled the long-running routing agent and requests small,
reviewable work items instead of another open-ended completion task.
The post-cancellation working checkpoint has **1,124 tracks, 87 vias and
59 unconnected items**. Its PCB SHA-256 is
`2d88301f48ad05dc01384b90111f16615f176a7f4704eab82a1e3560ef5c8bc0`;
placement SHA-256 is
`404a8c53dc0ce28f8769ec4a1926452564cbd3cd5f8c27d95b7ac2ebee1b55de`.
A separate private recovery copy preserves the final saved files. The
candidate remains incomplete and does not include all later part decisions.

For this restart, use **one foreground work item per turn**, without
background routing agents. Aim for 10-15 minutes per item; stop earlier when
the item is done or a blocker appears. Give commands explicit finite timeouts.
Allow at most one corrective retry within that budget, not a search/routing
loop. Report exactly what changed and what remains; publish accepted coherent
checkpoints before moving to another subsystem. A timeout or incomplete
result ends the item rather than authorizing a larger task.

| Next bounded item | Scope and stopping point |
|---|---|
| Restart baseline | Confirm cancellation, preserve the final saved checkpoint and explain the selected clock change. No routing regeneration. |
| Clock definitions and placement | Only Y1, C2/C3 and the necessary case-ground connections; retain R6 and D43. Apply the selected schematic/footprint definitions and inspect local fit. Stop if an unrelated move or wider redesign is needed. |
| Clock copper | Route only the oscillator/load-capacitor cluster and its returns; disclose any remaining opens. No USB, power-stage or whole-board routing in the same item. |

Subsequent USB, power and remaining-signal items must likewise name a small
set of references/nets and an explicit stopping point before starting.
Distinguish actual connectivity/clearance defects from departures from a
manufacturer's example land pattern; the latter require a reasoned
disposition, not an automatic global footprint redesign.

### Why the clock selection differs from the Adafruit source

No failure of Adafruit's clock circuit was demonstrated. The pinned source
records Y1 as **12 MHz / 12 pF, 2520**, with **22 pF C2/C3**, but an exact Y1
manufacturer orderable had not been established for our sourced assembly BOM.
A purchasable 2520 candidate had 150 ohm maximum ESR; that does not prove it
would fail, but it is not automatically equivalent to the original part.

The explicit project choice is instead the Raspberry Pi RP2040 guide's
tested **ABM8-272-T3**, 12 MHz with 10 pF specified load and 50 ohm maximum
ESR. This is a sourcing/reference choice, not evidence that Adafruit required
a redesign. The **15 pF C2/C3** values follow that different load requirement:
the two capacitors contribute approximately their series combination, plus
layout/pin stray capacitance. They are a matched oscillator-network change,
not an independent capacitor upgrade. R6 remains 1 kohm.

The [clock-source decision](device-component-selection.md#selected-clock-reference-revision)
records the larger 3225 footprint and manufacturer evidence. Its sourcing
is complete; native application is still pending in the recovered board.
Neither copying Adafruit nor using the Pi reference eliminates startup,
frequency and drive evaluation on our actual layout and low-battery supply.

**September 13 authorization:** the owner approves the
[printed-bell/front-electronics direction](printed-bell-revision.md) and
permits critical routing after coordinated engineering interface review,
without another owner viewing turn. The all-front D43 placement and complete
D70 printed assembly now retain the original PCB M2/USB/contact datums.
The earlier stage-1 PCB remains an immutable unrouted checkpoint. The separate
power-rework candidate now has a fresh exact mechanical bind; every subsequent
electrical change still needs its own current-source bind.
This does not close the power, USB land-pattern, actual cell/contact,
manufacturing or physical qualification gates below.

**September 13 power-review result:** the first separate routing checkpoint
has real copper but is incomplete. Its
[independent power review](../hardware/handbell/iterations/printed-bell-routing/reports/power-routing-review.md)
requires a short, broad F-side boost output-capacitor loop and an intentional
protector-sense pickoff that is not shared with load-return routing. These
corrections take priority over preserving the initial local placement or
adding more signal routes. A separate candidate may change the local
boost/protection-sense poses while retaining the D43, face, mount, USB and
contact interfaces; it needs a fresh exact mechanical bind before acceptance.
The review records provisional current/drop/copper assumptions, not a
thermal or manufacturing approval.

**September 14 milestone:** the
[power-rework package](../hardware/handbell/iterations/printed-bell-power-rework/README.md)
implements the F-side output loops and independent R26 pickoff. Its ten
recorded pose changes and conservative U1/U6 envelope enlargements fit the
complete regenerated assembly without changing the shell or fixed interfaces.
There are still 155 unconnected items, including the main Q1-to-boost feed;
power budgets, full routing and ground spreading are not closed. The
[USB qualification finding](usb-connector-qualification.md) adds an actual
lost-slot import correction, not merely an existing DRC disposition.

**September 11 owner-requested checkpoint:** implement and inspect the
[measured-shell T8 integration](t8-integration-plan.md) before starting copper.
The owner confirms the previous cartridge fits and has supplied new shell
stations, but wants the complete revised FreeCAD assembly first. The new
cell/contact/protection, smaller-flash footprint, USB and service interfaces
must be represented together; the old wing manifest cannot certify them.

The separate [83-part native T8 placement](../hardware/handbell/iterations/t8-protected-draft/README.md)
now supplies the new flash, contacts and protected return. Its
[electrical review](t8-electrical-revision.md) keeps the low-cell current
tradeoff and missing reverse-cell/temperature charging functions explicit.
These are draft engineering inputs, not closed safety gates. The
[coordinated T8 cartridge](../mechanical/studies/2026-09-11-t8-cartridge/README.md)
binds that exact placement into the full assembly. Owner review of the
6.25 mm mouthward shift and resulting exterior, actual contact/cell fit, USB
access and service arrangement still precedes routing.

**Preserved September 9 iteration:** the [two-face wing/cartridge handoff](electromechanical-wing-iteration.md)
and [native wing placement](../hardware/handbell/iterations/wing-draft/README.md)
record the separate 62F/11B candidate, mounting interfaces and current gates.
The earlier 0.2 print checkpoint below remains preserved, not overwritten.

**Historical 0.2 stopping point: print-fit and floorplanning, not Gerbers.**
The 0.2 PCB contains real footprints and correct pin/net assignments, but no
tracks, vias or ground planes. Its ratsnest lines show required connections;
they are not copper and do not demonstrate a usable current-return path.

The 40 mm speaker arrived and was measured on **2026-09-09**. The owner printed
the existing parts in PLA on a Creality K1C: the populated-PCBA proxy was good
and could fit relatively deeply, while some unspecified other pieces were
flimsy. No insertion depth/orientation was reported. Keep the original 43 mm
placement manifest fixed for that print snapshot; later electrical placement
changes must regenerate the populated-board mock-up rather than silently
diverge from it. See the [measured follow-up](../mechanical/studies/2026-09-09-measured-speaker/README.md).

**Orientation alternative, not a changed print:** the owner prefers the
populated face toward the speaker and handle-side space for a cylindrical
cell, using PCB contacts (through-hole or SMT) and a printed capture cradle
without battery wires. The [mechanical alternative](mechanical-feasibility.md#2026-09-07-speaker-facing-electronics-and-cylindrical-cell-alternative)
records the current cell-only screen and unclosed speaker/retention gates.
The original inward-component fit files are unchanged.

## What can proceed now

Review and refine critical placement against the actual RP2040, MAX98357A,
LSM6DSOX and TPS61023 reference layouts and manufacturer guidance. The current
packing optimizer does not enforce bypass distance, switching-loop geometry,
feedback isolation, thermal spreading or USB impedance. Those constraints take
priority over preserving its neat arrangement.

| Circuit | First layout work |
|---|---|
| RP2040 core | Put each bypass at the relevant supply/return pins; keep crystal/load-cap and QSPI routes short and coherent |
| TPS61023 | Review the VIN cap, inductor, switch node, output caps and ground as a coupled placement; use a quiet feedback return and avoid routing feedback alongside BOOST_SW |
| MAX98357A | Keep supply bypass and high-current returns local, provide the required thermal connection, and route both BTL paths deliberately |
| USB | Retain connector pad mapping and series/CC circuitry; route D+/D- as a short pair with a continuous reference, using the chosen fab stackup for geometry |
| IMU | Keep local supply bypasses close and establish physical axis orientation; avoid heat, switching-current bottlenecks and mechanically stressed attachment points |
| Ground/test access | Aim for a continuous return plane, not reflexively split audio/digital ground; place service pads without needlessly cutting that plane or blocking carrier access |

Do not choose arbitrary trace widths for VHI, V+, VAMP, BOOST_SW or the BTL
paths just because a default rule permits them. Establish copper weight,
maximum current, temperature rise, voltage drop and return geometry first.
The feedback net is a sensing connection, not part of a high-current route.

## Gates before committing to final copper

| Gate | Needed evidence |
|---|---|
| Board/carrier interface | Inert print fit, insertion/removal sequence, USB slot/load path, PCB support locations and usable service access |
| Actual speaker | Owner measured D40/H19, D32 basket rear at z12 and now D21.70/H7 magnet; intermediate basket/rim detail, terminals, wire exits, vent, excursion and tolerance remain open |
| Battery | Suitable current/charge ratings and reviewed protection, either on the cell or the instrument PCB; model complete contacts/capture/insulation, reverse-insertion handling and service access. The T8 candidate is unprotected, and boost protection alone does not satisfy this gate |
| Boost parts | Exact inductor and capacitor MPNs, land patterns/heights, saturation/thermal current and effective capacitance; settle the C29 DNP/compensation decision |
| Connectors | Mated body and cable-bend envelopes, polarity/retention/current ratings, and USB manufacturer land-pattern review |
| Power policy | USB input budget, charge/play policy, low-cell cutoff/protection and startup/mute/brownout behavior |
| Fabricator | Actual layer/copper/stackup rules, copper-edge/drill/mask constraints, component assembly support, fiducials and panelization requirements |

The four USB hole-clearance findings remain an explicit gate. Do not lower the
0.25 mm rule merely to hide source clearances of 0.1755/0.2144 mm. Select a
justified manufacturer/fab-compatible footprint solution and rerun the review.

Provisional core routing can begin after the first electrical floorplan review,
without waiting for finished application firmware. It is still rework-prone
until the mechanical and power footprints above are fixed. The present print
snapshot is therefore a deliberate checkpoint, not a claim that all layout
inputs are frozen.

## Routing and manufacturing sequence

1. Freeze the next reviewed placement/keepouts, while retaining the 0.2 fit
   snapshot as history.
2. Route the critical power/return, clock/flash and USB structures with
   appropriate constraints; then complete I2S, IMU, control and service nets.
3. Fill/review ground and thermal copper, then inspect disconnected islands,
   return detours, clearance, silk, polarity and assembly access.
4. Resolve DRC and schematic-parity findings and perform an independent layout
   review. Re-export the populated mechanical model and revisit fit.
5. Export matched Gerbers and plated/nonplated drill data from that revision,
   inspect them in a Gerber viewer, and package the intended fabrication files.
   A populated-board order also needs a sourced BOM and checked placement/CPL
   data; Gerbers alone do not describe the assembled components.

The JLC desktop application is a useful next preview/quotation step once that
package exists. Successful upload or a rendered board preview is not electrical
approval. **No manufacturing Gerbers are issued from this unrouted snapshot,
and no order or assembly submission is authorized by this document.**

## Printing scope

Use the [mechanical handoff](mechanical-feasibility.md) for the actual files and
their readiness. Requested fit artifacts are a populated-board proxy, inert
battery blocks, carrier/grille parts and speaker dummies in STEP/STL form.
The board proxy must remain connected/printable without pretending its boxes
are exact manufacturer bodies.

For the speaker, distinguish an illustrative stepped/basket shape from the
**40.9 mm diameter x 18.5 mm deep conservative envelope**. The historical image specifies frame 40.5 +/-0.4 mm, magnet 22 +/-0.5 mm,
overall depth 18 +/-0.5 mm and rim 2.7 +/-0.3 mm. The arrived speaker's **19 mm**
reported depth supersedes that earlier 18.5 mm gauge for current fit work.
The new study separates owner-measured stations from assumed straight basket
interpolation and from a stepped body envelope. Terminals, vent and tolerances
are still unknown; do not treat an interpolated shape as a measured full profile.

Import in millimetres at **100% scale**. Start with the slicer's established
K1C/PLA profile rather than invented temperatures or speeds. Measure a printed
gauge with calipers; small features and first-layer expansion can bias fit.
Some 0402-sized details may not reproduce faithfully with a typical nozzle.
PLA dummies are for handling and geometry only, not electrical, acoustic,
load-bearing or battery-temperature qualification. Never force a live pouch
cell into a tight fit test.
