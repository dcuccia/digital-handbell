# Digital Handbell

An open-source, motion-triggered electronic handbell for affordable educational
music-making. Replace the clapper in a children's play handbell with a speaker,
rechargeable battery, and compact electronics. A natural ringing gesture should
produce a convincing bell sound; the instrument should be quiet between notes.

**Status: reference import and prototyping preparation, not a fabrication-ready
or child-use-qualified design.** An attributed
[KiCad conversion of the upstream reference](hardware/reference/adafruit-5768/README.md)
is available. No custom handbell schematic, PCB, firmware, or enclosure has been
released.

The working first-revision baseline is the
[Adafruit RP2040 Prop-Maker Feather (5768)](https://www.adafruit.com/product/5768):
RP2040, CircuitPython, MAX98357A I2S DAC/amplifier, LIS3DH accelerometer, USB-C,
and single-cell LiPo charging. We intend to reuse documented, code-supported
open hardware, remove unnecessary peripheral branches, and create a circular
board. This is a starting hypothesis, not a frozen BOM.

For the handbell derivative, [LSM6DSOX is the recommended six-axis sensor
candidate](docs/motion-sensing.md) for strike plus chest-stop/rest recognition.
The imported reference retains its original LIS3DH; no substitution is made
until the gesture, electrical, and assembly decisions are reviewed.

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
- Keep wireless optional. Evaluate six-axis sensing now for the explicit
  chest-stop/rest requirement; the unchanged reference board itself has neither
  a radio nor a gyroscope.
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

This planning revision links to upstream sources; it does not vendor their CAD,
code, recordings, or branding. This is an independent project, not an
Adafruit-endorsed product.
