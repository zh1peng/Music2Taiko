from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
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
    return warnings


def summarize_beatmap(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    notes = payload.get("notes", [])
    events = payload.get("drum_events", [])
    times = sorted(float(note["time_sec"]) for note in notes)
    duration = max(times, default=0.0)
    lanes = Counter(str(note.get("lane", "unknown")) for note in notes)
    drum_classes = Counter(str(event.get("drum_class", "unknown")) for event in events)
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
    }
    summary["warnings"] = _warnings(summary)
    return summary


def summarize_beatmaps(paths: dict[str, Path]) -> dict[str, Any]:
    payloads = {
        difficulty: json.loads(path.read_text(encoding="utf-8"))
        for difficulty, path in paths.items()
    }
    first_payload = payloads.get("hard") or next(iter(payloads.values()))
    return {
        "schema_version": "drum2taiko.review.v1",
        "title": first_payload.get("title", ""),
        "source_audio": first_payload.get("source_audio", ""),
        "drum_event_source": first_payload.get("drum_event_source", ""),
        "tempo_bpm": first_payload.get("tempo_bpm", 0.0),
        "audio_offset_ms": first_payload.get("audio_offset_ms", 0.0),
        "chart_offset_ms": first_payload.get("chart_offset_ms", 0.0),
        "difficulties": {
            difficulty: summarize_beatmap(path)
            for difficulty, path in sorted(paths.items())
        },
    }


def write_review_report(paths: dict[str, Path], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summarize_beatmaps(paths), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
