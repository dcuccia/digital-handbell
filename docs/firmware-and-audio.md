# CircuitPython, gesture, and audio plan

## Starting stack

Use an owner-approved RP2040 Prop-Maker Feather bench setup to prove the signal chain before
custom-board bring-up. The documented starting APIs are
`audiobusio.I2SOut`, `audiocore.WaveFile`, `audiomixer.Mixer`, and
`adafruit_lis3dh` with `adafruit_bus_device`. `synthio` is a separate synthesis
experiment, not a commitment to replace recorded samples.

Sources and pinned revisions are in the [catalog](reference-designs.md).
Record the exact CircuitPython build, library bundle, application revision,
asset hashes, wiring, and board revision for every measurement.

For the explicit chest-stop/rest requirement, add the
[LSM6DSOX comparison experiment](motion-sensing.md) to the stock LIS3DH setup.
The LSM6DS driver returns gyro values in **radians/second**. Use the actual
`adafruit_lsm6ds.lsm6dsox.LSM6DSOX` class and Feather bus, not an outdated guide
constructor or another board's IMU power aliases.
The separate schematic now uses LSM6DSOX. Before bring-up, address the
[pinned driver's CTRL9_XL descriptor defect](motion-sensing.md): I3C-disable
bit 1 must be set and reserved bit 0 clear, without disturbing other fields.
No hardware purchase or working firmware is implied by this plan.

## Experiments before choosing behavior

| Question | Experiment and recorded result |
|---|---|
| Recorded or synthesized bell? | Compare original/explicitly licensed recordings against synthesized partials/envelopes at the same playback level |
| Note range and timbre? | Evaluate the desired lowest/highest notes in candidate drivers/cavities; small-driver fundamental loss may still leave recognizable partials |
| Fixed note per bell or selectable? | Compare simple USB configuration against buttons; establish reset/default behavior and classroom setup effort |
| Natural trigger? | Record timestamped acceleration from ringing, pickup, set-down, walking, deliberate shaking, and sound playback |
| Accelerometer enough? | Quantify missed strikes and false triggers before paying the cost/power/layout penalty of a six-axis sensor |
| Damping/retrigger/polyphony? | Define what happens on rapid repeated strokes and simulated hand damping; compare restart, overlap, and release envelopes |
| Chest-stop versus ordinary handling? | Compare recent-stroke context, return trajectory, gyro/pose features, and settling; a tap alone does not prove chest contact |
| Quiet ready state or power-gated idle? | Measure hiss, click transients, current, and first-strike latency in both modes |

No musical or usability threshold is approved yet. Set targets with the project
owner in E01 and record actual measurements rather than calling performance
"acceptable" without a criterion.

## Motion pipeline

Keep time-critical acquisition and trigger decisions separate from file
operations, USB writes, console printing, and expensive processing. Start with
timestamped samples or interrupt-assisted acquisition, then tune gravity
handling, orientation, filtering, hysteresis, retrigger suppression, and
velocity-to-level mapping against recorded examples.

The LIS3DH driver's convenience `shake()` implementation samples over a default
0.1-second window with sleeps. It is useful demonstration code, not an assumed
low-latency musical trigger. Raw/interrupt-driven processing and a nonblocking
state machine need evaluation. Audio vibration coupling into the accelerometer
is a specific false-trigger scenario.

Retain a replayable dataset and algorithm parameters with each result. Do not
store identifiable recordings of children or publish participant information.
Synthetic/mechanical motion fixtures and non-identifying sensor traces are
preferable for a public repository.

## Audio, storage, and silence

Benchmark mono PCM first. For scale, uncompressed 44.1 kHz, 16-bit mono audio
requires `44,100 * 2 = 88,200 bytes/second`; a five-second note uses 441,000 bytes
before file overhead. An 8 MB flash device is shared with firmware/filesystem
overhead. Count actual free space, asset count, RAM buffers, mixer voices, and
CPU load before promising a complete note set.

**2026-09-10 capacity clarification:** 8 MB was inherited from the Prop-Maker
reference, not established as a handbell requirement. The owner's lower-end
RP2040 use case is one or a few approximately five-second chimes. Two such
44.1 kHz/16-bit mono recordings need 882,000 bytes before headers. Keeping
external flash is necessary for standalone firmware/storage on this RP2040
design; embedding audio in the firmware does not eliminate that chip.
The [flash sourcing comparison](flash-sourcing.md) separates stocked
footprint-change alternatives from near-4x4 options without verified stock.

The inspected CircuitPython revision
[`fd40abc29cf5c8ea111e16b3e6cc21b180974ae3`](https://github.com/adafruit/circuitpython/tree/fd40abc29cf5c8ea111e16b3e6cc21b180974ae3)
normally reserves 1020 KiB for firmware plus 4 KiB for settings, leaving
1 MiB of partition space on a 2 MiB device or 3 MiB on a 4 MiB device,
before filesystem overhead, Python code and libraries. A 2 MiB build is
plausible but relatively tight for two full-rate WAVs; 4 MiB leaves more
room without requiring MP3 or abandoning CircuitPython.

Importantly, RP2040
[`internal_flash.c`](https://github.com/adafruit/circuitpython/blob/fd40abc29cf5c8ea111e16b3e6cc21b180974ae3/ports/raspberrypi/supervisor/internal_flash.c)
reads the JEDEC capacity byte at runtime. A density change does not, by
itself, prove that an existing UF2 will address beyond the device. Conversely,
capacity detection does not establish boot compatibility: the
[`gen_stage2.py`](https://github.com/adafruit/circuitpython/blob/fd40abc29cf5c8ea111e16b3e6cc21b180974ae3/ports/raspberrypi/gen_stage2.py)
configuration also determines quad-enable writes and read mode. Select the
exact flash family/suffix in the handbell board definition and exercise
cold boot, BOOTSEL recovery, filesystem sizing/read/write and audio streaming
before approving a smaller flash. The stock Feather configuration is not
automatically a qualified handbell build.

Choose sample rate, voice count, and mixer buffer size experimentally. Larger
buffers may reduce underruns while increasing trigger-to-sound delay. The
historical [CircuitPython issue 7322](https://github.com/adafruit/circuitpython/issues/7322)
is a useful stress scenario; rerun against the actual selected build.

The [MAX98357 datasheet](https://cdn-shop.adafruit.com/product-files/3006/MAX98357A-MAX98357B.pdf)
recommends ramping digital audio down before shutdown. Evaluate an envelope,
draining the tail/buffers, and orderly amp disable/startup. Verify reset,
firmware reload, USB insertion/removal, low battery, and unexpected software
failure as well as normal idle. Power gating may save current but introduce
startup delay, pops, or back-power issues; it is not automatically "silent."

A 1S-powered amp does not guarantee the advertised 5 V output. For example,
the [breakout guide](https://learn.adafruit.com/adafruit-max98357-i2s-class-d-mono-amp/pinouts)
lists about 1 W into 4 ohm at 3.3 V and 1% THD. Select level limits using the
actual speaker and rail range; distinguish unclipped output from maximum
headline power.

### Approved compact-revision behavior

This scope is now wired in [0.2](electrical-reduction-and-placement.md):
GPIO20 **HIGH=mute / LOW=play**, GPIO23 enables switched input and boost,
SD_MODE selects left audio when unmuted, and the gain jumper remains open/9 dB.
There is no delivered firmware yet. Preserve the stock GPIO19 `EXTERNAL_BUTTON`
distinction and remove the old servo/NeoPixel roles in the custom board definition.

The owner now requests a 4 ohm mono speaker and electronics capable of the
3 W high end with a boosted rail. The MAX98357A's typical 5 V / 4 ohm figures
are 2.5 W at 1% THD+N and 3.2 W at 10% THD+N under its specified test conditions.
The candidate 40 mm Gikfun speaker has conflicting seller power ratings.
Neither the electronics target nor a software volume limit qualifies that
speaker. See the [power/fit review](compact-power-and-packaging.md).

Use an explicitly selected I2S channel, or verified identical samples in both
slots. Mono does not eliminate BCLK/LRCLK or their valid timing. Keep 9 dB gain
as the starting evaluation setting rather than automatically choosing maximum
gain; determine digital headroom and a speaker-specific limit from evidence.
For shutdown, fade/drain the audio, assert mute, then sequence clocks and
power. Do not remove LRCLK while BCLK continues; the datasheet warns of
unexpected/DC output in that condition. Verify reset and fault defaults too.

The approved external button uses GPIO19, the schematic `BUTTON` net and stock
`EXTERNAL_BUTTON` alias, not stock `board.BUTTON` (GPIO7). Give physical
chest-stop and explicit enrollment gestures separate, debounced state-machine
semantics. Keep the ordinary GPIO13 status LED; removing NeoPixel hardware
also requires updating the board's status configuration.

## Early ESP32-S3 wireless experiment

Wireless remains optional to sounding a bell, but its enclosure feasibility
should be explored **before freezing a shared carrier**, not after layout.
Prioritize sound-file/configuration programming over streaming live audio.
Optional practice telemetry should be timestamped/asynchronous, with dropped
or disconnected transport unable to delay a local strike or damping action.
Do not collect or publish identifying student data by default.

Use stable device identity plus a QR label, separately assignable musical note,
and explicit local enrollment (for example a long button press plus LED/chirp).
A unique ID is not an authentication secret. Reserve a USB recovery route.
Pairing gestures must not silently remap an instrument during ordinary playing.

S3-MINI-1 `-N8` has 8 MB flash without PSRAM; `-N4R2` trades down to 4 MB flash
for 2 MB PSRAM. Select the exact module/build from actual sound-storage and
working-memory budgets, not body size alone. CircuitPython support exists for
both S3 and C3, but C3 lacks a CIRCUITPY USB mass-storage workflow. Check the
chosen build's BLE and I2S APIs instead of inferring them from the chip radio.

CircuitPython's [web workflow](https://docs.circuitpython.org/en/latest/docs/workflows.html#web)
supports file/code/config maintenance; it is not a complete secure interpreter
OTA system. Its documented HTTP Basic authentication is unencrypted. Use a
controlled development network and define authenticated updates, interrupted
write recovery and access policy before educational deployment. A future
training server is a separate deliverable, not implemented firmware here.

## Power and educational workflow

Define ready-to-play, sounding, idle, sleep/off, USB maintenance, and charging
states, including transitions and visible indications. Treat acoustic silence
and low electrical power as separate requirements. Whole-instrument current
must be measured; amplifier-only datasheet figures are insufficient.

Document data-capable USB cables, CircuitPython install, safe ejection, asset
updates, note configuration, reset/BOOT recovery, and replacement-part polarity.
RP2040 ROM recovery is a useful baseline. A distributed custom board needs its
own board definition and authorized USB identity, not merely an Adafruit UF2
renamed as our product.

Every distributed sound must have a documented source, author, license, and
allowed modifications. Code-example licensing does not automatically cover
bundled recordings. Prefer original/generated or explicitly licensed assets.
