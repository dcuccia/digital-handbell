# Parts readiness for the full PCBA quotation

This independent audit covers the preserved initial routing candidate at
`b63a121b1ca990a64b00f231a85dd715126319af`, not the active power rework.
Its source [BOM](../hardware/handbell/iterations/printed-bell-routing/reports/bom-draft.csv)
has SHA-256 `b760b993757a85d4b0bb9b32155a34244e6282fbc9127692afbd5df36a8bd0e0`.
PCB and manifest hashes begin `075c7b7c` and `cc935ef4`.

**83 parts are fitted: 81 F and 2 B. Fifteen fitted rows have an MPN field;
68 do not, and there is no manufacturer column.** Some exact identities are
recoverable from values/source metadata, so this is not a claim that all
68 devices are unknown. It is nevertheless not a complete turnkey BOM.

The [quotation plan](pcba-quotation-plan.md) requires a sourced, matched final
package. Do not overwrite this immutable draft CSV to suggest its original
metadata was already procurement-ready.

## First sourcing increment

The separate [standard-passive register](../hardware/handbell/parts/README.md)
now provides manufacturer-verified candidates for 53 fitted references.
It identifies candidates for 48 formerly blank rows and confirms five already
specified identities without editing the preserved BOM. Full nominal/tolerance
dimensions and the actual Yageo TCR range are recorded from direct sources.
Application, final land/paste/placement and supplier review remain open;
this is progress toward the complete BOM, not a completed quotation package.

## Subsequent source decisions

The [USB register](../hardware/handbell/parts/hro-usb-candidate.json) identifies
X6 and its required engineering footprint/mechanical correction. The
[power-component register](../hardware/handbell/parts/power-component-candidates.json)
now selects L1, C26-C28 and FB1/FB2 prototype candidates, with actual biased
capacitance/current evidence and source-backed land/paste changes. The five
already selected 10 uF capacitors receive the corresponding part-specific
land treatment because they share the oversized source pattern.

These provide candidate identities for seven more formerly blank references.
The [device register](../hardware/handbell/parts/device-component-candidates.json)
then selects all thirteen remaining formerly blank identities and confirms
Q4, including the explicit DMP2045UFY4-7 replacement for NRND Q3 and the
tested ABM8-272-T3 crystal reference. C2/C3 explicitly change to sourced
15 pF parts with dedicated reflow lands. Implement the larger crystal
within the unchanged D43 board; actual fit is not yet established.
Circuit/package gates are in
[the device handoff](device-component-selection.md).
The selected parts still need to be applied to the new native candidate and
matched final supplier BOM; neither this progress nor the existing MPN fields
establishes complete package/process qualification. The audit tables below
retain the original draft's definitions rather than rewriting its history.

## Stopped final audit: remaining assembly inputs

At the owner's request to wrap up the long-running work, the final
nine-reference audit has stopped and handed back its findings. The
[structured audit](../hardware/handbell/parts/existing-part-review.json)
preserves eight identity groups, source URLs/hashes and unresolved operations.
It inspected the frozen power-rework package, **not the active quote
candidate**, and applied no native changes.

| References | Finding requiring disposition before freezing |
|---|---|
| J1 | Retain Molex 5040500291, alias 504050-0291. Manufacturer nominal lands agree; body height is 2.00 +/-0.15 mm. Preserve the larger proxy and map the specified pickup region rather than using its proxy centre. |
| J2 | Complete identity is SM02B-SRSS-TB(LF)(SN). Nominal side-entry lands agree; toleranced maximum geometry and actual pickup datum remain unresolved. |
| U5 | TI's example uses 0.67 x 0.30 mm pads at X +/-0.74, versus frozen 0.65 x 0.275 at +/-0.635. Local depth needs 1.70 mm for the body, or 2.00 including the documented protrusion allowance. |
| R27 | Panasonic's part-specific example permits 1.15 x 1.40 mm pads at X +/-1.025. Maximum package is 2.20 x 1.45 x 0.75 mm; frozen depth and height each underbound it by 0.05 mm. Preserve the independent sense connections when reconciling lands. |
| BT1/BT2 | Keystone 254 is bulk; 254TR is the reel option, not an automatic substitution. Confirm Rev C and account for its 16.97 mm upper drawing height separately from nominal/loaded contact geometry. Both contacts require assembly. |
| U1/U6/Q5 | Retain the existing exact identities and documented flash/protector geometry corrections. Fine-package stencil/handling remains a supplier disposition; Q5's native circular paste is about 19.5% smaller in area than TI's rounded-square example. |

These differences are **not demonstrated solder failures**, and they are not
silently waived or patched during wrap-up. Contact-height tolerance requires
coordinated mechanical work, not simply changing a number in a released model.
Pickup/rotation, connector hold-down joints, the common stencil/reflow profile,
thermal-pad vias and the distinct under-R27 transition still need an explicit
manufacturing disposition. Do not infer a complete board's reflow profile from
one semiconductor's MSL/260 C classification.

The current source-selection records and this stopped audit are durable
inputs to the next deliberate revision. They do not establish completed
routing, a matched final mechanical assembly or upload-ready quotation files.
No further research or implementation is authorized by this audit handoff.

## Capacitors: 29 fitted

| Group | Count | Existing definition and required action |
|---|---:|---|
| C1,C4,C5,C19,C20 | 5 | 10 uF/16 V, 0805. Select manufacturer/MPN, dielectric/tolerance, maximum dimensions and suitable effective capacitance. |
| C2,C3 | 2 | 22 pF, 0402. Specify dielectric/tolerance/voltage and reconcile with the actual crystal. C0G/NP0 is a proposed specification, not a recorded selection. |
| C6,C7,C9,C12,C13,C14,C16,C18,C23,C24 | 10 | 100 nF, 0402. Voltage, dielectric, tolerance and MPN are absent. The selected C30 identity is not automatically assigned to these references. |
| C8,C10,C11,C15,C17 | 5 | 1 uF/25 V, 0402. Select actual orderable parts and verify DC-bias/dimensions. |
| C21,C22 | 2 | 220 pF, 0402. Define dielectric, tolerance, voltage and EMI/pulse behavior. |
| C25 | 1 | 10 nF, 0402. Complete voltage/dielectric/tolerance/MPN. |
| C26,C27,C28 | 3 | 22 uF, 0805; no voltage/dielectric/tolerance/MPN. Priority power selections: effective capacitance at input/output bias, temperature/tolerance, ESR/ripple and maximum body dimensions. C29 remains DNP unless explicitly changed. |
| C30 | 1 | Explicit Murata GRM155R71C104KA88D, 100 nF/16 V X7R. Complete the exact manufacturer/package evidence; its height entry is still a planning proxy. |

Source BOM lines 4-33. The generic 0805 capacitor height is an unqualified
2.0 mm proxy, not a verified manufacturer maximum.

## Resistors: 28 fitted

| Group | Count | Existing value/identity |
|---|---:|---|
| R1-R5,R7,R14,R15,R18,R21 | 10 | 10 kohm, generic 0402 |
| R6,R11,R22 | 3 | 1 kohm, generic 0402 |
| R8,R12,R13 | 3 | 5.1 kohm, generic 0402; charge-programming and USB-C functions still need application-specific tolerance review |
| R9,R10 | 2 | 22 ohm, generic 0402 |
| R16,R17,R24 | 3 | 100 kohm, generic 0402; R24 is the boost divider's lower leg |
| R20 | 1 | 4.7 kohm, generic 0402 |
| R23 | 1 | 732 kohm, generic 0402; do not let the assembler round the divider value |
| R25 | 1 | Yageo RC0402FR-07330RL, 330 ohm |
| R26 | 1 | Yageo RC0402FR-072K2L, 2.2 kohm |
| R27 | 1 | Panasonic ERJ-6BWFR033V, 33 mohm, 1%, 0.5 W, 0805 |
| R28,R29 | 2 | Yageo RC0402FR-075M1L, 5.1 Mohm |

Source BOM lines 54-81. Generic rows need exact manufacturer/orderable,
tolerance, power and TCR. The five explicit rows still need package/derating
evidence; do not infer the high-resistance part's TCR/voltage parameters from
the 330 ohm family member. R27's 0.7 mm manifest height is not a sourced
maximum, and its nominal power rating is not a board-level thermal result.

## Other components: 26 fitted

| References | Count | Audit disposition |
|---|---:|---|
| BT1,BT2 | 2 | Keystone 254, real B-side assembly. Confirm supplied revision, packaging/pickup and assembly operation. Nominal free-contact height is not loaded spring/retention/current qualification. |
| IC1 | 1 | Recover Raspberry Pi RP2040 from the existing identity/source C2040; do not procure by the footprint name. |
| IC4 | 1 | Recover ST LSM6DSOXTR from the existing exact value. Front placement does not eliminate supplier-tier restrictions. |
| U1 | 1 | Winbond W25Q16JVUXIQ TR is explicit; retain the actual UX land/paste pattern. Correct the maximum-XY proxy below. |
| U2 | 1 | RT9080-3.3 is incomplete. RT9080-33GJ5 is a proposed Richtek orderable, subject to non-SNS pin/package comparison, not already selected. |
| U3 | 1 | Recover Microchip MCP73831T-2ACI/OT from the exact existing value. Preserve the AC charging-profile option. |
| U4 | 1 | MAX98357A is a family name. MAX98357AETE+T is a proposed TQFN orderable; do not substitute a WLP package. |
| U5 | 1 | TI TPS61023DRLR is explicit; attach exact DRL package/manufacturing limits. |
| U6 | 1 | TI BQ29700DSER is explicit. Retain the deliberately reviewed all-NSMD pattern and correct the maximum-XY proxy below. |
| Q1 | 1 | AOS AO3401 base identity; resolve ordering/package evidence. Do not silently change to AO3401A or a clone. |
| Q2,Q4 | 2 | Q4 is AO3400A. Q2's C20917 catalog identifier maps to AOS AO3400A, but imported versus standard SOT23 land patterns still need reconciliation. |
| Q3 | 1 | Diodes DMG3415UFY base identity; freeze orderable/packing suffix and preserve the corrected custom drain land. |
| Q5 | 1 | TI CSD83325L, YJE6 PicoStar. Maximum 1.15 x 2.20 x 0.22 mm has source support; confirm assembly capability and authorized sourcing. |
| D3 | 1 | 1N4148 plus SOD323_MINI is not a package-specific orderable. Select the actual SOD323 device/polarity/ratings. |
| D4 | 1 | Nexperia PMEG2020AEA base identity. Reconcile exact orderable and SOD323F drawing; generic SOD323 names are not interchangeable. |
| FB1,FB2 | 2 | Only "Ferrite", 0603. Define actual impedance/frequency, DCR, rated/DC-bias current and maximum dimensions before selecting. |
| CHG0,L0 | 2 | Orange/red 0603 LEDs need separate exact orderables, polarity, electrical/optical specifications and dimensions. |
| J1 | 1 | Molex 504050-0291 is explicit. Confirm manufacturer/mating/current evidence; 3.1 mm remains a proxy. |
| J2 | 1 | JST SM02B-SRSS-TB is explicit. Confirm suffix/finish and side-entry package; do not substitute BM02/top-entry. |
| L1 | 1 | 1 uH and TDK_VLC5045 footprint family do not establish an orderable. Priority: actual saturation/thermal current, DCR/loss, tolerance, lands and maximum height. Do not invent a part number from the family name or shrink the 5 mm proxy without evidence. |
| X6 | 1 | CUSB31-CFM2AX-01-X footprint alias versus source C165948/HRO TYPE-C-31-M-12 is unresolved. Obtain the exact manufacturer drawing and reconcile the actual lands, NPTH/anchors, mouth and height. |
| Y1 | 1 | 12 MHz/12 pF, 2.5 x 2 mm is not an orderable. Freeze crystal load/ESR/drive/tolerance/stability/pin case/height; do not substitute an oscillator. |

Source BOM lines 2-3, 34, 38-53, 96-103. Existing device/package evidence is
in [the T8 electrical revision](t8-electrical-revision.md), particularly its
flash, protection, contact and footprint sections. Public catalog identity
leads for [Q2](https://jlcpcb.com/partdetail/AO3400A/C20917) and
[X6](https://jlcpcb.com/partdetail/Korean_HropartsElec-TYPE_C_31_M12/C165948)
are not proof of land-pattern compatibility or current stock.

## Geometry and assembly corrections

The manifest has 78 unqualified height-proxy entries, three entries with
manufacturer-height evidence and two nominal contact-height entries.

- U1's depth is 2.0 mm, but the reviewed Winbond dimension is 2.0 +/- 0.1 mm:
  use 2.1 mm maximum along the appropriate transformed axis. The other axis
  already has the larger envelope. See the T8 flash drawing discussion and
  initial manifest lines 2580-2603.
- U6's depth is 1.5 mm; TI DSE0006A 4220552/B permits 1.55 mm. Enlarge the
  relevant envelope in the new candidate, not the preserved snapshot or pad
  identities. See [BQ2970 package drawing](https://www.ti.com/lit/ds/symlink/bq2970.pdf)
  and initial manifest lines 2700-2723.

Proxy centres and native origins also differ: X6 Y-1.115 mm, J2 Y+0.350 mm,
Q3 Y+0.2725 mm and U4 X-0.170709 mm. None of those differences alone defines
the assembly pickup point. Explicitly review actual package centres, pin 1,
cathodes and bottom-side rotation. Inherited rotation metadata is not a
universal correction. The split-land contacts need particular handling.

The original candidate's actual outline bounds are **44.50 x 48.35 mm**,
including contact tabs and USB tongue, not a D43 circular coupon. Preserve
that outline and coordinate supplier-defined rails/tooling/depanelization.
Define thermal-pad via, under-resistor via and stencil treatment. U1's narrow
0.15 x 1.20 mm paste aperture and Q5/U6 packages require specific capability
review. Do not erase USB-clearance findings to obtain a superficially clean
quote export.

## Population and closure

Include both BT1 and BT2. Exclude C29 (DNP), the 18 copper-only features
CHG_EN0/D+1/D-1/GAIN0/TP3-TP16, and MH1/MH2 from component loading.
X1 is absent, not an extra purchase line. Copper jumpers are not fictitious
zero-ohm resistors.

First close L1, C26-C28, FB1/FB2, X6, Y1 and D3; normalize recoverable device
identities and finish the ordinary passive specifications in parallel.
Record explicit proposals and selection/package evidence before exporting a
complete sourced BOM. Incompatible lands and unspecified parts/processes
are quotation-input problems, not merely future functional tests.

Later powered, acoustic, runtime, enclosed-temperature, contact/fault and
charging qualification may remain clearly disclosed prototype gates at
quotation time. No supplier upload, purchase or live-cell approval is implied.
Owning epics: E04/#4, E05/#5, E07/#7 and E08/#8.
