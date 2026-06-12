import sys
import tempfile
import unittest
from pathlib import Path

from drum2taiko.separation.demucs import DemucsConfig, build_demucs_command, separate_drums


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
        self.assertEqual(command[-1], "song.mp3")

    def test_build_demucs_command_accepts_gpu_quality_options(self):
        config = DemucsConfig(model="htdemucs_ft", device="cuda", segment=7)

        command = build_demucs_command(Path("song.mp3"), Path("work/stems"), config)

        self.assertIn("htdemucs_ft", command)
        self.assertIn("cuda", command)
        self.assertIn("--segment", command)
        self.assertIn("7", command)

    def test_separate_drums_returns_generated_drums_wav(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "song.mp3"
            output = root / "stems"
            audio.write_bytes(b"fake audio")

            def fake_runner(command):
                expected = output / "htdemucs" / "song" / "drums.wav"
                expected.parent.mkdir(parents=True)
                expected.write_bytes(b"fake drums")

            drums = separate_drums(audio, output, runner=fake_runner)

        self.assertEqual(drums.name, "drums.wav")
        self.assertEqual(drums.parent.name, "song")


if __name__ == "__main__":
    unittest.main()
