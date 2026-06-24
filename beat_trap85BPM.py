from mido import Message, MidiFile, MidiTrack, MetaMessage

mid = MidiFile(ticks_per_beat=480)

melody = MidiTrack()
bass = MidiTrack()
drums = MidiTrack()

mid.tracks.append(melody)
mid.tracks.append(bass)
mid.tracks.append(drums)

tempo = 666667  # 90 BPM
melody.append(MetaMessage('set_tempo', tempo=tempo))

ticks_per_bar = 1920
bars = 64

# =========================
# 🎹 PROGRESSIONS VARIÉES
# =========================
progressions = [
    [[60,64,67], [62,65,69], [65,69,72], [67,71,74]],   # A
    [[60,64,67], [65,69,72], [67,71,74], [62,65,69]],   # B
    [[62,65,69], [67,71,74], [60,64,67], [65,69,72]]    # C
]

for i in range(bars):

    # change progression selon sections
    if i < 16:
        prog = progressions[0]
    elif i < 32:
        prog = progressions[1]
    elif i < 48:
        prog = progressions[2]
    else:
        prog = progressions[0]

    chord = prog[i % 4]

    # VARIATION RYTHMIQUE
    if i % 8 == 7:
        # accords plus courts (variation)
        for note in chord:
            melody.append(Message('note_on', note=note, velocity=65, time=0))
        for note in chord:
            melody.append(Message('note_off', note=note, velocity=65, time=960))
    else:
        # accords longs
        for note in chord:
            melody.append(Message('note_on', note=note, velocity=60, time=0))
        for note in chord:
            melody.append(Message('note_off', note=note, velocity=60, time=ticks_per_bar))

# =========================
# 🎸 BASSE ÉVOLUTIVE
# =========================
bass_lines = [
    [36, 38, 41, 43],
    [36, 36, 43],
    [38, 41, 36]
]

for i in range(bars):

    line = bass_lines[i % len(bass_lines)]

    for note in line:
        bass.append(Message('note_on', note=note, velocity=90, time=0))
        bass.append(Message('note_off', note=note, velocity=90, time=480))

# =========================
# 🥁 DRUMS AVEC VARIATION
# =========================
for i in range(bars):

    # BREAKS réguliers
    if i % 16 == 15:
        # fill
        for _ in range(6):
            drums.append(Message('note_on', note=42, velocity=70, time=0, channel=9))
            drums.append(Message('note_off', note=42, velocity=70, time=120, channel=9))
        continue

    # KICK varie
    if i % 4 in [0, 2]:
        drums.append(Message('note_on', note=36, velocity=100, time=0, channel=9))
        drums.append(Message('note_off', note=36, velocity=100, time=480, channel=9))

    # SNARE stable
    drums.append(Message('note_on', note=38, velocity=110, time=480, channel=9))
    drums.append(Message('note_off', note=38, velocity=110, time=480, channel=9))

    # HI-HAT léger swing
    for _ in range(4):
        drums.append(Message('note_on', note=42, velocity=55, time=0, channel=9))
        drums.append(Message('note_off', note=42, velocity=55, time=220, channel=9))

# =========================
# 💾 EXPORT
# =========================
mid.save("mc_solaar_dynamic.mid")

print("✅ Beat non répétitif généré !")
