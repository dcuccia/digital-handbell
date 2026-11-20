# Firmware bring-up (first articles)

[Firmware guide](../../firmware/README.md) · [Architecture](architecture.md) · [Validation plan](../validation-plan.md)

This guide covers the software side of bringing up one prototype board.
It **does not replace the electrical bring-up gates** owned by
[#9 (E09)](https://github.com/dcuccia/digital-handbell/issues/9) and
[review package R6](../pcb-review-2026-11.md). Inspect the board against the
[incoming checks](../../hardware/handbell/quote-prep/2026-11-09-six-layer/unresolved-before-ordering.md).
Confirm protection, rails and current draw with a current-limited supply
before relying on these scripts. Start with one board and no cell fitted
unless the power plan says otherwise.

Record every step in a dated note: board serial or marking, CircuitPython
version (`bringup.info` prints it), the firmware package version and hash,
supply voltage and current limit, results, and anything unexpected.
"Worked" is less useful than the numbers each step prints.

## 0. Prepare a computer (once)

```
python firmware/scripts/ci.py            # tests, build, package
```

The zip in `firmware/dist/` contains the CircuitPython UF2 and the
`CIRCUITPY/` tree. Have a serial terminal ready (Mu, `tio`, PuTTY or the
VS Code CircuitPython extension).

## 1. ROM boot and CircuitPython

1. Connect USB. A board with blank flash should enumerate as the
   **`RPI-RP2`** drive (RP2040 ROM bootloader). If it doesn't, stop and
   check USB, the 3V3 rail, the crystal and the QSPI flash (R1/R2 items).
2. Copy `uf2/adafruit-circuitpython-raspberry_pi_pico-en_US-10.3.2.uf2` onto
   `RPI-RP2`. The board should reboot as **`CIRCUITPY`**. This is the first
   test of the W25Q16JV flash and its boot configuration.
3. Open the serial console. Press Enter for the REPL banner.

The status LED on GPIO13 will not light: the Pico build's status LED is
GPIO25, which is unconnected on this board. That is expected.

## 2. Copy the firmware

```
python firmware/scripts/deploy.py        # finds CIRCUITPY, writes changed files
```

`code.py` starts the instrument at once. Press **Ctrl-C** at the console
to reach the REPL for the bring-up scripts. The instrument mutes and powers
down audio first. Pressing Ctrl-D later restarts it.

## 3. Bring-up scripts, in order

Run each at the REPL with `import bringup.<name>`. To run one again, press
Ctrl-D, then Ctrl-C, then import it again. Every script holds AMP_MUTE high
and POWER low, except where it deliberately changes them, and restores that
state on exit.

| Step | Command | Pass looks like | Record |
|---|---|---|---|
| a | `import bringup.info` | CircuitPython 10.3.2, `raspberry_pi_pico`, about 1 MiB total `CIRCUITPY` | Free space after deploy; compare with `build.json` |
| b | `import bringup.blink` | LED blinks 10 times. It faces inward and may need a light path | Visible or not |
| c | `import bringup.i2c_imu` | Scan shows `0x6a`; WHO_AM_I `0x6C`; CTRL9_XL bit 1 = 1, bit 0 = 0 on re-read; at rest \|a\| ≈ 9.8 m/s², gyro ≈ 0 | Printed values. This closes the hardware part of [#13](https://github.com/dcuccia/digital-handbell/issues/13) |
| d | `import bringup.button` (needs a switch on J2) | One `pressed`/`released` per press (no chatter); click, double, long and very_long recognized | Any chatter; switch type |
| e | `import bringup.audio_tone` | Steps 1-6 print. Quiet 440 Hz tone at level 0.05 | Supply current at each step, clicks at 2/4/6, hiss at 4. **Use a current-limited supply** |
| f | `import bringup.audio_files` | Synth, WAV and MP3 bells play; overlapping MP3s play without glitches | `play()` times, timbre, glitches |
| g | `import bringup.loop_rate` | New samples/s close to 416 for burst reads | Loops/s, samples/s, max loop gap, `gc.collect()` time |
| h | `import bringup.battery` | On this board: reports that there is no sense line | Nothing; it exists for the next revision ([#17](https://github.com/dcuccia/digital-handbell/issues/17)) |

Anything that points to a board change (wrong footprint, missing access,
marginal rail) should become a
[board revision request](../hardware-revision-requests.md) as well as a
bring-up record.

`audio_tone` and `audio_files` are the first time the boost, amplifier and
speaker run together. Start at the default low levels. Raise
`audio.level.max` only once you have heard the result and checked
temperatures and current. The 9 dB gain jumper stays open.

## 4. The instrument

Press Ctrl-D to run `code.py`. Watch the console:

- `hello` with `"kind": "bell"`, and the CTRL9_XL line
- `status` every 5 s: `rateHz` (IMU samples/s), `loopHz`, `maxGapMs`,
  `memFree`, `audio` state
- `gesture` lines when you ring, and `select` lines when you click

Try, and note what happens:

1. Ring the bell slowly, then quickly. Does each stroke sound once? Does
   anything ring while you only lift or carry it?
2. Click to step through bells. The LED should count the bell position,
   with a soft preview of each note.
3. Ring, then press the button while the note sounds: it should damp.
4. Hold the button 1 s to lock, then click: the LED shows "locked" and the
   bell stays the same.
5. Hold the button 5 s to enter maintenance mode: rings report but stay
   silent. Click to exit.
6. Leave the bell still for 20 s. `status` should show `audio: off`. The
   next ring should sound promptly, because motion pre-wakes the amplifier.

## 5. Measurements to make once it sounds

These turn "it works" into evidence (see the
[plan](plan-and-experiments.md#experiments-before-choosing-behavior)):

- **Strike-to-sound latency.** Record ringing with a phone microphone
  close to the bell. The mechanical clapper sound (if any) or a tap on the
  shell marks the strike; the speaker onset marks the sound. Compare MP3,
  WAV (`sounds/test/A5.wav`) and `synth` bells by editing `bells.json`.
  The MP3 encoding alone adds about 50 ms at 22.05 kHz
  ([audio assets](audio-assets.md#mp3-start-delay)).
- **False and missed rings.** Run `import bringup.record_trace` and on the
  computer
  `python firmware/scripts/capture_trace.py --label "full rings, slow"`.
  Then replay offline with `replay.py` ([gesture tuning](gesture-tuning.md)).
- **Quiet idle.** Hiss and clicks with the amplifier awake but silent,
  then current asleep versus awake.
- **Levels.** Find a speaker-safe `audio.level.max` from listening and
  temperature, not from datasheet headline power.

## Recovery

- **Back to `RPI-RP2`:** at the REPL,
  `import microcontroller; microcontroller.on_next_reset(microcontroller.RunMode.UF2); microcontroller.reset()`.
  Or hold TP3 (USBBOOT) to GND while connecting USB.
- **Filesystem corrupted:** `import storage; storage.erase_filesystem()`
  at the REPL, then deploy again.
- **Error blink (fast LED):** read the console; the error is printed and
  repeated every 10 s. Audio is already muted and off.

## Reporting

Open or update an issue under [#9](https://github.com/dcuccia/digital-handbell/issues/9)
with the record above, the firmware package version and hash, and any
trace files (non-identifying motion only). Firmware bugs go under
[#6](https://github.com/dcuccia/digital-handbell/issues/6).
