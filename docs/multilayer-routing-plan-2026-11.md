# Six/eight-layer routing plan - November 2026

Reviewed plan for owner approval. It was drafted, then critiqued by a GPT-6
Astra rubber-duck review, and all of that review's corrections are applied
below. Approving this plan approves **preparation on private copies only**
(work groups G1-G5, no spending). DeepPCB credit, the final stackup and the
kept-copper list are approved separately at Gate A.

## Why more layers now (and why the earlier analysis said no)

The October six-layer choice used roles S/G/S/G/G/S (signal/ground/...): three
signal layers, the same as today's four-layer S/G/S/S. It bought better return
paths, not routing room. Layer roles are our choice; the fab's stackup only
fixes the spacing between layers.

Two things are different now:

1. **The MCU no longer sits over the battery contacts** (moved-MCU placement
   `swap-5`; contact-blocked IC1 pins 28 -> 0). Ordinary through-vias can now
   escape the MCU, and long nets can cross *under* the contact band on inner
   layers (the band forbids only vias and B.Cu copper) with vias outside it.
2. **A +3V3 power plane removes most supply routing** (+3V3 had over 100
   track segments around the MCU).

Remaining opens on the moved four-layer board are long cross-board nets
(USBBOOT, POWER, VHI, D13, GND islands) and flash/USB links near the MCU.
This plan is a **bounded experiment, not a completion prediction.** B.Cu stays
heavily restricted by the contacts, so count it as partial routing capacity.

## Fab facts (JLCPCB, checked November 6)

- Six layers: typical stackup SIG/GND/PWR/SIG/GND/SIG; minimum trace/space
  0.09 mm, via 0.15/0.25 mm.
- **Via-in-pad filling (POFV) is free on 6-20 layers**, published hole range
  0.2-0.5 mm with separation rules. Confirm the five retained process vias in
  the quote/CAM review. POFV is still copper on the bottom: it does **not**
  grant an exception to the battery-contact restriction.
- Earlier work already has: six-layer **JLC06161H-3313E** (inner signal
  layers about 0.1 mm from their ground planes, 1.12 mm from each other) and
  eight-layer **JLC08161H-2116** with fresh 90-ohm USB pair geometry on four
  signal layers.
- Price: the owner reports six and eight layers cost about the same; web
  estimates disagree. **Owner checks a live JLCPCB quote** (about 45 x 49 mm,
  5 pcs, 1.6 mm, ENIG) for both before Gate A.

## Layer-role options

| Option | Construction and roles | Signal layers | Planes | Trade-off |
|---|---|---|---|---|
| 6A (JLC typical) | S / GND / PWR / S / GND / S | F, In3, B (one inner) | 2 GND + 1 power | Power plane, but In3 references power (0.11 mm) more than GND (0.55 mm). Least routing gain. |
| **6C** | JLC06161H-3313E S / GND / S / S / GND / S | F, In2, In3, B | 2 GND | Two well-separated inner signal layers each next to GND; +3V3 as wide routes/pours on inner layers, no dedicated plane. |
| **8** | JLC08161H-2116, roles chosen from its exact gaps, e.g. S / GND / S / PWR / GND / S / GND / S | F, In2, In5, B | 3 GND + 1 power | Both benefits. Put USB, clock and QSPI on layers that are closest to GND. On the recorded construction In2 is 0.153 mm from In3 and 0.3 mm from In1, so revisit which inner layer is power. |

**Recommendation:** eight layers if the live quote is within a few dollars
of six; otherwise 6C. In1 remains the protected GND plane in every option.

## Work groups (order matters)

### G1 - Stackup decision (owner quote + agent)
- Set the KiCad stackup to the chosen JLC construction and record layer roles
  and which signals may use which layers.
- Rules stay inside the standard process: signal 0.15 mm track/space,
  power clearance 0.2 mm, new vias 0.5/0.3 mm (above JLC minimums).
- **USB:** target about 90 ohm differential (Raspberry Pi RP2040 hardware
  guide), short coupled pair on F.Cu over uninterrupted In1 GND, reusing the
  October geometry for the chosen stackup. Paid impedance certification is
  probably unnecessary for this short route, but the design target stays.

### G2 - Placement freeze and mechanical check (agent)
- Apply the `swap-5` part positions to a clean copy of the authoritative
  board, not to DeepPCB-routed copies; re-run the courtyard legalizer.
- Confirm USB access, buttons, contacts and mounting holes are unchanged;
  height-screen moved parts against the speaker/magnet envelope; FreeCAD
  re-bind once frozen.

### G3 - Kept copper and critical circuits, before bulk routing (agent)
DeepPCB does not honour "protected wiring", so a small fixed set is kept and
everything else is routed fresh. Critical circuits are **routed or
constrained first**, never left as ordinary nets:
- **Keep unchanged:** battery-contact feeds, battery-protection and boost
  cells (including the boost hot loop), private-return copper (R24.2-C28.2,
  R26.2-R27.2), the five process vias.
- **Carry with the MCU move where still valid:** crystal (Y1/C2/C3/R6),
  QSPI flash links and IC1-adjacent decoupler loops, including VCORE. Where
  the move broke them, the agent re-routes these locally with explicit
  constraints (short, single-layer where possible, over GND) **before**
  DeepPCB runs.
- **USB pair:** routed by the agent to the G1 target.
- Everything else (I2S, IMU, GPIO, test points, long power links) goes to
  DeepPCB.

### G4 - Planes, supply map and guards (agent designs; owner approves the explained trade-offs)
- **Supply map:** the agent writes a rail/zone map. +3V3 is a substantially
  continuous plane (eight-layer) or wide inner pours (6C). VBAT, VHI and VAMP
  are distinct rails with their own zones or routes and permitted
  source/load connections. VCORE stays local routing.
- **Current and thermal:** worst-case low-battery boost input current, peak
  and ripple current, copper weight, plane necks, thermal spokes and
  parallel vias. These set real widths and via counts per rail, including the
  class-D speaker outputs, instead of a generic "0.3 mm or wider".
- **Plane connections:** placed by our tool (stub plus via to the plane),
  because DeepPCB added no plane vias in earlier runs. An **exception list**
  is mandatory: R24.2 and R26.2 must reach GND only through their private
  pickoffs; `/CELL_NEG` never touches GND. Guards are applied on every
  conducting layer, and the filled-copper topology is verified, not just
  "reaches GND".
- **Contact band:** no via or via annulus anywhere in the band. Pads inside
  it escape on F.Cu to vias outside it. Ground planes connect at permitted
  locations on both sides of the band.
- **DeepPCB copy only:** clearance raised to 0.18 mm signal, 0.23 mm power and
  0.45 mm edge, because DeepPCB undercuts requested clearances. Checks always
  use the real rules.

### G5 - Tools, frozen baseline and controls (agent)
- Make the tools layer-count aware: `prepare_deeppcb_input.py`
  (stackup, planes, guards on all layers), `route_gaps.py` (all allowed
  signal layers), `stitch_gnd_islands.py` (plane by net, honouring the
  exception list).
- `check_routing_result.py` additions: no new tracks on any plane layer; every
  GND/+3V3 pad reaches its plane **except** the exception list;
  private-return bypass detection through new planes; contact-band check
  using via annuli.
- **Freeze the prepared, plane-connected board as the routing baseline**
  (hash recorded). All later checks compare against it.
- **Controls before any spend:**
  - Negative cases: a new-plane private-return bypass, a disconnected plane
    island, a missing stitch, a contact-band via and lost kept copper. Each
    must fail the check.
  - A no-routing DeepPCB import/export round trip of the frozen board must
    pass the check unchanged.
- **Timebox:** agent preparation G1-G5 is limited to about two working
  sessions. Unfinished items return to the owner instead of continuing
  open-ended.

### G6 - DeepPCB iteration protocol (spend, after Gate A)
1. Free: upload the frozen board, read its stats, and run the free IC1
   fanout. Require usable legal escapes with the power connections already
   in place, not only "zero pins in keep-outs".
2. Run 1: full route, 15-minute cap, stop after about 3 minutes without
   progress, and **confirm via the API that the job actually stopped** (the
   driver's wait timeout alone does not stop it). About $7.50.
3. Post-process: merge onto the frozen baseline (via de-duplication), remove
   only new conflicting copper, `route_gaps.py`, stitch, DRC under real
   rules, standard check.
4. **Gate B:** continue only if the post-cleanup open count on the frozen
   placement is at most about 15, and the remainder is a concrete,
   repairable list. DeepPCB's own count does not decide this. Then at most
   one more 15-minute run.
5. Budget: about **$15 is the target** for this experiment. The owner will
   add $30 when it is time, so about $34 is available. That is a guide, not
   a hard cap: continue past $15 only when Gate B criteria show real
   progress, and report spending at each gate.

### G7 - Acceptance, then fabrication, then bring-up (separate approvals)
- **Routing acceptance:** zero opens; DRC clean under real rules; schematic
  parity dispositioned; plane topology and exception list verified;
  CELL_NEG isolated; private returns intact; plain-language electrical review
  (decoupling, USB pair, supply currents).
- **Fabrication approval:** mechanical re-bind; Gerber/drill/BOM/CPL for
  JLCPCB with the stackup and POFV called out; live quote; owner orders.
- **Powered bring-up:** a separate later step; a prototype is bench-only,
  not for child use.

## Gates

- **Approval now:** preparation G1-G5 on private copies, no spending.
- **Gate A (before any spend):** stackup chosen from the live quote; the
  kept-copper list and supply map approved; tools pass their controls;
  free upload and fanout look sane. Then owner tops up credit as needed.
- **Gate B:** see G6.
- **Fallbacks if Gate B fails:** the owner's JST battery lead (removes the
  contact band), or a freelancer for the best board.
