# AGENTS.md

## Project

Drum2Taiko is an independent chart-authoring project for converting MP3/WAV music into an approximate drum-event layer and then into playable Taiko-style `don` / `ka` beatmaps.

## Working Rules

- Prefer small, verifiable changes.
- Treat Demucs as an optional upstream drum-stem provider, not a required runtime dependency.
- Do not map full-mix onsets directly to `don` / `ka` when improving chart quality.
- Check or expose `audio_offset_ms` / `chart_offset_ms` before changing local note placement.
- Keep `drum_events[]` as the intermediate layer between audio analysis and Taiko `notes[]`.
- Preserve PsyGodot rhythm_drum JSON compatibility unless explicitly changing output format.

## Key Files

- Package CLI: `drum2taiko/cli.py`
- Pipeline orchestration: `drum2taiko/pipeline.py`
- Audio/drum-event analysis: `drum2taiko/analysis/candidates.py`
- Demucs wrapper: `drum2taiko/separation/demucs.py`
- PsyGodot exporter: `drum2taiko/io/psygodot.py`
- Tests: `tests/`
- Skill entry, currently secondary documentation: `skills/taiko-chart-authoring/SKILL.md`

## Verification

Run focused tests after generator changes:

```powershell
python -m unittest discover -s tests
```

Run skill validation after skill metadata or `SKILL.md` changes when the validator is available:

```powershell
python C:\Users\frued\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\taiko-chart-authoring
```
