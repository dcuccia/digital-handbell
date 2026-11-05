# Routing completion plan - November 2026

Goal: a fabricable **engineering-prototype** PCB in about two to three weeks,
with bounded spending and no further open-ended agent routing loops. This
plan supersedes "await Quilter support" as the next step. It does not
authorize purchases, uploads to new services or ordering; each spend below
needs the owner's explicit approval.

## What we have learned

| Evidence | Lesson |
|---|---|
| Authoritative four-layer board `adc262b3` has **37 opens** after roughly $1k of LLM-driven routing | Agents made real progress, but the cost was mostly qualification/checker tooling around each small move, not routing itself. |
| Quilter four-, six- and eight-layer jobs (October) | Useful placement and routing ideas, but no candidate finished. The best eight-layer standard result still has 34 opens, all six QSPI nets open, and 64-76 tracks below our 0.1778 mm floor. Beta results trade opens for shorts/collisions. |
| Quilter support (October 16) | Product help only, no layout review. Advice: more room around IC1, iterate placement, run small parallel experiments. No reply to our width follow-up is expected. |
| Every route repeatedly stalls at **IC1** (RP2040 core supply, its decouplers and USB) | The long tail is a local placement/congestion problem. A router of any kind cannot solve it with all parts fixed and our clearance rules. |
| Freerouting closed 0/7 trial opens; tscircuit failed preservation | Free classic autorouters are not the answer for the hard part. |

Our four-layer board is further along than any Quilter output where it
matters: QSPI flash, the crystal clock, IMU, battery contacts, boost/protection
cells and the five process vias are already routed and reviewed, and its
placement was modeled in the mechanical CAD (a final re-bind is still
required: `mechanical_rebind_required=true`). The eight-layer candidates use a
different placement, need eight layers, and would require mechanical
re-binding. **Recommendation: finish the four-layer board.** Keep all Quilter
outputs as reference only.

## The 37 remaining opens

From the post-IMU triage (38 opens) minus the accepted C13 ground stitch.
Step 1 regenerates the exact list for `adc262b3`.

**Group E - short low-speed signal hops (about 18 opens):**
I2S_BCLK/DIN/LRCLK (IC1-U4 links plus TP12-TP14), AMP_MUTE (TP15), ~RESET
(R1, TP7), SWCLK/SWDIO (TP4/TP5), INT (IC1.34-IC4.4), D13 (IC1.16-R7),
GAIN, BUTTON, POWER (IC1.35-Q2-U5; an enable/gate control, not a supply).
These should be quick with KiCad's interactive push-and-shove router.

**Group H1 - MCU core and USB (about 6 opens plus IC1 grounds):**
VCORE (2), D+/D- (IC1-R9/R10), USB_D+/USB_D- (R9/R10-X6), and the IC1
decoupler/C18 ground islands. This is where small decoupler moves may help.

**Group H2 - power, audio and ground returns (about 9 opens plus the other
GND islands):** VBUS (2), VHI, VBAT, VAMP, VO+ (C22-J1), FB2-U4.10, and GND
islands at the USB shell, charger/battery, flash, gain and power switch.
These need current/return judgment and are spread across the board, not
only near IC1.

GND contributes six of the 37 opens across H1/H2.

Optional simplification (owner decision): removing I2S/AMP_MUTE test points
TP12-TP15 would remove about four opens. This is a design change: schematic,
PCB, BOM/CPL and parity must change together, and any replacement "via test
access" must stay physically probeable after assembly. Keep SWD, RESET and
BOOT access for recovery.

## Change how we work

1. **A human routes in the KiCad GUI; agents support.** Interactive routing
   with live DRC is how professionals finish boards like this. Agents prepare
   the punch list, constraints and suggested strategy, then check the result
   between sessions. Agents stop generating copper geometry move by move.
2. **Allow small, explicit placement moves around IC1, inside agreed
   envelopes.** Proposed movable parts: C6, C7, C8, C13, C17, C18, R1, R9,
   R10. Before anyone moves them, the agent derives each part's allowed
   region from the mechanical model (speaker/magnet height, battery-contact
   metal, USB). Every accepted move is recorded in the placement manifest.
   The earlier rejected "source-cell" attempt failed in agent implementation,
   not because the move was physically impossible.
3. **Fix inputs first, then check once per session.** Freeze the netlist and
   rule set before routing (Step 0). Each routing session ends with one
   standard check (below), not a qualification report for every edit.

## Plan

**Status, November 5:** proposed plan only. No board, rule, upload, purchase
or freelancer contact has happened. Owner decisions below gate Step 0.

### Step 0 - freeze inputs (agent, about 1-2 hours, before routing)

1. Regenerate the exact open list for `adc262b3`.
2. Review the **46 schematic-parity findings** (22 explicit-unconnected-pad
   names, 24 auto-named nets). Fix or approve each so routers work against an
   unambiguous netlist. Record the frozen PCB/schematic/project hashes.
3. Write the **standard session check**: KiCad 10.0.6 DRC on a copy with
   zone refill, `--schematic-parity --severity-all`, plus our engineering
   rules where they are stricter than the project file: 0.1778 mm minimum
   new track, 0.20 mm foreign-copper clearance (the project file says 0.1778),
   0.25 mm hole/contact clearance, battery-contact keep-outs. Compare against
   the frozen baseline: opens may only decrease; no new shorts, clearance or
   width findings; no lost existing joins; private returns and CELL_NEG
   isolation intact.
4. Write the via specification: **new ordinary vias** use one stated size;
   the existing exceptions stay untouched (four U4 vias about 0.604/0.35 mm,
   C24's 0.60/0.30 mm, and the five filled/capped process vias).
5. Derive movement envelopes for the movable-part list.

### Week 1 - three low-cost parallel tracks (time-boxed)

**Track A - owner-driven easy closure (recommended; about 3-6 hours).**
Agent produces a printable punch list for Group E: each connection, its pads,
suggested layer and via strategy, and keep-out reminders (battery-contact
metal, protected In1 GND, private returns). Owner routes them in KiCad on a
working copy, guided as needed. Agent runs the standard check after each
session. Expected outcome: 37 -> about 19 opens, and
the owner gains the skill for the next board.

**Track B - DeepPCB probe on a copy (owner approves upload and a credit cap,
e.g. $50).** DeepPCB has an open-source KiCad plugin and pay-as-you-go
credits. Its free trial appears limited to 100 components (we have 104
references); check how it counts before buying credit. Vendor material says
it can route selected nets and keep existing copper; that is **not yet
verified**. First test import/export and locked-copper preservation, then
one run of 30-60 minutes. Keep the result only if it passes the standard
check and closes named groups. Stop at the cap; build no tooling around it.

**Track C - freelance quotes for H1/H2 (no spend until owner approves).**
Agent prepares a reproducible packet: frozen KiCad project and hashes, exact
open-group list, stackup and layer roles, net classes and current needs,
USB 90-ohm pair geometry, movable-part envelopes, locked copper/pours and
process-via list, mechanical keep-outs (STEP), the standard check commands
and accepted-warning list, and required native KiCad deliverables. Completion
is defined by passing the standard check; scope-changing moves need owner
approval. Owner requests fixed-price quotes from two or three KiCad layout
freelancers. A finishing job of this size is typically hours to a few days
of experienced effort; confirm with real quotes, not this estimate.

Altium (ActiveRoute) is a fallback only: the KiCad-to-Altium round trip
risks fidelity, and it conflicts with the low-cost open-source goal.
Further Quilter jobs on this board are not recommended; Quilter remains an
option for a future greenfield revision using placement-first runs.

### Stop rules (to avoid a long tail)

- Each routing session is 60-90 minutes and must close named groups while
  passing the standard check. A session that closes nothing acceptable ends
  that approach for H1/H2.
- Stop immediately if a closure needs an unapproved part move, a change to
  existing protected copper, or a rule relaxation; bring it to the owner.
- **Choose a freelancer by the end of week 1** if H1 or H2 has not started
  closing, rather than waiting for week 2 to fail.
- Do not restart broad agent routing, router bake-offs or layer sweeps.

### Week 2 - finish H1/H2

Owner or freelancer, within the approved movable-part envelopes. Accepted
moves update the placement manifest; re-bind the mechanical model as soon as
placement is frozen. Agent runs the standard check on each returned board and
reports specific problems only.

### Week 3 - pre-fabrication gate and quote package

**Pre-fabrication gate (required before ordering):**

1. Zero unconnected items; the standard check passes with no errors except a
   short, written list of accepted inherited warnings.
2. Schematic parity clean or matching the Step 0 dispositions.
3. Electrical checklist: raw CELL_NEG isolated from protected GND; private
   returns R24.2-C28.2 and R26.2-R27.2 not bypassed; IC1 decouplers close with
   short returns; USB D+/D- routed as a pair; supply/ground track widths
   reasonable for expected current.
4. Five protected process vias unchanged, and the chosen fabricator confirms
   resin fill, planarization, copper capping and price for them in the quote.
5. Mechanical: final re-bind into the FreeCAD assembly confirms moved parts
   still clear the speaker/magnet, contacts and USB opening.
6. Exports: Gerbers, drill, BOM and placement (CPL) for JLCPCB and PCBWay per
   [the quotation plan](pcba-quotation-plan.md), including both rear battery
   contacts and X6.

Then obtain quotes; ordering still requires the owner's explicit approval.
A prototype is for bench bring-up, not child use.

## Owner decisions needed to start

1. Confirm the four-layer board as the baseline.
2. Approve the proposed movable-part list around IC1.
3. Decide whether the I2S/AMP_MUTE test points may change.
4. Approve a DeepPCB credit cap (or skip Track B).
5. Approve requesting freelance quotes (no commitment).

Once approved, the agent starts with Step 0, then produces the Track A punch
list on a working copy.
