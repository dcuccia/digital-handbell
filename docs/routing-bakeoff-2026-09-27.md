# Purpose-built routing bakeoff - September 27, 2026

**Local assessment complete; Quilter execution awaits preservation/import review.
No experimental routing is accepted.**

**September 28 support clarification:** human Quilter support identifies the
preservation control on the **next step, Constraints, table 2: Define Your
Own Constraints**, with pours added **by net name**. The previous search
stopped at Circuit Comprehension and therefore did not establish that the
control was missing from the workflow. That navigation conclusion is
superseded. Advance the existing draft for inspection, without submitting.
Both required pours are on `GND`; inspect whether the control preserves both
F and In1 zones and their exclusions. Do not enter zone names into a net-name
field or add `/PROT_FET_RETURN` as a general ground pour. Actual UI behavior,
existing In2 trace preservation under the selected vendor stackup, and the
reported import/comprehension errors remain unverified.
Manual/LLM-driven routing is paused. The owner requested approximately
90 minutes of active investigation, normally at most 30 minutes per approach,
with no trace-by-trace cleanup and no automatic continuation of manual routing.

## Snapshot and isolation

The accepted design was already committed at `92b3af9`; the assessment
authorization/pause is committed at `a8dfafe`.

- PCB: `adc262b3e7056cb9031387c55262b5cf99e599ae6e28970f9784f5237e662314`.
- Manifest: `b849b5defb95f010f555d43b6d261fdea3ef37e240aee0190a607fb519c642f8`.
- Separate local `baseline`, `freerouting`, `quilter` and `tscircuit` copies
  were created, each with 50 source/package files plus root attribution and
  license notices. A snapshot manifest binds the files to the commit.
- The held, disconnected MCU fanout fixture is **not** an assessment input.
- No experiment may import into or merge with the working PCB.

The owner expressly approved a sanitized public-design upload to Quilter and
created an account. This does not authorize paid execution, purchases or
fabrication. Personal KiCad preferences, credentials, reports containing
ambient machine data and unrelated files are excluded from the input package.
Quilter's public terms contain a performance-benchmarking restriction.
After being informed, the owner clarified that their purpose is private
adoption evaluation, not performance benchmarking. This records the owner's
intent, not vendor permission or a legal conclusion. No Quilter performance
result has been measured or published.

## Engineering baseline

Fresh native and independent filled-connectivity checks reproduce **37 opens**,
234 other DRC findings and 46 explicitly enabled schematic-parity findings.
All 46 parity notices are warning-level `net_conflict` items: 22 explicit
unconnected-pad net names and 24 auto-named nets. These remain release
dispositions, not proof that every schematic/PCB discrepancy is harmless.
Both tested candidates retain the same counts, with no additional native
error-level findings. This is not a clean DRC release: the opens and warnings
remain.
An autorouter's own airwire count is not interchangeable with KiCad's count.

| Layer | Intended role |
|---|---|
| F.Cu | Components, local decoupling, critical signals and switching loops |
| In1.Cu | Substantially continuous protected GND; not routine signal routing |
| In2.Cu | Power distribution and specifically released lower-speed routing |
| B.Cu | Existing power/contact copper and constrained routing; not a free surface |

The nominal board thickness is 1.6 mm. The actual fabrication dielectric and
copper construction is not yet selected/qualified. USB full-speed remains
approximately 90-ohm differential design intent, not a verified impedance
claim. Fast signals cannot simply be moved to either inner layer.
The native PCB has four enabled copper layers but **no detailed `stackup`
block**. An importer that asks for physical layer construction must not be
treated as having read an already-qualified fabrication stackup.

The board contains 325 physical pads, 1,107 track segments and 97 through-vias.
Track counts/lengths are F: 903 / 735.668 mm; In2: 24 / 37.798 mm;
B: 180 / 320.147 mm. In1 has no signal tracks. **Zero native tracks/vias
are locked**; preservation currently depends on engineering policy and
source-bound checking. Each Freerouting DSN explicitly marked all existing
wires/vias `protect`.

Already-connected critical structures include QSPI, the local crystal
network, boost switching/feedback nets, private protection nodes, and +3V3
distribution. Whole-system power and return closure is not complete:
VCORE, VBAT, VHI, VBUS, VAMP, GND, USB and part of the audio output remain
among the reserved opens below.

F and In1 have native GND zones with deliberate private-return,
switching-node and crystal-region exclusions. Preserve raw `/CELL_NEG`
isolation and the R26/R27 and R24/C28 private returns. A pour outline is
not equivalent to the saved filled polygons or their connectivity.

Native net classes are `Default`, `power` and `thickpower`, with nominal
widths 0.20, 0.1778 and 0.3048 mm. Assignment patterns are sparse and do not
fully encode engineering priorities or current requirements. Native project
minima include older 0.1778 mm clearance, 0.025 mm edge clearance and
0.005 mm polygon error. Exercised engineering/refill requirements are
0.20 mm foreign-copper clearance, 0.25 mm edge/hole/contact clearance and
0.001 mm polygon error. Do not use the weaker defaults as waivers.

New ordinary vias use 0.604/0.35 mm copper/drill and cannot overlap F/B SMD
lands, even on the same net. Rear contact metal extends beyond native pads.
All five mandatory resin-filled/capped vias stay unchanged. Through-via
lands remain conductive even when filled or tented.

### Approximate remaining-work classification

These counts use the complete post-IMU ledger, adjusted for the subsequently
accepted C13 ground stitch (GND decreased from seven to six opens).
They classify routing risk, not guaranteed routability or completion time.

| Class | Nets / obligations | Native opens |
|---|---|---:|
| A: engineering-heavy | GND 6; USB/D+/D- 4; VCORE 2; VBUS 2; VBAT, VHI, VAMP, VO+, Net-(FB2-P$1) one each | 19 |
| B: constrained automation | I2S_BCLK/DIN/LRCLK two each; POWER enable 2; GAIN, SWCLK, SWDIO one each | 11 |
| C: ordinary candidates | AMP_MUTE 2; BUTTON, D13, INT one each; reset 2 | 7 |

The first local router trial is limited to class C. Existing copper is
protected across **all** classes. Class B is not blanket authorization to
route clocks over split references. USB, crystal/Y1/C2/C3/R6, QSPI, local
decoupling, switching/protection and audio-current topology remain reserved.
Connectivity alone is not powered, SI/PI, thermal or safety qualification.

## Prior experiment: a real external autorouter

The earlier experiment used **Freerouting 2.4.1 via Specctra DSN/SES**,
not KiCad's Attempt Finish. Its small two-layer, F-only/no-via GAIN trial
timed out at 60 seconds. An explicit routing-disabled control completed
in approximately 6 seconds. Legacy short flags had not reliably disabled
routing or selected classes; the corrected experiment used explicit settings.

The no-routing exchange rounded 78 footprint positions by up to about
0.0665 micrometers and changed trace segmentation/coordinate records.
Those differences were not newly completed connections. This is an
integration/preservation concern, not evidence that tiny rounding alone
makes a board electrically defective. See [prior evidence](routing-tooling.md#freerouting-pilot).

## Results

### Freerouting: no demonstrated routing leverage in the tested scope

The local stable workflow used Freerouting **2.4.1**, portable Temurin
25.0.4.1+1-LTS and KiCad 10.0.6 native DSN export / SES import. Analytics,
API/MCP servers and job saving were disabled. Existing wiring was protected,
fanout and optimization disabled, and routing limited to one pass/one thread.
Original classes were ignored; the five class-C nets were assigned to a
separate target class.

**Scope limitation:** only F.Cu/no-new-via routing was exercised. The
through-via/contact-metal constraints were not qualified in the DSN model,
so the experiment did not unlock In2 or B merely to obtain a result.
The two exported plane outlines were omitted from DSN; actual F/In1
connectivity was restored and checked through native refill, not inferred
from those outlines. **This is not a test of Freerouting's full multilayer
capability**, nor evidence that another qualified integration cannot help.

| Trial | Engine time | Target opens closed | Native opens after refill | New native DRC findings |
|---|---:|---:|---:|---:|
| No-routing exchange control | 6.594 s | 0, by design | 37 | 0 |
| Initial routing, 0.25 mm target width | 128.860 s | 0 / 7 | 37 | 0 |
| Matched 0.20 mm no-routing control | 4.297 s | 0, by design | 37 | 0 |
| Corrected routing, native 0.20 mm width | 49.578 s | 0 / 7 | 37 | 0 |

Root identified and corrected an initial setup confound: the executor had
chosen 0.25 mm instead of the native Default width of 0.20 mm. At the
0.4 mm MCU pitch this can prevent a centered escape satisfying 0.20 mm
clearance. The corrected run still closed no connection. That removes
the width mismatch as a sufficient explanation; it does **not** establish
the actual failure cause or prove geometric impossibility.

The no-routing control moved 78 footprint origins by at most 0.00005 mm,
changed no orientations, and removed/added 356/338 exact geometry records.
These are exchange-rounding/segmentation changes, not routing progress.
The routing-enabled candidate retained the control's geometry records and
added 128 F records, including non-target nets; it introduced **zero vias**.
The only target length changes were microscopic: AMP_MUTE +0.000100 mm and
BUTTON +0.000424 mm, with unchanged physical-pad partitions.
GND's recorded centerline total increased by 86.220118 mm, but overlapping
or duplicate records have not been distinguished from new physical area.
Do not treat that length as 86 mm of useful newly routed ground.

Native refill used the established 0.20/0.25/0.001 mm recipe. Both results
preserve all recorded net partitions, with no graph shorts or floating
copper. The engine's own 117 incomplete connections and 190 clearance
violations differ from native counts and are not acceptance evidence.
Private-return cut proofs and exposed-contact safety were not newly
qualified for arbitrary router output; no integration is approved.

Root inspected the supplied F/In1/In2/B plots: the MCU/crystal region,
lower switching region and broad B contact/power layout remain recognizable,
with the expected In1 crystal/switching exclusions. No useful new target
path or layer-transition pattern exists to assess. The plots are coarse
review evidence, not measurement of tiny exchange changes or proof of
high-frequency return quality. An optional track-area diagnostic could not
run because Shapely was absent; no dependency was installed for that
nonessential measurement.

**Disposition:** reject both scratch results and stop. No optional breadth
run, hand cleanup, copper transplantation, or full-board automatic routing
was performed. A future local-router trial first needs a demonstrably
faithful constraint/exchange model; repeating trace-level LLM babysitting
would defeat this exercise.

Public compact evidence:
[initial/control report](measurements/2026-09-27-router-bakeoff/freerouting-bakeoff-report.json)
and [corrected-width report](measurements/2026-09-27-router-bakeoff/freerouting-width020-report.json).
Their hashes are respectively `c51da7a7...` and `f4678027...`.
Raw DSN/SES, scratch PCBs, native reports, helpers and views remain in the
separate local experiment directory, not the authoritative package.

### Quilter: uploaded and comprehension reviewed; no routing job

Official documentation directly supports this use case: components inside
the board boundary retain position/orientation, existing traces/vias retain
their paths, and incomplete pre-routed connections may be completed.
However, **internal copper is deleted/regenerated unless input-stackup
preservation is selected**. Pours must be named and individually included
in the Preserved Pours table; KiCad locks alone are not sufficient.

The separate loose-file input set is ready:
`handbell.kicad_pcb`, `handbell.kicad_sch`, `handbell.kicad_pro`.
There are no hierarchical child schematic files. Board footprints are
embedded. The source contains 104 total footprints, 1,107 segments and
97 vias; the footprint total includes test/mechanical/non-fitted items
and is not the 83-part fitted assembly count.
Required named pours are `quote-native-F-GND-v1` and `in1-protected-gnd-v1`.
A separate `ASSESSMENT-CONSTRAINTS.txt` explains the engineering requirements;
it is a human review aid, not a claim that the uploader enforces prose.

The user operates the signed-in browser and confirmed uploading all three
files. They supplied setup screenshots and eight downloaded Circuit
Comprehension CSVs. No routing-job submission or returned candidate is
confirmed. No credentials were requested or obtained.

The observed UI exposes layer classes and editable fabrication minima.
The JLCPCB preset initially classified both inner layers as GND; the owner
was instructed to change the second inner layer to Signal for mixed use.
This is setup guidance, not a source stackup change or evidence that
existing inner copper will be retained.

**Actual import/comprehension findings:**

| Observation from the uploaded input / downloaded CSV | Engineering disposition |
|---|---|
| Parser reports 16 board components missing from schematic | Native inspection finds 14 present, with matching symbol UUID path suffixes. Only MH1/MH2 are genuinely board-only. Do not reconstruct 14 existing circuit symbols to appease this warning. |
| Pin-count mismatch | Native audit identifies duplicate BT1/BT2 pad numbers, connector mechanical MP pads and an unnumbered U1 pad. Import handling remains unqualified. |
| USB D+/D- and USB_D+/USB_D- inferred as 100-ohm pairs | Does not match approximately 90-ohm design intent. Do not accept the inferred value. |
| VO+/VO- inferred as a 100-ohm digital pair | Incorrect treatment of class-D audio output circuitry. Remove that impedance-pair classification before any job. |
| GND and /PROT_FET_RETURN both classified as ground nets | /PROT_FET_RETURN is a distinct protection/current-sense-side node connected through R27, not a general ground reference. It must not become an alternate plane or bypass R27. |
| All seven listed rails set to 500 mA and `use_power_pour=true` | Unverified inferred current budgets and blanket pour creation are not approved. This is not a physical power-layout specification. |
| Crystal and switching-converter tables empty | No explicit inferred Y1/R6 or U5/L1 critical-loop constraints. Existing copper remains protected, but automatic comprehension is incomplete. |
| Most +3V3 capacitors assigned to U2.5 | Shared-net attachment is not identification of each MCU/IMU local decoupling role. |
| C6 assigned to IC1.23; C8 assigned to IC1.50 | Our local design connects C6 to DVDD50 and C8 to the regulator-output group IC1.45. Inference does not capture intended local current paths. |
| C2/C3 appear as bypass capacitors; C21/C22 appear as ferrite-pin bypasses | These are crystal-load and audio-filter capacitors, respectively, not ordinary supply decouplers. |
| CSV assigns equal `100` capacitance to native 0.1 uF, 1 uF and 10 uF parts | The supplied UI PDF confirms nF units. For example, C5 is 10 uF in the source but 100 nF in the inference; C8 is 1 uF but 100 nF. |
| No preserved-pour CSV among the eight downloads | Preservation has not been demonstrated; absence of a CSV alone does not prove the feature is unavailable. |

The exported CSVs are retained unchanged in the isolated local experiment
and as [unaccepted inference evidence](measurements/2026-09-27-router-bakeoff/quilter-inferred).
They are useful diagnostic evidence, **not accepted constraints**. No mass
manual correction or schematic/netlist rewrite has been performed.

The owner's complete three-page Circuit Comprehension PDF identifies
UI/API **1.39.1**. Its category list ends after Crystal Oscillators and
BGA Components; no Preserved Pours control appears in that captured page.
This is an observed interface/documentation gap, not proof that the feature
cannot exist behind another account setting or workflow. Together with the
missing input-stackup option, it blocks this preservation-sensitive job.
Use vendor assistance rather than silently permitting ground regeneration.
The support chatbot repeated the documentation without locating the missing
control; the owner requested escalation and was offered a human handoff.
This September 27 observation is superseded by the September 28 navigation
clarification above; successful preservation is still not demonstrated.

Important review gates from official documentation:

- Generic KiCad support is documented, but no explicit KiCad 10 compatibility
  assurance was found. A successful parse must be checked against native inputs.
- General preparation documentation and the dedicated preserved-pours page
  conflict on internal-pour availability. Actual preservation of In1 GND,
  its exclusions and its no-signal role is a go/no-go gate.
- Differential-pair settings document 85/100 ohms, not our 90-ohm USB target.
  Geometry overrides exist but are not proof of a supported 90-ohm physics check.
- Timing-sensitive controls are documented as not publicly available.
  Crystal detection excludes load-limiting-resistor cases, relevant to R6.
  Existing QSPI/crystal copper must not be treated as generic reroutable logic.
- Inferred power currents and selected switcher capacitors are not project
  requirements. Review the actual associations; do not invent current budgets.
- Signals omitted from Circuit Comprehension are treated as generic low-speed
  digital signals. No dedicated private/Kelvin-sense constraint was found.
  Preserve the battery-protection sense topology explicitly.
- Rear battery metal is not guaranteed to be inferred from native pads.
  Enforced keepouts and full via-span restrictions need review.
- Free-tier eligibility and this account's entitlement were not verified.
  Pricing is per project based on unrouted pins, not our 37-open count.
  Stop at payment, upgrade, or an ambiguous submission/download charge.
- Documented job time is 15 minutes to 24 hours, often first results within
  an hour. A completed candidate inside this assessment is not guaranteed.
  A vendor "successful" candidate can still be less than fully connected.

No public CLI/API invocation contract was found. Hosted UI is the currently
documented path; enterprise integrations are not evidence of an available
local routing CLI.

### tscircuit: real incremental import exists, but fails preservation needs

Current official source is more capable than footprint-only import.
It supports `.kicad_pcb` -> Circuit JSON, importing existing traces/vias,
selected connections or regional rerouting, and KiCad export. There is
even a KiCad 10 named-net connectivity test and an imported-Arduino reroute
example. It would be inaccurate to dismiss it simply as requiring a complete
TypeScript re-entry of every board.

However, the round trip reconstructs semantics this project must preserve:

| Source finding | Consequence here |
|---|---|
| Export initializes KiCad 9 format, 1.6 mm thickness, basic setup and internal layers typed as signal | Not preservation of our input settings or protected layer strategy |
| Zone import retains reduced polygon/layer/net data rather than the original rule object | Original refill semantics are not retained |
| Pour export creates new UUIDs, 0.15 mm clearance, 0.25 mm minimum thickness, 0.5 mm thermal settings and island-removal mode 0 | Conflicts with our source-bound GND/refill requirements |
| Trace conversion stitches routes and approximates arcs | Not a native-object-preserving copper patch |
| Unassigned connections can route after selected phases | Phase selection is not automatically a strict selected-net-only gate |

**Stop disposition:** no migration, installation or demo. A preservation-safe
adapter would be a separate integration project, exceeding this assessment's
potential benefit. Consider tscircuit for a future greenfield design or
separately scoped tool development, not as a drop-in round trip for this PCB.

Source revisions examined by the research executor: importer `3ff650e`,
exporter `9e66a9b`, core `43fd7e3`, props `1b255f1`, RunFrame `d32d609`
(upstream September 25-27, 2026). These were source inspections, not executed
conversion tests on this board.

## Comparison and recommended execution architecture

| Approach | Setup effort observed | Connections completed | DRC / preservation | Routing quality and cleanup | This board / next greenfield |
|---|---|---|---|---|---|
| Freerouting local DSN/SES | Reused prior tooling; control, one conservative trial and one width correction | 0/7 tested; 37 remain | No new native findings; exchange not byte-exact; extra non-target records | No useful target routes; integration cleanup unjustified | No demonstrated leverage in tested F-only scope; multilayer remains unassessed / potentially useful with router-ready constraints |
| Quilter | Account/UI upload and constraint review; now support-dependent | Not measured; no routing job | Import/inference and internal-copper preservation unresolved | Cannot grade unseen routes; substantial constraint preparation currently needed | Promising documented incremental workflow, blocked here / promising, with early verified comprehension and stackup |
| tscircuit | Short documentation/source reconnaissance; no installation or migration | Not measured | Converter reconstructs rules, layers and pours | Preservation adapter would exceed this trial's value | Not a drop-in solution / stronger greenfield candidate |

| Approach | Non-interactive operation | LLM involvement after setup | Obvious engineering concern categories |
|---|---|---|---|
| Freerouting | Local CLI exercised end-to-end | Low engine involvement, but presently high constraint/exchange investigation; no trace cleanup justified | Scope enforcement, exchange geometry, unqualified multilayer/contact model, no closure |
| Quilter | Hosted UI exercised; no public CLI/API contract verified | Front-loaded comprehension review plus exception review; actual steady-state effort unknown | Input association/value parsing, private returns, impedance/audio classification, missing critical associations, preserved layers/pours |
| tscircuit | Code/CLI workflows documented, not exercised here | Potentially low for greenfield; substantial adapter work for this source-preserving use | Stackup/rule loss, zone/refill loss, geometric reconstruction and selected-scope semantics |

**Recommendation: keep KiCad authoritative and adopt a guarded router
handoff architecture, not unrestricted autorouting or continued LLM
trace-by-trace construction. No tested product is ready for bulk acceptance
on this exact board today.**

1. Frontier-model engineering defines layer roles, native rule overrides,
   critical nets/current loops, return corridors, physical contact exclusions
   and explicit preservation contracts. Critical structures are completed
   or explicitly reserved before routine routing consumes their access.
2. A purpose-built router performs bounded bulk geometry only after a cheap
   qualification control demonstrates the required input semantics, existing
   copper protection and layer/net restrictions. Treat cloud comprehension
   as editable hypotheses, not circuit truth.
3. KiCad remains the native source of truth. Import only into disposable
   copies; refill, compare original pad groups and geometry, run full
   DRC/parity, and verify process/contact/private-return requirements.
4. Frontier-model review addresses exceptions and sampled topology—not each
   trace. Reject runs with no useful closure or large cleanup burdens.
   Any future transfer of accepted new copper needs separate authorization
   and an exact-source integration gate.

The next adoption step is **Quilter support qualification**, not another
blind run: locate/enable the actual preservation workflow and resolve the
specific KiCad import findings. If that cannot be done economically,
evaluate whether a small deterministic local constraint bridge is worth
building before more Freerouting trials. Neither path is automatically
authorized by this report.

For a greenfield board, choose and encode a supported physical stackup
early, use consistent native symbols/footprints and values, establish
complete decoupling/return/via-access cells, and test router interoperability
before investing in dense partial routing.

### Time and accounting

The four completed Freerouting engine calls total **189.329 seconds**
(about 3.16 minutes); these are engine wall times, not total engineering
effort. The corrected-width control/run/native analysis measured
114.782 seconds of subprocess work and fit its five-minute correction
window. Public-product research took approximately 12 minutes elapsed.
Account-side interaction, screenshot review, preparation and validation
dominated the overall workflow. No precise task-local token or tool-call
accounting was collected; historic agent lifetime counters would be
misleading. The approximately 90-minute active budget was an upper target,
not a reason to keep testing after preservation/no-progress gates failed.

**Final state:** accepted board and manifest plus all four experiment-source
copies retain their initial hashes. No schematic, placement, rules, outline,
stackup or active routing changed. Manual/LLM routing remains paused.

## External sources reviewed

- Quilter [pre-placed components](https://docs.quilter.ai/design-parameters/pre-placed-components),
  [pre-routed traces](https://docs.quilter.ai/design-parameters/pre-routed-traces),
  [preserved pours](https://docs.quilter.ai/design-parameters/preserved-pours),
  [stackups](https://docs.quilter.ai/design-parameters/stackups).
- Quilter [upload workflow](https://docs.quilter.ai/using-quilter/upload-your-design-files),
  [Circuit Comprehension](https://docs.quilter.ai/using-quilter/define-physics-comprehensions),
  [differential pairs](https://docs.quilter.ai/physics-constraints/differential-pairs),
  [timing-sensitive signals](https://docs.quilter.ai/physics-constraints/timing-sensitive-signals),
  [crystals](https://docs.quilter.ai/physics-constraints/crystal-oscillators).
- Quilter [pricing](https://www.quilter.ai/pricing),
  [free tier](https://www.quilter.ai/free-ai-pcb-design),
  [terms](https://www.quilter.ai/terms),
  [job submission](https://docs.quilter.ai/using-quilter/submit-your-layout-job).
- tscircuit [KiCad import](https://docs.tscircuit.com/guides/importing-modules-and-chips/importing-from-kicad),
  [routing phases](https://docs.tscircuit.com/elements/autoroutingphase),
  [KiCad export](https://docs.tscircuit.com/command-line/tsci-export).
- tscircuit source: [import pipeline](https://github.com/tscircuit/kicad-to-circuit-json/blob/3ff650e/lib/KicadToCircuitJsonConverter.ts),
  [zone import](https://github.com/tscircuit/kicad-to-circuit-json/blob/3ff650e/lib/stages/pcb/CollectZonesStage.ts),
  [board initialization](https://github.com/tscircuit/circuit-json-to-kicad/blob/9e66a9b/lib/pcb/stages/InitializePcbStage.ts),
  [pour export](https://github.com/tscircuit/circuit-json-to-kicad/blob/9e66a9b/lib/pcb/stages/AddCopperPoursStage.ts).
