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
