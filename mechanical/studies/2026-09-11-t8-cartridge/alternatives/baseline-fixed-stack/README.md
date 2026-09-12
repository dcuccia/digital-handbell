# Measured-shell T8 cartridge — inert assembly review

**A separate September 11 design study, not a fabrication release, a live-cell
holder qualification or routing approval.** All earlier prints and generators
remain unchanged. The exact protected-T8 placement and owner measurement bytes
are copied into this study and embedded, base64-encoded, in its native document.
Read `fit-report.json` for the actual generated conflicts; successful export
does **not** mean every design gate passed.

**Current decision gate:** the complete fixed stack has no unintended *internal*
material intersections, but its T8/254 insulating cradle and cover **do not fit
the working metal shell**. Even the rounded minimum cell-clearance/guard
reference intersects it. Do not force this assembly, shrink a cell, trim a live
contact or treat it as the already-tested older print. The full model deliberately
preserves the failing parts for owner review; see the bounded alternatives below.

## Open this model

- `t8-cartridge.FCStd`: individually selectable BRep parts, transparent working
  metal shell, handle exterior, front/back component proxies, cell, contact
  metal, four structural prints and hardware. Color/visibility properties are
  saved without launching FreeCAD; headless generation does not prove their
  rendering in a GUI.
- `t8-cartridge-with-shell.step`: complete review assembly and proposed shell
  openings. `t8-cartridge-assembly.step` omits the shell/handle.
- `body.step`, `yoke.step`, `battery-cradle.step`, `battery-cover.step`:
  individual structural BReps.
- `INERT-*.stl`: unitless inert fit models; import **mm, 100%, without scaling**.
  They retain assembly coordinates, not print-bed coordinates. Translate or
  reorient only when preparing a separately approved inert print.
- `inner-outer-profile-and-datums.svg`: novice-oriented profile explanation.
- `placement-snapshot.json`, `measurements-snapshot.json`: exact original bytes.
- `parameters.json`: reproducible parameter values; pass with `--parameters`
  to regenerate. Spreadsheet edits alone do not rebuild source-generated BReps.
- `fit-report.json`, `artifact-manifest.json`, `completion.json`:
  tool versions, source/output hashes, exact Booleans/distances, path samples
  and native/STEP/STL round-trip checks.

`ConstructionReferences` contains alternative/reference solids, not extra
installed parts. Contact *body boxes*, where retained invisibly for comparison,
are not the material shapes used for cell-interference calculations. A spring
base underneath a cell must not be represented as a tall solid block through it.
Component models are original declared proxies, not manufacturer STEP files.
**The released PCBA print dummy excludes BT1/BT2 contacts**, explicitly named
`INERT-populated-t8-pcba-without-contacts.stl`, with a matching standalone STEP.
It is one connected solid, not a contact-fit gauge. Full contacts remain in
`populated-t8-pcba.step`, both complete assembly STEPs and the native document;
they are not removed from the fitted BOM or classified as copper-only features.

The corrected outward-thickness source primitives create four nonmanifold
mesh edges at the spring/base junction: x±18.685, z22.4, between |y|1.59 and4.445.
No full-contact STL is released, and the obsolete file is removed rather than
retained as a misleading printable artifact. The report records the actual
edge endpoints/facet counts. Their unspecified fold roots are not repaired with
invented bridging metal. Each contact remains one named native instance with
three BRep solids; the summary separately records two contact objects and six
contact BRep solids. This is a contact-fold/printability gate, not a claim that
a physical Keystone clip consists of separate pieces. The **four structural
print STLs and the contact-free PCBA dummy are each connected**.

Dark-grey F and brown B proxies distinguish the board faces; contact metal is
silver, the body green, yoke amber, cradle/cover blue/cyan and full cell purple.
The hidden `USBAnchorReservation1` is the exact supplied XY reservation
projected from Bz22.1 to the inferred cavity stationz41.75 solely because
anchor height is unknown. It is **not** physical metal, a measured anchor
height or a supplied USB-hole print gauge.

The spring polyline is the **cell-facing surface**, not a centerline.
Its0.30 mm thickness extends **outward in +X for BT1 and −X for BT2**.
The builder checks segment coordinates and rejects material penetration into the
nominal cell. This supersedes the initial centered-thickness interpretation.
Loaded ear angles are−80..52 and128..260 degrees, with17.0 mm outer width;
the drawing's16.61 mm value is an **unloaded reference**. Neither this width
nor the loaded proxy establishes permitted spring deflection or contact force.

## Datums, measurements and fitting allowances

The mouth/front plane is **z0**. Positive z points into the bell toward the
handle. PCB F faces the speaker at **z20.5**; PCB B faces the cell at **z22.1**.
The main board body remains **D43 × 1.6**. The exact new manifest also supplies
small local contact-pad tabs (to x±22.25) and a supported USB tongue
(x±5.75 to y−24.1); the model consumes that actual polygon, not a substituted
round disk. Making the front plastic better fill the mouth does not justify
growing the main electronics disk.

The working inside shell follows owner-measured **ID71.68@z0**,
**ID69.75@z4.9**, and roughly **ID50@z14.9**. The owner explicitly confirmed
the first taper's end as 4.9 + 10 = **14.9 mm**. At approximately z41.75,
**ID36.12 is inferred**, not measured: OD38.42 minus twice the owner-requested
1.15 mm wall assumption.

The model uses a **radial** 1.15 mm wall offset, not constant thickness normal
to the sloping wall. Thus the modeled first three ODs are73.98,72.05,52.30,
not all the raw OD73.15,73.15,51.50 observations. The raw discrepancies remain
in the unmodified dated record. The cubic concave curve between z4.9 and14.9,
straight upper taper and final cone/closure above z41.75 are provisional.
Ovality, paint, uncertainty and handle-attachment intrusion are unmeasured.

The front flange is **D75.5, external**. Compared with mouth ID71.68 it spans
1.91 mm radially beyond the opening; only the actual shell lip provides bearing.
Against raw OD73.15 its cosmetic overhang is1.175 mm radially. Against modeled
OD73.98 it is0.76 mm. These are geometric differences, not a tested clamp margin.
The register follows the new inside profile through **z9**, with **0.30 mm
radial clearance assumed for an inert print**, rather than the old D69 cylinder.
The flange must not be scaled to fit *inside* the mouth.

Speaker screening retains **D40/H19**, measured rear basket **D32@z12** and
updated magnet **D21.70/H7**. The conservative conditional body is D40 through
z12 followed by the magnet through z19. The illustrative straight basket is
not substituted into collision checks to make a conflict vanish.
The removable yoke's **D22.1** aperture means0.40 mm diametral/0.20 mm radial
nominal play, down from old D22.8. This is a **print assumption**, not a
measured tolerance, squeeze fit or instruction to force anything past the magnet.
Its z12.3 underside leaves0.3 mm to the measured rear-basket station.
Rim thickness, permitted bearing surfaces, intermediate basket, terminals,
wire exits, rear vent and cone excursion remain unknown. No arbitrary speaker
surface is approved for preload.

## Four pieces and their load paths

1. **Front body:** grille, speaker front seat, measured-profile register, two
   yoke supports and integral USB insulating tunnel/bezel.
2. **Removable yoke:** tighter magnet opening, speaker escape stops and locally
   supporting PCB bosses.
3. **Battery cradle:** lower insulating can/end-contact guards, two mounting
   legs on the existing board-mount reservations, and independent cover seats.
4. **Removable battery cover:** upper can/end guards and positive screw closure.

Positive battery retention and reversible servicing take precedence over the
older two-piece claim. Battery insertion/shaking forces are intended to pass
through the cradle and its mounting legs, into the locally supported board
mounts/yoke, then body/shell attachment—not through SMT contact solder joints.
The force, contact preload, cell heat, nut pullout, screw torque, fatigue,
layer orientation and plastic creep have not been qualified.

The full provisional T8 **D16.4 × L34** body is never shrunk or clipped to make
the shell fit. Supplier dimensions are not measured maximum cell dimensions;
button-top height/diameter and the contradictory generic extension note remain
unresolved. A reference screen uses the full can's rounded all-direction offset,
nominal clearance0.15 plus plastic1.25 mm. The implemented guard uses original
analytical cylindrical stock and conservative local contact-pocket stock around
the exact thin terminal primitives, not a box replacing the metal through the
cell. This printable stock can be more restrictive than the rounded reference.
The contact lands intentionally terminate at PCB B z22.1; the model does not
put plastic through the FR4 to claim complete terminal insulation. That boundary
and the lower can/base spacing need electrical-layout/barrier qualification.
Metal contacts and fasteners also
receive explicit shell-distance checks. A largest-z check alone is insufficient.
The report retains any guard/shell/PCB conflict rather than subtracting the shell
from the guard. Contact-clearance pockets are subtracted from the plastic,
not from the metal or cell. Thin seams, tool openings, contact apertures, wrapper abrasion,
positive-button access and intentional electrical contact zones remain gates.
**A geometrical offset is not an insulation rating.**

In a low-side protection circuit, the raw negative can and protected board GND
can separate electrically on a fault. Insulate the can from **both** the bell
and protected GND. The board protector cannot interrupt an external raw
positive-to-negative short made through the metal bell.

## Hardware: M2, not M3; captive nuts, not unknown insert pilots

The earlier print had **2.2 mm clearance holes for M2 screws**, not M3 holes.
Its D3 × L4 heat-set-insert bodies were placeholders without selected knurls,
installation pilots or pullout evidence. This study instead uses accessible
**ordinary M2 hex captive nuts**; do not install a heat-set insert into these
hexagonal pockets or force an M3 screw through the board.

| Joint | Dimension-screen hardware | Intended capture |
|---|---|---|
| Yoke to body, two joints | M2×6 socket cap screw; M2 nut | Nut side-loaded below1.45 mm of real body roof |
| PCB/cradle to yoke, two joints | M2×6 socket cap screw; M2 nut | Nut side-loaded below1.40 mm of yoke-boss roof; head recessed into cradle |
| Cover to cradle, two joints | M2×6 socket cap screw; M2 nut | Nut side-loaded below1.45 mm of cradle-ear roof |
| Shell to carrier, two joints | Insulating nylon M2×6 screw and M2 nut | Opposed radial carrier pockets, no electrical bridge to board mounts |

Rounded lower-screw guards and raised cover-screw cups are integral to the
yoke/cover, not additional pieces. The lower joints are moved to radius23.5 and
the heads toward the mouth so the guards do not consume the previous0.25 mm
hardware/shell margin. The report gives their actual BRep distances.

The common metal fastener screen is **DIN934-style M2 nut AF4 × H1.6** and
**ISO4762-style M2 cap head D3.8 × H2**, with smooth D2 shanks and no helical
threads. Nut pockets are **AF4.2** and screw holes **D2.2**, both unqualified
print allowances. The shell's D2.4 proposed holes are a separate clearance
assumption, not PCB drills. A1.5 mm hex key is the nominal cap-screw tool.
Reference tables: [DIN934](https://www.fasteners.eu/standards/DIN/934/) and
[ISO4762](https://www.fasteners.eu/standards/ISO/4762/). These identify the
dimensional family; no purchased supplier lot or nylon-head equivalence is
qualified. Measure chosen hardware and do a nut-pocket coupon before deciding
fit or torque. All six metal screws use the **same M2×6 size**; there are six
metal nuts plus two insulating shell screws/nuts. Full nominal nut engagement
is1.6 mm in all three metal joint types. Blind tip gaps are0.4,1.1,0.3 mm
for body, PCB/cradle and cover respectively. The PCB screw heads end atz24.9,
inside cups ending atz26.15:1.25 mm recessed axially and1.30 mm radially inside
the cup's exterior. The local clamping floor is0.8 mm and remains a strength
gate. Thread engagement/stack intersections are model screens only.

**Why side-loading matters:** merely dropping a nut into a top-open pocket and
closing it with the next part does not clamp the pocket's parent; nut and screw
could lift out together. Here the nut bears against a real roof belonging to
the part being fastened. The horizontal loading slot stays open for service;
the engaged screw prevents sideways nut escape. With a screw removed completely,
the nut can become loose: work over a tray, outside the bell, with no cell.

Insulating shell screws are intentional: they cannot join a grounded board
screw or raw battery terminal to the bell. Strength, damage, torque and whether
nylon hardware is adequate remain open; substituting metal requires a renewed
isolation/load review, not merely changing the model color.

## Installation and service — outside the bell first

**No live cell, physical shell modification or fabrication is authorized by this
study.** The following is the proposed assembly architecture for inert review.

1. With yoke/PCB absent, place the speaker front-first toward its z0 seat.
   A D40 frame cannot pass through the installed D22.1 yoke.
2. Slide the two lower M2 nuts sideways under their body roofs, lower the yoke
   over the magnet, and install the two M2×6 screws from the handle-facing side.
   Do not preload an unverified
   speaker bearing surface.
3. Side-load the two yoke-boss nuts. Lower the PCBA onto its supported mounting
   pads, then place the empty cradle and install the two recessed M2×6 screws. Contact
   positions come from the final new manifest, never from the older wing study.
4. Check the actual cradle/contact insertion path and all retained fit findings
   with an inert cell. Side-load cover nuts and fit the cover with two M2×6 screws.
   The cover is a positive restraint, not a spring-contact substitute.
5. With USB cable absent and both shell screws absent, align the integral bezel
   with the proposed **mouth-open -Y slot** and insert the entire cartridge +z.
   The front flange stops at the mouth; the USB solder anchors are not the
   insertion stop or shell attachment.
6. Install the two opposed insulating shell screws only after their supported
   carrier pockets and actual bell-hole locations are approved.

To service, **unplug USB first**, remove both shell screws completely and pull
the whole cartridge **out toward the mouth (-z)**. The slot is axially open to
the mouth so the connector/bezel can leave with it. A closed side hole would
trap a protruding connector; hiding the shell in CAD would not resolve that.
Remove the cover for cell access only with the cartridge out. For PCB/speaker
access reverse the sequence: cover/cell, cradle/PCB, yoke, speaker.
Path samples are rigid-body screens—not continuous, tilted, cable-inclusive,
tool-inclusive or tolerance-qualified proofs.

## USB and proposed shell modification

The integral bezel supports an insulating channel between connector and bell.
It is **open at the handle-facing end**, allowing the PCB/USB tongue to lower
into place before the cradle is attached. An upper crossbar would block that
assembly motion. Its independent under-USB ledge ends atz16.8,0.2 mm below the
source proxy's z17 underside; this is an unqualified support take-up gap, not
permission to bend the connector or treat solder anchors as a structural stop.
Its -Y shell slot, open to z0, remains covered by the installed carrier structure.
Two radial attachment holes are modeled at **±X, z3**; they are a proposal,
not a ready drilling jig. There is no hidden adhesive dependency.

The report compares the **exact consumed connector proxy** with the working
*outside* shell, not merely the cavity. Maximum supported electrical placement
may still leave it recessed. **No flush claim is made.** An unselected
8.8 × 8 × 2.6 mm USB nose screen is for first access checks only; actual plug
nose projection, overmold width, mating travel, cable bend, support force and
connector mouth datum require a chosen drawing or measurement. A plastic
tunnel cannot turn an unsupported relocated connector into a valid footprint.

## Provenance, reproducibility and gates

### Actual fit findings and bounded alternatives

The final values remain machine-readable in `fit-report.json`. Representative
results from the supplied83-component manifest:

| Exact BRep screen | Result |
|---|---|
| Internal material overlaps | **0**, including **0 contact/cell material penetration** with the corrected outward-thickness construction |
| Printed structural pieces | **4**, each one connected valid solid |
| Body / working shell | No overlap; minimum0.180 mm, reflecting the concave profile and assumed0.30 radial register gap |
| Guarded yoke / working shell | No overlap; minimum0.296 mm; plastic, not exposed fastener |
| Metal yoke screws / shell | Minimum1.696 mm, improved from the older approximate0.35 mm screw finding |
| Metal PCB screws / shell | Minimum1.841 mm; heads recessed in insulating cradle cups |
| Metal cover screws / shell | Minimum2.763 mm |
| Bare full T8 envelope / shell | No overlap; minimum**1.081 mm**, below a1.25 mm guard target even before clearance |
| Rounded full-cell reference,0.15 clearance +1.25 offset | **9.141 mm³ shell overlap**, not just a squared stock-corner artifact |
| Actual cradle / shell | **2.641 mm³ overlap** |
| Actual cover / shell | **135.675 mm³ overlap** |
| Each supplied loaded254 metal contact / shell | Approximately**0.02175 mm³** nominal interference retained; no tolerance clearance may be inferred |
| Speaker / component minimum gap |0.500 mm |
| Yoke / component minimum gap |0.250 mm; remains unqualified despite no material collision |
| Modeled straight hex-key paths | No collisions with the parts present at their assembly stage; key handles and tilted access excluded |

All ±0.5 mm cell displacement probes meet positive plastic stops in their
appropriate directions. This is not a shake/drop test or a quantified load split
between cradle and spring contact. Springs can still be loaded before a nominal
clearance closes. The loaded ear proxies touch the can envelope tangentially;
in particular a positive clip cannot be declared insulated from a negative can
without an actual wrapper/liner/contact-force review.

The contact base occupiesz22.1..22.4 and the full can startsz23.68, leaving
**1.28 mm total**. A1.25 mm layer plus two nonzero clearance allowances cannot
be silently fitted into that space. The upper254 spring is also the wrong place
to assume free insulating thickness: its supplied tall end nearly touches the
working shell.

**Bounded next choices, not fabricated fit claims:**

1. Rework/select a shorter, genuinely drawing-supported contact geometry and
   an actual maximum cell/button envelope, while keeping independent can
   support and full terminal insulation. The current fixed D43/Fz20.5 stack
   does not establish that a different clip fits. The electrical/contact
   investigation owns that selection; this study does not trim a254 spring.
2. Reconsider stack location and front projection together. Existing mouthward
   translation samples of the current failed guards retain10.423 mm³ shell
   overlap at5 mm shift and0.060725 mm³ at8 mm; the12 mm sample is clear.
   This brackets only those sampled **guard/shell intersections**, not a new
   accepted configuration. Moving only the PCB toward the mouth would hit the
   speaker; moving the whole stack requires a redesigned outward front body,
   flange supports, USB opening and screw locations. A12 mm shift is not an
   instruction to insert the present design differently.
3. Revisit the cell family/size with owner approval if the combined measured
   shell, complete254 geometry and proud-plastic target remain mandatory.
   Do not reduce the reported protection/insulation target simply to turn a
   fit report green.

Current service-path samples start from a conflicting guard configuration;
they therefore **do not prove that this complete assembly can first be
installed or withdrawn in a real shell**. The mouth-open USB-slot architecture
removes the *separate* closed-hole connector trap. Internal speaker→yoke→PCB
order and access remain modeled, but the external guard gate must close before
using that procedure physically.

See [REPRODUCE.md](REPRODUCE.md). FreeCAD exports STEP before tessellation,
reopens native files, compares BRep symmetric differences (not just bounding
boxes), reconstructs solid BReps from STL and verifies embedded raw source
bytes. The report distinguishes intended cell/terminal contact from other
material intersections. Nominal distances are not manufacturing tolerances.

The original geometry, script, SVG and this documentation are MIT under
[mechanical/LICENSE](../../LICENSE). No vendor photo, third-party CAD or
manufacturer mesh was copied. Mixed populated models preserve adapted
electronics **CC BY-SA3.0** context, including the complete
[Adafruit-derived hardware notices](../../../hardware/handbell/README.md)
and [attribution policy](../../../ATTRIBUTION.md). Referenced sources retain
Limor Fried/Ladyada for Adafruit Industries (5768/4654) and Bryan Siepert for
Adafruit Industries (4438). Carry those notices with standalone populated files.
There is no vendor endorsement or blanket-MIT relicensing.

Owning work remains E01/#1 (measurements), E04/#4 (protection/contact/flash),
E05/#5 (capture, service, USB), E07/#7 (placed assembly before routing) and
E10/#10 (eventual retention/insulation/use qualification).
