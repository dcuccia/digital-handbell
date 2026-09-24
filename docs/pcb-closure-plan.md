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

**September 24: complete local primitive block staged; acceptance pending.**
The [layer-correction result](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-signal-layer-correction.json)
records working PCB
`e954884c4a7369d2c6363ba825a50d6189be9d7127a415288b107f7832382b8a`
and manifest `b55d8dc21d4430e2da7e9c2e0e0166ea335f0a2c70b0113d748194f69d6341a5`.
The recovery pair `reports/imu-coupled-working.*` now holds those bytes;
earlier repaired-supply versions remain in Git history.

The shallower CS detour and additional ordinary INT B-to-F transition
passed simultaneous native geometry. The proposed R15 move, conditional
spur removal, ground reroute and signal plan are now actually applied.
All local supply/exterior duties, SCL including R14, SDA including R15,
INT2-to-TP6 and INT-to-local-F-exit are connected primitively with zero
shorts. GND1/2/3 reaches C23.2 and GND6/7 reaches the local via.
All nine changed/new ordinary vias pass same-net-inclusive off-pad checks.
The 21 zone definitions are unchanged and have no filled caches.
INT still does not reach IC1.34; that external connection is not claimed.

**Next bounded item: electrical qualification of these exact saved bytes.**
Preserve an immutable unfilled pair; refill a separate output using the
exercised settings, with matching project/rules inputs. Persist each gate.
Compare the full accepted baseline's connected pad groups, not just IMU
representatives. Require both new returns to MAIN, no lost prior groups,
cross-net shorts or floating copper, both actual private-terminal cuts,
CELL_NEG isolation, full contact/drill/clearance and source/manifest/zone
invariants, then native DRC with an explicit open-count comparison.
Expected local progress is at least the two GND opens and SCL pullup open;
do not assert 38 opens before measuring the filled board.

Run one 15-minute qualification item with at most two validator-only
corrections; no new routing or placement changes. Source-invariant checks
must include all cumulative rework releases from the accepted source,
including the proved conditional spur removal and preserved exterior
geometry. Do not weaken the acceptance criteria to match a failing result.
If a routing defect appears, retain evidence and return a finite repair
list instead of modifying copper inside a validation task.

Even electrical qualification does not promote this candidate. The
actual return-plane continuity, local decoupling supply/return paths,
B/In2 signal adjacency and via transitions still need engineering review,
and moved IC4/R15 require exact mechanical rebinding. The authoritative
board remains the unchanged 41-open checkpoint until all applicable gates.

**September 24, 10:59 explicit resumption.** Resume from the matched
`3c7006c1...` / `a1278051...` repaired supply candidate, not the failed
in-memory signal proposal. The accepted 41-open board remains unchanged.
The prior stop is historical; preserve its evidence and retry accounting.

**One next bounded item: targeted CS detour and INT layer change.**
Keep the already-screened simultaneous signal plan and replace only the
two failed geometric assumptions. For CS, replace the offending waypoint
`(90.8,94.5)` with a shallower `(90.7,94.2)` between `(91.45,94.2)` and
IC4.12. This keeps the feed north of the IC4.11 NC land, subject to native
clearance against the SCL transition and every other proposed item.

For INT, do not squeeze the B exit between the fixed C24/supply vias and
USBBOOT diagonal. Retain its initial B route and use one additional
ordinary 0.604/0.35 mm through-via, starting near `(91.8,92.14)`, to exit
on F. Starting B approach:
`(87.97,91.72) -> (89,92.1) -> (90,92.5) -> (91,92.5) -> (91.8,92.14)`.
Starting F continuation:
`(91.8,92.14) -> (92,91.4) -> (93.1,91.4)`.
This avoids crossing the retained USBBOOT trace on B; it is not a proof
of full-span via legality or a connection to IC1.34. All coordinates are
seeds, not rule waivers. Check the particularly constrained distance to
the proposed SDA B route, SCL F route and INT2 In2 route simultaneously.

Retain the previous R15-only move, conditional clipped-stub cut proof,
GND123-to-C23.2 target, off-pad controls and protected outside geometry.
One 15-minute item with at most two local corrections; save actual coupled
copper and a matching manifest only when its native geometry is legal.
If primitively restored, qualified refill and full electrical gates follow
within the budget or as the next coherent item. Mechanical rebinding and
full return-path/stackup review still gate promotion.

**Historical September 23 stopping checkpoint.** The owner
requested a logical stop within 20-30 minutes at 17:02. The current
signal-closure item has ended after its initial attempt and two local
corrections; Sol confirmed idle and no subsequent routing, refill, DRC or
CAD work. Finish the checkpoint rather than start a late redesign.
The earlier unattended continuation was suspended until the explicit
September 24 resumption above.

The authoritative package remains PCB
`c7b6b6fdb9857f7ea993e3cad37c04e852981eceea5146802cadb35865b2cec7`,
manifest `08bf866d80f74775ff4099e4734da0d445fd359843f61637bf453abf002fe667`,
with the previously recorded **41 opens**. No fresh accepted-board DRC
or fabrication qualification is claimed.

**Exact next-session starting artifact:** the archived, matching
`reports/imu-coupled-working.kicad_pcb`
(`3c7006c1ec8df011b146a8696e60aeb778ab2760259186169c4bc7328c54c243`)
and `reports/imu-coupled-working-manifest.json`
(`a1278051b8513645b56089464ce2a9f2d4ea970a6ee913a33ca003dcfe5e6e5b`).
This preserves the actual local supply tree, repaired ordinary VDDIO via,
INT2-to-TP6 connection, tentative SCL escape and five ground straps.
Only IC4 has moved north 0.50 mm in this working copy; R15 is still at its
accepted position. It remains incomplete, unfilled and unaccepted.

The [signal-closure result](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-signal-closure.json)
and [exact final screen state](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-signal-closure-state.json)
preserve the failed simultaneous plan. The source plan, cut control,
proposed R15 neighbour/proxy checks and eight proposed ordinary-via
process/contact/drill checks passed, but the complete trace geometry did
not. **None** of that proposal's R15 move, GND123 reroute, via reallocations,
stub deletion or new SCL/SDA/INT copper was written.

| Remaining engineering decision | Exact last-tested geometry, not an approved route |
|---|---|
| SCL transition and CS branch must coexist | SCL transition `(91.02,93.492711)` competes with the saved CS branch. The final 0.25 mm F CS detour `(91.45,94.2) -> (90.8,94.5) -> IC4.12 (90.412306,93.992711)` hits IC4.11's NC land. A prior SCL-via shift instead hit INT2 on In2 and proposed SDA on F. |
| INT exit must avoid the fixed vias and other signals | Final 0.1778 mm B points were `(87.97,91.72) -> (89,92.1) -> (90,92.5) -> (91.8,92.5) -> (92.2,93) -> (93.1,93)`. The last two segments hit C24's fixed GND via `fa83a8ab...` and/or the fixed supply via `ae5186f8...`; earlier attempts hit the fixed USBBOOT branch/via. |

**One next item after resumption:** Astra reviews these two coupled
geometry decisions against the complete native obstacles, then releases a
specific local correction or explicit additional layer transition to Sol.
Retain the repaired supply candidate and the already-passed source-bound
evidence. Do not count repeated witnesses as additional defects, repeat the
exhausted three screens, or silently widen the region/rules. Full signal
restoration, MAIN-ground refill proof, preserved groups/no floating copper,
private returns/CELL_NEG/contact/source/manifest/native DRC and exact
mechanical rebinding remain gates. No quotation release or ordering.

**Ordinary VDDIO repair passed; complete local supply connectivity retained.**
The [four-item repair](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-vddio-via-repair.json)
moves the held via to `(87.85,92.7)` without a via-in-pad dependency.
All supply pads/exterior groups, earlier signal paths and five ground straps
remain connected primitively, with zero shorts. Working PCB
`3c7006c1ec8df011b146a8696e60aeb778ab2760259186169c4bc7328c54c243`
and matching manifest
`a1278051b8513645b56089464ce2a9f2d4ea970a6ee913a33ca003dcfe5e6e5b`
replace the prior recovery pair. They remain unfilled and unaccepted.

**Next: coupled SCL/SDA/INT completion using the explicit
[engineering seed plan](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-signal-closure-plan.json).**
It keeps IC4/C23/C24/R14 fixed at their working poses, moves only R15 north
0.50 mm, and reallocates tentative local transitions to make room for all
three signal duties together. No coordinates are clearance waivers.

Two new transition sites are proposed above the retained upper B conductor.
Native source inspection identifies that conductor (`4ef0b7ff...`) as
`Net-(L0-PadA)`, the LED branch, not a clock as the earlier site report said.
Its physical obstruction remains real and its copper stays fixed. Release
new copper only in the additional upper corridor x86.6..93.1, y89.2..90.5;
no unrelated routing or components there may change. A named clipped +3V3
dead-end stub may be removed only after an actual cut proof establishes no
lost pad-group connectivity, allowing the R15 move without pretending a
temporary clipping point is a permanent functional interface.

The Mode-1 GND straps may return through an explicit F link to C23.2,
freeing their tentative via site for SDA. MAIN attachment must then be
reproved by refill, not assumed from the original C23 acceptance. The plan
preserves the restored VDD/CS/INT2 paths, power trunk, ordinary-via process
rules and all other outside geometry. Run a simultaneous native screen and
save the actual evolving candidate with matching manifest. One 15-minute
item and at most two local corrections; full acceptance/CAD gates remain.

**Earlier supply candidate -- held pending the now-completed via repair.**
The [supply-tree report](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-supply-tree.json)
binds private PCB `329a5d56c6fa0723095e97debc296c0b9c459fef698caf3fef6b8336817f17ca`
and manifest `bb2fcfbd5f37bd0831f92a586c314d788717099476486c2f8b3bb4e7e6985980`.
All local supply pads and three exterior supply groups reach the fixed
bridge, with the earlier signals/ground straps preserved. Cached/shared
search took 2,392 expansions and 4,877 exact edge checks, about 1.5 seconds
before smoothing, rather than timing out on repeated per-site searches.

The missing same-net SMD non-overlap gate then correctly rejected VDDIO
via `8172b557...` at `(88.2,92.85)`: it overlaps IC4.5 and would introduce
an unauthorized via-in-pad dependency. C23 and the three saved ordinary
ground/INT2 anchors passed. Both on-pad negative and off-pad positive
controls passed. Hold the candidate; electrical connectivity is not process
acceptance. The public working recovery pair remains the earlier `206afad5...`
checkpoint until a repaired pair is reviewed.

**Next item: surgical ordinary-via repair, not another supply-tree search.**
Move only the held VDDIO via and its IC4.5/R15.1 F connections and In2
entry, retaining the shared trunk and every established connection.
Remove the script's unqualified `y >= 92.85` escape filter; it is not a
design rule or a demonstrated signal reservation. A native-screened
off-pad location near `(87.85,92.7)` is a starting hypothesis, with the
In2 entry rejoining `(88.2,92.9)`. Require the complete ordinary-via
process/foreign/hole/contact gates and actual preserved connectivity,
not just same-net clearance exemption. Limit this repair to six minutes
and two local corrections; no new via process, rule reduction or part move.

**Latest working checkpoint: VDD/CS/C24 and INT2 restored.**
The [paired-route report](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-vdd-int2-routing.json)
binds recovery PCB `206afad547838c26afbf6ca6056af8d0b7073ea00938599598e83792a5bb7f38`
and matching manifest `6ae59fbf552d8b9e0541926db8aee2b655a7c5268a566ee0cf1151d1f6e7ceb0`.
The `imu-coupled-working` recovery files now contain that pair; earlier
versions remain in Git history. Seven 0.25 mm F segments restore the
fixed supply bridge-to-C24-to-VDD/CS tree. An ordinary INT2 transition,
two F segments and three In2 segments reconnect IC4.9 to TP6 through the
existing external group. All five ground straps survive; zero primitive
shorts are reported. No refill, full DRC or accepted-board change.

Native [front](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-working-front.png)
and [inner](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-working-inner.png)
views bind those exact bytes. Root review confirms the intended separation
of the south-side F supply branch and northward/inner-layer interrupt
escape. The inner route stays north of the clock exclusion. These primitive
views omit filled planes and drill voids, so they do not prove return-plane,
electrical-performance or mechanical qualification.

**Next item: finish the branched VDDIO/C23 feed without repeating the slow
search unchanged.** The 0.1 mm-grid implementation repeatedly constructed
native collision objects across up to 16,000 expansions per site pair,
exceeded its 120-second deadline and saved no supply copper. This is
incomplete search evidence, not a demonstrated geometric blockage.
Reuse the legal access-site lists and current saved candidate. Cache/
prefilter immutable native obstacles per layer and width, or screen a
small obstacle-derived bent-path set; retain final exact native checks.
Use a shared search toward the existing supply group rather than restarting
the same expensive traversal for every pair. Measure stage/expansion counts,
invalidate caches after copper changes, and keep finite execution limits.
The south-of-INT2-via inner corridor is a routing hypothesis, not a clearance
waiver. Restore pullup/exterior power duties if straightforward within the
same bounded item; remaining I2C/INT and all acceptance gates stay explicit.

**Latest private result: all five IMU ground pads explicitly strapped.**
The [branched-supply report](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-branched-supply.json)
records PCB `098dc7fd919340176ffb41f177525015b0e27f806abd5783121beecf593ea37b`:
IC4.1/2/3/6/7 each reach their intended return via, with zero primitive
shorts. MAIN attachment remains pending refill. The private manifest still
has the preceding PCB binding and must be refreshed before further use;
the archived `imu-coupled-working` PCB/manifest remain the earlier matched
pair from `d824251`. No additional supply copper or accepted-board change.

The scan found 31 legal VDDIO and 82 legal C23 access sites, but then
required another transition near IC4.8. Its reported "north" VDD box,
y94.95..95.55, is actually south of the moved pad at y94.655211 and entirely
contact-excluded. That failed box is not a requirement for a VDD via.

**Astra's next coupled topology:** feed IC4.8 and IC4.12 on F from C24.1,
with C24 supplied from the existing fixed +3V3 bridge via on F. Route VDD
south of the IMU bottom pad row, keeping the existing capacitor return.
Move the competing IC4.9/INT2 escape north into the cleared package interior
and onto In2 instead of forcing both crossing connections onto F.
The former SDA transition location `(89.6195,93.5809)` is an explicitly
released candidate INT2 via site, subject to full native checks.

For INT2 only, extend the allowed new-copper corridor on In2 to
x93.1..94.2, y92.1..92.95, ending at the existing INT2 via
`3a4ecc82-02d7-5513-8c89-db4de4adc534`, `(94.04,92.3102)`.
Preserve that via and every outside primitive. Connecting this existing
external group must restore IC4.9-to-TP6 and the retained clipped F branch;
it need not recreate the former local F route. The In1 clock exclusion
begins below this corridor; no clock, USB, contact or bridge relaxation is
authorized. Native multilayer/return-path checks still apply.

Reuse the legal VDDIO/C23 access evidence for their branched feed rather
than restarting a placement sweep. Keep the same private candidate and
15-minute/two-correction limit, refresh the manifest at each save, and
retain useful routing even if remaining signal duties need another item.

**Current private work: two return anchors saved; supply tree still open.**
The [coupled-routing report](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-coupled-routing.json)
binds private PCB `00006ee9641dd1dabb266a7bb1129ff6ba8022ae9bdf0c6c231842aab5b21d67`
and manifest `efb3b31da5dad9dd548f1b250d49e07259c58e3bfc46ca425360f8d250aebbfe`.
Recovery copies are `reports/imu-coupled-working.kicad_pcb` and
`reports/imu-coupled-working-manifest.json`; these remain incomplete,
unfilled and unaccepted. The accepted board is still unchanged at 41 opens.

The actual working copy adds GND vias at `(87.9,93.6)` and `(90.7,91.65)`
with F links, and removes the remaining authorized local +3V3 fanout for
replacement. Root review narrows the report's group-level wording: its
primitive checks establish IC4.6 and IC4.1 to their respective vias,
not individually all five ground pads. IC4.2/3/7 connectivity still needs
explicit evidence, and neither MAIN-plane attachment is claimed without
refill. No complete-candidate source, DRC or CAD gate has run.

Four one-transition VDDIO constructions with direct In2 feeds failed.
Do not repeat that star-layout assumption. **Astra's next topology choice
is a branched In2 supply distribution with separate ordinary transitions
where needed for legal short capacitor/device F connections.** Use native
obstacle-aware bends rather than requiring a straight bridge-to-via segment.
The tentative INT reservation and private ground/SCL routing may be revised
to make the whole block fit; none has acquired accepted-board status.
Keep the same component-movement limits and protected exterior/critical
geometry, and test every IC4 ground member explicitly. Restore the complete
prior +3V3 pad group and exterior duties; save actual progress with its
remaining obligations under the existing 15-minute/two-correction rules.

**Working fanout fixture qualified; accepted board still unchanged.**
The [method report](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-fanout-method.json)
and [18-gate validation](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-fanout-method-validation.json)
now establish a real clipped/ripped-up working copy and replacement SCL
escape, not moved-pad tails. The archived incomplete PCB is
`reports/imu-fanout-method-staged.kicad_pcb`, SHA-256
`6df836645cebbd8f2d793822a182dd95db14604f2119820510db107cc4e19087`;
its staged manifest is `800321ae0044a199ff506f6b648609e7d6ac44e0413fcbb3afa7b1711f72466a`.
These are recovery inputs, not a self-contained package or accepted routing.
All zone definitions, non-IC4 footprints and protected/exterior geometry
survive; caches alone were invalidated. Mutation controls reject actual
rule, footprint and boundary changes. The active package remains at 41 opens.

**Next item: complete coupled IMU routing on that one private candidate.**
Prioritize paired supply/return geometry and reserve or route the interrupt
and I2C escapes together. Preserve the tentative SCL route where useful,
but do not freeze it against a better complete local topology. Both 100 nF
capacitors remain: allocate C23 to IC4.5 VDDIO and C24 to IC4.8 VDD, with
explicit local supply/return paths; IC4.12 is the required CS supply tie.
`/IMU_INT2` reaches TP6 in the accepted design and must not be discarded as
an unused single-pad net.

Astra additionally releases local +3V3 transition vias `6421709a...` and
`6d56c09b...` for necessary relocation/replacement within the same rectangle.
They are routing choices, not mechanical datums. This extends the previously
released `1c15a7a2...` and SDA `aa47961d...` scope; it does not release the
accepted In2 bridge or its `ae5186f8...` endpoint. Restore all supply pads
and boundary duties with preserved width/current-path requirements. Keep
IC4 at its staged pose for this item; the four local passives retain their
previously released individual 0.75 mm translation limit and unchanged
rotations. C24's capped via must follow its pad if moved.

One 15-minute item, at most two corrective retries: modify the actual
private copper, not only proposal masks. Save each useful state and its
remaining obligations before expensive checks. A partial power/return
foundation is not promotion; only the full coupled block, required
electrical gates and mechanical rebind can change the authoritative board.

**September 23, 14:48 owner authorization: continue while the owner is away.**
The owner explicitly requested continued iteration over the next couple of
hours, aligned with the agreed priorities and strategies. Retain the bounded
item/retry/checkpoint rules and pinned Sol execution; no fabrication,
supplier upload or purchasing authority is added.

**Current item: real rip-up and replacement-fanout method.** Build one
private, explicitly incomplete working PCB/manifest from the unchanged
41-open accepted source. A disconnected intermediate is permitted during
authorized rework; complete restoration is an acceptance gate, not a
requirement to retain every obsolete local connection while editing.

The native rework rectangle is x86.6..93.1, y90.5..95.9 mm. Start with
IC4 alone moved north 0.50 mm, preserving all rotations and other parts.
Cut the justified affected branches from the 69-track inventory and clip
the internal portions of six declared boundary tracks to that rectangle.
The seventh, `a8cbe912...`, belongs to the accepted In2 supply bridge and
remains wholly protected, along with its endpoint via and all other
accepted critical routes. Preserve exterior geometry and declare actual
retained terminals, rather than old IC4 pad centres. The two previously
released local vias may be removed in the incomplete fixture, with their
replacement obligations recorded; this is not completed connectivity.

Require native loading, source/exterior invariants and a real split/rejoin
control. Invalidate stale filled caches without changing zone definitions.
Then demonstrate an actual native-screened SCL path from moved IC4.13 to
the retained boundary port `(93.1,92.7368)`, using existing routing helpers,
not straight tails to obsolete pad terminals. Limit this preparatory item
to 12 minutes and two implementation corrections. Preserve one working
artifact and a concise terminal/cut ledger, even if later routing is
incomplete; do not start a generic router/tooling project.

The SCL path is tentative method evidence, not accepted routing that may
consume the remaining ground/power/INT corridors. After reviewing this
artifact, the next dependent items are complete coupled IMU replacement
routing, electrical acceptance gates, then required mechanical rebinding.
Those milestones must preserve every prior connection and close the two
IMU ground groups and SCL pull-up before promotion. Reuse useful staged
work with a finite repair list instead of repeatedly starting new layouts.

**Latest result: execution incomplete, not a failed complete re-layout.**
The [three-construction report](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-coordinated-relayout-trial.json)
(SHA-256 `81bd4b3b371dc102cc41222107f124cdf608182fd404b92508a03d8b7b3901cf`)
contains rejected preliminary geometry only. No candidate, staged manifest,
refill, DRC or mechanical review was produced. The accepted PCB/manifest
remain exactly `c7b6b6fd...` / `08bf866d...`, with **41 opens**.

Root requested an evidence-only clarification, with no further routing.
The executor confirmed that SDA via `aa47961d...` was omitted from its
fixed-obstacle mask but never given a replacement transition/topology.
It did not implement boundary clipping and kept the relevant crossing
tracks wholly fixed, despite permission to replace their internal portions.
It used straight moved-pad-to-old-terminal tails, not a complete replacement
I2C/supply layout. P1/P2 also reused the same contact-excluded GND67 site.
These are limitations of the exercised method, not evidence that the
owner-authorized re-layout freedoms are exhausted.

A concrete pin-fanout hazard is visible in the recorded native coordinates:
after IC4 moves north by 0.50 mm, its new SCL pad IC4.13 is at
`(90.412306,93.492711)`, exactly the old SDA pad IC4.14 centre. Retaining
that former SDA terminal and adding a tail cannot preserve separation.
The affected fanout must be replaced back to appropriate retained external
connections, rather than treating old pad centres as fixed interfaces.
This coordinate consequence is not a new routed-candidate DRC result.

**Disposition:** preserve the report unchanged, but do not accept it as
completion or exhaustion of the coordinated re-layout. The three-plan/
two-correction trial has ended; Sol is idle. Do not launch another placement
or short-tail sweep. The next engineering item must establish an actual
replacement-fanout method, including declared internal boundary cuts and
complete replacement connections, within the existing release below.
No additional owner permission to use those already-released freedoms is
needed. Escalate a tooling/method limitation honestly rather than asking
for increasingly relaxed board constraints. CAD review remains blocked
until an electrical candidate exists.

**Owner-approved scope retained for method redesign.** The owner selected
"Authorize coordinated local IMU re-layout (recommended)" after checkpoint
`8e41215`. The completed item released one separate staged trial to the
verified GPT-5.6 Sol executor, maximum 15 minutes including validation/reporting,
three coherent layout plans and at most two corrective retries. That trial
and its retry allowance have ended; the permissions below do not restart it.
They change local via/placement constraints, not manufacturing rules or
board interfaces.

- IC4, C23/C24 and R14/R15 may move individually by at most 0.75 mm from
  the accepted positions; preserve rotations, native pad definitions and
  all other parts. Prefer unchanged parts where the complete plan fits.
- Release relocation/replacement of SDA via
  `aa47961d-0754-5f3e-b69c-68e3b7f9079f` and +3V3 via
  `1c15a7a2-2065-55a0-bfec-88da501cad88`, with complete replacement paths.
  Other existing vias remain fixed except that C24's mandatory filled/capped
  via must follow its pad if C24 moves. New ordinary vias retain the
  0.604/0.35 mm policy and full contact/tab clearance, including B copper.
- Use only necessary local trace replacements from the 69-track inventory.
  Internal portions of the seven boundary traces may also be reworked
  after defining the exact local boundary; preserve their outside geometry
  and connection duties. The accepted In2 supply bridge, USBBOOT route,
  C12 feed, clock/USB/protection structures and all outside circuitry remain
  protected. Keep the 21 zone definitions/guards and both private returns.
- Require both IMU ground groups and the R14 SCL pull-up to connect while
  preserving all prior supply, SDA, SCL and IMU_INT2 connectivity. Prove a
  compatible INT escape/local exit; its outside connection to IC1.34 may
  remain open. Bent escapes or an ordinary In2 transition are permitted,
  rather than assuming the earlier straight-west screen is exhaustive.
  A complete local result would reduce 41 opens to at most 38, not qualify
  the whole board.
- Stage source-preserving PCB and matching manifest changes separately.
  Require the native geometry, refill/DRC, complete connectivity, contact,
  private-return and source-preservation gates; mark incomplete gates
  explicitly if the budget expires. Moved-part proxy screening is not
  full-assembly qualification: exact CAD rebind/mechanical review is
  required before acceptance. Do not edit the authoritative package or
  quotation process map based on an unaccepted staged candidate.

**Historical fixed-placement trial -- complete and blocked.**
The [twelve-plan result](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-fixed-placement-trial.json)
(SHA-256 `a8e41d199a974a597aea4813f11112d01428e0e2e671d7902e51d6e22f246659`)
rejects all released combinations before candidate generation. The tested
straight west INT escape excludes the entire proposed IC4.6/7 via-centre
region. The tested INT transition vias are only 0.061-0.369 mm from the
ground vias, versus the required 0.804 mm centre spacing. Some combinations
also fail fixed-pad/via constraints. The proposal regions were upper-bound
geometry, not independently qualified via locations.

No traces were removed, no candidate exists, and no refill or candidate DRC
was run. The recorded tool execution was 38.094 seconds; this is not the
total engineering/review time. The accepted PCB remains **41 opens**:
`c7b6b6fdb9857f7ea993e3cad37c04e852981eceea5146802cadb35865b2cec7`;
manifest:
`08bf866d80f74775ff4099e4734da0d445fd359843f61637bf453abf002fe667`.
These bytes are unchanged. Existing acceptance evidence is reused by exact
hash, not described as freshly rerun.

This rules out the twelve tested plans, not all fixed-placement solutions.
The earlier bounded cardinal screen did not establish that every bent or
different-length INT escape is impossible. Do not restart substantially
similar trials under a new name.

**Historical recommendation, now authorized within the limits above:** one coordinated IMU
re-layout item for IC4, C23/C24 and R14/R15, including their local routing
vias rather than freezing every existing transition. Prefer retaining
parts where a complete coupled plan permits it; consider small individual
adjustments only for a demonstrated conflict, not another blind rigid-shift
sweep. Explicitly identify any via moves and affected local/boundary trace
sections before staging. Ground, supply/decoupling, pull-ups and INT/SCL/SDA
must fit together, with every prior connection restored. Preserve the
outline, mounts, USB, contacts, outside circuitry, accepted critical routes,
CELL_NEG isolation and private returns. Any placement change also requires
the exact manifest/CAD rebind and mechanical review before acceptance.
The previous rigid translations were not accepted by that comparison;
the new release requires a complete coupled candidate, not adoption of a
placement sketch or relaxed clearance/manufacturing rules.

**Historical authorization -- completed with the blocker above:** the owner
approved the fixed-placement rework trial and also
requested a plan to address the most constrained routing groups first
and apply the lessons to the remaining board. Follow the
[bottleneck-first sequence](routing-agent-policy.md#bottleneck-first-closure-sequence).
One ten-minute separate trial is released for the case-A local boundary,
with at most two corrective retries and no part/via moves or rule changes.
First verify that proposed ground, INT, SCL and SDA escapes coexist with
the necessary supply/decoupling connections. Then replace only the
necessary named local traces, preserving the seven external ports and
all pre-existing connected pad groups. The 69-track list is a maximum
boundary of analysis, not a blanket removal instruction.

If a mutually compatible plan cannot be constructed within the item,
stop with the exact conflicting geometry and saved partial evidence;
do not route easier signals through unresolved critical corridors.
No acceptance is possible without restoration of every disturbed
connection and closure of at least one intended IMU ground group.
The active board remains **41 opens** until that review.

**Coordinated proposal reviewed -- prefer fixed placement, not yet routed.**
The [four-case comparison](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-coordinated-layout-proposal.json)
finds no immediate fixed-copper or planning-envelope conflict in case A
(current placement). The 0.25/0.50 mm north shifts each introduce three
fixed conflicts; the 0.75 mm shift introduces six. None improves the
screened INT/SCL/SDA escape directions. Do not implement those translations.

Case A was preferred for that trial, not a proven routable layout.
Its return regions assume removal of 69 specifically inventoried local
trace sections; this is not permission to delete them wholesale. Every
affected supply, decoupling, pull-up and signal connection and all seven
protected external ports must survive a completed rework. The IC4.6/7
candidate region is only 0.001876 mm2 and lies alongside the reserved
INT escape. Independently clear return and signal screens do not prove
that both can coexist; mutual clearance must be checked before staging
any copper.

Historical recommendation, subsequently approved and now blocked: one
bounded separate fixed-placement local rework trial. First construct a mutually compatible
return/signal plan and enumerate the minimal affected trace set within
the proposal's local boundary. Stage only if required reconnections fit;
never promote a board with broken pre-existing connections. Preserve all
parts, pads, existing vias, outside routing and mechanical interfaces.
Stop on a concrete coupled-routing blocker rather than widening the
placement search. The active board remains **41 opens**, unchanged.

**Owner-authorized coordinated IMU proposal:** the owner selected
"Review coordinated IMU routing and possible small placement adjustments."
Release one proposal-only item for IC4, C23, C24, R14 and R15 and their
local power/ground/SCL/SDA/INT escapes. Compare a fixed-placement local
routing rework with three simple rigid cluster shifts north by 0.25,
0.50 and 0.75 mm (negative native y). These are comparison cases, not
approved moves. C24's centered capped via must follow its pad in any
shifted proposal and retain its process requirement.

Keep the board outline, mounts, USB, battery/contact interfaces, existing
In2 +3V3 bridge, accepted USBBOOT route, C12 feed and all outside circuitry
fixed. Identify exactly which local track sections a future rework would
replace and its external connection points; do not assume a common net
name proves that a cut is harmless. Reuse current native geometry and
placement envelopes to screen the alternatives against fixed neighbours,
contact/via exclusions and potential ground/signal escape corridors.
Keep actual measured geometry separate from planning proxies.

Return a compact comparison with original/proposed coordinates, conflicts,
external connection duties, and geometry-supported options for root
review. An unrouted placement sketch is not routing or CAD qualification.
No native design, manifest, route, footprint, rule, process or mechanical
interface is to change in this item. Limit work to ten minutes and at
most two corrective retries; do not expand the placement search.

**Local power-track diagnosis complete; IMU work remains blocked:** the
[five-case comparison](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-power-return-cut-review.json)
produced no change in either target's conservative centre domain and no
passing connection. Keep all four tracks: removing `8b67bfa8...` would
disconnect R14.1 from +3V3, and removing all four would also leave
`c9710cc0...` floating. The other three are individually graph-redundant,
but their removal offers no demonstrated return-space benefit.
The source remains unchanged at **41 opens**.

This rules out the proposed benefit of those four omissions under the
tested constraints, not every fixed-placement routing solution. Stop the
local point/cut-screen sequence. Recommended next scope, pending owner
direction: one coordinated IMU-area escape/layout proposal covering both
ground groups and preserving the SCL/SDA/INT and supply paths. Consider
local trace changes and, only as proposals, small component adjustments
if needed; retain the board outline, mounts, USB and battery/contact
interfaces. No component move, reroute, smaller via, narrowed trace or
manufacturing-rule change is authorized by this diagnosis.

Tooling lesson: an aggregate list of items intersecting an initial search
domain does not identify the constraints that limit the final usable
region. Here the four named traces are near y94.95..95.68, where the
rear-contact restriction already excludes the proposed through-via.
Inspect constraint overlap and actual coordinates before selecting a
track for further cut or reroute analysis.

**IMU feasible-space result:** the
[native region analysis](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-feasible-space-review.json)
found no passing connection. IC4.6/7's conservative centre domain is
empty. IC4.1/2/3 has a 0.000758729344 mm2 region, but all three checked
straight F stubs collide with the immutable IC4.4 interrupt pad. This
does not establish global impossibility. No design or fill changed;
the accepted board remains **41 opens**.

Root disposition: do not widen the point sweep, move the interrupt pad,
or relax clearances. The next bounded read-only question is whether the
four named local F +3V3 tracks responsible for part of the exclusion can
be changed without redesigning placement: `2439bd57...`, `56011162...`,
`76a37864...`, `8b67bfa8...`. Compare the unchanged source with five
in-memory cases (each track omitted individually, then all four).
Keep all pads, drills, contacts, other tracks and protected regions fixed.
Report newly available centre/connection space and exact +3V3 pad-group
cut consequences, including C23/C24 and IC4 supply attachments.
This is not authorization to delete or reroute any track.

The prior region report explicitly used a 0.502 mm contact offset
(0.302 mm via radius plus 0.20 mm). The new comparison must use the
released 0.25 mm contact clearance (0.552 mm offset), preserve the old
report, and state this difference. No proposal was accepted under the
older construction. Use conservative-domain qualifications throughout;
stop after the finite comparison for a coupled power/return decision.

**September 23 explicit owner resume.** The owner requested "let's resume."
The evening pause is superseded. Start only the agreed bounded read-only
IMU feasible-space analysis; no routing, placement or refill is released
by this item. The working tree and saved source hashes were verified
unchanged, and the existing executor still resolves to `gpt-5.6-sol`.

Resume from `hardware/handbell/iterations/printed-bell-four-layer`:
PCB SHA-256
`c7b6b6fdb9857f7ea993e3cad37c04e852981eceea5146802cadb35865b2cec7`;
manifest SHA-256
`08bf866d80f74775ff4099e4734da0d445fd359843f61637bf453abf002fe667`.
The accepted board has **41 opens**, 233 warnings and 46 historical
parity notices. C12/C23/C24 ground closures are accepted; C24's explicit
filled/capped treatment requirement remains mandatory and unqualified
for supplier/assembly use. Latest blocked IMU evidence was pushed in
`dc2784c`; there is no unaccepted IMU PCB candidate to recover.

The resumed bounded read-only feasible-via-centre analysis will
address IC4.6/7 and IC4.1/2/3 in the previously released local region,
using actual native copper, pads, drills, contacts and plane constraints.
Include interior space; do not repeat the exhausted bridge/point screens.
Return feasible regions plus exact checked connection proposals, or
source-bound blockers and approximation limits, before any routing change.
Retain the Astra engineering / explicitly pinned Sol execution split.

Use native x87.5..92.5, y91.0..95.2 mm and the established ordinary
0.604/0.35 mm off-pad through-via. Derive candidate-centre regions from
the complete native geometry, including interior access, rather than
another grid or outward-offset point set. Account for every enabled
copper layer, pad/drill/slot, rear-contact and protected-region constraint,
main-In1 access and a possible 0.30 mm F stub of at most 1.05 mm.
Record conservative polygon-approximation limits and evaluate any
representative centres/stubs with the existing exact native predicates.
Bound the item to eight minutes including at most one corrective retry;
native subprocesses get explicit timeouts. Return feasible regions and
at most six checked proposals per target group, or concrete blockers.
An empty conservative region is not a global impossibility proof.
No general router, new process, via-in-pad, rule relaxation or source
change is authorized. Stop for root review when the report is complete.

**IMU return batch blocked; accepted board unchanged:** the
[bounded batch report](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-ground-batch.json)
records no passing proposal: IC4.6/7 had 0/4 F bridges and 0/27 via
sites; IC4.1/2/3 had 0/4 bridges and 0/48 via sites. Fixed signal/power
copper, pads, drills and rear-contact exclusions blocked the tested
geometry. No candidate, routing, refill or new DRC run occurred.
The active PCB/manifest remain `c7b6b6fd...` / `08bf866d...`, **41 opens**.
The item used its two corrective retries; do not extend the same screen.

Recommended next item, pending owner direction: one bounded native
feasible-via-centre analysis of this local IMU region, including interior
and edge access rather than another point sweep. Subtract the full-span
copper, pad, drill, contact and protected-region constraints from the
allowed region, then screen any resulting representative centre and its
short F connection against the actual native shapes. This would determine
whether the finite samples missed usable space before authorizing local
trace changes. It is not permission to build a general router, relax
rules, move parts or claim global impossibility from an empty conservative
approximation. Alternatively, park the IMU item and select an independent
batch under its own engineering release.

**Remaining-routing inventory complete:** the
[exact native ledger](../hardware/handbell/iterations/printed-bell-four-layer/reports/remaining-routing-inventory.json)
reconciles 25 disconnected nets to **41 opens**: nine GND, two VCORE,
and 30 across 23 other nets. It records actual pad groups, coordinates
and existing layer transitions. Power/return topology, USB, debug, I2S,
SCL/GAIN and clock/QSPI constraints remain reserved for root decisions;
low-speed controls are not automatically released into their corridors.

The subsequent [IMU local-return batch](routing-agent-policy.md#imu-local-return-closure-batch)
covered the existing IC4.1/2/3 and IC4.6/7 GND groups together.
Prefer short F joins to existing main ground; use only screened ordinary
off-pad vias if needed. Preserve the Mode-1 interface, current signal
copper, contact exclusions and all other design decisions. Stop on
obstacles requiring rerouting rather than expanding the scope.
Its blocked outcome is recorded above; the accepted board remains **41 opens**.

**Current accepted checkpoint: 41 opens.** Astra accepts exact PCB
`c7b6b6fdb9857f7ea993e3cad37c04e852981eceea5146802cadb35865b2cec7`,
manifest `08bf866d80f74775ff4099e4734da0d445fd359843f61637bf453abf002fe667`.
The [C24 acceptance and treatment record](../hardware/handbell/iterations/printed-bell-four-layer/reports/c24-filled-via-acceptance.json)
adds only via `fa83a8ab-a7d3-5826-adce-43ff4f25a03d` at
(92.004083,93.491669), 0.60/0.30 mm. It connects C24 ground without
changing the original land/apertures or F/In1 filled geometry.
All prior groups/private returns remain intact.

This via requires resin fill, planarization and copper capping in addition
to U4's four vias; the source-bound instruction must accompany quotation
and fabrication data because no native treatment flags were added.
Supplier, registration, flatness, stencil, yield and cost are still open.
The local supply-ground connectivity batch is complete, not all board
ground or power routing: nine GND and two VCORE opens remain.

The subsequent read-only inventory and next released batch are recorded
above. Earlier entries below are historical.

**C24 centered via feasible; one staged trial released:** the
[native feasibility report](../hardware/handbell/iterations/printed-bell-four-layer/reports/c24-via-in-pad-feasibility.json)
finds that the existing Default-class 0.60/0.30 mm through-via fits C24.2's
0.60 mm square copper exactly and passes all-layer clearance, drill,
contact and main-In1 screens. Its nominal drill annulus is 0.15 mm.
The 0.604/0.35 mm option exceeds the land by 0.002 mm radially and is
rejected. No board changes occurred during the study.

Astra releases one [centered filled/capped GND-via trial](routing-agent-policy.md#c24-centered-filledcapped-ground-via-trial),
with no part, track, pad, mask or paste changes. This via requires explicitly
named resin-fill/planarization/copper-cap treatment; tenting is insufficient.
Supplier registration, capping/flatness, stencil, yield and cost remain
unqualified. Full saved-candidate evidence and root review are still needed
before promotion. The accepted board remains **42 opens**.

**C24 ordinary local attempt blocked:** the
[bounded closure screen](../hardware/handbell/iterations/printed-bell-four-layer/reports/c24-ground-closure.json)
found no passing proposal among four F bridges and 48 whole-island
ordinary-via sites. The nearest main-ground gap is now 0.675778 mm,
but its bridges cross local +3V3 copper; vias are constrained by SCL,
SDA, power copper, drills and rear-contact metal. No candidate, refill
or design change occurred; the accepted board remains **42 opens**.

Next is a [read-only filled/capped through-via feasibility review](routing-agent-policy.md#c24-filledcapped-through-via-feasibility-review)
at C24.2's exact pad centre, using only the established 0.604/0.35 mm
and Default-class 0.60/0.30 mm definitions. Check native pad containment
and all-layer obstructions before considering that process; do not assume
via-in-pad solves a back-layer collision. Existing U4 process requirements
are not proof of C24 supplier acceptance or unchanged cost. No routing,
pad/paste changes, blind vias, rule reduction or fabrication is released.

**Current accepted checkpoint: 42 opens.** Astra accepts exact PCB
`834086079bc792165adcf642d41f3fd52c65446a355904934fcdf39b289227eb`,
manifest `054f203553f7051e12f098acac9683539488e77e4a42266439b48c519dbf39dd`.
The [paired C12 acceptance](../hardware/handbell/iterations/printed-bell-four-layer/reports/c12-paired-feed-acceptance.json)
replaces only the upstream F supply feed with a 0.25 mm F stub, one
ordinary +3V3 via and a 0.5077 mm In2 connection. The local capacitor/MCU
branch is unchanged. Refill joins C12 ground; all prior connections and
private pickoffs remain intact. In1 stays connected around the reviewed
local antipad, and remote cache differences are bounded to at most 1 IU.

The subsequent [bounded C24 ground closure](routing-agent-policy.md#c24-local-ground-closure)
attempt is recorded above. C24 is the remaining
unresolved group from the local supply-ground batch, not the last board
ground connection. VCORE/other routing, stackup, CAD binding, parity and
manufacturing gates remain open. Older entries below are historical.

**C12 access review complete; next paired trial:** the
[whole-island screen](../hardware/handbell/iterations/printed-bell-four-layer/reports/c12-island-access-review.json)
found no passing site among 38 geometry-derived ordinary-via proposals.
The 2.353169 mm2 C12 F island is constrained by multiple power, USBBOOT,
SCL and VHI items. This is not global impossibility, nor proof that
another USBBOOT move would be sufficient.

Astra's next [bounded paired trial](routing-agent-policy.md#c12-paired-supply-feed-and-ground-closure-trial)
replaces the necessary long upstream F +3V3 feed with a short connection
to the existing In2 supply bridge, while preserving the local capacitor/
MCU branch. It tests nine specific ordinary +3V3-via sites, not another
GND-via sweep. That may free the measured C12 ground bridge. No deletion
is acceptable without restored supply and actual C12 ground closure.
The new power via's local plane antipad must be reviewed; all existing
private returns, contacts, components and other routing stay protected.
The accepted board remains **43 opens** pending the staged result.

**Current accepted checkpoint: 43 opens.** Astra accepts and promotes exact
PCB `01a943c795ba97246c9681ad64088dfeb68ca94008cc9f08081d4c4f90789b00`,
manifest `d69d1ae6267eafe5976e528fd47d30cbed81ff01df058dbceca9d9c6cdc49b8c`.
The [C23 acceptance record](../hardware/handbell/iterations/printed-bell-four-layer/reports/c23-usbboot-acceptance.json)
binds the complete saved-candidate evidence. The local USBBOOT move to In2
connects C23 ground without new vias or component moves; path length is
unchanged. All previous groups/private returns survive. Remote F comparison
components require at most 2 IU of native opposite-fill inflation, within
the 10-IU limit, and preserve actual clearances. In1 is unchanged.
The earlier failed fragment-intersection mechanism remains unknown;
electrical attachment is established from actual board-island connectivity.

The subsequent read-only C12 ground-island review is complete; its result
and the next specifically released scope are above. C24 and remaining
VCORE/routing, stackup, CAD binding, parity and manufacturing gates remain
open. Earlier entries below are historical.

**Owner-authorized completion of missing C23 gates:** the owner selected
"Finish missing gates using actual board-island connectivity." Electrical
attachment is to be proved by the qualified graph of actual saved filled
islands and primitives, not by treating each Boolean-difference sliver as
an independent copper island. Retain the separate 10-IU displacement,
actual clearance and final DRC/connectivity requirements. One six-minute
completion item, with at most two corrective retries, is authorized.
No routing, refill or clearance relaxation is permitted; promotion still
requires root review. The accepted board remains at **44 opens**.

**Preserved second stop; not promoted:** isolated native API controls
[passed](../hardware/handbell/iterations/printed-bell-four-layer/reports/c23-usbboot-validation-controls.json).
The [saved-candidate review](../hardware/handbell/iterations/printed-bell-four-layer/reports/c23-usbboot-validation-final.json)
now proves source/zone preservation, all 130 previous connected pad groups,
only the intended C23/main-GND merge, both private-terminal cuts, no graph
shorts or floating copper, and per-layer clearance/guard/contact invariants.
It then stops while trying to associate a microscopic Boolean-difference
fragment with a filled GND island. The complete displacement and final
DRC-reuse gates are not recorded as passed. The repair retry budget is
exhausted; execution stopped until the owner authorization recorded above.

The exact unaccepted board is now durably archived as
[`reports/c23-usbboot-staged.kicad_pcb`](../hardware/handbell/iterations/printed-bell-four-layer/reports/c23-usbboot-staged.kicad_pcb),
SHA-256 `01a943c795ba97246c9681ad64088dfeb68ca94008cc9f08081d4c4f90789b00`.
This is evidence, not a second active design or a standalone project:
its matching project/libraries are bound in the review report.
The active PCB remains `7927882f...` at **44 opens**.

Root assessment: a Boolean-difference fragment is a comparison artifact,
not necessarily a separately representable copper island. Its failed
intersection must not override or silently replace the full saved-board
connectivity evidence. The cause of that failed intersection is still
unproven. The now owner-approved next item uses the complete
native filled-island graph for electrical attachment, retains the independent
10-IU displacement and actual clearance requirements, and finishes only the
missing gates. Do not reroute, refill, relax clearances or restart a general
geometry-tool investigation.

**Owner-authorized validator repair:** after the failed final-gate item,
the owner explicitly selected "Repair validator in isolation, then
validate the saved candidate." One new bounded validation-only item is
released: exercise unit conversion, artifact binding and new native
geometry operations on positive/negative controls first, then run the
complete saved-candidate gates. Limit the item to ten minutes and at most
two corrective retries. No rerouting, refill, rule changes or promotion
is authorized. The board remains at **44 accepted opens** until the
43-open staged candidate completes review.

**Preserved failed final-gate attempt:** the
[final-gate attempt](../hardware/handbell/iterations/printed-bell-four-layer/reports/c23-usbboot-final-gates.json)
completed only input/dependency binding. A saved-DRC path error consumed
the allowed correction; the corrected validator then called
`pcbnew.IU_PER_MM`, which KiCad 10's Python module does not expose.
The displacement, clearance, full connectivity, private-return and
source-preservation gates in this item did not run. This is an incomplete
validator, not evidence of another board defect. No copper, fill, manifest
or candidate bytes changed. Accepted PCB `7927882f...` remained at
**44 opens**; staged `01a943c7...` remained unaccepted at its previously
recorded 43 opens. The correction loop stopped for owner direction;
the separately authorized next item is recorded above.

**C23 refill-control review:** the
[identical-recipe no-routing control](../hardware/handbell/iterations/printed-bell-four-layer/reports/c23-usbboot-refill-control.json)
reproduces the accepted F/In1 geometry exactly. Candidate remote changes
are five microscopic boundary components totaling 0.0000002468985 mm2,
not a substantive remote copper addition. The native cause remains
unproven. Area alone is insufficient for acceptance: the final saved-board
review must bound each remote boundary change to at most 0.000010 mm
(10 native coordinate units), retain actual clearance/private guards,
and complete any acceptance gates skipped after the original locality
exception. This bound is only for these five source-bound cache changes;
it does not relax any design rule or establish a manufacturing tolerance.
No rerouting, refill, fill splicing or promotion is authorized during
that review. The accepted board remains at **44 opens**.
The corridor report now redacts its personal session path and records its
original execution-report hash; earlier references to that hash remain
historical evidence, not claims about the redacted file's current bytes.

**C23 trial, not accepted:** the
[staged corridor report](../hardware/handbell/iterations/printed-bell-four-layer/reports/c23-usbboot-corridor.json)
records a proven five-track USBBOOT chain replaced by two In2 segments
between existing vias. Both paths are 6.454773 mm; the replacement is
0.20 mm wide. Refill connects C23 to main GND without an extra bridge:
43 opens, 233 warnings, no new non-open findings, unchanged In1 fill,
and C24 still separate. However, F fill has a 3.347430 mm2 symmetric
difference (predominantly local added copper) with bounds
extending to x114.733807, outside the authorized local corridor.
Candidate `01a943c795ba97246c9681ad64088dfeb68ca94008cc9f08081d4c4f90789b00`
is therefore held, not promoted. The accepted board remains
`7927882f...` at **44 opens**. Next is a bounded no-routing refill control
on that exact accepted source, using the candidate's identical recipe,
to separate baseline refill changes from routing-induced changes and
identify every remote changed region. No further copper edits or fill
splicing are authorized by this diagnostic item.

**Current engineering decision:** the
[exact cut analysis](../hardware/handbell/iterations/printed-bell-four-layer/reports/remaining-ground-cut-review.json)
shows that deleting the named +3V3 blocker disconnects C12.1/IC1.10.
Keep that feed. USBBOOT has existing layer transitions on both sides of
the C23 obstruction; SCL at C24 does not. The staged trial followed the
[USBBOOT corridor relief](routing-agent-policy.md#usbboot-corridor-relief-for-c23):
prove and replace only the unbranched F chain between the two specified
existing vias with In2 copper, then close the measured C23 ground gap.
No new vias, part moves, C12 supply change, C24 SCL reroute or USB data-pair
change is authorized. The accepted board remains at 44 opens until the
complete staged result passes review.

**Remaining-ground obstacle review:** all three groups have native F filled
islands close to main GND, but their nearest boundary bridges cross fixed
copper. C12's 0.5788 mm gap crosses F +3V3 track `a869dd24...`, not the
new In2 bridge. C23's 0.5788 mm gap crosses two USBBOOT tracks. C24's
1.391996 mm gap crosses SCL/USBBOOT and two plated vias; contact metal
also rejected some candidate sites.
The [source-bound review](../hardware/handbell/iterations/printed-bell-four-layer/reports/remaining-ground-obstacle-review.json)
did not authorize obstacle removal. The subsequent read-only cut analysis
and local USBBOOT/SCL transition inventory informed the engineering
decision above. The accepted board stays at 44 opens.

**Latest radial-batch decision:** the
[336-site follow-up](../hardware/handbell/iterations/printed-bell-four-layer/reports/supply-ground-radial-batch.json)
produced a validated candidate closing C4, shared C11/C15 and U2 ground
groups. Astra approves exact PCB
`7927882fa05f05411c6bf9e12782326f55572aa0b450cc2e26e9ea534ab3add7`
for promotion: **44 opens**, 233 warnings, unchanged F/In1 fill geometry
and preserved prior connected groups/private pickoffs. It adds three
off-pad 0.604/0.35 mm through-vias and 0.30 mm F stubs of 0.80, 0.80
and 1.05 mm. This is not local high-frequency or manufacturing qualification.
C12, C23 and C24 had no feasible site in their fixed 48-site sets.
Next: review their exact obstacles and possible existing-copper access,
not another unguided sample sweep or automatic component move.
Promotion is complete with manifest
`a7a04cc74f0b487beda240c9b868dec54afbe32cd60fa003ec9e6578bc8717e7`;
the [acceptance record](../hardware/handbell/iterations/printed-bell-four-layer/reports/supply-ground-radial-acceptance.json)
binds exact saved bytes and reused evidence. This supersedes the older
47-open and 48-open states below; those remain historical checkpoints.

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
