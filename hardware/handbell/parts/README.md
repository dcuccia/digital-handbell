# Sourced part candidates

This separate register supplies **manufacturer-verified prototype candidates**,
not a complete supplier upload or authority to purchase. It leaves the frozen
schematics, BOMs, footprints and placement packages unchanged.

`standard-passive-candidates.json` covers **53 fitted references**: 26
non-boost capacitors and 27 ordinary resistors. It provides identities for
48 previously blank MPN rows and confirms five already specified rows.
C26-C28, the power inductor/beads, shunt and remaining device/connector
selections are outside this register.

The choices preserve existing nominal capacitance/resistance and specified
minimum voltage. They prefer consistent Murata/Yageo families, including the
already recorded C30/R25/R26/R28/R29 identities. Application/land/paste/
supplier review remains explicit; importing this list must not be mistaken
for closing the whole [quotation handoff](../../../docs/pcba-quotation-plan.md).

`hro-usb-candidate.json` separately identifies **HRO TYPE-C-31-M-12 / C165948**
for X6. It records the visually read 2020-12-08 drawing, derived datums and
explicit project DFM deviations for the new quote candidate. Its current
1.4 mm front-slot recommendation differs from the old source; true plated
slots, larger annular rings, four shifted power/ground lands and matching
paste are required. It also adds the previously absent mouth-position
component tolerance to the mechanical handoff. This is not an exact
manufacturer footprint, an implemented native change or supplier approval;
see [the USB qualification record](../../../docs/usb-connector-qualification.md).

`power-component-candidates.json` selects the six L1/C26-C28/FB1-FB2 prototype
candidates and records their current/bias data and required native land/paste
changes. It also covers the closely coupled land treatment for the five
already selected 10 uF capacitors sharing the oversized source pattern.
No larger body envelope is required for these six parts; keep the conservative
heights. See [power-component selection](../../../docs/power-component-selection.md).

## Direct source evidence

On September 14, 2026, the actual manufacturer product pages, their public
catalog responses and linked specifications were read. The JSON records
response/document SHA-256 values. Raw responses and manufacturer PDFs were
kept as local research evidence, not redistributed as project-owned material.

For Murata, open
`https://pim.murata.com/en-global/pim/details/?partNum=<MPN>`.
Its browser uses the public read-only search endpoint
`https://pimapi.murata.com/public/api/pim/v1/products/search`, with this
observed POST query:

```json
{
  "searchCondClass": 3,
  "partNum": "<MPN>",
  "page": 1,
  "pageSize": 20,
  "productCategoryId": "ceramicCapacitorSMD",
  "languageRegion": "en-global",
  "series": "",
  "sortKey": "",
  "valSearchCondList": [],
  "rangeValSearchCondList": [],
  "dateRangeSearchCondList": []
}
```

Require a unique result whose `partNumWithPackageCode` contains the exact
orderable, not merely a similarly named family. Specifications and versioned
PDF links are in `productSearchResult[0].itemInfoList`. Use the full dimensional
display including tolerance: some API numeric `thicknessMax.value` fields
still contain the nominal number despite a larger displayed maximum.
Some `capacitanceTolerance.value` fields likewise contain nominal capacitance,
not tolerance; use the explicit tolerance display and the linked specification.

For Yageo, open `https://yageogroup.com/products/Resistors/part/<MPN>`.
The observed public GET
`https://yageogroup.com/search/unique-parts/<MPN>?displayArea=COMPONENT_EDGE_PART_DETAIL`
provides exact identity, resistance, tolerance, power and package. The linked
RC_L specification is **V.14, November 14, 2025**; pages 4, 5 and 7 define
dimensions, ratings/TCR and derating.

## Important distinctions

| Quantity | Verified manufacturer basis |
|---|---|
| Murata 0805 maximum body | 2.1 x 1.35 x 1.35 mm, not the 2.0 x 1.25 x 1.25 mm nominal size |
| Murata 0402 maximum body | 1.05 x 0.55 x 0.55 mm, not 1.0 x 0.5 x 0.5 mm |
| Yageo 0402 maximum body | 1.05 x 0.55 x 0.40 mm |
| R23 orderable | RC0402FR-07732KL is **732 kohm**, not 73.2 kohm |
| Selected Yageo TCR | V.14 specifies +/-100 ppm/C for the selected 1/16 W values above 10 ohm through 10 Mohm, including 5.1 Mohm |
| Resistor voltage | Limited by both 50 V maximum working voltage and the derated power/resistance relationship |

Search summaries had incorrectly reported some nominal dimensions as maxima,
misread 732 kohm and assigned a different high-resistance TCR range. Those
claims were discarded in favor of direct manufacturer records.

These passive body limits are manufacturer data, not project measurements or
a qualified mounted-assembly envelope. Their existing conservative proxies
are retained; the separate USB register explicitly requires a larger front bound.
Part-specific DC-bias and circuit behavior, final supplier codes, placement/
paste and assembly processes remain to be resolved in the complete handoff.
The manufacturer catalog's production indication is not a stock promise.

Original register and explanations: MIT. Adapted electronics and their
exports retain the hardware attribution/license scope in `ATTRIBUTION.md`.
