import tomllib
import unittest
from pathlib import Path


class PackagingTests(unittest.TestCase):
    def test_optional_dependency_groups_use_unambiguous_names(self):
        metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
        optional_dependencies = metadata["project"]["optional-dependencies"]

        self.assertNotIn("audio", optional_dependencies)
        self.assertIn("analysis", optional_dependencies)
        self.assertEqual(optional_dependencies["analysis"], ["librosa>=0.10", "numpy>=1.24"])


if __name__ == "__main__":
    unittest.main()
