# IMU traces

Recorded motion for tuning and regression tests, in JSON lines. Each line is
one HGP-shaped message:

- `{"type": "meta", "label": "...", "recorded": "..."}`: first line, written by
  `scripts/capture_trace.py`
- `{"type": "raw", "cols": ["t","ax","ay","az","gx","gy","gz"], "s": [[...], ...]}`:
  `t` in device milliseconds, acceleration in m/s² **including gravity**,
  rotation rate in deg/s
- `{"type": "gesture", ...}`: rings the device detected while recording

Captures land in `traces/local/`, which git ignores. Move a trace up into
this folder only when it is useful as a shared example, and give it a
descriptive name such as `full-rings-slow.jsonl`.

**Privacy:** traces must not identify anyone. Describe the motion, not the
person. Do not record children's sessions here. Synthetic or mechanical
fixtures are preferred for the public repository (see
`docs/firmware/plan-and-experiments.md`).

Replay with `python firmware/scripts/replay.py <trace>` (see
`docs/firmware/gesture-tuning.md`).
