# Interactive PCBA visualization

This static viewer presents public six-layer PCB snapshot `2f738ccb`. It is
for design exploration only: it is not an assembly drawing, mechanical-fit
check, circuit review, fabrication release, or safety qualification. The
latest six-layer assembly, especially J1's mated plug and wire exit, is not
qualified by this visualization.

The KiCad GLB export emitted a VBUS pad-cutting boolean warning and
self-intersection warnings. These do not prevent visual rendering, but they
are an additional reason not to measure the mesh or treat it as authoritative
manufacturing geometry. See [`manifest.json`](manifest.json) for source and
asset hashes.

The component-side and rear stills remain visible above the interactive view.
The viewer has no automatic motion. Its orbit target is the circular PCB
center at KiCad (100, 100) mm and the board mid-plane (0.79 mm in this export),
or glTF (0.1, 0.00079, 0.1) m. Explicit coordinates avoid the exported model's
origin-inclusive automatic bounds. Panning and tap-to-recenter are disabled;
only rotation and zoom are enabled.

## What is shown

The board and copper come from public snapshot
[`2f738ccb`](https://github.com/dcuccia/digital-handbell/blob/main/hardware/handbell/iterations/printed-bell-six-layer-review/handbell.kicad_pcb).
The 3D models were added to a scratch copy only. The generated GLB contains
77 KiCad-library models on fitted components, the source board's existing
J2 model, and three project proxies from [`proxies/`](proxies/). Generic package models represent package shape, not exact vendor
parts.

- X6 uses the KiCad GCT USB4105-xx-A 16-pin top-mount model as a visual
  stand-in for the board's HRO USB-C connector. Its main pad row was aligned
  to the local X6 footprint; it is not the fitted connector's exact body or
  mating geometry.
- L1 uses the library's 5 mm inductor package model as a stand-in for the
  TDK VLS5045EX.
- BT1/BT2 use [`battery-contact-project-proxy.step`](proxies/battery-contact-project-proxy.step):
  the `ContactMetal_BT1` body from the extended-run FreeCAD assembly,
  translated (-11.625, 0, -26.6) mm to the footprint origin. It is the
  project's kinematic proxy, not vendor CAD or loaded-spring geometry.
- J1 uses [`j1-achl-proxy.step`](proxies/j1-achl-proxy.step), a
  4.2 x 4.4 x 1.2 mm box with a top recess for JST ACHL
  BM02B-ACHLKS-GAN-ETF. No plug or wire is modelled.
- Q3 and Q5 have no body model. Test lands, mounting holes and solder jumpers remain board features.
  DNP C29 is excluded.

Do not use the image to infer connector clearance, component height, battery
contact geometry, enclosure fit, assembly orientation, electrical correctness,
or manufacturability. Use the native board, sourced parts and mechanical
review for those questions.

## Rebuild

Use KiCad 10.0.6's bundled Python and CLI, plus the KiCad 3D model library.
From the repository root, create a scratch board outside the checkout:

```powershell
$kicad = "$env:LOCALAPPDATA\Programs\KiCad\10.0"
$scratch = "$env:TEMP\handbell-3d-preview"
New-Item -ItemType Directory -Force $scratch | Out-Null
& "$kicad\bin\python.exe" docs\3d\build_preview.py `
  --source hardware\handbell\iterations\printed-bell-six-layer-review\handbell.kicad_pcb `
  --output "$scratch\handbell-preview.kicad_pcb" `
  --model-root "$kicad\share\kicad\3dmodels"
& "$kicad\bin\kicad-cli.exe" pcb export glb --force --no-dnp `
  --include-tracks --include-pads --include-zones --include-inner-copper `
  --include-silkscreen --include-soldermask `
  --output "$scratch\handbell-pcba-raw.glb" "$scratch\handbell-preview.kicad_pcb"
npx --yes @gltf-transform/cli optimize "$scratch\handbell-pcba-raw.glb" `
  "$scratch\handbell-pcba.glb" --compress draco --simplify false
```

The published model also attaches the two proxy STEP files above to BT1,
BT2 and J1 in the scratch board (KiCad default offset/rotation/scale) before
export. `build_preview.py` does not yet do this step. The stills use
`kicad-cli pcb render` at 1800x1100, perspective, rotation `305,0,45`
with `--side top` and `--side bottom`.

The final GLB is copied to this directory. The source board, its manifest,
schematic and project remain unchanged. KiCad's 3D library license is
CC BY-SA 4.0 with a design/generated-file exception; see the linked
[license and attribution](https://github.com/dcuccia/digital-handbell/blob/main/ATTRIBUTION.md#license-boundaries).
Draco is used because the meshopt-optimized file failed to load in the tested
viewer, while the Draco file loaded successfully.
