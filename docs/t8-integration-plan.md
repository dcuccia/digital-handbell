# Measured-shell T8 integration and pre-routing review

**2026-09-11: owner-requested next revision.** Preserve the September 7 print
snapshot and September 9 wing/cartridge draft. This revision targets a complete
placed assembly for review in FreeCAD **before starting routing**, not a
fabrication or live-cell release.

## Measurements and the working shell

The [dated measurement record](measurements/2026-09-11-shell-speaker-inputs.json)
preserves the raw caliper reports, the owner's clarifications, and derived
quantities separately. All axial stations are measured from the mouth toward
the handle.

| Station / feature | Owner report |
|---|---|
| Mouth, z0 | OD73.15 / ID71.68 |
| z4.90 | OD73.15 / ID69.75 |
| First concave taper | 10.00 axial travel after z4.90; end at **z14.90**, explicitly confirmed |
| End of that taper | Rough OD51.50 / ID50.00 |
| Before final taper | OD38.42 at approximately **z41.75** |
| Bell body height | 45.55 |
| Handle | Height85.50; OD18.52 at bell, OD15.01 at top |
| Speaker magnet | **OD21.70**, superseding22.00; owner confirmed this means the speaker, not a battery magnet |
| Other speaker dimensions | Earlier D40/H19, basket rear D32 at z12, magnetH7 remain current |

The owner subsequently measured the lip wall directly as **1.15 mm** and
requested that uniform thickness as the working CAD assumption. It does not
reconcile with all paired OD/ID reports: half their differences is0.735,
1.70 and0.75 mm at the first three stations. Do not silently rewrite those
readings. Prioritize measured inside stations for cavity fit, document how the
1.15 mm model wall is constructed, and label the inferred **ID36.12 at
z41.75** as a calculation, not a caliper measurement.

Intermediate concave curvature, the final closure above z41.75, roundness,
production variation and handle-fastener intrusion remain unmeasured. A
rendered curve is not new measurement evidence.

The owner confirms the new printed design fits inside the bell but seems
slightly undersized radially. This supports revising the front register and
flange; it does not establish a measured clearance or require enlarging the
43 mm electronics disk. The original D72 external flange was designed for an
assumed D70 mouth, so its bearing against the now-measured ID71.68 needs
reconsideration rather than uniform scaling of every part.

## Electrical and battery scope

Use the owner's preferred **Vapcell T8 button-top** as the next candidate and
the stocked **W25Q16JVUXIQ TR, 2 MB** flash option. The flash requires its
USON2x3 footprint; it must not be assigned the inherited USON4x4 lands.
The [flash source review](flash-sourcing.md) retains exact ordering and
firmware compatibility evidence.

The seller's approximate D16.4 x L34 T8 dimensions remain supplier evidence,
not owner measurements or maximum tolerances. Exact positive-button geometry
and the conflicting generic manufacturer button-extension note remain
contact/retention qualification items. The
[cell/protection review](battery-contact-options.md#2026-09-11-vapcell-t8-and-pcb-level-protection-alternative)
records current and charge-profile evidence.

Keep the protection design compact and deliberate. A boost-only fallback is
not equivalent: a short on the battery rail or elsewhere on the board can
bypass the converter, and its low-voltage operation does not prevent cell
overdischarge. Review a small single-cell fault protector and isolation
devices, all charging/discharge paths, and actual footprint area. No fuel
gauge or series-cell balancing is required by this 1S architecture.

The earlier schematic connected battery negative directly to board GND.
With a low-side protector, **raw cell negative and protected system GND are
different nets**, joined through the conducting protection stage in normal
operation and separated on cutoff. USB shield/ground, screw pads and signal
returns must not accidentally bridge that separation. If a different topology
is selected, document its actual grounding contract rather than repeating this
example as an implemented fact.

Keep the metal bell electrically isolated from terminals, cell can, board
fasteners and USB hardware. A floating bell can still short a cell if both
terminals contact it. The metal can of a conventional cylindrical Li-ion cell
is associated with negative; the wrapper alone is not an abrasion-resistant
holder. A direct short across the raw cell outside the protected interface
cannot be cleared by a downstream board protector.

The requested **1-1.5 mm proud plastic** is a geometric design target, not an
electrical insulation rating. Apply it to terminal guards and likely contact
directions during insertion, installed use and removal, not merely the
largest z coordinate. The capture structure must carry battery motion and
insertion loads independently of SMT solder joints. Temperature charging
policy, reverse insertion, vent clearance and approved rechargeable-cell
identification remain explicit responsibilities.

## Mechanical and service scope

Make the following interfaces agree in a single assembled model:

- The measured mouth register, an external flange with real bearing area,
  and positive removable shell attachment.
- A tighter clearance opening around the D21.70 magnet, without pretending
  that print allowance is a measured tolerance or applying unspecified force
  to the speaker cone, basket, magnet or vent.
- Actual battery-contact lands and original dimensioned contact proxies,
  an insulating cradle/cover, terminal shielding and accessible fasteners.
- PCB support and tool paths that do not load the IMU, bridge electrical
  isolation, or collide with the cell.
- USB mouth position relative to the **outside** of the working shell,
  footprint/anchor support, insulated cutout and plug approach.
- A realistic cartridge insertion/removal path. A connector protruding
  through a closed side hole can trap the cartridge; serviceability must not
  be demonstrated only with that shell hidden.

The former draft used **M2 screws**, 2.2 mm PCB clearance drills and
**D3 x L4 insert envelopes**. Those insert envelopes were placeholders, not a
selected M3 or M2.5 receptacle. Do not force M3 screws into the fit prints.
Select and document a coherent new screw/insert or captive-nut system, its
clearance holes, engagement and installation steps. A molded insert pocket
and a screw-clearance hole serve different purposes.

## Completion and routing sequence

1. Record the measurements and settle the working geometric interpretation.
2. Implement the separate native schematic/placement with flash, cell-contact
   and compact protection changes; preserve unrelated connections and source
   libraries.
3. Generate the new mechanical study from that exact placement manifest.
   Include the cell, contacts, insulating capture, shell attachment, speaker,
   USB access and all fasteners rather than a board-only approximation.
4. Review native correspondence, component/structure clearances and assembly
   paths. Keep open findings visible; an ERC/DRC pass is not safety approval.
5. Open the complete FreeCAD assembly for owner review. **Do not begin
   routing merely because generation succeeded.**
6. After placement/interface approval, route the critical power, returns,
   clock/flash and USB structures first, then the remaining nets. Finish
   electrical/DFM/parity and mechanical review before manufacturing exports.

Final copper still needs exact power-component selection, charging/use policy,
USB footprint/fab compatibility and the chosen layer/copper/stackup rules.
The known inherited USB hole-clearance findings may not be hidden by lowering
the rule. Firmware completeness and a production quotation do not need to
block a clearly identified placement review.

Owning epics: E01/#1 for measurements, E04/#4 for power/flash/contacts,
E05/#5 for capture/service, E07/#7 for placement/routing, and E10/#10 for
insulation, retention and eventual use qualification.
