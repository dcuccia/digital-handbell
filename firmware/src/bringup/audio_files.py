"""Play the three voice kinds through the real audio engine and time them.

Plays a synthio bell, the uncompressed test WAV and the test MP3 for the
same note, then two overlapping WAV strikes (retrigger). Prints how long each
``play`` call takes in Python and the cold-start delay through power-up.
MP3 is kept only for comparison: decoding it during play drops out under app
load (see docs/firmware/audio-assets.md), so instrument bells use WAV.
Acoustic strike-to-sound latency needs a microphone; see
docs/firmware/bring-up.md.
"""

import time

from bringup._board import PINS, banner
from handbell.core import config
from handbell.core.bells import Bell
from handbell.hw.audio import CircuitPythonAudio
from handbell.hw.io import MonotonicClock

LEVEL = 0.25
NOTE = "A5"
WAV = "sounds/test/A5.wav"
MP3 = "sounds/test/A5.mp3"
LISTEN_S = 2.5

cfg = config.parse()
bells = [Bell(NOTE, "synth"), Bell(NOTE, WAV), Bell(NOTE, MP3)]
clock = MonotonicClock()

banner("audio_files: synth, WAV, MP3 for %s at level %.2f" % (NOTE, LEVEL))
audio = CircuitPythonAudio(PINS, cfg.audio, cfg.power, bells)


def run_until(seconds):
    end = clock.now_us() + int(seconds * 1000000)
    while clock.now_us() < end:
        audio.tick(clock.now_us())


def exists(path):
    try:
        open(path).close()
        return True
    except OSError:
        return False


try:
    for bell in bells:
        if bell.kind != "synth" and not exists(bell.sound):
            print("skip %s: %s not found (deploy sounds first)" % (bell.kind, bell.sound))
            continue
        t0 = clock.now_us()
        audio.play(bell, LEVEL, t0)
        t1 = clock.now_us()
        while not audio.is_awake():
            audio.tick(clock.now_us())
        audio.tick(clock.now_us())
        print(
            "%-5s play() %5.1f ms; started %5.1f ms after request (includes power-up when cold)"
            % (bell.kind, (t1 - t0) / 1000, (audio.last_start_latency_us or 0) / 1000)
        )
        run_until(LISTEN_S)
        audio.damp(clock.now_us(), cfg.audio["damp_ms"])
        run_until(0.3)

    print("retrigger: two WAV strikes 150 ms apart (two voices overlapping)")
    wav = bells[1]
    if exists(wav.sound):
        audio.play(wav, LEVEL, clock.now_us())
        run_until(0.15)
        t0 = clock.now_us()
        audio.play(wav, LEVEL, t0)
        print("second play() %.1f ms" % ((clock.now_us() - t0) / 1000))
        run_until(LISTEN_S)
    else:
        print("skip retrigger: %s not found" % wav.sound)
finally:
    audio.shutdown()
print("Record: timbre of each, any glitches (especially MP3), play() times.")
