# Firmware

CircuitPython firmware for the digital handbell: ring the bell to play the
selected note, press the J2 button to change notes or damp, and read
HGP-shaped messages on the USB serial console.

**Status (November 2026): written and tested on a computer, not yet run on
the custom board.** The prototype PCBAs arrive the week of November 23.
Everything here has passed CPython tests, including stand-ins for
CircuitPython modules, and the CircuitPython 10.3.2 compiler.
Musical behavior, latency, levels and power behavior still need bench
evidence. Follow the [bring-up guide](../docs/firmware/bring-up.md) and the
E09 electrical gates before powering a board.

| Read | For |
|---|---|
| [Getting started](../docs/firmware/getting-started.md) | Install a release zip on a board without Python |
| [Bring-up guide](../docs/firmware/bring-up.md) | First power-up, step by step, and what to record |
| [Architecture](../docs/firmware/architecture.md) | Layers, ports, ESP32-S3 seam, HGP alignment |
| [Audio assets](../docs/firmware/audio-assets.md) | MP3/WAV/synth budgets on 2 MB, the measured MP3 start delay, adding sounds |
| [Gesture tuning](../docs/firmware/gesture-tuning.md) | Detector parameters, recording and replaying traces |

## Quick start

You need Python 3.11+ on Windows, macOS or Linux.

```
python firmware/scripts/ci.py        # setup + tests + build + package (what CI runs)
python firmware/scripts/deploy.py    # copy firmware/build/CIRCUITPY to the board
```

Each step is also a standalone script. All are idempotent, exit non-zero on
failure and write JSON reports to `firmware/build/reports/`:

| Script | Does |
|---|---|
| `setup_dev.py` | Installs pytest, lameenc and pyserial if missing |
| `test.py` | pytest, then compiles all device code with the pinned CircuitPython `mpy-cross` |
| `build.py` | Validates `bells.json` and compiles `handbell/` to `.mpy`. Extracts the pinned Adafruit libraries and generates sounds. Checks the flash budget (exit 2 if over) |
| `package.py` | Reproducible zip in `firmware/dist/`: CIRCUITPY tree, pinned Pico UF2, manifest, install notes |
| `deploy.py` | Writes changed files to a mounted CIRCUITPY drive. Keeps your `bells.json` and other files |
| `publish.py` | Creates a GitHub release from a `firmware-v<version>` tag (CI does this) |
| `capture_trace.py` | Records the board's serial output to `traces/local/*.jsonl` |
| `replay.py` | Runs recorded traces through the same detector and instrument code on a computer |
| `make_sounds.py` | Generates the original synthesized bell sounds (called by `build.py`) |
| `ci.py` | `setup_dev` → `test` → `build` → `package` |

Every download (`mpy-cross`, Adafruit bundle, UF2) is pinned with a SHA-256
in [`toolchain.json`](toolchain.json) and cached in `firmware/.cache/`.
CI ([`firmware.yml`](../.github/workflows/firmware.yml)) runs `ci.py` on
Windows and Ubuntu. [`firmware-release.yml`](../.github/workflows/firmware-release.yml)
publishes on a `firmware-v*` tag. Neither workflow contains build logic.

## Installing on a board

1. **CircuitPython.** A board with blank flash shows up as the `RPI-RP2` drive.
   Copy the Raspberry Pi Pico UF2 for CircuitPython 10.3.2 onto it. It is
   in the package zip, or download it from the URL in `toolchain.json`. The
   handbell uses the Pico's W25Q16JV flash family, so the Pico build is the
   day-one target until a custom board definition exists. The board has no
   BOOT button. To get back to `RPI-RP2` later, run
   `import microcontroller; microcontroller.on_next_reset(microcontroller.RunMode.UF2); microcontroller.reset()`
   in the REPL, or hold TP3 (USBBOOT) to GND while connecting USB.
2. **Firmware.** Run `python firmware/scripts/deploy.py`, or copy the
   package's `CIRCUITPY/` contents. Eject the drive before unplugging.
3. **Serial console.** Use any terminal (Mu, `tio`, PuTTY, the VS Code
   CircuitPython extension). Ctrl-C stops the instrument; it mutes and
   powers down audio before reaching the REPL. Ctrl-D restarts it.

### Bench option before the custom board

A **Feather RP2040 Prop-Maker (5768)** with an **LSM6DSOX breakout (4438)**
on STEMMA QT shares the handbell's I2S, power, button and I2C pins. Put the
Feather Prop-Maker UF2 on it and the same firmware selects the
`feather_propmaker_rp2040` profile automatically. That board has no mute
line, so EXTERNAL_POWER alone gates the amplifier.

## Using the instrument

**Ring** the bell to play the selected note. Ringing harder plays louder,
within the conservative `audio.level` limits. Motion at the start of a
stroke powers up the amplifier ahead of the strike. After `keep_awake_s`
of quiet, the firmware mutes it and turns it off.

**J2 button.** The connector is side-entry JST-SH: pin 1 to a normally-open
switch, pin 2 to GND. The defaults below can be changed in `bells.json`:

| When | Click | Double-click | Hold ~1 s | Hold 5 s |
|---|---|---|---|---|
| Silent (play mode) | Next bell, with a soft preview | Previous bell | Lock/unlock selection | Maintenance mode |
| Sounding | Damp on press (immediate) | - | - | Maintenance mode |
| Maintenance (LED blinks 1 Hz) | Exit | Toggle accessible mode | - | Exit |
| Accessible mode | Press rings the selected bell | - | - | Maintenance mode |

In maintenance mode, rings are detected and reported but make no sound,
which is useful for tuning. The selected bell, lock and mode are saved in
non-volatile memory (`microcontroller.nvm`) and survive power cycles.

**Status LED (GPIO13).** Brief blink every 3 s when idle. A flash on each
ring. After a selection change it blinks once per bell position (1 = first
bell). Rapid double blinks mean locked. A fast continuous blink means an
error; the serial console shows the message. On boards with battery sensing
(not the November 2026 board), the idle blink becomes a double blink when
low and a triple blink when critical.

**Serial messages.** One JSON object per line, shaped like Go Go
HarmoniYo's HGP v0: `hello` at start, `gesture` (`ring`/`damp`) with
back-dated `t`, `vel` and detection delay `det`, `select` on note changes and
`status` every 5 s with sample rate, loop timing and free memory. Set
`"debug": {"raw": true}` to also stream IMU rows for trace capture.

## Configuration: `bells.json`

[`src/bells.json`](src/bells.json) is copied to the board root. Missing keys
take the defaults in [`handbell/core/config.py`](src/handbell/core/config.py).
Unknown keys or values fail at startup with a clear message, so a typo
cannot pass silently. The main keys:

| Key | Meaning |
|---|---|
| `bells` | Resident notes, in button order: `{"id": "C5", "sound": "sounds/C5.mp3", "gain": 1.0}`. Set `sound` to `"synth"` for a modelled bell that uses no storage |
| `select` | `"cycle"` (button changes the bell) or `"fixed"` |
| `mode` | `"play"` or `"accessible"` (button rings) |
| `ring.sens` | `"normal"` or `"quick"` (HGP sensitivity) |
| `detector` | Ring detector overrides, such as `{"min_decel": 5000, "axis": [1, 0, 0]}` ([tuning](../docs/firmware/gesture-tuning.md)) |
| `controls` | Per-mode, per-state map of `click`/`double`/`long`/`very_long`/`down` to actions |
| `audio` | `sample_rate` (all sounds must match), `voices`, `retrigger`, `damp_ms`, `level` {min,max,curve}, `preview_level` |
| `power` | `keep_awake_s`, `settle_ms` (boost/amplifier settle before clocks), `wake_on_motion` |
| `imu` | `rate_hz` (416), `gyro_dps` (2000), `accel_g` (16), `fast_read` |
| `battery` | `low_v`, `critical_v`, `hysteresis_v`, `samples`, `sample_s`, `critical_action` (`"silence"`/`"warn"`). Used only on boards with a sense line ([#17](https://github.com/dcuccia/digital-handbell/issues/17)); thresholds are provisional |
| `debug` | `events`, `status_s`, `raw` |

`CIRCUITPY` is read-only to the firmware while it is USB-mounted. Edit
`bells.json` from the computer; the board reloads when the file is saved.

## Layout

```
firmware/
  src/                 -> becomes CIRCUITPY
    code.py            entry point (handbell.main)
    bells.json         instrument configuration
    handbell/core/     pure Python: gestures, controls, bells, config, HGP events, instrument
    handbell/hw/       CircuitPython adapters over unmodified Adafruit libraries
    handbell/platforms/  board profiles (handbell_rp2040, feather_propmaker_rp2040, esp32s3 seam, desktop sim)
    bringup/           standalone first-article scripts
  scripts/             standalone build/test/package/deploy/publish/trace tools
  tests/               pytest (core, adapters with CircuitPython stand-ins, scripts)
  traces/              curated, non-identifying IMU traces; traces/local/ is ignored
  toolchain.json       pinned CircuitPython, mpy-cross, bundle and budget
```

Generated output (`build/`, `dist/`, `.cache/`) is ignored by git.
