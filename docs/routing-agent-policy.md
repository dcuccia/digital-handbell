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

Keep any necessary special process explicit in the generic fabrication
notes and quotation options, independent of a vendor promotion. Preserve
manufacturer MPNs and a fab-neutral native/Gerber/drill master; supplier BOM
and placement conventions remain separate exports. Existing tall-contact,
USB-anchor, sourcing and full-PCBA gates still apply.

### Batches, not one-net conversations

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
