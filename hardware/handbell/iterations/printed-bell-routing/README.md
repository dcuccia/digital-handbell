# Printed bell — partial critical-routing candidate

**September13,2026: actual routed copper, not a functioning or fabrication-ready
board.** This separate native project consumes the parent's explicit mechanical
copper release and preserves the published `printed-bell-front` placement.
Open `handbell.kicad_pro` with **KiCad10.0.6**.

There are **921 track segments,38 through vias and no zones** on the original
two copper layers. Native connectivity proves **59 requested endpoint pairs**,
**14 complete multi-pad nets** and **nine partially connected nets**.
Unconnected items decreased from **222 to148**. Unrouted circuitry still
prevents operation; this is a useful beginning of layout, not a finished circuit.

**The owner-requested high-current review requires rework.** The
[independent review](reports/power-routing-review.md) identifies the boost
output-capacitor hot loop and shared protector-sense routing as corrections
needed before freezing the power layout. It also distinguishes actual load
paths from sense/capacitor branches and avoids treating overlapped traces as
isolated bottlenecks. Preserve this checkpoint as review evidence; it is not
a board to power or fabricate.

## Native review artifacts

| Artifact | Scope |
|---|---|
| [Front copper PDF](reports/front-native.pdf), [front SVG](reports/front-native.svg) | Actual F copper and retained native footprint drawings |
| [Rear-facing PDF](reports/rear-native.pdf), [rear SVG](reports/rear-native.svg) | Actual B copper, contact lands and readable polarity/orientation/chemistry silk; plotted from the cell side |
| [Service-label review](reports/service-label-review.json) | Actual glyph envelopes, B copper/M2 clearance and immutable capture sight-column screen |
| [Schematic PDF](reports/handbell-schematic.pdf), [schematic SVG](reports/schematic-svg/handbell.svg) | Exact unchanged T8 electrical circuit |
| [Placement manifest](placement-manifest.json) | New PCB hash, unchanged geometry and explicit mechanical-rebind requirement |
| [Routing review](reports/routing-review.json) | Full hashes, actual native connected-pad islands, completed endpoint pairs, remaining intents, widths and measured necks |
| [Routing data](routing-data.json), [generation binding](routing-build.json) | Actual track/via coordinates, nets, widths, groups and overwrite protection |
| [Native input bindings](reports/native-input-bindings.json) | KiCad10.0.6 CLI hash, exact native inputs, report hashes and export commands |
| [Mechanical release](mechanical-release.json), [released evidence](released-mechanical-evidence.json) | Parent authorization and exact approved mechanical evidence consumed |
| [Battery interface](battery-contact-interface.json) | Unchanged contact lands and thin metal primitives |

## What is actually connected

- All **six MCU-to-flash endpoints** are connected. Four QSPI data nets and
  QSPI_SCK are complete. The MCU–flash **CS branch** is connected, but the
  CS pullup/recovery branches remain incomplete, so **QSPI_CS is not a complete net**.
- The crystal input/output/series/load-capacitor signal nets are complete.
  Their ground-return branches are connected to the MCU thermal ground bank.
  This is connectivity evidence, not oscillator stability.
- Most local3V3 bypass branches and the VREG input/output connections are
  present. VCORE and multiple capacitor ground returns remain incomplete.
- Q5 retains its real SOURCE1/SOURCE2/gate identifiers. Outside source-pad
  fanouts connect to separate0.6mm B source buses, avoiding the intervening
  F gate pads. **No PCB common-drain pad is invented.**
- The main Q5 source2-to-R27 return now uses a0.6mm F/B path. An earlier
  approximately8.3mm minimum-width main-return attempt was removed rather
  than relabeled as acceptable power routing. R29's fine trace is only its
  high-impedance gate-discharge branch.
- U6 filtered supply, DOUT, V- sense and protected-FET-return nets are
  complete. R26's GND endpoint reaches the **system side R27.2** deliberately.
  COUT, raw-negative/VSS and cell-contact connections remain incomplete.
  Shared-GND geometry and voltage drops still need review; the endpoint
  check does not claim a current-isolated, four-terminal Kelvin measurement.
- The boost SW/inductor, VIN/input-capacitor, output-capacitor and local
  return branches contain real copper. The boost protected return reaches
  R27 via an upper-bank route, **not the narrow B corridor under the MCU**.
  **Feedback wiring remains incomplete; the boost is not operable.**
- Amplifier PVDD/thermal-ground branches and some filtered output branches
  are connected. Its bypass returns, second output path, speaker connector
  completion and dedicated main return remain unfinished.

Complete-net names are recorded individually in the native routing review:
`/PROT_BAT`, `/PROT_DOUT`, `/PROT_FET_RETURN`, `/PROT_VM`, `BOOST_SW`,
`Net-(C3-Pad2)`, `Net-(FB1-P$1)`, `Net-(IC1-XIN)`, `Net-(IC1-XOUT)`,
`QSPI_DATA[0..3]` and `QSPI_SCK`. Single-pad NC nets are **not** counted as
successfully routed nets. No copper-only island without a physical pad is accepted.

## Actual geometry and electrical limitations

This is deterministic, obstacle-checked first-pass routing, not a negotiated
interactive layout or timing-optimized escape. Actual routed endpoint lengths
are intentionally distinct from stage1's straight-line floorplan distances:

| Connection | Routed polyline length |
|---|---:|
| MCU–flash CS | 2.316mm |
| QSPI DATA1 / DATA2 | 8.731 /3.746mm |
| QSPI DATA0 / DATA3 | 11.916 /29.005mm |
| QSPI clock | 17.740mm |
| MCU XIN–crystal | 10.931mm, including two transitions |
| MCU XOUT–series resistor | 2.065mm |

**Those detours require further optimization and signal/return review.**
Neither clock impedance, QSPI timing, USB impedance, oscillator loading nor
an operating frequency has been qualified. Two data nets use B transitions;
this does not establish an uninterrupted ground reference below them.

Routing widths are explicit engineering geometry, not inherited netclass
names used as a current rating:

- **0.1778mm:** inherited minimum-width signal geometry and bounded small-land
  power necks. Maximum recorded endpoint neck is approximately**1.368mm**
  against the1.6mm planning cap.
- **0.6mm:** local power bodies, separate Q5 source buses and local thermal meshes.
- **0.8mm:** the protected boost-return body above the contact row.

At an **assumed35µm copper** and nominal resistivity0.0172Ω·mm²/m, a40mm
long0.8mm trace is approximately24.6mΩ. A hypothetical2A would produce
about49mV drop. This was a working corridor voltage-drop screen, **not a2A
rating**, selected copper weight or thermal/fault analysis. The longest
0.1778mm endpoint neck is approximately3.78mΩ under the same assumptions.
Vias, pad junctions, copper tolerance, heating and current sharing are not
included. Actual individual neck records and trace lengths are in the report;
do not sum a branched-net length table as if it were one series resistor.

### Ground and contact safety constraints

All GND vias and B tracks avoid **both VBAT and CELL_NEG contact lands** and
the retained conductive contact-base projections. They do not rely on solder
mask as qualified contact/cell-can insulation.

The nominal3mm inner-land gap permits only2.6mm GND copper with0.2mm clearance.
The nine MCU thermal vias remain within the checked central safe bank.
Wider power-return B routing is confined outside y±7mm; the central bank is
**not** presented as a qualified boost/amplifier current return.
Local boost/thermal B copper is not a continuous board-wide ground plane.
There are **no pours**, so no unreviewed zone-island or plane-connectivity
claim is hidden in this release.

There are explicit process gates:

- Nine MCU and four amplifier vias lie in thermal pads: filled/capped
  via-in-pad, stencil and assembly treatment require agreement. Do not order
  an unspecified open-via process and assume normal paste behavior.
- The added main-return transition at **(−14.7,+9.55)** is between R27's
  lands, underneath its body, not through a land. Its mask/tenting, physical
  assembly and thermal effect still require review.
- Other transitions are generated off-pad; the original source/library
  geometry and local pad angles are retained exactly.
- Raw cell/contact insulation, fault SOA, loaded contact resistance and
  current/temperature performance are not qualified by DRC.

## Polarity, chemistry and mechanical handoff

B.SilkS now contains **`+ POS`**, **`− NEG`** and **`< T8 BUTTON END`**.
The labels are correctly mirrored for B and the export is a real rear-facing
view. In that view, the positive contact is on the left, hence the **left
arrow** in the readable instruction. The stage1 proposed right-arrow text
was not blindly reused.

The initially proposed polarity positions were obscured by the cradle.
Only these silk marks moved: `+ POS` to **(+15.7,+11)** and `- NEG` to
**(-15.7,+11)**, with 0.9 mm text and 0.15 mm strokes. The orientation
instruction remains at (0,+10.5).

Actual ink/stroke bounds fit the mechanical maximum rectangles, not just the
nominal font sizes:

| Label | Actual glyph width x height | Maximum rectangle |
|---|---:|---:|
| `+ POS` | 4.2643 x1.0500 mm | 4.4 x1.4 mm |
| `- NEG` | 4.2214 x1.0500 mm | 4.4 x1.4 mm |
| `< T8 BUTTON END` | 10.8929 x0.9500 mm | 12 x1.4 mm |

The checker enforces the exact centers and each ink edge inside its rectangle.
The left-pointing arrow is intentional in the readable rear view: it points
to `+ POS`, not to the negative contact. The larger 0.2 mm screening envelope
below is a conservative visibility/edge test, not permission for larger text.

The B service area also carries this readable, mirrored four-line warning:

```text
1S Li-ion
4.2V ONLY
NO PRIMARY
CR123A
```

All four lines use **1.0 mm text / 0.15 mm strokes**, centered at x0 and
y-15.6, -14.0, -12.1 and -10.5 mm respectively. Full-length single-line
alternatives intersected the capture; wrapping avoids shrinking the warning
to fit. The rear PDF shows the actual glyphs, not illustrative overlay text.

The dedicated screen uses KiCad10.0.6 glyph shapes against **all B copper at
0.25 mm clearance**, including masked tracks/vias, and checks the M2 keepouts.
FreeCAD1.1.3 / OpenCascade7.8.1 then checks glyph bounding rectangles enlarged
by 0.2 mm against the exact PCB and 20 mm sight columns above B.
The visibility model is the parent's completed cosmetic revision, SHA-256
`f0dae8f6e5c62fa41f64d16ebe4bbf2f22cd5f65a266f279c2537c6fae2416fc`,
read from commit `4bbdcbb0ee1724b450b66f3a03abcaa8c48333d1`. Its embedded
stage1 PCB, manifest, schematic and contact bytes must match the frozen source.
This separate visibility binding does not replace the original copper-release
authorization at `6e7ef9ef4dd1f6611695e73227630fdc5c8dae7a`.
All seven labels are clear of the corrected cradle, cell, contacts and retained
hardware with the **cartridge outside the shell and the cover/cover screws
removed**. The immutable model is opened read-only in an isolated temporary
copy; no mechanical source is changed. This is a nominal service-view screen,
not proof of printed legibility or permission to use a live cell.

The mechanical consumer must repeat visibility review after the final rebind
and confirm physical legibility in the supported insertion workflow. If the
PCB warning is obscured in that workflow, a visible compartment label repeating
**`1S Li-ion 4.2V ONLY / NO PRIMARY CR123A`** is required instead of relying on
hidden PCB text. A CR123A-size holder can accept a disposable primary cell and
**the charger cannot identify its chemistry**. Neither polarity nor chemistry
labels prevent wrong-cell charging/reversal or provide a safety qualification.

All104 footprints and all325 physical pad records are retained **byte-for-byte
inside the PCB**, including poses, nets, local rotations, mask/paste/drills,
custom copper and source identifiers. D43 body, exact tabs/tongue, two M2
mounts, USB origin/mouth, F25/B26.6, contact geometry and all83 fitted component
proxies remain unchanged. Population is still**81F electronics +2B contacts**;
rear contacts remain real assembly operations.

The new manifest identifies the new PCB bytes while its geometry fields match
stage1 exactly. **Parent must rebind the mechanical artifacts to this final
candidate**, even though only copper and silk changed.

Mechanical authorization is pinned explicitly to commit
**`6e7ef9ef4dd1f6611695e73227630fdc5c8dae7a`**, including its release JSON,
native model, artifact manifest, fit report, completion token and review status.
The router/checker cross-check their hashes and exact stage1 PCB, schematic,
manifest and contact bindings. They no longer inspect the mutable mechanical
root or choose a release from `HEAD`.

The parent's subsequent cosmetic correction closes exposed **shell/cartridge
retaining-joint pockets/lugs**, not PCB M2 mounts, USB, contacts or electronic
poses. This does not waive any electronic-interface equality check or transfer
approval to changed interfaces. `released-mechanical-evidence.json` records the
six immutable objects. Parent will rebind and recheck the corrected final
mechanical artifacts against this candidate.

## Native results

- **0ERC**; exact schematic/netlist correspondence.
- **237 physical DRC findings:** the same four USB hole-clearance errors
  and233 existing silk/text findings. No new shorts, track/pad clearance,
  mask bridges, courtyard/library errors or dangling tracks.
- **148 remaining unconnected items**, independently matching the native
  connectivity engine and DRC.
- **46 identical inherited CLI parity warnings**; no new GUI parity approval.

The checker proves each claimed endpoint connection through KiCad's actual
copper connectivity engine, records all pad islands per net, checks routing
data against actual native track/via geometry and verifies the unchanged
footprints/interfaces. Tiny native-reported grid/neck overshoots are physically
removed; this is not a waiver, and endpoint connectivity is rechecked afterward.

## Reproduce and preserve manual work

From repository root, with existing Python/numpy and KiCad10.0.6:

```powershell
python .\tools\route_printed_bell.py
python .\tools\route_printed_bell.py --finish-return
python .\tools\check_printed_bell_routing.py --run-native
python .\tools\check_printed_bell_routing.py
```

The native connectivity pass loads the matching installed KiCad Python API.
`--run-native` also invokes this package's `screen_service_labels.py` using
the existing FreeCAD1.1 installation and the pinned initial release objects.
Library tables point exclusively to this package's copied local libraries.
No new package installation, external autorouter or manufacturing service is used.

The generator refuses edited candidate/native dependencies and never writes
the stage1 package or mechanics. `--resume` is an engineering reroute operation,
not a substitute for the required widened-return finish and new native check.
Do not run this generator over manual routing; make a deliberate new workflow
and bind the changed inputs instead.

To refresh only committed release provenance, without rewriting the routed
PCB or its manifest, use `python .\tools\route_printed_bell.py --refresh-release`,
then renew this candidate's native reports with the checker. This does not
alter stage1 or any mechanical files.

For the service-label change alone on the existing bound candidate, without
rerouting or changing any other native item:

```powershell
python .\tools\route_printed_bell.py --update-silk
python .\tools\check_printed_bell_routing.py --run-native
```

The silk-only writer refuses manual edits, preserves every non-service-text
native item byte-for-byte, updates the PCB hash in the manifest and records
that equality in `routing-build.json`. The mechanical rebind must use these
new PCB/manifest bytes even though all copper and physical interfaces are
unchanged.

After the parent completes the final mechanical rebind, repeat actual-glyph
visibility against that exact current model:

```powershell
python .\hardware\handbell\iterations\printed-bell-routing\screen_service_labels.py --current-mechanical
```

This first requires a completed, byte-bound mechanical package and rejects a
model still embedding the old stage-1 PCB or manifest. It opens only a temporary
copy, repeats the same geometric screen, verifies that the source evidence did
not change, and writes `reports/service-label-current-mechanical-review.json`.
That separate report records the current native, completion and artifact
bindings without replacing the immutable visibility or copper-release
evidence. It is deliberately not an electrical-manifest input: refreshing a
visibility report must not cause a circular mechanical/electrical rebind.

## Unclosed qualification and attribution

The unchanged MCP73831 profile, absence of cell-temperature charge inhibit/
safety timer, absent reverse-cell electronics, Q5/shunt fault SOA, contact
capture/insulation and component current/thermal limits remain open.
The partial board must not be powered, fabricated or treated as a child-use kit.
No purchase, fabrication submission or new schematic protection is authorized.

Hardware remains **CC BY-SA3.0 Unported**, with complete `LICENSE.txt`,
unchanged Adafruit notices and copied source-evidence records. The5768/4654
sources credit **Limor Fried/Ladyada for Adafruit Industries**;4438 credits
**Bryan Siepert for Adafruit Industries**. Standard KiCad library design
exceptions do not relicense the adapted hardware. Original routing/checking
tools and explanations use MIT. This independent derivative is not endorsed
by the source vendors.
