# Initial power-routing review

September 13, 2026. Scope: the first routed checkpoint, PCB SHA-256
`075c7b7cb0a98e302af29f5985bbf020111df5b1be385e5ebfa61be236b04250`,
manifest `cc935ef468e8fb8d0fda5d55010e8883eab1f8b578078f2dcc4f77fe456fe69f`.
The owner explicitly requested extra care with high-current routes and widths.
This independent review used actual KiCad 10.0.6 copper/pad geometry and
connectivity, not only the generated route-group names.

**Result: rework is required before freezing this power layout.** The strongest
finding is the boost output-capacitor switching loop, not a demonstrated
trace-overheating failure. The existing 148 unconnected items remain declared
unfinished work; this review does not turn the checkpoint into an operable or
fabrication-ready board.

## Required corrections

### Boost output-capacitor hot loop

U5's VOUT/GND pins face the inductor side while C27/C28 are on the opposite
side. Neither capacitor has an all-front-copper return to U5.4. Both require
F-B-F transitions through 0.30 mm drilled vias, and U5.6 reaches the output
copper through narrow branching exits. The SW escape occupies the side needed
for a compact VOUT-capacitor-GND loop.

Later same-net overlaps create real shortcuts. Approximate connected
centerline walks are 4.0/5.3 mm from U5.6 to C27.1/C28.1 and 3.0/4.1 mm from
their ground lands to U5.4, excluding vertical barrel length and treating pads
as connection regions. Longer generated branch totals are **not** unavoidable
series paths.

The topology nevertheless resembles the explicitly discouraged bottom-layer
capacitor-ground connection and wrong-side SW routing in
[TI SLVAES4, pages 4-5](https://www.ti.com/lit/an/slvaes4/slvaes4.pdf).
[TPS61023 datasheet section 10.1, page 18](https://www.ti.com/lit/ds/symlink/tps61023.pdf)
identifies this fast-edge output loop as the most critical path.

Try a local U5/L1/C27/C28 orientation/placement change permitting short, broad,
direct F-side output-capacitor connections; adjust the SW escape accordingly.
Width increases or extra remote vias alone do not resolve this topology.
Preserve the immutable placement and initial-routing checkpoints. Any moved
component requires an explicitly updated manifest and mechanical rebind.

Native evidence in `handbell.kicad_pcb`: U5.6 exits at lines 21302-21304 and
21571; positive capacitor routing at 21305-21317; capacitor grounds at
21318-21347; transitions at 21731 and 21741-21746.

### Protector sense pickoff

R26.2 reaches the correct R27.2 system-side net, but its 13.245 mm fine route
merges into U2/U3/shared-ground conductors before the shunt, including near
(-10.1,+4.8). It samples a distributed conductor rather than a quiet shunt
pickoff. Shared load currents can affect the detected voltage against an
approximately 100 mV threshold.

This is not a wrong-net finding or a claim that the unfinished amplifier
currently sends 2 A through that fine trace. Route R26.2 independently to a
deliberate R27.2 pickoff, avoiding other load-return joins before that point.
Give the still-open U6.VSS connection an intentional raw-negative source
reference; never bridge CELL_NEG to protected GND. Also shorten/rework the
indirect R24 ground branch through the switching return network.

Native evidence: sense routing at lines 20896-20914, shared returns at
21509-21532 and 21564, R24 branch at 21361-21380.

## Actual copper inventory

Coordinates below are board-relative; native coordinates add 100 mm to X/Y.
Drawn lengths sum the specified segments. Pads, overlaps and parallel branches
can shorten the electrical path; these are not equivalent-resistance results.
Resistance examples use 35 um copper at nominal 20 C and
0.0172 ohm.mm2/m resistivity, before unspecified manufacturing tolerances.

| Section | Actual geometry and current interpretation |
|---|---|
| Cell/source trunks | BT1-VBAT-Q3-VHI-Q1-V+ and BT2-Q5 are not routed. Their entire source/return path still needs continuous review. |
| Q5 source fanouts | Two 0.704 mm x 0.1778 mm Source1 escapes and two 0.772 mm x 0.1778 mm Source2 escapes, separate 2.7 mm x 0.6 mm B buses, one 0.60/0.30 mm via per escape. Full drawn neck estimates are 1.95/2.13 mOhm each; much lies within pad/via copper. Do not assume equal current division. |
| R27.1-Source2 bus | 5.264 mm of 0.6 mm F/B copper and one common transition at (-14.7,+9.55), under the resistor body. Drawn copper is about 4.31 mOhm, or 8.6/12.9 mV at 2/3 A, excluding source branches/barrels. |
| Boost GND-R27.2 | 11.317 mm of 0.8 mm body, transitions at (-4.25,+17.2) and (-7.95,+13.5). Body is about 6.95 mOhm, or 13.9 mV at 2 A. Two hypothetical 25 um-plated barrels add about 2.34 mOhm. This is not a 40 mm path. |
| L1.P$2-U5.5 SW | 2.977 mm drawn: 2.651 mm at 0.1778 mm and 0.326 mm at 0.6 mm. After pad/broad-copper coverage, about 0.65 mm remains clearly exposed and narrow near U5.5, approximately 1.8 mOhm. It carries inductor ripple/current, not only gate current. Shorten/widen the necessary escape without unnecessarily enlarging SW copper. |
| C26.1-L1.P$1 | 11.698 mm drawn, including 9.641 mm at 0.6 mm around the inductor. That broad portion is about 7.90 mOhm. Future source-feed placement determines sustained versus capacitor-ripple current. |
| C26.1-U5.3 VIN | 3.137 mm drawn, mixed widths. This is the IC-bias/local-decoupling spur, not the inductor's full input-current path. |
| U5.6-C27/C28 | Mixed widths with about 0.50/0.66 mm exposed narrow centerline on alternate exits. Capacitor returns require B transitions. Assess pulse/RMS current and inductance; neither entire drawn neck is the sole series resistor. |
| VAMP distribution | 38.409 mm authored 0.6 mm body, approximately 36.2 mm overlap-aware connected walk, no vias. Authored body is about 31.46 mOhm: 24 mV at 0.75 A or 31 mV at 1 A, before exits/return. The dedicated amplifier return remains unfinished. |
| U4 local bypass/grounds | Positive bypass branches are 2.592/2.497 mm drawn. Ground pins have roughly 0.35 mm exposed 0.1778 mm gaps between lands; longer recorded necks largely overlap the thermal pad. Four 0.604/0.35 mm thermal vias feed a small local mesh, not a board-wide ground plane. Bypass ground lands and the main return remain open. |
| BTL/filter branches | U4.9-FB1.1 is 3.689 mm drawn, with broad copper bypassing much apparent fine necking. FB1.2-C22.1 and FB2.2-C21.1 are 2.645/2.111 mm, mostly fine copper. Capacitor spurs need not carry speaker current if the future broad speaker trunks tee in appropriately. |

Native line groups for that inventory: Q5 20809-20814/21727-21730;
R27 return 21669-21704/21751; boost return 20815-20827/21731-21732;
SW 21245-21254; C26-L1 21265-21291; VIN 21255-21264;
VAMP 21571-21627; U4 21381-21432/21723-21726; BTL 21433-21471.

No surviving 8.3 mm minimum-width main protection return was found. The
originally recorded 1.027/1.301 mm boost-return endpoint necks are also
bypassed by later 0.6 mm copper physically contacting U5.4 and R27.2
(lines 21335-21336, 21537-21541, 21565-21568). Treating their route-group
labels as isolated full-current bottlenecks would overstate the problem.

U2/U3 ground-pin branches are not automatically 2 A load or 196 mA charging
conductors. Their eventual current depends on shared connections, not their
endpoint names.

## Working review assumptions for the next candidate

These are provisional engineering targets under the owner's development
authorization, not owner-qualified operating ratings:

| Quantity | Planning basis |
|---|---|
| Cell/source/protection copper | 2 A continuous screen and 3 A sensitivity case; neither is a guaranteed permissible operating current or protection setting. |
| 5 V distribution | 1 A screen. A 3 W audio goal with assumed 80-90% amplifier efficiency implies about 0.67-0.75 A average at 5 V. |
| Speaker conductors | Ideal 3 W into 4 ohms implies 0.866 A RMS and 1.225 A peak per conductor; neither speaker terminal is GND. |
| Boost ripple | Provisional 1 uH/typical 1 MHz gives about 1.23 A peak-to-peak for idealized 2.8 V to 5 V conversion. A 2 A mean could reach about 2.6 A peak. Actual part inductance, saturation, frequency, startup and limiting remain open. |
| Copper | 35 um nominal for calculations; obtain minimum finished copper, width and barrel plating before manufacturing. The label "1 oz" alone is insufficient. |
| Resistance sensitivity | Hypothetical 30 um/60 C conductor gives about 1.35 times the 20 C/35 um resistance before width tolerance. 60 C is a calculation case, not an allowed cell/enclosure temperature. |
| Copper-only cell-path drop | Provisional target no more than 50 mV round-trip at 2 A, with a separately stated review if it cannot be met. Contacts, MOSFETs and the deliberate 33 mOhm shunt are additional, not hidden inside this budget. |
| Copper-only 5 V drop | Provisional target no more than 100 mV round-trip at 1 A, separate from the cell/source path. |
| Conductor heating | Provisional rise target no more than 10 C, subject to an agreed local-ambient envelope and suitable IPC-2152-based analysis/measurements. No IPC curve-derived rating has been established. |

At assumed 1.6 mm board thickness and 25 um wall plating, a 0.30 mm barrel is
about 1.17 mOhm. Its DC resistance does not qualify temperature, switching
inductance or fabrication reliability. The protector's threshold/tolerance,
FET resistance, shunt and operating temperature do not constitute a precise
2 A current limiter or guarantee 3 A audio operation.

## Rework order and remaining gates

Fix the boost hot loop and protection pickoff first. Reserve paired supply
and return paths before spending more area on signal routing. Prefer broad
trunks/local copper where available, retaining narrow copper only for genuine
low-current branches or bounded necessary package escapes.

Complete the amplifier bypass returns and dedicated main return, and provide
useful boost/amplifier ground spreading/stitching. Review an additional
parallel transition on the common Q5 return where geometry permits.
[MAX98357A/B Rev.7, page 33](https://cdn-shop.adafruit.com/product-files/3006/MAX98357A-MAX98357B.pdf)
calls for wide supply/output/ground conductors and bulk-capacitance
consideration with long supply traces.

Two layers remain a reasonable next attempt; this review does not establish
a need for four layers or a larger board. Preserve the contact copper/base
exclusions and central corridor's limited role. Never rely on solder mask as
qualified raw-cell insulation or bridge CELL_NEG to protected GND.

The 13 thermal-pad vias, under-R27 transition, minimum copper/plating,
inductor/capacitor current characteristics, unfinished routing, USB-clearance
findings and existing component/fault/charge/physical-fit gates remain open.
No fabrication, live-cell or child-use approval follows from this review.

Related tracking: E04/#4, E05/#5 and E07/#7.
