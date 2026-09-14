# Printed-bell power-rework native review

**PASS implemented native screens; PARTIAL ENGINEERING CANDIDATE, NOT APPROVED**

Not a functional, current, thermal, charge/fault, fabrication or mechanical-fit approval.

- KiCad: 10.0.6; PCB SHA-256 `6132f8d3ec508f8ae023888052cc2a1f8b2c24f2c38d9d12dca3234ba887dcc1`.
- 674 tracks / 35 vias / no zones; 325 unchanged physical pads.
- Changed root poses: C26, C27, C28, C29, L1, R23, R24, R25, R26, U5.
- ERC: 0; retained USB hole findings: 4; inherited CLI parity: 46.
- Unconnected items: 148 -> 155.
- Previously connected physical-pad pair regressions: 163.

## Native views

[Front PDF](front-native.pdf) / [rear mirrored PDF](rear-native.pdf) / [front SVG](front-native.svg) / [rear mirrored SVG](rear-native.svg).
[Schematic PDF](handbell-schematic.pdf).
Same-coordinate boost crops: [before F](boost-before-front-detail.svg) / [after F](boost-after-front-detail.svg) / [before B](boost-before-back-detail.svg) / [after B](boost-after-back-detail.svg). B detail is a through-board view, not mirrored.

## Native power topology

| Endpoint pair | Before all-F | After all-F |
|---|---|---|
| U5.6 - C27.1 | True | True |
| U5.4 - C27.2 | False | True |
| U5.6 - C28.1 | True | True |
| U5.4 - C28.2 | False | True |

R26.2 -> actual R27.2 terminal independent pickoff: **True**.
Pad/track contacts and barrel transitions are derived from native copper shapes, not route groups.
Paths are contact-hop witnesses, not shortest walks or isolated series-resistance calculations.

## Net completion

| Net | Before | After | Pad islands before/after |
|---|---|---|---|
| +3V3 | partial | partial | 21 / 21 |
| /CELL_NEG | partial | complete | 5 / 1 |
| /IMU_INT2 | unrouted | unrouted | 2 / 2 |
| /PROT_BAT | complete | complete | 1 / 1 |
| /PROT_COUT | unrouted | unrouted | 3 / 3 |
| /PROT_DOUT | complete | partial | 1 / 2 |
| /PROT_FET_RETURN | complete | complete | 1 / 1 |
| /PROT_VM | complete | complete | 1 / 1 |
| AMP_MUTE | unrouted | unrouted | 4 / 4 |
| BOOST_FB | unrouted | partial | 4 / 2 |
| BOOST_SW | complete | complete | 1 / 1 |
| BUTTON | unrouted | unrouted | 4 / 4 |
| BUTTON_EXT | unrouted | unrouted | 2 / 2 |
| CC1 | unrouted | unrouted | 2 / 2 |
| CC2 | unrouted | unrouted | 2 / 2 |
| D+ | unrouted | unrouted | 2 / 2 |
| D- | unrouted | unrouted | 2 / 2 |
| D13 | unrouted | unrouted | 2 / 2 |
| EN | unrouted | unrouted | 2 / 2 |
| GAIN | unrouted | unrouted | 2 / 2 |
| GND | partial | partial | 38 / 49 |
| I2S_BCLK | unrouted | unrouted | 3 / 3 |
| I2S_DIN | unrouted | unrouted | 3 / 3 |
| I2S_LRCLK | unrouted | unrouted | 3 / 3 |
| I2S_MOD | unrouted | unrouted | 3 / 3 |
| INT | unrouted | unrouted | 2 / 2 |
| Net-(C3-Pad2) | complete | complete | 1 / 1 |
| Net-(CHG0-PadC) | unrouted | unrouted | 2 / 2 |
| Net-(D3-PadA) | unrouted | unrouted | 2 / 2 |
| Net-(FB1-P$1) | complete | complete | 1 / 1 |
| Net-(FB2-P$1) | unrouted | unrouted | 2 / 2 |
| Net-(IC1-XIN) | complete | complete | 1 / 1 |
| Net-(IC1-XOUT) | complete | complete | 1 / 1 |
| Net-(L0-PadA) | unrouted | unrouted | 2 / 2 |
| Net-(U3-PROG) | unrouted | unrouted | 2 / 2 |
| Net-(U3-STAT) | unrouted | unrouted | 2 / 2 |
| Net-(U3-VBAT) | unrouted | unrouted | 2 / 2 |
| POWER | unrouted | unrouted | 5 / 5 |
| QSPI_CS | partial | partial | 3 / 3 |
| QSPI_DATA[0] | complete | unrouted | 1 / 2 |
| QSPI_DATA[1] | complete | unrouted | 1 / 2 |
| QSPI_DATA[2] | complete | complete | 1 / 1 |
| QSPI_DATA[3] | complete | complete | 1 / 1 |
| QSPI_SCK | complete | complete | 1 / 1 |
| SCL | unrouted | unrouted | 3 / 3 |
| SDA | unrouted | unrouted | 3 / 3 |
| SWCLK | unrouted | unrouted | 2 / 2 |
| SWDIO | unrouted | unrouted | 2 / 2 |
| USBBOOT | unrouted | unrouted | 3 / 3 |
| USB_D+ | unrouted | unrouted | 4 / 4 |
| USB_D- | unrouted | unrouted | 4 / 4 |
| V+ | partial | partial | 2 / 2 |
| VAMP | partial | partial | 3 / 5 |
| VBAT | unrouted | partial | 7 / 4 |
| VBUS | unrouted | unrouted | 7 / 7 |
| VCORE | partial | unrouted | 5 / 7 |
| VHI | unrouted | partial | 7 / 5 |
| VO+ | partial | partial | 2 / 2 |
| VO- | partial | partial | 2 / 2 |
| unconnected-(IC1-GPIO0-Pad2) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC1-GPIO1-Pad3) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC1-GPIO10-Pad13) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC1-GPIO11-Pad14) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC1-GPIO12-Pad15) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC1-GPIO14-Pad17) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC1-GPIO15-Pad18) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC1-GPIO21-Pad32) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC1-GPIO24-Pad36) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC1-GPIO25-Pad37) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC1-GPIO26{slash}AD0-Pad38) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC1-GPIO27{slash}AD1-Pad39) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC1-GPIO28{slash}AD2-Pad40) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC1-GPIO29{slash}AD3-Pad41) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC1-GPIO4-Pad6) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC1-GPIO5-Pad7) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC1-GPIO6-Pad8) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC1-GPIO8-Pad11) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC1-GPIO9-Pad12) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC4-OCS_AUX-Pad10) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(IC4-SDO_AUX-Pad11) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(U2-NC-Pad4) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(U6-NC-Pad1) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(X6-SBU1-PadA8) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| unconnected-(X6-SBU2-PadB8) | single_pad_or_NC | single_pad_or_NC | 1 / 1 |
| ~{ENABLE} | unrouted | unrouted | 3 / 3 |
| ~{RESET} | unrouted | unrouted | 3 / 3 |

## Validation failures

No failure of the implemented screens. Routing and qualification remain incomplete.

## Remaining gates

The former mechanical/service-label checker is not run against this package. Its package-bound
globals and prior fit approval are not reusable evidence for moved electronics. The exact new
manifest/PCB still require mechanical rebind, assembled label visibility and physical review.
Native service glyphs and all seven full rectangles are separately screened against rear copper.
Review exposed power widths, loop area, SW escape, R24 quiet ground, source/return completion,
finished copper and via process, current/thermal/charge/fault behavior before any release.
