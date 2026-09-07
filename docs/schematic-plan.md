# Schematic-first and CAD plan

## Tool choice and beginner workflow

**Use KiCad**, an open-source schematic/PCB tool with native editable
project files, electrical/design rule checking, 3D viewing, and manufacturing
exports. KiCad 10.0.6 and its standard libraries were installed and exercised on
2026-09-07. The upstream 5768 schematic and PCB have been imported into native
files; see [setup/readiness](kicad-setup.md) and the
[reference package](../hardware/reference/adafruit-5768/README.md).
The separate [handbell integration draft](../hardware/handbell/README.md) now
contains LSM6DSOX and the dispositions of the original 50 ERC findings.
It is not yet the fully reduced/frozen schematic. No EDA subscription or
third-party importer is needed.

The [official KiCad project-manager manual](https://docs.kicad.org/10.0/en/kicad/kicad.html)
documents importing EAGLE 6.x-or-newer XML `.sch` / `.brd` projects through
**File > Import Non-KiCad Project**. The inspected Adafruit sources use that
format. Import is a supported route, not a promise of lossless translation.
Menu wording can vary with the installed release.

1. Install the stable Windows release from [kicad.org/download](https://www.kicad.org/download/),
   including standard symbol/footprint libraries. Record the actual version.
2. Pin and obtain the selected upstream `.sch` and matching `.brd`, README,
   license, and relevant library assets under the attribution policy.
3. Import the **unmodified baseline** into a separate reference project. Keep
   the original source unchanged; do not immediately delete unwanted parts.
4. Compare schematic sheets, net membership, symbol pin numbers, device/package
   choices, footprints, board layers, zones, and rule settings to upstream.
   Save an import report including every repair and unresolved warning.
5. Create the handbell derivative from that reviewed baseline. Record
   retained/removed/changed blocks and make small, reviewable changes.
6. Export a readable schematic PDF for novice review alongside the editable
   project. Run ERC, document intentional exceptions, and compare critical
   net connectivity to the baseline.

**Can we cut and paste?** Reuse is technically feasible, subject to upstream
license terms. Import and derive whole understood blocks first; preserve
their attribution and required circuit context. Literal cross-tool copy/paste
is not an electrical-validation method. If import fails, use a reviewed manual
redraw of the licensed circuit with an explicit source-to-net mapping rather
than silently inventing substitutes.

## Proposed schematic organization

| Sheet/block | Required content and decisions |
|---|---|
| USB-C and external interface | Connector/anchors, CC1/CC2, USB data routing constraints, shield policy, ESD/input protection review, VBUS sensing if needed |
| Charger and system power | Cell-specific charger current/voltage, source selection, protection/temperature strategy, input budget, status, cutoff/off behavior |
| RP2040 core | All supply pins/decouplers, 12 MHz clock, QSPI flash, reset, BOOT recovery, SWD/test contacts, USB series/support parts |
| Audio | MAX98357A variant, rail, gain/channel selection, SD_MODE behavior, local bulk/bypass, output EMI network, keyed speaker connector |
| Motion | Approved LSM6DSOX, Mode 1 straps, supply, address, pullups, interrupts, orientation |
| Controls and test | Power/note/volume controls as selected, necessary indications, battery sense if selected, test-point and production-programming map |

The [approved compact-revision scope](compact-power-and-packaging.md) removes
Feather/servo/RGB/STEMMA branches, adds the GPIO19 two-pin button harness and
independent audio mute, and targets a source-backed boosted amplifier rail.
The 0.1 artifacts do not yet implement these decisions. Reuse small, reviewed
0402 support parts where suitable; qualify bulk capacitance and magnetics
instead of mechanically shrinking every footprint.

Do not copy the LIS3DH breakout's level shifting and regulator into an already
compatible 3.3 V system without a reason. Equally, do not remove a shared I2C
pullup or power-switch bias resistor merely because a connector disappears.

## Schematic review checklist

- [x] Source revisions, license evidence, and a retained/removed/changed block
  inventory are recorded; imported reference netlist is reviewable.
- [ ] Every power pin, exposed pad, no-connect, pullup, decoupler, flash/clock
  support component, and required test connection is accounted for.
- [ ] GPIO aliases match the firmware contract; PIO I2S clock adjacency and
  reset-time control states are correct.
- [ ] USB connector pin numbering, independent CC resistors, cable orientation,
  5 V input limits, shield/ESD strategy, and connector anchors are reviewed.
- [ ] Selected cell datasheet, polarity, protection, current rating, charge
  limits, temperature requirements, retention space, and cutoff are recorded.
- [ ] USB-only, battery-only, USB+cell, unplug/replug, amplifier peaks, disabled
  state, and brownout/restart have an explicit power-path analysis.
- [ ] Charge current is set for the actual cell. Die thermal regulation is not
  misrepresented as cell-temperature protection.
- [ ] Speaker impedance/power, gain, digital level limits, BTL labeling,
  SD_MODE/channel thresholds, and rail range are consistent.
- [ ] Boost inductor/capacitor ratings and effective values, switching loops,
  low-cell current, enable/isolation/discharge, startup and USB transitions
  are reviewed against the selected reference and exact parts.
- [ ] Quiescent/off states and power sequencing are defined, including possible
  back-power through I2S/control pins when the amp supply is off.
- [ ] Candidate MPNs, footprints, pad numbering, stock/assembly options,
  substitutions, and at least provisional costs are linked to the BOM.
- [x] ERC findings are resolved or individually justified; no blanket disabling
  (0.1 draft; rerun after every schematic change).
- [ ] Reviewer signs off the schematic together with known limits. ERC alone
  is not evidence of functional, acoustic, thermal, or safety performance.

## Persistent artifacts at completion

The schematic epic must deliver native KiCad project/schematic files,
project-local custom libraries where needed, an exported PDF, BOM draft,
net/pin comparison, import/change report, license notices, and recorded review.
The repository contains both upstream references and a separate **0.1 handbell
integration draft**, with PDF, BOM draft, net/pad comparison and clean ERC.
Peripheral reduction, complete MPN/footprint review, cell/audio decisions and
independent electrical signoff remain open before derivative freeze.

Use project-relative library paths. Exclude machine-local preferences, lock
files, caches, and credentials; do not exclude necessary custom footprints or
source models. Record tool versions and export steps once actually exercised.
