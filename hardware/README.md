# Hardware

[Project home](../README.md) · [Board review](../docs/pcb-review-2026-11.md) · [Mechanical guide](../mechanical/README.md)

## Open the right design

| Directory | Status and purpose |
|---|---|
| [Six-layer review snapshot](handbell/iterations/printed-bell-six-layer-review/README.md) | **Current electronics review target.** PCB `2f738ccb`, zero opens; remaining DRC/parity and engineering review gates are explicit. |
| [Six-layer quote package](handbell/quote-prep/2026-11-09-six-layer/README.md) | BOM/CPL, export checks, supplier quote and before-ordering list for that exact snapshot. Not production release files. |
| [Revision guide](handbell/iterations/README.md) | Which older PCB studies to use for history, not for ordering |
| [Original 0.2 derivative](handbell/README.md#preserved-02-electrical-and-placement-draft) | Early unrouted schematic/placement and its electrical integration notes |
| [Parts evidence](handbell/parts/README.md) | Candidate identities and manufacturer-based dimensional/process work; not live stock |
| [Adafruit 5768 reference](reference/adafruit-5768/README.md) | Pinned Prop-Maker Feather source and native conversion |
| [Adafruit 4438 reference](reference/adafruit-4438/README.md) | Pinned LSM6DSOX source and native conversion |
| [Adafruit 4654 reference](reference/adafruit-4654/README.md) | Pinned TPS61023 MiniBoost source and native conversion |

Keep the **whole repository checkout**: library tables can reference sibling
packages. Do not bulk-refresh legacy footprint aliases, overwrite an old
board with a generator, or use an old `bom-draft.csv` for the current board.
Native KiCad sources are the editable design; Gerbers, renders and CPL files
are revision-specific outputs.

Hardware adaptations retain [CC BY-SA 3.0 and upstream notices](../ATTRIBUTION.md);
the root MIT license does not replace them. Private router experiments and
backup records are not required to open the public review snapshot.
