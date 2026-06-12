import json
import math
import tempfile
import unittest
from pathlib import Path

from drum2taiko.io.psygodot import build_beatmap, write_beatmaps


class PsyGodotTests(unittest.TestCase):
    def test_build_beatmap_preserves_drum_events_and_applies_chart_offset(self):
        events = [
            {
                "time_sec": 1.0,
                "quantized_time_sec": 1.0,
                "strength": 0.92,
                "subdivision": 0,
                "beat_index": 1,
                "drum_class": "kick",
                "confidence": 0.86,
                "is_accent": True,
            },
            {
                "time_sec": 1.5,
                "quantized_time_sec": 1.5,
                "strength": 0.66,
                "subdivision": 2,
                "beat_index": 1,
                "drum_class": "hat",
                "confidence": 0.72,
                "is_accent": False,
            },
        ]

        beatmap = build_beatmap(
            events,
            difficulty="hard",
            source_path="song.wav",
            title="Song",
            audio_offset_ms=12.0,
            chart_offset_ms=25.0,
        )

        self.assertEqual(beatmap["audio_offset_ms"], 12.0)
        self.assertEqual(beatmap["chart_offset_ms"], 25.0)
        self.assertEqual([event["drum_class"] for event in beatmap["drum_events"]], ["kick", "hat"])
        self.assertEqual([note["lane"] for note in beatmap["notes"]], ["don", "ka"])
        self.assertTrue(math.isclose(beatmap["notes"][0]["time_sec"], 1.025, abs_tol=0.0001))

    def test_write_beatmaps_passes_offsets_to_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_beatmaps(
                [0.5, 1.0, 1.5],
                Path(tmp),
                source_path="track.wav",
                title="track",
                audio_offset_ms=10.0,
                chart_offset_ms=-20.0,
            )
            payload = json.loads(paths["hard"].read_text(encoding="utf-8"))

        self.assertEqual(payload["audio_offset_ms"], 10.0)
        self.assertEqual(payload["chart_offset_ms"], -20.0)
        self.assertTrue(payload["drum_events"])


if __name__ == "__main__":
    unittest.main()
