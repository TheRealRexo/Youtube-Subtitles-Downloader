"""Helpers for locating bundled and source-tree resources."""

from __future__ import annotations

import sys
from pathlib import Path


def resource_path(*parts: str) -> Path:
    """Return a resource path in both development and PyInstaller builds."""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    else:
        # src/youtube_subtitles_downloader/resources.py -> project root
        base = Path(__file__).resolve().parent.parent.parent
    return base.joinpath(*parts)
