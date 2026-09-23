# Routing automation: exercised tools and lessons

September 15, 2026. The owner authorizes bounded tooling/autorouting trials
and requests that their lessons remain in the repository. This is not
authorization for cloud routing, supplier uploads or automatic acceptance.

## Current conclusion

**Native local review views:** `tools/render_clock_detail.py` now also accepts
`--pcb`, `--layer`, `--bounds XMIN YMIN XMAX YMAX` in native millimetres,
and repeated `--highlight-net` options. The default clock view and its
1200 x 1020 size remain available. Views carry the actual PCB SHA-256,
reject disabled layers/invalid bounds, and refuse to save if the input
changes during rendering. F, B and In2 views were exercised with KiCad
10.0.6. These are non-mirrored native-coordinate primitive silhouettes:
zone fills, drill voids and physical contact envelopes are not rendered.
They aid local engineering review, not clearance, plane or assembly proof.

```powershell
$pcb = '.\hardware\handbell\iterations\printed-bell-four-layer\handbell.kicad_pcb'
python .\tools\render_clock_detail.py --pcb $pcb --layer F.Cu --bounds 86.1 90 94.5 96 --highlight-net '+3V3' --output "$env:TEMP\imu-front.png"
```

**September 23 working fanout method:** a source-preserving private fixture
now contains actual boundary clipping, obsolete-fanout removal and a new
three-segment SCL escape. Its primitive graph has no shorts, but the rest
of the IMU block remains incomplete. The
[saved-fixture validation](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-fanout-method-validation.json)
passes all 18 gates, including deliberate one-IU rule, footprint and boundary
mutations. Compare zone definitions separately from intentionally removed
`filled_polygon` caches; do not either reject cache invalidation as a rule
change or ignore a genuine zone-parameter change. Validate the saved artifact
without regenerating it, and distinguish reused geometry results from a
fresh DRC/refill. An explicitly incomplete working copy permits genuine
replacement routing; retaining every obsolete local terminal does not.

**September 23 re-layout execution limitation:** the subsequent
[three-construction screen](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-coordinated-relayout-trial.json)
did not implement the authorized complete local re-layout. The executor
confirmed that it neither replaced the SDA transition nor clipped/reworked
the permitted internal boundary traces. It tested moved-pad tails to old
terminals instead of replacement I2C/supply fanout. Preserve those rejected
constructions, but do not infer that the broader authorized scope failed.

For a fine-pitch package, an old terminal can become a different-net pad
after a move: a 0.50 mm north shift puts IC4.13 SCL exactly at IC4.14's old
SDA centre. Reconnecting to every old terminal is therefore not a general
placement-preservation strategy. Identify legitimate retained connection
points outside the affected fanout and synthesize the substitute paths.
Omitting a movable via from an obstacle mask does not supply its replacement
connection. Likewise, permission to reroute inside a boundary is not exercised
by continuing to treat whole crossing tracks as fixed. Distinguish authorized,
actually attempted and completed freedoms explicitly in reports.

**September 23 joint-plan result:** all twelve released fixed-placement
IMU plans failed before a board candidate was written. The entire proposed
IC4.6/7 via-centre region conflicts with the tested straight INT-west
escape; the three tested INT transition positions also conflict with the
ground vias. Additional fixed-copper hits remain separate constraints.
Nonempty proposal regions are upper bounds, not legal via/stub proofs.
The [trial report](../hardware/handbell/iterations/printed-bell-four-layer/reports/imu-fixed-placement-trial.json)
records 38.094 seconds of tool execution, no trace removal and no candidate
refill/DRC. It does not prove that every bent or different-length escape
fails, nor measure total engineering time.

Apply the joint compatibility gate when selecting a local floorplan, not
only after choosing separate return and signal routes. Distinguish fixed
mechanical/critical interfaces from inherited routing choices: an ordinary
local transition via is not automatically an immutable mounting datum.
Changing such a constraint still needs explicit engineering release and
restoration of every affected connection. After repeated no-progress
screens, decide the coordinated re-layout scope rather than increasing
sample counts or declaring all fixed-placement routing impossible.

**September 23 IMU domain lesson:** conservative region construction
distinguishes potential via-centre space from a legal connection: three
centres survived for IC4.1/2/3, but every tested straight stub hit IC4.4.
Also distinguish initial-domain obstacle witnesses from active constraints
on the final space. Omitting four local +3V3 tracks had no geometric
benefit because rear-contact restrictions already excluded their region;
one omission would break R14's supply. Inspect coordinates and overlapping
constraint masks before commissioning a cut analysis. Preserve the stated
approximation/clearance assumptions, and do not turn an empty conservative
domain into a global impossibility claim.

**C23 closure and validator lesson:** native controls and complete saved-board
checks now support the accepted 43-open checkpoint. A no-routing refill
control reproduced the source exactly. Five remote comparison components
required at most 2 IU of opposite-fill inflation and passed actual
clearances; their Boolean-intersection failure mechanism remains unknown.
Use the qualified graph of actual filled islands for electrical attachment,
not a requirement that each derived difference sliver be a separately
representable copper island. Keep displacement and clearance proofs
independent: tiny area or a distant bounding-box extent is not either proof.
Exercise actual Python bindings and boundary semantics before full-board
validation; `pcb.FromMM(1.0)` is exercised, `pcbnew.IU_PER_MM` is unavailable.
Persist passed gates before subsequent assertions can fail, preserve
failed evidence, and distinguish reused DRC from a fresh execution.
See [closure gates](../hardware/handbell/iterations/printed-bell-four-layer/reports/c23-usbboot-closure-gates.json)
and `tools/check_c23_usbboot_validation_controls.py`.

**Latest radial screen:** replacing four axis samples with a fixed
three-radius/sixteen-direction set found usable sites for three of six
ground groups (C4, C11/C15 and U2). All 336 rows were persisted before
validation; the compact report retains counts, selected geometry and blocker
identities. The staged result has 44 opens and unchanged F/In1 fill geometry.
This demonstrates that the earlier four-site failures were not proof of
geometric exhaustion. C12/C23/C24 still need obstacle-based engineering
review rather than another unconstrained search.

**Latest ground-stitch validation:** isolated circle, slot and contact
controls pass, followed by the full read-only saved-candidate suite.
Circular drill clearance uses exact integer squared-distance comparisons;
slotted holes use native effective-hole shapes, not a circular substitute.
Boundary controls distinguish exact minimum clearance from one internal unit
inside/outside. The [final report](../hardware/handbell/iterations/printed-bell-four-layer/reports/supply-ground-stitch-validation-final.json)
records unchanged F/In1 filled area, all preserved connections/private returns
and 47 opens for the saved candidate. Earlier checker failures below remain
historical. No new routing or refill occurred to obtain this result.
Graph paths through filled islands establish topology, not a physical trace
length or high-frequency return quality.

**September 22 ground-stitch checker lesson:** a copied validator assigned
the ten F-only private exclusions to In1 and reported a false guard failure.
The same eight intersections occur on the accepted baseline and candidate.
Bind each guard to its declared native layer and validate that declaration
against the released plan; a correct polygon on the wrong layer is still
an invalid check. Preserve the failed evidence, exercise baseline controls,
and finish the full saved-candidate suite before any acceptance. The
[diagnosis](../hardware/handbell/iterations/printed-bell-four-layer/reports/supply-ground-stitch-diagnosis.json)
does not establish a valid candidate by itself. Persist finite screening
counts and blocked-group reasons before later checks can fail; these were
lost in the initial stitch attempt and must not be invented.

The corrected guard validator subsequently passed guard and connectivity
checks but stopped at a via-span assertion that compared native layer
enumeration to physical stack order. KiCad's `GetLayerSet().Seq()` is not
physical stack order: validate membership independently of iteration order
and check the native via span/type explicitly. Physical ordering requires
the existing ordinal conversion. This stop does not itself establish an
incorrect via; the full remaining contact/drill/DRC/fill-delta gates are
still required. One surgical validation-only correction is authorized;
no further copper generation or refill is part of it.

That final correction passed the layer membership controls but stopped on
the circle-to-circle `Collide` overload during drill checking. Do not
interpret Python binding exceptions as geometric collision results. This
run remains incomplete; no additional corrective run is authorized by the
exhausted item. A future repair should first exercise the exact required
native shape operation in isolation, reusing known working collision
helpers rather than discovering overload errors late in full-board checks.

**September 22 supply bridge:** native connected-group terminals and a finite
polyline batch produced an accepted 0.40 mm In2 +3V3 bridge with no new vias.
Candidate 11 of 11 examined avoided fixed copper and unexplained In1 gaps;
48 opens remain. Existing F/In1 fill inputs/caches were unchanged, and native
DRC did not request a refill. This exercised a narrow inner-route construction
and verification path, not a generic multilayer router. The session-local
executor and its two implementation corrections are identified in the
[acceptance record](../hardware/handbell/iterations/printed-bell-four-layer/reports/in2-3v3-bridge-acceptance.json);
the report and PCB preserve the exact reproducible three-segment geometry.

**September 22:** root engineering review accepted the exact saved
explicit-settings plane candidate as an incremental routing baseline.
The [promotion record](../hardware/handbell/iterations/printed-bell-four-layer/reports/in1-plane-acceptance.json)
binds the 49-open PCB and updated manifest to identical project/library
dependencies. No native check or refill was repeated for byte-exact promotion.
The earlier pause and unaccepted-stage descriptions below are historical.
The next gate is actual connected-group/return-corridor release, not another
round of fixture or refill development.

**End-of-day September 21:** engineering is paused. The explicit-settings
production In1 candidate passes the recorded scalar and supplementary
private-return/source-preservation checks and has 49 opens, but remains
unaccepted pending root actual-copper/return-path review. The accepted board
still has 51 opens. The [handoff](pcb-closure-plan.md#owner-pause-and-next-item)
links the saved candidate archive and actual native views.
The discarded bounding-box-only SVG was not a copper plot; never use island
bounding rectangles as evidence of plane continuity. Executed tool hashes
remain bound to their respective runs, even when later rendering-only
corrections change the checked-in tool.

**Latest September 21 result: the saved-native graph controls passed.**
[`check_four_layer_graph.py`](../tools/check_four_layer_graph.py) now extracts
fixture syntax from the accepted native PCB instead of creating native
objects through Python. In a fresh persistent workspace, KiCad reports the
exact deliberately crossing GND/+3V3 track UUID pair on In1, and the graph
reports that short without merging the distinct logical net groups.

The separate plane fixture proves C23/C24 GND disconnected before fill and
still disconnected in the post-fill primitive graph, but connected through
an exact native In1 filled island and via annuli in the filled graph.
A present, still-GND In2-only witness remains disconnected. Same-XY F/In1
conductors without a via also remain separate. The hardened confirmation's
CLI refill/save stage took 2.500 seconds. These results qualify the exercised
graph/filled-island behavior, not production routing or plane topology.

The [accepted control report](../hardware/handbell/iterations/printed-bell-four-layer/reports/four-layer-graph-saved-native-control.json)
binds source, fixtures and executed tools. Reproduce with
`python tools\check_four_layer_graph.py --work-dir C:\Temp\NEW_GRAPH_CONTROL`;
the directory must not exist. Native workers have finite timeouts, stage
logs are retained even on failure, and public reports omit machine paths.
No old workspace is reused or relabelled with current tool hashes.
The source/manifest guards must match; raw fixtures retain the derivative's
CC BY-SA provenance. No production board was changed.

**Production trial:** the first staged In1 plane completed native refill in
3.656 seconds and DRC in 3.312 seconds, but failed the existing filled-pad
group preservation gate. Its 50 opens, unchanged 233 warnings and zero other
native errors do not override that regression. The source remains unchanged
at 51 opens. Preserve the candidate and identify the separated subset before
changing geometry: a list of all former group members is not a list of
independent root faults. The unfinished staging script must not be treated
as a complete plane acceptance checker.

The read-only diagnosis isolates only **C25.2**. Canonical and transplanted
F/In1 fill blocks match exactly; neither cache transfer nor either private-via
guard's serialization explains the change. The CLI refill input had no
same-stem project, and merely supplying that project would still not replay
the accepted settings: `refill_front_ground.py` explicitly tightens clearance,
edge and polygon-error limits in memory. The project's polygon error is
0.005 mm; the exercised recipe requires 0.001 mm. These are concrete
workflow differences, not yet proof of the specific causal setting.
The incomplete staging script is disabled before writes/processes.

The [explicit-settings replay](../hardware/handbell/iterations/printed-bell-four-layer/reports/in1-refill-settings-control.json)
passes: all 22 F fill blocks are reproduced, all 137 prior pad groups remain
connected, C25.2 retains its connection to MH1.1, and both private pickoffs
remain independent until their terminals. No shorts or floating copper were
found. No inner plane was present and native DRC was not rerun; this is not
production-plane acceptance.

**Next:** replay the released In1 geometry using the established settings,
with all missing per-layer acceptance gates implemented first. Do not
change geometry to hide a refill regression. The legacy F/B-only route
search/masks remain unqualified for inner routing. They need not be rebuilt
before a native plane operation that does not use them; qualify only the
tools actually used by the next bounded operation. Keep the failed paths
below as history, not the current graph status. Their native crash causes
were not established by the successful replacement workflow.

**September 21 four-layer update:** the logical migration baseline is now
`printed-bell-four-layer`; the two-layer pilot below is historical. Primitive
and filled-zone graph code now enumerates enabled copper layers in physical
order rather than assuming F/B. Basic separation, through-via/inner-annulus,
short-reporting and unchanged production pad-group controls passed in the
initial experiment, but **the full all-layer graph gate is not qualified**.

The native-fill fixture initially lacked a finite board outline and used a
positive witness that was already joined by primitive copper. After those
test defects were corrected, native In1 fill completed, but a post-fill
different-net-crossing assertion failed before the plane-connectivity
assertions ran. Do not bypass that assertion or blame the real board.
The next diagnostic must compare fixture UUID/net identities and graph
edges before native connectivity build and after fill, identifying the
state change before any further correction. Preserve the partial
[control report](../hardware/handbell/iterations/printed-bell-four-layer/reports/four-layer-graph-control.json).
The corrected fixture has not qualified production inner routing/planes.
Old F/B routing masks and the F-only ground checker remain unreleased for
that purpose.

The owner-approved saved-file alternative also stopped within its attempt
limit. Its short fixture completed creation, native CLI DRC and a fresh
graph check, but the separate plane creator crashed with `0xC0000374`
before saving. The CLI's actual `--refill-zones --save-board` support was
confirmed; **the plane CLI/refill stage was never reached**. This is not
evidence against four-layer PCBs or the CLI's ability to fill a valid file.
Unfortunately the harness's automatic temporary-directory cleanup discarded
the successful-stage details after the later exception. The
[saved-file report](../hardware/handbell/iterations/printed-bell-four-layer/reports/four-layer-graph-file-control.json)
states that evidence loss rather than reconstructing measurements.

Automatic runs of the unfinished control are now disabled. Before any
further attempt, replace the unreliable plane-creation path with a known-good
saved fixture, retain workspaces/logs on failure, require the actual native
short finding rather than any clearance finding, and use a **same-net**
unconnected conductor for the cross-layer-isolation negative control.
The present different-net CONTROL witness cannot distinguish layer isolation
from net filtering. These are fixture/harness issues, not permission to
relax the graph or production-board checks.

**Native KiCad API analysis is established; Freerouting integration remains
experimental.** Keep using exact geometry and connectivity, with images as
an explanatory aid. The remaining automation gap is generating constrained
route alternatives, not reading the board.

Do not replace the accepted PCB with a whole imported SES board. The
no-routing control changes existing geometry even without routing. That is
not proof of a functional defect, but it creates unnecessary source, layout
and artifact-rebinding work.

The accepted PCB remains `f26b8c6`, SHA-256
`57ae2c0b54e1313fb175ccdecdee07ebda07abed5151e776c9767511135d440f`,
with 52 opens. **No routing proposal from this pilot was promoted.**

## What has worked

| Technique | Evidence and lesson |
|---|---|
| Query complete relevant nets and obstacles through `pcbnew` before planning | The complete VHI chain exposed its existing layer transitions and the MCU ground grid. Inspect all obstacle classes, not just the first visible conflicting trace. |
| Numerically screen a bounded candidate batch | Three via-array layouts were screened for the VHI/C8 corridor; the accepted layout retained nine vias and feed widths. This was a geometry pre-screen, not a general autorouter. |
| Read actual courtyards before moving parts | The C6 proxy-envelope screen passed while native courtyards overlapped. Proxy envelopes, native courtyards and physical qualification are different constraints. |
| Reuse source-bound native and independent checks | `check_front_ground.py` preserves previous groups and private returns and can require named new connections. Refill only staged candidates; retain the original source text outside accepted edits. |
| Compare against a no-routing control | It separates exchange-induced coordinate/segmentation changes from actual routing work. Do not count those changes as progress. |
| Route between existing connected groups, not only nominated pads | The VCORE grid could reach C7 from C6, but not C8. Native geometry confirms C7 is already connected to C8; demanding a new path all the way to C8 unnecessarily retraces a narrow existing branch. |
| Stop processes with explicit deadlines | The external 60-second deadlines terminated unfinished engine runs. Pass limits alone are not wall-clock limits. |

## Freerouting pilot

Versions and verified download digests are in
[`freerouting-toolchain.json`](../tools/experiments/freerouting-toolchain.json).
The official Freerouting 2.4.1 JAR and portable Temurin 25 runtime were
downloaded and verified locally. Neither binaries nor upstream source are
vendored. No system-wide Java installation or PATH change was made.

The requested routing scope was one GAIN net, F only, no new vias, existing
wires/vias protected, fanout and optimization off, one routing pass, and a
60-second external deadline. Analytics and API/MCP servers were explicitly
disabled. No public routing service was used.

| Case | Engine wall time | Outcome |
|---|---:|---|
| Legacy short flags, intended no-route control | 60.171 s | Timed out; routing was active |
| Legacy short flags, requested GAIN route | 60.156 s | Timed out |
| Explicit routing-off control | 6.329 s | Completed SES exchange |
| Explicit settings, requested GAIN route | 60.203 s | Timed out |
| Bundled v19 engine, explicit settings, requested GAIN route | 60.094 s | Timed out |
| Persisted safe-default routing-off control | 5.500 s | Completed; repeated the same geometry-difference counts |

Elapsed times include engine startup and termination overhead. Some cases
ran concurrently with independent controls; these are observations, not
isolated performance benchmarks. No completed routed GAIN session was
obtained, so **the requested routing restrictions are not yet qualified**.
Do not interpret the engine's reported 176 unrouted items as our native
52-open baseline.
The DSN loads also reported eight warnings whose individual dispositions
were not established in this pilot.

### Settings trap: do not rely on `-inc`

At the pinned revision, legacy `GlobalSettings` parses `-inc`, but the
headless `CliSettings.mapFlagToProperty()` maps only `mp` and `mt`. The
headless job uses the merged settings path. Use explicit long settings,
and verify behavior rather than assuming the documented short form works:

```text
--router.ignore_net_classes=kicad_default,power,thickpower
--router.enabled=false
```

The second line is for a **no-routing control**, not a routing job. The
persisted harness now always uses explicit settings and returns a nonzero
exit status on timeout, engine failure or missing session output.

Sources: pinned [CLI documentation](https://github.com/freerouting/freerouting/blob/ae3d377740b6ffa744bed1bab26625fe0278fa90/docs/command_line_arguments.md),
[CliSettings](https://github.com/freerouting/freerouting/blob/ae3d377740b6ffa744bed1bab26625fe0278fa90/src/main/java/app/freerouting/settings/sources/CliSettings.java),
and [headless job setup](https://github.com/freerouting/freerouting/blob/ae3d377740b6ffa744bed1bab26625fe0278fa90/src/main/java/app/freerouting/Freerouting.java).
The remaining routing timeout cause was **not established**; do not
attribute it conclusively to the filter or algorithm.

### Exchange is a proposal interface, not our source of truth

The no-routing control:

- Translated 78 footprints by up to **0.0000664831 mm** (about 0.0665 micrometers);
  no footprint orientations changed.
- Removed 309 and added 292 exact track/via geometry records in a multiset
  comparison. Rounding and segmentation changes are not newly routed work.
- Retained 52 native unconnected items and produced zero native DRC errors.
  This was not a refilled, independently qualified replacement board.

The tiny translations are not presented as fabrication-significant defects.
They demonstrate why importing the entire board needlessly changes already
reviewed source geometry. Any integration should transfer **only new
authorized copper** onto the original board, then apply our normal gates.

Other export findings:

- DSN declares 0.1-micrometer coordinate resolution.
- It emits a 50-micrometer SMD-to-SMD exception; the pilot raises that to the
  project's 200-micrometer floor.
- The GND zone is exported as an outline plane, not our proven filled
  connectivity. The pilot removes that plane and defers real fill to KiCad.
- Pour-only exclusions become conservative routing keepouts in DSN.
- Exported class widths are not substitutes for the manually designed power
  paths: `power` is 0.1778 mm, while existing power paths may be much wider.
- The conductive battery bases are separate model constraints, not ordinary
  native copper. The F-only/no-via pilot does not qualify their representation
  for unrestricted routing.

## Reproduction and next bounded step

[`freerouting_pilot.py`](../tools/experiments/freerouting_pilot.py) requires the
pinned PCB and JAR, a new output directory, and explicit local tool paths:

```powershell
python -c "import subprocess; subprocess.run(['python', r'tools\experiments\freerouting_pilot.py', '--java', r'C:\local-tools\temurin\bin\java.exe', '--jar', r'C:\local-tools\freerouting-2.4.1.jar', '--output', r'C:\pilot-output\control', '--no-routing'], check=True, timeout=110)"
```

Replace the example tool/output paths with the verified local paths. Omitting
`--no-routing` requests the GAIN experiment; `--legacy-engine` requests the
bundled v19 algorithm. The returned PCB is disposable and never auto-promoted.
Compact source-bound results are in
[`routing-tool-pilot.json`](measurements/2026-09-15-routing-tool-pilot.json).

**Next investment:** a reduced, one-net geometric problem and additions-only
transfer, rather than more blind whole-board runs or debugging the entire
upstream router. Enforce scope in the problem itself, retain fixed copper and
custom exclusions, and reject proposals that alter other nets or violate the
native/filled checks. Demonstrate one useful proposal within a fresh bounded
item before expanding scope. No savings or routing-completion guarantee is
claimed yet.

## Subsequent VCORE grid attempt

The existing `route_printed_bell.Router.search` was reused with native-shape
obstacle masks, a 0.05 mm grid, 0.20 mm traces, retained contact-metal
reservations and an 80,000-expansion cap per connection. A native numeric-type
correction and one clearance-screen correction exhausted the retry allowance.
Neither routing search produced a C6.2/C8.1 candidate. C18 was not attempted.
The board remains unchanged; this is not evidence that its layout is impossible.

The read-only [diagnostic](../hardware/handbell/iterations/printed-bell-clock-draft/reports/core-distribution-diagnostic.json)
shows C7.2 in C6.2's reachable F grid component. The
[attempt record](../hardware/handbell/iterations/printed-bell-clock-draft/reports/core-distribution-attempt.json)
confirms native connected groups: C6/IC1.50; C7/C8/IC1.45; C18/IC1.23.
The chosen endpoint therefore made the search needlessly traverse an already
connected narrow branch. Sampled reachability still requires exact segment
and filled-board review before any route is accepted.

Next: connect C6's group at **C7.2**, then connect C18 to the merged group.
Do not move parts, alter 3V3 or shrink the grid merely because this fixed-pad
search failed. The experimental staging branch has not produced an accepted
board and is not a manufacturing flow.

Reproduce only the read-only diagnosis from the repository root:

```powershell
python -c "import subprocess; subprocess.run(['python', r'tools\experiments\diagnose_core_distribution.py', r'C:\pilot-output\core-diagnostic.json'], check=True, timeout=90)"
```

Use an existing output parent and a new report filename. Both experiments
require the exact accepted `57ae2c0b...` board.

### Group-terminal follow-up: preserve supply and return together

The C6.2/C7.2 candidate generated in 2.094 seconds, with thirteen 0.20 mm
F tracks and no new vias or moved parts. It was **rejected**, not promoted:
refilling split the original capacitor-ground group into C6 alone, C17 alone,
and C7/C8/C13 together. The candidate had 53 opens despite joining the VCORE
groups and having no other native DRC errors.

Two corrections reserved explicit F ground connections before searching
for VCORE, first on the 0.05 mm grid and then at 0.025 mm. Neither found a
VCORE path within the fixed budget. The
[preserved attempt](../hardware/handbell/iterations/printed-bell-clock-draft/reports/core-distribution-right-attempt.json)
records the initial copper and failed corrections. The original board still
has 52 opens. C18 was not attempted.

**Affected item stopped:** a coordinated supply/return corridor repair is
needed before another attempt here. Neither faster search nor a connected
signal compensates for losing its return. This does not prove the two-layer
board impossible; the fixed-layout, sampled search cannot resolve it yet.

### GAIN follow-up: report why search stopped

An independent GAIN attempt also stopped without accepted copper.
A 3V3 via/two-endpoint shift near U4 was screened as a local escape correction,
but did not produce a route. The final 8 mm-margin, 160,000-expansion-budget
attempt exhausted its masked component after **147 expansions**. This is not
a timeout or evidence that a larger computation budget will fix it.
The [attempt record](../hardware/handbell/iterations/printed-bell-clock-draft/reports/gain-routing-attempt.json)
preserves all cases and the unapplied correction. Twelve nearby gain-jumper
positions also failed the copper screen; none was moved.

The existing search now distinguishes missing endpoints, expansion-limit
exhaustion and no path in its sampled domain. That diagnostic distinction is
not a proof of continuous geometric impossibility. Stop GAIN retries pending
local escape/topology review; retain the accepted 52-open board.

### Accepted short-branch result

The independent R2.1/CHG0.C branch generated in **2.0 seconds** using the
same native-mask search. Seven 0.20 mm F segments were accepted after filled
connectivity preserved all previous groups/private returns; no part, via or
existing-track changes were needed. The board now has **51 opens**.
See [`charge-led-routing.json`](../hardware/handbell/iterations/printed-bell-clock-draft/reports/charge-led-routing.json).
This is demonstrated usefulness on one short branch, not qualification of
the router for arbitrary nets or evidence of a total completion cost.
