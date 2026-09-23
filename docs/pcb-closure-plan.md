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

**Remaining-ground finite screen:** the
[24-site result](../hardware/handbell/iterations/printed-bell-four-layer/reports/supply-ground-remaining-batch.json)
generated no candidate; the accepted PCB stays at 47 opens. These were
0.65 mm axis-offset samples, not an exhaustive clearance search. No parts
will be moved on that evidence. Next is the
[fixed multi-radius follow-up](routing-agent-policy.md#remaining-ground-sampling-follow-up):
at most 336 sites inside the already released short-escape region, with
unchanged contact, pad, clearance and private-return constraints. Preserve
all counts and stop at the fixed set rather than growing an adaptive search.

**Latest September 22 decision:** the isolated validator controls and full
read-only saved-candidate suite now pass. Astra approves exact ground-stitch
candidate `453b9f6da227cc3ce4fe0a664e4d0e05d159a6cbe41b00c72d2b009e1c3ffe43`
for mechanical promotion as a connectivity milestone: **47 opens**,
233 warnings, and unchanged F/In1 fill geometry. The existing C9/R4/R8
ground group joins main GND; all prior groups and private pickoffs survive.
This does not qualify C9's local high-frequency return or establish a
physical zero-length path through its common filled island.
See the [full validation](../hardware/handbell/iterations/printed-bell-four-layer/reports/supply-ground-stitch-validation-final.json)
and [isolated controls](../hardware/handbell/iterations/printed-bell-four-layer/reports/supply-ground-stitch-validation-controls.json).
The earlier failures below remain historical evidence, not the final result.
Promotion is complete: the active PCB is that exact `453b9f6d...` candidate,
bound to manifest
`1bf38f7a9e6f9a1b086844a6309103f8935ecfcb8ef142bed7ccc0acc473ec2a`.
Only manifest status/PCB hash changed; all component geometry remains intact.
The [acceptance record](../hardware/handbell/iterations/printed-bell-four-layer/reports/supply-ground-stitch-acceptance.json)
binds the controls, final validation and reused native DRC evidence.
Other released ground-group screening counts and blockers were not persisted;
do not claim those groups completed or exhaustively screened. VCORE, local
return performance, physical stackup and manufacturing gates remain open.
Next bounded work: preserve the accepted stitch and screen the six remaining
released groups (C4, C11/C15, C12, C23, C24 and U2), with counts and blockers
saved before validation. Do not repeat the C9/R4 site selection or silently
extend its exhausted search history. Reuse the now-exercised shape and
guard-layer checks rather than recreating native API wrappers.

**September 22 owner resume (current):** bounded engineering has resumed.
The preceding +3V3 checkpoint PCB is
`5dc0ebe6b75a2325826460ece80d3f1b2cb45bc1af8341baa79358d85e3136d8`,
manifest `cdff8e0501a015039bc10c9b01a8f92dfde1a3edc2b7247914952d971073df41`.
The [accepted +3V3 bridge](../hardware/handbell/iterations/printed-bell-four-layer/reports/in2-3v3-bridge-acceptance.json)
joins its two groups with three In2 segments, 0.40 mm wide and 9.840281 mm
total length, between existing vias. **48 opens remain: 16 GND, two VCORE
and 30 others**, with 233 warnings. All previous copper, planes, placement
and private pickoffs are retained; source-bound checks were reused for
byte-exact promotion. The whole +3V3 net is now connected, not the whole
power system. Next released work is the
[local supply-ground stitch batch](routing-agent-policy.md#september-22-local-supply-ground-stitch-batch).
No VCORE relocation or wider escape search is authorized by that batch.

**Supply-ground batch outcome:** the bounded staged attempt is rejected,
not promoted. It added a candidate return at R4.1 in C9's existing GND
group, but stopped at the refilled-zone guard-overlap gate after two
implementation corrections. Its observed 47 opens do not supersede the
accepted 48-open board. The
[failed-stage record](../hardware/handbell/iterations/printed-bell-four-layer/reports/supply-ground-stitch-batch.json)
preserves exact artifact hashes and incomplete acceptance checks.
Next is read-only identification of the exact island/guard/layer and whether
the checker applied each guard to its own layer. No further site selection,
refill, guard relaxation or automatic acceptance is authorized by that
diagnosis. Remote continuity through R4 does not itself qualify C9's local
high-frequency return.

The [read-only diagnosis](../hardware/handbell/iterations/printed-bell-four-layer/reports/supply-ground-stitch-diagnosis.json)
identifies a checker-scope defect: all ten historical F-only exclusions
were incorrectly assigned to In1. The erroneous predicate produces the same
eight intersections on the unchanged baseline and candidate; it is not
evidence of a fill regression. The original failed-run report remains intact.
A separate validation-only item is authorized on the saved candidate:
correct the layer mapping, demonstrate baseline controls, and complete all
previously interrupted acceptance gates without new geometry or refill.
No copper is accepted by the diagnosis alone. Candidate-site counts and
other-group blockers were not persisted; do not reconstruct those as facts
or describe the remainder of the released batch as exhausted.

The corrected guard run passed the layer controls, all filled-layer
clearances and connectivity preservation, but stopped on an order-sensitive
via-layer assertion. Root identified that it compared native enumeration
with physical stack order. One final validation-only correction will compare
the actual layer set and native span without assuming enumeration order.
No stitch is accepted until the remaining via/contact/drill, DRC and
fill-change gates finish. If that run stops, preserve the partial result
and escalate rather than extend the correction loop.

**Current stop after the final validation correction:** the layer-set
correction and preceding guard/connectivity gates passed, but native
`SHAPE_CIRCLE.Collide(SHAPE_CIRCLE, clearance)` selected an incompatible
overload during drill checking. This is an API invocation failure, not a
measured clearance violation. The
[latest failed report](../hardware/handbell/iterations/printed-bell-four-layer/reports/supply-ground-stitch-validation.json)
and [prior via-order failure](../hardware/handbell/iterations/printed-bell-four-layer/reports/supply-ground-stitch-validation-failed-via-order.json)
remain separate evidence. Drill/contact completion, C9 path-length context,
fill-change locality and final DRC evidence acceptance are incomplete.
The accepted board stays at 48 opens; the saved 47-open candidate is not
promoted. Do not start another corrective execution automatically.
Escalate to the owner for a separately bounded validator-repair decision
or defer the candidate. The agent is idle; no routing/refill is running.

**Subsequent explicit owner decision:** "Repair validator in isolation, then
validate the saved candidate." This authorizes one new bounded tooling item:
prove the exact circle/slot/contact operations with small controls first,
then run the complete read-only suite on unchanged candidate `453b9f6d...`.
No routing, refill, geometry generation or promotion is included. Preserve
both failed validation reports; record controls and the final run separately.
Stop if the isolated repair budget or final run fails, rather than extending
another full-board correction loop.

**Earlier September 22 plane acceptance:**
Astra reviewed the saved actual-copper detail and supplementary proofs and
approved exact candidate `19d3bf9a1ab37dcc7af29f0cc99cc44a98564f878402beee15af3ce0a731ff78`
as the next incremental routing baseline. The existing +3V3/VAMP/V+ crossings
are retained with their existing F returns; no new fast-signal crossing or
final SI/PI approval is inferred. See the
[engineering disposition](routing-agent-policy.md#september-22-first-plane-engineering-disposition).
Sol completed the byte-exact promotion and manifest-source rebinding,
without a refill or reroute. The
[acceptance record](../hardware/handbell/iterations/printed-bell-four-layer/reports/in1-plane-acceptance.json)
binds the new PCB to manifest
`ce915418d33442f6ab42b155f6a7bc95c05e6c7032574d58044963ca4d066741`.
Only manifest status and PCB hash changed; all geometry and 47 non-PCB archive
dependencies are unchanged. **49 opens and 233 warnings remain**; 46 historical
schematic-parity notices still need disposition. Checks were reused for
identical source-bound bytes, not represented as fresh native execution.
The [saved-open inventory](../hardware/handbell/iterations/printed-bell-four-layer/reports/four-layer-remaining-connections.json)
contains 16 GND and two VCORE opens, among the remaining groups. Its unknown
track/zone endpoints must be resolved through the native graph rather than
treated as pad references. Next, review the remaining connected groups and release
a paired core-supply/return routing batch without consuming USB/clock corridors.
Physical stackup, parity, whole-CAD rebind and manufacturing remain open.

The [finite core screen](../hardware/handbell/iterations/printed-bell-four-layer/reports/core-supply-return-release-screen.json)
resolves three VCORE groups and two +3V3 groups. Its 24 sampled new-via
escapes do not release a complete VCORE route; rear-contact and fixed-copper
constraints remain. This is not an exhaustive impossibility result.
Next released execution is the
[existing-via +3V3 In2 bridge](routing-agent-policy.md#september-22-supply-bridge-release)
in the upper corridor, without new vias, component moves or a narrower trunk.
VCORE escape geometry and associated ground completion remain deferred,
not silently dropped.

**September 21 end-of-day pause (historical):** stop engineering; only saved-work
preservation and publication are authorized. Sol confirmed it is idle with no
running subprocess. Do not automatically continue the earlier sequence.

- Accepted package: `printed-bell-four-layer`, PCB SHA-256
  `d91837ed9f5cff10d709521e448f6deae3aac3a52abed88c34271ee809e25418`,
  manifest `ed64e9c92bd2cc7dc90a00cd98689f511517151c909052e7b23b3840d101f381`;
  **51 opens**, no accepted inner copper.
- Unaccepted staged PCB: `19d3bf9a1ab37dcc7af29f0cc99cc44a98564f878402beee15af3ce0a731ff78`,
  **49 opens**, one In1 island, both private returns and prior connected
  groups preserved. It is saved with its matching project/libraries in
  [`staged-in1-settings-replay.zip`](../hardware/handbell/iterations/printed-bell-four-layer/reports/staged-in1-settings-replay.zip)
  (SHA-256 `1259ca815cb6a70f44ff5927d12ffc62bba48af98d7ba572faa98103ae3ef388`).
  Extract separately, never over the accepted package. The archive retains
  derivative CC BY-SA licensing and omits personal `.kicad_prl` preferences.
  It has no newly accepted manifest or CAD binding.
- Completed review evidence:
  [`in1-plane-settings-replay.json`](../hardware/handbell/iterations/printed-bell-four-layer/reports/in1-plane-settings-replay.json),
  [`in1-plane-review-supplement.json`](../hardware/handbell/iterations/printed-bell-four-layer/reports/in1-plane-review-supplement.json),
  [actual native In1 plot](../hardware/handbell/iterations/printed-bell-four-layer/reports/in1-plane-native.svg)
  and [clock/boost detail](../hardware/handbell/iterations/printed-bell-four-layer/reports/in1-plane-review-details.png).
  Supplemental checks cover all 220 F private-item/island clearances,
  exact nine In1 guards, 1,483 unchanged non-zone source blocks, and four
  preserved all-F local boost paths. Root engineering acceptance is unfinished.

**One next item, only after explicit resume:** inspect these already-saved
actual-copper views and the ten other-power-segment/void witnesses, dispose
of return-path concerns, and decide whether to promote this exact candidate.
Do not refill, reroute or regenerate artifacts merely to resume. If accepted,
bind the exact PCB into the manifest and record acceptance before releasing
the next routing batch. Otherwise retain this candidate with a finite repair
list. Physical stackup, parity notices, full CAD rebind and manufacturing
qualification remain separate open gates.

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
**Saved-native graph gate subsequently passed:** source-derived fixtures
demonstrate the exact inner-layer short, via/island-only ground connection
and same-net layer isolation. See
[`four-layer-graph-saved-native-control.json`](../hardware/handbell/iterations/printed-bell-four-layer/reports/four-layer-graph-saved-native-control.json).
No source PCB changed. Production private-return inventory is now reviewed:
only two private-branch vias enter In1. Astra released one staged protected
GND plane with exact guards around those vias, local switching-copper
exclusions and a provisional clock-region exclusion. See the
[bounded plane release](routing-agent-policy.md#first-protected-ground-candidate-release).
The first staged candidate is rejected: native DRC reports 50 opens and no
other errors, but the filled-graph comparison finds a previously connected
GND pad group split. The accepted board remains at 51 opens. No plane,
exclusion change or private-pickoff approval is inferred from the lower
airwire count. The next item is read-only diagnosis of the exact separated
pad subset and refill/transplant differences, not another plane trial.
The staging script is incomplete as an acceptance checker: explicit
per-layer exclusion/clearance/edge and source-invariant gates remain required
before any later promotion. See the
[partial result](../hardware/handbell/iterations/printed-bell-four-layer/reports/in1-plane-first-stage.json).
The [read-only diagnosis](../hardware/handbell/iterations/printed-bell-four-layer/reports/in1-plane-regression-diagnosis.json)
isolates exactly **C25.2**, not the other 21 pads in its original group.
Canonical CLI output and transplanted F/In1 fill blocks match exactly, so
the regression occurred during refill, not transplantation. Both private-via
guard bounds also match exactly. The refill input lacked a same-stem project;
moreover, the existing accepted refill recipe explicitly tightens project
settings (including 0.001 mm polygon error versus the project's 0.005 mm).
Neither omission's individual causal effect has been measured.
The staging script is now disabled before any write or native process.
The [no-new-copper replay](../hardware/handbell/iterations/printed-bell-four-layer/reports/in1-refill-settings-control.json)
now passes: the existing `tools/refill_front_ground.py` recipe reproduces all
22 F fill blocks, preserves 137 connected pad groups and both private
pickoffs, and retains MH1.1-to-C25.2 continuity without shorts/floating
copper. Native DRC was not rerun on that isolated control. This proves a
working explicit-settings refill path, not which individual setting caused
the failed trial.
Next: one staged replay of the same released In1 geometry using that
explicit-settings path and a complete per-layer checker. Do not reconnect
C25 by moving parts or altering existing tracks/exclusions. Keep the failed
trial separate, require exact guard coordinates and source invariants, and
stop on any new topology/geometry failure rather than adjusting the plane
inside the replay.
The [explicit-settings In1 replay](../hardware/handbell/iterations/printed-bell-four-layer/reports/in1-plane-settings-replay.json)
now passes the implemented scalar gates: 49 opens, unchanged 233 warnings,
all 137 prior pad groups preserved, both private pickoffs preserved, and one
In1 island of approximately 1371.62 mm2. It joins three existing GND groups
without changing placement or routing primitives. **It is still staged,
not promoted.** Root review found that the first SVG depicted only island
bounding rectangles, not actual copper; that figure was removed and replaced
with the native plot and actual-polygon details linked above. Supplementary
original-F private-guard checks are now complete, but root review remains
paused. The ten other-net
trace/void witnesses are five +3V3, two VAMP and three V+ power segments,
not ten independent signal defects; local return paths still need review.
Native plane work does not require
using the still-unqualified F/B-only route search; qualify that engine only
if it will actually be used for inner routing.

**Earlier tooling checkpoint, superseded by the saved-native control:** primitive/zone graph enumeration now
supports enabled copper layers and plated spans. The bounded native-fill
control is not accepted: a corrected finite fixture fills In1 successfully,
but a subsequent different-net crossing appears connected and stops the
test before filled-plane assertions. No production copper changed.
Do not release inner routes or repeat the fill loop. The next diagnostic is
an exact fixture net/UUID/edge comparison across native connectivity build
and fill, not another board routing attempt. Previous pad-group fingerprints
are reusable only while both production inputs and graph-code hashes match.

The subsequently authorized saved-file attempt also failed: short-fixture
creation/CLI/graph stages completed, but the separate plane creator crashed
before saving (`0xC0000374`); native plane refill was never reached. Its
temporary-directory cleanup lost the per-stage evidence. No further run
is authorized by that exhausted item, and automatic invocation of the
unfinished control is disabled. The next decision is whether to replace
fixture creation with a known-good saved native example or change checker
implementation; do not resume routing or treat this as a real PCB failure.
The source-bound [report](../hardware/handbell/iterations/printed-bell-four-layer/reports/four-layer-graph-file-control.json)
and [tooling lessons](routing-tooling.md#current-conclusion) preserve the
precise limitations and required harness repairs.

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
