# Audio To Chart Mapping

Use this reference when converting audio analysis into chart decisions. Current evidence includes OGG drum-event summaries, but not yet a full note-level aligned sample set. Treat these rules as conservative authoring guidance until `aligned_samples` exists.

## Current Audio Evidence

Processed audio source:

- 107 OGG files from the current corpus
- HPSS/percussive extraction
- coarse drum classes: `kick`, `snare`, `hat`, `cymbal`, `tom`, `unknown`

Observed drum-event counts:

| Drum class | Count | Interpretation |
| --- | ---: | --- |
| `unknown` | 23,871 | Ambiguous transients; use cautiously |
| `hat` | 13,417 | High-frequency rhythmic motion |
| `snare` | 12,485 | Mid-frequency hits and backbeat-like anchors |
| `tom` | 5,342 | Mid/low fills or ambiguous drum hits |
| `kick` | 2,716 | Low-frequency anchors |
| `cymbal` | 1,293 | Full/high accents and crashes |

Do not use event counts as direct note counts. They are candidate anchors.

## Mapping Principles

| Audio event | Chart response |
| --- | --- |
| strong low transient / kick-like event | Prefer `don` or `big_don` on structural accents |
| snare-like event | Use `don` or `ka` according to the section motif |
| hat-like event | Use `ka` sparingly, especially for off-beat answers |
| cymbal-like event | Use phrase accent, `big_don`, `big_ka`, roll, or section change marker |
| tom/fill-like event | Use short `don`/`ka` burst or roll if difficulty supports it |
| unknown event | Ignore unless it aligns with beat grid and supports a clear motif |

## Offset First

Before deciding whether mapping is wrong, check whole-song offset:

- Compare TJA `OFFSET` against perceived sync.
- Treat 30-80 ms as musically significant.
- Do not move local notes to compensate for a global offset error.

Current corpus offsets range from -15.968s to 0.3s, so large offsets are real in the source data. Do not assume all charts start near 0.

## Density Decisions

Use audio event density to choose how much of the rhythm to express:

- Low event density: use sparse anchors and phrase markings.
- Mid event density: use repeated motifs and simple responses.
- High event density: select a playable subset; do not chart every event.
- Sustained peak energy: allow denser 8- or 16-slot patterns.
- Transition/fill: consider short bursts, rolls, or balloons.

Course density should follow `corpus-overview.md` before local exceptions:

- Easy: about 1.3 hit notes/sec baseline
- Normal: about 2.4 hit notes/sec baseline
- Hard: about 3.8 hit notes/sec baseline
- Oni: about 6.0 hit notes/sec baseline
- Edit: about 7.2 hit notes/sec baseline

## Section Behavior

Use the audio energy curve, not only onset count:

- Intro: sparse anchors; establish timing.
- Verse: preserve groove and leave space.
- Build: increase density or color gradually.
- Chorus/drop: strongest recurring motif.
- Bridge/break: simplify or change texture.
- Fill/transition: short burst, roll, or balloon when musically justified.

## What Not To Do

Avoid these failure modes:

- full-mix onset to `don`/`ka` one-to-one mapping
- mapping every hat event to `ka`
- using `unknown` events as notes without musical justification
- generating dense charts without recurring motifs
- ignoring `big_don`, `big_ka`, rolls, and balloons in training data
- copying a source TJA measure into a new song without matching the new audio phrase

## Next Evidence Needed

The next corpus pipeline should produce `aligned_samples` so this reference can move from heuristic mapping to evidence-based mapping.
