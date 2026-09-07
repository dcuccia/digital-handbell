# Handbell schematic: 0.1 integration draft

**LSM6DSOX is integrated; this is not a fabrication release.** Open
[`handbell.kicad_pro`](handbell.kicad_pro) in KiCad 10.0.6, then its schematic.
For a CAD-free view, use the [schematic PDF](reports/handbell-schematic.pdf).
There is deliberately **no handbell PCB layout** in this directory.

The owner approved the sensor change on 2026-09-07. This revision replaces the
5768 reference's LIS3DH, resolves its original ERC findings in a separate
derivative, and establishes explicit sensor/debug connections. It intentionally
retains the other Feather branches to keep this change reviewable. Removing
servo/NeoPixel/header circuitry and selecting the speaker connector remain E04
work, not completed reductions hidden inside this revision.

**Later 2026-09-07 scope update:** the owner approved the compact GPIO19-button,
no-STEMMA/header/RGB revision and a boosted audio/mute review. The
[power/packaging assessment](../../docs/compact-power-and-packaging.md) records
those decisions, candidate sources and remaining gates. This directory's
native CAD/PDF/netlist still represents **0.1**, not that forthcoming revision.

## Artifacts and scope

| Artifact | Purpose |
|---|---|
| [Native schematic](handbell.kicad_sch), [local symbols](Handbell.kicad_sym) | Editable design; source-derived and mode-specific symbol definitions |
| [PDF](reports/handbell-schematic.pdf), [XML netlist](reports/handbell-netlist.xml) | Human and machine-readable views |
| [ERC disposition](reports/erc-review.md), [machine-readable dispositions](reports/erc-dispositions.json) | Individual treatment of all 50 original findings and collateral warnings |
| [Current ERC](reports/handbell-erc.json) | Zero errors and zero warnings under the unchanged baseline rules; no exclusions |
| [Connectivity/pad review](reports/connectivity-review.json) | 76 retained components, 75 retained connection groups, all 14 sensor lands |
| [BOM draft](reports/bom-draft.csv) | Values and footprints, with incomplete MPN/assembly choices explicitly marked |

The footprint table refers to the two sibling reference packages using
`${KIPRJMOD}`-relative paths. Keep the **whole repository checkout** together;
copying only this directory omits required footprints. Standard KiCad libraries
provide `power:PWR_FLAG`. The exported schematic also embeds its symbols.

## Reuse, authorship and license

This independent adaptation is **CC BY-SA 3.0 Unported**:
[complete license](LICENSE.txt). It is not an Adafruit product or endorsement.

- Core, power, audio and other retained circuitry: Adafruit RP2040 Prop-Maker
  Feather 5768, designed by Limor Fried/Ladyada for Adafruit Industries,
  source commit `408fa9a40c0a01a3a65497ef42a29e0b08fe711e`.
  [Full original notice and source](../reference/adafruit-5768/upstream/README.md).
- SOX symbol and LGA-14L footprint: Adafruit LSM6DSOX 4438, designed by
  **Bryan Siepert for Adafruit Industries**, source commit
  `c05abef4675b0380fbf3d23171615a2f1ac0b130`.
  [Full original notice and source](../reference/adafruit-4438/upstream/README.md).
- Integration, changed wiring, electrical pin types, annotations and review:
  the dcuccia digital-handbell project, with AI assistance, 2026-09-07.
- The standard KiCad `PWR_FLAG` symbol is used in the design under KiCad's
  [CC BY-SA 4.0 library license with design exception](https://www.kicad.org/libraries/license/).
  It is not redistributed in `Handbell.kicad_sym` as a library collection.
  Original verification scripts under `tools` remain MIT-licensed.

Both upstream references are preserved separately. The old Adafruit graphical
title frame was removed from this derivative and replaced with an independent
title block carrying attribution; upstream notices were not removed.

## LSM6DSOX electrical contract

**IC4 = LSM6DSOXTR**, LGA-14L, nominal 2.5 x 3.0 x 0.83 mm. It operates from
the common regulated **3.3 V**, not raw battery voltage. This is an I2C-only,
ST **Mode 1** implementation at seven-bit address **0x6A**.

| Physical pad | Function | Connection |
|---|---|---|
| 1 | SDO/SA0 | GND: fixed address 0x6A |
| 2, 3 | SDx, SCx | GND: unused Mode 1 auxiliary pins must not float |
| 4 | INT1 | `INT`, RP2040 GPIO22 / IC1 physical pin 34 |
| 5 | VDDIO | +3V3, local C24 = 100 nF to GND |
| 6, 7 | GND | Both physical pads to GND; imported symbol has stacked pins |
| 8 | VDD | +3V3, local C23 = 100 nF to GND |
| 9 | INT2 / DEN | `IMU_INT2` to TP6 only; no second MCU connection yet |
| 10 | OCS_Aux | Explicit NC; its physical land must still be soldered |
| 11 | SDO_Aux | Explicit NC; its physical land must still be soldered |
| 12 | CS | +3V3: I2C interface selected |
| 13 | SCL | GPIO3 / IC1 pin 5; existing R14 = 10 kohm to +3V3 |
| 14 | SDA | GPIO2 / IC1 pin 4; existing R15 = 10 kohm to +3V3 |

No duplicate regulator, BSS138 level shifter, CS diode or additional I2C
pull-up bank is imported from the breakout. Two local 100 nF bypass capacitors
follow ST's application circuit rather than treating the breakout's shared
100 nF and regulator bulk capacitance as interchangeable.

**Deliberate difference from Adafruit 4438:** its auxiliary pins go to JP2.
This fixed-function design instead follows ST's Mode 1 instructions: SDx/SCx
are tied to GND; OCS_Aux is NC; SDO_Aux is NC (ST also permits VDDIO).
The source symbol's generic bidirectional types are specialized to this mode
in `LSM6DSOX_I2C_MODE1`. Do not reuse that symbol for sensor-hub/OIS wiring
without reviewing the types, straps and firmware.

Evidence: [ST LSM6DSOX datasheet](https://www.st.com/resource/en/datasheet/lsm6dsox.pdf),
DS12814 Rev 3, Table 1 pp.8-9, section 5.1 pp.18-19, Figure 24 p.39 and Table 20
p.42. The reviewed ST-authored Rev 3 document was obtained through JLC's
[C481766 datasheet link](https://jlcpcb.com/partdetail/C481766) when the direct
ST fetch failed; page numbers above are **Rev 3**, not Rev 4. Original Adafruit
pin-to-pad mapping is in its pinned
[schematic lines 5463-5482](https://github.com/adafruit/Adafruit-LSM6DSOX-PCB/blob/c05abef4675b0380fbf3d23171615a2f1ac0b130/Adafruit_LSM6DSOX.sch#L5463-L5482).

## Preserved and changed connections

All non-sensor component values, footprints and pin-to-pin groups are retained.
I2S remains GPIO16 data, GPIO17 bit clock and GPIO18 word select; amplifier
power enable remains GPIO23. Changes beyond the sensor are:

- TP4 on SWCLK and TP5 on SWDIO make debug-pad intent explicit. They reuse the
  reference's 1.5 mm copper test-pad footprint; they are not fitted components.
  Adjacent GND/3V3 probing and physical accessibility remain layout decisions.
- Power-output/ground/mounting-terminal electrical types are corrected in the
  derivative library; intentional unused pins have NC markers.
- Redundant label-bearing wire tails are trimmed or removed without changing
  retained connections. Five power flags declare external/discrete sources;
  they are annotations, not added supplies or a proof of every power state.
- The inherited `1.2V` rail name becomes **`VCORE`**, with identical connections.
  RP2040's datasheet specifies a 1.1 V reset nominal for its internal regulator;
  a copied net label is not a voltage measurement or firmware setting.

## Firmware prerequisite discovered during integration

The inspected CircuitPython LSM6DS snapshot redefines `_i3c_disable` from
CTRL9_XL bit 1 to bit 0, and the SOX constructor uses that descriptor.
For this non-I3C design, verify **bit 1 set, reserved bit 0 clear**, preserving
other bits. Do not assume an unmodified copy of that inspected snapshot is
ready for bring-up. See the [motion document](../../docs/motion-sensing.md)
for pinned source evidence and the bring-up gate.
Execution is tracked in [E06 child issue #13](https://github.com/dcuccia/digital-handbell/issues/13).

Keep sensor-hub master, pass-through, OIS and DEN disabled. Retain the default
auxiliary pull-ups when leaving pads 10/11 NC. Route chosen events explicitly
to INT1; a physical interrupt wire does not configure interrupt behavior.

## Not resolved by this revision

Cell choice, charger current/temperature/protection, cutoff and play-while-charge
policy; speaker impedance/power, gain and quiet-idle sequencing; USB input/ESD
review; final controls/connectors; complete MPN/assembly quote; circular fit,
orientation, placement/routing, ground/current-return paths and mechanical
support; actual sound, latency, gestures, runtime and safety.

In particular, the inherited R8 = 5.1 kohm is about **196 mA nominal** charge
current, not an approved setting for an unspecified cell. Neither speaker lead
is ground: the MAX98357A output is BTL. E02/E04 remain open; zero ERC findings
are not independent electrical, acoustic, thermal or child-use signoff.

## Reproduce exports and checks

From the repository root in PowerShell, with Python 3.10+ and KiCad installed:

```powershell
$Cli = "$env:LOCALAPPDATA\Programs\KiCad\10.0\bin\kicad-cli.exe"
$Sch = ".\hardware\handbell\handbell.kicad_sch"
$Reports = ".\hardware\handbell\reports"
& $Cli sch export pdf --exclude-pdf-metadata --output "$Reports\handbell-schematic.pdf" $Sch
& $Cli sch export netlist --format kicadxml --output "$Reports\handbell-netlist.xml" $Sch
& $Cli sch erc --exit-code-violations --format json --output "$Reports\handbell-erc.json" $Sch
python .\tools\check_handbell.py --kicad-cli $Cli
```

Stop on a nonzero exit code. The final command freshly exports all three
schematics in temporary storage, checks both source imports and the derivative,
and updates the connectivity report and BOM draft. It uses only Python's
standard library. Its expected changes describe this 0.1 integration; future
intentional reductions must update that explicit contract, not bypass it.
These commands do not create or qualify a PCB.
