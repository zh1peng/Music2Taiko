import tomllib
import unittest
from pathlib import Path


class PackagingTests(unittest.TestCase):
    def test_project_does_not_define_optional_dependency_shortcuts(self):
        metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

        self.assertNotIn("optional-dependencies", metadata["project"])

    def test_runtime_dependencies_are_explicit(self):
        metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual(
            metadata["project"]["dependencies"],
            ["librosa>=0.10", "numpy>=1.24", "demucs"],
        )


if __name__ == "__main__":
    unittest.main()
