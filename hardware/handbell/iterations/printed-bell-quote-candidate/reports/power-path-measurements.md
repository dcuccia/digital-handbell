# Quote-candidate actual-copper path measurements

**Screening only; copper-drop targets remain NOT_DEMONSTRATED.**
A connected row has a finite sampled copper walk, not a measured/equivalent resistance. OPEN or native-short cases have no invented round-trip total.

Candidate PCB SHA-256: `2d88301f48ad05dc01384b90111f16615f176a7f4704eab82a1e3560ef5c8bc0`
Source PCB SHA-256: `6132f8d3ec508f8ae023888052cc2a1f8b2c24f2c38d9d12dca3234ba887dcc1`
Analyzer SHA-256: `c378834e3138ac1138a0f36acbb072ece348158a1b2cbeb8440f4b13de2b820f`
KiCad `10.0.6`; Python `3.11.9`; numpy `2.4.2`. E04/#4, E05/#5, E07/#7.

Bound native review: **INCOMPLETE routing; quotation/fabrication BLOCKED**; 0 checker errors; 59 unconnected items.
Native report input/tool hashes and full findings remain in the JSON. This measurement does not replace or waive completion-review.json/md.

With an F-ground fill, GND connectivity uses actual filled islands but its walk, neck and resistance values are NOT MODELED. Nonground copper is still measured; no track-only return estimate or invented whole-loop budget is assigned to the plane.

## Connected current corridors

| Path | Status / layer | XY incl. pad travel (mm) | Barrels | Min. strip width (mm) | Nominal chosen-strip (mOhm) |
|---|---|---:|---:|---:|---:|
| BT1.1 -> Q3.3 | CONNECTED_CHOSEN_WALK / F.Cu/B.Cu | 11.6 | 1 | 0.035 | 12 |
| Q3.2 -> Q1.2 | CONNECTED_CHOSEN_WALK / F.Cu/B.Cu | 2.24 | 0 | 0.3 | 2 |
| Q1.3 -> L1.P$1 | CONNECTED_CHOSEN_WALK / F.Cu/B.Cu | 7.06 | 0 | 0.75 | 3.1 |
| U5.4 -> R27.2 | NOT_MODELED_FILLED_GND_NETWORK / F.Cu/B.Cu | - | - | - | - |
| R27.1 -> Q5.A2 | CONNECTED_CHOSEN_WALK / F.Cu/B.Cu | 4.47 | 2 | 0.018 | 22 |
| R27.1 -> Q5.C2 | CONNECTED_CHOSEN_WALK / F.Cu/B.Cu | 6.74 | 2 | 0.018 | 26 |
| Q5.A1 -> BT2.1 | CONNECTED_CHOSEN_WALK / F.Cu/B.Cu | 15.6 | 1 | 0.082 | 21 |
| Q5.C1 -> BT2.1 | CONNECTED_CHOSEN_WALK / F.Cu/B.Cu | 13 | 1 | 0.018 | 21 |
| C28.1 -> C19.1 | CONNECTED_CHOSEN_WALK / F.Cu/B.Cu | 25.8 | 0 | 0.13 | 27 |
| C28.1 -> U4.7 | CONNECTED_CHOSEN_WALK / F.Cu/B.Cu | 28.4 | 0 | 0.13 | 32 |
| C28.1 -> U4.8 | CONNECTED_CHOSEN_WALK / F.Cu/B.Cu | 27.9 | 0 | 0.13 | 30 |
| U4.THERMAL -> C27.2 | NOT_MODELED_FILLED_GND_NETWORK / F.Cu/B.Cu | - | - | - | - |
| U4.11 -> C27.2 | NOT_MODELED_FILLED_GND_NETWORK / F.Cu/B.Cu | - | - | - | - |
| C19.2 -> C27.2 | NOT_MODELED_FILLED_GND_NETWORK / F.Cu/B.Cu | - | - | - | - |
| C19.1 -> U4.7 | CONNECTED_CHOSEN_WALK / F.Cu/B.Cu | 2.89 | 0 | 0.17 | 5.6 |
| C19.1 -> U4.8 | CONNECTED_CHOSEN_WALK / F.Cu/B.Cu | 2.44 | 0 | 0.24 | 3.9 |
| U4.THERMAL -> C19.2 | NOT_MODELED_FILLED_GND_NETWORK / F.Cu/B.Cu | - | - | - | - |
| U5.5 -> L1.P$2 | CONNECTED_CHOSEN_WALK / F.Cu/B.Cu | 6.13 | 0 | 0.2 | 6.6 |
| C26.1 -> L1.P$1 | CONNECTED_CHOSEN_WALK / F.Cu/B.Cu | 3.9 | 0 | 1.1 | 1.3 |
| C26.2 -> U5.4 | NOT_MODELED_FILLED_GND_NETWORK / F.Cu/B.Cu | - | - | - | - |
| C26.1 -> U5.3 | CONNECTED_CHOSEN_WALK / F.Cu/B.Cu | 8.93 | 0 | 0.04 | 42 |
| R24.2 -> C28.2 | NOT_MODELED_FILLED_GND_NETWORK / F.Cu/B.Cu | - | - | - | - |
| R26.2 -> R27.2 | NOT_MODELED_FILLED_GND_NETWORK / F.Cu/B.Cu | - | - | - | - |
| U4.11 -> U4.THERMAL | NOT_MODELED_FILLED_GND_NETWORK / F.Cu/B.Cu | - | - | - | - |
| U5.6 -> C27.1 | CONNECTED_CHOSEN_WALK / F.Cu | 2.23 | 0 | 0.3 | 2.2 |
| C27.2 -> U5.4 | NOT_MODELED_FILLED_GND_NETWORK / F.Cu | - | - | - | - |
| U5.6 -> C28.1 | CONNECTED_CHOSEN_WALK / F.Cu | 4.32 | 0 | 0.3 | 3.5 |
| C28.2 -> U5.4 | NOT_MODELED_FILLED_GND_NETWORK / F.Cu | - | - | - | - |

## Paired copper-only budgets

| Conditional loop | Case (A) | Nominal / 1.35x drop (mV) | Budget at target current | Result |
|---|---:|---:|---:|---|
| cell_via_a2_a1 | - | - | 50 mV @ 2 A | NOT_DEMONSTRATED: OPEN or unmeasured section: no numerical round-trip total is reported |
| cell_via_a2_c1 | - | - | 50 mV @ 2 A | NOT_DEMONSTRATED: OPEN or unmeasured section: no numerical round-trip total is reported |
| cell_via_c2_a1 | - | - | 50 mV @ 2 A | NOT_DEMONSTRATED: OPEN or unmeasured section: no numerical round-trip total is reported |
| cell_via_c2_c1 | - | - | 50 mV @ 2 A | NOT_DEMONSTRATED: OPEN or unmeasured section: no numerical round-trip total is reported |
| 5V_amp7_thermal | - | - | 100 mV @ 1 A | NOT_DEMONSTRATED: OPEN or unmeasured section: no numerical round-trip total is reported |
| 5V_amp7_11 | - | - | 100 mV @ 1 A | NOT_DEMONSTRATED: OPEN or unmeasured section: no numerical round-trip total is reported |
| 5V_amp8_thermal | - | - | 100 mV @ 1 A | NOT_DEMONSTRATED: OPEN or unmeasured section: no numerical round-trip total is reported |
| 5V_amp8_11 | - | - | 100 mV @ 1 A | NOT_DEMONSTRATED: OPEN or unmeasured section: no numerical round-trip total is reported |
| 5V_bulk_capacitor_endpoints | - | - | 100 mV @ 1 A | NOT_DEMONSTRATED: OPEN or unmeasured section: no numerical round-trip total is reported |

Cell Q5 alternatives are separate whole-current chosen walks, never parallel sums or equal-sharing claims. 3 A is sensitivity, not an approved operating current. An above-budget chosen strip does not prove the actual parallel-copper network fails; a below-budget strip does not qualify it.

Contacts and FET losses are unknown and excluded. The separate nominal 33 mOhm shunt alone adds 66 mV at 2 A or 99 mV at 3 A, before tolerance/temperature.

## Boost capacitor native source-to-candidate comparison

| Capacitor | Source paired XY / vias | Candidate paired XY / vias | Native all-F source -> candidate | Candidate rough all-F area |
|---|---:|---:|---|---:|
| C27 | 4.46 mm / 0 | NOT_DEMONSTRATED | True -> True | not meaningful/available |
| C28 | 8.63 mm / 0 | NOT_DEMONSTRATED | True -> True | not meaningful/available |

Loop lengths include finite pad travel; they are not the frozen review's pad-as-region numbers. Area is only a simple all-F walk polygon with straight IC/capacitor pin closures, not an inductance model. Each capacitor is separate; capacitances/parallel branches are not added.

## Exposed fine copper

| Native pad-adjacent inventory | Minimum exposed width (mm) | Total drawn (mm) | Uncovered centerline (mm) |
|---|---:|---:|---:|
| U5_SW_minimum_escape | 0.2 | 2.13 | 1.21 |
| output_VAMP_small_pin_exits | 0.3 | 0.815 | 0.09 |
| Q5_pad_adjacent_fine_including_bias_branches | 0.1778 | 2.95 | 1.15 |

Lengths here are inventories, not series resistance. The JSON contains exact native owners, covered/exposed intervals, actual narrow pieces on each selected main walk, and conditional currents. Pad/annulus/broader-trace coverage is subtracted; drilled-out centerline is not counted as copper. R24/R26/VIN bias and ripple branches have no automatic 2 A load.

## Counts and unresolved gates

Candidate: {'physical_pads': 325, 'tracks': 1124, 'vias': 87, 'physical_net_islands': 145, 'multi_pad_nets_not_complete': 27}. Source: {'physical_pads': 325, 'tracks': 674, 'vias': 35, 'physical_net_islands': 241, 'multi_pad_nets_not_complete': 49}.
Candidate native shape shorts: 0; geometry-walk diagnostics: 1.
The complete diagnostic and input-hash inventories are in the JSON. Native shape connectivity is not DRC; USB findings, clearance/short findings, residual islands and native-review gates remain visible.

## Method and assumptions

- Native KiCad copper, not authored route groups, owns connectivity and path selection.
- Track/pad/via walks are supported. With the checked F-ground fill, only nonground walks/neck estimates are evaluated; filled GND connectivity is native but its resistance is not modeled.
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
- No IPC-2152 or 10 C temperature-rise claim, ampacity, functional, fault, charging, fabrication, mechanical, live-cell or child-use signoff follows. Native diagnostics remain release gates.
- The actual final native file, not intended SES groups or former via positions, owns the result. Bias/sense tracks are classified by physical endpoints and chosen-walk ownership.
- Two off-pad return vias, when present, are inventoried individually. Neither their presence nor four outside Q5 fanouts establishes equal current division or final network performance.

Inputs were hash-checked before and after the calculation; this is not a cross-process generator lock. Rerun only after a coherent final build. These reports do not alter the parent-owned review. The measurement JSON SHA-256 embedded below pairs these two outputs.

Measurement JSON SHA-256: `3e92ab84ce5eb989d6ddf1c3f6ebce2fe521989f444544101c3d74e819f5e5bb`
