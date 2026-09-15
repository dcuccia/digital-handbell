# Routing automation: exercised tools and lessons

September 15, 2026. The owner authorizes bounded tooling/autorouting trials
and requests that their lessons remain in the repository. This is not
authorization for cloud routing, supplier uploads or automatic acceptance.

## Current conclusion

**Native KiCad API analysis is established; Freerouting integration remains
experimental.** Keep using exact geometry and connectivity, with images as
an explanatory aid. The remaining automation gap is generating constrained
route alternatives, not reading the board.

Do not replace the accepted PCB with a whole imported SES board. The
no-routing control changes existing geometry even without routing. That is
not proof of a functional defect, but it creates unnecessary source, layout
and artifact-rebinding work.

The accepted PCB remains `f26b8c6`, SHA-256
`57ae2c0b54e1313fb175ccdecdee07ebda07abed5151e776c9767511135d440f`,
with 52 opens. **No routing proposal from this pilot was promoted.**

## What has worked

| Technique | Evidence and lesson |
|---|---|
| Query complete relevant nets and obstacles through `pcbnew` before planning | The complete VHI chain exposed its existing layer transitions and the MCU ground grid. Inspect all obstacle classes, not just the first visible conflicting trace. |
| Numerically screen a bounded candidate batch | Three via-array layouts were screened for the VHI/C8 corridor; the accepted layout retained nine vias and feed widths. This was a geometry pre-screen, not a general autorouter. |
| Read actual courtyards before moving parts | The C6 proxy-envelope screen passed while native courtyards overlapped. Proxy envelopes, native courtyards and physical qualification are different constraints. |
| Reuse source-bound native and independent checks | `check_front_ground.py` preserves previous groups and private returns and can require named new connections. Refill only staged candidates; retain the original source text outside accepted edits. |
| Compare against a no-routing control | It separates exchange-induced coordinate/segmentation changes from actual routing work. Do not count those changes as progress. |
| Stop processes with explicit deadlines | The external 60-second deadlines terminated unfinished engine runs. Pass limits alone are not wall-clock limits. |

## Freerouting pilot

Versions and verified download digests are in
[`freerouting-toolchain.json`](../tools/experiments/freerouting-toolchain.json).
The official Freerouting 2.4.1 JAR and portable Temurin 25 runtime were
downloaded and verified locally. Neither binaries nor upstream source are
vendored. No system-wide Java installation or PATH change was made.

The requested routing scope was one GAIN net, F only, no new vias, existing
wires/vias protected, fanout and optimization off, one routing pass, and a
60-second external deadline. Analytics and API/MCP servers were explicitly
disabled. No public routing service was used.

| Case | Engine wall time | Outcome |
|---|---:|---|
| Legacy short flags, intended no-route control | 60.171 s | Timed out; routing was active |
| Legacy short flags, requested GAIN route | 60.156 s | Timed out |
| Explicit routing-off control | 6.329 s | Completed SES exchange |
| Explicit settings, requested GAIN route | 60.203 s | Timed out |
| Bundled v19 engine, explicit settings, requested GAIN route | 60.094 s | Timed out |
| Persisted safe-default routing-off control | 5.500 s | Completed; repeated the same geometry-difference counts |

Elapsed times include engine startup and termination overhead. Some cases
ran concurrently with independent controls; these are observations, not
isolated performance benchmarks. No completed routed GAIN session was
obtained, so **the requested routing restrictions are not yet qualified**.
Do not interpret the engine's reported 176 unrouted items as our native
52-open baseline.
The DSN loads also reported eight warnings whose individual dispositions
were not established in this pilot.

### Settings trap: do not rely on `-inc`

At the pinned revision, legacy `GlobalSettings` parses `-inc`, but the
headless `CliSettings.mapFlagToProperty()` maps only `mp` and `mt`. The
headless job uses the merged settings path. Use explicit long settings,
and verify behavior rather than assuming the documented short form works:

```text
--router.ignore_net_classes=kicad_default,power,thickpower
--router.enabled=false
```

The second line is for a **no-routing control**, not a routing job. The
persisted harness now always uses explicit settings and returns a nonzero
exit status on timeout, engine failure or missing session output.

Sources: pinned [CLI documentation](https://github.com/freerouting/freerouting/blob/ae3d377740b6ffa744bed1bab26625fe0278fa90/docs/command_line_arguments.md),
[CliSettings](https://github.com/freerouting/freerouting/blob/ae3d377740b6ffa744bed1bab26625fe0278fa90/src/main/java/app/freerouting/settings/sources/CliSettings.java),
and [headless job setup](https://github.com/freerouting/freerouting/blob/ae3d377740b6ffa744bed1bab26625fe0278fa90/src/main/java/app/freerouting/Freerouting.java).
The remaining routing timeout cause was **not established**; do not
attribute it conclusively to the filter or algorithm.

### Exchange is a proposal interface, not our source of truth

The no-routing control:

- Translated 78 footprints by up to **0.0000664831 mm** (about 0.0665 micrometers);
  no footprint orientations changed.
- Removed 309 and added 292 exact track/via geometry records in a multiset
  comparison. Rounding and segmentation changes are not newly routed work.
- Retained 52 native unconnected items and produced zero native DRC errors.
  This was not a refilled, independently qualified replacement board.

The tiny translations are not presented as fabrication-significant defects.
They demonstrate why importing the entire board needlessly changes already
reviewed source geometry. Any integration should transfer **only new
authorized copper** onto the original board, then apply our normal gates.

Other export findings:

- DSN declares 0.1-micrometer coordinate resolution.
- It emits a 50-micrometer SMD-to-SMD exception; the pilot raises that to the
  project's 200-micrometer floor.
- The GND zone is exported as an outline plane, not our proven filled
  connectivity. The pilot removes that plane and defers real fill to KiCad.
- Pour-only exclusions become conservative routing keepouts in DSN.
- Exported class widths are not substitutes for the manually designed power
  paths: `power` is 0.1778 mm, while existing power paths may be much wider.
- The conductive battery bases are separate model constraints, not ordinary
  native copper. The F-only/no-via pilot does not qualify their representation
  for unrestricted routing.

## Reproduction and next bounded step

[`freerouting_pilot.py`](../tools/experiments/freerouting_pilot.py) requires the
pinned PCB and JAR, a new output directory, and explicit local tool paths:

```powershell
python -c "import subprocess; subprocess.run(['python', r'tools\experiments\freerouting_pilot.py', '--java', r'C:\local-tools\temurin\bin\java.exe', '--jar', r'C:\local-tools\freerouting-2.4.1.jar', '--output', r'C:\pilot-output\control', '--no-routing'], check=True, timeout=110)"
```

Replace the example tool/output paths with the verified local paths. Omitting
`--no-routing` requests the GAIN experiment; `--legacy-engine` requests the
bundled v19 algorithm. The returned PCB is disposable and never auto-promoted.
Compact source-bound results are in
[`routing-tool-pilot.json`](measurements/2026-09-15-routing-tool-pilot.json).

**Next investment:** a reduced, one-net geometric problem and additions-only
transfer, rather than more blind whole-board runs or debugging the entire
upstream router. Enforce scope in the problem itself, retain fixed copper and
custom exclusions, and reject proposals that alter other nets or violate the
native/filled checks. Demonstrate one useful proposal within a fresh bounded
item before expanding scope. No savings or routing-completion guarantee is
claimed yet.
