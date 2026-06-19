from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from music2taiko.io.tja import BEATS_PER_MEASURE, SLOTS_PER_MEASURE


WINDOWS_RESERVED_NAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
}
DIFFICULTY_LEVELS = {"easy": 3, "normal": 5, "hard": 7, "oni": 8, "edit": 10}
DIFFICULTY_DENSITY = {"easy": 0.35, "normal": 0.55, "hard": 0.78, "oni": 1.0, "edit": 1.15}
DIFFICULTY_MAX_KA_RATIO = {"easy": 0.18, "normal": 0.35, "hard": 0.4, "oni": 0.38, "edit": 0.45}
DIFFICULTY_MAX_KA_RUN = {"easy": 1, "normal": 2, "hard": 2, "oni": 2, "edit": 3}
DEFAULT_PATTERNS = {
    "easy": "D--- ---- D--- ----",
    "normal": "D--- D--- K--- D---",
    "hard": "D-DK D-DK D-K- D---",
    "oni": "D-DK D-DK D-KD D---",
    "edit": "D-DK DKDD K-DK DDK-",
}


def normalize_output_id(title: str, *, song_id: str = "", max_length: int = 48) -> str:
    text = title.strip()
    if song_id:
        prefix_pattern = rf"^{re.escape(song_id)}\s*[-_ ]\s*"
        text = re.sub(prefix_pattern, "", text, flags=re.IGNORECASE)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", text)
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).lower()
    text = re.sub(r"-+", "-", text).strip(" ._-")
    if not text:
        text = "chart"
    if song_id:
        output_id = f"{song_id.lower()}-{text}"
    else:
        output_id = text
    if len(output_id) > max_length:
        truncated = output_id[:max_length].strip(" ._-")
        boundary = truncated.rfind("-")
        if boundary > 0 and boundary >= max_length // 2:
            truncated = truncated[:boundary]
        output_id = truncated.strip(" ._-")
    if not output_id or output_id.lower() in WINDOWS_RESERVED_NAMES:
        output_id = f"{(song_id or 'chart').lower()}-chart"[:max_length].strip(" ._-")
    return output_id


def _tempo_from_events(events: list[dict[str, Any]], default: float = 120.0) -> float:
    values = [float(event["tempo_bpm"]) for event in events if event.get("tempo_bpm")]
    return round(sum(values) / len(values), 3) if values else default


def _event_density(events: list[dict[str, Any]], duration_sec: float) -> float:
    if duration_sec <= 0.0:
        duration_sec = max((float(event.get("time_sec", 0.0)) for event in events), default=0.0)
    return len(events) / duration_sec if duration_sec > 0.0 else 0.0


def _course_summary(record: dict[str, Any], difficulty: str) -> dict[str, Any]:
    target = difficulty.lower()
    for summary in record.get("course_summaries", []):
        if str(summary.get("course", "")).lower() == target:
            return summary
    return {}


def retrieve_similar_charts(
    *,
    bpm: float,
    duration_sec: float,
    drum_events: list[dict[str, Any]],
    difficulty: str,
    corpus_dir: str | Path,
    limit: int = 5,
) -> list[dict[str, Any]]:
    manifest_path = Path(corpus_dir) / "manifest.json"
    if not manifest_path.exists():
        return []
    records = json.loads(manifest_path.read_text(encoding="utf-8"))
    target_density = _event_density(drum_events, duration_sec)
    difficulty_key = difficulty.lower()
    matches: list[dict[str, Any]] = []

    for record in records:
        if difficulty_key not in {str(course).lower() for course in record.get("courses", [])}:
            continue
        record_bpm = float(record.get("bpm", 0.0) or 0.0)
        record_duration = float(record.get("audio_duration_sec", 0.0) or 0.0)
        record_density = _event_density([{}] * int(record.get("drum_event_count", 0)), record_duration)
        bpm_score = max(0.0, 1.0 - abs(record_bpm - bpm) / max(180.0, bpm, record_bpm, 1.0))
        density_score = max(0.0, 1.0 - abs(record_density - target_density) / max(target_density, record_density, 1.0))
        duration_score = max(0.0, 1.0 - abs(record_duration - duration_sec) / max(duration_sec, record_duration, 1.0))
        course = _course_summary(record, difficulty)
        level_score = 1.0 if course else 0.75
        similarity = (bpm_score * 0.38) + (density_score * 0.32) + (duration_score * 0.15) + (level_score * 0.15)
        reasons = []
        if bpm_score >= 0.9:
            reasons.append("BPM near target")
        if density_score >= 0.8:
            reasons.append("drum-event density near target")
        if duration_score >= 0.8:
            reasons.append("duration near target")
        if course:
            reasons.append(f"has {difficulty_key} course")
        matches.append(
            {
                "song_id": record.get("song_id", ""),
                "title": record.get("title", ""),
                "bpm": record_bpm,
                "difficulty": difficulty_key,
                "similarity": round(similarity, 4),
                "similarity_reasons": reasons,
                "useful_guidance": [
                    "compare density and phrase spacing",
                    "reuse style principles, not exact measures",
                ],
            }
        )

    return sorted(matches, key=lambda item: item["similarity"], reverse=True)[:limit]


def _anchor_role(event: dict[str, Any]) -> str:
    drum_class = str(event.get("drum_class", "unknown")).lower()
    if bool(event.get("is_accent")) or drum_class in {"kick", "cymbal"}:
        return "primary"
    if drum_class in {"tom", "snare"}:
        return "fill"
    if drum_class in {"hat"}:
        return "offbeat"
    return "secondary"


def _suggested_symbol(event: dict[str, Any]) -> str:
    drum_class = str(event.get("drum_class", "unknown")).lower()
    if drum_class in {"hat", "cymbal"}:
        return "K"
    return "D"


def build_candidate_timing_anchors(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    anchors: list[dict[str, Any]] = []
    for event in sorted(events, key=lambda item: float(item.get("quantized_time_sec", item.get("time_sec", 0.0)))):
        time_sec = float(event.get("quantized_time_sec", event.get("time_sec", 0.0)))
        anchors.append(
            {
                "time_sec": round(time_sec, 6),
                "source_time_sec": round(float(event.get("time_sec", time_sec)), 6),
                "beat_index": event.get("beat_index"),
                "subdivision": event.get("subdivision"),
                "drum_class": event.get("drum_class", "unknown"),
                "strength": event.get("strength", 0.0),
                "confidence": event.get("confidence", 0.0),
                "is_accent": bool(event.get("is_accent")),
                "role": _anchor_role(event),
                "suggested_symbol": _suggested_symbol(event),
            }
        )
    return anchors


def build_arrangement_context(
    *,
    title: str,
    difficulty: str,
    bpm: float,
    drum_events: list[dict[str, Any]],
    retrieval_matches: list[dict[str, Any]],
) -> dict[str, Any]:
    anchors = build_candidate_timing_anchors(drum_events)
    return {
        "title": title,
        "difficulty": difficulty.lower(),
        "estimated_bpm": float(bpm),
        "drum_event_count": len(drum_events),
        "candidate_timing_anchors": anchors,
        "retrieval_context": {
            "matches": retrieval_matches,
            "instructions": [
                "Use retrieved songs for pattern style and density only.",
                "Place notes only on candidate_timing_anchors or deliberate musical accents.",
                "Do not copy source chart timing.",
            ],
        },
        "pattern_plan_schema": {
            "difficulty": difficulty.lower(),
            "level": DIFFICULTY_LEVELS.get(difficulty.lower(), 8),
            "sections": [
                {
                    "name": "main",
                    "start_sec": 0.0,
                    "end_sec": anchors[-1]["time_sec"] if anchors else 0.0,
                    "pattern": DEFAULT_PATTERNS.get(difficulty.lower(), "DKD"),
                    "use_big_on_accents": True,
                }
            ],
        },
    }


def default_pattern_plan(context: dict[str, Any]) -> dict[str, Any]:
    difficulty = str(context.get("difficulty", "oni")).lower()
    anchors = context.get("candidate_timing_anchors", [])
    end_sec = float(anchors[-1]["time_sec"]) if anchors else 0.0
    return {
        "difficulty": difficulty,
        "level": DIFFICULTY_LEVELS.get(difficulty, 8),
        "rationale": "Default plan generated from local anchors; LLM/skill may replace this with a richer design.",
        "sections": [
            {
                "name": "main",
                "start_sec": 0.0,
                "end_sec": end_sec,
                "pattern": DEFAULT_PATTERNS.get(difficulty, "DKD"),
                "use_big_on_accents": True,
            }
        ],
    }


def _nearest_event(note_time: float, events: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not events:
        return None
    return min(events, key=lambda event: abs(float(event.get("quantized_time_sec", event.get("time_sec", 0.0))) - note_time))


def build_aligned_samples(
    song_id: str,
    course: str,
    chart_notes: list[dict[str, Any]],
    drum_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for note in chart_notes:
        note_time = float(note.get("time_sec", note.get("start_sec", 0.0)))
        nearest = _nearest_event(note_time, drum_events)
        if nearest is None:
            audio_window = {
                "nearest_drum_class": "none",
                "nearest_event_delta_ms": None,
                "strength": 0.0,
                "confidence": 0.0,
            }
        else:
            event_time = float(nearest.get("quantized_time_sec", nearest.get("time_sec", 0.0)))
            audio_window = {
                "nearest_drum_class": nearest.get("drum_class", "unknown"),
                "nearest_event_delta_ms": round((event_time - note_time) * 1000.0, 3),
                "strength": nearest.get("strength", 0.0),
                "confidence": nearest.get("confidence", 0.0),
            }
        samples.append(
            {
                "song_id": song_id,
                "course": course,
                "time_sec": round(note_time, 6),
                "beat_index": note.get("beat_index"),
                "subdivision": note.get("subdivision"),
                "audio_window": audio_window,
                "chart_decision": note.get("type") or note.get("lane") or "unknown",
            }
        )
    return samples


def _pattern_symbols(pattern: str) -> list[str]:
    symbols = [char.upper() for char in pattern if char.strip()]
    return [symbol for symbol in symbols if symbol in {"D", "K", "B", "C", "R", "-"}]


def _symbol_to_note_type(symbol: str, anchor: dict[str, Any], *, use_big_on_accents: bool) -> str | None:
    if symbol == "-":
        return None
    if symbol == "R":
        return "roll"
    if symbol == "B":
        return "big_don"
    if symbol == "C":
        return "big_ka"
    if symbol == "K":
        return "big_ka" if use_big_on_accents and anchor.get("is_accent") and anchor.get("drum_class") == "cymbal" else "ka"
    if symbol == "D":
        return "big_don" if use_big_on_accents and anchor.get("is_accent") and anchor.get("drum_class") == "kick" else "don"
    return None


def _pattern_symbol_for_time(symbols: list[str], time_sec: float, bpm: float) -> str:
    measure_slot = _tja_slot(time_sec, bpm) % SLOTS_PER_MEASURE
    return symbols[measure_slot % len(symbols)]


def _tja_slot(time_sec: float, bpm: float) -> int:
    beat_sec = 60.0 / float(bpm)
    slot_sec = (beat_sec * BEATS_PER_MEASURE) / SLOTS_PER_MEASURE
    return int(round(float(time_sec) / slot_sec))


def _dedupe_notes_for_tja_grid(
    notes: list[dict[str, Any]],
    duration_notes: list[dict[str, Any]],
    *,
    bpm: float,
) -> list[dict[str, Any]]:
    blocked_slots = set()
    for duration in duration_notes:
        start_sec = float(duration.get("start_sec", duration.get("time_sec", 0.0)))
        end_sec = float(duration.get("end_sec", start_sec))
        blocked_slots.add(_tja_slot(start_sec, bpm))
        blocked_slots.add(_tja_slot(end_sec, bpm))

    deduped: list[dict[str, Any]] = []
    occupied_slots = set(blocked_slots)
    for note in sorted(notes, key=lambda item: float(item["time_sec"])):
        slot = _tja_slot(float(note["time_sec"]), bpm)
        if slot in occupied_slots:
            continue
        occupied_slots.add(slot)
        deduped.append(note)
    return deduped


def _is_ka_note(note: dict[str, Any]) -> bool:
    return str(note.get("type", "")).lower() in {"ka", "big_ka"}


def _convert_ka_to_don(note: dict[str, Any]) -> None:
    note["type"] = "big_don" if str(note.get("type", "")).lower() == "big_ka" else "don"


def _ka_preservation_score(note: dict[str, Any]) -> tuple[float, float, int]:
    drum_class = str(note.get("source_drum_class", "")).lower()
    strength = float(note.get("strength", 0.0) or 0.0)
    subdivision = int(note.get("subdivision", 0) or 0)
    class_bonus = 0.25 if drum_class in {"hat", "cymbal"} else 0.0
    offbeat_bonus = 0.15 if subdivision in {1, 3} else 0.0
    backbeat_bonus = 0.08 if subdivision == 2 else 0.0
    big_bonus = 0.1 if str(note.get("type", "")).lower() == "big_ka" else 0.0
    return (class_bonus + offbeat_bonus + backbeat_bonus + big_bonus + strength, strength, subdivision)


def _apply_tja_color_balance(notes: list[dict[str, Any]], difficulty: str) -> None:
    max_run = DIFFICULTY_MAX_KA_RUN.get(difficulty, 2)
    run_length = 0
    for note in notes:
        if _is_ka_note(note):
            run_length += 1
            if run_length > max_run:
                _convert_ka_to_don(note)
                run_length = 0
        else:
            run_length = 0

    ka_indices = [index for index, note in enumerate(notes) if _is_ka_note(note)]
    if not ka_indices:
        return
    max_ratio = DIFFICULTY_MAX_KA_RATIO.get(difficulty, 0.4)
    max_ka = max(1, min(len(notes) // 2, max(2, int(len(notes) * max_ratio))))
    excess = len(ka_indices) - max_ka
    if excess <= 0:
        return

    candidates = sorted(ka_indices, key=lambda index: (_ka_preservation_score(notes[index]), index))
    for index in candidates[:excess]:
        _convert_ka_to_don(notes[index])


def apply_pattern_plan_to_anchors(
    anchors: list[dict[str, Any]],
    pattern_plan: dict[str, Any],
    *,
    bpm: float,
    title: str = "",
    song_id: str = "draft",
    lead_in_sec: float = 0.0,
) -> dict[str, Any]:
    difficulty = str(pattern_plan.get("difficulty", "oni")).lower()
    notes: list[dict[str, Any]] = []
    duration_notes: list[dict[str, Any]] = []

    for section in pattern_plan.get("sections", []):
        start_sec = float(section.get("start_sec", 0.0))
        end_sec = float(section.get("end_sec", anchors[-1]["time_sec"] if anchors else 0.0))
        symbols = _pattern_symbols(str(section.get("pattern", DEFAULT_PATTERNS.get(difficulty, "DKD"))))
        if not symbols:
            symbols = ["D"]
        use_big = bool(section.get("use_big_on_accents", True))
        section_start = max(start_sec, float(lead_in_sec))
        section_anchors = [anchor for anchor in anchors if section_start <= float(anchor["time_sec"]) <= end_sec]
        for anchor in section_anchors:
            symbol = _pattern_symbol_for_time(symbols, float(anchor["time_sec"]), bpm)
            note_type = _symbol_to_note_type(symbol, anchor, use_big_on_accents=use_big)
            if note_type is None:
                continue
            if note_type == "roll":
                duration_notes.append(
                    {
                        "start_sec": round(float(anchor["time_sec"]), 6),
                        "end_sec": round(float(anchor["time_sec"]) + 1.0, 6),
                        "type": "roll",
                    }
                )
                continue
            notes.append(
                {
                    "time_sec": round(float(anchor["time_sec"]), 6),
                    "type": note_type,
                    "source_drum_class": anchor.get("drum_class", "unknown"),
                    "strength": anchor.get("strength", 0.0),
                    "beat_index": anchor.get("beat_index"),
                    "subdivision": anchor.get("subdivision"),
                    "pattern_section": section.get("name", "section"),
                }
            )

    notes = _dedupe_notes_for_tja_grid(notes, duration_notes, bpm=bpm)
    _apply_tja_color_balance(notes, difficulty)
    return {
        "title": title,
        "difficulty": difficulty,
        "level": int(pattern_plan.get("level") or DIFFICULTY_LEVELS.get(difficulty, 8)),
        "tempo_bpm": float(bpm),
        "notes": notes,
        "duration_notes": duration_notes,
        "aligned_samples": build_aligned_samples(song_id, difficulty.title(), notes, anchors),
        "pattern_plan": pattern_plan,
    }


def _event_note_type(event: dict[str, Any], difficulty: str, index: int) -> str:
    drum_class = str(event.get("drum_class", "unknown")).lower()
    strength = float(event.get("strength", 0.0) or 0.0)
    is_accent = bool(event.get("is_accent"))
    advanced = difficulty in {"hard", "oni", "edit"}
    if drum_class == "kick":
        return "big_don" if advanced and is_accent and strength >= 0.9 else "don"
    if drum_class in {"hat", "cymbal"}:
        return "big_ka" if advanced and drum_class == "cymbal" and strength >= 0.9 else "ka"
    if drum_class == "snare":
        return "ka" if index % 2 else "don"
    if drum_class == "tom":
        return "ka" if index % 2 else "don"
    return "don" if is_accent else "ka"


def compose_course_from_events(
    events: list[dict[str, Any]],
    *,
    difficulty: str,
    bpm: float,
    level: int | None = None,
    title: str = "",
    song_id: str = "draft",
) -> dict[str, Any]:
    difficulty_key = difficulty.lower()
    density = DIFFICULTY_DENSITY.get(difficulty_key, 1.0)
    ordered = sorted(events, key=lambda event: float(event.get("quantized_time_sec", event.get("time_sec", 0.0))))
    selected: list[dict[str, Any]] = []
    min_gap = {"easy": 0.42, "normal": 0.28, "hard": 0.18, "oni": 0.12, "edit": 0.1}.get(difficulty_key, 0.12)
    last_time = -999.0

    for event in ordered:
        event_time = float(event.get("quantized_time_sec", event.get("time_sec", 0.0)))
        strength = float(event.get("strength", 0.0) or 0.0)
        is_accent = bool(event.get("is_accent"))
        keep = is_accent or strength >= (0.72 / density)
        if not keep or event_time - last_time < min_gap:
            continue
        selected.append(event)
        last_time = event_time

    notes: list[dict[str, Any]] = []
    for index, event in enumerate(selected):
        event_time = float(event.get("quantized_time_sec", event.get("time_sec", 0.0)))
        notes.append(
            {
                "time_sec": round(event_time, 6),
                "type": _event_note_type(event, difficulty_key, index),
                "source_drum_class": event.get("drum_class", "unknown"),
                "strength": event.get("strength", 0.0),
                "beat_index": event.get("beat_index"),
                "subdivision": event.get("subdivision"),
            }
        )

    duration_notes: list[dict[str, Any]] = []
    for left, right in zip(selected, selected[1:]):
        start = float(left.get("quantized_time_sec", left.get("time_sec", 0.0)))
        end = float(right.get("quantized_time_sec", right.get("time_sec", 0.0)))
        if difficulty_key in {"normal", "hard", "oni", "edit"} and end - start >= 1.2 and bool(left.get("is_accent")):
            duration_notes.append(
                {
                    "start_sec": round(start, 6),
                    "end_sec": round(min(end, start + 1.5), 6),
                    "type": "roll",
                }
            )
            if len(duration_notes) >= 2:
                break

    return {
        "title": title,
        "difficulty": difficulty_key,
        "level": int(level or DIFFICULTY_LEVELS.get(difficulty_key, 8)),
        "tempo_bpm": float(bpm),
        "notes": notes,
        "duration_notes": duration_notes,
        "aligned_samples": build_aligned_samples(song_id, difficulty_key.title(), notes, events),
    }
