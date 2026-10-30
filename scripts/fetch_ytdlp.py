#!/usr/bin/env python3
"""Download a standalone yt-dlp binary for the current build platform."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import stat
import subprocess
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "vendor"
RELEASES = "https://github.com/yt-dlp/yt-dlp/releases"


def release_asset() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        return "yt-dlp_macos"
    if system == "windows":
        return "yt-dlp.exe"
    if system == "linux":
        if machine in {"x86_64", "amd64"}:
            return "yt-dlp_linux"
        if machine in {"aarch64", "arm64"}:
            return "yt-dlp_linux_aarch64"
        if machine.startswith("armv7"):
            return "yt-dlp_linux_armv7l"
        raise RuntimeError(f"Unsupported Linux architecture: {machine}")

    raise RuntimeError(f"Unsupported platform: {system} {machine}")


def target_name(asset: str) -> str:
    return "yt-dlp.exe" if asset.endswith(".exe") else "yt-dlp"


def download(url: str, destination: Path) -> None:
    existing_bytes = destination.stat().st_size if destination.exists() else 0
    headers = {
        "User-Agent": "YouTube-Subtitles-Downloader-build/1.0",
        "Accept": "application/octet-stream",
    }
    if existing_bytes:
        headers["Range"] = f"bytes={existing_bytes}-"

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=300) as response:
        status = getattr(response, "status", 200)
        mode = "ab" if existing_bytes and status == 206 else "wb"
        with destination.open(mode) as output:
            shutil.copyfileobj(response, output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version",
        default=os.environ.get("YTDLP_VERSION"),
        help="Release tag, for example 2026.10.21 (default: latest)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Download even if vendor/yt-dlp already exists",
    )
    args = parser.parse_args()

    try:
        asset = release_asset()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    destination = VENDOR / target_name(asset)
    if destination.exists() and not args.force:
        print(f"Using existing {destination}")
        return 0

    if args.version:
        url = f"{RELEASES}/download/{args.version}/{asset}"
    else:
        url = f"{RELEASES}/latest/download/{asset}"

    VENDOR.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".part")

    if args.force:
        temporary.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)

    print(f"Downloading {url}")
    try:
        download(url, temporary)
        temporary.replace(destination)
    except Exception as exc:  # noqa: BLE001 - build helper
        temporary.unlink(missing_ok=True)
        print(f"Could not download yt-dlp: {exc}", file=sys.stderr)
        return 1

    if os.name != "nt":
        destination.chmod(destination.stat().st_mode | stat.S_IXUSR)

    try:
        result = subprocess.run(
            [str(destination), "--version"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        version = (result.stdout or "").strip() or "unknown"
    except Exception:
        version = "unknown"

    print(f"Bundled yt-dlp {version} at {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
