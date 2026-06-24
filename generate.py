import struct
import math
from pathlib import Path


def encode_vlq(value):
    """Encode an integer as MIDI variable-length quantity."""
    if value == 0:
        return b"\x00"

    bytes_list = []
    while value > 0:
        bytes_list.append(value & 0x7F)
        value >>= 7
    bytes_list.reverse()

    for i in range(len(bytes_list) - 1):
        bytes_list[i] |= 0x80
    return bytes(bytes_list)


def create_rap_piano():
    # Header: format 0, 1 track, 96 ticks per beat.
    header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, 96)

    bpm = 96
    ticks_per_beat = 96
    ticks_per_bar = ticks_per_beat * 4
    ticks_per_step = ticks_per_bar // 16

    # Channels: 0=piano+bass instrument channel, 9=drums.
    piano_channel = 0
    drum_channel = 9

    events = bytearray()
    # Tempo: 96 BPM.
    events += b"\x00\xFF\x51\x03\x09\x89\x68"
    # Piano and drum mix controls.
    events += b"\x00\xB0\x07\x78" + b"\x00\xB0\x0B\x70"
    events += b"\x00\xB9\x07\x74" + b"\x00\xB9\x0B\x6C"

    scheduled = []

    def schedule_note(start_tick, duration, channel, note, velocity):
        on_status = 0x90 + channel
        off_status = 0x80 + channel
        scheduled.append((start_tick, 1, bytes([on_status, note, velocity])))
        scheduled.append((start_tick + duration, 0, bytes([off_status, note, 0x00])))

    def schedule_chord(start_tick, duration, channel, notes, velocity):
        for note in notes:
            schedule_note(start_tick, duration, channel, note, velocity)

    def add_hats(bar_start, velocity=40, open_hat=False, swing=0):
        for step in range(0, 16, 2):
            accent = 10 if step % 4 == 2 else 0
            tick = bar_start + step * ticks_per_step
            # Léger shuffle: décale les contretemps pour humaniser le groove.
            if step % 4 == 2:
                tick += swing
            schedule_note(
                tick,
                10,
                drum_channel,
                42,
                min(127, velocity + accent),
            )
        if open_hat:
            schedule_note(bar_start + 15 * ticks_per_step, 24, drum_channel, 46, 52)

    def add_transition_fill(bar_start, intensity=60):
        # Fill court en fin de mesure pour annoncer la section suivante.
        fill_hits = [
            (12, 45, intensity),
            (13, 47, intensity + 4),
            (14, 50, intensity + 8),
            (15, 38, intensity + 10),
        ]
        for step, note, velocity in fill_hits:
            schedule_note(bar_start + step * ticks_per_step, 12, drum_channel, note, min(127, velocity))

    def add_drum_groove(bar_start, style, bar_index=0, with_fill=False):
        if style == "intro":
            add_hats(bar_start, velocity=34, swing=4)
            for step in (0, 10):
                schedule_note(bar_start + step * ticks_per_step, 16, drum_channel, 36, 58)
            if with_fill:
                add_transition_fill(bar_start, intensity=50)
            return

        if style == "outro":
            add_hats(bar_start, velocity=28, swing=3)
            for step in (0, 8):
                schedule_note(bar_start + step * ticks_per_step, 14, drum_channel, 36, 46)
            if with_fill:
                add_transition_fill(bar_start, intensity=44)
            return

        if style == "chorus":
            add_hats(bar_start, velocity=50, open_hat=True, swing=6)
            kick_patterns = [
                (0, 3, 6, 10, 14),
                (0, 4, 7, 10, 14),
            ]
            kick_steps = kick_patterns[bar_index % len(kick_patterns)]
            snare_steps = (4, 12)
        else:
            add_hats(bar_start, velocity=42, swing=5)
            kick_patterns = [
                (0, 6, 10, 14),
                (0, 5, 10, 13),
            ]
            kick_steps = kick_patterns[bar_index % len(kick_patterns)]
            snare_steps = (4, 12)

        for step in kick_steps:
            schedule_note(bar_start + step * ticks_per_step, 16, drum_channel, 36, 74)
        for step in snare_steps:
            schedule_note(bar_start + step * ticks_per_step, 16, drum_channel, 38, 86)
        # Ghost snares discrètes pour épaissir le pocket.
        for step in (2, 11):
            schedule_note(bar_start + step * ticks_per_step, 10, drum_channel, 38, 38)

        if with_fill:
            add_transition_fill(bar_start, intensity=62)

    def add_bass_groove(bar_start, root, style, velocity=58):
        if style == "chorus":
            notes = (root, root + 7, root + 12, root + 7)
            steps = (0, 6, 10, 14)
        elif style == "outro":
            notes = (root, root, root + 5)
            steps = (0, 8, 13)
        else:
            notes = (root, root, root + 7, root)
            steps = (0, 6, 10, 14)

        for step, note in zip(steps, notes):
            schedule_note(bar_start + step * ticks_per_step, 18, piano_channel, note, velocity)

    def add_piano_comp(bar_start, chord, velocity, add_upper=False):
        hits = (0, 3, 7, 10, 13)
        chord_notes = list(chord)
        if add_upper:
            chord_notes.extend(note + 12 for note in chord)

        for step in hits:
            schedule_chord(bar_start + step * ticks_per_step, 18, piano_channel, chord_notes, velocity)

    def add_piano_arp(bar_start, chord, velocity):
        pattern = (chord[0], chord[1], chord[2], chord[1], chord[0] + 12, chord[2], chord[1], chord[2])
        for step, note in zip((0, 2, 4, 6, 8, 10, 12, 14), pattern):
            schedule_note(bar_start + step * ticks_per_step, 18, piano_channel, note, velocity)

    # Chords in mid register, bass roots lower (palette mineure).
    d_minor = [50, 53, 57]
    b_flat = [46, 49, 53]
    g_minor = [55, 58, 62]
    c_minor = [48, 51, 55]
    a_minor = [45, 48, 52]

    sections = []
    sections.extend([
        ("intro", d_minor, 38),
        ("intro", d_minor, 38),
        ("intro", b_flat, 34),
        ("intro", b_flat, 34),
    ])

    verse_loop = [
        ("verse", d_minor, 38),
        ("verse", b_flat, 34),
        ("verse", g_minor, 43),
        ("verse", c_minor, 36),
    ]
    sections.extend(verse_loop)
    sections.extend(verse_loop)

    sections.extend([
        ("chorus", b_flat, 34),
        ("chorus", c_minor, 36),
        ("chorus", d_minor, 38),
        ("chorus", a_minor, 45),
    ])

    sections.extend(verse_loop)
    sections.extend(verse_loop)

    sections.extend([
        ("outro", d_minor, 38),
        ("outro", b_flat, 34),
        ("outro", d_minor, 38),
        ("outro", d_minor, 38),
        ("outro", c_minor, 36),
        ("outro", d_minor, 38),
    ])

    # Allonge automatiquement la prod pour éviter qu'elle se termine avant le texte.
    # Marge large: certains lecteurs MIDI ignorent le tempo et jouent plus vite.
    # On allonge donc la piste pour qu'elle reste au-dessus de la durée du texte.
    target_duration_seconds = 170.0
    bar_seconds = (60.0 / bpm) * 4
    min_total_bars = math.ceil(target_duration_seconds / bar_seconds)

    if len(sections) < min_total_bars:
        tail_vamp = [
            ("verse", d_minor, 38),
            ("verse", b_flat, 34),
            ("verse", g_minor, 43),
            ("verse", c_minor, 36),
        ]
        tail_index = 0
        while len(sections) < min_total_bars:
            sections.append(tail_vamp[tail_index % len(tail_vamp)])
            tail_index += 1

    for bar_index, (style, chord, bass_root) in enumerate(sections):
        bar_start = bar_index * ticks_per_bar
        next_style = sections[bar_index + 1][0] if bar_index + 1 < len(sections) else None
        with_fill = next_style is not None and next_style != style

        if style == "intro":
            add_bass_groove(bar_start, bass_root, "verse", velocity=42)
            add_piano_comp(bar_start, chord, velocity=40, add_upper=False)
            add_drum_groove(bar_start, "intro", bar_index=bar_index, with_fill=with_fill)
        elif style == "chorus":
            add_bass_groove(bar_start, bass_root, "chorus", velocity=68)
            add_piano_comp(bar_start, chord, velocity=66, add_upper=True)
            add_drum_groove(bar_start, "chorus", bar_index=bar_index, with_fill=with_fill)
        elif style == "outro":
            add_bass_groove(bar_start, bass_root, "outro", velocity=40)
            add_piano_comp(bar_start, chord, velocity=34, add_upper=False)
            add_drum_groove(bar_start, "outro", bar_index=bar_index, with_fill=with_fill)
        else:
            add_bass_groove(bar_start, bass_root, "verse", velocity=58)
            if bar_index % 2 == 0:
                add_piano_arp(bar_start, chord, velocity=52)
            else:
                add_piano_comp(bar_start, chord, velocity=50, add_upper=False)
            add_drum_groove(bar_start, "verse", bar_index=bar_index, with_fill=with_fill)

    # Absolute ticks -> delta events.
    # Start with meta/config events so every player honors 84 BPM and channel levels.
    body = bytearray(events)
    current_tick = 0
    for tick, priority, payload in sorted(scheduled, key=lambda item: (item[0], item[1])):
        body += encode_vlq(tick - current_tick) + payload
        current_tick = tick

    body += b"\x00\xFF\x2F\x00"
    track = b"MTrk" + struct.pack(">I", len(body)) + body

    output_path = Path("instru_piano_rap.mid")
    output_bytes = header + track

    try:
        with open(output_path, "wb") as f:
            f.write(output_bytes)
        duration_seconds = len(sections) * bar_seconds
        print(f"🎵 L'accompagnement complet 'instru_piano_rap.mid' a été généré ({bpm} BPM, {len(sections)} mesures, ~{duration_seconds:.1f}s) !")
    except PermissionError:
        fallback_path = Path("temp") / "instru_piano_rap_fort.mid"
        fallback_path.parent.mkdir(parents=True, exist_ok=True)
        with open(fallback_path, "wb") as f:
            f.write(output_bytes)
        duration_seconds = len(sections) * bar_seconds
        print(f"🎵 'instru_piano_rap.mid' est verrouillé, une copie a été générée dans 'temp/instru_piano_rap_fort.mid' ({bpm} BPM, {len(sections)} mesures, ~{duration_seconds:.1f}s) !")


if __name__ == "__main__":
    create_rap_piano()
