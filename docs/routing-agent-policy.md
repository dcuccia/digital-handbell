# Astra engineering lead / Sol routing executor

Owner-authorized September 21, 2026. This resumes the September 16 pause
conditionally on verified Sol dispatch; it does not change any PCB rules,
accepted geometry, supplier gates or prior failed-attempt history.

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

## Baseline and engineering reservations

Active package: `hardware/handbell/iterations/printed-bell-clock-draft`.
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

**Next engineering gate:** Astra must define a local IMU/pull-up supply,
SCL/SDA and return corridor together before releasing more SCL execution.
Read-only native geometry may evaluate options, but no supply reroute,
placement change or B-side crossing is authorized by this checkpoint.
Other control nets remain unreleased where they compete with reserved
critical corridors. The accepted state remains 51 opens.

## Work and acceptance

Sol executes established constraints, not redesigns. Preserve placement,
existing good routing, footprints, stackup, net classes, design/zone/pair rules
and fixed interfaces. Native rule evaluation is necessary but insufficient.
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
isolation and contact-metal reservations. Use the existing refill, native DRC
and independent filled checks, requiring named new connections. No whole SES
replacement; no silence of clearance findings. Astra additionally reviews
return-current routes, plane cuts, adjacency, loop area, decoupling topology,
and vias/stubs. A DRC pass alone never promotes a candidate.

Full personal runtime logs remain local; publish only compact model/effort,
outcome and source-bound engineering evidence, not profiles or credentials.
