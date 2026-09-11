# 0.2 electrical reduction and placement handoff

**Editable engineering draft, not an order-ready board.** This revision implements
the approved reduction in native KiCad and provides a **43 mm, two-copper-layer,
one-component-face placement candidate**. It has no tracks, vias or planes.
Placement feasibility is not routing feasibility, a minimum diameter, a thermal
result, or proof that the assembly fits the real bell.

Use the [schematic PDF](../hardware/handbell/reports/handbell-schematic.pdf),
[placement view](../hardware/handbell/placement/placement-top.svg) and
[mechanical feasibility handoff](mechanical-feasibility.md) together.
The earlier [power/packaging review](compact-power-and-packaging.md) remains a
historical decision record; this document describes the implemented revision.

## What changed

| Area | Implemented in 0.2 |
|---|---|
| Expansion | Removed Feather headers, STEMMA QT, servo and external RGB connectors, RGB level shifter/resistor, onboard NeoPixel, old mounting holes/fiducials |
| Recovery | Removed physical BOOT/reset switches while preserving ROM recovery and reset access as copper service pads |
| Audio power | Added the pinned Adafruit 4654 TPS61023 block, with 1 uH / 5 x 5 mm inductor provision and a 732 kohm / 100 kohm divider; about 5 V, not an assumed 5.2 V |
| Power control | Retained source selection and Q1/Q2 switching; GPIO23 enables both the switched converter input and converter EN; R17 keeps POWER low by default |
| Mute/channel | Added GPIO20-controlled AO3400A pull-down on SD_MODE; R18 is now 10 kohm to VAMP, selecting the left channel when unmuted |
| Button | Side-entry JST-SH SM02B-SRSS-TB, GPIO19 through 1 kohm, 10 kohm released-state pull-up and 10 nF filtering |
| Speaker | Separate Molex Pico-Lock 504050-0291 connector: pin 1 VO+, pin 2 VO-; neither is ground |
| Indication | Retained CHG0 charger LED and L0 GPIO13 firmware LED; no RGB indicator |
| Sensor/core | Retained the 0.1 LSM6DSOX Mode 1 interface, RP2040/flash/clock/USB, regulated logic supply and charger/source-selection circuitry |

There are **93 component-or-copper-feature references**: **74 fitted front-face
parts**, **18 reverse-face copper features**, and **one DNP capacitor provision**.
Copper-only test/jumper pads do not require second-face component assembly.
Small signal passives largely retain 0402 footprints. Boost capacitors, power
parts and connectors are not indiscriminately shrunk to 0402.

The [explicit reduction record](../hardware/handbell/reports/electrical-reduction.json)
lists removals, additions and new nets. Sixty-two retained reference components
and 73 projected connection groups are covered by the connectivity contract;
R18, the six amplifier-rail pins and three footprint changes are explicit
exceptions, not silent source edits.

## Mono audio and quiet-idle intent

`POWER` (GPIO23) is active high. `AMP_MUTE` (GPIO20) is **high to mute,
low to play**. R20 = 4.7 kohm pulls the MOSFET gate up to +3V3 so the powered,
reset-state logic domain requests mute. This is not an all-fault or brownout
silence guarantee.

Q4 sinks SD_MODE without connecting a 3.3 V GPIO directly to the amplifier's
5 V-class domain. R18 = 10 kohm references SD_MODE to **VAMP**, not always-on
+3V3. With the amplifier's minimum 92 kohm internal pull-down, a nominal 5 V
rail gives approximately 4.51 V on SD_MODE when Q4 is off, above the specified
1.5 V maximum left-selection boundary. When Q4 is on, it sinks approximately
0.5 mA through R18. Its suitability must include the actual gate voltage and
power-state behavior, not only a threshold-voltage headline.

Start with **9 dB gain** and left-channel audio; mono assets should feed that
channel, or be deliberately duplicated in stereo. The open three-pad GAIN
jumper retains selectable GND/GAIN/VAMP connections. Increasing gain does not
create additional supply headroom. A 3 W high-end electronics scenario into
4 ohm is not a promise of 3 W low-distortion sound, nor does it resolve the
EK1794 seller's 3 W title versus 2 W description.

Firmware should request mute before enabling power, establish valid clocks/data,
allow power/startup settling, and then unmute with an amplitude ramp. On stopping,
fade/drain the audio, mute, and only then change clocks/power. Do not stop LRCLK
while continuing BCLK. Bench work must cover USB insertion/removal, reset,
brownout, startup/shutdown clicks, idle hiss, and residual VAMP capacitor charge.
No audio firmware or measured acoustic result is delivered by this CAD revision.

Primary references: [MAX98357A datasheet](https://cdn-shop.adafruit.com/product-files/3006/MAX98357A-MAX98357B.pdf),
[AO3400A datasheet](https://www.aosmd.com/sites/default/files/res/datasheets/AO3400A.pdf),
[TPS61023 datasheet](https://www.ti.com/lit/ds/symlink/tps61023.pdf).

## Power and sourcing gates

The MiniBoost source is now [pinned and imported](../hardware/reference/adafruit-4654/README.md).
Its default-on EN pull-up is deliberately omitted; the existing POWER pull-down
defines the new default. The original upstream reference remains unchanged.
The converter's 3.7 A typical **valley switch-current limit** is not a 3.7 A
output rating.

L1's exact MPN is pending. Inductance, saturation/thermal current, DCR, height,
land pattern and overload behavior all require review. WE-MAIA is a family,
not a selected drop-in part. C26/C27/C28 use the source 22 uF/0805 provisions;
their dielectric, rated voltage and **effective** capacitance under bias matter.
Retained C19/C16 add output capacitance. **C29 = 220 pF DNP** reserves a
feed-forward option; effective output capacitance and compensation must be
resolved against TI guidance before freezing assembly. It is not a proven
stability fix.

The charger remains MCP73831 with R8 = 5.1 kohm, about **196 mA nominal**,
unapproved for an unspecified cell. No cell has been selected. Screen a
factory-protected 1S pack for at least 2 A continuous capability plus transient
margin, then establish charge limits, low-cell cutoff, protection, temperature,
runtime and lead/connector ratings. Do not improvise loose-cell paralleling.
Input-current budgeting and play-while-charge policy remain open: a 5 V USB
connector does not imply unrestricted current.

**2026-09-11 alternative under review:** the owner's proposed unprotected
[Vapcell T8 and protection-function review](battery-contact-options.md#2026-09-11-vapcell-t8-and-pcb-level-protection-alternative)
could move cell protection onto the main PCB. The current charger/source
selector does not already supply a complete cell-protection system; the
factory-protected-pack assumption above cannot simply be dropped.

J1's exact mating harness/current and body envelope still need primary
manufacturer confirmation. J2 is deliberately **side-entry**: the
[JST drawing](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf) gives 2.95 mm
reference mated height versus 6.3 mm for top-entry. The model screens J2 at
3.1 mm and includes an additional 0.7 mm front mating allowance; cable bend
and manufacturing maxima are not established. Battery JST-PH, speaker
Pico-Lock and button JST-SH are intentionally different connector families.

## Service access and firmware contract

| Access | Net / role |
|---|---|
| TP3 | BOOT/USBBOOT, not reset |
| TP4 / TP5 | SWCLK / SWDIO |
| TP6 | IMU INT2; no second MCU interrupt connection |
| TP7 / TP8 / TP9 | RUN/reset / GND / +3V3 |
| TP10 / TP11 | VAMP / VBAT |
| TP12 / TP13 / TP14 | I2S DIN / BCLK / LRCLK |
| TP15 / TP16 | AMP_MUTE / POWER |
| D+1 / D-1 | USB data probing |

GPIO19 is stock CircuitPython **`EXTERNAL_BUTTON`**; `board.BUTTON` is GPIO7.
GPIO20 replaces the old servo function. A custom board definition should remove
RGB status behavior and expose the new mute alias. Stock UF2 pin resemblance
does not by itself qualify the complete custom board. The
[LSM6DS initialization gate](motion-sensing.md) remains open.

Reverse-side service pads need a usable fixture/access route after carrier
design; their presence alone does not establish assembled accessibility.
Inward-facing LEDs may need an optical opening/light guide or relocation.
Never connect an earth-referenced scope ground to either BTL speaker output.

## Placement and the new working shell profile

The owner's current assumption is:

```text
D(z) = 50 - (16/30) * (z - 13) mm, for z = 13 .. 43 mm
```

Here z is inward from the opening. The near-face 5 mm and curved transition
to z=13 remain adjustable approximations, not measurements extracted from the
photo. The prior 40 mm-at-z22 example is superseded, not newly confirmed.
The photo is not redistributed.

The candidate substrate occupies **z=20.0..21.6 mm**, with components facing
**inward**. At z=21.6, the assumed shell ID is 45.413 mm, leaving about
**1.207 mm radial space around a 43 mm substrate**, before allocating carrier
walls, fit tolerances or insulation. At z=26.6, the assumed ID falls to
42.747 mm; taller parts therefore must be inset rather than placed at the rim.
The PCB's circular area is approximately **1,452 mm2**, not a summed-component
area or a routed minimum.

The current placement uses actual footprint pads, fabrication graphics and
non-text silkscreen bounds, expanded by 0.25 mm per edge or the larger existing
courtyard. Heights are declared screening assumptions, not qualified 3D bodies.
The optimizer begins with source MCU/boost locations but moves parts; **source
routing was not copied**, and local bypass/power-loop placement still needs
electrical refinement. The rectangular-envelope pass reports no overlaps or
non-USB boundary conflicts. USB explicitly requires a shell cutout; this is
not a demonstrated insertion path, cable fit or structural mounting method.

The FreeCAD handoff adds speaker, cell placeholders and carrier geometry.
Use its reported interferences and assumptions rather than inferring a complete
fit from the circle above. The original September 7 study used a 40.9 x 18.5 mm
retail cylinder, not a measured basket/terminal/vent model. The
[September 9 follow-up](../mechanical/studies/2026-09-09-measured-speaker/README.md)
uses the owner's arrived-part stations including **19 mm** overall depth and
preserves the original files. It identifies the magnet/placement and battery
constraints for the next speaker-facing electrical floorplan.

The [routing-readiness handoff](routing-readiness.md) records the owner's
K1C/PLA fit-print plan and the concrete gates between this ratsnest and a
Gerber/BOM/CPL release.

## Native CAD review and remaining DRC

The schematic has **0 ERC errors / 0 warnings**, with the original severity
matrix and exclusions unchanged. The three source imports reproduce **71 / 17 /
6** connected source groups. This is connectivity evidence, not power simulation.

Placement work exposed and corrected specific representation issues:

- The source Q3 drain extension was netless F.Cu graphics. The
  [derivative footprint](../hardware/handbell/Handbell.pretty/DFN2015-3_DrainPad.kicad_mod)
  associates that exact copper polygon with pad 3, retaining the source
  copper/mask/paste unions; [correction record](../hardware/handbell/reports/footprint-correction.json).
- CHG_EN0 uses KiCad's standard bridged jumper with an explicit net-tie group;
  GAIN0 uses its standard open three-pad jumper. Intentional mask bridges are
  declared per footprint, not globally suppressed.
- KiCad 10 embedded pad/text angles remain local to the footprint. Applying
  the root rotation twice created false geometry; the generator preserves
  local angles and correctly mirrors back-face geometry.

The native PCB still has **197 DRC findings plus 203 unconnected items**:
193 unfinished silkscreen/text findings and four source USB NPTH-to-copper
clearances. The latter are **0.1755 / 0.2144 mm versus a 0.25 mm requirement**.
Resolve the actual connector land pattern and fabricator capabilities; do not
shrink holes/pads or weaken the rule just to make the report green.
There are no remaining unintended short, copper-clearance, solder-mask-bridge
or library-mismatch findings in this candidate.

**CLI versus GUI parity:** KiCad 10.0.6's CLI fallback reports 46 "No
corresponding pin" warnings on auto-named/NC nets, although fresh full netlist
exports contain those pins. The paired schematic/PCB editors report **zero
schematic-parity findings** after correcting imported metadata and escaping
pin-name slashes in NC net names. Both the [full GUI report](../hardware/handbell/placement/placement-gui-drc.rpt)
and [byte-bound record](../hardware/handbell/placement/placement-gui-review.json)
are retained; the CLI output is not suppressed or presented as clean.
KiCad's [CLI handler](https://github.com/KiCad/kicad-source-mirror/blob/master/pcbnew/pcbnew_jobs_handler.cpp)
also documents limitations of its separate netlisting fallback; this observed
case is not asserted to be identical to its linked upstream issue.

The inherited project copper-edge setting is not a final fabrication rule.
Establish the selected fab's rule set, routing/current returns, USB geometry,
mounting/keepouts, real body/plug models and BOM before ordering.
One copper layer has not been laid out or established feasible.

## Reproducing the candidate

Use Python 3.10+ and KiCad 10.0.6 with standard libraries, from the repository root:

```powershell
$Cli = "$env:LOCALAPPDATA\Programs\KiCad\10.0\bin\kicad-cli.exe"
python .\tools\place_handbell.py --diameter 43 --front-z 20 --steps 160000
python .\tools\check_handbell.py --kicad-cli $Cli --placement
& $Cli pcb export step --force --board-only --user-origin 100x100mm --output .\hardware\handbell\placement\pcb-substrate.step .\hardware\handbell\handbell.kicad_pcb
```

Stop on a nonzero exit code. The generator refuses to overwrite manual PCB
changes or any tracks/vias/zones. It consumes the current exported schematic
netlist; regenerate that after schematic edits. `--placement` checks native
pad/net correspondence and runs schematic-parity DRC while retaining the
explicit unresolved findings above. The STEP file is substrate-only; it is not
an exact populated-board assembly. FreeCAD regeneration is documented separately.

If CAD/project bytes change, the GUI evidence binding intentionally becomes
stale. Open both editors from the same KiCad manager, run **Inspect > Design
Rules Checker** with **Test for parity between PCB and schematic** enabled,
and save `placement\placement-gui-drc.rpt`. Resolve parity findings, then run:

```powershell
python .\tools\check_handbell.py --kicad-cli $Cli --placement --record-gui-review
```

This binds the fresh report to the current schematic, board and project hashes;
it does not waive the physical DRC findings. Source `JLC_ROTATION` and supplier
fields are inherited metadata, not approved placement corrections or a current
assembly quote/CPL.

An ESP32-S3 variant can reuse the functional audio/power/button interfaces, not
this RP2040 pinout or a presumed free patch of PCB. Radio memory, boot/USB,
current peaks and antenna clearance inside a metal bell require a separate
placement/RF pass before a shared carrier is frozen. QR identity and enrollment
remain firmware/system work, not components added in this revision.
