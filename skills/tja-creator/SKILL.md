---
name: tja-creator
description: Use when creating, improving, evaluating, or rebalancing TJA/Taiko-style rhythm game beatmaps/charts for MP3/WAV/OGG songs, especially when charts feel off-beat, need TJA parsing, drum-event analysis, or target PsyGodot rhythm_drum JSON beatmaps with easy/normal/hard difficulties.
---

# TJA Creator

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
   - Low difficulty must preserve the source groove, not randomly delete notes.
   - Do not treat difficulty as note count only. For dense songs, Easy may still contain many notes because it should cover the basic drum pulse. Increase difficulty mainly through pattern complexity: color changes, syncopation, bursts, rolls, big notes, phrase variation, and sustained streams.
   - Standard TJA exports should include `easy`, `normal`, `hard`, and `oni`. Keep clear progression: Easy covers core drum anchors with simple repeated patterns; Normal adds readable answers; Hard adds bursts and syncopation; Oni uses the richest pattern language and highest sustained complexity.

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
  "generator": "tja-creator",
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

## LLM-Assisted Generation Flow

For new-song TJA generation, use the package as a deterministic toolchain and keep chart design decisions in the skill/LLM layer:

1. Run `music2taiko create-tja <audio> --out <dir> --difficulties easy,normal,hard,oni` to generate the four standard playable courses by default:
   - `arrangement_context.json`: source-song drum events, candidate timing anchors, retrieval matches, and pattern-plan schema.
   - `pattern_plan.json`: default editable pattern plan.
   - `.tja`, `.ogg`, `retrieval.json`, and `aligned_samples.json`.
2. Keep a lead-in safety window. Do not place playable notes before `--lead-in-sec` seconds, default `2.5`, unless the user explicitly asks for an instant-start chart.
3. Review `arrangement_context.json` with `references/retrieval-guide.md`, `references/corpus-patterns.md`, `references/audio-to-chart-mapping.md`, and `references/evaluation-rubric.md`.
4. If the default plan is too generic, write a revised `pattern_plan.json`. For multiple courses, prefer:
   ```json
   {
     "difficulties": {
       "easy": {"difficulty": "easy", "level": 3, "sections": []},
       "normal": {"difficulty": "normal", "level": 5, "sections": []},
       "hard": {"difficulty": "hard", "level": 6, "sections": []},
       "oni": {"difficulty": "oni", "level": 8, "sections": []}
     }
   }
   ```
   Borrow pattern language and density from similar corpus songs, but place notes only on the new song's candidate anchors or clearly justified musical accents.
   Anchor coverage should follow the song. For a drum-dense song, Easy should still cover the basic groove and may use 60-80% of reliable anchors with simple D-heavy motifs; Normal can use 75-90% with more K answers; Hard/Oni can use most anchors while increasing burst, color, big-note, and roll complexity. For sparse songs, do not invent density just to satisfy a ratio.
5. Re-run `music2taiko create-tja ... --difficulties easy,normal,hard,oni --pattern-plan <pattern_plan.json>` to apply the design plan to the source-song anchors.
6. If audio and context are already generated, skip decoding/analysis and re-render from note generation onward with `--reuse-context <arrangement_context.json>`.
7. Review the exported TJA and `aligned_samples.json`; revise the plan rather than copying source chart timing.

Pattern plans are design instructions, not timing sources. Python maps the plan onto the new song's drum anchors; the LLM/skill decides motif, density, color flow, and roll/balloon intent.

## Reference Routing

Load references only when relevant:

- Read `references/tja-format.md` when parsing, validating, or writing TJA files, especially when handling `3/4` big notes, `5/6/7/9` duration starts, `8` ends, `BALLOON`, `#BPMCHANGE`, `#MEASURE`, or `#DELAY`.
- Read `references/corpus-overview.md` when choosing target density, course expectations, note-type ratios, or corpus-level style assumptions.
- Read `references/song-index.md` when selecting numbered reference songs from the local database.
- Read `references/corpus-patterns.md` when choosing observed pattern families from the processed corpus.
- Read `references/retrieval-guide.md` when using the local corpus as retrieval support for a new chart.
- Read `references/audio-to-chart-mapping.md` when mapping OGG/MP3/WAV audio features and drum events into chart decisions.
- Read `references/output-compatibility.md` before exporting TJA, PsyGodot JSON, audio copies, folders, or generated chart packs, especially when source titles are long or contain punctuation/Unicode.
- Read `references/pattern-library.md` when composing or revising playable bar-level motifs.
- Read `references/evaluation-rubric.md` before calling a draft playable or final.

The processed corpus data lives under `tja-wiki/`. Treat the Markdown references as LLM-readable summaries and the JSON files as supporting evidence. Do not load the raw database or all wiki JSON into context unless a task specifically needs it.
