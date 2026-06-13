from __future__ import annotations

from pathlib import Path
from typing import Any


COURSE_NAMES = {"easy": "Easy", "normal": "Normal", "hard": "Hard"}
COURSE_LEVELS = {"easy": 3, "normal": 5, "hard": 7}
TJA_NOTE_BY_LANE = {"don": "1", "ka": "2"}
SLOTS_PER_MEASURE = 16
BEATS_PER_MEASURE = 4


def _tempo_bpm(beatmaps: dict[str, dict[str, Any]]) -> float:
    for difficulty in ("hard", "normal", "easy"):
        value = beatmaps.get(difficulty, {}).get("tempo_bpm", 0.0)
        if value:
            return float(value)
    return 120.0


def _course_lines(beatmap: dict[str, Any], bpm: float) -> list[str]:
    beat_sec = 60.0 / bpm
    slot_sec = (beat_sec * BEATS_PER_MEASURE) / SLOTS_PER_MEASURE
    notes = sorted(beatmap.get("notes", []), key=lambda note: float(note.get("time_sec", 0.0)))
    last_slot = max((int(round(float(note.get("time_sec", 0.0)) / slot_sec)) for note in notes), default=0)
    measure_count = (last_slot // SLOTS_PER_MEASURE) + 1
    measures = [["0"] * SLOTS_PER_MEASURE for _ in range(measure_count)]

    for note in notes:
        lane = str(note.get("lane", "")).lower()
        symbol = TJA_NOTE_BY_LANE.get(lane)
        if symbol is None:
            continue
        slot = int(round(float(note.get("time_sec", 0.0)) / slot_sec))
        if slot < 0:
            continue
        measure_index = slot // SLOTS_PER_MEASURE
        slot_index = slot % SLOTS_PER_MEASURE
        while measure_index >= len(measures):
            measures.append(["0"] * SLOTS_PER_MEASURE)
        measures[measure_index][slot_index] = symbol

    return ["".join(measure) + "," for measure in measures]


def render_tja(
    beatmaps: dict[str, dict[str, Any]],
    *,
    title: str,
    audio_filename: str,
    offset_sec: float = 0.0,
    demo_start_sec: float = 0.0,
    genre: str = "Generated",
    maker: str = "Drum2Taiko",
) -> str:
    bpm = _tempo_bpm(beatmaps)
    lines = [
        f"TITLE:{title}",
        f"BPM:{bpm:.3f}",
        f"WAVE:{audio_filename}",
        f"OFFSET:{offset_sec:.3f}",
        f"DEMOSTART:{demo_start_sec:.3f}",
        f"GENRE:{genre}",
        f"MAKER:{maker}",
        "",
    ]

    for difficulty in ("easy", "normal", "hard"):
        beatmap = beatmaps.get(difficulty)
        if not beatmap:
            continue
        lines.extend(
            [
                f"COURSE:{COURSE_NAMES[difficulty]}",
                f"LEVEL:{COURSE_LEVELS[difficulty]}",
                "#START",
                *_course_lines(beatmap, bpm),
                "#END",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_tja(
    beatmaps: dict[str, dict[str, Any]],
    output_path: str | Path,
    *,
    title: str,
    audio_filename: str,
    offset_sec: float = 0.0,
) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_tja(beatmaps, title=title, audio_filename=audio_filename, offset_sec=offset_sec),
        encoding="utf-8-sig",
    )
    return output
