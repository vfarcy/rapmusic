import random
from pathlib import Path

from music21 import chord, instrument, key, note, stream, tempo


SEED = 1994
SWING = 0.07
TONE_CENTER = "C"
MODE = "minor"
BPM = 88

rng = random.Random(SEED)


def clamp(value, low, high):
    return max(low, min(high, value))


def add_human_note(part, n, beat_offset, vel, jitter=0.03, dur_jitter=0.05):
    n.volume.velocity = int(clamp(vel + rng.randint(-8, 8), 30, 120))
    n.quarterLength = max(0.18, n.quarterLength + rng.uniform(-dur_jitter, dur_jitter))
    part.insert(max(0, beat_offset + rng.uniform(-jitter, jitter)), n)


def add_drums_flow_ready(part, start_bar, bars, energy=0.7):
    for bar in range(bars):
        bar_start = (start_bar + bar) * 4
        phrase_pos = bar % 4

        # 8th hats with small dropouts on phrase endings to leave space for vocals.
        hat_steps = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5]
        if phrase_pos == 3:
            hat_steps = [0, 0.5, 1, 1.5, 2, 2.5]

        for beat in hat_steps:
            hh = note.Note(42)
            hh.quarterLength = 0.5
            swing_push = SWING if int(beat * 2) % 2 == 1 else 0
            add_human_note(part, hh, bar_start + beat + swing_push, int(54 + 18 * energy), jitter=0.01)

        for beat in (0, 2.5):
            kick = note.Note(36)
            kick.quarterLength = 0.5
            add_human_note(part, kick, bar_start + beat, int(88 + 24 * energy), jitter=0.015)

        if rng.random() < (0.32 + 0.25 * energy):
            ghost_kick = note.Note(36)
            ghost_kick.quarterLength = 0.25
            ghost_offset = rng.choice([1.75, 3.25])
            add_human_note(part, ghost_kick, bar_start + ghost_offset, int(52 + 12 * energy), jitter=0.015)

        for beat in (1, 3):
            sn = note.Note(38)
            sn.quarterLength = 0.5
            add_human_note(part, sn, bar_start + beat, int(82 + 26 * energy), jitter=0.012)

        if phrase_pos == 3 and rng.random() < 0.55:
            fill = note.Note(39)
            fill.quarterLength = 0.25
            add_human_note(part, fill, bar_start + 3.75, int(62 + 20 * energy), jitter=0.01)
        elif rng.random() < 0.28:
            ghost_sn = note.Note(40)
            ghost_sn.quarterLength = 0.25
            add_human_note(part, ghost_sn, bar_start + 2.75, int(42 + 12 * energy), jitter=0.012)


def add_bass_flow_ready(part, progression, start_bar, bars, intensity=0.65):
    for bar in range(bars):
        chord_tones = progression[bar % len(progression)]
        root = note.Note(chord_tones[0])
        root.transpose("-P8", inPlace=True)
        bar_start = (start_bar + bar) * 4
        phrase_pos = bar % 4

        root_hit = note.Note(root.pitch)
        root_hit.quarterLength = 2.0
        add_human_note(part, root_hit, bar_start, int(66 + 20 * intensity), jitter=0.015)

        if phrase_pos != 3:
            walk = note.Note(rng.choice(chord_tones[1:]))
            walk.transpose("-P8", inPlace=True)
            walk.quarterLength = 0.5
            add_human_note(part, walk, bar_start + 2.0, int(56 + 16 * intensity), jitter=0.02)

        fifth = note.Note(root.pitch)
        fifth.transpose("P5", inPlace=True)
        fifth.quarterLength = 0.75
        add_human_note(part, fifth, bar_start + 3.0, int(60 + 16 * intensity), jitter=0.02)

        if phrase_pos != 3:
            tail = note.Note(root.pitch)
            tail.quarterLength = 0.5
            add_human_note(part, tail, bar_start + 3.5, int(52 + 14 * intensity), jitter=0.02)


def add_piano_flow_ready(part, progression, start_bar, bars, intensity=0.7):
    for bar in range(bars):
        chord_tones = progression[bar % len(progression)]
        bar_start = (start_bar + bar) * 4
        phrase_pos = bar % 4

        stab = chord.Chord(chord_tones)
        stab.quarterLength = 1.0
        add_human_note(part, stab, bar_start + 0.75, int(50 + 20 * intensity), jitter=0.02, dur_jitter=0.07)

        stab2 = chord.Chord(chord_tones)
        stab2.transpose("P8", inPlace=True)
        stab2.quarterLength = 0.75
        add_human_note(part, stab2, bar_start + 2.85 + SWING, int(46 + 16 * intensity), jitter=0.025, dur_jitter=0.07)

        if phrase_pos in (1, 2) and rng.random() < 0.55:
            fill_pitch = rng.choice(chord_tones)
            fill = note.Note(fill_pitch)
            fill.quarterLength = 0.5
            add_human_note(part, fill, bar_start + 3.35, int(42 + 14 * intensity), jitter=0.025)


def add_count_in(part, bars=1):
    for bar in range(bars):
        bar_start = bar * 4
        for beat in (0, 1, 2, 3):
            click = note.Note(37)
            click.quarterLength = 0.25
            add_human_note(part, click, bar_start + beat, 74, jitter=0.0, dur_jitter=0.0)


def add_outro_tail(drums, bass, piano, start_bar, progression):
    bar_start = start_bar * 4

    # Soft closing crash then silence on drums.
    crash = note.Note(49)
    crash.quarterLength = 1.0
    add_human_note(drums, crash, bar_start, vel=54, jitter=0.0, dur_jitter=0.0)

    last_chord = chord.Chord(progression[-1])
    last_chord.quarterLength = 6.0
    add_human_note(piano, last_chord, bar_start + 0.25, vel=42, jitter=0.01, dur_jitter=0.0)

    top_note = note.Note(progression[-1][-1])
    top_note.quarterLength = 3.0
    add_human_note(piano, top_note, bar_start + 2.0, vel=36, jitter=0.01, dur_jitter=0.0)

    root = note.Note(progression[-1][0])
    root.transpose("-P8", inPlace=True)
    root.quarterLength = 4.0
    add_human_note(bass, root, bar_start, vel=40, jitter=0.01, dur_jitter=0.0)


def main():
    score = stream.Score()
    score.append(tempo.MetronomeMark(number=BPM))
    score.append(key.Key(TONE_CENTER, MODE))

    drums = stream.Part()
    drums.append(instrument.UnpitchedPercussion())

    bass = stream.Part()
    bass.append(instrument.ElectricBass())

    piano = stream.Part()
    piano.append(instrument.ElectricPiano())

    intro = [
        ["C4", "Eb4", "G4"],
        ["Ab3", "C4", "Eb4"],
    ]
    verse = [
        ["C4", "Eb4", "G4"],
        ["Ab3", "C4", "Eb4"],
        ["F3", "Ab3", "C4"],
        ["G3", "Bb3", "D4"],
    ]
    chorus = [
        ["Ab3", "C4", "Eb4"],
        ["F3", "Ab3", "C4"],
        ["C4", "Eb4", "G4"],
        ["Bb3", "D4", "F4"],
    ]

    arrangement = [
        (intro, 4, 0.48),
        (verse, 16, 0.66),
        (chorus, 8, 0.8),
        (verse, 16, 0.7),
        (chorus, 8, 0.84),
        (intro, 4, 0.42),
    ]

    count_in_bars = 1
    add_count_in(drums, bars=count_in_bars)

    cursor = count_in_bars
    for progression, bars, energy in arrangement:
        add_drums_flow_ready(drums, cursor, bars, energy=energy)
        add_bass_flow_ready(bass, progression, cursor, bars, intensity=energy)
        add_piano_flow_ready(piano, progression, cursor, bars, intensity=energy)
        cursor += bars

    add_outro_tail(drums, bass, piano, cursor, intro)

    score.insert(0, drums)
    score.insert(0, bass)
    score.insert(0, piano)

    out_file = "mc_solaar_flow_ready.mid"
    try:
        score.write("midi", out_file)
        print(f"Beat genere: {out_file}")
    except PermissionError:
        fallback = Path(out_file).with_stem("mc_solaar_flow_ready_v2")
        score.write("midi", str(fallback))
        print(f"Beat genere (fallback): {fallback}")


if __name__ == "__main__":
    main()