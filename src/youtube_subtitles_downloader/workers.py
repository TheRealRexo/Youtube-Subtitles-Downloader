"""Background workers for metadata, subtitle, and video operations."""

from __future__ import annotations

import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from .backend import (
    ToolNotFoundError,
    parse_metadata,
    process_error,
    require_ffmpeg,
    run_ytdlp,
)


class AnalyzeWorker(QThread):
    """Fetch video metadata with yt-dlp without downloading the video."""

    succeeded = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, url: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._url = url

    def run(self) -> None:
        try:
            completed = run_ytdlp(
                ["--dump-json", "--skip-download", self._url],
                timeout=120,
            )
        except ToolNotFoundError as exc:
            self.failed.emit(str(exc))
            return
        except subprocess.TimeoutExpired:
            self.failed.emit("Metadata analysis timed out after 120 seconds.")
            return
        except OSError as exc:
            self.failed.emit(f"Could not start yt-dlp: {exc}")
            return
        except Exception as exc:  # noqa: BLE001 - report worker errors to the UI
            self.failed.emit(f"Unexpected metadata error: {exc}")
            return

        if completed.returncode != 0:
            self.failed.emit(
                process_error(
                    completed,
                    f"yt-dlp exited with code {completed.returncode}.",
                )
            )
            return

        stdout = (completed.stdout or "").strip()
        if not stdout:
            self.failed.emit("yt-dlp returned no metadata for this URL.")
            return

        metadata = parse_metadata(stdout)
        if metadata is None:
            self.failed.emit("Could not parse the metadata returned by yt-dlp.")
            return

        self.succeeded.emit(metadata)


class ExtractWorker(QThread):
    """Download the selected subtitle track and convert it to SRT."""

    succeeded = pyqtSignal(str, str)
    failed = pyqtSignal(str)

    def __init__(
        self,
        url: str,
        language: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._url = url
        self._language = language

    @staticmethod
    def choose_subtitle_file(files: list[Path], language: str) -> Path:
        language_marker = f".{language}."
        for path in files:
            if language_marker in path.name:
                return path
        for path in files:
            if path.name.endswith(f".{language}.srt"):
                return path
        return files[0]

    def run(self) -> None:
        try:
            ffmpeg = require_ffmpeg()
            with tempfile.TemporaryDirectory(prefix="subyou-") as temp_dir:
                # Keep every generated file inside the temporary directory.
                output_template = os.path.join(temp_dir, "%(id)s.%(ext)s")
                command = [
                    "--skip-download",
                    "--write-subs",
                    "--write-auto-subs",
                    "--sub-lang",
                    self._language,
                    "--convert-subs",
                    "srt",
                    "--ffmpeg-location",
                    str(ffmpeg.parent),
                    self._url,
                    "-o",
                    output_template,
                ]
                completed = run_ytdlp(command, timeout=300)

                if completed.returncode != 0:
                    self.failed.emit(
                        process_error(
                            completed,
                            f"yt-dlp exited with code {completed.returncode}.",
                        )
                    )
                    return

                subtitle_files = sorted(Path(temp_dir).rglob("*.srt"))
                if not subtitle_files:
                    self.failed.emit(
                        process_error(
                            completed,
                            "yt-dlp finished, but no SRT file was produced. "
                            "The selected language may not have a usable track.",
                        )
                    )
                    return

                chosen = self.choose_subtitle_file(
                    subtitle_files, self._language
                )
                raw_text = chosen.read_text(
                    encoding="utf-8", errors="replace"
                )

                if not raw_text.strip():
                    self.failed.emit("The downloaded subtitle file was empty.")
                    return

                # Intentionally preserve the file exactly as yt-dlp wrote it.
                self.succeeded.emit(raw_text, self._language)
        except ToolNotFoundError as exc:
            self.failed.emit(str(exc))
        except subprocess.TimeoutExpired:
            self.failed.emit("Subtitle extraction timed out after 300 seconds.")
        except OSError as exc:
            self.failed.emit(f"Could not extract subtitles: {exc}")
        except Exception as exc:  # noqa: BLE001 - report worker errors to the UI
            self.failed.emit(f"Unexpected subtitle extraction error: {exc}")


class DownloadWorker(QThread):
    """Download the best video-only stream and merge it to MP4."""

    succeeded = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(
        self,
        url: str,
        destination: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._url = url
        self._destination = Path(destination)
        self._timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def run(self) -> None:
        try:
            ffmpeg = require_ffmpeg()
            self._destination.mkdir(parents=True, exist_ok=True)
            output_template = str(
                self._destination / f"video_{self._timestamp}.%(ext)s"
            )
            command = [
                "-f",
                "bestvideo*+bestaudio/best",
                "--merge-output-format",
                "mp4",
                "--ffmpeg-location",
                str(ffmpeg.parent),
                "-o",
                output_template,
                self._url,
            ]
            completed = run_ytdlp(command, timeout=3600)

            if completed.returncode != 0:
                self.failed.emit(
                    process_error(
                        completed,
                        f"yt-dlp exited with code {completed.returncode}.",
                    )
                )
                return

            files = sorted(
                self._destination.glob(f"video_{self._timestamp}.*")
            )
            if not files:
                self.failed.emit(
                    "The download finished, but the output file could not be found."
                )
                return

            final_file = next(
                (path for path in files if path.suffix.lower() == ".mp4"),
                files[0],
            )
            self.succeeded.emit(str(final_file))
        except ToolNotFoundError as exc:
            self.failed.emit(str(exc))
        except subprocess.TimeoutExpired:
            self.failed.emit("Video download timed out after 3600 seconds.")
        except OSError as exc:
            self.failed.emit(f"Could not download the video: {exc}")
        except Exception as exc:  # noqa: BLE001 - report worker errors to the UI
            self.failed.emit(f"Unexpected video download error: {exc}")
