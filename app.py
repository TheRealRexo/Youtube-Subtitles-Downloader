#!/usr/bin/env python3
"""Compatibility launcher for running the app from the project root."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from youtube_subtitles_downloader.main import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
