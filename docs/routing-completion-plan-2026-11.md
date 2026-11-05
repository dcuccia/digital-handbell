# Routing completion plan - November 2026

Goal: a fabricable **engineering-prototype** PCB in about two to three weeks,
**driven by routing tools, not by the owner routing by hand**. The owner is
a software developer, not a layout engineer: the owner's role is decisions,
account setup and spending approval. Agents prepare inputs, make small
placement edits and run checks. This plan does not itself authorize purchases,
accounts, uploads or ordering; each needs the owner's explicit approval.

## What we have learned

| Evidence | Lesson |
|---|---|
| Authoritative four-layer board `adc262b3` has **37 opens** after roughly $1k of LLM-driven routing | Agents made real progress, but most cost went to qualifying each small hand-made copper move. Agents should not resume move-by-move routing. |
| Quilter **already tried to finish this exact board** (October 1-2, v1.1/v1.2, reported 89-91% routed) | Its output did not keep the protected In1 GND pour as an exact structure, none of the 24 existing In2 segments matched, and the better candidate shorted different nets. It was rejected for use. |
| Quilter four-, six- and eight-layer placement-first jobs (October) | No candidate finished. Best eight-layer standard result: 34 opens, all six QSPI nets open, 64-76 tracks below our 0.1778 mm floor, different placement. Beta results trade opens for shorts. |
| Quilter support (October 16) | Product help only, no layout review. Advice: more room around IC1, iterate placement, run small parallel experiments. No reply expected. |
| Hard routes repeatedly stall around **IC1** (RP2040 core supply, decouplers, USB) and some distributed power returns | Part of the long tail is placement congestion. Any router needs a little more room there, not just more attempts. |
| Freerouting closed 0/7 trial opens; tscircuit failed preservation | Free classic autorouters are not the answer for the hard part. |

The four-layer board is further along where it matters: QSPI flash, the
crystal clock, IMU, battery contacts, boost/protection cells and the five
process vias are already routed and reviewed. **Recommendation: finish the
four-layer board with a tool that routes only the missing connections and
keeps existing copper.** Keep all Quilter outputs as reference.

## The 37 remaining opens

From the post-IMU triage (38 opens) minus the accepted C13 ground stitch;
Step 0 regenerates the exact list.

- **About 18 short low-speed signals:** I2S (IC1-U4 plus TP12-TP14),
  AMP_MUTE (TP15), ~RESET, SWD, INT, D13, GAIN, BUTTON, POWER (enable
  control). Any competent router should handle these.
- **About 6 MCU core/USB opens plus IC1 grounds:** VCORE, D+/D-, USB_D+/D-.
  Most likely to need small decoupler moves.
- **About 13 power/audio/ground-return opens:** VBUS, VHI, VBAT, VAMP, VO+,
  FB2 and ground islands at the USB shell, charger/battery, flash, gain and
  power switch. These need sensible widths and return paths.

Optional simplification (owner decision): removing debug test points
TP12-TP15 removes about four opens. That is a design change (schematic, BOM
and placement files change together). Keep SWD, RESET and BOOT access.

## Who does what

| Role | Responsibility |
|---|---|
| **Routing tool** (DeepPCB first) | Routes the missing connections on a copy of the board. |
| **Agent** | Prepares a clean input; checks every tool result; makes small, approved part moves (placement only, no hand routing); prepares fabrication files. |
| **Owner** | Approves decisions and spending; creates the DeepPCB account and API key; clicks "Route" in the KiCad plugin if the agent cannot drive the web app. |
| **Freelance layout engineer** (fallback only) | Finishes whatever the tools cannot, for a fixed price. |

## Plan

**Status, November 5:** approved by the owner; Step 0 complete; boards
uploaded to DeepPCB with existing wiring protected; waiting for the owner to
buy credits. No routing job, purchase or freelancer contact has happened.

### Progress log

**November 5 owner decisions:** four-layer baseline confirmed (move to six or
eight layers only if it clearly gives line-of-sight to completion); all steps
approved, fail fast and preserve personal budget; DeepPCB account exists
(Google sign-in, owner's Chrome); parts may move freely except keep USB and
important buttons/switches accessible, board may grow 10-20% if needed; test
points may go anywhere; freelancer step gated until the owner is prompted.
See the [freelancer explainer](layout-freelancer-explainer-2026-11.md).

**November 5 Step 0 completed (no spending):**

- `tools/prepare_deeppcb_input.py` copies the verified authoritative files to
  a private work folder and builds the routing input: eight reviewed
  battery-contact guards (no tracks, vias or pours on B.Cu), the twelve
  private-return guards now also block new tracks and vias, In1 marked as a
  power plane with a whole-board track keep-out (vias still allowed), 0.3 mm
  edge clearance, Default class 0.2/0.2 mm with 0.6/0.3 mm vias, and a 0.3 mm
  `power` class for VBUS, VBAT, VHI and VAMP. A 100-footprint free-trial probe
  copy omits TP12-TP15.
- KiCad 10.0.6 DRC with refill: the unchanged baseline has **38 opens**
  (37 was recorded from saved fills) and **no errors**, only warnings. The
  routing input has the same 38 opens plus 74 inherited errors (existing
  protected copper inside the new guard areas, two edge findings). The probe
  has 34 opens.
- `tools/check_routing_result.py` is the standard check. Controls: unchanged
  copy fails (no opens closed); a removed track, new `/CELL_NEG` copper and new
  copper on private pad R24.2 are each caught.
- Schematic parity (46 naming warnings) is deferred to the pre-fab gate: the
  router receives only the PCB and project, whose nets are authoritative.
  USB on the RP2040 is 12 Mbit/s full speed, so a short pair needs no tight
  impedance control; no USB net class was added.

**DeepPCB facts verified November 5:** $30 per routing hour pay-as-you-go
($28/h and $26.7/h in larger packs). Free trial: 30 minutes, one board, up to
4 layers, 150 airwires and 100 components. Official API spec offers
`CurrentProtectedWiring` ("protect existing wiring"); the KiCad plugin
defaults to `CurrentUnprotectedWiring`, so we use `tools/deeppcb_route.py`,
which always requests protection and refuses paid runs without an explicit
cost cap.

**Blocked on owner (one action):** Playwright is not signed in to DeepPCB,
and creating an API key needs owner approval. Owner: open
`https://app.deeppcb.ai/integration`, create a key, and save only the key
text in `C:\Users\david.cuccia\.deeppcb\api_key.txt`.

**November 5, 15:40 update:** key provided. Two boards uploaded with
`CurrentProtectedWiring`; no job started, nothing spent:

| Upload | DeepPCB board id | Components | Pins | Unrouted (DeepPCB) | Total airwires | Free? |
|---|---|---|---|---|---|---|
| Trial probe (no TP12-TP15) | `b966cf25-b402-44f7-9757-c9871830181f` | 100 | 306 | 27 | 220 | No |
| Full routing input | `a4535c0f-c4cb-4271-bc9a-1cac47c64acf` | 104 | 310 | 31 | 224 | No |

The free trial is unusable: its 150-airwire limit counts **all** connections,
routed or not. Both boards need credits at 0.5 per minute ($30/hour). Account
balance is $0, and buying credits is an owner payment action.

**Next (owner):** buy the 1-hour ($30) pack at
`https://app.deeppcb.ai/time-balance`. **Then the agent:** start the existing
full-input board for 30 minutes (`deeppcb_route.py start --state full-run.json
--minutes 30 --allow-paid --max-usd 15`), wait, download, DRC and the standard
check. Keep the result only if existing copper is preserved and opens fall;
the remaining 30 minutes fund one placement-assist round. If existing copper
is not preserved, stop DeepPCB.

Original runbook once credits exist:

1. `deeppcb_route.py create` on the free-trial probe, then `status` to see
   whether it is free (`requiresCredits`). If it is not free, stop and ask
   before any paid run.
2. Start up to 30 minutes, wait, download, run DRC and the standard check
   against the probe baseline.
3. If existing copper is not preserved, stop DeepPCB (fail fast). If it is,
   proceed to the full input as a capped paid run (about $15 for 30 minutes)
   and the placement-assist loop.

### Step 0 - prepare a clean input (agent, about 1-2 hours)

1. Regenerate the exact open list for `adc262b3` on a copy.
2. Review the **46 schematic-parity findings** (22 explicit-unconnected-pad
   names, 24 auto-named nets) so the tool routes against an unambiguous
   netlist. Record frozen PCB/schematic/project hashes.
3. Set the board's design rules to our real limits, so the tool cannot use
   weaker defaults: 0.1778 mm minimum track, 0.20 mm clearance (the project
   file currently says 0.1778), one stated size for new vias, wider power
   net classes, and the USB 90-ohm pair.
4. Mark existing copper and the protected In1 GND plane as locked, and add
   keep-outs for battery-contact metal. List the existing via exceptions
   (four U4 vias about 0.604/0.35 mm, C24's 0.60/0.30 mm, five filled/capped
   process vias) so nothing "fixes" them.
5. Write one **standard check**, run after every tool result: KiCad 10.0.6
   DRC with zone refill and schematic parity on a copy, compared with the
   frozen baseline. Pass means: opens decreased; no new shorts, clearance or
   width errors; no existing connection lost; In1 GND plane, private returns
   (R24.2-C28.2, R26.2-R27.2) and CELL_NEG isolation intact.

### Step 1 - DeepPCB on the unchanged placement (about 1 day; cap e.g. $50)

DeepPCB is a pay-as-you-go cloud router with an open-source KiCad plugin.
Its free trial appears limited to 100 components (we have 104), so expect a
small credit purchase. Vendor material says it routes only selected nets and
keeps existing copper; **this is unverified**, and it is exactly what Quilter
failed on this board.

1. Owner creates the account and approves the upload and credit cap.
2. First run a short preservation test: does the returned board keep every
   existing track, via and the In1 plane? If not, stop this tool.
3. Then route all missing connections. Apply the standard check.

Outcome: either finished, or a smaller set of residual opens.

### Step 2 - placement-assist loop (at most 3 rounds; total cap e.g. $100)

If opens remain, the agent makes **small placement-only changes** that give
the router room, then the tool routes again:

- Only parts on the approved list may move (proposed: C6, C7, C8, C13, C17,
  C18, R1, R9, R10, plus any part the residual list clearly implicates and
  the owner approves). Each stays inside a region derived from the
  mechanical model (speaker/magnet height, battery contacts, USB).
- Copper attached only to moved parts is removed so the tool can reroute it;
  everything else stays locked.
- A round counts only if its result passes the standard check **and** open
  count drops. Two rounds without progress end the loop.

Placement edits are reliable for agents. Agents do not hand-route; the only
exception is a final handful (five or fewer) of short, obvious connections,
each accepted only by the standard check.

### Step 3 - fallback if tools stall

Choose one, owner's decision:

- **Freelancer (recommended fallback):** agent prepares a reproducible packet
  (frozen project and hashes, residual list, rules, locked copper, movable
  envelopes, mechanical keep-outs, check commands). Ask two or three KiCad
  layout freelancers for fixed-price quotes to finish the residual only,
  with completion defined as passing the standard check. A residual job of
  this size is typically hours to a few days of expert effort; confirm with
  real quotes.
- **One Quilter run** on the improved placement (free for personal use), but
  only after a cheap preservation test, given its earlier loss of In1/In2.

Not recommended: Altium (its automatic Situs router is weaker, ActiveRoute
needs a human operator, and the round trip conflicts with the open-source
goal), new layer sweeps, or restarting broad agent routing.

### Step 4 - pre-fabrication gate and quote package (agent, about 2-3 days)

1. Zero unconnected items; standard check passes with no errors except a
   short, written list of accepted inherited warnings.
2. Schematic parity clean or matching the Step 0 dispositions.
3. Electrical review list: CELL_NEG isolated from protected GND; private
   returns not bypassed; IC1 decouplers close with short returns; USB pair
   routed together; supply/ground widths reasonable for expected current.
   For an owner without EE background, the agent produces a plain-language
   report, and a paid one-hour review by an EE is worth considering.
4. Five protected process vias unchanged; the chosen fabricator confirms
   resin fill, planarization, capping and price in the quote.
5. Mechanical re-bind into the FreeCAD assembly confirms moved parts still
   fit (a re-bind is already required: `mechanical_rebind_required=true`).
6. Gerbers, drill, BOM and placement (CPL) files for JLCPCB and PCBWay per
   [the quotation plan](pcba-quotation-plan.md), including both rear battery
   contacts and X6.

Ordering requires the owner's explicit approval. A prototype is for bench
bring-up, not child use.

## Stop rules and budget

- Tool spend capped per step (e.g. $50, then $100 total) unless the owner
  raises it.
- Every tool result is accepted only through the standard check.
- If DeepPCB fails preservation, or the loop makes no progress for two
  rounds, go straight to Step 3; do not try additional tools by default.
- Any rule relaxation, protected-copper change or unapproved move goes to
  the owner first.

## Owner decisions needed to start

1. Confirm the four-layer board as the starting point.
2. Approve Step 0 (agent preparation; no spending).
3. Approve creating a DeepPCB account, uploading the board and a credit cap.
4. Approve the movable-part list (agent will show the allowed regions).
5. Decide whether debug test points TP12-TP15 can change.
6. Pre-approve asking freelancers for quotes if the tools stall (no
   commitment).
