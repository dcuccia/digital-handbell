# Printed-bell quotation-candidate check

**INCOMPLETE routing; quotation/fabrication BLOCKED**

Not a quotation/fabrication release, functional/safety qualification or mechanical-fit approval.

- Native tracks / vias: 1124 / 87.
- Native unconnected items: 155 source -> 59 candidate.
- ERC findings: 0.
- Physical DRC types: `{"hole_clearance": 4, "silk_edge_clearance": 5, "silk_over_copper": 108, "silk_overlap": 52, "text_height": 72, "text_thickness": 2}`.
- CLI parity findings: 46 (not waived).
- Source-connected pair regressions: 0.
- Exact hashes, native findings, pad islands and endpoint witnesses are in completion-review.json.

## Input hashes

- `handbell.kicad_pcb`: `2d88301f48ad05dc01384b90111f16615f176a7f4704eab82a1e3560ef5c8bc0`
- `handbell.kicad_sch`: `e131a8d093795df7285bcae4a8886ffe01106c6513a19bd588ee7c29c6993b4f`
- `handbell.kicad_pro`: `8213261803c4a032c6351311ed43db6249720a8cb334ebd15e3daca210899990`
- `placement-manifest.json`: `404a8c53dc0ce28f8769ec4a1926452564cbd3cd5f8c27d95b7ac2ebee1b55de`
- `battery-contact-interface.json`: `f96133d9f044600167477bcddbf67c43311ed0897066db9fa63d8e7f8118467b`
- `routing-data.json`: `75c11cd27a497709437d69c86928e88b6d4971536597b84189f71c62e5c11a9d`
- `completion-build.json`: `e1aeaecbcf3e5b0f2e7819915d508d6c9326c19cd95d312533a01e05bd348955`

## Residual native net islands

| Net | Source islands | Candidate islands | Status |
|---|---:|---:|---|
| +3V3 | 21 | 2 | partial |
| /IMU_INT2 | 2 | 1 | complete |
| /PROT_COUT | 3 | 1 | complete |
| /PROT_DOUT | 2 | 1 | complete |
| AMP_MUTE | 4 | 3 | partial |
| BOOST_FB | 2 | 1 | complete |
| BUTTON | 4 | 2 | partial |
| BUTTON_EXT | 2 | 1 | complete |
| CC1 | 2 | 1 | complete |
| CC2 | 2 | 1 | complete |
| D+ | 2 | 2 | unrouted |
| D- | 2 | 2 | unrouted |
| D13 | 2 | 2 | unrouted |
| EN | 2 | 1 | complete |
| GAIN | 2 | 2 | unrouted |
| GND | 49 | 23 | partial |
| I2S_BCLK | 3 | 3 | unrouted |
| I2S_DIN | 3 | 3 | unrouted |
| I2S_LRCLK | 3 | 3 | unrouted |
| I2S_MOD | 3 | 1 | complete |
| INT | 2 | 2 | unrouted |
| Net-(CHG0-PadC) | 2 | 2 | unrouted |
| Net-(D3-PadA) | 2 | 1 | complete |
| Net-(FB2-P$1) | 2 | 2 | unrouted |
| Net-(L0-PadA) | 2 | 1 | complete |
| Net-(U3-PROG) | 2 | 1 | complete |
| Net-(U3-STAT) | 2 | 1 | complete |
| Net-(U3-VBAT) | 2 | 1 | complete |
| POWER | 5 | 3 | partial |
| QSPI_CS | 3 | 1 | complete |
| QSPI_DATA[0] | 2 | 1 | complete |
| QSPI_DATA[1] | 2 | 1 | complete |
| SCL | 3 | 2 | partial |
| SDA | 3 | 1 | complete |
| SWCLK | 2 | 2 | unrouted |
| SWDIO | 2 | 2 | unrouted |
| USBBOOT | 3 | 1 | complete |
| USB_D+ | 4 | 2 | partial |
| USB_D- | 4 | 2 | partial |
| V+ | 2 | 1 | complete |
| VAMP | 5 | 2 | partial |
| VBAT | 4 | 2 | partial |
| VBUS | 7 | 3 | partial |
| VCORE | 7 | 6 | partial |
| VHI | 5 | 2 | partial |
| VO+ | 2 | 2 | partial |
| VO- | 2 | 1 | complete |
| ~{ENABLE} | 3 | 1 | complete |
| ~{RESET} | 3 | 3 | unrouted |

Physical pad UUIDs for every open island are retained in the JSON, not replaced with zero claims.

## Failed checks

No failure of the implemented screens; this is still an incomplete/blocked engineering candidate.

## Mandatory remaining gates

- All residual native net islands/unconnected items must be routed; every source-connected pair must remain connected.
- Four original USB hole-clearance errors and 46 original CLI parity findings persist; none is a waiver.
- Inherited silk warnings remain visible engineering review work.
- Full mechanical assembly and service-visibility rebind to this exact PCB/manifest is always required.
- No current, thermal, noise, charging/fault, contact insulation/retention or child-use qualification.
- No supplier upload, purchase, fabrication/assembly order or operational approval.

Native exports: [schematic](handbell-schematic.pdf), [front](front-native.pdf), [mirrored rear](rear-native.pdf), [front SVG](front-native.svg), [rear SVG](rear-native.svg).
