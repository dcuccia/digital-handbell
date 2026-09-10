# Wing placement and integrated cartridge iteration

**2026-09-09: draft iteration, not an electrical/structural manufacturing release.**
The owner requested selective rear-face components in the battery-free wings,
ground-assigned mounting holes for sturdier supports, and fewer separate
printed parts. The original print kit and electrical baseline are preserved.

The [native wing placement](../hardware/handbell/iterations/wing-draft/README.md)
is separate from the [integrated-cartridge study](../mechanical/studies/2026-09-09-integrated-cartridge/README.md).
Their shared schema-2 placement manifest is the dimensional contract; a body
that merely resembles the PCB is not a substitute for that input.

## What is unblocked

The installed KiCad/FreeCAD toolchains, pinned circuit references, measured
speaker stations and successful bare-PCBA print are enough to make this draft.
Waiting for final firmware, a fully sourced production BOM or finished sound
assets is unnecessary for a placement/cartridge experiment.

The new 43 mm PCB keeps the source circuit nets and footprints, puts **62
fitted parts toward the speaker and 11 toward the handle**, and reserves the
central back region for battery/contact planning. The old X1 wired-battery
connector is DNP in all its schematic units and on the PCB; C29 stays DNP.
No unqualified clip footprint or battery-protection circuit is silently added.

The boost is a coherent source-based rear block rather than a lone inductor
moved far from its capacitors. The rear amplifier block has an explicit local
bypass arrangement. The speaker connector and output filter stay on the
speaker-facing outer annulus. USB anchors reserve space on **both** faces:
moving a component to B does not avoid a through-board anchor or drill.

Core placement is source-seeded, with bounded local capacitor-spacing changes
to eliminate crowded courtyard relationships. Critical routing, thermal
spreading and return paths still need a routing-led review. This is more
deliberate than the initial global packing example, not finished copper.

## Mounts and assembly architecture

The board has two M2 clearance footprints at (+10,+15.7) and (-10,-15.7) mm
from its center, with 2.2 mm plated drills and 4.4 mm copper pads. Each gets a
3.2 mm-radius support/head/tool reservation on both faces. The pads are
**assigned GND**, not electrically connected by nonexistent routing.

Grounding is separate from structural strength. The retaining structure must
support the board locally and carry speaker/battery/insertion loads; an
unsupported PCB and its solder joints must not become the main mechanical
frame. Avoid transferring attachment stress into the IMU. Choose screw,
washer, shoulder/insert and engagement lengths together, and prevent metal
hardware from contacting the cell can or terminals.

The delivered mechanical draft has **two primary printed pieces**: an
integrated grille/front seat/lower-support body and a removable capture yoke
with PCB-support bosses. Four M2 screw placeholders, four insert placeholders
and two washers provide the internal fastener concept; exact hardware is not
selected or qualified.

Speaker loading is deliberately sequenced: insert the D40 speaker into the
body first, add the yoke over the D22 magnet, then add the PCB and its screws.
The lower supports leave a nominal D40.6 passage. The installed yoke's D22.8
opening does not admit the D40 frame; trying to insert the speaker afterward is
explicitly a blocked sequence. The study records swept translation bounds,
sampled poses and finite-displacement stop probes, not merely a final pose.

The body has an **external D72 flange** and an integral D69 register for the
assumed D70 mouth. That flange intentionally remains outside the opening;
do not scale the entire model down to 70 mm. Lip registration is not an
implemented shell attachment. No retained battery assembly is included.

The actual component/speaker and component/yoke screens have no material
overlaps, but their smallest nominal separations are only 0.5 mm and
0.254 mm respectively (the latter at U3). Yoke/shell and lower screw-head/shell
distances are about 0.263 and 0.354 mm. These are not allocated tolerance,
thermal, vibration or structural margins. The capture concept also has
0.3 mm nominal axial and 0.4 mm radial play; bearing surfaces and any
preload/damping provision still need attention before claiming a quiet mount.

The integrated study owns the complete dimensions, insertion evidence,
raw interferences and limitations. Do not infer a stronger, fully retained
or child-ready assembly from a thicker-looking model.

## Assembly cost is a decision gate, not a reason to stop drafting

Two copper layers, two-sided component assembly and through-hole secondary
operations are distinct supplier capabilities. Evaluate the current JLC tier
and actual BOM restrictions rather than assuming that a one-face board
automatically qualifies for the least expensive service.

**Official JLCPCB information retrieved September 9, 2026 PDT:**

| Capability | Economic | Standard |
|---|---|---|
| Component placement sides | Single-sided SMT/through-hole | Single- or double-sided SMT/through-hole |
| Mixed SMT and THT | Supported, subject to the single-sided restriction | Supported |
| Front electronics plus JLC-installed rear SMT contacts/parts | No published Economic exception established | Published two-sided route |

Sources: [assembly capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)
and [assembly FAQs](https://jlcpcb.com/help/article/pcb-assembly-faqs).
Both tiers describe manual/THT work, but manual-assembly pricing is not an
exception permitting reverse-side SMT placement in Economic. Customer-installed
parts after delivery are a separate option; their remaining factory job must
still qualify for its chosen tier.

The selected [LSM6DSOXTR / C481766 listing](https://jlcpcb.com/partdetail/C481766)
currently says **Standard Only, SMT Assembly, X-ray Required**. The alternate
[LSM6DS3TR-C / C967633 listing](https://jlcpcb.com/partdetail/C967633) has the same
tier/X-ray restrictions. Thus the selected IMU already presents a Standard-only
listing restriction before any part is moved rearward. X-ray alone does not
prove Standard is required; the explicit part-listing restriction matters.
This is not a submitted-job determination, and the rest of the BOM has not
received a complete current supplier-eligibility audit.

The [dedicated pricing page](https://jlcpcb.com/help/article/pcb-assembly-price),
last updated **September 8, 2026**, gives these order-level charges in USD:

| Charge | Economic | Standard, one face | Standard, two faces |
|---|---:|---:|---:|
| Setup | 8.18 | 25.56 | 51.12 |
| Stencil | 1.53 | 8.21 | 16.42 |
| Setup + stencil subtotal | 9.71 | 33.77 | 67.54 |

The published two-face increment over Standard one-face is therefore
**USD33.77 per order for those two charges alone**, not a complete price delta
or a per-board fee. For ten boards, that particular increment is about USD3.38
per board before other charges. Components, assembly work, X-ray, tooling,
framing, shipping and tax are not included in that comparison.

The same price page lists USD3.58/order hand-soldering labor and
USD0.0164/manual joint for the first 10,000 joints under both tiers. The general
FAQ still displays different older manual prices; prefer the dated pricing
page rather than mixing tables. Its USD14.93 minimum difference when both
tiers are available for the same order is a minimum-total-difference rule, not
an automatic USD14.93 surcharge to add to the table.

Standard's published **70 x 70 mm minimum manufacturing size and required
edge rails** also need attention. The 43 mm circuit outline is not thereby
forced to become a 70 mm finished board, but an appropriate frame/panel and
factory acceptance are needed; do not assume a naked 43 mm circle is directly
eligible. No design files have been submitted for quotation or manufacturing.

The two-face candidate is an exploration, not a supplier quote or an approved
production route. Compare its complete assembled cost with an alternative
that retains one-face factory SMT and uses deliberate manual completion only
where genuinely practical. Large hidden inductor terminations are not
automatically novice-friendly hand-soldering work. Inherited supplier rotation
fields are not an order-ready BOM/CPL for changed poses and faces.

For this prototype, **Standard two-sided assembly is the sensible route to
evaluate first**, given the chosen IMU's listing and the useful wing space.
Retain one-face/manual-completion as a quoted comparison, not an assumed
Economic shortcut that asks a novice to install an LGA IMU.

## What still blocks final layout and fabrication

| Gate | Remaining evidence / decision |
|---|---|
| Cell and contacts | Exact protected cell, maximum dimensions, discharge/charge limits, button geometry, loaded contact travel/height and independent capture; the red planning corridor is not a fitted holder |
| Battery input | Replace the DNP X1 provision with the selected interface and reviewed reverse-insertion/protection/charging arrangement |
| Real enclosure and assembly | Quantified PCB depth/orientation, shell profile/tolerance at supports, actual speaker insertion and service access |
| Speaker details | Terminals, wire exit, rear vent, rim/bearing surfaces, excursion and required clearance; stations alone do not define all of them |
| Retention hardware | Screw/insert/shoulder lengths, positive capture, load paths, material/process choices and fit feedback from the new draft |
| USB | Supported slot/mating/load path and a manufacturer/fab-compatible resolution of the four retained internal hole-clearance findings |
| Power parts/layout | Exact inductor/capacitor MPNs, effective capacitance, saturation/thermal current, compensation, current-return and heat-spreading geometry |
| Assembly route | Current supplier tier/component eligibility, panel/fixture requirements, full BOM/CPL orientation and actual quotation |
| Electrical behavior | Charge/play policy, current budget, mute/startup/brownout behavior and prototype measurements |

These are gates on final copper, orders and a functional enclosed prototype;
they do not invalidate a clearly labeled placement/fit draft. No manufacturing
Gerbers/drills, order-ready assembly files or fabrication order are issued.

## Evidence and provenance

The wing project records native ERC/DRC and direct pin/net/side/DNP/pose checks.
Its known CLI auto-net fallback is retained; the earlier baseline GUI review
does not automatically approve the new variant. The mechanical report must
identify the exact consumed manifest and preserve failed fit conditions.

Adafruit-derived electronics retain the parent CC BY-SA notices. Original
tools and new mechanical primitives are MIT; supplier drawings and third-party
print files are not imported without their applicable permissions/notices.
Owning epics: E04/#4, E05/#5 and E07/#7, with assembly economics in E08/#8.
