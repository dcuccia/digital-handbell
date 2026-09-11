# T8 electrical revision: placed, protected-return draft

**2026-09-11 — native KiCad engineering draft, not permission to install a live
cell, charge, fabricate or distribute a kit.** Open the separate
[T8 project](../hardware/handbell/iterations/t8-protected-draft/README.md).
The wing project, original print snapshots, source libraries and reference
projects remain unchanged. The next owner checkpoint is the **complete new
FreeCAD assembly before routing**.

## Implemented scope and limits

- U1 becomes **Winbond W25Q16JVUXIQ TR**, 16 Mbit / 2 MB, with a new UX
  USON2x3 footprint. It is not the inherited 4x4 footprint.
- BT1/BT2 are two **Keystone 254 revision C SMT contacts** for the provisional
  Vapcell T8 button-top geometry. X1 is removed from **all three schematic
  units and the board**, not retained as a parallel bypass inlet.
- U6 **BQ29700DSER**, Q5 **CSD83325L**, and six passives implement a separate
  whole-cell fault-protection return path. The circuit is native schematic
  and pad/net data, not merely a diagram or a BOM suggestion.
- There are **83 fitted components: 70 F and 13 B**, plus 18 copper-only
  features, C29 DNP and two board-only mounting pads: **104 references**.
  The 325 physical pad records include two USB NPTH records and one flash
  paste-only aperture; 322 have copper pad numbers.
- Core, flash origin, crystal, boost and amplifier cluster poses are retained
  from the wing placement. U1's smaller body changes its envelope, not its
  signal numbers. Other F-side parts are re-placed around the new protection
  block. C16 stays adjacent to the amplifier PVDD area.
- The substrate keeps the D43 main body and M2 mounting centers, adding only
  the contact-pad support tabs and a supported USB tongue described below.
  It still has **no tracks, vias or planes**.
- The final coordinated frame moves the whole internal stack6.25 mm toward
  the mouth: Fz14.25/Bz15.85, cell center25.63, speakerfront-6.25.
  Only X6 moves in XY, another2.75 mm outward; the other native poses are
  frozen. The selected1.0 mm guard is a nominal fit target, not insulation
  or live-cell qualification.

The eight protection parts occupy roughly an **8 x 6 mm planning region**,
including local component clearances. This is a placement result, not routed
area, a thermal design or a production price. It avoids a fuel gauge,
balancing and a new charger, none of which is necessary just to implement
the independent protection function.

**Important tradeoff:** the selected conservative overcurrent network does
**not guarantee 2 A continuous operation at low cell voltage/hot silicon**.
It intentionally avoids the much higher fault threshold obtained from the
tiny FET alone. Low-cell loud-note nuisance shutdown and the exact operating
current budget remain prominent qualification gates, not silently met targets.

## Why TPS61023 protection is not substituted

TPS61023's approximately 5.7 V **output** OVP and 3.7 A typical **valley
switch-current** limit do not provide cell overvoltage/undervoltage fault
disconnect or protect the charger, always-on LDO, battery wiring/contact
shorts or the whole instrument's discharge current. Its input operating
range extends below the cell's discharge endpoint.

The retained MCP73831 provides normal CC/CV charging and charger die thermal
management. Neither its normal 4.2 V regulation nor its reverse leakage
blocking is an independent whole-cell fault-protection stage.

## Exact implemented topology

`VBAT` is the common positive terminal. **`CELL_NEG` is raw B-, not GND.**
Every retained load and the charger use protected system `GND`; so do USB
**signal-ground** pins, recovery ground and both mounting pads. The retained
USB shell-anchor pads **X6.M1-M4 are unassigned**, not connected to GND in the
native design. No shield bond has been reviewed or added. Treat the shield
as a conductive external interface requiring insulation regardless of any
connection made by a mating cable/host; this is not a `CELL_NEG` bypass.

```text
BT1 / cell+ ------------------------------------------------ VBAT / system+
          |                                                   |
          +-- R25 330R --> U6.BAT; C30 100n to CELL_NEG         |
                                                              |
BT2 / cell- -- CELL_NEG -- S1 [Q5: two common-drain N-FETs] S2 -- R27 33m -- GND
                          G1 = U6.DOUT              G2 = U6.COUT             |
                U6.VSS = CELL_NEG                    U6.V- <-- R26 2.2k ---+
```

R28 = 5.1 Mohm joins G1 to S1; R29 = 5.1 Mohm joins G2 to S2. These follow
TI's external high-impedance gate-discharge recommendation. Section 5.1 also
describes internal high-impedance discharge paths; the external pair is
deliberately included instead of relying on that description alone.
The FETs' common drain is internal and **has no external PCB pad**.

### Reviewed physical pin map

| Part / land | Function / net |
|---|---|
| U6.1 | NC, explicit schematic NC marker and real unconnected copper land |
| U6.2 | COUT / `PROT_COUT` |
| U6.3 | DOUT / `PROT_DOUT` |
| U6.4 | VSS / `CELL_NEG` |
| U6.5 | BAT / `PROT_BAT`, behind R25 |
| U6.6 | V- / `PROT_VM`, through R26 to system GND |
| Q5.A1, Q5.C1 | Source1 / `CELL_NEG` |
| Q5.B1 | Gate1 / `PROT_DOUT` |
| Q5.A2, Q5.C2 | Source2 / `PROT_FET_RETURN` |
| Q5.B2 | Gate2 / `PROT_COUT` |
| R27.1 / R27.2 | `PROT_FET_RETURN` / GND |
| BT1, both lands numbered1 | VBAT |
| BT2, both lands numbered1 | `CELL_NEG` |

Q5 uses TI's **A/B/C row, 1/2 column physical identifiers**, not invented
1..6 mappings. Top view: column1 is left; A is top; B contains the gates.

The body diodes point **S1 → common drain ← S2**:

- **Discharge:** conventional return current travels GND → R27 → S2 →
  common drain → S1 → cell-. DOUT low turns off Q5's S1 transistor,
  whose body diode opposes that return. Discharge is interrupted even
  though the other transistor can remain on.
- **Charge:** current travels cell- → S1 → common drain → S2 → R27 → GND.
  COUT low turns off the S2 transistor; its body diode opposes charging.
- The opposite diode permits the intended recovery direction after UVP/OVP.
  Actual restart, load removal, charger insertion and depleted-cell behavior
  still require the TI state-machine/bench review; no arbitrary automatic
  recovery promise is made.

Removing both FET conduction paths does not provide infinite galvanic
isolation: the protector's bias, sense and high-value gate circuits still
exist. It removes the intended **high-current** return. Never bridge B- to
GND with a scope ground, USB shell, metal fastener, battery can or the bell.
The raw cell and contacts still require short-safe insulation; a short
directly across the raw contacts or a loose cell lies outside this cutoff.

The original charger pin3 still reaches VBAT through closed CHG_EN0;
pin2 is system GND. Q3/D4 source selection, U2 always-on 3.3 V logic supply,
Q1/Q2/GPIO23 audio switching and all retained pin/net assignments are
unchanged. Thus USB insertion does **not create a board-designed raw-negative
bypass**. External accidental grounding can still defeat the low-side stage.

## Threshold, current and thermal calculations

Sources: TI **SLUSBU9I, August 2024**, device table p3, pin descriptions p4,
threshold/timer tables p6, design/layout pp19–22; TI **SLPS494C,
November 2023**, electrical table p3 and package drawing 4221674/C.
These are manufacturer specifications, not project measurements.

| BQ29700 function | Nominal | Specified spread / delay |
|---|---:|---|
| Overcharge detection | 4.275 V | ±10 mV at25°C; ±20 mV at0..60°C; 1.25 s ±20% |
| Overdischarge detection | 2.800 V | ±50 mV at25°C; 144 ms ±20% |
| Discharge overcurrent | +100 mV across V-/VSS | ±10 mV at25°C; ±15 mV at-40..85°C; 20 ms ±20% |
| Charge overcurrent | -100 mV | ±10 mV at25°C; ±15 mV at-40..85°C; 8 ms ±20% |
| Short-circuit detection | +500 mV | ±100 mV at25°C; 250 us ±50% |

The normal 4.20 V charger target remains below the independent fault
threshold. **4.275 V is not a recommended T8 charge voltage.** Applicability
of the fault excursion, delay and recovery to the supplied cell is still
an electrical-review gate. UVP's nominal 2.8 V is above Vapcell's stated
2.5 V discharge endpoint; cell sag can trip earlier under load.

R25/C30 have nominal RC = 33 us. At the protector's specified 5.5 uA maximum
normal supply current, R25 alone drops approximately 1.82 mV, increasing
the raw-cell detection voltage by that amount. Do not turn these tabulated
conditions into a guaranteed full-temperature cell cutoff range.

The selected **Panasonic ERJ-6BWFR033V**, 33 milliohm ±1%, 0805, 0.5 W,
is in series with the entire return. V- therefore senses **R27 + both FETs
+ copper**, not R27 alone. No analog current regulator is created.

| Gate-bias example,25°C | Q5 total source-source resistance | Nominal OCD estimate |
|---|---:|---:|
| VGS=3.8 V | 10.9 milliohm typical; 8.8..13.0 specified | 100/(33+10.9) = **2.28 A** |
| VGS=2.5 V | 17.5 milliohm typical; 12..23 specified | 100/(33+17.5) = **1.98 A** |
| VGS=4.5 V, comparative only | 9.9 milliohm typical; 7.9..11.9 specified | 100/(33+9.9) = **2.33 A** |

Actual gate drive is generated from the cell/protector and is not guaranteed
equal to those example biases. The cell cannot supply a 4.5 V gate bias;
that row provides the lowest tabulated resistance used in a deliberately
conservative comparison.

At25°C, combining 90..110 mV OCD with 32.67..33.33 milliohm R27 gives:

- At the 3.8 V resistance bounds: **1.94..2.65 A**.
- At the 2.5 V resistance bounds: **1.60..2.46 A**.
- Using the lowest tabulated FET resistance, 7.9 milliohm, gives a conditional
  upper estimate **2.71 A**. This is **not** an all-temperature guaranteed
  maximum: cold FET resistance, resistor drift, gate bias, sense offset and
  copper are not bounded by that single25°C calculation.

The 3 A cell CDR is **not a protection-trip setting** or a permitted pulse
specification. The selected conservative range may interrupt a sustained
2 A low-cell load. Removing R27 would give a nominal ~9.17 A OCD at3.8 V:
small FET area alone does not provide an appropriate current limit.
Do not lower R27 simply to stop audio dropouts without repeating the
cell/fault/current/thermal assessment.

At2 A, R27 dissipates132 mW; Q5 about44 mW at the3.8 V typical resistance.
At3 A those values become297 mW and98 mW. At2 A and the2.5 V maximum FET
resistance, Q5 dissipates92 mW. PCB heat spreading, enclosure temperature,
resistor derating, contact resistance and pulse-energy limits remain open.

The nominal500 mV short threshold divided by43.9 milliohm is about11.4 A,
**not the actual short current**. Actual fault current depends on cell
impedance, contacts, copper, gate transitions and source voltage. The maximum
specified375 us detector delay exceeds the conditions for Q5's headline
52 A pulse figure (≤100 us, limited duty); **that pulse figure does not prove
survival here**. Review the actual transient SOA, resistor pulse energy,
gate transients and terminal faults before live-cell testing.

## Charging, temperature and reversed-cell gates

The charger remains **MCP73831T-2ACI/OT**, R8=5.1 kohm:
approximately196 mA nominal with AC-option termination at7.5%, or14.7 mA.
This is below Vapcell's500 mA standard charge current, but **not its published
100 mA termination profile**. The historical50 mA review value is not a
replacement approval. Do not silently change R8, substitute charger suffixes
or approve charging from current alone.

**No automatic cell-temperature charge inhibit is implemented.** Charger
die thermal regulation is not cell-temperature monitoring. No charge safety
timer is added. The current permitted workflow is an **inert fit study**;
ordinary unsupervised/enclosed charging is not approved. Resolve the supplied
cell's charging limits, monitoring/inhibit strategy and fault behavior before
powering a battery prototype.

**No reverse-cell electronics are claimed.** A reversed removable cell can
violate the protector/charger/system ratings; the330 ohm filter is not a
reverse-battery solution. The mechanical positive-button access/keying
proposal must be tested with the actual terminal and wrong-cell/reversed
insertion cases, or a separately reviewed reverse-insertion stage added.
Printed polarity text and an unqualified button recess do not close this gate.
CR123A-shaped access must not invite charging disposable primary cells.

No cell balancing is needed for one series cell. No fuel gauge is required
for these fault functions. This draft is deliberately **not called a complete
BMS**.

## Package and land-pattern review

### Winbond UX, not XG

The inspected W25Q16JV Revision I (December24,2024), section11.3 / printed
p67, specifies UX body **D=3.0±0.1, E=2.0±0.1**,0.5 mm terminal pitch,
height0.60 mm maximum, terminal width0.20..0.30 and length0.40..0.50 mm.
Pin1..8 retain the original QSPI/VCC/GND mapping.

The new independently drawn lands are0.60 x0.30 mm at x=±1.25,
y=-0.75,-0.25,+0.25,+0.75 mm. The narrow center metal is
**D1=0.20 nominal x E1=1.60 nominal** (ranges0.15..0.25 /1.55..1.65),
not the XG2.3 x3.0 mm exposed area and not the old2 x3 mm PCB pad.
The actual native `PAD` land is0.20 x1.60 mm to GND; one separate
paste-only0.15 x1.20 aperture gives56.25% nominal copper coverage.

Winbond's [technical FAQ](https://www.winbond.com/hq/support/faq/technical/?__locale=en)
permits leaving this otherwise unconnected center metal floating or joining
device GND. The footprint follows the retained permitted GND assignment.
Terminal overlap, exposed-strip tolerances, stencil release/volume and the
narrow paste aperture still require assembler review. This is an original
package-informed land pattern, **not a copied/approved vendor land pattern**.
Keep exposed PCB vias out from under the strip.

CircuitPython's exact Winbond descriptor/boot/QE configuration, cold boot,
UF2 recovery, JEDEC ID,2 MB filesystem behavior and actual audio free space
remain the [flash study's](flash-sourcing.md) firmware gates.

### Protection packages

- BQ29700DSER: DSE0006A WSON6,1.5 x1.5 nominal,0.8 mm maximum height;
  no exposed center pad. The native footprint uses a documented **all-NSMD
  adaptation** of TI's exposed-land example: pin1 is0.80 x0.25 at
  x=-0.55,y=-0.5; pins2/3 are0.70 x0.25 at x=-0.6,y=0/+0.5;
  pins6/5/4 are0.70 x0.25 at x=+0.6,y=-0.5/0/+0.5;0.05 mm mask expansion.
  TI's example depicts SMD copper expansion on its left side; reproducing
  that larger copper created two0.15 mm clearance findings under the retained
  0.20 mm rule. The implemented all-NSMD lands retain the example's exposed
  dimensions instead, with0.25 mm row gap. **The rule was not weakened or
  excluded.** Assembly review must approve this deliberate land/mask choice.
- CSD83325L: YJE0006A PicoStar,1.15 x2.20 mm maximum plan dimensions,
  **0.22 mm maximum height**,0.65 mm row/column pitch. Pads are0.30 mm circles
  at x=±0.325 and y=-0.65,0,+0.65, with0.05 mm mask expansion, following
  TI's preferred NSMD example. This is a very thin chip-scale part; factory
  assembly capability, handling/yield and sourcing cost are gates.
- R27: original0805 land provision,1.0 x1.4 lands at x=±1.0. The selected
  resistor's mounting, pulse handling and temperature derating require
  manufacturer/assembler reconciliation before release.

## Contact, cradle and USB handoff

The authoritative coordinates are the new
[`battery-contact-interface.json`](../hardware/handbell/iterations/t8-protected-draft/battery-contact-interface.json)
and byte-bound
[`placement-manifest.json`](../hardware/handbell/iterations/t8-protected-draft/placement-manifest.json).
The contact proxies are **dimensioned thin primitives**, not solid battery-
intersecting bounding blocks. Their loaded bends/arcs are explicit kinematic
assumptions, not manufacturer STEP geometry or qualified spring travel.

The provisional cell is16.4 mm diameter and **34.0 mm total button-top length**,
axisX, centered(0,0,25.63), endsx=±17. The34.0 value follows the exact retailer's
approximate listing; Vapcell's generic extra2–3 mm button note remains a
conflict. No maximum length, button diameter/height, cell tolerance, dimple
preload, current rating or retained shock performance is invented.

Keystone254revC nominal dimple height9.78 mm above B atz15.85 sets the selected
cell center25.63. Drawing metal thickness0.30, base length19.88,
base width11.13, unloaded transverse reference16.61, and nominal height16.59
are distinct from installed cell diameter and loaded contact envelope.
The original loaded-ear interpretation has8.2 mm inner radius and0.30 mm
metal, hence17.0 mm outer width; its maximum arc angle52° keeps its height
within the nominal spring's16.59 mm model envelope. This is **not** evidence
that the drawing's16.61 mm unloaded width permits that deflection. The
native contact F.Fab/courtyard and manifest reserve the larger candidate
loaded width. Build spring thickness **outward from** its cell-facing
polyline, not symmetrically into the cell.
The earless57's lower7.23 mm dimple was not silently substituted: its exact
positive-button engagement would need a different review.

| Interface | Common assembly coordinates,mm |
|---|---|
| BT1 positive inner/outer land centers | (+3.62,0) / (+19.63,0), B |
| BT2 raw-negative inner/outer land centers | (-3.62,0) / (-19.63,0), B |
| Inner / outer land sizes | 4.24 x5.20 /4.24 x3.30 |
| Pair inner-pad-edge gap | 3.00; drawing CR123A `L`≤3.66 is this gap, **not cell length** |
| Contact support tabs | Local x=±22.25, y=±2.30 outer boundaries |
| Board faces | Fz14.25, Bz15.85; mainD43 |
| M2 mounts | (+10,+15.7),(-10,-15.7); drill2.2/pad4.4; radius3.2 support/tool reservation |
| USB tongue | x=±5.75, outery=-26.85 |
| X6 native footprint origin | (0,-22.82), native rotation180° |
| Actual retained X6 F.Fab mouth | (0,-27.90); nominal width8.94; F.Fab depth7.35 |
| USB body Z screen | z10.75..14.25; inherited3.5 mm height proxy, not a mated maximum |
| Cell / spring top | Cell centerz25.63; springtopz32.44 |
| Speaker / grille front | Speakerz=-6.25; mechanical grillez=-10.75 |

The enlarged contact pad span is43.50 mm; simply retaining a circularD43
edge would leave the outer lands insufficiently supported. The small tabs
provide an explicit substrate solution, to be reconciled with the measured
shell and insulating cradle. The USB tongue likewise supports the retained
anchors instead of moving their pads off the substrate.

The body mouth, not the footprint-envelope center, is placed at y=-27.90.
The mechanical working outside surface isy=-27.85547 at connector midheight
z12.50, so the mouth projects approximately0.0445 mm at that station.
This is **not flush at every Z or across the whole flat mouth** on the curved
shell and does not establish the mating plug/strain-relief envelope. A deliberate shell
opening, support under the tongue, anchor-tail clearance, insulation,
cartridge repeatability and reversible service path are required together.
The B-side USB through-anchor reservation is preserved and translated with X6.

Plastic must carry insertion/shake loads, capture the cell without damaging
its wrapper or blocking its vent, and isolate the raw can/contacts from
grounded hardware and the metal bell. The requested1–1.5 mm proud plastic is
a design target, not qualified creepage, abrasion, thermal or impact evidence.

### Mechanical coordination: selected stack translation

The mechanically selected alternative moves the **entire internal
speaker/yoke/PCB/cell/contact stack6.25 mm mouthward**. All relative axial
gaps and all non-USB native XY/angles/faces are unchanged. The grille/front
body may project farther outside; the measured mouth register and shell
attachment stay fixed. No PCB-only compression was inferred from the
owner's qualitative eyeballed speaker gap.

The exact bounded BRep report is preserved as
[`stack-shift-screen-evidence.json`](../hardware/handbell/iterations/t8-protected-draft/reports/stack-shift-screen-evidence.json).
It records the original input hashes and selected candidate. Its bytes are
bound into the new manifest and native evidence; it is not substituted for
the final complete mechanical assembly's own new-input binding.

| Whole-stack mouthward shift / plastic wall | Bounded guard-stock result |
|---|---|
| 1.5 mm /1.0 mm | 27.475 mm3 shell overlap; rejected |
| 2.0 mm /1.0 mm | 18.845 mm3 shell overlap; rejected |
| 6.0 mm /1.0 mm | No overlap,0.2315 mm shell gap; below declared0.25 mm nominal-margin target |
| **6.25 mm /1.0 mm, selected** | **No overlap,0.29406 mm nominal shell gap** |
| 7.25 mm /1.25 mm | No overlap,0.2943 mm shell gap; greater outward projection, not selected |

The guard stock uses0.10 mm nominal clearance and the selected **1.0 mm**
plastic thickness, within the owner's1–1.5 mm range. The upper254 spring,
not the bare cell, sets this much larger translation. The0.29406 mm result
is a bounded geometric distance, **not a manufacturing tolerance, dielectric
rating or impact/abrasion allowance**. The complete rebuilt body, cradle,
cover, fasteners and service path still require their own BRep review against
the new manifest. Positive-ear insulation and loaded-contact qualification
remain open even when all nominal external intersections are eliminated.

The electrical generator's fast station-chord screen and the mechanical
model's explicitly declared curved profile are different approximations.
The parent-owned measured/inferred station bytes are hash-bound; neither
method turns the inferred upper profile or chosen1.15 mm radial wall into
additional measurements.

### Historical initial-stack blockers and unresolved insulation

The original Fz20.5/Bz22.1, cellcenter31.88 model failed before this
translation. At its spring-top stationz38.69, the working interpolated shell radius is
18.85093 mm. The **cell-facing** spring corner(18.2,4.445,38.69) leaves
only0.11599 mm radial room. Including the specified0.30 mm outward thickness
moves the outer corner tox18.5, giving **-0.17558 mm radial clearance** in
this full-width kinematic spring interpretation: the metal proxy itself
can intersect the working shell before adding an external barrier.
The mechanical BRep report must include that outer surface, not merely
the centerline/cell-facing point. Actual rounded spring shape, supplied
contact deflection and shell curvature are not thereby measured.

The original cell-cylinder underside wasz23.68; the metal base top wasz22.40.
The selected coordinates arez17.43 andz16.15 respectively.
Only **1.28 mm total** remains. A1.25 mm barrier leaves **0.03 mm nominal**
before any installation clearance or cell/contact/print variation; the
selected1.0 mm layer leaves0.28 mm before those allowances. This
does not establish an installable or qualified insulating separation.
SMT solder-land exceptions must remain local; they do not justify removing
the broader cell or terminal barrier wherever it intersects.

The assumed ear inner radius8.2 mm conforms to the16.4 mm overall cell
cylinder. That cylinder does not resolve the negative can, wrapper and
positive button individually. In particular, a positive clip's ears
cannot be declared independently insulated from the negative can based
only on an uncharacterized wrapper or nominal tangency.

The changed stack addresses the bounded external guard conflict without
changing the contact family or trimming the metal/cell. It does not by itself
close the electrical-insulation gaps. The cradle/cover must supply an
independent mechanical load path and an independently reviewed liner/can
isolation where required; owner review still precedes routing.

The mechanical consumer also identified an undimensioned fold-root limitation
in these screening primitives. Outside the narrow3.18 mm outer solder tab,
the outward spring and under-cell base can meet only along an edge at
x=18.685,z22.4 in the original stack (selectedz16.15). This can produce non-manifold mesh
edges despite retaining the complete analytical assembly. Do not invent
metal bridges or claim a vendor-exact bend radius. A clearly labeled
**contact-free inert PCBA print** is permissible as a separate scope;
the complete native/assembly model must still retain both contact objects
and all83 fitted components. Neither export scope qualifies the contact.

## Sourcing and provenance

Manufacturer documents were inspected directly, including package drawings,
and are linked rather than redistributed. The native protection symbols,
lands and thin contact interpretation are **original factual implementations**;
no vendor PDF/image/STEP model is imported into the deliverable.

| Item | Source and dated availability scope |
|---|---|
| BQ29700DSER | [TI exact orderable](https://www.ti.com/product/BQ2970/part-details/BQ29700DSER); [DigiKey exact product5973173](https://www.digikey.com/en/products/detail/texas-instruments/BQ29700DSER/5973173). Active manufacturer orderable and distributor listing verified; current quantity/price not independently captured. Indexed stock counts conflicted and are not a quote. |
| CSD83325L | [TI exact orderable](https://www.ti.com/product/CSD83325L/part-details/CSD83325L); [DigiKey product5039318](https://www.digikey.com/en/products/detail/texas-instruments/CSD83325L/5039318). Retrieved regional page says buy-now/ships-today but is labeled **Marketplace**; do not assume its seller/channel or indexed stock/price is a verified authorized-distributor offer. Source from TI/confirmed authorized stock before release. |
| ERJ-6BWFR033V | [DigiKey product1466366](https://www.digikey.com/en/products/detail/panasonic-industry/ERJ-6BWFR033V/1466366); retrieved Mexican page identifies33mohm±1%,0.5W,0805 and buy-now/ships-today, not Marketplace. Current numeric stock/price remains unverified. |
| Winbond UX | Exact stocked2 MB candidate and September10 observed pricing are in [flash-sourcing.md](flash-sourcing.md); not a fresh September11 reservation. |
| Keystone254 | ManufacturerrevC drawing and September9 stock/price observation are in [battery-contact-options.md](battery-contact-options.md); confirm delivered revision. |

RC0402FR-07330RL, RC0402FR-072K2L, RC0402FR-075M1L (two), and
GRM155R71C104KA88D are exact passive BOM candidates. Their sourcing/assembly
availability is not a quoted turnkey BOM. BQ2970's tiny package and low
component count make this a compact candidate; no total assembled price,
guaranteed stock or purchase is claimed.

The Adafruit-derived circuit remains **CC BY-SA3.0**, with complete license
and original5768/4438/4654 notices beside the new project. KiCad standard
library material remains under its design exception. Original tools and
this documentation are MIT; they do not relicense the hardware.

## Native validation and remaining work

KiCad **10.0.6** actually produced:

- **0 ERC** findings, unchanged project severity/rules, no new exclusions.
- **244 physical DRC findings:**98 silk-over-copper,72 text-height,
  61 silk-overlap,7 silk-edge,2 text-thickness and the **four inherited X6
  hole-clearance** findings. No copper clearance, mask bridge, courtyard
  or library mismatch findings remain in this candidate.
- **222 unconnected items**, expected for this deliberately unrouted board.
- **46 known CLI auto-net/NC-pin parity fallback findings**, retained in full.
  No paired-editor GUI review is claimed for this variant.

The dedicated checker verifies278 unchanged retained pin/net assignments;
the exact allowed new circuit; raw-negative membership; every native pad/net;
retained local pad geometry; core/boost/audio poses; all fitted sides and Z
bounds; contacts, outline and mounts; unchanged rules; and hashes of native
inputs, dependency libraries, manifest and exported reports. The selected
frame additionally binds the frozen native XY seed, measured-profile input
and exact bounded stack-screen snapshot. It checks that every non-USB pose
is unchanged and that the selected guard-stock case meets its declared
nominal margin.

Reproduce the selected frame without running the original placement optimizer:

```powershell
python .\tools\draft_t8_placement.py --preserve-xy --front-z 14.25 --usb-mouth-y -27.90 --guard-mm 1.0
python .\tools\check_t8_placement.py --run-native
python .\tools\check_t8_placement.py
```

`--preview` on the first command screens parameters without writing CAD,
manifest, contact interface or the frozen seed.

The remaining work includes charge/reversal/temperature decisions, cell and
contact samples, quiet-mute power-state behavior, protection faults/SOA/
recovery, loaded mechanical fit/insulation, real USB land-pattern clearance,
critical routing/current returns/thermal copper, remaining MPNs and the full
assembly quote. **A clean correspondence/ERC check is not functional or
safety signoff.** Owning epics: E04/#4, E05/#5, E07/#7, E08/#8 and E10/#10.
