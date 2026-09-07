# Decision log

Planning snapshot: 2026-09-06. A provisional choice is a starting point for
experiments, not a final component or manufacturing commitment.

| ID | Decision / question | Current disposition | Evidence to close or revisit |
|---|---|---|---|
| D01 | Repository continuity | Retain the existing public `dcuccia/digital-handbell`, history, MIT license, 2023 notes and diagram | New planning and linked execution issues |
| D02 | Integrated baseline | Prefer Adafruit 5768 for first bench work and schematic derivation | Audio/motion/power experiments and import review |
| D03 | First MCU/runtime | RP2040 + CircuitPython provisionally preferred; no first-revision wireless requirement | Latency, audio/memory, idle/wake and USB workflow evidence |
| D04 | Sensor | Start with LIS3DH acceleration, preserving the original six-DOF idea as an option | Recorded gesture corpus and measured false/missed triggers |
| D05 | CAD | KiCad 10.0.6 installed; pinned EAGLE reference converted on 2026-09-07 | Initial connected-net comparison passes; ERC and complete footprint/layout review remain open |
| D06 | Hardware reuse license | Retain source-compatible CC BY-SA 3.0 for adaptations of verified sources; preserve root MIT for original code/docs | Full notices and per-file provenance at import; resolve 4884 version before use |
| D07 | Packaging | Prefer circular, one-face assembly, two copper layers | Measured shell stack, complete placement/routing and comparative quotes |
| D08 | Audio rail and quiet idle | Start by studying 5768's unboosted switched rail; independent mute/boost remain open | Headroom, noise/clicks, current, low-cell behavior and sequencing |
| D09 | Cell and charger | No cell/capacity/current selected; do not adopt 196/200 mA blindly | Cell data, thermal/protection strategy, runtime and USB input budget |
| D10 | Play while charging | Unresolved; must be explicitly permitted or prevented | System power-path/input-current and charging/temperature evidence |
| D11 | Speaker and cavity | No selected driver; compare shallow/light vs deeper alternatives | Actual fit, matched-level listening/response, mass, distortion and current |
| D12 | USB and mounting | Preserve slot/opposite screw and printed-carrier concepts; neither selected | Supported load path, assembly access, retention and isolation |
| D13 | Musical behavior | Note range, tuning, fixed/selectable note, retrigger/damping/polyphony and controls open | Requirements and prototype comparison |
| D14 | Fabrication/assembly | Quote JLCPCB populated boards; use OSH Park as bare-board alternative | DFM acceptance and complete cost at actual quantities |
| D15 | Future wireless | ESP32-S3 is the preferred candidate to evaluate before C3 for native USB usability | Explicit use case, CircuitPython protocol support, RF/metal-shell assessment, power and synchronization |

For a change, append date, rationale, alternatives, affected requirements,
upstream/prototype evidence, and the deciding issue. Do not overwrite an earlier
decision's rationale as if the new choice had always been established.

## 2026-09-07: precursor scope and CAD readiness

The owner clarified that the 2023 wireless/6-DOF work is a precursor vision,
not a binding requirement for the current instrument. Preserve it as history
without treating every earlier feature as mandatory.

D05 advances from a recommendation to an exercised toolchain: KiCad 10.0.6,
standard libraries, native schematic/PCB import, schematic PDF/netlist exports,
and ERC execution. All 71 nonempty upstream board-signal pin groups match the
imported schematic after accounting for six reference-name conversions.
The initial import still has 50 ERC findings. The
[reference report](../hardware/reference/adafruit-5768/README.md) records the
limits; this is not schematic approval or a handbell design release.

## Initial risk register

| Risk | Mitigation / owning epic |
|---|---|
| Source import changes connectivity or package mapping | Preserve reference, compare nets/pins/footprints; E02/E04 |
| Tiny speaker lacks useful response for desired notes | Compare cavity-mounted drivers early; E03/E05 |
| Idle hiss/clicks or audible USB/power artifacts | Define states, measure transitions, review supply/SD_MODE; E03/E04/E09 |
| Audio vibrations or ordinary handling trigger notes | Record real motion corpus and refine nonblocking classifier; E06/E09 |
| Power savings lose the first strike or increase latency | Measure wake and always-ready alternatives; E03/E06 |
| Reference charge current unsuitable for small cell | Cell-specific design and independent review; E01/E04 |
| Board fits in 2D but not behind speaker/cell | Tolerance-aware 3D stack and assembly mock-up; E01/E05/E07 |
| USB or screw loads crack solder joints or damage cell | Supported carrier, stops, insulation, retention review; E05/E10 |
| Fine-pitch/rare parts undermine low-cost assembly | Early catalog BOM and quote, planned substitutions; E04/E07/E08 |
| MIT label hides hardware or asset obligations | Separate provenance/license scopes; E02/E11 |
| Wireless is ineffective inside metal shell | Defer radio; require antenna/enclosure evaluation; E12 |
| Educational prototype mistaken for child-ready product | Explicit safety/compliance gate before pilot/distribution; E10/E11 |
