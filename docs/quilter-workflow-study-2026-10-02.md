# Quilter workflow learning study

Owner approved October 2 at 14:05 local; fully personal project.
The goal is an economical owner/agent/layout-service workflow, not recovery
of sunk token cost or human-style trace aesthetics. The two rejected raw
outputs and the authoritative 37-open board remain immutable evidence.
Tracking: E04/#4, E05/#5, E07/#7 and E08/#8.

## Two parallel, bounded items

1. **Read-only diagnostic:** compare the actual saved copper in v1.1/v1.2
   against the accepted source. Measure useful joins, lost prior groups,
   remaining opens and native findings without repair, refill or promotion.
   This explicitly releases measurement beyond the earlier preservation
   stop; it does not reverse rejection for integration.
2. **Fresh-layout brief:** reorganize the same circuit into functional
   groups, with fixed mechanical interfaces and controlled placement freedom.
   The [source-bound contract](design-inputs/2026-10-02-quilter-workflow.json)
   assigns all 104 references, including copper-only features and C29 DNP.
   Native staging and imported-constraint qualification are separate items.

Native execution remains pinned Sol/medium with a runtime gate. Astra owns
engineering requirements and acceptance. Target 10-15 minutes per coherent
item, finite subprocess timeouts and no more than two tooling corrections.
Preserve partial evidence and stop on a concrete blocker.

## Existing-output diagnostic checkpoint

The read-only saved-fill diagnostic reproduced the source's 37 graph opens.
Neither raw output was changed or refilled. KiCad 10.0.6 DRC used each
returned project and a separately copied source schematic/library context;
the schematic was not supplied by Quilter.

| Artifact | Same-net graph opens | Native unconnected items | Other native errors / warnings | Parity warnings |
|---|---:|---:|---:|---:|
| Accepted source | 37 | 37, reused source-bound baseline | 234 non-open findings, reused baseline | 46, reused baseline |
| v1.1 | 38 | 38 | 257 / 201 | 46 |
| v1.2 | 22 | 24 | 640 / 211 | 46 |

v1.1 closes VBAT but splits the previously complete USBBOOT and SDA groups.
v1.2 has 15 fewer same-net graph opens with no prior pad-group split found:
I2S_BCLK, I2S_LRCLK, USB_D+, USB_D-, VBAT, VBUS, VHI, VO+ and
`Net-(FB2-P$1)` become complete in that graph. AMP_MUTE, POWER and GND
each improve by one open. The previously unmatched In2 records therefore
did not all translate into lost electrical joins: +3V3 and /IMU_INT2 are
complete in both outputs, and USBBOOT/SDA are complete in v1.2.

These are **same-net routing gains, not 15 accepted electrical repairs**.
The graph reports foreign-net contacts in both outputs; v1.2 also has 21
native `shorting_items` findings, including a RESET via contacting the
MCU GND exposed pad. The graph does not join different-net objects through
these contacts, so the reported gains do not rely on shorts. The graph's
22 versus native 24 unconnected count
for v1.2 remains unreconciled; do not invent a cause or hide the discrepancy.

Do not equate hundreds of witnesses with hundreds of independent fixes.
Each candidate has 65 drill-minimum and 65 via-diameter findings against
returned 0.35/0.604 mm project minima; the example preserved CC2 via is
0.30/0.60 mm. These expose an inherited-via/rule mismatch, not 130 new
routing operations. All 11 v1.1 graph contact witnesses involve cached
zones (two zone UUIDs). Of 187 v1.2 witnesses, 157 involve cached zones
(eight zone UUIDs), while 30 do not. Native v1.2 short findings comprise
seven pad/via, four pad/track, five track/track and five track/via witnesses,
plus a separate crossing. These categories overlap the graph evidence,
not additional independent defect totals. Refill sensitivity was not tested;
the non-zone contacts cannot be attributed solely to the zone-fill cache.
No correction effort has been measured.

**Learning disposition:** v1.2 demonstrates real additional same-net routing,
but neither candidate demonstrates an integration-ready or economical
completion workflow. Continue the fresh-input/constraint track rather than
hand-cleaning these outputs or repeating their setup unchanged.
The original preservation rejection remains in effect.

Local evidence under the experimental root:
`quilter\outputs\useful-connectivity-diagnostic-20261002T1408`.
`report.json` SHA-256:
`0e15cc01e608197aee1b0f4547f2cfdf20f090b9583ba2ff471d676863dad493`.
It binds the diagnostic script, graph helpers, original/copy PCB hashes,
per-net partitions and native execution context. Native DRC reports are
`v1.1-drc.json` and `v1.2-drc.json`. Script elapsed time was 150.03 seconds,
not total engineering time or platform compute time. Authoritative source
and both original output PCB hashes remained unchanged.
The saved-evidence supplement `short-evidence-clarification.json` has SHA-256
`0b1110a3821815da4432387e2b804d4924d55001e19b84b1685aefe5ad8259fd`;
it groups witnesses and records the graph-union and rule-context limits
without another native run.

## Initial placement strategy

Keep BT1/BT2, MH1/MH2, X6, J1 and J2 at their exact accepted native poses.
Retain the outline, mounts, contact metal, connector/USB access, component
height limits and front-electronics/rear-contact split. The nominal D43
circle is not a replacement for the outline with tabs and USB tongue.

Keep U4 and C24 at their current poses for the first input, with their five
mandatory filled/planarized/capped vias. This is a deliberate limited seed,
not a claim that the whole old floorplan must survive. Independent vias
cannot be assumed to follow a movable component in Quilter. A relocatable
process block or an ordinary-via alternative would need separate evidence.
Thus this is a largely fresh layout with two process seeds, not an empty
board falsely stripped of manufacturing obligations.

The other references may move/rotate on F subject to the contract. Keep
electrically related groups together without inventing narrow placement
rectangles: MCU supply/return, crystal, flash/boot, USB, IMU, regulator,
charger, source selection, audio switch, boost, protection, amplifier/filter,
button, indication and debug. Associate capacitance with the actual supply
pin, not merely a shared +3V3 net. Group membership is not by itself a
decoupling-distance, return-path or switching-loop constraint.

Two important input traps:

- Quilter can flip unplaced components unless tied to a layer-specific
  placement region. The single-sided candidate filter is not enforcement.
- Off-board grouping regions do not constrain the side. We must verify
  actual KiCad region associations and F-only behavior in the imported
  model before submitting, not rely on how a staging picture looks.

Mechanical envelopes remain screening inputs, not qualified tolerances.
The manifest contains historical landmark/proxy fields as well as native
origins; fixed poses must come from the exact accepted PCB, not stale
descriptive coordinates. Newly moved parts require exact mechanical rebinding.
IC4 rotation also changes the sensor-to-bell coordinate mapping.

## Preserve engineering intent, not obsolete obstacles

Fresh-layout preparation may replace ordinary old routing on an isolated
copy after a complete keepout/seed inventory. It must not delete footprint
copper, corrected USB slots/lands, custom Q3 geometry or the five process
vias. No old source file is a scratch input.

Fixed rear-contact/USB/mount restrictions remain fixed. Crystal,
switch-node and private-return exclusions tied to moved components must
be re-expressed against those components, not copied at stale coordinates.
Through-vias still expose conductive B lands under battery metal even when
filled or tented. More copper layers do not solve that access restriction.

Raw CELL_NEG is not protected GND. PROT_FET_RETURN is not a general ground
plane. Preserve R26/R27 and R24/C28 private pickoffs and short local boost
output-capacitor supply/return loops. If an essential duty cannot be encoded
in Quilter, explicitly retain a reviewed local block or use a qualified
independent topology gate; do not silently let it become a generic signal.

No generic 500mA rail table, 100ohm speaker-output pair, incorrect capacitor
values or empty clock/switching comprehension is approved for reuse.
Current budgets and powered behavior remain provisional engineering gates.

## Layer comparison and cost

Prepare comparable real four- and six-layer constructions once the common
input is qualified. Eight layers is optional if it adds little setup/review
and remains free. Use actual supplier construction data and explicit return
references; do not merely increase the enabled-layer count. Let placement
adapt while holding outline, BOM, electrical and manufacturing requirements
constant. This compares complete workflows, not layer count in isolation.

Measure native outcomes, defect roots, owner/agent interventions, setup and
review effort, actual service cost, manufacturing implications and elapsed
turnaround. Do not invent token costs or internal compute measurements from
wall time. A visually unusual layout can be useful; electrical/process
failures cannot be hidden by a completion percentage.

Public pricing checked October 2:

- [Free tier](https://www.quilter.ai/free-ai-pcb-design): personal/academic
  eligibility, free access, unlimited iterations and product features.
- [Paid pricing](https://www.quilter.ai/pricing): per project, based on
  unrouted input pins, with iterations and parallel jobs included and
  advertised 10% BOM flexibility. No public dollar-per-pin quote found.
- The prior job's 96 pins-to-route is neither 37 native opens nor 325
  physical pads. A fresh input can change that count and any paid quote.
- Confirm this account's actual free terms before submission. Stop at
  payment/upgrade or a changed agreement needing owner action.
- Personal use does not itself settle output-redistribution rights.
  [Terms](https://www.quilter.ai/terms) and third-party hardware attribution
  remain a gate before publishing Quilter native designs or a kit.

## Native inventory blocker and stopping point

The inventory did **not** complete. KiCad 10.0.6 Python compatibility failures
exhausted the initial attempt plus two corrections: library-ID formatting,
UTF8 field conversion, then a native assertion from `PCB_VIA.GetWidth()`
without a layer argument. The last attempt reached its 120-second hard
timeout and was stopped. No inventory JSON or prepared input was produced.
This is our tooling failure, not a measured Quilter limitation.

Local evidence under the experimental root:
`quilter\outputs\inventory-20261002T141349-sol`.
The blocker report `inventory-run-blocker.json` has SHA-256
`9e666f06f3e3824fa6900adceae5fe8fd0233e4adb74bbb638f97d3e3fa6deaa`;
the failed script `native_constraint_inventory.py` has SHA-256
`e683e036830811daefd3e6f716f663389d04ea919ee9814ee23df1f7d9192ef5`.
Root independently rechecked all four authoritative package hashes after
the failure; they still match the contract. No placement, copper, original
output, or CAD changed, and no cloud job was submitted.

**Root disposition:** do not simply change the via accessor and rerun.
Review of the failed script also found acceptance-relevant gaps:

- Keepout purpose is classified from names, without the required supporting
  source/report evidence. Unknown or ambiguous duties must remain unresolved.
- Polygon extraction omits holes; fill-read exceptions silently become null.
  A deletion/relocation inventory needs complete geometry and explicit failures.
- The check labeled "81 electronics" counts all 102 non-contact references,
  rather than the fitted manifest subset. Via/pad binding tests only equal
  centers and nets, not actual copper contact for offset process vias.

No values from the uncompleted script qualify the native inventory.
The earlier source/manifest-backed group brief remains a proposal, not
proof that placement regions or process seeds have now been inventoried.
The retry budget is exhausted, so fresh-input preparation and layer trials
are **blocked**, with no automatic repair or additional native run released.

## Next item, requiring a new bounded authorization

Repair only the isolated inventory tool, reusing exercised KiCad accessors
and source-bound report/manifest definitions rather than another untested API
sequence. Address the gaps above before one bounded read-only rerun. Stop
with either a complete evidence-bearing inventory or a concrete failure;
do not move parts, delete copper, choose a stackup or submit a job.

The inventory's unchanged engineering objective is:

Start from the exact source hashes in the JSON, not the held MCU fanout
fixture or either Quilter output. In one new private staging directory,
inventory fixed poses, functional-group pin associations, five process vias,
fixed/mechanism-relative keepouts and height restrictions. Prove all 104
references are assigned exactly once and preserve 325 physical pad identities.
Stop with the explicit constraint map and any unsupported import requirement
before moving parts or deleting ordinary copper. That separates engineering
intent from irreversible-looking preparation and avoids another blindly
configured cloud run.

References: Quilter [placement guide](https://docs.quilter.ai/guides/placement-guide),
[KiCad regions](https://docs.quilter.ai/design-parameters/placement-regions),
[single-sided requirement](https://docs.quilter.ai/design-parameters/single-sided-placement),
[keepouts](https://docs.quilter.ai/design-parameters/keepouts),
[stackups](https://docs.quilter.ai/design-parameters/stackups).
