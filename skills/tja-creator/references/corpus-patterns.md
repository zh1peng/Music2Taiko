# Corpus Patterns

Use this reference when selecting style examples from the processed corpus. These are observed TJA measure strings, not templates to copy blindly.

## How To Read Patterns

- `0` means a full rest measure represented with one empty slot.
- `1` / `2` are don/ka.
- `3` / `4` are big don/big ka.
- `5...8`, `6...8`, `7...8`, and `9...8` are duration-note spans.
- Short strings such as `1111` divide a measure into four slots.
- Longer strings such as `12121212` or `1010201122102010` divide the measure more finely.

A pattern's musical density depends on both note count and string length. Always reinterpret it against the current song BPM and measure length.

## Top Observed Patterns

### Easy

| Pattern | Count | Use |
| --- | ---: | --- |
| `1` | 1,017 | single accent |
| `0` | 970 | rest / phrase space |
| `2` | 753 | single accent |
| `1010` | 645 | mixed motif |
| `1110` | 470 | mixed motif |
| `2020` | 405 | mixed motif |
| `11` | 296 | alternating or pulse motif |
| `22` | 270 | alternating or pulse motif |
| `1020` | 259 | mixed motif |
| `1111` | 232 | alternating or pulse motif |
| `1202` | 196 | mixed motif |
| `2220` | 193 | mixed motif |
| `3` | 185 | single accent |
| `5008` | 176 | duration-note measure |
| `1212` | 166 | alternating or pulse motif |

### Normal

| Pattern | Count | Use |
| --- | ---: | --- |
| `0` | 910 | rest / phrase space |
| `1111` | 381 | alternating or pulse motif |
| `1` | 227 | single accent |
| `2222` | 203 | alternating or pulse motif |
| `2` | 202 | single accent |
| `1110` | 193 | mixed motif |
| `1010` | 189 | mixed motif |
| `1212` | 186 | alternating or pulse motif |
| `2020` | 118 | mixed motif |
| `1020` | 113 | mixed motif |
| `5008` | 101 | duration-note measure |
| `3` | 98 | single accent |
| `10201120` | 95 | mixed motif |
| `1122` | 90 | alternating or pulse motif |
| `10101011` | 87 | mixed motif |

### Hard

| Pattern | Count | Use |
| --- | ---: | --- |
| `0` | 891 | rest / phrase space |
| `1111` | 148 | alternating or pulse motif |
| `1` | 147 | single accent |
| `10201120` | 91 | mixed motif |
| `2` | 91 | single accent |
| `3` | 78 | single accent |
| `2222` | 72 | alternating or pulse motif |
| `11201120` | 62 | mixed motif |
| `12121212` | 59 | alternating or pulse motif |
| `1212` | 52 | alternating or pulse motif |
| `3333` | 50 | mixed motif |
| `1010` | 45 | mixed motif |
| `10101011` | 44 | mixed motif |
| `21212121` | 41 | alternating or pulse motif |
| `1011` | 41 | mixed motif |

### Oni

| Pattern | Count | Use |
| --- | ---: | --- |
| `0` | 640 | rest / phrase space |
| `1` | 219 | single accent |
| `2` | 116 | single accent |
| `3` | 67 | single accent |
| `12121212` | 55 | alternating or pulse motif |
| `1111` | 52 | alternating or pulse motif |
| `3333` | 48 | mixed motif |
| `7008` | 30 | duration-note measure |
| `2222` | 29 | alternating or pulse motif |
| `100010002000200010001000100100200200200200100000` | 24 | mixed motif |
| `1212` | 20 | alternating or pulse motif |
| `10112022` | 19 | mixed motif |
| `11112011` | 18 | mixed motif |
| `3033` | 18 | mixed motif |
| `1011201010401010` | 17 | mixed motif |

### Edit

| Pattern | Count | Use |
| --- | ---: | --- |
| `0` | 646 | rest / phrase space |
| `1` | 351 | single accent |
| `2` | 231 | single accent |
| `10` | 70 | mixed motif |
| `20` | 36 | mixed motif |
| `1111` | 32 | alternating or pulse motif |
| `11` | 25 | alternating or pulse motif |
| `010` | 23 | mixed motif |
| `100010102000200010001000100100200200200200100000` | 20 | mixed motif |
| `3` | 19 | single accent |
| `12121212` | 18 | alternating or pulse motif |
| `1002102010201222` | 17 | mixed motif |
| `10122121` | 17 | mixed motif |
| `21112121` | 17 | alternating or pulse motif |
| `10201120` | 16 | mixed motif |

## Measure Length Distribution

| Course | Common lengths |
| --- | --- |
| Easy | 4 slots (5,510), 1 slots (3,271), 8 slots (1,162), 2 slots (1,089), 3 slots (430), 16 slots (125) |
| Normal | 8 slots (4,524), 4 slots (3,884), 1 slots (1,668), 16 slots (808), 2 slots (435), 3 slots (326) |
| Hard | 8 slots (4,736), 16 slots (3,536), 4 slots (1,393), 1 slots (1,384), 12 slots (311), 6 slots (227) |
| Oni | 16 slots (6,023), 8 slots (2,528), 1 slots (1,167), 4 slots (722), 48 slots (594), 12 slots (363) |
| Edit | 16 slots (2,893), 1 slots (1,340), 8 slots (915), 48 slots (612), 4 slots (314), 32 slots (219) |

## Authoring Guidance

Use corpus patterns as style anchors:

1. Match the target course grid first.
2. Choose a small family of motifs for a section.
3. Preserve rest measures and single-accent measures as part of the style.
4. Use dense 16-slot patterns only when the audio supports sustained energy.
5. Do not copy rare long patterns unless the new song has a clear matching fill or texture.
