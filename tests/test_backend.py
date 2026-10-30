"""Backend helper tests that do not require a display server."""

from __future__ import annotations

import subprocess
import unittest

from youtube_subtitles_downloader.backend import (
    install_hint,
    parse_metadata,
    process_error,
)


class BackendTests(unittest.TestCase):
    def test_parse_metadata_uses_last_json_line(self) -> None:
        stdout = 'not json\n{"title": "First"}\n{"title": "Second"}\n'
        self.assertEqual(parse_metadata(stdout), {"title": "Second"})

    def test_parse_metadata_returns_none_for_invalid_output(self) -> None:
        self.assertIsNone(parse_metadata("no metadata here"))

    def test_process_error_prefers_stderr(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["yt-dlp"], returncode=1, stdout="stdout", stderr="stderr"
        )
        self.assertEqual(process_error(completed, "fallback"), "stderr")

    def test_process_error_uses_fallback(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["yt-dlp"], returncode=1, stdout="", stderr=""
        )
        self.assertEqual(process_error(completed, "fallback"), "fallback")

    def test_install_hints_are_non_empty(self) -> None:
        self.assertTrue(install_hint("yt-dlp"))
        self.assertTrue(install_hint("ffmpeg"))


if __name__ == "__main__":
    unittest.main()
