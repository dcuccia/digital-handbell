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

Private files: `multilayer-20261106\6c-crit2` under the bakeoff root. DRC
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

## G5 - Tools and fixes so far

- New: `tools/build_multilayer_input.py` (kept-copper rule, stackup
  transplant, In1 -> In4 zone mirroring) and `tools/fit_parts_to_copper.py`
  (nudge parts off kept copper; drop moved copper in keep-outs; avoid a
  height zone).
- `tools/route_gaps.py` now takes the layer list, a net filter, via cost and
  supply widths.
- **Bug fix:** DRC net names with brackets (`QSPI_DATA[3]`) were truncated
  by three tools, so such nets were silently skipped; a shared parser
  (`drc_net`) fixes it.
- KiCad's Python API breaks process-wide after removing items. Tools now
  edit in separate processes.
- Still to do: plane-aware standard check with negative controls, plane
  stitching honouring the exception list, the +3V3 pour, and the free
  DeepPCB import/export round trip.
