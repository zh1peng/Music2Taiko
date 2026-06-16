# Output Compatibility

Use this reference before exporting TJA, PsyGodot JSON, audio copies, folders, or generated chart packs.

## Core Rule

Separate display text from filesystem identifiers:

- Display title: human-readable, may preserve original casing and Unicode when the target game handles it.
- Output ID: short, stable, filesystem-safe, used for folders, filenames, JSON IDs, and generated prefixes.
- Source title: original metadata retained for review notes or optional metadata fields.

Do not use raw song titles directly as output filenames. Long titles, punctuation, path separators, emoji, control characters, and reserved device names can break loading or packaging.

## Recommended Limits

Use conservative limits unless a target runtime explicitly supports more:

| Field | Limit | Example |
| --- | ---: | --- |
| output ID / filename stem | 48 chars | `099-dreaming-to-be-with-you` |
| output folder name | 64 chars | `099-dreaming-to-be-with-you` |
| display title | 80 chars | `Dreaming to be with you` |
| JSON note/chart IDs | 64 chars | `oni_0001` |
| full output path | keep below 180 chars | avoid deeply nested exports |

If the original title exceeds the display limit, shorten it for display and keep the full title in review notes or metadata such as `source_title`.

## Filename Normalization

For output IDs and filename stems:

1. Start with the stable song ID when available, such as `001`, `099`, or `CH1`.
2. Append a short normalized title.
3. Lowercase ASCII letters when possible.
4. Replace whitespace and punctuation runs with a single hyphen.
5. Remove Windows-forbidden characters: `< > : " / \ | ? *`.
6. Remove control characters.
7. Trim leading/trailing spaces, dots, underscores, and hyphens.
8. Collapse repeated hyphens.
9. Avoid reserved Windows names: `CON`, `PRN`, `AUX`, `NUL`, `COM1` to `COM9`, `LPT1` to `LPT9`.
10. Truncate to the configured limit without leaving a trailing hyphen.

Examples:

| Source | Output ID |
| --- | --- |
| `001 - CITYSCAPE` | `001-cityscape` |
| `099 - Dreaming to be with you` | `099-dreaming-to-be-with-you` |
| `CH1 - WE ARE OPTK!!` | `ch1-we-are-optk` |
| `Very long title with punctuation?!` | `085-very-long-title` |

If transliteration is not available, keep the numeric ID and use a generic suffix:

```text
137-chart
```

This is better than generating an unsafe or unreadable filename.

## TJA Export Rules

For TJA:

- Keep `TITLE:` readable but bounded.
- Keep `WAVE:` equal to the actual audio filename in the output folder.
- Use short audio filenames derived from the output ID, such as `001-cityscape.ogg`.
- Write UTF-8 with BOM when targeting OpenTaiko-style compatibility.
- Preserve original title, artist, and source path in comments or sidecar review notes when needed.

Recommended output layout:

```text
001-cityscape/
  001-cityscape.tja
  001-cityscape.ogg
  jacket.png
  review.md
```

## PsyGodot JSON Rules

For PsyGodot-style JSON:

- `title`: display title, bounded.
- `source_audio`: short relative audio filename.
- `generator`: `tja-creator`.
- note IDs: stable and compact, such as `oni_000001`.
- optional metadata may include `source_title`, `source_tja_path`, `output_id`, and `original_wave`.

Example:

```json
{
  "title": "Dreaming to be with you",
  "source_title": "Dreaming to be with you",
  "output_id": "099-dreaming-to-be-with-you",
  "source_audio": "099-dreaming-to-be-with-you.ogg"
}
```

## Review Checklist

Before calling an export ready:

- output folder name is short and safe
- `.tja`, `.json`, `.ogg`, and image filenames are short and consistent
- `WAVE:` points to an existing file in the output folder
- display title is readable and not excessively long
- original title is retained somewhere if shortened
- no reserved Windows filename is used
- full output path is not deeply nested

If any item fails, normalize names before judging chart or game-loading behavior.
