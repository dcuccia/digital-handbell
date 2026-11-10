# Quote-prep package: six-layer review board (November 9-10, 2026)

**QUOTE ONLY - not a fabrication release.** These files prepare inputs for a
supplier price quote from the public review snapshot. They are not an order, a
payment, a design sign-off, or a powered-use or child-use approval. Zero opens
is a routing milestone; see the
[PR and release boundaries](../../../../docs/pcb-review-2026-11.md#pr-and-release-boundaries).

## What has and has not happened at the supplier

- The bare-PCB Gerber/drill ZIP described below was uploaded **once**, on
  2026-11-10, to JLCPCB's public instant-quote page in an interactive session.
  JLC parsed it as "Detected 6 layer board of 48.35x44.5mm".
- JLC **auto-saved** that upload to the account's "Projects > Quotes" history
  (toast: "Success! The file has been saved to the 'Projects > Quotes' menu.").
  This is a quote-history record, not an order and not a cart item. The owner
  can decide whether to keep it; whether it can be removed was not checked.
- Nothing was ordered, paid, put in the cart or accepted (no terms, no coupon).
  No BOM or CPL file was uploaded, the "PCB Assembly" and "Stencil" options
  stayed off, and no part was matched.
- Display-only probes of surface finish and via covering changed only the
  displayed price. The page was restored to JLC's defaults afterwards.
- Later on 2026-11-10, with owner approval, the PCBA step ran on the web
  quote page. The unchanged BOM/CPL were uploaded, all 44 lines were matched
  to in-stock LCSC parts (two substitutions: R27 and J2), and a quote was
  obtained: **$277.16 for 5 assembled boards before shipping**. The owner
  then selected 10 PCBs with 8 assembled, quoted live at **$345.84** before
  shipping. Nothing was added to the cart or ordered. See
  [pcba-quote-2026-11-10.md](pcba-quote-2026-11-10.md); it supersedes the
  "no BOM/CPL uploaded" statement above for that later session.

## Why this exists

The [PCBA quotation plan](../../../../docs/pcba-quotation-plan.md) authorizes
preparing quotation assets, not ordering or paying. This directory turns the
exact public snapshot into inputs a supplier can price, and records what was
checked and what was not. The other two documents here carry the open items:

- [fab-options.md](fab-options.md): fabrication options, what JLC's public
  page and live order form showed, and the questions only the supplier or the
  owner can answer.
- [unresolved-before-ordering.md](unresolved-before-ordering.md): every gate
  between this package and an actual order.

## What is ready, and what is not

| Area | Status |
|---|---|
| Bare-PCB inputs (Gerber/drill ZIP) | Prepared from the exact snapshot, statically verified, and parsed by JLC once. Not a CAM acceptance and not a quote the owner has accepted. |
| Placement file (CPL) | 83 rows, checked against the BOM and the board. Rotation conventions and the two bottom-side parts are unconfirmed at JLC. |
| BOM | 44 rows covering 83 fitted references. Only 8 rows carry an LCSC code; 36 are `NEEDS LCSC CODE`. Nothing was matched at JLC. |
| Fabrication options | Defaults observed live. Open questions (via-fill size, surface finish, outline tolerance, silk text) are in [fab-options.md](fab-options.md). |
| Remaining gates | [unresolved-before-ordering.md](unresolved-before-ordering.md). |

Do not call this package "quote-ready" or "order-ready" until that list is
dispositioned.

## Source of record

The exports come from the exact public snapshot, not from the private working
board:

```text
hardware/handbell/iterations/printed-bell-six-layer-review/
  handbell.kicad_pcb  2f738ccbae390424b7248feb94bac5e0c677b81224d5d8f8b290bbb0cc6792e2
  handbell.kicad_pro  78f6c36e62d8e2f724c6a081e6355b4ec6fc98efc0aba2a099498dd3d56335f4
  handbell.kicad_sch  72110104cef60ed84bad1cbcbab5527bd644a686984fa69b4a1b9f7e3abfd21f
```

The private `best-0-testen` board (PCB `0051b2e3`) differs from the snapshot
only in J1's footprint expression; the
[snapshot README](../../iterations/printed-bell-six-layer-review/README.md)
explains that derivation. The owner decides which board is the source of
record for an actual order. Any other source needs a fresh export and a fresh
`verify` run; every hash below is bound to this snapshot.

## Files

`MANIFEST.sha256` records SHA-256 for the nine hash-bound files. It does not
list itself, `.gitattributes` or the narrative documents.

| File | Content | Hash-bound |
|---|---|---|
| `jlc-bom.csv` | JLC-format BOM: 44 rows, 83 fitted references, `LCSC Part #` filled for 8 rows | yes |
| `cpl.csv` | Placement file, 83 rows (`Designator,Mid X,Mid Y,Layer,Rotation`) | yes |
| `sourcing-bom.csv` | One row per BOM line: MPN, manufacturer, LCSC code, provenance, status, notes | yes |
| `pcbway-bom.csv` | The same lines in PCBWay column order | yes |
| `inventory.json` | Counts and the 21 references excluded from the BOM/CPL, with reasons | yes |
| `verification.json` | Static verification report: 67 PASS, 4 INFO, 0 WARN, 0 FAIL | yes |
| `lcsc-register.json` | The six catalog entries behind the 8 filled rows; status "VERIFY LIVE" | yes |
| `expectations.json` | 19 independent expectations that `verify` checks against the exports | yes |
| `private-artifacts.sha256` | SHA-256 of the 25 private export files, by relative name | yes |
| `MANIFEST.sha256` | The nine hashes above | not self-listed |
| `.gitattributes` | `-text` for `*.csv`, `*.json`, `*.sha256`, so committed bytes equal hashed bytes | no |
| `README.md`, `fab-options.md`, `unresolved-before-ordering.md` | Narrative | no |

Only 8 of the 44 BOM rows carry an LCSC code. They are catalog evidence
recorded in this repository (status `VERIFY LIVE`), not confirmed matches,
stock or tier. No LCSC code was guessed for the other 36 rows.

## Private export artifacts

The generated exports are not committed. They live in the private evidence
folder under the relative name `quote-prep-20261109\`:

```text
quote-prep-20261109\
  gerbers\   13 Gerber layers and the .gbrjob (14 files)
  drill\     PTH and NPTH Excellon, two drill maps, drill report (5 files)
  pos\       pos-all.csv, pos-fitted.csv
  pdf\       top-assembly.pdf, bottom-assembly.pdf
  upload\    handbell-six-layer-quote-only-gerber-drill.zip
  work\      snapshot-copy\ (the export input), receipts
  sol-export-receipt.json
```

The upload ZIP has 15 flat entries (13 Gerbers plus `PTH.drl` and `NPTH.drl`);
the job file, drill maps and drill report are not in it.

```text
handbell-six-layer-quote-only-gerber-drill.zip
  222,603 bytes
  SHA-256 0bdddd0fbe1ed08c564b101ee978906e8feba50767c9dd88f062020d0f722099
```

They are not committed because they are generated output, not source;
Gerber and PDF files embed timestamps, so a fresh export differs byte for
byte; and `private-artifacts.sha256` already pins the exact bytes that were
used. The receipt holds absolute private paths, so it stays private too.

## Export recipe

KiCad 10.0.6 `kicad-cli`, run through the verified Sol executor (pinned
`gpt-5.6-sol`, medium effort; the export turn's model, effort and
sub-agent initiator were confirmed from the session event log, as the
[executor policy](../../../../docs/routing-agent-policy.md) requires).
Every command exited 0 under a 120 second hard timeout. The input was a
**copy** of the snapshot (`work\snapshot-copy\`), so the snapshot was never
opened by KiCad.

```text
kicad-cli pcb export gerbers --output <export-root>\gerbers --layers F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts --subtract-soldermask --precision 6 <snapshot-copy>\handbell.kicad_pcb

kicad-cli pcb export drill --output <export-root>\drill --format excellon --drill-origin absolute --excellon-zeros-format decimal --excellon-oval-format alternate --excellon-units mm --excellon-separate-th --generate-map --map-format gerberx2 --gerber-precision 6 --generate-report --report-path <export-root>\drill\handbell-drill-report.txt <snapshot-copy>\handbell.kicad_pcb

kicad-cli pcb export pos --output <export-root>\pos\pos-all.csv --side both --format csv --units mm <snapshot-copy>\handbell.kicad_pcb
kicad-cli pcb export pos --output <export-root>\pos\pos-fitted.csv --side both --format csv --units mm --exclude-dnp <snapshot-copy>\handbell.kicad_pcb

kicad-cli pcb export pdf --output <export-root>\pdf\top-assembly.pdf --layers F.Silkscreen,F.Fab,Edge.Cuts --mode-single --black-and-white --drill-shape-opt 2 --scale 1 <snapshot-copy>\handbell.kicad_pcb
kicad-cli pcb export pdf --output <export-root>\pdf\bottom-assembly.pdf --layers B.Silkscreen,B.Fab,Edge.Cuts --mode-single --mirror --black-and-white --drill-shape-opt 2 --scale 1 <snapshot-copy>\handbell.kicad_pcb
```

Notes that affect how far to trust the output:

- **No zone refill.** The export used the fills stored in the snapshot (no
  `--check-zones`). JLC's own KiCad guide refills zones in the GUI first; this
  package deliberately did not, so the copper is exactly what the snapshot
  stores. A refilled board is a different board state and would need its own
  verification.
- The copy has 57 files against 56 in the snapshot: `kicad-cli` wrote a
  `handbell.kicad_prl` there. The snapshot is unchanged.
- The ZIP was assembled from the 13 Gerber files and the two Excellon files.
- Tools used for verification: gerbonara 1.5.0, resvg-py 0.5.0, Pillow 13.0.0,
  Python 3.11.9.

## Verification

[`verify`](../../../../tools/build_quote_package.py) parses the exports
independently of KiCad and compares them with the snapshot and with
`expectations.json`. Result in `verification.json`: **67 PASS, 4 INFO,
0 WARN, 0 FAIL**. The checks cover:

- BOM versus CPL: both name the same 83 fitted references.
- Outline: one closed loop of 163 segments, bounding box 44.5 x 48.35 mm,
  perimeter 150.683 mm, area 1523.74 mm2. JLC independently parsed
  48.35 x 44.5 mm.
- Vias: 169, all through (F to B).
- Drills: PTH 175 (0.300 round 153, 0.350 round 12, 0.500 round 4, 0.600 slot 4,
  2.200 round 2) and NPTH 2 (0.650 round); file function matches.
- Position files and CPL rows; ZIP members; job-file size (44.55 x 48.4 mm,
  the bounding box plus the 0.05 mm Edge.Cuts stroke).
- Gerber layers: file function, content inside the outline, outline, and for
  F.Cu and B.Cu the pad positions, pad nets and flash coverage against the
  snapshot.
- Stackup arithmetic: copper 0.1308 mm plus dielectric 1.5196 mm equals
  1.6504 mm; `general.thickness` is 1.6.
- Receipt re-hash: all 24 files in the Sol receipt match.

The four INFO lines are screens, not verdicts: 18 via/pad pairs with 7 fully
inside (a via-in-pad screen), the stackup summary, and the object counts of
the two silkscreen layers (3242 and 413).

**What it does not prove.** It does not show functional correctness, JLC CAM
acceptance, rotation conventions, stock, tier, or that any capability limit
passes. It proves the exports correspond to the snapshot and that BOM and
CPL agree with each other.

## Render sanity check

Each Gerber was rendered with gerbonara (`to_pretty_svg`) and rasterized with
resvg-py (which rejects SVG width and height with an `mm` suffix, so the
suffix is stripped first). Ten renders were produced and reviewed by eye for
outline, pours, drills and silk placement. Nine are distinct images: the In1
and In4 renders are byte-identical (confirmed by hash, 2026-11-10), and their
Gerbers differ only in the FileFunction header (L2 versus L5). Both are GND
planes with one filled polygon and ten keepouts in the snapshot. The PNGs are
not committed.

## CPL and population conventions

- 83 rows. BT1 and BT2 are the only Bottom parts; X6 (the USB connector) is
  present.
- Y is negated (KiCad export convention). Positions are footprint origins,
  not body centres. No JLC rotation offset is applied.
- Header order here is `Designator,Mid X,Mid Y,Layer,Rotation`; JLC's guide
  lists `Designator, Mid X, Mid Y, Rotation, Layer`, so confirm the column
  mapping on upload.
- 21 references are excluded: C29 (DNP); CHG_EN0, D+1, D-1, GAIN0 and the
  test points TP3-TP16 (copper-only features); MH1 and MH2 (board-only).
  `inventory.json` lists each with its reason.
- Some footprints carry rotation hints (`ROT=270` on L0, U4 and CHG0;
  `JLC_ROTATION=270` and `JLC_ROTATION_1=0` on U2 and U3). No global
  correction is applied; check each in JLC's 3D preview.

## Reproduce and re-verify

All commands run from the repository root. The scripts need only the standard
library, except the Gerber checks, which need gerbonara 1.5.0.

```text
python -B -m unittest discover -s tools -p "test_build_quote_package.py"

python -B tools/build_quote_package.py build ^
  --pcb hardware/handbell/iterations/printed-bell-six-layer-review/handbell.kicad_pcb ^
  --register hardware/handbell/quote-prep/2026-11-09-six-layer/lcsc-register.json ^
  --out-dir <scratch>

cd hardware/handbell/quote-prep/2026-11-09-six-layer
sha256sum -c MANIFEST.sha256
```

- `build` writes exactly five files (`jlc-bom.csv`, `sourcing-bom.csv`,
  `pcbway-bom.csv`, `cpl.csv`, `inventory.json`); a rebuild should match the
  committed copies byte for byte.
- `verify` needs a private export root. Re-export with the recipe above and
  omit `--receipt`. Gerber and PDF hashes will differ because of embedded
  timestamps. Write `--out` to a scratch path: `verification.json` is
  hash-bound and rewriting it invalidates `MANIFEST.sha256`.
- `hashlist --check private-artifacts.sha256 --root <private-root>` (or
  `sha256sum -c` from the private root) checks the 25 private files.
- If any hash-bound file changes, regenerate `MANIFEST.sha256` with
  `hashlist`. A change to the board invalidates every export and result here.
- Line endings: `expectations.json` and `lcsc-register.json` are CRLF on disk;
  the `.gitattributes` `-text` rule keeps git from translating any hash-bound
  file.
