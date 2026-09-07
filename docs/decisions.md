# Decision log

Planning snapshot, updated 2026-09-07. A provisional choice is a starting point for
experiments, not a final component or manufacturing commitment.

| ID | Decision / question | Current disposition | Evidence to close or revisit |
|---|---|---|---|
| D01 | Repository continuity | Retain the existing public `dcuccia/digital-handbell`, history, MIT license, 2023 notes and diagram | New planning and linked execution issues |
| D02 | Integrated baseline | Prefer Adafruit 5768 for first bench work and schematic derivation | Audio/motion/power experiments and import review |
| D03 | First MCU/runtime | RP2040 + CircuitPython provisionally preferred; no first-revision wireless requirement | Latency, audio/memory, idle/wake and USB workflow evidence |
| D04 | Sensor | Owner approved LSM6DSOX on 2026-09-07; integrated at 0x6A in the separate draft; retain LIS3DH for bench comparison | Gyro-enabled/disabled gesture comparison, driver initialization, full electrical review, and assembled BOM quote |
| D05 | CAD | KiCad 10.0.6 exercised; three pinned references converted; reduced draft has 0 ERC errors/warnings with no exclusions | Complete footprint/routing review and electrical freeze remain open |
| D06 | Hardware reuse license | Retain source-compatible CC BY-SA 3.0 for adaptations of verified sources; preserve root MIT for original code/docs | Full notices and per-file provenance at import; resolve 4884 version before use |
| D07 | Packaging | 0.2 investigates an inward-component 43 mm solid disk at z20..21.6 using the owner's new taper assumption | Real-shell/part tolerances, carrier access, complete routing and comparative quotes |
| D08 | Audio rail and quiet idle | TPS61023 5 V-class boost and independent GPIO20 mute implemented in 0.2; mono-left selection and initial 9 dB gain | Exact power parts, rail budget, noise, low-cell behavior and sequencing remain unqualified |
| D09 | Cell and charger | No pack selected; screen protected 1S packs for at least 2 A continuous plus transient margin; no automatic need for 1S2P | Full load/thermal/protection/runtime/USB budget and cell-specific charging |
| D10 | Play while charging | Unresolved; must be explicitly permitted or prevented | System power-path/input-current and charging/temperature evidence |
| D11 | Speaker and cavity | EK1725 on hand; smaller EK1794 candidate has conflicting 3 W title / 2 W description | Actual fit, qualified power limits, matched-level response, mass, distortion and current |
| D12 | USB and mounting | Printed removable cartridge and grille, preassembled outside shell, is leading concept | Bonded mounting interface, supported USB load path, service access, retention and isolation |
| D13 | Musical behavior | Note range, tuning, fixed/selectable note, retrigger/damping/polyphony and controls open | Requirements and prototype comparison |
| D14 | Fabrication/assembly | Quote JLCPCB populated boards; use OSH Park as bare-board alternative | DFM acceptance and complete cost at actual quantities |
| D15 | Wireless exploration | Owner favors S3-MINI; evaluate early for sound programming, QR identity and optional practice telemetry | Exact memory/build, RF with real shell/cell/speaker, power budget and protected updates; local sounding remains offline |

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
