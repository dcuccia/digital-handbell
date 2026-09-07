# Adafruit MiniBoost TPS61023 reference

**Immutable imported reference, not a qualified handbell power supply.**
Source: [Adafruit TPS61023 PCB](https://github.com/adafruit/Adafruit-TPS61023-PCB/tree/82b5a33a1900a5c13849029bc84e7856a44086e0),
product [4654](https://www.adafruit.com/product/4654), commit
`82b5a33a1900a5c13849029bc84e7856a44086e0`.

Designed by **Limor Fried/Ladyada for Adafruit Industries**. The complete
[original README and required notice](upstream/README.md) and
[CC BY-SA 3.0 Unported license](upstream/license.txt) accompany byte-exact
EAGLE sources. Native conversions retain those terms, not the root MIT license.
This reference/adaptation is not an Adafruit endorsement.

KiCad 10.0.6 imported the schematic through its EAGLE project importer and the
PCB through its native CLI. The
[import record](reports/import-review.json) contains source hashes:
**six source connection groups match**, and **18 physical pads** in the seven
standalone footprint types match source locations, dimensions and rectangle axes.
Standalone footprints were normalized from native PCB poses before use.

The [reference ERC](reports/reference-erc.json) retains its **four initial
findings**, not suppressed or confused with the handbell derivative's ERC.
The [PDF](reports/reference-schematic.pdf) and
[netlist](reports/reference-netlist.xml) support review. Raw PCB import is not a
complete routing/geometry/thermal audit; do not assume it proves source copper
fidelity merely because standalone lands were checked.

The source divider is **732 kohm / 100 kohm**, approximately a 5 V rail despite
the README/product's 5.2 V prose. It uses TPS61023, 1 uH in a 5 x 5 mm footprint,
three 22 uF/0805 capacitors and default EN pull-up. It is **not a charger**.
Exact magnetic/capacitor MPNs and ratings remain unresolved for the handbell.

The [0.2 derivative](../../handbell/README.md) omits the default-on EN pull-up,
uses the existing GPIO23 POWER pull-down/switching, adds an optional DNP
feed-forward provision, and supplies the amplifier through VAMP. It does not
modify this reference or blindly reuse its routing.
