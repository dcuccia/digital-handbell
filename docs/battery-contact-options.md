# Compact-cell PCB contacts and retention

**2026-09-09: sourcing/geometry comparison, not a selected cell or holder.**
The owner favors a low-cost, wire-free battery connection on the handle-facing
side of the PCB, opposite the speaker-facing electronics. Prioritize compact
SMD options while retaining through-hole alternatives. The owner supplied
[Keystone 54 at RS](https://us.rs-online.com/product/keystone-electronics/54/70229904/)
as a through-hole example; a printed cradle and positive capture should carry
the mechanical loads instead of the contact solder joints alone.

## Manufacturer-backed contact shortlist

**Keystone 254 is the SMT counterpart to 54. Keystone 52 is through-hole,
not SMT.** The earless 57/557 family is an alternative for a custom capture
cradle. Each row below uses **two identical contacts, one at each cell end**,
not separately purchased positive/negative contacts.

Dimensions are mm. Contact height is **not installed cell height**; a 16.8 mm
cell cannot become an 11.83 mm-high assembly by using a shorter contact.

| Part / source drawing | Mount and geometry | Relevant drawing dimensions / limits |
|---|---|---|
| [57](https://ken.keyeuro.eu/pdf/57.pdf), rev. D, 2024-07-09; 557 matte-tin variant | SMT, no retaining ears; first earless comparison for an original cradle | Base length 15.57 +/-0.38, width 6.35, contact H11.83 +/-0.38, dimple center 7.23 +/-0.38 above base. Catalog says "No Ears," not a numeric diameter range; nominal 2/3A mounting example exists. |
| [254](https://ken.keyeuro.eu/pdf/254.pdf), rev. C, 2023-09-14 | SMT with retaining ears; direct comparison to the owner's 54 | Drawing specifies 16-19 mm cells; base length 19.88, unloaded transverse envelope 16.61 REF, base width 11.13, H16.59 +/-0.38, dimple center 9.78 +/-0.38. Loaded envelope still needed. |
| [53](https://ken.keyeuro.eu/pdf/53.pdf), rev. C, 2016-10-06; 553 matte-tin variant | Smaller eared SMT option | K75 gives 13.5-16.9 mm diameter: a 16.8 mm cell is near the upper end. Base length 16.81 +/-0.38, unloaded transverse envelope 13.82 REF, base width 9.37, H15.06 +/-0.38, dimple center 9.11 +/-0.38. |
| [52](https://ken.keyeuro.eu/pdf/52.pdf), rev. J, 2025-01-30 | Earless through-hole comparison, not an SMT counterpart | Width 6.35 +/-0.15, H13.34 +/-0.38, dimple center 7.11 +/-0.38, leg projection 3.94 +/-0.38; two 1.78-1.85 diameter holes at 7.62 pitch per contact. No numerical cell-diameter range supplied. |
| [54](https://ken.keyeuro.eu/pdf/54.pdf), rev. E, 2016-09-06 | Through-hole with retaining ears; owner's example | Drawing specifies 16-19 mm cells; H16.59 +/-0.38, base width 11.13, dimple center 9.77, three 3.05-long legs; three 1.83 diameter holes per contact at 5.08 transverse / 7.62 longitudinal pitch. |

The manufacturer-authored sources were retrieved and visually read from its
European archive, including the [2025 K75 battery section, page 13](https://www.keystone-europe.com/wp-content/uploads/2025/08/battery-clips-contacts-holders.pdf#page=13)
and [mounting details, printed pages 39-40](https://www.keystone-europe.com/wp-content/uploads/2025/08/battery-clips-contacts-layout-mounting-details.pdf).
K75 identifies 553/557 as matte-tin variants of 53/57 and lists tape-and-reel
options. Earlier search summaries had wrongly called 52 SMT; use the drawings,
not those summaries or guessed distributor dimensions.

**No numerical current rating, contact-resistance limit, spring-force/travel
curve, or shock/vibration severity rating was found in these retrieved
drawings/catalog pages.** Qualitative low-resistance or vibration claims do not
approve a 2 A handbell application. The lower dimple on 57 especially requires
checking engagement with the exact positive button at the proposed cradle
height, not merely drawing a cylinder above its pads.

### Do not mix contact footprint datums or drawing revisions

For 57, the drawing shows one 3.96 x 5.08 minimum pad and one 3.96 x 2.34 pad,
with 15.57 minimum footprint length. Its pair-spacing datum is 31.2 for the
nominal 2/3A example and 48.23 for AA; these are drawing-specific datums, **not
approved cell-end spacings for our protected 16340**. The 53 drawing uses the
same pad sizes but 16.81 minimum footprint length; K75 lists a 35.1 pair datum
for its nominal 17 x 34.5 mm 2/3A example.

The 254 rev. C drawing uses flat SMT pads, not a PCB-drilled mounting layout.
It specifies a 4.24 minimum longitudinal pad dimension with transverse pad
dimensions 5.20 and 3.30 minimum. Its CR123A "L" value, 3.66 maximum, is the
indicated **inner-pad-edge spacing**, not battery length.
[PCN23-025](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/5555/PCN23-025.pdf)
records replacement of mounting solder legs with solder holes. K75's mounting
page still depicts holes and gives a different 6.9 mm datum for its nominal
2/3A example. Do not combine those revisions/reference cells into one land
pattern; confirm the supplied revision before footprint capture.

For comparison, 54's CR123A inner-hole pair datum is 14.50; K75 lists 17.0 for
52's nominal 2/3A inner-hole datum. A pin pitch or pad-spacing datum is not the
complete clip-pair envelope. No footprint is imported or qualified here.

## Exact battery leads and observed prices

| Product / primary evidence | Disposition |
|---|---|
| [Fenix ARB-L16-700UP](https://www.fenixlighting.com/products/fenix-arb-l16-700up-built-in-usb-rechargeable-battery), specifically **UP**, not U: protected button-top, 700 mAh, 3.6 V, D16.8 x L35.5; manufacturer states 2.5 A maximum discharge / stable output | Strongest exact cylindrical current candidate found. [Torch Direct](https://www.torchdirect.co.uk/fenix-16340-3-6-v-700-mah-high-discharge-usb-protected-rechargeable-li-ion-battery-arb-l16-700up.html) explicitly describes 2.5 A continuous. Longer than the compact geometry example; terminal/button detail, tolerances, transient/protection-trip behavior and allowed terminal-charging conditions remain gates. |
| [KeepPower RCR123A 800 mAh, id635](https://www.keeppower.com.cn/products_detail.php?id=635): protected, maximum D16.8 x L34, 3.7 V nominal / 4.2 V maximum | Compact body example only; no manufacturer continuous-discharge rating retrieved, so >=2 A capability remains unestablished. |
| [KeepPower P1634C 700 mAh, id354](https://www.keeppower.com.cn/products_detail.php?id=354): protected, published D16.7 x L35.7 (+/-0.2), 3.7 V | Longer alternative with no manufacturer CDR retrieved. Do not transfer a different seller/product rating. |
| [LiPol LP502828 500 mAh with PCM](https://www.lipobatteries.net/wp-content/uploads/2021/03/LP502828-500mAh-datasheet-.pdf), drawing FD_2828_70, 2020-05-01: 28 +/-0.5 x 28 +/-1.0 x 5.0 +/-0.3, 50 mm wires, 500 mA maximum continuous | Does not meet the current screen or wire-free arrangement. The separate 2-4.5 A protection-detection threshold is not a discharge rating. This rejects this example, not every high-rate protected pouch. |

[KeepPower P1634C2, id679](https://www.keeppower.com.cn/products_detail.php?id=679)
is deliberately excluded from the ordinary button-top comparison: its
manufacturer describes both positive and negative terminals at the positive
end. It is not a silent replacement for the cells above.

Small-quantity observations retrieved on **2026-09-09**, not a procurement quote:

| Listing | Observed price/availability |
|---|---|
| [Keystone 57, DigiKey UK](https://www.digikey.co.uk/en/products/detail/keystone-electronics/57/2137882) | GBP0.22 each, GBP0.44 for two contacts, excluding VAT; 51,406 listed available |
| [Keystone 254, DigiKey UK](https://www.digikey.co.uk/en/products/detail/keystone-electronics/254/9646025) | GBP0.48 each, GBP0.96 for two contacts, excluding VAT; 14,182 listed available |
| Fenix ARB-L16-700UP, manufacturer listing above | USD7.95, listed in stock; no count |

Contact prices exclude the cell, cradle, fasteners, shipping, tax and PCB
assembly operations. Do not convert a UK retail listing into an assumed US/JLC
assembled cost. Nothing has been purchased or ordered.

## 2026-09-11: Vapcell T8 and PCB-level protection alternative

The owner proposed the
[Liion Wholesale Vapcell T8 button-top offer](https://liionwholesale.com/products/vapcell-t8-16340-rcr123a-3a-button-top-850mah-battery-genuine?variant=31955045056581)
at **USD2.69 each for 100**, an owner-reported quantity price not independently
reproduced from the retrieved page. The seller explicitly lists **Protected:
NO**, 850 mAh typical / 820 mAh minimum, 3.6 V nominal / 4.2 V peak,
3 A manufacturer-rated maximum discharge, and approximate 16.4 x 34.0 mm.

[Vapcell's T8 specification](https://www.vapcelltech.com/h-pd-60.html?fromMid=470)
explicitly describes **3 A maximum continuous discharge**, 4.20 V end of
charge, 2.5 V end of discharge, 500 mA standard CC/CV charge with 100 mA
cutoff, and 1000 mA quick charge. These are manufacturer claims, not project
measurements. The nominal voltage and paper continuous-current rating suit
the current screening target; neither approves the enclosed system.

Two details need clarification before selecting the exact supplied version:

- Vapcell gives 16.4 x 34.0 mm but also says adding a button top can add
  2-3 mm. The retailer describes its button-top item as approximately
  34.0 mm. Obtain the actual maximum total length, button dimensions and
  tolerances; do not silently model it as either 34 or 36-37 mm.
- The manufacturer page gives 100 mA charge termination, while the
  [2020 independent review](https://lygte-info.dk/review/batteries2012/Vapcell%20INR16340%20850mAh%20T8%20(Cyan)%202020%20UK.html)
  quotes 50 mA. Those historical review cells were supplied by Vapcell, and
  the review's favorable conclusion concerns capacity at 1 A or below.
  It does not qualify today's batch at the handbell's load. Confirm the
  applicable charge specification, low-cell sag and temperature behavior.

The integrated USB charger on the earlier Fenix candidate is not needed by
the handbell. An unprotected cell can instead be considered with protection
on the main PCB; this changes where protection lives rather than removing
it. The current design assumed a factory-protected pack and does **not**
already implement that alternative.

### What the current charger and power circuit actually provide

The wing netlist retains `MCP73831T-2ACI/OT`, R8 = 5.1 kohm, the closed
charge-enable jumper, D4/Q3 source selection and Q1/Q2 audio-rail switching.
There is no dedicated cell-protector IC, battery fault-disconnect FET pair,
cell thermistor or qualified reverse-insertion stage. The regulator EN pin
is pulled up; no autonomous cell undervoltage cutoff is established.

| Function | Current implementation / limit |
|---|---|
| Normal charging | MCP73831 CC/CV to nominal 4.20 V, about 196 mA programmed current; preconditioning, termination and automatic recharge |
| Charge-current limit | Applies to the charger path, not cell discharge current into the whole board or a battery short |
| Charger thermal protection | Die-temperature regulation/shutdown; not measurement of cell temperature |
| Input loss / reverse leakage | Charger input UVLO and reverse blocking prevent back-discharge through the charger; neither is cell undervoltage protection or reverse-insertion protection |
| Cell overvoltage fault disconnect | Not separately implemented; normal 4.2 V regulation is not an independent overcharge protector |
| Cell overdischarge cutoff | Not implemented as a battery-protection function |
| Cell discharge overcurrent / short disconnect | Not implemented as a whole-cell protection function |
| Cold/hot-cell charge inhibit | No NTC input on this five-pin charger and no cell-temperature circuit in the draft |
| Charge safety timer | No built-in timeout in this charger |
| Boost local protection | TPS61023 switch-current limit, output OVP/short protection and thermal shutdown; not a whole-cell BMS |

Microchip's [manufacturer-authored MCP73831 datasheet, Adafruit mirror](https://cdn-shop.adafruit.com/datasheets/MCP73831.pdf)
is DS21984A (2005), sections 4.5-4.9, 5.1, 6.1.1.4 and the ordering table.
Its AC option terminates at 7.5% of programmed current: approximately
14.7 mA with the present R8. Although 196 mA is below Vapcell's published
500 mA standard current, the resulting complete charge profile is not the
same as either published T8 termination example. Review the exact current
device/cell specifications before changing R8 or approving charging.

[TI's TPS61023 description](https://www.ti.com/product/TPS61023) specifies
a 3.7 A typical **valley switch-current** limit and 5.7 V **output** OVP.
It can run at input voltages far below the cell's published discharge endpoint.
Neither number is a safe battery discharge-current/undervoltage setting.
Similarly, the USB/battery selector is not a general-purpose BMS.

Adopting the unprotected T8 would require a reviewed single-cell protector
with charge/discharge fault isolation (commonly a protector IC plus
back-to-back MOSFETs, or an integrated equivalent), coordinated thresholds,
delays and fault currents, cell-temperature charging policy, and explicit
reverse-insertion handling. Both charging and discharge paths must respect
the protection stage, without an unintended USB/ground bypass. Independent
retention, insulation and a short-safe battery compartment remain necessary.
Protection on the PCB does not protect a loose cell outside the instrument.

There is no series-cell balancing requirement for this 1S design. A fuel
gauge is optional and cannot substitute for hardware fault protection.
This is a credible cell/architecture candidate, **not approval to insert an
unprotected cell into the current draft**. No new circuit, part selection,
purchase or fit claim is made. Owning epics: E04/#4, E05/#5 and E07/#7.

## What counts as a complete comparison

| Evidence | Why it matters here |
|---|---|
| Exact cell SKU and its maximum diameter/length | Protection boards, button tops and wrappers can exceed nominal 16340 dimensions |
| Installed cell center height and contact/holder outer envelope | The bare cell fits only narrowly in the assumed taper; a low-profile clip can still lift it too far |
| Loaded contact spacing, spring travel and allowed insertion range | The cell must contact reliably without excessive compression or bending the PCB |
| Actual contact/body retention design | A generic metal clip is not automatically both the terminal contact and a complete shaken-cell restraint |
| Current, resistance, plating and temperature data | The system screens cells for >=2 A continuous plus transient margin; contact loss/voltage drop and heating remain separate gates |
| Drawing-based land pattern and mounting process | SMT adds battery-face assembly; through-hole adds tails and soldering clearance toward the speaker |
| Price per contact and quantity per cell, plus assembly | A two-piece contact pair, cradle, hardware and second assembly operation must be compared against a complete holder |
| Controlled sourcing and current availability | One distributor quote is not a production cost or interchangeable substitute approval |

SMD versus through-hole is not a safety or quality ranking. For either type,
review the manufacturer's land pattern, solder-joint loading, board support,
cell-can insulation and mating-cycle requirements. Do not invent a current
rating from the cell size or a supplier's generic "high current" description.

## Geometry remains the limiting comparison

The [measured-speaker study](../mechanical/studies/2026-09-09-measured-speaker/README.md)
retains five battery-body alternatives: a compact 16340 example, the published
Fenix body, nominal 18350 and two flat-pouch placeholders. At a z20 PCB front with 1 mm board-to-cell
standoff, the D16.8 x L34 body has about 0.56 mm shortest distance to the assumed
shell; its uniform 1 mm clearance envelope does not fit. Moving the PCB inward
reduces that margin. This is not an installed-clip result. The Fenix body is 1.5 mm longer and has
slight nominal interference (about 0.21 mm3) in the z20/1 mm-standoff case.
Its current-related advantage must be evaluated against that geometric penalty,
not assigned the smaller KeepPower envelope or rejected for every revised stack.

The flat-pouch placeholders preserve more geometric clearance in this screen,
but no purchasable pack with the necessary current/charge capability has been
qualified. The nominal 18350 screen excludes protection/button-top enlargement
and already interferes in the tested configurations. Keep real protected 16340
and suitably rated flat-pouch options active rather than declaring a winner
from nominal capacity, price or cell-body dimensions alone.

No contact, cradle, carrier, populated electronics or battery combination has
been shown to fit simultaneously. The original X1 wired-battery connector
remains in the unchanged comparison; a committed wire-free design should
replace it, not keep both by default.

Carry **57/557 plus an original captive cradle**, and **254 rev. C plus a
cradle**, as the two primary SMT contact studies. Keep the earless/eared
alternatives distinct and retain a protected-pouch option. This is a shortlist
for loaded-contact CAD and samples, not a selected battery/holder combination.

## Electrical and mechanical adoption gates

The intended rechargeable chemistry is 3.6/3.7 V nominal Li-ion with a 4.2 V
charge limit, subject to the selected cell's complete specification. A
CR123A-shaped compartment must not imply permission to charge disposable
CR123A cells or a different-voltage rechargeable chemistry. Review approved-cell
identification, access control and the system's reverse-insertion protection.
Cell-internal protection does not necessarily protect the instrument against
reversed insertion.

Contacts can connect directly into a reviewed battery-input circuit without
wires. That still requires a schematic/BOM change, contact-bounce/brownout
handling, adequate copper, charging/USB policy and service-pad access. No
existing protection function should be assumed from the keyed JST connector
that a removable contact arrangement would replace.

Use an original printed cradle/cover to distribute insertion and shake loads
through supported attachments. Prevent axial/radial escape without damaging
the wrapper, pinching a pouch or obstructing a cell vent. Solder mask and the
cell wrapper alone are not a qualified abrasion/insulation scheme. PLA fit
prints are not live-cell restraints, temperature-qualified parts or child-use
hardware.

If adopting a third-party printable holder, inspect its actual license and
retain applicable notices before importing its CAD/STL. No third-party holder
geometry is included here. Owning epics: E04/#4, E05/#5 and E07/#7.

The retrieved manufacturer drawings contain proprietary/reproduction notices.
They and their inspection images are retained only as session research aids,
not redistributed or relabeled MIT in this public repository. This document
links to the original sources and records factual dimensional findings.
