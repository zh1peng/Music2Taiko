import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from music2taiko.audio.ogg import convert_to_ogg
from music2taiko.io.tja import parse_tja, render_tja, write_tja


BEATMAPS = {
    "easy": {
        "difficulty": "easy",
        "tempo_bpm": 120.0,
        "notes": [{"time_sec": 0.0, "lane": "don"}],
    },
    "normal": {
        "difficulty": "normal",
        "tempo_bpm": 120.0,
        "notes": [
            {"time_sec": 0.0, "lane": "don"},
            {"time_sec": 0.25, "lane": "ka"},
            {"time_sec": 1.875, "lane": "don"},
            {"time_sec": 2.0, "lane": "ka"},
        ],
    },
}


class TjaTests(unittest.TestCase):
    def test_parse_tja_reads_multiple_courses_and_duration_notes(self):
        source = "\n".join(
            [
                "TITLE:Example",
                "BPM:120",
                "WAVE:Example.ogg",
                "OFFSET:-0.224",
                "",
                "COURSE:Oni",
                "LEVEL:6",
                "BALLOON:12",
                "#START",
                "1000200030004000,",
                "7008,",
                "#END",
                "",
                "COURSE:Easy",
                "LEVEL:3",
                "#START",
                "12,",
                "#END",
            ]
        )

        chart = parse_tja(source)

        self.assertEqual(chart["title"], "Example")
        self.assertEqual(chart["wave"], "Example.ogg")
        self.assertEqual(chart["bpm"], 120.0)
        self.assertEqual(chart["offset_sec"], -0.224)
        self.assertEqual([course["course"] for course in chart["courses"]], ["Oni", "Easy"])
        oni = chart["courses"][0]
        self.assertEqual(oni["level"], 6)
        self.assertEqual(oni["balloon"], [12])
        self.assertEqual([note["type"] for note in oni["notes"][:4]], ["don", "ka", "big_don", "big_ka"])
        self.assertEqual(oni["duration_notes"][0]["type"], "balloon")
        self.assertEqual(oni["duration_notes"][0]["required_hits"], 12)
        self.assertEqual(oni["duration_notes"][0]["start_code"], "7")
        self.assertEqual(oni["duration_notes"][0]["end_code"], "8")
        self.assertAlmostEqual(oni["duration_notes"][0]["start_sec"], 2.0)
        self.assertAlmostEqual(oni["duration_notes"][0]["end_sec"], 3.5)

    def test_render_tja_exports_big_notes_rolls_and_balloons(self):
        beatmaps = {
            "oni": {
                "difficulty": "oni",
                "level": 8,
                "tempo_bpm": 120.0,
                "notes": [
                    {"time_sec": 0.0, "type": "big_don"},
                    {"time_sec": 0.5, "type": "big_ka"},
                ],
                "duration_notes": [
                    {"start_sec": 1.0, "end_sec": 1.5, "type": "roll"},
                    {"start_sec": 2.0, "end_sec": 2.5, "type": "balloon", "required_hits": 12},
                ],
            }
        }

        tja = render_tja(beatmaps, title="Song", audio_filename="song.ogg")

        self.assertIn("COURSE:Oni", tja)
        self.assertIn("LEVEL:8", tja)
        self.assertIn("BALLOON:12", tja)
        self.assertIn("3000400050008000,", tja)
        self.assertIn("7000800000000000,", tja)

    def test_render_tja_writes_metadata_courses_and_16th_grid_notes(self):
        tja = render_tja(BEATMAPS, title="Song", audio_filename="Song.ogg")

        self.assertIn("TITLE:Song", tja)
        self.assertIn("BPM:120.000", tja)
        self.assertIn("WAVE:Song.ogg", tja)
        self.assertIn("OFFSET:0.000", tja)
        self.assertIn("COURSE:Easy", tja)
        self.assertIn("COURSE:Normal", tja)
        self.assertIn("1020000000000001,", tja)
        self.assertIn("2000000000000000,", tja)

    def test_write_tja_uses_utf8_bom_for_open_taiko_compatibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_tja(
                BEATMAPS,
                Path(tmp) / "Song.tja",
                title="Song",
                audio_filename="Song.ogg",
            )
            raw = path.read_bytes()

        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        self.assertIn("TITLE:Song", raw.decode("utf-8-sig"))

    def test_convert_to_ogg_writes_vorbis_audio(self):
        import numpy as np

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "song.ogg"

            class FakeSoundFile:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, traceback):
                    output.write_bytes(b"fake ogg")
                    return False

                def write(self, chunk):
                    pass

            with patch("music2taiko.audio.ogg._load_audio", return_value=(np.zeros(800, dtype=np.float32), 8000)), patch(
                "music2taiko.audio.ogg._open_sound_file",
                return_value=FakeSoundFile(),
            ) as open_sound_file:
                result = convert_to_ogg("source.wav", output)

            self.assertEqual(result, output)
            self.assertGreater(output.stat().st_size, 0)
            open_sound_file.assert_called_once_with(output, sample_rate=8000, channels=1)

    def test_convert_to_ogg_streams_audio_in_chunks(self):
        import numpy as np

        writes = []

        class FakeSoundFile:
            def __init__(self, path, mode, samplerate, channels, format, subtype):
                self.path = path
                self.mode = mode
                self.samplerate = samplerate
                self.channels = channels
                self.format = format
                self.subtype = subtype

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def write(self, chunk):
                writes.append(chunk.copy())

        samples = np.zeros((2, 5000), dtype=np.float32)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "song.ogg"
            with patch("music2taiko.audio.ogg._load_audio", return_value=(samples, 44100)), patch(
                "music2taiko.audio.ogg._open_sound_file",
                side_effect=lambda path, *, sample_rate, channels: FakeSoundFile(
                    path,
                    mode="w",
                    samplerate=sample_rate,
                    channels=channels,
                    format="OGG",
                    subtype="VORBIS",
                ),
            ):
                result = convert_to_ogg("song.mp3", output, chunk_size=1024)

        self.assertEqual(result, output)
        self.assertGreater(len(writes), 1)
        self.assertLessEqual(max(len(chunk) for chunk in writes), 1024)
        self.assertEqual(writes[0].shape, (1024, 2))


if __name__ == "__main__":
    unittest.main()
