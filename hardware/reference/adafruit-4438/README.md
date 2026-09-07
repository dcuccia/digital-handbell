# Adafruit 4438 LSM6DSOX reference

Pinned, unchanged EAGLE source plus a KiCad 10.0.6 conversion, made 2026-09-07.
This is a **reference**, not the handbell derivative or a fabrication release.

Source: [Adafruit-LSM6DSOX-PCB](https://github.com/adafruit/Adafruit-LSM6DSOX-PCB/tree/c05abef4675b0380fbf3d23171615a2f1ac0b130),
commit **`c05abef4675b0380fbf3d23171615a2f1ac0b130`**.
[Product 4438](https://www.adafruit.com/product/4438);
[learning guide](https://learn.adafruit.com/lsm6dsox-and-ism330dhc-6-dof-imu).

**Designed by Bryan Siepert for Adafruit Industries.** This package and its
derived CAD/review exports retain **CC BY-SA 3.0 Unported**, not the root MIT
license. See the [complete license](LICENSE.txt), the verbatim
[upstream README](upstream/README.md) and [upstream license](upstream/license.txt).
The original README, including its asset links, is unchanged; product images
are not vendored. This project is not endorsed or manufactured by Adafruit.

## Source bytes

Downloaded directly from the pinned GitHub revision; `.gitattributes` disables
line-ending conversion for `upstream/**` and the copied license.

| File | SHA-256 |
|---|---|
| `Adafruit_LSM6DSOX.sch` | `7fe13187c92c2170aa739ca57b0ee3c0541cc95609738b708574141811c1302c` |
| `Adafruit_LSM6DSOX.brd` | `42b56029ffb6dddc04ed11b2173ebecbe7d558b3489007661546e2276abea58a` |
| `README.md` | `baeae983e8d6afd022d590fa3b07986c18d62cfbf57a65a75fa80cc6a9fd9f7b` |
| `license.txt` | `075dad5e5fc96c27014fabc269f4f5732909cffd178a486f546d982b6cf86b74` |

## Conversion and evidence

Used **File > Import Non-KiCad Project > EAGLE Project**, selected the pinned
schematic and matching board, auto-matched imported layers, and saved both
editors. Native files and project-local libraries are in `kicad`.

- [Schematic PDF](reports/reference-schematic.pdf)
- [XML netlist](reports/reference-netlist.xml)
- [Initial ERC](reports/reference-erc.json): **24 findings retained**, not waived.
- **All 17 nonempty upstream board-signal connection groups match** the native
  schematic. This source needs no reference-designator renaming for comparison.
- The LGA-14L import preserves all **14 numbered lands**, their positions,
  sizes, rectangular-pad axes, and top copper/paste/mask layers. GND's two
  physical pads, 6 and 7, remain separate stacked symbol pins.

Reproduce the net/pad comparison with
[`tools/check_handbell.py`](../../../tools/check_handbell.py) as described in
the [derivative handoff](../../handbell/README.md). Its
[report](../../handbell/reports/connectivity-review.json) records the results.
This does not establish complete board-geometry, design-rule, assembly,
functional or safety equivalence. The breakout's remaining ERC findings have
not been silently edited out of this reference.

Only the sensor symbol and footprint are reused by the handbell. The derivative
follows ST's fixed Mode 1 wiring rather than copying the breakout's auxiliary
header and floating SDx/SCx connections. Its regulator, level shifters, CS diode
and resistor networks are not needed on the common 3.3 V handbell bus.
