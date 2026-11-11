# Documentation

[Project home](../README.md) · [Gallery](design-gallery.md) · [Roadmap](roadmap.md) · [Contributing](../CONTRIBUTING.md)

Start with the current design below. Dated studies record what was known at
the time; their words "current" or "next" do not override newer review records.

## Current design and review

| Document | Use it for |
|---|---|
| [Design gallery](design-gallery.md) | Bell, board and populated-PCBA views, with dates and source limits |
| [Roadmap](roadmap.md) | Current priorities and the path to a working instrument |
| [Six-layer board review](pcb-review-2026-11.md) | Exact snapshot, remaining risks and review packages R1-R6 |
| [Hardware guide](../hardware/README.md) | Native KiCad, libraries, reference designs and revision selection |
| [Mechanical guide](../mechanical/README.md) | FreeCAD/STEP/STL inventory and the six-layer integration gap |
| [Order package](../hardware/handbell/quote-prep/2026-11-09-six-layer/README.md) | Source-bound BOM/CPL, export recipe and order status |
| [Quote record](../hardware/handbell/quote-prep/2026-11-09-six-layer/pcba-quote-2026-11-10.md) | November 10 prices, 10-PCB/8-assembly scenario and live part selections |
| [Incoming checks](../hardware/handbell/quote-prep/2026-11-09-six-layer/unresolved-before-ordering.md) | Sourcing, placement and process items to confirm on arrival |

## Understand and contribute

| Topic | Reading |
|---|---|
| Goals and requirements | [Project brief](project-brief.md), [epic specifications](epics.md), [decision log](decisions.md) |
| Circuit architecture | [Architecture](architecture.md), [T8 electrical revision](t8-electrical-revision.md) |
| Sound and motion | [Firmware/audio](firmware-and-audio.md), [motion sensing](motion-sensing.md) |
| Measurements and mechanics | [Printed-bell design](printed-bell-revision.md), [material/handle notes](printed-bell-material-and-handle.md), [measured inputs](measurements/2026-09-11-shell-speaker-inputs.json) |
| Review and testing | [Validation plan](validation-plan.md), [USB qualification](usb-connector-qualification.md) |
| Source reuse and tools | [Reference catalog](reference-designs.md), [KiCad setup](kicad-setup.md), [tool guide](../tools/README.md), [attribution](../ATTRIBUTION.md) |

## Working conventions

- **Current summaries:** project README, roadmap and directory guides point
  to the current artifacts, not to the most recently named old folder.
- **Engineering evidence:** dated reports, manifests and design inputs bind
  conclusions to exact files. A new image does not update a CAD model.
- **Originals and derivatives:** preserve upstream references and historical
  snapshots. A new board/CAD revision gets its own directory and evidence.
- **Public versus private:** publish source, attributed views and sanitized
  results. Account captures, private backup receipts, credentials and raw
  router downloads do not belong in this repository.

The private router-bakeoff archive was backed up and removed locally on
November 10. Historical absolute paths in its ledgers are archive locators,
not files a fresh clone provides. Current review sources and public CAD
remain in this repository; owner-private recovery records are kept separately.

## History and research

These are useful when investigating a specific decision, not the onboarding
sequence or a queue of authorized work.

| Period / subject | Preserved record |
|---|---|
| Original concept | [2023 notes](../Design%20Notes.md), [system diagram](../System%20Diagram.pptx) |
| Reference reduction and first layout | [0.2 handoff](electrical-reduction-and-placement.md), [schematic plan](schematic-plan.md), [compact power/packaging](compact-power-and-packaging.md) |
| Wing and T8 packaging | [Wing iteration](electromechanical-wing-iteration.md), [T8 integration](t8-integration-plan.md), [mechanical feasibility](mechanical-feasibility.md) |
| Earlier part/process work | [BOM readiness](pcba-bom-readiness.md), [quotation requirements](pcba-quotation-plan.md), [power selection](power-component-selection.md), [device selection](device-component-selection.md) |
| Two-/four-layer closure | [Closure ledger](pcb-closure-plan.md), [routing readiness](routing-readiness.md), [routing tooling](routing-tooling.md) |
| Router comparison | [September bakeoff](routing-bakeoff-2026-09-27.md), [October handoff](agent-handoff-2026-10-01.md), [Quilter workflow study](quilter-workflow-study-2026-10-02.md) |
| Reusable Quilter lessons | [Quilter playbook](quilter-playbook.md); documented, observed and proposed behavior kept distinct |
| Six-layer closure | [Multilayer plan](multilayer-routing-plan-2026-11.md), [November ledger](multilayer-gate-a-2026-11.md) |
| Next-revision method | [Agent-first workflow](agent-first-pcb-workflow.md), [routing-agent policy](routing-agent-policy.md) |

`measurements/` holds source-bound JSON/SVG evidence; `design-inputs/`
holds dated interface contracts. `images/showcase/` contains only
presentation derivatives described in the [gallery](design-gallery.md).
Neither image folders nor old `bom-draft.csv` files are manufacturing inputs.
