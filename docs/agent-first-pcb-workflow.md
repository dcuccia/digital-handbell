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

Most of this project's routing cost came from decisions made before
routing. A dense IC was placed over a via keep-out. A decoupling capacitor
drifted away from its pin. The stackup was too thin for the pin field.
Autorouters (DeepPCB, Quilter) do 80-90% of a board in minutes, but they
cannot fix a blocked placement, and they plateau on the last 10-15 links.
Freeze placement rules and keep-outs first, choose a stackup that suits the
pin density, run one productive autorouter pass, then finish with
deterministic, checked tools. Spend money on placement fixes, not on
repeated re-routes.

## Phase 1: Requirements and constraints (before schematic capture is "done")

- Write down the hard interfaces: board outline, connectors, buttons, USB
  access, mounting, battery contacts, and height zones. Each one becomes a
  keep-out or a fixed position.
- Write down current per supply net, and derive copper width from it. Put
  widths in net classes. Distinguish **power-path** copper (load current)
  from **signal-level taps** on a supply net, such as divider or pull-up
  resistors. Taps can be minimum width; blanket rules waste routing space.
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

## Phase 4: Stackup choice

- Choose layers by pin density and the number of critical return paths, not
  by habit. Here, four layers stalled. The JLC 3313E six-layer stackup
  (signal/GND/signal/signal/GND/signal: four routing layers, each next to a
  ground plane) cut the problem from 25+ opens to 12 in one run.
- Use a real fab stackup and its impedance calculator for controlled pairs
  (USB 90 ohm). Price both options live; at prototype quantity six layers
  cost about $35-49 and eight about $90 here.
- Avoid HDI (blind/buried vias, via-in-pad) unless budgeted. Through-vias
  with standard 0.3 mm drill are enough when placement is sane.

## Phase 5: Autorouter run (DeepPCB or similar)

- Freeze a baseline with pre-reviewed critical copper. Upload a **copy**
  with router-friendly rules: wider clearances than the real minimum
  (0.18 versus 0.15 mm) and a larger edge clearance. Remove board-wide
  plane "no track" rule areas, which make fanout think every pin is blocked.
- Assume the router ignores "protected" copper and undercuts clearances.
  Treat its output as a proposal.
- Watch progress and stop on plateau. Most gain arrives in the first 3-5
  minutes. Cap spend per run (`--allow-paid --max-usd`). If the API reports
  no stats, the cap is the only stop.
- **One productive run per placement.** Fresh re-routes of the same
  placement landed at 11-14 opens but stranded different links. Their
  copper cannot be transplanted, because each net's route depends on the
  others.

## Phase 6: Deterministic post-processing (no judgment, all checked)

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
and no DRC type or count grows.

## Phase 7: Finishing the long tail

- Use per-net, path-aware rip-up and reroute (`tools/reroute_with_ripup.py`).
  Only router- or agent-made copper may be ripped up, never frozen copper.
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
- Save the report, with an explicit held status, before asserting, and
  exit nonzero on a held control, so every failure leaves evidence.
- Confirm that an API exists in the installed `pcbnew.py` before relying
  on it. Re-verify an executor's runtime after a pause: handles expire.

## Roles, budgets and stopping

- The owner approves spend, stackup, placement policy and fabrication.
  Agents run bounded items: about 15-45 minutes, an initial attempt plus at
  most two corrections, an explicit stop condition, and an honest report.
- Pin routing executors and verify their runtime (`routing-agent-policy.md`).
  The lead verifies the session's `subagent.configured` record when an
  executor cannot see it.
- Keep the authoritative board immutable. Do all experiments on private
  copies, with hashes recorded.
- If two bounded attempts show no measurable progress, escalate: change the
  placement, the stackup, or bring in a person. Do not escalate by running
  the same tool again.
