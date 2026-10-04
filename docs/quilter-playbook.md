# Quilter playbook: an agent-assisted layout workflow

Use this guide to prepare useful jobs and evaluate their results without
relearning every experiment. Optimize for an acceptable board with bounded
owner/agent effort, not trace aesthetics or recovery of sunk costs.

Evidence reviewed through **October 3, 2026**: Quilter UI 1.40.0/API 1.40.1
and KiCad 10.0.6. This is a living procedure, not a platform guarantee.
The [workflow study](quilter-workflow-study-2026-10-02.md) retains the dated
reasoning; its linked ledgers bind exact files and results. The
[closure plan](pcb-closure-plan.md#owner-pause-and-next-item) controls current
authorization and blockers. This guide does not release another job,
native-tool retry, source edit, purchase or fabrication.

## What the evidence supports

| Finding | Evidence and limit | Working guideline |
|---|---|---|
| Selected existing routing can survive while Quilter adds useful routes. | Both [contact-control outputs](measurements/2026-09-27-router-bakeoff/quilter-contact-routing-output-review-2026-10-03.json) preserve the checked inventory and connect both test pairs on B without new vias. Native DRC and inner-plane isolation remain incomplete. | Retain reviewed critical blocks where useful; independently verify preservation and new copper. Do not equate this small control with full-board qualification. |
| Preservation is not automatic for every input/configuration. | Earlier [full-board outputs](measurements/2026-09-27-router-bakeoff/quilter-output-preservation-2026-10-02.json) lacked the original inner GND zone and exact matches for 24 In2 segments. That did not prove 24 lost electrical connections. | Inspect returned copper and planes before ranking routing improvement. Distinguish record changes from connectivity loss. |
| Import recognition is weaker than routing evidence. | The [first contact preview](measurements/2026-09-27-router-bakeoff/quilter-contact-feed-import-2026-10-03.json) had zero pins to route. The later control had actual unrouted pairs and legal-path witnesses. | Submit a diagnostic only when it can exercise the behavior in question; a parsed preview alone is not that experiment. |
| A green dashboard has a limited scope. | The contact job's one physics pass was an inferred VBAT 500 mA check; its new-violation lists were empty. Local output DRC did not finish. | Record which checks ran, their assumptions and whether they cover inherited or new findings. Do not translate "100%" into engineering acceptance. |
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

## 2. Build a source-bound input contract

Keep the authoritative board and raw experiments immutable. Record the
exact PCB/project/schematic/manifest hashes, reference and physical-pad
counts, net identities, fixed/movable references, protected copper/vias,
outline, layer roles, physical stackup and applicable process requirements.
Use native poses, including footprint rotation, rather than stale proxies.

Define each movable part's final allowed area from the intersection of
its side, height, access and electrical restrictions. Quilter's
[documented region behavior](https://docs.quilter.ai/guides/placement-guide)
combines assigned regions by **union**, not intersection. A broad F region
plus a narrow height region can therefore enlarge, rather than restrict,
the allowed space. Verify assignments and F-only behavior after import;
a single-sided preference or candidate filter is not proof of enforcement.

Keep placement regions separate from safety keepouts. Inspect each
keepout's actual track/via/pour flags and layers; a suggestive name is not
a rule. Screen full copper shapes, including the B annulus of through-vias.
Filling or tenting a via does not remove its conductive rear land.

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

Read expanded values, not profile names. In our control, the display kept
"6 mil / 6 mil" and rounded width to 0.178 mm while the saved value was
0.1778 mm. Its 0.600/0.300 mm via minima and 0.508 mm margin were
**diagnostic choices**, not permission to replace product manufacturing rules.

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

Classify results as **retain with a finite gap**, **reject for a demonstrated
contract violation**, or **accept for a specifically stated scope**. Preserve
useful candidates while fixing a local validation problem. Do not rerun
Quilter to cure a checker timeout, or automatically repair/merge an output.

## 6. Spend effort on discriminating comparisons

Use one qualified packaging envelope and comparable BOM, interfaces,
electrical and manufacturing requirements for a four-/six-layer comparison.
Use real supplier stackups and let approved placement adapt; this compares
complete workflows, not layer count alone. Add eight layers only for a
specific unresolved question, not as an automatic factorial experiment.

Track setup effort, agent/owner interventions, validation effort, time to
first/final result, actual service charges and manufacturing implications.
Compare root defects and native outcomes, not only percent routed or
repeated DRC witnesses. Extra layers can alter special-process cost; obtain
an actual quote rather than assuming either four or six layers is cheaper.
Do not infer internal compute or token cost from elapsed wall time.

Keep local items within the [bounded execution policy](routing-agent-policy.md).
Use hard subprocess termination limits, not just initial output waits.
Persist executable/arguments, input/tool hashes, stdout/stderr and exit or
timeout metadata **before and throughout execution**, including failure.
Our two output DRC timeouts lacked preserved streams, so their exact stage
could not be diagnosed. Do not repeat an opaque invocation or count a
timeout as a board failure. Reuse unchanged evidence and qualify a new
binding/parser operation in a small control before expensive downstream work.

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

The current evidence still leaves **native output DRC/inner-plane isolation,
movable F-only placement, full-board comprehension and four-/six-layer
benefit** unresolved. Track their disposition in the closure plan; do not
promote them to proven capabilities through repetition in progress reports.
