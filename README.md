<p align="center">
  <img src="assets/icon.png" width="112" alt="YouTube Subtitles Downloader icon">
</p>

<h1 align="center">YouTube Subtitles Downloader</h1>

<p align="center">
  A native, cross-platform desktop app for downloading YouTube subtitles as clean SRT files.
</p>

<p align="center">
  <a href="https://github.com/TheRealRexo/Youtube-Subtitles-Downloader/actions/workflows/build.yml">
    <img src="https://github.com/TheRealRexo/Youtube-Subtitles-Downloader/actions/workflows/build.yml/badge.svg" alt="Build status">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-AGPL--3.0-orange" alt="AGPL-3.0 license">
  </a>
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-blue" alt="macOS, Windows, Linux">
</p>

YouTube Subtitles Downloader uses [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) to inspect videos, list official and auto-generated subtitle tracks, extract the selected language, and preserve the resulting SRT timing blocks exactly as written.

## Features

- Native PyQt6 desktop interface with a modern dark theme.
- Analyze a YouTube URL and list every official and automatic caption track.
- Language picker shows `en [Official]`, `ko [Auto]`, and similar labels.
- Extract the selected track as raw SRT, with no line cleaning or timing changes.
- Copy the SRT to the clipboard with `pyperclip`.
- Save with an automatic filename such as `subtitles_en_20261030_143000.srt`.
- Download the video-only stream to `video_20261030_143000.mp4`.
- Asynchronous `QThread` workers keep the UI responsive.
- Live URL tracking resets stale language choices and disables extraction.
- macOS combo-box popup fix using an independent `QListView` and explicit dark QSS.
- Cross-platform tool discovery for `yt-dlp` and `ffmpeg`, including Finder/Explorer-launched apps.
- Build scripts and GitHub Actions workflows for macOS, Windows, and Linux.

## Download

Prebuilt desktop bundles are published on the [Releases page](https://github.com/TheRealRexo/Youtube-Subtitles-Downloader/releases).

| Platform | Package |
| --- | --- |
| macOS Apple Silicon | `YoutubeSubtitlesDownloader-macos-arm64.zip` |
| macOS Intel | `YoutubeSubtitlesDownloader-macos-x86_64.zip` |
| Windows x64 | `YoutubeSubtitlesDownloader-windows-x64.zip` |
| Linux x64 | `YoutubeSubtitlesDownloader-linux-x64.tar.gz` |

### macOS

1. Download and unzip the macOS package.
2. Drag **Youtube Subtitles Downloader.app** into `/Applications`.
3. Open it from Launchpad or Applications.

The build is ad-hoc signed. If macOS blocks the first launch, right-click the app and choose **Open**.

### Windows

1. Download and unzip the Windows package.
2. Run `Youtube Subtitles Downloader.exe` from the extracted folder.

An optional Inno Setup installer script is available at `packaging/windows/installer.iss`.

### Linux

```bash
tar -xzf YoutubeSubtitlesDownloader-linux-x64.tar.gz
cd "Youtube Subtitles Downloader"
./"Youtube Subtitles Downloader"
```

Or install it for the current user:

```bash
./install.sh
youtube-subtitles-downloader
```

## Run From Source

### macOS with Homebrew Python

```bash
git clone https://github.com/TheRealRexo/Youtube-Subtitles-Downloader.git
cd Youtube-Subtitles-Downloader

/opt/homebrew/bin/python3 -m pip install --break-system-packages -r requirements.txt
/opt/homebrew/bin/python3 app.py
```

### Windows and Linux

A virtual environment is recommended:

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

You can also install the package as a command:

```bash
python -m pip install -e .
youtube-subtitles-downloader
```

## External Tools

The prebuilt applications bundle a standalone `yt-dlp` binary. `ffmpeg` is required for subtitle conversion to SRT and for merging video-only streams into MP4.

| Platform | Install |
| --- | --- |
| macOS | `brew install yt-dlp ffmpeg` |
| Windows | `winget install yt-dlp.yt-dlp` and `winget install Gyan.FFmpeg` |
| Linux | `sudo apt install yt-dlp ffmpeg` |

The app searches for tools in this order:

1. `YTDLP_PATH` / `FFMPEG_PATH` environment variables.
2. Bundled binaries inside the app (`vendor/` during development, `bin/` in packaged builds).
3. The system `PATH`.
4. Common installation folders such as `/opt/homebrew/bin`, `/usr/local/bin`, `~/.local/bin`, WinGet Links, Scoop shims, Chocolatey, and Python Scripts folders.

To bundle `ffmpeg` and `ffprobe`, place the platform binaries in `vendor/` before building. The PyInstaller spec includes them automatically.

## Build Native Bundles

Install the development dependencies first:

```bash
python -m pip install -r requirements-dev.txt
```

On macOS Homebrew Python:

```bash
/opt/homebrew/bin/python3 -m pip install --break-system-packages -r requirements-dev.txt
```

Build for the current operating system:

```bash
python scripts/build.py
```

Build and install the macOS app into `/Applications`:

```bash
python scripts/build.py --install
```

Useful options:

```text
--install             Install the macOS .app into /Applications
--no-bundle-ytdlp     Do not download a standalone yt-dlp into the build
--skip-icons          Reuse committed icon files
--clean               Remove dist/ and build/ before building
--no-package          Build without creating a zip or tarball
--sign-identity ID    macOS codesign identity (default: ad-hoc "-")
```

Build outputs:

| Platform | Output |
| --- | --- |
| macOS | `dist/Youtube Subtitles Downloader.app` and a `.zip` |
| Windows | `dist/Youtube Subtitles Downloader/` and a `.zip` |
| Linux | `dist/Youtube Subtitles Downloader/` and a `.tar.gz` |

## GitHub Actions

`.github/workflows/build.yml` builds and uploads artifacts for:

- macOS arm64
- macOS x86_64
- Windows x64
- Linux x64

Pushing a tag such as `v1.0.0` also creates a GitHub Release and attaches the platform archives.

## Project Layout

```text
src/youtube_subtitles_downloader/
  backend.py       Tool discovery, subprocess environment, yt-dlp helpers
  main.py          QApplication entry point
  main_window.py   Main window and UI state
  resources.py     Source and PyInstaller resource paths
  theme.py         Dark palette, QSS, platform font selection
  workers.py       QThread metadata, subtitle, and video workers
packaging/
  YoutubeSubtitlesDownloader.spec
  linux/
  windows/
scripts/
  build.py
  build_icons.py
  fetch_ytdlp.py
assets/
  icon.svg
  icon.icns
  icon.ico
  icon.png
```

## Usage

1. Paste a YouTube URL.
2. Click **Analyze Video**.
3. Pick a language from the dropdown.
4. Click **Extract SRT**.
5. Copy the result, save it, or download the video only.

If you edit the URL after analysis, the language list resets and extraction is disabled until you analyze the new URL.

## Notes

- This project does not bypass DRM or access controls. Use it only for content you are allowed to download.
- Respect YouTube's Terms of Service and the rights of content creators.
- `ffmpeg` is a separate project with its own license terms.
- The app is licensed under AGPL-3.0-or-later. See [LICENSE](LICENSE).
