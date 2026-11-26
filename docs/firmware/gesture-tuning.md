# Gesture detection and tuning

[Firmware guide](../../firmware/README.md) · [Architecture](architecture.md#hgp-alignment) · [Motion sensing](../motion-sensing.md)

## What is detected today

| Gesture | Source | Status |
|---|---|---|
| `ring` | Gyroscope stroke: an abrupt stop after a fast rotation | Implemented; S1 phone defaults, **untuned on the bell** |
| `damp` | J2 button press while sounding | Implemented |
| `damp` | Acceleration impact shortly after a ring (chest stop) | Experimental, **off by default** (`"damp": {"enabled": true}`) |
| `ring` (key) | J2 press in accessible mode | Implemented |
| `lv`, `shake`, `martellato` | - | Reserved in HGP; not implemented |

A pose or impact alone does not prove chest contact
([motion sensing](../motion-sensing.md)). Treat the experimental damp
detector as a data-collection aid until traces justify it.

## How the ring detector works

Ported from Go Go HarmoniYo's S1 phone spike, with the same parameter
names in snake_case and the same units. The signal is angular speed in
deg/s: `|ω|`, or `ω·axis` once a forward-stroke axis is set.

1. A stroke **arms** when the signal exceeds `arm_omega` (150).
2. It tracks the peak and ends when the signal falls below
   `release_ratio` (0.5) × peak.
3. It is a **ring** only if the peak ≥ `min_peak_omega` (200) **and** the
   maximum deceleration ≥ `min_decel` (6000 deg/s²). A bell rings when it
   is stopped sharply; waving and lifting are smooth.
4. The reported time `t` is back-dated to the moment of maximum
   deceleration, with sub-sample interpolation.
5. A `refractory_ms` (150) period and re-arm below `rearm_omega` (100)
   prevent double triggers.

`vel` = peak ÷ `full_scale_omega` (1000 deg/s), clamped to 0..1. It maps to
playback level through `audio.level` {min, max, curve}.

**Sensitivity.** `ring.sens: "quick"` lowers thresholds (HGP's per-player
setting). Fast-passage adaptation (`adapt_params`, `expected_ioi`) is
ported for when a host sends cues over a link; standalone it stays at
`normal` unless configured.

**Axis.** With `"axis": null` any direction rings, including a hard return
swing. Once the board's orientation in the handle is fixed, set the
forward-stroke axis in device coordinates, for example
`"detector": {"axis": [0, 1, 0]}`. That ignores return swings and enables
two-direction shakes in fast passages. `learn_axis()` can derive it from a
few recorded rings (see below).

## Tuning workflow

Tune on a computer from recordings, not by editing code on the board.

1. **Record.** On the board: `import bringup.record_trace`. On the computer:

   ```
   python firmware/scripts/capture_trace.py --label "full rings, slow" --seconds 60
   ```

   Record separate sessions for ringing at different speeds, picking up
   and setting down, walking with the bell, deliberate shaking, playing
   with the speaker sounding (vibration coupling) and chest stops. Label
   the motion, never the person. Files go to `firmware/traces/local/`,
   which git ignores.
2. **Replay** through exactly the code that runs on the board:

   ```
   python firmware/scripts/replay.py firmware/traces/local/*.jsonl
   python firmware/scripts/replay.py trace.jsonl --params '{"min_decel": 5000, "axis": [0, 1, 0]}'
   ```

   It prints detected rings (`t`, `vel`, `det`), the count the board itself
   detected while recording, and what the instrument would have played.
3. **Decide with numbers.** For each candidate parameter set, count missed
   rings in the ringing traces and false rings in the handling traces.
   Agree targets with the owner first (E01); don't call a rate
   "acceptable" without one.
4. **Apply** the chosen overrides in `bells.json` under `detector`. Keep the
   traces that justified them: promote non-identifying examples to
   `firmware/traces/` and add a regression test that replays them.

The instrument also streams raw rows when `"debug": {"raw": true}`, which
records real playing with detection side by side. Printing costs loop
time; check `status.rateHz`.

### First-article measurement (2026-11-25)

On the assembled first-article bell, the owner reported that light taps
rang it. A five-minute capture with deliberately low thresholds
(`arm_omega` 60, `min_peak_omega` 80, `min_decel` 1000) printed every
stroke while the owner tapped and rang it in separate groups:

| Group | Peak angular speed (deg/s) | Max deceleration (deg/s²) | Peak acceleration (m/s²) |
|---|---|---|---|
| Normal rings (7) | 577-939 | 24,000-40,000 | 61-74 |
| Soft rings (2) | 452-570 | 17,000-18,000 | 43-49 |
| Light taps (6) | 134-251 | 12,000-45,000 | 48-77 |

Taps stop as abruptly as rings and jolt as hard, so `min_decel` and
acceleration don't separate them; peak angular speed does. The shipped
`bells.json` and defaults therefore override **`min_peak_omega` to 350**,
midway between the strongest tap and the softest ring. The other
parameters keep the Go Go HarmoniYo defaults. This is a small, unlabelled
sample: one 254 deg/s stroke was ambiguous, and no ring trace was saved.
Lower the value toward 300 if soft rings are missed, or raise it if taps
still ring, and repeat the capture with `capture_trace.py` before changing
the default again.

## Timing budget to measure

| Stage | Expected | How to measure |
|---|---|---|
| IMU sample period | 2.4 ms at 416 Hz | `bringup.loop_rate`, `status.rateHz` |
| Detection delay `det` (fire time minus back-dated strike) | Tens of ms: the stroke must decelerate past half its peak | `gesture.det` on the console |
| Amplifier wake | 0 when pre-woken by motion; about 55 ms cold | `bringup.audio_files`, `status.audio` |
| Sound start | Up to one mixer buffer (2048 bytes ≈ 46 ms at 22.05 kHz mono) plus MP3 priming (~50 ms) | Microphone recording ([bring-up](bring-up.md#5-measurements-to-make-once-it-sounds)) |

`audio.buffer_size` trades underrun risk against latency. Reduce it
only with evidence of no glitches. See the
[plan](plan-and-experiments.md#audio-storage-and-silence) and the
historical [CircuitPython #7322](https://github.com/adafruit/circuitpython/issues/7322).

## Keeping congruent with Go Go HarmoniYo

Traces use HGP's `raw` columns, so the same recordings can be replayed
through the TypeScript detector in that project. Parameter names, units
and defaults match S1 at `51ae4af5`; the handbell's `min_peak_omega`
override (350, above) is a per-instrument config value, not a changed
default. When either side changes a detector
default, record it in both repositories' notes rather than letting them
drift silently.
