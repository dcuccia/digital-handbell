# Reference-design catalog

Research snapshot, updated 2026-09-07. Product IDs are the stable catalog keys.
Repository commits below pin inspected sources, not the revision guaranteed to
ship in a purchased product. Reference boards are useful design evidence, not
proof that a reduced circular relayout will work identically.

All Adafruit electronics repositories cataloged below contain native EAGLE XML
`.sch` and `.brd` files. See [CAD workflow](schematic-plan.md) and
[licensing](../ATTRIBUTION.md) before copying or converting them.

## Integrated and audio references

| Product | Role and important distinction | Guide | Hardware repository and inspected revision |
|---|---|---|---|
| [5768: RP2040 Prop-Maker Feather](https://www.adafruit.com/product/5768) | Leading integrated baseline: RP2040, 8 MB external flash, MAX98357A, LIS3DH, USB-C, charger, switched peripheral rail. Accelerometer only; no boosted 5 V battery supply. | [Guide](https://learn.adafruit.com/adafruit-rp2040-prop-maker-feather), [downloads](https://learn.adafruit.com/adafruit-rp2040-prop-maker-feather/downloads-2) | [Adafruit-RP2040-Prop-Maker-Feather-PCB](https://github.com/adafruit/Adafruit-RP2040-Prop-Maker-Feather-PCB/tree/408fa9a40c0a01a3a65497ef42a29e0b08fe711e), `408fa9a40c0a01a3a65497ef42a29e0b08fe711e` |
| [3988: Prop-Maker FeatherWing](https://www.adafruit.com/product/3988) | Historical peripheral-only reference. **PAM8302 analog-input** amplifier, not the I2S circuit. LIS3DH, switched supply, LED drivers; no MCU or charger. | [Guide](https://learn.adafruit.com/adafruit-prop-maker-featherwing), [downloads](https://learn.adafruit.com/adafruit-prop-maker-featherwing/downloads) | [Adafruit-Prop-Maker-FeatherWing-PCB](https://github.com/adafruit/Adafruit-Prop-Maker-FeatherWing-PCB/tree/f0e322ee15e06fe7810d9ec08f992a1b2fbe9bc2), `f0e322ee15e06fe7810d9ec08f992a1b2fbe9bc2` |
| [3006: MAX98357A I2S 3 W class-D breakout](https://www.adafruit.com/product/3006) | Mono digital audio/reference layout. Power depends on supply, load, and distortion; "3 W" is not a clean-output guarantee from 1S LiPo. | [Guide](https://learn.adafruit.com/adafruit-max98357-i2s-class-d-mono-amp), [downloads](https://learn.adafruit.com/adafruit-max98357-i2s-class-d-mono-amp/downloads) | [Adafruit-MAX98357-I2S-Amp-Breakout](https://github.com/adafruit/Adafruit-MAX98357-I2S-Amp-Breakout/tree/c7cf21b4a83affb8bd0ee4fb8251d5b266d964ff), `c7cf21b4a83affb8bd0ee4fb8251d5b266d964ff` |
| [5770: I2S Amplifier BFF for QT Py/Xiao](https://www.adafruit.com/product/5770) | Resolves the unnamed BFF in the initial list. Compact MAX98357A audio-only circuit; stock mapping A0=DIN, A1=LRCLK, A2=BCLK. No charger or sensor. | [Guide](https://learn.adafruit.com/i2s-amplifier-bff), [downloads](https://learn.adafruit.com/i2s-amplifier-bff/downloads) | [Adafruit-I2S-Amplifier-BFF-PCB](https://github.com/adafruit/Adafruit-I2S-Amplifier-BFF-PCB/tree/fe191f0585be438605feca267afa38fe587e57f4), `fe191f0585be438605feca267afa38fe587e57f4` |

For 5768, use `Adafruit Feather RP2040 Prop-Maker.sch` / `.brd`.
For 3006, use `Adafruit MAX98357 Breakout.sch` / `.brd`: that repository also
contains a different, newer stereo design. For 3988 use
`Adafruit Prop Maker FeatherWing.sch` / `.brd`; for 5770 use
`Adafruit I2S Amplifier BFF.sch` / `.brd`.

## MCU, charging, and sensor alternatives

| Product | Useful content / limitation | Guide | Hardware repository and inspected revision |
|---|---|---|---|
| [4884: Feather RP2040](https://www.adafruit.com/product/4884) | RP2040, 8 MB flash, USB-C, MCP73831 charger, discrete USB/battery selection. Hardware license version unresolved; see attribution. | [Guide](https://learn.adafruit.com/adafruit-feather-rp2040-pico), [downloads](https://learn.adafruit.com/adafruit-feather-rp2040-pico/downloads) | [Adafruit-Feather-RP2040-PCB](https://github.com/adafruit/Adafruit-Feather-RP2040-PCB/tree/ea88166891ee0a1697a3899a5d55ab3722a2f125), `ea88166891ee0a1697a3899a5d55ab3722a2f125` |
| [5302: KB2040 RP2040 Kee Boar Driver](https://www.adafruit.com/product/5302) | Compact RP2040, 8 MB flash, AP2112K-3.3, no charger. Vendor documents a two-layer, 7/7 mil, 0402-passive implementation: useful layout precedent. | [Guide](https://learn.adafruit.com/adafruit-kb2040), [downloads](https://learn.adafruit.com/adafruit-kb2040/downloads) | [Adafruit-KB2040-PCB](https://github.com/adafruit/Adafruit-KB2040-PCB/tree/b4160dcf4385ef2cc30e9652489328321720ee4b), `b4160dcf4385ef2cc30e9652489328321720ee4b` |
| [4900: QT Py RP2040](https://www.adafruit.com/product/4900) | Compact RP2040/8 MB flash/AP2112K-3.3, no charger. Uses bottom-side components; its density does not demonstrate one-face assembly feasibility. | [Guide](https://learn.adafruit.com/adafruit-qt-py-2040), [downloads](https://learn.adafruit.com/adafruit-qt-py-2040/downloads) | [Adafruit-QT-Py-RP2040-PCB](https://github.com/adafruit/Adafruit-QT-Py-RP2040-PCB/tree/5b6ebd1661fd5250b4f60bdba14d5c475259b7f4), `5b6ebd1661fd5250b4f60bdba14d5c475259b7f4` |
| [5397: LiIon/LiPoly Charger BFF](https://www.adafruit.com/product/5397) | MCP73831, approximately 200 mA, switch and Schottky battery feed. Uses host USB connector. Battery-mode "5V" rail is not boosted. Rev C adds external-switch pads. | [Guide](https://learn.adafruit.com/adafruit-qt-py-charger-bff), [downloads](https://learn.adafruit.com/adafruit-qt-py-charger-bff/downloads) | [Adafruit-Charger-BFF-PCB](https://github.com/adafruit/Adafruit-Charger-BFF-PCB/tree/2acd339ac57539b236e1b072488f581ea56e3a4c), `2acd339ac57539b236e1b072488f581ea56e3a4c` |
| [5426: QT Py ESP32-S3, 8 MB flash / no PSRAM](https://www.adafruit.com/product/5426) | Native general-purpose USB, hardware I2S, Wi-Fi/BLE-capable MCU. This SKU has no PSRAM; battery pads are not a charger. Future option, not RP2040 drop-in. | [Guide](https://learn.adafruit.com/adafruit-qt-py-esp32-s3), [downloads](https://learn.adafruit.com/adafruit-qt-py-esp32-s3/downloads) | [Adafruit-QT-Py-ESP32-S3-PCB](https://github.com/adafruit/Adafruit-QT-Py-ESP32-S3-PCB/tree/333b35f9c77338d69816e542e7c6aa4db271d432), `333b35f9c77338d69816e542e7c6aa4db271d432` |
| [5405: QT Py ESP32-C3](https://www.adafruit.com/product/5405) | ESP32-C3FH4, 4 MB flash, hardware I2S, Wi-Fi/BLE-capable MCU. Fixed-function USB Serial/JTAG, not an S3-style USB device controller; no charger. | [Guide](https://learn.adafruit.com/adafruit-qt-py-esp32-c3-wifi-dev-board), [downloads](https://learn.adafruit.com/adafruit-qt-py-esp32-c3-wifi-dev-board/downloads) | [Adafruit-QT-Py-ESP32-C3-PCB](https://github.com/adafruit/Adafruit-QT-Py-ESP32-C3-PCB/tree/8618fb52d806fb184ec5807490db0a9b084ffa9c), `8618fb52d806fb184ec5807490db0a9b084ffa9c` |
| [4410: USB-C Micro-Lipo charger](https://www.adafruit.com/product/4410) | MCP73831, 100 mA default / advertised 500 mA jumper option. Charger only, not a managed system power path. Select `Adafruit USB C microlipo charger.*`, not another connector variant. | [Guide](https://learn.adafruit.com/adafruit-microlipo-and-minilipo-battery-chargers), [downloads](https://learn.adafruit.com/adafruit-microlipo-and-minilipo-battery-chargers/downloads) | [Adafruit-MicroLipo-PCB](https://github.com/adafruit/Adafruit-MicroLipo-PCB/tree/d8ab4b0f00c69a9f337a8d697bd15e0b9bae2e25), `d8ab4b0f00c69a9f337a8d697bd15e0b9bae2e25` |
| [2809: LIS3DH triple-axis accelerometer](https://www.adafruit.com/product/2809) | Three acceleration axes, selectable +/-2/4/8/16 g, I2C/SPI, tap/motion interrupt. **No gyroscope.** Breakout regulation and level shifting may be redundant in a common 3.3 V system. | [Guide](https://learn.adafruit.com/adafruit-lis3dh-triple-axis-accelerometer-breakout), [downloads](https://learn.adafruit.com/adafruit-lis3dh-triple-axis-accelerometer-breakout/downloads) | [Adafruit-LIS3DH-Breakout-PCB](https://github.com/adafruit/Adafruit-LIS3DH-Breakout-PCB/tree/f5f3e1b33fec19a56b2c14c69bb1b97c1c4f2861), `f5f3e1b33fec19a56b2c14c69bb1b97c1c4f2861` |

## Six-axis candidates added 2026-09-07

See the [motion-sensor decision](motion-sensing.md) for the owner-approved choice,
chest-stop ambiguity, software API details, and dated sourcing/assembly findings.
The [4438 source](../hardware/reference/adafruit-4438/README.md) is now vendored
and adapted in the separate handbell draft. The 5768 reference remains unchanged;
4503 remains catalog-only.

| Product | Role and qualification | Guide | Hardware source |
|---|---|---|---|
| [4438: LSM6DSOX 6-DoF IMU](https://www.adafruit.com/product/4438) | Owner-approved and integrated; CC BY-SA 3.0 hardware; basic I2C readout without ML, with the documented CTRL9_XL bring-up gate | [Guide](https://learn.adafruit.com/lsm6dsox-and-ism330dhc-6-dof-imu), [downloads](https://learn.adafruit.com/lsm6dsox-and-ism330dhc-6-dof-imu/downloads) | [Adafruit-LSM6DSOX-PCB](https://github.com/adafruit/Adafruit-LSM6DSOX-PCB/tree/c05abef4675b0380fbf3d23171615a2f1ac0b130), `c05abef4675b0380fbf3d23171615a2f1ac0b130`; `Adafruit_LSM6DSOX.sch` / `.brd` |
| [4503: LSM6DS3TR-C 6-DoF IMU](https://www.adafruit.com/product/4503) | Economical alternative; resolve overlapping MIT/CC hardware notices and inconsistent lifecycle descriptions before production use | [Guide](https://learn.adafruit.com/adafruit-lsm6ds3tr-c-6-dof-accel-gyro-imu), [downloads](https://learn.adafruit.com/adafruit-lsm6ds3tr-c-6-dof-accel-gyro-imu/downloads) | [Adafruit-LSM6DS3TR-C-PCB](https://github.com/adafruit/Adafruit-LSM6DS3TR-C-PCB/tree/9bf02b7214d35f2699bfd24737865511e4f9f114), `9bf02b7214d35f2699bfd24737865511e4f9f114`; `Adafruit_LSM6DS3.sch` / `.brd` |

The inspected [Adafruit CircuitPython LSM6DS](https://github.com/adafruit/Adafruit_CircuitPython_LSM6DS/tree/cdfc14a687a138aa0f2c6abab061bfc1bfafa561)
source is `cdfc14a687a138aa0f2c6abab061bfc1bfafa561`, separately MIT-licensed.
Current subclass modules expose acceleration in m/s^2 and gyro in rad/s.

## Boost references added 2026-09-07

These are inspected, **catalog-only** sources, not imported KiCad blocks or
qualified handbell parts. The owner independently identified MiniBoost during
the same review. Both source READMEs credit Limor Fried/Ladyada for Adafruit
Industries and both `license.txt` files specify CC BY-SA 3.0 Unported.

| Product | Source findings / role | Pinned hardware |
|---|---|---|
| [2030 PowerBoost 1000 Basic](https://www.adafruit.com/product/2030) | TPS61030RSAR; 6.8 uH, 8 x 8 mm inductor footprint; nominal 5.175 V; no charger | [Source](https://github.com/adafruit/Adafruit-PowerBoost-1000-PCB/tree/493d06d70537ce418355b395bb251a661d683150), `493d06d70537ce418355b395bb251a661d683150`; [downloads](https://learn.adafruit.com/adafruit-powerboost-1000-basic/downloads) |
| [4654 MiniBoost TPS61023](https://www.adafruit.com/product/4654) | Leading compact boost candidate: SOT563, 1 uH / 5 x 5 mm inductor footprint, three 22 uF/0805 capacitors; no charger; exact magnetic/capacitor MPNs unresolved | [Source](https://github.com/adafruit/Adafruit-TPS61023-PCB/tree/82b5a33a1900a5c13849029bc84e7856a44086e0), `82b5a33a1900a5c13849029bc84e7856a44086e0`; `Adafruit TPS61023.sch` / `.brd` |

MiniBoost's source uses **732 kohm/100 kohm feedback**, corresponding to a
5 V-class rail, while product/README prose says 5.2 V. This is unresolved
source/prose disagreement, not a measurement of a retail unit. Source EN has
a 100 kohm pull-up to VIN; the derivative needs its own default-state/MCU
voltage review. Full circuit, current and layout implications are in the
[compact review](compact-power-and-packaging.md).

The [WE-MAIA family](https://www.we-online.com/en/components/products/WE-MAIA)
is an owner-proposed magnetic alternative, not a reviewed drop-in MPN.
Use exact manufacturer curves/land patterns before substituting.

## Software and primary technical sources

| Source | Evidence / intended use |
|---|---|
| [Prop-Maker CircuitPython guide](https://learn.adafruit.com/adafruit-rp2040-prop-maker-feather/circuitpython) | Beginner installation/recovery and vendor examples; not a finished handbell application |
| [CircuitPython board definition](https://github.com/adafruit/circuitpython/tree/d897c15f24b2a6de6529f138aed4705327020dab/ports/raspberrypi/boards/adafruit_feather_rp2040_prop_maker) | GPIO aliases, flash support, board identity; inspected release-source snapshot |
| [RP2040 I2S implementation](https://github.com/adafruit/circuitpython/blob/d897c15f24b2a6de6529f138aed4705327020dab/ports/raspberrypi/common-hal/audiobusio/I2SOut.c) | PIO/DMA implementation; generated BCLK/word-select require consecutive GPIOs |
| [LIS3DH CircuitPython driver](https://github.com/adafruit/Adafruit_CircuitPython_LIS3DH/tree/cd40b482a098a62ecce1b4c62a1f1930be984e16) | Acceleration, tap, shake and interrupts; MIT; requires `adafruit_bus_device` |
| [Adafruit Learning System examples](https://github.com/adafruit/Adafruit_Learning_System_Guides/tree/e45576f18a6d6fc345c89be725dbb22bf6d647ea) | Code provenance; inspected relevant examples carry MIT headers; audit asset rights separately |
| [MAX98357A/B datasheet](https://cdn-shop.adafruit.com/product-files/3006/MAX98357A-MAX98357B.pdf) | A=I2S, B=left-justified; power/THD curves, SD_MODE, startup, bypassing and layout |
| [MCP73831 datasheet](https://ww1.microchip.com/downloads/en/DeviceDoc/20001984g.pdf) | Charge-current setting, termination, thermal regulation, operating limits |
| [Microchip AN1149](https://ww1.microchip.com/downloads/en/appnotes/01149b.pdf) | External load sharing and why a system load on the battery node can affect termination |
| [RP2040 hardware-design guide](https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf) | Core/clock/flash/USB and PCB implementation cross-check; review before schematic freeze |
| [TPS61030 datasheet](https://www.ti.com/lit/ds/symlink/tps61030.pdf) | PowerBoost controller limits, shutdown, magnetics, compensation and layout |
| [TPS61023 datasheet](https://www.ti.com/lit/ds/symlink/tps61023.pdf) | MiniBoost controller pinout, approximately 0.6 V reference, valley current limit, true disconnect/pass-through and layout |
| [ESP32-S3-MINI-1/-1U datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3-mini-1_mini-1u_datasheet_en.pdf) | Reviewed v1.7: antenna module 15.4 x 20.5 x 2.4 mm; -N8 = 8 MB flash/no PSRAM; -N4R2 = 4 MB flash/2 MB PSRAM; exact variant/build and RF clearances matter |
| [ESP32-C3-MINI-1 datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-c3-mini-1_datasheet_en.pdf) | Reviewed v2.2: antenna module 13.2 x 16.6 x 2.4 mm; recommended N4X/H4X versus legacy NRND N4/H4; not S3 native USB or pin-compatible |

## Documentation discrepancies and limits

- The 5770 [pinout page](https://learn.adafruit.com/i2s-amplifier-bff/pinouts)
  calls its amplifier "MAX93785"; the pinned schematic identifies U1 as
  MAX98357A. Record this as a guide typo, not a different chip.
- Some MCU landing-page prose disagrees with source hardware: the QT Py RP2040
  page has a legacy 4 MB description, while current product/source specify
  8 MB; a Feather page mentions a 24 MHz crystal while the schematic specifies
  12 MHz. Resolve BOM decisions against the pinned schematic and manufacturer
  requirements, not a single summary paragraph.
- [CircuitPython issue 7322](https://github.com/adafruit/circuitpython/issues/7322)
  documents historical audio-buffer/glitch/latency tradeoffs during competing
  transfers. It is a regression scenario to investigate, not proof of a defect
  in the selected current build.
- Do not assume BLE support from a chip's radio capability alone. Confirm the
  chosen CircuitPython build and protocol APIs if wireless becomes scope.
- The [ESP32-C3 CircuitPython page](https://circuitpython.org/board/adafruit_qtpy_esp32c3/)
  confirms support but explicitly lacks a `CIRCUITPY` USB drive; serial install
  and Web Workflow differ from the preferred offline drag-and-drop experience.
- The S3 [no-PSRAM build](https://circuitpython.org/board/adafruit_qtpy_esp32s3_nopsram/)
  is the relevant 5426 target. Blank custom hardware needs provisioning; do not
  assume a retail board's installed TinyUF2 bootloader is present.

## Enclosure and historical sources

The initial shell inspiration was
[Amazon B09P4NTLWK](https://www.amazon.com/Colorful-Handbells-Musical-Instrument-Wedding/dp/B09P4NTLWK).
Its usable internal dimensions were **not established** by the accessible
listing. The owner subsequently identified the actually purchased
[B01EABRWO6 set](https://www.amazon.com/dp/B01EABRWO6). Its reported estimates and
the owner-supplied 40 mm-speaker drawing are captured in the
[measurement record](measurements/shell-speaker-inputs.json), not treated as
qualified manufacturing dimensions. Gikfun EK1725/EK1794 comparisons and the
40 mm seller power-rating conflict are in
[mechanics and manufacturing](mechanics-and-manufacturing.md).

Preserved from [2023 notes](../Design%20Notes.md), not newly selected:

| Historical reference | Disposition |
|---|---|
| [Seeed XIAO BLE Sense nRF52840](https://www.seeedstudio.com/Seeed-XIAO-BLE-Sense-nRF52840-p-5253.html) | Future wireless/sensor comparison; source/licensing audit not performed here |
| [ILabs Challenger RP2040 WiFi/BLE MkII](https://ilabs.se/product/challenger-rp2040-wifi-ble-mkii-with-chip-antenna-and-16bit-accelerometer/?currency=USD) | Historical integrated alternative; not evaluated as current baseline |
| [Amazon Rhythm Band B0002E363C](https://www.amazon.com/Rhythm-Band-Note-Metal-Bells/dp/B0002E363C) | Alternate shell; dimensions/tolerances unverified |
| [Adafruit 3968](https://www.adafruit.com/product/3968) | Original speaker link retained; accessible page did not establish useful specifications, so not used for sizing |
| [Adafruit 5498](https://www.adafruit.com/product/5498) | Original "power switch?" reference is a **momentary SPDT step switch with LED**, not by itself a latching battery disconnect |

Current illustrative speaker comparisons and fabrication sources live in
[mechanics and manufacturing](mechanics-and-manufacturing.md).
