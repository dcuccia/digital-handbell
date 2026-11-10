# Agent-first PCB workflow: lessons and best practices

This is the short guide. Evidence and history are in the linked documents.
It is for an owner who is a software developer, not a layout engineer:
tools and agents do the routing, and the owner approves decisions and
spending.

Evidence:

- [routing tooling lessons](routing-tooling.md)
- [six-layer Gate A results](multilayer-gate-a-2026-11.md)
- [multilayer plan](multilayer-routing-plan-2026-11.md)
- [Quilter playbook](quilter-playbook.md)
- [agent routing policy](routing-agent-policy.md)

## The one-paragraph version

We have not measured how much of the total cost was caused by placement
versus tooling. The record does show repeated rework around a dense IC
over a via keep-out, misplaced decouplers, inaccessible returns and
constrained interconnects. Start with
the system's power, return and data paths; design critical functional cells
and their interfaces together; then select placement and a real stackup.
Use a bounded autorouter run for the remaining interconnect and checked
local replacements for a finite tail. The six-layer candidate eventually
reached zero opens, but neither a service's routing percentage nor native
connectivity proves electrical or manufacturing readiness.

## Phase 0: System architecture before coordinates

This is the recommended next-revision method, not a claim that we exercised
it end-to-end or measured its savings. It applies to a small respin as well
as an MCU replacement. Keep the zero-open milestone as the comparison
baseline; do not start a redesign just to demonstrate the method.

Draw the source-to-load **power tree and its return paths**, and the data/
control connections between subsystems, before optimizing component poses.
For each connection, record voltage, current/load cases or edge-rate needs,
local decoupling, return/reference, candidate layer, width/impedance intent,
transition space and service/recovery duty. Unknown budgets stay unknown;
a shared net name is not a shared current or noise requirement.

| Functional cell | Design locally first | Reserve between cells |
|---|---|---|
| USB/source selection, charger and cell protection | Actual contact metal, source-switch paths, sense pickoffs, raw CELL_NEG versus protected GND, insulation | Charging/load-current paths and returns; no ground bypass of the protector |
| Audio boost and amplifier | Switching hot loop, input/output capacitors, feedback/private returns, amplifier decoupling and output filter | Supply/return capacity and the complete two-wire BTL speaker path, not a speaker-to-GND shortcut |
| MCU/core, flash and crystal | Every supply pin and capacitor return, boot/test straps, crystal/load network, QSPI escape and debug access | Usable through-via sites, USB pair with reference continuity, I2S/control corridors |
| IMU and external controls | Supply/ground, mode straps, pullups, interrupt and connector duties | I2C/interrupt/button interfaces and their returns; placement/axis constraints |

These are **functional placement cells**, not isolated ground islands.
Use a coherent protected-ground reference where appropriate; do not split
digital/audio ground by label. Deliberate protection-side isolation and
private sense paths are separate, source-backed circuit requirements.

Define each cell's interface contract: actual terminal identities, required
branches/joins, permitted moves, layer transitions, current/return duties,
mechanical envelope and acceptance evidence. Review the small critical
circuits before routing the rest. Do not retain whole shared nets or every
old escape trace simply to keep a cell "protected".

The November review found four contract outputs missing. They are method
requirements, not evidence about the current board:

1. A pin-level entry-copper contract: the bypass capacitor, the maximum
   loop, and the minimum entry width and length to the trunk.
2. Widths in netclasses **and** enforceable DRC rules. Netclass patterns
   cover every net, including GND and /CELL_NEG, and each finding count is
   recorded beside the rules in force when it was produced.
3. Numeric evidence for controlled pairs: coupled fraction, intra-pair
   skew, layer list, and reference transitions with their stitching vias.
4. Via protection (IPC-4761 type, filling, capping) as a cell-contract
   output, with per-via properties gated in the PCB and not only in a
   fabrication note.

Sketch several meaningful floorplans cheaply, not hundreds of tiny poses.
Orient cell interfaces toward their destinations and reserve the wide
power/return routes, coupled pairs and transition sites before ordinary
controls occupy them. Check the interfaces together: locally valid cells
can still be impossible to connect at their boundaries. Move a flexible
connector or adapt printed supports when justified rather than protecting
an arbitrary old coordinate at the expense of the circuit.

**Placement release gate:** show actual pin-to-capacitor supply *and return*
paths, all-layer legal transition sites, critical escape corridors, real
contact/body/access constraints and a feasible inter-cell routing sketch.
Body fit, schematic connectivity and an inner-layer empty corridor alone
are insufficient. Bind checks to the candidate geometry; repeat affected
checks when a cell, connector, rail route or stackup changes.

## Phase 1: Requirements and constraints (before schematic capture is "done")

- Classify interfaces as genuinely fixed, bounded-flexible or preferred:
  outline, connectors, buttons, USB access, mounting, contacts and height
  zones. Encode real metal/access exclusions, not every old coordinate.
  Connector reachability and a workable harness can permit relocation.
- Write down current per supply net, and derive copper width from it. Put
  widths in net classes. Distinguish **power-path** copper (load current)
  from **signal-level taps** on a supply net, such as divider or pull-up
  resistors. Qualify tap width against its actual duty and process rules;
  blanket full-load widths waste routing space, while blanket minimum-width
  supply routing is unsafe.
- Decide which circuits are critical and need hand-reviewed copper:
  switching-regulator loops, crystal, USB pair (impedance), battery and
  protection paths, private returns.

## Phase 2: Schematic with layout intent

- For every decoupling, input/output, crystal-load and boost capacitor,
  record **which pin it serves** and a maximum distance. The rule is the
  pin, not "near the IC". Example: C1 (10 µF on VHI) is the input capacitor
  of LDO U2; the reference supply-pad center distance is 1.45 mm.
  Its approximately 3.8 mm footprint-center distance is a different metric.
- Keep reference-design intent. When copying a vendor or open-hardware
  reference, read its layout as well as its schematic. Its placement shows
  which capacitor belongs to which pin.
- Plan test points and debug access (SWD, reset, boot) as parts with
  placement flexibility. They are often the easiest links to sacrifice
  wrongly. Keep recovery access.

## Phase 3: Mechanical keep-out map, then placement

- Render every keep-out (via-free, B.Cu-free, height-limited, contact
  bands) over the board before placing dense ICs. Never put a fine-pitch or
  via-hungry IC over a via keep-out. On this board that one mistake stalled
  every router at about 25 opens.
- Place by functional group: power entry, then regulators with their
  capacitors, then the MCU with decoupling and crystal, then interfaces.
  Leave escape space around the MCU on every side that has pins.
- **Check placement rules automatically** before routing: maximum
  pin-to-capacitor distances, crystal distances and keep-out overlaps.
  Agents moving parts to legalize courtyards will otherwise silently drag a
  capacitor away from its pin, and the router will then connect it with a
  long, thin trace. That is electrically connected but functionally wrong.
- For a repair, place the **connected cell**, not independently legal
  component centers. Check its actual pin geometry, noncrossing local supply
  and return paths, and via access before constructing a full-board trial.
  Moving a capacitor closer can still put its connection across another pin.
- Couple placement permission to a precise copper-replacement contract.
  Allowing a supporting resistor to move is ineffective if its old fanout
  remains immovable. Enumerate the released primitives, branch joins and
  terminal duties; do not release an entire shared supply or signal net.
  Classify copper against the exact protected baseline: "already present"
  does not mean frozen. A mistaken classification can block an authorized
  placement change without any real electrical reason.
  Record which cell translations and rotations were actually examined:
  a 0.05 mm IC shift does not exercise a 5 mm relocation allowance.
- Give every decoupling capacitor room for a legal ground via beside its
  ground pad. Map contact guards and protection-side copper before placing
  a regulator near them. Protection-side copper here is B.Cu `/CELL_NEG`,
  where a ground via would bypass the cell protection. A BT2 contact
  guard's bounding box starts 0.19 mm below U2's centre, so every pose a
  later local repair screened put a ground via in the guard, and four of
  the five also put one on `/CELL_NEG`.

## Phase 4: Stackup choice

- Choose layers by usable escape capacity and reference paths, not just
  total layer count. The six-layer 6C board uses
  signal/GND/signal/signal/GND/signal. Its frozen 86-open input reached
  11 opens through routing/post-processing. Placement, retained copper
  and tooling also changed versus earlier four-layer trials: this is not
  a controlled measurement of the benefit of adding two layers alone.
- Use a real fab stackup and its impedance calculator for controlled pairs
  (USB 90 ohm). The November 6 example quotes for five boards were about
  $35-49 for six layers and $90 for eight, with differing defaults; these
  are not current full PCB+assembly/process quotes.
- Separate **via-in-pad process** from **HDI**. This milestone uses
  filled/planarized/capped through-vias, including the owner-approved C7
  and GAIN0 exceptions; that is not permission for laser microvias or
  blind/buried vias. Standard through-vias still need all-layer clearance,
  land/annulus/hole checks and a qualified mask/stencil/process disposition.
- Screen real 4/6/8-layer constructions with the same circuit obligations,
  process assumptions and mechanical envelope before buying routing runs.
  Count usable signal/reference layers and legal transitions, not nominal
  layers. Reject a USB profile below the permitted width floor; do not
  invent impedance compatibility. Date quotes and include POFV/assembly
  charges, preparation and review effort, not bare-board price alone.

## Phase 5: Autorouter run (DeepPCB or similar)

- Freeze a baseline with pre-reviewed critical copper. Upload a **copy**
  with router-friendly rules: wider clearances than the real minimum
  (0.18 versus 0.15 mm) and a larger edge clearance. Remove board-wide
  plane "no track" rule areas, which make fanout think every pin is blocked.
- Do not assume a protection flag or imported rule is enforced. Exercise
  the relevant behavior and compare returned native data under intended
  rules; treat output as a proposal, not proof that all routers ignore rules.
- Watch progress and stop on plateau. Most gain arrives in the first 3-5
  minutes. Cap spend per run (`--allow-paid --max-usd`). If the API reports
  no stats, the cap is the only stop.
- **Default to one productive run per qualified placement.** Fresh re-routes
  of the same placement landed at 11-14 opens but stranded different links. Their
  copper cannot be transplanted, because each net's route depends on the
  others. Another run needs a specific changed hypothesis, a bounded
  release/restoration contract and an expected discriminating result.

## Phase 6: Checked post-processing under a reviewed contract

The standard pipeline is `tools/postprocess_router_result.ps1`:

1. Merge router copper onto the frozen baseline, only for open nets.
2. Stitch ground islands.
3. DRC.
4. Remove new copper that causes new conflicts or enters contact guards.
5. Run the grid A* gap router for short tails.
6. Stitch again.
7. Run the standard check: copper preservation, isolated nets, private
   returns, plane layers and DRC growth.

Every stage writes its own folder. Accept a board only if opens decrease
and no unapproved new findings appear. Category counts alone can hide a
new defect replacing an old one; compare objects/geometry and connected
groups, and investigate changed witnesses. A routing acceptance is not a
release acceptance.

## Phase 7: Finishing the long tail

- Route between **connected copper groups**, not only the two objects a
  DRC airwire happens to name. Inspect alternate attachment points on each
  group before moving a component or declaring its escape blocked.
  The default pair mode of `route_gaps.py` and the rip-up helper select
  individual DRC witnesses; both represent a zone endpoint by a small disk at the
  reported position, not its actual disconnected filled island. Their
  failures therefore do not exhaust group-to-group routes. However,
  `route_gaps.py --nearest-own-copper` already expands the goal to outside
  same-net copper on each layer; it was tried for GAIN0. Reuse that evidence,
  not an unchanged retry or a duplicate implementation. Resolve real
  island membership before using a zone witness as a route target.
- Bind a newly constructed escape to the router's **source** explicitly.
  `--nearest-own-copper` expands goals, not the starting group. For POWER,
  a literal F-track witness could not reach a via even after adding In3;
  starting at the new EN via found the inner-layer connection. Pass all
  intended signal layers explicitly: the tool defaults to F/In2/B, not
  six-layer 6C's F/In2/In3/B. Keep synthetic routing requests separate
  from native DRC evidence and verify the resulting connected-group merge.
- Use per-net, path-aware rip-up and reroute (`tools/reroute_with_ripup.py`).
  Its automatic rip-up scope is router- or agent-made copper, not frozen
  copper. A separately reviewed local replacement contract is required to
  change frozen copper; owner permission is not a blanket whole-net release.
  Accept a step only on a strict open decrease with no new DRC findings.
  This took the board from 11 to 8 opens at no cost.
- Do not rip up along straight corridors. That removed about 120 items and
  made the board worse.
- Supply nets must close at their approved width, or stay open and be
  reported. A thin link that makes DRC happy can still be an electrical
  defect. Review every narrow segment added to a supply net.
- Links that remain usually need a small, local placement change: a test
  point relocated, a capacitor moved, a part rotated. Make that an explicit,
  reviewed decision, then rebind the mechanical model.
- Before screening local moves, list the frozen copper, guards and
  protection-side copper within the move allowance. If they enclose the
  cell, local screens are unlikely to help. Release copper under a
  replacement contract, or hand the work to a person. Here four bounded
  items found no qualified pose that put C1 and C4 beside U2. Run Phase 3's
  capacitor-distance check before any copper around the cell is frozen,
  while moving a capacitor is still cheap.
- When a reviewed change releases a few frozen primitives, preserve every
  external branch and compare the untouched complement explicitly.
  `check_routing_result.py --allow-changed-nets` suppresses lost-copper
  findings for whole nets; it is not proof that only the approved local
  copper changed or that its replacement duties were restored.
- Keep a promising result with a finite defect rather than restarting the
  search. Here a smaller rear TP14 land joined the complete LRCLK group but
  missed one control-track clearance by 0.015 mm. A separately reviewed
  0.05 mm AMP_MUTE detour preserved its width/branches and closed that open
  without paid routing. The failed pad-only trials remain evidence, not
  accepted boards. Bare-land access and a matching local footprint library
  still matter; shrinking a pad does not waive either.
- Prefer a paired blocker replacement when a near miss identifies the
  exact cause. USBBOOT needed a local VBUS detour plus the C14 return
  stitch, not just a diode move. TESTEN needed the +3V3 via relocation
  **and** an In3 SDA jog; the via-only attempt shorted SDA. All-layer
  through-via access belongs in the cell design, not an afterthought.
  The broad IC1-window paid reroute instead increased opens from 1 to 6.
  These outcomes support targeted local contracts, not a claim that every
  near miss is cheaply repairable.

## Phase 8: Electrical and release review

Routing completion is not acceptance. Before fabrication, check:

- decoupling adjacency and loop areas;
- supply widths against current;
- the USB pair as a coupled, impedance-controlled route;
- planes and pours, and dangling stubs;
- schematic parity;
- the mechanical re-bind;
- fab outputs and a fresh quote.

Fabrication and power-on need separate owner approval.
Use the [zero-open milestone review](pcb-review-2026-11.md) for the current
board's specific outstanding evidence; this generic checklist is not its
completed disposition.

## Next revision: keep the evidence, change the experiment

For an MCU swap, first compare package escape/pin assignment, required
power/clock/flash parts, I2S implementation, USB and boot/debug support,
firmware/driver work, idle/peak power, sourcing and assembly process.
An integrated feature can remove a critical cell but introduce different
power, RF or software constraints. Freeze the required behavior, not the
RP2040 floorplan; require a new schematic/net/footprint equivalence review
where interfaces change. No replacement MCU is selected by this guide.

For either a small respin or a larger revision, compare a small number of
source-bound alternatives against the preserved milestone. Use unresolved
root connections, critical-loop/return quality, remaining review effort,
process dependence and total measured cost as outcomes, not only routed
percentage. Record agent preparation, native checks and human review effort
separately from router runtime/spend; do not infer compute cost from elapsed
wall time. The owner-reported earlier token expense is context, not an
audited lifetime project total.

DeepPCB v5 placement/Cooper capabilities are a **future experiment** here,
not exercised independent validation. A read-only second opinion could
help find missed risks, but must bind each finding to a source object and
be independently dispositioned. Check capabilities, upload scope and price
before a separately authorized run; remaining TESTEN minutes are not a
blanket budget for a new review or redesign.

## Screens and checkers

A defective helper costs a whole bounded attempt. Before a native run:

- Recompute the healthy positive case independently and statically, with
  the screen's real geometry model. A footprint without a courtyard
  outline falls back to its unexpanded bounding box in
  `tools/move_cluster.py`. Include via-to-pad gaps on every net and the
  full extent of neighbouring pads, not just their centres. This caught a
  template whose positive case could never pass, before any native run.
- Set witness tolerances above coordinate quantization. KiCad stores
  integer nanometres, and the installed `pcbnew.FromMM` truncates
  (`int(mm * 1e6)`), so a placed pad can land 1 nm from its computed
  target. Round explicitly when converting. A tolerance of exactly
  0.000001 mm held a screen after both of its controls had passed; use
  about 0.001 mm.
- Fail closed on empty geometry. Shapely returns NaN for a distance to an
  empty shape, and `NaN < limit` is false, so an empty obstacle passes
  silently. Count empty shapes in the report and hold on a nonzero count.
- Review a rejection as carefully as a pass. Confirm that each hit
  involves a foreign net and copper that really stays fixed before you
  call a pose impossible.
- Resolve each copper pair's actual net classes and local/custom overrides.
  The global minimum is only a floor: GND-to-VBUS here requires 0.20 mm
  even though both the global minimum and GND's Default class are 0.15 mm.
  An ordinary-via screen must also exclude component lands and check all
  holes, including same-net ones; copper-net equality is not process approval.
- Distinguish project-rule clearance from an additional screening margin.
  A rigid footprint move cannot enlarge intrinsic pad spacing. The U5
  POWER closure passed native rules but failed an extra 0.025 mm margin
  at two unchanged pad pairs and two new copper pairs. Keep that raw HOLD;
  any lead disposition must name the exact pairs, measured gaps and release
  limits rather than silently lower a checker threshold or call it a pass.
- Separate probe/component access from copper routing. A package-body
  outline can make a test land inaccessible without prohibiting an insulated
  trace beneath the body. Assess actual pads, underside metal, mask,
  assembly requirements and all-layer/contact constraints; do not turn a
  body bounding box into an invented track or via keep-out.
- Save the report, with an explicit held status, before asserting, and
  exit nonzero on a held control, so every failure leaves evidence.
- Confirm that an API exists in the installed `pcbnew.py` before relying
  on it. Re-verify an executor's runtime after a pause: handles expire.

## Roles, budgets and stopping

- The owner approves spend, stackup, placement policy and fabrication.
  Agents normally run 10-15 minute coherent items, including review, with
  an initial attempt plus at most two corrections, an explicit stop
  condition and an honest report. Longer allowances must be explicit.
- Keep the system-level plan with the lead and delegate a complete cell or
  interface obligation, not isolated field edits. Batch bookkeeping and
  reuse source-bound evidence when its invariants hold. Count preparation/
  checker repair against the budget; many small reports are not progress
  if they do not qualify a route, resolve a risk or enable the next gate.
- Pin routing executors and verify their runtime (`routing-agent-policy.md`).
  The lead verifies the session's `subagent.configured` record when an
  executor cannot see it.
- Keep the authoritative board immutable. Do all experiments on private
  copies, with hashes recorded.
- If two bounded attempts show no measurable progress, escalate: change the
  placement, the stackup, or bring in a person. Do not escalate by running
  the same tool again.
