from __future__ import annotations

from pathlib import Path
from typing import Any

from drum2taiko.io.tja import parse_tja


def _read_tja(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "shift_jis"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def _audio_path_for_tja(song_dir: Path, wave_name: str) -> Path:
    if wave_name:
        candidate = song_dir / wave_name
        if candidate.exists():
            return candidate
        lower_wave = wave_name.lower()
        for path in song_dir.iterdir():
            if path.name.lower() == lower_wave:
                return path
        return candidate

    audio_files = sorted(
        path
        for path in song_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".ogg", ".mp3", ".wav", ".flac", ".opus"}
    )
    return audio_files[0] if audio_files else song_dir / ""


def build_song_records(song_dir: str | Path) -> list[dict[str, Any]]:
    directory = Path(song_dir)
    records: list[dict[str, Any]] = []
    for tja_path in sorted(directory.glob("*.tja")):
        try:
            parsed = parse_tja(_read_tja(tja_path))
            audio_path = _audio_path_for_tja(directory, str(parsed.get("wave", "")))
            parse_status = "ok" if audio_path.exists() else "missing_audio"
            records.append(
                {
                    "song_dir": directory,
                    "tja_path": tja_path,
                    "audio_path": audio_path,
                    "title": parsed.get("title") or tja_path.stem,
                    "wave": parsed.get("wave", ""),
                    "bpm": parsed.get("bpm", 0.0),
                    "offset_sec": parsed.get("offset_sec", 0.0),
                    "courses": [course.get("course", "") for course in parsed.get("courses", [])],
                    "course_count": len(parsed.get("courses", [])),
                    "parse_status": parse_status,
                    "parsed": parsed,
                }
            )
        except Exception as exc:
            records.append(
                {
                    "song_dir": directory,
                    "tja_path": tja_path,
                    "audio_path": directory / "",
                    "title": tja_path.stem,
                    "wave": "",
                    "bpm": 0.0,
                    "offset_sec": 0.0,
                    "courses": [],
                    "course_count": 0,
                    "parse_status": "parse_error",
                    "error": str(exc),
                    "parsed": {},
                }
            )
    return records


def scan_chapter(chapter_dir: str | Path) -> list[dict[str, Any]]:
    chapter = Path(chapter_dir)
    records: list[dict[str, Any]] = []
    for song_dir in sorted(path for path in chapter.iterdir() if path.is_dir()):
        records.extend(build_song_records(song_dir))
    return records
