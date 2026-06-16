# Music2Taiko

[中文](README.md) | English

Music2Taiko is a Python package for turning MP3/WAV music into approximate Taiko-style beatmaps. It generates an inspectable `drum_events[]` layer first, then maps those events into `don` / `ka` notes and exports OpenTaiko/TJA packages. PsyGodot JSON is still available for debugging and compatibility.

The project is experimental. The goal is not to produce final charts in one click, but to create a useful draft that can be reviewed, tested in Godot, and iterated on.

## Workflow

```text
MP3/WAV audio
  -> Demucs drum stem, preferred
  -> librosa onset/drum analysis
  -> drum_events[]
  -> Taiko notes[]
  -> OpenTaiko TJA + OGG
```

## Features

- Demucs drum stem separation.
- Drum-event extraction from drum stems.
- `drum_events[]` with timing, quantized timing, strength, coarse drum class, confidence, band strengths, and timing error.
- `easy` / `normal` / `hard` chart generation.
- Normal-difficulty long-gap backfill.
- Deterministic short Taiko motifs for normal `don` / `ka` mapping.
- OpenTaiko/TJA package export with `.tja` chart and `.ogg` audio.
- PsyGodot rhythm_drum JSON export for debugging.
- `review_report.json` with offset, density, note-gap, lane distribution, and warning diagnostics.

## Install

```powershell
python -m pip install -e .
```

Dependencies are declared in `pyproject.toml`:

```text
librosa
numpy
demucs
```

For CUDA Demucs, install a CUDA-enabled PyTorch build for your hardware before installing this package. Do not install the PyPI package named `audio`; it is unrelated to Demucs or this project.

## Usage

The repository, package distribution, primary CLI, and Python implementation package are all named Music2Taiko / `music2taiko`.

Run the full OpenTaiko/TJA package workflow:

```powershell
python -m music2taiko build-opentaiko ".\song.mp3" --out opentaiko_out --title "Song"
```

Output:

```text
opentaiko_out/
  Song/
    Song.tja
    Song.ogg
    review_report.json
    debug_json/
    stems/
```

Run the PsyGodot JSON workflow:

```powershell
python -m music2taiko build ".\song.mp3" --out godot_out --title "Song"
```

Generate beatmaps without Demucs:

```powershell
python -m music2taiko generate ".\song.mp3" --out output\beatmaps --title "Song"
```

Generate with Demucs:

```powershell
python -m music2taiko generate ".\song.mp3" --out output\beatmaps --title "Song" --use-demucs
```

On Windows, MP3 stem output can avoid TorchCodec/shared-FFmpeg WAV save issues:

```powershell
python -m music2taiko generate ".\song.mp3" --out output\beatmaps --title "Song" --use-demucs --demucs-device cuda --demucs-model htdemucs --demucs-segment 7 --demucs-format mp3
```

Use an existing drum stem:

```powershell
python -m music2taiko generate ".\song.mp3" --out output\beatmaps --title "Song" --drum-stem ".\drums.mp3"
```

## Outputs

```text
godot_out/
  <title>_easy.json
  <title>_normal.json
  <title>_hard.json
  review_report.json
  stems/
```

Each beatmap contains `drum_events[]`, playable `notes[]`, offset metadata, difficulty metadata, and PsyGodot compatibility fields.

## Development

```powershell
python -m unittest discover
```

## Scope

Music2Taiko is not a full drum transcription engine or a final chart authoring replacement. It is a draft generator and analysis pipeline for iterating on drum-event quality, offset, density, difficulty shaping, and Taiko `don` / `ka` mapping.
