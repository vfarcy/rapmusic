from music21 import stream, chord

s = stream.Stream()

progression = [
    ["C4","E4","G4"],   # C
    ["A3","C4","E4"],   # Am
    ["F3","A3","C4"],   # F
    ["G3","B3","D4"],   # G
]

for ch in progression:
    c = chord.Chord(ch)
    c.quarterLength = 4
    s.append(c)

s.write('midi', 'rap_clean.mid')

