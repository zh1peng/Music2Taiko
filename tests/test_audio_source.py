import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class AudioSourceTests(unittest.TestCase):
    def test_local_audio_source_returns_path_without_download(self):
        from music2taiko.audio.source import resolve_audio_source

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "song.mp3"
            source.write_bytes(b"audio")

            resolved = resolve_audio_source(str(source), Path(tmp) / "downloads")

        self.assertEqual(resolved, source)

    def test_youtube_url_downloads_audio_to_download_dir(self):
        from music2taiko.audio.source import resolve_audio_source

        calls = {}

        def fake_downloader(url, output_dir):
            calls["url"] = url
            calls["output_dir"] = output_dir
            path = output_dir / "video.mp3"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"audio")
            return path

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_audio"
            resolved = resolve_audio_source(
                "https://youtu.be/example123",
                output_dir,
                downloader=fake_downloader,
            )

        self.assertEqual(resolved.name, "video.mp3")
        self.assertEqual(calls["url"], "https://youtu.be/example123")
        self.assertEqual(calls["output_dir"], output_dir)

    def test_schemeless_youtube_url_downloads_audio(self):
        from music2taiko.audio.source import resolve_audio_source

        calls = {}

        def fake_downloader(url, output_dir):
            calls["url"] = url
            path = output_dir / "video.mp3"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"audio")
            return path

        with tempfile.TemporaryDirectory() as tmp:
            resolved = resolve_audio_source(
                "youtube.com/watch?v=example123",
                Path(tmp) / "source_audio",
                downloader=fake_downloader,
            )

        self.assertEqual(resolved.name, "video.mp3")
        self.assertEqual(calls["url"], "https://youtube.com/watch?v=example123")

    def test_unsupported_url_is_rejected(self):
        from music2taiko.audio.source import resolve_audio_source

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "Only YouTube URLs"):
                resolve_audio_source("https://example.com/song.mp3", Path(tmp))

    def test_youtube_downloader_enables_node_ejs_and_ffmpeg(self):
        from music2taiko.audio.source import download_youtube_audio

        captured = {}

        class FakeYoutubeDL:
            def __init__(self, options):
                captured["options"] = options

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def extract_info(self, url, download):
                captured["url"] = url
                captured["download"] = download
                path = Path(captured["output_dir"]) / "video.mp3"
                path.write_bytes(b"audio")
                return {"requested_downloads": [{"filepath": str(path)}]}

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            captured["output_dir"] = output_dir
            with patch("yt_dlp.YoutubeDL", FakeYoutubeDL):
                with patch("music2taiko.audio.source._ffmpeg_location", return_value="ffmpeg.exe"):
                    resolved = download_youtube_audio("https://youtu.be/example123", output_dir)

        self.assertEqual(resolved.name, "video.mp3")
        self.assertEqual(captured["url"], "https://youtu.be/example123")
        self.assertTrue(captured["download"])
        self.assertEqual(captured["options"]["js_runtimes"], {"node": {}})
        self.assertEqual(captured["options"]["remote_components"], ["ejs:github"])
        self.assertEqual(captured["options"]["ffmpeg_location"], "ffmpeg.exe")


if __name__ == "__main__":
    unittest.main()
