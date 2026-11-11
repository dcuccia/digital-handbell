# Help build Digital Handbell

You do not need to be an electrical engineer to contribute. We are working
toward the first functioning custom instrument, and there is room for
software, music, mechanical design, electronics review and clear writing.

Start with the [gallery](docs/design-gallery.md) and
[roadmap](docs/roadmap.md), then comment on a relevant issue or
[open an issue](https://github.com/dcuccia/digital-handbell/issues/new)
describing a small contribution. Include what you want to produce and how
we could tell whether it works.

## Useful starting points

| Your interests | A useful first contribution | Workstream |
|---|---|---|
| Python / embedded software | A small, reproducible CircuitPython audio or motion experiment; document the board and library versions | [#6 Firmware and gestures](https://github.com/dcuccia/digital-handbell/issues/6), [#13 Sensor initialization](https://github.com/dcuccia/digital-handbell/issues/13) |
| Music / audio | Define ringing, damping and quiet-idle test cases, or contribute an original/licensed bell sample with provenance | [#3 Bench proof](https://github.com/dcuccia/digital-handbell/issues/3), [#6](https://github.com/dcuccia/digital-handbell/issues/6) |
| Electronics / PCB review | Review one R1-R3 item against the exact six-layer snapshot, with pin/net references and evidence | [#4 Electrical review](https://github.com/dcuccia/digital-handbell/issues/4), [#7 Layout and DFM](https://github.com/dcuccia/digital-handbell/issues/7) |
| FreeCAD / printing | Help plan the six-layer assembly update, especially J1's mated connector, wire exit and cartridge clearance | [#5 Mechanical integration](https://github.com/dcuccia/digital-handbell/issues/5) |
| Testing / tooling | Improve a narrowly scoped checker or design a repeatable bring-up record without modifying accepted board files | [#9 Bring-up](https://github.com/dcuccia/digital-handbell/issues/9), [#14 Tool qualification](https://github.com/dcuccia/digital-handbell/issues/14) |
| Documentation / teaching | Try the navigation as a newcomer and improve explanations, diagrams or assembly-review checklists | [#11 Open release](https://github.com/dcuccia/digital-handbell/issues/11) |

We have plans for firmware, but no released instrument application yet.
Discuss the target board and experiment before assuming there is a
ready-to-run firmware tree. Documentation and review contributions need
neither hardware nor a paid router account.

## Before changing files

1. Read [AGENTS.md](AGENTS.md) for repository engineering rules, and the
   relevant directory README for the exact revision. Start electronics work
   from the [six-layer review package](hardware/handbell/iterations/printed-bell-six-layer-review/README.md),
   not the original `hardware/handbell/handbell.kicad_pro`.
2. Keep the whole checkout for relative libraries. Use separate copies for
   new PCB/CAD experiments; do not regenerate historical snapshots in place.
   Read each tool's documented scope before running it.
3. Agree a bounded change and expected evidence. State what is measured,
   inferred or still unknown. Include the source revision/hash when a
   hardware conclusion depends on exact geometry.
4. Open a focused pull request to `main`, linking the issue. Explain the
   change, its limits and any checks actually performed. Update the relevant
   guide rather than appending progress logs to the project landing page.

KiCad 10.0.6 and FreeCAD 1.1.3 are the exercised CAD versions.
The [tool guide](tools/README.md) distinguishes static Python checks from
native CAD generation; there is no single command that validates the
whole instrument.

## Care, privacy and licensing

The current design is not a fabrication release or a safe-to-power/build
guide. Do not order boards, start paid routing, upload design files to a new
service or undertake live-cell experiments on the project's behalf without
the appropriate explicit approval and review.

Preserve reference notices and read [ATTRIBUTION.md](ATTRIBUTION.md).
Original software/docs/mechanics are MIT; adapted electronics are
CC BY-SA 3.0. Sound recordings and third-party CAD/images need their own
rights record. Do not commit account screenshots, credentials, private
backup details or identifying participant recordings.

Friendly explanations and honest negative results are valuable
contributions. A documented limitation is better than a claimed pass that
does not test the intended behavior.
