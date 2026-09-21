# Device identities and package corrections

September 14, 2026. The
[device register](../hardware/handbell/parts/device-component-candidates.json)
selects **thirteen formerly blank prototype device identities** and confirms
Q4. It records manufacturer sources, pin/polarity details, local-axis maximum
dimensions and unresolved manufacturing gates. These identities are not a
released supplier BOM, approval to purchase, or proof that every inherited
land/paste pattern is suitable.

All selected device identities are now applied in the continuing
[clock/integration draft](../hardware/handbell/iterations/printed-bell-clock-draft/README.md#all-fitted-part-identities-applied).
Its final identity batch preserves geometry. The separately completed clock/Q3
work and September 15 six-device envelope revision are applied. Remaining
copper-retention decisions are recorded below; supplier paste/process acceptance
and full mechanical qualification stay open.

| Reference | Selected identity | Principal distinction |
|---|---|---|
| CHG0 | Kingbright APT1608LSECK/J4-PRV | Low-current orange; J4, not J3 |
| L0 | Kingbright APT1608LSECK/J3-PRV | Low-current hyper red |
| D3 | Diodes 1N4148WS-7-F | Actual SOD323, not axial 1N4148 or a similarly named SOD123 part |
| D4 | Nexperia PMEG2020AEA,115 | Manufacturer package is SOD323, despite the imported SOD323F alias |
| IC1 | Raspberry Pi RP2040 | Official reel codes SC0914(7)/(13) are recorded separately |
| IC4 | ST LSM6DSOXTR | Correct LGA14, Mode 1 and existing firmware initialization gate retained |
| Q1 | AOS AO3401 | Manufacturer says Full Production; no AO3401A substitution is needed |
| Q2, Q4 | AOS AO3400A | C20917 resolves Q2; Q4 has a differently oriented native footprint |
| Q3 | Diodes DMP2045UFY4-7 | Explicit replacement for NRND DMG3415UFY4-7; corrected DFN drain retained |
| U2 | Richtek RT9080-33GJ5 | Fixed 3.3 V, non-N variant: pin 4 NC, not SNS |
| U3 | Microchip MCP73831T-2ACI/OT | Exact existing charger options retained |
| U4 | MAX98357AETE+T | T1633+4 16-TQFN, not the WLP option |
| Y1 | Abracon ABM8-272-T3 | RP2040 reference; deliberate 3225 footprint and 15 pF load-capacitor revision |

The researcher preserved original manufacturer documents and actual catalog
records locally; the parent confirmed all 24 named source hashes and
inspected the height/flash drawings. Twenty of those source records support
the first eleven selected groups. The subsequent Q3 selection adds four
manufacturer records from a separately hash-bound follow-up; all sixteen
follow-up source hashes were confirmed before adoption. Public records omit personal evidence paths
and do not redistribute manufacturer PDFs or images.

## Conservative package-envelope corrections

These changes belong only in the new quote candidate and its next complete
CAD bind. No archived board, placement or print is overwritten.

**Applied September 15** to the continuing manifest, retaining actual current
poses and offsets. The source-bound `reports/device-envelopes.json` records
no new overlap/outline/speaker screen conflicts. Native PCB/schematic files
are unchanged; this is not a fresh full-CAD or physical-fit approval.

| Reference | New local X x Y x Z screening envelope, mm | Reason |
|---|---|---|
| D3 | 3.04 x 1.40 x 1.20 | The drawing separates body thickness A2 from standoff A1; their conservative maximum sum is 1.20, not the old 1.10 |
| D4 | 3.00 x 1.35 x 1.10 | Actual SOD323 maximum width and height exceed the old 1.30/1.00 values |
| Q1/Q2 | 3.354 x 3.20 x 1.50 | Add the manufacturer-permitted mold-flash screen to the body's long axis |
| Q4 | 3.35 x 3.354 x 1.50 | The same package's long axis is local Y in this footprint |
| U3 | 3.60 x 3.8002 x 1.50 | Conservative BSC/profile and permitted-flash derivation, not an ordinary-body size claim |

Mold flash is a small plastic protrusion left by package molding. AOS permits
less than 0.127 mm per non-lead side beyond its 3.10 mm body length, giving
a conservative 3.354 mm screening bound. Microchip separately excludes up
to 0.25 mm per side; the recorded profile-based bare-length derivation gives
3.10 mm and hence a 3.60 mm flash-inclusive screen.

These are conservative component screens, **not measured mounted dimensions**
or a complete combination of solder lift, placement accuracy, PCB distortion
and printed-part tolerances. Manufacturing should review the interpretations
before the final envelope is frozen. Do not shrink other existing proxies or
discard native-to-proxy center offsets.

## Electrical identity does not approve the old footprint

The new candidate must address the part-specific land/paste/polarity findings
in the register. Examples include the LEDs' recommended 0.85 mm land gap
versus the old 0.70 mm, D3/D4's actual SOD323 recommendations, and U2's
recommended 0.7 x 1.0 mm pads versus the old 0.55 x 1.2 mm pads.
These differences are not themselves evidence that previous hardware failed,
but they cannot be hidden behind a generic package label.

U4's selected exposed pad is nominally 1.10 mm square, maximum 1.25 mm;
the native thermal copper is 1.50 mm square. Its actual paste, thermal vias,
mask and supplier soldering process need an explicit disposition. Neither
full-pad paste nor filled/capped vias are automatically approved by this
identity selection. Preserve the intended GND return and remeasure altered
current-carrying geometry where applicable.

Keep actual pin/net mappings, including diode/LED `C`/`A` identities and
manufacturer pin-1 cathode conventions. Do not widen all similarly named
footprints globally or silently replace RT9080 with its SNS variant.

The two LED candidates are specified optically at 2 mA, but the actual board
uses **10 kohm R2/R7**. Illustrative currents are about 0.28-0.32 mA for
the charging LED and 0.15 mA for the GPIO LED. These are operating-point
examples, not guaranteed bounds or guaranteed visible brightness. The
resistors are not changed to force the datasheet's optical test current.

## September 15 remaining land and assembly dispositions

The current native land choices are retained for continued routing unless
listed as changed below. This closes a copper-design decision, **not** supplier
process acceptance. Example-pattern differences alone are not evidence that
the adopted Adafruit design failed.

| References | Routing disposition | Explicit quotation/assembly condition |
|---|---|---|
| CHG0/L0 | Retain 0.8 x 0.8 mm lands at 1.50 mm pitch. The manufacturer example uses the same land size at 1.65 mm pitch; retain the mapped C/A polarity and source layout rather than moving parts solely to copy the example. | Confirm paste, placement and joints for the exact selected LEDs. Do not change the 10 kohm resistors to match an optical-test current. |
| D3 | Retain 0.9 x 0.8 mm lands at 2.14 mm pitch. The selected SOD323 lead-span/terminal bounds fit the centered land region; C remains USBBOOT. | Full-pad paste is larger than the manufacturer's 0.59 x 0.45 mm land example. Assembler must review solder volume; this is not a manufacturer-prescribed stencil or a demonstrated solder failure. |
| D4 | Retain 1.0 x 0.8 mm lands at 2.00 mm pitch for the selected actual SOD323 package, not the stale SOD323F alias. A remains VBUS, C remains VHI. | Confirm exact suffix/packing and stencil volume. The corrected maximum envelope is already applied. |
| U2 | Retain 0.55 x 1.20 mm lands, 0.95 mm pitch and 2.6002 mm row spacing. Nominal pin layout agrees; the 0.559 mm maximum lead width exceeds the land by 0.009 mm overall. This small width difference alone does not establish a failed joint. Pin 4 stays NC. | Obtain placement/joint acceptance rather than silently claiming the Richtek 0.7 x 1.0 mm example was applied. |
| U4 | Retain the imported copper, peripheral openings and four thermal vias. The actual center paste is one **1.143 x 1.143 mm square**, not full 1.5 x 1.5 mm pad paste. Retain it as the quotation stencil baseline. | Specify filled-and-copper-capped treatment for those four vias in the quote-only process notes below. Stencil volume/voiding and the 16 explicit peripheral mask openings require assembler review; do not add duplicate automatic mask openings. |

For U4, the center paste area is 1.306449 mm2, about 58.1% of the 2.25 mm2
copper land. Comparing only that percentage is not a solder-process approval:
the selected package's exposed pad is nominally 1.10 mm square and its
placement, paste release and finished voiding still matter.

The retained-part audit is likewise split into copper and process decisions:
J1/J2 keep their agreeing nominal connector patterns and all reinforcement
joints; BT1/BT2 keep their split lands and fixed datums; U1 keeps the previously
corrected terminal/center-strip geometry; U6 keeps the documented all-NSMD
adaptation; Q5 keeps its manufacturer-matching circular copper lands and
current circular paste. U5/R27's selected corrections are now applied in
`reports/power-device-lands.json`. No further native land change is selected
by this pass.

J2's toleranced maximum, connector pickup mapping, U1's 0.15 x 1.20 mm
center-strip aperture, U6's all-NSMD assembly and Q5's paste-area difference
remain explicit supplier questions, not hidden waivers. BT1/BT2's 16.97 mm
upper drawing height must be screened in the coordinated mechanical model;
do not stretch the nominal contact primitives or invent loaded geometry.

### U4 quote-only via treatment

September 21 update: the owner approved a separate four-layer migration.
The treatment below remains required for the retained U4 geometry until a
specific simpler alternative passes thermal, electrical and stencil review.
Extra ground-plane access alone does not qualify an off-pad substitute.

For the matched quotation assets, specify **nonconductive resin fill,
planarization and copper capping** on U4's four existing 0.35 mm nominal-drill
thermal vias. Keep the two-layer board and current copper as the baseline.
Their native PCB centers in mm are:

| X | Y | Via UUID |
|---|---|---|
| 110.400323 | 89.587211 | `eb628663-2af6-5175-bd63-91e9eecb0258` |
| 110.400323 | 90.237211 | `d9dcd570-3f7d-5000-b8d1-12b9b39f93b5` |
| 111.050323 | 89.587211 | `545fee40-3fbd-59ae-bd8d-30ffe16436ec` |
| 111.050323 | 90.237211 | `c63c289d-af32-592b-9732-d17507fbf476` |

Transform these coordinates with the final fabrication datum; do not mistake
this native-coordinate table for a finished vendor drawing. Ordinary tenting
is not an equivalent process: the vias sit inside the thermal land's mask
opening and can draw solder away without controlled treatment.

This is a **quotation requirement, not a verified service or cost** at either
vendor. Supplier confirmation of two-layer availability, cap finish/flatness
and stencil is required before manufacture. If unavailable, report the
constraint or separately priced alternative; do not silently change the
stackup, relocate vias or replace capping with ordinary tenting.

The [official JLCPCB via-treatment guide](https://jlcpcb.com/help/article/pcb-via-covering),
read September 15, distinguishes resin-filled/capped vias from ink plugging
and tenting, and specifically excludes via-in-pad from ordinary ink plugging.
Its statement that resin filling is free at six layers and above does **not**
establish a two-layer prohibition. Neither vendor's two-layer availability or
price was established here, and no quote was requested.

## Q3 replacement decision

Select **DMP2045UFY4-7** instead of the manufacturer-NRND DMG3415UFY4-7.
The old/new package drawings agree, so keep the corrected DFN lands, explicit
paste/mask, 2.855 x 1.575 x 1.0 mm proxy and 0.2725 mm centre displacement.
Pin 1 is gate/VBUS, pin 2 source/VHI and pin 3 the large drain/VBAT.
The intrinsic diode conducts from VBAT toward VHI during battery startup.

This is package-compatible, **not electrically identical**. At 25 C the
maximum resistance increases 39 to 45 milliohm at -4.5 V gate drive and
52 to 58 milliohm at -2.5 V, under their matching specified currents.
An illustrative 2 A comparison at the latter limits adds 12 mV/24 mW;
it does not rate the board. The new 1.8 V resistance test is at only 0.1 A,
not the old 2 A condition. Drain voltage increases to 20 V; gate maximum
remains +/-8 V.

Do not retain the old 500 nA gate-leakage guarantee at 5 V: the new datasheet
only specifies 10 microamp at 8 V. Gate charge, capacitance and internal gate
resistance also differ; the real VBUS/10 kohm gate network needs startup and
USB-transition measurements, not an assumed identical switching waveform.
Neither the body-diode current figure nor the thermal ratings are independent
of the manufacturer's specified test-board copper.

[PCN-2792-REV1](https://www.diodes.com/assets/PCN-Files/Diodes_PCN_2792_and_Qual_Rpt.pdf),
dated January 27, 2026 with April 27 implementation, names exact
DMP2045UFY4-7 in table 4. Its change is Cu-to-PdCu bond wire, not the
mold-compound changes in other tables. This supports current manufacturing
continuity, not a stock/lifetime guarantee or an observed Active field.
No reverse-cell or ideal-diode protection is added.

**Native application:** the continuing
[clock/integration draft](../hardware/handbell/iterations/printed-bell-clock-draft/README.md)
now identifies Q3 as DMP2045UFY4 with exact MPN **DMP2045UFY4-7**, manufacturer
and datasheet fields in its schematic and PCB, plus the placement manifest.
It retains the generic P-channel symbol and corrected DFN footprint rather
than inventing a different circuit symbol or changing copper. All three nets,
pad primitives, placement and the actual pose-dependent proxy offset are
unchanged. The scoped report is `reports/q3-native-identity.json`; the updated
schematic is `reports/q3-schematic.pdf`. Earlier native variants remain intact.
This implements the identity choice, not its remaining powered or supplier gates.

## Selected clock-reference revision

The bounded 2520 search did not establish a lower-ESR exact orderable.
ECS-120-12-36-AGN-TR remains a conditional 12 MHz/12 pF/150 ohm option,
not the preferred reference. A seemingly lower-ESR Multicomp ordering string
had contradictory primary tables; its suffix was not accepted as a rating.

Select **Abracon ABM8-272-T3**, explicitly recommended
in Raspberry Pi's RP2040 hardware guide: 12 MHz, 10 pF load, 50 ohm maximum
ESR and 200 microwatt maximum drive. Its 3.2 x 2.5 mm package is larger than
the old crystal, but the board must remain D43. This is authorization to
implement the local revision, not a claim that the finished routing fits.

The exact 2024 manufacturer PDF still contains only three sheets and
references an absent height table. The matching manufacturer-hosted
[ABM8 family drawing](https://abracon.com/Resonators/abm8.pdf), revised
July 29, 2020, supplies the actual **0.80 mm maximum** height table and
recommended lands. Its body/terminal dimensions, pin arrangement and
variable-chamfer note match the exact part. Use it for geometry only;
its generic electrical/MSL defaults do not override the exact part.

Use four **1.30 x 1.05 mm rectangular lands at 2.30 x 1.75 mm centre pitch**,
with 1.00/0.70 mm X/Y gaps. The new **3.60 x 2.80 x 1.00 mm screening
envelope** contains both maximum bare body and recommended copper while
retaining the existing height allowance. It is not a qualified placement
courtyard. The register specifies body-centred pin coordinates; chamfer
location alone does not identify pin 1 or the assembly rotation.

This reference uses 15 pF load capacitors and 1 kohm series resistance for
3.3 V IOVDD. C2/C3 now explicitly select **Murata GRM1555C1H150JA01D**,
15 pF/C0G/50 V/+/-5%, replacing only the earlier 22 pF group. The original
catalog response and part-specific PDF agree on the complete orderable,
maximum 1.05 x 0.55 x 0.55 mm body and D packing.

While rerouting this clock cluster, select dedicated **0.40 x 0.50 mm
capacitor lands at X +/-0.40 mm**. These follow the manufacturer's reflow
range, unlike the old 0.60 mm pad length. Update corresponding paste/mask;
do not alter all 0402 footprints or shrink the existing capacitor proxies.
Keep C3 on the crystal side of R6, and keep R6 at 1 kohm.

Even the tested reference needs
startup/drive/load evaluation on this layout, particularly when the battery
and LDO approach dropout rather than maintaining 3.3 V.
The Pi guide explicitly warns that reduced IOVDD can stop oscillation with
1 kohm; any later damping change must also recheck drive at maximum IOVDD.

The preserved Y1 symbol has only pins 1/3, while physical pads 2/4 have no net.
The selected crystal's grounded metal-case pads require a corresponding
four-terminal symbol, schematic/netlist and PCB grounding change. A PCB-only
ground assignment would not close source equivalence.

The routing candidate owns native implementation and its evidence; the
parent then rebinds the complete assembly and prepares the
[matched quotation handoff](pcba-quotation-plan.md). Prototype electrical,
thermal, fault, acoustic and child-use qualification remain separate gates.
Tracking: E04/#4, E05/#5, E07/#7 and E08/#8.
