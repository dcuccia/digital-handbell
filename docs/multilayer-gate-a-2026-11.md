# Gate A proposal - six-layer preparation (November 6)

Prepared under the approved [six/eight-layer plan](multilayer-routing-plan-2026-11.md).
Private copies only; no spending. Owner decisions are marked **Decide**.

## G1 - Stackup: 6C recommended

Live JLCPCB quote page (November 6, about 45 x 49 mm, 5 pcs, 1.6 mm, standard
build time): **six layers about $35-49, eight layers about $90**. The page's
defaults (finish, material) change with layer count, so these are
approximate. Eight layers costs about $40-55 more, not "a few dollars", so the
plan's rule selects **6C: JLC06161H-3313E, layer roles S / GND / S / S / GND / S**
(F, In1 GND, In2, In3, In4 GND, B). The stackup is copied from the October
native board (`c7497180`), so it is not re-derived.

**Decide:** accept 6C, or pay for eight layers to also get a dedicated +3V3
plane.

## G2 - Placement frozen on a clean six-layer copy

- Part poses come from the moved-MCU placement (`swap-5`): 41 parts moved
  (MCU cluster up under USB, charger group into the centre band). USB,
  buttons, battery contacts, the boost/protection cells and mounting holes
  are unchanged.
- Placement conflicts with kept copper were resolved by nudging D3 (0.6 mm)
  and D4 (0.5 mm); R9/R10 stay put and one carried-over flash track was
  re-routed instead.
- **Height screen against the speaker magnet** (21.7 mm diameter up to
  z = 23.5 mm; PCB front face at z = 25 mm):
  - All parts over the magnet clear it, using real part heights.
  - C1 and C20 (Murata GRM21B, 1.25 mm +/- 0.1 mm thick) clear it by only
    about 0.15 mm. The manifest's 2.0 mm figure is a conservative
    placeholder.
  - **Decide:** accept the thin margin (the owner earlier allowed up to
    2 mm extra speaker spacing), or move these capacitors away from their
    chips.
- Still to do: FreeCAD re-bind of the frozen placement.

Private files: `multilayer-20261106\6c-frozen` under the bakeoff root. DRC
under real rules has **no new errors**; only the 71 reviewed keep-out
findings inherited from the authoritative board remain. **86 opens.**

## G3 - Kept copper (built by `tools/build_multilayer_input.py`)

Rule: each existing copper island is treated as follows.

| Island touches | Action | Items |
|---|---|---|
| Only unmoved parts | Keep exactly | 545 |
| Only moved parts that all moved together | Move with them | 80 |
| Both moved and unmoved parts | Drop; route fresh | 579 |

- Kept whole: battery protection (/CELL_NEG, all /PROT_*), boost (V+,
  BOOST_SW, BOOST_FB, ~ENABLE, EN), audio output (VO+, VO-, FB1),
  BUTTON_EXT, VAMP, plus contact feeds, private-return copper and the five
  process vias.
- Moved with the MCU: flash (QSPI), crystal output, part of VCORE and the
  charger links.
- **Critical circuits routed by the agent before DeepPCB:**
  - Done: crystal, flash chip-select and data, and the USB data lines
    (both resistor sides) - 15 of 17 connections, rule-clean.
  - Still open: two short VCORE (core supply) hops beside the MCU.
  - The USB pair was routed as two separate traces. It still needs a
    coupled, 90-ohm-geometry re-route before acceptance.

**Decide:** approve this kept-copper rule.

## G4 - Supply map (proposal)

Based on the repository's existing provisional targets
(`printed-bell-routing/reports/power-routing-review.md`): cell/source 2 A
continuous (3 A sensitivity), 5 V distribution 1 A, speaker 1.2 A peak.

| Rail | Role | Proposed copper (1 oz outer) |
|---|---|---|
| VBAT, VHI, V+ | Cell -> source switch -> boost input; carries the boost current | 0.8-1.0 mm on F/B, or local pours; at least 3 vias at each layer change; avoid inner 0.5 oz layers for long runs |
| VAMP | Boost 5 V output to amplifier | 0.5-0.8 mm (already kept as reviewed) |
| VBUS | USB 5 V in, charger and source switch | 0.5 mm |
| +3V3 | Regulator to MCU, flash, IMU (low current) | 0.25 mm routes, plus a local **+3V3 pour on In3** under the MCU/flash area to replace most of the 32 short supply links |
| VCORE | MCU core regulator output to its decouplers | Short local routes, 0.25 mm where it fits |
| GND | Return | In1 and In4 planes, F pour, stitching vias |

- Today's "power" class is 0.3 mm for VBUS/VBAT/VHI/VAMP, which is too
  narrow for the 2 A cell path.
- **Decide:** approve the new widths, and the In3 +3V3 pour limited to the
  MCU area.
- Guards: the battery-contact band allows no vias or B.Cu copper; private-
  return guards are mirrored onto the new In4 plane; /CELL_NEG never touches
  GND. Plane stitching must skip R24.2 and R26.2.

## G5 - Tools and fixes (done)

- New tools:
  - `tools/build_multilayer_input.py`: kept-copper rule, stackup
    transplant, In1 -> In4 zone mirroring.
  - `tools/fit_parts_to_copper.py`: nudges parts off kept copper, drops
    moved copper in keep-outs, keeps parts out of a height zone.
- `tools/route_gaps.py` now takes the layer list, a net filter, via cost and
  supply widths, and never emits zero-length segments.
- **Bug fix:** DRC net names with brackets (`QSPI_DATA[3]`) were truncated
  by three tools, so such nets were silently skipped; a shared parser
  (`drc_net`) fixes it.
- KiCad's Python API breaks process-wide after removing items; tools now
  edit in separate processes.
- **Standard check is now plane-aware:**
  - It rejects new tracks on any power-type layer (In1, In4).
  - It flags new vias inside the copper island of a private-return pad
    (R24.2, R26.2), which a plane would otherwise join.
  - It ignores zero-length items.
- **Negative controls (six layers), each FAILs as required:**
  - a private-return via;
  - a track on In4;
  - a via in the battery-contact band;
  - new /CELL_NEG copper;
  - a removed 5.1 mm protected /PROT_COUT track.
- **Frozen baseline:** `multilayer-20261106\6c-frozen`, PCB SHA-256
  `b82f2fe3474f32711bc0f36c4d3a83546f57121b0bf268a3a75a299b5564f93d`;
  86 opens, no new DRC errors.
- **Free DeepPCB checks:**
  - **Round trip:** the unrouted revision downloaded and preserved every
    part and copper item (three zero-length router stubs were removed
    beforehand).
  - **Fanout:** DeepPCB sees 6 layers and 3 planes. The board-wide "no
    tracks" rule areas on the plane layers made DeepPCB count all 57 IC1
    pins as in a keep-out. With those areas removed from the DeepPCB copy
    only (the check still enforces no plane tracks), 0 pins are in
    keep-outs and 44/57 escape. The other 13 sit beside the pre-routed
    critical circuits.
- **DeepPCB copy** `multilayer-20261106\deeppcb-input2`, uploaded as board
  `d254093c-a410-4a5a-95e1-dd72885c83d3`: the frozen board without plane
  no-track areas, with clearances raised to 0.18 / 0.23 / 0.45 mm. No routing
  job started.
- Plane stitching needs no new exception logic. The private-return guards
  already forbid vias and pours on F/In1/In4 around R24.2/R26.2, and the
  check's private-bypass test catches any violation.

## Decisions needed at Gate A

1. Stackup: 6C (recommended) or eight layers (about $40-55 more per 5 pcs).
2. C1/C20: accept the thin magnet margin, or move/substitute them.
3. Kept-copper rule (G3).
4. Supply widths and the In3 +3V3 pour (G4). The agent applies these to the
   frozen board before the first paid run.
5. Then top up DeepPCB credit. Run 1 is a 15-minute full route, about $7.50.

## Gate A approved (November 6, 10:22) and routing results

**Owner decisions:** six layers (6C); the C1/C20 magnet margin is fine;
kept-copper rule and supply widths approved; $30 credit added (the $15
target is a guide, not a hard cap).

- Net classes applied to the frozen board: `thickpower` 0.8 mm (VBAT, VHI,
  V+), `power` 0.5 mm (VBUS, VAMP), `supply` 0.25 mm (+3V3, VCORE). No new
  DRC errors.
- **+3V3 pour on In3: deferred to after routing**, as a fill-around zone,
  so it does not block In3 signal routing.

| Step | KiCad opens | Notes |
|---|---|---|
| Frozen six-layer baseline | 86 | |
| DeepPCB run 1 (protected, 13 min, plateau stop) | 14 after merge | DeepPCB count 83 -> 12. Merge: 6 edge-clearance findings, 1 B.Cu VBAT track in a contact guard (removed). |
| Clean + gap router + stitch (free) | **12** | **No new DRC errors**; only dangling-stub warnings. Best board `best-12-open-6c` (`d62a0494...`). |
| Run 2 (protected, from the 12-open board, 4 min) | 12 | Added nothing; plateau stop. |
| Run 3 (unprotected, 10 min) | 14 after cleanup | Worse; discarded. |
| Gap router with 10 mm search window | 12 | No change: the remaining links are blocked by routed copper. |

DeepPCB spend: about **$14**; **$20.35** credit left. Remaining 12 opens:
SWDIO (TP5), ~RESET (TP7), I2S_LRCLK x2 (IC1-U4, IC1-TP14), POWER (U5-Q2),
USBBOOT (to D3), VBUS (U3-CHG0), VHI (to C1), VO+ (J1-C22), and 3 GND pour
islands.

Next (free, agent): relocate test points onto their own nets' existing
copper (owner allowed test points anywhere), then targeted
rip-up-and-reroute of blocking router-made copper for the long nets.

### Free follow-up (November 6, 11:15-12:00)

- `tools/relocate_test_points.py` (new): moves single-pad test points onto
  own-net copper, or (`--near`) into a free spot next to own-net pads, for
  the gap router to link.
  - TP7 (~RESET) moved 10 mm and was linked: **11 opens**, still no new DRC
    errors.
  - TP14 moved next to U4, but its link is not yet routed.
  - TP5 has no legal spot near IC1.
- `tools/rip_corridor.py` (new, experimental): rip-up of router-made copper
  along straight corridors. Too crude: it ripped about 120 items and ended
  at 18 opens. Rejected; corridor rip-up needs per-net, path-aware
  selection.
- **Best board:** `multilayer-20261106\best-11-open-6c`, PCB SHA-256
  `be2b98c3c023821bc1c78b6fc206ddf39806f2fb72b1326ad01e648bc4e7064c`.
  Moves TP7 and TP14 only, versus the frozen placement.
- Remaining 11:

  | Link | Length |
  |---|---|
  | SWDIO IC1-TP5 | 6.5 mm |
  | I2S_LRCLK IC1-U4 | 13.8 mm |
  | I2S_LRCLK U4-TP14 | 6.1 mm |
  | POWER U5-Q2 | 16.7 mm |
  | USBBOOT to D3 | 21.3 mm |
  | VBUS U3-CHG0 | 7.8 mm |
  | VHI to C1 | 7.8 mm |
  | VO+ J1-C22 | 8.9 mm |
  | GND islands, including IC1 pin 19 (TESTEN) and GAIN0 pin 1 | 3 links |

- DeepPCB credit left: **$20.35** (about $14 used).
- Still open before acceptance:
  - USB pair as a coupled 90-ohm route.
  - +3V3 pour on In3.
  - Remove dangling stubs.
  - Electrical review and mechanical re-bind.

### Run 4: fresh 15-minute route of frozen placement plus test-point moves (November 6, afternoon)

- New standard pipeline: `tools/postprocess_router_result.ps1`. It chains
  merge, GND stitch, conflict clean, `tools/remove_guard_copper.py` (new),
  gap route, stitch, gap route and the standard check, one folder per
  stage.
- New baseline `multilayer-20261106\6c-frozen-tp`: the frozen board with
  only TP7/TP14 moved. It has the same 86 opens and 71 inherited
  `items_not_allowed` as the frozen board.
  - The first attempt used `move_cluster.py`; its legalizer removed three
    vias, so it was discarded and the upload (a08e5272) was not run.
- DeepPCB board 3b3e141c, protected, 15 minutes (about $7.50).
  - The API returned no stats during the run, so the plateau stop could
    not trigger and the run used its full cap.
  - After the pipeline: **14 opens**, no new DRC errors, three more
    dangling items. **Worse than best-11.**
- Run 4 did close five links that are open on best-11 (SWDIO, VHI at C1,
  both I2S_LRCLK, VBUS U3-CHG0). A net-copper transplant onto best-11 was
  tried:
  - All four nets together: 49 clearance errors and 38 shorts; 14 opens
    after cleaning.
  - Each net alone: still 2-34 clearance errors plus shorts.
  - Rejected. Router copper for one net depends on that run's routing of
    the others.
- Lesson: fresh full re-routes of the same placement reach a similar open
  count (11-14), but strand different links. More DeepPCB minutes on this
  placement are not a good use of credit. The remaining links need
  per-net, path-aware finishing on the best board.
- DeepPCB credit left: about **$12.85**. Best board is still
  `best-11-open-6c`.

## Finishing pass 1 (Sol)

Runtime gate: the lead supplied the `subagent.configured` event for agent
`c522a19f-8e09-450d-885c-15b9912cdc50` at `2026-11-06T20:00:35Z`; it records
`gpt-5.6-sol`, medium reasoning and `explicit_override`.

`tools/reroute_with_ripup.py` adds deterministic per-net soft-obstacle A*.
Copper absent from `6c-frozen-tp` is costly but traversable; frozen copper,
pads, hard holes, keep-outs and the edge remain hard. The tool removes only
the crossed router-made primitives and records their UUIDs as replacement
obligations. Routing and restoration remain separate fresh processes because
pcbnew wrappers are unsafe after removal.

The initial SWDIO attempt found a path after 264,414 expansions in 4.859 s,
but required removing eight SWCLK/I2S_DIN/RESET primitives. Routine restoration
closed only I2S_DIN, leaving 14 opens, so the trial was rejected. The first
correction targeted narrow VHI. It found a path after 15,941 expansions in
2.141 s, removed two GND and two `/IMU_INT2` router-made F tracks, added eleven
0.15 mm VHI tracks plus one 0.50/0.30 mm through-via, and restored `/IMU_INT2`
with 42 new 0.15 mm F tracks. The two removed GND tracks were not required by
the filled connectivity: the same three GND opens remain and no prior open
group regressed. Final native DRC has **10 opens**, the same 71 inherited
`items_not_allowed`, and no new finding type or count versus best-11.

Private candidate:
`multilayer-20261106/finish-pass1/02-rip-vhi/handbell.kicad_pcb`,
SHA-256 `4d0a08d2b7184efbea55879f9b850eebf6ad6a1fad30e8353a11757a620a708a`.
The frozen-baseline standard check fails only because the candidate retains
the already-known best-11 dangling-warning delta (six tracks and one via versus
four tracks and no vias in the frozen board); those counts did not grow from
best-11. Placement, frozen copper, planes, contact exclusions, private returns,
USB D+/D-, stackup and rules are unchanged. KiCad CLI 10.0.6 and Python 3.11.9
were used. This is staged routing evidence, not Astra engineering acceptance
or a fabrication release.

### Lead review of finishing pass 1 (November 6)

- Runtime verified from the session's `subagent.configured` event:
  `gpt-5.6-sol`, effort medium.
- `finish-pass1\02-rip-vhi` (4d0a08d2…) is accepted as the **connectivity
  best: 10 opens**. Its DRC matches best-11 apart from one fewer open.
- **Electrical review item (required before acceptance):** VHI has 0.15 mm
  copper, against the approved 0.8 mm.
  - best-11 already had about 15 mm of it (mostly F.Cu stubs, 4 mm on
    In3).
  - Pass 1 adds 9.4 mm (6.7 mm on In3) to reach C1 (10 µF VHI
    decoupling).
  - C1 is connected, but its high-frequency decoupling value through
    about 9 mm of thin trace is doubtful.

## Finishing pass 2 (Sol)

Pass 2 started from accepted staged candidate
`finish-pass1/02-rip-vhi` (`4d0a08d2...`, 10 opens) and retained the same
verified Sol/medium runtime. The final private candidate is
`finish-pass2/07-rip-vbus/handbell.kicad_pcb`, SHA-256
`e158ccd251325b63b8f03e1d3230dce9c6098b2702356208ec46d68465f9c826`,
with **8 opens**.

The long I2S_LRCLK link from U4.14 to IC1.29 was closed with 0.15 mm signal
copper after path-aware removal and restoration of four router-made items.
The first restoration left one preserved CC2 via and one preserved INT track
dangling; `tools/repair_new_dangling.py` now deterministically reconnects such
newly dangling preserved items through the existing clearance-aware A*. The
corrected candidate restored the best-10 dangling counts. TP14-to-U4 remains
open: the selective-rip proposal did not produce a route, and both on-copper
and 2 mm near-anchor TP14 relocation screens found no legal position.

The later optional VBUS trial closed U3.4-to-CHG0.A and restored its one
I2S_DIN replacement obligation. Every pass-2 VBUS addition is at the approved
width: two F, 46 B and seven In2 tracks at **0.50 mm**, plus three
**0.50/0.30 mm** through-vias. No pass-2 0.15 mm copper was added to VBUS,
VHI, VBAT, V+, VAMP, VO+/VO-, +3V3, VCORE or POWER. `route_gaps.py` and the
rip-up planner now accept an explicit `--net-width NET MM` without changing
their defaults; this was used only to screen VO+ at the existing 0.60 mm power
width. That screen exhausted its sampled component after 420 expansions and
added nothing.

Other bounded outcomes:

- TP5 relocation, including the 2 mm near-anchor screen, found no legal SWDIO
  position. The rejected pass-1 SWDIO rip-up result was not promoted.
- USBBOOT itself routed after four selective removals, but neither the
  full-width 0.25 mm +3V3 replacement nor the D3-anode replacement found a
  path. The whole trial was rejected.
- POWER is in the native Default class, but its path screen still exhausted
  after only 67 expansions with hard/frozen obstacles; no copper was changed.
- VO+ was screened at 0.60 mm, matching its existing wide local copper, and
  left open rather than adding prohibited 0.15 mm supply copper.

Native KiCad 10.0.6 DRC retains the 71 inherited `items_not_allowed` and
exactly the best-10 six track-dangling plus one via-dangling warnings; no
finding type or count grew. The direct best-10 check passes, 10 to 8 opens.
The frozen-baseline standard check fails only on that already-known dangling
warning delta. Placement, frozen copper, planes, USB D+/D-, contact
exclusions, private returns, stackup and rules remain unchanged. This is
staged connectivity evidence for Astra review, not promotion or fabrication
acceptance.

## Finishing pass 3 (Sol)

Pass 3 started from accepted best-8
`finish-pass2/07-rip-vbus/handbell.kicad_pcb`
(`e158ccd251325b63b8f03e1d3230dce9c6098b2702356208ec46d68465f9c826`).
No trial strictly reduced the open count, so **no pass-3 PCB was accepted**;
the exact best-8 board, DRC and checks remain authoritative and were not
rerun unchanged.

`relocate_test_points.py` now supports one aggregate path-aware A* over all
legal relocation candidates rather than a separate expensive search per
position. It can screen both faces, keeps B candidates outside every B-side
rule area (including the contact guards/band), and requires an actual
F/In2/In3/B route to the reported endpoint. The 12 mm, 0.5 mm-grid screen
tested 176 legal F/B TP5 candidates and 233 legal F/B TP14 candidates. None
had a route under the fixed copper, hole, edge, courtyard, via and rule-area
constraints. Both test points therefore remain unchanged:

- TP5: `(95.073680, 95.191699)` mm, F.Cu, -90 degrees.
- TP14: `(110.799999, 94.512211)` mm, F.Cu, 180 degrees.

The deeper full-width power screens also stopped before any removable-net
obligation was created, so the released two-level restoration was not
applicable. POWER U5.2-Q2.1 exhausted the hard-obstacle component after 67
expansions with a 12 mm margin. VO+ J1.1-C22.1, screened at 0.60 mm to match
its existing wide local copper, exhausted after 420 expansions; increasing
the margin from 5 to 12 mm did not change that component.

The final GND stitch pass added no via; the remaining 2.443 mm2 F island had
no legal site. A new `route_gaps.py --nearest-own-copper` mode then tried each
reported GND item against the nearest separate GND track, pad or via on F.Cu.
The zero-distance pour report, GAIN0 group and IC1.19 TESTEN group all returned
`no path`; no copper was written.

Pass 3 added no board copper, including no supply copper, moved no component
and changed no DRC/check result. Trial artifacts are retained under
`multilayer-20261106/finish-pass3`; they are blocker evidence, not candidates
for promotion. The unresolved engineering question is whether any of these
hard endpoint enclosures warrants a placement/frozen-copper change; this pass
does not authorize one.
  - Widen this copper, or move C1, before fabrication. Do not count it as
    finished supply routing.

### Lead design review: capacitor adjacency (November 6)

- New read-only screen `tools/check_cap_adjacency.py` measures each
  capacitor's distance to the pin it serves, optionally against a reference
  layout. Explicit rules name the pin. Results for best-8 against the
  Adafruit 5768 reference:
  - **C1** (U2 RT9080 LDO input, VHI): 12.95 mm versus 1.45 mm in the
    reference. **Defect**: it is connected through about 9 mm of 0.15 mm
    trace. Fix in finishing pass 4 by moving C1 within 3 mm of U2.1.
  - C20 (VBAT bulk): 12.7 mm from Q3, but the reference is also about
    11 mm. This is battery-node bulk capacitance, not IC decoupling. Not a
    defect.
  - Also flagged; review before fabrication rather than move now:
    - C2/C3 crystal loads: 3.6/5.1 mm versus 1.2/2.6 mm in the reference.
      The crystal copper was pre-reviewed.
    - C7 VCORE: 5.8 mm versus 2.2 mm.
    - C4 LDO output: 5.1 mm versus 2.8 mm. C5 is a second output
      capacitor at 3.0 mm.
    - C15: 3.9 mm.
    - C25 (button debounce, not decoupling) and C26/C28 are expected
      placements.
- Remaining thin VHI copper to R3/R16 (10k/100k) is signal-level and
  acceptable at 0.15 mm. Only C1's path was a power-path concern.
- The pass 3 negative result means the remaining links are boxed in by
  frozen copper. Pass 4 diagnoses which frozen items, so that any change
  is an explicit, reviewed decision.

## Finishing pass 4 (Sol)

Pass 4 started from accepted best-8
`finish-pass2/07-rip-vbus/handbell.kicad_pcb`
(`e158ccd251325b63b8f03e1d3230dce9c6098b2702356208ec46d68465f9c826`).
No PCB candidate was written or accepted, so the exact best-8 board, DRC and
checks remain authoritative.

### C1 decoupling placement screen

`tools/move_c1_decoupling.py` screened four orthogonal rotations on 0.25 mm
and corrective 0.10 mm grids. A candidate had to put C1.1 within 3.0 mm of
U2.1, preserve zero courtyard overlap, avoid footprint/pad keep-outs and
contact guards, admit a clearance-aware 0.50 mm VHI route, and provide an
adjacent legal GND through-via plus short F trace. Frozen copper was never
eligible for removal.

No candidate passed the placement geometry, before routing or old-branch
removal. The three nearest useful 0.25 mm-grid candidates all rotate C1 to
90 degrees and are blocked by C4's courtyard:

| C1 centre (mm) | C1.1-to-U2.1 | Blocker |
|---|---:|---|
| 85.0132, 90.6921 | 1.1000 mm | C4 courtyard |
| 84.7632, 90.6921 | 1.1281 mm | C4 courtyard |
| 85.2632, 90.6921 | 1.1281 mm | C4 courtyard |

The 0.10 mm correction confirmed that still-closer positions overlap U2
itself. The required adjacency check on retained best-8 therefore remains
flagged at **12.95 mm** versus 1.45 mm in the Adafruit reference. C1, its old
0.15 mm VHI branch and all other copper remain byte-for-byte unchanged. A
coordinated C4/C1 placement decision is now required; this screen does not
authorize moving C4.

### Frozen endpoint enclosure diagnosis

`finish-pass4/enclosures.json` binds best-8 and frozen-board hashes and lists
the nearest frozen pad/track/via/rule-area witnesses for both ends of all
eight opens. Compact engineering dispositions:

| Open group | Representative frozen bounds | Smallest single change | Risk |
|---|---|---|---|
| POWER U5-Q2 | U5 V+/BOOST_FB cell; Q2 `~ENABLE` track `29cc6e59...` | Shift that enable escape about 0.3 mm and restore it | High: power selection/boost adjacency |
| VO+ J1-C22 | J1 B.VBAT `dbfe8896...`, F.VAMP `76a1d351...`; C22 GND/USB D- | Shift C22 about 0.5 mm toward J1 and replace local VO+/GND | High: BTL output current and USB adjacency |
| GND IC1.19 | XIN track `b239cecf...` and via `56beb5d8...` | Move the XIN escape about 0.3 mm and restore the clock route | Very high: crystal plus MCU return |
| GND GAIN0.1 | F.VBAT `0d6ce402...`, B.VBAT `2f49a8db...`, GAIN/VAMP pads | Move the nearest F.VBAT segment about 0.3 mm | High: source current beside amplifier gain |
| F.GND island | USB anchor X6.M3 `ec4d64cc...` on all layers | Revise the zone neck around X6.M3 and refill | Medium-high: USB mechanics/return |
| USBBOOT-D3 | IC1 +3V3 pad `c924f4a0...`; R18 I2S_MOD/VAMP pads | Move R18 about 0.3 mm and restore its fanout | Medium-high: amplifier mode/supply |
| SWDIO TP5-IC1 | IC1 SWCLK/RESET pads and VCORE track `1a7d010e...`; TP5 R13 pads | Reroute the VCORE escape about 0.3 mm | Very high: core PI versus recovery access |
| LRCLK TP14-U4 | USB D+ In2 `0d5ce84c...`; U4 GND `0858c33e...` and thermal group | Move TP14 beyond the prior 12 mm domain | Medium: preferable to USB/thermal reroute |

These are diagnosis options, not released changes. Pass 4 added no copper,
moved no component, changed no DRC/check result and spent no routing credit.

## Finishing pass 5 (Sol)

Pass 5 started from accepted best-8
`finish-pass2/07-rip-vbus/handbell.kicad_pcb`
(`e158ccd251325b63b8f03e1d3230dce9c6098b2702356208ec46d68465f9c826`).
No trial met the acceptance gates, so **no pass-5 PCB was accepted** and the
best-8 board, DRC and checks remain authoritative.

### Coordinated U2 regulator cell

The pre-edit attachment inventory found:

- C1: only removable VHI/GND routing.
- C4: removable +3V3 routing plus frozen pad-only GND stub
  `eaf8141b-3b2b-57f3-b759-95b87b6412d0`.
- C5: removable +3V3 routing; no frozen attached track.
- U2: removable VHI/+3V3, but frozen GND stub
  `0fc7f4e7-93d3-5057-98be-eb289f73920e` and EN stub
  `7c618612-5597-54c6-8341-424b52c21d93`.

`tools/move_u2_regulator_cell.py` screened four rotations on a 0.25 mm grid,
zero courtyard overlap, applicable keep-outs, direct 0.50 mm VHI and 0.25 mm
+3V3 links, and a GND connection no more than 1 mm to a new or existing via.
The initial fixed-U2/C5 search found 28 C1 candidates but zero C4 candidates.
The first correction allowed C5 to move; C4 and C5 each still had zero legal
candidates. The final correction also allowed short returns to existing GND
vias, with the same result. Dominant C4/C5 blockers were U2 courtyard
(1,242 samples), surrounding R17/R15/IC4/R14 courtyards, foreign copper and
103 otherwise placed candidates without a legal GND-via return.

The correction budget ended before exercising U2 movement. Moving U2 would
also require explicit replacement of the frozen GND and EN pad stubs listed
above. No part or copper changed. Final retained adjacency is:

| Capacitor | Served pin | Best-8 distance | Limit | Reference |
|---|---|---:|---:|---:|
| C1 | U2.1 VIN | 12.95 mm | 3.0 mm | 1.45 mm |
| C4 | U2.5 VOUT | 5.08 mm | 3.0 mm | 2.83 mm |
| C5 | U2.5 VOUT | 3.04 mm | unchanged part | 4.18 mm |

### F.GND island

`tools/remove_gnd_dead_island.py` changes only
`quote-native-F-GND-v1` to area-based island removal and refills natively.
The first trial exposed the KiCad squared-internal-unit API and was rejected.
The corrected file wrote `island_area_min 3`, but native DRC still reported
eight opens, retained the zone-to-zone open, and introduced ten
`isolated_copper` warnings. It was rejected; the zone and fills in best-8 are
unchanged.

### TP14 expanded relocation

The path-aware relocation domain was expanded to the whole practical board
(`--near 30`, F/B, contact guards retained). None of 1,144 legal placement
candidates had an actual route to U4.14. TP14 remains at
`(110.799999, 94.512211)` mm on F.Cu, 180 degrees.

Pass 5 added no copper, including no supply copper, moved no component,
changed no accepted DRC/check result and spent no routing credit. Trial
artifacts are retained under `multilayer-20261106/finish-pass5`.

### Lead disposition after finishing passes 3-5 (November 6, evening)

- Passes 3-5 (Sol, no spend) produced **no accepted candidate**. The best
  board stays `finish-pass2\07-rip-vbus` (e158ccd2, **8 opens**,
  rule-clean apart from the 71 inherited items).
- Evidence:
  - Test-point relocation: 176, 233 and then 1,144 legal positions, none
    routable.
  - The U2 regulator cell cannot be rebuilt at fixed U2: there are 28 legal
    C1 spots but 0 for C4 or C5, blocked by the U2, R14/R15/R17, IC4, TP16
    and Q2 courtyards.
  - Dead-island removal left the open and added isolated-copper warnings.
- Every remaining link is enclosed by frozen (reviewed critical) copper:
  clock/XIN, VCORE escape, boost cell, VBAT, the USB pair or C22 GND
  (`finish-pass4\enclosures.json`).
- **Stop rule reached:** three bounded passes with no measurable progress.
  Further gains need one of:
  - a wider local re-placement (U2 cell plus neighbours) that releases
    adjacent frozen copper, followed by one autorouter run and finishing;
  - a person with an interactive push-and-shove router.

  Either is an owner decision. Do not start more agent passes on the
  current placement.
- C1/C4 adjacency defects (12.95/5.08 mm against reference 1.45/2.83 mm)
  stay open review items, to be fixed in the same re-placement or by a
  person.

### Owner-approved local re-arrangement and one route (November 6, 15:22)

The owner explicitly selects the agent re-arrangement plus one DeepPCB
run. This is a new coordinated placement item, not another attempt on the
unchanged placement or a waiver of the previous rejected results.

- Preserve best-8 `finish-pass2\07-rip-vbus`, PCB SHA-256
  `e158ccd251325b63b8f03e1d3230dce9c6098b2702356208ec46d68465f9c826`.
  The authoritative four-layer PCB/project/schematic remain untouched.
- Prepare a separate U2 regulator-neighborhood layout, allowing a coherent
  movement of its input/output capacitors and directly obstructing local
  passives rather than repeatedly testing one capacitor against a fixed U2.
  Enumerate every changed pose, removed copper primitive and interrupted
  terminal/branch obligation. Keep the outline, stackup, interfaces,
  source-selection/protection, boost, clock and MCU/core blocks unchanged
  unless a further explicit engineering disposition identifies a necessary
  narrow change.
- Before cloud spend, demonstrate short real C1-to-VIN and output-capacitor
  paths, local ground access, native pose/pad agreement, and no new
  non-open DRC errors under the intended project rules. Distance alone is
  a placement screen, not decoupling or stability qualification. Increased
  opens from deliberately released fanout must be enumerated for restoration;
  they are allowed in the router input, not silently accepted in the result.
- Run at most one newly qualified input for 15 minutes, with a $7.50 ceiling
  at the observed $0.50/minute rate. Reconfirm the live rate before starting.
  Missing progress statistics are not evidence of a plateau; retain the
  duration cap and confirm a terminal service state.
- Preserve native output before processing. Merge against the revised
  protected baseline and compare the result against both that input and
  best-8. Do not use blanket `--narrow-net VHI VCORE` finishing. Confirm
  supply widths, complete guard clearance, local supply/return paths and
  restored obligations, not merely DRC counts.

No run has started at this authorization checkpoint. The freelancer brief
remains unposted. Preparation or validation failure stops spending rather
than submitting an unqualified board.

**Post-processing preparation:** the wrapper no longer passes blanket
`--narrow-net VHI VCORE`; it retains the gap router's approved supply widths
and explicitly uses 0.6 mm for the two speaker-output nets. Every native
child now has a hard timeout, retained stdout/stderr and a checked exit
status. Existing work folders and receipts are refused rather than erased;
intermediate boards remain available. Native DRC requests all track errors,
so its baseline must use the same reporting mode. Six software-only
controls passed: successful child, nonzero exit, timeout, reused receipt,
existing work folder and routing-width arguments. These controls do not
qualify a board or replace the returned-copper width/geometry audit.

### Rearrangement preparation stopped (November 6, 15:34)

The runtime-verified Sol executor exhausted its initial construction plus
two corrections before producing a qualified input. **No DeepPCB call or
paid run occurred.** Best-8 remains the retained candidate, not electrical
or fabrication acceptance. Lead rechecked its full `e158ccd2` hash and the
authoritative PCB/project/schematic `adc262b3`/`82132618`/`ec93cc6f`.

Private evidence is under `multilayer-20261106\regulator-rearrangement-20261106`:
`00-source`, `01-initial`, `02-correction1`, `03-correction2`, with native
boards, reports, DRC and supervised execution records. Final attempted PCB:
`1382dde8a23cce1badec7797f12b3166a1c3db443a85693eb38eb16e6139fd69`.
The unqualified preparation helpers are retained in `held-tools-lead`
(`inspect_regulator_neighborhood.py`, hash `00ea3f11`;
`prepare_regulator_rearrangement.py`, hash `4b195859`), not promoted as
reusable placement tooling.

The executor reports final poses in millimetres/degrees:

| Ref | Original x, y, angle | Attempted x, y, angle |
| --- | --- | --- |
| U2 | 84.063240, 93.992200, 180 | 84.063240, 94.042200, 180 |
| C1 | 95.965225, 98.708818, 90 | 86.400000, 93.200000, 0 |
| C4 | 84.006419, 90.585985, 0 | 84.167315, 91.570000, 90 |
| C5 | 83.821409, 97.491452, 0 | unchanged |

C1/VIN and C4/VOUT direct F branches measure 0.6683/2.9943 mm at
0.50/0.25 mm width. Nominal ground approaches measure 1.0000, 0.8485 and
0.3902 mm. These dimensions are **not accepted paths**: C1 ground conflicts
with R15.1 and R14.2; C4's supply connection crosses regulator VHI/GND
terminals, a retained GND via and the local return.

Matching all-track, all-severity DRC reports show 400 -> 440 violations,
8 -> 18 opens and unchanged 46 parity records. New reported hard classes
include four clearance, one hole-clearance, eight shorting-item and eight
solder-mask-bridge records; these counts are witnesses, not independent
root defects. The 71 inherited `items_not_allowed` records remain.

Twenty-three copper items were removed: the three released frozen U2
GND/EN and C4 GND stubs plus twenty router/agent fanout items on +3V3, SCL,
VHI, D13, I2S_BCLK and GND. The local replacements fail DRC and the
fanout restoration ledger is unfinished. Untouched-complement, filled
return, courtyard and mechanical qualification remain incomplete; absence
of an increased keepout count does not substitute for those checks.

**Lead disposition:** reject the attempted input and hold spending. The
final U2 move was only 0.05 mm. This result does not establish that the
authorized 5 mm coordinated neighborhood was adequately explored, nor
that moving R14/R15 is inherently forbidden: their poses were released,
but the executor had characterized their fanout as frozen (corrected below).
A future item needs a coherent cell
pose and exact support-fanout replacement contract before constructing
another board. Stop here rather than reset the exhausted correction budget
or ask the router to fix a shorted input. No human contact/payment,
fabrication release or promotion of the attempted board follows.

### Autopilot-continued whole-cell alternative (November 6, 15:35)

An autopilot continuation under the owner's standing 15:22 approval (not a
new owner message; corrected 16:15) resumes implementation after the
held result. The new item changes the geometry strategy; it does not restart
the exhausted direct-capacitor construction or spend on an unqualified input.

A saved-data executor follow-up corrects two important limitations:

- The five attached R14/R15 branches are best-8 router/agent additions,
  absent from the frozen copper set. Calling their fanout frozen was wrong;
  their enumerated replacement already fits the released scope.
- Earlier initial/correction-one trials moved U2 by (0, +4.5) mm; the last
  trial moved it by (0, +0.05) mm. No X-offset or rotated U2 was tried.
  Neither earlier construction provided a coherent noncrossing local cell.

The specific supporting branches are R14.1 +3V3 `6ffdc49f` and `a9bc8ccf`
(both joins mandatory), R14.2 SCL `268c67ad`, R15.1 +3V3 `549cec34` and
R15.2 SDA `4de761fe`. Their source pin identities and exact boundary
coordinates remain in the executor handoff. Full original primitive and
branch-contact accounting is required before any removal, not just this
short identifier list.

New private root: `multilayer-20261106\regulator-cell-outward-20261106`.
The executor screens one finite batch of connected-cell templates:
U2 offsets (1.5,0), (3,0), (4.5,0), (1.5,1.5), (3,1.5), (4.5,1.5) mm,
each at native 0/90/180/270-degree orientation. C1 and C4 face their
respective supply rows from outside the package, with short outward
ground connections and qualified through-via access. Supporting passive
movement remains within the existing allowance. Screen self-crossings,
fixed geometry and the retained complement after explicit proposed cuts;
do not reject a cell merely because eligible router copper or an allowed
movable support initially occupies it.

Only a screened coherent cell may become a native board trial. Local
capacitor connections/returns must close; enumerated remote distribution,
EN and supporting-fanout opens may wait for the router. This avoids
reintroducing shorts in an attempt to restore every remote connection
before autorouting. Existing frozen-release limits, mechanical/guard
requirements and source preservation stay unchanged.

Preparation stops by 15:57, with no new native child after 15:52 and at
most initial plus two corrections. Saved-fill ground attachment, exact
complement/open restoration and matching-mode non-open DRC comparison
still gate spending. The previously approved single run remains unspent
and capped at 15 minutes/$7.50; no second run is authorized.

### Outward-cell screen held (November 6, 15:42)

No candidate was constructed and no routing credit was spent. The executor
used all three permitted revisions: initial mistakenly treated C5/R3 as
fixed obstacles; correction one recognized all allowed movable supports;
correction two increased capacitor spacing to clear internal courtyards.
The final 24 offset/rotation combinations failed as follows:

| Executed-template rejection | Count |
| --- | --- |
| U2 courtyard versus fixed IC4 | 12 |
| C4 courtyard versus fixed C24 | 4 |
| Internal foreign-net collision | 5 |
| C4 courtyard versus fixed IC4 | 2 |
| C1 courtyard versus fixed IC4 | 1 |

This is an implementation-limited screen, not a demonstration that the
regulator cannot be rearranged. The helper used vectors from U2's origin
to its supply pins to orient the capacitors, rather than the package-row
normals. Its final five internal collision failures lack exact conflicting
primitive-pair records. The seven capacitor/fixed-part conflicts apply to
the executed capacitor poses, not every possible cell at those U2 origins.
Only the twelve U2/IC4 overlap reports directly reject those exact IC poses
under the courtyard model.

Each revision used one native load, reported at 2.484, 1.219 and 0.937
seconds, without timeout. No native full-board DRC, copper removal, new
serialized pose, or filled-return qualification occurred. Proposed 1.20 mm
supply links and 0.65 mm ground approaches are template dimensions only.
All five R14/R15 branch obligations and the protected stub set remain
untouched; there is no activated restoration ledger or qualified input.

Preserve `01-initial`, `02-correction1`, `03-correction2` and private
`screen_and_build.py`, SHA-256
`7b9bc5adcff2f9e98bf9c030c8f07fb8aa3eb0018055fb0ed9dea11bd23b442e`.
Lead rechecked best-8's unchanged full `e158ccd2` hash.
The executor is idle. Stop rather than silently spending the unused clock
budget on a fourth correction. A separately authorized next item would
repair and explicitly prove the noncrossing row-normal template first,
with exact failing pairs retained, before revisiting the five internally
rejected cases. Do not broaden the placement batch or spend on a shorted
input.

### Template-only repair resumed (November 6, 15:43)

The 15:42:53 autopilot continuation (owner's 15:22 approval; corrected
16:15) releases the narrow repair. Lead read the complete 231-line
executed helper before granting another execution. The review
establishes more than the previously suspected radial-cap problem:

- `side=(-o1[1],o1[0])` sends U2's GND return along its pin row, toward
  VIN, rather than outward normal to that row. Both cap orientation and
  the IC GND return must use the native package-row normal.
- The C4 released-stub UUID has `3b2` instead of `3b2b`; missing-ID
  assertions are required before relying on the release set.
- The layer list omits In4.Cu, so its prospective full-span via check
  is incomplete.
- The unexecuted builder projects F-only shapes onto every routing layer,
  omits other required shapes, and records net names rather than complete
  interrupted branch obligations. That builder remains unreleased.

A fresh private helper is screen-only. It must prove the internal
row-normal cell independently of board obstacles, reject an actual
old-lateral-return mutation with named conflicting shapes, and retain
native orientation/orthogonality witnesses. Only after that positive
template may it examine the exact five saved internal-failure cases.
All six layers, exact source/release identities and support-placement
limitations must be explicit. It cannot save a board or invoke the
old construction tail. Code preparation ends by 15:51; complete lead
review precedes one corrected native screen, with no automatic retry.
Source and the one unspent paid-run allowance remain unchanged.

### Template v2 held before execution (November 6, 16:15)

No native screen, PCB or routing credit has been used in this item.
Lead review rejected the initial revision, `screen_row_normal_only.py`
(SHA-256 `0c4e094c3f5b90de…`), before execution:

| Item | Defect | Required correction |
| --- | --- | --- |
| A | Radial "outward" test; U2.5's 0.95 mm row offset gives about -0.81 | Signed side test `dot(p5-centre, normal) < 0` |
| B | Assertions could precede saved evidence | Write both control records and a HELD report first; exit nonzero |
| C | No hole, via-rule, contact-guard or edge checks | Add them; otherwise GEOMETRY_QUALIFICATION_PENDING, never a pass; F-footprint courtyards only |
| D | 0.65 mm U2 ground approach overlaps U2's own pad | Lead specified 1.00 mm; record via gaps to every SMT pad; negative control must name its pair |
| E | Implied full qualification | Support holds are permitted outcomes; no qualified-board claim |
| F | Incomplete records | Save track endpoints/widths and via centre/drill/diameter |

Correction one, `screen_row_normal_only_v2.py` (492 lines, SHA-256
`bdf144f3b746b94c…`), passed only a supervised compile. Lead static
geometry at the source pose shows its own positive control must fail.
C1 pad 1, 1.20 mm along the row normal from U2.1, spans X
84.388-85.638 mm; the 0.65 mm U2 ground via, 1.00 mm from U2.2, is
centred at X 84.063. Its annulus touches C1.1 (zero gap) and the 0.30 mm
ground track passes 0.175 mm from it. The 1.00 mm figure was the lead's
own item-D template choice: the 15:22 contract requires short real
C1-to-VIN/output-capacitor paths and local ground access, but sets no
1.00 mm limit. No native screen was released for a template whose healthy
case cannot pass.

The 15:51 preparation deadline passed without an executable revision,
and the previous executor handle expired. Replacement executor
`c4511095` is runtime-verified GPT-5.6 Sol/medium from its configuration
event. This checkpoint splits the remaining work rather than silently
extending the old window.

Correction two (v3) is the final allowed revision. It keeps every v2
check and revises only the lead template and gates:

- C1 pad 1 = U2.1 + 1.20 mm row normal + 0.30 mm along the row away
  from U2.2; C4 is unchanged.
- U2 ground via = U2.2 + 1.20 mm row normal; C1/C4 ground vias stay
  1.00 mm beyond their pad 2.
- Any via-to-SMT-pad gap below 0.20 mm, on any net, is an internal
  reject; same-net gaps to fixed and support pads are also checked.
- Rule areas include footprint-owned areas as well as board zones.
- The negative mutation changes only the via direction, toward VIN at
  1.20 mm, and must reject with a named U2 ground-versus-U2.1 pair.
- Control failures write explicit held report states and exit nonzero.

Lead hand calculation at the source pose gives at least 0.275 mm between
the ground via and U2.2, 0.300 mm to C1.1, 0.475 mm between ground track
and C1.1, and 0.638 mm between the 0.50 mm VIN track and the via.

Window: code by 16:25; full lead review and an independent static
positive-control check by 16:31; one supervised native screen (120 s
limit) started by 16:33; disposition by 16:39. No further correction.
A GEOMETRY_QUALIFICATION_PENDING case still needs a construction contract,
restoration ledger, saved-fill ground proof and matching-mode DRC before
the one capped run. Support holds or rejections stop for an owner
decision. Best-8, source and the unspent run allowance remain unchanged.

### Template v3 screen held on witness tolerance (November 6, 16:28)

The lead's independent static check (pure Python and Shapely, no pcbnew;
16:25:56, exit 0) passed v3's source-pose positive control. Fallback-box
separations are 0.30 mm for U2-C1 and U2-C4. Minimum foreign copper gap
is 0.30 mm (C1.1 to the U2 ground via). Minimum via-to-pad gap is
0.275 mm (U2.2, same net). Drills clear and the negative named pair is
present. The board text shows U2, C1 and C4 have no courtyard graphics,
user-layer graphics or footprint zones. The screen's courtyard test
(`tools/move_cluster.py` `footprint_area`) therefore falls back to the
unexpanded `GetBoundingBox(False)` box that the check emulated.
`FOOTPRINT.Zones()` exists in the installed KiCad 10 `pcbnew.py`.

One supervised native screen (executor `c4511095`, Sol/medium) ran at
16:28:13-16:28:14 local: 1.125 s, no timeout, supervisor and child exit 2.
Report `row-normal-v3-screen-report.json` (SHA-256 `b12d822b…`) has
status HELD_C1_WITNESS_FAILED.

| Gate | Result |
| --- | --- |
| Positive control | Passed: zero copper, courtyard, drill and via-pad findings; U2.2 via gap 0.275 mm |
| Negative control | Rejected: four copper findings, including named pair U2.1 (VHI) to U2 ground track (GND) at 0 mm, plus one via-pad intersection |
| Release identities | All three frozen releases and five support branches found; none missing |
| Layers | All six copper layers |
| C1 witness | Normal 1.200001 mm, row 0.300000 mm, tolerance 0.000001 mm |

Line 323 of the helper asserts `abs(normal - 1.20) <= 1e-6` mm. The
installed KiCad 10 `pcbnew.FromMM` truncates (`int(mm * 1e6)`) rather
than rounding, so `SetPosition(VECTOR2I(FromMM(x), FromMM(y)))` placed C1
at y 90.592099 instead of 90.5921 (and C4 at x 85.013239 instead of
85.01324). C1.1 therefore lands 1 nm farther from U2.1 along the normal.
This is a helper tolerance defect, not a geometric failure: both controls
had already passed. The lead's static review did not compare assertion
tolerances with coordinate conversion.

The screen therefore exited before the fixed-obstacle stage. None of
the five cases, and no rule-area inventory, was evaluated. No PCB was
constructed, no copper removed and no credit spent. The receipt binds
BOARD `e158ccd2…c826`, FROZEN `b82f2fe3…` and v3 `8802e453…`; the lead
re-hashed all three unchanged at 16:29 and 16:32. Stderr contains only
duplicate wx image-handler warnings.

v3 was this item's final permitted revision, so no correction or rerun
follows. Preserve v1-v3, `static_check_v3_template.py` and all receipts.
The single approved run (15 minutes/$7.50) remains unspent.

The next step requires an owner choice. One option is to authorize a
tolerance-only change (0.000001 to 0.001 mm on lines 323-324, no other
edit) and one native screen. A GEOMETRY_QUALIFICATION_PENDING case would
still need the construction contract, restoration ledger, saved-fill
ground proof and matching-mode DRC before the run. The alternative is to
stop the rearrangement and keep best-8, with C1/U2 decoupling as a
documented finishing requirement (already item 2 of the finishing brief).

### Item 4: autonomous tolerance-only v4 screen (November 6, 16:37)

At about 16:36 the lead offered the owner the choice above through the
app's question prompt. The app replied that the owner was unavailable and
asked the agent to work autonomously. At about 16:37 the lead therefore
selected the tolerance-only option under the owner's 15:22 approval
(rearrangement plus one run). This is a lead decision recorded as such,
not an owner selection. It is a new bounded item: an initial attempt plus
at most two corrections, each one supervised read-only native screen of
at most 120 s. No board writes, copper removal or spend.

v4 is a copy of v3 with these edits only:

- C1 witness tolerance on lines 323-324 changed from 0.000001 to 0.001 mm,
  the same 1 µm tolerance line 195 already uses.
- Version and provenance labels: `v4`, the v3 SHA-256, and the version in
  held reports.
- One diagnostic-only addition beyond the 16:32 proposal: counts of empty
  fixed-obstacle, SMT-pad and rule-area shapes in the final report. Shapely
  returns NaN for a distance to empty geometry, and `NaN < limit` is false,
  so an empty obstacle would be skipped silently. The counts make that
  measurable. They change no status.

Lines 192-193 keep their 0.000001 tolerances. The lead emulated the
installed `FromMM` (`int(mm * 1e6)`) for all five U2 case poses (source
84.06324, 93.9922 plus the case offsets). Every pose lands exactly on a
nanometre, so the row witnesses remain valid there.

### Item 4 outcome: every pose rejected, rearrangement stopped (November 6, 16:47)

The lead diffed v4 (SHA-256 `7a90cb8d…a4bf`) against v3 and found only
the edits listed above. A supervised `py_compile` passed (exit 0,
0.125 s). One supervised native screen (executor `c4511095`, Sol/medium,
120 s limit) ran at 16:44:06-16:44:07 local: 1.328 s, no timeout,
supervisor and child exit 0. Report `row-normal-v4-screen-report.json`
(SHA-256 `b59fdc2c…6693`) has status SCREEN_ONLY. No correction was used.

| Gate | Result |
| --- | --- |
| Positive control | Passed; C1 witness 1.200001 mm, now within the 0.001 mm tolerance |
| Negative control | Rejected; named pair U2.1 (VHI) to the U2 ground track (GND) at 0 mm |
| Release identities | Three frozen releases and five support branches present and unique |
| Empty shapes | Zero on all six copper layers, zero fixed SMT pads, zero rule areas |

All five U2/C1/C4 poses are FIXED_REJECT. The lead checked every
external hit: none is same-net. Each is a foreign-net overlap, or a gap
below the 0.2 mm requirement, against copper or pads that stay fixed:

| U2 move (mm), rotation | Decisive conflicts |
| --- | --- |
| +1.5, 0; 0° | C1.2 and its ground track on frozen POWER (0 mm); C1 ground via on frozen B.Cu `/CELL_NEG` (0 mm); C4 ground track and via on TP3 (USBBOOT) (0 mm); U2 and C1 ground vias in the BT2 contact guard |
| +1.5, 0; 180° | C4.2 on four frozen POWER objects (0 mm); C4 ground via on `/CELL_NEG` (0 mm) and in the BT2 contact guard |
| +1.5, +1.5; 0° | U2.5 (+3V3) on frozen GND (0 mm); C1 ground via on `/CELL_NEG` (0 mm); C4 ground via on a frozen hole (0 mm); four further gaps of 0.126-0.156 mm; two vias in the BT2 contact guard |
| +1.5, +1.5; 90° | C4.2 and its ground track on frozen POWER (0 mm); U2 and C1 ground vias in the BT2 contact guard |
| +1.5, +1.5; 180° | U2.3 (EN) on frozen GND (0 mm); C4.2 on frozen POWER (0 mm); C4 ground via on `/CELL_NEG` and frozen `~{ENABLE}` (0 mm); C4.1 (+3V3) 0.124-0.158 mm from POWER; via in the BT2 contact guard |

Every case also places at least one ordinary ground via inside
`CONTACT_METAL_GUARD_BT2.base.3`, whose bounding box starts at y 94.185
mm, only 0.19 mm below U2's source centre (y 93.992 mm). Four cases put
a through ground via on frozen B.Cu `/CELL_NEG` copper: a short there
would bypass the cell protection, so these rejections are
safety-relevant, not marginal. Each case also holds on three to five
supporting parts (C5, R14, R15, R17, Q2, TP16) that would need their own
moved-support contracts. In the screened directions the U2 cell is
bounded by frozen POWER, GND and `~{ENABLE}` copper, the BT2 contact
guard below it and `/CELL_NEG` on B.Cu. That is consistent with
finishing passes 3-5: no screened local move places C1 and C4 beside U2
without releasing frozen copper. It does not prove that no pose exists.

The lead re-hashed BOARD `e158ccd2…c826`, FROZEN `b82f2fe3…`, v4 and its
report at 16:47, all unchanged. No PCB was constructed, no copper removed
and no credit spent. Preserve v1-v4, all reports and all receipts.

Disposition (lead, under the 15:22 approval): stop the rearrangement and
keep best-8. The single approved run stays unspent, because the only
input available is the unchanged placement and the approval excludes an
unchanged-placement retry. Items 1-4 produced no qualified geometry, so
the stop rule applies; running the same screen again is not an option.
C1/U2 and C4/U2 decoupling remain item 2 of the finishing brief.

At that November 6 checkpoint, any further step required an owner choice:

1. Wider re-placement. Release the frozen POWER, GND and `~{ENABLE}`
   objects that the report identifies, and TP3 if needed, with their
   replacement duties. Keep `/CELL_NEG` intact and move the cell, or at
   least its ground vias, clear of the BT2 contact guard and that copper.
   Then requalify the geometry and spend the one run. This is a larger,
   new scope: the screen above shows the cell's neighbours, not their
   replacement routes.
2. A human finisher with `docs/finishing-job-brief-2026-11.md`, which
   already includes the C1/C4 moves.
3. Accept best-8 as the agent result and stop.

### November 7 wider U2 replacement trial held

The owner approved a wider local U2/C1/C4 re-placement attempt, with the
previously approved single DeepPCB run still capped at 15 minutes/$7.50.
The run is conditional on a fully qualified private input; this item did
not authorize uploading or routing an unqualified candidate.

Sol's one isolated construction attempt used the immutable best-8 source
`e158ccd251325b63b8f03e1d3230dce9c6098b2702356208ec46d68465f9c826` and
saved evidence under the private bakeoff root at
`multilayer-20261107\regulator-wide-replacement`. It moved U2 from
(84.06324, 93.99220, 180) to (82.06324, 93.29220, 180), C1 to
(83.01324, 91.09210, 90), C4 to (83.01324, 95.49230, -90), and R3 to
(80.00000, 94.00000, 0). It removed only the three previously released
U2/C4 pad stubs and added nine F.Cu tracks plus two ordinary through-vias.
The additional nearby POWER and `~{ENABLE}` segments eligible under this
local scope remained unchanged.

Native KiCad 10.0.6 all-track/all-severity DRC rejected the candidate:

| Finding | Best-8 | Trial |
|---|---:|---:|
| Unconnected records | 8 | 11 |
| Shorting items | 0 | 45 |
| Clearance | 0 | 18 |
| Hole clearance | 0 | 23 |
| Copper-edge clearance | 0 | 3 |
| Tracks crossing | 0 | 4 |
| Dangling tracks | 6 | 10 |
| Items not allowed | 71 | 72 |

The reported shorts include the new EN routes colliding with existing
VHI/AMP_MUTE copper and GND/EN crossings. These indicate that this specific
cell pose and local route pattern are not usable. They do not prove all
broader poses fail. The candidate stopped at the first native legality
gate: full six-layer via-span/contact-guard, CELL_NEG, private-return,
plane, untouched-complement and endpoint-restoration checks did not run.
The candidate was never a qualified router input.

Preserve `HELD-report.json`, `build-report.json`, the failed candidate and
its DRC. Best-8 was independently re-hashed unchanged
(`e158ccd2…c826`); frozen remains `b82f2fe3…`. No DeepPCB upload/run or
spend occurred. The run remains unspent and must not be used on this failed
candidate. A different cell/return-transition geometry must be engineered
and qualified first, or the owner may choose the prepared human-finisher
brief or accept best-8. Do not retry this pose or infer physical impossibility.

The new private evidence was captured in the encrypted off-machine restic
snapshot `8358a65d` (4,373 files, 628.122 MiB). A no-cache
`check --read-data` found no errors in both snapshots/seven packs; a complete
restore verified all 4,373 SHA-256 entries against the saved manifest and
the current evidence root. Best-8 and frozen board hashes matched. Private
receipts and manifests are under `%USERPROFILE%\.digital-handbell\backup`;
no credentials are in this repository. Backup is still one-time, not scheduled.

### November 7 C1/C4 capacitor move paused during preparation

The owner approved a narrower strategy: keep U2 where it is and move only
its two capacitors. C1 (the VHI input capacitor, now about 12 mm away on
0.15 mm copper) would sit north of U2 beside U2.1, in C4's old area. C4
(the +3V3 output capacitor) would sit beside U2.5. The existing capped
DeepPCB run (at most 15 minutes / $7.50) may be used only if the candidate
passes every input gate. The owner also waived the Sol-only executor rule
for that session only; reconfirm executor choice when resuming.

The owner paused the work before any candidate existed. Read-only
preparation is saved in the private
`multilayer-20261107\regulator-north-ground-transition` folder (27 files,
4.3 MiB): a best-8 copy that re-hashes `e158ccd2…`, baseline DRC, a window
inventory with full UUIDs and frozen flags, layer renders, and a KiCad
10.0.6 API probe. After refill, the probe reproduces the 8 unconnected
items. Findings so far:

- With our strict screening margins, C1 at 90 degrees has a narrow window,
  about cy 90.71-90.74 for cx 85.15-85.94, bounded by TP3, U2.1/U2.2 and R15.
  Relaxing the 0.15 mm same-net pad spacing widens it to about cy 90.89.
  These are bounding-box estimates that native shapes must confirm.
- C1 needs a 0.3 mm GND stub from frozen GND track `eaf8141b`, whose end
  now sits on the C4.2 pad at (84.9064, 90.586). Its VHI pad should overlap
  feed `9a737d67`; check natively.
- C4's south-east site is clear of the frozen POWER copper, which starts at
  R17.1 (y about 98.5). No vias exist in that window.
- C1, C4, C5 and U2 have no courtyards, so moving them cannot create
  courtyard-overlap findings. Moved reference text needs relocation or hiding
  and must be reported as a silk-only change.
- Rule areas restrict only B.Cu and In1/In4, so F.Cu part moves are not
  blocked by them. No new vias are planned.

No candidate board, native DRC, DeepPCB upload or spend has occurred.
Best-8 and frozen (`b82f2fe3…`) were re-hashed unchanged at the pause. The
preparation folder is not yet in a restic snapshot; it can be regenerated
from best-8. Next item: write and run the read-only pose/stub planner
(`plan_candidate.py` in that folder), then native DRC and the standard
gates on at most the best few variants. Hold without spending if no pose
qualifies.

### November 8 C1/C4 move built; DeepPCB run gave no gain

The owner approved up to 60 DeepPCB minutes (about $30): move C1/C4, try
TP5/TP14 relocation, then route whatever passes the gates. All work is in
the private `regulator-north-ground-transition\plan` folder.

- **C1/C4 candidate `plan\v1`** (`plan_candidate.py`): C1 at (85.55, 90.76)
  rot 90, C4 at (86.40, 96.75) rot 0; old long chains pruned, short stubs
  added. Native DRC on a copy (`plan\v1-drc`): no new copper, clearance,
  short, hole or courtyard findings; opens 8 -> 8 (USBBOOT reports a
  different witness on the same open). Cap adjacency improves C1->U2.1 from
  12.95 to 1.16 mm and C4->U2.5 from 5.08 to 1.54 mm. The standard check
  fails only on silk: silk_over_copper 94 -> 97 (R15/TP3/R17/C5 reference
  text over the new pads; C1/C4 references hidden, text_height 72 -> 70).
  This is a cosmetic waiver, not a routing gain.
- **TP5/TP14 relocation:** a shapely free-space screen (`plan\tp_screen.py`)
  finds no legal 1.5 mm pad position within 6 mm of the SWDIO or I2S_LRCLK
  targets at 0.16-0.20 mm clearance; about 99% of grid points hit copper.
  Smaller-pad hits fall under IC1's body (unreliable imported courtyards)
  and were discarded. Not attempted further.
- **DeepPCB:** input `plan\v1-deeppcb` (v1 minus the two plane no-track
  areas, run 4's raised-clearance project), board
  `7f4cd69b-5f08-4d41-814b-d8e1ed1cb8b0`, CurrentProtectedWiring, one
  15-minute run (14:09-14:24, 15.02 burned minutes at $0.50/min, about
  $7.50). DeepPCB's own count went 5 -> 6 unconnected air wires; its last
  revision came at about 2 minutes. The standard post-processing
  (`plan\v1-post`) ends at 8 -> 8 opens with no new copper kept. No second
  run: repeating the same placement is not justified.

Best-8 (`e158ccd2…`) and frozen (`b82f2fe3…`) re-hash unchanged. The v1
candidate is retained as an electrical-quality improvement (decoupling
distance) with no open-count change; it is not promoted. Remaining options:
accept v1 or best-8 and close the 8 opens with the human-finisher brief
(`docs/finishing-job-brief-2026-11.md`), or a larger placement redesign.

### November 8, 15:01: silk waiver approved; best-8-c1c4 becomes the finisher base

The owner approved the silk_over_copper waiver ("sounds fine to me").
Root re-checked the copied `plan\v1-drc` board (`2e8e16bf…`) before
promoting it:

- **Silk detail:** four new findings are the R15, R17, TP3 and C5
  reference labels over C1/C4 pads; one old finding (C1's reference over
  TP5) cleared. Fabricators clip silk from pads, so there is no electrical
  effect. Labels may be nudged during finishing.
- **Copper diff against best-8:** removes the old 0.15 mm VHI chain and
  via to C1 (12 items) and the long +3V3 In3/F detour and via to C4
  (5 items), plus one 0.15 mm GND stub. Adds one 1.008 mm +3V3 stub
  (0.25 mm) and one GND stub (0.30 mm). USBBOOT copper is identical; only
  KiCad's open witness changed.
- **Standard check against `6c-frozen-tp`** with `--allow-move C1 C4`:
  opens 86 -> 8, no lost frozen copper, only C1/C4 moved. track_dangling
  4 -> 6 and via_dangling 0 -> 1 are the findings already present in best-8;
  silk_over_copper 94 -> 97 is the waived item.

Promoted copy: private `multilayer-20261108\best-8-c1c4` (board, project,
schematic, DRC, check, cap-adjacency reports, `waiver-silk.json`,
`SHA256SUMS`). New finisher bundle `multilayer-20261108\finishing-job-bundle-c1c4`
and its zip (`e9aece5d…`). Its brief drops the capacitor-move deliverable.
Best-8 (`e158ccd2…`), frozen (`b82f2fe3…`) and the November 6 bundle are
kept unchanged as fallbacks. The brief is still not posted; posting and any
payment remain owner actions.

### November 8: bounded functional-group strategy review

The owner prefers time-boxed agent-led design to hiring a finisher and
accepts awkward test-point access. Three parallel read-only reviews covered
debug/boot (three opens), power/audio (three), and ground/reference (two).
This is strategy selection, not permission to implement all proposals.
No native KiCad operation, board change, router submission or spend occurred.
Current `best-8-c1c4` (`2e8e16bf`), historical best-8 (`e158ccd2`) and frozen
(`b82f2fe3`) were hash-bound before the review.

**Shared tooling finding:** the default pair mode of
`route_gaps.py:96-112,290-301` and `reroute_with_ripup.py:96-105,260-277`
select the DRC witness objects, not
every possible attachment on their connected groups. A zone is approximated
by a 0.25 mm disk at its reported point, not the actual filled island.
Failure of these searches does not exhaust group-to-group routing.
This does not invalidate every prior search: `route_gaps.py:305-324` already
has `--nearest-own-copper`, expanding the goal to outside same-net copper
on each layer, and that mode was tried for GAIN0. Dedicated ground stitching
also exists. Reuse their saved evidence first; the review does not justify
an unchanged retry or a new general group-routing implementation.
The same net name alone does not establish membership in the same connected
group, and a zone UUID can identify multiple disconnected fill islands.

| Obligation | Preferred design direction | Escalation only if needed |
| --- | --- | --- |
| SWDIO / TP5 | Preserve SWD recovery; screen a smaller, inconvenient but physically reachable service land with a short dogleg or legal off-pad transition, using actual connected-group geometry. | A precisely bounded neighboring escape replacement, with all VCORE/reset/clock duties preserved. |
| I2S_LRCLK / TP14 | Establish that MCU-to-amplifier clock connectivity is intact; move/resize only the diagnostic tap onto an accessible part of that connected group. | Omitting this diagnostic pad would need a separate explicit schematic decision, not a claim of routing improvement. |
| USBBOOT / D3.C | Keep the recovery circuit; inspect all attachment points on its disconnected groups before choosing a local escape replacement. | A coordinated diode/support-cell move, preserving every terminal, not deleting the boot branch. |
| POWER / U5.2--Q2.1 | Treat this as boost-enable control, not load-current copper. First try legal group attachments without changing the boost cell. | Review the local Q2 enable escape as a specific replacement, not a release of the boost power/feedback loop. |
| VO+ / J1.1--C22.1 | Preserve speaker-output/filter duties and established width; inspect complete copper groups. | Move C22 with BOTH its VO+ and GND connections if a short local cell can be qualified without disturbing USB, VBAT or VAMP. |
| GND / GAIN0.1 | Ordinary main-GND attachment unless an actual private-return duty is found; inspect reachable GND and possible jumper orientation before touching power copper. | A bounded gain-jumper relocation; moving frozen VBAT is a higher-risk last option, not the first choice. |
| GND / IC1.19 TESTEN | A mandatory tie-down, not an optional diagnostic pad. Examine legal off-pad ground access to actual main GND. | A short, explicitly reviewed oscillator-escape replacement; preserve crystal geometry and return duties. |
| F.Cu GND island near X6 | Identify the real filled polygon and every attached pad/reference duty, then consider a legal stitch or local neck repair. | Never delete the island as cosmetic copper without proving it carries no functional or reference obligation. |

**Lead dispositions and evidence limits:** the workers proposed strategies,
not screened coordinates. No new land/via site is accepted. Previously
rejected TP14 sites under an IC remain rejected; awkward access does not
mean physically inaccessible. A DRC pair is not a two-terminal net census.
The debug worker corrected its omitted MCU LRCLK terminal and withdrew
an inferred R18-to-USBBOOT connection: R18 was named as an obstacle, not
a terminal. Its text scan did not certify an exhaustive terminal list or
connected-group membership, so neither claim is accepted from that scan.
Likewise, X6 having ground pads does not prove which disconnected polygon
contains them; the worker's inferred island-membership claim is not accepted.
USB signal-ground pins and connector shield/anchor duties are distinct.
No via-at-pad proposal or new special process is released.
POWER and its neighboring `~ENABLE` obstruction are different nets.
The older brief's VO+ "0.6 mm" denotes the trial **track width**, not the
gap distance (the reported pad centers are approximately 8.9 mm apart).
Sub-millimeter part/track moves remain hypotheses, not clearance evidence.

**Proposed next budget:** three sequential 15-minute gates, not another
parallel board-editing exercise. First reuse saved connectivity/fill evidence
to produce actual group boundaries, mandatory terminal duties and a small
list of accessible service-land/ground-attachment candidates. Stop if that
concrete output is unavailable; do not build a new general routing framework.
Second, screen and construct only the best low-disturbance service/ground
candidate on one private copy. Third, restore and validate that complete
candidate, or use the remaining time on one independently justified local
cell after a successful checkpoint. Initial plus two corrections within
each timebox, no automatic budget reset. Frozen/control/clock releases
require an exact reviewed replacement contract before construction.

Acceptance must prove named new connections and unchanged prior connectivity,
not merely a reduced DRC count. Compare all copper outside the enumerated
release: `check_routing_result.py:179-180` exempts whole net names under
`--allow-changed-nets`, which cannot substitute for that complement proof.
Keep C1/C4 adjacency, plane roles, private returns, contact exclusions and
CELL_NEG isolation. No DeepPCB run until a changed, qualified problem has
legal endpoints/corridors that the previous run did not have.

Reduced test-point convenience is compatible with this direction, but zero
opens alone cannot promise reliable operation. Retain the focused electrical
and mechanical release review plus a small first-board bring-up covering
power/current/temperature, USB/programming/recovery and audio operation.
An extensive production-test fixture is not a prerequisite for this prototype.

## November 8 closure gates (autopilot, no spend)

**Gate 1, connected-group census** (private `multilayer-20261108\closure-gates\gate1`,
`group_census.py`/`groups.json`, on unchanged best-8-c1c4 `2e8e16bf`):
SWDIO IC1.25 and TP5 are each alone, with no SWDIO copper at all; I2S_LRCLK
IC1.29-U4.14 is connected and only TP14 is isolated; POWER U5.2, USBBOOT D3.C
and VO+ J1.1 (apart from the F-only C22.1/FB1.2 group) are isolated. Three GND
singletons: C7.1 together with F zone island #11 (2.443 mm²), GAIN0.1 and
IC1.19 (TESTEN). **Correction:** the "X6-area island" in earlier notes is
C7.1's (VCORE decoupling) ground pad, not an X6 feature.

**Gate 2, stub plus new via to In1 GND** (`gate2\gnd_stub_via_screen.py`, read-only):
0.5/0.3 mm via, annulus inside In1 fill (0.05 mm inset), clear of foreign
copper on all layers and via keep-outs; 0.2 mm F stub, straight then
two-segment, within 2.5 mm. **No legal site** for any of the three.
C7.1 has zero via-legal area. GAIN0.1's only via region (x101.9-102.6,
y108.0-109.7, 0.64 mm²) is separated from the pad by a VBAT F track at
x101.35 (y107.2-109.8). IC1.19's region (0.04 mm², y≈84.35) is separated
by the D13 F track at y85.3 and the adjacent QFN pins; XIN's via/stub
blocks the west side. These are finite-screen results, not impossibility.

Gate 3 (refill/DRC/complement) was not reached. No board edit, save, DRC or
DeepPCB spend. These finite GND screens do not establish that all eight opens
require moving existing copper or hiring a finisher. A reviewed local
replacement is a proposed next approach, not the only physically possible one.

## November 8, 17:36 local copper-replacement authorization

The owner says, "I'm ok with moving existing copper." The first bounded item
is a local VBAT detour beside GAIN0, with exact primitives and all attachment
duties reviewed before construction. Work is on private derivatives of
best-8-c1c4 `2e8e16bf`, never the base itself. Preserve source-current widths,
all existing branches, component poses, plane roles, contact exclusions,
private returns, CELL_NEG isolation and mandatory process vias. No general
VBAT release, new supply-layer transition or DeepPCB spend is authorized by
this item. D13/XIN/clock changes are outside this first trial.

The Sol/medium executor passed a read-only runtime probe, with the parent
verifying actual configured model/effort and first-dispatched-model events.
The contract checkpoint is 17:42, no new native child after 17:48, and the
engineering stop is 17:51. Initial plus two corrections is the total allowance,
with hard child-process timeouts and preserved executed revisions/results.
Acceptance requires the named GAIN0 join, restored VBAT duties, no prior
connected-group split, exact unchanged-complement preservation and no new
native DRC defects; a lower open count alone is insufficient.

**Outcome: contract held; no construction.** The executor identified eight
affected 0.1778 mm F.Cu primitives between (98.2, 107.15) and (101.55, 109.8),
including frozen `0d6ce402-...`. Five additional source-side track/interior
contacts, including via `0ba3129d-...`, prevent treating this as a simple
two-endpoint chain. VBAT's connected pad group includes BT1.1, C20.1,
CHG_EN0.2, Q3.3, R25.1 and TP11.P$1.

The finite proposal screen considered three VBAT detours and five GND links
(15 pairs); none passed. Each VBAT detour conflicts with fixed +3V3 copper.
Only GND proposal G2 reached saved main F.Cu GND fill, and it conflicts with
the closest proposed VBAT detours. This is a finite proposal rejection, not
proof that GAIN0 cannot be connected after a different coordinated change.
No PCB mutation/save, refill, DRC, cloud upload or paid run occurred.
The screen retained the existing 0.1778 mm VBAT width, not 0.8-1.0 mm.
The closest reported clearance miss is a **0.010096 mm deficit**:
0.189904 mm measured gap versus 0.200000 mm required, not a 0.010096 mm gap.
The five source-side contacts are four tracks and one via, not pads.

**Lead dispositions:** the existing narrow width is not proof of its local
current duty. Before a replacement is qualified, distinguish load-current
copper from a signal-level tap using the actual branch connections; do not
blindly preserve or widen an entire supply net. The seven adjoining segments'
frozen/router provenance is unresolved, but that is not an authorization
blocker: this item expressly allowed specific replacements of either. The
geometric rejection stands independently. Do not retry these three detours
unchanged or silently extend the release to +3V3.

Private evidence is under `multilayer-20261108\gain0-vbat-replacement-1736`:
`stage1-contract.json` (final clarified `cee49fce...`; initial report hash
`82674719...` is superseded), `local-inventory.json` (`ba872d3c...`),
`vbat-group.json` (`f2accf7a...`) and `proposal-screen.json` (`0030c246...`).
The initial inventory timed out at its 90-second limit; a corrected read-only
inventory completed and the separate finite proposal screen returned no pair.
The executor reports 17 PowerShell children, including four native board-load
children, not three individual executions; one non-native CLI-path lookup
also failed. The initial report arrived at 17:42:33.470, missing the contract
checkpoint by 33.470 seconds. No item process remains live. Raw reports were
retained through the report-only clarification; no further native run followed.
Best-8-c1c4 remains unchanged
at eight opens. Next engineering work needs the local current/branch contract
and a genuinely different coordinated corridor, not more router minutes or
another request for general permission to move copper.

Private evidence backup: restic snapshot `333cc7ba`, parent `42bceb0a`;
4,555 files, 658.338 MiB, six new files. Backup exited successfully; integrity
check and restore were not repeated for this snapshot.

## November 8, 17:52 service-pad closure direction

The owner requests agent-driven forward progress; hiring a human finisher
is not an available dependency. The lead selects TP14 before another
power-copper replacement. The existing IC1.29-U4.14 LRCLK connection stays
intact; only its disconnected diagnostic pad needs attachment.

The read-only Sol/medium probe identifies a materially different search.
TP14 currently has a 1.5 mm circular pad. The earlier smaller-pad screen
used three selected anchor neighbourhoods within 6 mm, not the complete
61-member connected LRCLK group or every accessible F/B track/via surface.
Its smaller-pad hits under IC1 remain rejected. The new finite screen uses
existing connected track samples/via centres and 1.0, 0.8 or 0.6 mm bare
service lands. This is not a repeat of the 1,144 unchanged-pad relocation
poses or a new free-space router.

After verifying actual Sol/medium runtime metadata, the lead releases a
private TP14-only placement/side/pad-size derivative, including matching
mask/courtyard/Fab/silk geometry. All existing tracks/vias and other parts
remain unchanged. Preserve pad/footprint identities, net and schematic
binding; no paste, fitted component, new hole or special via process.
Real body/contact exclusion and accessible probing space are mandatory.
Native DRC, exact complement and existing-group preservation gate any
promotion; a smaller pad or lower open count alone is not acceptance.
The item stops engineering at 18:07, with no new native child after 18:04
and a report checkpoint at 18:08. No DeepPCB spend is released.

**TP14-only outcome, 18:03: held but with a finite repair.** Three private
revisions put TP14 on the existing connected LRCLK via at (110.950, 87.712).
All join TP14 to IC1.29/U4.14 and reduce opens 8 -> 7 without changing tracks
or vias. None is accepted: the initial 1.0 mm F land has shorts/clearance/mask
defects because selection omitted nearby BCLK tracks; it was not screened
legal. The 0.6 mm F correction has nine BCLK clearance findings (0.1254-0.1476
mm against 0.150 mm). The 0.6 mm B correction has one AMP_MUTE clearance
finding: 0.1350 mm against 0.150 mm, no shorts or mask bridges. The initial
plus two corrections are exhausted; no fourth TP14-only revision is released.
The executor initially claimed the 18:04 cutoff had passed at 18:00; the lead
checked the actual clock and used the remaining original allowance, not an
extension. No matching local footprint was made for these rejected revisions.
Private evidence: `tp14-service-1752`, final candidate `e2f13601...`,
DRC `c86a9dfa...`, summary `5386633e...`. Best-8-c1c4 stays unchanged.

**Next coordinated item:** rather than abandon the seven-open diagnostic or
ask again for permission to move copper, the lead releases a different,
exact replacement contract. Only B.Cu AMP_MUTE track
`2abd2d2e-57cf-49cb-8396-8f73340d516e` may change beside the 0.6 mm B test land.
Preserve its width, endpoints and every branch/interior contact; keep the
replacement within 0.25 mm of its old centreline with at most 0.5 mm extra
length. No new vias or adjoining-track release. Construction is conditional
on the full paired geometry screen with 0.025 mm margin and actual B-side
contact/assembly access, not only U4's front-body outline. This new item
stops at 18:18, no native start after 18:15, report by 18:19; no paid routing.

### 18:08 acceptance: TP14 closed; seven opens remain

The coordinated candidate completed at 18:07:23 and the lead accepts exact
PCB `7cb61fef122cea12cb0797e83587ebe513d4994354cb592256e69dd76ff280d0`
for incremental routing continuation. Its private finisher package is
`multilayer-20261108\best-7-tp14`; the source is
`tp14-amp-mute-1804\rev3`. Best-8-c1c4 `2e8e16bf` and every failed trial stay
unchanged. No DeepPCB time or money was used.

TP14 becomes a 0.6 mm bare B.Cu/B.Mask probe land at (110.950, 87.712), over
the existing LRCLK via. It has no paste or new hole. The released AMP_MUTE
segment retains its 0.15 mm width and endpoints (110.44, 84.252) and
(110.44, 88.39); the replacement runs through (110.39, 84.752) and
(110.39, 87.89). Maximum displacement is 0.05 mm and added length is
0.004988 mm. Both existing endpoint contacts survive. Twenty finite
templates produced three passing routes; no other existing track changed.

Native KiCad 10.0.6 refill and all-track/all-severity/parity DRC give **8 -> 7
opens**, unchanged 46 parity notices and no growing non-open defect class.
Silk overlap falls 52 -> 50, silk-over-copper 97 -> 95 and library issues
97 -> 96. This is improvement against the baseline, not a clean-board claim.
LRCLK now has one group containing IC1.29, U4.14 and TP14; AMP_MUTE retains
IC1.31, Q4.1, R20.2 and TP15. No prior terminal group splits were reported.
The exact complement preserves every track/via except the released segment
and its two new endpoint segments; only TP14's footprint changes and all
41 zone definitions match. Project rules are byte-identical.

The portable `Handbell_Local:TP_BareProbe_D0.6mm` footprint, project-relative
`fp-lib-table` and TP14 schematic assignment agree. The schematic's only
line change is that footprint property. Parent verification binds every
final-summary hash, the unchanged protected base and the raw native counts.
The B land intersects no fitted-body or rule area; the nearest contact
guard is 6.173 mm away. This supports bare-board rear probing, not loaded
contact, complete assembly access or fabrication qualification.

Evidence: final DRC `a0702493...`, exact complement `c7fa2c8b...`,
routing check `2c47f5d7...`, rear-access proof `819073bd...`,
final summary `0943d7b4...`. The three coordinated revisions were an initial
LIB_ID-constructor failure before save, a geometry-passing revision with a
local-library mismatch, and the final matching native footprint export.
The earlier TP14-only three failures remain separately preserved.

Remaining duties are SWDIO, USBBOOT, POWER, VO+ and three GND groups
(C7.1, GAIN0.1 and IC1.19). TP14 is no longer on the repair list. Retain the
same approach: use an exact connected group and a narrowly released adjacent
control route before disturbing broad power/clock routing or buying another
unchanged-placement router run. Historical finisher bundles still describe
the older eight-open board; they are not the current seven-open package.

Administrative promotion verified 19 files, excluding KiCad personal
preferences; acceptance receipt `7706baad...`. Private backup snapshot
`f569bdf9` (parent `333cc7ba`) includes the accepted package and both trial
families: 4,709 files, 674.644 MiB. Backup exited successfully; integrity
check and restore were not repeated.

## November 8, 18:13 autonomous continuation

The owner explicitly requests continued progress without prompting after
each accepted connection. A successful local checkpoint is not completion
of the routing task. Preserve it and select the next ready bounded item,
while retaining finite retry limits and escalating genuine blockers rather
than silently extending an exhausted search.

The next item starts from accepted best-7-tp14 `7cb61fef`: a small accessible
TP5 service land and short SWDIO escape from IC1.25. Unlike LRCLK, SWDIO has
no existing routed group to attach to; the MCU pin and test land are each
isolated. Prior unchanged-pad and under-IC proposals remain rejected.
Neighbouring copper may be replaced only under an exact reviewed contract,
with complete branch restoration and untouched-complement evidence.

The verified Sol/medium executor binds IC1.25 at (96.550, 88.900), with a
0.875 x 0.200 mm land and actual IC1 body boundary x=96.5..103.5,
y=84..91. TP5 is presently a 1.5 mm F land. The released first candidate
uses a 0.6/0.8/1.0 mm bare service land and short 0.15 mm SWDIO escape,
without changing neighbouring copper. An ordinary through-via is allowed
only if required and clear of all-layer copper, holes and contact guards.
Preserve the accepted TP14 package and every other footprint/route/zone
definition; require a matching local footprint and schematic assignment.
This item stops at 18:28, with no native child starting after 18:25 and a
report by 18:29. No paid router run is released.

**SWDIO item stopped at 18:18 on tooling, not geometry.** Initial plus two
corrections were consumed: wrong interpreter without Shapely; native UUID
conversion failure after switching interpreter; then a complete-shape
screen exceeding its hard 30-second limit. No candidate or site-result report
was produced. The last helper is retained at
`swdio-service-1813\screen_construct.py` (`89e3c42a...`). No board was saved,
refilled or promoted. The finite screen did not establish infeasibility.
Do not silently run a fourth SWDIO attempt.

The lead continues with an independent, previously proposed GAIN0 cell
strategy rather than another VBAT detour: establish the jumper's actual
default bridge/configuration and consider a small whole-jumper relocation
with both GND and GAIN duties restored. VBAT/VAMP remain unchanged; exact
local GAIN-copper replacement still requires the lead's contract. This
changes the component being allowed to move rather than repeating the
fixed-pose ground/via or power-detour screens. Best-7-tp14 remains the base.

**GAIN0 source correction and 18:20 contract:** it is a three-pad normally-
open selector, not a two-pad jumper: pad 1 GND, pad 2 GAIN, pad 3 VAMP.
Preserve all three pads, their spacing, continuous mask opening and both
selectable gain settings. No copper bridge is currently serialized.
The lead permits short same-layer GAIN (0.15 mm) and VAMP (0.1778 mm)
attachments to their exact retained source terminals, at most 3 mm each.
This VAMP branch is a gain-selection tap, not a new amplifier-current feed;
existing power copper remains fixed. A move need not detach a terminal if
the moved pad still overlaps it; actual contact, not centre coincidence,
determines that.

A finite 32-pose screen combines eight translations within 2 mm with four
rotations. All three terminal attachments must work together, including
GND to actual main F fill, with no new via. Geometry/native children have
hard 90-second limits; the whole item ends 18:33, no native start after
18:30 and report by 18:34. No source mutation or paid router run is released.

**GAIN0 finite result:** all 32 released poses fail foreign-copper clearance
and/or courtyard checks before attachment construction. Rightward poses
enter fixed VBAT; leftward poses enter Q3/R7/R24, VBAT or L0 structures.
The final native geometry screen completed in 0.703 seconds with no empty
shapes. Two earlier implementation corrections addressed a Shapely
`dict_values` argument and SWIG-object identity incorrectly retaining the
jumper's own pads as obstacles. Those three attempts exhaust this item.
No PCB save, refill or native DRC followed. This is not a proof against
every possible pose within 2 mm. Evidence: `gain0-cell-1820`,
`screen-report.json` (`5431b58a...`), script `c52b94e4...`, and `attempts.json`.

The next independent probe is POWER, the boost-enable control connection,
not the load-current rail. It must determine whether the previously named
Q2-side `~ENABLE` escape replacement addresses a useful group attachment
and whether U5.2 has a legal exit; changing one end does not prove a complete
route. No boost power/feedback-loop change or repeated fixed-route sweep is
released. All seven opens and the accepted best-7 baseline remain unchanged.

Private snapshot `042e1dd7` preserves the new SWDIO/GAIN0 evidence (parent
`f569bdf9`, 4,713 files, 674.754 MiB; four new files). Backup succeeded;
integrity/restore were not repeated. The saved package has the final helpers,
GAIN0 report and attempt record, not separately archived copies of every
failed helper revision; retain that provenance limitation rather than claim
complete revision preservation.

**POWER probe:** the Q2-side three-segment `~ENABLE` detour would open only
one end. U5.2 is separately hemmed in by its adjacent BOOST_FB/VIN pads and
the V+ input feed west of EN. The lead declines a Q2-only construction.
This is not a request for the owner to approve copper movement again:
the next engineering contract considers a small same-layer V+ input-feed
replacement, preserving width, cap/branch duties and endpoints with at most
0.5 mm added path. BOOST_FB, switching copper, private returns, placement
and special via processes remain unreleased.

The bounded `power-entry-1827` item first identifies the exact input-feed
UUIDs and all attached duties, then screens at most 12 paired feed-detour/
EN-exit templates. No board construction before that exact contract is
reviewed. Geometry/native child limit is 90 seconds; initial plus two
corrections total. Engineering stop 18:40, no native start after 18:37,
report by 18:41. No paid router run.

**POWER input-feed result:** 12 same-F detour/EN-exit pairs produced no
qualified pair. The existing seven-segment V+ pin-feed section is 3.268521 mm
long, from (96.665, 115.7) to (95.85, 113.1), with C26.1/source/L1.P$1
connections outside the released section. At y=114.7 the reported gap
between L1.P$2 switching copper and U5.1 feedback-pad copper is 0.675 mm;
the screen's two-trace allocation requires 0.8528 mm. This establishes a
blocker for that local same-layer contract, not every route or layer strategy.
No candidate was built. Receipt `power-entry-1827\stage1-receipt.json`,
`9cac9114...`.

**18:36 broader local implementation:** the lead releases a three-pose U5
cell study, eastward +0.4/+0.5/+0.6 mm with unchanged orientation, identities
and all six terminal duties. Fixed L1/capacitors/divider/private-pickoff
terminals and process vias remain mandatory. Replacement fanout must restore
every exterior join, preserve widths and input-cap/feedback/switching
relationships, and provide an actual EN exit; a legal component centre is
insufficient. The existing V+ pin feed may not become longer or narrower.
No whole-net rip-up, board-outline change, special vias or paid run.
Exact replacement geometry is reviewed before construction. Stop 18:49,
no native start after 18:46, report by 18:50.

The lead also corrects the probe's under-body assumption: an IC body alone
does not prohibit insulated routing underneath it. Under-body EN exits must
be judged against actual pad/underside-metal/process geometry and full via
span, not rejected merely as "inside the body." Probe-land access is a
different requirement. No pad/clearance/assembly exemption follows.

**U5 screen: retain the +0.4 mm pose for a specific completion.** Three
geometry revisions found a mechanically clear pose at (97.7, 115.2), with
unchanged orientation. Actual pad overlap retains BOOST_FB and the full
3.268521 mm V+ chain without rerouting either. A proposed 0.15 mm EN route
uses pad-free under-body space to an off-row ordinary-via site (97.7, 114.2).
The 0.810 mm opposing-pad gap is insufficient for the screened centred via,
but that does not reject the off-row site. Proposed BOOST_SW replacement
is 2.0161 mm versus 2.135 mm removed, retaining width and its external join.

The pose remains HELD: moved U5.5 conflicts with two existing 0.8 mm GND/
VAMP branch continuations. The old three-pose item is stopped after initial
plus two corrections. Receipt `power-u5-cell-1836\stage1-receipt.json`,
`f910c38e...`; no board was constructed.

The next, specifically expanded contract releases exactly those two branches
(`1882384a-8437-51aa-84e0-67f4c472cc46`,
`5f740232-0ad1-5df6-a1d0-daa1b956e7bf`) in addition to the prior two
BOOST_SW segments and local GND/VAMP stubs. Preserve all exterior joins,
private pickoffs, 0.8 mm broad copper and short 0.3 mm pad necks (each at
most 1 mm exposed length). Apply the stricter actual net clearance plus
0.025 mm; the earlier 0.185 mm suggested clearance is not a blanket pass.
No other part or power-net release. Screen the complete paired geometry,
construct only if it passes, then attempt the remaining POWER connection
using the existing single-net router. A useful local cell that fails the
long connection stays separately held, not promoted or discarded.

The completion item is `power-u5-complete-1840`, stop 19:00, no native start
after 18:57 and report by 19:01. No paid router run or fabrication release.

**Complete U5 cell staged:** `power-u5-complete-1840\rev2` PCB `393b23b9...`
moves only U5 +0.4 mm, replaces exactly the six released tracks, preserves
V+/BOOST_FB, and adds a POWER escape with off-pad via
`3f9b8296-6b59-4dee-8083-76f098779939` at (97.7, 114.2).
The GND/VAMP exposed 0.3 mm necks become 0.650 mm (was 0.525); their
0.8 mm branches shorten to 0.450694 mm. BOOST_SW shortens to 2.008079 mm.
Local native geometric clearance has no new findings, but opens remain
7 -> 7. A new dangling via and missing local TP14 library context keep
the standard result held. The library context must be restored, not waived.

The first long-link invocation found no path but used legacy F/In2/B
defaults, omitting 6C's In3 signal layer. The lead identified a second
invocation issue: `route_gaps.py` expands goals, not the source group.
The correction must start at the newly qualified EN via, not a trapped
literal pad witness, and explicitly enable F/In2/In3/B. Any substitute
routing-request JSON is labelled synthetic and kept separate from native
DRC evidence. This correction stays within the current completion item's
allowance and deadline; it is not acceptance or an unchanged router rerun.

**Corrected invocation closes POWER, pending final lead disposition.**
Four layers with the old F-track source still found no path (4.234 s;
1,112 reachable cells, all F, none via-capable). The third route invocation,
using the EN via as source, routed in 5.906 s: 208 In3 segments, 0.15 mm
width, 20.58 mm centreline, no additional vias. Q2-side copper stayed
unchanged. Filled candidate `rev2-routed4-via\handbell.kicad_pcb`,
`dacfb543...`, has 6 opens versus 7, identical 396 non-open findings and
46 parity notices. Exact local-library context removes the temporary TP14
warning. No paid run.

The lead independently verifies exact PCB hashes, identical project/
schematic/local-library bytes, all unchanged copper/footprint subtrees
(except U5's +0.4 mm pose), zone definitions and other top-level fields.
Exactly six released tracks disappear; 218 copper objects are added.
Source-bound `parent-complement.json` records that parsed comparison.
The executor's filled-island graph finds zero prior terminal-group splits
and only the authorized POWER merge. Main GND retains 61 terminals;
private-net and CELL_NEG memberships are unchanged.

The In3 route has 20.333646 mm of actual In4 main-GND reference under its
20.580004 mm centreline; the 0.246357 mm uncovered span is at the EN-via
transition. BOOST_SW's full centreline shortens 6.735 -> 6.608079 mm,
while its right extent grows 0.171064 mm; fixed L1/capacitors remain.
The two 0.3 mm necks are 0.650 mm and the broad branches shorten.
These are geometry witnesses, not measured switching performance.

The package witness uses the source six-pad DRL footprint, with no exposed
centre pad or copper graphics. With no F.Fab body present, its silhouette
comes from F.Silk; the via centre is outside that silhouette, not proof
that its entire annulus is outside it. One failed F.Fab-assumption helper
receipt and its corrected witness are preserved. Final review must
explicitly reconcile the original uniform 0.175 mm screen with the
released stricter-net-plus-0.025 mm margin: project V+/VAMP require 0.20 mm.
Native DRC establishes the rule floor, not that extra screening margin.
Candidate remains staged while this final finite witness is checked.

### November 8, 20:24: six-open baseline accepted with explicit margin disposition

The final read-only clearance witness completed at 18:52, before the
original item's deadline: 224 subjects (218 new copper items and six moved
U5 pads), 1.219 s wall time, no new board write or routing. It returned
**HOLD**, even though its process exit was zero. Seven failed item records
represent four physical conditions, not seven defects:

| Condition | Actual gap | Project floor | Extra screening target |
|---|---:|---:|---:|
| New broad GND/VAMP branches | 0.202272 mm | 0.200 mm | 0.225 mm |
| New VAMP neck to BOOST_SW | 0.203939 mm | 0.200 mm | 0.225 mm |
| U5.2 POWER to U5.3 V+ pads | 0.200 mm | 0.200 mm | 0.225 mm |
| U5.5 BOOST_SW to U5.6 VAMP pads | 0.200 mm | 0.200 mm | 0.225 mm |

The latter two spacings are intrinsic to the unchanged footprint, not
created by its translation. All added POWER tracks and its full-span via
pass the extra margin. Report `clearance-witness.json`, `486f9376...`, and
helper `9e9e632a...` remain unchanged; no threshold or result was rewritten.
The helper uses an explicit net-name clearance mapping matching this exact
project, not a general KiCad rule resolver.

**Lead disposition:** accept exact `dacfb543...` as an incremental routing
baseline at the unchanged native project rules, with the four listed
exceptions to the additional agent-imposed screening margin. This is not a
claim that the stricter screen passed. The two new copper gaps have only
0.002272/0.003939 mm nominal headroom above the project floor; retain them
for final manufacturing review rather than silently generalize the exception.
The owner asked whether to accept and push; the specific margin question
returned owner-unavailable/autonomous handling. No explicit owner waiver is
claimed. This is the lead's delegated engineering decision for continued
routing, not fabrication, powered-use or electrical-performance approval.

The actual In4 fill boundary is 0.450499 mm from the EN-via centre,
consistent with its 0.250 mm annulus radius plus 0.200 mm zone clearance.
The 0.246357 mm uncovered route projection is therefore the ordinary
transition antipad, not a long reference-plane split. The lead retains the
20.58 mm enable-control route and the source-bound local switching-cell
changes: shorter actual SW/return paths, unchanged widths/exterior joins,
fixed capacitors/inductor and preserved feedback/private pickoffs. This
does not establish measured noise, current or thermal performance. No new
return stitch or fully outside-body via annulus is claimed.

**Promoted package:** private `multilayer-20261108\best-6-power`,
PCB SHA-256 `dacfb543f2eabedf1e4bf77e9612e94e74f022aa514535bc0f08167bbbc9cdc4`.
Administrative exact copies only: 26 package/evidence files verified before
writing `acceptance.json`; no native save/refill/routing on promotion.
Project, schematic, local footprint and table match best-7 exactly;
`.kicad_prl` is excluded. The acceptance records the margin exceptions,
all six removed tracks, evidence, preservation and release limits.
Best-7 `7cb61fef...`, best-8-c1c4 and older sources remain immutable.

Six opens remain: SWDIO, USBBOOT, VO+, GND C7.1's island, GAIN0.1 and
IC1.19 TESTEN. The next bounded item is USBBOOT: review D3.C's escape
against the complete connected group and preserve both diode terminal
duties before selecting any local replacement. Do not repeat previous
fixed-route/R18 screens unchanged. U5's mechanical rebinding and the
remaining electrical/manufacturing gates are still outstanding.

Private Azure/restic snapshot `1678e902` (parent `042e1dd7`) now preserves
the POWER experiments, failed witnesses and accepted six-open package:
4,798 files, 684.590 MiB, 85 new files. Backup exited successfully; no fresh
full-data integrity check or restore was performed for this snapshot.
The PCB packages remain private; the public commit carries this handoff,
engineering disposition and reusable workflow lessons.

### November 8, 20:28: USBBOOT local-cell continuation

The owner requests continued autonomous implementation after the six-open
checkpoint. A fresh executor's configured Sol/medium and first-dispatched
model are verified. Source is immutable best-6-power `dacfb543...`;
private work is `usbboot-cell-2028`. First bind the complete USBBOOT group,
both D3 terminal nets, actual attached anode fanout and all branch joins.
Screen at most 12 paired templates with D3 translated within 1.5 mm,
unchanged package/orientation, and every other part and unrelated copper
fixed. Any anode replacement requires exact lead review before construction.
Do not repeat the exhausted fixed-route/R18 screens or treat an obstacle as
a terminal. Both ends and any ordinary via's complete span must be usable.
Source-contract report target 20:32; item stop 20:42, no native start after
20:39, final report 20:43. Initial plus two corrections; hard 90-second
geometry/native and 30-second static children. No paid router run.

**Translation screen stopped:** the final report binds D3 at
(109.353, 104.733939), -90 degrees, and identifies the five 0.15 mm F tracks
between D3.A and R11.2. D3.C is USBBOOT; the opposite group contains IC1.9
and TP3, with existing vias at (99.156, 84.914) and (84.832, 87.390).
None of 12 translated direct-F paired templates passes. This is not a
local-transition feasibility result: the helper attempts long F cathode
lines to remote group endpoints and never screens an adjacent cathode via.
The lead also identifies SWIG parent equality in the D3 exclusion and a
group pool without filled zones; the claimed complete group therefore
requires confirming that neither relevant net has zone copper. Via spans
on all six layers do not establish tracks on all six.

The attempt history includes a quoting preflight failure, pad-class failure,
90-second screen timeout and final successful screen. The folder initially
contains only the last helper/report, not separately preserved failed
helpers or receipts. Preserve that provenance gap. The translation screen
is exhausted; do not rerun it as a correction.

**Distinct fixed-D3 transition contract:** keep D3 and ALL existing copper
unchanged. Screen eight local off-pad 0.5/0.3 mm ordinary via sites at
cardinal offsets 0.8/1.1 mm from D3.C (109.353, 103.663939), each with a
direct 0.15 mm F stub. Use actual pad shapes and stricter project net-pair
rules, all-layer fixed copper, contact/edge/drill restrictions and UUID
identity. Normal refillable GND antipads are allowed, not cuts in fixed
private copper. No added arbitrary screening margin or reuse of U5's
source-specific exceptions.

If a complete site passes, construction is released for one additive-only
private candidate followed by one USBBOOT-only four-signal-layer route,
starting at the new via and targeting the real opposite group. Preserve
the anode chain, all parts and all old copper; require 6 -> 5 with no
native finding growth, exact complement and preserved filled groups.
No site means stop, not expand the eight-site set. This changes topology,
not the exhausted translation screen's parameters. The original 20:42
stop/20:39 native-start cutoff remains; executed revisions/receipts must
be preserved and no paid run is released.

**Eight-site result: NO_SITE.** All eight cathode-via centres fall in
`CONTACT_METAL_GUARD_BT1.base.3`
(`0f6959e1-644e-5a0a-aca1-8d8044c98517`). East/south sites have no additional
fixed-copper blocker; north hits VAMP and west-1.1 hits R18/VAMP.
No candidate, route, refill or DRC followed. The source remains `dacfb543`.
The 0.907-second run preserves `fixed-via-screen.json` (`ef3f500c...`),
helper `6ff4430c...` and receipt `3543398d...`. Zero USBBOOT/anode copper
zones are confirmed, resolving that earlier group-pool limitation.
The original translation failures remain explicitly missing, not recovered.

The lead stops the eight-site strategy and releases a final boundary-derived
test under the SAME 20:42/20:39 deadlines: exactly two rays, east and south
from fixed D3.C, using the actual union of all via guards to derive the first
fully off-guard 0.5 mm via centre, plus 0.01 mm numerical reserve.
Maximum direct F stub is 5 mm. This is not a ninth nearby grid point or
permission to move copper. Check the complete stub/full-span via and actual
edge/hole restrictions before using the existing additive-only construction
contract. At most two derived sites, no resampling; failure escalates the
contact/corridor problem instead of another local batch. No paid run.

**Final USBBOOT result: no candidate.** BT1 base.3 spans x105.435..118.935,
y94.185..105.815 mm. Including the via radius and reserve, east's first
exit is 9.842 mm from D3.C, outside the 5 mm contract. South exits after
2.411061 mm at approximately (109.353, 106.075001), but its straight stub
crosses D3.A/its required anode track and the B via overlaps BUTTON_EXT
`ee5f1aec...`. No resampling, router call, refill or board write followed.
Report `guard-boundary-ray-screen.json` (`30fbcdee...`) and its exact-boundary
supplement (`310f5a9f...`) preserve the finite result. Best-6 is unchanged.
Stop this item's USBBOOT geometry; a future diode/control-cell corridor
decision must address the actual anode and B-side duties, not repeat nearby
via screens or infer physical impossibility.

**Next independent item: finite SWDIO tooling recovery.** The earlier
smaller-land attempt produced no geometry result. Reviewing its retained
helper shows thousands of candidate shapes with repeated whole-inventory
distance scans, plus an unsafe first-matching schematic-footprint replacement
in its unexecuted construction tail. The new item must cache scoped F copper,
use a small finite land set and bind any schematic edit to TP5 itself.
No unchanged rerun, global footprint substitution, copper removal or lost
recovery function. Base remains best-6. New item stops 20:52, with no native
child after 20:49; its separate runtime gate precedes execution.

At 20:38 the fresh executor's configured Sol/medium and first-dispatched
model match. Released finite screen: nine 0.6 mm F bare-land centres,
x95.50/95.65/95.80 crossed with y88.70/88.90/89.10; each gets a direct
0.15 mm link from IC1.25 or one dogleg through (95.95, 88.9).
Only TP5's pose/land and matching schematic footprint property may change;
the existing local 0.6 mm library and TP14 must remain untouched. No vias,
other moved parts or removed copper. Construction is conditional on complete
clearance/access screening, then 6 -> 5 native/connected-group preservation.
No expansion of this finite set. Private folder:
`swdio-service-recovery-2038`.

The cached screen completes in 0.312 s with zero qualified 0.6 mm sites.
Parent review finds a reporting/configuration defect: it hardcodes 0.20 mm,
not the requested net-pair rules, and labels actual gap as "margin."
Best-site recorded gaps at (95.80, 89.10) are 0.028150 mm to RESET and
0.051347 mm to VCORE, not positive headroom; these also miss 0.15 mm.
Preserve the raw report (`8eea08b1...`) and produce a static rule-bound
disposition, not a silently corrected original result.

The lead releases one local repair at that SAME best centre, not more
grid points: a 0.30 mm bare microprobe land with the existing direct/dogleg
choices and actual net-pair rules. The 0.15 mm radius reduction may help,
but the complete route and physical access must be rechecked. This is
deliberately small service access; do not claim universal hand-probe
usability. The land must remain exposed outside fitted bodies. If qualified,
add a separate local 0.3 mm footprint, preserving TP14/the 0.6 mm library,
and apply only the TP5-bound schematic property. Same 6 -> 5 acceptance
gates and 20:52/20:49 cutoffs; no further size reduction or centre change.

**SWDIO geometry result: one dogleg qualifies, builder not yet qualified.**
The corrected saved-rule supplement maps SWDIO/RESET and VCORE/+3V3 to
0.15 mm project clearance. The original 0.6 mm sites all fail; their report's
misnamed "margin" values were gaps, not headroom. At the single released
0.30 mm centre `(95.80, 89.10)`, the direct line fails to IC1.26 RESET
(0.102143 mm gap versus 0.150 mm). The dogleg through `(95.95, 88.90)`
passes the local geometry screen, with fitted-body bounding gaps of 0.455370
mm (C18), 0.522534 mm (C14) and 0.550000 mm (IC1). This is bounded
microprobe access evidence, not universal probe usability.

Native construction attempts then failed three times: two KiCad `LSET`
API mismatches, followed by a schematic-binding assertion after a private
board refill. That partial candidate is unaccepted and has no DRC,
connectivity or exact-complement qualification. The assertion came from
searching only for indented `symbol` nodes; TP5's symbol UUID
`eeee113d-ae59-4cdc-abe9-679e1836adbb` begins at column zero. The correct
next action is a new bounded **builder-only** item using parsed UUID plus
Reference binding and a precise one-property schematic diff. Do not retry
geometry, change land size/centre, globally replace a footprint string,
or use the partial board. Preserve best-6 immutable. Build, refill and full
native acceptance are separate gates; a helper fix alone is not closure.

### November 8, 23:39 - SWDIO TP5 closure accepted (6 -> 5)

The separate builder-recovery item is complete and its exact private output is
accepted as the next routing-continuation baseline:
`multilayer-20261108\best-5-swdio`. Source `best-6-power` remains unchanged.
The accepted PCB SHA-256 is
`f8ec463b9384e6618726346155de6bab3bb312bb7e226a6f0cea8e5bde66b9ba`;
the prior base is
`dacfb543f2eabedf1e4bf77e9612e94e74f022aa514535bc0f08167bbbc9cdc4`.

The recovery correctly bound the schematic edit to TP5's symbol UUID
`eeee113d-ae59-4cdc-abe9-679e1836adbb` and `Reference=TP5`, changing only its
footprint property. It moves only TP5 to (95.8, 89.1), changes its land to a
0.30 mm bare F.Cu/F.Mask land with no paste, and adds two 0.15 mm F.Cu SWDIO
segments through (95.95, 88.9). The existing 0.6 mm TP14 footprint/library
is untouched. This is intentionally small, awkward fine-probe access; it is
not universal hand-probe or fixture qualification.

KiCad 10.0.6 all-track/all-severity/parity DRC reports 6 -> 5 opens, 396 -> 391
non-open findings, and unchanged parity (46). Only SWDIO's open disappears;
no finding type grows. The standard routing checker and exact-complement
checker pass. All 2,166 pre-existing copper blocks, 103 other footprint
blocks, 41 zone definitions, In1 serialization, private returns, CELL_NEG,
POWER changes, project file and schematic parity remain preserved. The exact
candidate package has a 46-file hash manifest and an acceptance record.
Earlier native receipt overwrite during correction is disclosed in the
private `swdio-builder-recovery-2329\final-summary.json`; recovered evidence
and constructor revisions are retained.

The next bounded independent item is a source-bound ground connectivity and
attachment census on this exact five-open baseline, first resolving the C7.1
filled GND island and finite accessible service-pad/terminal sites. Reuse
unchanged saved evidence only where exact invariance is demonstrated. Do not
repeat the exhausted USBBOOT local via/exit searches, TP5 geometry searches,
or invoke another paid router run. Five opens remain: USBBOOT, VO+, GND at
C7.1, GAIN0.1 and IC1.19 TESTEN. This routing-continuation acceptance is not
fabrication, powered-use, safety, or child-use approval.
