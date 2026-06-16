# Corpus Overview

Use this reference for corpus-level style and density guidance. It is an LLM-readable summary of generated data under `tja-wiki/corpus/`.

## Current Evidence Scope

Processed source collections:

- `01 OpenTaiko Chapter I`
- `02 OpenTaiko Chapter II`
- `03 OpenTaiko Chapter III`

Current totals:

- 107 song records
- Parse status: ok=107
- Courses: Edit=60, Oni=107, Hard=107, Normal=107, Easy=107
- BPM range: 21.0 to 327.375
- TJA offset range: -15.968s to 0.3s

Treat Chapter names as source metadata only. Retrieval should primarily use song ID, BPM, density, audio features, note types, and pattern similarity.

## Course Density

Average notes/sec below is computed per course using all available songs for that course.

| Course | Songs | Avg level | Hit notes | Duration notes | Avg hit notes/sec |
| --- | ---: | ---: | ---: | ---: | ---: |
| Easy | 107 | 3.36 | 22,026 | 1,096 | 1.35 |
| Normal | 107 | 5.07 | 38,700 | 1,120 | 2.36 |
| Hard | 107 | 6.50 | 62,564 | 1,061 | 3.82 |
| Oni | 107 | 8.53 | 97,831 | 836 | 5.98 |
| Edit | 60 | 9.55 | 64,475 | 428 | 7.23 |

Use these as starting targets, not hard caps. Local sections should still rise and fall with the song.

## Note Type Counts

Hit note totals by course:

| Course | Don | Ka | Big don | Big ka |
| --- | ---: | ---: | ---: | ---: |
| Easy | 11,140 | 8,535 | 1,449 | 902 |
| Normal | 20,152 | 15,783 | 1,654 | 1,111 |
| Hard | 33,470 | 26,028 | 1,931 | 1,135 |
| Oni | 50,850 | 43,506 | 2,131 | 1,344 |
| Edit | 33,163 | 29,262 | 1,215 | 835 |

Observations:

- `don` remains the most common hit type in every course.
- `ka` becomes more prominent as density rises, but it does not replace `don` as the main anchor.
- Big notes appear in every course and should be preserved as separate authoring choices.
- Easy still contains `ka`, big notes, rolls, and balloons; low difficulty is not only `don`.

## Duration Note Counts

Duration note totals by course:

| Course | Roll | Big roll | Balloon | Special balloon |
| --- | ---: | ---: | ---: | ---: |
| Easy | 754 | 153 | 152 | 37 |
| Normal | 809 | 157 | 123 | 31 |
| Hard | 774 | 147 | 110 | 30 |
| Oni | 552 | 88 | 174 | 22 |
| Edit | 201 | 68 | 74 | 85 |

Observations:

- Rolls are common across all standard courses.
- Balloons appear across all courses and usually carry explicit hit counts through `BALLOON`.
- Edit has high hit-note density but relatively modest duration-note count compared with its hit density.

## Audio Event Summary

Current OGG analysis uses HPSS/percussive extraction and coarse drum-event classification.

| Drum class | Count | Interpretation |
| --- | ---: | --- |
| `unknown` | 23,871 | Ambiguous transients; use cautiously |
| `hat` | 13,417 | High-frequency rhythmic motion |
| `snare` | 12,485 | Mid-frequency hits and backbeat-like anchors |
| `tom` | 5,342 | Mid/low fills or ambiguous drum hits |
| `kick` | 2,716 | Low-frequency anchors |
| `cymbal` | 1,293 | Full/high accents and crashes |

The high `unknown` count means audio classification is evidence, not ground truth. Use it to find candidate anchors, then apply charting judgment and pattern constraints.

## Practical Use

When authoring a new chart:

1. Use TJA/audio analysis to estimate BPM, offset, beat grid, drum-event density, and section energy.
2. Pick target course density from this corpus as a baseline.
3. Retrieve songs or patterns with similar BPM and event density.
4. Reuse style principles, not exact note placement.
5. Validate with the evaluation rubric and note-level review.
