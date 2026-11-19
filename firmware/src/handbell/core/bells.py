"""Bells resident on the instrument and how one is selected.

A ``BellSet`` corresponds to HGP's ``assign.bells`` plus its ``select``
scheme. The handbell's single button cycles through the set ("cycle"), or the
set is a single fixed bell ("fixed").
"""

from handbell.core import pitch

SELECT_SCHEMES = ("cycle", "fixed")


class Bell:
    """One playable note.

    ``sound`` is ``"synth"`` (modelled bell, no storage) or a path to a
    ``.mp3``/``.wav`` asset on CIRCUITPY.
    """

    def __init__(self, id, sound, gain=1.0, label=None):
        self.id = pitch.normalize(id)
        self.midi = pitch.name_to_midi(self.id)
        self.sound = sound
        self.gain = float(gain)
        self.label = label if label is not None else self.id[:-1]

    @property
    def frequency(self):
        return pitch.midi_to_hz(self.midi)

    @property
    def kind(self):
        if self.sound == "synth":
            return "synth"
        lower = self.sound.lower()
        if lower.endswith(".mp3"):
            return "mp3"
        if lower.endswith(".wav"):
            return "wav"
        return "unknown"

    def to_hgp(self):
        return {"id": self.id, "label": self.label, "midi": self.midi}

    def __repr__(self):
        return "Bell(%s, %s)" % (self.id, self.sound)


class BellSet:
    def __init__(self, bells, select="cycle", index=0):
        if not bells:
            raise ValueError("a bell set needs at least one bell")
        if select not in SELECT_SCHEMES:
            raise ValueError("unknown select scheme: %r" % (select,))
        self.bells = list(bells)
        self.select = select
        self.index = index if 0 <= index < len(self.bells) else 0

    def __len__(self):
        return len(self.bells)

    @property
    def selected(self):
        return self.bells[self.index]

    @property
    def can_change(self):
        return self.select == "cycle" and len(self.bells) > 1

    def step(self, delta):
        """Move the selection by ``delta`` (wrapping). Return True if changed."""
        if not self.can_change:
            return False
        self.index = (self.index + delta) % len(self.bells)
        return True

    def find(self, bell_id):
        target = pitch.normalize(bell_id)
        for i, bell in enumerate(self.bells):
            if bell.id == target:
                return i
        return -1
