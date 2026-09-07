# Project brief

Captured from the project discussion on 2026-09-06. Requirements below distinguish
requested outcomes from implementation hypotheses. Numeric performance, cost,
and mechanical limits are deliberately not invented.

## Intended experience

A player rings a lightweight handbell-shaped instrument. Motion triggers a
digitally generated or recorded bell note through a local speaker. The concept
should be economical enough for schools, churches, and educational groups, with
straightforward assembly, charging, programming, and repair.

The starting enclosure is a children's play handbell with its clapper removed.
The speaker faces outward through the bell opening. A circular PCB sits behind
the speaker; a protected single-cell LiPo and a retaining structure share the
remaining volume. The intended musical note range, player ages, and whether
each bell has a fixed or selectable note remain open.

## Requirements register

| ID | Requirement or preference | Status / evidence needed |
|---|---|---|
| R01 | Maintain a public project under `dcuccia` with durable plans and epics | Existing repository retained; GitHub execution tracking |
| R02 | MCU capable of I2S audio; prefer RP2040 for the first experiment | Working baseline; RP2040 implements I2S through PIO |
| R03 | Prefer CircuitPython and novice-friendly USB programming | Working baseline; custom-board identity/provisioning still required |
| R04 | Integrated I2S DAC/class-D amplifier and local mono speaker | MAX98357A candidate; no separate DAC needed |
| R05 | Rechargeable 1S LiPo with USB-C charging | Cell, protection, charge current, temperature handling, and runtime TBD |
| R06 | Motion sensing for a natural ringing gesture | Owner-approved LSM6DSOX in the draft; compare acceleration/gyro against stock LIS3DH for strike plus chest-stop/rest; performance and assembled BOM not frozen |
| R07 | USB-C at the circular board edge, usable from outside the bell | Connector, shell slot, cable clearance, and load transfer TBD |
| R08 | Speaker faces outward; electronics sit behind it | Measure internal taper and usable depth with actual parts |
| R09 | Prefer outward-facing component/connectors for accessible assembly | Confirm assembly sequence before speaker blocks access |
| R10 | Plug-in speaker wiring, preferably a keyed JST-family connector | Exact family, polarity marking, pitch, retention, and current rating TBD |
| R11 | Prefer one-face component assembly on a two-layer circular PCB | Feasibility goal, not a committed diameter or layer count |
| R12 | Consider two stacked PCBs if justified by fit or cost | Compare added height, interconnects, supports, labor, and failure points |
| R13 | Good bell timbre, useful acoustic output, quiet between chimes | Define note range, SPL/distance, noise, distortion, and transient targets |
| R14 | Preserve clean audio behavior when combining reference circuits | Review supply loops, return paths, startup/mute behavior, and layout |
| R15 | Reuse mature, documented, code-supported open hardware | Prefer pinned Adafruit sources, guides, examples, and known errata |
| R16 | Proper attribution across electronics, code, assets, and documentation | Maintain per-source license/provenance and modifications |
| R17 | Remove unnecessary duplicated circuitry and peripheral branches | Removal must preserve shared rails, protection, pullups, and decoupling |
| R18 | Very low total cost and straightforward novice assembly | Target unit/set prices and quantities TBD; quote complete BOM and labor |
| R19 | JLCPCB-compatible fabrication/assembly; evaluate OSH Park | Separate bare-board service from assembly service |
| R20 | Beginner-friendly design tooling and instructions | KiCad recommended; record installed version and import procedure |
| R21 | Retain ESP32-S3 wireless as a possible future direction | Not needed for first bell; RF and software work are separate scope |
| R22 | Robust retention, battery containment, and serviceability | Safety, shake/drop, fastener, and USB-load evidence needed |
| R23 | Educationally useful operation and maintenance | Note assignment, controls, recovery, charging workflow, and kit instructions TBD |
| R24 | Record uncertainty and measured versus estimated results honestly | Do not turn vendor examples, ERC/DRC passes, or calculations into product qualification |
| R25 | Distinguish a handbell strike from a chest-stop/rest damping gesture | Added 2026-09-07; evaluate temporal motion context, gyro benefit, and handling/contact ambiguity |

## 2026-09-07 clarification

The 2023 work is an earlier precursor vision, not a requirement to retain all
its features. The current gesture requirements explicitly include both a
handbell strike and bringing the bell to the chest to stop/damp it and rest.

The owner is open to approximately **$1-2 additional component BOM cost** for a
meaningfully more capable motion sensor, while preferring mature reference
hardware, documented CircuitPython support, and straightforward tooling.
This is budget latitude for a justified upgrade, not a verified supplier-price
delta or a requirement to use on-chip machine learning.

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
PCB, and battery and attaches or bonds inside the bell. Explore assembly access,
adhesive/paint compatibility, print creep, repair, and drop retention.

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

## Initial scope boundary

The next engineering artifact is a reviewed, reduced schematic derived from
the selected baseline. This planning revision does not assert a completed CAD
import, selected cell, final speaker, routing solution, or finished firmware.
Wireless coordination, apps, and fleet management remain later options.
