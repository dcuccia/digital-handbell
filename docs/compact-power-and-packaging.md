# Compact power and packaging review

**Historical review:** the subsequent [0.2 electrical/placement handoff](electrical-reduction-and-placement.md)
implements the reduction and TPS61023 block. The [FreeCAD study](mechanical-feasibility.md)
uses the newer owner-assumed D50 at z13 to D34 at z43 profile. Statements below
about unchanged 0.1 CAD and the earlier hypothetical taper describe this review
at its original publication, not the current repository.

Date: 2026-09-07. **Recommendation: investigate the smaller Adafruit TPS61023
MiniBoost circuit, one suitably rated protected 1S pack, and a printed
near-mouth cartridge before forcing a solid PCB behind the speaker.**
Prefer one-face assembly on two copper layers; neither a 40 mm disk nor an
annular outline has been demonstrated routable.

This records engineering review and owner-approved next-revision scope.
**The published native schematic remains 0.1: unboosted and not yet reduced.**
No new boost CAD, mechanical solid, routed board, selected cell, assembled quote
or speaker power qualification is claimed. No parts have been ordered.

## Approved scope versus remaining choices

| Area | Next-revision direction | Still to resolve |
|---|---|---|
| Expansion/RGB | Remove Feather headers, servo, large multifunction terminal, NeoPixel/level-shifter branch and STEMMA QT | Explicit component/net changes while preserving shared support circuits |
| Button | Two-pin keyed harness, GPIO19 `BUTTON` net to GND | Exact connector, released-state pull-up, cable protection and debounce; stock alias is `EXTERNAL_BUTTON`, not `board.BUTTON` |
| Indication | Hardware charge LED plus ordinary GPIO13 status LED | Current/visibility and firmware patterns; GPIO13 LED is not a reset indicator |
| Audio | Mono, 4 ohm, electronics sized for the 3 W high end; independent mute and deliberate channel selection | Boost implementation, digital limits, noise, distortion, speaker qualification |
| Service | Compact power/control/I2S/IMU/debug pads | Accessible probing/programming after assembly; whether BOOT/reset switches become pads |
| Packaging | Printed cartridge and grille, preassembled outside the shell | Measured axial profile, speaker basket, cell envelope, connector access and tolerances |
| Wireless | Early ESP32-S3-MINI enclosure experiment; sound programming, QR identity and optional practice telemetry | Exact module/memory/build, antenna location, power budget and protected updates |

Detailed preservation rules are in [architecture](architecture.md). In
particular, retain the IMU pull-ups when removing STEMMA QT, preserve C18
on VCORE and C16 on the shared amplifier rail, and account explicitly for
Q1/Q2/source selection before replacing their functions.

## Boost comparison: reuse a coherent circuit

Both sources credit **Limor Fried/Ladyada for Adafruit Industries** and carry
**CC BY-SA 3.0 Unported**. They are source-inspected, catalog-only candidates;
their CAD is not yet vendored/imported into the handbell.

| Property | [2030 PowerBoost 1000 Basic][2030] | [4654 MiniBoost TPS61023][4654] |
|---|---|---|
| Actual controller | TPS61030RSAR, 4 x 4 mm QFN-16 | TPS61023, 1.2 x 1.6 mm SOT563 |
| Pinned source | [`493d06d70537ce418355b395bb251a661d683150`][2030-source] | [`82b5a33a1900a5c13849029bc84e7856a44086e0`][4654-source] |
| Source inductor | 6.8 uH; 8 x 8 mm footprint | 1 uH; 5 x 5 mm body drawing, `INDUCTOR_5X5MM_TDK_VLC5045` footprint |
| Exact inductor MPN / height | Not specified by the source value/footprint | Not specified; the footprint's family name is not a complete approved MPN |
| Source input capacitors | 10 uF + 100 nF | C2 = 22 uF, 0805 |
| Source output capacitors | 2.2 uF + two 100 uF/1210 | C1/C3 = 22 uF each, 0805 |
| Divider | 1.87 Mohm / 200 kohm: nominal 5.175 V | R2/R3 = 732 kohm / 100 kohm: approximately 5 V, **not the advertised 5.2 V** |
| Source enable default | 200 kohm pull-up to battery | R1 = 100 kohm pull-up to VIN |
| Switch-current limit | 4 A typical **peak** | 3.7 A typical **valley**; neither number is output current |
| Shutdown | True input/output disconnect | True input/output disconnect |
| Battery charging | None | None |

**New source/prose discrepancy:** MiniBoost's product/README says 5.2 V, but
both pinned `.sch` and `.brd` use 732 kohm/100 kohm. TI's [datasheet][tps61023],
pp.5 and 12-13, gives the approximately 0.6 V feedback reference and the same
divider in its 5 V example. Using the listed typical PWM/PFM references gives
about **4.95/5.00 V**, before resistor tolerances and other errors. This is a
documentation/source mismatch, not a measured finding about a purchased unit.
Use a deliberately specified **5 V-class audio rail**, with a full tolerance,
pass-through and overshoot budget below the MAX98357A's 5.5 V operating maximum.
Do not silently adopt 5.2 V because the product title says so.

MiniBoost's source has eight electrical parts on the top face. Their existing
placement spans approximately **9.22 x 9.50 mm**, using pad and non-text
body/silkscreen bounds; a 0.25 mm allowance per outer edge makes this about
**9.72 x 10.00 mm**. This excludes the breakout header, mounting hole, fiducial
and graphics. The whole source board is 11.43 x 17.78 mm. The smaller rectangle
is a **placement screen**, not a thermally qualified converter area or
permission to cut away reference ground/return copper.

Adafruit reports 0.8 A output at 3.0 V input, 1.1 A at 3.5 V and 1.4 A at
4.0 V, using a bench supply/electronic load. Those results support evaluating
the approximately 0.67 A amplifier demand calculated below. They are not
guaranteed production limits at arbitrary cell impedance, temperature,
layout or simultaneous radio load.

The original PowerBoost is a useful, documented boost reference, but its
larger controller, inductor and output capacitors are less attractive here.
Start from MiniBoost's coherent power block rather than swapping one tiny
inductor into PowerBoost and assuming equivalent behavior.

### Integration requirements

Keep charging, system source selection and the 3.3 V logic/IMU branch distinct
from the boosted audio branch. Neither booster is a charger or a complete
system power manager. Review VHI source-switch/diode current and thermal losses
under the new load; a previously adequate unboosted path is not automatically
adequate for boosted audio.

Replace the breakout's default-on enable bias with an intentionally reviewed
reset/default state. Do not attach a 3.3 V MCU directly to an enable net still
pulled up to raw USB/battery without checking voltage/backfeed behavior.
True disconnect stops the normal input-to-output path; it does not discharge
the output capacitor immediately or prove isolation from signal-pin paths.
The TPS61023 also passes input through rather than buck-regulating when input
exceeds the selected output. Review USB-only, battery-only, charge-and-play,
unplug/replug, startup, brownout and fault states.

Keep switching-current loops compact, place the IC/inductor/capacitors as a
coherent block, isolate feedback from SW, and retain a continuous ground
reference and thermal copper. Both controllers use light-load power-saving
behavior; switching frequency alone does not establish inaudible operation.

## Cell current: capacity is not the discharge rating

For **3 W electrical power into the speaker**, assume 90% amplifier efficiency
and 78-88% boost efficiency as a planning range. This is not a guaranteed
efficiency range across all voltages.

```text
Audio-only cell current = 3 W / (Vcell * 0.90 * boost_efficiency)
Amplifier supply demand = 3 W / 0.90 = 3.33 W
At 5 V: approximately 0.67 A; at 5.2 V: approximately 0.64 A
```

| Cell voltage | Audio-only cell current |
|---|---:|
| 4.2 V | 0.90-1.02 A |
| 3.7 V | 1.02-1.16 A |
| 3.0 V | 1.26-1.42 A |

Add MCU/IMU/radio consumption, source-path losses and startup/transient margin.
For scale, 0.2 W additional cell-side consumption adds about 48-67 mA across
these voltages; **0.2 W is an example, not a measured board budget**.
The assumed full-output boost loss alone is about **0.45-0.94 W**, plus
approximately 0.33 W amplifier loss. Enclosed thermal behavior matters even
with a physically small controller.

**500 mAh is capacity, not a 0.5 A discharge limit.** For example, a documented
500 mAh, 4C continuous-rated pack corresponds to 2 A. A pack genuinely limited
to 0.5 A continuous is insufficient for this scenario; two such cells would
still be insufficient near depletion. Prefer **one factory-protected 1S pack**,
initially screening for at least **2 A continuous capability** and documented
transient/protection/connector margins. That may be a single cell; 1S2P is not
inherently necessary. If a parallel pack is warranted, use a properly engineered
factory pack, not novice wiring of separate charged pouches.

Capacity/runtime, physical envelope, charge-current limit, protection trip
behavior and cell-temperature requirements are separate selection inputs.
The boost's low operating-voltage capability is **not LiPo cutoff**.
Neither the existing roughly 196 mA charger setting nor 3 W play-while-charging
is approved. A default USB source budget can be exceeded by audio plus logic
and charging; USB-C CC pulldowns alone do not authorize arbitrary input current.

## Inductors and 0402: shrink selectively

The [WE-MAIA family][maia] is a candidate family, not a selected drop-in part.
The initial lower-risk path is the existing MiniBoost-sized magnetic footprint.
An exact smaller alternative requires effective inductance versus DC current
and temperature, tolerance, saturation-current definition, RMS/temperature-rise
rating, hot DCR, core loss at switching frequency, height and land-pattern review.
Startup/overload current matters, not just steady audio demand. TPS61023's
valley-limit figure must not be compared directly with an inductor's peak
saturation limit.

TI specifies 0.37-2.9 uH for TPS61023 and uses 1 uH in its example. That is not
permission to choose any value in the range without recalculating ripple,
peak current and loop behavior. A 6.8 uH PowerBoost inductor and a 1 uH MiniBoost
inductor belong to different reviewed controller designs, not interchangeable
size choices. Effective output capacitance and feed-forward compensation also
need review; TI recommends compensation treatment above 40 uF output capacitance.

The existing handbell already has **38 0402 footprints**, with five 0805 bulk
capacitors. Ordinary resistors and suitable bypasses can use 0402; bulk
capacitors require actual voltage/DC-bias/ripple/temperature evidence. The
MiniBoost source uses 0603 resistors and 0805 capacitors; its passives are not
already uniformly 0402. Magnetics, connectors and power/thermal copper will
not become smaller simply by standardizing resistor footprints.

## Mono, gain and silence

The [MAX98357A datasheet][max98357], pp.5, 7, 17-18, 28 and 33, gives typical
5 V / 4 ohm results of **2.5 W at 1% THD+N** and **3.2 W at 10% THD+N** under
its specified load/test conditions. Designing for the 3 W high end is reasonable;
calling it 3 W clean continuous output would not be.

Keep **9 dB gain** as the initial evaluation setting, with digital headroom
and a speaker-specific level ceiling. More gain cannot create battery-voltage
headroom. A 3 W sine into 4 ohm is 3.46 Vrms and 0.87 Arms; connector/wire
selection must account for peak and RMS current, not just nominal impedance.

The current 1 Mohm R18 and nominal 100 kohm internal SD_MODE pulldown produce
approximately 0.273/0.336/0.382 V at 3.0/3.7/4.2 V supply. The published lower
mode boundary can be as high as 0.355 V; therefore the copied battery-dependent
average-channel bias needs review. Raising the rail changes the operating
point again. This is an identified margin concern, not a measured failure.

For one speaker, prefer an explicitly selected **left I2S slot with independent
shutdown** rather than unnecessarily relying on a narrow analog averaging
window. Firmware must put mono audio in that slot, or duplicate it in both.
One candidate is an amp-rail-referenced mode pull-up plus a small external
pull-down transistor with a default-muted control state. This avoids directly
presenting the amp rail to a 3.3 V GPIO; exact parts, thresholds, logic polarity,
reset behavior and unpowered states still require schematic review.

Fade/drain audio before mute, then sequence clocks and power. Do not stop
LRCLK while BCLK continues; the datasheet warns of possible unexpected/DC
output. Establish readiness before unmuting on startup, and cover resets,
firmware reload, faults and USB changes. Neither BTL output may be tied to GND.

## Packaging and manufacturing conclusion

The [mechanical report](mechanics-and-manufacturing.md) includes owner estimates,
retail drawing tolerances, an original diagram and reproducible calculations.
The essential distinction is **70 mm at the mouth versus much less behind an
18.5 mm-deep speaker**. The 40 mm internal shell measurement has no established
axial station, so a real profile is still required.

The earlier **45-55 mm** screen was for a reduced **unboosted RP2040**, not an
S3 or boosted design. Its planning-envelope total was about 721 mm^2 after the
listed header/servo/RGB removals; removing STEMMA subtracts another ~34.5 mm^2.
The new button/speaker interfaces, mute and boost still add area. Connector
and BOOT/reset choices may save some back. These sums do not demonstrate a
40 mm routed board, and the earlier range was not a proven minimum either.

A hypothetical **66 mm OD / 43 mm aperture** board offers 1,969 mm^2 gross
area, but only an 11.5 mm-wide band. Its S3-MINI body cannot fit wholly in that
band; explore an offset speaker/aperture or wider electronics bay. A shallow
printed mouth extension may make component height and antenna placement easier.
Do not assume the handle is hollow or usable.

Prefer a bonded mounting interface with a **removable printed cartridge,
speaker baffle and grille**, not a permanently glued-in battery. Model assembly
outside the bell, USB support/slot access, insulation, vent and cone clearance,
grille open area/stiffness, cell retention and service access.

[JLC's official table][jlc] confirms Economic single-face placement and Standard
single/double-face placement; a one-face design can still need Standard because
of the selected BOM. If two faces become justified, factory assembly is a real
option. Do not assume a bottom-terminated molded inductor is easy to hand solder,
or move it across the PCB without the rest of its critical-loop layout review.
Keep two copper layers as the first attempt; a single copper layer remains
unsubstantiated and is not the compact, low-risk baseline.

## Tooling and next engineering gate

KiCad schematic/export tooling is available. Parametric mechanical CAD
(for example FreeCAD with STEP/STL) and SPICE model/setup work are possible
follow-on workflows, but **neither a 3D-CAD nor an LTspice workflow has been
configured/exercised for this project yet**.

SPICE need not be a prerequisite for a faithful, source-backed power block.
It becomes useful for particular model-supported stability/transient questions.
Neither simulation nor reference reuse replaces current-limited bench evidence
for startup, low-cell transients, shutdown/backfeed, clipping/noise, EMI and
temperature, or physical acoustic/fit evidence.

Proceed with electrical reduction and a **placement/3D feasibility pass**, not
final routing. The blocking freeze inputs are the shell's depth-indexed profile,
speaker basket/terminal and power evidence, actual cell envelope/rating, charge/
USB operating policy, and exact connector/power MPNs. RF must be tried with the
speaker, cell and real shell before an S3 carrier is frozen. Sound generation
stays local; file updates and optional telemetry must not determine strike timing.

Tracking: [E01 #1](https://github.com/dcuccia/digital-handbell/issues/1),
[E04 #4](https://github.com/dcuccia/digital-handbell/issues/4),
[E05 #5](https://github.com/dcuccia/digital-handbell/issues/5),
[E07 #7](https://github.com/dcuccia/digital-handbell/issues/7),
[E12 #12](https://github.com/dcuccia/digital-handbell/issues/12).

[2030]: https://www.adafruit.com/product/2030
[4654]: https://www.adafruit.com/product/4654
[2030-source]: https://github.com/adafruit/Adafruit-PowerBoost-1000-PCB/tree/493d06d70537ce418355b395bb251a661d683150
[4654-source]: https://github.com/adafruit/Adafruit-TPS61023-PCB/tree/82b5a33a1900a5c13849029bc84e7856a44086e0
[tps61023]: https://www.ti.com/lit/ds/symlink/tps61023.pdf
[max98357]: https://cdn-shop.adafruit.com/product-files/3006/MAX98357A-MAX98357B.pdf
[maia]: https://www.we-online.com/en/components/products/WE-MAIA
[jlc]: https://jlcpcb.com/capabilities/pcb-assembly-capabilities
