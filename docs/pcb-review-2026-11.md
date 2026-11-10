# Zero-open PCB milestone: review entry point

The November 9 milestone closes routing connectivity on a **six-layer
candidate**, not electrical, manufacturing, mechanical or safety acceptance.
The owner requested a PR to `main` for both board review and lessons for
the next revision. Opening or merging that milestone PR does not approve
fabrication, powered use, supplier uploads or further paid routing.

## What to review first

Read this brief, the [snapshot README](../hardware/handbell/iterations/printed-bell-six-layer-review/README.md)
and [manifest](../hardware/handbell/iterations/printed-bell-six-layer-review/MANIFEST.sha256), and the
[agent-first workflow](agent-first-pcb-workflow.md). Use the
[November ledger](multilayer-gate-a-2026-11.md) for individual dispositions.
The long [Quilter study](quilter-workflow-study-2026-10-02.md) and
[playbook](quilter-playbook.md) retain earlier evidence; they are not the
current board's release record.

This branch includes the cumulative evaluation history and experimental
tools, not just the final TESTEN change. Many helpers have deliberately
narrow source/geometry assumptions. Their inclusion does not qualify them
as general-purpose routers or validators.

## Exact source and publication gate

The preserved private milestone is `multilayer-20261109\best-0-testen`:

```text
handbell.kicad_pcb
SHA-256 0051b2e32c78533f102f3e20cb1bdac3c23377ec9d53b594b4ae5deda663a6bd
```

Its immediate parent is `best-1-usbboot`, PCB
`bae58edd2c31f94cf12ba2072045e98007f6474ea3216f3d98123993c535406f`.
The historical 37-open four-layer PCB remains unchanged at
`hardware/handbell/iterations/printed-bell-four-layer`; the new milestone
must not overwrite it or relabel its CAD/placement manifest as current.

The owner approved a **separate provenance-cleared review snapshot** in
this PR. It is now published at
`hardware/handbell/iterations/printed-bell-six-layer-review`, PCB SHA-256
`2f738ccbae390424b7248feb94bac5e0c677b81224d5d8f8b290bbb0cc6792e2`.
J1 was independently rebuilt from the official JST dimensional drawing
after the earlier converted library asset's redistribution terms could not
be cleared. Its pad semantics, pose and nets match; every byte outside J1's
footprint expression is unchanged. This publication derivative is **not**
hash-identical to the private milestone. Project and schematic remain exact.

The [publication validation](../hardware/handbell/iterations/printed-bell-six-layer-review/reports/publication-validation.json)
binds the manufacturer source, dimensions, hashes and native results.
All board footprints resolve; embedded schematic symbols permit review,
but blanket library refresh remains unsupported for three documented legacy
aliases. No current CAD/placement manifest is claimed.

Future publication changes remain gated on an exact file allowlist, hashes,
library completeness and applicable hardware notices. Do not copy the whole private
trial directory: `.kicad_prl`, lock files, account/browser material and backup
records are excluded. Imported footprint provenance must be resolved, not
silently assigned the root MIT license. Any unresolved publication blocker
must be stated in the PR rather than hidden by substituting a different PCB.

## Evidence at the routing milestone

The final change couples a +3V3 via relocation with an In3 SDA detour and
the F.Cu IC1.19 TESTEN-to-exposed-pad connection. The via-only attempt
closed the open but shorted SDA; it was rejected. The paired change was
accepted for routing continuation after independent lead DRC/checker runs.

| Same-environment native result | Parent | Milestone |
|---|---:|---:|
| Unconnected items | 1 | 0 |
| Non-open findings | 388 | 388 |
| Schematic-parity findings | 46 | 46 |

Saved final-stage evidence reports unchanged SDA terminal membership,
connected SDA and all 33 +3V3 terminals, refilled ground antipads, and a
standard-checker PASS allowing changed nets +3V3/GND/SDA. The lead rerun
confirms counts by category and checker PASS. The broad changed-net
allowlist is **not** by itself an exact local-complement proof; retain the
UUID/geometry and connectivity evidence for review.

| Remaining non-open category | Count |
|---|---:|
| `items_not_allowed` | 71 |
| `track_dangling` / `via_dangling` | 6 / 1 |
| `lib_footprint_issues` | 97 |
| `silk_edge_clearance` | 5 |
| `text_height` / `text_thickness` | 69 / 2 |
| `silk_overlap` / `silk_over_copper` | 47 / 90 |

The table above describes the private routing milestone. The packaged
publication derivative has **291 non-open findings, zero opens and 46
parity findings** in the fresh native run. The difference is 97 missing-
library findings disappearing after supplying the local libraries, not
97 repaired copper defects. Every other category is unchanged. The
[published native report](../hardware/handbell/iterations/printed-bell-six-layer-review/reports/native-drc.json)
is the review input.

These are not all cosmetic or waived. Unchanged counts can also conceal
different subjects. Review the actual objects and rule origins, grouping
repeated witnesses into root issues while retaining every raw finding.
Library findings vary with the installed environment; compare under one
declared environment rather than calling a changed count a board defect.

## Board-review work packages

Each package produces a source-bound finding/disposition record, not
automatic PCB edits. Identify severity, affected refs/nets/objects, evidence,
decision owner and whether the item blocks fabrication. Work in bounded
items and revalidate affected dependencies after a correction.

| Package | Required review and exit evidence |
|---|---|
| R1: Native rules and parity | Disposition all 71 prohibited-item findings, 46 parity findings and dangling copper. Library availability now resolves the former 97 missing-library findings, but does not prove library-to-board equivalence or justify bulk refresh. Distinguish intended exceptions from real net/geometry errors; no blanket waiver because the previous board had them. Confirm project/embedded rules and exact local-delta preservation, not only category counts. |
| R2: Power, returns and critical signals | Review branch current/drop/thermal budgets, necks/vias, boost loops/private pickoffs, CELL_NEG isolation, and each MCU/IMU capacitor's supply and return. The ledger explicitly records USB initially routed as separate traces: establish coupled 90-ohm geometry and reference continuity on the actual stackup, including transitions and both resistor-side pairs. Review clock, QSPI, I2S and TESTEN/boot/recovery duties. Zero opens is not SI/PI evidence. |
| R3: Process and margins | Inventory every filled/planarized/capped through-via, including U4/C24 and the C7/GAIN0 additions; reconcile exact via identities with pad/mask/paste and IPC-4761 Type VII fabrication notes. Confirm supplier support and cost. No HDI/laser microvias. Review the narrow-margin table below and actual rule minima. |
| R4: Mechanical and service | Rebind the exact new board and placements into the assembly. Check contact/cell isolation, speaker height, mounts, USB mating, assembly order and service access. Include relocated JST ACHL J1 and its mating harness; preserve both BTL leads. TP5 is a 0.30 mm microprobe land, TP14 a 0.6 mm rear land, not qualified universal hand probing. Do not reuse historical CAD as if it matched. |
| R5: Assembly and quotation | Generate matched BOM/CPL, fabrication/drill and assembly outputs only from the reviewed revision. Reconcile J1 `BM02B-ACHLKS-GAN-ETF` / C594367, all fitted back-side contacts, X6 slots/placement and DNP exclusions. Carry process notes and the exact silk waiver; a supplier quote is neither an order nor functional approval. |
| R6: Bring-up and acceptance | Define a bounded, risk-based bring-up before powered use: protection/charging/source selection, rails, USB/boot/debug, IMU initialization, audio/mute and thermal/current behavior. The owner's limited testing preference does not establish reliability or remove these gates. No child-use claim follows from a working prototype. |

Known margins/dispositions to carry into R3:

| Subject | Recorded geometry | Existing disposition / still needed |
|---|---|---|
| TESTEN-area +3V3 via to IC1 exposed pad | 0.200 mm copper gap, at the rule limit | Final routing pass, no extra headroom; process review remains |
| Same via to SDA / AMP_MUTE / In2 VBUS | 0.255 / 0.231 / 0.255 mm | Retain exact all-layer clearance witnesses and hole checks |
| U5-area new GND/VAMP branches | 0.202272 mm against 0.200 mm floor | Lead accepted for continued routing, not an owner fabrication waiver |
| U5-area VAMP / BOOST_SW | 0.203939 mm against 0.200 mm floor | Same; original stricter-screen HOLD stays preserved |
| Two intrinsic U5 pad pairs | 0.200 mm | Footprint-intrinsic, not improved by translation; supplier/process disposition |
| Silkscreen over pads after C1/C4 relocation | Owner approved the scoped silk waiver | Do not extend it to mask/copper, identification elsewhere or every remaining warning |

## Lessons review: what changes next time

**Observed:** ordinary routing made substantial progress, but the final
connections required understanding subsystem and cross-layer dependencies.
C1/C4 had to return near U2; service lands could move without deleting
recovery; J1's connector/placement change enabled VO+; C7/GAIN0 needed
explicit process choices; USBBOOT/C14 and TESTEN/SDA needed paired local
repairs. The broad last-open DeepPCB trial cost $7.50 and worsened opens
from 1 to 6; the successful local TESTEN closure used no further paid run.
This does not quantify total agent cost or prove local routing is always
cheaper.

**Recommended change:** design functional cells and the inter-cell power,
return and data corridors before freezing geometry. Carry pin-level
capacitor, branch, ground-transition, boot and connector duties in cell
contracts. "Islands" must not mean arbitrary ground-plane splits. Review
interfaces and all-layer access before spending on detailed routing. The
[evergreen workflow](agent-first-pcb-workflow.md#phase-0-system-architecture-before-coordinates)
is the implementation guidance, including placement gates and MCU-swap
evaluation criteria; this is a proposed improvement, not a measured saving.

**Next-time experiments, not launched:** compare a small number of
subsystem-first floorplans and real stackups under the same obligations;
evaluate an MCU change by whole-system hardware/software/process cost,
not pin count alone. DeepPCB v5 placement/Cooper could supply a bounded
comparison or second opinion after capability/price checks and separate
authorization. No Cooper review has been run or substituted for R1-R6.

Quilter produced useful diagnostic routing and exercised partial-copper
preservation, but its product candidates were not accepted; imported rules,
returned native preservation, widths and critical paths needed independent
checks. DeepPCB plus later local engineering produced this milestone.
Different inputs, placement, stackups and effort prevent an apples-to-apples
vendor ranking. Prefer measured end-to-end effort and remaining root risks
over service-reported routed percentages.

## PR and release boundaries

The milestone PR can preserve a clearly limited, reviewable engineering
checkpoint while R1-R6 remain open. Merge must not be presented as closing
E04/#4, E05/#5, E07/#7 or E08/#8. Track review findings in the PR and linked
epics, and link each resolved item to the exact revised artifacts.

Fabrication release requires the applicable review dispositions, matching
outputs and explicit owner approval. Paid routing, external review upload,
supplier submission/order and powered-use approval are separate decisions;
the unspent TESTEN routing budget does not automatically transfer to them.
