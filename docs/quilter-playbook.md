# Quilter playbook: an agent-assisted layout workflow

Use this guide to prepare useful jobs and evaluate their results without
relearning every experiment. Optimize for an acceptable board with bounded
owner/agent effort, not trace aesthetics or recovery of sunk costs.

Evidence reviewed through **October 4, 2026**: Quilter UI 1.40.0/API 1.40.1
and KiCad 10.0.6. This is a living procedure, not a platform guarantee.
The [workflow study](quilter-workflow-study-2026-10-02.md) retains the dated
reasoning; its linked ledgers bind exact files and results. The
[closure plan](pcb-closure-plan.md#owner-pause-and-next-item) controls current
authorization and blockers. This guide does not release another job,
native-tool retry, source edit, purchase or fabrication.

## What the evidence supports

| Finding | Evidence and limit | Working guideline |
|---|---|---|
| Selected existing routing can survive while Quilter adds useful routes. | Both [contact-control outputs](measurements/2026-09-27-router-bakeoff/quilter-contact-routing-output-review-2026-10-03.json) preserve the checked inventory and connect both test pairs on B without new vias. [Recovered native DRC](measurements/2026-09-27-router-bakeoff/quilter-contact-native-validation-2026-10-04.json) reports zero opens but 45 findings each. The [saved-plane supplement](measurements/2026-09-27-router-bakeoff/quilter-contact-plane-isolation-2026-10-04.json) passes all 20 foreign-via isolation and 20 GND attachment cases. | Retain reviewed critical blocks where useful; independently verify preservation and new copper. This diagnostic behavior is qualified, not a clean or accepted product board. |
| Preservation is not automatic for every input/configuration. | Earlier [full-board outputs](measurements/2026-09-27-router-bakeoff/quilter-output-preservation-2026-10-02.json) lacked the original inner GND zone and exact matches for 24 In2 segments. That did not prove 24 lost electrical connections. | Inspect returned copper and planes before ranking routing improvement. Distinguish record changes from connectivity loss. |
| Import recognition is weaker than routing evidence. | The [first contact preview](measurements/2026-09-27-router-bakeoff/quilter-contact-feed-import-2026-10-03.json) had zero pins to route. The later control had actual unrouted pairs and legal-path witnesses. | Submit a diagnostic only when it can exercise the behavior in question; a parsed preview alone is not that experiment. |
| A green dashboard has a limited scope. | The contact job's one physics pass was an inferred VBAT 500 mA check; its new-violation lists were empty. Native DRC subsequently completed with inherited, rule-dependent and new isolated-fill findings. | Record which checks ran, their assumptions and whether they cover inherited or new findings. Do not translate "100%" into engineering acceptance. |
| Time to first result differs from time to final result. | [Candidate receipts](measurements/2026-09-27-router-bakeoff/quilter-contact-routing-control-2026-10-03.json) show about 6m20s for 1.1 and 2h7m15s for 1.2. | Evaluate an available useful candidate without waiting unnecessarily for final optimization. Do not extrapolate this tiny job's runtime to a full board. |

Use **observed** for a result demonstrated on identified artifacts,
**documented** for a vendor statement, and **proposed** for a workflow
choice not yet exercised. A documented capability is not an observed
pass; an incomplete check is not a demonstrated design failure.

## 1. Decide what freedom to give the service

Choose the question before editing the input:

- **Complete existing routing:** retain the explicitly protected placement,
  feeds and copper; measure preservation and remaining connectivity.
- **Explore a fresh layout:** retain real interfaces and reviewed critical
  or process blocks, while releasing ordinary placement/routing on a
  disposable copy. Do not accidentally freeze an old floorplan by retaining
  all its intermediate escape traces.

The agent's job is to express engineering intent and review results;
Quilter's job is placement/routing search. Do not use repeated manual
LLM trace placement as the default way to compensate for an unclear input.

Separate genuinely fixed requirements from preferences. Preserve real
component dimensions, contact metal, insulation, mating/service access,
critical current/return paths and required manufacturing processes.
Allow approved enclosure/support changes instead of treating old plastic
geometry as immutable. Rebind the complete assembly before accepting a
selected layout, not after every disposable iteration.

Organize functional groups around actual duties: supply pins and their
capacitors, crystal/load capacitors, switching loops, USB, protection and
private sense returns. Shared net names or visually grouped parts do not
by themselves establish the right electrical associations or distances.
For unsupported essential constraints, retain a reviewed block, provide
an explicit independent acceptance check, or stop; never silently omit them.

**Proposed practice, not yet full-board exercised:** retain only a few
source-reviewed sensitive cells and release ordinary layout around them.
An exact retained block needs copper identities and external terminal/
junction obligations, not just a list of fixed footprints or a rectangular
cut. Check private pickoffs at the actual terminal lands; shared-net
continuity is not equivalent. The handbell's selected first-comparison
boost/protection/clock strategy leaves72 of104 references eligible;
the complete input and physical/electrical constraints are not yet qualified.
See the [common-input disposition](quilter-workflow-study-2026-10-02.md#common-input-strategy-retain-critical-cells-release-ordinary-layout).

**Observed relative-constraint path, not qualified routing behavior:** the
[October4 capability disposition](measurements/2026-09-27-router-bakeoff/quilter-movable-domain-disposition-2026-10-04.json)
finds Custom Component Proximity in the current client and an existing-job
schema: child component, parent component/pin and maximum distance in mm.
The help explicitly says best effort, with a final distance PRC; there is
no explicit child-pin field. Use it only for a reviewed relationship not
already covered by bypass comprehension. Its10mm new-row default is not
an engineering target, and proximity does not bound routed length,
return paths or private topology. Prefer legitimate relative constraints
over needless fixed rooms, but qualify persistence and actual behavior.

Keep public documentation, client code, saved schemas and executed
constraints separate. Timing controls remain described as unavailable
in public prose, while the current client and old-job schema expose their
fields; neither justifies claiming a working timing constraint. Likewise,
the documented crystal limitation for series/load-limiting resistors
remains relevant to R6. Manually adding a row cannot be assumed to repair
unsupported topology. Preserve R6 and the real load-capacitor connections;
resolve the missing contract before freezing the MCU or releasing clocks
as generic low-speed signals.

Bind physical pad number, schematic function and imported service PIN
token separately. The [clock binding](measurements/2026-09-27-router-bakeoff/quilter-clock-relative-contract-2026-10-04.json)
corroborates20=XIN and21=XOUT, but descriptive20/XIN is not a verified
API value. Nor does a GND net make every terminal a suitable ground
anchor: pin19 is TESTEN; P$1 is the actual exposed ground.
Keep source observations distinct from new acceptance limits. A historical
route width, a literal old guard rectangle and a zone's min_thickness
cannot establish a new proximity threshold or moved quiet-area margin.
Reconcile intentional plane exclusions with reference/return intent by
layer and purpose instead of imposing contradictory blanket rules.

**Retained-cell proof discipline:** connect the selected graph to actual
source-bound pad lands and enumerate its joins to copper that will be
removed. A connected graph of hardcoded coordinates is not yet that proof;
hashing an old report without comparing its relevant geometry does not
rebind the coordinates. The initial
[preserved-clock packet](measurements/2026-09-27-router-bakeoff/quilter-preserved-clock-qualification-2026-10-04.json)
exposed both gaps at root review. Its executed missing-member controls
exercise membership, not connectivity or complete identity coverage.
Keep those claims separate even when all reported controls pass.
The [October5 recovery](measurements/2026-09-27-router-bakeoff/quilter-preserved-clock-boundary-recovery-2026-10-05.json)
resolves the clock pad/path gap from the already available current-source
native inventory. Search the authoritative geometry record before reviving
older diagnostic coordinates. For an internally self-contained ordinary
cell, preserve its local paths and external terminal/net obligations;
do not freeze every historical fanout, via or pour contact. This is not a
waiver for private/Kelvin paths or final reference/return behavior.
Name contact-incidence groups accurately: shared object identities do not
prove one physical junction, and counting pad/via pairs as "not endpoint
matches" is not an independent segment-interior control.

**Observed local-net distinction:** every physical terminal on six
protector/feedback nets belongs to the proposed retained cells. Retaining
their complete source primitives preserves parallel branches missed by
path-only selection. This is justified by the all-terminal inventory,
not merely the net's name, and does not justify retaining global GND or
amplifier feeds. Current-sharing and process qualification remain separate.
See the [local-circuit evidence](measurements/2026-09-27-router-bakeoff/quilter-critical-local-retention-2026-10-04.json).

**Observed retention limit:** complete source-local routing can preserve
an inherited physical conflict too. The
[complete212 contact screen](measurements/2026-09-27-router-bakeoff/quilter-critical-retained-contact-screen-2026-10-04.json)
finds one non-process PROT_COUT via with0.225 mm nominal metal clearance
against required0.25 mm, although all five mandatory process seeds pass.
Screen the complete proposed retention, not only its protected seeds.
Distinguish an unmet clearance from actual metal overlap, and a real
flat-edge shortfall from conservative corner-envelope effects. Hold the
input and assess the affected route's role; neither source fidelity nor
a small numerical shortfall authorizes a clearance waiver or silent repair.
The [COUT dependency check](measurements/2026-09-27-router-bakeoff/quilter-prot-cout-retention-disposition-2026-10-04.json)
then proves that simply omitting the conflicting via breaks charge-gate
control. Prefer a clearly scoped whole-net rerouting obligation over
accidentally retained dangling copper when partial retention cannot
preserve the intended function. This remains a proposed workflow choice,
requiring all-terminal restoration and electrical/physical qualification.
Keep selection validity, complete-input eligibility and returned-routing
acceptance as distinct states. The [COUT contract controls](measurements/2026-09-27-router-bakeoff/quilter-prot-cout-release-contract-2026-10-04.json)
accept a deliberate three-terminal unrouted specification without calling
it a connected output; they also reject the connected but contact-blocked
old route. Counts or one passing dimension cannot substitute for the others.

## 2. Build a source-bound input contract

Keep the authoritative board and raw experiments immutable. Record the
exact PCB/project/schematic/manifest hashes, reference and physical-pad
counts, net identities, fixed/movable references, protected copper/vias,
outline, layer roles, physical stackup and applicable process requirements.
Publish the execution scope before an executor pins its dependencies;
keep subsequent progress bookkeeping outside those frozen inputs. The
first preserved-clock attempt correctly failed closed when a concurrent
root scope update changed the pinned workflow file. That avoidable
coordination failure consumed a correction, not evidence of a PCB defect.
Use native poses, including footprint rotation, for both protected objects
and candidate obstacles rather than stale proxies.
Check any local-to-global transform against saved native coordinates and
known source-track endpoint joins before trusting generated keepouts.
Include signed90/270-degree cases: a180-degree case alone cannot distinguish
rotation sign. The [failed private-guard proposal](measurements/2026-09-27-router-bakeoff/quilter-private-tap-guard-definition-2026-10-04.json)
put two guards on opposite pads while its self-consistency controls passed.
Do not count tests sharing the same erroneous geometry as independent proof;
prefer a previously qualified native-coordinate source over a new transform.

Qualify candidate generation before trusting a precise narrow-phase result.
The [collateral review](measurements/2026-09-27-router-bakeoff/quilter-private-guard-collateral-2026-10-04.json)
correctly measures46 enumerated pairs, but root found the upstream broad
phase still used the wrong transform for non-private pads. A repair of
protected objects alone does not fix obstacle coverage; omitted pairs can
remain untested. Rebuild conservative candidates from the same qualified
geometry source and compare additions/removals before claiming completeness.
The subsequent [bound-population audit](measurements/2026-09-27-router-bakeoff/quilter-private-guard-candidate-coverage-2026-10-04.json)
does this for all177 retained primitives and97 native fixed pads, including
actual through-layer membership. It removes four wrong-pose pairs without
finding new collateral contact. Keep self pairs separate from design
conflicts, and fail on missing geometry rather than silently shrinking the
population: one8um segment needed a separately bound saved-native source.
This qualifies the exercised shapes and source, not arbitrary future
geometry; a far-away shape's valid bounds do not qualify its narrow-phase
intersection algorithm.
Also distinguish a prospective guard-halo conflict from actual copper
contact or minimum-clearance failure. An unchanged terminal-bank overlap
can be intentional; reuse source-bound topology evidence instead of
automatically redesigning the circuit or waiving all same-net findings.

**Proposed reusable staging practice:** capture a compact native geometry
record once for a specific source revision: UUID/reference/pad/net identity,
global pose, dimensions, shape and conductive layers. Bind it to the source
and extractor versions. Reuse that record for cheap static iterations; a
source/dependency change requires explicit requalification, not a silent
fallback. Keep source facts separate from derived guards, encoded ECAD
rules and observed router behavior. A pass at one stage does not certify
the next. This is a small evidence pipeline, not a reason to build a new
general-purpose CAD framework for each project.

**Observed local recovery:** the [private-guard repair](measurements/2026-09-27-router-bakeoff/quilter-private-tap-guard-repair-2026-10-04.json)
consumes the saved native pad inventory directly and matches all four
private endpoints without another native load. It rejects both known bad
poses before generating guards, separately from membership/flag checks.
This supports reusing a qualified geometry record for unchanged source;
it does not qualify new sources, polygon serialization or router enforcement.
Give evidence both a resolvable artifact location and a hash: a digest alone
is not enough for the next reviewer to find the geometry record.

Define each movable part's final allowed area from the intersection of
its side, height, access and electrical restrictions. Quilter's
[documented region behavior](https://docs.quilter.ai/guides/placement-guide)
combines assigned regions by **union**, not intersection. A broad F region
plus a narrow height region can therefore enlarge, rather than restrict,
the allowed space. Verify assignments and F-only behavior after import;
a single-sided preference or candidate filter is not proof of enforcement.

**Documented, reconfirmed October 4; movable behavior still untested here:**
an off-board region is a grouping hint whose size, shape and side are
ignored. An on-board or edge-overlapping region constrains placement.
For KiCad, a named top/bottom rule area with every keepout restriction
cleared represents a placement region; review/manual component assignment
after import remains necessary. Do not use a true safety keepout as a
placement room or expect an off-board grouping hint to enforce F-only.
See [KiCad region setup](https://docs.quilter.ai/design-parameters/placement-regions.md)
and [single-sided requirements](https://docs.quilter.ai/design-parameters/single-sided-placement.md).

**Observed native representation, not placer behavior:** the isolated
[F-room control](measurements/2026-09-27-router-bakeoff/quilter-f-placement-region-native-control-2026-10-04.json)
preserves a named F rule area with all five restrictions allowed through
KiCad10.0.6 save/reload, without changing its overlapping restrictive guard.
Root compares the entire new-room subtree and all58 original subtrees
with multiplicity and checks UUID uniqueness. Merely recording a contour
or comparing UUID-keyed dictionaries would not establish those facts.
The deliberate overlapping-room witness is not a useful cloud-placement
input: retain separate gates for real geometry, association and placement.

Keep placement regions separate from safety keepouts. Inspect each
keepout's actual track/via/pour flags and layers; a suggestive name is not
a rule. Screen full copper shapes, including the B annulus of through-vias.

Re-evaluate which parts actually move before building more domain classes.
At the handbell's selected+2mm spacing, the saved height screen leaves only
L1 and X6 at/above the nominal3.5mm ceiling; both are fixed under the later
27-reference retention. Thus eligible fitted movers no longer require a
separate tall-part magnet class. This reuses source-bound height/membership
evidence, not a new fit claim. It does not give every reference the same
origin polygon: full body/rotation, board-edge, access and copper-feature
obligations still need encoding. Qualify the smallest missing representation
control before generating dozens of unnecessary regions.
Filling or tenting a via does not remove its conductive rear land.

**Purpose-specific private-return protection:** prevent new taps where the
private copper actually conducts. Surface-only branches need surface
track/pad/via protection; existing through-vias need isolation on every
layer they reach, including newly added planes. Do not copy every surface
rectangle into inner-plane voids: the handbell's two private through-vias,
not all ten F exclusions, define its inherited conductive inner-layer
exposure. Switching/clock coupling exclusions serve a different purpose.
Follow the [layer-role policy](routing-agent-policy.md#first-protected-ground-candidate-release).
Quilter's [keepout documentation](https://docs.quilter.ai/design-parameters/keepouts.md)
generically includes components, but does not specify a KiCad pad/footprint
flag matrix. Our fixed-component contact control does not establish
movable-pad exclusion or all-layer private-tap protection.

Do not mistake a prospective "no new taps" engineering requirement for a
native new-objects-only rule. The
[completed native control](measurements/2026-09-27-router-bakeoff/quilter-native-tool-completion-2026-10-04.json)
also reports the retained source objects inside the restrictive guards.
Keep such diagnostic intrusions bound to exact identities and geometry;
their presence does not authorize deleting the copper, a blanket same-net
exception, or suppressing future violations. Product representation and
the router's treatment of pre-existing copper need their own disposition.

**Selected experimental pattern, not full-board exercised: restrictive
guards plus an immutable baseline.**
When a required guard encloses an intentionally retained connection, keep
the guard intact and identify the existing intrusion by guard, object,
layer, net and full geometry. Do not erase the connection to obtain a green
input DRC, cut a hole in the guard, or exempt the whole net. A returned
object may match that baseline only if it is genuinely unchanged; new
objects, changed geometry and new contacts remain failures. A preserved
zone outline/UUID never grandfathers a changed fill.

This is an independent acceptance comparison, not a native rule exemption
or proof of cloud enforcement. Reconcile the complete native input findings,
including footprint-level findings outside a pad/track screen, before
submission. Use the first meaningful returned layout to evaluate the
remaining importer/router behavior rather than creating an endless series
of zero-work controls. Prefer already-qualified conservative rectangles
over a new curved-geometry implementation when their extra blocked area
and affected existing objects can be explicitly accepted; smaller voids
are an optimization, not automatically a prerequisite.
The [native rectangle decision](measurements/2026-09-27-router-bakeoff/quilter-native-guard-encoding-2026-10-04.json)
accepts eight explicit overcoverage relationships without changing copper.
Its one-off measurement is not a reusable-validator qualification:
declarative controls are not executed negative tests, and printed expected
layer order is not parsed evidence. Reuse independently bound facts where
valid; preserve the missing controls as requirements for the full-input
validator rather than reporting them as passes.

**Observed layer-expansion control:** the
[private-plane experiment](measurements/2026-09-27-router-bakeoff/quilter-private-plane-control-2026-10-04.json)
keeps both private vias0.25mm from saved inner fills in four- and six-layer
fixtures; omitting one new inner guard creates actual copper contact.
Extend through-via protection to every newly enabled conductive layer,
then challenge one deliberately omitted guard. Measure saved full polygons
with holes against whole copper shapes. A local filled witness under an
F-only guard checks nonprojection without needlessly voiding entire planes.
Use a separate anchor to reject empty-fill false successes, but distinguish
anchor-via contact from a terminal-connected functional ground network.
Verify actual serialized layer mapping and per-UUID preservation rather
than trusting a printed expected-order list or unchanged object counts.
These rectangle-fixture observations do not establish curved-rule fidelity,
product grounding, supplier layer roles or importer behavior.

Do not flatten elevated or moving contact geometry into an unjustified
full-height rectangle, or assume that permitting contact pads makes every
track beneath the metal safe. The retained-feed/blanket-guard contradiction
in our diagnostic is intentional test evidence, not a clean product rule.

## 3. Resolve a capability uncertainty with the smallest useful experiment

Reuse qualified evidence when its inputs and assumptions are unchanged.
Do not build another tiny fixture for every job. When an untested behavior
could invalidate the larger workflow, use a bounded isolated control:

1. Name the behavior and a measurable pass/fail condition.
2. Include real routing work, an easy reference connection and a known
   legal path for the constrained connection. Keep proof paths out of the
   uploaded copper.
3. Exercise the relevant failure condition in the local checker. If the
   output takes a different layer, report what it actually exercised.
4. Qualify the saved file and importer representation before submission.

Keep a tiny diagnostic separate from the product-board project: the
[documented project policy](https://docs.quilter.ai/using-quilter/start-a-project.md)
requires later inputs to stay within 10% of the initial pin/component/
footprint/BOM profile. Include the intended terminals before the first
upload; do not assume a substantial fixture expansion is a valid iteration.

## 4. Review the imported model and actual saved settings

Upload only the approved design-file whitelist; never include personal
preferences, credentials, browser state or unrelated reports. Check:

- **Population and work:** fitted references, physical pads/nets, components
  to place and pins to route. Pins-to-route is not native open-count.
- **Placement and geometry:** fixed poses, side restrictions, region
  assignments, keepout polygons/flags/layers and protected process seeds.
- **Stackup and rules:** actual saved width, clearance, via size/drill,
  board margin, layer classes and preserved-pour/inner-copper behavior.
- **Circuit comprehension:** actual capacitor/pin associations, currents,
  impedances, ground identity and switching topology, not plausible-looking
  inferred labels. Never relabel a boost circuit to fit an unsupported model.
  Verify AI-generated datasheet summaries against the actual dated primary
  document too. Our COUT study's search summary invented routing restrictions
  absent from the cited TI layout section. Conversely, no stated numerical
  limit does not mean unrestricted routing or replace project insulation rules.

Read expanded values, not profile names. In our control, the display kept
"6 mil / 6 mil" and rounded width to 0.178 mm while the saved value was
0.1778 mm. Its 0.600/0.300 mm via minima and 0.508 mm margin were
**diagnostic choices**, not permission to replace product manufacturing rules.

Check coupled fabrication limits, not just each field separately:
`via diameter >= drill + 2 * minimum annular ring`. Our proposed new-via
lower bounds 0.604/0.350 mm imply 0.127 mm rings; a 0.150 mm ring rule
requires at least 0.650 mm diameter at that drill. Preserved ordinary vias,
new vias and mandatory filled/capped seeds may need different dispositions.
Do not silently grow a protected seed or lower a global rule to hide this
conflict; obtain a compatible process/rule contract and recheck geometry.

Four enabled copper layers do not establish a physical stackup. The
[pre-routed-trace documentation](https://docs.quilter.ai/design-parameters/pre-routed-traces.md)
describes fixed in-outline traces/vias but warns about inner-copper
replacement when the input stackup is not preserved. Review the selected
mode and returned planes; preservation checkboxes alone are insufficient.

Keep different importer features distinct. The KiCad job's ECAD constraint
table warned that parsing supported Altium only, while its geometric
keepout metadata did contain eight B track/via/pour exclusions. Neither
message alone settles complete constraint fidelity.

Authenticated Playwright UI operation is exercised. No public documented
API/SDK/CLI was found in our search; that is not proof that none exists.
Prefer the supported UI workflow rather than depending on private submit
endpoints. Already-fetched response values can clarify rounded settings;
keep raw browser evidence local and ignored, and do not collect account
responses merely to search for pricing.

## 5. Authorize once, then evaluate native output before acceptance

Confirm project eligibility, permitted data use and the exact submission
scope. [Published free-personal terms](https://www.quilter.ai/free-ai-pcb-design),
an account's Free Tier notice and an explicit price quote are different
evidence. Our account's Free Tier notice appeared at **download**, not
final submission. Absence of a price is not a zero-price quote: the owner
explicitly authorized that one policy-based start. Do not generalize it
into standing paid-use or unrestricted submission permission.

Free-use disclosures include using inputs/metadata for training puzzles.
Sanitized public-design upload approval does not authorize confidential
uploads or settle output-redistribution rights. Recheck current terms when
use changes, retain [attribution boundaries](../ATTRIBUTION.md), and stop
at a payment, upgrade or new agreement requiring owner action.

Record one confirmed launch and its job/configuration identifiers. Do not
duplicate a job because completion is slow or silently create monitoring.
Preserve raw complete-board archives and extract separate candidates safely.

Assess in this order:

1. **Preservation:** compare native component/pad/net identities and poses,
   retained trace/via geometry, guards, outline, layer enablement and rules.
   Normalize only demonstrated serialization differences. Changed display
   names are not missing layers; unmatched segments require separate
   connectivity analysis before claiming lost connections.
2. **Added routing:** establish actual connected copper, shorts, trace
   widths, whole-stroke/annulus clearances, layer transitions, return paths
   and plane isolation. Check new saved fills against foreign-net vias.
3. **Native and engineering gates:** run the applicable native checks,
   distinguish inherited/new/configuration-dependent findings, and complete
   electrical, process and assembly review. A static trace screen does not
   cover inner-plane isolation or replace these gates.

**Observed diagnostic limit:** a connected GND plane can still be a floating
network. In this deliberately truncated fixture, each saved inner fill is
one island attached to all five GND vias, but there are no GND component
pads. The isolated-copper warnings remain valid and are explained by that
missing terminal context, not waived or evidence of battery-net shorts.
Measure actual filled polygons against full foreign-via copper/barrels;
zone outlines and zero-open counts cannot prove isolation. Our minimum
saved clearance is 0.206229 mm against 0.20 mm, only 0.006229 mm spare:
this is a nominal exact-file check, not fabrication tolerance or powered
protection evidence. A future refill must be qualified separately.
See the [saved-plane evidence](measurements/2026-09-27-router-bakeoff/quilter-contact-plane-isolation-2026-10-04.json).

Classify results as **retain with a finite gap**, **reject for a demonstrated
contract violation**, or **accept for a specifically stated scope**. Preserve
useful candidates while fixing a local validation problem. Do not rerun
Quilter to cure a checker timeout, or automatically repair/merge an output.

## 6. Spend effort on discriminating comparisons

Set an **overall preparation budget and a go/no-go deliverable** before
starting local qualification tasks. Per-item time limits do not control
the accumulated cost of many successful or repaired items. Count scope
definition, root review, handoff and tooling corrections as preparation,
not just subprocess runtime. Stop a dependency chain that exceeds the
experiment's expected learning value rather than renewing it by default.

Separate input truth, submitted configuration, observed router behavior
and hardware release. Define indispensable restrictions and output
acceptance criteria up front, but test actual new routing, reference
continuity and final placement on returned candidates. Do not require
proof of an unrun outcome before starting a disposable experiment.
Conversely, output review is not an excuse to submit missing or knowingly
misrepresented essential input constraints. The
[October5 stage table](quilter-workflow-study-2026-10-02.md#october-5-budgeted-path-to-a-useful-experiment)
records this distinction for the handbell comparison.

**Selected study practice, not yet routed:** choose layer purposes from
the actual dielectric adjacency, not the layer count. Our
[3313 profiles](measurements/2026-09-27-router-bakeoff/quilter-four-six-role-selection-2026-10-04.json)
use S/G/S/S versus S/G/S/G/G/S: six layers improve reference availability
without adding two signal layers. A nearby mixed-use layer is not
automatically a continuous return plane. Keep electrical roles, native
layer identities/types and service-detected purposes distinct and reconcile
all three during import.

Check supported physics targets before staging, but distinguish documentation,
client entry, backend solving and returned routing. **Documented:** Quilter
lists85/100-ohm choices. **Observed in the current client implementation:**
the impedance field uses numeric text entry with positive-value validation;
the independent single-ended target can be blank. Thus the old documentation
does not establish frontend impossibility for our90-ohm intent. Actual
editable-draft persistence and90-ohm solving are still unverified. Keep the
requirement, prepare the qualified stackup, and test that exact input at
preview; do not create a circular dependency or duplicate a job merely to
probe a selector. See the [capability disposition](measurements/2026-09-27-router-bakeoff/quilter-usb-impedance-capability-2026-10-04.json).

Inspect achieved per-layer values and current solve status, not just the
target label or a green aggregate. The old job displays100-ohm calculations
with different reported single-ended values; do not invent an independent
single-ended requirement by halving the differential target. Its layer named
"Ground Layer 2" is classified copper-signal, reinforcing the need to inspect
actual roles. Neither those old computations nor a manual width/gap override
qualifies a new90-ohm result. Frequency/material assumptions and any tolerance
need an explicit basis; bit rate alone is not a carrier-frequency specification.

**Observed process-screen lesson:** the
[13-by97 source screen](measurements/2026-09-27-router-bakeoff/quilter-retained-via-pad-process-screen-2026-10-04.json)
proves positive separation from fixed lands without a new generic curved
geometry engine. It does not qualify solder-mask dams, tenting or assembly,
or protect against future moved pads. Distinguish existing immutable via
families from new-route minima: raising a global annular minimum can reject
retained processed seeds, while lowering it can underconstrain new vias.
Use explicit retained-versus-new checks, never silent resizing or exemptions
that extend to changed objects.

Use one qualified packaging envelope and comparable BOM, interfaces,
electrical and manufacturing requirements for a four-/six-layer comparison.
Use real supplier stackups and let approved placement adapt; this compares
complete workflows, not layer count alone. Add eight layers only for a
specific unresolved question, not as an automatic factorial experiment.

**Proposed comparison gates, not completed handbell qualifications:**

| Gate | Evidence required before advancing |
|---|---|
| Source and retained-circuit definition | Exact common BOM/pad identities, retained copper, fixed interfaces and explicit rerouting/restoration duties. |
| Geometric truth and constraint definition | Independent native-coordinate witnesses; full-shape placement, contact/access and private-path coverage on applicable layers. A same-net bypass cannot be dismissed as electrically equivalent. |
| Two manufacturable stackups | Real supplier constructions, explicit signal/reference roles, compatible ordinary and filled/capped vias, and stackup-specific impedance geometry. |
| Native encoding and importer behavior | Round-trip identities/geometry, expected native rule behavior, imported movable population, region assignments and saved settings. Unsupported duties need a reviewed disposition. |
| Comparable execution and output review | Individually authorized jobs from qualified packages; identical acceptance criteria, preserved raw outputs and an account of effort, failures and manufacturing implications. |

These are release dependencies, not a ban on parallel bounded investigation:
supplier-stackup and movable-domain evidence can advance independently.
Each native input still needs all applicable prerequisites before release.

Share requirements rather than forcing byte-identical layer-dependent
geometry: use the same packaging envelope, population, retained circuitry,
functional duties, minimum clearances and process requirements. Allow
placement, signal-layer assignments, reference adjacency and impedance
dimensions to adapt to each real stackup, documenting those differences.
Otherwise a supposedly controlled comparison can accidentally handicap
one construction or weaken its requirements.

Prepare both packages against the same common specification before
launching either. Parallel jobs are useful only after both independently
pass their gates; launching an unqualified second case creates more
results, not a better comparison. Treat routing completeness, critical
transitions/returns, root defects and total preparation/review/process cost
as outcomes, with preservation and safety requirements as acceptance gates.
Do not promise a comparison date merely because one tooling blocker clears.

Track setup effort, agent/owner interventions, validation effort, time to
first/final result, actual service charges and manufacturing implications.
Compare root defects and native outcomes, not only percent routed or
repeated DRC witnesses. Extra layers can alter special-process cost; obtain
an actual quote rather than assuming either four or six layers is cheaper.
Do not infer internal compute or token cost from elapsed wall time.

**Observed construction distinction:** the [3313 source screen](measurements/2026-09-27-router-bakeoff/quilter-four-six-stackup-source-screen-2026-10-04.json)
binds actual dielectric/copper rows for the shortlisted four/six-layer
constructions, not just nominal thickness or layer count. Both outer
dielectrics are0.0994mm; six layers also have a thin central gap between
two potential routing layers. Choose explicit reference purposes before
counting useful signal layers. The earlier saved generic Quilter4-layer
preset has different dielectric dimensions and is not an equivalent model.
Quilter documents input-defined stackups and ground/power naming hints;
verify the detected classes, material values and returned stackup rather
than trusting a supplier label or layer name.

Separate a supplier's dimensional capability, process conditions, order
eligibility and price. Both protected via families meet the cited POFV
hole/ring ranges, but that does not settle nearby-hole clearance or cap
planarity. Preserve ambiguous diagram/quality wording for disposition
instead of inventing tolerances or converting an advertised maximum into
a guaranteed minimum.

For hole-process screens, inventory every physical drilled pad, including
unfitted parts, alignment holes, slots and mounts; do not use a fitted-BOM
filter. Reuse saved native global centers and bound whole holes/copper,
including offsets. A conservative enclosing-shape clearance above the
threshold can establish nominal separation; one below it is inconclusive
until exact geometry is examined. Keep an ambiguous supplier measurement
boundary and via process classification separate from the geometric result.
The [process-hole screen](measurements/2026-09-27-router-bakeoff/quilter-process-hole-spacing-screen-2026-10-04.json)
exercises this method on40 component-pad and65 other-via pairs, but only
for its bound source coordinates; new placement/routing invalidates reuse.

Keep local items within the [bounded execution policy](routing-agent-policy.md).
Use hard subprocess termination limits, not just initial output waits.
Apply the same rule to static analyzers: the fast process-hole run completed
successfully, but its90-second initial wait did not enforce the required
limit. Preserve that noncompliance explicitly; neither a short duration nor
a later report-only amendment retroactively supplies a supervisor receipt.
Persist executable/arguments, input/tool hashes, stdout/stderr and exit or
timeout metadata **before and throughout execution**, including failure.
Our two initial output DRC timeouts lacked preserved streams, so their exact
stage could not be diagnosed. The subsequent logged runs completed on
unchanged returned bytes/settings in 42.219 and 3.844 seconds; their success
does not identify the old timeout cause. Do not repeat an opaque invocation
or count a timeout as a board failure. Reuse unchanged evidence and qualify
a new binding/parser operation in a small control before expensive downstream work.

**Observed native-tool trap:** both successful DRC processes exited zero
while reporting 45 findings. Parse the report (or deliberately configure
the supported violation-exit option); process success is not a clean-board
result. Compare rule context as well as geometry: the returned project
introduced a 0.15 mm annular-ring minimum that flags four unchanged 0.127 mm
rings. Never resize preserved copper or suppress checks merely to make
different rule contexts appear equivalent. See the
[native recovery evidence](measurements/2026-09-27-router-bakeoff/quilter-contact-native-validation-2026-10-04.json).

**Repeated tooling failure, October 4:** a reused helper is not qualified
merely because it worked against an older board/API. Preflight the exact
Python/pcbnew ABI and separate track/via serialization: KiCad10 vias require
an explicit layer for `GetWidth`, while the exercised track binding does
not accept that argument. Test both object types before a whole-board
analysis; do not blanket-replace calls or suppress a desktop assertion.
The [retention inventory](measurements/2026-09-27-router-bakeoff/quilter-critical-block-retention-2026-10-04.json)
exhausted three attempts on these binding errors without qualifying a
retained block. Its incomplete result is not evidence against Quilter.
The separately authorized [recovery](measurements/2026-09-27-router-bakeoff/quilter-critical-block-retention-recovery-2026-10-04.json)
passes the type-specific tests and completes one native load in1.842s.
Preflight the complete logging runner too, not only helper functions.
Exercise zero exit, deliberate nonzero exit and timeout capture. A final
`ok` marker, empty stderr and an exited PID do not establish a numeric exit
code; keep a missing code explicit rather than synthesizing success.
Keep timeout status separate from the killed child's platform-dependent
code. Our qualified Windows control records child1 and supervisor124,
not a POSIX-style negative signal code; see the
[runner evidence](measurements/2026-09-27-router-bakeoff/quilter-critical-ground-input-interfaces-2026-10-04.json).
Compile each changed analyzer revision before launching native work; a
later caching edit introduced a syntax failure despite the earlier preflight.

**Observed bootstrap recurrence:** the [private native control](measurements/2026-09-27-router-bakeoff/quilter-private-guard-native-control-2026-10-04.json)
again lost module and DLL search paths in fresh children. Reuse the complete
qualified launcher, not just its Python executable or a prior shell's
environment. Keep the object returned by `os.add_dll_directory` alive
through the native scope, then close it explicitly.
The later [F-room control](measurements/2026-09-27-router-bakeoff/quilter-f-placement-region-native-control-2026-10-04.json)
still consumed two attempts before importing pcbnew: absolute Python alone
did not supply the module path. In the exercised Windows installation,
`KiCad\10.0\bin` is the DLL directory and
`KiCad\10.0\bin\Lib\site-packages` is the Python module directory; one is
not a substitute for the other. Reuse both explicit paths in the child,
checking their existence before native work. Count a started Python child
that fails import as a child failure, not a launcher failure or board load.
Snapshot each executed script before editing it: matching recovered bytes
to an earlier receipt hash can repair evidence loss, but is not a
pre-execution snapshot and should not become the normal workflow.
In that same execution
environment, preflight a known pad UUID
and required getters before running the larger control. Missing identity
readback must stop qualification; successful file I/O and a populated board
are not a substitute. Preserve bounded DRC timeout evidence and diagnose
its stage before increasing limits or rerunning the same command.

Qualify the reusable runner separately from one successful native result.
Reject reused output locations; require a successful child exit and a fresh,
parsed report with the expected schema, not merely an existing filename.
Write each child invocation/PID before waiting so an outer timeout leaves
useful evidence. Process-tree supervision must contain the child before it
can spawn descendants. Regression controls must cover these failure paths,
not just the happy path. Bind every result to the exact executed tool
revision; later fixes do not retroactively qualify an earlier run.
The [initial repair](measurements/2026-09-27-router-bakeoff/quilter-native-tool-repair-2026-10-04.json)
recovered observations but did not qualify its final changed code.
The subsequent [completion](measurements/2026-09-27-router-bakeoff/quilter-native-tool-completion-2026-10-04.json)
binds ten supervised regressions and an actual corrected-revision replay:
identical native readback and a DRC report differing only in date.
Use `tools/supervise_process.py` for the exercised64-bit Windows runner;
`tools/inspect_native_guard_fixture.py` is deliberately bound to this exact
diagnostic fixture/project, not a general product-board validator.
Invoke with absolute executable/script paths and separate new receipt/
payload locations; relative scripts resolve under the child working
directory. The ledger records the actual argument array.

Save actual starting and executed tool/report copies before edits, verify
their hashes against the invocation, and then update acceptance separately.
A hash alone records identity but does not preserve a retrievable revision.
The completion demonstrates this practice; the earlier repair's missing
standalone copies remain a documented provenance limitation.

**Observed selection trap:** the recovered all-pairs graph added113 objects
beyond a62-object explicit-duty core. A path between two internal pads can
wander through the larger board. Retain copper for named electrical duties;
inspect boundary dependencies without automatically fixing every encountered
component. Group graph edges by true external connection and distinguish
layer-specific witnesses from unrestricted connectivity. A successful
inventory is not an approved retained block.

**Observed subgraph trap:** retained copper includes retained pad lands,
not only trace/via UUIDs and the two query endpoints. Excluding intermediate
U6.4 pad copper falsely broke the R28 witness; the saved native path
resolved it without adding copper or rerunning KiCad. Recompute boundaries
when reducing a selection: edges internal to the old union may become
external. Build the effective retention union first, including independently
protected process vias as well as the named copper set and retained pads.
Removing a misclassified seed from a report count does not repair the
already-computed component geometry. Count separated electrical duties, not all lost pad-pair
combinations. See the [corrected core review](measurements/2026-09-27-router-bakeoff/quilter-critical-core-boundaries-2026-10-04.json).

**Observed protection limit:** the source's 19 areas prohibit pours, not
new same-net tracks/vias. Saved-plane isolation is not future routing
protection. Rule names and absence of same-layer contacts also cannot
prove that an inner-layer exclusion covers an outer-layer circuit's XY
projection; qualify that projection and every relevant new layer explicitly.

**Observed attachment-screen limit:** subtract the actual candidate when
labeling copper unselected, not one duty's path tree. Distinguish pads
outside that duty from pads outside the retained footprint set. Two
attachment UUIDs may represent a pad and track at one physical junction;
they do not prove a distinct parallel current path. Use such screens to
direct geometry review, not to manufacture defect counts or freeze whole
external networks. Classify each module's interface separately: a global
feed legitimately reaches several destination terminals. Requiring its
entire network to touch only one land is not a useful local-cut test.

**Proposed bounded takeoff practice:** if a source feeder overlaps the
protected local bus, consider retaining that complete existing primitive
to its next real boundary instead of clipping it or freezing its whole
downstream network. Make the extent/placement tradeoff explicit and keep
downstream restoration duties separate from fixed geometric ports. The
handbell's two VAMP takeoffs and one GND feeder are a planning selection
only; this input has not been exercised in Quilter. Numerous downstream
contacts along one retained feeder do not make each old coordinate a
mandatory port or require preserving the entire global network.

**Observed physical-check limit:** a connectivity witness omitted a
1.2 mm source BOOST_SW track that contributes real copper beyond the
selected shapes. Complete-local-net inventory recovered it without new
routing. Exact polygon work also needs explicit edge/corner-tangency and
native contact-tolerance controls: an empty Boolean intersection is not
proof that no graph contact exists. Cache native shapes and narrow pair
tests conservatively by net/layer/bounds, but use actual geometry for the
decision. The [bounded physical review](measurements/2026-09-27-router-bakeoff/quilter-critical-physical-attachments-2026-10-04.json)
retains partial evidence after three attempts; no fourth retry follows
merely because the overall owner time window has time remaining.

**Documented cost distinction:** current JLCPCB pages separate via sizing
from component-PTH annular rules and advertise filled/capped via-in-pad at
no additional charge for6+ layers. Their headline board promotion is not
a quote for our assembly. Compare the same required process on both layer
counts, rather than dropping filled/capped seeds to make four layers look
cheaper. See the [public-source screen](quilter-workflow-study-2026-10-02.md#independent-public-supplier-screen).

## Keep the guidelines alive

At each meaningful checkpoint, update the existing run ledger with the
question, controlled changes, input/configuration/output identities,
expected versus observed behavior, timing/effort, acceptance limits and
one next decision. Put raw detail there, not in this guide.

When a result changes how we should work, update the relevant rule here:
state the practice, link its evidence and retain its applicability limits.
Mark it observed, documented or proposed. If new evidence contradicts a
rule, revise that rule and link the counterexample rather than appending
another conflicting "latest" instruction. Do not invent a new rule when
the experiment only confirms an existing one.

The current evidence still leaves **movable F-only placement, full-board
placement/access and circuit comprehension, product process rules, and four-/six-layer
benefit** unresolved. Track their disposition in the closure plan; do not
promote them to proven capabilities through repetition in progress reports.
