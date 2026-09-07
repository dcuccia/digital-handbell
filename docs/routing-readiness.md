# From fit mock-up to routed PCB

**Current stopping point: print-fit and electrical floorplanning, not Gerbers.**
The 0.2 PCB contains real footprints and correct pin/net assignments, but no
tracks, vias or ground planes. Its ratsnest lines show required connections;
they are not copper and do not demonstrate a usable current-return path.

The owner reports the 40 mm speakers are ordered, with arrival expected
**Wednesday, 2026-09-09**. Inert mock-ups can be printed before then on the
owner's **Creality K1C using PLA**. Keep the current 43 mm placement manifest
fixed for that fit study; later electrical placement changes must regenerate
the populated-board mock-up rather than silently diverge from it.

## What can proceed now

Review and refine critical placement against the actual RP2040, MAX98357A,
LSM6DSOX and TPS61023 reference layouts and manufacturer guidance. The current
packing optimizer does not enforce bypass distance, switching-loop geometry,
feedback isolation, thermal spreading or USB impedance. Those constraints take
priority over preserving its neat arrangement.

| Circuit | First layout work |
|---|---|
| RP2040 core | Put each bypass at the relevant supply/return pins; keep crystal/load-cap and QSPI routes short and coherent |
| TPS61023 | Review the VIN cap, inductor, switch node, output caps and ground as a coupled placement; use a quiet feedback return and avoid routing feedback alongside BOOST_SW |
| MAX98357A | Keep supply bypass and high-current returns local, provide the required thermal connection, and route both BTL paths deliberately |
| USB | Retain connector pad mapping and series/CC circuitry; route D+/D- as a short pair with a continuous reference, using the chosen fab stackup for geometry |
| IMU | Keep local supply bypasses close and establish physical axis orientation; avoid heat, switching-current bottlenecks and mechanically stressed attachment points |
| Ground/test access | Aim for a continuous return plane, not reflexively split audio/digital ground; place service pads without needlessly cutting that plane or blocking carrier access |

Do not choose arbitrary trace widths for VHI, V+, VAMP, BOOST_SW or the BTL
paths just because a default rule permits them. Establish copper weight,
maximum current, temperature rise, voltage drop and return geometry first.
The feedback net is a sensing connection, not part of a high-current route.

## Gates before committing to final copper

| Gate | Needed evidence |
|---|---|
| Board/carrier interface | Inert print fit, insertion/removal sequence, USB slot/load path, PCB support locations and usable service access |
| Actual speaker | Caliper measurements of the basket, magnet, terminals, vent and front clearance; the supplied image does not dimension the complete profile |
| Battery | A real protected pack with suitable current/charge ratings and a complete lead/connector envelope; a rectangular dummy is not a selected battery |
| Boost parts | Exact inductor and capacitor MPNs, land patterns/heights, saturation/thermal current and effective capacitance; settle the C29 DNP/compensation decision |
| Connectors | Mated body and cable-bend envelopes, polarity/retention/current ratings, and USB manufacturer land-pattern review |
| Power policy | USB input budget, charge/play policy, low-cell cutoff/protection and startup/mute/brownout behavior |
| Fabricator | Actual layer/copper/stackup rules, copper-edge/drill/mask constraints, component assembly support, fiducials and panelization requirements |

The four USB hole-clearance findings remain an explicit gate. Do not lower the
0.25 mm rule merely to hide source clearances of 0.1755/0.2144 mm. Select a
justified manufacturer/fab-compatible footprint solution and rerun the review.

Provisional core routing can begin after the first electrical floorplan review,
without waiting for finished application firmware. It is still rework-prone
until the mechanical and power footprints above are fixed. The present print
snapshot is therefore a deliberate checkpoint, not a claim that all layout
inputs are frozen.

## Routing and manufacturing sequence

1. Freeze the next reviewed placement/keepouts, while retaining the 0.2 fit
   snapshot as history.
2. Route the critical power/return, clock/flash and USB structures with
   appropriate constraints; then complete I2S, IMU, control and service nets.
3. Fill/review ground and thermal copper, then inspect disconnected islands,
   return detours, clearance, silk, polarity and assembly access.
4. Resolve DRC and schematic-parity findings and perform an independent layout
   review. Re-export the populated mechanical model and revisit fit.
5. Export matched Gerbers and plated/nonplated drill data from that revision,
   inspect them in a Gerber viewer, and package the intended fabrication files.
   A populated-board order also needs a sourced BOM and checked placement/CPL
   data; Gerbers alone do not describe the assembled components.

The JLC desktop application is a useful next preview/quotation step once that
package exists. Successful upload or a rendered board preview is not electrical
approval. **No manufacturing Gerbers are issued from this unrouted snapshot,
and no order or assembly submission is authorized by this document.**

## Printing scope

Use the [mechanical handoff](mechanical-feasibility.md) for the actual files and
their readiness. Requested fit artifacts are a populated-board proxy, inert
battery blocks, carrier/grille parts and speaker dummies in STEP/STL form.
The board proxy must remain connected/printable without pretending its boxes
are exact manufacturer bodies.

For the speaker, distinguish an illustrative stepped/basket shape from the
**40.9 mm diameter x 18.5 mm deep conservative envelope**. The image specifies
frame 40.5 +/-0.4 mm, magnet 22 +/-0.5 mm, overall depth 18 +/-0.5 mm and rim
2.7 +/-0.3 mm. It does not specify magnet thickness, basket taper or terminals.
Do not claim inferred intermediate dimensions are measured.

Import in millimetres at **100% scale**. Start with the slicer's established
K1C/PLA profile rather than invented temperatures or speeds. Measure a printed
gauge with calipers; small features and first-layer expansion can bias fit.
Some 0402-sized details may not reproduce faithfully with a typical nozzle.
PLA dummies are for handling and geometry only, not electrical, acoustic,
load-bearing or battery-temperature qualification. Never force a live pouch
cell into a tight fit test.
