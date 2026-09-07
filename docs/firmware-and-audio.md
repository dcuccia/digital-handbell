# CircuitPython, gesture, and audio plan

## Starting stack

Use the purchased RP2040 Prop-Maker Feather to prove the signal chain before
custom-board bring-up. The documented starting APIs are
`audiobusio.I2SOut`, `audiocore.WaveFile`, `audiomixer.Mixer`, and
`adafruit_lis3dh` with `adafruit_bus_device`. `synthio` is a separate synthesis
experiment, not a commitment to replace recorded samples.

Sources and pinned revisions are in the [catalog](reference-designs.md).
Record the exact CircuitPython build, library bundle, application revision,
asset hashes, wiring, and board revision for every measurement.

## Experiments before choosing behavior

| Question | Experiment and recorded result |
|---|---|
| Recorded or synthesized bell? | Compare original/explicitly licensed recordings against synthesized partials/envelopes at the same playback level |
| Note range and timbre? | Evaluate the desired lowest/highest notes in candidate drivers/cavities; small-driver fundamental loss may still leave recognizable partials |
| Fixed note per bell or selectable? | Compare simple USB configuration against buttons; establish reset/default behavior and classroom setup effort |
| Natural trigger? | Record timestamped acceleration from ringing, pickup, set-down, walking, deliberate shaking, and sound playback |
| Accelerometer enough? | Quantify missed strikes and false triggers before paying the cost/power/layout penalty of a six-axis sensor |
| Damping/retrigger/polyphony? | Define what happens on rapid repeated strokes and simulated hand damping; compare restart, overlap, and release envelopes |
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
