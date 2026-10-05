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

**Current October 5, 07:58: stop after three failed static attempts.**
The [completion ledger](measurements/2026-09-27-router-bakeoff/quilter-input-completion-2026-10-05.json)
records partial reservation encoding but no complete r3 pair or native
execution. The checker needs both representation normalization and
missing independent outline/zone/profile/plane comparisons; its nominal
mutation helper mutates nothing and has no accepted result. Final code
is archived privately. Source/r2 remain unchanged; r2 stays held.
Executor exited07:54:35. A new bounded checker completion requires
authorization; remaining wall time does not renew the exhausted retries.

**Historical authorization October 5, 07:50:** finish the paired-input implementation gaps
under a new bounded authorization. Same verified Sol/medium executor
adds native F footprint-only MH1/MH2/J1/J2/X6 reservations and source-bound
semantic matchers/negative controls on preserved r3 derivatives.
Execution08:02/report08:03/root08:05, initial plus two corrections.
Expanded209/164 screening and finding disposition remain in this finite
completion scope if time permits. No source-native edit/load, refill,
routing or cloud; r1/r2 stay immutable and upload remains held.

**Prior October 5, 07:48: paired inputs constructed, not usable yet.**
Preserve [r2 and its source-bound ledger](measurements/2026-09-27-router-bakeoff/quilter-input-construction-2026-10-05.json).
Native counts104/325/209 and final manifest hashes are recorded, but
MH1/MH2/J1/J2/X6 native reservations and semantic preservation matchers
are incomplete. Expanded209/164 screening and finding disposition remain.
Contact flags/core types were corrected without source changes; four DRC
was not repeated, six has317 findings/184 opens. All three attempts are
exhausted; executor idle since07:46:19. No preview/upload/submission release.
One future bounded completion should target these exact encoding and
comparison gaps, not restart the source-selection or placement search.

**Historical authorization October 5, 07:36:** owner explicitly requests the two input
packages. This new construction item may generate isolated full
four/six derivatives from the selected209/32/72 contract, then load/save/
reload and run bounded native diagnostics on those derivatives only.
Verified Sol/medium`bbf4e823...` stops07:47/report07:48/root07:50.
Source-native loads/edits, refill, routing and cloud actions are excluded.
Constructed, native-checked and preview-qualified are separate outcomes;
preserve partial files and name any remaining gate rather than call a
parseable file usable by default.

**Prior October 5, 07:28: clock selection accepted; full trial NO-GO.**
The [current-source recovery](measurements/2026-09-27-router-bakeoff/quilter-preserved-clock-boundary-recovery-2026-10-05.json)
closes pad binding and self-contained local signal/return paths. Select
209 primitives,32 fixed references/164 pads and72 eligible for comparison
preparation only. Ordinary interfaces carry source terminal/net restoration
duties, not preservation of every old fanout or saved-pour contact.
No new source or PCB bytes. The common allowed-F/electrical encoding,
expanded209/164 coverage and two complete native inputs remain missing.
Stop the owner-approved capped attempt early rather than launch another
repair chain. The next separately scoped deliverable is common-input
implementation and qualified previews, not more clock inventory.
No source change, full input generation, cloud job or new executor item
is released by this no-go. See the
[stage/readiness table](quilter-workflow-study-2026-10-02.md#october-5-budgeted-path-to-a-useful-experiment).

**Prior October 4, 21:26: HOLD.** The preserved-clock packet retains
exact membership facts but does not qualify the proposed209-copper/32-fixed
block. Y1 case-pad coordinate rebinding and complete external conductive
contacts remain unclosed; an endpoint-only screen is insufficient.
Both corrections are exhausted, with final child completion21:24:52.
No demonstrated PCB defect; keep177 and27/77, source and experiments.
A new bounded endpoint/boundary-proof authorization is required before
further execution. No native retry, full input, cloud job or integration.
See the [held ledger](measurements/2026-09-27-router-bakeoff/quilter-preserved-clock-qualification-2026-10-04.json).

**Prior authorization October 4, 21:14:** owner explicitly selects a bounded qualification
of preserved IC1/Y1/R6/C2/C3 for the first four/six comparison. Verified
Sol/medium continues the reviewed clock task through21:25,
report21:26/root21:29. Qualify complete clock signals, finite local returns
to actual P$1 and external restoration duties before expanding177 or
applying the prospective32/72 partition. No hidden movable-pad dependency,
whole-GND retention, extra frozen references, native load, source change,
full input or cloud job. This would not test MCU relocation.

**Prior accepted October 4, 19:40:** source clock bindings are accepted from one
0.86s static extraction: all eight terminals on three signal nets, correct
R6 ends, C2/C3 loads and Y1 case grounds. Source is unchanged; executor idle.
The [clock ledger](measurements/2026-09-27-router-bakeoff/quilter-clock-relative-contract-2026-10-04.json)
does not complete the engineering acceptance contract. Next reconcile
clock reference/return intent with the intentional In1 pour hole and
choose justified study screening criteria. Native pad numbers, schematic
names and imported PIN tokens remain separate; ground-tied TESTEN19 is
not a true MCU return terminal. No more inventory, source/candidate change,
automatic MCU freeze, added retention or cloud release.

**Prior October 4, 19:27:** read-only domain disposition finds an
additional relative-placement path: Custom Component Proximity, explicitly
best effort, with parent-pin/max-distance fields but no child-pin field.
Existing-job timing fields likewise do not prove actual availability or
execution. Do not use the10mm UI default as an engineering threshold.
The known R6 oscillator limitation remains. Next bind source
IC1/Y1/R6/C2/C3 terminals and independent clock/return/exclusion obligations,
not more arbitrary rooms, an MCU freeze or automatic added retention.
See the [disposition](measurements/2026-09-27-router-bakeoff/quilter-movable-domain-disposition-2026-10-04.json).
Physical domains and complete electrical/native/import gates remain open;
no source edit, full input, cloud object or new job.

**Prior accepted October 4, 19:15:** the isolated F-room native serialization
control passes on returned`3a5f6d89...`: one new all-clear room, all58
original subtrees/guards/fills intact, complete new-room equality and
unique UUIDs. Two child import failures preceded the successful third
attempt; receipts and recovered exact failed scripts are preserved.
No fourth run. The executor is idle and all five source hashes unchanged.
See the [control ledger](measurements/2026-09-27-router-bakeoff/quilter-f-placement-region-native-control-2026-10-04.json).
Next is source-bound movable-domain requirements/representation from
existing evidence. Actual product domains, importer association and
body/rotation/F-only placement remain unqualified; no full input or cloud.

**Prior October 4, 19:06: common F-height class simplified.**
The+2mm height screen's only nonpositive cases, L1/X6, are both fixed under
the current27/77 partition. Eligible fitted movers need no tall-part class,
but this does not establish a whole-body/access domain. The subsequent
native F-room serialization control is now qualified above, with all
restrictive source guards preserved.
No full input, cloud upload or placement/routing job. Canonical new-via
fields are synchronized to0.650/0.350mm with0.150mm minimum ring.

**Prior October 4, 18:56:90-ohm intent retained; current-client path identified.**
The [capability disposition](measurements/2026-09-27-router-bakeoff/quilter-usb-impedance-capability-2026-10-04.json)
finds numeric frontend entry rather than an85/100-only selector. Actual90
persistence/solving remains unverified; saved100-ohm results are not a proxy.
Continue independent local domain/profile qualification, then require
nonstale90-ohm per-layer results on each qualified preview before submission.
No duplicated job, new input, recompute request, substitution or source edit.
Full native/import findings and returned-object/fill checks remain gates.

**Prior October 4, 18:42: study roles and retained-via geometry selected.**
The [role decision](measurements/2026-09-27-router-bakeoff/quilter-four-six-role-selection-2026-10-04.json)
selects real JLC 3313 S/G/S/S and S/G/S/G/G/S constructions, not generic
four/six presets. The [13-by97 screen](measurements/2026-09-27-router-bakeoff/quilter-retained-via-pad-process-screen-2026-10-04.json)
finds no fixed-land overlap for the other13 retained vias. Their mask/
assembly treatment remains unqualified; preserve all18 vias and the five
required filled/planarized/capped seeds. New ordinary starting geometry
is0.650/0.350mm with0.150mm ring, not a source resize or global-rule waiver.
The subsequent USB capability/engineering disposition is above:
documented85/100-ohm choices do not establish support for our90-ohm target.
No unsupported substitution, manual routing, source change, full input or
cloud job. Movable domains and complete native/import/output gates remain.

**Prior October 4, 18:26: native rectangles selected after owner continuation.**
The [encoding decision](measurements/2026-09-27-router-bakeoff/quilter-native-guard-encoding-2026-10-04.json)
selects the existing 18/22 guard obligations and preserves the exact eight
additional rectangle-only retained intrusions. No source copper changes.
The private measurement script's unexecuted controls and unimplemented
matcher remain unqualified; actual layer order reuses older exact-file
evidence. Its three launcher attempts are exhausted, with no rerun.
The subsequent layer-purpose/minimum selection is recorded above.
Full movable domains, complete native input
findings and new/changed returned-object/fill checks remain before jobs.

**Prior October 4, 18:00: bound obstacle coverage accepted; hour closes.**
The [coverage ledger](measurements/2026-09-27-router-bakeoff/quilter-private-guard-candidate-coverage-2026-10-04.json)
qualifies the exact 177 retained primitives and 97 native fixed pads.
It closes the upstream pose/layer-coverage gap without new collateral
contact: 42 prior pairs remain, four wrong-pose false positives disappear,
and 18 self pairs are recorded separately. Existing terminal-bank joins
and DOUT's valid 0.212066 mm copper gap are unchanged.

The three supervised executions are complete; no further run or new
engineering item starts this hour. The 37-open source and all experiments
remain preserved. This is source-bound geometry, not generic shape-engine
qualification: degenerate roundrect narrow-phase handling needs a separate
correction/test before such a pad becomes a nearby candidate; it does not
affect this exact run's enclosing bounds or surviving pairs.

Next, on continuation, select the native guard representation and exact
retained-source intrusion contract for the four private pads, six private
tracks and two private vias. Expected output is an encoding disposition,
not a changed board: no blanket same-net waiver, feed removal or automatic
input/upload. Movable placement domains, supplier layer purposes/processes,
functional grounding and full native/importer gates remain separate.

**Earlier 17:26 local plane control accepted; current hour ends18:11.**
No new item after18:01. The
[plane ledger](measurements/2026-09-27-router-bakeoff/quilter-private-plane-control-2026-10-04.json)
qualifies4/8 isolated four/six-layer private-via cases at0.250000mm and
one missing-In3-guard negative with direct fill contact. Saved source-subset
records and physical layer order reconcile. An anchor VIA proves local
nonempty-fill contact, not functional grounding. Three native attempts
are exhausted, with no rerun. The collateral/retained-join item and its
coverage follow-up are now completed as described above. No source-native load/edit,
full product input, routing, cloud job or manufacturing release.

**17:01 finite tool completion accepted:** ten supervised regressions
and one corrected-revision native replay pass. Eight pad records/four
pose witnesses and23 rule areas match; the2.468-second DRC differs from
the first diagnostic result only in date. Actual revision snapshots,
receipts and unchanged source hashes are verified in the
[completion ledger](measurements/2026-09-27-router-bakeoff/quilter-native-tool-completion-2026-10-04.json).
The tooling blocker is closed. Next engineering work must address full
guard representation/retained-copper treatment, fill isolation and
six-layer mapping before full inputs/import qualification. No product
rules, full input, routing, cloud job or fabrication is released.

**Historical16:36 tool repair partial, stopped:** native UUID/pose readback and
diagnostic DRC now complete on the isolated fixture, but root review
required two code corrections. Five subprocess controls pass; missing
fixture mocks and a native replay of the final revision still prevent
reusable-tool qualification. Next is that finite completion item, not a
fresh inventory or product run. Preserve all evidence/source; no full
input, six-layer/fill, routing or cloud release. See the
[repair scope and result](quilter-workflow-study-2026-10-02.md#october-4-1636-bounded-native-tool-repair).

**Current-coordinate process-hole screen accepted:** the
[spacing ledger](measurements/2026-09-27-router-bakeoff/quilter-process-hole-spacing-screen-2026-10-04.json)
binds five required processed vias against eight drilled component pads
and13 other retained vias. Conservative full-copper/pad gaps exceed0.45mm
in all40/65 pairs; minima6.907610/13.543012mm. All source hashes remain
unchanged. This is not cap/planarity, supplier acceptance, future-geometry
or other-via process qualification. One static run completed, but no hard
timeout was evidenced; the ledger distinguishes initial wait from a limit.
The separately authorized native-runner/UUID/DRC recovery is now bounded
above. No input generation or cloud job follows from the spacing result.

**Supplier screen complete, constructions not selected:** the
[source-bound comparison packet](measurements/2026-09-27-router-bakeoff/quilter-four-six-stackup-source-screen-2026-10-04.json)
supplies actual3313 dielectric/copper rows and POFV conditions. Exact hole
spacing interpretation and cap/planarity remain open; published size/ring
ranges and the subsequent current-coordinate clearance screen do not
qualify manufacturing. The native guard blocker
below is not waived, and no source/input/cloud changes are released.

**Native-control gate held:** [1fd27e9d...](measurements/2026-09-27-router-bakeoff/quilter-private-guard-native-control-2026-10-04.json)
establishes static source-subset preparation and native load/save, not
complete roundtrip or rule behavior. UUID lookup is incomplete and CLI
DRC times out at30 seconds. All three old attempts are consumed; preserve
evidence. The new16:36 repair has its own bounded authorization, not a reset
of those attempts. Analytic guards and selected177 remain unchanged.
Supplier evidence does not release either full input past the native gate.

**14:20 continuation:** another owner-authorized hour ends15:20, with
no new item after15:10. First is isolated native guard-encoding/behavior
qualification of the repaired source subset, not a full-board input.
Analysis14:32/report14:33/root14:35; three90-second attempts maximum.
Native fixture-only saves/loads and diagnostic fail probes are allowed;
authoritative source edits, product routing and cloud jobs are not.
Native behavior, importer enforcement and selected supplier constructions
remain distinct gates even if four/six logical fixture layers pass.

**Current checkpoint: analytic private guards selected after repair.** The
[native-oracle repair](measurements/2026-09-27-router-bakeoff/quilter-private-tap-guard-repair-2026-10-04.json)
resolves the pad-transform blocker without another KiCad load. Root selects
the corrected specification only; source177 retention is unchanged and
native serialization/behavior and Quilter enforcement are not qualified.
Two static executions completed; the failed proposal stays preserved.
Stop at this checkpoint under the existing hour. Next is one bounded
isolated native guard-encoding/behavior control, with no full-board staging
or new job. Actual supplier stackups, movable domains and importer
qualification remain necessary for comparable four/six-layer packages.

**14:07 recovery released:** the owner explicitly asks to continue unblocking
and preserve reusable staging/gating strategies toward a four/six-layer
comparison. One checker-only repair uses already-saved native global pad
geometry, with independent all-endpoint and signed-quarter-turn witnesses.
Analysis14:14/report14:15/root14:19; three90-second executions maximum,
zero native loads, no new downstream item after14:09. This does not
release a full input or job. Both future layer packages require the same
common requirements and independent native/import/process qualification.

**Historical stop: private-guard geometry is invalid.** Root rejects the
[guard proposal](measurements/2026-09-27-router-bakeoff/quilter-private-tap-guard-definition-2026-10-04.json)
after saved native coordinates expose opposite-pad placement for R26.2
and C28.2. This is our checker failure, not evidence against Quilter.
Three analyzer attempts are exhausted; no fourth run or corrected guard
generation is released by the remaining hour. Source and selected177
are unchanged, and the executor is idle. Next requires a separately
authorized checker-only repair using saved native coordinates, quarter-turn
cases and actual private-track endpoint witnesses before any guard coverage
claim. No native inventory rerun, full input, routing or cloud job.

**Historical13:19 owner continuation:** stop14:19 local and start no new item after14:09.
First define and statically qualify the COUT replacement/retention contract,
including R29's parallel discharge duty, the exact177 retained primitives
and all-three-terminal output restoration. Same verified Sol/medium;
analysis13:31/report13:32/root13:34, initial plus two corrective attempts.
No new native disposition run, source edit, manual repair, generated input
or cloud submission is released. Proceed only through reviewed dependencies.

**13:29 conditional177 selection:** the
[static contract audit](measurements/2026-09-27-router-bakeoff/quilter-prot-cout-release-contract-2026-10-04.json)
qualifies exact membership and restoration semantics. Root selects that
definition for subsequent input qualification, not actual copper removal,
board generation or returned-route acceptance. Preserve all27 fixed refs,
five seeds,30 feeds and non-COUT connections; restore U6.2/Q5.B2/R29.1
and retain R29.2/PROT_FET_RETURN. The measured source floor is0.1778 mm,
subject to stricter selected fabrication rules and later route review.
Its private-tap guard dependency is now held as recorded above. Keep the
actual-conducting-layer policy; do not copy F-only exclusions blindly into
inner planes. Full geometry, stackup/process and native/import gates remain.

**Historical12:57 stopping checkpoint:** the
[PROT_COUT source disposition](measurements/2026-09-27-router-bakeoff/quilter-prot-cout-retention-disposition-2026-10-04.json)
proves neither the offending via nor the complete five-object B branch is
redundant. Either omission disconnects U6.2 from Q5.B2/R29.1 and leaves
old dangling copper. Root's recommended next study is whole-net routing
release with every terminal restored; hypothetical retained177 is not an
approved input or permission to remove copper. COUT is charge-FET control,
not load-current routing, and R29 is a parallel high-value discharge path.
Complete212 remains held; source is unchanged and executor idle. No further
item is released this hour. Next bounded item on continuation: qualify the
one-net electrical/layer/contact/private-guard and restoration contract,
without moving contacts, weakening clearance or resuming manual routing.

**Historical12:10 owner hour:** stop13:10 local, no new item after13:00.
Begin the separately bounded complete-retention/interface-model recovery:
proposed186 plus five process seeds and retained pads, explicit contact
controls and the C28.1/VAMP local bank interface. Same verified Sol/medium;
analysis12:22/report12:23/root12:25, at most three90-second native runs.
This supersedes the execution hold only for the new reviewed scope.
Source, physical/input qualification and cloud/payment gates remain intact.

**12:45 retained-copper contact blocker:** the
[static screen](measurements/2026-09-27-router-bakeoff/quilter-critical-retained-contact-screen-2026-10-04.json)
finds `/PROT_COUT` via `2f82654e...`0.225 mm from the nominal BT2 base,
0.025 mm short of the0.25 mm requirement. This flat-side witness is not
merely conservative corner expansion, but no nominal metal overlap exists.
Complete212 is held; do not repair, move/remove copper, waive isolation
or proceed to input generation. One static run/zero native loads; all
five mandatory process seeds clear all eight guards. Next is bounded
read-only source-role/dependency analysis of the exact PROT_COUT route.
Private guard, placement/process and input qualification remain blocked
dependencies, not automatic work to run past the conflict.

**12:34 GND/V+ interface disposition:** root provisionally retains the18
whole-source additions in the
[interface report](measurements/2026-09-27-router-bakeoff/quilter-critical-ground-input-interfaces-2026-10-04.json)
and existing1.0 mm,8.061 mm GND feeder `3598d04b...`: complete planning
union212 including five process seeds, plus97 pads on27 proposed fixed refs.
No clipping, new fixed parts or global-network retention. Q1 remains
movable and its old `fce9acd5...` feeder remains unselected; ordinary net
restoration is not a demand to preserve every old connection coordinate.
The runner now proves numeric0/nonzero/timeout capture; all three native
loads exited0. This item is exhausted and source is unchanged. Next is a
bounded nominal contact-metal screen of the complete212 B copper/via
annuli, not generation or approval of a full-board input. Private same-net
tap prevention, placement/process and native/import gates remain.

**12:22 recovered VAMP interface:** root provisionally selects the two
complete source takeoffs identified in the
[report](measurements/2026-09-27-router-bakeoff/quilter-critical-interface-recovery-2026-10-04.json),
including the8.132 mm,1.0 mm-wide feeder instead of clipping it or absorbing
the whole55-object network. Planning basis193 includes five process seeds;
97 physical pads on27 refs remain separately bound. No source/input change.
The item exhausted three executions/two loads; numeric exit codes were not
retained, although final terminal output and artifacts exist. Preserve that
limit, stop this item's executions and preflight exit capture before the
next distinct GND/V+ interface disposition.

**October 4 physical-cut stopping point:** the bounded item exhausted
three attempts and returned partial evidence, not a retained-input approval.
The [report](measurements/2026-09-27-router-bakeoff/quilter-critical-physical-attachments-2026-10-04.json)
qualifies complete BOOST_SW inventory and proposes one existing 1.2 mm
track addition for union186. The rest remains held: process-seed geometry
was omitted from the subtraction basis, global endpoints were tested
against an overly restrictive single-land criterion, and tangency-only
graph contacts were not fully covered. These are qualification limits,
not proof of defective source copper or failed Quilter routing.
Stop native retries and preserve all source/raw evidence. The next item
requires a separately scoped, complete-retention/module-port review,
starting with the recorded C28.1/VAMP bus contact; no broad inventory loop,
source change, routing, input generation or cloud is released.

**Local-circuit selection evidence completed:** six source-local nets pass
the all-physical-pad gate, with 105 complete primitives including four
PROT_FET_RETURN vias. The [corrected report](measurements/2026-09-27-router-bakeoff/quilter-critical-local-retention-2026-10-04.json)
binds the 185-object combined proposal and 142 boundaries. Named global
paths are not yet physically retention-qualified. Nine per-duty attachment
candidates are not nine defects: some copper is already retained, and
multiple attachment UUIDs can share a physical junction.
Next inspect exact local parallel/attachment geometry and terminal
boundaries without widening the fixed set or retaining global amplifier
feeds blindly. Source, earlier reports and raw outputs stay unchanged;
no input generation, routing, repair, integration or cloud is released.

**Core-only review completed:** the corrected source-bound
[report](measurements/2026-09-27-router-bakeoff/quilter-critical-core-boundaries-2026-10-04.json)
confirms all five boost F paths, two private GND paths and five CELL_NEG
duties with 62 copper objects plus retained pads. A report-only correction
restored intermediate U6.4 pad copper to the R28 witness; no extra routing
or native rerun was needed. The 71 boundary edges and 52 lost internal
pad-pair relationships are not independent port/repair counts.
Current saved fills do not intersect the checked private objects; all 19
rules remain pours-only, without qualified projected coverage or future
private-tap prevention. Accept this evidence, not the retained set/27-77
partition. Next select named local input-power, feedback and protector
source paths while leaving ordinary global connections reroutable.
No source change, full input, repair, integration or cloud is released.

**Retention recovery completed:** eight preflight tests and one1.842s
native private-copy inventory now produce five required boost F paths
and both private GND pickoff witnesses. The corrected bindings no longer
block analysis. Root accepts the recovered evidence only:62 explicit-duty
objects versus113 all-pairs extras,264 graph boundaries, and coarse rule
touches do not yet establish an approved retained block. Next qualify the
core-only boundaries/private-pour treatment before27/77 approval or staging.
See the [recovery report](measurements/2026-09-27-router-bakeoff/quilter-critical-block-retention-recovery-2026-10-04.json);
source and all failed evidence remain unchanged.

**10:48 bounded recovery authorized:** owner permits repair/preflight of the
retention analyzer and a conditional read-only inventory retry, preserving
old failures. Same verified Sol/medium executor; analysis11:00, report11:01,
root11:03; at most three90-second native analyzer executions. No source
changes, save/refill/DRC, staging/cloud or automatic27/77 approval. The
earlier retry stop below is superseded only for this explicitly scoped item.

**October 4 retention inventory stopped:** three attempts failed on Python/
pcbnew ABI and type-specific width serialization. The desktop assertion was
our private child PID14516, terminated by its 90-second timeout; no Jenkins
service was used. All three child PIDs are absent and source hashes unchanged.
Preserve the [incomplete receipt](measurements/2026-09-27-router-bakeoff/quilter-critical-block-retention-2026-10-04.json).
No complete copper/port set or 27-fixed/77-movable partition is approved.
The next recovery needs separate bounded authorization and static/toolchain
preflight before native execution, not a fourth attempt under the old item.
The successful contact diagnostic remains qualified for its limited scope.

**October 4, 09:58 continuation:** owner permits approximately two hours
of sequential bounded work, ending by 11:58 with no new item after 11:48.
The first item **recovered native DRC** on unchanged isolated contact-output
copies: zero opens and 45 findings each. The
[native supplement](measurements/2026-09-27-router-bakeoff/quilter-contact-native-validation-2026-10-04.json)
separates 39 inherited, four returned-rule annular-ring and two new
isolated-fill findings. The subsequent
[saved-plane supplement](measurements/2026-09-27-router-bakeoff/quilter-contact-plane-isolation-2026-10-04.json)
passes 20/20 foreign-via isolation cases (minimum 0.206229 mm against
0.20 mm) and 20/20 GND seed attachments. Each plane is one nonempty island;
isolated-copper warnings reflect zero component GND terminals in the
truncated fixture. Root qualifies the retained-feed/guard routing
diagnostic only, not product/process/loaded-contact suitability or DRC
cleanliness. No refill, repair or source change. The common-input contract
now prefers two retained boost/protection cells, prospectively 27 fixed/
77 movable refs, with exact source copper/port qualification still required.
Next is that bounded retention/boundary inventory; staging/upload/submission
remains held. Via-family/ring compatibility and actual supplier stackups
remain explicit gates, not reasons to resize protected process seeds.
See the [continuation contract](quilter-workflow-study-2026-10-02.md#october-4-bounded-autonomous-continuation).

**Historical October 3: returned controls retained with a validation gap.**
Both native files preserve the input inventory and connect both test nets
entirely on B while clearing guards in the static geometry check. The
[output review](measurements/2026-09-27-router-bakeoff/quilter-contact-routing-output-review-2026-10-03.json)
records added In1/In2 GND fills and two 60-second native DRC timeouts.
This is useful routing evidence, not full native/plane acceptance and not
a demonstrated design failure. Preserve both candidates and the unchanged
37-open source. Next resolve the bounded native-validation blocker and
check inner-plane isolation; do not repeat Quilter, repair/merge or stage
the full board automatically.

**Latest: contact-routing diagnostic launched at 17:49 on October 3.**
The [job](https://app.quilter.ai/jobs/6ac19efbfc0d2d776ed14911)
was started once after explicit owner approval to rely on the published
free-personal policy without a displayed account-specific quote. The UI
confirms launch and work in progress; no payment or new terms appeared.
Six fixed components, eight pins and four pins to route remain bound by the
[control ledger](measurements/2026-09-27-router-bakeoff/quilter-contact-routing-control-2026-10-03.json);
no output has been reviewed. Next preserve native output and assess retained
objects/guards and new copper before routing benefit. No duplicate, broader
trial, repair, integration or automatic monitoring.

**Latest: corrected contact-routing input is qualified.** The approved
checker/report correction passes; static/native PCB bytes are unchanged.
The [control ledger](measurements/2026-09-27-router-bakeoff/quilter-contact-routing-control-2026-10-03.json)
releases only the exact native board/project pair for a separate diagnostic
setup and one reviewed, confirmed-free routing submission. No native rerun,
full-board staging, paid use, new agreement or fabrication.

**Latest: contact-routing control held at root witness review.** The saved
six-component native fixture preserves prior geometry, but its path checker
misplaces BT2's rotated pads and retains a stale import-only report statement.
Two corrections are exhausted; seek a bounded checker/report repair using
the saved native files. No upload, native rerun or source change is released
by the serialization result alone. See the
[control disposition](quilter-workflow-study-2026-10-02.md#1713-approved-contact-routing-control).

**Latest: separate diagnostic import preview completed.** Two files are
Parsed after reload; eight keepout lookup entries, two components/four pins,
zero to route. Stop here as requested: no submission or source changes.
The [next proposal](quilter-workflow-study-2026-10-02.md#contact-feed-import-preview-completed)
is a separately approved nonzero-work behavioral test with native-output
preservation/guard checks, not a full-board or zero-work routing run.

### Earlier checkpoints (historical; latest status above governs)

**Local contact-feed fixture qualification complete.** The owner-approved
next item is the separate diagnostic import preview using only the exact
board/project pair in the [import ledger](measurements/2026-09-27-router-bakeoff/quilter-contact-feed-import-2026-10-03.json).
Keep all intentional DRC contradictions visible and stop before submission;
no full-board or manufacturing acceptance follows.

**Owner approved preparation and import preview only.** Build/qualify the
small contact-feed variant, then upload its board/project to a separate
diagnostic draft, stopping before compilation/submission or payments.
Propose next steps at that stopping point. Local preparation starts
16:49:26, executor stops 17:01 and root checkpoints by 17:04; no source
edit or full-board staging. The prior read-only hold is superseded only
for this [bounded scope](quilter-workflow-study-2026-10-02.md#1635-quilter-diagnostic-readiness).

**Latest: read-only Quilter readiness check complete.** Authentication
works; no login needed. Public personal free use is reconfirmed, not an
account-specific price. No new cloud object, upload or submission exists.
Next proposed scope is a locally qualified contact-feed fixture and a
separate diagnostic draft/import preview, pending owner approval. Keep
that separate from actual routing-enforcement proof and the full-board
layer trials. See the [bounded scope](quilter-workflow-study-2026-10-02.md#1635-quilter-diagnostic-readiness).

**Latest: hybrid contact-feed candidate identified, representation gated.**
The read-only [feed selection](quilter-workflow-study-2026-10-02.md#existing-contact-feed-retention-candidate)
contains 30 B segments and five ordinary transition vias, not a new board.
All candidate vias clear nominal contact guards; the negative sense/supply
return branch serves C30.2/U6.4/R28.2. Keep it distinct from the R26/R27
private pickup. Inherited via sizing and preplaced-feed/all-track-keepout
precedence remain open. Next determine supported representation read-only
and separately scope any necessary import control. Preserve source and
experiments; no blanket-rule rerun, full staging or cloud release.

**Latest: native contact-fixture controls established.** Six rule
expectations and all five process-via keepout checks pass on the isolated
fixture, with limited serialization normalization and no source change.
The next engineering item is a read-only inspection of existing BT1/BT2
B.Cu feeds for a retained-block strategy; the blanket track guard remains
incompatible with an unqualified fresh contact feed. No actual-board
staging or cloud release. See the
[native evidence limits](quilter-workflow-study-2026-10-02.md#native-fixture-control-now-established).

**October 3, 15:46 static tooling recovery:** the repaired builder and seven
tests now produce a source-bound isolated text fixture without native loads.
The next allowed native scope is only that fixture's load/save and explicit
rule controls. Complete contact treatment remains unresolved: all four
pads are inside the blanket track guards, but pad copper does not cover
all contact metal. Preserve the source and require a reviewed retained-feed
or net-aware treatment before any complete input staging. See the
[current static checkpoint](quilter-workflow-study-2026-10-02.md#1546-resumption-static-builder-qualified).

**October 3, 15:33 native tooling stop:** both the surface-fixture attempt
and explicitly authorized parser repair exhausted their separate three-
attempt budgets without saving a fixture. No new electrical or Quilter
result is established. Source is unchanged; preserve both failed builders.
Next requires static/source-extraction qualification before another native
attempt, not automatic retry or whole-board staging. See the
[repair outcome](quilter-workflow-study-2026-10-02.md#152930-explicitly-authorized-parser-repair).

**October 3, 14:14 contact result:** nominal base/spring guards clear all
five protected vias, with three synthetic in-memory native collision
controls. This resolves the C24 projection conflict, not full input
qualification. The raw fragment still lacks native-origin conversion,
explicit complete flag controls and a save/reload proof; via-only rules
do not protect against foreign B tracks/pours or preserve intended contact
feeds by themselves. Initial plus two corrections are exhausted.
Next proposed bounded item is a BT1/BT2 surface-rule fixture, not whole-board
staging. Read the [exact evidence limits and height-datum correction](quilter-workflow-study-2026-10-02.md#bounded-result-and-exact-limits).
Accepted PCB/manifest and all experiments remain preserved.

**October 3, 13:46 concrete geometry result:** the
[D45/tongue outline fragment and reservation packet](quilter-workflow-study-2026-10-02.md#october-3-trial-envelope-engineering-review)
are retained as proposals. Source-edge containment and whole L1/mount
screens pass; no native input was staged. Next resolve the conservative
BT2 shadow versus protected C24 seed without deleting the via or waiving
isolation, and explicitly carry connector-access assumptions. Actual
C24-to-base clearance exceeds the required value by 0.393331 mm; the
coarse shadow overlap is not a short. Full contact/load/access and native
import qualification remain distinct gates. Source and cloud are unchanged.

**October 3, 13:20 resumed with packaging flexibility:** confirmed study
bounds are main PCB D43-45 mm and 0-2 mm additional board/speaker spacing.
The owner permits adapting all printed enclosure pieces after selecting a
worthwhile layout while retaining the general bell shape. Existing plastic
supports need not constrain every placement iteration. Real component,
contact/cell, hardware, insulation/load-path and mating/service requirements
remain; do not uniformly scale the board or physical parts. The next study
has completed four cheap endpoint calculations: D45 gives 9.52% more
nominal disk area and +2 mm leaves L1 as the only eligible fitted F part
without positive nominal magnet clearance. D45/+2 is the provisional
target for exact trial-domain qualification, not accepted geometry.
Use one shared qualified packaging envelope for four/six layers, not a
cloud-job matrix. Preserve accepted
source and all previous CAD; no manual routing or automatic integration.
See the [updated workflow](quilter-workflow-study-2026-10-02.md#october-3-flexible-packaging-study).

**October 3 mapping checkpoint:** authenticated browser observation works,
but no new cloud input/job was created. The saved partial mechanical
screen binds 104 references, nine fixed poses, five process vias and
current height/contact data; source hashes remain unchanged. Full
height-dependent support, hardware, loaded-contact and service envelopes
are still required before PCB staging. The next bounded item is a
read-only projection of the existing saved CAD, not an assembly rebuild
or another inventory. The local yoke planning station z19.3 must not be
confused with the complete yoke, whose saved geometry reaches z25.
See the [screen, limits and exact next input](quilter-workflow-study-2026-10-02.md#october-3-allowed-domain-engineering-disposition).

**October 2 recovered checkpoint:** the final bounded pass completed the
raw native inventory: 104 footprints, 325 pads, nine fixed poses, 95 eligible
movers, 81 F/two B fitted parts and five bound process vias. All four source
hashes remain unchanged. The 19 native rule areas prohibit pours only;
external mechanical/height/access allowed domains and relocated electrical
duties must be mapped before staging. No more inventory reruns, copper
removal, placement preparation or cloud jobs are released at this checkpoint.
Native work ended at 14:30:57, before the owner's 15:00 deadline.
See the [accepted raw evidence and next gate](quilter-workflow-study-2026-10-02.md#recovered-native-inventory-and-preparation-gate).

**October 2, 14:22 owner resumption:** a few bounded reruns are approved,
with work finished before 15:00 local. Recover the inventory first, with
at most three native executions in ten minutes and a 14:34 stop.
Stop starting new items by 14:50. No source changes or qualification-gate
waivers follow from this deadline extension. See the [completed recovery scope](quilter-workflow-study-2026-10-02.md#completed-bounded-recovery-scope).

**October 2 inventory stopping point:** the fresh-track native inventory
exhausted its initial attempt and two corrections with no inventory output.
Final failure: a KiCad via-accessor assertion and hard timeout. Root's
review additionally rejects name-only keepout classification, incomplete
polygon/fill handling and fitted-count/process-contact shortcuts.
The four source hashes are unchanged. No automatic retry, prepared input
or layer trial is released; a newly authorized bounded tooling repair must
precede further native work. See the [historical blocker](quilter-workflow-study-2026-10-02.md#historical-native-inventory-blocker).

**October 2 diagnostic checkpoint:** v1.2 improves saved-fill same-net graph
opens from 37 to 22 without a detected prior pad-group split; v1.1 regresses
to 38. Native DRC counts are 24/38 respectively, leaving v1.2's discrepancy
unreconciled. Foreign-net contacts and native shorts preclude acceptance;
raw counts also include inherited-via/rule mismatches and untested fill
cache effects. See the [source-bound diagnostic](quilter-workflow-study-2026-10-02.md#existing-output-diagnostic-checkpoint).
The separate native constraint inventory subsequently blocked as recorded
above; output cleanup remains unreleased.

**October 2, 14:05: personal workflow study approved.** The owner prioritizes
learning an efficient agent-plus-service process, not preservation of sunk
routing effort. Run bounded read-only diagnosis of v1.1/v1.2 and a separate
flexible functional-group engineering brief in parallel. Then qualify native
input/constraints before confirmed-free four/six-layer trials (eight optional).
The [study and exact next item](quilter-workflow-study-2026-10-02.md) preserve
fixed interfaces, five process vias, accepted sources and all experiments.
The output-rejection decision remains; no repair/merge, manual routing,
purchase, fabrication or powered use is released.

**October 2: both Quilter outputs rejected for integration at the preservation
gate.** Checked placement and all 325 native pad geometry/net records match,
but the original named In1 GND zone has no exact structural substitute and
all 24 original In2 segment records are unmatched (13 +3V3, 2 USBBOOT,
3 /IMU_INT2, 6 SDA). Four copper layers remain enabled; renamed layer
displays are not layer loss. Record differences are not lost-connection
counts, and zone structural differences are not an electrical-equivalence
proof. Native routing benefit was not measured after this stop.
The authoritative 37-open package and raw downloads are unchanged.
See the [corrected evidence, local artifact map and limits](agent-handoff-2026-10-01.md#october-2-bounded-preservation-result).
No repair, merge, rerun, support loop, manual routing or CAD work is released.
The October 1 running/waiting state below is historical.

**October 1, 16:02 local: Quilter running; transition to a new session.**
The owner reports the tool working and will supply results. No native
candidate has been received/reviewed. The canonical fresh-session entry is
[the detailed handoff](agent-handoff-2026-10-01.md): source hashes, local
artifact map, actual configured/inferred limitations, session identity and
the bounded preservation-first evaluation plan. Preserve raw returned files,
evaluate only in a new experimental directory, and do not resume manual
routing or merge a candidate automatically.

**October 1: proceed to a disposable Quilter diagnostic, not another support
loop.** Downloaded job inputs match the authoritative PCB/schematic/project
byte-for-byte. Latest inferred constraints remain incorrect in the previously
recorded ways. The owner prefers observing tool output; one free as-configured
run can measure preservation and connectivity, with both existing GND pours
selected. No job submission is confirmed. This supersedes the support-first
hold below, not the no-merge/no-fabrication boundary. Evaluate the returned
native files against the exact baseline before considering any integration.
See [diagnostic limits](routing-bakeoff-2026-09-27.md).

**September 28 Quilter support response:** preserved pours are configured
under **Constraints -> table 2, Define Your Own Constraints**, by net name,
not on the Circuit Comprehension page previously inspected. Next inspect
that table in the existing draft; both intended zones use `GND`. Confirm
F/In1 zone/exclusion and existing In2 trace preservation, plus outstanding
import/inference corrections, before submitting. No PCB edits or routing
job are authorized by this navigation clarification. See the
[updated assessment](routing-bakeoff-2026-09-27.md).

**September 27: manual/LLM routing paused for a purpose-built-router bakeoff.**
The [assessment report](routing-bakeoff-2026-09-27.md) records the completed
local tests: Freerouting's native-width F-only sample closed 0/7 opens;
no multilayer routing claim is made. tscircuit's conversion semantics do
not meet this board's preservation requirement. Quilter's uploaded
comprehension and missing preservation controls require vendor assistance;
the owner has requested a human support handoff. No cloud job is confirmed.
Accepted PCB/manifest and all experiment-source copies remain unchanged.
The next gate is that support response, not automatic continuation of
routing, source corrections or further autorouter trials.

The owner authorizes about 90 minutes of active assessment, normally at most
30 minutes per approach: establish a source-bound baseline, test stable
Freerouting conservatively, assess Quilter, and briefly investigate
tscircuit's existing-project round trip. Separate disposable copies start
from accepted `adc262b3...` / `b849b5de...` at commit `92b3af9`;
the held MCU fixture is not a starting board. No experimental result may
be imported or merged into the working board. Existing engineering layer,
return, process and contact constraints still apply.

The owner explicitly authorized uploading a sanitized copy of the public
design to their Quilter account. Exclude personal preferences, credentials
and unrelated files; no paid execution, purchase or fabrication is approved.
The final deliverable is a concise measured comparison and low-LLM routing
architecture recommendation. Do not resume the oscillator audit or manual
routing at the end of this assessment.

**Fanout fixture prepared, held for an incomplete oscillator audit.**
The [preparation report](../hardware/handbell/iterations/printed-bell-four-layer/reports/mcu-fanout-fixture-preparation.json)
records private fixture `0acc6277...`, 138 removed local F segments and
six clipped boundary parents with retained exterior terminals. The five
previously omitted blockers are released; fixed vias, pads and the recorded
private-pickoff primitives remain. The fixture is intentionally unfilled
and disconnected, not a PCB candidate.

Root found that the follow-up oscillator audit checked C19/C20
(VAMP/VBAT capacitors), not C2/C3, the 15 pF capacitors on Y1's actual
`Net-(IC1-XIN)` / `Net-(C3-Pad2)` nets. Its empty intersection therefore
does not prove the required oscillator protection. No physical violation
has yet been established, but the fixture is not released for placement.
The bounded review is stopped; Sol is idle.

**Next bounded item:** correct only the Y1/C2/C3 oscillator-structure audit,
including ground-return branches rather than pad intersections alone.
Compare those exact native structures against the released 144 parent
segments. Preserve any mistakenly released fragments, or establish that
none were released. Do not start another placement or routing search.
The replay tool `tools/replay_mcu_fanout_fixture.py` reconstructs the
recorded fixture from accepted source and report into a new private file;
existing outputs, including the active PCB, must not be overwritten.
Accepted `adc262b3...` / `b849b5de...` remains unchanged at 37 opens.

**Broader fanout study: two conditional ports, no accepted placement.**
The [partial proposal](../hardware/handbell/iterations/printed-bell-four-layer/reports/mcu-fanout-coordinated-proposal.json)
identifies ordinary VCORE sites at `(105.016667,103.627273)` and
`(94.996667,104.945455)` after its explicit conditional removals. These
are not implemented ports or proof of complete fanout. The proposed
C13/C17/C18/R1 poses collide with fixed copper/pads and are rejected.

Root identified a scope-model gap: the 23-track removal inventory omitted
the local +3V3 blockers `d269dfaa...` / `fcbd8a3e...` and the VCORE
branch `f466a216...` / `50ee0fe3...` / `e70cc137...`. Those then appeared
as fixed obstacles in proposed corridors even though coordinated local
power rework is authorized. Fixed USB resistor lands and VHI/VBAT remain
real constraints; removing obsolete local fanout does not remove them.

**Historical fixture-preparation scope (now held above):** construct one reusable private fanout fixture with
exact eligible local F route fragments removed and all required terminals
and boundary connections inventoried. Native bounds are
`[93.5,98.5,110.0,107.2]` mm. Eligible nets are local +3V3/VCORE/GND,
reset and the authorized USB/QSPI escapes; preserve fixed component
lands, through-vias, mechanical interfaces, protection/clock structures
and all out-of-region copper. Retain MCU exposed-pad ground spokes.
Do not use stale F fill as current connectivity evidence. This is
scope/fixture preparation only, not another placement guess or routing
attempt; stop within eight minutes with a source-bound fixture or error.
Accepted `adc262b3...` / `b849b5de...` stays unchanged at 37 opens.

**Owner approved a broader coordinated MCU fanout proposal.** The new
twelve-minute proposal scope may reconsider C6/C7/C8/C13/C17/C18 and
R1 positions plus local power/ground and USB/QSPI escape corridors.
Keep the MCU, contacts, USB connector, other component positions, outline
and mounts fixed; preserve IMU, oscillator, switching/protection structures
and the five mandatory process vias. This is not implementation approval.
Establish ordinary transition access and continuous capacitor-return
paths before selecting the fanout. Restore all disturbed +3V3, VCORE,
ground and reset associations. Proposed USB/QSPI changes need explicit
layer/reference review, not an assumption that all inner layers are free.
The rejected 39-open source-cell remains evidence, not a starting candidate;
use accepted `adc262b3...` / `b849b5de...` at 37 opens.

**Source-cell candidate rejected: two ground regressions.** Root recovered
the counts from the saved `319a45f9...` candidate without further routing
or refill. Native, independent graph and physical-pad-group counts agree:
37 opens before, 39 after. C8.2 is isolated; C6.1/C7.1/C17.2 form a second
newly detached ground group. C13.2 remains on MAIN, and the three VCORE
groups are unchanged. No shorts or floating copper were found, but those
checks do not compensate for disconnected capacitor returns.

The [corrected diagnostic record](../hardware/handbell/iterations/printed-bell-four-layer/reports/mcu-vcore-source-cell-proposal.json)
and explicitly rejected recovery PCB preserve the result. The executor's
count-reporting error was corrected separately from the physical failure.
Other source/clearance/DRC/placement gates remain unverified; there is no
accepted candidate manifest. Do not rerun the exhausted geometry attempt,
promote the recovery, or treat a connected VCORE via as a completed cell.
Accepted PCB/manifest remain `adc262b3...` / `b849b5de...`, at 37 opens.

**Escalation:** the proposed supply escape cut the shared ground structure
that the previous accepted stitch restored. Before another trial, choose
whether to broaden the coordinated MCU fanout study to include surrounding
local constraints such as R1/C13 and critical-route access, or reconsider
the rear copper/contact interface or manufacturing approach. No such scope
extension is yet authorized. The failure concerns this exact candidate;
it is not a proof that ordinary four-layer construction is impossible.
Sol is idle pending that engineering scope decision.

**Eastern port proposal passes; complete the source connection before
implementing it.** The [exact local proposal](../hardware/handbell/iterations/printed-bell-four-layer/reports/mcu-east-vcore-port-proposal.json)
supports the 0.25 mm +3V3 L detour with preserved attachments and ordinary
via access at `(105.045,106.0)`. It does not yet qualify refill, VCORE
feeding or the complete MCU supply network. Root corrected the missing
proposal overlay and verified its registration against two native vias.

**Next bounded item: private regulator-output source-cell proposal.**
Test C8 shifted north by 0.10 mm, retaining its 1 uF value and pin association,
and a 0.25 mm F VCORE path from its new pad 1 centre
`(104.993069,102.330145)` through `(104.993069,102.98)`,
`(106.67,102.98)` and `(106.67,104.8)` to an ordinary via at
`(105.045,105.55)`. Retain the +3V3 L detour and all other placement/copper.
The higher via position is an explicit alternative intended to leave
more room for ground below the via; it is not already qualified.
Check actual fixed geometry, capacitor-pad clearance, full-span contact
clearance and refill connectivity, especially all five eastern capacitor
grounds through the unchanged C13 stitch. Preserve every previous connected
group. The local pin-to-C8 decoupling route must remain intact.

Only a private proposal/candidate and its evidence are released, not an
active-board edit or acceptance. Stop within twelve minutes at a source
cell with credible supply/return evidence or a concrete blocker. This
does not close IC1.50/C6, the western VCORE group, C18 ground or R1 access,
and an unchanged open count must not be presented as connectivity progress.

**September 27 resumed: disposition the exact eastern +3V3 blocker.**
Astra verified that several eastern port-map witnesses fail only against
F segment `6c98d6c9-8ede-5cc4-a70e-ab1fa103ccf7`, which was not included
in the prior conditional-removal inventory. Release one eight-minute
proposal-only check replacing its `(104.35,105.15)` to `(105.85,106.65)`
diagonal with a 0.25 mm F path through `(104.35,106.65)`, retaining every
same-net branch join as well as the endpoints. Check a reserved ordinary
VCORE via at `(105.045,106.0)` against both fixed copper and the replacement.
This is within the authorized local +3V3 study, not a VHI/VBAT release.
No component move, active-board edit or floating VCORE via is authorized.
Stop at a qualified local proposal or a concrete blocker within the budget.

The western witnesses also include R1.1, a fixed 10K reset pull-up pad,
as well as its +3V3 approach tracks. R1 is not in the five-capacitor move
scope. Eastern port feasibility must not be presented as resolution of
western access, C18 ground, capacitor placement or the complete VCORE feed.
Accepted PCB/manifest remain `adc262b3...` / `b849b5de...` with 37 opens.

**Coordinated MCU study and bounded port map are preserved, not accepted
routing.** The [rejected-trial record and port appendix](../hardware/handbell/iterations/printed-bell-four-layer/reports/mcu-vcore-local-relayout-proposal.json)
retain the proposed five-capacitor geometry and its conflicts. Astra
rejected the inference that this trial required changing VHI/VBAT or
moving additional components. The subsequent 160-centre map found no
clear tested port in its specified east/west windows under either fixed
geometry or the exact conditional-removal inventory. That is a bounded
negative result, not proof that every local rework or ordinary-via
topology is impossible.

Keep the accepted 37-open `adc262b3...` / `b849b5de...` package unchanged.
Sol is idle. Before another placement/routing trial, Astra must disposition
the remaining fixed blockers and the tested conditional-removal scope;
no broader power-corridor modification, blind-via process or component
move is released. The layer/placement/return and manufacturing gates are
now consolidated in `docs/routing-agent-policy.md` and the router profile.

**Owner approved the coordinated MCU study.** After the fixed-route
inventory below, the owner selected the recommended supply/return study.
Sol is preparing one concrete proposal within a twelve-minute budget.
Only proposed local +3V3/VCORE/GND rework and necessary
C6/C7/C8/C17/C18 moves are in scope; the accepted PCB is not being edited.
Keep IC1, contacts, outline, mounts, USB, clock, IMU and the C13 stitch
fixed. Resolve all three VCORE groups, C18 ground and ordinary off-contact
transition access together. Actual proposal review precedes implementation;
four copper layers do not override rear-contact or return-path constraints.

**VCORE fixed-route preparation found no released path; scope decision
required.** The [source-bound inventory](../hardware/handbell/iterations/printed-bell-four-layer/reports/mcu-vcore-strategy-inventory.json)
records three VCORE groups: IC1.45/C7/C8 (regulator output),
IC1.50/C6 (east DVDD), and IC1.23/C18 (west DVDD). The tested 18 F forms
for each supply connection failed; ten local ordinary-via positions per
VCORE group and eight near C18 GND also failed. These bounded witnesses
are not exhaustive routing or placement-impossibility proofs.

Astra resolved the two universal east-link blocker UUIDs against native
source: `d269dfaa-bef6-5f59-b918-0cefd4b841f2` and
`fcbd8a3e-d67e-55bf-bc7c-7f2822b47e3c` are actual F +3V3 segments,
not cached ground fill. Rear VBAT copper and BT1/BT2 metal also constrain
through-via access. In1 GND may receive refill-generated antipads only
with subsequent continuity review; it is not a signal-routing layer.
C18.1 remains a separate GND island, so a supply-only west-load fix
would not complete its decoupling circuit.

**Recommended next scope, pending owner choice:** one bounded coordinated
MCU supply/return study that may propose local +3V3/VCORE/GND rerouting
and, only where necessary, moves of C6/C7/C8/C17/C18. Keep IC1, contacts,
outline, mounts, USB, clock, IMU and the accepted C13 stitch fixed.
Return one proposed topology with supply/return paths, transition access,
explicit changed primitives/poses and mechanical implications before any
implementation. No new part sourcing, advanced via process, clearance
waiver, active-board edits or CAD rebuild is authorized by this proposal.
If the bounded study cannot identify a credible topology, stop and report
the structural conflict rather than expand the search.

Accepted PCB/manifest remain `adc262b3...` / `b849b5de...`, with 37 opens.
Sol is idle; no VCORE route or placement change is released.

**September 25 eastern MCU ground accepted: 37 opens.** Astra reviewed
the exact two-node delta and saved filled F/In1 views, accepting PCB
`adc262b3e7056cb9031387c55262b5cf99e599ae6e28970f9784f5237e662314`
with manifest
`b849b5defb95f010f555d43b6d261fdea3ef37e240aee0190a607fb519c642f8`.
The [acceptance record](../hardware/handbell/iterations/printed-bell-four-layer/reports/mcu-east-ground-acceptance.json)
binds the preserved stage and its validation. All five eastern decap
grounds now reach In1 MAIN and MCU ground. Existing copper, placement,
private returns and required process vias are preserved; 234 non-open
findings and 46 enabled parity findings remain.

The new segment lies within the shared filled ground area; its 1.322814 mm
length is not a complete decoupling loop or a sole-width current path.
The ground island still wraps around VCORE copper. Retain this incremental
improvement without claiming exact island bottleneck width or qualified PI.
The accepted CAD remains a historical exact match to `d2a098b0...`, not
the new board. `mechanical_rebind_required` is now true even though all
component poses, heights and mechanical interfaces are unchanged.

**Next item:** return to VCORE distribution between IC1.45/C7/C8 and
IC1.50/C6, preserving the new ground stitch and the third IC1.23/C18
group. Astra must select the supply-layer/width/return strategy before
Sol generates routing. No VCORE route or part move is released by this
ground acceptance.

**September 25 off-contact via found; one staged candidate is released.**
The [escape assessment](../hardware/handbell/iterations/printed-bell-four-layer/reports/mcu-east-ground-escape-assessment.json)
records the exhausted direct/dogleg F-to-MAIN screen separately from the
subsequent 169-position off-contact via screen. One alternative has both
a legal via and a short F escape: C13.2 GND at `(106.010546, 103.640537)`
to `(105.13, 104.627692)`, with a 0.25 mm trace and a 0.604/0.35 mm
ordinary through-via. The added trace is 1.322814 mm; this is not the
complete capacitor return-path length. Nominal modeled contact clearance
is 0.253002 mm, not a manufacturing-tolerance qualification.

Astra releases only those two new copper nodes in a separate staged PCB,
with qualified two-zone refill, preserved source/private returns and
fresh connectivity/clearance checks. Expected connectivity is 38 to 37
opens. All five grounds must reach In1 MAIN and the MCU ground pad.
Review actual filled F/In1 geometry before acceptance: the shared F island
has no defined centreline, and the earlier 15-point In1 screen does not
prove continuous reference coverage. Active PCB `d2a098b0...`, manifest
`aa68559e...` and the accepted CAD remain unchanged pending review.
No supply/USB reroute, part move, new search or active promotion is released.

**September 25 owner resumption: assess a different ground escape.**
The owner resumed from `1ac52ba`. Astra released one eight-minute read-only
Sol assessment of the existing C6/C7/C8/C13/C17 GND group's complete copper,
not another local C6/C8 via search. Within native bounds
`[102.0, 98.5, 109.0, 107.5]` mm, screen an F connection to existing
MAIN-connected F copper or an ordinary via outside the complete rear-contact
exclusion. Prefer existing grounded copper when it avoids an extra via.
The deliverable is at most two numerical route alternatives with actual
clearances, each capacitor's return path and underlying In1 continuity.
Preserve all source geometry and constraints. No candidate is authorized
for PCB insertion until Astra reviews its return-path tradeoff.
The failed short-via item below remains exhausted; the accepted board
and matched CAD remain unchanged.

**Eastern MCU ground strategy is blocked; no copper was changed.**
The [bounded screening record](../hardware/handbell/iterations/printed-bell-four-layer/reports/mcu-east-ground-blocker.json)
binds the unchanged accepted PCB `d2a098b0...`, manifest `aa68559e...`
and battery-contact model. All 79 C6 and 102 C8 candidates inside the
released region failed modeled rear-contact metal clearance. The tested
via diameter was 0.604 mm with 0.25 mm metal clearance. Other rejection
classes overlap; their counts must not be added as independent failures.
C8 is the native 1 uF / 25 V capacitor. No staged PCB was created.

The initial attempt and two implementation corrections are exhausted.
The previous local-via release below is historical, not permission to
repeat or expand its search. The modeled BT1 under-cell base covers
native X 105.685-118.685, Y 94.435-105.565 mm, with adjacent tabs.
This is the documented screening model, not measured loaded-contact
geometry or proof that every possible return route is impossible.

**Next proposed item, not yet released:** assess a longer F ground escape
from the existing shared group to an ordinary via outside the complete
BT1 metal exclusion, then review the resulting decoupler return paths
before routing. Keep placement, contacts, protected In1 and supply copper
fixed. Do not infer that solder mask or filled/capped through-vias permit
conductive B lands under contact metal. If no acceptable ordinary-via
return emerges, escalate the topology/mechanical/process choice rather
than silently relax clearance. Sol is idle; affected routing is blocked.

**Post-IMU triage is complete.** The source-bound
[connected-group inventory](../hardware/handbell/iterations/printed-bell-four-layer/reports/post-imu-routing-triage.json)
reconciles 38 opens across 24 disconnected nets. Its suggested nearest
VCORE edge is not yet released: C6.1, C7.1, C8.2, C13.2 and C17.2 form
one isolated GND group. Restore that group's local return before extending
VCORE distribution. The next bounded staged candidate may add short F GND
escapes and ordinary off-pad through-vias near C6 and C8 into actual In1
MAIN GND. Preserve all existing copper and placement; do not change VCORE,
USB, clock, zones, rules or the five mandatory filled/capped vias.
Screen complete native obstacles, all-layer via clearance, same-net SMD
overlap and battery-contact exclusions. If local ordinary vias cannot
satisfy those gates, return the measured blocker rather than move parts or
substitute filled vias. Candidate acceptance requires all five grounds
to reach MAIN, preserved prior groups/private returns and fresh saved-fill
clearance/connectivity evidence. Active accepted PCB remains `d2a098b0...`
until review; this release is not automatic promotion.

**IMU closure is now the accepted incremental checkpoint.** Active PCB
`d2a098b0dcd198fb790e6dd4341c036814aabba7fa2ef7c278c79a0a2c916711`
and manifest
`aa68559eebaf8a43c369f549deed1f025d393bafe2d4323d2098fa4712ef622c`
are bound by [the acceptance record](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-closure-acceptance.json).
The immutable CAD snapshot remains `443fe1b5...`; its exact three-field
lifecycle bridge is recorded, not claimed as byte equality. The completed
native CAD remains `b2dff347...`. **38 opens, 234 warnings and 46 enabled
parity findings remain.** Both obsolete branches are retired; external
INT-to-IC1.34 is still unfinished. All five U4/C24 mandatory process-via
identities were checked against actual native nodes before publication.

**Next bounded scope: read-only MCU/power-return routing triage.** Extract
the current connected groups and actual pad/net identities for IC1 core
supplies/grounds, their decouplers and the remaining USB/power returns.
Reserve sensitive corridors before ordinary controls. Reuse the accepted
IMU evidence and preserve its placements, routing and five mandatory
filled/capped vias. No new route or placement move is released until
Astra selects a concrete next connection strategy from that inventory.
This closes the IMU integration item, not the whole board or powered,
supplier, safety or fabrication gates.

**The authorized CAD run completed and passed its checker.** The
[extended-run record](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-cad-extended-run.json)
(`4762f642...`) records FreeCAD 1.1.3, 440.1 seconds, zero nominal
overlaps/material intersections, validated native/12 STEP/9 STL outputs,
and all existing skin, contact and assembly/service gates. Root reran the
source-bound checker successfully. The native model is `b2dff347...`,
artifact manifest `63cf25b4...`, and exact CAD input manifest `443fe1b5...`
for PCB `d2a098b0...`. The nominal USB mouth stays -27.9; the conservative
front envelope -28.05 clears the new skin rear plane -28.25 by 0.20 mm.
This is engineering-prototype integration, not powered, supplier,
fabrication or child-use qualification.

**Next: promote the qualified IMU checkpoint, without more geometry
changes or another CAD build.** Copy the exact PCB into the active package.
Derive the active manifest from the preserved CAD input snapshot, changing
only lifecycle metadata: `status` to
`INCREMENTAL_IMU_CLOSURE_ACCEPTED`, `current_stage_report` to
`reports/imu-closure-acceptance.json`, and
`mechanical_rebind_required` to `false`. Record and verify this exact
three-field bridge: CAD remains byte-bound to its immutable snapshot,
while every geometry, component, source and interface field equals the
active manifest. Do not claim the two manifest byte hashes are identical.
The acceptance record must bind both hashes, the unchanged native PCB,
electrical/CAD evidence, and the prior accepted Git checkpoint.
Keep all snapshots and models unchanged. Following promotion, the next
engineering scope is the remaining MCU supply/ground and USB/power-return
groups, not optional IMU optimization.

The generated native log contains local installation paths and remains
ignored/private. Its hash is recorded as run evidence, but it is not part
of the checked CAD artifact manifest or the public model bundle.

**Owner selected one extended CAD run:** after the saved `fa98909`
checkpoint, the owner explicitly authorized a **30-minute maximum native
run**, instead of splitting the builder immediately. Use the unchanged
CAD snapshot and reviewed builder in a new
`imu-four-layer-review/extended-run` output directory, preserving the
original partial output. Run with `--launch-timeout-seconds 1800`; retain
all existing geometry/roundtrip checks and run the checker only after a
fresh completion. A timeout or new interference stops this attempt with
its evidence; this is not authorization for another retry or an extension
of future item budgets. No routing, placement or promotion is released.

**CAD stopped at its time budget; do not repeat the monolithic build
unchanged.** The [integration handoff](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-cad-integration.json)
(`2c862a3a...`) records the exact 49-file CAD snapshot, manifest
`443fe1b5...`, implemented legacy/HRO input guards and coordinated USB
skin correction. A single 540-second FreeCAD run produced a native model
(`7eb5fa9f...`) and two STEP files, but did not complete export/roundtrip
validation. No fit report, artifact manifest, completion marker or passing
checker result exists. The partial output is **not accepted or print-ready**.
Its old `BUILD_IN_PROGRESS` marker is historical: the owned process ended.

Root reviewed the code and corrected three directly coupled details:
the nominal mouth remains Y -27.9, distinct from the conservative
envelope front -28.05; the underledge Z-gap is not the front-skin Y-gap;
and future timeouts preserve captured native output and a timed-out
status instead of discarding the progress log. Nonfinite new USB datums
are rejected. Legacy/HRO and invalid-input controls plus a mocked timeout
passed. These follow-up edits did not regenerate CAD. The partial native
file embeds the actual as-built builder `4a2aa8b2...`, independently
verified; it is not claimed to have been generated by the revised builder.

**Decision boundary:** preserve this checkpoint and choose bounded
native-generation/export-validation stages, or explicitly authorize one
longer native run. Do not silently exceed the per-item budget, weaken
roundtrip/geometry checks or create another full-build retry loop.
Electrical state remains the qualified cleaned candidate `d2a098b0...`;
active-board promotion and further routing remain held for CAD completion.

**The cleaned IMU candidate has completed its saved-board electrical
checks.** [Final validation](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-cleanup-final-validation.json)
(`920ad674...`) confirms **38 native/independent opens, 234 warnings,
46 parity findings with parity explicitly enabled**, and no non-open
errors. All 325 pads and prior connected groups remain; ground, CELL_NEG,
both private pickoffs, TP6 and the INT exit pass. Actual filled polygons
pass the 0.20 mm foreign-copper and layer-specific exclusion checks.
The two obsolete warnings are gone. The API repair succeeded; no further
validator repair cycle is needed.

**Next bounded item: exact CAD rebind and the already selected USB skin
correction.** Keep the active 41-open package unchanged for now. Stage the
exact cleaned PCB `d2a098b0...` with its schema-2 manifest/companions in
`reports/imu-cad-inputs` under the four-layer package; this is a source
snapshot, not another routing candidate. The staging manifest may change
only `status` to `INCREMENTAL_IMU_LAYOUT_ENGINEERING_REVIEW` and
`current_stage_report` to `../imu-cleanup-final-validation.json`.
Every other field, including the PCB hash and all poses, must match
`62ea87d6...`. Use a separate output under
`mechanical/studies/2026-09-13-printed-bell/imu-four-layer-review`.
All public input paths must remain repository-relative; copy only the
actual schematic, contact file, project, libraries/tables and licence,
not personal KiCad preferences or entire historical report directories.

Update the builder to accept only the legacy USB geometry or the
specifically reviewed HRO case: MPN `TYPE-C-31-M-12`, footprint
`Handbell:USB_C_HRO_TYPE_C_31_M_12_Handbell`, centre `(0,-24.01)`,
envelope `9.64 x 8.08 x 3.5`, rotation -180 and native datum
`(0,-22.82)`. Do not broadly exempt USB fields. The new case uses the
front-skin centre -28.75 and proof face -29.25 described below; legacy
geometry retains its old positions. Update all linked stock/mask/proof
coordinates together and retain every skin, loading, assembly and
contact check. Exercise legacy/new/invalid input controls before native
generation. Do not modify the frozen T8 helpers or accepted study.
Use an explicit owned-process-tree deadline within the item budget.
If CAD reveals another interference or exceeds the budget, preserve the
partial result and stop; do not lower heights, move parts or waive checks.
Full CAD review and any display-only camera issue remain distinct from
electrical acceptance, powered qualification or fabrication approval.

**Cleanup DRC confirms 38 opens and 234 warnings; graph/fill validation
is still incomplete.** The [saved-board validation report](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-cleanup-validation.json)
records removal of both obsolete dangling warnings, no new dangling
findings, no non-open errors and unchanged silk identities. Its source
and manifest checks pass. The board remains `d2a098b0...`.

**The reported zero schematic-parity count is not a clearance of that
gate.** Root inspected the command: it omitted `--schematic-parity`.
The empty output array is not comparable to the earlier enabled check's
46 notices; the report's derived "removed" parity identities are invalid.
Keep those 46 unresolved until a matching enabled comparison is run.

The graph harness first treated island records as objects, then expected
a nonexistent dictionary `net` key. Root inspected `zone_graph.py`:
`zone_islands` holds metadata, while
`graph.items[island["uuid"]].GetNetname()` and the corresponding
`graph.vertices[node]["net"]` supply the actual net. This is an interface
error, not an established board defect. Also, zero shorts does not prove
the required 0.20 mm foreign-fill clearance.

**Final targeted tooling repair before escalation:** use the inspected
API, persist graph assertions before subsequent fill checks, check actual
filled polygons against foreign copper and applicable layer-specific
guards, and run DRC with schematic parity explicitly enabled. Preserve
all previous reports and immutable board bytes. No new general validator,
refill or copper work is authorized. If this focused completion fails,
stop the affected workflow with its concrete blocker rather than starting
another renamed repair cycle. CAD is still blocked.

**Both obsolete branches are removed in a held cleanup candidate; fresh
connectivity/DRC remain pending.** Native topology confirmed the +3V3
segment ends at a retained multi-segment junction, and the five-item
INT2 branch is padless through its retired via to the retained live via.
The [cleanup report](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-obsolete-branch-cleanup.json)
records those exact six removals and completed refill (17 F polygons,
one In1 polygon). Recovery PCB `d2a098b0...` and manifest `62ea87d6...`
are preserved separately; `79a1dee3...` and the accepted board are unchanged.

The executor stopped on 18 extra newline bytes in its raw, cache-stripped
comparison. Root then compared the **complete ordered parsed
S-expressions**, excluding only the six authorized top-level nodes and
each zone's `filled_polygon` children. Every remaining atom, including
whitespace inside quoted strings, matches. There are no new nodes, and
the removal set is exact. Manifest differences are only the PCB hash,
private held status and stage-report path. This resolves the source
interpretation; do not alter or regenerate the board to fix harmless
inter-node whitespace. Do not replace this with a global whitespace
regular expression that would hide changes inside quoted properties.

**Next item: finish saved-board cleanup validation on `d2a098b0...`,
without another edit or refill.** Apply the inspected parser-aware source
contract, then independently persist graph/ground/CELL_NEG/private-pickoff
checks and fresh native DRC/warning identities. Verify changed fill's
clearance/contact effects rather than reusing old fill evidence. No claim
that the two warnings disappeared is made until native DRC completes.
One focused harness correction is permitted; another interface mismatch
must be reported without another all-in-one rebuild. CAD remains blocked
on that result. The original report with local traceback paths is retained
privately as `files/imu-obsolete-branch-cleanup-agent-original.json`
(`4724e7d7...`); its public copy only redacts those personal paths.

**Astra local-layout review: retain this candidate for prototype
continuation; no further IMU placement reset is justified by the present
evidence.** The [filled views and conductor records](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-engineering-review-inputs.json)
(`06cc7163...`) bind `79a1dee3...`. Root inspected all four local layers and
the In1 overview. In1 has local merged antipads but no board-spanning cut
through the IMU region; the clock exclusion lies south of these local
routes. This is a qualitative return-path review, not a minimum-neck or
impedance measurement.

C23/VDDIO uses **F-In2-F**, correcting the earlier B-feed description.
Its conservative full-primitive planar sum is 5.246407 mm; C24/VDD uses
4.156550 mm on F. Neither figure includes barrel length or represents an
exact pin-centre electrical length. C23.2 and all IC4 grounds share F
island 11, with the power-ground stitch at `(87.9,93.8)`. C24.2 has its
own small F island and capped via into In1. The supply-side detours are a
recorded decoupling compromise, not ideal placement. Retain them for this
prototype rather than introduce another special-process via or move parts
without a concrete power-integrity conflict. The [verified ST guidance](motion-sensing.md#layout-review-basis)
does not supply a numeric length waiver: local supply noise, startup and
sensor operation under audio load still require powered verification.

SCL and INT use local B runs; SDA includes In2 routing and a B external
continuation, while INT2 uses In2. Sparse In2 routing is not a second
ground plane. Keep these as the intended I2C/interrupt connections, not
authorization for a faster SPI/I3C interface. No local crossing of the
clock-plane exclusion or change to protected switching/clock/USB copper
was identified. Physical stackup and whole-board interface review remain
open. Root's private PNG conversion inlined SVG text sizes because MuPDF
ignored CSS class font sizes; original SVGs were not modified. Fine
polygon outline seams are not white copper voids.

**Next bounded item: retire the two obsolete terminal branches before
binding CAD.** Removing one segment can merely move a dangling warning,
so inspect the complete branch topology first. Release removal of
`a672a427...` (+3V3) only if it terminates at a retained junction; no
additional power copper is released. For `/IMU_INT2`, release the obsolete
branch from the free `ca326628...` end through the old
`cd251294-41e9-523f-958c-e73cc84fd87d` via at `(94.8392,95.1136)` up to,
but **not including**, the still-used
`3a4ecc82-02d7-5513-8c89-db4de4adc534` via at `(94.04,92.3102)`.
Inventory exact UUIDs and prove this is a padless, junction-free leaf
branch before deletion; otherwise stop for review. Preserve TP6, its
functional route, the new In2 feed, INT exit and all other copper.
Use a separate cleanup candidate, qualified refill and fresh graph/DRC;
both obsolete warnings must disappear without new dangling warnings or
lost connections. Preserve `79a1dee3...` and all its evidence. CAD rebind
is the following separate dependency, not part of this cleanup.

CAD preflight was rechecked without edits: `build_printed_bell.py` still
compares X6 to the old T8 envelope at lines 163-167. The documented
0.15 mm outward front-skin correction must coordinate
`usb_skin_stock` (current centre Y -28.6), its front-face proof plane
(Y -29.1), and `tongue_mask` (centre Y -28.6), not merely relax the input
guard. For the specifically qualified X6 front bound -28.05, the
corresponding proposed values are -28.75, -29.25 and -28.75, restoring
the 0.20 mm nominal rear-plane gap. Preserve the legacy/development case,
native USB datum, skin continuity, enclosure and service-path checks.
These values are a pending CAD implementation contract, not a proved fit.

**The remaining copper geometry gate passed.** The
[geometry report](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-geometry-qualification.json)
(`3050b132...`) covers all 61 new local segments and ten ordinary vias,
including actual filled-island geometry, same-net-inclusive SMD land
overlap, drill/USB-slot and contact/base/tab checks. The five retained
exteriors retain their separate exact-source contract. No new In1 signal
traces or unauthorized centreline excursions were found. Input PCB
`79a1dee3...` and manifest `eb37d87f...` remain unchanged and unpromoted.

**Next item is engineering review, not another general validation pass.**
Sol may extract source-bound native filled-plane/layer views and the
actual C23/VDDIO and C24/VDD route/stitch geometry for Astra's review.
Show filled holes, coordinates and local returns; primitive-only pictures
or a single connected-plane component are insufficient. Report route
length definitions and limitations, not inferred impedance/inductance or
manufacturing qualification. Preserve copper and all completed evidence.
Astra then decides the return-path/decoupling/adjacency disposition before
the separate exact CAD rebind and any explicitly authorized stub trims.

**Exact source/manifest/process preservation passed; geometry is still
pending.** The [source/process report](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-source-process-qualification.json)
(`a4a75996...`) checks the explicit removal sets, five retained exterior
pieces, unchanged critical copper/zone definitions, and exact IC4/R15
poses. Source-derived negative controls reject unauthorized retained
geometry, local pad/text, manifest and removal changes. U4's four thermal
vias and complete footprint, plus C24's via/land/paste/mask, are preserved;
the five filled/planarized/capped-via requirements remain mandatory.

**Next bounded item: complete the released-region and all-ten-via geometry
gate on unchanged `79a1dee3...` / `eb37d87f...`.** Check all 61 new local
segments plus five exact retained exterior pieces, all ten new ordinary
vias, and actual filled geometry. Enforce the released net/layer/region
contract, 0.20 mm foreign clearance, same-net-inclusive off-pad rule,
actual hole shapes/new-new drills, and 0.25 mm contact/base/tab clearance.
The current project minimum annulus is 0.10 mm; the prescribed new
0.604/0.35 mm pattern has a nominal 0.127 mm annulus. Report both rather
than inventing a stricter project setting or claiming fabrication yield.
Reuse unchanged completed gates; no routing, refill, trims, CAD or promotion.
Return explicit residual gates if the bounded pass cannot finish.

**Corrected ground proof passes; no ground repair is needed.**
The [anchor review](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-ground-anchor-review.json)
(`19328537...`) confirms C24.2 belongs to the actual In1 GND island in
both accepted and filled boards. C23.2 and all five IC4 GND pads reach
that island in the filled candidate. The negative control rejects
IC1.49 because it is +3V3. All seven `/CELL_NEG` pads and its 55 copper
items remain in one component isolated from GND; the actual slash-prefixed
net is checked, not an empty `CELL_NEG` lookup. This supersedes only the
false ground-failure interpretation, not the other pending gates.

Read-only cut proofs show that `a672a427...` (+3V3) and `ca326628...`
(/IMU_INT2) can each be removed without losing their current connected
pad groups. They remain preserved for now. The INT local exit is
intentionally unfinished and must remain. Silk findings stay in the
late manufacturing cleanup, not a copper-clearance waiver.

**Next bounded item: exact source/process/geometry qualification of the
unchanged filled pair `79a1dee3...` / `eb37d87f...`.** Apply the cumulative
source contract below, reject unauthorized node/field changes with
negative controls, and check all ten new ordinary vias against same-net
lands, drill/barrel/contact constraints. Preserve U4/C24 mandatory
filled/capped treatment and original lands. Reuse hash-bound graph/DRC,
ground and pickoff evidence; do not refill, trim stubs, move parts or
promote the candidate. Persist completed gates separately if the bounded
item cannot finish. CAD and actual layout/return-path engineering review
remain required after these checks.

Root's first look at the source-bound F/In2 primitive views supports keeping
this candidate, not reopening placement. Those images omit filled planes
and drill voids and therefore cannot sign off return paths. The subsequent
engineering review must inspect the actual In1 apertures/local necks and
trace both decoupling loops to IC4.6/7: C23-to-VDDIO includes the B-side
feed and two supply transitions, whereas C24-to-VDD uses the local F
tree and its capped ground via. Measure those paths and their reference
plane continuity rather than inferring high-frequency decoupling quality
from all-net connectivity or total plane area. Review SCL/SDA/interrupt
layer transitions and adjacency too; physical dielectric stackup and
powered behavior remain separate qualifications.

**Saved-board diagnostics measure 38 opens, but the MAIN-ground failure
claim used the wrong net.** The
[diagnostic report](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-electrical-diagnostics.json)
records fresh graph/DRC agreement: 41 accepted opens versus 38 candidate
opens, no shorts/floating copper, no lost accepted pad groups, and both
private pickoffs preserved. The filled recovery pair is unchanged at
`79a1dee3...` / `eb37d87f...`; it is still unaccepted.

Root checked the alleged MAIN reference against native source:
**IC1.49 is +3V3, not GND.** Disconnection of the IMU grounds from that pad
is therefore not evidence of a ground defect. Preserve the diagnostic report
unchanged as historical evidence, but do not route a "repair" to that pad or
repeat its failed-ground conclusion. C23.2 already belonged to the accepted
MAIN ground group, so the preserved-group result and its retained IMU
connection also require resolving this contradictory harness assertion.

**Next item: anchor-correct saved-board review, no copper/refill changes.**
Assert each anchor's actual net before connectivity checks. Establish
C24.2 on the accepted main GND component/In1 island, then test C24.2,
C23.2 and all five IMU ground pads on the unchanged filled candidate.
Include a negative control rejecting +3V3 IC1.49 as a GND anchor. Use the
correct net/component for CELL_NEG isolation. Reuse unchanged diagnostic
and private-pickoff evidence by exact hash; no automatic routing repair.

The fresh native DRC has no non-open errors, unchanged 46 parity notices,
and 236 warnings versus 233 accepted. Three new warnings are dangling
tracks: the intended unfinished INT exit and the preserved +3V3/INT2
exterior stubs. There are also changed silk witnesses from local rework.
Classify the intentional exit versus redundant stubs and identify exact
potential trims with cut proofs, but do not edit them in this review.
Complete exact source/pose/process/contact/off-pad qualification and CAD
remain separate gates; neither a reduced count nor a UUID inventory passes
them.

**Cumulative source-review contract prepared while ground review runs.**
Root compared the accepted and filled S-expressions: the only changed
shared UUID nodes are IC4 and R15. Excluding only each footprint's
top-level `at`, their complete definitions match; all other shared nodes
match apart from zone-fill caches. Non-UUID top-level definitions match.
The two exact origins are `(89.499806,93.492711,270)` and
`(87.082668,92.101941,90)`, each a 0.50 mm northward translation.

The 75 removed segments comprise exactly the 69 source F/B segments on
`+3V3`, SCL, SDA and `/IMU_INT2` wholly inside the original rework rectangle,
plus the six explicitly recorded boundary splits in
`imu-fanout-method.json`. No other net/layer qualifies for that removal
policy. Four removed source vias are `aa47961d...`, `6421709a...`,
`6d56c09b...` and `1c15a7a2...`, covered by the later signal/supply releases.
Five exterior replacements must retain their exact original
outside-endpoint-to-port geometry, layer, width and net. The sixth,
`a25f792f...`, has its separate conditional spur-cut authorization and
connectivity proof; do not generalize it to other outside tracks.
Added copper is 66 segments and ten ordinary vias, exclusively on the
released IMU nets. This is an inventory, not a geometry acceptance:
verify the released local/new-only upper/INT2-only extension boundaries,
allowed layers, exact via roles and dimensions, and preserved fixed
bridge/USBBOOT/critical structures. Explicit interface endpoints on a
rectangle edge include their normal end caps, not permission to extend
routes arbitrarily outside it.

Manifest differences are limited to the bound PCB hash, private status,
stage-report path, and the three pose representations of each moved part.
IC4 and native/common origins use the exact recorded translations.
R15 `y_mm` is `-7.898059`: it was quantized to the native 1 nm grid,
0.394640284 nm from subtracting 0.50 mm from the old floating-point proxy.
Require that specific value and unchanged X/rotation/other fields, not an
arbitrary coordinate tolerance or broad pose-field exemption. The future
validator must mutate retained source geometry and a moved footprint's
local pad/text geometry in negative controls; dropping every nested `at`
would incorrectly hide those changes. Still pending are full authorized
delta validation, geometry/process/contact checks and mechanical rebind.

**Electrical qualification held at a validator interface error, not a
measured board failure.** The
[initial qualification report](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-electrical-qualification.json)
preserves filled PCB `79a1dee30ac2fd21db66270067aa0d055ca94828967244d4cb43100700236d78`
and matching manifest
`eb37d87f2f8d09a2cd74fc432ca66f07531c92680530193024f5e15e0879da6e`.
Refill retained all 21 zone definitions, with 17 F polygons and one In1
polygon. The subsequent harness wrongly required `None` from
`component_comparison_self_test()`, whose documented implementation returns
a dictionary of four successful merge/split/missing-item controls.
The run ended at its correction cap before graph comparisons or fresh DRC.
Preserve the report and exact filled pair; do not repeat the refill.

**Next: narrowly repair control-result handling and measure the saved board.**
Use the actual control schemas and record their returned details. Run full
connected-group/short/floating/IMU-return comparisons and matching-project
native DRC as separate persisted diagnostic stages so one failure does not
erase or prevent collecting the other useful evidence. No routing changes.
One 15-minute item, one control-harness correction; stop additional
validator interface errors with explicit pending gates, not another chain
of speculative fixes.

Root also identified that membership of a UUID anywhere in a historical
report is not authorization for arbitrary changes to that item. The current
validator's UUID-text membership screen is an inventory aid only, not full
cumulative source preservation. Exact permitted fields/geometry, complete
manifest deltas and all mandatory process primitives need separate evidence
before electrical acceptance. Do not label a graph/DRC diagnostic pass as
completion of those pending gates.

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
