from __future__ import annotations

from pathlib import Path
from typing import Any


COURSE_NAMES = {"easy": "Easy", "normal": "Normal", "hard": "Hard", "oni": "Oni", "edit": "Edit"}
COURSE_LEVELS = {"easy": 3, "normal": 5, "hard": 7, "oni": 8, "edit": 10}
TJA_NOTE_BY_LANE = {"don": "1", "ka": "2"}
TJA_NOTE_BY_TYPE = {"don": "1", "ka": "2", "big_don": "3", "big_ka": "4"}
TJA_DURATION_START_BY_TYPE = {"roll": "5", "big_roll": "6", "balloon": "7", "special_balloon": "9"}
SLOTS_PER_MEASURE = 16
BEATS_PER_MEASURE = 4
HIT_NOTE_TYPES = {"1": "don", "2": "ka", "3": "big_don", "4": "big_ka"}
DURATION_NOTE_TYPES = {"5": "roll", "6": "big_roll", "7": "balloon", "9": "special_balloon"}


def _parse_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value.strip())
    except ValueError:
        return default


def _parse_int(value: str, default: int = 0) -> int:
    try:
        return int(float(value.strip()))
    except ValueError:
        return default


def _parse_csv_ints(value: str) -> list[int]:
    items: list[int] = []
    for item in value.split(","):
        item = item.strip()
        if item:
            items.append(_parse_int(item))
    return items


def _clean_tja_line(line: str) -> str:
    for marker in ("//", ";"):
        if marker in line:
            line = line.split(marker, 1)[0]
    return line.strip()


def _header_value(line: str) -> tuple[str, str] | None:
    if ":" not in line or line.startswith("#"):
        return None
    key, value = line.split(":", 1)
    return key.strip().upper(), value.strip()


def _note_time(cursor_sec: float, measure_sec: float, slot_index: int, slot_count: int) -> float:
    return round(cursor_sec + (measure_sec * slot_index / slot_count), 6)


def parse_tja(text: str) -> dict[str, Any]:
    """Parse the common single-player TJA subset used for dataset learning."""
    metadata: dict[str, Any] = {
        "title": "",
        "subtitle": "",
        "wave": "",
        "bpm": 120.0,
        "offset_sec": 0.0,
        "courses": [],
    }
    current_course: dict[str, Any] | None = None
    inside_notes = False
    current_bpm = 120.0
    measure_numerator = 4.0
    measure_denominator = 4.0
    cursor_sec = 0.0
    open_duration: dict[str, Any] | None = None
    balloon_index = 0

    for raw_line in text.splitlines():
        line = _clean_tja_line(raw_line)
        if not line:
            continue

        header = _header_value(line)
        if header and not inside_notes:
            key, value = header
            if key == "TITLE":
                metadata["title"] = value
            elif key == "SUBTITLE":
                metadata["subtitle"] = value
            elif key == "WAVE":
                metadata["wave"] = value
            elif key == "BPM":
                metadata["bpm"] = _parse_float(value, 120.0)
                current_bpm = metadata["bpm"]
            elif key == "OFFSET":
                metadata["offset_sec"] = _parse_float(value)
            elif key == "COURSE":
                current_course = {
                    "course": value,
                    "level": 0,
                    "balloon": [],
                    "notes": [],
                    "duration_notes": [],
                    "commands": [],
                }
                metadata["courses"].append(current_course)
            elif current_course is not None and key == "LEVEL":
                current_course["level"] = _parse_int(value)
            elif current_course is not None and key == "BALLOON":
                current_course["balloon"] = _parse_csv_ints(value)
            continue

        if line == "#START":
            if current_course is None:
                current_course = {
                    "course": "Oni",
                    "level": 0,
                    "balloon": [],
                    "notes": [],
                    "duration_notes": [],
                    "commands": [],
                }
                metadata["courses"].append(current_course)
            inside_notes = True
            current_bpm = float(metadata["bpm"])
            measure_numerator = 4.0
            measure_denominator = 4.0
            cursor_sec = 0.0
            open_duration = None
            balloon_index = 0
            continue

        if line == "#END":
            inside_notes = False
            open_duration = None
            continue

        if not inside_notes or current_course is None:
            continue

        if line.startswith("#"):
            parts = line.split(maxsplit=1)
            command = parts[0].upper()
            value = parts[1].strip() if len(parts) > 1 else ""
            current_course["commands"].append({"time_sec": round(cursor_sec, 6), "command": command, "value": value})
            if command == "#BPMCHANGE":
                current_bpm = _parse_float(value, current_bpm)
            elif command == "#MEASURE" and "/" in value:
                numerator, denominator = value.split("/", 1)
                measure_numerator = _parse_float(numerator, 4.0)
                measure_denominator = _parse_float(denominator, 4.0)
            elif command == "#DELAY":
                cursor_sec += _parse_float(value)
            continue

        measure_text = line
        has_measure_end = measure_text.endswith(",")
        if has_measure_end:
            measure_text = measure_text[:-1]
        symbols = [char for char in measure_text if char.strip()]
        if not symbols:
            if has_measure_end:
                cursor_sec += (60.0 / current_bpm) * BEATS_PER_MEASURE * (measure_numerator / measure_denominator)
            continue

        measure_sec = (60.0 / current_bpm) * BEATS_PER_MEASURE * (measure_numerator / measure_denominator)
        for slot_index, symbol in enumerate(symbols):
            time_sec = _note_time(cursor_sec, measure_sec, slot_index, len(symbols))
            if symbol in HIT_NOTE_TYPES:
                current_course["notes"].append(
                    {
                        "time_sec": time_sec,
                        "type": HIT_NOTE_TYPES[symbol],
                        "source_code": symbol,
                        "measure_time_sec": round(cursor_sec, 6),
                        "slot_index": slot_index,
                        "slot_count": len(symbols),
                    }
                )
            elif symbol in DURATION_NOTE_TYPES:
                required_hits = None
                if symbol in {"7", "9"} and balloon_index < len(current_course["balloon"]):
                    required_hits = current_course["balloon"][balloon_index]
                    balloon_index += 1
                open_duration = {
                    "type": DURATION_NOTE_TYPES[symbol],
                    "start_sec": time_sec,
                    "end_sec": time_sec,
                    "start_code": symbol,
                    "end_code": "",
                    "required_hits": required_hits,
                    "measure_time_sec": round(cursor_sec, 6),
                    "slot_index": slot_index,
                    "slot_count": len(symbols),
                }
            elif symbol == "8" and open_duration is not None:
                open_duration["end_sec"] = time_sec
                open_duration["end_code"] = symbol
                current_course["duration_notes"].append(open_duration)
                open_duration = None

        if has_measure_end:
            cursor_sec += measure_sec

    return metadata


def _tempo_bpm(beatmaps: dict[str, dict[str, Any]]) -> float:
    for difficulty in ("edit", "oni", "hard", "normal", "easy"):
        value = beatmaps.get(difficulty, {}).get("tempo_bpm", 0.0)
        if value:
            return float(value)
    for beatmap in beatmaps.values():
        value = beatmap.get("tempo_bpm", 0.0)
        if value:
            return float(value)
    return 120.0


def _note_symbol(note: dict[str, Any]) -> str | None:
    source_code = str(note.get("source_code", ""))
    if source_code in HIT_NOTE_TYPES:
        return source_code
    note_type = str(note.get("type", "")).lower()
    if note_type in TJA_NOTE_BY_TYPE:
        return TJA_NOTE_BY_TYPE[note_type]
    lane = str(note.get("lane", "")).lower()
    return TJA_NOTE_BY_LANE.get(lane)


def _duration_start_symbol(duration: dict[str, Any]) -> str | None:
    source_code = str(duration.get("start_code", ""))
    if source_code in DURATION_NOTE_TYPES:
        return source_code
    duration_type = str(duration.get("type", "")).lower()
    return TJA_DURATION_START_BY_TYPE.get(duration_type)


def _slot_for_time(time_sec: float, slot_sec: float) -> int:
    return int(round(float(time_sec) / slot_sec))


def _course_lines(beatmap: dict[str, Any], bpm: float) -> list[str]:
    beat_sec = 60.0 / bpm
    slot_sec = (beat_sec * BEATS_PER_MEASURE) / SLOTS_PER_MEASURE
    notes = sorted(beatmap.get("notes", []), key=lambda note: float(note.get("time_sec", 0.0)))
    durations = sorted(
        beatmap.get("duration_notes", []),
        key=lambda duration: float(duration.get("start_sec", duration.get("time_sec", 0.0))),
    )
    hit_slots = [_slot_for_time(float(note.get("time_sec", 0.0)), slot_sec) for note in notes]
    duration_slots = [
        _slot_for_time(float(duration.get("end_sec", duration.get("start_sec", 0.0))), slot_sec)
        for duration in durations
    ]
    last_slot = max([*hit_slots, *duration_slots], default=0)
    measure_count = (last_slot // SLOTS_PER_MEASURE) + 1
    measures = [["0"] * SLOTS_PER_MEASURE for _ in range(measure_count)]

    for note in notes:
        symbol = _note_symbol(note)
        if symbol is None:
            continue
        slot = _slot_for_time(float(note.get("time_sec", 0.0)), slot_sec)
        if slot < 0:
            continue
        measure_index = slot // SLOTS_PER_MEASURE
        slot_index = slot % SLOTS_PER_MEASURE
        while measure_index >= len(measures):
            measures.append(["0"] * SLOTS_PER_MEASURE)
        measures[measure_index][slot_index] = symbol

    for duration in durations:
        start_symbol = _duration_start_symbol(duration)
        if start_symbol is None:
            continue
        start_slot = _slot_for_time(float(duration.get("start_sec", duration.get("time_sec", 0.0))), slot_sec)
        end_slot = _slot_for_time(float(duration.get("end_sec", duration.get("start_sec", 0.0))), slot_sec)
        if start_slot < 0 or end_slot < start_slot:
            continue
        for slot, symbol in ((start_slot, start_symbol), (end_slot, "8")):
            measure_index = slot // SLOTS_PER_MEASURE
            slot_index = slot % SLOTS_PER_MEASURE
            while measure_index >= len(measures):
                measures.append(["0"] * SLOTS_PER_MEASURE)
            measures[measure_index][slot_index] = symbol

    return ["".join(measure) + "," for measure in measures]


def _balloon_values(beatmap: dict[str, Any]) -> list[int]:
    values: list[int] = []
    for duration in beatmap.get("duration_notes", []):
        if str(duration.get("type", "")).lower() not in {"balloon", "special_balloon"}:
            continue
        value = duration.get("required_hits")
        if value is not None:
            values.append(int(value))
    return values


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

    for difficulty in ("easy", "normal", "hard", "oni", "edit"):
        beatmap = beatmaps.get(difficulty)
        if not beatmap:
            continue
        course_name = COURSE_NAMES.get(difficulty, str(beatmap.get("course") or difficulty).title())
        level = int(beatmap.get("level") or COURSE_LEVELS.get(difficulty, 7))
        balloons = _balloon_values(beatmap)
        lines.extend(
            [
                f"COURSE:{course_name}",
                f"LEVEL:{level}",
                *([f"BALLOON:{','.join(str(value) for value in balloons)}"] if balloons else []),
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
