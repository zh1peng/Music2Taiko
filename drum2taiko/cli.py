from __future__ import annotations

import argparse
from pathlib import Path

from drum2taiko.pipeline import (
    DEFAULT_TJA_DIFFICULTIES,
    build_beatmap_package,
    build_opentaiko_package,
    create_tja_package,
    generate_beatmaps,
)
from drum2taiko.separation.demucs import DemucsConfig, separate_drums


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="drum2taiko", description="Generate Taiko-style PsyGodot beatmaps.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    separate_parser = subparsers.add_parser("separate", help="Create a Demucs drums stem.")
    separate_parser.add_argument("audio", help="Input MP3/WAV file")
    separate_parser.add_argument("--out", required=True, help="Directory for separated stems")
    separate_parser.add_argument("--demucs-model", default="htdemucs", help="Demucs model name")
    separate_parser.add_argument("--demucs-device", default="", help="Demucs device, for example cuda or cpu")
    separate_parser.add_argument("--demucs-segment", type=int, default=None, help="Demucs segment length in seconds")
    separate_parser.add_argument("--demucs-format", choices=["wav", "mp3"], default="wav", help="Demucs stem output format")

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
    generate_parser.add_argument("--demucs-model", default="htdemucs", help="Demucs model name")
    generate_parser.add_argument("--demucs-device", default="", help="Demucs device, for example cuda or cpu")
    generate_parser.add_argument("--demucs-segment", type=int, default=None, help="Demucs segment length in seconds")
    generate_parser.add_argument("--demucs-format", choices=["wav", "mp3"], default="wav", help="Demucs stem output format")

    build_parser = subparsers.add_parser("build", help="Run the full MP3/WAV to beatmap draft workflow.")
    build_parser.add_argument("audio", help="Input MP3/WAV file")
    build_parser.add_argument("--out", required=True, help="Directory for Godot-ready generated files")
    build_parser.add_argument("--title", default="", help="Display title; defaults to input filename")
    build_parser.add_argument("--output-prefix", default="", help="Filename prefix for generated JSON files")
    build_parser.add_argument("--audio-offset-ms", type=float, default=0.0, help="Metadata for song-level audio offset")
    build_parser.add_argument("--chart-offset-ms", type=float, default=0.0, help="Shift generated chart note times")
    build_parser.add_argument("--stems-dir", default="", help="Directory for Demucs output")
    build_parser.add_argument("--demucs-model", default="htdemucs", help="Demucs model name")
    build_parser.add_argument("--demucs-device", default="cuda", help="Demucs device, for example cuda or cpu")
    build_parser.add_argument("--demucs-segment", type=int, default=7, help="Demucs segment length in seconds")
    build_parser.add_argument("--demucs-format", choices=["wav", "mp3"], default="mp3", help="Demucs stem output format")

    opentaiko_parser = subparsers.add_parser("build-opentaiko", help="Run the full workflow and export TJA + OGG.")
    opentaiko_parser.add_argument("audio", help="Input MP3/WAV file")
    opentaiko_parser.add_argument("--out", required=True, help="Directory for OpenTaiko-ready package output")
    opentaiko_parser.add_argument("--title", default="", help="Display title; defaults to input filename")
    opentaiko_parser.add_argument("--output-prefix", default="", help="Folder and filename prefix for TJA/OGG output")
    opentaiko_parser.add_argument("--audio-offset-ms", type=float, default=0.0, help="Metadata for song-level audio offset")
    opentaiko_parser.add_argument("--chart-offset-ms", type=float, default=0.0, help="Shift generated chart note times")
    opentaiko_parser.add_argument("--stems-dir", default="", help="Directory for Demucs output")
    opentaiko_parser.add_argument("--demucs-model", default="htdemucs", help="Demucs model name")
    opentaiko_parser.add_argument("--demucs-device", default="cuda", help="Demucs device, for example cuda or cpu")
    opentaiko_parser.add_argument("--demucs-segment", type=int, default=7, help="Demucs segment length in seconds")
    opentaiko_parser.add_argument("--demucs-format", choices=["wav", "mp3"], default="mp3", help="Demucs stem output format")

    create_tja_parser = subparsers.add_parser("create-tja", help="Create a multi-difficulty TJA draft from a new song.")
    create_tja_parser.add_argument("audio", help="Input MP3/WAV/OGG file")
    create_tja_parser.add_argument("--out", required=True, help="Directory for generated TJA package")
    create_tja_parser.add_argument("--difficulty", default="oni", choices=["easy", "normal", "hard", "oni", "edit"])
    create_tja_parser.add_argument(
        "--difficulties",
        default="",
        help=f"Comma-separated courses; defaults to --difficulty unless set, for example {','.join(DEFAULT_TJA_DIFFICULTIES)}",
    )
    create_tja_parser.add_argument("--title", default="", help="Display title; defaults to input filename")
    create_tja_parser.add_argument("--song-id", default="", help="Stable short song ID for output filenames")
    create_tja_parser.add_argument("--output-prefix", default="", help="Safe output prefix; defaults to normalized title")
    create_tja_parser.add_argument("--corpus-dir", default="", help="Derived corpus directory for retrieval")
    create_tja_parser.add_argument("--pattern-plan", default="", help="JSON pattern plan produced by LLM/skill")
    create_tja_parser.add_argument("--reuse-context", default="", help="Existing arrangement_context.json to render without audio analysis")
    create_tja_parser.add_argument("--lead-in-sec", type=float, default=2.5, help="Do not place notes before this time")
    create_tja_parser.add_argument("--level", type=int, default=None, help="TJA course level override")

    args = parser.parse_args(argv)
    if args.command == "separate":
        config = DemucsConfig(
            model=args.demucs_model,
            device=args.demucs_device,
            segment=args.demucs_segment,
            output_format=args.demucs_format,
        )
        print(separate_drums(Path(args.audio), Path(args.out), config=config))
        return 0

    if args.command == "build":
        result = build_beatmap_package(
            Path(args.audio),
            Path(args.out),
            title=args.title or None,
            output_prefix=args.output_prefix or None,
            audio_offset_ms=args.audio_offset_ms,
            chart_offset_ms=args.chart_offset_ms,
            stems_dir=args.stems_dir or None,
            demucs_model=args.demucs_model,
            demucs_device=args.demucs_device,
            demucs_segment=args.demucs_segment,
            demucs_format=args.demucs_format,
        )
        for difficulty in ("easy", "normal", "hard"):
            print(result["beatmaps"][difficulty])
        print(result["report"])
        return 0

    if args.command == "build-opentaiko":
        result = build_opentaiko_package(
            Path(args.audio),
            Path(args.out),
            title=args.title or None,
            output_prefix=args.output_prefix or None,
            audio_offset_ms=args.audio_offset_ms,
            chart_offset_ms=args.chart_offset_ms,
            stems_dir=args.stems_dir or None,
            demucs_model=args.demucs_model,
            demucs_device=args.demucs_device,
            demucs_segment=args.demucs_segment,
            demucs_format=args.demucs_format,
        )
        print(result["package_dir"])
        print(result["tja"])
        print(result["audio"])
        print(result["report"])
        return 0

    if args.command == "create-tja":
        difficulties = [item.strip().lower() for item in args.difficulties.split(",") if item.strip()] or None
        result = create_tja_package(
            Path(args.audio),
            Path(args.out),
            difficulty=args.difficulty,
            difficulties=difficulties,
            title=args.title or None,
            song_id=args.song_id,
            output_prefix=args.output_prefix or None,
            corpus_dir=Path(args.corpus_dir) if args.corpus_dir else None,
            pattern_plan_path=Path(args.pattern_plan) if args.pattern_plan else None,
            reuse_context_path=Path(args.reuse_context) if args.reuse_context else None,
            lead_in_sec=args.lead_in_sec,
            level=args.level,
        )
        print(result["package_dir"])
        print(result["tja"])
        print(result["audio"])
        print(result["retrieval"])
        print(result["arrangement_context"])
        print(result["pattern_plan"])
        print(result["aligned_samples"])
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
        demucs_model=args.demucs_model,
        demucs_device=args.demucs_device,
        demucs_segment=args.demucs_segment,
        demucs_format=args.demucs_format,
    )
    for difficulty in ("easy", "normal", "hard"):
        print(paths[difficulty])
    return 0
