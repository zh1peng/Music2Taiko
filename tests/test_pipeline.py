import json
import tempfile
import unittest
from pathlib import Path

from music2taiko.io.psygodot import write_beatmaps
from music2taiko.pipeline import (
    DEFAULT_TJA_DIFFICULTIES,
    build_beatmap_package,
    build_opentaiko_package,
    create_tja_package,
    generate_beatmaps,
)


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

    def test_create_tja_package_writes_default_four_difficulty_tja_with_retrieval_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "Very Long / Unsafe Song Name.mp3"
            audio = root / "unsafe song.mp3"
            audio.write_bytes(b"fake audio")
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "manifest.json").write_text(
                json.dumps(
                    [
                        {
                            "song_id": "001",
                            "title": "Reference",
                            "bpm": 120.0,
                            "audio_duration_sec": 2.0,
                            "drum_event_count": 2,
                            "courses": ["Oni"],
                            "course_summaries": [{"course": "Oni", "level": 8, "note_total": 12}],
                        }
                    ]
                ),
                encoding="utf-8",
            )

            def fake_extractor(source, *, drum_stem_path=None):
                events = []
                for event in EVENTS:
                    copy = event.copy()
                    copy["tempo_bpm"] = 120.0
                    events.append(copy)
                return events

            def fake_audio_converter(source, output):
                Path(output).write_bytes(b"fake ogg")
                return Path(output)

            result = create_tja_package(
                audio,
                root / "out",
                title="Unsafe Song Name With Extra Words",
                song_id="099",
                corpus_dir=corpus,
                extractor=fake_extractor,
                audio_converter=fake_audio_converter,
                lead_in_sec=0.0,
            )

            tja_text = result["tja"].read_text(encoding="utf-8-sig")
            retrieval = json.loads(result["retrieval"].read_text(encoding="utf-8"))
            aligned = json.loads(result["aligned_samples"].read_text(encoding="utf-8"))
            context = json.loads(result["arrangement_context"].read_text(encoding="utf-8"))
            plan = json.loads(result["pattern_plan"].read_text(encoding="utf-8"))

        self.assertEqual(result["package_dir"].name, "099-unsafe-song-name-with-extra-words")
        self.assertEqual(result["audio"].name, "099-unsafe-song-name-with-extra-words.ogg")
        self.assertEqual(DEFAULT_TJA_DIFFICULTIES, ("easy", "normal", "hard", "oni"))
        self.assertIn("COURSE:Easy", tja_text)
        self.assertIn("COURSE:Normal", tja_text)
        self.assertIn("COURSE:Hard", tja_text)
        self.assertIn("COURSE:Oni", tja_text)
        self.assertIn("WAVE:099-unsafe-song-name-with-extra-words.ogg", tja_text)
        self.assertEqual(retrieval["matches"][0]["song_id"], "001")
        self.assertEqual(set(aligned["samples"]), {"easy", "normal", "hard", "oni"})
        self.assertTrue(aligned["samples"]["oni"])
        self.assertTrue(context["candidate_timing_anchors"])
        self.assertEqual(set(plan["difficulties"]), {"easy", "normal", "hard", "oni"})

    def test_create_tja_package_can_write_three_difficulties_and_lead_in_silence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "song.mp3"
            audio.write_bytes(b"fake audio")

            def fake_extractor(source, *, drum_stem_path=None):
                events = []
                for time_sec in (1.0, 3.0, 3.5, 4.0):
                    event = EVENTS[0].copy()
                    event["time_sec"] = time_sec
                    event["quantized_time_sec"] = time_sec
                    event["tempo_bpm"] = 120.0
                    events.append(event)
                return events

            def fake_audio_converter(source, output):
                Path(output).write_bytes(b"fake ogg")
                return Path(output)

            result = create_tja_package(
                audio,
                root / "out",
                difficulties=["easy", "normal", "oni"],
                title="Song",
                extractor=fake_extractor,
                audio_converter=fake_audio_converter,
                lead_in_sec=2.5,
            )

            tja_text = result["tja"].read_text(encoding="utf-8-sig")
            aligned = json.loads(result["aligned_samples"].read_text(encoding="utf-8"))

        self.assertIn("COURSE:Easy", tja_text)
        self.assertIn("COURSE:Normal", tja_text)
        self.assertIn("COURSE:Oni", tja_text)
        self.assertEqual(set(aligned["samples"]), {"easy", "normal", "oni"})
        for samples in aligned["samples"].values():
            self.assertGreaterEqual(samples[0]["time_sec"], 2.5)

    def test_create_tja_package_can_reuse_context_without_audio_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "song.mp3"
            audio.write_bytes(b"fake audio")
            context_path = root / "arrangement_context.json"
            context_path.write_text(
                json.dumps(
                    {
                        "title": "Song",
                        "difficulty": "oni",
                        "estimated_bpm": 120.0,
                        "drum_event_count": 2,
                        "candidate_timing_anchors": [
                            {"time_sec": 3.0, "drum_class": "kick", "strength": 1.0, "confidence": 1.0, "is_accent": True},
                            {"time_sec": 3.5, "drum_class": "hat", "strength": 1.0, "confidence": 1.0, "is_accent": False},
                        ],
                        "retrieval_context": {"matches": [{"song_id": "001"}]},
                    }
                ),
                encoding="utf-8",
            )

            def fail_extractor(source, *, drum_stem_path=None):
                raise AssertionError("extractor should not run")

            def fail_audio_converter(source, output):
                raise AssertionError("audio converter should not run")

            result = create_tja_package(
                audio,
                root / "out",
                title="Song",
                output_prefix="song",
                reuse_context_path=context_path,
                difficulties=["easy", "normal", "oni"],
                extractor=fail_extractor,
                audio_converter=fail_audio_converter,
            )

            tja_text = result["tja"].read_text(encoding="utf-8-sig")

        self.assertIn("WAVE:song.ogg", tja_text)
        self.assertIn("COURSE:Easy", tja_text)
        self.assertIn("COURSE:Oni", tja_text)

    def test_create_tja_package_can_apply_external_llm_pattern_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "song.mp3"
            audio.write_bytes(b"fake audio")
            plan_path = root / "pattern_plan.json"
            plan_path.write_text(
                json.dumps(
                    {
                        "difficulty": "oni",
                        "level": 8,
                        "sections": [
                            {
                                "name": "main",
                                "start_sec": 0.0,
                                "end_sec": 2.0,
                                "pattern": "KKK",
                                "use_big_on_accents": False,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            def fake_extractor(source, *, drum_stem_path=None):
                events = []
                for event in EVENTS:
                    copy = event.copy()
                    copy["tempo_bpm"] = 120.0
                    events.append(copy)
                return events

            def fake_audio_converter(source, output):
                Path(output).write_bytes(b"fake ogg")
                return Path(output)

            result = create_tja_package(
                audio,
                root / "out",
                difficulty="oni",
                title="Song",
                pattern_plan_path=plan_path,
                extractor=fake_extractor,
                audio_converter=fake_audio_converter,
                lead_in_sec=0.0,
            )

            tja_text = result["tja"].read_text(encoding="utf-8-sig")

        self.assertIn("0000000020002000,", tja_text)


if __name__ == "__main__":
    unittest.main()
