from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from drum2taiko.analysis.candidates import extract_drum_events
from drum2taiko.io.psygodot import write_beatmaps
from drum2taiko.separation.demucs import DemucsConfig, separate_drums


Extractor = Callable[..., list[dict[str, Any]]]
Separator = Callable[..., Path]


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
    extractor: Extractor = extract_drum_events,
    separator: Separator = separate_drums,
) -> dict[str, Path]:
    source = Path(audio_path)
    resolved_stem = Path(drum_stem_path) if drum_stem_path else None
    event_source = "demucs_drums" if resolved_stem else ""

    if use_demucs:
        stem_output = Path(stems_dir) if stems_dir else Path(output_dir) / "stems"
        config = DemucsConfig(model=demucs_model, device=demucs_device, segment=demucs_segment)
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
