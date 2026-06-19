from __future__ import annotations

from pathlib import Path
from typing import Callable
from urllib.parse import urlparse


Downloader = Callable[[str, Path], Path]


def _with_default_scheme(value: str) -> str:
    lowered = value.lower()
    if lowered.startswith(("youtube.com/", "www.youtube.com/", "m.youtube.com/", "youtu.be/")):
        return f"https://{value}"
    return value


def _is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _is_youtube_url(value: str) -> bool:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    return (
        host == "youtu.be"
        or host == "youtube.com"
        or host.endswith(".youtube.com")
        or host == "youtube-nocookie.com"
        or host.endswith(".youtube-nocookie.com")
    )


def _ffmpeg_location() -> str | None:
    try:
        import imageio_ffmpeg
    except ModuleNotFoundError:
        return None
    return imageio_ffmpeg.get_ffmpeg_exe()


def _existing_download_path(ydl: object, info: dict, output_dir: Path) -> Path:
    candidates: list[Path] = []
    for item in info.get("requested_downloads", []) or []:
        if item.get("filepath"):
            candidates.append(Path(item["filepath"]))
        if item.get("filename"):
            candidates.append(Path(item["filename"]))

    if info.get("filepath"):
        candidates.append(Path(info["filepath"]))

    prepare_filename = getattr(ydl, "prepare_filename", None)
    if callable(prepare_filename):
        prepared = Path(prepare_filename(info))
        candidates.append(prepared)
        candidates.append(prepared.with_suffix(".mp3"))

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0] if candidates else output_dir


def download_youtube_audio(url: str, output_dir: str | Path) -> Path:
    from yt_dlp import YoutubeDL

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    options = {
        "format": "bestaudio/best",
        "js_runtimes": {"node": {}},
        "noplaylist": True,
        "outtmpl": str(output / "%(title).200B-%(id)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "remote_components": ["ejs:github"],
    }
    ffmpeg = _ffmpeg_location()
    if ffmpeg:
        options["ffmpeg_location"] = ffmpeg

    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        return _existing_download_path(ydl, info, output)


def resolve_audio_source(
    value: str | Path,
    download_dir: str | Path,
    *,
    downloader: Downloader = download_youtube_audio,
) -> Path:
    source = _with_default_scheme(str(value))
    if not _is_url(source):
        return Path(value)
    if not _is_youtube_url(source):
        raise ValueError("Only YouTube URLs are supported as remote audio input.")
    return downloader(source, Path(download_dir))
