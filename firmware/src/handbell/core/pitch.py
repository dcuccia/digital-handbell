"""Scientific pitch names, MIDI numbers and frequencies.

Bell ids use the same convention as Go Go HarmoniYo's HGP: scientific pitch
names with sharps ("C5", "F#4"). Flats are accepted on input and normalized.
"""

NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
_FLATS = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#", "Cb": "B", "Fb": "E"}


def name_to_midi(name):
    """Return the MIDI number for a scientific pitch name such as "F#4"."""
    if not isinstance(name, str) or len(name) < 2:
        raise ValueError("invalid pitch name: %r" % (name,))
    letter = name[0].upper()
    rest = name[1:]
    accidental = ""
    if rest and rest[0] in "#b":
        accidental = rest[0]
        rest = rest[1:]
    try:
        octave = int(rest)
    except ValueError:
        raise ValueError("invalid pitch name: %r" % (name,))
    pitch = letter + accidental
    octave_shift = 0
    if accidental == "b":
        if pitch not in _FLATS:
            raise ValueError("invalid pitch name: %r" % (name,))
        if pitch == "Cb":
            octave_shift = -1
        pitch = _FLATS[pitch]
    if pitch not in NAMES:
        raise ValueError("invalid pitch name: %r" % (name,))
    midi = (octave + 1 + octave_shift) * 12 + NAMES.index(pitch)
    if not 0 <= midi <= 127:
        raise ValueError("pitch out of MIDI range: %r" % (name,))
    return midi


def midi_to_name(midi):
    """Return the sharp-spelled scientific pitch name for a MIDI number."""
    midi = int(midi)
    if not 0 <= midi <= 127:
        raise ValueError("MIDI number out of range: %r" % (midi,))
    return NAMES[midi % 12] + str(midi // 12 - 1)


def normalize(name):
    """Return the canonical sharp spelling of a pitch name."""
    return midi_to_name(name_to_midi(name))


def midi_to_hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)
