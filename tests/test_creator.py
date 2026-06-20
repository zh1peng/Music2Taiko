import json
import tempfile
import unittest
from pathlib import Path

from music2taiko.creator import (
    apply_pattern_plan_to_anchors,
    build_aligned_samples,
    build_arrangement_context,
    build_candidate_timing_anchors,
    compose_course_from_events,
    default_pattern_plan,
    normalize_output_id,
    retrieve_similar_charts,
)


EVENTS = [
    {
        "time_sec": 0.0,
        "quantized_time_sec": 0.0,
        "strength": 0.95,
        "drum_class": "kick",
        "confidence": 0.9,
        "is_accent": True,
        "beat_index": 0,
        "subdivision": 0,
    },
    {
        "time_sec": 0.5,
        "quantized_time_sec": 0.5,
        "strength": 0.75,
        "drum_class": "hat",
        "confidence": 0.8,
        "is_accent": False,
        "beat_index": 0,
        "subdivision": 2,
    },
    {
        "time_sec": 1.0,
        "quantized_time_sec": 1.0,
        "strength": 0.96,
        "drum_class": "cymbal",
        "confidence": 0.9,
        "is_accent": True,
        "beat_index": 1,
        "subdivision": 0,
    },
]


class CreatorTests(unittest.TestCase):
    def test_normalize_output_id_shortens_and_sanitizes_titles(self):
        output_id = normalize_output_id(
            '099 - Very long title with / forbidden : characters and lots of trailing words?!',
            song_id="099",
            max_length=32,
        )

        self.assertEqual(output_id, "099-very-long-title-with")
        self.assertLessEqual(len(output_id), 32)

    def test_retrieve_similar_charts_ranks_by_bpm_and_event_density(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp)
            (corpus / "manifest.json").write_text(
                json.dumps(
                    [
                        {
                            "song_id": "001",
                            "title": "Close",
                            "bpm": 121.0,
                            "audio_duration_sec": 60.0,
                            "drum_event_count": 120,
                            "courses": ["Oni"],
                            "course_summaries": [{"course": "Oni", "level": 8, "note_total": 360}],
                        },
                        {
                            "song_id": "002",
                            "title": "Far",
                            "bpm": 200.0,
                            "audio_duration_sec": 60.0,
                            "drum_event_count": 700,
                            "courses": ["Oni"],
                            "course_summaries": [{"course": "Oni", "level": 8, "note_total": 900}],
                        },
                    ]
                ),
                encoding="utf-8",
            )

            matches = retrieve_similar_charts(
                bpm=120.0,
                duration_sec=60.0,
                drum_events=EVENTS * 40,
                difficulty="oni",
                corpus_dir=corpus,
                limit=2,
            )

        self.assertEqual(matches[0]["song_id"], "001")
        self.assertGreater(matches[0]["similarity"], matches[1]["similarity"])
        self.assertTrue(matches[0]["similarity_reasons"])

    def test_compose_course_from_events_maps_audio_events_to_full_tja_types(self):
        course = compose_course_from_events(
            EVENTS,
            difficulty="oni",
            bpm=120.0,
            level=8,
            title="Song",
        )

        self.assertEqual(course["difficulty"], "oni")
        self.assertEqual(course["level"], 8)
        self.assertEqual([note["type"] for note in course["notes"]], ["big_don", "ka", "big_ka"])
        self.assertTrue(course["aligned_samples"])

    def test_build_arrangement_context_exposes_anchors_and_retrieval_for_llm(self):
        matches = [{"song_id": "001", "title": "Reference", "similarity": 0.9}]

        context = build_arrangement_context(
            title="Song",
            difficulty="oni",
            bpm=120.0,
            drum_events=EVENTS,
            retrieval_matches=matches,
        )

        self.assertEqual(context["title"], "Song")
        self.assertEqual(context["difficulty"], "oni")
        self.assertEqual(context["retrieval_context"]["matches"], matches)
        self.assertEqual(context["candidate_timing_anchors"][0]["role"], "primary")
        self.assertEqual(context["candidate_timing_anchors"][1]["suggested_symbol"], "K")

    def test_apply_pattern_plan_to_anchors_uses_plan_symbols_on_source_timing(self):
        anchors = build_candidate_timing_anchors(EVENTS)
        plan = {
            "difficulty": "oni",
            "level": 8,
            "sections": [
                {
                    "name": "main",
                    "start_sec": 0.0,
                    "end_sec": 2.0,
                    "pattern": "DKD",
                    "use_big_on_accents": False,
                }
            ],
        }

        course = apply_pattern_plan_to_anchors(
            anchors,
            plan,
            bpm=120.0,
            title="Song",
            song_id="song",
        )

        self.assertEqual([note["time_sec"] for note in course["notes"]], [0.0, 0.5, 1.0])
        self.assertEqual([note["type"] for note in course["notes"]], ["don", "ka", "don"])
        self.assertTrue(course["aligned_samples"])

    def test_apply_pattern_plan_resets_pattern_phase_by_measure_grid(self):
        anchors = [
            {"time_sec": 0.0, "drum_class": "kick", "strength": 1.0, "confidence": 1.0, "is_accent": False},
            {"time_sec": 0.25, "drum_class": "hat", "strength": 1.0, "confidence": 1.0, "is_accent": False},
            {"time_sec": 2.0, "drum_class": "kick", "strength": 1.0, "confidence": 1.0, "is_accent": False},
            {"time_sec": 2.25, "drum_class": "hat", "strength": 1.0, "confidence": 1.0, "is_accent": False},
        ]
        plan = {
            "difficulty": "normal",
            "level": 5,
            "sections": [{"name": "main", "start_sec": 0.0, "end_sec": 3.0, "pattern": "D-K-"}],
        }

        course = apply_pattern_plan_to_anchors(anchors, plan, bpm=120.0, song_id="song")

        self.assertEqual([note["time_sec"] for note in course["notes"]], [0.0, 0.25, 2.0, 2.25])
        self.assertEqual([note["type"] for note in course["notes"]], ["don", "ka", "don", "ka"])

    def test_apply_pattern_plan_keeps_ka_as_accent_color_not_sustained_run(self):
        anchors = [
            {"time_sec": 0.375, "drum_class": "hat", "strength": 1.0, "confidence": 1.0, "is_accent": False},
            {"time_sec": 0.875, "drum_class": "hat", "strength": 0.8, "confidence": 0.8, "is_accent": False},
            {"time_sec": 1.25, "drum_class": "hat", "strength": 0.7, "confidence": 0.7, "is_accent": False},
            {"time_sec": 2.375, "drum_class": "hat", "strength": 0.65, "confidence": 0.7, "is_accent": False},
        ]
        plan = {
            "difficulty": "hard",
            "level": 7,
            "sections": [
                {"name": "main", "start_sec": 0.0, "end_sec": 3.0, "pattern": "D-DK D-DK D-K- D---"}
            ],
        }

        course = apply_pattern_plan_to_anchors(anchors, plan, bpm=120.0, song_id="song")
        note_types = [note["type"] for note in course["notes"]]

        self.assertNotIn(["ka", "ka", "ka"], [note_types[index : index + 3] for index in range(len(note_types) - 2)])

    def test_apply_pattern_plan_orients_blue_lead_triplets_as_red_call_blue_answer(self):
        anchors = [
            {"time_sec": 1.25, "drum_class": "snare", "strength": 0.9, "confidence": 0.9, "is_accent": False},
            {"time_sec": 1.375, "drum_class": "snare", "strength": 0.8, "confidence": 0.8, "is_accent": False},
            {"time_sec": 1.5, "drum_class": "tom", "strength": 0.75, "confidence": 0.8, "is_accent": False},
        ]
        plan = {
            "difficulty": "oni",
            "level": 8,
            "sections": [
                {"name": "main", "start_sec": 0.0, "end_sec": 2.0, "pattern": "D-DK D-DK D-KD D---"}
            ],
        }

        course = apply_pattern_plan_to_anchors(anchors, plan, bpm=120.0, song_id="song")

        self.assertEqual([note["type"] for note in course["notes"]], ["don", "ka", "ka"])

    def test_apply_pattern_plan_allows_clear_hat_or_cymbal_answer_to_lead_two_note_answer(self):
        anchors = [
            {"time_sec": 1.25, "drum_class": "hat", "strength": 0.95, "confidence": 0.95, "is_accent": False},
            {"time_sec": 1.375, "drum_class": "snare", "strength": 0.8, "confidence": 0.8, "is_accent": False},
        ]
        plan = {
            "difficulty": "hard",
            "level": 7,
            "sections": [
                {"name": "main", "start_sec": 0.0, "end_sec": 2.0, "pattern": "D-DK D-DK D-KD D---"}
            ],
        }

        course = apply_pattern_plan_to_anchors(anchors, plan, bpm=120.0, song_id="song")

        self.assertEqual([note["type"] for note in course["notes"]], ["ka", "don"])

    def test_apply_pattern_plan_still_orients_hat_lead_kdd_triplets(self):
        anchors = [
            {"time_sec": 1.25, "drum_class": "hat", "strength": 0.95, "confidence": 0.95, "is_accent": False},
            {"time_sec": 1.375, "drum_class": "snare", "strength": 0.8, "confidence": 0.8, "is_accent": False},
            {"time_sec": 1.5, "drum_class": "tom", "strength": 0.75, "confidence": 0.8, "is_accent": False},
        ]
        plan = {
            "difficulty": "hard",
            "level": 7,
            "sections": [
                {"name": "main", "start_sec": 0.0, "end_sec": 2.0, "pattern": "D-DK D-DK D-KD D---"}
            ],
        }

        course = apply_pattern_plan_to_anchors(anchors, plan, bpm=120.0, song_id="song")

        self.assertEqual([note["type"] for note in course["notes"]], ["don", "ka", "ka"])

    def test_apply_pattern_plan_orients_blue_lead_motifs_inside_long_phrases(self):
        anchors = [
            {"time_sec": 0.0, "drum_class": "kick", "strength": 0.9, "confidence": 0.9, "is_accent": True},
            {"time_sec": 0.125, "drum_class": "snare", "strength": 0.8, "confidence": 0.8, "is_accent": False},
            {"time_sec": 0.25, "drum_class": "snare", "strength": 0.8, "confidence": 0.8, "is_accent": False},
            {"time_sec": 0.375, "drum_class": "tom", "strength": 0.75, "confidence": 0.8, "is_accent": False},
            {"time_sec": 0.5, "drum_class": "tom", "strength": 0.7, "confidence": 0.8, "is_accent": False},
        ]
        plan = {
            "difficulty": "oni",
            "level": 8,
            "sections": [{"name": "main", "start_sec": 0.0, "end_sec": 2.0, "pattern": "DDKDD"}],
        }

        course = apply_pattern_plan_to_anchors(anchors, plan, bpm=120.0, song_id="song")

        self.assertNotIn(
            ["ka", "don", "don"],
            [[note["type"] for note in course["notes"]][index : index + 3] for index in range(3)],
        )
        self.assertEqual([note["type"] for note in course["notes"]][2:5], ["don", "ka", "ka"])

    def test_apply_pattern_plan_orients_visual_triplets_in_fast_songs(self):
        anchors = [
            {"time_sec": 0.0, "drum_class": "snare", "strength": 0.8, "confidence": 0.8, "is_accent": False},
            {"time_sec": 0.34, "drum_class": "tom", "strength": 0.75, "confidence": 0.8, "is_accent": False},
            {"time_sec": 0.68, "drum_class": "tom", "strength": 0.7, "confidence": 0.8, "is_accent": False},
        ]
        plan = {
            "difficulty": "hard",
            "level": 7,
            "sections": [{"name": "main", "start_sec": 0.0, "end_sec": 2.0, "pattern": "K----D---D------"}],
        }

        course = apply_pattern_plan_to_anchors(anchors, plan, bpm=200.0, song_id="song")

        self.assertEqual([note["type"] for note in course["notes"]], ["don", "ka", "ka"])

    def test_default_easy_and_normal_patterns_cover_basic_pulse_without_sparse_deletion(self):
        anchors = [
            {
                "time_sec": index * 0.25,
                "drum_class": "kick" if index % 4 == 0 else "snare",
                "strength": 0.85,
                "confidence": 0.8,
                "is_accent": index % 4 == 0,
            }
            for index in range(16)
        ]

        easy = apply_pattern_plan_to_anchors(
            anchors,
            default_pattern_plan({"difficulty": "easy", "candidate_timing_anchors": anchors}),
            bpm=120.0,
            song_id="song",
        )
        normal = apply_pattern_plan_to_anchors(
            anchors,
            default_pattern_plan({"difficulty": "normal", "candidate_timing_anchors": anchors}),
            bpm=120.0,
            song_id="song",
        )

        self.assertGreaterEqual(len(easy["notes"]), 8)
        self.assertGreaterEqual(len(normal["notes"]), 12)
        self.assertGreaterEqual(len(normal["notes"]), len(easy["notes"]))
        self.assertGreaterEqual(
            sum(1 for note in easy["notes"] if note["type"] in {"don", "big_don"}),
            len(easy["notes"]) - 2,
        )

    def test_apply_pattern_plan_dedupes_notes_that_share_tja_slots(self):
        anchors = [
            {"time_sec": 0.0, "drum_class": "kick", "strength": 1.0, "confidence": 1.0, "is_accent": True},
            {"time_sec": 0.04, "drum_class": "snare", "strength": 1.0, "confidence": 1.0, "is_accent": True},
            {"time_sec": 0.25, "drum_class": "hat", "strength": 1.0, "confidence": 1.0, "is_accent": False},
        ]
        plan = {
            "difficulty": "oni",
            "level": 8,
            "sections": [{"name": "main", "start_sec": 0.0, "end_sec": 1.0, "pattern": "DDD"}],
        }

        course = apply_pattern_plan_to_anchors(anchors, plan, bpm=120.0, song_id="song")

        self.assertEqual([note["time_sec"] for note in course["notes"]], [0.0, 0.25])
        self.assertEqual(len(course["aligned_samples"]), 2)

    def test_apply_pattern_plan_respects_lead_in_silence(self):
        anchors = build_candidate_timing_anchors(
            [
                {**EVENTS[0], "time_sec": 1.0, "quantized_time_sec": 1.0},
                {**EVENTS[1], "time_sec": 3.0, "quantized_time_sec": 3.0},
            ]
        )
        plan = {
            "difficulty": "normal",
            "level": 5,
            "sections": [{"name": "main", "start_sec": 0.0, "end_sec": 4.0, "pattern": "DD"}],
        }

        course = apply_pattern_plan_to_anchors(anchors, plan, bpm=120.0, lead_in_sec=2.5)

        self.assertEqual([note["time_sec"] for note in course["notes"]], [3.0])

    def test_default_pattern_plan_is_editable_llm_design_payload(self):
        context = build_arrangement_context(
            title="Song",
            difficulty="normal",
            bpm=120.0,
            drum_events=EVENTS,
            retrieval_matches=[],
        )

        plan = default_pattern_plan(context)

        self.assertEqual(plan["difficulty"], "normal")
        self.assertIn("sections", plan)
        self.assertIn("pattern", plan["sections"][0])

    def test_build_aligned_samples_links_chart_notes_to_nearest_drum_events(self):
        chart_notes = [{"time_sec": 0.48, "type": "ka"}]

        samples = build_aligned_samples("song", "Oni", chart_notes, EVENTS)

        self.assertEqual(samples[0]["song_id"], "song")
        self.assertEqual(samples[0]["course"], "Oni")
        self.assertEqual(samples[0]["chart_decision"], "ka")
        self.assertEqual(samples[0]["audio_window"]["nearest_drum_class"], "hat")
        self.assertAlmostEqual(samples[0]["audio_window"]["nearest_event_delta_ms"], 20.0)

    def test_compose_course_from_events_keeps_easy_and_normal_groove_anchors(self):
        events = [
            {
                "time_sec": index * 0.25,
                "quantized_time_sec": index * 0.25,
                "strength": 0.62,
                "drum_class": "hat" if index % 2 else "kick",
                "confidence": 0.8,
                "is_accent": index % 4 == 0,
                "beat_index": index // 2,
                "subdivision": (index % 2) * 2,
            }
            for index in range(16)
        ]

        easy = compose_course_from_events(events, difficulty="easy", bpm=120.0, title="Song")
        normal = compose_course_from_events(events, difficulty="normal", bpm=120.0, title="Song")

        self.assertGreaterEqual(len(easy["notes"]), 8)
        self.assertGreaterEqual(len(normal["notes"]), 12)
        self.assertGreaterEqual(len(normal["notes"]), len(easy["notes"]))


if __name__ == "__main__":
    unittest.main()
