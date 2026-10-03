# Quilter workflow learning study

Owner approved October 2 at 14:05 local; fully personal project.
The goal is an economical owner/agent/layout-service workflow, not recovery
of sunk token cost or human-style trace aesthetics. The two rejected raw
outputs and the authoritative 37-open board remain immutable evidence.
Tracking: E04/#4, E05/#5, E07/#7 and E08/#8.

**October 3, approximately 14:30 owner continuation:** keep advancing for
the next hour. Use **15:30 local as the conservative stop**, stop starting
new items by 15:20 and leave time for the final checkpoint. Work remains
sequential and bounded to 10-15 minute items with at most two corrections.
Start with the BT1/BT2 surface-rule fixture below; continue only through
qualified dependencies. This is not permission to waive a blocker, alter
the source, pay, fabricate, power hardware or submit unqualified input.

**October 3, 13:20 owner update:** continue the study with modest packaging
flexibility. The owner explicitly confirmed a nominal **D43-45 mm main PCB
body and 0-2 mm additional PCB-to-speaker spacing**, retaining the general
bell shape. The coordinated enclosure update may wait until a worthwhile
layout is selected. See the [current flexible-packaging scope](#october-3-flexible-packaging-study).
This supersedes treating all existing plastic supports as immutable
obstacles, not real-part/access/electrical requirements or source protection.

**Morning checkpoint:** authenticated read-only browser access and a partial
mechanical screen are established. The existing job and authoritative source
remain unchanged; qualified trial domains and imported-model checks still
precede a new job. No further inventory rerun is needed.

**Historical October 2, 14:22 owner update:** a few bounded reruns were authorized, with work
finished before 15:00 local. First recover the read-only inventory in one
ten-minute item, at most three native executions with 90-second subprocess
limits, stopping by 14:34. Stop starting new items by 14:50 and reserve
checkpoint time. This supersedes the no-retry hold below, not source,
input-qualification, payment, process or acceptance gates.

## October 3 flexible packaging study

The owner wants a practical layout-service workflow, not a PCB forced to
fit an enclosure designed around the earlier manual floorplan. Keep the
general bell shape and do not repeatedly regenerate CAD. The confirmed
limits are **study bounds**, not a chosen final board/enclosure size:
main PCB diameter 43-45 mm, nominal 1.6 mm board thickness, and up to
2 mm more axial separation between PCB and speaker.

The diameter allowance is **2 mm total, or 1 mm per radial side**. It is
not permission to scale every board coordinate, shrink real components or
stretch the battery contacts. The true outline includes tabs and a USB
tongue; a disk-area calculation cannot qualify its reconstruction. Likewise,
moving the board towards the handle moves its contacts, cell and associated
rear packaging together. It does not create free rear volume or allow
compression of the contact/cell stack.

| Keep as a physical/electrical requirement | Permit adaptation instead of freezing old geometry |
|---|---|
| Actual speaker, components, contact/cell datums and unscaled footprints | Board main-body envelope within the study bounds; corresponding modest shell changes |
| Five mandatory process vias, contact-metal clearance, protected/raw-negative isolation | Printed yoke legs, support webs, cartridge and cradle/cover geometry |
| Real holes/fasteners, engagement, insulating/structural material and tool access | Shape and location of printed supports, subject to those same load/access duties |
| USB and J1/J2 mating, cable/latch access and recovery-pad service | Bezel, connector access channel and wire routing when the selected layout is rebound |
| Component-relative decoupling, clock/boost/private-return constraints | Former coordinate-bound floorplan and obsolete pour-exclusion coordinates, after explicit re-expression |

Keep the nine current fixed XY poses and five process vias for the first
comparison as a **variable-control choice**, not a claim that every mount
or connector can never move. Any later XY change needs its exact associated
interface disposition; do not independently stretch contact pairs or detach
process vias from their protected pads.

**Changed next-step strategy:** do not spend the next item deriving a
mandatory placement mask from every old plastic support. Use saved CAD as
reference evidence where it describes real hardware and access, carry an
explicit adaptation ledger for redesignable plastic, and construct
conservative trial reservations for the selected packaging envelope.
Unknown loaded-contact motion, real mating paths and minimum structural or
insulation requirements are not silently made acceptable by deferring CAD.
An unsupported constraint must be reserved, retained as a reviewed block,
or escalated before it is relied on.

The cheap size sensitivity uses only four endpoint combinations
(`D43/D45` times `+0/+2 mm`), **not four cloud jobs**. Select one packaging
envelope shared by the four/six-layer comparison so the experiment does not
confound layer count with a different board size. Eight layers remains
optional, not a default extra branch.

Full coordinated native enclosure/assembly rebinding remains required
before accepting a selected layout, fabrication or powered use. It is no
longer required at every disposable placement iteration.

### Size sensitivity and engineering choice

The [source-bound numerical report](measurements/2026-09-27-router-bakeoff/quilter-packaging-sensitivity-2026-10-03.json)
is accepted for arithmetic/requirement planning only. Root independently
checked all 81 F rows in every case, strict sign classifications, 104-reference
accounting, formulas and unchanged PCB/schematic/project/manifest hashes.
No native CAD/PCB tool ran; no component, outline, copper or assembly was
changed.

The endpoint calculation shows that the small allowance is useful:

| Nominal main body | Extra speaker spacing | Disk-area proxy | F bodies below / equal to / above nominal magnet gap |
|---|---|---|---|
| D43 | 0 mm | 1,452.20 mm2 | 64 / 5 / 12 |
| D45 | 0 mm | 1,590.43 mm2 | 64 / 5 / 12 |
| D43 | 2 mm | 1,452.20 mm2 | 79 / 1 / 1 |
| D45 | 2 mm | 1,590.43 mm2 | 79 / 1 / 1 |

D45 provides a **9.52% larger nominal disk area**, not a demonstrated
9.52% increase in usable routing space. The 2 mm axial allowance increases
the nominal magnet gap from 1.5 to 3.5 mm. Among the **76 eligible fitted
F parts**, those not strictly below that gap fall from 14 to **one: L1**.
The other zero-gap part at +2 mm is the fixed X6 USB connector, which
remains peripheral; zero gap is not accepted clearance or a relocation
proposal. The two rear contacts are not included in this front-face test.

**Astra's provisional choice for input qualification is D45 with +2 mm
spacing**, shared by the first four/six-layer comparison. This uses the
owner's modest allowance to remove avoidable placement restrictions before
spending cloud/review effort. It is not a final-size or mechanical-fit
acceptance. Do not run all four geometries in the cloud or begin a shrink
optimization; revisit dimensions only for a concrete result or conflict.

At +2 mm, the PCB faces would be z27/z28.6, cell centre z38.38 and nominal
contact top z45.19 rather than z43.19. Those are rigid-translation study
stations, not newly authored CAD. The contact drawing's 0.38 mm height
tolerance is additional dimensional information, not a complete loaded
motion envelope. Shell taper, crown/handle hardware and service paths
still require coordinated adaptation; raising the board alone does not
prove the rear assembly fits.

**Next bounded item:** qualify one exact D45/+2 trial envelope and its
physical reservations, without regenerating the whole enclosure. Preserve
the tab/USB-tongue interfaces explicitly, keep the nine initial fixed poses
and five process seeds, reserve whole-body peripheral space for L1, and
account for contact metal, hardware and connector/service access. Record
each plastic adaptation separately from real occupied/access volumes.
Only after that result should the disposable PCB be staged and imported
for placer/association/rule qualification. No routing or cloud job is
released merely by the arithmetic result.

The reproducible standard-library calculation and exact input-contract
snapshot remain under experimental
`quilter\outputs\packaging-sensitivity-20261003T1328-sol`.
Final report SHA-256:
`85368ffc33fd1dd0cea22a9de8ac3510f39821953d939bf8f0a83d6d1d315b8c`;
`calculate_packaging_sensitivity.py`:
`3186fb654af4eae0e4ed772027aa5b05f7ed6a700a2bbf6ccfb7400a4e264142`;
`workflow-contract-input-snapshot.json`:
`f9412acd0a552a7986811b5f8a07a4dd549e7251876a2818861d954e6d46cde7`.
That snapshot is the calculation-time contract; this live workflow later
adds the report digest and lead's provisional decision. Replay using the
recorded input bytes in a disposable context, not by replacing live files.
One corrective pass fixed a mislabeled PCB-front station key; reported
area/count results did not change.

The public [placement guide](https://docs.quilter.ai/guides/placement-guide)
and [KiCad region instructions](https://docs.quilter.ai/design-parameters/placement-regions)
were rechecked during this item. On-board components are treated as
preplaced, and retained vias block placement. Therefore merely enlarging
the old board or unlocking footprints would still not exercise the placer:
an eventual disposable input must stage intended movers outside its
**new** outline, retain only explicitly required copper/process geometry,
and verify the imported movable population. KiCad region membership must
be reviewed manually; F-only restrictions and the union semantics still
apply. None of those preparation operations was performed in this item.

## October 3 trial-envelope engineering review

**Concrete geometry packet complete; full input release remains gated.**
The [trial-envelope JSON](measurements/2026-09-27-router-bakeoff/quilter-trial-envelope-2026-10-03.json)
and [Edge.Cuts text fragment](measurements/2026-09-27-router-bakeoff/quilter-d45-edge-cuts-fragment-2026-10-03.txt)
are accepted as proposal/evidence, not applied to a board. The fragment is
not a complete KiCad document and has not passed a native round trip.

The afternoon continuation turns the D45/+2 choice into an explicit
outline proposal and physical-reservation records, not a newly routed or
staged PCB. The main-body circle may absorb the old contact support tabs;
their required laminate/pad support must remain, not necessarily their
former protruding shape. The USB tongue retains its 11.5 mm width and
common-Y -26.85 mm end. No footprint, contact spacing or pad is scaled.

The analytic union has **1,643.301 mm2 area and 45 x 49.35 mm bounds**,
including the tongue. Its ordered contour has three arcs and three lines.
Root independently checked the serialized endpoints/arc points and proved
that every one of the 163 old outline segments lies wholly in the new
disk or tongue rectangle. All four outer tab corners are inside the D45
disk. The exact parameter definition is separate from six-decimal
coordinate serialization (maximum per-coordinate rounding 0.000000487 mm).
This establishes containment, not native PCB/fabricator acceptance.

The source L1 whole-body example has 12.7446 mm minimum distance to the
origin, exceeding the R11.1 magnet-planning exclusion, and clears both
R3.2 mount reservations while lying wholly in D45. This confirms at least
one geometric peripheral location; it is not an electrical placement or
via-access approval. Seven fixed fitted proxies plus two mount domains,
all 104 classifications and five exact process-via records are carried.

The independent hardware/access review establishes these distinctions:

| Existing evidence | Trial treatment | Still not established |
|---|---|---|
| MH1/MH2 each already specify a 3.2 mm planning radius, 2.2 mm drill and 4.4 mm pad | Preserve that radius as a component/hardware reservation, not just a drill circle | Supplier tolerances, screw engagement and the adapted assembly/service path |
| Modeled M2 head D3.8, nut AF4 and straight driver R0.95 | Head R1.9, hex-nut circumradius 2.3094 and driver all fit nominally within R3.2, including an additional 0.25 mm radial allowance | An XY containment calculation is not a complete tool insertion or strength test |
| J2 current proxy is 4.8 x 6.25 x 3.1 mm | Preserve its offset and rotation; its depth already includes the historical 0.7 mm front mating planning allowance | Full cable bend, latch/finger access and toleranced mating maximum; do not add the 0.7 mm twice |
| X6 current body protrudes beyond the tongue and needs a cutout | Preserve its exact native datum and existing B-side planning reservation | Complete plug/overmold/mating and redesigned bezel load path |
| Contact primitives distinguish board-adjacent bases from elevated spring/ears | Keep actual base geometry separate from a conservative full-height projected shadow | Loaded travel is not bounded by either a nominal proxy or the height tolerance alone |

Source evidence: `tools/build_t8_cartridge.py` SHA-256
`22e806153f313685a9a96d12b90070bb1985259b50261011ac6ce0d298a4f04c`
defines the nominal M2 head/nut solids;
`tools/build_printed_bell.py`
`dcfae50c8a030af0c00d735107bc55b472a29d3b94d7cddb3d9eccbbfedcab14`
contains the inherited hardware and straight-driver screen.
The earlier J2 interpretation is recorded in
`docs/mechanical-feasibility.md`
`bd81f3bede2195f01e1686d4637e7d3e243dbdfa01818941bacf5cf13880bec9`.
These sources are read as evidence, not rerun to rebuild the assembly.

Both complete R3.2 mount reservations fit within the D45 main body with
0.6858 mm nominal radial room. This is useful additional space compared
with using only the drill holes as obstacles, but it does not include
manufacturing allowances beyond the stated planning geometry. The nominal
hex-nut circumradius plus 0.25 mm leaves 0.6406 mm inside the reservation.
The existing straight-driver check also did not include every component
as an obstacle; it cannot be transferred wholesale to arbitrary placement.

**Contact-mask disposition is the concrete next blocker.** A deliberately
coarse full-height contact shadow, expanded by 0.25 mm clearance plus the
new-via 0.302 mm radius, covers the existing C24 process-via centre. The
actual board-adjacent base polygons do not: using C24's actual 0.300 mm
copper radius leaves **0.393331 mm beyond the required 0.25 mm clearance**.
All 30 checks (five protected vias against six bases) have positive
clearance margins. This is a distinction between a projected envelope
and actual base geometry, **not a detected short**, and not evidence that
loaded contact travel is qualified.

Do not emit the coarse shadow as an unconditional native keepout that
contradicts the mandatory C24 seed. Do not fix that by deleting the via,
waiving contact isolation or carving an unexplained exception hole.
The next bounded item must resolve a process-aware, height-relevant
contact reservation and explicitly carry the remaining fixed-connector
access assumptions. Preserve the existing process qualification; no new
ordinary-via-under-metal permission follows. Full loaded-state/mating
qualification remains distinct from a documented disposable-trial
planning assumption. Unsupported geometry must stay visibly gated.

Final evidence is under experimental
`quilter\outputs\d45-analytic-reservations-20261003T134856`.
Report SHA-256
`4178978d8e52db4d0b498e9e12aafdca5e43f098e43a7d084877ece1ed0da655`;
fragment
`d9b47afe0d0003cdab874b49ea1d9bfb845975ff648b059178bfa09dc6169b53`;
`generate_trial_envelope.py`
`bd46635a2955443c8e97d8b1684c2e87104536e9011da9bea6b4439d9494e0d2`;
workflow snapshot
`a1a950c96caed1401c39cb9acb9f2e4e520714ed705e8873e4ed31bfb3f30b0c`.
The script remains local; its original worktree binding must be supplied
appropriately when replaying elsewhere. Root checked the corrected
whole-body/actual-via-radius calculations and rehashed all four source
files. Source is unchanged; 37 opens is inherited from that unchanged
baseline, not a new native measurement. No PCB, CAD or cloud job changed.

## October 3 contact and access disposition

**The C24 conflict came from collapsing a three-dimensional contact into a
full-height rectangle, not from a demonstrated board-plane collision.**
The earlier rectangular-shadow proposal remains preserved as evidence; it
must not become an unconditional keepout with a special hole for C24.

Existing `tools/validate_supply_ground_stitch.py` represents contact metal
with the six base/tab rectangles. Its associated acceptance report concerns
the **September 22 R4 stitch**, not the current C13 stitch, and its contact
test uses 0.20 mm. It establishes prior representation only: neither that
historical source binding nor its weaker clearance proves this study's
0.25 mm requirement. The source contact builder separately constructs
elevated spring strips and annular ears. Rigidly translating the PCB and
contacts by +2 mm does not change their relative clearances.

For a **nominal trial via guard**, use the six physical base/tab rectangles
and conservatively include both complete spring-wall XY projections. Expand
each physical rectangle by 0.25 mm and encode it as a B.Cu via-only rule
area. Native collision must use the full via copper shape. A separate
point-centre screen adds the via radius: 0.552 mm total for new 0.604 mm
vias, but 0.550 mm for the retained 0.600 mm C24 via. Do not add the radius
twice. Keep the elevated-ear geometry and full-height proxy as assembly
review information rather than pretending every elevated feature touches
the board. This is not loaded-travel or manufacturing qualification.

**Via-only is intentional and incomplete.** An all-track prohibition
blanketing a contact's own landing pads can obstruct its intended power
connection. Conversely, leaving track/pour flags clear does not permit
foreign-net B copper under conductive contact bases. That requires a
separate net-aware exclusion or a reviewed retained contact-feed block,
plus independent returned-copper checks. Quilter's public
[keepout documentation](https://docs.quilter.ai/design-parameters/keepouts)
describes ordinary keepouts but does not establish this net-aware behavior.
Do not infer it from native KiCad success. No new ordinary via or masked
copper under actual battery metal is accepted by this representation.

The fixed-access planning assumptions are explicit:

| Interface | Carry into the disposable-study requirements | Do not infer |
|---|---|---|
| J1 | Exact fixed datum and existing 7.96 x 6.72 x 3.1 mm proxy; retain its larger planning height | A smaller nominal manufacturer body proves cable, latch or tool clearance |
| J2 | Exact fixed datum and offset 4.8 x 6.25 x 3.1 mm proxy, including its existing 0.7 mm front mating allowance | Another 0.7 mm should be added, or the proxy bounds the complete harness |
| X6 | Fixed datum, intentional body overhang beyond the tongue and existing B anchor/access reservation | The tongue bounds the plug/overmold or qualifies the rebuilt bezel |
| MH1/MH2 | Complete R3.2 planning reservations and real unscaled M2 hardware | Nominal radial containment proves screw engagement or a component-free driver path |
| Recovery pads and rear assembly | Preserve service access, insulated contact/cell separation and an adapted assembly/removal path | Unknown access can be encoded as zero clearance or omitted because plastic is adaptable |

These are retained source planning assumptions, not invented maximum
mating/loaded envelopes. Full-board staging/submission remains gated on
their explicit native/import treatment and the remaining electrical and
surface-copper constraints. Full assembly rebinding still precedes layout
acceptance; it is not required to rebuild the enclosure for a small
standalone rule-area control.

### Bounded result and exact limits

The [raw calculation/control report](measurements/2026-09-27-router-bakeoff/quilter-contact-via-mask-2026-10-03.json)
is retained with its `PROPOSAL_EVIDENCE_ONLY_NOT_ACCEPTED` status. Root
accepts the nominal mask arithmetic and limited in-memory collision
evidence, **not a production-ready native fragment or full contact/access
qualification**.

All five protected vias clear all eight proposed guards. Root separately
checked the full copper circles against the **square-expanded** rectangles,
not just Euclidean clearance to the original metal: all 40 checks pass,
with C24 still limiting at **0.393331 mm spare**. The spring-wall projections
are x[17,18.985], y[-4.445,4.445] for BT1 and their X mirror for BT2.
No seed is removed, moved or exempted from a mask.

The contact gaps relative to the **moving PCB B face** are identical in
both packaging cases:

| Nominal feature minimum | Baseline B = 26.6 mm | Translated B = 28.6 mm |
|---|---:|---:|
| Base | 0 mm | 0 mm |
| Spring | 0.3 mm | 0.3 mm |
| Ear, conservative complete-circle bound | 1.28 mm | 1.28 mm |
| Ear, actual nominal angular sectors | 1.409134 mm | 1.409134 mm |

**Report interpretation correction:** the raw `*_gap_from_source_pcb_B_mm`
fields deliberately subtract the old 26.6 mm datum. Their +2 case values
are not clearances to the translated board. The executor's summary table
presented them as gaps under the new datum; that interpretation is rejected.
Use `feature_z - contact_B_plane_mm`, as checked above. No extra rear-contact
clearance is created by translating the assembly. Nominal sector geometry
still does not bound actual spring travel, tolerances or deformation.

KiCad 10.0.6 was exercised on a new four-layer **in-memory microfixture**.
Eight B.Cu rule areas had via prohibition enabled and track/pad/pour
prohibition disabled. Three synthetic 0.604 mm via shapes collided as
expected: inside a base and 0.01 mm inside the clearance threshold were
rejected; 0.01 mm outside was clear. This was a direct native polygon/shape
collision check, **not native DRC or a serialized save/reload test**.
The five real seeds were checked analytically, not instantiated in that
native control. Footprint prohibition was not explicitly read back.

The raw fragment also uses **common XY centred at (0,0)**, not the source
PCB's (100,100) origin. It has no native area names and was not reloaded;
do not paste it into the real-board coordinate frame. A production encoding
must apply the +100/+100 translation exactly once, name the areas, explicitly
set/check every restriction and prove save/reload behavior. These limits
do not invalidate the numerical mask, but prevent treating the fragment
as a qualified drop-in artifact.

The initial run and two corrections are exhausted; no further execution
was requested. **Next proposed bounded item:** a disposable BT1/BT2
surface-rule fixture that preserves legitimate contact-pad feeds while
rejecting foreign B tracks/pours and forbidden vias, with explicit
coordinate conversion and native round-trip controls. Do not stage the
104-reference layout or submit a cloud job merely because the via-only
screen passed. Connector/service assumptions above remain visible gates.

Raw evidence is under experimental
`quilter\outputs\contact-via-mask-20261003T1418`:
report SHA-256
`489503349d1f05968ea165237a99bbd01e4381983b1f40273a9ab98fdef17fda`;
script
`25be5690cc159bddee81064bc2cc4d8c02665ec9b4e2b832dbb7d6d4c69a324f`;
common-frame fragment
`d8963c662b85723ef70c9b7cf7d5758325e15b0b56bce1b2c94ac08bcdbcca60`.
The script reuses the earlier `a1a950c9...` workflow snapshot, not the live
post-outline contract; exact manifest/contact/trial-report hashes are
recorded separately. Root rehashed the current PCB, schematic, project and
manifest against the reported source hashes. All are unchanged. No source
board load, actual-board staging, routing, refill, CAD rebuild or cloud
operation occurred.

### 14:29 surface-fixture attempt: native tooling blocked

No fixture was saved. The initial attempt and two corrections failed on
KiCad Python API calls: unavailable `BOARD_DESIGN_SETTINGS.SetTrackWidth`,
the required argument to `FOOTPRINT.Duplicate`, then its generic
`BOARD_ITEM` return without `Pads`. No DRC, refill, reload, pad-edge result
or contact-rule behavior was established. These are tooling failures, not
evidence that a legitimate contact escape is impossible.

The executor loaded the source read-only three times, exceeding the
requested one load; this is recorded as a scope deviation, not hidden as a
successful retry. Root rechecked all four authoritative source hashes;
none changed. Preserve external evidence under
`quilter\outputs\bt-contact-native-surface-rule-20261003T1431`:
`build_fixture.py`
`97e7f3f9ffaf050dc1b2726a972d813c15d04abf4a95434bfc9222351ff3b0f7`,
and failed `fixture-report.json`
`0b57c6820df94b6c72811100cc650d5075c131a9ebe140de89886809ea215624`.

Native continuation is held at the exhausted retry limit. The proposed
repair is to construct the small fixture from exact source S-expression
subtrees using the existing parser, avoiding guessed cloning APIs, then
run a bounded save/reload/control pass. This needs a new explicit bounded
tooling-repair authorization; the one-hour allowance does not silently
reset failed-attempt limits.

A useful, still untested alternative is to determine whether the existing
contact pads already cover the base metal sufficiently for ordinary
foreign-net pad clearance to protect it. That could allow legitimate
same-net feeds without a blanket track prohibition. Do not assume such
coverage, create surrogate copper, shrink metal or lower the 0.25 mm duty.

Primary documentation was also checked directly:
[uploads](https://docs.quilter.ai/using-quilter/upload-your-design-files.md)
describe PCB, schematic and optional project files, but do not establish
`.kicad_dru` support. The
[pre-routed trace rule](https://docs.quilter.ai/design-parameters/pre-routed-traces.md)
does not require a lock flag: in-outline traces/vias are considered
pre-placed, while internal copper may be deleted when the input stackup is
not preserved. Neither statement proves actual returned preservation.
The [switching-converter model](https://docs.quilter.ai/physics-constraints/switching-converters.md)
describes an output-inductor configuration and proximity/path checks; do
not assume it expresses this boost circuit's complete loop/private-pickoff
requirements or all parallel capacitors.

## October 3 authenticated browser checkpoint

The owner signed into the Playwright-controlled browser and approved
continuation at 10:57 local. Project navigation, candidate summaries,
read-only Job Details, accordion tables and the account menu were exercised
through the ordinary UI. No undocumented endpoint was called. No upload,
duplicate, new project/job, constraint edit, rating, support message,
purchase or submission occurred. Authentication remains browser-local;
do not export cookies/tokens or commit raw snapshots. `.playwright-mcp/`
is ignored because snapshots can contain account or login metadata.

**Access limits:** this establishes observation/navigation, not reliable
automation of editable grids, component associations, file upload or the
board canvas. The account menu exposed only Sign Out, not a free-tier or
billing entitlement. Confirm actual free submission terms at the qualified
new-job review; existing-project access is not proof of free future jobs.
No public documented API/SDK/CLI was found in the public documentation
search. The UI footer's API version is not an offer of public API access.

The saved job now reports:

| Observation | Interpretation |
|---|---|
| 104 components, zero to place, 326 vendor pins, 96 to route | Still the fixed-placement experiment, not an exercise of the placer; vendor pins are not 325 physical pads |
| Elapsed 3 h 47 m 44 s | Displayed completed-job turnaround, not active engineering effort or internal compute cost |
| 16 references reported missing from schematic | Reconfirms the earlier importer warning; existing source audit establishes 14 present with matching UUID suffixes, only MH1/MH2 board-only |
| No placement-region, crystal, switching-converter, custom-proximity or ECAD-parsed-constraint records | Those capabilities were not configured in this job; empty ECAD records do not by themselves prove keepouts were dropped |
| Two preserved-pour records | Records alone do not override the separately documented stackup/pour regeneration behavior |
| Custom Component Proximity section exists, with no records | Potential grouping mechanism worth inspecting on a qualified disposable draft; semantics and editing are not established |

The 16 warning references are
`BT1 BT2 C30 J1 J2 MH1 MH2 Q5 R25 R26 R27 R28 R29 U1 U6 Y1`.
For the fresh input, verify their imported pin/parent associations and
comprehensions explicitly before relying on automatic grouping, especially
the protector, flash and crystal. Do not reconstruct valid source symbols
or start another support loop just to clear a warning. Explicit associations
may be an acceptable remedy only if the imported connectivity and behavior
can be demonstrated.

Expanded **saved fabrication values** display:
width 0.178 mm, clearance 0.20 mm, via diameter/drill 0.604/0.35 mm,
board margin **0.508 mm**. The width is displayed rounded; exact storage
precision was not queried. The board margin differs from the requested
0.25 mm, while the collapsed label still says "6 mil / 6 mil".
Future runs must record expanded values, not infer them from a preset name.
This does not prove how every rule was enforced during compilation.

Expanded **saved stackup** is labeled JLCPCB 4-Layer and displays
F/In1/In2/B copper at 0.035/0.015/0.015/0.035 mm, dielectric separations
0.21/1.065/0.21 mm, and copper classes Signal/Ground/Signal/Signal.
"Ground Layer 2" is a display name despite its Signal class.
The table labels the middle FR4-Generic dielectric as prepreg; record that
as displayed, not a verified supplier material construction. This is not
the newly shortlisted JLC04161H-3313 stackup, and neither is selected for
the next trial.

**Morning next item (revised by the afternoon scope above):** construct the source-bound allowed-domain map using
the recovered inventory and existing mechanical inputs. Carry the known
parser/comprehension issues as explicit import checks. Do not re-inventory,
alter the historical job, or submit before those gates pass.

## October 3 allowed-domain engineering disposition

The saved map is a **partial mechanical screen**, not a ready-to-import set
of placement regions. Reusing the accepted JSON can establish the speaker
height restriction and modeled board-adjacent contact metal without another
native board load. It cannot establish the complete component/service space
from the old placement's individual clearance measurements.

Evidence: [numerical report](measurements/2026-09-27-router-bakeoff/quilter-mechanical-screen-2026-10-03.json)
and [illustrative two-panel SVG](measurements/2026-09-27-router-bakeoff/quilter-mechanical-screen-2026-10-03.svg).
Both panels use the same non-mirrored common XY coordinates. The SVG retains
crowded USB caption placement and is not a geometry import; use the reviewed
JSON for exact values. No moving component bodies or complete allowed
domains are plotted.

The **81 fitted F components** comprise 64 below 1.5 mm, five equal to
1.5 mm (`Q1/Q2/Q4/U2/U3`) and 12 above it. The latter are
`C1/C4/C5/C19/C20/C26/C27/C28/L1/J1/J2/X6`; J1/J2/X6 remain fixed.
The report's all-fitted total of 14 above 1.5 mm additionally includes the
two B contacts; do not apply the front speaker-height test to those contacts.
All 104 references, nine fixed poses and five process-via points are
accounted for, including separate non-fitted classifications for C29,
18 copper features and two mounts.

Root independently checked the report against the current manifest/contact
data and accepted inventory, and rehashed the PCB/manifest/schematic/project:
all four authoritative source hashes remain unchanged. The renderer's
before/after hash fields repeat inherited inventory evidence, not fresh
measurements; the independent root check establishes current preservation.
No native CAD tool was loaded and no source geometry was changed.

The reproducible renderer and raw artifacts remain in experimental
`quilter\outputs\mechanical-map-screen-20261003T111238-sol`.
Final SHA-256 values are JSON
`2d26b2a73d72d5864976cd9945b073c25e1b77dab624d22eefe57590c0a0975c`,
SVG `6048599f321a2b3a33a7ad9a7c20a845a5ccf2300b9e219ac2b01920d9184d1b`,
and `render_map.py`
`3440071db151cb4c9995d1bd4397f8aa8c134d32ccb66fe73af92c9ff95596ed`.
These are source-derived project screening exports, not Quilter output or
browser account data; retain the hardware's
[attribution/license context](../ATTRIBUTION.md).

| Obligation | Source-backed encoding approach | Remaining gate |
|---|---|---|
| F component height versus speaker | Use F z25 and magnet rear z23.5: 1.5 mm nominal axial gap over the D21.70 magnet. Evaluate the entire rotated component body, not its origin. | Below 1.5 mm is only a nominal speaker clearance; equal height has zero gap. Tolerance, supports and other obstacles still apply. |
| Through-via access versus rear metal | Start with both contact base/tab primitives and native pad copper. For a new 0.604 mm via, a center exclusion needs 0.302 mm copper radius plus the 0.25 mm contact clearance. | Complete loaded-contact/spring/ear and service restrictions remain separate; a drawing of base metal alone is not the whole allowed-via map. |
| Mounts, yoke and carrier | Project actual occupied solid slices over each component's z interval, preserving support and tool-access volumes. | Drill circles and entire-object bounding boxes are not adequate substitutions. |
| X6 and J1/J2 | Preserve exact native poses, current body offsets and documented USB rear planning reservation. | Plug, latch, wire and service paths require their own envelope; a connector body alone is insufficient. |
| Copper-only features and C29 DNP | Preserve source footprint/pad geometry and recovery access; classify separately from fitted bodies. | Do not invent a zero fitted height or omit their copper/assembly-space obligations. |
| Clock, boost and private returns | Re-express the 19 pour-only exclusions against retained or relocated actual circuit geometry. Explicitly check capacitor parent pins and private-terminal topology. | Regions/proximity alone cannot establish return-current, quiet-pickoff or layer-reference behavior. Unsupported duties need a reviewed retained block or demonstrated independent check. |
| Quilter region geometry | Intersect the full requirements locally before assigning regions, because assigned regions combine by union. | Establish actual whole-footprint versus origin semantics and supported rotation behavior before choosing offsets/erosions; do not double-apply or omit body clearance. |

An important source distinction emerged: the placement manifest's
`speaker_screen.yoke_top_z_mm = 19.3` is a local planning station, **not the
whole yoke's maximum height**. The existing assembly's `fit-report.json`
records `RetainedSpeakerCaptureYoke` reaching z25, and the carrier reaching
z27. Thus the nominal L1-bottom z20 minus local station z19.3 = 0.7 mm
cannot qualify an arbitrary new L1 position. The individual BRep contains
supports/features not represented by a uniform horizontal yoke ceiling.

Reuse the immutable saved geometry under
`mechanical\studies\2026-09-13-printed-bell\imu-four-layer-review\extended-run`
for the next projection item rather than regenerating the whole assembly:
`printed-bell.FCStd` SHA-256
`b2dff3477a5543f4f011277ab4e4d63765fbb84121a9c537709c63e3f43a610d`,
and `fit-report.json` SHA-256
`4ffdfcc7177dbd406b8af0ef0f602343a9fd49d8a4a4b1ada9cd6b76b46055de`.
This CAD is bound to the immutable IMU PCB `d2a098b0...`, not the current
`adc262b3...` bytes. A new projection must establish unchanged fixed
mechanical interfaces and current component envelopes explicitly; do not
silently treat the old fit pass as acceptance of moved components.

**Morning remaining mapping item (superseded where plastic is redesignable):** read the saved BRep without rebuilding it,
extract height-indexed support/hardware and required service reservations,
and combine them with the current native footprint/body/rotation mapping.
Stop with a source-bound allowed-domain result or exact unsupported
envelopes. No off-board staging, copper removal, upload or cloud submission
is released by the partial screen.

## Two parallel, bounded items

1. **Read-only diagnostic:** compare the actual saved copper in v1.1/v1.2
   against the accepted source. Measure useful joins, lost prior groups,
   remaining opens and native findings without repair, refill or promotion.
   This explicitly releases measurement beyond the earlier preservation
   stop; it does not reverse rejection for integration.
2. **Fresh-layout brief:** reorganize the same circuit into functional
   groups, with fixed mechanical interfaces and controlled placement freedom.
   The [source-bound contract](design-inputs/2026-10-02-quilter-workflow.json)
   assigns all 104 references, including copper-only features and C29 DNP.
   Native staging and imported-constraint qualification are separate items.

Native execution remains pinned Sol/medium with a runtime gate. Astra owns
engineering requirements and acceptance. Target 10-15 minutes per coherent
item, finite subprocess timeouts and no more than two tooling corrections.
Preserve partial evidence and stop on a concrete blocker.

## Existing-output diagnostic checkpoint

The read-only saved-fill diagnostic reproduced the source's 37 graph opens.
Neither raw output was changed or refilled. KiCad 10.0.6 DRC used each
returned project and a separately copied source schematic/library context;
the schematic was not supplied by Quilter.

| Artifact | Same-net graph opens | Native unconnected items | Other native errors / warnings | Parity warnings |
|---|---:|---:|---:|---:|
| Accepted source | 37 | 37, reused source-bound baseline | 234 non-open findings, reused baseline | 46, reused baseline |
| v1.1 | 38 | 38 | 257 / 201 | 46 |
| v1.2 | 22 | 24 | 640 / 211 | 46 |

v1.1 closes VBAT but splits the previously complete USBBOOT and SDA groups.
v1.2 has 15 fewer same-net graph opens with no prior pad-group split found:
I2S_BCLK, I2S_LRCLK, USB_D+, USB_D-, VBAT, VBUS, VHI, VO+ and
`Net-(FB2-P$1)` become complete in that graph. AMP_MUTE, POWER and GND
each improve by one open. The previously unmatched In2 records therefore
did not all translate into lost electrical joins: +3V3 and /IMU_INT2 are
complete in both outputs, and USBBOOT/SDA are complete in v1.2.

These are **same-net routing gains, not 15 accepted electrical repairs**.
The graph reports foreign-net contacts in both outputs; v1.2 also has 21
native `shorting_items` findings, including a RESET via contacting the
MCU GND exposed pad. The graph does not join different-net objects through
these contacts, so the reported gains do not rely on shorts. The graph's
22 versus native 24 unconnected count
for v1.2 remains unreconciled; do not invent a cause or hide the discrepancy.

Do not equate hundreds of witnesses with hundreds of independent fixes.
Each candidate has 65 drill-minimum and 65 via-diameter findings against
returned 0.35/0.604 mm project minima; the example preserved CC2 via is
0.30/0.60 mm. These expose an inherited-via/rule mismatch, not 130 new
routing operations. All 11 v1.1 graph contact witnesses involve cached
zones (two zone UUIDs). Of 187 v1.2 witnesses, 157 involve cached zones
(eight zone UUIDs), while 30 do not. Native v1.2 short findings comprise
seven pad/via, four pad/track, five track/track and five track/via witnesses,
plus a separate crossing. These categories overlap the graph evidence,
not additional independent defect totals. Refill sensitivity was not tested;
the non-zone contacts cannot be attributed solely to the zone-fill cache.
No correction effort has been measured.

**Learning disposition:** v1.2 demonstrates real additional same-net routing,
but neither candidate demonstrates an integration-ready or economical
completion workflow. Continue the fresh-input/constraint track rather than
hand-cleaning these outputs or repeating their setup unchanged.
The original preservation rejection remains in effect.

Local evidence under the experimental root:
`quilter\outputs\useful-connectivity-diagnostic-20261002T1408`.
`report.json` SHA-256:
`0e15cc01e608197aee1b0f4547f2cfdf20f090b9583ba2ff471d676863dad493`.
It binds the diagnostic script, graph helpers, original/copy PCB hashes,
per-net partitions and native execution context. Native DRC reports are
`v1.1-drc.json` and `v1.2-drc.json`. Script elapsed time was 150.03 seconds,
not total engineering time or platform compute time. Authoritative source
and both original output PCB hashes remained unchanged.
The saved-evidence supplement `short-evidence-clarification.json` has SHA-256
`0b1110a3821815da4432387e2b804d4924d55001e19b84b1685aefe5ad8259fd`;
it groups witnesses and records the graph-union and rule-context limits
without another native run.

## Initial placement strategy

Keep BT1/BT2, MH1/MH2, X6, J1 and J2 at their exact accepted native poses.
Retain the outline, mounts, contact metal, connector/USB access, component
height limits and front-electronics/rear-contact split. The nominal D43
circle is not a replacement for the outline with tabs and USB tongue.

Keep U4 and C24 at their current poses for the first input, with their five
mandatory filled/planarized/capped vias. This is a deliberate limited seed,
not a claim that the whole old floorplan must survive. Independent vias
cannot be assumed to follow a movable component in Quilter. A relocatable
process block or an ordinary-via alternative would need separate evidence.
Thus this is a largely fresh layout with two process seeds, not an empty
board falsely stripped of manufacturing obligations.

The other references may move/rotate on F subject to the contract. Keep
electrically related groups together without inventing narrow placement
rectangles: MCU supply/return, crystal, flash/boot, USB, IMU, regulator,
charger, source selection, audio switch, boost, protection, amplifier/filter,
button, indication and debug. Associate capacitance with the actual supply
pin, not merely a shared +3V3 net. Group membership is not by itself a
decoupling-distance, return-path or switching-loop constraint.

Two important input traps:

- Quilter can flip unplaced components unless tied to a layer-specific
  placement region. The single-sided candidate filter is not enforcement.
- Off-board grouping regions do not constrain the side. We must verify
  actual KiCad region associations and F-only behavior in the imported
  model before submitting, not rely on how a staging picture looks.

Mechanical envelopes remain screening inputs, not qualified tolerances.
The manifest contains historical landmark/proxy fields as well as native
origins; fixed poses must come from the exact accepted PCB, not stale
descriptive coordinates. Newly moved parts require exact mechanical rebinding.
IC4 rotation also changes the sensor-to-bell coordinate mapping.

### Documentation findings that change input preparation

The [placement guide](https://docs.quilter.ai/guides/placement-guide) says
multiple regions assigned to one component form a **union**, not an
intersection. Assigning a broad F region plus a smaller height/group region
would therefore enlarge the allowed space, not enforce both constraints.
First intersect that component's F-side, height, access and electrical
requirements into its final allowed domain; encode multiple polygons only
to represent allowed patches of that domain. Do not add an off-board
grouping region and assume it preserves the on-board F restriction.
These semantics are documented, not yet verified on our imported input.

The [KiCad region instructions](https://docs.quilter.ai/design-parameters/placement-regions)
explicitly require reviewing/manual assignment of component references.
Their generic upload step also mentions automatic association; use the
stricter review requirement rather than assuming either association behavior.
Keep real safety keepouts separate from restriction-free placement regions.

[Bypass comprehension](https://docs.quilter.ai/physics-constraints/bypass-capacitors)
supports explicit capacitor/component/pin/value assignments; this is a
useful service capability we have not yet exercised correctly. Schematic
wire proximity is a heuristic, not a substitute for the reviewed pin map.
[Switching-converter comprehension](https://docs.quilter.ai/physics-constraints/switching-converters)
documents an output-inductor configuration and may choose one of multiple
capacitors arbitrarily. That does not establish support for our TPS61023
boost's exact input-inductor/output-capacitor/quiet-pickoff topology.
Do not relabel its parts to force a match. It needs a reviewed local-block
or independent topology-check disposition before unrestricted placement.

## Preserve engineering intent, not obsolete obstacles

Fresh-layout preparation may replace ordinary old routing on an isolated
copy after a complete keepout/seed inventory. It must not delete footprint
copper, corrected USB slots/lands, custom Q3 geometry or the five process
vias. No old source file is a scratch input.

Fixed rear-contact/USB/mount restrictions remain fixed. Crystal,
switch-node and private-return exclusions tied to moved components must
be re-expressed against those components, not copied at stale coordinates.
Through-vias still expose conductive B lands under battery metal even when
filled or tented. More copper layers do not solve that access restriction.

Raw CELL_NEG is not protected GND. PROT_FET_RETURN is not a general ground
plane. Preserve R26/R27 and R24/C28 private pickoffs and short local boost
output-capacitor supply/return loops. If an essential duty cannot be encoded
in Quilter, explicitly retain a reviewed local block or use a qualified
independent topology gate; do not silently let it become a generic signal.

No generic 500mA rail table, 100ohm speaker-output pair, incorrect capacitor
values or empty clock/switching comprehension is approved for reuse.
Current budgets and powered behavior remain provisional engineering gates.

## Layer comparison and cost

Prepare comparable real four- and six-layer constructions once the common
input is qualified. Eight layers is optional if it adds little setup/review
and remains free. Use actual supplier construction data and explicit return
references; do not merely increase the enabled-layer count. Let placement
adapt while holding outline, BOM, electrical and manufacturing requirements
constant. This compares complete workflows, not layer count in isolation.

Measure native outcomes, defect roots, owner/agent interventions, setup and
review effort, actual service cost, manufacturing implications and elapsed
turnaround. Do not invent token costs or internal compute measurements from
wall time. A visually unusual layout can be useful; electrical/process
failures cannot be hidden by a completion percentage.

Public pricing checked October 2:

- [Free tier](https://www.quilter.ai/free-ai-pcb-design): personal/academic
  eligibility, free access, unlimited iterations and product features.
- [Paid pricing](https://www.quilter.ai/pricing): per project, based on
  unrouted input pins, with iterations and parallel jobs included and
  advertised 10% BOM flexibility. No public dollar-per-pin quote found.
- The prior job's 96 pins-to-route is neither 37 native opens nor 325
  physical pads. A fresh input can change that count and any paid quote.
- Confirm this account's actual free terms before submission. Stop at
  payment/upgrade or a changed agreement needing owner action.
- Personal use does not itself settle output-redistribution rights.
  [Terms](https://www.quilter.ai/terms) and third-party hardware attribution
  remain a gate before publishing Quilter native designs or a kit.

**Manufacturing trade worth testing:** JLCPCB's
[published POFV policy](https://jlcpcb.com/news/free-via-in-pad-6-20-layer-pcbs-pofv)
states that, for its international market, resin-filled/copper-capped
via-in-pad is included on 6-20-layer boards while four-layer POFV is charged.
The [via-covering guide](https://jlcpcb.com/help/article/pcb-via-covering)
separately defines nonconductive epoxy fill plus copper cap, distinct from
ink plugging or tenting. Our five mandatory process vias make this a real
cost variable: six layers must not be dismissed as automatically more
expensive overall. This is published vendor policy, not a quote, eligibility
confirmation or qualification of our exact geometry. The POFV article also
specifies via-hole and hole-spacing conditions; do not replace the project's
clearances or assume its sample dimensions apply to our five vias.

The [official impedance listing](https://jlcpcb.com/impedance) identifies
`JLC04161H-3313` and `JLC06161H-3313` as possible four-/six-layer comparison
constructions. These are only a shortlist: full material/copper/dielectric
dimensions, layer roles, actual Quilter preset identity and process
eligibility still need an exact binding. No stackup was selected or ordered.

## Recovered native inventory and preparation gate

The final pass reused the repository's exercised `tools/kicad_sexpr.py`
parser, matched native pads by UUID and parent reference rather than
ordinal position, and used the explicit-layer via accessor. It completed
in two native executions; the final inventory script took 0.687 seconds,
not counting setup/review. The earlier failures were extraction/tooling
errors, not evidence of missing source pads or expensive PCB computation.

| Inventory | Accepted raw evidence |
|---|---|
| Identity | 104 footprints, 325 physical pads; all group references assigned once; native and serialized UUID/parent associations |
| Placement | Nine fixed native poses, 95 eligible movers; all 83 fitted manifest sides agree with native data: 81 F, BT1/BT2 B |
| Process seeds | Four U4 GND vias at **0.604/0.35 mm**, touching U4.THERMAL; C24 GND via at **0.60/0.30 mm**, touching C24.2 |
| Zones | 19 component-relative electrical rule areas and two GND zones; exact definitions, layer IDs, outlines, holes and saved fills |
| Source | All four authoritative package hashes unchanged |

BT1's two physical pads both use number `1` but have distinct UUIDs; they
must not be collapsed. The via contacts above use native effective-copper
intersection, not bounding-box overlap. The executor's summary rounded U4
diameter to 0.60 mm; the native JSON's **0.604 mm** is authoritative.
C24 retains an explicit accepted-process geometry exception to the new
ordinary-via minima; this is not permission for new 0.30 mm drill vias.

All 19 rule areas prohibit **copper pours only**: seven F guards for
R24/C28, three F guards for R26/R27, two In1 private-return exclusions,
six In1 BOOST_SW exclusions and one In1 crystal-region exclusion.
They do not prohibit footprints, vias, pads or tracks. Their electrical
purposes are accounted for, but this is not proof that their old coordinates
remain suitable after placement/routing changes.

**Disposition:** accept the report as a complete raw inventory, not as a
placement-ready input. No native fixed-mechanical rule areas encode the
full battery-contact bodies, mount hardware, USB/service or connector-access
envelopes. Keeping the existing 19 rule areas would therefore not enforce
the mechanical constraints. Before a disposable input can move parts or
discard old copper, map those external envelopes and height limits into
per-reference allowed domains and define how moved electrical exclusions
and private paths will be reconstructed or retained. The proposed 95 movable
references remain eligibility, not a successful-placement claim.

Local evidence under the experimental root:
`quilter\outputs\inventory-final-recovery-20261002T142910-sol`.
The complete report `native-constraint-inventory.json` has SHA-256
`edba323c00da212fd881be71cc98f5d1afd8d8ca15ac4545c4b79bf609a7b7ba`;
the script has SHA-256
`a0760d1633caa10421ffe07034df1ec3d32c88b1cf40ff2fd2c8aab597a2d47e`.
`source-hashes-after.json` has SHA-256
`60762a93e3be33842958407336ae3d805966b63ae7236b6a254178ec9a03a9bc`.
The raw 3.9 MB report remains local rather than duplicating the PCB in Git.
All failed attempts remain alongside it as evidence.

**One next item:** produce the source-bound mechanical/electrical
allowed-domain map using this inventory and the existing assembly inputs.
No further inventory rerun, copper deletion, off-board staging, CAD build
or cloud trial is released at this checkpoint. Stackup/process and imported
comprehension qualification remain later gates.

## Historical native inventory blocker

The inventory did **not** complete. KiCad 10.0.6 Python compatibility failures
exhausted the initial attempt plus two corrections: library-ID formatting,
UTF8 field conversion, then a native assertion from `PCB_VIA.GetWidth()`
without a layer argument. The last attempt reached its 120-second hard
timeout and was stopped. No inventory JSON or prepared input was produced.
This is our tooling failure, not a measured Quilter limitation.

Local evidence under the experimental root:
`quilter\outputs\inventory-20261002T141349-sol`.
The blocker report `inventory-run-blocker.json` has SHA-256
`9e666f06f3e3824fa6900adceae5fe8fd0233e4adb74bbb638f97d3e3fa6deaa`;
the failed script `native_constraint_inventory.py` has SHA-256
`e683e036830811daefd3e6f716f663389d04ea919ee9814ee23df1f7d9192ef5`.
Root independently rechecked all four authoritative package hashes after
the failure; they still match the contract. No placement, copper, original
output, or CAD changed, and no cloud job was submitted.

**Root disposition:** do not simply change the via accessor and rerun.
Review of the failed script also found acceptance-relevant gaps:

- Keepout purpose is classified from names, without the required supporting
  source/report evidence. Unknown or ambiguous duties must remain unresolved.
- Polygon extraction omits holes; fill-read exceptions silently become null.
  A deletion/relocation inventory needs complete geometry and explicit failures.
- The check labeled "81 electronics" counts all 102 non-contact references,
  rather than the fitted manifest subset. Via/pad binding tests only equal
  centers and nets, not actual copper contact for offset process vias.

No values from the uncompleted script qualify the native inventory.
The earlier source/manifest-backed group brief remains a proposal, not
proof that placement regions or process seeds have now been inventoried.
The retry budget is exhausted, so fresh-input preparation and layer trials
are **blocked**, with no automatic repair or additional native run released.

## Completed bounded recovery scope

Repair only the isolated inventory tool, reusing exercised KiCad accessors
and source-bound report/manifest definitions rather than another untested API
sequence. Address the gaps above before one bounded read-only rerun. Stop
with either a complete evidence-bearing inventory or a concrete failure;
do not move parts, delete copper, choose a stackup or submit a job.
The owner's 14:22 update supplies this bounded authorization.

The first recovery pass used three native executions and stopped with a
serialized/native pad-association failure at BT1; it produced no complete
inventory. Root then identified the already exercised `tools/kicad_sexpr.py`
tree parser and explicit-layer via accessor in the successful preservation
audit. A **second and final** corrected-method pass is released under the
same owner authorization: at most two native executions in ten minutes,
stop by 14:40. No regex/nested-UUID or ordinal association shortcut is
allowed. Persist each completed stage, distinguish raw data from unproved
engineering gates, and stop after this pass regardless of outcome.

The inventory's unchanged engineering objective is:

Start from the exact source hashes in the JSON, not the held MCU fanout
fixture or either Quilter output. In one new private staging directory,
inventory fixed poses, functional-group pin associations, five process vias,
fixed/mechanism-relative keepouts and height restrictions. Prove all 104
references are assigned exactly once and preserve 325 physical pad identities.
Stop with the explicit constraint map and any unsupported import requirement
before moving parts or deleting ordinary copper. That separates engineering
intent from irreversible-looking preparation and avoids another blindly
configured cloud run.

References: Quilter [placement guide](https://docs.quilter.ai/guides/placement-guide),
[KiCad regions](https://docs.quilter.ai/design-parameters/placement-regions),
[single-sided requirement](https://docs.quilter.ai/design-parameters/single-sided-placement),
[keepouts](https://docs.quilter.ai/design-parameters/keepouts),
[stackups](https://docs.quilter.ai/design-parameters/stackups).
