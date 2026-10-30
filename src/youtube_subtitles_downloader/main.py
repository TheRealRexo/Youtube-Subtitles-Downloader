"""Application entry point."""

from __future__ import annotations

import os
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from . import APP_NAME, __version__
from .main_window import SubtitleDownloaderWindow
from .resources import resource_path
from .theme import APP_STYLESHEET, build_dark_palette


def _set_windows_app_id() -> None:
    """Give Windows a stable taskbar identity for the app icon."""
    if os.name != "nt":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "com.therealrexo.youtubesubtitlesdownloader"
        )
    except Exception:
        pass


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv if argv is None else argv)

    if "--version" in args:
        print(f"{APP_NAME} {__version__}")
        return 0

    if "--self-test" in args:
        from .backend import find_ffmpeg, find_ytdlp

        ytdlp = find_ytdlp()
        ffmpeg = find_ffmpeg()
        print(f"yt-dlp: {ytdlp or 'not found'}")
        print(f"ffmpeg: {ffmpeg or 'not found'}")
        return 0 if ytdlp is not None else 1

    _set_windows_app_id()

    app = QApplication(args)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName("TheRealRexo")
    app.setOrganizationDomain("github.com")
    app.setApplicationVersion(__version__)
    app.setQuitOnLastWindowClosed(True)
    app.setStyle("Fusion")
    app.setPalette(build_dark_palette())
    app.setStyleSheet(APP_STYLESHEET)

    if sys.platform.startswith("linux"):
        app.setDesktopFileName("youtube-subtitles-downloader")

    icon_path = resource_path("assets", "icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = SubtitleDownloaderWindow()
    window.show()
    return app.exec()
