import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


class CliTests(unittest.TestCase):
    def test_python_module_generate_writes_three_beatmaps(self):
        from music2taiko import cli

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "song.wav"
            audio.write_bytes(b"fake audio")
            output = root / "beatmaps"

            def fake_generate(audio_path, output_dir, **kwargs):
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                paths = {}
                for difficulty in ("easy", "normal", "hard"):
                    path = Path(output_dir) / f"song_{difficulty}.json"
                    path.write_text(
                        json.dumps({"title": kwargs["title"], "difficulty": difficulty, "notes": [{"lane": "don"}]}),
                        encoding="utf-8",
                    )
                    paths[difficulty] = path
                return paths

            with patch("music2taiko.cli.generate_beatmaps", side_effect=fake_generate):
                stdout = StringIO()
                with redirect_stdout(stdout):
                    exit_code = cli.main(["generate", str(audio), "--out", str(output), "--title", "Impulse Song"])

            paths = [Path(line) for line in stdout.getvalue().splitlines() if line.strip()]
            hard = json.loads((output / "song_hard.json").read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(paths), 3)
        self.assertEqual(hard["title"], "Impulse Song")
        self.assertTrue(hard["notes"])

    def test_generate_accepts_demucs_model_and_device_options(self):
        from music2taiko import cli

        with patch("music2taiko.cli.generate_beatmaps") as generate:
            generate.return_value = {
                "easy": Path("easy.json"),
                "normal": Path("normal.json"),
                "hard": Path("hard.json"),
            }

            with redirect_stdout(StringIO()):
                exit_code = cli.main(
                    [
                        "generate",
                        "song.mp3",
                        "--out",
                        "beatmaps",
                        "--use-demucs",
                        "--demucs-model",
                        "htdemucs_ft",
                        "--demucs-device",
                        "cuda",
                        "--demucs-segment",
                        "7",
                        "--demucs-format",
                        "mp3",
                    ]
                )

        self.assertEqual(exit_code, 0)
        _, kwargs = generate.call_args
        self.assertEqual(kwargs["demucs_model"], "htdemucs_ft")
        self.assertEqual(kwargs["demucs_device"], "cuda")
        self.assertEqual(kwargs["demucs_segment"], 7)
        self.assertEqual(kwargs["demucs_format"], "mp3")

    def test_build_command_uses_one_step_workflow(self):
        from music2taiko import cli

        with patch("music2taiko.cli.build_beatmap_package") as build:
            build.return_value = {
                "beatmaps": {
                    "easy": Path("easy.json"),
                    "normal": Path("normal.json"),
                    "hard": Path("hard.json"),
                },
                "report": Path("review_report.json"),
            }

            with redirect_stdout(StringIO()):
                exit_code = cli.main(["build", "song.mp3", "--out", "godot_out", "--title", "Song"])

        self.assertEqual(exit_code, 0)
        _, kwargs = build.call_args
        self.assertEqual(kwargs["title"], "Song")
        self.assertEqual(kwargs["demucs_device"], "cuda")
        self.assertEqual(kwargs["demucs_format"], "mp3")

    def test_build_opentaiko_command_uses_tja_package_workflow(self):
        from music2taiko import cli

        with patch("music2taiko.cli.build_opentaiko_package") as build:
            build.return_value = {
                "package_dir": Path("opentaiko_out") / "Song",
                "tja": Path("opentaiko_out") / "Song" / "Song.tja",
                "audio": Path("opentaiko_out") / "Song" / "Song.ogg",
                "beatmaps": {
                    "easy": Path("easy.json"),
                    "normal": Path("normal.json"),
                    "hard": Path("hard.json"),
                },
                "report": Path("review_report.json"),
            }

            with redirect_stdout(StringIO()):
                exit_code = cli.main(["build-opentaiko", "song.mp3", "--out", "opentaiko_out", "--title", "Song"])

        self.assertEqual(exit_code, 0)
        _, kwargs = build.call_args
        self.assertEqual(kwargs["title"], "Song")
        self.assertEqual(kwargs["demucs_device"], "cuda")
        self.assertEqual(kwargs["demucs_format"], "mp3")

    def test_create_tja_command_uses_creator_workflow(self):
        from music2taiko import cli

        with patch("music2taiko.cli.create_tja_package") as create:
            create.return_value = {
                "package_dir": Path("out") / "001-song",
                "tja": Path("out") / "001-song" / "001-song.tja",
                "audio": Path("out") / "001-song" / "001-song.ogg",
                "retrieval": Path("out") / "001-song" / "retrieval.json",
                "aligned_samples": Path("out") / "001-song" / "aligned_samples.json",
                "arrangement_context": Path("out") / "001-song" / "arrangement_context.json",
                "pattern_plan": Path("out") / "001-song" / "pattern_plan.json",
            }

            with redirect_stdout(StringIO()):
                exit_code = cli.main(
                    [
                        "create-tja",
                        "song.ogg",
                        "--out",
                        "out",
                        "--difficulty",
                        "oni",
                        "--title",
                        "Song",
                        "--song-id",
                        "001",
                        "--corpus-dir",
                        "tja-wiki/corpus",
                        "--pattern-plan",
                        "pattern_plan.json",
                    ]
                )

        self.assertEqual(exit_code, 0)
        _, kwargs = create.call_args
        self.assertEqual(kwargs["difficulty"], "oni")
        self.assertEqual(kwargs["title"], "Song")
        self.assertEqual(kwargs["song_id"], "001")
        self.assertEqual(kwargs["corpus_dir"], Path("tja-wiki/corpus"))
        self.assertEqual(kwargs["pattern_plan_path"], Path("pattern_plan.json"))
        self.assertTrue(kwargs["use_demucs"])
        self.assertEqual(kwargs["demucs_device"], "cpu")
        self.assertEqual(kwargs["demucs_format"], "mp3")

    def test_create_tja_command_accepts_demucs_options_and_no_demucs(self):
        from music2taiko import cli

        with patch("music2taiko.cli.create_tja_package") as create:
            create.return_value = {
                "package_dir": Path("out") / "song",
                "tja": Path("out") / "song" / "song.tja",
                "audio": Path("out") / "song" / "song.ogg",
                "retrieval": Path("out") / "song" / "retrieval.json",
                "aligned_samples": Path("out") / "song" / "aligned_samples.json",
                "arrangement_context": Path("out") / "song" / "arrangement_context.json",
                "pattern_plan": Path("out") / "song" / "pattern_plan.json",
            }

            with redirect_stdout(StringIO()):
                exit_code = cli.main(
                    [
                        "create-tja",
                        "song.mp3",
                        "--out",
                        "out",
                        "--no-demucs",
                        "--demucs-model",
                        "htdemucs_ft",
                        "--demucs-device",
                        "cuda",
                        "--demucs-segment",
                        "7",
                        "--demucs-format",
                        "mp3",
                    ]
                )

        self.assertEqual(exit_code, 0)
        _, kwargs = create.call_args
        self.assertFalse(kwargs["use_demucs"])
        self.assertEqual(kwargs["demucs_model"], "htdemucs_ft")
        self.assertEqual(kwargs["demucs_device"], "cuda")
        self.assertEqual(kwargs["demucs_segment"], 7)
        self.assertEqual(kwargs["demucs_format"], "mp3")

    def test_create_tja_command_accepts_multi_course_reuse_context(self):
        from music2taiko import cli

        with patch("music2taiko.cli.create_tja_package") as create:
            create.return_value = {
                "package_dir": Path("out") / "song",
                "tja": Path("out") / "song" / "song.tja",
                "audio": Path("out") / "song" / "song.ogg",
                "retrieval": Path("out") / "song" / "retrieval.json",
                "aligned_samples": Path("out") / "song" / "aligned_samples.json",
                "arrangement_context": Path("out") / "song" / "arrangement_context.json",
                "pattern_plan": Path("out") / "song" / "pattern_plan.json",
            }

            with redirect_stdout(StringIO()):
                exit_code = cli.main(
                    [
                        "create-tja",
                        "song.mp3",
                        "--out",
                        "out",
                        "--difficulties",
                        "easy,normal,oni",
                        "--reuse-context",
                        "arrangement_context.json",
                        "--lead-in-sec",
                        "3.0",
                    ]
                )

        self.assertEqual(exit_code, 0)
        _, kwargs = create.call_args
        self.assertEqual(kwargs["difficulties"], ["easy", "normal", "oni"])
        self.assertEqual(kwargs["reuse_context_path"], Path("arrangement_context.json"))
        self.assertEqual(kwargs["lead_in_sec"], 3.0)

    def test_create_tja_command_resolves_youtube_url_before_pipeline(self):
        from music2taiko import cli

        resolved_audio = Path("out") / "source_audio" / "video.mp3"

        with patch("music2taiko.cli.resolve_audio_source", return_value=resolved_audio) as resolve:
            with patch("music2taiko.cli.create_tja_package") as create:
                create.return_value = {
                    "package_dir": Path("out") / "video",
                    "tja": Path("out") / "video" / "video.tja",
                    "audio": Path("out") / "video" / "video.ogg",
                    "retrieval": Path("out") / "video" / "retrieval.json",
                    "aligned_samples": Path("out") / "video" / "aligned_samples.json",
                    "arrangement_context": Path("out") / "video" / "arrangement_context.json",
                    "pattern_plan": Path("out") / "video" / "pattern_plan.json",
                }

                with redirect_stdout(StringIO()):
                    exit_code = cli.main(["create-tja", "https://youtu.be/example123", "--out", "out"])

        self.assertEqual(exit_code, 0)
        resolve.assert_called_once_with("https://youtu.be/example123", Path("out") / "source_audio")
        create.assert_called_once()
        args, _ = create.call_args
        self.assertEqual(args[0], resolved_audio)


if __name__ == "__main__":
    unittest.main()
