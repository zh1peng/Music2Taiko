from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

from drum2taiko.analysis.candidates import extract_drum_events
from drum2taiko.audio.ogg import convert_to_ogg
from drum2taiko.io.psygodot import write_beatmaps
from drum2taiko.io.tja import write_tja
from drum2taiko.review import write_review_report
from drum2taiko.separation.demucs import DemucsConfig, separate_drums


Extractor = Callable[..., list[dict[str, Any]]]
Separator = Callable[..., Path]
AudioConverter = Callable[[str | Path, str | Path], Path]


def _safe_package_name(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]+', "_", value).strip().strip(".")
    return cleaned or "song"


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
