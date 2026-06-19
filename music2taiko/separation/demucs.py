from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from os import environ, pathsep
from pathlib import Path
from typing import Any, Callable, Sequence


CommandRunner = Callable[..., object]


@dataclass(frozen=True)
class DemucsConfig:
    model: str = "htdemucs"
    device: str = ""
    segment: int | None = None
    output_format: str = "mp3"


def build_demucs_command(audio_path: str | Path, output_dir: str | Path, config: DemucsConfig | None = None) -> list[str]:
    resolved_config = config or DemucsConfig()
    command = [
        sys.executable,
        "-m",
        "demucs",
        "-n",
        resolved_config.model,
        "--two-stems=drums",
        "-o",
        str(output_dir),
    ]
    if resolved_config.device:
        command.extend(["-d", resolved_config.device])
    if resolved_config.segment is not None:
        command.extend(["--segment", str(resolved_config.segment)])
    if resolved_config.output_format == "mp3":
        command.append("--mp3")
    elif resolved_config.output_format != "wav":
        raise ValueError(f"unsupported Demucs output format: {resolved_config.output_format}")
    command.append(str(audio_path))
    return command


def expected_drums_path(audio_path: str | Path, output_dir: str | Path, config: DemucsConfig | None = None) -> Path:
    resolved_config = config or DemucsConfig()
    return Path(output_dir) / resolved_config.model / Path(audio_path).stem / f"drums.{resolved_config.output_format}"


def build_demucs_subprocess_env(
    *,
    ffmpeg_locator: Callable[[], tuple[str, str]] | None = None,
) -> dict[str, Any]:
    env: dict[str, Any] = dict(environ)
    env["PYTHONIOENCODING"] = "utf-8"

    locator = ffmpeg_locator
    if locator is None:
        try:
            from static_ffmpeg.run import get_or_fetch_platform_executables_else_raise, get_platform_dir
        except Exception:
            locator = None
        else:
            platform_dir = Path(get_platform_dir())
            suffix = ".exe" if sys.platform == "win32" else ""
            installed = (platform_dir / f"ffmpeg{suffix}", platform_dir / f"ffprobe{suffix}")
            if installed[0].exists() and installed[1].exists():
                locator = lambda: (str(installed[0]), str(installed[1]))
            else:
                locator = get_or_fetch_platform_executables_else_raise

    if locator is not None:
        try:
            ffmpeg_exe, _ = locator()
        except Exception:
            pass
        else:
            ffmpeg_dir = str(Path(ffmpeg_exe).parent)
            env["PATH"] = pathsep.join([ffmpeg_dir, env.get("PATH", "")])

    return env


def separate_drums(
    audio_path: str | Path,
    output_dir: str | Path,
    *,
    config: DemucsConfig | None = None,
    runner: CommandRunner | None = None,
) -> Path:
    resolved_config = config or DemucsConfig()
    command = build_demucs_command(audio_path, output_dir, resolved_config)
    env = build_demucs_subprocess_env()
    if runner is None:
        subprocess.run(command, check=True, env=env)
    else:
        runner(command, env=env)

    drums = expected_drums_path(audio_path, output_dir, resolved_config)
    if not drums.exists():
        raise FileNotFoundError(f"Demucs completed but drums stem was not found: {drums}")
    return drums
