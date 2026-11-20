import pytest

from handbell.core.bells import Bell, BellSet
from handbell.core.controls import ButtonGrammar
from handbell.core.indicator import LedPattern
from handbell.core.pitch import midi_to_hz, midi_to_name, name_to_midi, normalize

MS = 1000


@pytest.mark.parametrize(
    "name,midi",
    [("C4", 60), ("A4", 69), ("F#4", 66), ("Bb4", 70), ("C-1", 0), ("G9", 127), ("Cb4", 59), ("E#4", None)],
)
def test_pitch_names(name, midi):
    if midi is None:
        with pytest.raises(ValueError):
            name_to_midi(name)
    else:
        assert name_to_midi(name) == midi


def test_pitch_round_trip_and_frequency():
    assert normalize("Db5") == "C#5"
    assert all(name_to_midi(midi_to_name(m)) == m for m in range(128))
    assert midi_to_hz(69) == pytest.approx(440.0)


def test_bell_kinds_and_set_cycling():
    bells = [Bell("C5", "sounds/C5.mp3"), Bell("D5", "synth"), Bell("E5", "sounds/E5.WAV")]
    assert [b.kind for b in bells] == ["mp3", "synth", "wav"]
    s = BellSet(bells)
    assert s.step(-1) and s.selected.id == "E5"
    assert s.step(1) and s.selected.id == "C5"
    fixed = BellSet(bells, "fixed")
    assert not fixed.step(1) and fixed.selected.id == "C5"
    assert s.find("Db5") == -1 and s.find("D5") == 1


def collect(grammar, script):
    """Run (time_ms, 'press'|'release'|'tick') steps and collect gestures."""
    out = []
    for t_ms, what in script:
        t = int(t_ms * MS)
        if what == "press":
            out += grammar.press(t)
        elif what == "release":
            out += grammar.release(t)
        else:
            out += grammar.tick(t)
    return [e for e in out if e not in ("down", "up")]


def test_click_waits_for_double_window_only_when_enabled():
    g = ButtonGrammar()
    assert collect(g, [(0, "press"), (80, "release"), (200, "tick"), (400, "tick")]) == ["click"]
    g = ButtonGrammar()
    g.double_enabled = False
    assert collect(g, [(0, "press"), (80, "release")]) == ["click"]


def test_double_long_and_very_long():
    g = ButtonGrammar()
    assert collect(g, [(0, "press"), (80, "release"), (200, "press"), (260, "release"), (700, "tick")]) == ["double"]
    g = ButtonGrammar()
    assert collect(g, [(0, "press"), (900, "tick"), (1200, "release"), (2000, "tick")]) == ["long_hint", "long"]
    g = ButtonGrammar()
    assert collect(g, [(0, "press"), (900, "tick"), (5100, "tick"), (6000, "release")]) == ["long_hint", "very_long"]


def test_down_is_immediate():
    g = ButtonGrammar()
    assert g.press(0) == ["down"] and g.pressed
    assert g.press(10) == []


def test_invalid_timing_rejected():
    with pytest.raises(ValueError):
        ButtonGrammar(double_ms=900, long_ms=800)


def test_led_overlay_then_background():
    p = LedPattern("heartbeat")
    assert p.level(0) is True
    assert p.level(100 * MS) is False
    p.show("count", 1000 * MS, count=2)
    seq = [p.level((1000 + d) * MS) for d in (0, 160, 360, 560, 1000)]
    assert seq == [True, False, True, False, False]
    p.background("error", 2000 * MS)
    assert p.level(2050 * MS) is True and p.level(2150 * MS) is False
