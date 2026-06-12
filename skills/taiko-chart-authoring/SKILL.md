---
name: taiko-chart-authoring
description: Use when creating, improving, evaluating, or rebalancing Taiko-style rhythm game beatmaps/charts for MP3/WAV songs, especially when charts feel off-beat, need drum-event analysis, or target PsyGodot rhythm_drum JSON beatmaps with easy/normal/hard difficulties.
---

# Taiko Chart Authoring

## Core Principle

Treat charting as arranging a playable drum part over the song. Do not convert every detected onset into a note, and do not map full-audio onsets directly to Don/Ka. First build or inspect a drum-event layer: when drum-like events happen, how strong they are, which coarse drum class they resemble, and how confident the timing is. Then use pattern design, difficulty control, constraints, and play-review notes to decide the final Taiko chart.

Never copy official commercial charts. Use Taiko-like design vocabulary (`D = don`, `K = ka`, `R = roll`, `- = rest`) but produce original patterns.

## Required Workflow

1. **Analyze the song offline**
   - Detect BPM, global offset, beat grid, candidate drum events, and rough sections.
   - Calibrate `audio_offset_ms` or `chart_offset_ms` before changing Don/Ka rules. A 30-80 ms whole-song offset can make a good chart feel wrong.
   - Prefer a separated drum stem or percussive-enhanced audio over full-mix onset detection. Use Demucs drums output when available; use HPSS/percussive audio only as a fallback.
   - In this repo, `tools/beatmap_generator/beatmap_generator.py` is only a scaffold generator. Treat its output as timing proposals, not final drum truth.
   - For details, read `references/workflow.md`.

2. **Build the drum-event layer**
   - Represent drum-like timing anchors before Taiko mapping.
   - Include `drum_events[]` with `time_sec`, `quantized_time_sec`, `beat_index`, `subdivision`, `strength`, `drum_class`, `confidence`, and `is_accent`.
   - Use coarse classes first: `kick`, `snare`, `hat`, `cymbal`, `tom`, `unknown`. Do not attempt full professional drum transcription unless specifically requested.
   - Use low-frequency transients for kick-like events, mid-frequency transients for snare/tom-like events, high-frequency transients for hat/cymbal-like events, and full-band spikes for accents.

3. **Plan the difficulty curve**
   - Define section roles: intro, verse, pre-chorus, chorus/drop, bridge/break, outro.
   - Assign target density, rest frequency, burst allowance, color-change rate, and fatigue limits per section.
   - Low difficulty must preserve groove, not randomly delete notes.

4. **Choose patterns by musical phrase**
   - Author by half-bar or bar patterns, not note-by-note.
   - Use repeated motifs, call-and-response, and controlled variations.
   - Read `references/pattern-library.md` before creating or heavily revising charts.

5. **Map drum events to Don/Ka as game language**
   - Use drum events as rhythm anchors, not as a one-to-one real drum score.
   - Map kick and strong phrase landings to `D`.
   - Map hi-hat/cymbal-like answers and light off-beats to `K`.
   - Map snare to `D` or `K` depending on the section motif; prefer consistency over literal transcription.
   - Map tom fills to controlled `D/K` alternation only when the difficulty supports it.
   - Keep ghost notes and dense hat motion for hard charts only, and remove them when they create noise rather than groove.
   - Use `R` only for sustained energy, fills, transitions, or build-ups.

6. **Enforce constraints**
   - Check note density, minimum gap, burst length, color switching, repeated pattern count, rest spacing, and local difficulty spikes.
   - Read `references/evaluation-rubric.md` for constraints and scoring.

7. **Write review notes**
   - Record the offset assumption, drum-event source, why each difficulty works, which sections need playtesting, and where manual tuning changed the extracted scaffold.
   - If the chart is only an auto-extracted draft, label it as a draft.

## PsyGodot Rhythm Drum Output

For `examples/rhythm_drum`, write JSON beatmaps with:

```json
{
  "schema_version": "psygodot.beatmap.v1",
  "title": "Song Title",
  "source_audio": "song.mp3",
  "audio_offset_ms": 0,
  "difficulty": "normal",
  "generator": "taiko-chart-authoring",
  "algorithm_version": "human_authored_v1",
  "tempo_bpm": 150.0,
  "density_notes_per_sec": 1.5,
  "drum_events": [
    {
      "time_sec": 1.218,
      "quantized_time_sec": 1.234,
      "beat_index": 4,
      "subdivision": 0,
      "strength": 0.91,
      "drum_class": "kick",
      "confidence": 0.78,
      "is_accent": true
    }
  ],
  "notes": [
    {"id": "normal_0001", "time_sec": 1.234, "lane": "don", "window_ms": 110}
  ]
}
```

Use `lane: "don"` for `D`, `lane: "ka"` for `K`. Roll notes are not implemented in the current game; represent rolls only in review notes unless the runtime supports them.

If the current runtime or schema cannot consume `drum_events`, keep them in authoring metadata or a sidecar file and still write playable `notes[]` for Godot.

## Quality Bar

A playable chart should have:

- notes aligned to beat grid or clear musical accents
- offset reviewed before judging timing quality
- Taiko notes derived from drum-event anchors or clearly justified musical accents
- a memorable motif per major section
- difficulty that rises and falls with the song structure
- readable rests and phrase endings
- no long stretches of unmotivated dense notes
- no abrupt difficulty spikes unless tied to an obvious fill/drop
- review notes explaining remaining risks

If automatic extraction conflicts with playability, prefer playability.
