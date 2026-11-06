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

**Status, November 6:** Steps 0-2 done; best clean result is still 25 opens.
Moving the MCU cleared the battery-contact blockage, but DeepPCB's output
needs rule repair before it beats 25 (see the November 6 entry below).
Lessons are summarized in [routing tooling](routing-tooling.md#current-conclusion).

**Status, November 5, 16:10:** Steps 0-2 done. DeepPCB plus automatic
filtering and ground stitching took the board from 38 to 25 opens, then
stalled at the RP2040 pins. **16:20 owner decision:** freelancer option is on
the back burner (cost and turnaround); continue iterating with DeepPCB
(including its single-component fanout API) and agent-driven placement and
layout for the stickiest pieces.

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

**November 5, 16:10 DeepPCB result: 38 -> 25 opens, then stopped (fail fast).**
Owner bought one hour ($30); 18 minutes ($9.02) used, about $21 left.

| Step | Opens (KiCad) | Notes |
|---|---|---|
| Baseline routing input | 38 | 0.2 mm signal rules |
| Run 1, 5.5 min, protected mode | - | DeepPCB **did not honour "protect existing wiring"**: it rerouted the reviewed crystal clock (XIN/XOUT), charger STAT and some VBAT copper, and ran VBAT through a battery-contact guard. Its web summary says one keep-out type was ignored and edge clearance is 0.05 mm. Stopped. |
| Filtered merge (`tools/merge_router_nets.py`) | 31 | Keep every baseline item; add DeepPCB copper only on previously open nets; exclude VBAT (contact guard) and AMP_MUTE (edge via). Passes the check. |
| Run 2, relaxed signal rules, 7.5 min | 28 | Signal class 0.15 mm track/space, 0.5/0.3 mm vias (JLC standard reportedly 0.10 mm and 0.45/0.20 mm). Closed D13, two I2S lines, a TP and part of VCORE; new tracks split the F GND pour (+2 islands). |
| GND stitching (`tools/stitch_gnd_islands.py`) | **25** | Four 0.6/0.3 mm GND vias into In1 where every layer is clear. Passes the check: no part moved, all existing copper kept, no new DRC errors. |
| Run 3, 5 min | 25 | Plateaued; nothing usable. Second pass without progress, so DeepPCB stopped. |

Best candidate (private): `deeppcb-20261105\best-25-open-relaxed`, PCB
`ce81d6af...`. It needs owner approval of the 0.15 mm signal rules before
fabrication use, plus the normal electrical review of DeepPCB's new routes.

**Remaining 25 opens:** 13 at RP2040 (IC1) pins (~RESET x2, SWCLK, SWDIO,
D+, D-, I2S_DIN, INT, POWER x2, BUTTON, AMP_MUTE, VCORE); 6 GND islands with
no safe via site; GAIN, VBAT, VBUS, USB_D+, USB_D-, VO+. Tools - Quilter,
DeepPCB and earlier agents - all stall at IC1 pin escape. That tail needs a
layout judgement around IC1 (small part moves, escape pattern), which is the
gated freelancer step.

**November 5, 16:30 - why IC1 is stuck (physical constraint, not a router
limit):** IC1 sits directly over the rear battery-contact bases. The
`CONTACT_METAL_GUARD_BT1.base.1` and `BT2.base.1` areas (needed so no via or
B.Cu copper touches the cell terminal metal or bypasses CELL_NEG isolation)
cover IC1's left and right pin rows. Those pins cannot drop a via near the
chip; they must run about 2 mm on F.Cu past nearby decouplers first.
DeepPCB's free single-component fanout API (`POST /boards/{id}/fanout`)
reported the same: pins in keep-outs, 46/57 escaped. Removing the board-wide
In1 track keep-out reduced "pins in keep-out" from 57 to 28; the standard
check now separately rejects any new In1 track. Next: an Astra sub-agent
adds legal F.Cu escape stubs and vias for the open IC1 pins (no part moves),
then DeepPCB routes from them. Blind F-to-In2 vias would also avoid the
contacts but need costly HDI fabrication.

**November 5, 16:40 - iteration results; DeepPCB stopped again (fail fast).**
Total DeepPCB use 26.7 minutes ($13.34); about $16.66 credit remains.

| Attempt | Result |
|---|---|
| Free IC1 fanout on the 25-open board | No usable gain (escaped pins were already routed). |
| Remove board-wide In1 track keep-out, fanout again | IC1 pins in keep-outs 57 -> 28; no usable gain. |
| `tools/escape_ic1_pins.py` (grid A* F.Cu stubs to legal vias, 0.15 mm rules) | Individually some pins escape, but only by running under the QFN body, which blocks neighbours; with the body excluded almost nothing escapes. F.Cu around IC1 is saturated (104 +3V3 segments within 7 mm). D- has no exit at all. |
| Rip-up of +3V3/VCORE/USBBOOT/D13/GND tracks/I2S within 7 mm (`tools/rip_up_region.py`), fanout + 7.5 min route | DeepPCB 51 -> 15 by its count, but its routing again moved protected copper; the filtered merge creates shorts/clearance/crossings and reaches only 24 opens. Rejected. |

**Root cause:** IC1 sits over both battery contacts' inner bases. Their via
keep-outs cover IC1's left and right pin rows (28 of 57 pins), and the only
F.Cu escape space is already filled by supply routing. More router passes
will not change that. Realistic options (owner decision):

1. **Move IC1 and its cluster** about 6 mm north or south, so no IC1 pin row
   lies over the contact bases, then let DeepPCB route the area (the board
   may grow 10-20% if needed). Biggest benefit; a real placement change
   requiring a mechanical re-check.
2. **Relax the via keep-out under the positive (VBAT) contact only**, for
   example filled and capped vias under solder mask. Never under the
   negative contact, where it could bypass battery protection. Needs an
   explicit insulation decision.
3. **Six layers do not help** this specific wall: escape vias are still
   blocked through the contacts. Blind F-to-In2 vias would help but need HDI
   fabrication at extra cost.

**November 5, 16:45 owner decision:** move the MCU (no HDI). The owner is
flexible about where the MCU goes. A JST battery lead is acceptable only if
moving the MCU fails.

**November 6 - MCU move result.** Moving the processor cluster up under
the USB connector (`tools/move_cluster.py`, 41 parts and their internal
copper; courtyards legalized; private copy `deeppcb-20261105\swap-5`)
cleared the contact blockage: DeepPCB fanout reported **0** IC1 pins in
keep-outs, down from 28. A full 15-minute run ($7.50) reached DeepPCB's own
count of 18 missing of 222. After our filtered merge and stitching, KiCad
reports 31 opens plus 27 new rule violations: DeepPCB used about
0.125-0.137 mm clearance and 0.19 mm edge clearance, and made two shorts.
Removing only the new conflicting copper leaves **43 opens**, so this is
not yet better than the 25-open best (`best-25-open-relaxed`).

DeepPCB credit: 41.7 of 60 minutes used, **$9.16 left**. The authoritative
board is unchanged. Next options:

1. One more short DeepPCB run on the cleaned swap board with project
   clearances raised for DeepPCB only (for example 0.18 mm signal, wider
   edge), so its undercut output still meets 0.15 mm.
2. Have an agent repair the specific small clearance violations instead of
   deleting whole tracks.
3. Reconsider placement around the moved charger group (U3/R2/CHG0), where
   several violations occurred.

**November 6, 08:05-09:10 - all three options tried (owner: "try all three in
that order").** Best clean result is still **25 opens** on the original
placement (`best-25-open-relaxed`). DeepPCB credit left: **$4.36**.

| Option | Result |
|---|---|
| 1. DeepPCB with clearances raised for it only (0.18 signal, 0.23 power, 0.45 edge) on the cleaned moved board | Much cleaner output: 34 opens with 1 short, 1 clearance, 6 edge and 3 duplicate-via findings, versus 27 violations before. Then plateaued at DeepPCB's count of 17. About 10 minutes, $5. |
| 2. Repair instead of delete: duplicate-via filter, position-aware cleanup of new copper only, then `tools/route_gaps.py` (our clearance-aware F/In2/B grid router) | **28 opens, no new DRC errors**; only 4 extra dangling-stub warnings. Trimming the stubs cascades to 31. Not better than 25. |
| 3. Spread the moved charger group horizontally, rip its local wiring, re-route with `route_gaps.py` | 30 opens plus 4 shorts against copper that was not ripped. No improvement; stopped after one attempt. |

The moved placement's tail is now long cross-board nets (USBBOOT, POWER,
VHI, D13, GND) through DeepPCB's dense routing. Remaining realistic options:

1. A fresh DeepPCB full route of the moved placement, keeping only critical
   protected copper, with the raised clearances. About 15 minutes ($7.50)
   needs a small credit top-up.
2. The owner's fallback: a JST battery lead. Taking the contacts off the board
   would free the whole centre band.
3. A freelancer for the 25-open board (on the back burner).

**November 6, 09:00:** the owner asked whether six or eight layers could
separate signals from power. The answer is yes, now that the MCU is off the
contacts. See the reviewed
[six/eight-layer routing plan](multilayer-routing-plan-2026-11.md).

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
