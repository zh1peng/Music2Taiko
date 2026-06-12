from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Any


def _peak_nps(times: list[float], window_sec: float = 5.0) -> float:
    if not times:
        return 0.0
    peak = 0
    start = 0
    for end, time_sec in enumerate(times):
        while time_sec - times[start] > window_sec:
            start += 1
        peak = max(peak, end - start + 1)
    return round(peak / window_sec, 4)


def _min_gap_ms(times: list[float]) -> float:
    if len(times) < 2:
        return 0.0
    gaps = [later - earlier for earlier, later in zip(times, times[1:])]
    return round(min(gaps) * 1000.0, 3)


def _density_windows(times: list[float], window_sec: float = 10.0) -> list[dict[str, Any]]:
    if not times:
        return []
    last_time = max(times)
    windows = []
    start = 0.0
    while start <= last_time:
        end = start + window_sec
        count = sum(1 for time_sec in times if start <= time_sec < end)
        windows.append(
            {
                "start_sec": round(start, 3),
                "end_sec": round(end, 3),
                "count": count,
                "nps": round(count / window_sec, 4),
            }
        )
        start = end
    return windows


def _confidence_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    values = [float(event.get("confidence", 0.0)) for event in events]
    if not values:
        return {"min": 0.0, "avg": 0.0, "low_events": 0}
    return {
        "min": round(min(values), 4),
        "avg": round(mean(values), 4),
        "low_events": sum(1 for value in values if value < 0.55),
    }


def _timing_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    errors = [float(event.get("timing_error_ms", 0.0)) for event in events]
    if not errors:
        return {
            "median_error_ms": 0.0,
            "avg_abs_error_ms": 0.0,
            "p90_abs_error_ms": 0.0,
            "suggested_chart_offset_ms": 0.0,
        }
    abs_errors = sorted(abs(value) for value in errors)
    p90_index = min(len(abs_errors) - 1, int(round((len(abs_errors) - 1) * 0.9)))
    median_error = median(errors)
    return {
        "median_error_ms": round(median_error, 3),
        "avg_abs_error_ms": round(mean(abs_errors), 3),
        "p90_abs_error_ms": round(abs_errors[p90_index], 3),
        "suggested_chart_offset_ms": round(-median_error, 3),
    }


def _lane_motif(notes: list[dict[str, Any]]) -> dict[str, Any]:
    lanes = [str(note.get("lane", "unknown")) for note in notes]
    if not lanes:
        return {"switches": 0, "switch_rate": 0.0, "max_same_lane_run": 0}
    switches = sum(1 for previous, current in zip(lanes, lanes[1:]) if previous != current)
    max_run = 1
    current_run = 1
    for previous, current in zip(lanes, lanes[1:]):
        if previous == current:
            current_run += 1
        else:
            max_run = max(max_run, current_run)
            current_run = 1
    max_run = max(max_run, current_run)
    return {
        "switches": switches,
        "switch_rate": round(switches / max(1, len(lanes) - 1), 4),
        "max_same_lane_run": max_run,
    }


def _warnings(summary: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if summary["notes"] == 0:
        warnings.append("no notes generated")
    if summary["min_gap_ms"] and summary["min_gap_ms"] < 90:
        warnings.append("very short note gap")
    if summary["peak_5s_nps"] > 6.0:
        warnings.append("high local density")
    if summary["notes"] and summary["lanes"].get("ka", 0) == 0:
        warnings.append("no ka notes")
    if summary["lane_motif"]["max_same_lane_run"] >= 24:
        warnings.append("long same-lane run")
    return warnings


def _offset_confidence(summary: dict[str, Any]) -> str:
    if summary["drum_events"] < 5:
        return "low"
    if summary["timing"]["p90_abs_error_ms"] <= 45.0:
        return "high"
    if summary["timing"]["p90_abs_error_ms"] <= 80.0:
        return "medium"
    return "low"


def summarize_beatmap(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    notes = payload.get("notes", [])
    events = payload.get("drum_events", [])
    times = sorted(float(note["time_sec"]) for note in notes)
    duration = max(times, default=0.0)
    lanes = Counter(str(note.get("lane", "unknown")) for note in notes)
    drum_classes = Counter(str(event.get("drum_class", "unknown")) for event in events)
    lane_motif = _lane_motif(notes)
    summary = {
        "difficulty": payload.get("difficulty", ""),
        "notes": len(notes),
        "drum_events": len(events),
        "duration_sec": round(duration, 4),
        "avg_nps": round(len(notes) / duration, 4) if duration else 0.0,
        "peak_5s_nps": _peak_nps(times),
        "min_gap_ms": _min_gap_ms(times),
        "lanes": dict(sorted(lanes.items())),
        "drum_classes": dict(sorted(drum_classes.items())),
        "confidence": _confidence_summary(events),
        "timing": _timing_summary(events),
        "density_10s": _density_windows(times),
        "lane_motif": lane_motif,
    }
    summary["warnings"] = _warnings(summary)
    return summary


def summarize_beatmaps(paths: dict[str, Path]) -> dict[str, Any]:
    payloads = {
        difficulty: json.loads(path.read_text(encoding="utf-8"))
        for difficulty, path in paths.items()
    }
    first_payload = payloads.get("hard") or next(iter(payloads.values()))
    difficulty_summaries = {
        difficulty: summarize_beatmap(path)
        for difficulty, path in sorted(paths.items())
    }
    offset_source_name = "hard" if "hard" in difficulty_summaries else max(
        difficulty_summaries,
        key=lambda difficulty: difficulty_summaries[difficulty]["drum_events"],
    )
    offset_source = difficulty_summaries[offset_source_name]
    return {
        "schema_version": "drum2taiko.review.v1",
        "title": first_payload.get("title", ""),
        "source_audio": first_payload.get("source_audio", ""),
        "drum_event_source": first_payload.get("drum_event_source", ""),
        "tempo_bpm": first_payload.get("tempo_bpm", 0.0),
        "audio_offset_ms": first_payload.get("audio_offset_ms", 0.0),
        "chart_offset_ms": first_payload.get("chart_offset_ms", 0.0),
        "offset_calibration": {
            "source_difficulty": offset_source_name,
            "median_error_ms": offset_source["timing"]["median_error_ms"],
            "p90_abs_error_ms": offset_source["timing"]["p90_abs_error_ms"],
            "suggested_chart_offset_ms": offset_source["timing"]["suggested_chart_offset_ms"],
            "confidence": _offset_confidence(offset_source),
        },
        "difficulties": difficulty_summaries,
    }


def write_review_report(paths: dict[str, Path], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summarize_beatmaps(paths), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
