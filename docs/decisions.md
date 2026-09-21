# Decision log

Planning snapshot, updated 2026-09-11. A provisional choice is a starting point for
experiments, not a final component or manufacturing commitment.

| ID | Decision / question | Current disposition | Evidence to close or revisit |
|---|---|---|---|
| D01 | Repository continuity | Retain the existing public `dcuccia/digital-handbell`, history, MIT license, 2023 notes and diagram | New planning and linked execution issues |
| D02 | Integrated baseline | Prefer Adafruit 5768 for first bench work and schematic derivation | Audio/motion/power experiments and import review |
| D03 | First MCU/runtime | RP2040 + CircuitPython provisionally preferred; no first-revision wireless requirement | Latency, audio/memory, idle/wake and USB workflow evidence |
| D04 | Sensor | Owner approved LSM6DSOX on 2026-09-07; integrated at 0x6A in the separate draft; retain LIS3DH for bench comparison | Gyro-enabled/disabled gesture comparison, driver initialization, full electrical review, and assembled BOM quote |
| D05 | CAD | KiCad 10.0.6 exercised; three pinned references converted; reduced draft has 0 ERC errors/warnings with no exclusions | Complete footprint/routing review and electrical freeze remain open |
| D06 | Hardware reuse license | Retain source-compatible CC BY-SA 3.0 for adaptations of verified sources; preserve root MIT for original code/docs | Full notices and per-file provenance at import; resolve 4884 version before use |
| D07 | Packaging | Preserve the original print snapshot; separate 43 mm wing draft uses speaker-facing electronics, selective rear boost/audio groups and two M2 mounting interfaces | Actual cell/contact/cartridge fit, real-shell tolerances, insertion/service path and routing-led placement |
| D08 | Audio rail and quiet idle | TPS61023 5 V-class boost and independent GPIO20 mute implemented in 0.2; mono-left selection and initial 9 dB gain | Exact power parts, rail budget, noise, low-cell behavior and sequencing remain unqualified |
| D09 | Cell and charger | Owner requests a Vapcell T8 button-top contact/capture revision with compact PCB-level protection; retain >=2 A continuous screening plus transient margin; no live-cell approval | Exact supplied dimensions/button, contact load/travel, complete charging/protection/temperature/USB behavior, reverse insertion and mechanical capture |
| D10 | Play while charging | Unresolved; must be explicitly permitted or prevented | System power-path/input-current and charging/temperature evidence |
| D11 | Speaker and cavity | Arrived EK1794 D40/H19, basket rear D32 at z12, updated magnet D21.70/H7; September 11 measured shell stations and owner-assumed uniform 1.15 wall govern new work | Inconsistent raw OD/ID versus wall readings preserved; intermediate/final taper, terminals/vent, tolerances, full-stack retention, power and acoustic behavior |
| D12 | USB and mounting | Separate two-piece body/yoke draft integrates grille, speaker seat and PCB supports for external preassembly; no battery retainer or shell attachment implemented | Shell attachment, supported USB load path, service access, bearing/preload, hardware, retention and isolation |
| D13 | Musical behavior | Note range, tuning, fixed/selectable note, retrigger/damping/polyphony and controls open | Requirements and prototype comparison |
| D14 | Fabrication/assembly | Evaluate JLC Standard two-sided for the wing draft: Economic is single-sided and the selected IMU listing is already Standard Only; OSH Park remains a bare-board alternative | Actual job/BOM eligibility, framing/panelization, DFM and complete quantity-specific quote |
| D15 | Wireless exploration | Owner favors S3-MINI; evaluate early for sound programming, QR identity and optional practice telemetry | Exact memory/build, RF with real shell/cell/speaker, power budget and protected updates; local sounding remains offline |
| D16 | RP2040 flash capacity/sourcing | Owner requests stocked 2 MB W25Q16JVUXIQ TR for the next draft; new USON2x3 footprint, not a drop-in for inherited USON4x4 | Reviewed lands/paste, exact boot configuration, filesystem/audio budget and read/write/cold-boot evidence |

For a change, append date, rationale, alternatives, affected requirements,
upstream/prototype evidence, and the deciding issue. Do not overwrite an earlier
decision's rationale as if the new choice had always been established.

## 2026-09-07: precursor scope and CAD readiness

The owner clarified that the 2023 wireless/6-DOF work is a precursor vision,
not a binding requirement for the current instrument. Preserve it as history
without treating every earlier feature as mandatory.

D05 advances from a recommendation to an exercised toolchain: KiCad 10.0.6,
standard libraries, native schematic/PCB import, schematic PDF/netlist exports,
and ERC execution. All 71 nonempty upstream board-signal pin groups match the
imported schematic after accounting for six reference-name conversions.
The initial import still has 50 ERC findings. The
[reference report](../hardware/reference/adafruit-5768/README.md) records the
limits; this is not schematic approval or a handbell design release.

## 2026-09-07: six-axis motion recommendation

D04 originally proposed LIS3DH-first evaluation on the stock reference. With
the explicit strike **and chest-stop/rest** requirement, recommend LSM6DSOX
(Adafruit 4438) as the derivative's primary candidate. It adds angular-rate
evidence through a straightforward, inspected CircuitPython I2C driver and
has clear CC BY-SA 3.0 hardware provenance. The owner allows approximately
$1-2 sensor-related BOM increase when capability justifies it.

Retrieved LCSC sensor-only deltas were about $1.67 at ten or $1.39 at 100;
assembled-board cost remains unquoted. JLC's candidate listings were
Standard-only/Extended with X-ray requirements, so assembly economics must be
revisited for the whole BOM. LSM6DS3TR-C is cheaper in the retrieved channel but
has unresolved hardware-license scope and distributor lifecycle descriptions.

Use a temporal stroke/return/settle classifier before considering on-chip ML.
Neither accelerometer nor gyro identifies actual chest contact with certainty.
The [motion decision](motion-sensing.md) records sources, current API units,
bench wiring, alternate interactions, and evidence gates. No sensor substitution
has been made to the imported reference.

## 2026-09-07: owner approval and schematic integration

D04 advances from recommendation to owner-approved **LSM6DSOXTR**. The
[0.1 schematic draft](../hardware/handbell/README.md) replaces IC4's LIS3DH with
the actual 4438 symbol/footprint and ST Mode 1 connections. It retains the
shared 10 kohm I2C pull-ups, adds one local 100 nF bypass at each supply,
keeps INT1 on GPIO22 and exposes INT2 at TP6 only. No duplicate regulator or
breakout level shifter is added. The old references remain unchanged.

The [ERC record](../hardware/handbell/reports/erc-review.md) disposes of every
original finding, including incorrect imported power-pin semantics and dangling
wire tails. TP4/TP5 make SWD access explicit. All 76 non-sensor components retain
their values, footprints and connection topology. The source `1.2V` name is
changed to `VCORE` without a circuit change; the RP2040 reset nominal is 1.1 V.

Source review also found the pinned CircuitPython `_i3c_disable` descriptor
redefinition documented in [motion sensing](motion-sensing.md). Correct/read
back CTRL9_XL before bring-up. No firmware or physical-hardware outcome is
claimed. E02/E04 remain open, especially for full import/footprint review,
peripheral reduction, cell/power/audio choices and independent signoff.

## 2026-09-07: approved compact power and cartridge direction

The owner approved removing STEMMA QT in favor of a two-pin GPIO19 button
harness, independent amplifier mute/channel review, compact service access,
simple charge/status indication, and a printed cartridge plus grille.
Headers/servo/RGB branches are no longer desired expansion features.
These changes are recorded for the next revision; **the 0.1 CAD is unchanged**.

D08 advances from an unboosted study to a requested **3 W high-end electronics
scenario into 4 ohm**, not 3 W clean output or speaker qualification. Compare
PowerBoost 1000 Basic with the substantially smaller TPS61023 source block.
Inspecting the latter found 732 kohm/100 kohm feedback (approximately 5 V)
despite its 5.2 V prose. Resolve the rail explicitly, preserve tight power-loop
layout, and review exact magnetics/capacitors rather than calling WE-MAIA a
drop-in. Neither source is a charger.

D09 remains pack-specific: 500 mAh capacity does not imply a 0.5 A limit.
The full-output scenario needs about 0.90-1.42 A for audio alone across the
illustrative voltage/efficiency range. Prefer a suitably rated factory-protected
pack over improvised cell paralleling. Charge-and-play remains undecided.

D07/D11/D12 now use the owner's B01EABRWO6 shell estimates: 70 mm lip ID,
40 mm at an unspecified taper station, 44 mm body height and 85 mm handle
height. A retail 40 mm-speaker drawing gives a 40.9 mm maximum frame and
18.5 mm maximum depth. Its seller rating conflict is unresolved. Study an
offset/annular near-mouth PCB and removable printed cartridge before enforcing
a small disk behind the magnet. The hypothetical z=22 mm taper is explicitly
not a measured profile.

D15 permits early S3-MINI RF/firmware experiments before shared-carrier freeze.
Sound programming comes first; asynchronous practice telemetry is optional,
and local ringing must not depend on connectivity. Keep stable QR identity
separate from note assignment and authentication. Exact memory variant and
interpreter update strategy remain open.

Evidence, assumptions and next gates are in the
[power/fit review](compact-power-and-packaging.md) and
[mechanical screen](mechanics-and-manufacturing.md). Owning epics:
E01/#1, E04/#4, E05/#5, E06/#6, E07/#7 and E12/#12.

## 0.2: implemented reduction and revised axial assumption

The owner requested electrical reduction and actual-footprint placement/FreeCAD
feasibility, explicitly assuming 50 mm ID at z13 tapering linearly to 34 mm at
z43. Near the opening, the approximately flat first 5 mm and curved transition
remain adjustable. This is a working profile, not a measured tolerance model.
The earlier hypothetical 40 mm-at-z22 screen is superseded.

The [0.2 handoff](electrical-reduction-and-placement.md) implements the approved
reduction, TPS61023 boost, GPIO20 mute, filtered GPIO19 button harness and
distinct speaker connector. Copper recovery/debug access replaces large
headers and physical service switches. C29 remains DNP pending effective
capacitance/compensation review; no cell is selected. Reference copper semantics
were corrected only in documented derivative footprints, without suppressing
the unresolved USB hole-clearance findings.

The 43 mm candidate has 74 fitted top-face parts, 18 reverse copper features and
one DNP provision, with no routing. Its inward-facing component choice is a
feasibility alternative to the original outward-facing preference, not a
silent requirement change; assembly, LED visibility and service access must
be demonstrated. E04/E05/E07 remain open until their broader acceptance gates
are met. The mechanical handoff records the separate STEP/STL fit study.

## 2026-09-07: orientation clarification and wire-free cell capture

The owner clarified the desired next packaging alternative: electronics toward
the speaker, with handle-side space for a cylindrical cell and its retention.
Prefer PCB contacts plus a printed capture cradle without battery wires;
through-hole and SMT are both acceptable. Compare a mechanically fixed
commercial CR123A holder on total cost and fit. No cell or contact is selected.

The [mechanical alternative](mechanical-feasibility.md#2026-09-07-speaker-facing-electronics-and-cylindrical-cell-alternative)
records the cell-only 16340/18350 screen, speaker conflicts, contact mounting and
electrical safety gates. The initial positive compact-16340 result does not
include mounting/tolerances or qualify its discharge capability. A populated
face toward the speaker must be re-placed against the real speaker profile;
it is not a geometry-only flip of the existing layout.

The owner has begun printing the original fit kit and identifies this as a
thought experiment. Preserve that snapshot and its hashes; this update changes
planning only, not the schematic, native PCB, manifest or STEP/STL/FCStd files.
Affected decisions: D07/D09/D12; owning epics E04/#4, E05/#5 and E07/#7.

## 2026-09-09: arrived speaker and physical print feedback

The owner measured the arrived speaker: 40 mm frame OD, 19 mm front-to-magnet
rear depth, 32 mm basket rear OD at 12 mm from the front, and a 22 mm diameter,
7 mm tall magnet. The [input record](measurements/shell-speaker-inputs.json)
preserves these separately from the historical retailer dimensions. The old
18.5 mm-deep speaker gauge is too short for this measured part.

The owner reports that the populated-PCBA proxy print was good and could fit
relatively deeply. No insertion depth or tested orientation was supplied; this
does not replace the assumed shell taper. Some unspecified other parts were
flimsy. Record that feedback without labeling any particular rail/grille as a
confirmed failure or claiming that a stronger carrier has been delivered.

The [separate measured-station study](../mechanical/studies/2026-09-09-measured-speaker/README.md)
preserves the earlier artifacts and compares a rigidly flipped, unchanged
placement at six depths. No tested depth has the illustrative 0.5 mm nominal
speaker-body gap; moving the board inward also consumes cylindrical-cell space.
L1, J1 and the existing wired-battery connector X1 are key floorplanning
constraints. A wire-free cell design should not retain X1 by default.

D09 continues to compare compact protected 16340 and flat-pouch options. The
owner considers 16340 economical and requested particular attention to SMD
contacts, supplying Keystone 54 as a through-hole example. Through-hole remains
acceptable. [Contact research](battery-contact-options.md) must distinguish
part/drawing evidence from approximate price, bare-cell clearance and complete
clip/cradle fit; no battery/contact is selected.

Affected decisions: D07/D09/D11/D12; owning epics E01/#1, E04/#4, E05/#5 and
E07/#7. The next mechanical floorplan must respect the measured magnet,
electrical power-loop/bypass constraints and independent structural capture.

## 2026-09-09: selective rear wings and integrated supports

The owner requested a draft placement iteration that considers two-sided
assembly, especially its cost-tier implications, and larger parts on the
battery-free back wings. The owner also proposed ground-assigned through holes
for stronger standoffs and fewer separate printed pieces, while retaining a
workable speaker loading path.

The [wing draft](../hardware/handbell/iterations/wing-draft/README.md) keeps
62 fitted components on the speaker-facing F side and 11 on B, with a central
battery/contact reservation and USB through-board-anchor exclusion. X1 is
consistently DNP; this is not a completed replacement battery interface.
MH1/MH2 use stock plated 2.2 mm bores and 4.4 mm GND-assigned copper pads.
No trace/plane means those pads are not yet physically grounded.

The [electromechanical handoff](electromechanical-wing-iteration.md) records
the shared interface, delivered two-piece body/yoke and final-layout gates.
The D72 external flange registers at the assumed D70 mouth; it is not
shell attachment. Speaker insertion precedes the yoke and PCB. Nominal
component/yoke and structure/shell gaps around 0.25-0.35 mm remain tolerance
gates, and no retained battery is supplied. Factory
two-sided assembly and an inexpensive manual-completion alternative must be
compared on the actual job/BOM, not assumed equivalent from PCB layer count.
Do not make unsupported source-rotation, strength, insertion or cell-fit claims.

Affected decisions: D07/D09/D12/D14; owning epics E04/#4, E05/#5, E07/#7 and
E08/#8. No previous baseline or printable model is silently replaced.

Official JLC capabilities retrieved September 9 confirm Economic single-sided
and Standard single/double-sided component placement, independently of copper
layer count. C481766 (selected SOX) is currently Standard Only with required
X-ray; no whole-job quote/approval is inferred. The dedicated September 8
price table's setup+stencil subtotal rises from USD33.77 to USD67.54 for
Standard one versus two faces. The [cost/source record](electromechanical-wing-iteration.md#assembly-cost-is-a-decision-gate-not-a-reason-to-stop-drafting)
also retains Standard's framing/minimum-manufacturing-size gate and conflicting
older FAQ manual prices. No assembly order or file submission was made.

## 2026-09-10: smaller flash and authorized-distributor availability

The owner narrowed the lower-end RP2040 storage use case to one or a few
approximately five-second chimes and requested 2 MB / 4 MB near-drop-in
parts at major distributors. The [sourcing record](flash-sourcing.md) finds
stocked DigiKey alternatives, but not an immediately stocked 4 x 4 mm
near-drop-in: W25Q16JVUXIQ TR is 2 x 3 mm; MX25L3233FM2I-08G is 200-mil SOP.
Verified USD offers were retrieved through a regional DigiKey site, not a
US-address checkout. Mouser live stock could not be verified.

Winbond XGIQ parts are the near-footprint candidates, with matching nominal
terminal pitch/overlap and permission to ground the center pad; their
center-pad/paste/tolerance treatment still requires approval. No hardware,
placement, fit-print artifact, BOM selection or purchase is changed.

Pinned CircuitPython source supports the Winbond density families and the
Macronix family. RP2040 capacity detection is dynamic; density reduction alone
does not establish a UF2 incompatibility. Exact boot/QE configuration and
real filesystem/audio behavior still require review. The prior out-of-stock
8 MB candidate price is not a required flash cost.

Affected decisions: D03/D05/D16; owning epics E04/#4, E06/#6, E07/#7 and E08/#8.

## 2026-09-11: measured shell, T8 integration and owner review before routing

The owner confirms that the September 9 print iteration fits inside the bell
but is slightly small radially, and supplies
[new caliper measurements](measurements/2026-09-11-shell-speaker-inputs.json).
The first concave taper ends at z14.90, not z10 or the old assumed z13.
The final taper starts at approximately z41.75 with OD38.42; the speaker
magnet is now measured as D21.70. Other September 9 speaker stations remain
current. The owner explicitly requests a uniform 1.15 mm working wall,
despite the differing apparent thicknesses from the raw diameter pairs.
Keep those discrepancies visible and distinguish measured IDs from the
calculated upper ID36.12 and interpolated curves.

The owner requests an integrated contact/capture design around the unprotected
Vapcell T8 and the stocked 2 MB Winbond USON2x3 option. Compact whole-cell
protection is part of the electrical revision under review; the suggestion
of relying only on the boost converter is not adopted because battery-rail
shorts, other loads and cell overdischarge are outside its protection scope.
Cell versus board grounding, insulation from the metal bell, reverse
insertion and charging policy must be explicit. Neither this decision nor
the quoted cell price approves purchase or live-cell use.

D12 advances to a request for positive, reversible cartridge attachment,
insulating battery capture, and supported USB access biased toward outside
flush mounting where the footprint and service path permit. The old holes
were M2 clearance/heat-set-insert provisions, not M3; choose coherent hardware
and explain it in the new handoff rather than enlarging holes indiscriminately.
Reduce the magnet-opening play using a declared print allowance, not an
invented measurement tolerance or an unspecified interference fit.

The [integration plan](t8-integration-plan.md) requires a complete placed
FreeCAD assembly for owner review **before committing to routing**. Preserve
the old native projects and print files as snapshots, and bind the new
mechanics to the exact revised electrical placement. The remaining power
parts, USB land-pattern, manufacturing and physical qualification gates are
not closed by successful model generation.

Affected decisions: D07/D09/D11/D12/D16; owning epics E01/#1, E04/#4,
E05/#5, E07/#7 and E10/#10.

### Implemented review alternative: four-piece protected-T8 cartridge

The [coordinated model](../mechanical/studies/2026-09-11-t8-cartridge/README.md)
uses the exact 83-part T8 placement, D22.1 magnet opening, D75.5 external flange,
four printed structural pieces and M2x6 captive-nut joints rather than the
old unselected heat-set inserts. Two separate insulating shell fasteners and
a mouth-open USB slot permit proposed whole-cartridge withdrawal; USB solder
anchors are not the intended shell load path.

Full contact/guard geometry did not fit at the original axial placement.
The bounded study selects a **6.25 mm mouthward translation** with a 1.0 mm
plastic target and 0.10 mm nominal clearance. Speaker front becomes z-6.25
and grille front z-10.75. This is an engineering review alternative, **not an
owner-approved exterior**. Neither thinner undocumented insulation nor clipped
contact solids are used to hide the initial conflict. The initial model and
the 1.5/2.0 mm alternatives remain available as evidence.

The owner's approximate 1 mm spare-space observation remains a visual estimate.
The fit report includes 0.5/1.0 mm speaker-fixed spacing sensitivities without
silently changing released component heights or support/USB interfaces.
Positive nominal CAD gaps do not qualify cell dimensions, contact force,
wrapper abrasion, reverse insertion, thermal behavior or physical retention.

## 2026-09-13: original printed shell and front-face electronics

The owner reports that the prior inert pieces fit/work well and now approves
a single-piece printed cosmetic shell, removable flush grille/cartridge and
separate black handle, with a wooden option later and no broad handguard.
The [dated input contract](design-inputs/2026-09-13-printed-bell.json) records
that authorization and the supplied images' limited role as generic visual
inspiration, not traced geometry or licensed assets for redistribution.

The [new native electrical floorplan](../hardware/handbell/iterations/printed-bell-front/README.md)
fits 81 electronic parts on F plus two B-side contacts without increasing the
43 mm PCB body. The original M2 mounts and USB/contact datums remain intact.
Rear SMT contacts still require assembly operations, and the old IMU tier
restriction is not erased by changing component faces.

The [new mechanical model](../mechanical/studies/2026-09-13-printed-bell/README.md)
uses an original D70/H55.8 shell and 80 mm handle. It preserves the successful
cartridge architecture but eliminates the broad exterior skirt. Three
front-accessible M2x8 joints secure the cartridge; an internal-keyed M4x16
screw/washer/metal-nut joint secures the handle. This is the working compact
metric choice, not a qualified wood joint or interchangeable 8-32/1/4-20
hardware. Shell nut pockets retain closed exterior skin; the modest USB
front opening is supported by a real lip/skin and a removable channel filler.

The owner authorizes unattended critical routing once coordinated engineering
review establishes stable PCB interfaces. The exact all-front assembly now
supports that release without waiting for another viewing turn. Preserve the
stage-1 checkpoint and rebind the mechanical model after copper-only changes.
This is not an electrical-rule waiver, complete routing, fabrication order,
qualified silk-PLA structure or live-cell release.

The [material/fastener source review](printed-bell-material-and-handle.md)
records the manufacturer's actual silk-PLA ranges and unexercised fine-layer
starting settings. Contact height and the under-cell insulation are retained;
removing a floor is not a demonstrated 1-2 mm height saving. Polarity and
rechargeable-chemistry guidance remain necessary, including within a plastic
outer shell.

Affected decisions: D07/D09/D11/D12/D16; owning epics E04/#4, E05/#5, E07/#7,
E08/#8 for eventual supplier/process comparison and E10/#10 for qualification.

## 2026-09-13: routing-led power corrections

The owner requests incremental commit/push checkpoints and particular care
with high-current routes. The initial routed candidate is preserved as
`b63a121b1ca990a64b00f231a85dd715126319af`; its
[independent review](../hardware/handbell/iterations/printed-bell-routing/reports/power-routing-review.md)
requires correcting the boost output-capacitor hot loop and shared protector
sense pickup before freezing the power layout. No trace-overheating failure
was demonstrated, and nominal neck records are not equivalent to isolated
full-current bottlenecks where broad copper overlaps them.

Proceed with a separate power-first candidate under the existing unattended
engineering authorization. Local boost and protection-sense poses may change
for these corrections; preserve D43, all-front electronics, the actual
mount/USB/contact interfaces, circuit/net/pad identities, L1's full height
and the older packages. A new placement must receive its own exact mechanical
rebind. Wider remote traces/vias alone are not a substitute for fixing the
boost's fast-edge loop topology.

The review's 2 A cell/1 A 5 V screens, copper-only drop budgets and nominal
35 um copper are provisional engineering targets, not qualified current
ratings. Temperature-rise, minimum finished copper/plating, component/fault
limits and assembly processes still require evidence. Prefer paired supply/
return paths and local spreading before consuming area with more signal
routing. Two layers remain the next attempt; no need for four layers or a
larger board was established.

Affected decisions: D05/D08/D09/D14; owning epics E04/#4, E05/#5 and E07/#7.
No purchase, fabrication, live-cell or child-use release is authorized.

## 2026-09-14: sourced Q3 replacement and clock-reference direction

Under the existing engineering authorization, select **DMP2045UFY4-7** for
the new quote candidate instead of manufacturer-NRND DMG3415UFY4-7.
The [device handoff](device-component-selection.md) records the matched
package/pin/drain geometry, exact-orderable PCN and electrical differences.
This does not authorize silently carrying forward the old low-voltage leakage
guarantee, hotplug behavior or test-board current ratings.

A bounded 2520 crystal search did not establish a preferred lower-ESR exact
part. Evaluate the RP2040 guide's tested **ABM8-272-T3** 3225 reference and
15 pF load capacitors within the unchanged D43 board, rather than growing
the board or inferring impedance from a vendor suffix. Final lands, sourced
capacitors, height and local fit remain to be reconciled before adoption.
The earlier 22 pF selection is not silently superseded. Low-cell/LDO-dropout
startup and drive measurements remain necessary even with this reference.

These are source/implementation decisions, not completed routing, a supplier
quotation package, procurement approval or powered qualification.
Affected decisions: D02/D03/D05/D14; epics E04/#4, E07/#7 and E08/#8.

## 2026-09-14: clock-source selection completed

The bounded follow-up found matching primary ABM8 package evidence, including
the actual 0.80 mm maximum-height table and recommended lands. Select
**ABM8-272-T3** and explicitly supersede only C2/C3 with
**GRM1555C1H150JA01D, 15 pF**, retaining 1 kohm R6. This closes the selection
left open in the preceding entry, not the local-fit or powered gates.

The [device register](../hardware/handbell/parts/device-component-candidates.json)
records the exact/family source distinction, four-terminal pin/ground mapping,
1.30 x 1.05 mm crystal lands and 3.60 x 2.80 x 1.00 mm screening envelope.
The [passive register](../hardware/handbell/parts/standard-passive-candidates.json)
records the explicit 22-to-15 pF supersession and C2/C3-specific
0.40 x 0.50 mm reflow lands; other 0402 footprints and conservative capacitor
proxies are not changed by this decision.

Native implementation must remain inside D43 and preserve all fixed
interfaces. Rebind the complete assembly after actual placement/routing.
The 3.3 V reference does not qualify oscillator startup/drive at battery-fed
LDO dropout. A supplier quotation, order or powered release is not implied.
Affected decisions: D02/D03/D05/D14; epics E04/#4, E07/#7 and E08/#8.

## 2026-09-14: cost-aware prototype closure

The owner approves the [PCB closure plan](pcb-closure-plan.md) and requests
durable repository guidance plus incremental execution. Keep a promising
candidate with a finite repair list instead of abandoning it after a local
regression. Freeze required geometry decisions before expensive final routing;
batch metadata, reuse deterministic tools and perform complete checks at
coherent milestones. Generalizable agent principles are recorded in
`AGENTS.md`, without changing personal/global agent configuration.

Continue sequential bounded foreground items with up to two corrections,
and stop promptly on an owner pause. Preserve all earlier work and source
attribution. The target is a consistent engineering-prototype quotation
package, not functional/safety signoff or authorization to upload/order.
Owning epics: E04/#4, E05/#5, E07/#7 and E08/#8.

## 2026-09-15: land closure and quotation-process boundary

The continuing candidate now applies the six conservative device envelopes
and the selected U5/R27 land examples. Bounded local escape/exclusion repairs
preserve fixed poses, trace widths and private returns. The remaining
[native land choices are retained for routing](device-component-selection.md#september-15-remaining-land-and-assembly-dispositions),
with supplier questions recorded separately rather than treating every
example-footprint difference as a routing blocker.

For quotation, retain U4's current copper/vias and specify resin fill,
planarization and copper capping on its four thermal-pad vias. This is an
engineering quote baseline under the owner's standing development direction,
not owner approval of a fabrication cost or a verified two-layer service.
No stackup change, ordinary-tenting substitution or supplier request is
authorized by this decision. Stencil/assembly acceptance and coordinated
contact-height/CAD work remain open; no functional or child-use qualification
is implied.

## 2026-09-21: layer-count reassessment, not migration approval

The owner requested continued work plus a two/three/four-layer assessment
for JLCPCB Standard PCBA. The fixed-lattice R14 screen examined 936 poses;
eight passed preliminary pad/body checks, while the three shortest-distance
options retain direct-route conflicts. No placement was approved and the
accepted two-layer PCB/manifest remain unchanged at 51 opens.

Given D43, dense front population, rear battery-metal restrictions and
fragmented ground returns, Astra now recommends a separate four-layer
engineering candidate rather than continued two-layer-only local repairs.
This revisits the earlier low-cost target based on observed conflicts; it
does not prove two-layer routing impossible or erase prior work.
JLCPCB manufactures three-layer submissions as four. Its four-layer
filled/capped via process is explicitly offered at extra cost; two-layer
eligibility remains unverified. Standard assembly, X-ray for C481766,
panel handling, tall contacts and secondary USB-anchor soldering remain
independent costs and acceptance gates.

See the [engineering assessment](pcb-closure-plan.md#layer-count-reassessment-requested-september-21)
and [current supplier evidence](pcba-quotation-plan.md#current-jlcpcb-evidence).
The stackup is unchanged: obtain owner direction before a migration,
preserve the accepted source, and do not upload, order or claim turnkey
acceptance. Owning epics E07/#7 and E08/#8.

## 2026-09-21: owner-approved four-layer migration and portable-process policy

The owner explicitly approved four layers, pinned Sol routing in efficient
batches, and necessary special processes while preferring simpler equivalent
alternatives for affordability, repeatability and portability across fabs.
This supersedes the migration-approval gate in the preceding assessment.

Preserve the accepted two-layer package and establish one separate
`printed-bell-four-layer` candidate. First enable the four native layers
without changing source geometry, then qualify all-layer routing/checking
and release the ground/return strategy. The nominal thickness and mechanical
interfaces remain fixed; actual dielectric/copper stackup is a supplier
selection gate, not a guessed impedance specification.

The [execution contract](routing-agent-policy.md#four-layer-migration-and-efficient-execution)
assigns In1 to protected GND and In2 to released distribution/lower-speed
routing, preserves raw-contact/private-return exclusions, and defines
connected-group/corridor batches with one writer and engineering escalation.
Off-pad ordinary through-vias are preferred where equivalent. U4's current
filled/capped thermal vias remain required pending a bounded alternative
review; necessary special processes are not prohibited by the cost goal.
Native DRC alone is never sufficient acceptance.

No fabrication order, supplier upload, functional qualification or child-use
release is authorized. Owning epics E07/#7, E08/#8 and affected power/mechanical
reviews E04/#4, E05/#5.

## Risk register

| Risk | Mitigation / owning epic |
|---|---|
| Source import changes connectivity or package mapping | Preserve reference, compare nets/pins/footprints; E02/E04 |
| Tiny speaker lacks useful response for desired notes | Compare cavity-mounted drivers early; E03/E05 |
| Idle hiss/clicks or audible USB/power artifacts | Define states, measure transitions, review supply/SD_MODE; E03/E04/E09 |
| Audio vibrations or ordinary handling trigger notes | Record real motion corpus and refine nonblocking classifier; E06/E09 |
| Power savings lose the first strike or increase latency | Measure wake and always-ready alternatives; E03/E06 |
| Reference charge current unsuitable for small cell | Cell-specific design and independent review; E01/E04 |
| Board fits in 2D but not behind speaker/cell | Tolerance-aware 3D stack and assembly mock-up; E01/E05/E07 |
| USB or screw loads crack solder joints or damage cell | Supported carrier, stops, insulation, retention review; E05/E10 |
| Fine-pitch/rare parts undermine low-cost assembly | Early catalog BOM and quote, planned substitutions; E04/E07/E08 |
| MIT label hides hardware or asset obligations | Separate provenance/license scopes; E02/E11 |
| Wireless is ineffective inside metal shell | Defer radio; require antenna/enclosure evaluation; E12 |
| Educational prototype mistaken for child-ready product | Explicit safety/compliance gate before pilot/distribution; E10/E11 |
