# Firmware architecture

[Firmware guide](../../firmware/README.md) · [Bring-up](bring-up.md) · [Audio assets](audio-assets.md) · [Gesture tuning](gesture-tuning.md)

**Implemented November 2026 in [`firmware/`](../../firmware/README.md);
not yet run on the custom board.** This page explains the structure and the
reasons for it. Behavior claims stay limited to what the tests show until
bench evidence exists.

## Goals

1. **Day one on RP2040 with CircuitPython.** The subsystems were chosen
   because Adafruit ships proven CircuitPython support for them. The firmware
   uses `audiobusio`, `audiomixer`, `audiomp3`, `audiocore`, `synthio`,
   `keypad` and `adafruit_lsm6ds` **unmodified** and builds on top.
2. **A thin seam for ESP32-S3.** CircuitPython exposes the same APIs on S3,
   so a new target is a pin table, a capability flag and optionally a radio
   `Link`. It is not a second implementation.
3. **Testable without hardware.** Instrument logic is plain Python. It runs
   under CPython in CI against synthetic and recorded IMU traces.
4. **Congruent with Go Go HarmoniYo's HGP** in vocabulary, data shapes and
   detector parameters, with no code or package dependency.
5. **Standalone scripts.** Build, test, package, deploy and publish are
   scripts that people and CI run identically.

## The board

Pin roles come from the ordered netlist (`hardware/handbell`), via
[`handbell_rp2040.py`](../../firmware/src/handbell/platforms/handbell_rp2040.py):

| RP2040 | Net | Firmware role |
|---|---|---|
| GPIO2 / GPIO3 | SDA / SCL | LSM6DSOX at **0x6A** (SDO to GND), ST Mode 1 |
| GPIO22 | INT (IMU INT1) | Reserved for data-ready/wake; INT2 reaches only TP6 |
| GPIO16 / 17 / 18 | I2S DIN / BCLK / LRCLK | `audiobusio.I2SOut`; LRCLK = BCLK+1 as RP2040 PIO requires |
| GPIO19 | BUTTON | J2 JST-SH pin 1 `BUTTON_EXT`, pin 2 GND. 10 kohm pull-up, 1 kohm series, 10 nF. **Active low** |
| GPIO20 | AMP_MUTE | **High = mute**. R20 pulls high when undriven |
| GPIO23 | POWER | Switched input + boost. R17 pulls low when undriven |
| GPIO13 | D13 | Status LED |
| GPIO26-29 | unconnected | **No battery-voltage sense is available to firmware** |

Flash is a 2 MB W25Q16JVUXIQ, the family the stock Raspberry Pi Pico build
targets (`EXTERNAL_FLASH_DEVICES = "W25Q16JVxQ"`). The Pico build's
`board_init` drives no pins. Pins use `microcontroller.pin.GPIOxx`, so the
code does not depend on which board build is installed. A custom board
definition (our pin names, USB identity, `board_id`) is a later step that
needs only one line in `platforms/__init__.py`.

## Layers

```mermaid
flowchart TB
  main["code.py → handbell.main (config, profile, fail-safe)"] --> runtime["handbell.runtime (loop)"]
  runtime --> core
  subgraph core["handbell.core: pure Python, imports only math"]
    gestures["gestures: RingDetector, ImpactDetector, learn_axis"]
    controls["controls: ButtonGrammar"]
    bells["bells + pitch: Bell, BellSet"]
    instrument["instrument: state machine + action table"]
    events["events: HGP-shaped JSON"]
    config["config: defaults + validation"]
  end
  core -. "ports (handbell.ports)" .-> hw
  subgraph hw["handbell.hw: CircuitPython adapters"]
    audio["audio: I2S, mixer, MP3/WAV/synth, power + mute sequencing"]
    imu["imu: LSM6DSOX + CTRL9_XL fix + burst read"]
    io["io: keypad button, LED, NVM store, console link, clock"]
  end
  subgraph platforms["handbell.platforms"]
    p1["handbell_rp2040"]
    p2["feather_propmaker_rp2040 (bench)"]
    p3["esp32s3_handbell (seam, not defined)"]
    p4["desktop (CPython sim, host only)"]
  end
  platforms --> hw
```

- **core** never imports hardware modules, `time` or `gc`. It receives
  integer-microsecond timestamps, IMU samples and button edges, and calls
  the ports. [`tests/test_core_imports.py`](../../firmware/tests/test_core_imports.py)
  enforces this, along with CircuitPython-compatible syntax and modules.
- **Times are integer microseconds.** CircuitPython floats keep about 22
  significant bits, so a millisecond float clock would lose precision within
  about an hour. Detector arithmetic uses small relative values.
- **ports** ([`ports.py`](../../firmware/src/handbell/ports.py)) are
  documented duck-typed interfaces: Clock, MotionSource, ButtonSource, Audio,
  Indicator, Store and Link.
- **hw** adapters assert safe pin states first: audio construction drives
  AMP_MUTE high and POWER low before anything else can fail. Startup or
  runtime errors call `shutdown()` (mute, stop clocks, power off), print the
  error and blink the LED fast.

### Main loop

[`runtime.run`](../../firmware/src/handbell/runtime.py) is one cooperative
loop. It does five things:

1. Reads the IMU as one 16-byte burst from STATUS_REG, skipping samples the
   sensor has not refreshed.
2. Feeds the ring detector and instrument.
3. Polls `keypad` button events.
4. Ticks the audio sequencer and fades.
5. Calls `gc.collect()` only when no stroke, press or sound is in progress.

Audio plays from DMA in the background. Status messages report sample rate,
loop rate, maximum loop gap and free memory, so timing is measured on the
board rather than assumed.

### Audio power sequencing

From the [0.2 electrical contract](../electrical-reduction-and-placement.md#mono-audio-and-quiet-idle-intent):

| Step | Wake | Sleep |
|---|---|---|
| 1 | POWER high | Stop voices; AMP_MUTE high |
| 2 | Wait `settle_ms` (50) | Wait `mute_ms` (5) |
| 3 | Start I2S with mixer silence | Stop and deinit I2S (BCLK and LRCLK stop together) |
| 4 | Wait `clock_ms` (5); AMP_MUTE low | POWER low |
| 5 | Start the queued note | - |

I2S is deinitialized while the amplifier is unpowered so the RP2040 never
drives clocks into an unpowered MAX98357A. Motion pre-wakes this sequence
when a stroke arms, typically 100 ms or more before the strike, so a strike
does not wait for power-up. Without pre-wake, a cold strike waits about
55 ms. The tests check the ordering against stand-in modules; the actual
settle time, clicks and supply behavior are bench measurements.

### IMU initialization (issue #13)

The pinned `adafruit_lsm6ds` 4.6.3 (current upstream, commit `cdfc14a6`)
still redeclares `_i3c_disable` on CTRL9_XL bit 0. The library stays
unmodified. [`lsm6dsox_fix.py`](../../firmware/src/handbell/hw/lsm6dsox_fix.py)
does a read-modify-write after construction: it sets bit 1, clears reserved
bit 0, preserves bits 7..2 and verifies the readback. The startup banner
prints before/after values, and `bringup.i2c_imu` checks them.

## ESP32-S3 seam

[`esp32s3_handbell.py`](../../firmware/src/handbell/platforms/esp32s3_handbell.py)
is a deliberate placeholder that raises a clear error. Adding a real S3
board needs:

1. A pin table. Any free GPIOs can carry I2S on S3; the BCLK/LRCLK
   adjacency rule is RP2040-specific.
2. `CAPS["radio"]` and a `Link` adapter carrying the same HGP lines over BLE
   (`_bleio`) or Wi-Fi (`socketpool`).
3. Optionally a `Store` that accepts a paired host's `assign`, with a
   `boot.py` remount policy for writing `bells.json`.

`handbell.core` is reused unchanged. The local strike-to-sound path must
never wait on the radio. Pairing must use explicit enrollment
(maintenance mode is reserved for it) and must not silently remap a bell
during play. Radio feasibility inside the metal bell remains an E12 question.

## HGP alignment

[HGP v0](https://github.com/dcuccia/go-go-harmoniyo/blob/main/docs/protocol/hgp-v0.md)
already anticipates "digital-handbell ESP32-S3 bells". The projects share
vocabulary, shapes and traces; code is copied with attribution, not imported.

| Concept | HGP | Here |
|---|---|---|
| Bell identity | `id` scientific pitch (`"C5"`, sharps), `midi` | `Bell(id, sound, gain)`; flats normalized to sharps |
| Assigned bells | `assign.bells`, `select` | `bells.json` with the same shape. `select: "cycle"` is a new value (HGP has `zones` for phones) |
| Gesture | `g`: `ring`, `damp`, and reserved `lv`, `shake`, `martellato` | Same strings. `ring` from motion or key; `damp` from button (and experimental motion) |
| Event | `seq, g, t, bell, sel, vel (0..1), det, src` | Same fields. `t` is back-dated to the strike; `vel` = peak deg/s ÷ 1000 |
| Device | `hello` with `kind`, `sensors`, `gestures`, `sound` | Same, with `kind: "bell"` |
| Detector tuning | `armOmega`, `minPeakOmega`, `minDecel`, `refractoryMs`; `sens` `normal`/`quick` | Same names in snake_case, same units and defaults |
| Raw traces | `raw.cols ["t","ax","ay","az","gx","gy","gz"]` | Same; acceleration includes gravity |
| Transport | WebSocket now, "BLE GATT, UDP, serial" future | USB serial, one JSON line per message |

`RingDetector`, `learn_axis`, `adapt_params`, `expected_ioi` and
`ImpactDetector` are ported from the S1 spike at commit `51ae4af5` (MIT).
There are two deliberate differences, both documented in
[`gestures.py`](../../firmware/src/handbell/core/gestures.py):

- Integer-microsecond time with incremental deceleration tracking, which
  avoids allocation.
- An impact threshold of `mean + max(min_jump, k·dev)`, because IMU
  acceleration includes gravity.

Proposals to upstream into HGP: `select: "cycle"`, `kind: "bell"` device
conventions, and noting gravity-inclusive raw rows.

## Deliberately out of scope

Wireless pairing, remote bell assignment, OTA updates, telemetry, an S3
board, battery-level reporting (no sense line), deep sleep and IMU-interrupt
wake are out of scope. The seams leave room for each one.
