# Measured-shell T8 cartridge: coordinated mouthward stack

**A nominal placed-fit study for owner review before routing, not a fabrication,
live-cell, contact-force or child-use approval.** The entire internal stack is
moved **6.25 mm toward the mouth**, preserving its speaker/yoke/PCB/cell gaps.
The mouth register stays fixed and the front body projects farther outside.
The chosen battery-guard target is **1.0 mm plastic**, within the owner's
1-1.5 mm range, with **0.10 mm nominal cell/contact clearance**.

The initial fixed-stack result is preserved under
[`alternatives/baseline-fixed-stack`](alternatives/baseline-fixed-stack/README.md).
It is not silently relabeled as fitting. The bounded alternative and its exact
source hashes are in
[`alternatives/whole-stack-screen/stack-shift-fit-report.json`](alternatives/whole-stack-screen/stack-shift-fit-report.json).
All September 7/9 studies and existing generators remain unchanged.

## Why the shift is 6.25 mm rather than 2 mm

The upper, full-thickness Keystone 254 spring limits the fit, not the bare cell.
At a 2 mm shift the bare cell clears the working shell by1.581 mm, but the
contact metal clears by only0.331 mm: that does not leave room for a1.0 mm
guard. The screen first tried the suggested1.5/2 mm shifts, then used the
analytic upper-contact corner to choose two quarter-millimetre brackets.
It did not run a blind optimizer or clip the metal.

| Whole-stack mouthward shift | Plastic target | Full rounded guard-stock result |
|---|---|---|
|1.5 mm |1.0 mm |27.475 mm3 shell overlap |
|2.0 mm |1.0 mm |18.845 mm3 shell overlap |
|6.0 mm |1.0 mm |No overlap;0.231 mm shell margin |
|**6.25 mm, chosen** |**1.0 mm** |**No overlap;0.294 mm shell margin** |
|7.0 mm |1.25 mm |No overlap;0.232 mm shell margin |
|7.25 mm |1.25 mm |No overlap;0.294 mm shell margin |

The rounded stock uses conservative local contact bounding solids with rounded
external corners, not an oversized rectangular corner and not a substituted
solid contact box through the cell. Its0.25 mm nominal shell-margin target is
a design assumption, **not measured print, paint or shell tolerance**.
The chosen1.0 mm option avoids another1 mm of external projection.

## Exact coordinated interface

All coordinates are **mm**. Mouth/front is z0; positive z is toward the handle.
The builder consumes the updated electrical manifest and contact interface
directly. It does not silently shift electronics imported from an old manifest.

| Feature | Current working coordinate |
|---|---|
| Speaker front / grille front |z-6.25 / z-10.75 |
| Rear basket station / magnet rear |z5.75 / z12.75 |
| Capture ring |z6.05..8.55 |
| PCB speaker-facing F / handle-facing B |z14.25 / z15.85 |
| T8 axis, X-oriented |(0,0,25.63), D16.4 x totalL34 provisional |
| Cell bottom / top |z17.43 / z33.83 |
| Contact B landing / spring top |z15.85 / z32.44 |
| Cover split |z25.75 |
| PCB mounting holes |(+10,+15.7), (-10,-15.7), D2.2 |
| USB native origin / source mouth |(0,-22.82) / (0,-27.90) |
| USB body-height proxy |z10.75..14.25 |
| Fixed shell attachment locations |Opposed X sides, outer-wall center z3 |

The main PCB remains D43 x1.6 with the **actual supplied outline polygon**:
contact-pad tabs to x+/-22.25, y+/-2.3 and a USB tongue x+/-5.75 to y-26.85.
The tongue/mouth move2.75 mm outward from the fixed-stack variant. All other
component XY, mount and contact-pad positions remain supplied by electrical.

The current manifest/companion hashes, actual PCB/schematic hashes and raw
snapshots are in `fit-report.json` and `artifact-manifest.json`.
The coordinated manifest at generation is
`4e8e27f7241e76850ef4fb9719a45acf0ab49ccfe9e1d651ef60f278b20da46c`;
the companion is
`e93d72ef211b7615634f255153a413b826d05c1495fa19d967c64456b647c4a6`.
An electrical source change requires a new build, not reuse of old fit values.

## Open the files

| File | Scope |
|---|---|
| `t8-cartridge.FCStd` | Selectable BReps, colored components, transparent working shell, parameters, exact base64 raw-input/source snapshots |
| `t8-cartridge-with-shell.step` | Complete placed study with proposed shell slot/holes and handle exterior |
| `t8-cartridge-assembly.step` | Complete cartridge including full contact primitives, without shell/handle |
| `body.step`, `yoke.step`, `battery-cradle.step`, `battery-cover.step` | Four separate structural parts |
| `populated-t8-pcba.step` | Full supplied PCBA/contact geometry; not a mesh-printability approval |
| `INERT-body.stl`, `INERT-yoke.stl`, `INERT-battery-cradle.stl`, `INERT-battery-cover.stl` | Four connected structural inert print models |
| `INERT-populated-t8-pcba-without-contacts.stl` and matching STEP | Explicitly contact-free, connected PCBA fit dummy |
| `INERT-speaker-body-screen.stl`, `INERT-T8-full-cell.stl` | Full inert dimensional bodies, not live parts |
| `inner-outer-profile-and-datums.svg` | Original novice-oriented section, measured/inferred stations and shifted datums |
| `fit-report.json`, `artifact-manifest.json`, `completion.json` | Exact Booleans/distances, path samples, source/output hashes and fresh completion |
| `placement-snapshot.json`, `contact_interface-snapshot.json`, `measurements-snapshot.json` | Exact consumed raw bytes, not reformatted approximations |

**STL is unitless: import mm,100%, without scaling.** Files retain assembly
coordinates, not print-bed coordinates; translate/reorient only for a separately
approved inert print. No G-code, printer job, physical drilling or fabrication
order is supplied.

Dark-grey F and brown B boxes distinguish the board faces; contact metal is
silver, body green, yoke amber, cradle/cover blue/cyan and cell purple.
`ConstructionReferences` contains hidden gauges, alternative/exact-source
comparison shapes and the USB anchor reservation, not extra fitted parts.
View properties are written headlessly; parent coordinates the actual GUI review.

### Contact geometry and the deliberately limited PCBA print dummy

The source spring polyline is its **cell-facing boundary**. The0.30 mm
thickness extends outward +X for BT1 and -X for mirrored BT2. Segment coordinates
are checked, and contact material must not penetrate the nominal cell.
Loaded ear angles are[-80,52] and[128,260] degrees, innerR8.2/outerR8.5.
The17.0 mm loaded outer width is an unqualified kinematic assumption, not an
approved deformation from the drawing's16.61 mm unloaded reference.

The contact base/spring junction has four nonmanifold mesh edges outside the
narrow outer solder tab. The full native/STEP geometry remains unchanged;
no connecting metal is invented to make an STL pass. The released PCBA STL
therefore explicitly omits BT1/BT2. They remain in the fitted83-component model
and BOM and are **not** reclassified as copper-only features.
Each contact is one instance containing three BRep solids; their fold-root
geometry and actual loaded form still need review. The report records the
nonmanifold edge endpoints/facet counts. No full-contact PCBA STL is released.

## Measurements versus assumptions

The model prioritizes owner-measured **ID71.68 atz0, ID69.75 atz4.9 and rough
ID50 atz14.9**. The first concave section ends at4.9+10=14.9, explicitly
confirmed. **ID36.12 at approximatez41.75 is inferred**, not measured:
OD38.42 minus twice the owner-requested1.15 wall assumption.

The1.15 mm wall is a **radial offset**, not constant normal thickness.
Working ODs at the first three stations are73.98,72.05,52.30; raw observations
remain73.15,73.15,51.50. The disagreements are preserved in the exact record.
Concave interpolation, the straight upper taper and the final closure above
z41.75 are provisional. Roundness, paint, uncertainty and handle-fastener
intrusion remain unmeasured. Handle exterior H85.5/D18.52..15.01 does not imply
usable internal handle space.

The fixed register follows that inner profile throughz9 with an assumed0.30 mm
radial print clearance. Two localized carrier pads intentionally bear on the
working cavity at the shell fasteners. The **D75.5 flange is external** and now
ends at the mouth plane; it is not shrunk to fit inside ID71.68. The external
skirt connects the mouth to the translated front plate. It projects6.25 mm
before the lower plate/grille; the grille front is10.75 mm outside the mouth.
Cosmetic overhang, mass, strength and acoustic behavior are not qualified.

Speaker dimensions remain D40/H19, rear basket D32 at speaker-relativez12 and
magnet D21.70/H7. The conservative conditional body remains D40 through the
basket depth, followed by the magnet; the illustrative tapered basket is not
substituted to hide collisions. Opening D22.1 gives0.4 mm diametral nominal
magnet play; the rear-basket gap remains0.3 mm. These are print assumptions,
not measured tolerances, permissible preload or a reason to force the speaker.
Rim bearing, intermediate basket, terminals, wire exits, vent and cone excursion
remain unknown.

## Four pieces, load paths and M2 hardware

The body integrates grille/seat, fixed register, external skirt, supports and
USB bezel. The removable yoke closes the speaker loading path and supports
the PCB. The cradle and separate cover provide positive can/end capture.
Cell loads are intended to pass through the cradle legs, locally supported
board mounts, yoke and body rather than SMT solder joints. Loaded force sharing,
spring travel, torque, creep and retention strength remain unqualified.

**M2 means2 mm nominal thread, not M3.** The board holes are2.2 mm clearance
drills. Hex nut pockets are not heat-set-insert pilots.

| Joint | Hardware / nominal stack |
|---|---|
| Two body-to-yoke joints | M2x6 cap screws and M2 nuts;1.45 mm roof,1.6 mm full nut engagement,0.4 mm blind-tip gap |
| Two PCB/cradle-to-yoke joints | M2x6 cap screws and M2 nuts;1.40 mm roof,0.8 mm clamping floor,1.1 mm blind-tip gap |
| Two cover-to-cradle joints | M2x6 cap screws and M2 nuts;1.45 mm roof,0.3 mm blind-tip gap |
| Two shell-to-carrier joints | Insulating nylon M2x6 screws and M2 nuts, separate from board hardware |

All six metal screws use the same M2x6 size. The dimension screen uses
DIN934-style nuts AF4/H1.6, ISO4762-style cap heads D3.8/H2 and nominal1.5AF
hex-key access. Nut pockets AF4.2 and screw bores D2.2 are unqualified print
allowances. Family references: [DIN934](https://www.fasteners.eu/standards/DIN/934/)
and [ISO4762](https://www.fasteners.eu/standards/ISO/4762/). No chosen supplier
lot, nylon head shape, thread form, knurl, torque or pullout rating is qualified.
The old D3xL4 insert placeholders are not reused.

The six metal nuts enter **sideways beneath real roofs** belonging to the part being fastened.
A top-open nut pocket closed only by the next part would not clamp its parent.
The engaged screw prevents sideways escape; a fully removed screw can release
a nut, so service over a tray with no live cell.
The two nylon shell nuts instead enter from the bell-axis side along open-ended
hexagonal sockets aligned with the inclined shell screws. A vertical insertion
chute was collision-checked and rejected. Their final outer nut faces bear on
the socket roofs; nominal engagement is1.6 mm with0.55 mm of screw beyond each
nut. The declared insertion path is included in the BRep report.

PCB screw heads end atz18.65 inside cups endingz19.90, recessed1.25 mm axially
and1.30 mm radially. Lower and cover screw guards are integral printed features.
The two shell screws follow the working lip's surface normal, approximately
**11.14 degrees handleward from the local radial direction**. Their under-head
planes contact the modeled outside instead of floating above it; local carrier
pads bear on the inside. These are proposed CAD/template locations, not
instructions to drill an unmeasured bell. Nylon substitution, paint damage,
clamping pressure, weakening of the shell and installation tooling remain gates.

## Assembly and service path

1. Outside the bell and before the yoke/PCB, load the nylon shell nuts from the
   inner ends of their inclined hexagonal sockets. Load the lower metal body nuts next: lower them
   through the register at radius26.5, move outward above the supports, lower
   at radius29.1, then slide inward into the roofed pockets. The report records
   the waypoints; do not push nuts through the external skirt.
2. With yoke/PCB absent, lower the speaker front-first onto its shifted seat.
   Its D40 frame cannot pass through the installed D22.1 capture opening.
3. Lower the yoke over the magnet and fit its two M2x6 screws. Do not preload
   an unverified speaker bearing surface.
4. Side-load the yoke-boss nuts, lower the PCBA into the **open-top** USB bezel,
   add the empty cradle and install the two recessed M2x6 screws.
5. Evaluate only with an inert cell, side-load the cover nuts and fit the cover.
   Positive retention does not qualify actual cell insertion, contact load,
   wrapper abrasion or reverse-insertion behavior.
6. Unplug USB and remove both shell screws before sliding the whole cartridge
   through the mouth, aligning its bezel with the mouth-open -Y slot.
   The front flange and carrier pads are the load-bearing interfaces, not USB
   solder anchors. Fit the insulating shell screws only after owner review.

For service unplug first, remove both shell screws and withdraw the **whole
cartridge mouthward (-z)**. Remove the cover/cell, then cradle/PCB, then yoke
and speaker as needed. The slot is open all the way toz0; a closed side hole
would trap a protruding USB connector. Nut, screw-tool, speaker, yoke, PCB,
cover and complete-cartridge motions are recorded as exact swept bounds where
available and explicit pose samples otherwise. They do not prove every tilted,
cabled or deforming motion.

The under-USB ledge ends atz10.55, leaving0.2 mm to the source body'sz10.75
underside. The proposed slot ends atz17.75 and bezel atz17.45. The source mouth
y-27.90 is approximately0.045 mm outward of the working shell at midpointz12.5;
the curved wall creates a different recessed/protruding band at other heights.
**No whole-face flush or selected-plug claim is made.** The unselected
8.8x8x2.6 mm plug-nose approach screen is not an approved mating travel/overmold.
USB tails remain unmeasured: copper1x2 and drill0.60 dimensions are not metal
tail dimensions. The full B projection is retained as a hidden planning
reservation, not a fabricated occupied height. Inherited electrical USB-hole
clearance findings are not waived or resized here.

## Fit evidence and remaining gates

The owner's later visual estimate of approximately 1 mm spare speaker-to-PCB
space is recorded as an estimate, not a measured minimum clearance.
`speaker_pcb_spacing_sensitivity` in the fit report compares 0.5 and 1.0 mm
PCB-only mouthward reductions with the speaker fixed. It preserves each
component's height/XY and reports individual speaker and unchanged-yoke
contacts/intersections. These comparisons do not modify the delivered
placement, supports or USB interface. A zero-distance contact is not positive
assembly clearance; reclaiming space by relocating parts is a separate design
change, not justification for silently shortening every standoff.

`fit-report.json` is authoritative for the current generated results. It
includes all physical pair intersections, uncut/cut shell comparisons,
metal-to-shell distances, the full guard stock **before** contact/PCB reliefs,
and a measured BRep material section under the cell.

The1.0 mm exterior guard uses0.10 mm clearance assumptions. Contact-ear pockets
follow the actual supplied angular sectors rather than erasing a full cylinder
through the bottom support. At x8/y0 the available under-cell section is1.08 mm;
the build checks that actual cradle material retains at least the chosen1.0 mm.
Other contact pockets use matched rounded offsets so a square clearance corner
does not thin a rounded outer wall. Each actual pocket BRep is positively
offset by1.0 mm; Boolean containment proves the entire expanded pocket stays
inside its stock. Additional containment checks establish the corresponding
bound for the union, before intentional PCB landing and fastener reliefs.
The report retains every witness and verifies that the global pocket contains
no unproved extra void. This constructive3D bound avoids an unsupported OCC
nested-shell extrema operation; it is not a bounding-box or single-height
proxy. Neither it nor the specific under-cell section is a global dielectric
or tolerance rating.
Intentional SMT lands terminate at PCB B; there is no plastic forced through FR4
to claim insulation, and no guard is clipped to the shell.

The bare T8 D16.4/L34, exact positive button, maximum cell dimensions, loaded
ear geometry and contact force remain unqualified. Positive ears approach the
wrapped negative can; the wrapper is **not credited as qualified independent
insulation**. Raw cell negative must remain isolated from both bell and
protected GND when the low-side protector opens. The circuit cannot clear a
short made directly across the raw cell outside its protected interface.

Minimum speaker/component and yoke/component gaps remain0.5 and approximately
0.25 mm; L1 is kept at its full5.0 mm height and its cradle gap remains0.30 mm.
These and the0.294 mm guard/shell margin require physical dimensional review.
Selected plastic/material, manufacturing variation, thermal/charge policy,
live-cell identification, vent clearance, reverse insertion, strength,
drop/shake, acoustic behavior and eventual child suitability are still gates.
**A nominal fit result is not routing, fabrication or safety signoff.**

## Reproduction and attribution

See [REPRODUCE.md](REPRODUCE.md). STEP precedes tessellation; native and STEP
are reopened and compared by BRep symmetric differences, not only bounding
boxes. Released STLs are reimported as closed manifold meshes and reconstructed
BReps. Raw source/measurement/electrical bytes and hashes are preserved.

Original geometry, code, SVG and documentation are MIT under
[mechanical/LICENSE](../../LICENSE). No vendor photograph, third-party CAD or
manufacturer mesh is copied. Mixed populated exports retain the adapted
electronics' **CC BY-SA3.0** context and complete
[hardware notices](../../../hardware/handbell/README.md) and
[attribution policy](../../../ATTRIBUTION.md), including Limor Fried/Ladyada
for Adafruit Industries (5768/4654) and Bryan Siepert for Adafruit Industries
(4438). Carry those notices with standalone populated files.

Owning epics remain E01/#1 (measurements), E04/#4 (electrical/contact interface),
E05/#5 (capture/service), E07/#7 (placed review before routing), and E10/#10
(eventual insulation/retention/use qualification). No purchase, physical
modification, routing, GUI launch or commit was performed by this mechanical task.
