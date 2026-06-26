import re
from pathlib import Path

SOURCE = Path("paroles_bilan_thermique_flow_accentue.txt")
TARGET = Path("paroles_bilan_thermique_flow_v2_1e_and_a.txt")

MEASURE_RE = re.compile(r"^(\[M\d+\])\s+(.*)$")
SYLLABLE_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿŒœÇç0-9']+", re.UNICODE)
GRID = "1 e & a | 2 e & a | 3 e & a | 4 e & a"
SLOT_LABELS = ["1", "e", "&", "a"] * 4

def split_syllables(text: str) -> list[str]:
    raw = SYLLABLE_RE.findall(text)
    out: list[str] = []
    for token in raw:
        chunks = [chunk for chunk in token.split("-") if chunk]
        if chunks:
            out.extend(chunks)
    return out


def place_hits(line: str) -> list[bool]:
    slots = [False] * 16
    parts = [part.strip() for part in line.split("//")]

    # If there is a vocal split marker, place first segment on beats 1-2 and second on beats 3-4.
    ranges = [(0, 7), (8, 15)] if len(parts) >= 2 else [(0, 15)]

    for idx, part in enumerate(parts):
        if idx >= len(ranges):
            r_start, r_end = ranges[-1]
        else:
            r_start, r_end = ranges[idx]

        syllables = split_syllables(part)
        if not syllables:
            continue

        span = r_end - r_start + 1
        for i, syl in enumerate(syllables):
            pos = r_start + round(i * (span - 1) / max(1, len(syllables) - 1))
            has_upper = any(c.isalpha() and c.isupper() for c in syl)
            if has_upper:
                slots[pos] = True

    return slots


def render_hit_row(hits: list[bool]) -> str:
    cells = ["X" if hit else "." for hit in hits]
    groups = [" ".join(cells[i : i + 4]) for i in range(0, 16, 4)]
    return " | ".join(groups)


def render_label_row() -> str:
    groups = [" ".join(SLOT_LABELS[i : i + 4]) for i in range(0, 16, 4)]
    return " | ".join(groups)


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    out: list[str] = []

    out.append("Titre: Bilan Thermique (Flow V2 - 1e&a)")
    out.append("Tempo: 88 BPM")
    out.append("")
    out.append("Legende:")
    out.append("- Grille: subdivision 1-e-&-a sur 4 temps")
    out.append("- Accent map: X = appui vocal, . = passage")
    out.append("- Les lignes [Mxx] restent les memes pour la pose")
    out.append("")

    for line in lines:
        m = MEASURE_RE.match(line.strip())
        if not m:
            out.append(line)
            continue

        measure, lyric = m.group(1), m.group(2)
        hits = place_hits(lyric)

        out.append(f"{measure} {lyric}")
        out.append(f"      Grid      : {GRID}")
        out.append(f"      Subdiv    : {render_label_row()}")
        out.append(f"      Accent map: {render_hit_row(hits)}")

    TARGET.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Generated: {TARGET}")


if __name__ == "__main__":
    main()
