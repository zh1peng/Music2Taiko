# Chart Authoring Workflow

## 1. Prepare Analysis

Use the audio file as source material, not as a command to place every transient.

Collect:

- BPM and offset
- beat grid and bar lines
- rough sections: intro, verse, pre-chorus, chorus/drop, bridge/break, outro
- candidate drum events: kick/snare/hat/cymbal/tom-like hits, accents, fills
- non-drum accents only when they are obvious chart anchors: vocal phrase endings, chord changes, melodic hits
- energy curve: quiet, build, peak, release

First check whole-song sync. If the chart feels consistently early or late, adjust `audio_offset_ms` or `chart_offset_ms` before changing note placement. Treat 30-80 ms as musically significant.

In this repo, create a scaffold:

```powershell
python tools/beatmap_generator/beatmap_generator.py <audio.mp3> examples/rhythm_drum/beatmaps --title "<title>" --output-prefix <safe_prefix>
```

Then inspect and revise. The scaffold is allowed to be wrong; it is a timing proposal.

## 2. Build A Drum-Event Layer

Prefer this pipeline:

```text
MP3/WAV
  -> drum stem or percussive-enhanced audio
  -> drum_events[]
  -> Taiko chart notes[]
  -> Godot JSON
```

Use Demucs drums output when available. Demucs-style source separation is a better starting point than full-mix onset detection because melodic attacks, bass cuts, and synth transients can look like drum hits in the full mix. If Demucs is unavailable, use HPSS/percussive-enhanced audio and mark confidence lower.

Detect onsets on the drum stem, then classify coarsely:

| Feature | Likely class |
| --- | --- |
| Low-frequency transient | `kick` |
| Mid-frequency transient | `snare` or `tom` |
| High-frequency transient | `hat` or `cymbal` |
| Full-band strong transient | `accent` / crash / fill |

Write or inspect an intermediate layer before final Don/Ka mapping:

```json
{
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
  ]
}
```

Do not try to create a complete real drum score by default. The goal is an approximate event layer that answers: where is a drum-like anchor, how strong is it, what kind of drum does it resemble, and how trustworthy is it?

## 3. Map Drum Events To Taiko Anchors

Use the event layer as rhythm evidence, then design a playable chart.

| Drum event | Taiko mapping |
| --- | --- |
| `kick` | Usually `D` |
| `snare` | `D` or `K`, chosen by motif |
| strong crash/accent | Strong `D` or phrase landing |
| `hat` / `cymbal` | Usually `K`, often thinned |
| `tom` fill | Controlled `D/K` alternation |
| ghost notes | Hard only, often removed |

Do not map real drums one-to-one. Thin dense hats, remove weak ghost notes, simplify complex fills, and choose one anchor when kick and snare collide. Real drum logic is not always good rhythm-game logic.

## 4. Plan Per Difficulty

Use separate goals, not only note-count scaling.

Easy:

- Follow downbeats and obvious phrase accents.
- Preserve groove with sparse notes.
- Avoid 16th streams.
- Prefer `D`; use `K` only for clear contrast.

Normal:

- Add half-beat support and simple call-response.
- Use short repeated motifs.
- Allow occasional `DK` or `D-K-` color.
- Give rest space at phrase ends.

Hard:

- Add high-confidence off-beats, syncopation, and short bursts.
- Use section motifs and variations.
- Keep dense sections readable as patterns.
- Avoid random color flips.

## 5. Segment The Song

For each section, decide what the chart follows:

- Intro: melody or obvious synth/guitar rhythm, low density.
- Verse: vocal phrasing, sparse support, breathing space.
- Pre-chorus/build: gradually increase density.
- Chorus/drop: main motif, strongest density, repeatable hook.
- Bridge/break: reduce notes or change texture.
- Fill/drop-prep: short burst or roll-style note group if supported.

Write this plan before editing many notes. It prevents flat charts.

## 6. Compose By Pattern

Work in half-bars or bars. Choose a pattern that matches:

- section type
- target difficulty
- accent locations
- previous one to four bars
- desired motif repetition or variation

Do not decide every note independently. A good chart reads as musical sentences.

## 7. Constraint Pass

After drafting:

- check whole-song offset again before judging local timing
- remove notes that do not align with beat grid or salient accents
- remove events with low drum confidence unless they serve a clear motif
- cap local NPS spikes
- shorten bursts that exceed difficulty goals
- add rests before/after busy sections
- reduce color switching where it feels arbitrary
- add motif recurrence in chorus/drop sections

## 8. Play Review Notes

For each difficulty, write:

- offset setting and whether sync still needs playtest
- drum-event source: Demucs drums, HPSS/percussive, manual anchors, or mixed
- what musical element it follows
- main motif
- hardest section and why
- places requiring human playtest
- changes made from the extracted scaffold

Do not call a chart final without review notes.
