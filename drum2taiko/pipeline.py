from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

from drum2taiko.analysis.candidates import extract_drum_events
from drum2taiko.audio.ogg import convert_to_ogg
from drum2taiko.creator import (
    apply_pattern_plan_to_anchors,
    build_arrangement_context,
    default_pattern_plan,
    normalize_output_id,
    retrieve_similar_charts,
)
from drum2taiko.io.psygodot import write_beatmaps
from drum2taiko.io.tja import write_tja
from drum2taiko.review import write_review_report
from drum2taiko.separation.demucs import DemucsConfig, separate_drums


Extractor = Callable[..., list[dict[str, Any]]]
Separator = Callable[..., Path]
AudioConverter = Callable[[str | Path, str | Path], Path]
DEFAULT_TJA_DIFFICULTIES = ("easy", "normal", "hard", "oni")


def _safe_package_name(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]+', "_", value).strip().strip(".")
    return cleaned or "song"


def _duration_from_events(events: list[dict[str, Any]]) -> float:
    return max((float(event.get("time_sec", 0.0)) for event in events), default=0.0)


def _tempo_from_events(events: list[dict[str, Any]], default: float = 120.0) -> float:
    values = [float(event["tempo_bpm"]) for event in events if event.get("tempo_bpm")]
    return round(sum(values) / len(values), 3) if values else default


def _default_plan_for_difficulty(context: dict[str, Any], difficulty: str) -> dict[str, Any]:
    scoped_context = dict(context)
    scoped_context["difficulty"] = difficulty
    return default_pattern_plan(scoped_context)


def _plan_for_difficulty(
    pattern_plan: dict[str, Any] | None,
    context: dict[str, Any],
    difficulty: str,
) -> dict[str, Any]:
    if pattern_plan and isinstance(pattern_plan.get("difficulties"), dict):
        plan = pattern_plan["difficulties"].get(difficulty)
        if plan:
            return plan
    if pattern_plan and str(pattern_plan.get("difficulty", "")).lower() == difficulty:
        return pattern_plan
    return _default_plan_for_difficulty(context, difficulty)


def generate_beatmaps(
    audio_path: str | Path,
    output_dir: str | Path,
    *,
    title: str | None = None,
    output_prefix: str | None = None,
    audio_offset_ms: float = 0.0,
    chart_offset_ms: float = 0.0,
    drum_stem_path: str | Path | None = None,
    use_demucs: bool = False,
    stems_dir: str | Path | None = None,
    demucs_model: str = "htdemucs",
    demucs_device: str = "",
    demucs_segment: int | None = None,
    demucs_format: str = "wav",
    extractor: Extractor = extract_drum_events,
    separator: Separator = separate_drums,
) -> dict[str, Path]:
    source = Path(audio_path)
    resolved_stem = Path(drum_stem_path) if drum_stem_path else None
    event_source = "demucs_drums" if resolved_stem else ""

    if use_demucs:
        stem_output = Path(stems_dir) if stems_dir else Path(output_dir) / "stems"
        config = DemucsConfig(
            model=demucs_model,
            device=demucs_device,
            segment=demucs_segment,
            output_format=demucs_format,
        )
        resolved_stem = separator(source, stem_output, config=config)
        event_source = "demucs_drums"

    events = extractor(source, drum_stem_path=resolved_stem)
    return write_beatmaps(
        events,
        output_dir,
        source_path=source,
        title=title or source.stem,
        output_prefix=output_prefix,
        audio_offset_ms=audio_offset_ms,
        chart_offset_ms=chart_offset_ms,
        drum_event_source=event_source,
    )


def build_beatmap_package(
    audio_path: str | Path,
    output_dir: str | Path,
    *,
    title: str | None = None,
    output_prefix: str | None = None,
    audio_offset_ms: float = 0.0,
    chart_offset_ms: float = 0.0,
    stems_dir: str | Path | None = None,
    demucs_model: str = "htdemucs",
    demucs_device: str = "cuda",
    demucs_segment: int | None = 7,
    demucs_format: str = "mp3",
    extractor: Extractor = extract_drum_events,
    separator: Separator = separate_drums,
) -> dict[str, Any]:
    output = Path(output_dir)
    beatmaps = generate_beatmaps(
        audio_path,
        output,
        title=title,
        output_prefix=output_prefix,
        audio_offset_ms=audio_offset_ms,
        chart_offset_ms=chart_offset_ms,
        use_demucs=True,
        stems_dir=stems_dir or output / "stems",
        demucs_model=demucs_model,
        demucs_device=demucs_device,
        demucs_segment=demucs_segment,
        demucs_format=demucs_format,
        extractor=extractor,
        separator=separator,
    )
    report = write_review_report(beatmaps, output / "review_report.json")
    return {"beatmaps": beatmaps, "report": report}


def build_opentaiko_package(
    audio_path: str | Path,
    output_dir: str | Path,
    *,
    title: str | None = None,
    output_prefix: str | None = None,
    audio_offset_ms: float = 0.0,
    chart_offset_ms: float = 0.0,
    stems_dir: str | Path | None = None,
    demucs_model: str = "htdemucs",
    demucs_device: str = "cuda",
    demucs_segment: int | None = 7,
    demucs_format: str = "mp3",
    extractor: Extractor = extract_drum_events,
    separator: Separator = separate_drums,
    audio_converter: AudioConverter = convert_to_ogg,
) -> dict[str, Any]:
    source = Path(audio_path)
    display_title = title or source.stem
    package_name = _safe_package_name(output_prefix or display_title)
    package_dir = Path(output_dir) / package_name
    debug_dir = package_dir / "debug_json"
    audio_output = package_dir / f"{package_name}.ogg"
    tja_output = package_dir / f"{package_name}.tja"

    package_dir.mkdir(parents=True, exist_ok=True)
    audio_path_out = audio_converter(source, audio_output)
    beatmaps = generate_beatmaps(
        source,
        debug_dir,
        title=display_title,
        output_prefix=package_name,
        audio_offset_ms=audio_offset_ms,
        chart_offset_ms=chart_offset_ms,
        use_demucs=True,
        stems_dir=stems_dir or package_dir / "stems",
        demucs_model=demucs_model,
        demucs_device=demucs_device,
        demucs_segment=demucs_segment,
        demucs_format=demucs_format,
        extractor=extractor,
        separator=separator,
    )
    report = write_review_report(beatmaps, package_dir / "review_report.json")
    payloads = {
        difficulty: json.loads(path.read_text(encoding="utf-8"))
        for difficulty, path in beatmaps.items()
    }
    tja = write_tja(payloads, tja_output, title=display_title, audio_filename=Path(audio_path_out).name)
    return {
        "package_dir": package_dir,
        "audio": Path(audio_path_out),
        "tja": tja,
        "beatmaps": beatmaps,
        "report": report,
    }


def create_tja_package(
    audio_path: str | Path,
    output_dir: str | Path,
    *,
    difficulty: str = "oni",
    difficulties: list[str] | tuple[str, ...] | None = None,
    title: str | None = None,
    song_id: str = "",
    output_prefix: str | None = None,
    corpus_dir: str | Path | None = None,
    pattern_plan_path: str | Path | None = None,
    reuse_context_path: str | Path | None = None,
    lead_in_sec: float = 2.5,
    level: int | None = None,
    extractor: Extractor = extract_drum_events,
    audio_converter: AudioConverter = convert_to_ogg,
) -> dict[str, Any]:
    source = Path(audio_path)
    display_title = title or source.stem
    course_keys = [item.lower() for item in (difficulties or DEFAULT_TJA_DIFFICULTIES)]
    output_id = normalize_output_id(output_prefix or display_title, song_id=song_id)
    package_dir = Path(output_dir) / output_id
    package_dir.mkdir(parents=True, exist_ok=True)

    audio_output = package_dir / f"{output_id}.ogg"
    tja_output = package_dir / f"{output_id}.tja"
    retrieval_output = package_dir / "retrieval.json"
    context_output = package_dir / "arrangement_context.json"
    plan_output = package_dir / "pattern_plan.json"
    aligned_output = package_dir / "aligned_samples.json"

    if reuse_context_path:
        audio_path_out = audio_output
        context = json.loads(Path(reuse_context_path).read_text(encoding="utf-8"))
        bpm = float(context.get("estimated_bpm", 120.0))
        events = []
        matches = context.get("retrieval_context", {}).get("matches", [])
    else:
        audio_path_out = audio_converter(source, audio_output)
        events = extractor(source)
        bpm = _tempo_from_events(events)
        duration_sec = _duration_from_events(events)
        corpus = Path(corpus_dir) if corpus_dir else Path("derived") / "tja-creator" / "corpus"
        matches = retrieve_similar_charts(
            bpm=bpm,
            duration_sec=duration_sec,
            drum_events=events,
            difficulty=course_keys[-1],
            corpus_dir=corpus,
        )
        context = build_arrangement_context(
            title=display_title,
            difficulty=course_keys[-1],
            bpm=bpm,
            drum_events=events,
            retrieval_matches=matches,
        )

    source_plan = json.loads(Path(pattern_plan_path).read_text(encoding="utf-8")) if pattern_plan_path else None
    courses: dict[str, dict[str, Any]] = {}
    effective_plans: dict[str, dict[str, Any]] = {}
    for course_key in course_keys:
        course_plan = _plan_for_difficulty(source_plan, context, course_key)
        if level is not None:
            course_plan = dict(course_plan)
            course_plan["level"] = int(level)
        effective_plans[course_key] = course_plan
        courses[course_key] = apply_pattern_plan_to_anchors(
            context["candidate_timing_anchors"],
            course_plan,
            bpm=bpm,
            title=display_title,
            song_id=output_id,
            lead_in_sec=lead_in_sec,
        )

    tja = write_tja(
        courses,
        tja_output,
        title=display_title[:80],
        audio_filename=Path(audio_path_out).name,
    )
    retrieval_output.write_text(
        json.dumps(
            {
                "source_audio": str(source),
                "output_id": output_id,
                "difficulty": course_keys[0] if len(course_keys) == 1 else course_keys,
                "estimated_bpm": bpm,
                "drum_event_count": len(events),
                "matches": matches,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    context_output.write_text(json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8")
    plan_payload: dict[str, Any]
    if len(effective_plans) == 1:
        plan_payload = next(iter(effective_plans.values()))
    else:
        plan_payload = {"difficulties": effective_plans}
    plan_output.write_text(json.dumps(plan_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    aligned_samples = (
        next(iter(courses.values())).get("aligned_samples", [])
        if len(courses) == 1
        else {course_key: course.get("aligned_samples", []) for course_key, course in courses.items()}
    )
    aligned_output.write_text(
        json.dumps(
            {
                "source_audio": str(source),
                "output_id": output_id,
                "difficulty": course_keys[0] if len(course_keys) == 1 else course_keys,
                "samples": aligned_samples,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "package_dir": package_dir,
        "audio": Path(audio_path_out),
        "tja": tja,
        "retrieval": retrieval_output,
        "arrangement_context": context_output,
        "pattern_plan": plan_output,
        "aligned_samples": aligned_output,
        "matches": matches,
    }
