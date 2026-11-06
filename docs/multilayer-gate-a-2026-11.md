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
