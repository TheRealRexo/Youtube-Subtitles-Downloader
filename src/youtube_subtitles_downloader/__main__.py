"""Allow ``python -m youtube_subtitles_downloader`` and PyInstaller entry."""

from youtube_subtitles_downloader.main import main


if __name__ == "__main__":
    raise SystemExit(main())
