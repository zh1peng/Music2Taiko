# Evaluation Rubric

Use this rubric to score draft charts and decide what to revise.

## Objective Score

```text
score =
  musical_fit * 0.35
+ difficulty_match * 0.25
+ pattern_coherence * 0.20
+ controlled_variety * 0.10
+ section_shape * 0.10
- fatigue_penalty
- random_jump_penalty
- overfill_penalty
```

## Musical Fit

Reward:

- chart-wide offset has been checked before local note edits
- notes are supported by drum-event anchors or intentional non-drum musical accents
- notes on downbeats, beat grid, or clear syncopated accents
- section starts and phrase endings marked intentionally
- chorus/drop motifs matching the hook
- fills placed before transitions

Penalize:

- whole chart feels consistently early or late with no `audio_offset_ms` or `chart_offset_ms` review
- direct full-mix onset conversion with no drum-event review
- notes caused by weak transient noise
- dense notes during quiet/vocal-light material without musical reason
- notes far from beat grid or clear accent

## Difficulty Match

Check:

- average notes per second
- peak notes per second over 2-second windows
- minimum gap between notes
- max 16th burst length
- color switch rate
- rest frequency
- longest continuous play section

Suggested ranges are song-dependent, but use these starting points:

Easy:

- sparse downbeats and accents
- no long 16th bursts
- generous rests
- mostly `D`

Normal:

- regular 8th motion
- short color motifs
- occasional two- or three-note bursts
- phrase-end rests

Hard:

- denser motifs and syncopation
- controlled bursts
- higher color variation
- still readable as repeated patterns

## Pattern Coherence

Reward:

- repeated motif in each major section
- variations at phrase endings
- call-and-response across adjacent bars
- hard charts that are difficult but learnable

Penalize:

- every bar unrelated to the previous bar
- color assignment based only on frequency band
- long streams without motif

## Controlled Variety

A chart should not be flat, but variation must be motivated.

Good variation:

- change ending every 2 or 4 bars
- add fill before chorus/drop
- simplify bridge or break
- increase density in build-up

Bad variation:

- random `D/K` alternation
- density spikes with no musical event
- no rest after a difficult burst

## Red Flags

Fix these before calling a chart playable:

- auto-extracted draft with no manual edits
- chart feels off-beat but offset was not checked first
- Don/Ka mapping comes directly from full-mix onsets instead of drum events or explicit musical anchors
- note density changes only by taking every Nth onset
- low difficulty loses groove because too many structural beats were removed
- high difficulty is dense but not patterned
- selected audio has no matching generated beatmaps
- chart cannot explain what musical element it follows per section
- no review notes exist

## Review Note Template

```markdown
## <difficulty>

- Offset: <audio_offset_ms/chart_offset_ms and sync risk>
- Drum-event source: <Demucs drums / HPSS / manual / mixed>
- Follows: <drums / vocal phrase / melody / chord rhythm / section accents>
- Main motif: `<pattern>`
- Density plan: <how density changes by section>
- Hardest section: <timestamp range and why>
- Manual edits from scaffold: <what was removed, moved, or patterned>
- Playtest risks: <sync, fatigue, readability, missing rests>
```
