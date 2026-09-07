# KiCad setup and schematic readiness

Verified on Windows on 2026-09-07. **The tools needed to start schematic work
are installed and operational.** The remaining work is electrical design and
reference-import review, not installing an EDA subscription or importer plugin.

## Installed toolchain

| Item | Result |
|---|---|
| Package | Official `KiCad.KiCad`, version 10.0.6, installed through WinGet |
| Scope | Current Windows user; no machine-wide PATH modification |
| Executables | `%LOCALAPPDATA%\Programs\KiCad\10.0\bin` |
| GUI | Manager, schematic editor, and PCB editor opened with the reference |
| Standard libraries | 224 symbol-library files, 155 footprint-library directories, 105 3D-model-library directories in this installation |
| Global library tables | Initialized using KiCad's built-in libraries |
| Privacy | Anonymous data collection left disabled |
| Command line | Native schematic netlist/PDF export, ERC, and EAGLE PCB import exercised |
| Third-party plugins | None required or installed for this work |

The installer came from the official KiCad release linked by WinGet; WinGet
verified its SHA-256 before installation:
`9e24dc47119f7c472128c2f293c5e3f35569274a44c905e60a7514d47c16ce48`.
The official [Windows download page](https://www.kicad.org/download/windows/)
and [10.0.6 release](https://www.kicad.org/blog/2026/08/KiCad-10.0.6-Release/)
provide the distribution context. Counts are installation observations, not
compatibility guarantees for every future component.

Standard symbols include RP2040, MAX98357A, MCP73831-2-OT, LIS3DH, and LSM6DS3.
A similarly named symbol is not proof that its package/pinout matches a selected
suffix such as LSM6DS3TR-C. Review the exact MPN and footprint before use.
An exact LSM6DSOX symbol was not found in the installed `Sensor_Motion`
library. The [approved SOX block](../hardware/handbell/README.md) now uses the
actual Adafruit 4438 imported symbol/footprint, with all 14 physical pad mappings
compared and its symbol specialized to Mode 1. Do not substitute the LSM6DS3
symbol merely because the package outline looks similar.

## Open the handbell draft

Use **File > Open Project** and select:

```text
C:\Projects\dcuccia\digital-handbell\hardware\handbell\handbell.kicad_pro
```

Open its schematic, or read the
[PDF](../hardware/handbell/reports/handbell-schematic.pdf). The project deliberately
has no PCB yet. Keep the whole checkout: its footprint table references the
sibling reference packages. The [handoff](../hardware/handbell/README.md)
includes repeatable strict ERC and net/pad comparison commands.

## Open the reference

1. Start **KiCad 10.0** from the Windows Start menu.
2. Choose **File > Open Project** and open:

   ```text
   C:\Projects\dcuccia\digital-handbell\hardware\reference\adafruit-5768\kicad\Adafruit Feather RP2040 Prop-Maker.kicad_pro
   ```

3. Open the `.kicad_sch` entry for the schematic or `.kicad_pcb` for the board.
4. For a quick read without CAD, open the
   [schematic PDF](../hardware/reference/adafruit-5768/reports/reference-schematic.pdf).

The imported symbol and footprint libraries are project-local and use
`${KIPRJMOD}` paths. No personal library configuration is required to resolve
those imported assets. Keep this reference unchanged while a separate handbell
derivative is developed.

## Repeatable CLI access

The CLI is not assumed to be on PATH. In PowerShell:

```powershell
$KiCadCli = "$env:LOCALAPPDATA\Programs\KiCad\10.0\bin\kicad-cli.exe"
& $KiCadCli version
$Reference = "C:\Projects\dcuccia\digital-handbell\hardware\reference\adafruit-5768"
$Schematic = "$Reference\kicad\Adafruit Feather RP2040 Prop-Maker.kicad_sch"
& $KiCadCli sch export pdf --exclude-pdf-metadata --output "$env:TEMP\handbell-reference.pdf" $Schematic
& $KiCadCli sch export netlist --format kicadxml --output "$env:TEMP\handbell-reference.xml" $Schematic
& $KiCadCli sch erc --format json --output "$env:TEMP\handbell-reference-erc.json" $Schematic
```

Adjust the checkout/install path on another machine. ERC without
`--exit-code-violations` can return success while reporting violations; inspect
the report. The handbell derivative now uses that flag for enforcement, without
changing the inherited severity matrix or adding exclusions.

## Import behavior actually observed

KiCad 10.0.6 has `pcb import --format eagle`, but **no equivalent `sch import`
CLI subcommand**. Passing the EAGLE schematic directly to `sch export netlist`
failed with exit code 3. The working schematic route was the GUI:

**File > Import Non-KiCad Project > EAGLE Project**, selecting the pinned `.sch`
and a separate destination. KiCad also imported the matching `.brd`. At the
layer-mapping dialog, use **Auto-Match Layers**, review the mapping, and then
save both native editors. Do not stop with unsaved editor tabs.

The reference retained project-local libraries and produced native schematic
and PCB files. Relocating the package into this repository still allowed
schematic PDF export.

## What is ready, and what is not

We can now inspect the upstream circuit, make a separate reduced schematic,
assign reviewed parts, export review PDFs/netlists, and run ERC.

The imported reference is **not ERC-clean**: its initial report contains
13 errors and 37 warnings. Its 71 nonempty upstream board-net pin groups match
the schematic export after documented reference renaming, which is useful
connectivity evidence but does not prove footprint accuracy, layout geometry,
design-rule equivalence, or functional performance.

See the [import report](../hardware/reference/adafruit-5768/README.md).
E02 remains open for the remaining geometry/design-rule reviews. The separate
[handbell draft](../hardware/handbell/README.md) resolves all 50 original findings
and has zero current ERC findings; E04 remains open for reduction, electrical
decisions and complete review. The unchanged SOX breakout reference has its own
24 initial findings, preserved with that reference rather than globally waived.
