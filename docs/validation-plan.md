# Validation and release evidence

This is a planned evidence matrix, not a report of completed measurements.
Target values are TBD in E01; each protocol must record setup, instruments,
uncertainty, hardware/firmware revisions, input conditions, results, and
disposition. Preserve measured versus calculated versus vendor-specified labels.

## Evidence matrix

| ID | Requirements | Measurement / review | Gate |
|---|---|---|---|
| V01 | R08-R12 | Inner shell profile, tolerance-aware speaker/cell/PCB stack and assembly sequence using actual samples | Before outline freeze |
| V02 | R15-R17 | Pinned source licenses, import fidelity, source-to-net and retained/removed block review | Before schematic freeze |
| V03 | R02-R07 | Power/USB/GPIO/flash/boot schematic review and individually resolved ERC findings | Before layout |
| V04 | R05, R22 | Cell datasheet/protection/polarity, current/voltage/temperature limits, safe retention and cutoff strategy | Before cell-powered prototype |
| V05 | R04, R13-R14 | Acoustic response/timbre, SPL at fixed distance, clipping/distortion, driver excursion and temperature at defined levels | Speaker and gain selection |
| V06 | R13-R14 | Idle hiss/noise with stated bandwidth/distance, startup/shutdown clicks, USB/no-USB transitions, reload/reset, low battery | Audio/power design selection |
| V07 | R03, R06, R13, R25 | Strike-to-sound latency/jitter, repeated strokes, missed/false strikes and false damping; compare gyro-enabled/disabled chest-stop/rest recognition on the same motion corpus | Firmware and sensor selection |
| V08 | R05, R13 | Ready/play/sleep/off currents, peak current, actual runtime under a stated duty cycle, wake/first-strike behavior | Battery/power-mode selection |
| V09 | R05, R07 | USB-only/battery-only/combined operation, cable/source limits, unplug/replug, charger termination and thermal behavior | Before permitting play while charging |
| V10 | R07-R12, R22 | USB mating/load path, speaker/cell retention, cable abrasion, screw intrusion, metal insulation, shake/drop serviceability | Before educational pilot |
| V11 | R11-R12, R18-R19 | DRC, stackup, 3D clearances, footprints, BOM availability, panel/CPL preview and vendor acceptance | Before fabrication order |
| V12 | R02-R07 | Board bring-up: current-limited input, rails, recovery/programming, I2C/interrupt, I2S, speaker, protection/status functions | Before enclosing custom PCB |
| V13 | R16, R20, R23 | Reproducible export/install/recovery, attribution, complete kit instructions, assembly time and fault diagnosis | Release candidate |
| V14 | R13, R18, R22-R23 | Intended age/use classification, sound exposure, battery access, small parts, edges and appropriate compliance review | Before distribution to children |

## First bench procedure

Start with the integrated reference board and a current-limited bench supply,
then a documented compatible protected cell only after its limits are reviewed.
Confirm speaker impedance and BTL wiring before enabling audio. Compare a small
set of licensed/generated sounds at controlled levels. Record supply, load,
gain, digital level, cavity geometry, microphone distance, and motion behavior.

Use a shared time reference for motion/trigger and sound-onset measurement;
software timestamps alone do not establish acoustic latency. Report repeated
measurements and tails of the latency distribution, not only one best case.
Measure both quiet readiness and wake-from-sleep behavior.

Use differential/appropriately isolated measurement techniques for class-D
outputs. Neither speaker lead is ground; do not attach an earth-grounded
oscilloscope clip to a BTL output.

## Battery and child-use gates

A charger copied from a reference board is not a complete cell safety design.
The MCP73831's die thermal regulation does not measure pouch-cell temperature.
Set current and temperature handling from the selected cell manufacturer, not a
universal "1C" rule. Review input limits, charger dissipation, pack protection,
charging termination, and cutoff under actual system loads.

If playing while charging is deferred, specify and verify how the restriction
is enforced. That restriction does not eliminate cell-temperature, access, or
charging-safety requirements. Do not deliberately short, puncture, overcharge,
heat, or otherwise abuse live cells for informal project experiments.

Educational intent does not establish product safety. Plan adult/tool-controlled
cell access, captive parts, insulated edges, and assessment of parts released
by foreseeable use or drops. Determine applicable classification with a
qualified reviewer before child-use distribution.
US references include [CPSC toy guidance](https://www.cpsc.gov/Business--Manufacturing/Business-Education/Toy-Safety)
and [small-parts guidance](https://www.cpsc.gov/Business--Manufacturing/Business-Education/Business-Guidance/Small-Parts-for-Toys-and-Childrens-Products);
the applicable rules depend on the actual product, age group, and market.

## Evidence storage

At implementation, keep reviewed reports and small non-identifying measurement
datasets with the project; attach large raw files to versioned releases or an
identified durable store. Record file hashes and the analysis procedure.
Never publish personal participant data. Link each result and unresolved
anomaly from the owning epic; do not close a gate solely because a checklist
was generated.
