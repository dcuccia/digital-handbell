# Smaller RP2040 flash: sourcing and compatibility

**2026-09-10 sourcing study, not a selected or qualified BOM substitution.**
The owner requested in-stock 2 MB and 4 MB alternatives from major authorized
distributors. These capacities mean 16 Mbit and 32 Mbit respectively; they
are serial NOR flash, not DRAM or PSRAM. Availability and prices must be
observed for the exact ordering code rather than inferred from a general
memory-market description.

The inherited U1 is labeled `8MB QSPI`. No exact 8 MB purchasing MPN was
frozen, and the earlier out-of-stock pricing candidate was not a required
part. This study does not change the schematic, footprints, native reports,
placement manifest or current fit-print files.

## Result and purchasing shortlist

**Stocked alternatives were found for both densities, but no immediately
stocked 4 x 4 mm near-drop-in was verified at DigiKey or Mouser.**
There is a supply-versus-footprint tradeoff, not a completed drop-in selection.

The following stock and USD prices were read from the main inventory and
quantity-price records embedded in DigiKey product pages on September 10.
They are prices per consumed device at the requested purchase quantity,
not breakout-board prices or JLC assembly quotes.

| Capacity | Exact MPN | DigiKey SKU | Reported stock | USD each at 10 | USD each at 100 | Package / consequence |
|---|---|---|---:|---:|---:|---|
| 2 MB / 16 Mbit | W25Q16JVUXIQ TR | 256-W25Q16JVUXIQTRCT-ND | 29,088 | 1.75000 | 1.62480 | USON-8, 2 x 3 x 0.6 mm nominal; smaller than U1, but new footprint required |
| 4 MB / 32 Mbit | MX25L3233FM2I-08G | MX25L3233FM2I-08G-ND | 30,899 | 1.15300 | 1.07522 | 200-mil SOP-8; 5.30 mm listed body width, larger lead span; new footprint and placement review required |

Directly retrieved evidence:
[Winbond USD/cut-tape offer](https://www.digikey.com.mx/en/products/detail/winbond-electronics/W25Q16JVUXIQ-TR/15182307)
and [Macronix USD offer](https://www.digikey.com.mx/en/products/detail/macronix/MX25L3233FM2I-08G/7402341).
Corresponding US product pages:
[Winbond](https://www.digikey.com/en/products/detail/winbond-electronics/W25Q16JVUXIQ-TR/15182307)
and [Macronix](https://www.digikey.com/en/products/detail/macronix/MX25L3233FM2I-08G/7402341).

**Source limitations:** US pages were blocked during research. The successfully
fetched pages were DigiKey's Mexican regional offers explicitly denominated
in USD, not a US-address checkout confirmation; UK pages corroborated stock.
Primary offers identify DigiKey rather than marketplace sellers. The Winbond
page has a conflicting out-of-stock phrase in a substitute carousel, although
its main stock message, main quantity record and structured offer report
29,088/InStock. Recheck the selected cut-tape offer before purchase.
Mouser pages repeatedly timed out; no directly verified stocked Mouser offer
is claimed. Indexed non-stock statements are weaker evidence than live offers.

The Winbond cut-tape offer has MOQ/multiple one, costs USD1.87 at one piece
and lists a 4,000-piece manufacturer reel. Optional Digi-Reel adds USD7 and
is not included. The Macronix tube offer has MOQ/multiple one and costs
USD1.23 at one piece. Its full-tube size is 92, and the price at quantity 100
uses the published 92-unit tier; the offer does not require buying 184.
Shipping, tax, assembly, attrition, feeder loading and other services are
excluded. No stock is reserved and no purchase has been made.

### Mechanically closest options: stock is the blocker

| Capacity | Exact code | Availability evidence |
|---|---|---|
| 2 MB | W25Q16JVXGIQ TR | [DigiKey indexed listing](https://www.digikey.com/en/products/detail/winbond-electronics/W25Q16JVXGIQ-TR/6193777) reported zero/no backorders; Mouser indexed listing said non-stocked. Direct stock verification was unavailable. |
| 4 MB | W25Q32JVXGIQ TR | [Directly fetched DigiKey listing](https://www.digikey.co.uk/en/products/detail/winbond-electronics/W25Q32JVXGIQ-TR/5803986) reported zero stock and no backorders. |

Both use Winbond's **XG = 4 x 4 mm XSON** package. Do not confuse it with
**UX = 2 x 3 mm USON**; `W25Q16JVUXIQ` is not the same-footprint option.
The initial search lead `W25Q32JVUXIQ` was not verified as an orderable MPN.
Nor was the 4 x 3 mm `W25Q32JVUUIQ TR` a useful stocked fallback: its directly
retrieved DigiKey record was non-stocking/obsolete.

No useful in-stock 4 x 4 mm solution was established by the checked GigaDevice
or Macronix leads either. This is the result of this bounded search, not proof
that every authorized distributor lacks every possible 4 x 4 mm device.

**Recommendation:** the stocked 2 MB Winbond UX part is worth qualifying as a
compact cost-down option if the one/two-chime storage budget holds. Its
footprint change is local in principle but still needs a real layout review.
The stocked 4 MB Macronix SOP is an electrically plausible, software-described
fallback, not the preferred mechanical choice for this crowded circular PCB.
Do not enlarge the board or silently substitute it solely because its unit
price is lower. The XG parts remain the closest mechanical candidates if an
acceptable supply offer becomes available. No density or MPN is frozen here.

## Existing electrical and footprint contract

Source: the pinned Adafruit 5768
[USON8_4X4 footprint](../hardware/reference/adafruit-5768/kicad/Adafruit%20Feather%20RP2040%20Prop-Maker-import-fps.pretty/USON8_4X4.kicad_mod)
and the current wing
[exported netlist](../hardware/handbell/iterations/wing-draft/reports/handbell-netlist.xml).

| U1 pad | Existing signal |
|---|---|
| 1 | QSPI chip select |
| 2 | QSPI data 1 / MISO |
| 3 | QSPI data 2 / write protect |
| 4 | GND |
| 5 | QSPI data 0 / MOSI |
| 6 | QSPI clock |
| 7 | QSPI data 3 / hold |
| 8 | +3V3 |
| PAD | GND, central exposed-pad provision |

The footprint draws a 4 x 4 mm body and uses 0.8 mm terminal pitch.
Peripheral land centers are x = +/-1.85 mm and
y = -1.2, -0.4, +0.4, +1.2 mm. Each land's physical XY size is
0.6 x 0.4 mm (the source encodes 0.4 x 0.6 rotated 90 degrees).
The central copper land is 2 x 3 mm, with four 0.6 x 1 mm paste windows.

Matching eight signal numbers and body dimensions alone is insufficient.
Compare the candidate's lead locations, pitch, tolerances, body/installed
height, center-pad geometry and permitted center-pad connection, then
review solder-mask/paste treatment. A manufacturer package drawing describes
package metal, not necessarily its recommended PCB land pattern.

The present mechanical proxy assumes 1 mm U1 height. Manufacturer maximum
height and assembly standoff must be checked rather than treating that proxy
as a qualified component drawing. An SOIC-8, WSON 6 x 5 mm, or USON 2 x 3 mm
alternative is not a drop-in merely because its schematic pinout matches.
Exclude 1.8 V variants from this 3.3 V design.

### Winbond XG drawing comparison

Manufacturer-authored datasheets:
[W25Q16JV Revision I, December 24, 2024](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/6661/W25Q16JV.pdf),
PDF page 71 / printed page 70, section 11.6, and
[W25Q32JV Revision I, May 4, 2021](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/5059/W25Q32JV_RevI_5-4-21.pdf),
PDF page 71 / printed page 70, section 9.6.

Both XG drawings specify a 4.00 +/-0.10 mm square body, 0.8 mm pitch,
0.45 mm nominal / 0.50 mm maximum package height, 0.30 mm nominal terminal
width and 0.40 mm nominal terminal length. The nominal exposed pad is
2.3 x 3.0 mm (specified ranges 2.2..2.4 and 2.9..3.1).

The inherited peripheral copper overlaps the nominal terminal geometry:
the terminal extends radially from about 1.60 to 2.00 mm, while existing
copper extends from 1.55 to 2.15 mm; row centers and pitch agree. The
2 x 3 mm center copper is 0.3 mm narrower overall than the nominal package
exposed metal. This is evidence for a near-footprint candidate, not a
worst-case-tolerance or manufacturer-approved land-pattern result.
The four paste windows total 2.4 mm2: 40% of existing center copper or about
35% of nominal XG exposed metal. No solder-volume recommendation is inferred.

Winbond's [official technical FAQ](https://www.winbond.com/hq/support/faq/technical/?__locale=en)
says the center metal on WSON/XSON/USON packages is not connected to internal
signals and may float or connect to device GND; it also advises avoiding
exposed PCB vias beneath the pad. Thus the current ground assignment is
permitted, but paste, tolerances and assembly remain review items.
The datasheet's eight-pin assignments match the existing signal contract.

The stocked UX package is documented separately in the W25Q16JV datasheet,
PDF page 68, section 11.3. Its different geometry is not approved by the
XG comparison. The stocked Macronix M2 package is confirmed by the
[MX25L3233F Revision 1.7 datasheet](https://www.macronix.com/Lists/Datasheet/Attachments/8933/MX25L3233F,%203V,%2032Mb,%20v1.7.pdf),
pages 76-79. Its full height/lead-span/land pattern must be reviewed before
attempting placement; the present 1 mm proxy does not qualify that SOP.

## Firmware support and capacity

The [audio/storage plan](firmware-and-audio.md#audio-storage-and-silence)
records why 2 MB is plausible and 4 MB has more room for the owner's few
short chimes. The inspected CircuitPython commit is
[`fd40abc29cf5c8ea111e16b3e6cc21b180974ae3`](https://github.com/adafruit/circuitpython/tree/fd40abc29cf5c8ea111e16b3e6cc21b180974ae3);
its `data/nvm.toml` submodule is
[`a2a0c03c221a9bc37992147b5d4ad785a6e467fe`](https://github.com/adafruit/nvm.toml/tree/a2a0c03c221a9bc37992147b5d4ad785a6e467fe).
This is a pinned source inspection, not a tested release binary.

The database contains `W25Q16JVxQ`, `W25Q16JVxM`, `W25Q32JVxQ` and
`W25Q32JVxM` descriptors. The
[Raspberry Pi Pico board definition](https://github.com/adafruit/circuitpython/blob/fd40abc29cf5c8ea111e16b3e6cc21b180974ae3/ports/raspberrypi/boards/raspberry_pi_pico/mpconfigboard.mk)
explicitly uses `W25Q16JVxQ`. That is a useful software precedent, not a
claim that the Pico's physical flash package matches our lands.

The same pinned database explicitly contains
[`MX25L3233F`](https://github.com/adafruit/nvm.toml/blob/a2a0c03c221a9bc37992147b5d4ad785a6e467fe/flash/macronix/MX25L3233F.toml).
Its manufacturer defaults select status byte 1 and the part selects QE mask
0x40, unlike Winbond's status byte 2/mask 0x02. That is a software-family
precedent for the stocked Macronix fallback, not permission to use the stock
Feather boot-stage configuration unchanged. Boot and filesystem behavior
have not been exercised on either sourced candidate.

The Q and M suffix families have different JEDEC memory-type entries
(0x40 and 0x70) and can have different quad-enable/write settings.
For example, the pinned 16 Mbit Q descriptor uses a continuous status
write, while the 32 Mbit Q descriptor supports split writes. Use the exact
descriptor and manufacturer commands; do not treat all `W25QxxJV` suffixes
as interchangeable.

RP2040 CircuitPython detects normal JEDEC flash capacity at runtime.
Therefore a smaller density alone does not prove that a stock UF2 will
write beyond the chip. However, boot-stage read mode and quad-enable
configuration are generated from the configured flash families. The stock
Prop-Maker configuration names `GD25Q64C,W25Q64JVxQ`, not all candidate
devices. Define the actual handbell flash options and verify boot/read/write
behavior before adopting a different ordering code.

## Gates before implementing a substitution

1. Resolve the exact manufacturer code, distributor SKU, stock location,
   package, minimum purchase and actual USD quote; distributor stock is
   not a reservation or JLC assembly inventory.
2. Review manufacturer package and land-pattern drawings against all nine
   existing copper lands, including the grounded center pad.
3. Set the flash definition for the chosen device; retain correct handbell
   GPIOs and recovery access rather than flashing an unrelated board build.
4. Exercise cold boot, reset, BOOTSEL/UF2 recovery, JEDEC identification,
   filesystem capacity, erase/write/readback and power-cycle persistence.
5. Confirm actual code/library/audio free space and repeated audio playback
   while motion sensing runs. Preserve the current CAD/print evidence until
   a deliberate derivative update regenerates its dependent reports.

Owning epics: E04/#4 for flash/footprint selection, E06/#6 for firmware,
E07/#7 for placement/routing, and E08/#8 for purchasing and assembly.
Manufacturer documents are linked, not redistributed or relicensed.
