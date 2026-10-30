"""Worker helper tests that do not launch yt-dlp."""

from __future__ import annotations

import unittest
from pathlib import Path

from youtube_subtitles_downloader.workers import ExtractWorker


class ExtractWorkerTests(unittest.TestCase):
    def test_choose_subtitle_file_prefers_language(self) -> None:
        files = [
            Path("/tmp/video.de.srt"),
            Path("/tmp/video.en.srt"),
        ]
        chosen = ExtractWorker.choose_subtitle_file(files, "en")
        self.assertEqual(chosen.name, "video.en.srt")

    def test_choose_subtitle_file_falls_back_to_first(self) -> None:
        files = [Path("/tmp/video.de.srt")]
        chosen = ExtractWorker.choose_subtitle_file(files, "en")
        self.assertEqual(chosen.name, "video.de.srt")


if __name__ == "__main__":
    unittest.main()
