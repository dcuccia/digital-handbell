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
| CHG0/L0, D3/D4, U2, U4 | Review actual terminal coverage, paste/mask and thermal-via feasibility. Manufacturer-example differences require explicit retain/change dispositions, not automatic global replacement. | [Device register](device-component-selection.md), selected drawings and actual native lands; U4 exposed-pad/paste treatment remains open. |
| D3/D4, Q1/Q2/Q4, U3 | Apply already documented conservative envelope enlargements without shrinking other proxies or losing pose-dependent offsets. | Device register and final full-CAD fit. |
| U5, R27, remaining connectors/contacts | Complete the existing selected-part audit; retain until a specific correction is established, but do not call this qualified. | Existing-part review, exact pin/package/assembly checks and quotation process notes. |
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
the complete-identity baseline in `84469b7`:

```powershell
$work = Join-Path $env:TEMP ("handbell-ground-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $work | Out-Null
python -c "import subprocess; from pathlib import Path; p=Path(r'$work')/'baseline.kicad_pcb'; p.write_bytes(subprocess.run(['git','show','84469b7:hardware/handbell/iterations/printed-bell-clock-draft/handbell.kicad_pcb'], check=True, capture_output=True, timeout=15).stdout)"
python -c "import subprocess; subprocess.run(['python', r'tools\check_front_ground.py', r'hardware\handbell\iterations\printed-bell-clock-draft\handbell.kicad_pcb', '--baseline', r'$work\baseline.kicad_pcb', '--plan', r'hardware\handbell\iterations\printed-bell-clock-draft\reports\front-ground-plan.json', '--output', r'$work\ground-check.json'], check=True, timeout=360)"
```

KiCad 10.0.6 and its native Python API were exercised. The completed public run
used an initialized isolated `KICAD_CONFIG_HOME`; keep such preferences local.
Native graph runtime varies: two 180-second attempts expired, while the bounded
360-second run completed in about 165 seconds. Earlier same-purpose runs were
faster. No configuration or resource-contention cause is established. Stage and
CPU timings are recorded; do not turn a timeout into an unbounded retry.

## Owner pause and next item

**Paused after the September 14 wrap-up at the owner's explicit request.**
Do not continue automatically or schedule tomorrow's work; wait for the owner
to resume. No background engineering agent or routing loop was started.

Current package: `hardware/handbell/iterations/printed-bell-clock-draft`.
Current PCB SHA-256:
`f6a9d31192c7e59c4b81b7bcb281e23fd06cdc201e8a7a1f180ae7a8f860e3e4`.
Current report: `reports/power-lands.json`; public fill proof:
`reports/power-ground-check.json`. Status: **83/83 fitted MPNs, 56 opens,
zero other native DRC errors and 232 text/silk warnings**.

Next bounded item: apply the already documented conservative D3/D4,
Q1/Q2/Q4 and U3 envelope corrections and record resulting fit conflicts, if
any. Complete the remaining LED/diode/U2/U4 land/paste dispositions and
existing-part audit before declaring geometry frozen. No new sourcing or
automatic routing restart. Then follow core/power, constrained signals,
remaining controls and final ground closure in the sequence above.

The full mechanical bind, 0.15 mm USB bezel adjustment, native CAD camera-state
handoff, current budgets, supplier processes and matched quotation exports are
still pending. Preserve earlier prints, models and the recovered candidate.
No supplier upload/order, functional or child-use approval is implied.
