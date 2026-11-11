# Roadmap

[Project home](../README.md) · [Documentation](README.md) · [Contributing](../CONTRIBUTING.md)

**Updated November 10, 2026.** We have a zero-open six-layer layout, a
public review snapshot and a live prototype PCBA quote. We do not yet have
a demonstrated working custom instrument or a fabrication release.

## Now: review the design we have

| Workstream | Starting evidence | Next concrete outcome |
|---|---|---|
| Electrical and layout review | [Six-layer review brief](pcb-review-2026-11.md), snapshot `2f738ccb` | Disposition native rule/parity findings; review power/returns, USB, clock, decoupling and recovery. Track in [#4](https://github.com/dcuccia/digital-handbell/issues/4) / [#7](https://github.com/dcuccia/digital-handbell/issues/7). |
| Mechanical integration | [Completed four-layer-era FreeCAD assembly](../mechanical/README.md) | Rebind the six-layer board and actual part poses; add/check the J1 speaker-plug and wire-exit relief, mounts, USB access, cell isolation and service sequence. [#5](https://github.com/dcuccia/digital-handbell/issues/5). |
| Manufacturing and sourcing | [Quote package](../hardware/handbell/quote-prep/2026-11-09-six-layer/README.md) | Resolve via-fill/process questions, R27/J2 substitutions and every placement/polarity; produce a reviewed, matched order package. [#8](https://github.com/dcuccia/digital-handbell/issues/8). |
| Firmware and bench work | [Firmware/audio plan](firmware-and-audio.md), [sensor initialization gate](motion-sensing.md) | Reproducible audio/motion proof, custom-board pin mapping and replayable gesture cases. [#3](https://github.com/dcuccia/digital-handbell/issues/3), [#6](https://github.com/dcuccia/digital-handbell/issues/6), [#13](https://github.com/dcuccia/digital-handbell/issues/13). |

These can progress in parallel. Manufacturing release depends on the
applicable electrical, mechanical and process dispositions, not just a
price quote. The [before-ordering checklist](../hardware/handbell/quote-prep/2026-11-09-six-layer/unresolved-before-ordering.md)
is the detailed gate; the [review brief](pcb-review-2026-11.md) owns R1-R6.

The selected quote scenario is **10 PCBs with 8 assembled**, Standard
two-sided assembly, ENIG and epoxy-filled/capped through vias: **$345.84
before shipping and tax**, observed November 10. It is a batch quote, not
the complete cost of eight bells or a production unit-price promise.
Nothing has been ordered. HDI and an MCU change remain future options,
not selected redesigns.

## Next: first articles that tell us what works

1. **Release a traceable prototype batch.** Close or explicitly disposition
   blocking review items, obtain owner purchase approval, and record exact
   source, production files, substitutions and incoming inspection.
2. **Bring up one board in stages.** Establish a qualified, current-limited
   plan covering protection, rails, USB/boot/debug, sensor, audio/mute,
   charging and power transitions before relying on the rest of the batch.
3. **Make it an instrument.** Demonstrate note playback and ringing/damping
   behavior, then measure latency, false triggers, idle noise, thermal
   behavior and runtime in the actual enclosure.
4. **Decide whether to respin.** Base revisions on measurements and
   documented anomalies, not on a successful render or connectivity count.

See [validation](validation-plan.md) and
[#9: bring-up and integration](https://github.com/dcuccia/digital-handbell/issues/9).
No dates are promised before the remaining review and first-article results.

## Later: a reproducible, approachable open instrument

Publish a tested hardware/firmware combination, licensed sounds, assembly
instructions, recovery steps and realistic complete-build costs. Establish
the appropriate safety/durability review before a supervised educational
pilot. Wireless, MIDI/host integration and alternative MCUs can be evaluated
separately; the standalone bell must not depend on them.

## Milestones and tracking

| Milestone | Current interpretation |
|---|---|
| [M0: discovery and reference proof](https://github.com/dcuccia/digital-handbell/milestone/1) | Reference imports and measurements exist; a bench proof is still needed. |
| [M1: schematic and subsystem prototypes](https://github.com/dcuccia/digital-handbell/milestone/2) | Electrical and enclosure drafts exist; review and instrument behavior remain open. |
| [M2: custom hardware prototype](https://github.com/dcuccia/digital-handbell/milestone/3) | Current focus: routed six-layer design and quote, not yet an assembled/working prototype. |
| [M3: educational pilot and open release](https://github.com/dcuccia/digital-handbell/milestone/4) | Later; depends on evidence from integrated hardware and appropriate safety review. |
| [M4: future wireless exploration](https://github.com/dcuccia/digital-handbell/milestone/5) | Optional, not a first-instrument blocker. |

All twelve epic issues remain open as of this update. The
[project board](https://github.com/users/dcuccia/projects/1) tracks execution;
[epic specifications](epics.md) preserve the original acceptance criteria
and dependencies. We have not marked an epic complete just because a
design file or a quote exists.

## What we learned

Placement and power/return paths mattered as much as router choice. Quilter
produced useful diagnostic candidates; DeepPCB plus bounded local
engineering led to the zero-open milestone. Different inputs and effort
prevent a fair vendor ranking by routed percentage alone.

Future revisions start with functional cells, power/return/data interfaces
and legal transition access before freezing placement. The
[agent-first PCB workflow](agent-first-pcb-workflow.md) captures that method.
The [research index](README.md#history-and-research) retains the experiments;
it is not an instruction to repeat them.
