import argparse
import re
from pathlib import Path

import pyttsx3


DEFAULT_INPUT = Path("paroles_bilan_thermique_flow_accentue_fr.txt")
DEFAULT_OUTPUT = Path("vocal_guide.wav")
MEASURE_TAG_RE = re.compile(r"^\[M\d+\]\s*")


def is_section_or_meta(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.startswith("##") or stripped.startswith("###"):
        return True
    if stripped.startswith("[") and stripped.endswith("]"):
        return True

    low = stripped.lower()
    meta_prefixes = (
        "titre",
        "tempo",
        "cadence",
        "legende",
        "légende",
        "guide de pose",
    )
    return low.startswith(meta_prefixes)


def normalize_line(line: str, keep_measure_tags: bool) -> str:
    text = line.strip()
    if not keep_measure_tags:
        text = MEASURE_TAG_RE.sub("", text)

    text = text.replace("//", ", ")
    text = text.replace("...", ", ")
    return re.sub(r"\s+", " ", text).strip()


def build_spoken_text(path: Path, keep_measure_tags: bool) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    spoken_lines = []

    for line in lines:
        if is_section_or_meta(line):
            continue
        normalized = normalize_line(line, keep_measure_tags)
        if normalized:
            spoken_lines.append(normalized)

    return "\n".join(spoken_lines)


def select_voice(engine: pyttsx3.Engine, hint: str | None) -> None:
    voices = engine.getProperty("voices")
    if not voices:
        return

    if hint:
        hint_lower = hint.lower()
        for voice in voices:
            searchable = " ".join(
                [
                    str(getattr(voice, "id", "")),
                    str(getattr(voice, "name", "")),
                    " ".join(getattr(voice, "languages", []) or []),
                ]
            ).lower()
            if hint_lower in searchable:
                engine.setProperty("voice", voice.id)
                return

    for voice in voices:
        searchable = " ".join(
            [
                str(getattr(voice, "id", "")),
                str(getattr(voice, "name", "")),
                " ".join(getattr(voice, "languages", []) or []),
            ]
        ).lower()
        if "fr" in searchable or "french" in searchable:
            engine.setProperty("voice", voice.id)
            return


def synthesize_to_file(text: str, output_path: Path, rate: int, volume: float, voice_hint: str | None) -> None:
    engine = pyttsx3.init()
    engine.setProperty("rate", rate)
    engine.setProperty("volume", max(0.0, min(1.0, volume)))
    select_voice(engine, voice_hint)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    engine.save_to_file(text, str(output_path))
    engine.runAndWait()


def main() -> int:
    parser = argparse.ArgumentParser(description="Genere une voix guide (TTS) a partir des paroles.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Fichier de paroles UTF-8")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Fichier audio de sortie (.wav)")
    parser.add_argument("--rate", type=int, default=165, help="Vitesse TTS (default: 165)")
    parser.add_argument("--volume", type=float, default=1.0, help="Volume TTS 0.0-1.0 (default: 1.0)")
    parser.add_argument(
        "--voice-hint",
        default="french",
        help="Mot-cle pour choisir une voix (ex: french, fr, hortense)",
    )
    parser.add_argument(
        "--keep-measure-tags",
        action="store_true",
        help="Conserve les tags [Mxx] dans la voix guide",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Fichier introuvable: {input_path}")
        return 1

    text = build_spoken_text(input_path, keep_measure_tags=args.keep_measure_tags)
    if not text:
        print("Aucune ligne vocalisable trouvee dans le fichier.")
        return 1

    output_path = Path(args.output)
    synthesize_to_file(text, output_path, args.rate, args.volume, args.voice_hint)
    print(f"Voix guide generee: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
