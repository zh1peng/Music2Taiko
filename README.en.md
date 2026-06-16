<p align="center">
  <img src="assets/logo.png" alt="Music2Taiko logo" width="220">
</p>

# Music2Taiko

[中文](README.md) | English

**Convert any music to Taiko TJA.**

Music2Taiko is a Python package and chart-authoring workflow for converting MP3/WAV/OGG songs into playable Taiko-style `.tja` drafts. It analyzes the source audio into an inspectable `drum_events[]` layer, retrieves similar charting evidence from `tja-wiki`, builds arrangement context and pattern plans, then exports OpenTaiko-ready TJA packages.

The project is not a one-click final chart replacement. It is designed to give chart authors a strong editable draft: timing anchors from the source song, difficulty shaping across `easy` / `normal` / `hard` / `oni`, and wiki-backed pattern references from existing TJA charts.

## Why It Changed

Earlier versions mostly mapped detected drum events into simple `don` / `ka` charts. The current workflow adds a local TJA knowledge base:

- `tja-wiki/` stores processed reference data from existing TJA + OGG chart packs.
- Retrieval compares a new song against the corpus using BPM, event density, duration, rhythm features, and pattern evidence.
- The LLM/skill layer uses the wiki to choose charting patterns instead of copying timing from another song.
- Python keeps the deterministic parts: audio analysis, drum events, candidate timing anchors, pattern application, TJA export, and aligned sample output.
- Export supports multi-course TJA with regular notes, big notes, rolls, and balloons.

## Workflow

```text
new song audio
  -> audio conversion / optional drum analysis
  -> drum_events[] + timing anchors
  -> tja-wiki retrieval context
  -> pattern plan from skill/LLM guidance
  -> easy / normal / hard / oni TJA courses
  -> OpenTaiko package: .tja + .ogg + review artifacts
```

The core rule is that generated notes should stay loyal to the source song's drum events. The wiki is used for charting style, density, difficulty progression, and motif design, not for cloning another chart.

## Install

```powershell
python -m pip install -e .
```

Dependencies are declared in `pyproject.toml`:

```text
librosa
numpy
soundfile
demucs
```

Demucs is treated as an optional upstream drum-stem provider. The TJA creation pipeline can still run from normal audio input.

## Quick Start

Create a four-course TJA package:

```powershell
music2taiko create-tja ".\song.ogg" --out opentaiko_out --difficulties easy,normal,hard,oni
```

Equivalent module form:

```powershell
python -m music2taiko create-tja ".\song.ogg" --out opentaiko_out --difficulties easy,normal,hard,oni
```

Use a stable short output ID when the source title is long:

```powershell
music2taiko create-tja ".\Very Long Song Name.mp3" --out opentaiko_out --song-id 001 --title "Very Long Song Name"
```

Reuse an existing arrangement context without re-running audio analysis:

```powershell
music2taiko create-tja ".\song.ogg" --out opentaiko_out --reuse-context ".\opentaiko_out\song\arrangement_context.json"
```

Provide an LLM/skill-authored pattern plan:

```powershell
music2taiko create-tja ".\song.ogg" --out opentaiko_out --pattern-plan ".\pattern_plan.json"
```

## Output

`create-tja` writes an OpenTaiko-ready package:

```text
opentaiko_out/
  <safe-song-id>/
    <safe-song-id>.tja
    <safe-song-id>.ogg
    retrieval.json
    arrangement_context.json
    pattern_plan.json
    aligned_samples.json
```

Important artifacts:

- `retrieval.json`: similar songs and reference evidence selected from `tja-wiki/corpus`.
- `arrangement_context.json`: BPM, drum-event summary, density windows, anchors, and retrieval context for skill/LLM review.
- `pattern_plan.json`: the concrete charting plan used for each difficulty.
- `aligned_samples.json`: note-level links between generated notes and source-song drum events.
- `.tja`: exported TJA with `Easy`, `Normal`, `Hard`, and `Oni` courses by default.

## TJA Wiki

The checked-in `tja-wiki/` directory is the local knowledge base:

```text
tja-wiki/
  corpus/
    manifest.json
    pattern_stats.json
    tja_summary.json
    audio_drum_event_summary.json
  01 OpenTaiko Chapter I/
  02 OpenTaiko Chapter II/
  03 OpenTaiko Chapter III/
```

It is intentionally separate from the raw `database/` folder. The wiki contains compact, reusable evidence for retrieval and LLM-readable chart design, while the raw music/chart database can remain local and large.

## Legacy Workflows

Music2Taiko still includes earlier debug/export paths:

```powershell
python -m music2taiko build-opentaiko ".\song.mp3" --out opentaiko_out --title "Song"
python -m music2taiko build ".\song.mp3" --out godot_out --title "Song"
python -m music2taiko generate ".\song.mp3" --out output\beatmaps --title "Song"
```

These are useful for PsyGodot JSON debugging, drum-event review, and older experiments. For new TJA authoring, prefer `create-tja`.

## Development

Run tests:

```powershell
python -m unittest discover -s tests
```

Validate the chart-authoring skill:

```powershell
python C:\Users\frued\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\tja-creator
```

Project layout:

```text
music2taiko/
  cli.py
  pipeline.py
  creator.py
  analysis/
  io/
  separation/
skills/tja-creator/
tja-wiki/
tests/
assets/logo.png
```

## Scope

Music2Taiko is a draft generator and analysis pipeline. It does not replace human chart authorship, but it gives authors a structured starting point: source-song drum anchors, corpus-backed pattern guidance, four-difficulty progression, TJA export, and review artifacts that make iteration practical.
