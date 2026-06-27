import argparse
import ctypes
import os
import re
import struct
import sys
import subprocess
import time
from pathlib import Path


DEFAULT_LYRICS_FILE = Path("paroles_le_revers_du_fond_de_court.txt")
DEFAULT_MIDI_FILE = Path("instru_piano_rap.mid")
DEFAULT_MIDI_FALLBACK = Path("temp/instru_piano_rap_fort.mid")
DEFAULT_BPM = 96
DEFAULT_MIDI_LEAD = 0.8
DEFAULT_RAP_WORDS_PER_BEAT = 2.6
DEFAULT_SECTION_BEATS = 3.0
DEFAULT_BREATH_PAUSE = 0.14
SECTION_STYLES = {
    "title": "\033[1;36m",
    "section": "\033[1;33m",
    "lyric": "\033[0;97m",
    "active": "\033[1;32m",
    "dim": "\033[2;37m",
    "reset": "\033[0m",
}
WORD_SPLIT_RE = re.compile(r"\s+|\S+")
RAP_WORD_RE = re.compile(
    r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+(?:['’-][A-Za-zÀ-ÖØ-öø-ÿ0-9]+)*",
    flags=re.UNICODE,
)


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def ensure_utf8_console() -> None:
    if os.name == "nt":
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)
            kernel32.SetConsoleCP(65001)
        except (AttributeError, OSError):
            pass

    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def load_lyrics(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {path}")

    lines: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if line:
            lines.append(line)
    return lines


def is_section(line: str) -> bool:
    stripped = line.strip()
    if stripped.startswith("##") or stripped.startswith("###"):
        return True
    return stripped.startswith("[") and stripped.endswith("]")


def normalize_section_name(line: str) -> str | None:
    if not is_section(line):
        return None
    cleaned = line.replace("#", "").strip()
    cleaned = cleaned.replace("[", "").replace("]", "")
    return cleaned.lower()


def strip_markers(line: str) -> str:
    cleaned = line.replace("#", "").strip()
    if cleaned.startswith("[") and cleaned.endswith("]"):
        cleaned = cleaned[1:-1]
    return cleaned.strip()


def colorize(text: str, style: str, enabled: bool) -> str:
    if not enabled:
        return text
    return f"{SECTION_STYLES[style]}{text}{SECTION_STYLES['reset']}"


def section_label(line: str) -> str:
    cleaned = strip_markers(line)
    if cleaned.startswith("Titre :"):
        return cleaned
    return cleaned


def maybe_start_midi(path: Path) -> None:
    if not path.exists():
        print(f"MIDI introuvable: {path}")
        return

    try:
        os.startfile(path)
    except AttributeError:
        subprocess.Popen([str(path)], shell=True)
    except OSError as exc:
        print(f"Impossible d'ouvrir le MIDI: {exc}")


def resolve_midi_path(preferred: Path) -> Path:
    candidates = [preferred]
    if DEFAULT_MIDI_FALLBACK not in candidates:
        candidates.append(DEFAULT_MIDI_FALLBACK)

    existing_candidates = [path for path in candidates if path.exists()]
    if not existing_candidates:
        return preferred

    return max(existing_candidates, key=lambda path: path.stat().st_mtime)


def tokenize_line(line: str) -> list[str]:
    return WORD_SPLIT_RE.findall(line)


def render_word_line(line: str, word_index: int, use_color: bool) -> str:
    tokens = tokenize_line(line)
    word_positions = [i for i, token in enumerate(tokens) if not token.isspace()]
    current_word_position = word_positions[word_index] if word_index < len(word_positions) else None

    rendered: list[str] = []
    for index, token in enumerate(tokens):
        if token.isspace():
            rendered.append(token)
            continue

        if current_word_position is None:
            rendered.append(colorize(token, "lyric", use_color))
        elif index < current_word_position:
            rendered.append(colorize(token, "dim", use_color))
        elif index == current_word_position:
            rendered.append(colorize(token, "active", use_color))
        else:
            rendered.append(colorize(token, "lyric", use_color))

    return "".join(rendered)


def render_context_line(line: str, use_color: bool) -> str:
    if is_section(line):
        return colorize(f"  {section_label(line)}", "section", use_color)
    return colorize(f"  {line}", "dim", use_color)


def print_frame(
    title: str,
    lines: list[str],
    index: int,
    total: int,
    use_color: bool,
    word_index: int | None = None,
) -> None:
    clear_screen()
    print(colorize(title, "title", use_color))
    print(colorize("=" * len(title), "dim", use_color))
    print(colorize(f"{index}/{total}", "dim", use_color))
    print()
    active_pos = index - 1
    start = max(0, active_pos - 2)
    end = min(total, active_pos + 3)

    for line_pos in range(start, end):
        line = lines[line_pos]
        if line_pos == active_pos:
            if is_section(line):
                print(colorize(f"> {section_label(line)}", "section", use_color))
            elif word_index is None:
                print(colorize(f"> {line}", "active", use_color))
            else:
                print("> " + render_word_line(line, word_index, use_color))
        else:
            print(render_context_line(line, use_color))


def print_scroll_header(title: str, total: int, use_color: bool) -> None:
    print(colorize(title, "title", use_color))
    print(colorize("=" * len(title), "dim", use_color))
    print(colorize(f"{total} lignes", "dim", use_color))
    print()


def print_scroll_line(line: str, index: int, total: int, use_color: bool) -> None:
    progress = colorize(f"[{index:02d}/{total:02d}]", "dim", use_color)
    if is_section(line):
        print(f"{progress} " + colorize(section_label(line), "section", use_color))
    else:
        print(f"{progress} " + colorize(line, "active", use_color))


def print_scroll_word_progress(line: str, index: int, total: int, word_index: int, use_color: bool) -> None:
    progress = colorize(f"[{index:02d}/{total:02d}]", "dim", use_color)
    rendered_line = render_word_line(line, word_index, use_color)
    # In-place update avoids full-screen clears and reduces flicker.
    sys.stdout.write("\r\033[2K" + f"{progress} {rendered_line}")
    sys.stdout.flush()


def word_count(line: str) -> int:
    return len(RAP_WORD_RE.findall(line))


def punctuation_pause(line: str) -> float:
    comma_like = len(re.findall(r"[,;:]", line))
    stop_like = len(re.findall(r"[.!?…]", line))
    slash_like = len(re.findall(r"[/|]", line))
    return (comma_like * 0.06) + (stop_like * 0.12) + (slash_like * 0.08)


def build_timing_profile(lines: list[str], bpm: float) -> list[float]:
    durations: list[float] = []
    seconds_per_beat = 60.0 / bpm

    for index, line in enumerate(lines):
        if is_section(line):
            durations.append(max(1.0, seconds_per_beat * DEFAULT_SECTION_BEATS))
            continue

        words = max(1, word_count(line))
        # Rap/slam flow: stable spoken cadence with punctuation and breathing pauses.
        speed_boost = min(0.55, max(0, words - 8) * 0.035)
        words_per_beat = DEFAULT_RAP_WORDS_PER_BEAT + speed_boost
        spoken_duration = words * (seconds_per_beat / words_per_beat)
        breathing = DEFAULT_BREATH_PAUSE if words >= 6 else 0.08
        duration = spoken_duration + punctuation_pause(line) + breathing
        durations.append(max(0.85, duration))

    if durations and not is_section(lines[0]):
        durations[0] = max(durations[0], 1.6)

    return durations


def read_vlq(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    index = offset
    while index < len(data):
        byte = data[index]
        index += 1
        value = (value << 7) | (byte & 0x7F)
        if not (byte & 0x80):
            return value, index
    raise ValueError("VLQ MIDI invalide")


def midi_duration_seconds(path: Path) -> float | None:
    if not path.exists():
        return None

    try:
        data = path.read_bytes()
        if data[:4] != b"MThd":
            return None

        index = 4
        header_len = struct.unpack(">I", data[index : index + 4])[0]
        index += 4
        fmt, track_count, ticks_per_beat = struct.unpack(">HHH", data[index : index + 6])
        if fmt not in (0, 1) or ticks_per_beat == 0:
            return None
        index += header_len

        tempo_events: list[tuple[int, int]] = []
        end_of_track_ticks: list[int] = []

        for _ in range(track_count):
            if data[index : index + 4] != b"MTrk":
                return None
            index += 4
            track_len = struct.unpack(">I", data[index : index + 4])[0]
            index += 4
            track_end = index + track_len

            tick = 0
            running_status: int | None = None

            while index < track_end:
                delta, index = read_vlq(data, index)
                tick += delta

                status = data[index]
                if status < 0x80:
                    if running_status is None:
                        return None
                    status = running_status
                else:
                    index += 1
                    running_status = status

                if status == 0xFF:
                    meta_type = data[index]
                    index += 1
                    payload_len, index = read_vlq(data, index)
                    payload = data[index : index + payload_len]
                    index += payload_len

                    if meta_type == 0x51 and payload_len == 3:
                        tempo = (payload[0] << 16) | (payload[1] << 8) | payload[2]
                        tempo_events.append((tick, tempo))
                    elif meta_type == 0x2F:
                        end_of_track_ticks.append(tick)
                elif status in (0xF0, 0xF7):
                    payload_len, index = read_vlq(data, index)
                    index += payload_len
                else:
                    message_type = status & 0xF0
                    if message_type in (0xC0, 0xD0):
                        index += 1
                    else:
                        index += 2

            index = track_end

        if not end_of_track_ticks:
            return None

        max_tick = max(end_of_track_ticks)
        ordered_tempos = sorted(tempo_events, key=lambda item: item[0])
        if not ordered_tempos or ordered_tempos[0][0] != 0:
            ordered_tempos.insert(0, (0, 500000))

        seconds = 0.0
        current_tick = 0
        tempo_index = 0
        current_tempo = ordered_tempos[tempo_index][1]
        tempo_index += 1

        while current_tick < max_tick:
            next_tempo_tick = ordered_tempos[tempo_index][0] if tempo_index < len(ordered_tempos) else max_tick
            segment_end = min(next_tempo_tick, max_tick)
            if segment_end > current_tick:
                tick_span = segment_end - current_tick
                seconds += (tick_span / ticks_per_beat) * (current_tempo / 1_000_000)
                current_tick = segment_end

            if tempo_index < len(ordered_tempos) and current_tick == ordered_tempos[tempo_index][0]:
                current_tempo = ordered_tempos[tempo_index][1]
                tempo_index += 1

        return seconds
    except (IndexError, OSError, ValueError, struct.error):
        return None


def fit_timings_to_midi(timings: list[float], midi_path: Path, midi_lead: float) -> list[float]:
    return fit_timings_to_midi_with_mode(
        timings,
        midi_path,
        midi_lead,
        end_sync_mode="exact",
        tail_silence=0.0,
    )


def fit_timings_to_midi_with_mode(
    timings: list[float],
    midi_path: Path,
    midi_lead: float,
    end_sync_mode: str,
    tail_silence: float,
) -> list[float]:
    midi_seconds = midi_duration_seconds(midi_path)
    if midi_seconds is None:
        return timings

    base_total = sum(timings)
    desired_tail = max(0.0, tail_silence) if end_sync_mode == "tail-silence" else 0.0
    target_total = max(0.0, midi_seconds - max(0.0, midi_lead) - desired_tail)
    if base_total <= 0 or target_total <= 0:
        return timings

    scale = target_total / base_total
    return [duration * scale for duration in timings]


def run_karaoke(
    lines: list[str],
    auto: bool,
    delay: float,
    title: str,
    use_color: bool,
    sync_midi: bool,
    bpm: float,
    midi_file: Path | None,
    play_midi: bool,
    midi_lead: float,
    end_sync_mode: str,
    tail_silence: float,
    render_mode: str,
) -> None:
    total = len(lines)
    timings = build_timing_profile(lines, bpm) if sync_midi else [delay] * total

    resolved_midi_file = resolve_midi_path(midi_file) if midi_file is not None else None
    if auto and sync_midi and play_midi and resolved_midi_file is not None:
        timings = fit_timings_to_midi_with_mode(
            timings,
            resolved_midi_file,
            midi_lead,
            end_sync_mode=end_sync_mode,
            tail_silence=tail_silence,
        )

    timeline_start = time.monotonic()
    elapsed_target = 0.0

    def sleep_to_target(delta_seconds: float) -> None:
        nonlocal elapsed_target
        elapsed_target += max(0.0, delta_seconds)
        remaining = (timeline_start + elapsed_target) - time.monotonic()
        if remaining > 0:
            time.sleep(remaining)

    if play_midi and resolved_midi_file is not None:
        maybe_start_midi(resolved_midi_file)
        if auto:
            sleep_to_target(midi_lead)

    if render_mode == "scroll":
        print_scroll_header(title, total, use_color)

    for index, line in enumerate(lines, start=1):
        if render_mode == "scroll":
            if auto and not is_section(line):
                words = [token for token in tokenize_line(line) if not token.isspace()]
                per_word = max(0.08, timings[index - 1] / max(1, len(words)))
                for word_index in range(len(words)):
                    print_scroll_word_progress(line, index, total, word_index, use_color)
                    sleep_to_target(per_word)
                print()
                continue

            print_scroll_line(line, index, total, use_color)
            if auto:
                sleep_to_target(timings[index - 1])
                continue
            try:
                input("Entrée pour la ligne suivante...")
            except KeyboardInterrupt:
                break
            continue

        if auto and not is_section(line):
            words = [token for token in tokenize_line(line) if not token.isspace()]
            per_word = max(0.08, timings[index - 1] / max(1, len(words)))
            for word_index in range(len(words)):
                print_frame(title, lines, index, total, use_color, word_index)
                sleep_to_target(per_word)
            continue

        print_frame(title, lines, index, total, use_color)

        if auto:
            sleep_to_target(timings[index - 1])
            continue

        try:
            input("\nEntrée pour la ligne suivante...")
        except KeyboardInterrupt:
            break

    print()
    print("Fin du karaoké.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mini application karaoké en ligne de commande pour afficher les paroles."
    )
    parser.add_argument(
        "lyrics_file",
        nargs="?",
        default=str(DEFAULT_LYRICS_FILE),
        help=f"Chemin du fichier de paroles (défaut: {DEFAULT_LYRICS_FILE})",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Fait défiler les lignes automatiquement.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.2,
        help="Délai en secondes entre les lignes en mode automatique.",
    )
    parser.add_argument(
        "--title",
           default="Karaoké - Bilan Thermique",
        help="Titre affiché en haut de l'écran.",
    )
    parser.add_argument(
        "--color",
        dest="color",
        action="store_true",
        default=True,
        help="Active l'affichage en couleur.",
    )
    parser.add_argument(
        "--no-color",
        dest="color",
        action="store_false",
        help="Désactive l'affichage en couleur.",
    )
    parser.add_argument(
        "--sync-midi",
        action="store_true",
        help="Calcule les temps d'affichage selon le BPM et la structure du morceau.",
    )
    parser.add_argument(
        "--bpm",
        type=float,
        default=DEFAULT_BPM,
        help=f"BPM utilisé pour la synchro MIDI (défaut: {DEFAULT_BPM}).",
    )
    parser.add_argument(
        "--midi",
        default=str(DEFAULT_MIDI_FILE),
        help=f"Fichier MIDI à lancer en fond (défaut: {DEFAULT_MIDI_FILE}).",
    )
    parser.add_argument(
        "--play-midi",
        action="store_true",
        help="Lance le fichier MIDI en arrière-plan pendant le karaoké.",
    )
    parser.add_argument(
        "--midi-lead",
        type=float,
        default=DEFAULT_MIDI_LEAD,
        help=f"Temps d'attente après le lancement du MIDI avant le texte (défaut: {DEFAULT_MIDI_LEAD}).",
    )
    parser.add_argument(
        "--end-sync-mode",
        choices=("exact", "tail-silence"),
        default="exact",
        help="Mode de calage de fin: 'exact' termine texte+midi ensemble, 'tail-silence' garde une fin instrumentale.",
    )
    parser.add_argument(
        "--tail-silence",
        type=float,
        default=1.5,
        help="Silence final (secondes) conservé en mode 'tail-silence' (défaut: 1.5).",
    )
    parser.add_argument(
        "--render-mode",
        choices=("scroll", "frame"),
        default="scroll",
        help="Mode d'affichage: 'scroll' (sans scintillement) ou 'frame' (mot à mot).",
    )
    return parser


def main() -> int:
    ensure_utf8_console()

    parser = build_parser()
    args = parser.parse_args()

    lyrics_path = Path(args.lyrics_file)

    try:
        lines = load_lyrics(lyrics_path)
    except FileNotFoundError as exc:
        print(exc)
        return 1

    if not lines:
        print(f"Aucune parole trouvée dans {lyrics_path}")
        return 1

    run_karaoke(
        lines,
        auto=args.auto,
        delay=args.delay,
        title=args.title,
        use_color=args.color,
        sync_midi=args.sync_midi,
        bpm=args.bpm,
        midi_file=Path(args.midi) if args.play_midi else None,
        play_midi=args.play_midi,
        midi_lead=args.midi_lead,
        end_sync_mode=args.end_sync_mode,
        tail_silence=args.tail_silence,
        render_mode=args.render_mode,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())