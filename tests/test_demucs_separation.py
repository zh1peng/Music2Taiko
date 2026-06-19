import sys
import tempfile
import unittest
from os import pathsep
from pathlib import Path

from music2taiko.separation.demucs import (
    DemucsConfig,
    build_demucs_command,
    build_demucs_subprocess_env,
    separate_drums,
)


class DemucsSeparationTests(unittest.TestCase):
    def test_build_demucs_command_targets_drums_stem(self):
        config = DemucsConfig(model="htdemucs", device="cpu")

        command = build_demucs_command(Path("song.mp3"), Path("work/stems"), config)

        self.assertEqual(command[:3], [sys.executable, "-m", "demucs"])
        self.assertIn("-n", command)
        self.assertIn("htdemucs", command)
        self.assertIn("-d", command)
        self.assertIn("cpu", command)
        self.assertIn("--two-stems=drums", command)
        self.assertIn("--mp3", command)
        self.assertEqual(command[-1], "song.mp3")

    def test_build_demucs_command_accepts_gpu_quality_options(self):
        config = DemucsConfig(model="htdemucs_ft", device="cuda", segment=7)

        command = build_demucs_command(Path("song.mp3"), Path("work/stems"), config)

        self.assertIn("htdemucs_ft", command)
        self.assertIn("cuda", command)
        self.assertIn("--segment", command)
        self.assertIn("7", command)

    def test_build_demucs_command_can_write_mp3_stem(self):
        config = DemucsConfig(output_format="mp3")

        command = build_demucs_command(Path("song.mp3"), Path("work/stems"), config)

        self.assertIn("--mp3", command)

    def test_separate_drums_returns_generated_drums_mp3_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "song.mp3"
            output = root / "stems"
            audio.write_bytes(b"fake audio")

            def fake_runner(command, *, env=None):
                expected = output / "htdemucs" / "song" / "drums.mp3"
                expected.parent.mkdir(parents=True)
                expected.write_bytes(b"fake drums")

            drums = separate_drums(audio, output, runner=fake_runner)

        self.assertEqual(drums.name, "drums.mp3")
        self.assertEqual(drums.parent.name, "song")

    def test_separate_drums_returns_generated_drums_mp3(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "song.mp3"
            output = root / "stems"
            audio.write_bytes(b"fake audio")

            def fake_runner(command, *, env=None):
                expected = output / "htdemucs" / "song" / "drums.mp3"
                expected.parent.mkdir(parents=True)
                expected.write_bytes(b"fake drums")

            drums = separate_drums(audio, output, config=DemucsConfig(output_format="mp3"), runner=fake_runner)

        self.assertEqual(drums.name, "drums.mp3")

    def test_separate_drums_forces_utf8_subprocess_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "song ｜ unicode.mp3"
            output = root / "stems"
            audio.write_bytes(b"fake audio")
            observed = {}

            def fake_runner(command, *, env=None):
                observed["env"] = env
                expected = output / "htdemucs" / audio.stem / "drums.mp3"
                expected.parent.mkdir(parents=True)
                expected.write_bytes(b"fake drums")

            separate_drums(audio, output, runner=fake_runner)

        self.assertIsNotNone(observed["env"])
        self.assertEqual(observed["env"]["PYTHONIOENCODING"], "utf-8")

    def test_demucs_env_prefers_static_ffmpeg_tools(self):
        env = build_demucs_subprocess_env(
            ffmpeg_locator=lambda: (
                r"C:\tools\static-ffmpeg\ffmpeg.exe",
                r"C:\tools\static-ffmpeg\ffprobe.exe",
            )
        )

        self.assertEqual(env["PYTHONIOENCODING"], "utf-8")
        self.assertEqual(env["PATH"].split(pathsep)[0], r"C:\tools\static-ffmpeg")


if __name__ == "__main__":
    unittest.main()
