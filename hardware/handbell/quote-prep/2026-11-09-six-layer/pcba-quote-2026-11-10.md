# JLCPCB PCBA quote session (November 10, 2026)

Status: **quote only.** Nothing was ordered, paid or added to the cart.
No terms were accepted and no coupon was used. "Confirm Production file"
was not set. The owner approved the upload and LCSC part matching on the
JLC web quote page. Everything below is the live state observed on
2026-11-10 and must be re-checked before ordering.

## What was done

1. The same quote-only Gerber/drill ZIP was uploaded again. JLC re-saved it
   to "Projects > Quotes". It detected a 6-layer board, 48.35 x 44.5 mm.
   ENIG was selected; the quote shows via covering at $0.00. Confirm all PCB
   options against [fab-options.md](fab-options.md) before ordering.
2. The "Stencil" (bare PCB add-on) option was switched on by mistake, then
   switched off again before continuing.
3. PCB Assembly: **Standard, Both Sides, quantity 5.** The board has two
   bottom-side parts (BT1/BT2), so it needs Both Sides. Economic is top-only,
   so Standard is required. IC4 (LSM6DSOX) adds X-ray inspection.
4. The unchanged [jlc-bom.csv](jlc-bom.csv) and [cpl.csv](cpl.csv) were
   uploaded. JLC detected 44 BOM lines.
5. All 44 lines were matched to in-stock LCSC parts and selected. The table
   below lists them. The hash-bound CSVs were **not** edited; these are JLC-side
   selections only.
6. Placement preview: the parts land on their pads. One spot check (U3,
   SOT-23-5) shows the body's pin-1 mark on the pin-1 pad. JLC's engineering
   review of rotation and polarity after ordering is still required. The
   ROT/JLC_ROTATION hints in section C of
   [unresolved-before-ordering.md](unresolved-before-ordering.md) still apply.

## Quote (5 assembled boards, before shipping and tax)

| Item | USD |
|---|---|
| PCB (6L, ENIG, includes $32.00 special offer and $17.20 finish) | 49.20 |
| PCBA setup fee | 51.50 |
| PCBA stencil (part of assembly) | 16.54 |
| Components (41 priced items) | 84.15 |
| Feeder loading fees (Extended parts) | 63.55 |
| SMT assembly | 3.47 |
| X-ray inspection | 8.25 |
| Packaging | 0.50 |
| **Total (PCB 7-8 days, assembly 3-4 days)** | **277.16** |

The faster 2-3 day assembly option adds $49.63. Earlier probes put shipping
at about $26.60 (UPS DDP). JLCONE desktop advertises $1-20 lower prices.
Feeder loading fees come from Extended parts; reducing Extended parts is the
main lever on cost.

## Quantity scaling (November 10)

Bare-PCB web prices are from live quotes using the same 6-layer, ENIG and
epoxy-filled-and-capped settings, with a 7-8 day build and shipping excluded:

| PCB qty | Web price | Basis |
|---|---|---|
| 5 | 48.80 | special offer 32.00 + finish 16.80 |
| 10 | 64.10 | special offer 47.00 + finish 17.10 |
| 20 | 56.20 | engineering 33.00 + finish 17.60 + board 5.60 |

At quantity 20 the price is lower than at 10 because the 10-piece special
offer no longer applies.

The PCBA totals below are estimates, not live quotes. Each one is the PCB price
plus fixed fees of about 131.59 (setup, stencil and Extended feeders) plus
about 19.27 per assembled board (components 16.83, SMT 0.69, X-ray 1.65,
packaging 0.10). Applied to quantity 5, this model gives 276.74, against the
quoted 277.16.

| PCBs / assembled | Total | Per assembled board |
|---|---|---|
| 5 / 2 | ~219 | ~110 |
| 5 / 5 | 277.16 (quoted) | ~55 |
| 10 / 10 | ~388 | ~39 |
| 20 / 20 | ~573 | ~29 |

The quantity-2 estimate may be higher, because of component MOQ and attrition.
Larger quantities may be slightly lower, because of price breaks. Re-quote live
before ordering.

### Owner selection: 10 PCBs, 8 assembled (live quote, November 10)

The owner chose to assemble eight boards. JLC requires at least as many PCBs
as assembled boards, so the order is 10 PCBs with 8 assembled. The same
saved project was re-quoted live with 6 layers, ENIG, epoxy-filled and capped
vias, Standard PCBA, both sides and JLC edge rails. The model estimated $350.

| Item | USD |
|---|---|
| PCB (10 pcs: special offer 47.00 + ENIG 17.70) | 64.70 |
| Setup | 51.50 |
| Stencil | 16.54 |
| Components (41 items) | 130.91 |
| Extended-part feeders | 63.55 |
| SMT assembly | 4.93 |
| X-ray inspection | 13.20 |
| Packaging | 0.51 |
| **Total, before shipping and tax** | **345.84** |

That is about $43 per assembled board, plus about $27 UPS shipping. The BOM
quantities scaled correctly; for example, 16 battery clips for BT1/BT2. No
stock shortage was flagged. Build time: PCB 7-8 days, assembly 3-4 days
(2-3 days costs $49.63 more). Nothing was added to the cart or ordered.

## Live part selections (verify live before ordering)

| References | LCSC | Note |
|---|---|---|
| BT1, BT2 | C6993377 | Extended |
| C1, C4, C5, C19, C20 | C77075 | Extended |
| C2, C3 | C76950 | Extended |
| C6, C7, C9, C12, C13, C14, C16, C18, C23, C24; C30 | C1525 | Basic |
| C8, C10, C11, C15, C17 | C52923 | |
| C21, C22 | C1530 | |
| C25 | C15195 | |
| C26, C27, C28 | C86817 | Extended; 790 in stock |
| CHG0 | C5189028 | |
| D3 | C2128 | |
| D4 | C389354 | |
| FB1, FB2 | C113030 | |
| IC1 | C2040 | RP2040 |
| IC4 | C481766 | LSM6DSOX |
| J1 | C594367 | JST BM02B-ACHLKS-GAN-ETF |
| J2 | C160402 | **substitution**, see below |
| L0 | C5357909 | |
| L1 | C404484 | 131 in stock |
| Q1 | C181091 | |
| Q2, Q4 | C20917 | |
| Q3 | C2987009 | 54 in stock |
| Q5 | C2860700 | |
| 10 k / 1 k / 5.1 k / 22 ohm / 100 k / 4.7 k rows | C25744 / C11702 / C25905 / C25092 / C25741 / C25900 | Basic resistors |
| R23 | C137940 | |
| R25 | C25104 | |
| R26 | C25879 | |
| R27 | C845230 | **substitution**, see below |
| R28, R29 | C137956 | |
| U1 | C2843335 | |
| U2 | C841192 | |
| U3 | C424093 | |
| U4 | C910544 | |
| U5 | C919459 | |
| U6 | C183096 | |
| X6 | C165948 | USB-C; alias question remains in section B |
| Y1 | C20625731 | Extended |

### Substitutions (owner/engineering review before ordering)

- **R27** (protector current-sense, 33 mOhm). BOM part ERJ-6BWFR033V had
  only 7 in stock. Selected C845230 SMF08MAFR033T: 33 mOhm, 0.5 W, 1 %,
  50 ppm/degC, 0805. The value and footprint are the same. The rating is
  equal or better; confirm the TCR is acceptable for the protector trip point.
- **J2** (speaker/aux SH 1.0 mm). The BOM's C18337480 had no stock. Selected
  C160402, SM02B-SRSS-TB(LF)(SN), the same JST part with a different
  plating/packaging suffix.

### Stock risks

L1 (131), Q3 (54) and C86817 (790) have thin stock for repeat builds. JLC
can pre-order parts if they run out. Re-check stock on the order day.

## UI notes for the next session

- The "Parts confirmed" counter read 48 against 44 detected lines, and the
  quote lists 41 priced component items. This looks like a counting/merging
  difference; check that every row is ticked before saving.
- In the placement viewer, scroll to the top first; the first "Next" button
  advances. The canvas zooms with the mouse wheel.
