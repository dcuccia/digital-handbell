# Clock definitions checkpoint - not a fabrication package

September 14, 2026 bounded foreground item. This isolated derivative preserves
the recovered routing checkpoint under `input-checkpoint`; its exact source and
output hashes are in `reports/clock-definition.json`. The recovered
`printed-bell-quote-candidate` and accepted mechanical models were not edited.

## Implemented scope

- Y1: Abracon ABM8-272-T3, four-terminal schematic symbol with case pins 2/4
  connected to GND, dedicated 3.2 x 2.5 mm package and manufacturer-example lands.
- C2/C3: Murata GRM1555C1H150JA01D, 15 pF, dedicated manufacturer-example lands.
- R6 remains 1 kohm. No component centres, mounting holes, contacts or USB
  interfaces moved. Nonclock footprints and tracks/vias are unchanged.
- Old copper on the three oscillator nets was removed deliberately; **no new
  routing was added**. Cached zone fills were cleared, not accepted as current.

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

Whole-board DRC with in-memory zone refill exceeded its **60-second timeout** and
was terminated, without saving the board. It was not retried. No current DRC or
unconnected-item count is claimed. Clock copper, local clearance acceptance,
zone refill and full schematic/PCB parity remain pending; the old 59-open result
does not describe this draft. The placement manifest retains historical input
context; this README and clock report describe the new stage, not an updated
full-CAD binding or a completed quote package.

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
```

The default netlist format is KiCad S-expression, not XML. Use an explicit
subprocess timeout for future DRC attempts; a terminal wait limit alone does not
terminate work. Next item: clock-local copper and its local clearance gate only.
USB, other part revisions, mechanical rebinding and vendor exports remain
separate work. No procurement, powered-cell or child-use approval is implied.
