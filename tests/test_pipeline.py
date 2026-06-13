import json
import tempfile
import unittest
from pathlib import Path

from drum2taiko.io.psygodot import write_beatmaps
from drum2taiko.pipeline import build_beatmap_package, build_opentaiko_package, generate_beatmaps


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

            def fake_separator(source, output_dir, *, config=None):
                self.assertEqual(config.model, "htdemucs_ft")
                self.assertEqual(config.device, "cuda")
                self.assertEqual(config.segment, 7)
                self.assertEqual(config.output_format, "mp3")
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
                demucs_model="htdemucs_ft",
                demucs_device="cuda",
                demucs_segment=7,
                demucs_format="mp3",
                separator=fake_separator,
                extractor=fake_extractor,
            )

            hard = json.loads(paths["hard"].read_text(encoding="utf-8"))

        self.assertEqual(hard["drum_event_source"], "demucs_drums")
        self.assertEqual(hard["notes"][0]["lane"], "don")

    def test_build_beatmap_package_writes_report_and_uses_windows_cuda_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "song.mp3"
            audio.write_bytes(b"fake audio")

            def fake_separator(source, output_dir, *, config=None):
                self.assertEqual(config.model, "htdemucs")
                self.assertEqual(config.device, "cuda")
                self.assertEqual(config.segment, 7)
                self.assertEqual(config.output_format, "mp3")
                stem = output_dir / "htdemucs" / source.stem / "drums.mp3"
                stem.parent.mkdir(parents=True)
                stem.write_bytes(b"fake drums")
                return stem

            def fake_extractor(source, *, drum_stem_path=None):
                self.assertEqual(Path(drum_stem_path).name, "drums.mp3")
                return EVENTS

            result = build_beatmap_package(
                audio,
                root / "godot_out",
                title="Song",
                separator=fake_separator,
                extractor=fake_extractor,
            )

            report = json.loads(result["report"].read_text(encoding="utf-8"))

        self.assertEqual(set(result["beatmaps"]), {"easy", "normal", "hard"})
        self.assertEqual(report["title"], "Song")
        self.assertEqual(report["difficulties"]["hard"]["notes"], 2)

    def test_build_opentaiko_package_writes_tja_ogg_and_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "song.mp3"
            audio.write_bytes(b"fake audio")

            def fake_separator(source, output_dir, *, config=None):
                self.assertEqual(config.device, "cuda")
                stem = output_dir / "htdemucs" / source.stem / "drums.mp3"
                stem.parent.mkdir(parents=True)
                stem.write_bytes(b"fake drums")
                return stem

            def fake_extractor(source, *, drum_stem_path=None):
                self.assertEqual(Path(drum_stem_path).name, "drums.mp3")
                events = []
                for event in EVENTS:
                    copy = event.copy()
                    copy["tempo_bpm"] = 120.0
                    events.append(copy)
                return events

            def fake_audio_converter(source, output):
                Path(output).write_bytes(b"fake ogg")
                return Path(output)

            result = build_opentaiko_package(
                audio,
                root / "opentaiko_out",
                title="Song",
                separator=fake_separator,
                extractor=fake_extractor,
                audio_converter=fake_audio_converter,
            )

            tja_text = result["tja"].read_text(encoding="utf-8-sig")
            report = json.loads(result["report"].read_text(encoding="utf-8"))

        self.assertEqual(result["package_dir"].name, "Song")
        self.assertEqual(result["audio"].name, "Song.ogg")
        self.assertIn("WAVE:Song.ogg", tja_text)
        self.assertIn("COURSE:Normal", tja_text)
        self.assertIn("#START", tja_text)
        self.assertEqual(report["title"], "Song")


if __name__ == "__main__":
    unittest.main()
