# Device identities and package corrections

September 14, 2026. The
[device register](../hardware/handbell/parts/device-component-candidates.json)
selects **eleven formerly blank prototype device identities** and confirms
Q4. It records manufacturer sources, pin/polarity details, local-axis maximum
dimensions and unresolved manufacturing gates. These identities are not a
released supplier BOM, approval to purchase, or proof that every inherited
land/paste pattern is suitable.

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
| U2 | Richtek RT9080-33GJ5 | Fixed 3.3 V, non-N variant: pin 4 NC, not SNS |
| U3 | Microchip MCP73831T-2ACI/OT | Exact existing charger options retained |
| U4 | MAX98357AETE+T | T1633+4 16-TQFN, not the WLP option |

The researcher preserved original manufacturer documents and actual catalog
records locally; the parent confirmed all 24 named source hashes and
inspected the height/flash drawings. Twenty of those source records support
the presently selected groups. Public records omit personal evidence paths
and do not redistribute manufacturer PDFs or images.

## Conservative package-envelope corrections

These changes belong only in the new quote candidate and its next complete
CAD bind. No archived board, placement or print is overwritten.

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

## Two decisions remain open

**Q3:** the exact old ordering identity is DMG3415UFY4-7, which the manufacturer
marks NRND. The suggested DMP2045UFY4 replacement is under a bounded
electrical/pin/package comparison; it is not silently selected. The corrected
DFN drain mapping and source-selection behavior must be preserved.

**Y1:** ECS-120-12-36-AGN-TR is a real 12 MHz/12 pF/2520 candidate, but its
150 ohm ESR is not yet the preferred choice. A lower-ESR near-fit is being
evaluated. Keep R6 at 1 kohm and C2/C3 at 22 pF pending that decision.
Their series contribution is 11 pF; actual stray capacitance, oscillator
startup margin and drive power are not established by the nominal values.

The current Y1 symbol has only pins 1/3, while physical pads 2/4 have no net.
A selected crystal with grounded metal-case pads needs a corresponding
four-terminal symbol, schematic/netlist and PCB grounding change. A PCB-only
ground assignment would not close source equivalence.

The routing candidate owns native implementation and its evidence; the
parent then rebinds the complete assembly and prepares the
[matched quotation handoff](pcba-quotation-plan.md). Prototype electrical,
thermal, fault, acoustic and child-use qualification remain separate gates.
Tracking: E04/#4, E05/#5, E07/#7 and E08/#8.
