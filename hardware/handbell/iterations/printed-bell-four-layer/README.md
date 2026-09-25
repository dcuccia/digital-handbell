# Printed-bell four-layer routing baseline

**Current acceptance: eastern MCU ground closure.** Active PCB
`adc262b3e7056cb9031387c55262b5cf99e599ae6e28970f9784f5237e662314`
and manifest
`b849b5defb95f010f555d43b6d261fdea3ef37e240aee0190a607fb519c642f8`
have **37 opens, 234 non-open findings and 46 enabled parity findings**.
One ordinary off-contact via and a short F connection restore the shared
C6/C7/C8/C13/C17 ground island to In1 MAIN, with no placement or existing
copper changes. The [acceptance record](reports/mcu-east-ground-acceptance.json)
binds validation and Astra's filled-layer review. Exact CAD rebinding is
required; the prior completed IMU CAD is preserved, not relabeled as a
match to the new board. VCORE distribution remains unfinished. This is
not powered, PI, manufacturing or safety approval.

**Earlier acceptance: integrated IMU closure.** Active PCB at that checkpoint
`d2a098b0dcd198fb790e6dd4341c036814aabba7fa2ef7c278c79a0a2c916711`
and manifest
`aa68559eebaf8a43c369f549deed1f025d393bafe2d4323d2098fa4712ef622c`
have **38 opens, 234 warnings and 46 enabled schematic-parity findings**.
The [acceptance record](reports/imu-closure-acceptance.json) binds electrical
evidence and the completed full CAD, with an exact lifecycle-only bridge
to its immutable input manifest. IC4/R15 are each shifted north 0.50 mm;
local IMU supply, I2C, ground and INT2-to-TP6 are closed. External
INT-to-IC1.34 remains open. This is an incremental engineering checkpoint,
not fabrication, powered or safety approval.

**Earlier acceptance: C24 ground via.** One centered 0.60/0.30 mm
through-via connects C24.2 to the existing In1 ground plane, without
changing its land, mask, paste, other copper or F/In1 filled geometry.
PCB `c7b6b6fdb9857f7ea993e3cad37c04e852981eceea5146802cadb35865b2cec7`,
manifest `08bf866d80f74775ff4099e4734da0d445fd359843f61637bf453abf002fe667`.
**41 opens**, 233 warnings and 46 historical parity notices remain.
**Mandatory process:** this C24 via requires nonconductive resin fill,
planarization and copper capping, in addition to U4's four required vias.
Tenting is not a substitute; native treatment flags were not added.
Carry the [exact treatment map and acceptance record](reports/c24-filled-via-acceptance.json)
into quotation/fabrication notes. Supplier, stencil, yield and cost
qualification remain open. This is not fabrication or powered approval.
Earlier checkpoints below are historical.

**Separate incomplete IMU working fixture:** the
[archived PCB](reports/imu-fanout-method-staged.kicad_pcb) and
[manifest](reports/imu-fanout-method-staged-manifest.json) preserve an
unfilled, deliberately disconnected local rework with IC4 moved north
0.50 mm and one replacement SCL escape. They are **not the current accepted
board or a self-contained fabrication package**. The
[source-invariant qualification](reports/imu-fanout-method-validation.json)
does not qualify full routing, DRC, powered behavior or mechanical fit.
Continue only through the [current closure handoff](../../../../docs/pcb-closure-plan.md#owner-pause-and-next-item).

The subsequent [working PCB](reports/imu-coupled-working.kicad_pcb) and
[working manifest](reports/imu-coupled-working-manifest.json) now contain
the [complete local primitive block](reports/imu-signal-layer-correction.json):
local supply, SCL, SDA, INT2-to-TP6 and an INT local exit are connected.
At that primitive checkpoint, ground straps reached C23.2/local via but
MAIN-plane attachment had not yet been proved.
IC4 and R15 are each shifted north 0.50 mm in this working candidate.
Ordinary-via off-pad checks pass without a new via-in-pad dependency.
Their native
[front](reports/imu-working-front.png)/[inner](reports/imu-working-inner.png)
views are source-bound, not complete group/plane or source/DRC qualification.
Full electrical and mechanical acceptance gates remain open, along with
the external INT-to-MCU connection. The earlier
[failed signal screen](reports/imu-signal-closure.json) is historical;
the corrected plan was applied after explicit September 24 resumption.
Follow the [current handoff](../../../../docs/pcb-closure-plan.md#owner-pause-and-next-item).
Earlier working versions/reports are historical; the handoff records the
precise current evidence limits and remaining replacement duties.

**Separate filled recovery candidate, not promoted:** the
[filled PCB](reports/imu-electrical-filled.kicad_pcb) (`79a1dee3...`) and
[matching manifest](reports/imu-electrical-filled-manifest.json)
(`eb37d87f...`) have **38 opens**, 236 warnings, no non-open DRC errors,
and unchanged 46 parity notices. Existing connected pad groups and both
private protection-sense paths are preserved. The
[corrected ground review](reports/imu-ground-anchor-review.json) proves
all five IC4 ground pads and C23.2 reach the actual In1 GND island;
`/CELL_NEG` remains isolated. The earlier diagnostic failure used +3V3
IC1.49 as a ground reference and is superseded, not a repair obligation.
The three new dangling warnings are the intentional INT exit and two
preserved exterior stubs; none has been suppressed or trimmed.
Later source/process/geometry and CAD evidence supersede that stage's
pending gates. These historical recovery files are not quotation or
fabrication assets.

**Cleaned IMU candidate, electrical and CAD checks complete:** the
[cleanup PCB](reports/imu-cleanup-staged.kicad_pcb) (`d2a098b0...`) and
[manifest](reports/imu-cleanup-staged-manifest.json) (`62ea87d6...`)
remove only the two proved obsolete terminal branches. The
[final saved-board report](reports/imu-cleanup-final-validation.json)
confirms **38 opens, 234 warnings and 46 enabled parity findings**,
preserved connected groups/protected returns, and cleared fill/geometry
gates. The intentional unfinished INT exit remains. The earlier API and
unchecked-parity reports are historical, not remaining repair obligations.
The [completed CAD run](reports/imu-cad-extended-run.json) includes the
exact placement and approved USB skin adjustment, with preserved source
snapshot `443fe1b5...`. The exact cleaned PCB now replaces the accepted electrical package through
the lifecycle-metadata binding record above. The staged manifests remain
immutable historical evidence. It is not fabrication-ready.

**Earlier acceptance: paired C12 supply/ground closure.** A shorter feed
from the existing In2 +3V3 bridge replaces only the upstream F supply
segment, preserving the local capacitor-to-MCU wiring. One ordinary
through-via is added; native refill connects C12 ground.
PCB `834086079bc792165adcf642d41f3fd52c65446a355904934fcdf39b289227eb`,
manifest `054f203553f7051e12f098acac9683539488e77e4a42266439b48c519dbf39dd`.
**42 opens**, 233 warnings and 46 historical parity notices remain.
The protected In1 plane remains connected with the reviewed local
power-via antipad. No components moved; C24 remains unresolved.
See [acceptance and evidence reuse](reports/c12-paired-feed-acceptance.json).
Full electrical, thermal, mechanical and manufacturing qualification
remain open. Descriptions below are preserved historical checkpoints.

**Earlier acceptance: C23 ground closure.** Five local USBBOOT F segments
are replaced by two 0.20 mm In2 segments between existing vias, freeing
the front ground fill to connect C23. No parts moved or vias were added.
PCB `01a943c795ba97246c9681ad64088dfeb68ca94008cc9f08081d4c4f90789b00`,
manifest `d69d1ae6267eafe5976e528fd47d30cbed81ff01df058dbceca9d9c6cdc49b8c`.
**43 opens**, 233 warnings and 46 historical parity notices remain.
The In1 plane is unchanged; the five remote F comparison components pass
the reviewed native displacement and clearance bounds. The actual board
graph preserves prior connections and private pickoffs without shorts or
floating copper. C12 and C24 remain unresolved.
See [acceptance and evidence reuse](reports/c23-usbboot-acceptance.json).
This is not full electrical, thermal, mechanical or manufacturing approval.
Descriptions below are preserved historical checkpoints.

**Earlier September 22 radial acceptance:** the radial ground batch adds three
off-pad through-vias and short F stubs, joining C4, shared C11/C15 and U2.
PCB `7927882fa05f05411c6bf9e12782326f55572aa0b450cc2e26e9ea534ab3add7`,
manifest `a7a04cc74f0b487beda240c9b868dec54afbe32cd60fa003ec9e6578bc8717e7`.
**44 opens** and 233 warnings remain, with 46 historical parity notices.
Plane fills and prior copper are unchanged; local high-frequency, current,
thermal and manufacturing qualification remain open. C12, C23 and C24
remain unresolved within the finite screen.
See [radial-batch acceptance](reports/supply-ground-radial-acceptance.json).

**Earlier September 22 stitch acceptance:** an off-pad GND via and 0.65 mm F stub
at R4 connect the existing C9/R4/R8 group to main ground. The accepted PCB is
`453b9f6da227cc3ce4fe0a664e4d0e05d159a6cbe41b00c72d2b009e1c3ffe43`,
manifest `1bf38f7a9e6f9a1b086844a6309103f8935ecfcb8ef142bed7ccc0acc473ec2a`.
There are **47 opens**, 233 warnings and 46 historical parity notices.
F/In1 fill geometry is unchanged, all previous connected groups and private
pickoffs survive, and the remaining VCORE/ground connections are unfinished.
See [ground-stitch acceptance](reports/supply-ground-stitch-acceptance.json).
This is group-level connectivity, not C9 local high-frequency qualification.

**Earlier September 22 supply acceptance:** the +3V3 bridge adds three In2 segments
between existing vias, without changing placement, prior routes or plane
fills. PCB `5dc0ebe6b75a2325826460ece80d3f1b2cb45bc1af8341baa79358d85e3136d8`,
manifest `cdff8e0501a015039bc10c9b01a8f92dfde1a3edc2b7247914952d971073df41`.
There are **48 opens**, 233 warnings and 46 historical parity notices.
See the [bridge acceptance](reports/in2-3v3-bridge-acceptance.json).
Sixteen ground and two VCORE opens remain; this is not a powered-ready board.

**Earlier September 22 plane acceptance:** the first protected In1 ground plane is
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
