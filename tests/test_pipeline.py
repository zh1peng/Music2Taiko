import json
import tempfile
import unittest
from pathlib import Path

from drum2taiko.io.psygodot import write_beatmaps
from drum2taiko.pipeline import generate_beatmaps


EVENTS = [
    {
        "time_sec": 1.0,
        "quantized_time_sec": 1.0,
        "strength": 0.95,
        "subdivision": 0,
        "beat_index": 1,
        "drum_class": "kick",
        "confidence": 0.9,
        "is_accent": True,
    },
    {
        "time_sec": 1.5,
        "quantized_time_sec": 1.5,
        "strength": 0.82,
        "subdivision": 2,
        "beat_index": 1,
        "drum_class": "hat",
        "confidence": 0.8,
        "is_accent": False,
    },
]


class PipelineTests(unittest.TestCase):
    def test_write_beatmaps_exports_psygodot_files_from_drum_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_beatmaps(EVENTS, Path(tmp), source_path="song.mp3", title="Song")
            payload = json.loads(paths["hard"].read_text(encoding="utf-8"))

        self.assertEqual(set(paths), {"easy", "normal", "hard"})
        self.assertEqual(payload["schema_version"], "psygodot.beatmap.v1")
        self.assertEqual(payload["source_audio"], "song.mp3")
        self.assertEqual(payload["drum_events"][0]["drum_class"], "kick")
        self.assertEqual(payload["notes"][0]["lane"], "don")
        self.assertEqual(payload["notes"][1]["lane"], "ka")

    def test_generate_beatmaps_uses_demucs_drums_when_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "song.mp3"
            audio.write_bytes(b"fake audio")

            def fake_separator(source, output_dir):
                stem = output_dir / "htdemucs" / source.stem / "drums.wav"
                stem.parent.mkdir(parents=True)
                stem.write_bytes(b"fake drums")
                return stem

            def fake_extractor(source, *, drum_stem_path=None):
                self.assertEqual(Path(drum_stem_path).name, "drums.wav")
                return EVENTS

            paths = generate_beatmaps(
                audio,
                root / "beatmaps",
                title="Song",
                use_demucs=True,
                separator=fake_separator,
                extractor=fake_extractor,
            )

            hard = json.loads(paths["hard"].read_text(encoding="utf-8"))

        self.assertEqual(hard["drum_event_source"], "demucs_drums")
        self.assertEqual(hard["notes"][0]["lane"], "don")


if __name__ == "__main__":
    unittest.main()
