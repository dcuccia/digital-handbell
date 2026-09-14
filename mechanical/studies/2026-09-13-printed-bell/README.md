# Original printed bell — September 13

**Exact all-front stage-1 assembly; coordinated mechanical interface ready
for the parent's authorized routing stage.** The native and exports at this
study root bind the actual `printed-bell-front` PCB, schematic, manifest,
contact companion and source libraries: **81 F electronic parts plus two
fitted B contacts**. No PCB growth, changed mounts, USB relocation, lowered
cell or shortened inductor was required.

The current checker passes exact input/output hashes, native/STEP BRep
round trips, all nine inert meshes, zero static material overlaps and the
declared assembly/service poses. This is engineering confidence in the
**unchanged mechanical interface**, not electrical-rule waivers, physical
tolerances, a qualified print, live-cell use or fabrication approval.

The earlier `development` directory is explicitly a frozen mixed-face
checkpoint, **not the current assembly**. Open the root native below.
Final mode never automatically falls back to that old electronic population.

**Parent visual-review finding corrected:** the former R29.5 shell-fastener
pockets broke through the cosmetic exterior. Static nonintersection alone
had not established a closed skin. The three printed shell/carrier joints
are now at **R26.5, angles90/210/330 degrees**, with radial hex flats,
inside-only nut entry and positively verified **at least1 mm geometric
exterior stock**. The actual shell retains every original revolved cosmetic
side face except the intentional USB channel; measured missing face area
in the BRep check is **0 mm2**. PCB, USB, speaker, cell and contact datums
did not change. The earlier rendered checkpoint remains preserved at
commit `6e7ef9ef4dd1f6611695e73227630fdc5c8dae7a`; a new parent rendering
should use the corrected root native, not those earlier images.

## Released mechanical interface for routing

The actual all-front placement and full retained contacts fit the complete
shell/cartridge/yoke/capture/handle assembly. Critical routing can proceed
without changing the D43 outline, mounting holes, USB XY/Z, contact lands,
cell axis or speaker-relative PCB stack listed below. Keep these interfaces
fixed. Copper-only changes still require a new exact-byte bind by the parent;
do not silently treat a changed PCB hash as already reviewed.

| Bound source | SHA256 |
|---|---|
| Placement manifest | `710717186d5ecc795edaf3da7eec8f6532f34077906645a8fca32318320f23c4` |
| Actual PCB | `17dc83ce5dce2af72a816bc6d5224a874ad6c7fac6eac0bc59d0ced8662adf53` |
| Actual schematic | `e131a8d093795df7285bcae4a8886ffe01106c6513a19bd588ee7c29c6993b4f` |
| Contact companion | `f96133d9f044600167477bcddbf67c43311ed0897066db9fa63d8e7f8118467b` |
| Dated design-input bytes | `e0006b59412f4a0184744e0aa9cebbab2b7f11e57228aa5997de904f1b48916e` |

The electrical package retains its four known USB clearance findings and
unfinished silk/text findings; mechanical release does not waive them.
Actual USB tails/cable, loaded contact/cell geometry, insulation, strength,
temperature and printing gates remain open as detailed below.

## Shape and size

This is an original revolved Bezier design: continuous flared mouth, concave
sides and rounded narrow crown, with no broad handguard disk. No supplied
photograph, traced outline, logo or artwork is imported or redistributed.

| Working CAD feature | Dimension |
|---|---|
| Maximum shell diameter | 70 mm, versus previous 75.5 mm comparison |
| Shell body height | 55.8 mm, versus previous 56.3 mm assembly comparison |
| Handle above crown | 80 mm, versus previous 85.5 mm |
| Complete height | 135.8 mm |
| Grille/front mouth plane | z0, no projecting skirt |
| Speaker front / conservative basket rear / magnet rear | z4.5 / 16.5 / 23.5 |
| PCB F / B | z25 / 26.6 |
| Full D16.4 x L34 provisional cell axis | z36.38 |
| PCB mounting holes | (+10,+15.7), (-10,-15.7), D2.2 |
| USB native origin / mouth | (0,-22.82) / (0,-27.90) |

These are authored CAD dimensions, **not measured tolerances**. The profile
does not rescale the old metal bell. Its independent cavity follows the
retained hardware, and the flush carrier replaces the former projecting
external band. Exact part volumes and component/structure distances are in
`fit-report.json`; do not convert volumes to mass without a
declared material density and slicer settings. No normal wall thickness,
global printable tolerance or support-free claim is made.

Current nominal solid volumes (not slicer consumption or measured mass):

| Printed part | BRep volume |
|---|---:|
| One-piece shell | 22.413 cm3 |
| Black handle | 19.883 cm3 |
| Flush carrier/bezel | 9.656 cm3 |
| Retained yoke | 2.117 cm3 |
| Retained cradle | 2.112 cm3 |
| Service-relieved cover | 1.597 cm3 |

The carrier is approximately 57.4% lower volume than the preserved T8 body;
this comparison does not imply equal stiffness or printing time.
The actual **all-front** minimum component-to-speaker gap is **0.400 mm
(D3)**; the minimum component-to-yoke gap is **0.700 mm (L1)**. L1 retains its
full 5 mm height at z20..25 and clears the yoke top z19.3. The USB source
body-to-carrier ledge gap is **0.200 mm**. These small CAD distances are not
qualified printing, component-envelope or assembly tolerances.

## Six structural prints and the retained architecture

The shell is **one connected printed solid**, including its crown and three
cartridge attachment lugs. The black handle is separate. The cartridge still
has four pieces: flush grille/carrier, speaker yoke, cell cradle and cover.
Yoke and cradle are exact read-only T8 BReps translated into the new frame.
The cover retains that architecture but adds two straight upper-spring service
channels and outside wall stock, described below. Successful capture, M2
joints and under-cell insulation are not casually replaced.

The carrier has a flush perforated grille, speaker seat, two yoke supports,
USB support ledge and color-matched service-channel filler. Removing the
old exterior skirt reduces material without cutting away the cell capture.
The speaker remains the conservative D40 body through 12 mm, followed by
D21.70 x H7 magnet. An illustrative tapered basket is **not** substituted
to hide interference. Rim bearing, terminals, wires, vent and excursion
remain unqualified.

Only the inert PCBA STL omits BT1/BT2. Full **thin** contacts remain in native
and STEP. They are still fitted components and are not copper-only BOM
exclusions. Known T8 fold-root meshing limitations are not repaired by
inventing connecting metal.

### Battery insulation and retention

The cell remains at PCB B + 9.78 mm. The 0.30 mm contact base stays below a
verified 1.08 mm under-cell plastic section; no floor or contact is lowered
through metal for apparent height savings. Exact retained contact/guard
geometry is checked against the supplied contact contract in final mode.
The inherited constructive guard-stock proof is identified as historical
evidence for unchanged local material; its old metal-shell margin does not
apply to this new shell. The new full-PCBA service check found that the old
cover's purely vertical removal path crossed the outward-flared spring tips;
the old check had included only cell and cradle, not contact metal.
The new cover therefore has straight end clearances with added exterior
stock, preserving witnessed **1 mm actual external end, side and top walls**.
Neither thin contact nor the cradle floor is clipped. The split seam and
cell-facing contact opening remain intentional, unqualified insulation
interfaces—not a claim of a globally sealed dielectric enclosure.

The cover/cradle provides stops in all six directions with the cartridge
outside the shell. Half-millimetre inert-cell displacement probes demonstrate
geometric stops, **not** force, loaded spring travel or impact retention.
Plastic outside removes the former metal-shell short path but not the
positive contact below the negative cell can. Wrapper abrasion, independent
insulation, cell polarity/button, contact force and raw CELL_NEG isolation
from protected GND remain gates.

## USB and reversible servicing

There is a 15 mm wide **mouth-open** -Y shell channel, filled by a 14.4 mm
color-matched bezel integral with the cartridge. Installed cosmetic continuity
does not rely on a broad exterior band.

**Second parent visual finding corrected:** the original rearward loading
cuts removed the curved bezel above/around the connector, so the nominal
9.2 x3.1 cutter did **not** define the whole effective opening and a blue
PCB-edge strip remained exposed. The carrier now includes a real,
same-color **locally raised flat front skin**, not a visibility/rendering fix:

| Actual port feature | Authored dimensions |
|---|---|
| Skin width / height / thickness |14.4 /7.0 /1.0 mm |
| Front / rear planes |y-29.1 /-28.1 |
| Skin bottom / top |z20.0 /27.0 |
| Effective aperture |x-4.6..+4.6, z21.7..24.8: **9.2 x3.1 mm** |
| Material beside / below / above aperture |2.6 /1.7 /2.2 mm |
| Skin-to-source USB separation |0.200 mm |
| Skin-to-actual PCB separation |1.250 mm |
| Skin-to-shell separation |approximately1.055 mm |

The skin lies wholly ahead of the rear loading cuts beginning at y-28.0.
It joins the existing carrier rails with real material. The actual cut
front-face opening is **28.52 mm2**, exactly the intended aperture:
both additional opening area and blocked intended area are **0 mm2**.
The complete1 mm thick frame is contained in the released carrier.

The entire actual PCB tongue-front projection (x±5.75, z25.0..26.6) has
real1 mm material in front of it. The upper lip therefore conceals that
edge in the horizontal -Y front view; arbitrary oblique sightlines are not
claimed. This does not hide or move a PCB object in the native model.
The whole PCBA remains at least0.2 mm behind the skin rear plane for
**every pure Z loading translation**, and the complete assembly-path checks
still pass. The original receptacle/PCB datums and source envelopes are
unchanged, and the under-body ledge remains0.2 mm below the nominal USB body.
All carrier material remains within the existing D70 ceiling; shell
D70/H55.8 is unchanged.

An explicitly **unselected** 8.8 x 8 x 2.6 mm male-nose screen approaches
the source mouth without intersecting shell/bezel. In addition to pose
checks, the **exact continuous straight swept union** of that8 mm nose
over12 mm approach travel, spanning y-47.9..-27.9, has zero shell/carrier
intersection. This does not prove actual mating depth, overmold fit, a
complete cable or insertion force. Source
through-board anchor XY reservations are retained as hidden planning
projections, not invented tail-height solids.

Unplug before removing the three recessed front M2x8 screws. The captured
cartridge withdraws straight mouthward through the open channel; a closed
side hole would trap its protruding connector. The carrier ledge/rails,
front screws and shell are the intended handling-load path, not unsupported
solder anchors. Their physical force/deflection performance is unqualified.

### Closed-skin shell/cartridge fasteners

Only the three **printed shell-to-cartridge** joints moved. They are not the
two PCB mounting holes. Their common XY centers are (0,26.5),
(-22.949673,-13.25) and (+22.949673,-13.25). Rotating the pattern away from
the retained lower yoke posts/nuts and the USB channel permits inward
placement without colliding during whole-cartridge withdrawal.

Each M2 nut enters radially **from inside the empty shell**, through its
inward-opening slot. Nut/pocket hex flats face radially. The seated nut
occupies z7.0..8.6, inside a z7.0..8.9 pocket. The M2x8 screw head remains
recessed in the front carrier: under-head z2.3, tip z10.3, complete1.6 mm
nut-body coverage and1.7 mm beyond the nut. The nut bears on a witnessed
**3.7 mm actual shell floor**, with a **2.6 mm captive roof** above the pocket.
Neither nut fit nor nominal screw coverage is a qualified preload/thread,
torque, loose-part retention or printed-strength rating.

`shell_cartridge_joints` in the fit report records:

- **All nine actual void primitives**—three hex pockets, three inward
  loading slots and three screw bores—positively offset by1 mm and wholly
  contained within the unchanged outer solid, clear of the USB opening.
- The original lower cavity positively offset by1 mm and contained within
  that outer solid across the complete affected z band.
- Actual floor/roof annulus material contained in the released shell.
- Zero missing original cosmetic-side surface area except the deliberately
  mouth-open USB channel.

These constructive checks establish exterior stock without unsupported
nested-shell distance extrema or a rendering/transparency trick. Interior
nut entry and front screw access are intentionally open; there are **no
additional cosmetic side openings**. Exact static checks, inward nut
loading, front screw insertion/removal and driver paths, and cartridge
withdrawal with the shell nuts left installed all pass. D70/H55.8 and the
one-solid shell are unchanged.

### Rear polarity-label visibility

The proposed `+POS` at(+11,10.5) and `-NEG` at(-11,10.5) are **obscured by
the retained cradle**, even with the cover removed. The negative position
also projects beneath its retained cover-joint nut. No PCB was edited and
the active routing source was not read.

The following existing-PCB locations pass complete rectangular sight-column
checks with the cartridge outside the shell, cover and its screws removed,
and cell/contact metal still installed:

| B.SilkS text | Recommended common XY | Maximum screened text rectangle |
|---|---|---|
| `+POS` | **(+15.7,+11.0)** |4.4 x1.4 mm |
| `-NEG` | **(-15.7,+11.0)** |4.4 x1.4 mm |
| `T8 BUTTON END >` | **(0,+10.5), unchanged** |12.0 x1.4 mm |

The full rectangles lie on the exact existing PCB and have zero projected
capture/cell/contact/hardware obstruction. They are **mechanical reservations,
not inspected KiCad glyph bounds**: the electrical owner must keep actual
mirrored B.SilkS strokes within these envelopes and run native silk checks.
Hidden native reservation boxes and `back_silk_visibility` record both the
rejected initial locations and tested alternatives. These label moves do not
change the mechanical PCB freeze.

## Handle and shell load path

The working handle uses a **M4x16 machine screw** pointing handleward from
inside the empty crown, nominal pan head D8/H3.1, large washer
OD12/ID4.3/H1 and metal nut AF7/H3.2. This is a geometry selection using
parent-confirmed **supplier dimensional tables**, not inspected ISO primary
standards or a qualified hardware lot, and not an interchangeable 8-32 thread.
The [ISO7045-labelled supplier page](https://www.fasteners.eu/standards/ISO/7045/)
explicitly displays a **DIN7985** table. The model screens its maximum
head diameter 8.0 mm and height **3.25 mm**, M4x16 under-head length
15.65..16.35 mm, [nut](https://www.fasteners.eu/standards/ISO/4032/)
AF6.78..7.0/H2.9..3.2 and [large washer](https://www.fasteners.eu/standards/DIN/9021/)
ID4.3..4.48/OD11.57..12.0/H**0.9..1.1 mm**.

The nut slides through an accessible side tunnel and bears on real printed
material. A 12 x 10 x 2 mm keyed tenon engages the crown, so friction or
printed screw threads are not the only antirotation means. There is no
handguard disk. The nominal screw fully spans the 3.2 mm nut and projects
3.45 mm past it. Even the shortest screw with the thickest washer projects
3.0 mm beyond the maximum-height nut; full nut-body coverage is 2.9..3.2 mm.
This is **not certified effective thread engagement**: actual thread runout,
chamfers and a fully threaded supplier part still need confirmation.
The washer bearing region contains a checked OD12/ID4.4 annulus
of 2.35 mm actual shell material below the key pocket.

Nominally the screw head is z47.2..50.3, washer z50.3..51.3 and nut
z59.65..62.85. Tolerance cases hold the washer bearing plane at z51.3:
the thickest washer plus highest head reaches mouthward to **z46.95**.
The screw tip range is **z65.85..66.75**; the extended blind bore ends
at z68, leaving at least **1.25 mm** tip clearance.
The tolerance-case BReps and empty-shell insertion checks are recorded in
`handle_joint.supplier_tolerance_screen` and hidden native construction objects.
In the current retained capture geometry the screw-to-cell distance is
2.62 mm and screw-to-cover distance approximately 1.353 mm.
Those two values are **nominal**, not the conservative tolerance-case result.
At maximum head/washer thickness, the checked clearances are **2.370 mm to
the cell and 1.133 mm to the cover**. The authoritative report separately
lists each maximum-head/washer case.
None is a physical fit, torque, preload or printed-strength rating.
**M4x20 is not interchangeable:** its maximum tip would reach z70.8,
2.8 mm beyond this blind bore, requiring a redesign and new bind.

**Handle loads go through nut, screw, washer and integral shell crown, not
through the cell or PCB.** Install/remove this joint with the cartridge out;
the battery correctly blocks an axial driver when installed. The modeled
empty-shell straight-driver and screw/washer/nut insertion paths are recorded.

A later turned-wood option can use the same original exterior silhouette,
but needs a separately engineered metal insert/cross-dowel, keyed shoulder
and wood properties. No wood pilot, ordinary wood screw or printed thread
is qualified here. Changing the screw length requires checking engagement,
tip clearance and tool access again.

## Assembly and printing

1. With the shell empty, side-load the handle nut, fit the keyed handle and
   insert washer/screw upward through the mouth. Install the shell's three
   M2 nuts inward-to-outward in their roofed pockets.
2. Outside the shell, install the carrier nuts, load the speaker first, then
   fit the yoke and its two retained M2x6 screws. The D40 speaker cannot pass
   through the installed small magnet aperture.
3. Load the yoke nuts, lower the PCBA into the open-top USB support, then add
   the empty cradle and two M2x6 screws.
4. For inert evaluation only, install the cell surrogate, cover nuts and
   cover with its two M2x6 screws. Keep capture closed during whole-cartridge
   removal.
5. Align the port bezel, insert the cartridge and install three front M2x8
   screws. Reverse the sequence to service. Loose nuts need a tray.

The model includes static material intersections, finite withdrawal/plug
poses, speaker-before-yoke, yoke-over-magnet, PCBA loading, cover removal,
M2 driver access, handle installation and shell nut loading. Finite poses
are not exhaustive continuous-motion or deformable-contact proofs.

Print the **shell mouth-down/handle-up** and the **grille separately
face-down** for a smooth cosmetic exterior. The upper internal crown slopes,
nut-pocket roofs, locally raised USB surround/aperture roof and handle side tunnel need explicit slicer support/
bridging review. The wide mouth gives internal support-removal access
**before assembly**. No universal support-free claim is made. STLs retain
assembly coordinates: import millimetres at 100%, translate/reorient, never
scale. Material/strength/creep/temperature settings are the parent's separate
evidence work; silk appearance alone qualifies none of them.

## Files and review

Open [`printed-bell.FCStd`](printed-bell.FCStd) for the current assembly. Gold shell/
carrier, black handle, amber yoke, blue/cyan capture and purple cell have
saved headless visibility/color metadata. Construction references (USB nose,
anchor reservations, export compounds and driver) are hidden. Shell
transparency assists parent GUI inspection; no GUI approval is claimed.

The study root contains full assembly/cartridge/PCBA STEP, component STEP,
six structural INERT STLs plus contact-free PCBA, speaker and full-cell
surrogates, original profile SVG, exact raw-input snapshots, fit report,
artifact inventory, fresh completion marker and local build log.

See [REPRODUCE.md](REPRODUCE.md). The native report records FreeCAD1.1.3,
OpenCASCADE7.8.1 and bundled Python3.11.14. Its
`routing_interface.mechanical_freeze_recommended` is true for the **exact
bound stage-1 sources**, not a different board or an electrical/safety signoff.

Original mechanical geometry, SVG, code and documentation are MIT under
[`mechanical/LICENSE`](../../LICENSE). Mixed populated exports retain the
adapted electronics' **CC BY-SA 3.0** context and full
[hardware notices](../../../hardware/handbell/README.md) and
[attribution policy](../../../ATTRIBUTION.md): Limor Fried/Ladyada for
Adafruit Industries (5768/4654), Bryan Siepert for Adafruit Industries (4438).
Do not distribute populated files under a blanket MIT label.

Owning epics: E04/#4, E05/#5, E07/#7 and E10/#10. No purchase, fabrication,
live-cell activity, GUI launch, issue posting, commit or push is performed
by this mechanical implementation.
