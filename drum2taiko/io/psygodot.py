from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable

from drum2taiko.analysis.candidates import DRUM_CLASSES, candidate_from_time


SCHEMA_VERSION = "psygodot.beatmap.v1"
DIFFICULTIES = ("easy", "normal", "hard")
DIFFICULTY_WINDOW_MS = {"easy": 150, "normal": 110, "hard": 85}
DIFFICULTY_MIN_GAP_SEC = {"easy": 0.34, "normal": 0.28, "hard": 0.16}
DIFFICULTY_SCORE_FLOOR = {"easy": 0.46, "normal": 0.42, "hard": 0.24}
DIFFICULTY_MAX_SAME_LANE_RUN = {"easy": 999, "normal": 12, "hard": 16}
DIFFICULTY_BACKFILL_GAP_SEC = {"easy": 4.0, "normal": 4.0, "hard": 0.0}
EASY_ACTIVE_WINDOW_SEC = 4.0
EASY_ACTIVE_MIN_EVENTS = 6
EASY_ACTIVE_TARGET_RATIO = 0.68
EASY_ACTIVE_SCORE_FLOOR = 0.5
EASY_TAIKO_MOTIFS = (
    ("don", "don", "ka", "don"),
    ("don", "ka", "don", "don"),
    ("ka", "don", "don", "ka"),
)
NORMAL_TAIKO_MOTIFS = (
    ("don", "ka", "don"),
    ("don", "don", "ka"),
    ("don", "ka", "ka"),
)
ALGORITHM_VERSION = "drum2taiko_v1"


def _drum_class(value: Any) -> str:
    name = str(value or "unknown").lower()
    return name if name in DRUM_CLASSES else "unknown"


def _lane_for(index: int, difficulty: str, event: dict[str, Any]) -> str:
    drum_class = _drum_class(event.get("drum_class", "unknown"))
    strength = float(event.get("strength", 1.0))
    confidence = float(event.get("confidence", strength))
    is_accent = bool(event.get("is_accent", False))
    if difficulty == "easy":
        if drum_class == "kick":
            return "don"
        if drum_class in {"hat", "cymbal"} and confidence >= 0.4:
            return "ka"
        if drum_class in {"snare", "tom"} and confidence >= 0.55:
            return "ka"
        motif = EASY_TAIKO_MOTIFS[(index // 4) % len(EASY_TAIKO_MOTIFS)]
        return motif[index % len(motif)]
    subdivision = int(event.get("subdivision", 0))
    if drum_class == "kick":
        return "don"
    if difficulty == "normal":
        if is_accent and strength >= 0.82:
            return "don"
        if drum_class in {"hat", "cymbal"} and confidence >= 0.72 and strength >= 0.65:
            return "ka"
        motif = NORMAL_TAIKO_MOTIFS[(index // 3) % len(NORMAL_TAIKO_MOTIFS)]
        return motif[index % len(motif)]
    if drum_class in {"hat", "cymbal"}:
        return "ka"
    if drum_class == "tom" and difficulty == "hard":
        return "ka" if index % 2 else "don"
    if drum_class == "snare":
        return "ka" if subdivision in {1, 2, 3} or index % 3 == 1 else "don"
    return "ka" if subdivision in {1, 3} or (is_accent and index % 4 == 1) else "don"


def _normalize_event(item: float | dict[str, Any], fallback_index: int, chart_offset_ms: float = 0.0) -> dict[str, Any]:
    chart_offset_sec = float(chart_offset_ms) / 1000.0
    if isinstance(item, dict):
        event = item.copy()
        raw_time = round(float(event.get("time_sec", event.get("quantized_time_sec", 0.0))), 4)
        quantized_time = round(
            float(event.get("quantized_time_sec", event.get("time_sec", 0.0))) + chart_offset_sec,
            4,
        )
        event["time_sec"] = raw_time
        event["quantized_time_sec"] = quantized_time
        event["strength"] = float(event.get("strength", 1.0))
        event["subdivision"] = int(event.get("subdivision", fallback_index % 4))
        event["beat_index"] = int(event.get("beat_index", fallback_index // 4))
        event["is_accent"] = bool(event.get("is_accent", event["subdivision"] == 0 or event["strength"] >= 0.72))
        event["drum_class"] = _drum_class(event.get("drum_class", "unknown"))
        event["confidence"] = round(float(event.get("confidence", event["strength"])), 4)
        event["source_time_sec"] = round(float(event.get("source_time_sec", raw_time)), 4)
        event["timing_error_ms"] = round(float(event.get("timing_error_ms", 0.0)), 3)
        bands = event.get("band_strengths", {})
        event["band_strengths"] = {
            "low": round(float(bands.get("low", 0.0)), 4) if isinstance(bands, dict) else 0.0,
            "mid": round(float(bands.get("mid", 0.0)), 4) if isinstance(bands, dict) else 0.0,
            "high": round(float(bands.get("high", 0.0)), 4) if isinstance(bands, dict) else 0.0,
        }
        event["classification_margin"] = round(float(event.get("classification_margin", 0.0)), 4)
        return event
    event = candidate_from_time(float(item), 1.0, fallback_index)
    event["quantized_time_sec"] = round(float(event["quantized_time_sec"]) + chart_offset_sec, 4)
    return event


def _select_events(events: list[dict[str, Any]], difficulty: str) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    last_time = -999.0
    min_gap = DIFFICULTY_MIN_GAP_SEC[difficulty]
    score_floor = DIFFICULTY_SCORE_FLOOR[difficulty]

    for event in events:
        time_sec = float(event["quantized_time_sec"])
        strength = float(event.get("strength", 1.0))
        confidence = float(event.get("confidence", strength))
        subdivision = int(event.get("subdivision", 0))
        drum_class = _drum_class(event.get("drum_class", "unknown"))
        is_downbeat = subdivision == 0
        is_backbeat = subdivision == 2
        score = _event_score(event)

        if difficulty == "easy":
            if not (is_downbeat or is_backbeat or score >= 0.72):
                continue
            if score < score_floor and not is_downbeat:
                continue
        else:
            if difficulty != "hard" and drum_class in {"hat", "cymbal"} and not is_downbeat and strength < 0.78:
                continue
            if difficulty == "normal" and subdivision not in {0, 2} and strength < 0.65:
                continue
            if score < score_floor and not is_downbeat:
                continue
        if time_sec - last_time < min_gap:
            if selected and strength > float(selected[-1].get("strength", 0.0)) + 0.18:
                selected[-1] = event
                last_time = time_sec
            continue
        selected.append(event)
        last_time = time_sec
    filled = _backfill_long_gaps(events, selected, difficulty)
    if difficulty == "easy":
        return _adapt_easy_active_coverage(events, filled)
    return filled


def _event_score(event: dict[str, Any]) -> float:
    strength = float(event.get("strength", 1.0))
    confidence = float(event.get("confidence", strength))
    return (strength * 0.72) + (confidence * 0.28)


def _backfill_score(event: dict[str, Any], midpoint: float, gap_sec: float) -> float:
    subdivision = int(event.get("subdivision", 0))
    is_accent = bool(event.get("is_accent", False))
    center_bonus = 1.0 - min(1.0, abs(float(event["quantized_time_sec"]) - midpoint) / gap_sec)
    score = (_event_score(event) * 0.7) + (center_bonus * 0.15)
    if subdivision == 0:
        score += 0.18
    elif subdivision == 2:
        score += 0.08
    if is_accent:
        score += 0.1
    return score


def _is_far_enough_from_selected(
    event: dict[str, Any],
    selected: list[dict[str, Any]],
    min_gap: float,
) -> bool:
    time_sec = float(event["quantized_time_sec"])
    return all(abs(time_sec - float(note["quantized_time_sec"])) >= min_gap for note in selected)


def _active_window_score(event: dict[str, Any], midpoint: float, window_sec: float) -> float:
    center_bonus = 1.0 - min(1.0, abs(float(event["quantized_time_sec"]) - midpoint) / window_sec)
    subdivision = int(event.get("subdivision", 0))
    subdivision_bonus = 0.08 if subdivision in {0, 2} else 0.0
    return _event_score(event) + (center_bonus * 0.1) + subdivision_bonus


def _adapt_easy_active_coverage(
    events: list[dict[str, Any]],
    selected: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if len(events) < EASY_ACTIVE_MIN_EVENTS:
        return selected

    min_gap = DIFFICULTY_MIN_GAP_SEC["easy"]
    filled = sorted(selected, key=lambda event: float(event["quantized_time_sec"]))
    first_time = float(events[0]["quantized_time_sec"])
    last_time = float(events[-1]["quantized_time_sec"])
    window_start = first_time

    while window_start <= last_time:
        window_end = window_start + EASY_ACTIVE_WINDOW_SEC
        window_events = [
            event
            for event in events
            if window_start <= float(event["quantized_time_sec"]) < window_end
            and _event_score(event) >= EASY_ACTIVE_SCORE_FLOOR
        ]
        if len(window_events) >= EASY_ACTIVE_MIN_EVENTS:
            window_selected = [
                event
                for event in filled
                if window_start <= float(event["quantized_time_sec"]) < window_end
            ]
            target_count = math.ceil(len(window_events) * EASY_ACTIVE_TARGET_RATIO)
            needed = max(0, target_count - len(window_selected))
            if needed:
                selected_ids = {id(event) for event in filled}
                midpoint = (window_start + window_end) / 2.0
                candidates = [
                    event
                    for event in window_events
                    if id(event) not in selected_ids
                    and _is_far_enough_from_selected(event, filled, min_gap)
                ]
                candidates.sort(
                    key=lambda event: _active_window_score(event, midpoint, EASY_ACTIVE_WINDOW_SEC),
                    reverse=True,
                )
                for candidate in candidates:
                    if needed <= 0:
                        break
                    if not _is_far_enough_from_selected(candidate, filled, min_gap):
                        continue
                    filled.append(candidate)
                    needed -= 1
        window_start = window_end

    return sorted(filled, key=lambda event: float(event["quantized_time_sec"]))


def _best_backfill_candidate(
    events: list[dict[str, Any]],
    selected_ids: set[int],
    start_time: float,
    end_time: float,
    min_gap: float,
) -> dict[str, Any] | None:
    midpoint = (start_time + end_time) / 2.0
    gap_sec = end_time - start_time
    candidates = [
        event
        for event in events
        if id(event) not in selected_ids
        and start_time + min_gap <= float(event["quantized_time_sec"]) <= end_time - min_gap
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda event: _backfill_score(event, midpoint, gap_sec))


def _backfill_long_gaps(
    events: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    difficulty: str,
) -> list[dict[str, Any]]:
    max_gap = DIFFICULTY_BACKFILL_GAP_SEC[difficulty]
    if max_gap <= 0.0 or len(selected) < 2:
        return selected

    min_gap = DIFFICULTY_MIN_GAP_SEC[difficulty]
    filled = list(selected)
    while True:
        filled.sort(key=lambda event: float(event["quantized_time_sec"]))
        selected_ids = {id(event) for event in filled}
        inserted = False
        for previous, current in zip(filled, filled[1:]):
            start_time = float(previous["quantized_time_sec"])
            end_time = float(current["quantized_time_sec"])
            if end_time - start_time <= max_gap:
                continue
            candidate = _best_backfill_candidate(events, selected_ids, start_time, end_time, min_gap)
            if candidate is None:
                continue
            filled.append(candidate)
            inserted = True
            break
        if not inserted:
            return filled


def _opposite_lane(lane: str) -> str:
    return "ka" if lane == "don" else "don"


def _apply_lane_motif_limit(notes: list[dict[str, Any]], difficulty: str) -> None:
    max_run = DIFFICULTY_MAX_SAME_LANE_RUN[difficulty]
    previous_lane = ""
    run_length = 0
    for note in notes:
        lane = str(note["lane"])
        if lane == previous_lane:
            run_length += 1
        else:
            previous_lane = lane
            run_length = 1
        if run_length > max_run:
            note["lane"] = _opposite_lane(lane)
            previous_lane = str(note["lane"])
            run_length = 1


def build_beatmap(
    drum_events: Iterable[float | dict[str, Any]],
    *,
    difficulty: str,
    source_path: str | Path,
    title: str,
    audio_offset_ms: float = 0.0,
    chart_offset_ms: float = 0.0,
    drum_event_source: str = "",
) -> dict[str, Any]:
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty}")

    clean_events = []
    for index, item in enumerate(drum_events):
        event = _normalize_event(item, index, chart_offset_ms)
        time_sec = float(event["quantized_time_sec"])
        if math.isfinite(time_sec) and time_sec >= 0.0:
            clean_events.append(event)
    clean_events.sort(key=lambda event: (event["quantized_time_sec"], -event.get("strength", 0.0)))
    selected = _select_events(clean_events, difficulty)
    notes = [
        {
            "id": f"{difficulty}_{index + 1:04d}",
            "time_sec": round(float(event["quantized_time_sec"]), 4),
            "lane": _lane_for(index, difficulty, event),
            "window_ms": DIFFICULTY_WINDOW_MS[difficulty],
            "strength": round(float(event.get("strength", 1.0)), 4),
            "subdivision": int(event.get("subdivision", 0)),
        }
        for index, event in enumerate(selected)
    ]
    _apply_lane_motif_limit(notes, difficulty)
    duration = max((note["time_sec"] for note in notes), default=0.0)
    tempo_values = [event.get("tempo_bpm") for event in clean_events if event.get("tempo_bpm")]
    tempo_bpm = round(sum(tempo_values) / len(tempo_values), 3) if tempo_values else 0.0
    event_source_values = [
        str(event.get("drum_event_source", ""))
        for event in clean_events
        if event.get("drum_event_source")
    ]
    resolved_event_source = drum_event_source or (event_source_values[0] if event_source_values else "unknown")
    return {
        "schema_version": SCHEMA_VERSION,
        "title": title,
        "source_audio": Path(source_path).name,
        "audio_offset_ms": float(audio_offset_ms),
        "chart_offset_ms": float(chart_offset_ms),
        "difficulty": difficulty,
        "generator": "drum2taiko",
        "algorithm_version": ALGORITHM_VERSION,
        "drum_event_source": resolved_event_source,
        "tempo_bpm": tempo_bpm,
        "density_notes_per_sec": round(len(notes) / duration, 4) if duration else 0.0,
        "drum_events": [
            {
                "time_sec": round(float(event["time_sec"]), 4),
                "quantized_time_sec": round(float(event["quantized_time_sec"]), 4),
                "beat_index": int(event.get("beat_index", 0)),
                "subdivision": int(event.get("subdivision", 0)),
                "strength": round(float(event.get("strength", 1.0)), 4),
                "drum_class": _drum_class(event.get("drum_class", "unknown")),
                "confidence": round(float(event.get("confidence", event.get("strength", 1.0))), 4),
                "is_accent": bool(event.get("is_accent", False)),
                "source_time_sec": round(float(event.get("source_time_sec", event["time_sec"])), 4),
                "timing_error_ms": round(float(event.get("timing_error_ms", 0.0)), 3),
                "band_strengths": {
                    "low": round(float(event.get("band_strengths", {}).get("low", 0.0)), 4),
                    "mid": round(float(event.get("band_strengths", {}).get("mid", 0.0)), 4),
                    "high": round(float(event.get("band_strengths", {}).get("high", 0.0)), 4),
                },
                "classification_margin": round(float(event.get("classification_margin", 0.0)), 4),
            }
            for event in selected
        ],
        "notes": notes,
    }


def write_beatmaps(
    drum_events: Iterable[float | dict[str, Any]],
    output_dir: str | Path,
    *,
    source_path: str | Path,
    title: str,
    output_prefix: str | None = None,
    audio_offset_ms: float = 0.0,
    chart_offset_ms: float = 0.0,
    drum_event_source: str = "",
) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}
    events = list(drum_events)
    prefix = output_prefix or Path(source_path).stem
    for difficulty in DIFFICULTIES:
        beatmap = build_beatmap(
            events,
            difficulty=difficulty,
            source_path=source_path,
            title=title,
            audio_offset_ms=audio_offset_ms,
            chart_offset_ms=chart_offset_ms,
            drum_event_source=drum_event_source,
        )
        path = output / f"{prefix}_{difficulty}.json"
        path.write_text(json.dumps(beatmap, indent=2) + "\n", encoding="utf-8")
        paths[difficulty] = path
    return paths
