# USB-C connector: source fidelity and quotation gate

September 14, 2026. This is a source/manufacturing review, not a selected
replacement footprint or vendor approval. It applies to X6 in the initial
and power-rework routing candidates. Preserve the pinned EAGLE source and
the archived KiCad reference; correct the active derivative separately.

## Identity is not yet an approved land pattern

The pinned Adafruit 5768 EAGLE device carries `LCSC=C165948` under the generic
package alias `USB_C_CUSB31-CFM2AX-01-X`. The local BOM has `USB Type C` and no
approved manufacturer order code. The reviewed JLC listing identifies
**HRO / Korean Hroparts Elec TYPE-C-31-M-12**, C165948. The old package alias
is not a separately qualified alternative part number.

The current JLC-linked one-page drawing was retrieved with SHA-256
`6ae33d50ac47820114661138dc4e4659f40fdc5d4f485b46685dfec338da1a9e`.
The parent has now downloaded those exact bytes and visually read the full
page and detailed crops, including contrast-enhanced views that retain the
watermark. The original PDF is unchanged and remains session-local.
[The current product page](https://jlcpcb.com/partdetail/Korean_HropartsElec-TYPE_C_31_M12/C165948)
provides expiring download links; do not commit signed URLs or credentials.
The actual drawing is dated **2020-12-08, revision A** and names
`TYPE-C-31-M-12`, despite its generic `DETECTOR SWITCHS` title. Do not
redistribute the PDF or silently substitute the older drawing.

An [older distributor-hosted HRO drawing](https://electronilab.co/wp-content/uploads/2021/05/ConectorUSB_C_Korean-Hroparts-Elec-TYPE-C-31-M-12.pdf)
has SHA-256 `10f5c109651db799ec59d9cf3d7a343886569807ae03d3dd9094df92bf156e1d`;
it is not the same file. The
[published KiCad HRO footprint](https://github.com/KiCad/kicad-footprints/blob/master/Connector_USB.pretty/USB_C_Receptacle_HRO_TYPE-C-31-M-12.kicad_mod)
is useful secondary implementation evidence, not a substitute for the selected
part's drawing. Pin its actual revision and follow its license before any reuse.

## Definite mechanical import loss

The pinned EAGLE package contains elongated layer-46 milling openings. The
actual imported/native X6 instead has **four round 0.6 mm plated drills**.
Oval copper around a round drill does not create a plated slot.

| Anchor pair | Source opening | KiCad-local center after EAGLE Y conversion |
|---|---|---|
| M1/M2, rear row | 0.6 x 1.7 mm capsule | (+/-4.32, -1.70) mm |
| M3/M4, mouthward row | 0.6 x 1.2 mm capsule | (+/-4.32, +2.48) mm |

The source is
`hardware\reference\adafruit-5768\upstream\Adafruit Feather RP2040 Prop-Maker.sch`,
package milling lines 10410-10437. Its source revision remains
`408fa9a40c0a01a3a65497ef42a29e0b08fe711e`.
This is an additional source-to-drill fidelity finding; ERC/net equivalence
and the previous clearance report did not establish correct anchor openings.

Simply restoring the 1.7 mm slot inside the current 2.0 mm-long land leaves
only **0.15 mm nominal end annulus**. The land and process must be reviewed
together. The secondary KiCad implementation uses rear 1.0 x 2.1 mm lands
with 0.6 x 1.7 mm slots and front 1.0 x 1.6 mm lands with 0.6 x 1.2 mm slots.
Its signal lands, row position and numbering also differ; do not paste it
into the circuit without the complete mapping and drawing review.

## The four existing clearance findings

These are locator **NPTH-to-F-copper** distances, not hole-to-hole spacing.
The two locators are diameter 0.650 mm; the four neighboring copper lands
are 0.575 x 1.150 mm. Native board coordinates below include the (100,100)
board translation.

| Copper pad | Copper center, mm | Locator center, mm | Actual nominal gap, mm |
|---|---|---|---|
| A1B12, GND | 103.200, 79.455 | 102.890, 78.380 | 0.175506 |
| A4B9, VBUS | 102.400, 79.455 | 102.890, 78.380 | 0.214450 |
| B1A12, GND | 96.800, 79.455 | 97.110, 78.380 | 0.175506 |
| B4A9, VBUS | 97.600, 79.455 | 97.110, 78.380 | 0.214450 |

The project minimum is 0.25 mm. The reviewed JLC capability is 0.20 mm;
the two 0.175506 mm gaps fail even that. PCBWay publishes normal 0.20 mm
and minimum 0.15 mm; meeting its absolute minimum would not establish the
common two-vendor process or fix the lost slots. Do not lower the global rule
or trim copper without establishing terminal overlap and the correct pattern.

Official capability evidence:

- [JLC PCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities) and
  [NPTH guide](https://jlcpcb.com/blog/npth-design-guide).
- [PCBWay tolerances](https://www.pcbway.com/pcb_prototype/PCB_Manufacturing_tolerances.html),
  [capabilities](https://www.pcbway.com/capabilities.html) and
  [plated slots](https://www.pcbway.com/pcb_prototype/Plated_through_slots.html).

Both publish 0.5 mm minimum plated-slot width. JLC's two-layer slot length
is at least twice its width. Its two-layer 1 oz PTH annulus is 0.25 mm
recommended, 0.18 mm absolute minimum; the source-restored 0.15 mm end ring
is insufficient. JLC publishes +0.13/-0.08 mm plated-opening tolerance and
0.05 mm position tolerance. PCBWay lists PTH +/-0.08 mm and NPTH +/-0.05 mm;
confirm the chosen slot process. Nominal rule compliance is not a complete
finished-hole/lead/tolerance stack or supplier acceptance.

## Electrical, paste and assembly invariants

Preserve CC1=A5, CC2=B5, D+=A6/B6, D-=A7/B7, GND=A1B12/B1A12 and
VBUS=A4B9/B4A9. SBU A8/B8 remain explicitly NC. M1-M4 remain unassigned;
do not accidentally bond raw CELL_NEG through the shield or hardware.

X6 is fitted but its native footprint attributes are currently zero, not
`FP_SMD`. An SMD-only placement export can therefore omit this mixed-mount
connector. Include X6 explicitly in the 83-part assembly population, along
with both B-side SMT battery contacts.

The current footprint has eight explicit F.Paste polygons: four reduced
outer power/ground rectangles and four anchor polygons. Eight inner signal
lands have automatic paste. Do not globally enable paste or duplicate these
apertures. True slots require review of anchor paste volume and the assembly
provider's reflow/secondary-solder process.

The native origin (0,-22.820), manifest proxy center (0,-23.935) and source
F.Fab rectangle center (0,-24.225) mm are different. None is an approved pickup
datum. Qualify the component-side convention, centroid and supplier rotation
using a drawn witness. The existing 0.1234 mm nominal inner mask web also
depends on the eventual copper weight, solder-mask process and color.

## Required next revision

The [dimension and authorized-candidate register](../hardware/handbell/parts/hro-usb-candidate.json)
separates literal drawing values, derived coordinates and intentional project
deviations. **The current drawing differs from both the old EAGLE source and
the cited stock KiCad implementation.** In particular, its mouthward slots
are **0.6 x 1.4 mm**, not 0.6 x 1.2 mm; recommended locators are 0.60 mm, not
0.65 mm. Its 1.14 mm signal lands are essentially aligned with the original
Adafruit lands, not the stock KiCad row's larger rearward offset.

The authorized X6-only engineering variant retains the source's 0.65 mm
locators and inner signal lands. It uses actual 0.6 x 1.7 / 0.6 x 1.4 mm
plated slots, with enlarged 1.1 x 2.2 / 1.1 x 1.9 mm oval copper lands for
0.25 mm nominal annulus. Only the four outer combined GND/VBUS lands and
their reduced paste apertures move 0.20 mm rearward, away from the locating
holes. Their original sizes remain intact. Their new nominal Y interval
[-3.05,-1.90] mm still contains the complete nominal terminal projection
[-2.67,-2.27] mm; this is not a guaranteed worst-case terminal/placement stack.
The global clearance rule is not reduced. For the quote baseline, remove the
four anchor paste polygons and explicitly require **secondary soldering of
all four plated anchors after the SMT operation**. This avoids inventing a
qualified pin-in-paste volume from the old overprinted rectangles. Supplier
acceptance, short-tail wetting and barrel fill remain open; the anchors must
not simply be left unsoldered. Intrusive reflow would require a separately
reviewed stencil/process revision, not an undocumented supplier assumption.

This is a **drawing-supported, explicitly modified engineering footprint**,
not a claim of exact manufacturer-recommended geometry or physical
qualification. No stock KiCad CAD is imported. The new routing-candidate owner
has the implementation instructions; native copper/mask/paste/drill and
electrical mapping evidence are still required.

The side view shows a 3.26 mm body height above the SMT seating plane and four
tails 1.01 mm below it, with 0.10 mm general tolerance and a 0.10 mm seating
profile callout.
The tails therefore nominally end inside a 1.6 mm PCB; do not assume visible
tail protrusion or an already qualified through-hole solder process. Keep
the existing conservative B-side reservations.

The body drawing supports the existing nominal 8.94 x 7.35 mm body and mouth
datum. However, the 6.28 +/-0.15 mm mouth-to-locator dimension requires a
front component bound at y=-28.05, beyond the old nominal-only proxy. That
leaves only 0.05 mm to the current bezel rear plane. The next mechanical
revision must restore useful clearance without hiding the component bound;
moving only the printed bezel 0.15 mm outward would recover the earlier
0.20 mm screening gap without changing PCB/mouth datums or wall thickness.
That adjustment and the new exact full-CAD bind are not yet implemented.

Preserve the frozen reference and routed checkpoints. Component/PCB/placement
tolerances, actual part fit, supplier assembly operation, cable mating and
mechanical qualification remain separate gates.

Track through E02/#2 source fidelity, E04/#4 schematic/footprint, E05/#5
mechanical interface, E07/#7 layout and E08/#8 fabrication quotation.
No quote-ready Gerbers or manufacturing order follow from this investigation.
