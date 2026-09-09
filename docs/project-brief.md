# Project brief

Captured from the project discussions on 2026-09-06 and 2026-09-07. Requirements below distinguish
requested outcomes from implementation hypotheses. Numeric performance, cost,
and mechanical limits are deliberately not invented.

## Intended experience

A player rings a lightweight handbell-shaped instrument. Motion triggers a
digitally generated or recorded bell note through a local speaker. The concept
should be economical enough for schools, churches, and educational groups, with
straightforward assembly, charging, programming, and repair.

The starting enclosure is a children's play handbell with its clapper removed.
The speaker faces outward through the bell opening. A compact PCB, protected
single-cell LiPo and printed retaining structure share the remaining volume.
A solid disk behind the speaker was the initial concept; a near-mouth
annular/offset board is now also a fit-study candidate. The intended musical note range, player ages, and whether
each bell has a fixed or selectable note remain open.

## Requirements register

| ID | Requirement or preference | Status / evidence needed |
|---|---|---|
| R01 | Maintain a public project under `dcuccia` with durable plans and epics | Existing repository retained; GitHub execution tracking |
| R02 | MCU capable of I2S audio; prefer RP2040 for the first experiment | Working baseline; RP2040 implements I2S through PIO |
| R03 | Prefer CircuitPython and novice-friendly USB programming | Working baseline; custom-board identity/provisioning still required |
| R04 | Integrated I2S DAC/class-D amplifier and local mono 4 ohm speaker; design electronics for the 3 W high end | MAX98357A; boosted rail required for this target; 3 W low-distortion or speaker qualification is not established |
| R05 | Rechargeable 1S LiPo with USB-C charging | Cell, protection, charge current, temperature handling, and runtime TBD |
| R06 | Motion sensing for a natural ringing gesture | Owner-approved LSM6DSOX in the draft; compare acceleration/gyro against stock LIS3DH for strike plus chest-stop/rest; performance and assembled BOM not frozen |
| R07 | USB-C at the circular board edge, usable from outside the bell | Connector, shell slot, cable clearance, and load transfer TBD |
| R08 | Speaker faces outward; package electronics behind/around it in the shell | Owner estimates and retail speaker drawing captured; axial profile, basket, cell and clearances remain open |
| R09 | Prefer outward-facing component/connectors for accessible assembly | 0.2 compares inward-facing components to recover axial space; preassembly and service access still need confirmation |
| R10 | Plug-in speaker wiring, preferably a keyed JST-family connector | 0.2 selects distinct Molex Pico-Lock; final mating envelope/current qualification pending |
| R11 | Prefer one-face component assembly on a two-layer circular PCB | Feasibility goal, not a committed diameter or layer count |
| R12 | Consider two stacked PCBs if justified by fit or cost | Compare added height, interconnects, supports, labor, and failure points |
| R13 | Good bell timbre, useful acoustic output, quiet between chimes | Define note range, SPL/distance, noise, distortion, and transient targets |
| R14 | Preserve clean audio behavior when combining reference circuits | Review supply loops, return paths, startup/mute behavior, and layout |
| R15 | Reuse mature, documented, code-supported open hardware | Prefer pinned Adafruit sources, guides, examples, and known errata |
| R16 | Proper attribution across electronics, code, assets, and documentation | Maintain per-source license/provenance and modifications |
| R17 | Remove Feather headers, servo/RGB branches and STEMMA QT; retain simple charge/status LEDs | Implemented in 0.2; shared rails, pullups and decoupling retained |
| R18 | Very low total cost and straightforward novice assembly | Target unit/set prices and quantities TBD; quote complete BOM and labor |
| R19 | JLCPCB-compatible fabrication/assembly; evaluate OSH Park | Separate bare-board service from assembly service |
| R20 | Beginner-friendly design tooling and instructions | KiCad recommended; record installed version and import procedure |
| R21 | Evaluate an ESP32-S3-MINI wireless variant alongside RP2040 research | Sound programming, QR identity, optional asynchronous training telemetry; first sounding baseline stays local/offline |
| R22 | Robust retention, battery containment, and serviceability | Safety, shake/drop, fastener, and USB-load evidence needed |
| R23 | Educationally useful operation and maintenance | Note assignment, controls, recovery, charging workflow, and kit instructions TBD |
| R24 | Record uncertainty and measured versus estimated results honestly | Do not turn vendor examples, ERC/DRC passes, or calculations into product qualification |
| R25 | Distinguish a handbell strike from a chest-stop/rest damping gesture | Added 2026-09-07; evaluate temporal motion context, gyro benefit, and handling/contact ambiguity |
| R26 | Dedicated two-pin keyed button harness on RP2040 GPIO19 / schematic BUTTON net | Owner-approved replacement for STEMMA QT; stock CircuitPython alias is EXTERNAL_BUTTON, not board.BUTTON; connector/protection/debounce pending |
| R27 | Print the cartridge and speaker grille; preassemble outside the bell | Prefer removable cartridge with separately bonded mounting interface; retention, acoustic and dimensional evidence pending |
| R28 | Use 0402 where electrically and mechanically appropriate | Not a requirement to shrink bulk capacitors, magnetics, power parts or connectors indiscriminately |

## 2026-09-07 clarification

The 2023 work is an earlier precursor vision, not a requirement to retain all
its features. The current gesture requirements explicitly include both a
handbell strike and bringing the bell to the chest to stop/damp it and rest.

The owner is open to approximately **$1-2 additional component BOM cost** for a
meaningfully more capable motion sensor, while preferring mature reference
hardware, documented CircuitPython support, and straightforward tooling.
This is budget latitude for a justified upgrade, not a verified supplier-price
delta or a requirement to use on-chip machine learning.

## 2026-09-07 compact power and packaging inputs

The owner has the [B01EABRWO6 handbell set](https://www.amazon.com/dp/B01EABRWO6),
not necessarily the initial inspiration listing. Reported approximate dimensions
are 70 mm inside the lip, 40 mm inside an unspecified station halfway down the
smaller taper, 44 mm bell-body height and 85 mm handle height. **The axial
position of the 40 mm measurement and usable handle interior are unknown.**

Two Gikfun EK1725 2-inch speakers are already on hand. EK1794 40 mm speakers
were initially an unpurchased comparison candidate. The owner subsequently
reported ordering them, with arrival expected Wednesday, 2026-09-09; actual
dimensions and power limits are not yet qualified. The owner-supplied retail drawing
gives 40.5 +/-0.4 mm frame diameter, 22 +/-0.5 mm magnet diameter and
18 +/-0.5 mm overall depth; its 2.7 +/-0.3 mm rim dimension is not extra depth.
The 40 mm seller's 3 W title conflicts with a 2 W description rating.
Do not silently resolve this into a continuous/peak distinction.

The [power/fit review](compact-power-and-packaging.md) records approved
reductions, source-backed boost candidates, current budgets and manufacturing
options. [Structured inputs](measurements/shell-speaker-inputs.json) preserve
the origin and uncertainty of the dimensions. No cell, final outline or
boost/inductor MPN has been frozen, and the published 0.1 schematic has not yet
been rewired for these decisions.

## 2026-09-09 physical follow-up

The speaker arrived. The owner reports 40 mm frame OD, 19 mm overall depth,
32 mm basket-rear OD at 12 mm depth, and a 22 mm diameter x 7 mm magnet.
The [measured study](../mechanical/studies/2026-09-09-measured-speaker/README.md)
supersedes the earlier speaker-size assumption for new fit work without
overwriting the historical files or manufacturer uncertainty.

The populated-PCBA proxy printed well and could fit relatively deeply, with
no depth/orientation supplied. Some unspecified other mechanical pieces were
flimsy. Preserve the successful PCBA gauge and investigate structural load
paths rather than guessing which part failed or blindly thickening all parts.
Battery height remains a key constraint. Keep compact protected 16340 and flat
pouch alternatives active; the owner specifically requests SMD contact research
and supplied [Keystone 54](https://us.rs-online.com/product/keystone-electronics/54/70229904/)
as a through-hole example. Through-hole or SMT remains acceptable.

## Mechanical concepts to preserve

**Concept A: shell slot and opposite fastener.** The edge USB-C connector fits
through a slot in the bell housing. An opposite-side screw enters through the
shell into a horizontal female threaded receptacle, potentially SMT-mounted on
the PCB. This is an exploration item, not an approved structural design.
USB insertion loads need a supported mechanical load path; connector signal
pads and a distant SMT nut must not be assumed to provide it.

**Concept B: separate speaker carrier.** A printed adapter attaches the round
speaker to the bell housing, with separate PCB mounting features.

**Concept C: multilevel carrier.** A printed internal structure retains speaker,
PCB, battery and printed grille for assembly outside the bell. Prefer bonding
only its mounting interface, leaving the cartridge and battery serviceable.
Compare a shallow mouth extension and an offset/annular electronics bay against
a solid disk behind the magnet. Explore assembly access, adhesive/paint
compatibility, print creep, repair and drop retention.

For all concepts, evaluate metal-shell insulation, cell clearance, captive
hardware, screw-length stops, cable strain relief, acoustic volume, and speaker
vent clearance. An outward-facing JST is useful only if there is room to mate it
at the appropriate assembly step.

## Inputs to resolve, without blocking initial schematic research

| Input | Why it matters |
|---|---|
| Actual shell samples; inner diameter at multiple heights, depth, wall thickness, mass | Board envelope and tolerance stack |
| Intended age group and deployment geography | Product classification, access, sound exposure, and safety review |
| Note range, tuning reference, fixed/selectable notes, damping and retrigger behavior | Speaker, sound assets, controls, and gesture algorithm |
| Loudness at a specified distance and quiet-idle criterion | Acoustic comparison and amplifier operating point |
| Strike latency/jitter and false-trigger tolerances | Sampling, buffering, wake strategy, and sensor choice |
| Runtime, session length, storage interval, charging time | Battery capacity, power modes, and charger |
| Operation while plugged in; class-set charging arrangements | Power-path, thermal, USB-source budget, and classroom workflow |
| Target mass, unit/set budget, and build quantities | Driver, cell, enclosure, assembly service, and parts sourcing |
| Desired power/volume/note controls and status indications | Schematic I/O and accessible enclosure features |

The RP2040 "less than a dollar" expectation is an unverified sourcing hypothesis,
not an approved BOM price. Price the actual supplier, quantity, assembly SKU,
shipping, taxes, and yield.

## Current 0.2 scope and owner profile update

The owner subsequently requested actual reduction, placement and FreeCAD
STEP/STL work, with a working shell ID of 50 mm at z=13 mm inward, tapering
linearly to 34 mm at z=43 mm. The near-face 5 mm and curved transition remain
approximate. These assumptions supersede the earlier hypothetical z22 screen;
they do not establish manufacturing tolerances or a measured 3D shell.

The native [0.2 schematic and 43 mm placement](electrical-reduction-and-placement.md)
implement the reduction and boost/mute/button revision. The
[FreeCAD study](mechanical-feasibility.md) uses the updated profile.
No cell, qualified speaker, routed PCB or functioning firmware is released.
Early S3 radio experiments remain in scope; a deployed training system is not implied.
