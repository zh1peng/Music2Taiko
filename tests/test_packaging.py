import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


class PackagingTests(unittest.TestCase):
    def test_project_does_not_define_optional_dependency_shortcuts(self):
        metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

        self.assertNotIn("optional-dependencies", metadata["project"])

    def test_runtime_dependencies_are_explicit(self):
        metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual(
            metadata["project"]["dependencies"],
            [
                "librosa>=0.10",
                "numpy>=1.24",
                "soundfile>=0.13",
                "demucs",
                "yt-dlp",
                "imageio-ffmpeg",
                "static-ffmpeg",
            ],
        )


if __name__ == "__main__":
    unittest.main()
