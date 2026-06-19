from __future__ import annotations

from pathlib import Path


def _load_audio(source_path: str | Path):
    import librosa

    return librosa.load(str(source_path), sr=None, mono=False)


def _open_sound_file(output: Path, *, sample_rate: int, channels: int):
    import soundfile as sf

    return sf.SoundFile(
        output,
        mode="w",
        samplerate=sample_rate,
        channels=channels,
        format="OGG",
        subtype="VORBIS",
    )


def convert_to_ogg(source_path: str | Path, output_path: str | Path, *, chunk_size: int = 44100) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    samples, sample_rate = _load_audio(source_path)
    if getattr(samples, "ndim", 1) == 2:
        samples = samples.T
    channels = 1 if getattr(samples, "ndim", 1) == 1 else int(samples.shape[1])
    with _open_sound_file(output, sample_rate=sample_rate, channels=channels) as handle:
        for start in range(0, len(samples), chunk_size):
            handle.write(samples[start : start + chunk_size])
    return output
