# ERC review: original 0.1 dispositions and current 0.2

**Current 0.2:** the electrical reduction, boost/mute/button circuits and
service-pad changes also have **0 ERC errors / 0 warnings** under the unchanged
rules and empty exclusions. See the [revision handoff](../../../docs/electrical-reduction-and-placement.md)
and [current connectivity report](connectivity-review.json): 62 retained
components, 73 projected groups, source imports 71/17/6, and explicit changes.
The historical dispositions below describe 0.1; removed peripherals are no
longer present. They are retained as an audit trail, not a current BOM.

Reviewed 2026-09-07 using KiCad 10.0.6. **All 50 original findings are individually
disposed of in the separate derivative: 13 errors and 37 warnings.** The final
[handbell ERC](handbell-erc.json) has **0 errors and 0 warnings**.
No original reference files, severity settings, pin-conflict matrix or exclusions
were changed to achieve that result. The reference's four default ignored checks
remain unchanged; no new checks are disabled.

The [machine record](erc-dispositions.json) preserves each original finding and
its UUIDs, bound to the immutable input report's LF-normalized SHA-256.
Review hashes normalize Windows/Git line endings; upstream source-byte hashes
remain exact and separate. IDs below follow the
[original report](../../reference/adafruit-5768/reports/reference-erc.json) order.
Use UUIDs/native geometry rather than treating the exported JSON coordinates
as placement instructions: this KiCad export reports positions/lengths at
one hundredth of the corresponding native schematic millimetres.

## Individual dispositions

| Finding | Location | Disposition |
|---|---|---|
| ERC-01 | IC1.45 / core rail | Corrected VREG_VOUT to power_out. Renamed the inherited 1.2V label to VCORE without changing connections; RP2040 reset nominal is 1.1 V. |
| ERC-02 | VBUS | Added #FLG01 declaring the external USB source; this does not validate USB current budget or power states. |
| ERC-03 | GND | Added #FLG02 declaring the external power-return domain; no ground split or physical source added. |
| ERC-04 | U2.1 / VHI | Added #FLG03 at the output domain of the retained D4/Q3 discrete source-selection circuit. |
| ERC-05 | U2.4 | Named pin NC and added an explicit no-connect marker for the fixed-output RT9080. Not applicable to an adjustable RT9080N SNS variant. |
| ERC-06 | X6.A8 / SBU1 | Explicit NC for the USB2-only connector; CC and USB data wiring retained. |
| ERC-07 | X6.B8 / SBU2 | Explicit NC for the USB2-only connector; CC and USB data wiring retained. |
| ERC-08 | U3.3 / charge output | Corrected MCP73831 VBAT to power_out, as specified for its battery charge-control output. |
| ERC-09 | Old IC4.9 / INT2 | Superseded by sensor replacement. SOX pad 9 INT2 is connected to TP6, not left ambiguously open or tied to a rail. |
| ERC-10 | VBAT | Added #FLG04 declaring the external cell source. It is on the battery side of CHG_EN0; it does not provide cell protection. |
| ERC-11 | V+ | Added #FLG05 declaring Q1's switched peripheral-supply domain. Disabled-state/back-power behavior still requires review. |
| ERC-12 | LED1.3 / DO | Explicit NC on the retained onboard status NeoPixel's unused data output. |
| ERC-13 | U2.5 / +3V3 | Corrected the fixed-output RT9080 VOUT pin to power_out; no redundant +3V3 power flag added. |
| ERC-14 | RESET | Trimmed the open wire tail to the existing ~{RESET} label anchor; connected endpoints retained. |
| ERC-15 | SWCLK label / IC1.24 | Added explicit TP4 using the source's 1.5 mm copper test-pad footprint. |
| ERC-16 | SWDIO label / IC1.25 | Added explicit TP5 using the source's 1.5 mm copper test-pad footprint. |
| ERC-17 | TX | Trimmed the open wire tail to the existing TX label anchor; connected endpoints retained. |
| ERC-18 | RX | Trimmed the open wire tail to the existing RX label anchor; connected endpoints retained. |
| ERC-19 | SDA | Trimmed the open wire tail to the existing SDA label anchor; connected endpoints retained. |
| ERC-20 | SCL | Trimmed the open wire tail to the existing SCL label anchor; connected endpoints retained. |
| ERC-21 | D4 | Trimmed the open wire tail to the existing D4 label anchor; connected endpoints retained. |
| ERC-22 | D5 | Trimmed the open wire tail to the existing D5 label anchor; connected endpoints retained. |
| ERC-23 | D6 | Trimmed the open wire tail to the existing D6 label anchor; connected endpoints retained. |
| ERC-24 | USBBOOT | Trimmed the open wire tail to the existing USBBOOT label anchor; connected endpoints retained. |
| ERC-25 | MISO | Trimmed the open wire tail to the existing MISO label anchor; connected endpoints retained. |
| ERC-26 | D9 | Trimmed the open wire tail to the existing D9 label anchor; connected endpoints retained. |
| ERC-27 | D10 | Trimmed the open wire tail to the existing D10 label anchor; connected endpoints retained. |
| ERC-28 | D11 | Trimmed the open wire tail to the existing D11 label anchor; connected endpoints retained. |
| ERC-29 | D12 | Trimmed the open wire tail to the existing D12 label anchor; connected endpoints retained. |
| ERC-30 | D13 | Trimmed the open wire tail to the existing D13 label anchor; connected endpoints retained. |
| ERC-31 | SCK | Trimmed the open wire tail to the existing SCK label anchor; connected endpoints retained. |
| ERC-32 | MOSI | Trimmed the open wire tail to the existing MOSI label anchor; connected endpoints retained. |
| ERC-33 | I2S_DIN | Trimmed the open wire tail to the existing I2S_DIN label anchor; connected endpoints retained. |
| ERC-34 | I2S_BCLK | Trimmed the open wire tail to the existing I2S_BCLK label anchor; connected endpoints retained. |
| ERC-35 | I2S_LRCLK | Trimmed the open wire tail to the existing I2S_LRCLK label anchor; connected endpoints retained. |
| ERC-36 | BUTTON | Trimmed the open wire tail to the existing BUTTON label anchor; connected endpoints retained. |
| ERC-37 | SERVO | Trimmed the open wire tail to the existing SERVO label anchor; connected endpoints retained. |
| ERC-38 | PIXELS | Trimmed the open wire tail to the existing PIXELS label anchor; connected endpoints retained. |
| ERC-39 | INT | Trimmed the open wire tail to the existing INT label anchor; connected endpoints retained. |
| ERC-40 | POWER | Trimmed the open wire tail to the existing POWER label anchor; connected endpoints retained. |
| ERC-41 | D- | Trimmed the open wire tail to the existing D- label anchor; connected endpoints retained. |
| ERC-42 | D+ | Trimmed the open wire tail to the existing D+ label anchor; connected endpoints retained. |
| ERC-43 | SWCLK | Trimmed the open wire tail to the existing SWCLK label anchor; connected endpoints retained. |
| ERC-44 | SWDIO | Trimmed the open wire tail to the existing SWDIO label anchor; connected endpoints retained. |
| ERC-45 | level-shifter PIXELS | Trimmed the open wire tail to the existing PIXELS label anchor; connected endpoints retained. |
| ERC-46 | Old sensor INT stub | Superseded by the replacement block. A new terminated INT connection links SOX INT1 to the preserved GPIO22 net. |
| ERC-47 | POWER extension | Removed redundant open tail; the existing connected branch is retained. |
| ERC-48 | GAIN extension | Removed redundant open tail; the existing connected branch is retained. |
| ERC-49 | VO+ | Trimmed the open wire tail to the existing VO+ label anchor; connected endpoints retained. |
| ERC-50 | VO- | Trimmed the open wire tail to the existing VO- label anchor; connected endpoints retained. |

## Collateral warnings exposed by correct power-source modeling

Declaring real power sources exposed ten additional imported pin-type warnings;
they were corrected or superseded, not suppressed.

| Pins | Warnings | Disposition |
|---|---|---|
| Old IC4.7 SDO and IC4.10 RES(GND) | 2 | Removed with LIS3DH. The new SOX mode-specific symbol treats address/unused Mode 1 strap inputs correctly. |
| CONN1.MT1, CONN1.MT2 | 2 | Mechanical mounting terminals are passive, not bidirectional logic drivers. |
| X1.NC1, X1.NC2 | 2 | Battery-connector mounting terminals are passive; existing ground connections and pad numbers retained. |
| Q2.2 S | 1 | MOSFET source is passive. Consistently corrected its drain to passive and gate to input as well. |
| U1.8 VCC, U1.4 VSS, U1.PAD VSS | 3 | Flash supply/ground pins are power inputs; physical pin/pad identifiers and connections retained. |

The new SOX symbol explicitly models this I2C/Mode 1 use. Supply pins remain
power inputs, SDA bidirectional, SCL/CS/address/unused grounded auxiliary
inputs are inputs, and interrupt outputs are outputs. Pins 10/11 carry
explicit NC markers; their footprint lands remain present for soldering.

## Source evidence and limits

- [RP2040 datasheet](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf),
  pinout/power sections: VREG_VOUT is a power output; core reset nominal is 1.1 V.
- [Richtek RT9080 DS9080-09](https://www.richtek.com/assets/product_file/RT9080/DS9080-09.pdf),
  p.4: fixed-output pin 4 NC, pin 5 VOUT. An adjustable SNS variant is not interchangeable.
- [Microchip MCP73831/2 DS20001984G](https://ww1.microchip.com/downloads/en/DeviceDoc/20001984g.pdf),
  p.11, section 3.2: VBAT is the battery charge-control output.
- [SOX Mode 1 source and pin table](../README.md#lsm6dsox-electrical-contract)
  identifies the actual ST revision and the source-versus-breakout differences.

The original 0.1 connectivity review compared fresh exports:
**76 retained components and 75 retained connection groups**, unchanged values
and footprints outside IC4, the intended C23/C24/TP4/TP5/TP6 additions,
all 14 sensor pins/lands and the GPIO contract. It also reproduces the source
imports' 71 and 17 matching connected-net groups.

Power flags declare source intent only. They do not simulate MOSFET/jumper
states, charging current/termination, low-cell dropout or back-power. The
charger-output and external-cell nets are separated symbolically by CHG_EN0;
ERC does not substitute for review of their physical closed-jumper behavior.

Cell/temperature/current/protection, USB input/ESD, audio gain/load/quiet idle,
physical layout and independent whole-design electrical review remain open.
The newly identified CircuitPython CTRL9_XL initialization issue is also a
[bring-up gate](../../../docs/motion-sensing.md). This is not functional,
acoustic, thermal, mechanical or child-use signoff.
