import json
import subprocess
import sys
import tempfile
import unittest
import wave
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


class CliTests(unittest.TestCase):
    def test_python_module_generate_writes_three_beatmaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "impulses.wav"
            output = root / "beatmaps"
            rate = 8000
            samples = [0] * rate
            for start in [1600, 4400]:
                for offset in range(80):
                    samples[start + offset] = 28000

            with wave.open(str(audio), "wb") as handle:
                handle.setnchannels(1)
                handle.setsampwidth(2)
                handle.setframerate(rate)
                handle.writeframes(b"".join(sample.to_bytes(2, "little", signed=True) for sample in samples))

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "drum2taiko",
                    "generate",
                    str(audio),
                    "--out",
                    str(output),
                    "--title",
                    "Impulse Song",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            paths = [Path(line) for line in result.stdout.splitlines() if line.strip()]
            hard = json.loads((output / "impulses_hard.json").read_text(encoding="utf-8"))

        self.assertEqual(len(paths), 3)
        self.assertEqual(hard["title"], "Impulse Song")
        self.assertTrue(hard["notes"])

    def test_generate_accepts_demucs_model_and_device_options(self):
        from drum2taiko import cli

        with patch("drum2taiko.cli.generate_beatmaps") as generate:
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
        from drum2taiko import cli

        with patch("drum2taiko.cli.build_beatmap_package") as build:
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
        from drum2taiko import cli

        with patch("drum2taiko.cli.build_opentaiko_package") as build:
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


if __name__ == "__main__":
    unittest.main()
