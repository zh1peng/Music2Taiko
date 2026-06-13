import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from drum2taiko.audio.ogg import convert_to_ogg
from drum2taiko.io.tja import render_tja, write_tja


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
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.wav"
            output = Path(tmp) / "song.ogg"
            with wave.open(str(source), "wb") as handle:
                handle.setnchannels(1)
                handle.setsampwidth(2)
                handle.setframerate(8000)
                handle.writeframes((0).to_bytes(2, "little", signed=True) * 800)

            result = convert_to_ogg(source, output)

            self.assertEqual(result, output)
            self.assertGreater(output.stat().st_size, 0)

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
            with patch("librosa.load", return_value=(samples, 44100)), patch("soundfile.SoundFile", FakeSoundFile):
                result = convert_to_ogg("song.mp3", output, chunk_size=1024)

        self.assertEqual(result, output)
        self.assertGreater(len(writes), 1)
        self.assertLessEqual(max(len(chunk) for chunk in writes), 1024)
        self.assertEqual(writes[0].shape, (1024, 2))


if __name__ == "__main__":
    unittest.main()
