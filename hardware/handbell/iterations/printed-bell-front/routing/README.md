# Routing preparation — copper release still required

This directory adds **read-only preparation** to the stage-1 package published
at `23cb3fe26707f094ce3eaf365807c322bd2844ed`. It does not alter the native
PCB, schematic, project, footprints, manifest, contact interface or native
checker/report bindings. No candidate PCB, track, via or pour is emitted.

```powershell
python .\hardware\handbell\iterations\printed-bell-front\routing\prepare.py
```

The script checks the exact published stage-1 hashes and existing native
input/report bindings. It fingerprints all stage-1 package files before and
after its work, writing **only**:

- `routing-preparation.json`: actual transformed pad geometry, two-contact
  exclusion regions, proposed via locations,86 critical connection intents,
  source-bus corridor candidates, polarity-mark reservations and release gates.
- `routing-preparation.svg`: readable common-XY contact/via/marking review.

`--apply` deliberately fails. There is no native copper writer in this
preparation; a file called `release.json` cannot enable one. A separate,
explicit parent copper-release instruction and the completed mechanical
review's exact artifact/hash binding are required before implementing the
candidate-writer/apply stage.

## Ground geometry: both contact polarities matter

The two B-side inner lands run:

- **VBAT:** x1.50..5.74, y−2.60..2.60.
- **CELL_NEG:** x−5.74..−1.50, y−2.60..2.60.

Both are directly behind the MCU region. A GND thermal or stitching via in
either is wrong. In addition, the retained thin contact model puts conductive
base metal directly against B outside these lands. The preparation excludes
those base projections too; it does not treat solder mask as qualified
abrasion-proof insulation. A GND zone must avoid **both** raw contact nets
and these unqualified metal contact regions.

The nominal3mm gap between the inner lands becomes only **2.6mm of possible
GND copper** with the inherited0.2mm clearance. Using the existing GND
netclass's0.604mm via/0.35mm drill, the via-center corridor is only
**x−0.998..+0.998** at the contact row. A broad uninterrupted B ground plane
does not exist here.

The checker finds **nine geometrically valid MCU thermal-via candidates**
at x/y−0.8,0,+0.8, and **four amplifier thermal-via candidates** at its
thermal-center±0.325mm. These preserve both-side copper and drill clearances,
including the raw contacts. They are **not** a qualified via count, thermal
resistance or via-in-pad solder process. Filling/tenting, stencil design,
cell-side insulation and actual heat spreading remain unresolved.

Negative cases intentionally reject GND vias at x±1.3,±3.62 and±10,y0;
x0,y0 is accepted. The x±1.3 cases catch a via whose center misses a raw
contact but whose annulus/clearance does not. The x±10 cases catch conductive
contact-base exposure outside the actual solder lands.

## Local returns cannot be generated blindly

The candidate search found no legal **sampled off-pad GND via within2mm**
for C2,C3,C5,C6,C7,C8,C17 andC18. This is a bounded point search, not proof
that every possible nearby point is impossible. Other accepted points still
need an actually checked F-side connecting trace.

- C2/C3's oscillator return region has raw-negative contact/base geometry
  below it, not a GND reference plane. Plan a local F return/guard to IC1.19
  and the thermal-ground structure. Preserve Y1's two unassigned lands;
  they must not silently become ground pins.
- The right MCU bypass bank sits above VBAT land/base geometry. Plan F-side
  corner-return paths to the central safe ground bank, or use actually
  accessible outer ground vias; do not create a neat-looking but shorted
  array of vias immediately behind every capacitor.
- Flash/C10 return routing also needs a real return path; B beneath the
  positive contact base cannot be assumed to be its reference.
- Route deliberate boost/amplifier **F high-current returns** toward the
  system side of R27. Do not use the narrow central B neck as an assumed
  qualified shared high-current return.

After pouring, inspect real connectivity, necks and islands, and ensure
every retained GND pad reaches protected GND without any raw-negative bypass.
Keep the complete system on two copper layers unless later engineering
evidence explicitly establishes a need to reconsider that baseline.

## Routing order and concrete implementation work

The JSON contains exact native pad IDs/coordinates and same-net checks for
86 connection intents. These are not86 routed connections.

1. **Protection escape and returns:** preserve the actual Q5 A/B/C identifiers.
   A1/C1 are SOURCE1 and A2/C2 SOURCE2; B1/B2 are the gates **between** each
   pair. Straight F source-pair connections would short gates.
   The inter-land gap is0.35mm; a0.1778mm track with two0.2mm clearances
   needs0.5778mm, so do not invent an inner escape channel.
   Four proposed **outside** source-via locations and two separate B source
   buses have a conservative minimum-width geometric screen. They provide
   a workable escape direction without crossing the F gates; no common-drain
   PCB pad exists. Actual current-carrying width/area, via count and fault SOA
   remain unselected. R26's GND end must sense the system side **R27.2**;
   U6.VSS senses raw-negative on the cell side. Keep sense leads separate
   from the intended heavy-current drop.
2. **MCU local supplies, oscillator and QSPI:** establish the protected-GND
   bank/corner returns first, then short matched-net bypass connections,
   VREG1uF input/output and the VCORE branches. Route the clock/load/series
   network and six QSPI signals without casually crossing B contact voids.
   Preserve the real2MB USON2x3 flash lands. USB resistor-side connections
   are included, but no USB impedance or timing qualification is claimed.
3. **Boost:** connect inductor SW and local VIN/output capacitor loops with
   deliberate supply-and-return geometry. Keep the FB divider quiet and
   away from SW copper. Native inherited widths named `power` and
   `thickpower` are not evidence of safe current capability.
4. **Amplifier:** connect local PVDD/bulk bypass and thermal/GND structure,
   then both outward filtered BTL paths. Preserve differential speaker nets;
   neither output becomes ground. Tie the power return into the reviewed
   protected-GND path, not into the raw-cell contact geometry.
5. **Remaining power/control/recovery:** complete both physical lands of
   each battery contact, shared source selection, regulator/charger grounds,
   IMU/control and service access. Do not rely invisibly on the fitted
   contact's metal as a substitute PCB routing jumper.
6. **Silk and native validation:** add B polarity/orientation markings and
   render an actual rear-facing view. Preserve all footprint poses, local
   pad rotations, source libraries, outline/tab/mount/USB/contact datums and
   the original four USB clearance findings. Validate new copper with
   KiCad10.0.6 DRC/net correspondence and exact new candidate bindings.

No high-current width has been selected. The source-bus screen uses only the
existing minimum track width to establish geometric escape feasibility; it
does not prescribe a power route or support a current/temperature claim.
All other connection paths and widths remain explicitly null in the plan.

## B-side orientation markings

Proposed **silk-only** reservations are `+ POS` at(+11,10.5), `− NEG`
at(−11,10.5), and `T8 BUTTON END >` at(0,10.5), pointing to the positive end
in common assembly coordinates. They clear both B copper and the base-metal
projection by the declared0.5mm screen and avoid the M2 tool/support reserves.
They do not move footprints, change contact nets or add copper.

Native B.SilkS text must use the correct mirrored text setting so it reads
properly from the cell side. The mechanical consumer must confirm service-state
visibility outside capture structures. Polarity printing is not reverse-cell
protection and cannot replace mechanical polarity control.

## Limits, sources and next release

Collision screening reads actual KiCad10 footprint-plus-local-pad transforms.
Rectangles, circles and custom polygon copper are represented explicitly;
rounded-rectangle/oval corners are conservatively filled. This can reject a
usable location, but does not shrink actual copper to invent a clearance.
Source fanout segments are sampled with an extra half-step distance margin;
candidate via positions are screened individually and for mutual spacing.
Neither is a substitute for eventual native routed DRC.

The existing package's source evidence, Adafruit CC BY-SA3.0 hardware notices,
manufacturer guidance and original MIT tool/documentation distinction remain
in force. No external CAD or new manufacturer material is imported here.

The unchanged charger profile, absent cell-temperature charge inhibit,
absent reverse-cell circuit, short-circuit SOA, contact retention/insulation,
thermal behavior and assembly process remain open. This preparation supplies
no fabrication, purchase, live-cell or child-use approval.
