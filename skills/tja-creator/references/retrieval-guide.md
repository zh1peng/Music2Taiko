# Retrieval Guide

Use this reference when choosing examples from the corpus for a new chart. Retrieval should find similar authoring situations, not a chart to copy.

## Retrieval Inputs

For a new song, collect:

- audio path
- estimated BPM and beat grid
- offset assumption
- duration
- drum-event count and class distribution
- section energy curve
- target course and level
- requested style constraints

If a source TJA exists, also collect course list, note density, top patterns, roll/balloon usage, and big-note usage.

## Candidate Selection

Prefer these similarity dimensions:

1. BPM range
2. target course and level
3. audio drum-event density
4. duration-note usage if the song has long fills/builds
5. pattern grid length, such as 4-slot, 8-slot, 16-slot, or long-grid phrases
6. rough energy shape, such as sparse verse, dense drop, or medley-like structure

Do not rank by title, folder chapter, or surface metadata unless the user asks for a named style.

## Manual Retrieval Steps

1. Read `song-index.md` to find songs with similar BPM and event density.
2. Read `corpus-overview.md` for target course density.
3. Read `corpus-patterns.md` for common measure families in that course.
4. Read `audio-to-chart-mapping.md` to map the new song's drum events into playable anchors.
5. Draft original patterns for the new song.
6. Use `evaluation-rubric.md` to reject density spikes, random color changes, and weak offset assumptions.

## Reference Buckets

Fast songs:

- `110` ETHEREAL VELOCITY (Game Size), BPM 327.375, drum events 477, duration notes 28
- `046` ΣxilƎ, BPM 320.0, drum events 603, duration notes 144
- `058` pipie, BPM 314.0, drum events 941, duration notes 64
- `065` Bounded Quietude, BPM 280.0, drum events 423, duration notes 41
- `127` A symphony of a million years, BPM 280.0, drum events 494, duration notes 109
- `111` 2024 BPM IS NOT ENOUGH, BPM 253.0, drum events 552, duration notes 233
- `125` MajETCMAT, BPM 250.0, drum events 671, duration notes 90
- `121` PARANOiA Perpetuality, BPM 245.0, drum events 479, duration notes 26

Low-BPM songs:

- `085` i don't want to see the people i love see me in pain so i sometimes just wanna be left alone to cry in the dark, BPM 21.0, drum events 676, duration notes 3
- `030` Yami, BPM 87.5, drum events 598, duration notes 24
- `015` White Heart, BPM 95.0, drum events 281, duration notes 11
- `005` WTF?!, BPM 100.0, drum events 290, duration notes 6
- `028` Katharsis, BPM 100.0, drum events 315, duration notes 51
- `072` Scarlet Soul, BPM 100.0, drum events 444, duration notes 43
- `117` M_《Ji：Ü》, BPM 100.0, drum events 514, duration notes 31
- `116` Sotsugyou 2000, BPM 105.0, drum events 500, duration notes 32

Audio-dense songs:

- `CH1` WE ARE OPTK!!, BPM 188.0, drum events 1,175, duration notes 26
- `119` Fractured Eternity, BPM 230.0, drum events 1,152, duration notes 183
- `054` Synthsea, BPM 190.0, drum events 1,029, duration notes 19
- `021` Welcome To The Cafe, BPM 150.0, drum events 948, duration notes 11
- `058` pipie, BPM 314.0, drum events 941, duration notes 64
- `082` Comma, ~ Imi to Kouzou no Bunri, BPM 150.0, drum events 874, duration notes 1
- `010` BassBoL, BPM 210.0, drum events 848, duration notes 55
- `002` Zerstören, BPM 170.0, drum events 781, duration notes 43

Duration-note-heavy songs:

- `109` SUGARUSH~!!!, BPM 200.0, drum events 525, duration notes 241
- `111` 2024 BPM IS NOT ENOUGH, BPM 253.0, drum events 552, duration notes 233
- `137` ??? ~ T'soL Niamer-I ~, BPM 120.0, drum events 677, duration notes 214
- `048` The Nostalgic Messenger, BPM 172.0, drum events 445, duration notes 188
- `119` Fractured Eternity, BPM 230.0, drum events 1,152, duration notes 183
- `103` spliced, BPM 110.0, drum events 445, duration notes 155
- `046` ΣxilƎ, BPM 320.0, drum events 603, duration notes 144
- `127` A symphony of a million years, BPM 280.0, drum events 494, duration notes 109

## Retrieval Output Shape

When producing retrieval results for a charting task, summarize candidates like this:

```json
{
  "song_id": "001",
  "title": "cityscape",
  "similarity_reasons": [
    "BPM near target",
    "balanced mid-tempo corpus example",
    "has all five courses"
  ],
  "useful_guidance": [
    "use restrained duration notes",
    "preserve rest space",
    "compare Oni and Hard density"
  ],
  "do_not_copy": [
    "exact measure strings",
    "section timing"
  ]
}
```

## Safety Rule

Use corpus examples as evidence of charting choices. Do not output a new chart that is a time-shifted, BPM-scaled, or lightly edited copy of an existing TJA.
