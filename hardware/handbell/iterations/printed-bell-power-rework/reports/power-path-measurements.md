# Printed-bell actual-copper path measurements

**Screening only; copper-drop targets remain NOT_DEMONSTRATED.**
A connected row has a finite sampled copper walk, not a measured/equivalent resistance. OPEN rows have no invented round-trip total.

Candidate PCB SHA-256: `6132f8d3ec508f8ae023888052cc2a1f8b2c24f2c38d9d12dca3234ba887dcc1`
Source PCB SHA-256: `075c7b7cb0a98e302af29f5985bbf020111df5b1be385e5ebfa61be236b04250`
Analyzer SHA-256: `c48f73a438e5bc9a81d5e26437a3ce9f5f0ce4b61e82e17ddf6480bbaa4da6cf`
KiCad `10.0.6`; Python `3.11.9`; numpy `2.2.6`. E04/#4, E05/#5, E07/#7.

## Connected current corridors

| Path | Status | XY incl. pad travel (mm) | Barrels | Nominal chosen-strip (mOhm) |
|---|---|---:|---:|---:|
| BT1.1 -> Q3.3 | CONNECTED_CHOSEN_WALK | 16.9 | 1 | 13 |
| Q3.2 -> Q1.2 | CONNECTED_CHOSEN_WALK | 29.6 | 2 | 37 |
| Q1.3 -> L1.P$1 | OPEN | - | - | - |
| U5.4 -> R27.2 | CONNECTED_CHOSEN_WALK | 18.5 | 2 | 20 |
| R27.1 -> Q5.A2 | CONNECTED_CHOSEN_WALK | 3.89 | 2 | 13 |
| R27.1 -> Q5.C2 | CONNECTED_CHOSEN_WALK | 6.15 | 2 | 15 |
| Q5.A1 -> BT2.1 | CONNECTED_CHOSEN_WALK | 15.5 | 1 | 22 |
| Q5.C1 -> BT2.1 | CONNECTED_CHOSEN_WALK | 12.9 | 1 | 21 |
| C28.1 -> C19.1 | CONNECTED_CHOSEN_WALK | 25.9 | 0 | 20 |
| C28.1 -> U4.7 | CONNECTED_CHOSEN_WALK | 28.5 | 0 | 24 |
| C28.1 -> U4.8 | CONNECTED_CHOSEN_WALK | 28 | 0 | 23 |
| U4.THERMAL -> C27.2 | CONNECTED_CHOSEN_WALK | 37.7 | 2 | 45 |
| U4.11 -> C27.2 | CONNECTED_CHOSEN_WALK | 38.5 | 2 | 53 |
| C19.2 -> C27.2 | CONNECTED_CHOSEN_WALK | 31.3 | 0 | 22 |
| U5.5 -> L1.P$2 | CONNECTED_CHOSEN_WALK | 6.13 | 0 | 6.6 |
| C26.1 -> L1.P$1 | CONNECTED_CHOSEN_WALK | 3.9 | 0 | 1.3 |
| C26.1 -> U5.3 | CONNECTED_CHOSEN_WALK | 8.93 | 0 | 42 |
| R24.2 -> C28.2 | CONNECTED_CHOSEN_WALK | 11.9 | 2 | 56 |
| R26.2 -> R27.2 | CONNECTED_CHOSEN_WALK | 1.69 | 0 | 3.6 |
| U4.11 -> U4.THERMAL | CONNECTED_CHOSEN_WALK | 1.57 | 0 | 10 |
| U5.6 -> C27.1 | CONNECTED_CHOSEN_WALK | 2.23 | 0 | 2.2 |
| C27.2 -> U5.4 | CONNECTED_CHOSEN_WALK | 2.23 | 0 | 2.2 |
| U5.6 -> C28.1 | CONNECTED_CHOSEN_WALK | 4.32 | 0 | 3.5 |
| C28.2 -> U5.4 | CONNECTED_CHOSEN_WALK | 4.32 | 0 | 3.3 |

## Paired copper-only budgets

| Conditional loop | Case (A) | Nominal / 1.35x drop (mV) | Budget at target current | Result |
|---|---:|---:|---:|---|
| cell_via_a2_a1 | - | - | 50 mV @ 2 A | NOT_DEMONSTRATED: cell_vplus |
| cell_via_a2_c1 | - | - | 50 mV @ 2 A | NOT_DEMONSTRATED: cell_vplus |
| cell_via_c2_a1 | - | - | 50 mV @ 2 A | NOT_DEMONSTRATED: cell_vplus |
| cell_via_c2_c1 | - | - | 50 mV @ 2 A | NOT_DEMONSTRATED: cell_vplus |
| 5V_amp7_thermal | 1 | 69 / 93 | 100 mV @ 1 A | WITHIN_CHOSEN_WALK_ONLY; target NOT_DEMONSTRATED |
| 5V_amp7_11 | 1 | 76 / 1e+02 | 100 mV @ 1 A | ABOVE_CHOSEN_WALK_ONLY; target NOT_DEMONSTRATED |
| 5V_amp8_thermal | 1 | 68 / 92 | 100 mV @ 1 A | WITHIN_CHOSEN_WALK_ONLY; target NOT_DEMONSTRATED |
| 5V_amp8_11 | 1 | 75 / 1e+02 | 100 mV @ 1 A | ABOVE_CHOSEN_WALK_ONLY; target NOT_DEMONSTRATED |
| 5V_bulk_capacitor_endpoints | 1 | 42 / 56 | 100 mV @ 1 A | WITHIN_CHOSEN_WALK_ONLY; target NOT_DEMONSTRATED |

Cell Q5 alternatives are separate whole-current chosen walks, never parallel sums or equal-sharing claims. 3 A is sensitivity, not an approved operating current. An above-budget chosen strip does not prove the actual parallel-copper network fails; a below-budget strip does not qualify it.

Contacts and FET losses are unknown and excluded. The separate nominal 33 mOhm shunt alone adds 66 mV at 2 A or 99 mV at 3 A, before tolerance/temperature.

## Boost capacitor native source-to-candidate comparison

| Capacitor | Source paired XY / vias | Candidate paired XY / vias | Native all-F source -> candidate | Candidate rough all-F area |
|---|---:|---:|---|---:|
| C27 | 7.99 mm / 2 | 4.46 mm / 0 | False -> True | 2.81 mm2 |
| C28 | 12.2 mm / 2 | 8.63 mm / 0 | False -> True | 6.56 mm2 |

Loop lengths include finite pad travel; they are not the frozen review's pad-as-region numbers. Area is only a simple all-F walk polygon with straight IC/capacitor pin closures, not an inductance model. Each capacitor is separate; capacitances/parallel branches are not added.

## Exposed fine copper

| Native pad-adjacent inventory | Minimum exposed width (mm) | Total drawn (mm) | Uncovered centerline (mm) |
|---|---:|---:|---:|
| U5_SW_minimum_escape | 0.2 | 2.13 | 1.21 |
| output_VAMP_small_pin_exits | 0.3 | 0.815 | 0.09 |
| output_GND_small_pin_exits | 0.3 | 0.815 | 0.09 |
| Q5_pad_adjacent_fine_including_bias_branches | 0.1778 | 3.88 | 1.69 |
| amplifier_small_ground_exits | 0.3 | 4.5 | 1.05 |

Lengths here are inventories, not series resistance. The JSON contains exact native owners, covered/exposed intervals, actual narrow pieces on each selected main walk, and conditional currents. Pad/annulus/broader-trace coverage is subtracted; drilled-out centerline is not counted as copper. R24/R26/VIN bias and ripple branches have no automatic 2 A load.

## Counts and unresolved gates

Candidate: {'physical_pads': 325, 'tracks': 674, 'vias': 35, 'physical_net_islands': 241, 'multi_pad_nets_not_complete': 49}. Source: {'physical_pads': 325, 'tracks': 921, 'vias': 38, 'physical_net_islands': 234, 'multi_pad_nets_not_complete': 47}.
Candidate native shape shorts: 0; geometry-walk diagnostics: 0.
The complete diagnostic and input-hash inventories are in the JSON. Native shape connectivity is not DRC; previous QSPI/GND losses, USB findings, unfinished routing and parent-review gates remain open.

## Method and assumptions

- Native KiCad copper, not authored route groups, owns connectivity and path selection.
- Only F.Cu/B.Cu straight tracks, native pads and through vias are supported; no zones/arcs.
- Native inward copper polygons and outward drill polygons use a 1 nm polygonization bound; positive-width walk contacts use a 2 nm numerical guard. Boundary-only contact is not a usable walk.
- Dijkstra minimizes XY walk length plus 1.6 mm per layer transition on a finite portal graph. It is not the exact geometric shortest path, least-resistance path, or a 2-D current solution.
- An identical-XY overlap join has zero length; travel across a pad or between different contacts does not. Separate physical pads sharing a pin number are never internally shorted.
- Foil screening uses rho*L/(w*t). Each <=0.25 mm walk slice uses an inscribed strip width equal to twice its minimum distance to the same-net copper-union boundary, including holes.
- These restrictive chosen-strip estimates intentionally ignore parallel current redistribution. They can overstate drop; bends, junction spreading, barrel entry crowding, terminal injection and overlapping strips prevent calling them a rigorous upper bound or equivalent resistance.
- Neck inventory subtracts actual same-net pad, via-annulus and strictly broader-track coverage from drawn centerlines. Coverage is not proof of full-width bypass or absence of a 2-D bottleneck.
- A chosen-path current is a conditional load case, not a measured branch current. Bias, sense, feedback and capacitor-ripple spurs receive no blanket 2 A assignment.
- Nominal foil is assumed 35 um/20 C. The requested 30 um/60 C sensitivity is 1.35x nominal. 60 C is a calculation case, not an allowed cell/enclosure temperature.
- Via DCR uses thin-wall rho*board_thickness/(pi*drill*wall), conditional on 25 um wall plating and 1.6 mm board thickness. Neither plating nor finished copper is selected/qualified.
- Each selected barrel is charged once per traversal at its full conditional DCR. No equal sharing, parallel Q5 via division, or thermal-via-array resistance reduction is assumed.
- JSON decimal places preserve computational reproducibility, not measurement accuracy. Markdown resistance/drop screens are intentionally shown to about two significant digits.
- A barrel edge is a lumped annulus-to-annulus connection, not a vertical copper column at the reported annular XY port; its entry/exit spreading is not solved.
- Cell copper sections are concatenated only conditionally across the excluded ON-state selector/audio/protector FETs, shunt and converter. No copper edge bridges different nets.
- Copper budgets exclude contacts, solder interfaces, FETs, the deliberate 33 mOhm shunt, inductor winding, IC internals and capacitor ESR. These are separate additional losses.
- No IPC-2152 or 10 C temperature-rise claim, ampacity, functional, fault, fabrication, mechanical, live-cell or child-use signoff follows. Prior QSPI/GND losses are not waived.

Inputs were hash-checked before and after the calculation; this is not a cross-process generator lock. Rerun only after a coherent final build. These reports do not alter the parent-owned review.
