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
                "source_time_sec": 1.02,
                "timing_error_ms": -20.0,
                "band_strengths": {"low": 0.9, "mid": 0.2, "high": 0.1},
                "classification_margin": 0.7,
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
        self.assertEqual(beatmap["drum_events"][0]["source_time_sec"], 1.02)
        self.assertEqual(beatmap["drum_events"][0]["timing_error_ms"], -20.0)
        self.assertEqual(beatmap["drum_events"][0]["band_strengths"]["low"], 0.9)
        self.assertEqual(beatmap["drum_events"][0]["classification_margin"], 0.7)
        self.assertEqual([note["lane"] for note in beatmap["notes"]], ["don", "ka"])
        self.assertTrue(math.isclose(beatmap["notes"][0]["time_sec"], 1.025, abs_tol=0.0001))

    def test_easy_uses_ka_for_clear_cymbal_or_hat_contrast(self):
        events = [
            {
                "time_sec": 1.0,
                "quantized_time_sec": 1.0,
                "strength": 0.9,
                "subdivision": 0,
                "beat_index": 1,
                "drum_class": "kick",
                "confidence": 0.9,
                "is_accent": True,
            },
            {
                "time_sec": 2.0,
                "quantized_time_sec": 2.0,
                "strength": 0.88,
                "subdivision": 0,
                "beat_index": 2,
                "drum_class": "cymbal",
                "confidence": 0.82,
                "is_accent": True,
            },
        ]

        beatmap = build_beatmap(events, difficulty="easy", source_path="song.wav", title="Song")

        self.assertEqual([note["lane"] for note in beatmap["notes"]], ["don", "ka"])

    def test_easy_uses_snare_as_controlled_ka_contrast(self):
        events = [
            {
                "time_sec": 1.0,
                "quantized_time_sec": 1.0,
                "strength": 0.9,
                "subdivision": 0,
                "beat_index": 1,
                "drum_class": "kick",
                "confidence": 0.9,
                "is_accent": True,
            },
            {
                "time_sec": 2.0,
                "quantized_time_sec": 2.0,
                "strength": 0.82,
                "subdivision": 0,
                "beat_index": 2,
                "drum_class": "snare",
                "confidence": 0.7,
                "is_accent": True,
            },
        ]

        beatmap = build_beatmap(events, difficulty="easy", source_path="song.wav", title="Song")

        self.assertEqual([note["lane"] for note in beatmap["notes"]], ["don", "ka"])

    def test_easy_keeps_simple_backbeat_and_backfills_long_gaps(self):
        events = [
            {
                "time_sec": time_sec,
                "quantized_time_sec": time_sec,
                "strength": 0.86 if subdivision == 0 else 0.5,
                "subdivision": subdivision,
                "beat_index": index // 2,
                "drum_class": "kick" if subdivision == 0 else "unknown",
                "confidence": 0.82 if subdivision == 0 else 0.5,
                "is_accent": subdivision == 0,
            }
            for index, (time_sec, subdivision) in enumerate(
                [
                    (0.0, 0),
                    (2.0, 2),
                    (4.0, 2),
                    (6.0, 2),
                    (8.0, 2),
                    (10.0, 2),
                    (12.0, 0),
                ]
            )
        ]

        beatmap = build_beatmap(events, difficulty="easy", source_path="song.wav", title="Song")
        times = [note["time_sec"] for note in beatmap["notes"]]

        self.assertGreater(len(times), 2)
        self.assertLessEqual(max_note_gap(times), 4.0)

    def test_easy_uses_simple_taiko_motif_for_ambiguous_events(self):
        events = [
            {
                "time_sec": 1.0 + (index * 0.5),
                "quantized_time_sec": 1.0 + (index * 0.5),
                "strength": 0.66,
                "subdivision": 0 if index % 2 == 0 else 2,
                "beat_index": index // 2,
                "drum_class": "unknown",
                "confidence": 0.64,
                "is_accent": False,
            }
            for index in range(8)
        ]

        beatmap = build_beatmap(events, difficulty="easy", source_path="song.wav", title="Song")
        lanes = [note["lane"] for note in beatmap["notes"]]

        self.assertEqual(lanes, ["don", "don", "ka", "don", "don", "ka", "don", "don"])

    def test_easy_adapts_coverage_in_active_drum_passages(self):
        events = [
            {
                "time_sec": index * 0.5,
                "quantized_time_sec": index * 0.5,
                "strength": 0.56,
                "subdivision": index % 4,
                "beat_index": index // 4,
                "drum_class": "unknown",
                "confidence": 0.56,
                "is_accent": False,
            }
            for index in range(16)
        ]

        beatmap = build_beatmap(events, difficulty="easy", source_path="song.wav", title="Song")
        times = [note["time_sec"] for note in beatmap["notes"]]
        lanes = [note["lane"] for note in beatmap["notes"]]

        self.assertGreaterEqual(len(times), 11)
        self.assertLessEqual(max_note_gap(times), 1.0)
        self.assertIn("ka", lanes)
        self.assertLessEqual(max_same_lane_run(lanes), 3)

    def test_hard_breaks_excessively_long_same_lane_runs(self):
        events = [
            {
                "time_sec": 1.0 + (index * 0.2),
                "quantized_time_sec": 1.0 + (index * 0.2),
                "strength": 0.9,
                "subdivision": index % 4,
                "beat_index": index // 4,
                "drum_class": "hat",
                "confidence": 0.8,
                "is_accent": False,
            }
            for index in range(20)
        ]

        beatmap = build_beatmap(events, difficulty="hard", source_path="song.wav", title="Song")
        lanes = [note["lane"] for note in beatmap["notes"]]

        self.assertIn("don", lanes)
        self.assertLessEqual(max_same_lane_run(lanes), 16)

    def test_hard_caps_ka_ratio_for_dense_hat_or_cymbal_passages(self):
        events = [
            {
                "time_sec": 1.0 + (index * 0.2),
                "quantized_time_sec": 1.0 + (index * 0.2),
                "strength": 0.72,
                "subdivision": index % 4,
                "beat_index": index // 4,
                "drum_class": "hat",
                "confidence": 0.78,
                "is_accent": False,
            }
            for index in range(32)
        ]

        beatmap = build_beatmap(events, difficulty="hard", source_path="song.wav", title="Song")
        lanes = [note["lane"] for note in beatmap["notes"]]
        ka_ratio = lanes.count("ka") / len(lanes)

        self.assertLessEqual(ka_ratio, 0.45)
        self.assertGreater(lanes.count("ka"), 0)
        self.assertGreater(lanes.count("don"), lanes.count("ka"))

    def test_hard_caps_ka_ratio_after_mixed_drum_mapping(self):
        classes = ["hat", "snare", "cymbal", "snare"] * 12
        events = [
            {
                "time_sec": 1.0 + (index * 0.18),
                "quantized_time_sec": 1.0 + (index * 0.18),
                "strength": 0.74,
                "subdivision": index % 4,
                "beat_index": index // 4,
                "drum_class": drum_class,
                "confidence": 0.8,
                "is_accent": False,
            }
            for index, drum_class in enumerate(classes)
        ]

        beatmap = build_beatmap(events, difficulty="hard", source_path="song.wav", title="Song")
        lanes = [note["lane"] for note in beatmap["notes"]]
        ka_ratio = lanes.count("ka") / len(lanes)

        self.assertLessEqual(ka_ratio, 0.45)
        self.assertGreater(lanes.count("ka"), 0)

    def test_normal_backfills_long_gaps_from_available_drum_events(self):
        events = [
            {
                "time_sec": time_sec,
                "quantized_time_sec": time_sec,
                "strength": 0.9 if index in {0, 6} else 0.52,
                "subdivision": 0 if index in {0, 6} else 1,
                "beat_index": index,
                "drum_class": "kick" if index in {0, 6} else "unknown",
                "confidence": 0.85 if index in {0, 6} else 0.52,
                "is_accent": index in {0, 6},
            }
            for index, time_sec in enumerate([0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0])
        ]

        beatmap = build_beatmap(events, difficulty="normal", source_path="song.wav", title="Song")
        times = [note["time_sec"] for note in beatmap["notes"]]

        self.assertGreater(len(times), 2)
        self.assertLessEqual(max_note_gap(times), 4.0)

    def test_normal_uses_deterministic_taiko_motif_for_ambiguous_events(self):
        events = [
            {
                "time_sec": 1.0 + (index * 0.5),
                "quantized_time_sec": 1.0 + (index * 0.5),
                "strength": 0.72,
                "subdivision": 0 if index % 2 == 0 else 2,
                "beat_index": index // 2,
                "drum_class": "unknown",
                "confidence": 0.7,
                "is_accent": False,
            }
            for index in range(9)
        ]

        beatmap = build_beatmap(events, difficulty="normal", source_path="song.wav", title="Song")
        lanes = [note["lane"] for note in beatmap["notes"]]

        self.assertEqual(lanes, ["don", "ka", "don", "don", "don", "ka", "don", "ka", "ka"])

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


def max_same_lane_run(lanes):
    longest = 0
    current = 0
    previous = None
    for lane in lanes:
        current = current + 1 if lane == previous else 1
        longest = max(longest, current)
        previous = lane
    return longest


def max_note_gap(times):
    return max((later - earlier for earlier, later in zip(times, times[1:])), default=0.0)


if __name__ == "__main__":
    unittest.main()
