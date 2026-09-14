# Sourced boost and audio-filter parts

September 14, 2026. These are selected **prototype quotation candidates**,
not a purchase, assembly or safety approval. The
[machine-readable register](../hardware/handbell/parts/power-component-candidates.json)
records exact source URLs/hashes, dimensions, native changes and limits.
The frozen references and power-routing milestone are not edited.

The selected identities are now applied in the continuing
[clock/integration draft](../hardware/handbell/iterations/printed-bell-clock-draft/README.md#all-fitted-part-identities-applied).
The land/paste changes below remain pending; assigning an MPN did not change
the inherited copper or qualify its solder joints.

| References | Selected exact part | Important source limits |
|---|---|---|
| L1 | TDK **VLS5045EX-1R0N** | 1 uH +/-30%; 19.5 milliohm maximum DCR; manufacturer current figures use separate inductance-drop and temperature-rise criteria |
| C26-C28 | Murata **GRM21BR61C226ME44L** | 22 uF, 16 V, X5R; typical effective capacitance is about 9.96 uF each at 5 V |
| FB1/FB2 | Murata **BLM18SG121TN1D** | 120 ohm at 100 MHz, maximum initial DCR 25 milliohm; impedance falls substantially with current |

The parent directly read TDK's current product page: it lists **Production**,
magnetic shielding, the exact unsuffixed order code, maximum dimensions and
the same recommended lands as the 20160411 manufacturer drawing. This is
not a delivery/stock guarantee. The primary PDF was not retrieved; the older
drawing was viewed through a public mirror. Murata's exact catalog aliases,
versioned specifications and actual characteristic samples were obtained
directly from its public product-data APIs.

## Fit is not the same as an assembly-ready footprint

All six selected maximum bodies fit the existing conservative local envelopes.
Keep L1's full **5 mm** planning height, even though the selected part is
4.5 mm maximum. Do not use this selection to reduce PCB/speaker spacing.

The original lands are comparatively large and have full-pad paste. Their
similar package names do not establish a suitable solder joint for these
specific parts. The new quote candidate receives deliberate, part-specific
land and paste changes:

| Group | New copper land basis | Manufacturing treatment |
|---|---|---|
| L1 | 1.5 x 4.0 mm, centers +/-1.8 mm, gap 2.1 mm | TDK recommended pattern instead of old 2 x 5 mm full-pad paste |
| C26-C28 | 0.7 x 1.3 mm, centers +/-0.95 mm, gap 1.2 mm | Within Murata's reflow recommendation for this +/-0.20 mm body-tolerance group |
| C1/C4/C5/C19/C20 | 0.6 x 1.25 mm, centers +/-0.90 mm, gap 1.2 mm | Separate pattern for the already selected 10 uF GRM21 part's +/-0.10 mm body-tolerance group |
| FB1/FB2 | 0.65 x 1.2 mm copper, centers +/-0.675 mm | Explicit 0.65 x 0.7 mm solder-mask/paste windows, following the wide-copper/narrow-opening mounting arrangement |

The five additional capacitors are tightly coupled to this issue: the parent
confirmed that they have the same old 1.24 x 1.5 mm native pads/full paste as
C26-C28. Their selected values/MPNs do not change. This is not a blanket
replacement of every 0805 or 0603 footprint.

The ferrite manufacturer's 1.2 mm copper dimension is from its 35 um,
3-4 A mounting-reference category. It does not make the route, amplifier or
whole board a 3 A design. Ordinary pad mask/paste must not duplicate the
explicit windows. Preserve component/pad identities and nets; make the
library, schematic and actual board agree.

Changing copper lands also changes electrical geometry. Reconnect actual
traces and vias where necessary, preserve broad power/return approaches,
and remeasure uncovered necks and voltage-drop paths. Keep the short boost
output loops and the R26/R24 independent reference connections; their old
pad-boundary evidence does not automatically apply to smaller lands.
Supplier stencil/profile/assembly acceptance remains open.

## What the component ratings actually mean

**Inductor:** the 8.9 A catalog point is defined by a 30% inductance reduction;
the 5.1 A figure is a typical DC current causing 40 C self-heating. Neither
permits those currents in the enclosed bell. A tolerance-only 0.7 uH,
2.8-to-5 V, 1 MHz typical-frequency example gives 1.76 A peak-to-peak ripple.
At 2 A mean, this means approximately 2.88 A peak and 83 mW cold winding loss.
AC/core loss, hot DCR, bias-dependent inductance and startup/fault behavior
are not included. TPS61023's limit is a valley-current limit, not a guaranteed
peak-current ceiling.

**Capacitors:** ceramic capacitance falls with applied DC voltage. The
manufacturer's 25 C, 0.5 Vrms typical data give 9.96 uF at 5 V and 9.47 uF at
5.25 V for each selected 22 uF part. C26 must include USB-derived input
voltage, not only cell voltage. Temperature, initial tolerance and small
AC-amplitude effects cannot simply be multiplied into a guaranteed joint
minimum.

TI recommends **4-1000 uF effective output capacitance**, not an invented
20 uF hard minimum. Its 10 uF input statement applies to most applications.
Its feedforward-capacitor recommendation above 40 uF needs the complete
connected output network and operating conditions, not just three nameplate
values. **C29 remains DNP.** An ideal 0.75 A/1 MHz example using the two
typical 5 V-biased output capacitors gives about 16.6 mVpp capacitive ripple;
it excludes interconnect, ESR/ESL, control response and audio transients.

**Ferrites:** the selected pair's cold resistance gives about 37.5 mW loss at
the ideal 3 W/4 ohm planning current of 0.866 A RMS. At 1 A DC bias, typical
impedance is only about 14.7 ohm at 100 MHz and 70.2 ohm at 600 MHz. These
curves do not predict the complete switching/audio waveform or emissions.

BLM18SG331TN1D is a recorded, unselected alternative with stronger
high-frequency suppression but greater resistance and a lower catalog
current rating. Its MAX98357 evaluation-board precedent used 680 pF, whereas
this design retains **220 pF C21/C22**. Neither choice validates the complete
filter or proves 3 W of clean audio.

## Remaining handoff

The new routing candidate owns native implementation, actual mask/paste and
connectivity evidence, complete routing and updated current-budget work.
The parent consumes its exact final placement in the complete CAD model.
The [USB correction](usb-connector-qualification.md), remaining device
identities and [quotation process](pcba-quotation-plan.md) remain coordinated
dependencies. No fabrication exports are called quote-ready while these
native/assembly inputs are unfinished.

Manufacturer PDFs, mirrors and curve images are retained only as local
research evidence; the public register records factual parameters and hashes.
Original explanation/register: MIT. Adapted electronics retain CC BY-SA 3.0.
Tracking: E04/#4 electrical, E05/#5 mechanics, E07/#7 routing, E08/#8 quotation.
