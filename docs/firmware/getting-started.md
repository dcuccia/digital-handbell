# Getting started: put the firmware on a board

[Firmware docs](README.md) · [Bring-up](bring-up.md) · [Firmware guide (developers)](../../firmware/README.md)

This page is for anyone with a handbell board (or the
[Prop-Maker bench setup](../../firmware/README.md#bench-option-before-the-custom-board))
who wants to install the firmware **without Python or a build**. Developers
who want to change the code should start from the
[firmware guide](../../firmware/README.md).

> A brand-new prototype board must pass the electrical bring-up checks
> first ([#9](https://github.com/dcuccia/digital-handbell/issues/9), with a
> current-limited supply). This firmware is a prototype for testing, not a
> released kit.

## 1. Get the firmware zip

The zip contains everything: the CircuitPython UF2, the `CIRCUITPY/` files
and install notes. To get it:

- **Releases:** download `digital-handbell-firmware-<version>.zip` from the
  repository's [Releases](https://github.com/dcuccia/digital-handbell/releases).
  A release is published when a `firmware-v<version>` tag is pushed.
- **Latest build:** open the [firmware workflow runs](https://github.com/dcuccia/digital-handbell/actions/workflows/firmware.yml),
  choose the newest successful run and download the `firmware-package`
  artifact (it contains the zip). A GitHub login is required.

Check the download against the `.sha256` file beside it if you want to be
sure it is intact. Unzip it.

## 2. Install CircuitPython (once per board)

1. Connect the board with a **data-capable** USB-C cable.
2. A board with blank flash appears as a drive named **`RPI-RP2`**.
3. Copy `uf2/adafruit-circuitpython-raspberry_pi_pico-en_US-10.3.2.uf2`
   onto `RPI-RP2`. The board restarts and appears as **`CIRCUITPY`**.

On the bench Prop-Maker Feather, use the Feather Prop-Maker UF2 from
[circuitpython.org](https://circuitpython.org/board/adafruit_feather_rp2040_prop_maker/)
instead (version 10.3.2). Hold BOOT while pressing RESET to get `RPI-RP2`.

## 3. Copy the firmware

1. Open the unzipped `CIRCUITPY/` folder and copy **everything inside it**
   onto the `CIRCUITPY` drive, replacing files when asked.
   - **Updating** a board where you edited `bells.json`? Keep your copy;
     don't overwrite it.
2. **Eject** the drive before unplugging (Windows: "Eject"; macOS: drag to
   the Bin). Unplugging without ejecting can corrupt the files.

The board restarts and runs the instrument by itself.

## 4. Try it

- **Ring** the bell to play the selected note.
- **Click** the button (J2) for the next note; the LED blinks the note's
  position. **Double-click** for the previous note.
- **Press while a note sounds** to damp it.
- **Hold about 1 s** to lock the note so it can't change by accident.

The full button and LED reference is in the
[firmware guide](../../firmware/README.md#using-the-instrument).

## 5. Change the notes

Open `bells.json` on the `CIRCUITPY` drive in any text editor. The `bells`
list holds the resident notes in button order. Delete lines to keep fewer
notes, or reorder them. A note can use one of the included
`sounds/<note>.mp3` files, or `"sound": "synth"` for a modelled bell at any
pitch, for example `{"id": "G4", "sound": "synth"}`. Save the file and the
board restarts with the new list. If the file has a mistake, the LED blinks
fast and the console says what is wrong.

## 6. See what it is doing (optional)

Open a serial console to watch messages and errors. Any of these work:

- **Browser:** [code.circuitpython.org](https://code.circuitpython.org)
  (Chrome or Edge), connect over USB, then open the serial panel.
- [Mu editor](https://codewith.mu): click **Serial**.
- PuTTY, `screen` or `tio` on the board's serial port (any baud rate).

Each line is a JSON message, such as `{"type":"gesture","g":"ring",...}`
when you ring. Press **Ctrl-C** to stop the instrument; it mutes and powers
down audio first. Press **Ctrl-D** to start it again.

## If something goes wrong

| Symptom | Try |
|---|---|
| No `RPI-RP2` or `CIRCUITPY` drive | Another cable (many are charge-only); another USB port |
| LED blinks fast | Read the console message; usually a missing sound file or a `bells.json` typo |
| Files look corrupted | In the console, type `import storage; storage.erase_filesystem()`, then copy the files again |
| Need `RPI-RP2` again | In the console, type `import microcontroller; microcontroller.on_next_reset(microcontroller.RunMode.UF2); microcontroller.reset()` |

Please report what happened in an
[issue](https://github.com/dcuccia/digital-handbell/issues). Include the
zip's version (in `build_info.json` on the drive) and what you saw.
