import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from music2taiko.analysis.candidates import candidate_from_time, extract_drum_events


class AnalysisTests(unittest.TestCase):
    def test_candidate_from_time_includes_diagnostic_fields(self):
        event = candidate_from_time(1.25, strength=0.8, grid_index=4)

        self.assertEqual(event["source_time_sec"], 1.25)
        self.assertEqual(event["timing_error_ms"], 0.0)
        self.assertEqual(event["band_strengths"], {"low": 0.0, "mid": 0.0, "high": 0.0})
        self.assertEqual(event["classification_margin"], 0.0)

    def test_extract_drum_events_uses_16_bit_pcm_wav_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "impulses.wav"
            rate = 8000
            samples = [0] * rate
            for impulse_time in [0.2, 0.55]:
                start = int(rate * impulse_time)
                for offset in range(80):
                    samples[start + offset] = 28000

            with wave.open(str(path), "wb") as handle:
                handle.setnchannels(1)
                handle.setsampwidth(2)
                handle.setframerate(rate)
                handle.writeframes(b"".join(struct.pack("<h", sample) for sample in samples))

            events = extract_drum_events(path, prefer_librosa=False)

        self.assertEqual(len(events), 2)
        self.assertTrue(math.isclose(events[0]["time_sec"], 0.2, abs_tol=0.02), events)
        self.assertTrue(math.isclose(events[1]["time_sec"], 0.55, abs_tol=0.02), events)


if __name__ == "__main__":
    unittest.main()
