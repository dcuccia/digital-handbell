# Unresolved before ordering

**QUOTE ONLY - not a fabrication release.** Every item below stands between
this package and an actual order. Nothing has been ordered, paid or accepted.
The [README](README.md) says what was uploaded, and
[fab-options.md](fab-options.md) covers the fabrication options and questions.

## Owner decisions

1. **Source of record.** The package is bound to the public snapshot (PCB
   `2f738ccb`). The private working board `best-0-testen` (PCB `0051b2e3`)
   differs only in J1's footprint expression. Choose one; a different source
   needs a fresh export and a fresh `verify` run.
2. **Surface finish: decided 2026-11-10, ENIG with 1 U" gold** (+$16.80 at
   quantity 5). The owner chose it for corrosion resistance; see
   [Surface finish](fab-options.md#surface-finish).
3. **Via covering: selected 2026-11-10 (delegated by the owner), Epoxy
   Filled & Capped** (live default, $0.00). The question of whether its
   0.5 mm limit means drill or land is still open. It is handled by the
   draft order note's stop-and-contact clause and by confirming the
   production files; see
   [Vias and via protection](fab-options.md#vias-and-via-protection-the-main-open-question).
4. **Outline tolerance: selected 2026-11-10 (delegated by the owner),
   Regular +/-0.2 mm,** the only live choice. The printed mounts must absorb
   it (R4); see [Outline and tolerance](fab-options.md#outline-and-tolerance).
5. **Silk legibility.** At least 69 text items are below the project's 0.8 mm
   minimum height, and JLC's public page quotes 1.0 mm.
6. **Quantity, colour, lead time and panelization.**
7. **Quote acceptance.** Nothing has been accepted. The upload was auto-saved
   to the account's "Projects > Quotes" history; its removal was not checked,
   so see whether it can be deleted if it is
   not wanted.
8. **JLCONE or the web flow** for the ordering step (section H).
9. **Six-layer CAD rebind (R4).** Whether and when to regenerate the
   mechanical assembly for the six-layer board.

## A. Release gates (work packages R1 to R6)

The review doc defines six work packages in
[Board-review work packages](../../../../docs/pcb-review-2026-11.md#board-review-work-packages).
Zero opens does not close any of them.

| Gate | What it needs | State |
|---|---|---|
| R1 Native rules and parity | Disposition the 71 prohibited-item findings, the 46 parity findings and the dangling copper. The 97-finding difference from the private board (388 versus 291) is library availability, not copper repairs; do not bulk-refresh legacy footprint aliases. | open |
| R2 Power, returns and critical signals | USB D+ (36.40 mm) and D- (49.68 mm, branch-inclusive) run mostly on different layers: no skew or 90-ohm qualification is supported. Review clock, QSPI, I2S and TESTEN/boot. Zero opens is not SI/PI evidence. | open |
| R3 Process and margins | Inventory every filled, planarized and capped through-via (U4, C24, C7, GAIN0), state IPC-4761 Type VII on the order, confirm supplier support and cost. No HDI. | open; via-fill size question raised |
| R4 Mechanical and service | Rebind the exact board into the assembly: contact and cell isolation, speaker height, mounts, USB mating, service access, the relocated JST ACHL J1 and its mating harness, TP5 (0.30 mm microprobe land) and TP14 (0.6 mm rear land). | open; not started |
| R5 Assembly and quotation | This package. A supplier quote is neither an order nor functional approval. | in progress |
| R6 Bring-up and acceptance | Risk-based bring-up before powered use. No child-use claim. | open |

The public snapshot's native DRC recorded 0 opens, 46 parity findings and 291
non-open findings: 71 `items_not_allowed`, 6 `track_dangling`, 1
`via_dangling`, 5 `silk_edge_clearance`, 69 `text_height`, 2 `text_thickness`,
47 `silk_overlap` and 90 `silk_over_copper`. Which rules applied to that run
is undocumented, so compare counts only within one environment.

Narrow margins carried into R3 (accepted for routing continuation only):

| Pair | Margin |
|---|---|
| TESTEN-area +3V3 via to the IC1 exposed pad | 0.200 mm |
| Same via to SDA / AMP_MUTE / In2 VBUS | 0.255 / 0.231 / 0.255 mm |
| U5-area GND/VAMP branches | 0.202272 mm (floor 0.200 mm) |
| U5-area VAMP/BOOST_SW | 0.203939 mm |
| Two intrinsic U5 pad pairs | 0.200 mm |
| Silk over pads after the C1/C4 relocation | scoped owner silk waiver; do not extend |

## B. Sourcing (BOM)

- Only 8 of 44 BOM rows carry an LCSC code: D4 C389354, IC1 C2040, IC4
  C481766, J1 C594367, Q2 and Q4 C20917, U3 C424093 and X6 C165948. All are
  status `VERIFY LIVE`: catalog evidence recorded in this repository, not
  confirmed matches. Nothing was matched at JLC; stock and Basic/Extended
  tier are not asserted.
- 36 rows are `NEEDS LCSC CODE`: BT1/BT2; C1/C4/C5/C19/C20; C2/C3;
  C6/C7/C9/C12/C13/C14/C16/C18/C23/C24; C8/C10/C11/C15/C17; C21/C22; C25;
  C26/C27/C28; C30; CHG0; D3; FB1/FB2; J2; L0; L1; Q1; Q3; Q5; the resistor
  rows R1/R2/R3/R4/R5/R7/R14/R15/R18/R21, R6/R11/R22, R8/R12/R13, R9/R10,
  R16/R17/R24, R20, R23, R25, R26, R27 and R28/R29; U1; U2; U4; U5; U6; Y1.
- IC4 (LSM6DSOX) is Standard PCBA only and needs X-ray inspection.
- J1 is listed Extended in the November ledger. Confirm the ACHL part number,
  pickup datum, mating housing (SACH-003G crimps) and per-contact current.
- X6: the alias CUSB31-CFM2AX-01-X versus C165948 is unresolved
  ([pcba-bom-readiness.md](../../../../docs/pcba-bom-readiness.md) line 153,
  [usb-connector-qualification.md](../../../../docs/usb-connector-qualification.md)
  lines 30-41).
- Q2 and Q4 both map to C20917, but Q4 is a standard SOT23 with a rotated land
  while Q2 is SOT23-WIDE. Check both in the placement preview.
- IC1: "SC0914(7)" is a procurement order code, not an LCSC number
  ([device-component-candidates.json](../../parts/device-component-candidates.json),
  line 474).
- BT1/BT2 (Keystone 254) may not be stocked or placeable at JLC.
- The manufacturer field is blank in the sourcing BOM for BT1, BT2, J1, J2,
  Q4, Q5, R27, U1, U5 and U6.
- Codes matched in a later live session are recorded only as "verify live"
  candidates, never silently in the JLC BOM `LCSC Part #` column. Never invent
  codes.

## C. Assembly and placement

- 83 references are fitted (81 top, 2 bottom). Twenty-one are excluded: C29
  (DNP); CHG_EN0, D+1, D-1 and GAIN0 plus test points TP3 to TP16 (copper-only
  features); and MH1/MH2 (board-only).
- Rotation: JLC's per-package rotation offsets cannot be checked offline. The
  CPL applies no global correction. Check every rotation and polarity in JLC's
  placement preview. Rotation hints on the PCB: `ROT=270` on L0, U4 and CHG0;
  `JLC_ROTATION=270` and `JLC_ROTATION_1=0` on U2 and U3.
- BT1 and BT2 are the only bottom-side parts (BT1 at (111.625, -100), rotation
  0; BT2 at (88.375, -100), rotation 180). JLC's bottom-side convention is
  unconfirmed.
- CPL coordinates are the footprint origin, not the body centre, and Y is
  negated. The header is `Designator,Mid X,Mid Y,Layer,Rotation`; JLC's guide
  lists Designator, Mid X, Mid Y, Rotation, Layer, so confirm the column
  mapping on upload.
- BT1/BT2 height: the drawing's upper height is 16.97 mm against a nominal
  16.59 mm. Reconcile before trusting any clearance stack-up.
- X6 has four shell-anchor joints (through-board anchors). Ask JLC how they
  are soldered.
- Panelization and stencil: the board is below JLC's 70 x 70 mm SMT panel
  minimum, so assembly needs a panel. Stencil was left off in the live quote.

## D. Fabrication

See [fab-options.md](fab-options.md): defaults, price probes, the via-fill
question, surface finish, outline tolerance, slots, silk and the draft order
notes.

## E. Stale documents and renders

- [pcba-quotation-plan.md](../../../../docs/pcba-quotation-plan.md) and
  [device-component-selection.md](../../../../docs/device-component-selection.md)
  carry four-layer-era notes (U4 and C24 vias). Treat their numbers as history.
- [pcba-bom-readiness.md](../../../../docs/pcba-bom-readiness.md) is partly
  superseded by this package.
- The older `bom-draft.csv` files under `hardware/handbell/reports/` and
  `hardware/handbell/iterations/*/reports/` are stale. Do not overwrite them
  or use them as this board's BOM.
- The 3D renders in `mechanical/studies/2026-09-13-printed-bell/views/` and
  the CAD assembly in `mechanical/studies/2026-09-13-printed-bell/imu-four-layer-review/extended-run/`
  bind four-layer-era boards. They do not show the six-layer board or the
  relocated JST ACHL J1. A rebind is work package R4 and has not started.

## F. Supplier questions (assembly)

Carried forward from the September 15 table in
[device-component-selection.md](../../../../docs/device-component-selection.md)
(about lines 96-131) without re-checking against the six-layer snapshot:

| Part | Question for the assembler |
|---|---|
| CHG0, L0 | 0.8 x 0.8 mm lands at 1.50 mm pitch |
| D3 | 0.9 x 0.8 mm lands at 2.14 mm pitch |
| D4 | 1.0 x 0.8 mm lands at 2.00 mm pitch |
| U2 | 0.55 x 1.20 mm lands; the 0.559 mm maximum lead width exceeds the land by 0.009 mm |
| U4 | centre paste aperture 1.143 mm square (about 58.1 % of the copper land) and 16 peripheral mask openings need assembler review |
| J2 | toleranced maximum and pickup mapping |
| U1 | 0.15 x 1.20 mm centre-strip aperture |
| U6 | all-NSMD assembly |
| Q5 | paste-area difference |
| BT1, BT2 | 16.97 mm upper drawing height |

The fabrication questions (via fill, annular ring, slots and panelization) are
listed at the end of [fab-options.md](fab-options.md).

## G. Export caveats

- Gerbers were plotted from the stored zone fills; zones were not refilled.
  JLC's KiCad guide refills zones in the GUI; we deliberately did not.
- Gerber and PDF timestamps are not deterministic, so the private-artifact
  hashes document this export only.
- `kicad-cli` wrote a `.kicad_prl` into the export's working copy of the
  project (57 files versus 56 in the snapshot). The snapshot is unchanged.
- The ZIP holds 13 Gerbers and the two drill files (15 flat entries). The job
  file, drill maps and drill report are not in it.
- The Excellon text coordinate format in the PTH drill file was not compared
  with the board file. Order notes therefore use board-file coordinates.
- Verification is static. It shows the exports correspond to the snapshot's
  footprints, pads, nets, vias, holes and outline, and that the BOM and CPL
  agree. It does not show JLC CAM acceptance, rotation conventions, stock or
  functional correctness.

## H. Owner actions at JLC

1. Look at JLC's Gerber viewer and, once assembly is open, the placement
   preview (rotation, polarity, bottom-side parts).
2. PCBA: BOM/CPL upload and part matching are deferred until the owner is
   present. He deferred them twice; ask once more at that step. Record matches
   as "verify live" candidates only, and stop before the cart, an order or
   payment.
3. Keep the auto-saved "Projects > Quotes" record, or see whether it can be
   deleted (not checked).
4. Accept or reject a quote. That is the owner's act alone: no payment,
   coupon, terms or cart save has been made.
5. Choose JLCONE or the web flow. Per JLC's
   [FAQ](https://jlcpcb.com/help/article/jlcone-desktop-app), JLCONE is
   "a dedicated browser shell" for the existing JLCPCB site and is not
   mandatory. JLC's
   [announcement](https://jlcpcb.com/news/jlcpcb-jlcone-desktop-app) (August
   22, 2026) lists desktop-only promotions: a random $1 to $20 instant
   discount, a "$2 PCB" deal, exclusive shipping rates and a coupon pack.
   Neither page documents BOM matching or parts pre-procurement beyond the web
   flow. Whether a quote saved on the web carries over to JLCONE, and whether
   its shipping beats the $26.60 web estimate, are unverified. Suggested: stay
   on the web for quote prep and consider JLCONE at ordering time for the
   discounts. Installing it needs explicit owner approval.

   Recommendation for the agent-first workflow (2026-11-10): the agent does
   every preparation step on the web through Playwright: upload, options,
   BOM/CPL matching and preview review. Playwright reads the page structure
   and uploads files directly, and it has already done the Gerber upload.
   Driving JLCONE would need screenshot-level desktop automation for the
   same pages and adds no capability. JLCONE is useful only as the owner's
   checkout channel for its promotions, and only if the web-prepared quote
   or cart is visible there. The owner installs it and checks this; the
   agent does not.
