# Clock revision and local routing - not a fabrication package

September 14, 2026 bounded foreground items. This isolated derivative preserves
the recovered routing checkpoint under `input-checkpoint`; its exact source and
output hashes are in `reports/clock-definition.json`. The recovered
`printed-bell-quote-candidate` and accepted mechanical models were not edited.

The definition-only stage is preserved in commit `702f53b`. The current PCB adds
the first local copper increment; its current hash and exact added segments are
in `reports/clock-local-routing.json`. The older clock-definition report binds
the earlier stage, not the current PCB.

## Implemented scope

- Y1: Abracon ABM8-272-T3, four-terminal schematic symbol with case pins 2/4
  connected to GND, dedicated 3.2 x 2.5 mm package and manufacturer-example lands.
- C2/C3: Murata GRM1555C1H150JA01D, 15 pF, dedicated manufacturer-example lands.
- R6 remains 1 kohm. No component centres, mounting holes, contacts or USB
  interfaces moved. Nonclock footprints and tracks/vias are unchanged.
- The definition stage deliberately removed old oscillator-net copper and
  cached zone fills. The first routing increment adds **15 front-copper segments,
  no vias and no component movements**. Existing copper is unchanged.
- New connections: C2 to Y1 pin 3; C3 to Y1 pin 1 and R6 pin 1; the C2/C3
  ground pads to Y1 pin 4; and IC1 ground pin 19 to its exposed ground pad.
  These are partial connections, not a completed oscillator or ground network.

![First local clock copper, with unfinished MCU approaches](reports/clock-local-front.png)

This implements the separately recorded [clock selection](../../../../docs/device-component-selection.md),
not a repair of a demonstrated fault in Adafruit's design. Provenance and CC
BY-SA obligations remain in `LICENSE.txt` and `notices`.

## Evidence and remaining gates

KiCad 10.0.6 loaded the native board and both dedicated footprints. The exported
netlist establishes both Y1 case pins on GND and the intended C2/C3/R6 oscillator
nodes. ERC reports zero findings; the unchanged recovered source also reports
zero. `reports/clock-schematic.pdf` is the exported schematic for novice review.

The enlarged Y1 screening rectangle fits without moving components. Its nearest
same-face proxy gap is approximately 0.40 mm to R6. This is a nominal 2D bounding
box screen, **not** courtyard, soldering, mechanical or manufacturing acceptance.

The initial whole-board DRC/refill attempt exceeded its **60-second timeout**.
On resuming, even no-refill DRC reached a 30-second limit under the normal user
configuration. One corrective attempt with an initialized isolated KiCad
configuration completed. The specific offending user setting is not established.
Both before/after reports now use that same isolated configuration and **no
zone refill**; private preferences are not distributed.

The new tracks pass a conservative 0.20 mm native copper-shape screen, and a
physical connectivity graph confirms the six listed endpoint pairs. Native DRC
reports **92 to 86 unconnected items** under matching unfilled-zone conditions.
This is not comparable to the recovered board's 59-item filled-zone result.
The complete non-silkscreen finding multiset is unchanged: four inherited USB
hole-clearance errors and **three Clock footprint/library mismatch warnings**.
The latter were discovered by this resumed check and remain a definition
reconciliation gate, not a waiver. Existing silkscreen/text findings also remain.

The MCU XIN/XOUT approaches, Y1 pin 2 ground and the capacitor/case-ground
island's connection to protected ground remain unfinished. Those routes need
joint consideration around the MCU approach corridor and rear contact copper;
no unreviewed vias through that region were added. Zone refill, complete
schematic/PCB parity and full mechanical rebinding remain pending.

The first generation exposed a Windows default-encoding mismatch in inherited
symbol descriptions. One correction made UTF-8 explicit and regenerated the
draft before the successful ERC/netlist export. The generator now refuses to
overwrite the saved PCB; do not rerun it over subsequent edits.

## Reproducible commands

Run from this directory with the installed KiCad 10.0.6 `kicad-cli.exe`:

```powershell
kicad-cli sch erc --format json -o reports\erc.json handbell.kicad_sch
kicad-cli sch export netlist -o reports\netlist.kicad_net handbell.kicad_sch
kicad-cli sch export pdf -o reports\clock-schematic.pdf handbell.kicad_sch
kicad-cli pcb drc --format json --severity-all -o reports\clock-local-drc.json handbell.kicad_pcb
```

The default netlist format is KiCad S-expression, not XML. Use an explicit
subprocess timeout for future DRC attempts; a terminal wait limit alone does not
terminate work. For DRC, set `KICAD_CONFIG_HOME` to an initialized isolated KiCad
configuration and `KICAD10_SYMBOL_DIR` to the installed KiCad 10 symbol directory.
The exercised before/after DRC commands each had a 30-second process timeout.
`tools/route_clock_local.py` at the repository root applies only to the pinned
`702f53b` definition PCB and refuses to rerun over this increment.

Next item: reconcile the three Clock library/instance warnings without changing
pad geometry or placements; then resume the MCU approaches and return paths as
a separate bounded routing item. USB, other part revisions, mechanical rebinding and vendor exports remain
separate work. No procurement, powered-cell or child-use approval is implied.
