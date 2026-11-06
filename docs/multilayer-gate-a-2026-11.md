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
  - Widen this copper, or move C1, before fabrication. Do not count it as
    finished supply routing.
