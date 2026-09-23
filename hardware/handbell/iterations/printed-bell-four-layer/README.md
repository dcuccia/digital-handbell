# Printed-bell four-layer routing baseline

**September 22 current acceptance:** the first protected In1 ground plane is
promoted byte-for-byte from the saved candidate. The PCB is
`19d3bf9a1ab37dcc7af29f0cc99cc44a98564f878402beee15af3ce0a731ff78`;
manifest `ce915418d33442f6ab42b155f6a7bc95c05e6c7032574d58044963ca4d066741`.
There are **49 opens**, 233 warnings and 46 historical parity notices still
to disposition. All existing connected groups and both private returns are
preserved; component geometry and existing routing primitives are unchanged.
See [acceptance and exact evidence reuse](reports/in1-plane-acceptance.json).
Full CAD source binding, physical stackup and final engineering/manufacturing
qualification remain open. Earlier migration/staging descriptions below are
historical, not the current inner-copper state.

This package began as a **partial migration baseline**, not a routed four-layer
design, physical stackup qualification, fabrication release, or quotation
package. It was created from the exact accepted sibling
`../printed-bell-clock-draft` PCB
`a83cc417c96b05dd15c187e648b9fd2a35ba857c3a66f7d13aaaa42ae3bd9fff`.
That source package remains unchanged.
The repository pins this package's line endings with `-text` attributes so
its authoritative file hashes survive checkout on different platforms.
Inherited native/library formatting is intentionally preserved.

## Authorized logical layer reservation

- `F.Cu`: short critical routes and fitted parts.
- `In1.Cu`: reserved for a protected GND plane.
- `In2.Cu`: reserved for power and released lower-speed routing.
- `B.Cu`: battery contacts and constrained routes.

These are policy reservations only. No inner-layer plane, zone, trace, via,
or fill was added. Existing F/B copper, filled-zone caches, placement, nets,
pads, rules, outline, masks, paste, courtyards, zones, exclusions, and
through-via endpoints were not edited. Existing through vias now have native
`*.Cu` padstacks on all four enabled copper layers, so KiCad exposes inner
annuli; there is still no filled inner copper.

Nominal total board thickness remains 1.6 mm. Dielectric materials,
individual copper/dielectric thicknesses, impedance, and a
supplier-qualified physical stackup are pending.

The native KiCad 10.0.6 DRC result is
[`reports/four-layer-baseline-drc.json`](reports/four-layer-baseline-drc.json):
51 unconnected items, zero other errors, and 233 warnings, unchanged from the
accepted source counts. The compact migration evidence and tooling gate are in
[`reports/four-layer-baseline.json`](reports/four-layer-baseline.json).
The new invocation also enabled schematic parity and records 46 notices;
the historical comparison did not enable that check. These notices are
not covered by the unchanged geometry/error counts and require disposition
before release.

Historical source proofs remain in the source sibling and are not fresh
four-layer routing proof:

- `../printed-bell-clock-draft/reports/charge-led-routing.json`
- `../printed-bell-clock-draft/reports/charge-led-routing-drc.json`
- `../printed-bell-clock-draft/reports/charge-led-routing-ground-check.json`

The [saved-native graph control](reports/four-layer-graph-saved-native-control.json)
now exercises inner-layer short reporting, through-via annuli, exact filled
In1 connectivity and same-net In2 isolation. The failed earlier controls
remain historical evidence, not the current graph result.

Production plane topology, contact/private-return exclusions and engineering
acceptance are still required before adding copper. The old F/B routing
masks/search remain unqualified for inner routes. A native plane operation
using qualified graph checks does not require that unused search engine.

The [first staged production-plane result](reports/in1-plane-first-stage.json)
is rejected: a previously connected GND pad group split despite the native
open count decreasing to 50. No candidate copper is promoted into this
package. The saved candidate requires exact regression diagnosis and the
remaining per-layer acceptance gates before another engineering decision.

**September 21 end-of-day pause:** the subsequent
[explicit-settings replay](reports/in1-plane-settings-replay.json) preserves
the original connections and has 49 opens. Its
[supplementary review evidence](reports/in1-plane-review-supplement.json)
and [saved candidate archive](reports/staged-in1-settings-replay.zip) are
preserved separately; the top-level PCB/manifest are still the accepted
51-open migration baseline. The archive is not a quotation/fabrication
package and must not be extracted over this package. Root return-path review
and promotion remain unfinished. Resume only on explicit owner request.
