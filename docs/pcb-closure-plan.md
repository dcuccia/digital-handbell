# Cost-aware PCB closure plan

Owner-approved September 14, 2026. Target: a consistent **engineering-prototype
PCB + PCBA quotation package** for JLCPCB and PCBWay, not a perfected platform,
powered qualification, child-use release or permission to upload/order.

Tracking: [E04/#4](https://github.com/dcuccia/digital-handbell/issues/4),
[E05/#5](https://github.com/dcuccia/digital-handbell/issues/5),
[E07/#7](https://github.com/dcuccia/digital-handbell/issues/7) and
[E08/#8](https://github.com/dcuccia/digital-handbell/issues/8).

## One active candidate, preserved history

Continue in `hardware/handbell/iterations/printed-bell-clock-draft`.
Starting accepted PCB SHA-256:
`0c81f57fd3046248448d778230800849527c8a8ecaf501454314c82fffbe8db0`.
The local clock is routed; 65/83 fitted parts have MPNs. There are 82 native
opens without cached ground fill. These are starting facts, not a permanent
progress counter. Older variants, successful print snapshots and the
cancelled agent's untracked recovery package remain preserved.

The generic refill trial has 58 opens, but separates C25.2 from a previously
connected group. Its 21 lost pairwise relationships describe **one separated
pad**, not 21 independent faults. Keep the trial as a provisional repair
candidate. The recorded-settings replay exists but its full check timed out;
neither trial is accepted. C25 is 10 nF on BUTTON/GND. First establish its
actual continuity, then consider a local ground link or small move rather
than discarding the whole fill. Preserve the filter and correct return.

## Sequence and milestone gates

**First closure result:** the recorded-settings replay now restores C25
without a move and preserves both prior connectivity baselines and the
protected returns. Its [accepted report](../hardware/handbell/iterations/printed-bell-clock-draft/reports/front-ground-acceptance.json)
binds the current filled board: **57 opens**, with unchanged physical findings.
The starting facts and rejected trial above remain historical evidence.
The standalone refill recipe reproduces the accepted cache from the unfilled
source; geometry changes still require a new refill and review.

**USB closure result:** the authorized X6 pattern and local CC/VBUS repairs are
now applied, with 57 opens and zero native DRC errors. The four slot commands,
unchanged pin mapping and preserved connected groups are source-bound in the
[USB report](../hardware/handbell/iterations/printed-bell-clock-draft/reports/usb-geometry.json).
MPN coverage is 66/83. Remaining warnings, power geometry, supplier soldering
and full CAD/bezel integration are still open.

**Identity closure result:** one final device/power batch completes **83/83
matching fitted MPNs** across schematic, PCB and manifest, with geometry and
copper unchanged. The [complete-identity schematic](../hardware/handbell/iterations/printed-bell-clock-draft/reports/identified-schematic.pdf)
is available for novice review. Blank fields are closed; land/paste, envelope,
existing-part audit and supplier/assembly qualification are not.

1. **Geometry decisions, then necessary corrections.** Dispose of remaining
   package/land/paste/envelope questions once, using existing source evidence.
   Correct actual terminal, pin-map, clearance and assembly problems before
   final routing. Batch remaining identities; do not re-research settled
   parts. Record exceptions rather than automatically copying every example
   footprint or treating differences as approved.
2. **Critical connections, then remaining signals.** Preserve the ground
   strategy and private returns; finish core/power, constrained USB/audio,
   then controls. Allow economical local passive/test-pad moves while keeping
   D43, mount, USB and contact datums. No automatic outline growth.
3. **Final ground and electrical closure.** Refill after signal geometry
   stabilizes. Prove complete intended connectivity, no cross-net shorts,
   preserved private pickoffs and contact exclusions. Native DRC plus the
   essential independent checks remain gates; a smaller airwire count alone
   is insufficient.
4. **One coordinated handoff.** Complete manufacturing/silkscreen cleanup,
   rebind the exact final board/manifest into full CAD, then produce matched
   schematic, Gerber/drill, BOM, placement and assembly/process assets.
   Include both rear contacts and mixed-mount X6. Keep powered and supplier
   qualification limits explicit.

## First-pass geometry decision ledger

This is a triage, **not a claim that geometry is frozen**. "Review" means an
unresolved disposition; it is not permission to fabricate unchanged.

| Scope | Disposition for the next passes | Closure evidence |
|---|---|---|
| Y1/C2/C3/R6; Q3 | Retain accepted clock geometry/copper and corrected Q3 lands. Do not reopen their selections. | Current clock and Q3 reports; final mechanical bind still required. |
| X6 USB | Native correction applied, including local CC/VBUS repairs. Retain the new lands and datum. | [Source-bound native result](usb-connector-qualification.md#current-native-implementation); supplier process and mechanical acceptance remain open. |
| L1, C26-C28, C1/C4/C5/C19/C20, FB1/FB2 | Applied: four dedicated patterns across eleven references; no part moves or copper-primitive changes. | [Power selection](power-component-selection.md); actual connectivity/private pickoffs preserved and adjacent primitive exposure remeasured. Current and supplier qualification remain open. |
| CHG0/L0, D3/D4, U2, U4 | Retain current native copper for routing; preserve polarity/pin maps. U4 quotation baseline specifies filled/capped thermal vias, not ordinary tenting. | [Explicit retain/process dispositions](device-component-selection.md#september-15-remaining-land-and-assembly-dispositions); supplier two-layer capability, price and stencil acceptance remain open. |
| D3/D4, Q1/Q2/Q4, U3 | Applied September 15; current centers, rotations and native-to-proxy offsets preserved. No new proxy overlaps or outline/speaker screen conflicts. | `reports/device-envelopes.json`; full-CAD and physical fit remain open. |
| U5, R27 | Applied the recorded TI/Panasonic examples and conservative envelopes. One U5 escape correction and one matching R27.2 exclusion enlargement; no part moves or trace-width reductions. | `reports/power-device-lands.json`; preserved primitive/filled connectivity and private returns. Assembly/current qualification remains open. |
| Remaining connectors/contacts, U1/U6/Q5 | Retain documented current lands and fixed datums for routing; record fine-package/connector process questions. Contact upper-height tolerance needs coordinated mechanical work. | [Retain/process dispositions](device-component-selection.md#september-15-remaining-land-and-assembly-dispositions); no additional native land correction selected. |
| USB bezel | Carry the selected front bound and documented 0.15 mm outward bezel adjustment into the coordinated CAD revision. | Exact PCB/manifest bind; nominal clearance is not mating qualification. |
| Optional debug branches | Review for inline placement or deferral only if they reduce real routing work. No removals selected yet. | Explicit schematic/PCB agreement; preserve boot/reset/SWD, protection and necessary diagnostics. |
| Reference text | One late cleanup; polarity, chemistry and recovery labels are not optional. | Final manufacturing views and process limits. |

## Execution and cost controls

Use the bounded foreground, sequential-continuation and two-correction policy
in [AGENTS.md](../AGENTS.md). Name each region and stopping point before work;
target 10-15 minutes including reasoning and validation. Preserve an incomplete
candidate and its repair list if the item expires. Stop promptly when asked.

Reuse existing tools and concise reports. Do not create a routing framework or
consolidate historical scripts as a side project. Hidden metadata-only changes
need source/value/net/geometry invariants, not repeated unrelated copper work.
Perform local checks during edits and complete checks at milestone boundaries.
Connected-component comparison may replace equivalent pair enumeration, but
must detect missing pads and previously connected groups splitting.

A deterministic computation can be cheaper than repeated model-led microcycles.
Record stage timings when a check stalls, retain finite process deadlines, and
distinguish incomplete evidence from a design defect. Do not repeatedly run the
same failing whole-board check without a focused hypothesis.

The [September 15 routing-tool pilot](routing-tooling.md) records native-API
and numerical-screening lessons, pinned external tools and bounded failed
autorouting attempts. Freerouting is still experimental: no routed proposal
was promoted, and the accepted board remains unchanged. Do not repeat the
whole-board trials without a materially different, bounded hypothesis.

Escalate if closure requires changing fixed interfaces, major architecture,
unresolved protection/assembly conflicts, or repeated passes without measurable
progress. No remaining-dollar guarantee is made. Report progress as closed
functional groups and named remaining defects, not just counts or elapsed time.

## Reproducible filled-ground check

`tools/check_front_ground.py` and `tools/zone_graph.py` promote the exercised
filled-island and private-return checks without importing the private recovery
directory. `reports/front-ground-plan.json` in the active package contains the
one-F-zone/ten-exclusion contract and its source-plan hash. The promoted graph
functions/classes are AST-identical to the exercised implementation apart from
documentation. Existing island/hole/short checks are retained, with additional
component-comparison cases for merges, splits and missing pads/copper.

The checker is read-only and requires an already-filled previous baseline,
an exact candidate/manifest binding, the plan, and a **new** report output.
It compares connected groups, not every pad pair, and rejects shorts,
floating copper, changed pad/net identities, private-pickoff bypasses and
unexpected zone/exclusion plans. It does not run DRC or qualify assembly.
Use the separate source-preserving refill tool first when geometry changed.

Example from the repository root, reproducing the latest comparison against
the pre-corridor baseline in `70bfab3`:

```powershell
$work = Join-Path $env:TEMP ("handbell-ground-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $work | Out-Null
python -c "import subprocess; from pathlib import Path; p=Path(r'$work')/'baseline.kicad_pcb'; p.write_bytes(subprocess.run(['git','show','70bfab3:hardware/handbell/iterations/printed-bell-clock-draft/handbell.kicad_pcb'], check=True, capture_output=True, timeout=15).stdout)"
python -c "import subprocess; subprocess.run(['python', r'tools\check_front_ground.py', r'hardware\handbell\iterations\printed-bell-clock-draft\handbell.kicad_pcb', '--baseline', r'$work\baseline.kicad_pcb', '--plan', r'hardware\handbell\iterations\printed-bell-clock-draft\reports\front-ground-plan.json', '--require-connection', 'IC1.45', 'C8.1', '--require-connection', 'IC1.49', 'IC1.44', '--output', r'$work\ground-check.json'], check=True, timeout=360)"
```

KiCad 10.0.6 and its native Python API were exercised. The completed public run
used an initialized isolated `KICAD_CONFIG_HOME`; keep such preferences local.
Native graph runtime varies: two 180-second attempts expired, while the bounded
360-second run completed in about 165 seconds. Earlier same-purpose runs were
faster. No configuration or resource-contention cause is established. Stage and
CPU timings are recorded; do not turn a timeout into an unbounded retry.
The September 15 U5/R27 filled check completed in about 80 seconds with the
same 360-second deadline. Its plan enlarges only the existing R27.2 exclusion
to follow the larger land; it retains the 0.251 mm bounding margin and all ten
exclusions. Older reports remain bound to the older plan.

`tools/check_power_land_change.py` reuses the primitive graph, power-topology
and centerline-exposure methods for declared land/escape changes. It also
checks actual library agreement and unchanged component poses, via inventory
and track widths. The R27 exclusion-only correction reused the earlier
primitive proof and ERC after byte comparisons, rather than rerunning them;
`reports/power-device-local-reuse.json` records that limited reuse explicitly.

## Owner pause and next item

**September 21 subsequent owner approval:** migrate to four layers and have
pinned Sol agents execute efficient routing batches. Preserve the two-layer
source and create a separate `printed-bell-four-layer` baseline with unchanged
placement, interfaces and existing copper. The first gate is native layer
enablement plus source/geometry invariants; no new inner routing or planes
are accepted by that baseline alone. Next qualify all-layer tools and
release the protected-ground/return strategy. See the
[four-layer execution contract](routing-agent-policy.md#four-layer-migration-and-efficient-execution).
Prefer ordinary processes where equivalent; keep necessary filled/capped
vias until a reviewed alternative meets the same requirements. No supplier
upload, order or fabrication approval is included.

**Migration baseline accepted:** working package
`hardware/handbell/iterations/printed-bell-four-layer`, PCB SHA-256
`d91837ed9f5cff10d709521e448f6deae3aac3a52abed88c34271ee809e25418`.
Only native layer declarations changed; source bytes outside that node,
all existing geometry and component poses are preserved. No inner planes
or routes were added, so 51 opens remain. A serialization-only newline
correction was verified against raw bytes; the semantically identical
native report was reused explicitly, not rerun or represented as new routing
proof. Its newly enabled schematic-parity check reports 46 notices not
present in the differently configured historical report. Those need
disposition before release, not concealment inside an "all checks clean" claim.
Next item: qualify all-layer geometry/connectivity tools with a deterministic
cross-layer/via/plane control, then release the protected-ground strategy.

**September 21 conditional resume:** the owner requests Astra engineering
judgment with pinned Sol routine execution. See the
[routing-agent policy](routing-agent-policy.md) for exercised model gates,
critical-net reservations, preserved context and escalation rules. The
September 16 pause below is historical; no old retry budget is reset.

The required-model custom subagent and explicit Sol/medium compatibility
dispatch were exercised; direct CLI agent selection is not the fail-closed
path. Sol inventoried control-net conflicts, then performed native +3V3
branch-cut analysis and the final authorized F-only SCL correction. Removing
only the redundant fine-track pair in memory still produced no route
(2,793 expansions, 0.563 s). No accepted copper changed: still **51 opens**.
See the policy's linked source-bound reports. SCL's retry allowance is now
exhausted. The next item is **Astra's joint local IMU/pull-up supply,
SCL/SDA and return-corridor decision**, not another unconstrained route
search or removal of the required 0.25 mm supply branch.

The subsequent in-place R14 terminal-reversal screen also returned no
candidate; its limitations and executor scope deviation are preserved in
[the outcome](measurements/2026-09-21-r14-terminal-swap.json). No accepted PCB
or manifest bytes changed. Do not retry either trapped-pad strategy.
The next bounded engineering item is to evaluate **one R14 location beside
the existing SCL group**, jointly accounting for its supply connection,
native courtyard and local ground returns. No move is yet authorized.

**September 21 relocation screen:** Sol evaluated 936 fixed-lattice poses
in one read-only native batch. Eight passed the pad/body screen; the three
shortest-distance options still cross USBBOOT and/or IMU_INT2 on their direct
connections. Missing courtyards required body proxies and ground-fill effects
remain unreviewed. No position is approved and no PCB/manifest changed.
The [screen](measurements/2026-09-21-r14-relocation-screen.json) is not a
routability proof. Do not start another placement/search sweep.

### Layer-count reassessment requested September 21

Two layers were a defensible initial low-cost target for this circuit, not
an electrical requirement. The constraints evolved into D43, 81 front
electronic parts and two rear conductive battery contacts that reserve much
of the back routing area. We now have 51 opens, 18 of them ground, and
repeated local supply/signal conflicts. Earlier supply routing also split
ground groups. These are reasons to reconsider the architecture, not proof
that a skilled two-layer layout is impossible.

**Astra recommendation: prefer a four-layer engineering candidate before
more two-layer-only local repairs.** The principal benefit is a substantially
continuous protected-GND reference independent of most signal routing, plus
an internal routing/distribution layer. It is not two extra freely usable
signal layers. Preserve short local boost/decoupling loops; adding planes
does not correct bad placement or confer current/thermal qualification.

Three layers are not a useful purchasing compromise here: JLCPCB states
that it manufactures a three-layer submission as four layers. The
[Standard PCBA comparison](pcba-quotation-plan.md#september-21-layer-count-assessment)
records current official sources, fixed assembly fees and remaining
via-treatment, panel and tall-contact questions. No exact project price
or guaranteed engineering-time saving is established.

An initial role assignment to review against the supplier's actual stackup
is F/components and critical signals, In1/protected GND, In2/power and selected
lower-speed routing, B/remaining routing and contacts. Fast signals should
stay over an uninterrupted close reference; B routes cannot assume a
continuous reference if In2 is split. This is a study direction, not the
approved KiCad stackup.

Keep raw CELL_NEG isolated from protected GND, dedicated sense pickoffs
intact, and switching-node copper controlled. Buried copper may help cross
surface congestion, but an ordinary through-via still exposes a pad/barrel
on B: the battery-metal exclusions and insulation gates do not disappear.
Start with ordinary through-vias, not blind/buried vias or HDI.

Four layers can retain a single nominal 1.6 mm board and the same external
interfaces; they do not add assembly faces or mean stacked PCBs. Supplier
thickness tolerances, stackup/copper, via antipads and mechanical binding
still need review. USB geometry, filled/capped thermal vias, front/rear
assembly and actual part sourcing remain separate gates.

**At the time of this assessment no stackup migration was authorized.**
The subsequent owner approval above now authorizes a separate four-layer
candidate under the explicit migration gates, not an automatic plane fill.
Preserve the accepted two-layer package and reusable schematic, footprints,
MPNs, mechanics and topology reviews. A migration would use one separate
active candidate, revise native rules and plane/contact exclusions, review
which existing traces to retain, then rerun native connectivity/DRC,
independent supply/return checks and matched manufacturing/CAD binding.
Existing two-layer fill proofs would not qualify new internal planes.

**Paused September 16 at the owner's request.** Save and publish only;
do not continue engineering until explicitly resumed. The accepted board
remains the 51-open charge-indicator checkpoint `b2203c8`, with the hash
below. No SCL candidate was accepted and no supply branch was removed.

The unfinished `tools/route_scl_pullup.py` and existing-copper anchor support
are preserved as work in progress. Two bounded searches failed: R14.2 to
IC4.13, then to the existing SCL trunk at native (91.69, 92.7368). Both
exhausted the sampled component after 2,769 expansions, not the 80,000 cap.
The suspected enclosing 3V3 branches near R14 were inspected, but their
redundancy was **not established**. Do not remove them on that assumption.
See `reports/scl-pullup-attempt.json` in the active package.

The previously untracked `printed-bell-quote-candidate` is now preserved as
a historical recovery archive, not a replacement for the active board.
Machine-local KiCad preferences, locks and caches remain excluded.

**Resumed September 15 at the owner's explicit request**, following the
September 14 pause. Continue bounded sequential items; no background engineering
agent or routing loop was started.

Preserved two-layer package: `hardware/handbell/iterations/printed-bell-clock-draft`.
Preserved two-layer PCB SHA-256:
`a83cc417c96b05dd15c187e648b9fd2a35ba857c3a66f7d13aaaa42ae3bd9fff`.
Current native report: `reports/charge-led-routing.json`; prior six-envelope
revision: `reports/device-envelopes.json`; current public fill proof:
`reports/charge-led-routing-ground-check.json`. Status: **83/83 fitted MPNs, 51 opens,
zero other native DRC errors and 233 text/silk warnings**.

The six initial envelope corrections and subsequent U5/R27 corrections are
applied with no new screen conflicts or component moves. Twelve U5 segment
endpoints changed, with widths retained; R27's sense-return exclusion grew
with its land. Remaining copper dispositions are recorded as retained for
routing; the quote baseline names U4 filled/capped vias explicitly, without
claiming supplier acceptance or cost. The first core-decoupling link,
IC1.23 to C18.2, is now complete with one 0.15 mm 3V3 bend correction.

IC1.50/C6.2 is now connected after shortening QSPI_DATA[3] and moving the
C6/C17/C8/C13 column by +0.40/+0.32/+0.23/+0.14 mm in native Y. Courtyards,
trace widths, fixed interfaces and via inventory are preserved.

The next IC1.45/C8.1 trial was **not accepted**. Its proposed inner 3V3 bridge
intersects the existing VHI feed, and two residual lower 3V3 stubs approach
the proposed VCORE link. `reports/core-c8-attempt.json` records exact UUIDs,
the reproducible failed candidate and the two root defects. The considered
backside via location is inside the retained conductive BT1 base projection
and was not implemented.

**Corridor resolved:** the unchanged-width 0.80 mm VHI feed now uses the
central B neck, not the blocked contact-base area. All nine original MCU
ground vias and their drill/diameter are retained in a compact staggered
array; the 0.60 mm ground grid follows them. This frees the inner 3V3 bridge
and direct C8 regulator-output connection. Exact API geometry, three numerical
array screens and the existing native/independent gates supported the change;
no visual estimate or global autorouter supplied acceptance.

The moved via array needs stencil/via and thermal review; unchanged via count
does not prove unchanged thermal performance. No stackup change was made.
Next bounded item: the two remaining VCORE distribution connections between
the now-routed local decoupling groups. Two VCORE opens remain,
along with other power, signals and ground islands. No new sourcing by default.
Then follow constrained signals,
remaining controls and final ground closure in the sequence above.

The owner subsequently authorized a bounded automation pilot. It completed
without a usable routed result; [tooling lessons](routing-tooling.md) preserve
the settings and exchange limitations. Any further automation investment
must demonstrate one useful constrained proposal before widening scope;
it does not replace or reset the outstanding VCORE work.

A subsequent fixed-pad grid attempt also stopped at its retry limit, without
changing copper. Its [diagnosis](routing-tooling.md#subsequent-vcore-grid-attempt)
identifies an endpoint-selection limitation: C7.2 is already connected to
C8.1 and is reachable from C6's grid region. **Next: use C7.2 as the target
for the C6 group, then join C18 to the merged group.** Do not infer a need to
move parts or modify 3V3 from the failed C8-only search. Exact route acceptance
is still outstanding.

**C6/C7 follow-up stopped:** a generated F route split the local capacitor
ground group after refill. Both bounded ground-first corrections failed to
find VCORE paths. The [preserved supply/return attempt](routing-tooling.md#group-terminal-follow-up-preserve-supply-and-return-together)
is not accepted copper. This core-distribution item now needs a coordinated
corridor repair, not another unchanged-layout retry. Other independent
routing items may proceed under the owner's continued-work authorization.
The independent [GAIN attempt](routing-tooling.md#gain-follow-up-report-why-search-stopped)
also stopped at its correction limit without changing the board. Its sampled
component exhausted after 147 expansions, so do not respond with a larger
unfocused search budget. Prioritize short independent connections while
preserving these concrete local-layout blockers.

**Accepted independent progress:** R2.1/CHG0.C is connected with seven
0.20 mm F segments, no part moves or existing-copper changes, and preserved
filled groups/private returns. This closes one charge-indicator branch;
it does not resolve the core/Gain blockers or qualify powered behavior.

The full mechanical bind, 0.15 mm USB bezel adjustment, native CAD camera-state
handoff, current budgets, supplier processes and matched quotation exports are
still pending. Preserve earlier prints, models and the recovered candidate.
No supplier upload/order, functional or child-use approval is implied.
