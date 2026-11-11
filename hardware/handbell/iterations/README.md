# PCB revision guide

[Hardware home](../../README.md) · [Current review](../../../docs/pcb-review-2026-11.md)

**Use `printed-bell-six-layer-review` for current electronics review.**
Directory names such as `quote-candidate` and `clock-draft` describe older
milestones, not the newest or order-ready board.

| Revision | Role |
|---|---|
| [printed-bell-six-layer-review](printed-bell-six-layer-review/README.md) | **Current:** zero-open public six-layer snapshot `2f738ccb`, derived from private `best-0-testen` `0051b2e3`; review only |
| [printed-bell-four-layer](printed-bell-four-layer/README.md) | Preserved 37-open four-layer checkpoint `adc262b3`; not the six-layer source |
| [printed-bell-clock-draft](printed-bell-clock-draft/README.md) | Earlier two-layer clock/power/routing work |
| [printed-bell-quote-candidate](printed-bell-quote-candidate/README.md) | Historical quote-preparation candidate; **not** the November quote input |
| [printed-bell-power-rework](printed-bell-power-rework/README.md) | Boost-loop and protector-sense corrections; source of the preserved root printed-bell CAD |
| [printed-bell-routing](printed-bell-routing/README.md) | Initial partial routing and its power-layout review |
| [printed-bell-front](printed-bell-front/README.md) | All-front-electronics placement with two rear contacts |
| [t8-protected-draft](t8-protected-draft/README.md) | Compact cell protection, 2 MB flash and T8 contact architecture |
| [wing-draft](wing-draft/README.md) | Earlier mixed-face electronics/cartridge study |

These snapshots retain their local libraries, manifests and review records.
They have deliberately **not** been moved or deduplicated: relative library
paths, source hashes and CAD regeneration scripts depend on them.

The [November quotation package](../quote-prep/2026-11-09-six-layer/README.md)
is separate from every historical `reports/bom-draft.csv`. The
[mechanical guide](../../../mechanical/README.md) identifies the most recent
completed assembly; it still predates the six-layer board.
