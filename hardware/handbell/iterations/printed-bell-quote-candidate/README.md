# Printed-bell routing completion candidate

> **Historical recovery archive, committed September 16, 2026. Not the active
> candidate.** These files preserve the earlier interrupted routing work and
> its intermediate outputs; the historical status and hashes below are not
> current-board approval. Do not run its generators over the active package.
> Continue only after owner resume in
> [`printed-bell-clock-draft`](../printed-bell-clock-draft/README.md).
> The accepted board there has 51 opens at the pause. Existing hardware
> licenses and attribution notices in this archive remain in force.

**Development candidate, not a released quotation package or permission to
power, fabricate or order it.** This separate project continues the accepted
power rework toward the owner's full JLCPCB and PCBWay PCB+PCBA quotation
handoff. Current native connectivity, failures and residual nets are reported
in `reports/completion-review.json` and its Markdown companion; filenames or
an autorouter's completion message are not approval.

The immutable source is `printed-bell-power-rework`, PCB SHA-256
`6132f8d3ec508f8ae023888052cc2a1f8b2c24f2c38d9d12dca3234ba887dcc1`,
manifest SHA-256
`60e394c41bcfd7734b41c7713100360253164381f0217eed325386bd49977799`.
The parent's accepted mechanical model is
`2a923489d72297a27e0bd05760b09d3ed2e19513efced5a6510add9d7b53cb4b`;
that model approves neither the new local moves below nor later USB/part changes.
No old snapshot, source report folder or personal KiCad preferences are copied
or rewritten by the completion generator.

## Delivered bounded result

**Routing is not complete: 59 native unconnected items remain.** This milestone
reduces the source's 155 opens without a source-connected physical-pad-pair
regression. It contains 1,124 tracks, 87 through vias, one F-ground zone with
23 actual filled islands and ten pour-only private-reference exclusions.
Of 86 physical nets, 34 multi-pad nets are complete, 27 remain partial/unrouted,
and 25 are single-pad/NC nets. No B ground pour was added.

The compact cell-positive/Q3/Q1/boost feed, protector gate branches and all six
QSPI connections are real connected copper. The source's all-F output-capacitor
loops and terminal-cut-independent R26/R24 pickups remain intact.
The red F fill is **not a continuous ground return**: protected GND still has
23 disconnected pad islands, including separate MCU thermal/pin19 islands.
The board is non-operable; the MCU core rail, USB, I2S and other controls remain
incomplete. No Gerbers or quote-ready assembly ZIP has been generated.

| Authoritative candidate file | SHA-256 |
|---|---|
| `handbell.kicad_pcb` | `2d88301f48ad05dc01384b90111f16615f176a7f4704eab82a1e3560ef5c8bc0` |
| `placement-manifest.json` | `404a8c53dc0ce28f8769ec4a1926452564cbd3cd5f8c27d95b7ac2ebee1b55de` |
| `handbell.kicad_sch` | `e131a8d093795df7285bcae4a8886ffe01106c6513a19bd588ee7c29c6993b4f` |
| `battery-contact-interface.json` | `f96133d9f044600167477bcddbf67c43311ed0897066db9fa63d8e7f8118467b` |

KiCad 10.0.6 reports zero ERC findings and no new physical copper violations;
the four original USB-hole errors, 46 CLI parity findings and visible
silk/text warnings remain unresolved. Actual PDFs/SVGs, every open physical
pad UUID, exact local-pad proofs and native input bindings are in `reports`.
The seven rear labels remain readable from B, positive on the left and the
button arrow pointing left. Their full mechanical visibility needs rebind.

### Concrete remaining routing blockers

There are 22 required GND island joins and 37 other native joins. `VCORE`
has six islands: IC1.50, IC1.45, IC1.23, C18.2, C6.2 and the C8.1/C7.2 pair.
The regulator's +3V3 island is still separate from the large MCU/flash island;
VHI's C1/U2/R3 island and VBAT's charger/C20 island also remain separate.
USB D+/D-, the I2S triplet, reset/SWD, enable/control branches and the remaining
BTL paths must be completed. The JSON, not this abbreviated list, is exhaustive.

The current local floorplan needs another routing-led revision, not more
blind passes over rounded interchange files. The 0.8 mm USB-VHI passage uses
the MCU's east annulus: its outer edge is X2.7 while the perimeter lands start
at X3.0125. That 0.3125 mm gap cannot hold another 0.1778 mm track with 0.2 mm
clearance on both sides. The QSPI DATA3 detour also separates the VREG_OUT
escape from C6. Behind this area, the positive contact's inner land spans
X1.685..5.685, Y+/-2.54, and its conductive base continues outward over
Y+/-5.565. Foreign B vias/tracks cannot be used as an apparent easy crossover.
Reconsider the USB supply passage and local MCU/flash power fanout together;
do not preserve these particular tracks at the expense of core power/returns.
These are local routing constraints, not evidence that D43 or fixed interfaces
must change. No larger board or interface move is requested by this milestone.

`reports/additive-completion.json` records a bounded additional native-island
search after the local autorouter. It added 13 real island joins; unsuccessful
searches are not treated as proof of physical impossibility. Filled-copper
iteration now requires an explicit guarded new revision/refill, not stale pours.

`reports/power-path-measurements.md` gives actual selected copper walks.
The cell-positive, short VHI and switched-feed walks are approximately
11.6/2.24/7.06 mm, with nominal chosen-strip estimates of 12/2.0/3.1 mOhm.
Their sum is a **positive-side-only** screen, not round-trip resistance.
Very small inscribed-strip minima near annuli/junctions are analyzer walk
geometry, not claims that the PCB has 18 um drawn high-current tracks.
Filled-GND resistance and current redistribution are not modeled, so neither
the 50 mV cell nor 100 mV amplifier round-trip target is demonstrated.

## Physical scope

D43, two copper layers, F25/B26.6, all tabs/outline, M2 mounts, cell/contact/USB
datums and **81 front electronic parts plus two fitted rear SMT contacts**
remain fixed. All 325 physical pad identities/nets and full local pad
primitives/angles are retained. U1 depth remains 2.1 mm and U6 depth 1.55 mm;
L1 remains the full 5 mm proxy with nominal 0.7 mm yoke gap, and D3 remains
0.4 mm. Those are not a complete tolerance, thermal or part-qualification budget.

The additional root-pose changes are fully recorded in
`reports/footprint-movements.json`. Board-relative X,Y and native angles:

| Ref | Source X,Y,angle | New X,Y,angle | Purpose |
|---|---|---|---|
| Q1 | -18.872664,1.307474,0 | -6.4,8,90 | Colocate the switch with Q3/C26, avoiding a long 2 A perimeter detour |
| Q3 | -1.997257,-11.500683,90 | -2.5,7.45,0 | Shorten the cell-positive and VHI path; preserve the corrected custom drain land |
| U6 | -11.502673,7.349061,0 | -10.8,6.6,0 | Expose COUT beyond the Q5 source-via barrier without routing through NC copper |
| C30 | -11.596821,5.551993,0 | -8.9,7.1,270 | Face the adjacent U6 supply/VSS pins without blocking VM |
| R28 | -17.200715,6.750382,90 | -11.6,8.55,0 | Put the bias-only discharge resistor beside the controller rather than across source fanouts |
| R25 | -9.2,8.3,0 | -7.5,5.3,0 | Keep the filter beside its capacitor and clear the switched-power corridor |
| R7 | -2.998764,8.006721,90 | -3,10,0 | Clear Q3 while retaining the control resistor nearby |
| L0 | -5.000460,9.003011,90 | -2,-11.23,0 | Use the vacated selector envelope rather than obstructing compact power |
| U1 | 6.301448,-3.359246,90 | 6.301448,-3.159246,270 | Make all six QSPI signals planar on F despite the B contact lands |
| C10 | 5.294511,-6.217731,90 | 8.6,-2.2,0 | Keep bypass at the relocated flash VCC bank |
| R5 | 7.001181,-6.301464,90 | 6.901181,-6.701464,90 | Clear the CS path while retaining its pullup |
| R9 | 8.105371,0.242334,180 | 8.105371,0.642334,180 | Shift the USB series pair together, preserving spacing and values |
| R10 | 8.109565,-0.959133,180 | 8.109565,-0.559133,180 | Clear the rotated flash courtyard |

No component height, value, pin map or source library is changed. The full
mechanical model must be regenerated from the final exact manifest.

## Routing constraints

The direct all-F U5/C27/C28 positive and ground loops, independent R26-to-R27
and R24-to-C28 ground pickups, paired source escapes and thermal meshes remain
explicit routing constraints. Both raw contact lands and their conductive
base projections exclude foreign B copper and vias. BTL outputs are not GND.
All seven mirrored service/chemistry labels and their clear rectangles remain.

The former under-R27 common-return transition is replaced by a second
off-pad transition at (-16.6,+7.2), alongside (-16.6,+8.1). The short
R29 bias connection joins this local common return rather than its former
long perimeter detour. Parallel vias are not assumed to divide current equally
or constitute demonstrated ampacity.

The COUT connection uses an outside F gate escape and a bias-only B path
between the raw contact base and source bus. It is not a high-current return
corridor. U6 VSS returns to raw CELL_NEG, not protected GND. These connections
still require native checking after each copper revision.

The cell-positive feeder is 1.5 mm B copper, with two off-pad selector-entry
vias, 1.2 mm F landing copper and a bounded 0.6 mm drain escape. The short
VHI link has a bounded 0.3 mm selector escape and 1.0 mm body. The switched
Q1-to-C26 feed is 1.2 mm F copper. The positive feeder deliberately stays
clear of the separate USB-supply exit rather than taking a conflicting
shortest centerline.

The USB-fed VHI branch uses 0.8 mm copper and an F passage **outside** the
unchanged 3.2 mm MCU thermal land. Its off-pad transitions include two
under-package annular locations; assembly/mask treatment remains a process
gate, not a filled/capped-via mandate. This is a supply branch, not a shared
high-current return through the B contact gap. All six QSPI signals are
explicitly routed on F; their lengths and the new return environment need
timing/EMI review, not an assumed high-speed approval.

The local autorouter preserves locked power/local-loop/quiet/source-fanout
copper but may reroute other signal copper. Ground completion is deferred
to the explicit native F fill rather than arbitrary signal-width returns.
Native pad/island/clearance results, actual necks and load-path
measurements take precedence over route-group names and requested widths.
No continuous ground plane or thermal qualification is implied.

Keep the provisional 2 A cell / 3 A sensitivity, 1 A at 5 V, 35 um nominal
foil and 30 um/60 C resistance sensitivity. The 50/100 mV copper-only
round-trip targets are analysis cases, not current ratings. Contacts, FETs,
33 mOhm shunt, inductor losses and IC internals are additional. A selected
strip walk is not equivalent resistance of a branched/filled plane. No
temperature-rise, fault-SOA or safe live-cell result is claimed.

## Reproducible local tools

`route.py` uses an explicit authoritative source list and only used local
footprint libraries. `completion-build.json` protects native inputs against
accidental overwrite. It does not fingerprint ignored PRL files, locks,
caches, an ambient report directory or downstream mechanical artifacts.
Read-only geometry/search helpers are reused without old writer invocation
or module-global monkey-patching.

The generation pipeline below is for an **empty separate candidate package**
at the same iteration-directory depth, initially containing only these local
tools. Edited protected inputs, an existing SES/completion receipt and an
already filled PCB are refused. Do not delete guard receipts to overwrite
the delivered candidate:

```powershell
python .\route.py power
python .\route.py export-dsn
python .\run_local_router.py --java <path-to-java.exe> --jar <path-to-freerouting-1.9.0.jar> --passes 8
python .\route.py import-ses
python .\complete.py --apply
python .\check.py --run-native
python .\fill_ground.py --apply
python .\check.py --run-native
```

For the delivered candidate, rerun only the evidence commands:

```powershell
python .\check.py --run-native
python -B .\measure.py --pcb-sha256 (Get-FileHash .\handbell.kicad_pcb -Algorithm SHA256).Hash
```

Checker exit 2 is the expected honest incomplete/blocked result, not an
invitation to remove its gates. The actual saved native file is authoritative;
external routing and native airwire endpoint selection need not be byte-identical
between runs. Every regenerated result must carry its own exact bindings.

Specctra SES omits fixed wires. The exporter records their **native UUIDs**;
the importer reinstates exactly those original native items, rather than
guessing from rounded DSN coordinates. Re-exporting a rounded routed result
caused Freerouting normalization failures; use the exact generated power seed
for reproducible routing attempts, not accumulating interchange round trips.
The importer verifies the SES against the local-run receipt and removes only
redundant same-net segment centerlines contained in restored fixed copper.
Native endpoint/regression checks still own acceptance.

Freerouting 1.9.0 is an external GPL-licensed local tool, not redistributed
inside this project. Its pinned release JAR SHA-256 is
`9084a4888937a7f31f857ecc12aa7a37407f51160e4d2892dff9c9bb47ae3102`.
Download: https://github.com/freerouting/freerouting/releases/tag/v1.9.0 .
The exercised portable runtime is Temurin 17.0.20.1+1, Windows x64 JRE;
the publisher ZIP checksum is
`bc21a93923103cdaac93ee337b0ae4365e739fde36df823dd456bc67c8a9d352`.
Runtime binary/input/output hashes are recorded by `run_local_router.py`.

Analytics is disabled (`-da`), and process-local HTTP(S) proxies point to
loopback port 9. The resulting blocked version-query exception is visible in
the log; no design is uploaded to a remote routing API or vendor. Each
interchange input is tied to its exact native seed and manifest. An existing
SES output is refused rather than silently overwritten.

Native exports use KiCad 10.0.6 and an isolated default configuration. DRC
stalled with shared runtime configuration on both the accepted source and
candidate; the isolated configuration completes without changing board rules.
The installed standard `power.kicad_sym` dependency is explicitly registered
and hashed with the native tool identity. Custom project libraries remain
package-local exact copies. Logs record executable names, not home paths.

After signal routing, `fill_ground.py --apply` is a guarded one-shot F-only
ground fill. It preserves existing footprints/tracks/vias and protects the
private references with pour-only exclusions. The zone-aware checker uses
actual filled islands and holes, never a zone's unfilled outline. No B fill
or new vias are introduced. Solid ground attachment is an explicit assembly
heat-demand tradeoff, not soldering or thermal qualification.
The linked-hole boundaries are used exactly as saved by KiCad, without
integer-coordinate unfracturing/normalization. Repeated native DRC runs may
choose different representative airwire pairs; actual pad-island partitions,
unconnected counts and physical findings must still agree.

`measure.py --pcb-sha256 <hash>` measures actual nonground copper walks,
overlap-aware necks and conditional barrel drops. With the F fill present,
GND connectivity is checked but its resistance/neck distribution is explicitly
not modeled; whole-loop drop targets cannot be closed by a track-only estimate.

The checker emits fresh ERC/DRC/netlist and front/rear PDF/SVG outputs,
and rejects stale cached inputs or results. Exit 1 indicates failed/stale
checks; exit 2 indicates an incomplete or otherwise blocked candidate.
Only the declared native F-ground fill and its pour-only exclusions are supported.

## Still-required quotation and qualification work

X6 is untouched pending the parent's drawing/mapping correction. Its four
round anchor drills do not reproduce the EAGLE slots, and its four inherited
NPTH-to-copper clearances remain unwaived. Neither the nominal old USB
interface nor an autorouter run approves a replacement land pattern.

The L1/C26-C28/FB1-FB2 manufacturer study, USB review and other sourcing
sidecars are owned separately. Current values/family names do not freeze
orderable parts, dimensions, bias/ripple performance or process capability.
Any resulting footprint/body changes require explicit integration, rerouting
and exact mechanical rebind before final quotation exports.

No Gerber/drill quotation ZIP or supplier BOM/CPL is produced while connections,
parts and manufacturing inputs remain unresolved. Full PCBA must include both
rear contacts, with actual pickup/rotation and assembly process reviewed.
Quote readiness is separate from production, enclosed thermal, charging,
reversal, retention and child-use qualification. No supplier upload, quote
request on the owner's behalf, purchase or order is authorized.

Adapted hardware remains CC BY-SA 3.0 with the exact copied `LICENSE.txt` and
Adafruit notices. Root MIT does not relicense it. Original completion tools
and prose use MIT; external manufacturer documents and routing binaries are
not redistributed here. Parent owns publication and E04/#4, E05/#5, E07/#7
and E08/#8 coordination.
