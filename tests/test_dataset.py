import tempfile
import unittest
from pathlib import Path

from music2taiko.dataset import build_song_records, scan_chapter


class DatasetTests(unittest.TestCase):
    def test_scan_chapter_pairs_tja_with_wave_from_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            chapter = Path(tmp) / "chapter"
            song = chapter / "001 - Song"
            song.mkdir(parents=True)
            (song / "Song.tja").write_text(
                "\n".join(
                    [
                        "TITLE:Song",
                        "BPM:135",
                        "WAVE:audio.ogg",
                        "OFFSET:-0.1",
                        "COURSE:Oni",
                        "LEVEL:6",
                        "#START",
                        "1000,",
                        "#END",
                    ]
                ),
                encoding="utf-8",
            )
            (song / "audio.ogg").write_bytes(b"OggS")

            records = scan_chapter(chapter)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["title"], "Song")
        self.assertEqual(records[0]["parse_status"], "ok")
        self.assertEqual(records[0]["audio_path"].name, "audio.ogg")
        self.assertEqual(records[0]["courses"], ["Oni"])

    def test_build_song_records_returns_error_when_wave_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            song = Path(tmp) / "001 - Broken"
            song.mkdir()
            tja = song / "Broken.tja"
            tja.write_text("TITLE:Broken\nBPM:120\nWAVE:missing.ogg\n", encoding="utf-8")

            records = build_song_records(song)

        self.assertEqual(records[0]["parse_status"], "missing_audio")
        self.assertEqual(records[0]["audio_path"].name, "missing.ogg")


if __name__ == "__main__":
    unittest.main()
