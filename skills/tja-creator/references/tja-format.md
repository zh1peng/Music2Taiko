# TJA Format Notes

Use this reference when reading, writing, or reviewing TJA files.

## Core Metadata

Common headers:

| Field | Meaning |
| --- | --- |
| `TITLE` | Song title |
| `SUBTITLE` | Optional subtitle or artist display |
| `BPM` | Initial chart BPM |
| `WAVE` | Audio file path, usually relative to the `.tja` file |
| `OFFSET` | Chart/audio offset in seconds |
| `DEMOSTART` | Preview start time in seconds |
| `COURSE` | Difficulty course, such as `Easy`, `Normal`, `Hard`, `Oni`, `Edit` |
| `LEVEL` | Difficulty level |
| `BALLOON` | Comma-separated hit counts for balloon notes |

## Note Codes

Treat `1` to `4` as hit notes and `5`, `6`, `7`, `9` as duration note starts. Duration notes end at `8`.

| Code | Meaning | Internal type |
| --- | --- | --- |
| `0` | Rest / empty slot | none |
| `1` | Small don | `don` |
| `2` | Small ka | `ka` |
| `3` | Big don | `big_don` |
| `4` | Big ka | `big_ka` |
| `5` | Roll start | `roll` |
| `6` | Big roll start | `big_roll` |
| `7` | Balloon start | `balloon` |
| `8` | Roll/balloon end | duration end |
| `9` | Special balloon / simulator-specific duration start | `special_balloon` |

Keep the raw source code with every parsed note. Do not collapse `3` into `1` or `4` into `2` when studying human charts; big notes are part of the charting language.

## Timing Rules

Each comma ends a measure. The characters before the comma divide that measure evenly.

Examples:

```text
1000,
```

This is one measure with four slots. In 4/4, code `1` lands on beat 1.

```text
10101010,
```

This is one measure with eight slots. Codes land on 8th-note positions.

```text
1000200030004000,
```

This is one measure with sixteen slots. It contains `don`, `ka`, `big_don`, and `big_ka`.

## Commands To Preserve

Support these commands before treating a chart as timing-correct:

| Command | Effect |
| --- | --- |
| `#START` / `#END` | Begin/end a course body |
| `#BPMCHANGE <bpm>` | Change BPM from this point forward |
| `#MEASURE <n>/<d>` | Change measure length |
| `#DELAY <sec>` | Shift subsequent notes later |
| `#SCROLL <rate>` | Visual scroll only; preserve, but do not alter audio timing |
| `#GOGOSTART` / `#GOGOEND` | Mark Go-Go time; useful for energy/section analysis |
| `#BARLINEON` / `#BARLINEOFF` | Visual barline control |

Branching commands such as `#BRANCHSTART`, `#N`, `#E`, and `#M` need explicit branch handling. Do not silently merge branch bodies into a single chart.

## Parser Output Expectations

For learning and retrieval, store:

- metadata: title, wave, BPM, offset, source path
- per-course fields: course, level, `BALLOON`, commands
- hit notes: `time_sec`, type, source code, measure start, slot index, slot count
- duration notes: type, start, end, source start code, end code, required hits when available

Use `OFFSET` only after confirming the sign convention in the target runtime. A wrong offset sign can make correct note positions look wrong.
