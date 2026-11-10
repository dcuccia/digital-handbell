# Fabrication options and open questions (JLCPCB, bare PCB)

**QUOTE ONLY - not a fabrication release.** Nothing here selects an option for
an order. This page records what the exported files say, what JLC's public
capabilities page says, what JLC's live quote form showed on 2026-11-10, and
the questions only the supplier or the owner can answer. The
[package README](README.md) says exactly what was uploaded.

Source labels used below:

- **File**: read from the exact public snapshot by the static verifier.
- **Public page**: JLC's
  [capabilities page](https://jlcpcb.com/capabilities/pcb-capabilities),
  November 2026. Public text only: not an order-form check and not a quote.
- **Live**: observed in JLC's instant-quote form on 2026-11-10 after the
  Gerber/drill ZIP was parsed (quantity 5, 7-8 day build). Display only:
  nothing was saved to the cart, ordered or paid.
- **Screen**: a geometric check of the board against a public-page number.
  A screen is not a capability pass.

## What JLC parsed, and the defaults it showed

JLC reported "Detected 6 layer board of 48.35x44.5mm (1.904x1.752 inches)".
Its Dimensions fields read X 44.5 mm and Y 48.35 mm, matching the file's
44.5 x 48.35 mm bounding box. The preview showed a round board with a USB
tongue and looked right. No DFM warning or error was visible on the page.
Whether JLC runs a separate DFM check at "Confirm Production file" or at
cart/order time is unknown.

| Option | Default shown live |
|---|---|
| Layers / base material | 6 (High Precision PCB), FR-4, FR4 TG135 |
| Thickness | 1.6 mm (no 1.65 mm choice) |
| Colour / silkscreen | Green / White |
| Surface finish | OSP, $0.00 (ENIG available; HASL and LeadFree HASL disabled) |
| Copper | outer 1 oz, inner 0.5 oz |
| Via covering | Epoxy Filled & Capped, $0.00 |
| Minimum via hole / diameter | 0.3 mm / (0.4 / 0.45 mm) |
| Outline tolerance | +/-0.2 mm (Regular); +/-0.1 mm (Precision) disabled |
| Layer sequence / stackup | Not specified / not specified |
| Confirm Production file | No |
| Electrical test | Flying Probe Fully Test |
| PCB Assembly, Stencil | Off |
| Build time | 7-8 days, $0.00 |
| Web price, quantity 5 | $32.00 ("Special Offer"), plus a $26.60 shipping estimate |

Display-only price probes (all restored to the defaults afterwards):

| Selection (quantity 5, 7-8 days) | Via Covering line | Surface Finish line | Web price |
|---|---|---|---|
| OSP + Epoxy Filled & Capped (default) | $0.00 | $0.00 | $32.00 |
| ENIG + Epoxy Filled & Capped | $0.00 | $16.80 | $48.80 (inferred from the line items, not read) |
| ENIG + Epoxy Filled & Untented | $0.00 | $16.80 | $48.80 |
| ENIG + Copper paste Filled & Capped | $332.61 | $16.80 | $382.46 (includes a transient "Confirm Production file $1.05" line) |

Faster builds cost more: 3-4 days +$132.40, 2-3 days +$198.50. The shipping
estimate was $26.60 (UPS Express Saver DDP, 2-4 business days, 0.16 kg). The
"Desktop Price" toggle (a JLCONE promotion), the coupon panel and "Save to
cart" were not used.

## Vias and via protection (the main open question)

File: 169 through vias, all F.Cu to B.Cu. No blind, buried or HDI vias.

| Land / drill (mm) | Count |
|---|---|
| 0.5 / 0.3 | 111 |
| 0.6 / 0.3 | 42 |
| 0.604 / 0.35 | 12 |
| 0.75 / 0.5 | 4 |

The design requires these vias to be resin-filled, planarized and
copper-capped (via-in-pad). Positions are KiCad board-file coordinates in mm
(Y down), not Gerber or drill-file coordinates:

| Via | Land / drill | Position | Flags in the PCB file |
|---|---|---|---|
| U4 thermal (4 vias) | 0.604 / 0.35 | (110.400323, 89.587211), (110.400323, 90.237211), (111.050323, 89.587211), (111.050323, 90.237211) | none |
| C24.2 | 0.6 / 0.3 | (92.004083, 93.491669) | none |
| C7.1, GND | 0.5 / 0.3 | (109.311336, 92.500014) | `(capping yes)(filling yes)` |
| GAIN0.1, GND | 0.5 / 0.3 | (100.660031, 108.335848) | `(capping yes)(filling yes)` |

The U4 and C24 requirement is recorded in
[device-component-selection.md](../../../../docs/device-component-selection.md)
(about line 141) as a quotation requirement, not a verified service or cost.
C7.1 and GAIN0.1 are owner-approved via-in-pad exceptions that close opens
(IPC-4761 Type VII, to be stated on the order). The board default is
`(filling no)(capping no)`, so the five U4/C24 vias are protected only by the
written order note.

Live Via Covering choices for this board:

| Choice | State | Price at quantity 5 |
|---|---|---|
| Tented | disabled | - |
| Plugged | disabled | - |
| Epoxy Filled & Untented | enabled | $0.00 |
| Epoxy Filled & Capped | enabled, default | $0.00 |
| Copper paste Filled & Capped | enabled | +$332.61 |

Tooltips, quoted from the live page:

- Epoxy Filled & Capped (the default): "Vias should be at most 0.5 mm in
  diameter to avoid incomplete filling. Vias violating this size will be left
  unfilled." and "Vias are filled with epoxy resin and then plated over with
  copper to create a flat, solderable surface. Ideal for via-in-pad,
  multilayer boards, and thick boards."
- Epoxy Filled & Untented: "Soldermask is removed over the via and its annular
  ring. The via will be solderable and has the same surface finish as regular
  pads." and "Vias <= 0.3mm will be filled with epoxy resin, the via covering
  will be made according to your design (untented), which is named POFV
  process. This won't affect the testing; Vias > 0.3mm won't be filled." and
  "If you don't need to fill epoxy resin with those vias <= 0.3mm, please
  make a remark when placing an order."
- Copper paste Filled & Capped: tooltip not read.

**The ambiguity.** Neither tooltip says whether "diameter" means the drill or
the land (pad). The public page's "via diameters 0.15 to 0.55 mm" is equally
unspecific. The two readings give different answers for this board:

- If the Capped limit means **land** diameter, 58 vias would be left unfilled:
  42 x 0.6/0.3, 12 x 0.604/0.35 and 4 x 0.75/0.5. That includes the four U4
  thermal vias and C24.2, the ones the design requires filled. C7.1 and
  GAIN0.1 (0.5 land) would still qualify.
- If it means **drill** diameter, all 169 vias qualify (drills are 0.3, 0.35
  and 0.5 mm). Under the Untented tooltip's "<= 0.3mm" the 12 x 0.35 mm and
  4 x 0.5 mm drills would not be filled, but only for that option.

**Selected 2026-11-10 (delegated by the owner): Epoxy Filled & Capped,**
the live default at $0.00. It matches the non-conductive resin intent.
Copper-paste fill (+$332.61) is not needed. The drill-or-land question stays
open, so:

1. Use the draft order note below, which names the seven vias and says to
   stop and contact us before substituting.
2. At ordering, consider "Confirm Production file". A transient $1.05 line
   with that name appeared once during probing; the price is unverified.
   The option shows JLC's production files before manufacture.
3. Ask question 1 below if JLC's engineers do not answer it.

Under the drill reading, all 169 vias qualify.

This is a supplier question and an owner decision. Do not change the vias,
the stackup or the covering to get around it. If the supplier's rule excludes
any via in the table above, stop and ask the owner before substituting
tenting or plugging. Do not claim vendor IPC-4761 Type VII certification.

## Surface finish

- File: `copper_finish "None"` in the stackup, which is not an order choice.
- Public page: HASL, ENIG or OSP; boards with 6 or more layers do not support
  HASL.
- Live: OSP is the default at $0.00; ENIG adds $16.80 at quantity 5 and shows
  a Gold Thickness row (1 U" selected, 2 U" available). HASL choices are
  disabled.
- Owner decision. General practice, not a JLC claim: ENIG is flatter and keeps
  fine-pitch pads and bare test lands solderable longer, while OSP is cheaper
  and suits a single reflow soon after fabrication. The board has an RP2040
  QFN, an LSM6DSOX LGA and bare test lands (TP3 to TP16, plus TP5 as a 0.30 mm
  microprobe land), so ask JLC for advice before choosing.
- **Decided 2026-11-10: ENIG, 1 U" gold.** The owner chose ENIG for corrosion
  resistance. It also suits the QFN/LGA pads and the bare test lands. 1 U" is
  enough: the board has no edge fingers, and the battery contacts are
  soldered parts, not plated pads that wear.

## Stackup, thickness and impedance

- File: stackup sums to 1.6504 mm (copper 0.1308 + dielectric 1.5196);
  `general.thickness` is 1.6. Roles are S/G/S/S/G/S with In1 and In4 as GND.
  The intended construction is JLC06161H-3313E (finished 1.65 mm +/-10 %).
- Public page: thickness tolerance +/-10 % for 1.0 mm and up (1.65 mm gives
  1.485 to 1.815 mm); 3313 prepreg Dk 4.1; the page recommends specifying
  finished thickness in the order notes.
- Live: only 1.6 mm is offered near this value (0.8, 1.0, 1.2, 1.6 and 2.0 mm
  are enabled). "Specify Stackup: Yes" exists and links to JLC's impedance
  calculator; it was not used.
- Impedance: none requested and none claimed. USB was routed as separate
  traces; see work package R2 in the review doc.
- Question: what construction does the 1.6 mm six-layer option build, and does
  it match the S/G/S/S/G/S intent?

## Copper and track/space

- File: minimum track 0.15 mm and minimum clearance 0.15 mm (1167 track items
  at 0.15 mm).
- Public page: multilayer 1 oz 0.09/0.09 mm; 2 oz 0.15/0.15 mm; width
  tolerance +/-20 %. There is no separate inner-layer row, so whether the 1 oz
  figures apply to our 0.5 oz inner layers is open. Our minimums equal the
  2 oz row and are larger than the 1 oz row.
- Live: outer 1 oz and inner 0.5 oz defaults; price changes for 2 oz outer or
  1 oz inner were not observed.

## Outline and tolerance

- File: closed 163-segment outline, 44.5 x 48.35 mm bounding box, perimeter
  150.683 mm, area 1523.74 mm2. The project edge-copper rule is 0.3 mm.
- Public page: routed-edge tolerance +/-0.2 mm regular, +/-0.1 mm high
  precision. High precision needs a board of at least 50 x 50 mm with at
  least 3 tooling holes of 1.5 mm or more. Edge-copper clearance is at least
  0.2 mm.
- Live: Precision is disabled; Regular +/-0.2 mm is selected.
- Owner decision: is +/-0.2 mm acceptable for the PCB mounts in the printed
  cartridge and for the BT1/BT2 contact bases? This ties to work package R4.
- **Selected 2026-11-10 (delegated by the owner): Regular +/-0.2 mm.**
  Precision cannot be ordered for this board: it needs at least 50 x 50 mm
  and tooling holes. The 0.3 mm edge-copper rule exceeds the tolerance. The
  printed cartridge mounts are designed to adapt to the board, so R4 must
  give them +/-0.2 mm clearance in addition to the print tolerance. The
  board design is unchanged.

## Holes, slots and drill files

- File: PTH 175 (0.300 round 153, 0.350 round 12, 0.500 round 4, 0.600 slots
  4, 2.200 round 2) and NPTH 2 (0.65 round). The 169 vias account for the
  round 0.3, 0.35 and 0.5 mm holes. The four plated slots are the X6 USB
  shell anchors: 0.6 mm wide, overall length 1.4 mm (two) and 1.7 mm (two).
  The two plated 2.2 mm holes are MH1/MH2 (4.4 mm pads, at (110.0, 115.7) and
  (90.0, 84.3)). The two NPTHs are X6 locating holes with no copper ring, at
  (97.11, 78.38) and (102.89, 78.38). All positions are board-file
  coordinates (Y down).
- Public page: plated slot width minimum 0.5 mm (2-layer) or 0.35 mm
  (multilayer; the page is inconsistent), slot length at least twice the
  width; minimum NPTH 0.50 mm; rectangular holes are not supported.
- Questions:
  - Is the slot encoding in the Excellon files accepted by JLC's CAM (G85 slot
    format)? The verifier read the slots itself; JLC's acceptance is
    unobserved.
  - Does "length" mean the overall slot length or the segment between end
    centres? Overall length gives 2.33x and 2.83x the width; the end-centre
    reading would give 1.83x and 1.33x, below the 2x rule.
  - Does the NPTH annular-ring row (at least 0.45 mm) apply to the copper-free
    X6 NPTHs?

## Via and hole geometry against the public page (screens)

| Screen | Result | Public-page figure |
|---|---|---|
| Via land minus drill | 0.200 / 0.300 / 0.254 / 0.250 mm (ring 0.100 / 0.150 / 0.127 / 0.125 mm) | via land 0.1 mm larger than the hole (0.15 mm preferred) |
| Smallest via | 0.3 mm drill, 0.5 mm land | live label 0.3 mm / (0.4 / 0.45 mm), read as hole / (minimum / preferred diameter) |
| Component PTH rings | X6 0.25 mm; MH1/MH2 1.10 mm | PTH ring 0.20 recommended, 0.15 absolute minimum (multilayer 1 oz) |
| Via-to-via hole-edge gap | smallest 0.2786 mm; none below 0.25 mm; 18 pairs below 0.45 mm (context only) | 0.2 mm via-to-via |
| Pad-involved hole gap | smallest 0.5790 mm; none below 0.45 mm | 0.45 mm hole-to-hole for pads |
| Via-in-pad | 18 via/pad pairs, 7 with the via fully inside | screen only |

If the page's PTH annular-ring row were applied to vias, the 111 x 0.5/0.3
vias (ring 0.100 mm) would fall below its 0.15 mm absolute minimum. The
via-diameter rule is the one that names vias, so this is read as not
applying, but it is a JLC question.

**Not screened:** hole-to-copper, pad-to-track and SMD pad-to-pad spacing,
via-hole-to-track, PTH/NPTH-to-track, minimum SMD pad size, mask-to-trace
spacing, mask bridge, mask coverage of traces, same-net spacing, inner-layer
via and PTH hole-to-copper, edge-to-copper 0.3 mm versus the page's 0.2 mm,
and pad-to-silk spacing. Only JLC's CAM or DFM can answer these.

## Mask and silk

- File: pad-to-mask clearance 0, tenting on. The DRC snapshot lists 5
  `silk_edge_clearance`, 69 `text_height` (against the project's 0.8 mm
  minimum), 2 `text_thickness`, 47 `silk_overlap` and 90 `silk_over_copper`
  findings.
- Public page: mask openings at least 0.09 mm from neighbouring traces; mask
  bridge 0.10 mm (0.13 mm for black or white); silk line width at least
  0.15 mm; text height at least 1.0 mm; width-to-height ratio 1:6; pad-to-silk
  0.15 mm.
- Live: silkscreen is white only. Colours offered: green, purple, red, yellow,
  blue, white, black.
- Owner decision: at least 69 text items are below the project's 0.8 mm
  minimum and so below the page's 1.0 mm figure. Legibility is a cosmetic call
  and is not covered by the scoped owner silk waiver, which is limited to the
  C1/C4 relocation labels over pads. Do not extend it.

## Panelization

- Public page: an SMT assembly panel is at least 70 x 70 mm with 5 mm tooling
  edges, 2 mm tooling holes and 1 mm fiducials. Mouse-bite spacing is 1.6 or
  2 mm with 4 mm tabs (5 mm with mouse bites). V-cut tolerance is +/-0.4 mm
  with at least 0.4 mm copper clearance.
- File: the board is 44.5 x 48.35 mm, below that minimum, so assembly needs a
  panel (Panel by JLCPCB or by customer). A bare-PCB quote can stay a single
  PCB.
- Question: how does JLC panelize a round outline with USB tongues? A round
  outline is not suited to V-cut (an inference); do not place tabs over
  contacts or service features.

## Quantity, colour and lead time

Live: quantity 5 at $32.00 for a 7-8 day build, plus $26.60 shipping. The
"Special Offer" label is promotional. AGENTS.md records an earlier
owner-observed six-layer quote of about US$35-49 (five pieces, November 6),
which was not re-checked and was not for this file. Quantity, colour and lead
time are owner decisions.

## Draft order notes (owner to confirm before use)

These are draft remarks for the order form, not submitted anywhere.
Coordinates are KiCad board-file coordinates in mm with Y down, not Gerber or
drill-file coordinates.

```text
DRAFT - owner to confirm. Board-file coordinates (mm, Y down).

Via protection required by the design (please confirm you can do this):
fill with non-conductive resin, planarize and cap with copper
(IPC-4761 Type VII is the design intent):
  U4 thermal vias, 0.604 land / 0.35 drill, at
    (110.400323, 89.587211) (110.400323, 90.237211)
    (111.050323, 89.587211) (111.050323, 90.237211)
  C24 pad 2 via, 0.6 land / 0.3 drill, at (92.004083, 93.491669)
  C7 pad 1 via, 0.5 land / 0.3 drill, at (109.311336, 92.500014)
  GAIN0 pad 1 via, 0.5 land / 0.3 drill, at (100.660031, 108.335848)
If any of these cannot be filled and capped, stop and contact us before
substituting tenting or plugging.

Stackup: 6 layers, intended JLC06161H-3313E style (S/G/S/S/G/S),
finished thickness about 1.65 mm. Please confirm what the 1.6 mm option
builds. No impedance control requested.
Surface finish ENIG; via covering Epoxy Filled & Capped (as selected).
Four plated slots (X6 shell anchors): 0.6 mm wide, 1.4 and 1.7 mm long.
```

## Questions for JLC (fabrication)

1. For Epoxy Filled & Capped, does the 0.5 mm limit refer to the drill or the
   land, and will the five U4/C24 vias and the two POFV vias be filled and
   capped as listed?
2. Is the 0.1 mm via ring on the 111 x 0.5/0.3 vias acceptable?
3. Do the 1 oz track/space figures apply to 0.5 oz inner layers?
4. Is the slot encoding accepted, and how is slot length measured?
5. Does the NPTH annular-ring row apply to the copper-free X6 NPTHs?
6. What does the 1.6 mm six-layer option build, and does it match the
   intended stackup?
7. How is a round outline with USB tongues panelized for assembly?

The remaining gates before any order are in
[unresolved-before-ordering.md](unresolved-before-ordering.md).
