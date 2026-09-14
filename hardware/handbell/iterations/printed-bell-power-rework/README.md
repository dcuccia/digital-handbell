# Printed bell: critical power-rework milestone

**Non-operable partial routing, not fabrication, current, charging, thermal or
physical-fit approval. Do not power this board.** This separate KiCad 10.0.6
project addresses the two required corrections in the parent's
[independent review](../printed-bell-routing/reports/power-routing-review.md).
It does not overwrite either published electrical checkpoint.

This is an intermediate milestone toward the owner's
[JLCPCB and PCBWay full PCB+PCBA quotation handoff](../../../../docs/pcba-quotation-plan.md),
not the final deliverable. Complete remaining routing, sourced BOM and
manufacturing inputs, then bind the final mechanical model before generating
matched Gerber/drill, supplier-specific BOM/CPL and assembly/process assets.
Both fitted B SMT contacts must remain in the assembly population and cost
scope. Parent coordinates those next stages; this package contains no
quote-ready exports. Open nets and unresolved part/process choices must not
be concealed in a quote ZIP. Quote readiness is separate from production or
live-cell qualification; no vendor upload, order or purchase is authorized.

There are **674 tracks, 35 through vias, no zones, 12 complete multi-pad nets
and 11 partial nets**. All 325 physical pad identities, nets, complete local
pad primitives/angles and libraries remain intact. Native connectivity proves
64 declared endpoint pairs. Unconnected items are **155 versus 148**, with
163 previously connected physical-pad pairs lost; those losses are itemized,
not hidden behind the new power connections.

## Reviewable native evidence

| Artifact | What it contains |
|---|---|
| [Native project](handbell.kicad_pro) / [PCB](handbell.kicad_pcb) / [schematic](handbell.kicad_sch) | Actual two-layer candidate and unchanged circuit |
| [Front PDF](reports/front-native.pdf) / [rear PDF](reports/rear-native.pdf) | Actual native copper and readable rear chemistry/polarity labels |
| [Front SVG](reports/front-native.svg) / [rear SVG](reports/rear-native.svg) | Native vector views |
| [Boost before F](reports/boost-before-front-detail.svg) / [after F](reports/boost-after-front-detail.svg) | Matched-coordinate copper/silk details without the cluttered fabrication-value layer |
| [Boost before B](reports/boost-before-back-detail.svg) / [after B](reports/boost-after-back-detail.svg) | Through-board, non-mirrored companion details |
| [Native review](reports/routing-review.md) / [complete JSON](reports/routing-review.json) | ERC/DRC, actual pad islands, terminal-cut proofs, regressions and final hashes |
| [Power measurements](reports/power-path-measurements.md) / [complete JSON](reports/power-path-measurements.json) | Copper-aware walks, uncovered necks, provisional drop cases and limitations |
| [Pose changes](reports/footprint-movements.json) / [manifest](placement-manifest.json) | Exact transforms/rationales and new mechanical input |
| [Proxy enlargements](reports/proxy-envelope-adjustments.json) | Separate authorized U1/U6 maximum-depth corrections, local-to-board axes and manufacturer evidence |
| [Build binding](routing-build.json) / [native bindings](reports/native-input-bindings.json) | Source/tool/native bytes, commands, original-source guards and report hashes |

## Required corrections implemented

**Boost:** L1 is now behind U5. SW runs underneath the SOT563, not across
the capacitor-facing side. C27/C28 face U5 VOUT and GND; both positive and
ground connections are direct F-side copper, with 0.8 mm buses and bounded
0.30 mm pad exits. Neither local output-capacitor loop requires a via.
The separate load return takes off outside these local loops.

The same sampled native-copper walk method, including pad travel, gives:

| Capacitor loop | Old paired XY / transitions | New paired XY / transitions |
|---|---:|---:|
| C27 | 7.99 mm / 2 | 4.46 mm / 0 |
| C28 | 12.2 mm / 2 | 8.63 mm / 0 |

The simple planar walk areas are approximately 2.81 and 6.56 mm2, respectively.
These are geometric comparisons, not parasitic-inductance or stability results.
They intentionally differ from the earlier review's pad-as-region distances.

**Protector pickup:** R26.2 has a single approximately 1.691 mm direct F
pickoff to R27.2, replacing the former 13.245 mm drawn sense route through
shared returns. Removing only copper joins inside the actual R27.2 land leaves
the sense branch isolated from every other ground pad. Load returns enter
R27.2 from the right; the sense branch enters from below. U6.VSS is deliberately
connected to raw CELL_NEG, never protected GND.

**Feedback:** R23/R24 moved with the boost. R24 has its own reserved reference
to C28's ground land. A separate native terminal-cut check shows no load joins
before that land. The approximately 11.9 mm, two-transition reference is a
quiet-topology improvement, **not a short trace or demonstrated noise immunity**.
FB remains a partial net because the DNP C29 branch is not completed.

**Amplifier and returns:** both U4 supply pins are joined, C16/C19 positive and
ground bypass branches are connected, and a paired 5 V supply/return reaches
the boost bank. The three exposed thermal-pad-to-ground-pin gaps use 0.30 mm
orthogonal exits, approximately 0.35 mm exposed each. Local bypass returns
use off-pad transitions outside the raw-contact base areas, connecting to the
retained thermal mesh rather than an invented continuous ground plane.

The original four outside Q5 source escapes remain. An additional common
PROT_FET_RETURN transition at **(-16.6,+8.1)** is outside SMD lands and joins
R27.1 through a parallel branch. The old under-R27 transition remains too.
This provides parallel copper, not equal current sharing or qualified via
ampacity. Gate pads between source balls are not bridged.

## Exact authorized pose changes

Coordinates are board-relative X,Y in mm followed by the native KiCad angle.
Only root footprint poses change; all local pad geometry/angles stay exact.

| Ref | Previous X,Y,angle | New X,Y,angle | Reason |
|---|---|---|---|
| U5 | -4.198999,16.001796,0 | -2.7,15.2,0 | Face output bank; SW exits underneath toward L1 |
| L1 | 0.478653,15.758568,180 | -7,14.8,0 | Behind converter, outside magnet; full 5 mm height |
| C26 | -4.442651,18.407437,0 | -9.5,10.9,180 | V+ faces inductor input, GND faces protected return |
| C27 | -7.265563,15.705807,270 | 0.1,15.2,270 | Direct all-F first output loop |
| C28 | -9.383487,15.802423,270 | 2.2,15.2,270 | Parallel output bank |
| C29 | -6.603258,12.098491,0 | -5.7,11,0 | Keep DNP reservation clear of moved L1; still DNP |
| R23 | -4.199078,13.802444,180 | -1.8,12.7,180 | Local FB divider/output pickup |
| R24 | -4.197681,12.592618,0 | -2.1,11.4,0 | Separate quiet capacitor-ground reference |
| R25 | -11.599531,9.349843,0 | -9.2,8.3,0 | Remove bias resistor from R27 load-return approach |
| R26 | -14.602592,5.549142,0 | -13.6,11.7,90 | Independent nearby shunt pickup with courtyard clearance |

All unrelated footprints are byte-identical. No circuit/value, USB, contact,
mount, outline, copper-layer count or B electronic-population change is made.

### Authorized maximum body-depth corrections

The September 14 parent BOM-audit follow-up authorizes these two additional
**proxy-only enlargements**, applied in the new manifest after pose transforms:

| Ref | Local width x depth, old -> new (mm) | Manifest rotation | Board-axis expansion |
|---|---|---:|---|
| U1 | 3.1 x 2.0 -> 3.1 x 2.1 | -90 degrees | X, 0.05 mm each edge |
| U6 | 1.9 x 1.5 -> 1.9 x 1.55 | 0 degrees | Y, 0.025 mm each edge |

Winbond UX E=2.0 +/-0.1 mm and TI DSE0006A 4220552/B's 1.55 mm maximum
support these depths; the other local axes already have larger envelopes.
Previously inspected manufacturer-document revisions and hashes are carried
forward in the separate proxy report, not represented as new measurements.
Centres, native poses, heights, pads, nets and libraries are unchanged by
these corrections. The old nominal-depth clearance does **not** cover the
component tolerance. Fresh envelope screening and the parent's exact final
mechanical rebind are required; this is not a complete assembly-tolerance budget.

The preserved draft BOM still has 15/83 fitted rows with an MPN field and
68 blank fields, some with recoverable identities. It is not a sourced turnkey
BOM. L1's 1 uH/TDK_VLC5045 family, the three 22 uF/0805 C26-C28 entries and
generic FB1/FB2 do not freeze orderable parts. Parent-coordinated selection
studies and X6/USB research are separate; X6 remains unchanged here. Any later
part requiring different lands or body geometry needs explicit coordinated
revision before the full quotation handoff.

## Widths, exposed necks and provisional power budgets

The actual input-inductor feed is 1.2 mm; its copper-aware walk is about
3.90 mm. The bias-only C26-to-U5.VIN spur is approximately 8.95 mm at minimum
signal width and **does not carry full inductor current**. Cell-positive body
uses 1.2 mm, VHI uses 1.0 mm with genuine package exits, and raw-negative
body uses 1.0 mm into the existing outside source bus. Boost load return uses
1.2 mm B copper in the upper bank and 0.8 mm F takeoff/terminal connections.
The amplifier distribution bodies use 1.0 mm.

The SW connection has a **0.20 mm under-package section** feeding a 1.2 mm
body. The approximately 0.62 mm space between opposite SOT563 lands cannot
hold a broad trunk plus two unchanged 0.20 mm clearances. The complete narrow
SW inventory is 2.135 mm drawn and **1.21 mm uncovered after pad/broad-copper
coverage**, including the continuation beyond the directly pad-adjacent
segment. Its isolated full-width nominal resistance is about 2.97 mOhm.
This exposed segment is longer than the old review's approximately 0.65 mm:
the corrected topology is not advertised as an improvement of every neck.

Each 0.30 mm output-pin exit is 0.815 mm drawn but only approximately
0.09 mm uncovered after pad/broad-copper overlap. Do not treat the entire
drawn exit as an isolated series bottleneck. The four original Q5 source
escapes are approximately 0.704/0.772 mm each; their pad/annulus overlaps are
reported separately. The broader Q5 pad-adjacent inventory also contains
bias branches and must not all receive a 2 A assignment.

Use the review's **provisional** 2 A cell / 3 A sensitivity, 1 A at 5 V,
35 um nominal foil, and 1.35x 30 um/60 C resistance sensitivity. The unqualified
1 uH/1 MHz, 2.8-to-5 V example is about 1.23 App and 2.6 A peak at 2 A mean.
Neither 60 C nor a <=10 C conductor-rise target is an established operating
limit or measured thermal result.

The selected native-copper walks give approximately:

| Copper-only screen | Nominal / 1.35x drop | Interpretation |
|---|---:|---|
| Cell round trip, <=50 mV at 2 A | Not computed | Q1.3-to-L1 input remains open; target not demonstrated |
| 5 V bulk-capacitor endpoints, 1 A | 42 /56 mV | Numerically below 100 mV for this selected walk only |
| Amplifier supply pin to thermal return, 1 A | 68-69 /92-93 mV | Numerically below 100 mV for these selected walks only |
| Amplifier supply pin to small GND11 return, 1 A | 75-76 /102-103 mV | Sensitivity case exceeds 100 mV for this selected walk |

The analyzer uses finite native-shape contact portals and conservative
inscribed strips, not a least-resistance path or 2-D current solution. Junction
geometry can overstate those strip estimates. Neither a numerical pass nor an
exceedance proves the actual parallel network's equivalent drop. **Neither
whole-system copper budget is declared qualified or closed.**
Contacts, Q3/Q1/Q5, the deliberate 33 mOhm shunt, inductor winding, IC internals
and capacitor ESR are additional and excluded. The shunt alone is nominally
66/99 mV at 2/3 A. Conditional 0.30 mm barrel DCR is about 1.17 mOhm only if
1.6 mm board/25 um wall assumptions hold; plating is not selected.

## Native result and remaining work

ERC is zero. The four original USB hole-clearance findings and 46 CLI parity
findings remain, without rule changes or waivers. There are no new shorts,
copper clearance, mask-bridge, courtyard or dangling-copper findings.
All seven original B labels are unchanged and clear of candidate B copper;
foreign-net B tracks/vias avoid both raw contact lands and conductive base
projections. GND does not use the narrow central B gap as a shared power return.

The **V+ feed from Q1.3 (-18.872664,+0.307474) to C26.1 (-8.55,+10.9) remains
open** after the 1.2 mm body/limited escape search. COUT to Q5 and the R28 DOUT
discharge-gate branch remain open. Broader signal/enable/charger/BTL completion
is still needed. QSPI DATA0/DATA1, VCORE branches and multiple shared GND
branches from the old attempt were displaced or omitted. Native before/after
islands and every regressed pad pair are in the report.
Bounded search failure is not proof that an unapproved Q1 move or larger PCB
is necessary; neither has been applied or claimed necessary.

Thirteen retained thermal-pad vias, the inherited under-R27 transition, new
off-pad transitions and stencil/paste behavior require process/DFM review.
Filled/capped vias are **not mandated** without that review, nor are ordinary
open vias declared qualified. No pours or proven heat spreader are provided.
Inductor saturation/ripple/current, FET/fault SOA, charging profile,
temperature inhibit, reversal/primary-cell misuse, insulation and physical
retention remain unclosed. Labels do not detect chemistry or prevent reversal.

## Mechanical contract and reproduction

D43, F25/B26.6, original tabs/tongue, both M2 holes (+10,+15.7) and
(-10,-15.7), USB origin (0,-22.82)/mouth (0,-27.90), all battery-contact
geometry, nominal cell axis/center and **81F electronics +2B SMT contacts**
are unchanged. L1 remains 5 mm high with nominal z20 bottom and the original
0.7 mm yoke gap. The moved proxies have no overlap or outline/speaker-envelope
violation in the electrical screen; this is **not actual mechanical fit**.
The parent has now regenerated the complete corrected CAD using this exact
manifest: native SHA-256
`2a923489d72297a27e0bd05760b09d3ed2e19513efced5a6510add9d7b53cb4b`,
with no nominal material overlaps and refreshed views. See the
[current complete assembly](../../../../mechanical/studies/2026-09-13-printed-bell/README.md)
and [actual-label service evidence](reports/service-label-current-mechanical-review.json).
The producer's conservative manifest flags do not self-approve fit; the
separate exact consumer evidence records this completed intermediate bind.
Future routing, sourced-part and USB-footprint changes require their own bind.

From repository root, with existing Python/numpy and KiCad 10.0.6:

```powershell
python .\tools\route_printed_bell_power_rework.py
python .\tools\check_printed_bell_power_rework.py --run-native
$pcb = '.\hardware\handbell\iterations\printed-bell-power-rework\handbell.kicad_pcb'
python -B .\tools\analyze_printed_bell_power_paths.py --pcb-sha256 (Get-FileHash $pcb -Algorithm SHA256).Hash
python .\tools\check_printed_bell_power_rework.py
```

The generator refuses edited candidate/native dependencies. It reuses only
the old router's in-memory geometry/search engine and unchanged contact data;
it never monkey-patches module globals or runs the old writer/checker against
the new package. Native-reported sub0.01 mm grid overruns alone may be removed,
with fresh endpoint/native confirmation; larger dead ends fail for repair.
Source fingerprints exclude local `.kicad_prl` preferences, just as they
exclude locks/backups/bytecode. The checker consumes the same source-file set
as the writer; a clean checkout must not require an ignored personal-state file.
Native command records use the executable name, with its actual version and
binary SHA-256 recorded separately, rather than publishing a user-home path.
The shared S-expression parser and source attribute file also retain their
existing working bytes in Git, rather than depending on checkout-time newline
conversion. That publication-only line-ending correction changes no parser
logic or source PCB geometry.

**After each exact mechanical rebind**, run:

```powershell
python .\hardware\handbell\iterations\printed-bell-power-rework\screen_current_mechanical.py
```

This checks all four embedded electrical inputs against this package, then
checks the new copper/labels and actual current-model sight columns. It
refuses the still-stage1-bound f0dae8 model. The separate resulting report is
not an input to the mechanical build, avoiding a circular artifact dependency.

## Source and license boundaries

The source electrical checkpoint was published at
`b63a121b1ca990a64b00f231a85dd715126319af`; source service tooling was refreshed
at `222ddb816c882da5aee476a0d873a4490caf8ce3`. The parent's review is recorded
at `eb9041a6c0d4cd5b43adfb33383449f4a8ada6fc`. All source bindings are preserved.

TI's [SLVAES4](https://www.ti.com/lit/an/slvaes4/slvaes4.pdf), May 2020,
pp3-5, distinguishes wide local output loops from bottom-return/wrong-side-SW
mistakes and explicitly recommends routing SW under the device. Inspected PDF
SHA-256: `d0046c0259fc5b840fb89fdca1837b2f398a7da11e8f73b3a9748972de0fefcc`.
Also retain the review's [TPS61023 section 10.1](https://www.ti.com/lit/ds/symlink/tps61023.pdf)
and [MAX98357 Rev.7 p33](https://cdn-shop.adafruit.com/product-files/3006/MAX98357A-MAX98357B.pdf)
references. These are manufacturer guidance, not project measurements.
Manufacturer PDFs/images are not redistributed.

Adapted hardware remains **CC BY-SA 3.0**, not root MIT. Complete source
libraries, `LICENSE.txt`, original notices and source-evidence records are
copied unchanged. Credit Limor Fried/Ladyada for Adafruit Industries for
5768/4654 and Bryan Siepert for Adafruit Industries for 4438. Standard KiCad
library exceptions do not relicense that hardware. Original tools and prose
use MIT. No vendor endorsement or selected power-component qualification is
implied. Owning epics remain E04/#4, E05/#5 and E07/#7; parent owns publication.
