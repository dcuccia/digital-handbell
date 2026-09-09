# Digital Handbell

An open-source, motion-triggered electronic handbell for affordable educational
music-making. Replace the clapper in a children's play handbell with a speaker,
rechargeable battery, and compact electronics. A natural ringing gesture should
produce a convincing bell sound; the instrument should be quiet between notes.

**Status: 0.2 reduced schematic and 43 mm unrouted placement/3D feasibility draft,
not a fabrication-ready or child-use-qualified design.** The
[native KiCad draft](hardware/handbell/README.md) and
[schematic PDF](hardware/handbell/reports/handbell-schematic.pdf) integrate
LSM6DSOX, TPS61023 audio boost, independent mute, keyed speaker/button connectors
and service pads. Feather/RGB/servo/STEMMA extras are removed.
The [0.2 handoff](docs/electrical-reduction-and-placement.md) and
[mechanical models](docs/mechanical-feasibility.md) distinguish actual CAD,
screening assumptions and unresolved fit/power/manufacturing gates.
No routed PCB or functioning firmware has been released.

**September 9 measurements:** the arrived speaker is 40 mm OD x 19 mm overall,
with a 32 mm basket rear at 12 mm and a 22 mm x 7 mm magnet. The
[measured-speaker follow-up](mechanical/studies/2026-09-09-measured-speaker/README.md)
keeps the original print files intact and compares speaker-facing electronics
with cylindrical/pouch battery space. The PCBA print received positive fit
feedback; some other pieces need structural reconsideration.

The [compact power and packaging review](docs/compact-power-and-packaging.md)
records the earlier decisions behind this revision. Its hypothetical taper
example is superseded by the owner's z13/50 mm to z43/34 mm working profile.

The working first-revision baseline is the
[Adafruit RP2040 Prop-Maker Feather (5768)](https://www.adafruit.com/product/5768):
RP2040, CircuitPython, MAX98357A I2S DAC/amplifier, LIS3DH accelerometer, USB-C,
and single-cell LiPo charging. Its documented, code-supported circuitry is
adapted into the reduced circular candidate, with the sensor and audio-power
changes described above. This is not a frozen BOM.

The owner-approved [LSM6DSOX six-axis sensor](docs/motion-sensing.md) is now in
the separate handbell draft for strike plus chest-stop/rest development.
The imported reference retains its original LIS3DH. Gesture performance,
assembled cost and final electrical decisions remain evidence gates.

## Start here

| Document | Purpose |
|---|---|
| [Project brief](docs/project-brief.md) | Captured goals, requirements, open questions, and original mechanical ideas |
| [Reference catalog](docs/reference-designs.md) | Every proposed source, learning guides, source revisions, and important corrections |
| [Architecture](docs/architecture.md) | Proposed blocks, verified baseline GPIOs, and retain/remove decisions |
| [Schematic and CAD plan](docs/schematic-plan.md) | Beginner-oriented KiCad setup/import path and schematic review gates |
| [KiCad setup and readiness](docs/kicad-setup.md) | Installed tooling, opening the native reference, and remaining import-review work |
| [Firmware and audio](docs/firmware-and-audio.md) | CircuitPython, bell assets, strike detection, quiet idle, and power modes |
| [Motion-sensor decision](docs/motion-sensing.md) | LIS3DH versus six-axis sensing, chest-stop limits, CircuitPython APIs, and sourcing |
| [Mechanics and manufacturing](docs/mechanics-and-manufacturing.md) | Speaker/board trade space, measurements, mounting, JLCPCB and OSH Park |
| [Compact power and packaging review](docs/compact-power-and-packaging.md) | Approved next revision, boost/cell/mute review, speaker-rating conflict and fit constraints |
| [0.2 reduction and placement](docs/electrical-reduction-and-placement.md) | Implemented circuits, 43 mm candidate, service map and open routing/DFM gates |
| [Mechanical feasibility](docs/mechanical-feasibility.md) | Editable FreeCAD, STEP/STL, assumed shell profile and cartridge interference findings |
| [Routing readiness](docs/routing-readiness.md) | Print-fit checkpoint, electrical floorplanning gates and the path to reviewed Gerbers/BOM/CPL |
| [Validation plan](docs/validation-plan.md) | Measurements and evidence required before each hardware release |
| [Decision log](docs/decisions.md) | Provisional decisions and the evidence needed to close them |
| [Roadmap and epics](docs/roadmap.md) | Milestones, dependencies, scope, and acceptance criteria |
| [Attribution and licensing](ATTRIBUTION.md) | Hardware, software, sound-asset, and documentation provenance |

Track execution in the public
[Digital Handbell Project](https://github.com/users/dcuccia/projects/1),
[12 epic issues](https://github.com/dcuccia/digital-handbell/issues?q=is%3Aissue%20label%3Aepic),
and [five milestones](https://github.com/dcuccia/digital-handbell/milestones).
The epics include checklists, acceptance criteria, native blocked-by
relationships, and links to supporting plans.

## Design direction

- Start with a bench demonstration using the integrated Prop-Maker Feather,
  while developing the reduced schematic in parallel.
- Prefer a single circular PCB with components assembled on one face and two
  copper layers. Establish diameter through real placement and measured shell
  geometry, not the sum of chip areas. Compare four layers and stacked boards
  if evidence warrants them.
- Keep sounding local/offline; evaluate an S3-MINI wireless variant early
  enough to inform antenna/carrier choices. The draft already has six-axis
  sensing; the unchanged reference has neither a radio nor a gyroscope.
- Optimize complete assembled cost and novice assembly, not merely IC prices.
  Fine-pitch soldering should not be a prerequisite for an educational kit.

## Project history

The original [2023 design notes](Design%20Notes.md) and
[system diagram](System%20Diagram.pptx) are preserved unchanged. They considered
wireless connectivity, a host interface, and a six-degree-of-freedom IMU.
The 2026 planning baseline narrows the first experiment; it does not silently
erase those earlier ideas.

## Licensing and attribution

The existing [MIT license](LICENSE) remains in place for original project
software and documentation. It does **not** relicense third-party hardware,
software, images, or recordings. Most candidate Adafruit hardware sources use
CC BY-SA 3.0; adapted material must retain its applicable terms and notices.
See [ATTRIBUTION.md](ATTRIBUTION.md) before importing anything.

Pinned, licensed Adafruit CAD and notices are vendored in the reference
packages; the separate derivative identifies its modifications. No third-party
firmware or recordings are vendored. This is an independent project, not an
Adafruit-endorsed product.
