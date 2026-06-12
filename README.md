# Drum2Taiko

Drum2Taiko is a Python package for generating approximate Taiko-style beatmaps from MP3/WAV music. It uses existing audio libraries for source separation and onset analysis, then adds the project-specific layer: drum events, Taiko `don` / `ka` mapping, difficulty shaping, and PsyGodot rhythm_drum JSON export.

## Workflow

```text
MP3/WAV source audio
  -> Demucs drums stem, preferred
  -> librosa HPSS/percussive audio, fallback
  -> drum_events[]
  -> Taiko notes[]
  -> PsyGodot JSON
```

Demucs is optional. When it is available, use it to produce `drums.wav` before analysis. When it is not available, Drum2Taiko falls back to percussive analysis through librosa for supported audio.

## Package Layout

```text
drum2taiko/
  cli.py
  pipeline.py
  analysis/
    candidates.py
  separation/
    demucs.py
  io/
    psygodot.py
tests/
pyproject.toml
```

## Install

For package development:

```powershell
python -m pip install -e .
```

For MP3/WAV analysis with librosa:

```powershell
python -m pip install -e ".[audio]"
```

For optional Demucs separation:

```powershell
python -m pip install -e ".[audio,demucs]"
```

## Usage

Generate beatmaps with librosa HPSS fallback:

```powershell
python -m drum2taiko generate path\to\song.mp3 --out output\beatmaps --title "Song"
```

Run Demucs first and analyze its drums stem:

```powershell
python -m drum2taiko generate path\to\song.mp3 --out output\beatmaps --use-demucs
```

Use an existing drum stem:

```powershell
python -m drum2taiko generate path\to\song.mp3 --out output\beatmaps --drum-stem path\to\drums.wav
```

Only separate drums:

```powershell
python -m drum2taiko separate path\to\song.mp3 --out output\stems
```

Outputs are:

```text
*_easy.json
*_normal.json
*_hard.json
```

Each JSON contains `drum_events[]`, playable `notes[]`, offset metadata, difficulty metadata, and PsyGodot rhythm_drum compatibility fields.

## Tests

```powershell
python -m unittest discover -s tests
```

## Design Notes

- Do not map full-mix onsets directly to `don` / `ka`.
- Keep `drum_events[]` as the intermediate layer between audio analysis and Taiko notes.
- Treat Demucs as the preferred drum-stem provider, not a required runtime dependency.
- Treat PsyGodot JSON as an exporter, not the center of the package design.
