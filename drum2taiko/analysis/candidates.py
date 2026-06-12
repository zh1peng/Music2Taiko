from __future__ import annotations

import wave
from pathlib import Path
from typing import Any


DRUM_CLASSES = {"kick", "snare", "hat", "cymbal", "tom", "unknown"}


def _fallback_wav_onsets(path: Path) -> list[float]:
    with wave.open(str(path), "rb") as handle:
        frame_count = handle.getnframes()
        sample_rate = handle.getframerate()
        sample_width = handle.getsampwidth()
        channels = handle.getnchannels()
        raw = handle.readframes(frame_count)

    if sample_width != 2:
        raise ValueError("fallback WAV reader only supports 16-bit PCM")

    amplitudes: list[float] = []
    frame_width = sample_width * channels
    for offset in range(0, len(raw), frame_width):
        total = 0.0
        for channel in range(channels):
            start = offset + channel * sample_width
            sample = int.from_bytes(raw[start : start + sample_width], "little", signed=True)
            total += abs(sample) / 32768.0
        amplitudes.append(total / channels)

    if not amplitudes:
        return []

    block_size = max(1, sample_rate // 100)
    envelope = [
        sum(amplitudes[index : index + block_size]) / len(amplitudes[index : index + block_size])
        for index in range(0, len(amplitudes), block_size)
    ]
    threshold = max(envelope) * 0.45
    if threshold <= 0.0:
        return []

    times: list[float] = []
    last_time = -1.0
    for index, value in enumerate(envelope):
        previous = envelope[index - 1] if index else 0.0
        current_time = index * block_size / sample_rate
        if value >= threshold and previous < threshold and current_time - last_time >= 0.16:
            times.append(round(current_time, 4))
            last_time = current_time
    return times


def _tempo_value(value: Any) -> float:
    try:
        if hasattr(value, "__len__") and len(value) > 0:
            return float(value[0])
    except TypeError:
        pass
    return float(value)


def _frame_strength(onset_envelope: Any, frame: int) -> float:
    if len(onset_envelope) == 0:
        return 0.0
    index = max(0, min(int(frame), len(onset_envelope) - 1))
    return float(onset_envelope[index])


def _quantize_time(time_sec: float, anchor: float, step: float) -> tuple[float, int]:
    grid_index = int(round((time_sec - anchor) / step))
    return round(anchor + (grid_index * step), 4), grid_index


def candidate_from_time(time_sec: float, strength: float = 1.0, grid_index: int = 0) -> dict[str, Any]:
    subdivision = grid_index % 4
    is_accent = subdivision == 0 or strength >= 0.72
    return {
        "time_sec": round(float(time_sec), 4),
        "quantized_time_sec": round(float(time_sec), 4),
        "strength": round(float(strength), 6),
        "subdivision": subdivision,
        "beat_index": grid_index // 4,
        "drum_class": "unknown",
        "confidence": round(float(strength), 6),
        "is_accent": is_accent,
    }


def _safe_ratio(value: float, max_value: float) -> float:
    if max_value <= 0.0:
        return 0.0
    return max(0.0, min(1.0, float(value) / max_value))


def _band_onset_envelopes(librosa: Any, np: Any, samples: Any, sample_rate: int) -> dict[str, Any]:
    spectrum = np.abs(librosa.stft(samples))
    frequencies = librosa.fft_frequencies(sr=sample_rate)
    bands = {
        "low": frequencies < 180,
        "mid": (frequencies >= 180) & (frequencies < 2400),
        "high": frequencies >= 2400,
    }
    envelopes: dict[str, Any] = {}
    for name, mask in bands.items():
        if not np.any(mask):
            envelopes[name] = np.zeros(spectrum.shape[1])
            continue
        band_spectrum = librosa.amplitude_to_db(spectrum[mask, :], ref=np.max)
        envelopes[name] = librosa.onset.onset_strength(S=band_spectrum, sr=sample_rate, aggregate=np.median)
    return envelopes


def _classify_drum_event(
    low_strength: float,
    mid_strength: float,
    high_strength: float,
    full_strength: float,
    *,
    is_accent: bool,
) -> tuple[str, float]:
    strengths = {
        "low": max(0.0, float(low_strength)),
        "mid": max(0.0, float(mid_strength)),
        "high": max(0.0, float(high_strength)),
    }
    dominant = max(strengths, key=strengths.get)
    total = sum(strengths.values())
    dominance = strengths[dominant] / total if total > 0.0 else 0.0
    confidence = max(0.35, min(0.95, (dominance * 0.75) + (max(0.0, min(1.0, full_strength)) * 0.25)))

    if dominant == "low":
        if strengths["mid"] > strengths["low"] * 0.72:
            return "tom", round(confidence * 0.82, 4)
        return "kick", round(confidence, 4)
    if dominant == "mid":
        if strengths["low"] > strengths["mid"] * 0.68:
            return "tom", round(confidence * 0.86, 4)
        return "snare", round(confidence, 4)
    if is_accent and full_strength >= 0.72:
        return "cymbal", round(confidence, 4)
    return "hat", round(confidence, 4)


def extract_drum_events(
    path: str | Path,
    *,
    prefer_librosa: bool = True,
    drum_stem_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    audio_path = Path(path)
    if prefer_librosa:
        try:
            import librosa
            import numpy as np

            analysis_path = Path(drum_stem_path) if drum_stem_path else audio_path
            samples, sample_rate = librosa.load(str(analysis_path), sr=None, mono=True)
            if drum_stem_path:
                percussive = samples
                drum_event_source = "demucs_drums"
            else:
                _, percussive = librosa.effects.hpss(samples)
                drum_event_source = "hpss_percussive"

            onset_envelope = librosa.onset.onset_strength(y=percussive, sr=sample_rate, aggregate=np.median)
            band_envelopes = _band_onset_envelopes(librosa, np, percussive, sample_rate)
            tempo, beat_frames = librosa.beat.beat_track(
                onset_envelope=onset_envelope,
                sr=sample_rate,
                trim=False,
                tightness=110,
            )
            onset_frames = librosa.onset.onset_detect(
                onset_envelope=onset_envelope,
                sr=sample_rate,
                backtrack=False,
                pre_max=3,
                post_max=3,
                pre_avg=8,
                post_avg=8,
                delta=0.18,
                wait=3,
            )
            beat_times = [float(t) for t in librosa.frames_to_time(beat_frames, sr=sample_rate)]
            onset_times = [float(t) for t in librosa.frames_to_time(onset_frames, sr=sample_rate)]
            if len(beat_times) >= 2:
                beat_period = float(np.median(np.diff(beat_times)))
            else:
                beat_period = 60.0 / max(30.0, _tempo_value(tempo))
            beat_period = max(0.25, min(1.5, beat_period))
            grid_step = beat_period / 4.0
            anchor = beat_times[0] if beat_times else 0.0
            max_strength = float(np.max(onset_envelope)) if len(onset_envelope) else 1.0
            if max_strength <= 0.0:
                max_strength = 1.0
            max_band_strengths = {
                name: float(np.max(envelope)) if len(envelope) else 1.0
                for name, envelope in band_envelopes.items()
            }

            by_time: dict[float, dict[str, Any]] = {}
            max_quantize_error = min(0.09, grid_step * 0.48)

            for frame, time_sec in zip(onset_frames, onset_times):
                quantized, grid_index = _quantize_time(time_sec, anchor, grid_step)
                if quantized < 0.0 or abs(quantized - time_sec) > max_quantize_error:
                    continue
                strength = _frame_strength(onset_envelope, int(frame)) / max_strength
                if strength < 0.18:
                    continue
                candidate = candidate_from_time(quantized, strength, grid_index)
                candidate["time_sec"] = round(float(time_sec), 4)
                candidate["quantized_time_sec"] = quantized
                low = _safe_ratio(_frame_strength(band_envelopes["low"], int(frame)), max_band_strengths["low"])
                mid = _safe_ratio(_frame_strength(band_envelopes["mid"], int(frame)), max_band_strengths["mid"])
                high = _safe_ratio(_frame_strength(band_envelopes["high"], int(frame)), max_band_strengths["high"])
                drum_class, confidence = _classify_drum_event(
                    low,
                    mid,
                    high,
                    strength,
                    is_accent=bool(candidate["is_accent"]),
                )
                candidate["drum_class"] = drum_class
                candidate["confidence"] = confidence
                candidate["drum_event_source"] = drum_event_source
                event_key = candidate["quantized_time_sec"]
                existing = by_time.get(event_key)
                if existing is None or candidate["strength"] > existing["strength"]:
                    by_time[event_key] = candidate

            for frame, time_sec in zip(beat_frames, beat_times):
                quantized, grid_index = _quantize_time(time_sec, anchor, grid_step)
                strength = max(0.45, _frame_strength(onset_envelope, int(frame)) / max_strength)
                candidate = candidate_from_time(quantized, strength, grid_index)
                candidate["time_sec"] = round(float(time_sec), 4)
                candidate["quantized_time_sec"] = quantized
                candidate["drum_event_source"] = drum_event_source
                event_key = candidate["quantized_time_sec"]
                existing = by_time.get(event_key)
                if existing is None or candidate["strength"] > existing["strength"]:
                    by_time[event_key] = candidate

            events = sorted(by_time.values(), key=lambda item: item["time_sec"])
            for event in events:
                event["tempo_bpm"] = round(60.0 / beat_period, 3)
            return events
        except ImportError:
            pass

    if audio_path.suffix.lower() != ".wav":
        raise RuntimeError("MP3 analysis requires librosa. Install Drum2Taiko with audio dependencies.")
    return [candidate_from_time(time_sec) for time_sec in _fallback_wav_onsets(audio_path)]
