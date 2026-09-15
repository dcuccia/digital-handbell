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
