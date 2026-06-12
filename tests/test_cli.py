import json
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
