"""Amplifier power/mute/I2S sequencing with a quiet 440 Hz tone.

Use a current-limited supply first and keep the level low. Listen for clicks
at each step; the script pauses between steps so they can be told apart.
Edit LEVEL/SETTLE_S below to experiment; record what you change.
"""

import array
import math
import time

import audiobusio
import audiocore
import audiomixer

from bringup._board import PINS, SafeAudioPins, banner

SAMPLE_RATE = 22050
FREQUENCY = 440
LEVEL = 0.05
SETTLE_S = 0.05
CLOCK_S = 0.005
HOLD_S = 1.5
RAMP_S = 0.2
PAUSE_S = 1.0


def ramp(voice, start, end, seconds, steps=40):
    for i in range(steps + 1):
        voice.level = start + (end - start) * i / steps
        time.sleep(seconds / steps)


banner("audio_tone: %d Hz at level %.2f" % (FREQUENCY, LEVEL))
period = SAMPLE_RATE // FREQUENCY
tone = audiocore.RawSample(
    array.array("h", [int(30000 * math.sin(2 * math.pi * i / period)) for i in range(period)]),
    sample_rate=SAMPLE_RATE,
)
with SafeAudioPins() as hw:
    i2s = None
    try:
        print("1. muted, POWER low (idle). Listening for %.1f s" % PAUSE_S)
        time.sleep(PAUSE_S)
        print("2. POWER high (boost + amplifier supply); settle %.0f ms" % (SETTLE_S * 1000))
        if hw.power is not None:
            hw.power.value = True
        time.sleep(SETTLE_S + PAUSE_S)
        print("3. start I2S clocks with digital silence")
        i2s = audiobusio.I2SOut(PINS["i2s_bclk"], PINS["i2s_lrclk"], PINS["i2s_data"])
        mixer = audiomixer.Mixer(voice_count=1, sample_rate=SAMPLE_RATE, channel_count=1, bits_per_sample=16, samples_signed=True)
        i2s.play(mixer)
        time.sleep(CLOCK_S + PAUSE_S)
        print("4. unmute (AMP_MUTE low): listen for hiss/click with silence")
        if hw.mute is not None:
            hw.mute.value = False
        time.sleep(PAUSE_S)
        print("5. ramp the tone up, hold %.1f s, ramp down" % HOLD_S)
        voice = mixer.voice[0]
        voice.level = 0.0
        voice.play(tone, loop=True)
        ramp(voice, 0.0, LEVEL, RAMP_S)
        time.sleep(HOLD_S)
        ramp(voice, LEVEL, 0.0, RAMP_S)
        voice.stop()
        time.sleep(PAUSE_S)
        print("6. mute, then stop clocks, then POWER low")
        if hw.mute is not None:
            hw.mute.value = True
        time.sleep(0.005)
        i2s.stop()
        i2s.deinit()
        i2s = None
        if hw.power is not None:
            hw.power.value = False
        print("done")
    finally:
        if i2s is not None:
            if hw.mute is not None:
                hw.mute.value = True
            i2s.deinit()
print("Record: clicks at steps 2/4/6, hiss at step 4, tone quality, supply current at each step.")
