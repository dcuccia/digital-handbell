# Printed-bell logical four-layer baseline

This package is a **partial migration baseline**, not a routed four-layer
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
