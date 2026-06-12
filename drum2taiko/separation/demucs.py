from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


CommandRunner = Callable[[Sequence[str]], object]


@dataclass(frozen=True)
class DemucsConfig:
    model: str = "htdemucs"
    device: str = ""
    segment: int | None = None


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
    command.append(str(audio_path))
    return command


def expected_drums_path(audio_path: str | Path, output_dir: str | Path, config: DemucsConfig | None = None) -> Path:
    resolved_config = config or DemucsConfig()
    return Path(output_dir) / resolved_config.model / Path(audio_path).stem / "drums.wav"


def separate_drums(
    audio_path: str | Path,
    output_dir: str | Path,
    *,
    config: DemucsConfig | None = None,
    runner: CommandRunner | None = None,
) -> Path:
    resolved_config = config or DemucsConfig()
    command = build_demucs_command(audio_path, output_dir, resolved_config)
    if runner is None:
        subprocess.run(command, check=True)
    else:
        runner(command)

    drums = expected_drums_path(audio_path, output_dir, resolved_config)
    if not drums.exists():
        raise FileNotFoundError(f"Demucs completed but drums stem was not found: {drums}")
    return drums
