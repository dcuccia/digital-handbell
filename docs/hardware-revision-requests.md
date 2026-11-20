# Hardware revision requests

[Roadmap](roadmap.md) · [Board review](pcb-review-2026-11.md) · [Tracking issue #19](https://github.com/dcuccia/digital-handbell/issues/19)

The next PCB revision will be shaped by what the prototype batch teaches us.
This page explains how requests and fixes are collected until then.
**Collecting a request does not start a redesign.** It authorizes no routing
spend, supplier upload or fabrication; the owner selects scope at revision
kickoff.

## Where requests live

- **One GitHub issue per request**, labeled `next-board-rev`. Use the
  [Board revision request](https://github.com/dcuccia/digital-handbell/issues/new?template=board-revision-request.yml)
  form. It asks for the evidence, the affected references, nets or pins,
  the firmware and mechanical impact, a priority, and how we'd know the
  change works.
- **The pinned tracking issue, [#19](https://github.com/dcuccia/digital-handbell/issues/19)**,
  lists every request with its status, and keeps a checklist of candidates
  from earlier reviews that still need triage.
- The [label view](https://github.com/dcuccia/digital-handbell/issues?q=label%3Anext-board-rev)
  shows everything filed.

Issues stay the record of discussion and decisions. This page holds only
the process, so it does not go stale.

## Where requests come from

| Source | Example | Becomes a request when |
|---|---|---|
| Bring-up of the prototype batch ([#9](https://github.com/dcuccia/digital-handbell/issues/9), [bring-up guide](firmware/bring-up.md)) | A rail, pin or footprint misbehaves | The anomaly points to a board change rather than firmware or assembly |
| Review packages R1-R6 ([board review](pcb-review-2026-11.md)) | Narrow margins, process exceptions, service access | Someone proposes a concrete change and its cost |
| Capability gaps found by software or mechanical work | No battery-voltage sense ([#17](https://github.com/dcuccia/digital-handbell/issues/17)) | Always: describe the gap and its evidence |
| Options under evaluation | An MCU change ([#12](https://github.com/dcuccia/digital-handbell/issues/12)) | It is evaluated by whole-system cost, not pin count |

## Status and triage

**Proposed → accepted for next rev → done**, or **deferred/declined with a
reason**. At kickoff the owner reviews the tracking issue with bring-up
results in hand. Accepted requests then become inputs to the
[agent-first PCB workflow](agent-first-pcb-workflow.md): system
power/return/data map and functional-cell contracts first, placement and
routing after.

## Firmware-first requests

Where a request adds an input or output, write the firmware support first,
inactive on the current board, and test it on a computer. Enabling it on
the new board is then a profile entry in
[`firmware/src/handbell/platforms`](../firmware/src/handbell/platforms/).
Prefer the Raspberry Pi Pico pin conventions where they fit, so the stock
Pico CircuitPython build names the pins already: `board.VOLTAGE_MONITOR` on
GPIO29 and `board.VBUS_SENSE` on GPIO24. Battery and USB/charge sensing
(#17, #18) were done this way. See the
[firmware architecture](firmware/architecture.md#battery-and-power-sensing-next-revision).
