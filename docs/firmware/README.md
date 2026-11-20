# Firmware documentation

[Project home](../../README.md) · [Documentation index](../README.md) · [Firmware source](../../firmware/README.md)

| Document | Use it for |
|---|---|
| [Firmware guide](../../firmware/README.md) | Build, test, deploy, configure and use the instrument; script reference |
| [Getting started](getting-started.md) | Install a release zip on a board without Python; change notes; troubleshooting |
| [Bring-up](bring-up.md) | First power-up of a prototype board, step by step, and what to record |
| [Architecture](architecture.md) | Layers, ports, the board pin map, power sequencing, the ESP32-S3 seam, HGP alignment |
| [Audio assets](audio-assets.md) | Storage budget on 2 MB, the measured MP3 start delay, sound rules and provenance |
| [Gesture tuning](gesture-tuning.md) | Ring detector, recording and replaying traces, timing budget |
| [Requirements and experiments](plan-and-experiments.md) | The September plan and open questions the firmware still has to answer (formerly `firmware-and-audio.md`) |
| [Motion sensing](../motion-sensing.md) | LSM6DSOX selection, wiring and the CTRL9_XL defect background |

Status: the firmware is implemented and tested on a computer, not yet on
the custom board. Bring-up results belong in
[#9](https://github.com/dcuccia/digital-handbell/issues/9); firmware work
is tracked in [#6](https://github.com/dcuccia/digital-handbell/issues/6).
