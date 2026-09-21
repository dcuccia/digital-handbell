# JLCPCB and PCBWay quotation handoff

## Owner-requested endpoint

On September 13 the owner requested Gerbers and associated assets they can
upload for **full PCB fabrication plus PCBA quotations at JLCPCB and PCBWay**.
The handoff must therefore extend beyond the current partial-routing
checkpoint. This authorizes preparing local/public project assets, not
uploading to suppliers, requesting quotes on the owner's behalf, purchasing
parts or approving manufacture.

**Current status: planned deliverable, not an available quote-ready package.**
Power corrections, remaining routing, final part/placement consistency and
manufacturing inputs are still being developed. Do not generate an unrouted
placeholder ZIP and call it the completed handoff.

The [initial BOM-readiness audit](pcba-bom-readiness.md) separates recoverable
identities from genuinely unselected parts and records the exact population,
package-envelope corrections and sourcing/process work still required.
The [USB qualification study](usb-connector-qualification.md) also records
lost anchor-slot geometry in the import, the four real locator-to-copper
clearances, mixed-mount placement/paste concerns and the required
drawing-supported correction. This is not resolved by a global DRC waiver.

## Package contents

Prepare supplier-specific BOM/placement files with the same versioned native
design and fabrication data. Include a concise upload guide and source hashes.

| Asset | Required project content |
|---|---|
| Gerber ZIP | Actual final copper, solder mask, silkscreen and unambiguous board outline; top/bottom paste data for assembly/stencil use. Include no stale or conflicting exports. |
| Drill data | Matching Excellon plated/nonplated holes and slots, with the same units and datum as the Gerbers. |
| JLCPCB BOM | Comment/specification, designators and footprint in the supported format; also retain exact manufacturer/MPN, per-board quantity and a reviewed JLCPCB/LCSC code where available. Missing sourcing codes are explicit sourcing questions, not invented catalog matches. |
| PCBWay BOM | Manufacturer/MPN, designators, per-board quantity, package, description, assembly type and distributor references/notes in its turnkey template. |
| Placement/CPL | Per-fitted-part reference, true placement centre, X/Y in mm, side and rotation mapped to each supplier's convention. Use one documented fabrication/placement datum. |
| Assembly drawings | Front/back views with reference designators, pin 1, diode/LED polarity, battery-contact orientation and explicit fitted/DNP distinctions. |
| Fabrication/assembly notes | Layer count, thickness, copper/process assumptions, finish, mask/silk, tolerances needing confirmation, panel/tooling strategy, component overhangs and via/stencil treatment. |
| Reference models | Source-bound populated STEP/3D views, explicitly identifying simplified bodies; these supplement rather than replace placement and manufacturing data. |
| Release inventory | Native source revision/hash, BOM population, tool versions, exercised export commands, file hashes and the correct hardware attribution/license notices. |

Do not assume an imported EAGLE footprint's anchor is its component's pick-up
centre. Split-land battery contacts and USB need particular centre/orientation
attention. Check pin-1 and bottom-side conventions against the actual assembly
views rather than applying an unexplained global rotation correction.

## What "full PCBA" includes

The current population is **81 front electronic parts and two rear Keystone
254 SMT battery contacts**. Both contacts belong in the assembly BOM and
placement list. The supplier may choose an appropriate assembly operation,
but its price must include fitting them; do not describe this as purely
single-sided assembly or silently leave those contacts for the owner.

X6 also belongs in the fitted population even though its present mixed-mount
footprint lacks the SMD-only export attribute. Its plated anchors and the tall
rear contacts need explicit assembly-operation confirmation. The current
contact model reaches 16.59 mm from the B face; this is nominal geometry, not
a verified machine-height allowance or maximum qualified part dimension.
Include any necessary secondary soldering/fixture operation in the quote
rather than assuming both sides fit a standard automated process.

Derive the final population from the actual approved variant. Exclude DNP,
copper-only/test-feature references and mechanical holes from fitted component
quantities while documenting their intended status separately. All BOM,
placement and assembly-view references must agree.

Unless later requested, the board quotation excludes the battery, speaker,
printed enclosure/handle, mechanical assembly and shipping assumptions.
Factory firmware programming or functional testing requires an explicit
image/test specification; neither is silently included or claimed complete.
The owner chooses quantities and service options in the supplier's quote
workflow.

## Readiness and dependencies

The [September 15 land/process dispositions](device-component-selection.md#september-15-remaining-land-and-assembly-dispositions)
retain the remaining native copper for routing and distinguish supplier
questions from PCB changes. The quotation baseline must explicitly include
resin-filled/copper-capped treatment of U4's four named thermal vias on the
current two-layer board, subject to supplier availability and price.
Ordinary tenting is not a silent substitute. Ask for review of the existing
paste data against a proposed 0.10 mm stencil, including U1, U4, Q5, both
diodes and all connector/anchor operations; this is not an approved common
reflow profile. Any accepted stencil revision must be reflected in matched,
versioned exports before manufacture.

The subsequent VHI/core corridor revision relocates the nine MCU ground vias
while retaining their count, drill/diameter and existing exposed-pad mask/paste.
Use the coordinates in `reports/core-power-corridor.json` for MCU
stencil/via-treatment review; do not reuse an old thermal-via map or infer
thermal/process equivalence from the unchanged count. This is separate from
the four explicitly specified U4 filled/capped vias.

1. Correct the boost hot loop and protector sense routing, then complete the
   remaining signal, control, USB, power/return and BTL connections.
2. Resolve actual part identities and relevant electrical/package/height
   evidence. Generic value/footprint placeholders are not a complete sourced
   turnkey BOM.
3. Review copper/current assumptions, manufacturing-critical geometry and
   supplier process needs. Do not suppress the known USB clearance findings.
   The thermal-pad vias and under-resistor transition require explicit
   process/stencil treatment, not an unmentioned assumption.
4. Rebind the complete mechanical model to the exact final candidate, including
   moved component bodies, contacts and service-label visibility.
5. Export and inspect matched fabrication, drill, BOM and placement assets.
   Confirm full fitted-population parity and supplier-specific data mapping.
6. Publish the quote-only handoff with any supplier confirmation questions
   or separately priced process options stated clearly.

Request supplier panelization/tooling guidance for the circular, protruding-
connector board rather than inventing a production panel or placing breakaway
tabs over contacts/service features. Any subsequently panelized fabrication
and placement data must remain coordinated.

**Quote-ready does not mean production- or child-use-qualified.** Prototype
powered/thermal/acoustic testing cannot be claimed before hardware exists.
Those later gates need not be misrepresented as completed to obtain a quote.
Conversely, unfinished routing or an ambiguous population cannot be hidden
inside a package presented as the completed board. A quote does not authorize
placing an order or waive later owner approval.

## September 21 layer-count assessment

The owner requested a comparison of two, three and four copper layers for
**JLCPCB Standard PCBA**, not a stackup change or supplier submission.
The [engineering assessment](pcb-closure-plan.md#layer-count-reassessment-requested-september-21)
recommends evaluating a separate four-layer candidate before further
two-layer-only repairs. The accepted package remains two-layer and unrouted.

Copper layers and component faces are independent. With the same 83 fitted
parts, four layers do not turn the job into four-sided assembly or remove
the two rear contacts. The BOM and placement count need not increase, while
PCB fabrication adds inner-layer imaging, lamination and registration.
Matched exports would need the new internal copper layers and stackup notes,
as well as revalidated drill/plane clearances and existing paste/assembly data.

Compare **total delivered assembled-board cost**, not an advertised bare-PCB
promotion: PCB/panel fabrication, via fill/capping and finish, parts and
procurement attrition, front/back setup and stencils, placement/X-ray,
secondary soldering or fixtures, then shipping and tax. At quantity Q, a
batch-level fabrication/process increase of D adds D/Q per assembled board
only if panel yield, assembled quantity and all other charges remain equal.
No exact two-versus-four-layer project price has been obtained.

Standard PCBA must explicitly cover the nominally 16.59 mm tall rear contacts
and all four USB plated anchors. Extra copper layers do not resolve machine
height, retention through reflow, fixture access or secondary-solder needs.
Keep U4's resin-fill/planarization/copper-cap requirement separate from ordinary
via tenting; also review the changed MCU thermal-via map. Supplier process
availability and pricing must be confirmed for the selected layer count.

### Current JLCPCB evidence

Public official pages checked September 21, 2026; no files were uploaded,
no supplier was contacted and no project-specific quote was obtained.

| Topic | Published evidence and project consequence |
|---|---|
| Three layers | The [quote-page](https://cart.jlcpcb.com/quote/) tooltip says odd counts such as three are fabricated as the next even count. Compare two versus four, not a cheaper three-layer intermediate. |
| Four-layer stackup | [Impedance/stackup selections](https://jlcpcb.com/impedance) include nominal 1.6 mm four-layer boards. Select the actual dielectric/copper construction before reviewing USB geometry; nominal layer count alone does not define impedance or return coupling. |
| Required via treatment | [POFV guidance](https://jlcpcb.com/news/free-via-in-pad-6-20-layer-pcbs-pofv) explicitly charges extra for four-layer filling/capping; its free offering begins at six layers. [Via-covering guidance](https://jlcpcb.com/help/article/pcb-via-covering) describes epoxy fill, levelling and copper capping. Two-layer eligibility and the exact four-layer surcharge remain unverified. |
| Assembly service | [C481766 / LSM6DSOXTR](https://jlcpcb.com/partdetail/Stmicroelectronics-LSM6DSOXTR/C481766) is Standard Only and requires X-ray. Standard remains necessary even if the rear contacts receive a secondary operation rather than a normal second SMT pass. |
| Handling size | [Standard PCBA capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities) specify a 70 x 70 mm minimum single board/panel and require rails/fiducials. The D43 board therefore needs a compatible carrier/panel; layer count does not fix this. |
| Circular panel | [PCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities) allow circular JLC-panelized units from 20 x 20 mm, with mouse-bite connections and tooling strips on four sides. SMT tooling edges are 5 mm. Tab locations, residual edges, USB access and contact clearance require coordinated review. |
| Contact height | No reliable current official numeric top/bottom component-height limit was verified. The capability table's PCB-thickness "No limit" is not a component-height allowance. The nominal 16.59 mm contacts remain a process/fixture acceptance question. |
| Secondary operations | [Mechanical-component guidance](https://jlcpcb.com/help/article/introduction-smt-mechanical-assembly-components) provides a secondary-processing request mechanism, not acceptance of these contacts or X6. Specify all four anchor joints and the required outcome explicitly. |
| Timing | Standard capabilities publish assembly build time of at least four days, not total delivered lead time. Procurement, PCB fabrication, special processes, review, secondary work and shipping remain additional dependencies. |

The [detailed assembly price table](https://jlcpcb.com/help/article/pcb-assembly-price),
marked updated September 9, 2026, lists these USD amounts with an exchange-rate
caveat. They are published fee examples, not a quote:

| Standard PCBA item | Single face | Both faces |
|---|---:|---:|
| Setup/engineering | $25.56 | $51.12 |
| Stencil | $8.21 | $16.42 |
| Setup plus stencil subtotal only | $33.77 | $67.54 |

The same table lists SMT assembly at $0.0016 per solder joint for the
1-50,000-joint tier, feeder loading at $1.53 for Basic/Extended parts,
manual assembly at $0.0164 per joint for the 1-10,000-joint tier, and
hand-soldering labour at $3.58 per order. Parts, X-ray, applicable fixtures,
packing and other charges are additional. These fees are not multiplied by
the copper-layer count. The $67.54 double-face subtotal, if charged once
for a batch, allocates to $6.754 at ten assembled boards or $0.6754 at one
hundred; those numbers are neither total unit costs nor the four-layer premium.
If contacts are handled by a different operation, the supplier must quote
that actual process rather than blindly applying both SMT and manual fees.

Published process tables are not completely consistent. For filled vias,
the capabilities table lists 0.15-0.55 mm diameters, the covering guide
warns against holes over 0.5 mm, and the POFV announcement gives 0.2-0.5 mm
plus hole-separation/annular-ring conditions. U4's 0.35 mm nominal drill
being within those ranges does not establish the full local-pattern
acceptance. Do not invent a combined guaranteed rule or claim IPC-4761
Type VII certification not stated by the vendor. Similarly, prefer the
current detailed price table to conflicting older FAQ fees.

## Official file-format sources

Read on September 13, 2026; vendor templates may change before final export.

- [JLCPCB BOM requirements](https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly):
  lists Comment, Designator and Footprint, and CSV/XLS/XLSX. The project adds
  explicit sourced identities beyond those minimum upload fields.
- [JLCPCB placement requirements](https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly):
  Designator, centroid Mid X/Mid Y in mm, Top/Bottom layer and rotation;
  positive rotation is counterclockwise.
- [PCBWay assembly-file requirements](https://www.pcbway.com/assembly-file-requirements.html):
  turnkey BOM fields, RS-274X copper/silk/paste data, component centroid/side/
  rotation, and recommended supplemental assembly instructions.
- [PCBWay required production files](https://www.pcbway.com/helpcenter/pcb_assembly_ordering/What_files_are_requested_for_assembly_production_.html):
  Gerber/BOM/silk/centroid, mm coordinates and polarity/reference guidance.
- [PCBWay BOM field specification](https://www.pcbway.com/helpcenter/pcb_assembly_ordering/How_long_can_I_get_quotation_after_BOM_is_uploaded_.html):
  required MFG Part Number, Designator, Quantity and Footprint; additional
  manufacturer, description, SMD/THT and special-instruction fields.

These sources define data requirements, not supplier acceptance of this design
or a verified quote. No external quote/order has been submitted.

Owning epics: E07/#7 routing/DFM, E08/#8 sourcing/fabrication, with E04/#4
electrical and E05/#5 exact mechanical inputs.
