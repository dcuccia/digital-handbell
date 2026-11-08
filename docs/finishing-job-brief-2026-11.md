# Finishing-job brief: six-layer handbell PCB (ready to post; not posted)

Prepared November 6 after automated finishing reached its stop rule
([Gate A results](multilayer-gate-a-2026-11.md), end sections). Updated
November 8: the base is now best-8-c1c4 (`2e8e16bf`), which already has
C1 and C4 beside U2. The owner waived its silkscreen-over-pad increase,
so the capacitor-move deliverable is dropped. **The owner
decides whether and where to post.** Agents must not create accounts, post
jobs or pay anyone.

Where to post (from the [freelancer explainer](layout-freelancer-explainer-2026-11.md)):

- Upwork or Fiverr fixed-price, KiCad-experienced, with milestone escrow;
- or a PCBWay layout quote.

Expected budget: $75-300 for a scope this small. This is an estimate, not
a quote.

## Job text (copy and paste)

> **Finish routing of a nearly complete 6-layer KiCad 10 board (8 open
> links).** Open-source hobby project
> (an RP2040 digital handbell), about 45 x 49 mm, JLCPCB six-layer stackup
> JLC06161H-3313E (signal/GND/signal/signal/GND/signal). All parts are
> placed, and all but 8 connections are routed rule-clean.
>
> Deliverables:
> 1. Route the 8 remaining unconnected links listed in `opens.md`.
> 2. Keep C1 (10 µF, LDO U2 input) and C4 (U2 output) where they are,
>    within 3 mm of U2 pins 1 and 5. Optional: nudge the R15, R17, TP3 and
>    C5 reference labels off the C1/C4 pads. U2 sits next to a
>    battery-contact guard area and /CELL_NEG copper on B.Cu, so keep new
>    ground vias out of the guard and off /CELL_NEG.
> 3. Route the USB D+/D- pair (connector X6 to the protection part and the
>    MCU) as a coupled 90-ohm differential pair, using the JLC stackup
>    calculator.
> 4. The result must pass KiCad DRC with no new errors (71 known
>    `items_not_allowed` findings at the battery-contact keep-outs are
>    accepted) and zero unconnected items.
>
> Constraints:
> - Do not put tracks on In1/In4 (GND planes).
> - No vias or B.Cu copper inside the battery-contact guard rule areas.
> - Keep /CELL_NEG isolated.
> - Keep the private-return pads (R24.2, C28.2, R26.2, R27.2) on their
>   existing paths.
> - Supply widths: VBAT/VHI/V+ 0.8 mm; VBUS/VAMP 0.5 mm; +3V3/VCORE
>   0.25 mm. Short pad escapes of 1 mm or less may be narrower.
> - Through-vias only (0.5/0.3 mm or larger); no blind, buried or
>   via-in-pad vias.
> - Ask before moving anything other than passives or test points, or
>   before rerouting the crystal (Y1/C2/C3), the boost converter (U5 area)
>   or the battery-protection copper.
>
> Please return the .kicad_pcb file only. We validate with our own scripts.

## Remaining links (`opens.md` in the bundle)

| Link | Notes from automated diagnosis |
|---|---|
| POWER U5.2 to Q2.1 | Enclosed by the U5 boost cell and the Q2 ~ENABLE track |
| VO+ J1.1 to C22.1 (0.6 mm) | Enclosed by VBAT, VAMP, C22 GND and USB D- |
| GND IC1.19 (TESTEN) to GND | Enclosed by XIN track and via (crystal) |
| GND GAIN0.1 to GND | Enclosed by VBAT copper and GAIN/VAMP pads |
| F.Cu GND island near X6.M3 | Pour neck at the USB anchor |
| USBBOOT to D3.C | Blocked by an IC1 +3V3 pad and R18 pads |
| SWDIO TP5 to IC1.25 | Enclosed by SWCLK/RESET pads and VCORE escape |
| I2S_LRCLK TP14 to U4.14 | Blocked by USB D+ and U4 GND; TP14 may move anywhere |

Test points TP5/TP14 may move anywhere legal. SWD access (TP5) must stay.

## Acceptance (run by the agent after delivery)

1. `kicad-cli pcb drc --refill-zones --schematic-parity --severity-all`:
   - 0 unconnected items;
   - error types and counts no higher than best-8-c1c4 (its
     `silk_over_copper` count of 97 is waived; fewer is better);
   - dangling items reviewed.
2. `tools/check_routing_result.py` against `6c-frozen-tp`, with
   `--allow-move C1 C4` plus every part the person moved. Reviewed critical
   copper changes must be listed and explained.
3. `tools/check_cap_adjacency.py`: C1 and C4 still at 3 mm or less from
   their pins (now 1.16 and 1.54 mm).
4. Width audit: no new supply copper below its class, except pad escapes
   of 1 mm or less.
5. Electrical review of USB pair coupling and impedance, then a FreeCAD
   mechanical re-bind, before any fabrication approval.

## Bundle

The bundle is outside the repository:
`multilayer-20261108\finishing-job-bundle-c1c4\` under the bakeoff root,
plus a zip. It contains:

- best-8-c1c4 `handbell.kicad_pcb` (2e8e16bf);
- `.kicad_pro` with the net classes, and `.kicad_sch`;
- `drc.json`;
- `opens.md`;
- this brief;
- the stackup note.

The November 6 best-8 bundle remains in
`multilayer-20261106\finishing-job-bundle\` as a fallback.

All files are from the public OSS project, so they are fine to share with
a contractor.
