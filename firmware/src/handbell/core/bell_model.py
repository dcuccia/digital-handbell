"""A simple modal handbell model shared by asset generation and synthesis.

English handbells are tuned so the strike note and its twelfth (3x) dominate.
These partials are a starting point for listening comparisons, not a
measured model of a particular bell. Amplitudes sum to 1.0 so a single
strike at full level cannot clip.

Each partial is ``(frequency_ratio, amplitude, decay_seconds)`` where
``decay_seconds`` is the exponential time constant used by the asset
generator. synthio envelopes decay linearly, so the synth voice uses
``SYNTH_DECAY_FACTOR * decay_seconds`` as its decay time.
"""

PARTIALS = (
    (1.0, 0.52, 1.30),
    (1.0021, 0.08, 1.10),
    (3.0, 0.27, 0.80),
    (5.04, 0.09, 0.30),
    (8.15, 0.04, 0.12),
)

ATTACK_SECONDS = 0.002
SYNTH_DECAY_FACTOR = 3.0


def audible_partials(fundamental_hz, sample_rate):
    """Partials below 0.45 * sample_rate (leave margin under Nyquist)."""
    limit = 0.45 * sample_rate
    out = []
    for ratio, amp, decay in PARTIALS:
        f = fundamental_hz * ratio
        if f < limit:
            out.append((f, amp, decay))
    return out


def tail_seconds():
    """Time for the slowest partial to decay by about 60 dB."""
    longest = 0.0
    for _, _, decay in PARTIALS:
        if decay > longest:
            longest = decay
    return 6.9 * longest
