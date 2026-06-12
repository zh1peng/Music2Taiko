import json
import tempfile
import unittest
from pathlib import Path

from drum2taiko.io.psygodot import write_beatmaps
from drum2taiko.review import summarize_beatmaps, write_review_report


EVENTS = [
    {
        "time_sec": 1.02,
        "quantized_time_sec": 1.0,
        "source_time_sec": 1.02,
        "timing_error_ms": -20.0,
        "band_strengths": {"low": 0.9, "mid": 0.2, "high": 0.1},
        "classification_margin": 0.7,
        "strength": 0.95,
        "subdivision": 0,
        "beat_index": 1,
        "drum_class": "kick",
        "confidence": 0.9,
        "is_accent": True,
    },
    {
        "time_sec": 1.27,
        "quantized_time_sec": 1.25,
        "source_time_sec": 1.27,
        "timing_error_ms": -20.0,
        "band_strengths": {"low": 0.1, "mid": 0.2, "high": 0.8},
        "classification_margin": 0.6,
        "strength": 0.82,
        "subdivision": 1,
        "beat_index": 1,
        "drum_class": "hat",
        "confidence": 0.8,
        "is_accent": False,
    },
    {
        "time_sec": 1.53,
        "quantized_time_sec": 1.5,
        "source_time_sec": 1.53,
        "timing_error_ms": -30.0,
        "band_strengths": {"low": 0.2, "mid": 0.8, "high": 0.2},
        "classification_margin": 0.6,
        "strength": 0.88,
        "subdivision": 2,
        "beat_index": 1,
        "drum_class": "snare",
        "confidence": 0.84,
        "is_accent": False,
    },
]


class ReviewTests(unittest.TestCase):
    def test_summarize_beatmaps_reports_density_and_distribution(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_beatmaps(EVENTS, Path(tmp), source_path="song.mp3", title="Song")

            report = summarize_beatmaps(paths)

        self.assertEqual(report["schema_version"], "drum2taiko.review.v1")
        self.assertEqual(report["difficulties"]["hard"]["notes"], 3)
        self.assertEqual(report["difficulties"]["hard"]["drum_classes"]["kick"], 1)
        self.assertIn("don", report["difficulties"]["hard"]["lanes"])
        self.assertGreaterEqual(report["difficulties"]["hard"]["peak_5s_nps"], 0.0)
        self.assertEqual(report["difficulties"]["hard"]["confidence"]["low_events"], 0)
        self.assertEqual(report["difficulties"]["hard"]["timing"]["median_error_ms"], -20.0)
        self.assertEqual(report["difficulties"]["hard"]["timing"]["suggested_chart_offset_ms"], 20.0)
        self.assertTrue(report["difficulties"]["hard"]["density_10s"])
        self.assertIn("switch_rate", report["difficulties"]["hard"]["lane_motif"])
        self.assertGreaterEqual(report["difficulties"]["hard"]["lane_motif"]["max_same_lane_run"], 1)
        self.assertEqual(report["offset_calibration"]["suggested_chart_offset_ms"], 20.0)
        self.assertEqual(report["offset_calibration"]["source_difficulty"], "hard")

    def test_write_review_report_outputs_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_beatmaps(EVENTS, Path(tmp), source_path="song.mp3", title="Song")
            report_path = write_review_report(paths, Path(tmp) / "review_report.json")
            payload = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["title"], "Song")
        self.assertIn("normal", payload["difficulties"])


if __name__ == "__main__":
    unittest.main()
