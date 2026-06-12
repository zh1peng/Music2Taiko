from __future__ import annotations

import argparse
from pathlib import Path

from drum2taiko.pipeline import generate_beatmaps
from drum2taiko.separation.demucs import separate_drums


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="drum2taiko", description="Generate Taiko-style PsyGodot beatmaps.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    separate_parser = subparsers.add_parser("separate", help="Create a Demucs drums stem.")
    separate_parser.add_argument("audio", help="Input MP3/WAV file")
    separate_parser.add_argument("--out", required=True, help="Directory for separated stems")

    generate_parser = subparsers.add_parser("generate", help="Generate PsyGodot beatmap JSON files.")
    generate_parser.add_argument("audio", help="Input MP3/WAV file")
    generate_parser.add_argument("--out", required=True, help="Directory for generated beatmaps")
    generate_parser.add_argument("--title", default="", help="Display title; defaults to input filename")
    generate_parser.add_argument("--output-prefix", default="", help="Filename prefix for generated JSON files")
    generate_parser.add_argument("--audio-offset-ms", type=float, default=0.0, help="Metadata for song-level audio offset")
    generate_parser.add_argument("--chart-offset-ms", type=float, default=0.0, help="Shift generated chart note times")
    generate_parser.add_argument("--drum-stem", default="", help="Separated drums WAV/MP3 from Demucs or similar")
    generate_parser.add_argument("--use-demucs", action="store_true", help="Run Demucs first and analyze drums.wav")
    generate_parser.add_argument("--stems-dir", default="", help="Directory for Demucs output when --use-demucs is set")

    args = parser.parse_args(argv)
    if args.command == "separate":
        print(separate_drums(Path(args.audio), Path(args.out)))
        return 0

    paths = generate_beatmaps(
        Path(args.audio),
        Path(args.out),
        title=args.title or None,
        output_prefix=args.output_prefix or None,
        audio_offset_ms=args.audio_offset_ms,
        chart_offset_ms=args.chart_offset_ms,
        drum_stem_path=args.drum_stem or None,
        use_demucs=args.use_demucs,
        stems_dir=args.stems_dir or None,
    )
    for difficulty in ("easy", "normal", "hard"):
        print(paths[difficulty])
    return 0
