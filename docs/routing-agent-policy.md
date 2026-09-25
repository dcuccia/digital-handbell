# Astra engineering lead / Sol routing executor

Owner-authorized September 21, 2026. The owner subsequently approved migration
to four copper layers, retaining Astra engineering authority and pinned Sol
execution. The four-layer policy below supersedes the earlier two-layer-only
work scopes, not the preserved evidence, failed-attempt history or supplier gates.

## Model and invocation gate

Repository profile: `.github/agents/kicad-router.agent.md`, model
`gpt-5.6-sol`, `modelPolicy: required`, medium requested effort, automatic
invocation enabled. Root remains GPT-6 Astra. Native KiCad 10.0.6 API/CLI
access is through the shell; no KiCad MCP connection is assumed.

Copilot CLI 1.0.87 was exercised:

- An explicit `task` subagent override dispatched `gpt-5.6-sol` with
  `reasoningEffort: medium` while this root remained `gpt-6-astra`.
- A newly discovered `kicad-router` subagent resolved from its profile to
  `gpt-5.6-sol`; completed-event `firstDispatchedModel` also confirms Sol.
- A custom subagent requiring an unavailable synthetic model failed before
  execution instead of inheriting its parent's model.
- **Do not use direct `copilot --agent` selection as the fail-closed gate.**
  The same unavailable profile, selected directly, warned and fell back.
  Required-model enforcement was demonstrated on subagent dispatch only.
- The named-profile probe inherited the parent's **low** effort despite the
  profile requesting medium. Therefore also pass `reasoning_effort: medium`
  explicitly to every routing task and verify `subagent.configured`.

Compact [runtime evidence](measurements/2026-09-21-routing-agent-runtime.json)
records the actual outcomes. Explicit model/effort dispatch avoids the
named-profile effort-inheritance caveat above.

The already-running root's task schema does not list newly created custom
agents. Until its agent discovery refreshes, use the available `task` executor
with explicit `model: gpt-5.6-sol`, explicit medium effort, and instructions
to load the exact repository profile and this policy. This is a pinned Sol
execution path, not an Astra fallback. Once discovered, use `kicad-router`
directly, still explicitly supplying Sol and medium effort.

Before granting writes, run a read-only dispatch and inspect runtime
`subagent.started`, `subagent.configured` and `subagent.completed` metadata.
Reject an unexpected model or effort; self-reported identity is not proof.
Never omit the model override on the compatibility path, use Auto/inherit,
or retry an unavailable Sol task as Astra. If this path cannot be enforced,
stop and use the manual same-session fallback: `/model` to select Sol for
the approved executor brief, then `/model` back to Astra for engineering
review; keep the same conversation and source-bound handoff.

## Four-layer migration and efficient execution

The owner prioritizes an affordable, repeatable open design portable across
fabs. Necessary filled/capped vias or other processes are permitted; prefer
a simpler process when it meets the same electrical, thermal and assembly
requirements. This is not permission to replace qualified requirements with
cheaper unreviewed geometry or to order fabrication.

Preserve `printed-bell-clock-draft` at the exact hash below as the two-layer
reference. The accepted logical migration baseline and new working package is
`hardware/handbell/iterations/printed-bell-four-layer`, PCB SHA-256
`d91837ed9f5cff10d709521e448f6deae3aac3a52abed88c34271ee809e25418`.
Its `reports/four-layer-baseline.json` binds the unchanged native geometry,
51 opens and source bytes outside the layer declaration. No inner copper
was added. Its native report also records 46 schematic-parity notices from
a newly enabled check, not a historical same-mode comparison; disposition
remains required before release.
One active candidate, one writer; no independent edits
to several competing boards. Logical layer enablement alone is not routing
progress, plane completion or stackup qualification.

### Layer and interface contract

**Placement release gate: establish complete supply/return groups and
layer-transition access before freezing the local floorplan.** Place the
IC pins, their capacitors, short F connections, ground returns and ordinary
via access together. A component-body fit or a clear inner-layer corridor
does not qualify placement when the required through-vias cannot reach it.
For this board, screen actual rear-contact metal and fixed B power copper
before selecting transition sites or arranging capacitors around them.

Reserve switching loops, USB/clock/QSPI corridors and local decoupling
before routine controls. Separate noisy current paths by functional
placement and routing, not arbitrary digital/audio ground-plane splits.
Preserve raw CELL_NEG/protected-GND separation and private pickoffs as
specific circuit requirements. Review each route's return path, not just
its destination or airwire count.

For a coordinated re-layout proposal, identify exact old/new component
poses and replacement primitives, prove usable transition sites, and
account for every supply and return connection being disturbed. A rejected
trial with vias on known fixed copper is not evidence that a broader
mechanical or power-corridor release is necessary. Review overlays must
show relevant existing copper/contact obstacles, not just proposed boxes.
Refillable zone caches may be carved by an authorized route, but preserved
connected groups, private returns and reference continuity must then be
revalidated; fixed pads/tracks and zone definitions are not interchangeable
with fill caches.

| Copper layer | Initial role and limits |
|---|---|
| F.Cu | Components, short critical signals, local decoupling and switching loops. Preserve reviewed good routing unless Astra releases a specific change. |
| In1.Cu | Reserve for substantially continuous **protected GND**. No routine signal routing. Astra defines plane coverage, exclusions and return transitions before release. |
| In2.Cu | Power distribution and released lower-speed routing, with ground where useful. Do not turn every supply into a plane or route sensitive signals across split references. |
| B.Cu | Existing contacts and constrained routing outside exposed-metal reservations. It is not a free routing surface just because inner layers exist. |

Retain nominal 1.6 mm total thickness, outline, mounts, USB/contact interfaces
and existing component poses during baseline migration. Select an actual
conventional manufacturable stackup before impedance-sensitive route release;
no invented dielectric thickness, copper weight or cross-fab impedance claim.
Prefer common stock constructions, ordinary through-vias and existing
clearance rules over blind/buried vias, microvias, sequential lamination or
fabricator-minimum geometry. Those advanced processes need a specific
engineering reason, not just a shorter route.

**Impedance-aware routing is distinct from purchasing a controlled-impedance
fabrication service.** RP2040 USB is full-speed (12 Mbps), but Raspberry Pi's
[hardware design guide](https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf)
section 2.4.1 still targets approximately 90 ohms differential with
uninterrupted underlying ground. Use the chosen fabricator's actual stock
stackup to determine geometry; do not transfer the guide's two-layer trace
dimensions to this four-layer board. Whether a specified impedance
tolerance and supplier verification are required remains a release
decision. Do not waive USB, QSPI, clock or fast-edge return-path review
because the product has no gigabit interface.

Keep fast signals on F over uninterrupted In1 where practical. An In2 route
is not automatically well referenced through a thick core, and a B signal
cannot assume a continuous reference when In2 is split. Astra decides
critical layer transitions and return stitching once; Sol may then apply
that exact released pattern without repeatedly escalating identical cases.

Map exclusions by their actual purpose. Raw CELL_NEG must not connect to
protected GND; preserve R26/R27 and R24/C28 private sense/current paths.
New inner planes must not bypass those paths through existing same-net vias.
Review switching-node/clock regions and unintended plane capacitance.
Do not blindly copy or discard all old F-only exclusions on the inner layers.

Internal copper behind intact laminate is distinct from exposed surface
copper, but ordinary F-to-B vias have B pads/barrels. Sol must screen the
entire via span, all-layer pads/antipads and conductive contact footprints.
No ordinary masked copper/via under battery metal is newly authorized.
Slots, holes, edge clearances and hardware remain part of every layer's
obstacle model. Bare laminate is not a complete battery-insulation qualification.

### Manufacturing simplicity without hidden substitutions

For new connections prefer short off-pad escapes to ordinary through-vias,
with reviewed drill/annulus and solder-mask clearance. Retain existing via
sizes during migration; do not shrink them opportunistically. Multiple
ordinary vias may be better than an expensive filled via only where the
current, return-loop, thermal and land/paste geometry support that alternative.

U4's four resin-filled, planarized, copper-capped thermal vias remain the
current requirement. Four layers create an opportunity to review an off-pad
thermal/ground-spreading alternative; they do not prove it equivalent.
That is a separate bounded Astra decision with manufacturer/thermal/stencil
evidence. Tenting or ink plugging is not a silent replacement for capping.
The MCU exposed-pad vias have their own unresolved thermal/stencil review.

C24's accepted ground via adds a fifth explicitly mandatory resin-filled,
planarized, copper-capped via to the four at U4. Preserve the exact process
identities in the accepted reports; ordinary ground stitches such as the
C13 via do not acquire this requirement merely by connecting to In1.
Via-in-pad location, filling/capping treatment and blind/buried layer span
are separate properties. A filled/capped through-via remains conductive at
the back surface and cannot bypass the battery-contact exclusion.

Both [JLCPCB](https://jlcpcb.com/help/article/pcb-via-covering) and
[PCBWay](https://www.pcbway.com/pcb_prototype/PCB_Via_in_Pad.html) document
filled/capped via-in-pad processing. Treat it as an explicit fabrication
requirement, not a universal basic-service default. JLCPCB's
[POFV notice](https://jlcpcb.com/news/free-via-in-pad-6-20-layer-pcbs-pofv),
checked September 25, states that four-layer POFV incurs a charge.
Capability, dimensional limits, planarization/capping and quotation must
be confirmed for the exact package. Do not infer that VIPPO requires HDI,
or change layer count merely to obtain a promotional process price.

Keep any necessary special process explicit in the generic fabrication
notes and quotation options, independent of a vendor promotion. Preserve
manufacturer MPNs and a fab-neutral native/Gerber/drill master; supplier BOM
and placement conventions remain separate exports. Existing tall-contact,
USB-anchor, sourcing and full-PCBA gates still apply.

### First protected-ground candidate release

The source-bound `in1-exclusion-inventory.json` resolves all ten inherited
F-only private-return guards. Only two protected items enter In1: the
R24.2/C28.2 branch vias `6623be95-c657-5a8e-bedb-c5a73d42d40b` and
`eafa404c-be47-5f5c-8167-d39a967ba2e5`. The R26.2/R27.2 private branch
is F-only. This permits a first **staged**, not automatically accepted,
In1 GND plane with the following explicit strategy:

- Reuse the known native front-zone outline and conservative fill settings
  on a new In1/GND zone. Preserve the old F zone and all ten F exclusions.
  Add no vias, tracks, placement changes or other-layer copper.
- Duplicate only those two via exclusions onto In1, retaining their exact
  source bounds and 0.25 mm private-copper guard. Do not punch eight more
  holes merely because F-only pads/traces have projected rectangles.
  Require both actual private-terminal cut proofs on the full filled graph.
- Keep added In1 copper out of each of the six actual BOOST_SW item bounding
  boxes, expanded by 0.25 mm, rather than using a large box contaminated by
  unrelated clock components. This conservatively limits new capacitive
  coupling below existing switching copper without changing the local loop.
- Pending physical-stackup/load-capacitance review, keep added In1 copper
  outside the recorded crystal/Y1/C2/C3/R6 region expanded by 0.25 mm:
  native bounds `[90.1036, 96.152596, 97.2375, 100.263901]` mm.
  These switching/clock exclusions are provisional engineering choices,
  not universal manufacturer rules or permanent optimization targets.

Internal GND elsewhere may approach ordinary different-net plated copper
only under the retained native clearance rules. Explicitly check CELL_NEG
and protector nets; no ground bypass or contact/via permission is inferred.
In2 remains empty. Do not claim the plane is continuous before inspecting
its actual islands, narrow regions and all existing connections after fill.
Required acceptance includes exact nonauthorized-source invariants, no new
DRC errors, no prior filled-pad group splits, no floating copper/shorts,
both private-pickoff proofs, and the full per-layer keepout/clearance checks.
If that fails, stop for review rather than enlarge/delete exclusions or
move parts inside an ostensibly routine correction.

### Batches, not one-net conversations

#### September 22 first-plane engineering disposition

Astra reviewed the saved actual-polygon clock/boost detail and the
source-bound replay/supplement for PCB
`19d3bf9a1ab37dcc7af29f0cc99cc44a98564f878402beee15af3ce0a731ff78`.
Accept this exact candidate as an **incremental routing baseline**, not
final SI/PI, current, thermal or fabrication approval:

- The five +3V3 segments at the clock void are existing supply copper, not
  newly routed fast signals. Retain them and the existing F ground/clock
  structures. Do not assert a continuous In1 reference beneath those
  segments or route new fast signals through this void.
- The two VAMP and three V+ witnesses lie at the switching exclusions.
  Retain the existing local F supply/return topology: the four checked
  U5.4/U5.6-to-C27/C28 paths remain all-F without via transitions. The added
  plane does not replace these paths or demonstrate ripple-current sharing,
  loop impedance or ampacity. No exclusion enlargement/reroute is justified
  by these projection witnesses alone.
- One connected In1 island, preserved existing pad groups and exact private
  guard/cut checks support this limited acceptance. They do not prove uniform
  return impedance or make the remaining ground connections unnecessary.
  Keep the private-via holes and CELL_NEG separation; release no new vias
  under conductive battery-contact metal.

Promotion must retain the exact saved PCB bytes, rebind only the manifest's
PCB-source metadata, and leave component geometry and the old snapshots
unchanged. Reuse the recorded checks only after verifying their input/output
and project bindings. Physical stackup selection and full CAD rebinding stay
open. Next routing releases must screen their actual return corridors against
these voids and all plated antipads; In2 is not blanket permission to bypass
that review.

#### September 22 supply-bridge release

The bounded core-supply screen resolves three VCORE groups but does not
release their proposed new-via escapes: rear contact metal and fixed copper
block the sampled positions. Do not infer that all VCORE escapes are
impossible or move the floorplan on that evidence. Preserve those groups
for a separate engineering decision.

Release a separate staged +3V3 bridge between existing through-vias in its
two native connected groups. Prefer the upper terminal banks near
`(92.85, 93.35)` and `(101.802, 93.0055)` mm, considering other existing
terminals within native corridor x90..103, y90..95 mm. Use In2 only, a
0.40 mm trunk, retained 0.20 mm clearance, no new vias or F/B changes.
Screen at most 16 direct/45-degree/dogleg candidates and stop if none pass;
do not narrow the trunk or enlarge the corridor inside a corrective retry.
The entire corridor is above the clock exclusion. Verify actual In1
coverage along the selected path, distinguishing the existing endpoint
antipads from unintended plane gaps. Retain all existing plane exclusions.

This avoids treating the first UUID-sorted via pair as the only reachable
terminals and avoids new holes or rear-contact exposure. It closes one
supply connection, not the remaining decoupler grounds or power-system
qualification. Preserve existing regulator/decoupling topology and require
complete group-preservation/private-return checks and native DRC before
acceptance. In2 insertion alone must not silently trigger a changed F/In1
fill; either demonstrate unchanged fill inputs or use the established
explicit-settings refill and compare its result. No generic router rebuild,
placement change, USB/clock reroute or VCORE geometry change is authorized.

#### September 22 local supply-ground stitch batch

After the +3V3 bridge checkpoint, release short local returns for the
existing GND groups containing C4.2, C9.2, C11.2/C15.2, C12.2, C23.2,
C24.2 and U2.2. These are regulator/digital-decoupling returns, not permission
to change the private sense paths, charger ground, USB ground or amplifier
thermal-via process. Preserve all existing group members and local routing.

Prefer a short F link to existing main-GND copper; otherwise allow an
off-pad ordinary F-to-B GND via, diameter 0.604 mm/drill 0.35 mm, tying
directly into the accepted In1 island. Use a 0.30 mm F stub no longer than
1.5 mm from reachable copper in the target group. Require exact all-layer
clearance and the full battery contact-metal reservation, not just pad DRC.
Do not use solder mask as insulation, overlap any component pad, place vias
in clock/switch/private exclusions, or cut an existing In2 route/return.
Stay within the same source copper group when choosing a different terminal.

Execute the straightforward eligible groups in one bounded batch, not a
fixed per-net escalation schedule. Limit numerical screening to 28 candidate
sites total, at most one new via per target group, and no part moves,
trace deletion, reduced width/clearance, longer detour or new layer role.
Report blocked groups and their exact obstacles without improvising a
floorplan repair. Refill F/In1 using the proven explicit settings and retain
both private-terminal proofs, all prior connected groups, the +3V3 bridge,
and unchanged VCORE partitions. New ground connections are intentional;
ground-plane changes outside the local stitches still require review.
Do not infer current/thermal qualification or complete decoupling from
the number of airwires removed.

#### Remaining-ground sampling follow-up

The preserved 24-site screen found no feasible site for C4, C11/C15, C12,
C23, C24 or U2. It sampled 0.65 mm axis offsets (only two offsets per pad
for the shared C11/C15 group), not the full released 1.5 mm escape region.
This is not evidence that those groups require a floorplan change.

Authorize one deterministic follow-up with all constraints above unchanged:
sample 0.80, 1.05 and 1.30 mm radii at 16 directions around each of the seven
listed pad terminals, at most 336 sites total. Rank feasible escapes by
length and local return geometry. Reuse exact native obstacle and drill
checks; pad non-overlap applies even for GND, but legitimate same-net copper
contact is not a foreign-net violation. Count and persist every site before
refill/validation. No adaptive grid, additional radii, reduced rules, new
placement, larger vias, longer stubs or repeated full-board trials.
The finite follow-up replaces the prior item's site cap only; it does not
reset the accepted board or authorize rerouting the completed R4 stitch.

#### IMU local-return closure batch

The source-bound 41-open inventory identifies two disconnected IC4 GND
groups: IC4.1/2/3 (Mode-1 grounded interface pins) and IC4.6/7 (ground
pins). Release these together as one local-return batch before the
dependent IMU control routing. Do not change the established Mode-1
pin assignments, initialization gate, parts or current SCL/SDA copper.

Work within native x87.5..92.5, y91.0..95.2 mm. For each group, prefer
up to four short geometry-derived F connections to existing main GND
(including now-connected C23/C24 copper), width 0.30 mm, length at most
2 mm, with robust endpoint overlap. If needed, screen at most 48
geometry-derived off-pad 0.604/0.35 mm ordinary-via sites from the whole
connected island, using a 0.30 mm F stub of at most 1.05 mm. Reuse
shared legal copper/returns if that closes both groups without consuming
signal corridors. Do not repeat failed pad-centred grids or add via-in-pad.

Keep every existing pad, part, track, via, rule, zone definition, contact
reservation and private return unchanged. Existing through-via spans and
rear-contact exclusions apply even for a short inner-plane connection.
Do not reroute SCL/SDA/USBBOOT or power to make a site fit. Preserve
C24's mandatory capped-via process and both capacitor-ground closures.
In1 must retain its protected topology; no clock/boost exclusion changes.

Stage one coherent candidate containing whichever intended groups have
legal connections within the finite batch. Continue through straightforward
work, but stop rather than guessing if fixed obstacles need engineering.
Require native DRC and complete graph/private-return/source-preservation
gates; only the released groups may join main GND. One closed group gives
40 opens, both give 39. Record unresolved groups and blockers honestly.
Apply the established independent displacement/clearance checks for remote
cache differences. Root review is required before promotion.

#### C24 centered filled/capped ground-via trial

The read-only feasibility review passed the Default-class 0.60/0.30 mm
ordinary through-via at C24.2's exact centre (92.004083,93.491669) mm.
Astra releases one staged instance of that geometry, no other position,
size, new track or existing-copper edit. The 0.604/0.35 mm alternative
remains rejected because its annulus exceeds the original pad copper.

Preserve the native 0.600 mm square land, its explicit +0.0508 mm mask
margin and unchanged 0.600 mm square paste aperture. The circular annulus
fits the land exactly; its nominal drill annulus is 0.150 mm. This nominal
geometry is not a supplier registration, flatness or assembly-yield approval.
The new via must be explicitly identified by UUID and coordinates as
requiring nonconductive resin fill, planarization and copper capping.
Ordinary tenting is not a substitute. Use native treatment metadata only
if supported and exercised; otherwise preserve ordinary native geometry
and bind the mandatory process in the source-bound report/quotation notes.
Do not invent file syntax or claim Gerbers encode the required treatment.

The only permitted pad-overlap exception is the original C24.2 land.
Retain every existing track, via, part, pad, zone definition, rule,
private return and contact reservation. Require full native geometric
checks and only the C24/main-GND merge (42 to 41 opens). Reuse the
established refill/actual-island proof, independent remote displacement
bounds and actual clearances. Stop on any other topology or substantive
plane change. Promotion, manufacturing treatment acceptance and fabrication
are separate decisions; no supplier upload or order is authorized.

#### C24 filled/capped through-via feasibility review

The local C24 attempt found no passing proposal among four F bridges and
48 whole-island ordinary-via sites. Do not repeat or expand those screens.
Use the owner's existing permission to consider necessary filled/capped
vias for a read-only feasibility item, not automatic acceptance of a new
process. The quotation baseline already requires this treatment at U4;
that does not establish incremental cost or supplier acceptance for C24.

Inspect the exact C24.2 native copper, mask and paste shapes. At its exact
pad centre, screen only two ordinary through-via definitions:
0.604/0.35 mm and the existing Default-class 0.60/0.30 mm. Do not shrink
existing vias, lower rules, introduce microvias/blind vias, move parts,
or edit copper. A positive proposal must fit the original pad copper,
meet full-span foreign-copper/drill/contact/edge/private constraints,
and reach the actual In1 main plane. Pad overlap is intentional only for
this feasibility screen; it would require filled, planarized, copper-capped
treatment and subsequent explicit land/paste/process review, not tenting.

If back-layer copper blocks both choices, identify its exact items,
endpoints, existing layer transitions and pad-attachment/cut consequences.
Do not reroute or remove it. Return the combined feasibility evidence
before deciding whether a local existing-via layer transfer or another
engineering approach is appropriate. This review authorizes no candidate
generation, supplier upload, quotation claim or fabrication.

#### C24 local ground closure

After the accepted C12 paired-feed change, release one bounded C24.2
ground-closure item on the exact 42-open source. Prefer a short F bridge
between its existing filled island and main GND: screen at most four
geometry-derived boundary-pair proposals, width 0.30 mm and length at
most 2 mm, with robust endpoint overlap. If none passes, screen at most
48 geometry-derived ordinary-via proposals from the whole C24 island,
not a repeat of the old pad-centred radial grid.

Via proposals use diameter/drill 0.604/0.35 mm and a straight 0.30 mm F
stub of at most 1.05 mm. Keep geometry within native
x90.5..94.5, y91.5..95.1 mm. Preserve every existing track, via, pad,
part, supply feed, rule, zone definition, contact reservation and private
return. Apply full-span copper/drill/slot/contact screens for any via;
no via-in-pad, masked contact-metal workaround or special via process.
If an ordinary local connection cannot pass, stop with exact blockers.

Stage at most one passing proposal and use the established native refill
and complete acceptance gates. Require only C24.2 to join main GND
(42 to 41 opens), preservation of all other partitions and private cuts,
no shorts/floating copper or new non-open DRC findings, and no substantive
In1 plane change. Enumerate any remote cache differences and retain the
independent 10-IU containment and actual clearance requirements. Root
review remains mandatory before promotion; do not reroute SCL, USBBOOT,
VCORE or power to make this ordinary ground connection fit.

#### C12 paired supply-feed and ground-closure trial

The C12 whole-island review found no ordinary GND-via site in its bounded
38-site set. Do not repeat that screen or assume that moving USBBOOT alone
would resolve the other power, SCL and VHI obstacles.

Astra releases one separate staged paired replacement, not simple deletion
of the necessary +3V3 feed. Retain the entire existing C12.1-to-IC1.10
branch, including `8b1b53b0-240a-5fc7-b78e-b5ee023450c3`. Replace only
`a869dd24-8003-5303-82af-32d37e552b3a` with a short F feed to one new
ordinary +3V3 via and a short In2 connection to the existing +3V3 bridge.
The original F feed remains authoritative unless that complete replacement
and C12 ground closure pass review together.

Use exactly nine candidate via centres: x97.6765/97.8765/98.0765 crossed
with y94.7577/94.9077/95.0577 mm. Each uses diameter/drill 0.604/0.35 mm,
a straight 0.20 mm F stub from the retained branch endpoint
(97.8765,94.5077), and a 0.40 mm In2 connection to (via-x,94.25).
Do not alter the existing bridge, pads, parts, vias, rules or other tracks.
Screen all fixed foreign copper, pads, drills, slots, rear-contact metal
and exclusions with existing native helpers. No via-in-pad or new special
process is released. The paired feed replaces a longer 0.1778 mm branch;
this is not a current-capacity or power-integrity qualification.

Unlike a GND via, the proposed +3V3 via requires local F ground clearance
and an In1 antipad. Authorize the established native refill for that
specific purpose; do not treat permission to refill as permission to
disconnect existing groups or change private returns. In1 change must
remain confined to the new via's clearance neighborhood and preserve
plane continuity and the existing clock/boost exclusions.

After replacing the feed, close the measured C12/main-GND gap at
x95.433470, y94.218300..94.797100 mm by refill, or by one 0.30 mm F
bridge with at most 0.10 mm endpoint extension if needed. Retain the
local capacitor-to-MCU copper and require all +3V3 pads to stay connected.
Accept only the intended C12 GND merge (43 to 42 opens); any other merge,
split, clearance finding, remote substantive refill change or unresolved
return-path consequence stops for root review. Apply qualified actual
filled-island connectivity, not the rejected difference-fragment proxy.
No retries beyond the finite nine-site set or expansion to other nets.

#### USBBOOT corridor relief for C23

The exact +3V3 cut analysis separates C12.1/IC1.10 from their source.
Retain track `a869dd24-8003-5303-82af-32d37e552b3a`; it is not redundant.
C24's SCL group has no existing via transition and is not released for
rerouting by this decision.

Authorize one staged local USBBOOT reroute to free the C23 front-ground
corridor. USBBOOT is the D3.C/IC1.9/TP3 control net, not D+/D-/USB_D+/USB_D-.
Use existing through-vias `6a769f0c-bb2a-5e4f-a23f-f2870ed623cd`
at (87.7,88.95) and `45b3cf7f-e607-5ab4-b380-95baa0095dbd`
at (92.85,92.1) mm. First prove a unique unbranched F track chain between
them that includes the two named blocking segments `f64f7022...` and
`372abf98...`. If any interior pad, via or branch attachment would lose its
connection, stop rather than expanding the removal scope.

Replace only that proven chain with a 0.20 mm In2 connection between the
same vias, retaining 0.20 mm clearance and actual In1 return coverage.
Use at most 12 direct/45-degree/dogleg candidates within native
x87..93.5, y88..93 mm. Add no vias, change no pads/parts, and preserve all
other tracks and the +3V3 bridge. Keep D3, the MCU boot input and TP3
connected; do not treat connectivity through the MCU silicon as PCB copper.

With the F corridor freed, allow one 0.30 mm GND bridge at the measured
C23 island gap, (90.678764,90.389400) to (90.678764,89.810600) mm,
only if a native exact screen passes. Extend into the existing endpoint
islands by at most 0.10 mm if needed for robust contact; no sideways search.
The established refill may close this gap directly instead, in which case
do not add unnecessary copper. Require all previous groups/private returns,
unchanged non-USBBOOT net partitions except the intended C23 GND merge,
native DRC and exact per-layer protections. Stop on any other new merge or
remote/unexplained fill change. Acceptance requires actual C23 closure,
not merely moving a control trace and declaring the corridor improved.

First qualify the tools for four layers: actual enabled-layer enumeration,
via spans, multilayer obstacles, inner-plane fill/connectivity and source
invariants. The existing F/B-only grid and ground checkers are not qualified
merely by changing a layer-count setting. Add a small deterministic
cross-layer/via/plane control before accepting production-board inner routes.

The source-derived saved-native graph control has now passed; its report is
`printed-bell-four-layer/reports/four-layer-graph-saved-native-control.json`.
This releases the exercised graph/zone/via-span checks, not the old F/B
search engine or the actual board's ground topology. Qualify the tool used
by each operation: an explicitly reviewed native plane-fill operation need
not wait for an unused multilayer autorouter. Old routing masks/search must
not be used to claim inner-layer route legality.

Distinguish fixed copper from refillable zone copper in proposal tools.
A new signal through-via will need antipads in an existing GND plane; treating
the old fill cache as immutable copper would falsely forbid nearly every
such transition. Conversely, ignoring the plane is not acceptance: regenerate
its clearances and verify continuity, necks and return paths after insertion.
Keep rule-area exclusions and private-return restrictions hard constraints.
The intended F-to-In2 connection still requires a full F-to-B via clearance
and contact-metal screen; stopping a route on In2 does not create a blind via.

Then work in dependency order:

1. Establish the protected-ground/return strategy and reserve USB, clock,
   power/boost/protection and contact corridors; connect supply/return
   structures together rather than sacrifice one for the other.
2. Execute released critical-interface strategies and their return paths.
   Existing clock/QSPI and reviewed power structures are preserved unless
   deliberately revised, not automatically rerouted onto inner layers.
3. Complete routine connected groups in shared spatial corridors using the
   remaining F/In2/B freedom and already-approved via patterns. Query all
   useful terminals of each group rather than force a distant fixed pad.
4. Close remaining plane/return gaps, review the coherent board, then rebind
   mechanics and produce matched fabrication/assembly evidence.

Astra's release brief supplies the exact source hash, group/corridor scope,
reserved geometry, allowed layers/widths/vias, excluded changes, required
connections and stopping conditions. Sol executes all straightforward work
within that release and checkpoint budget, not "N nets then ask Astra."
It may choose among already-released geometric alternatives; it must not
reinterpret an implementation-only correction as another geometric trial.

Use one native board load and reusable per-layer spatial data per batch.
Invalidate affected geometry caches after edits. Screen a bounded candidate
set numerically, retain useful local solutions and group failures by root
obstacle. Stop and escalate when additional work requires a new electrical,
return-path, process or placement decision, or when progress/retry limits
are exhausted. Old failed two-layer searches are not rerun unchanged.

Use cheap scoped collision/connectivity checks while proposing routes.
At each coherent changed-copper checkpoint run native all-layer DRC,
refill and independent filled-connectivity/private-return/contact checks.
Require both named new connections and preservation of old required groups;
fewer opens alone is not acceptance. Do not pay for complete CAD/Gerber
regeneration at every local step, and do not replace release gates with
scoped checks. Record stop reason, runtime, actual source/output hashes,
connected groups, track/via deltas and remaining concerns compactly.

Independent Sol agents may inspect sourcing, geometry or evidence in
parallel; only one writes the candidate. Reuse loaded context and existing
agents where available, give each a bounded deliverable, and do not launch
a separate agent for every trivial segment. Every executor remains
explicitly Sol/medium, fail-closed; Astra accepts engineering milestones.

## Bottleneck-first closure sequence

September 23 owner request: use the IMU exercise to improve placement and
remaining routing efficiency. The lesson is not simply "route the IMU
first." Establish viable escape and return geometry for every highly
constrained functional group before freezing surrounding routing.
Footprint/envelope fit alone cannot establish that its pins are routable.

The relevant IMU group is IC4, C23/C24, R14/R15, both ground groups,
Mode-1 supply ties, and INT/SCL/SDA escapes, including full-span via
restrictions from the rear contacts. These concerns must coexist.
Ground-via space and a signal escape cannot each be counted as available
if they occupy the same corridor. Keep local capacitor-to-device current
paths explicit instead of treating a common supply/ground name as proof
of adequate return geometry.

For the remaining accepted board, use this dependency order:

| Priority | Coupled concern | Gate before releasing dependent routine work |
|---|---|---|
| 1 | IMU local returns, decoupling, pull-ups and signal escapes | Mutually compatible local routes, preserved existing connections and external ports; no movement assumed from the failed rigid-shift cases. |
| 2 | MCU VCORE distribution and its capacitor-ground cluster, USB/ESD/series-resistor pair corridors, and remaining charger/power-selection returns | Review these as distinct constrained groups and reserve their competing corridors together before ordinary GPIO fanout. USB physical stackup/return assumptions must be explicit; a layer count is not impedance qualification. |
| 3 | Remaining audio/output-current paths, amplifier return/mute/gain duties and I2S clocks/data including test-point branches | Preserve switching/private-sense topology and quiet returns; review loop areas and fast-edge/test-stub choices before completing adjacent controls. Existing accepted boost/protector work is retained unless a concrete conflict is found. |
| 4 | Low-speed controls and debug/recovery connections | Use the remaining released corridors; retain reset/boot/test access and escalate debug fast-edge or sensitive adjacency questions. Lower routing priority never makes recovery optional. |
| 5 | Whole-board electrical/mechanical/process closure | Complete native connectivity/DRC and parity dispositions, actual stackup/return/current review, CAD source rebind, mandatory via-treatment map and matched quotation exports. None is replaced by local passes. |

Within priorities 2 and 3, order competing groups by their actual free
space, dependency and replacement cost, not by net count. Do not start a
new broad inventory for every route: reuse the source-bound net ledger and
refresh only changed groups/corridors. Protection, raw-cell isolation and
mechanical contact exclusions remain invariant at every priority.

Efficiency rules learned here:

- Use whole connected copper groups and feasible regions, not only pad
  centres or repeated sparse grids. Classify clearance witnesses by the
  constraints that actually limit the final space before a cut analysis.
- Freeze a compatible local escape plan before expensive full-board work.
  Test simultaneous planned copper, not independent "clear" route sketches.
- Distinguish hard mechanical/critical interfaces from inherited routing
  choices when defining a rework boundary. Local transition vias may be
  candidates for explicit Astra release; Sol must not move them silently.
  Prove the replacement signal/power and return paths together before
  treating that freedom as a solution.
- A bounded cardinal escape screen is not an exhaustive direction proof.
  Proposal via-centre regions are upper bounds until native via, stub and
  joint-plan constraints all pass. The failed twelve-plan IMU trial does
  not rule out every fixed-placement solution.
- After a fine-pitch part moves, identify retained terminals outside its
  affected fanout. An old pad centre can coincide with a different-net
  moved pad; straight tails back to every old terminal are not a general
  re-layout method. Replace the implicated fanout, not the board rules.
- Reports must distinguish authorized freedoms from those actually
  exercised. An omitted via obstacle needs a complete replacement path;
  an allowed internal boundary reroute needs explicit clipping and preserved
  outside copper. Do not call an unimplemented topology an exhausted scope.
- Keep a useful candidate and a finite repair list. Do not reopen settled
  sourcing or move a cluster merely because one local route fails.
- Run cheap native geometry/topology checks during a batch; run full
  refill/DRC/private-return/source gates once a coherent candidate exists.
  Save intermediate successes and failures so a checker error does not
  erase completed evidence.
- Reuse exercised unit/shape APIs and actual filled-island connectivity.
  Keep approximation/displacement and physical-clearance tests separate.
  A diagnostic polygon sliver is not an independent physical copper island.
- Escalate repeated no-progress probes to one coordinated engineering
  decision rather than restarting similar searches under new task names.
  Sol executes the finite geometry work; Astra owns the coupled constraints
  and acceptance.

This sequence is a closure plan, not a claim that the board was previously
optimized or that the remaining work has a predictable duration or cost.
The historical two-layer routing, later four-layer approval and evolving
contact/interface evidence explain changing opportunities; they do not
excuse treating placement fit as routing feasibility.

## Preserved two-layer baseline and engineering reservations

Preserved package: `hardware/handbell/iterations/printed-bell-clock-draft`.
Starting PCB SHA-256:
`a83cc417c96b05dd15c187e648b9fd2a35ba857c3a66f7d13aaaa42ae3bd9fff`.
The accepted `charge-led-routing` reports show 51 opens. The historical
`printed-bell-quote-candidate` archive is not the active board.

Initial triage from the exact accepted filled-connectivity ledger:

| Reserve for Astra before routing | Why |
|---|---|
| D+/D-, USB_D+/USB_D-; SWCLK/SWDIO | USB pair geometry/return paths; debug clock integrity and recovery |
| I2S_BCLK, I2S_LRCLK, I2S_DIN | Clock/data adjacency, return continuity and audio-interface timing |
| VCORE, +3V3, GND | Core decoupling and supply distribution; 18 ground opens; prior VCORE route split returns |
| VBUS, VBAT, VHI, VAMP, VO+, Net-(FB2-P$1) | Power/current paths, boost/audio topology, BTL output filtering |
| POWER | Function/current-path classification required before treating the name as a control |
| GAIN, SCL | Existing local congestion blockers; no retry reset or removal of unproved-redundant 3V3 copper |
| All existing crystal/QSPI, boost, protection/sense and thermal structures | Preserve settled routing and private returns, even if not listed as opens |

Potential routine controls are AMP_MUTE, BUTTON, D13, INT and reset, but
they are **not automatically released**. Sol first inventories their physical
groups, endpoints, obstacle/return context and potential conflicts. Reset
must retain recovery access and noise immunity. Astra releases only regions
that cannot consume critical corridors; the central MCU/core/USB region and
boost/audio power regions remain reserved pending local review. Escalate
if no genuinely independent low-risk route exists.

The [Sol native inventory](measurements/2026-09-21-routing-control-inventory.json)
found no independent complete control net. Astra's local RESET review confirms
the short pull-up chord crosses F-side VBAT while B-side VHI and raw-contact
metal constrain transitions. Do not route RESET merely because its endpoint
distance is small. Keep TP7, TP15 and all recovery/service branches; no optional
branch removal is authorized.

For the SCL decision, Sol's
[primitive-graph cut analysis](measurements/2026-09-21-scl-enclosure-analysis.json)
found the
0.1778 mm pair `548c8552-ff4c-56b3-83d9-9d0a5389e3e2` /
`76a37864-74d8-5963-bcc4-18eb043accfd` topologically redundant, but the adjacent
0.25 mm F/B branch and its via deliver supply to the IMU/pull-up group.
Removing both separates R14.1/IC4.8. Therefore preserve the complete 0.25 mm
branch, via, SDA and part positions. Topological redundancy is not proof of
current-sharing equivalence.

Astra authorized only a **staged final SCL correction** removing that exact
fine-track pair, with the 0.25 mm supply path unchanged, to determine whether
an F-only SCL link can fit without moving any other copper. This is not
acceptance of the deletion: actual corridor benefit, source-bound pad groups,
supply/return continuity and local power-path review remain required.
No new via/B route, smaller clearance, wider search or placement change is
authorized. If the remaining branch still blocks SCL, stop rather than
extending the deletion. This consumes the remaining correction in the saved
SCL item, not a fresh retry allowance.

**Outcome:** Sol's [final correction](measurements/2026-09-21-scl-final-correction.json)
exhausted the bounded F-only sampled component after 2,793 expansions in
0.563 seconds. No route/candidate PCB was produced; no copper was removed
from the accepted board. This does not prove that every possible route is
impossible, but the fine-branch deletion did not solve the sampled corridor.
Do not repeat that search or delete the required wider supply branch.

**Historical two-layer engineering gate:** Astra must define a local IMU/pull-up supply,
SCL/SDA and return corridor together before releasing more SCL execution.
Read-only native geometry may evaluate options, but no supply reroute,
placement change or B-side crossing is authorized by this checkpoint.
Other control nets remain unreleased where they compete with reserved
critical corridors. The accepted state remains 51 opens.

### September 21 in-place R14 reversal screen

Native local analysis found R14's supply pad south of its SCL pad, with
the existing supply via northeast at (87.9, 93.6). Astra therefore allowed
a staged 180-degree terminal reversal about the unchanged R14 center,
removing only the two fine segments above and the immediate old-pad supply
spur `8b67bfa8-9f2d-5d11-b459-76494e6f41ef`. This would supply the upper pad
from the existing via and let the lower SCL pad escape south without moving
the wider supply network. No B routing or other placement change was allowed.

Sol verified the in-memory pad transform but obtained no SCL route.
The [record](measurements/2026-09-21-r14-terminal-swap.json) preserves the
negative result and its limits: search statistics were not captured, and
a second target search exceeded the one-target authorization. Neither was
accepted as a successful correction. The retained tool is now diagnostic-only,
with no PCB/manifest serialization, and records failure statistics. Do not
repeat these searches. The accepted PCB and placement manifest are unchanged.

This screen also found separate local filled-ground groups: IC4.1/2/3,
IC4.6/7, C23.2 and C24.2 are not a single continuous local return. R14's
immediate pocket is empty of fill, with nearby fill west of the pad.
Thus a signal-only geometric success would still require joint return review.

The subsequent two-layer item evaluated **local R14 relocation adjacent to the
existing SCL group**, with its short supply connection and ground-return
space together, rather than disturbing the 0.25 mm supply delivery or
retesting the trapped pocket. The screen approved no position. Four-layer
migration now takes priority over those two-layer-specific repairs.
Mechanical rebinding is required if a move is eventually accepted.

## Work and acceptance

Sol executes established constraints, not redesigns. Preserve placement,
existing good routing, footprints, stackup, net classes, design/zone/pair rules
and fixed interfaces except for precisely authorized migration/engineering
changes. Native rule evaluation is necessary but insufficient.
No supplier upload, purchasing, fabrication or child-use authorization.

Continue straightforward authorized work through bounded checkpoints, not
"N nets then ask Astra." Time/process limits and two corrective retries remain
runaway-work safeguards, not arbitrary engineering escalation thresholds.
One writer; staged candidates only until Astra accepts.

Escalate organically for SI/EMI/PI alternatives, high-speed/differential/clock
signals, sensitive analog or measurement paths, high-current/switching loops,
return/plane concerns, new via/stub tradeoffs, placement changes, significant
rerouting or competition for a more important corridor. Astra supplies the
decision and a concrete strategy, then returns routine execution to Sol.

Preserve actual filled-pad groups, source hashes, private pickoffs, raw-cell
isolation and contact-metal reservations. Use qualified all-layer refill,
native DRC and independent filled checks, requiring named new connections.
Old F/B-only checks cannot qualify new inner copper. No whole SES
replacement; no silence of clearance findings. Astra additionally reviews
return-current routes, plane cuts, adjacency, loop area, decoupling topology,
and vias/stubs. A DRC pass alone never promotes a candidate.

Full personal runtime logs remain local; publish only compact model/effort,
outcome and source-bound engineering evidence, not profiles or credentials.
