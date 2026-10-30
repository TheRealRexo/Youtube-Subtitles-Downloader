#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="Youtube Subtitles Downloader"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
INSTALL_ROOT="$DATA_HOME/youtube-subtitles-downloader"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$DATA_HOME/applications"
ICON_DIR="$DATA_HOME/icons/hicolor/512x512/apps"

mkdir -p "$BIN_DIR" "$DESKTOP_DIR" "$ICON_DIR"

if [ -d "$INSTALL_ROOT" ]; then
    rm -rf "$INSTALL_ROOT"
fi

mkdir -p "$INSTALL_ROOT"
cp -R "$SOURCE_DIR"/. "$INSTALL_ROOT"/

ln -sf "$INSTALL_ROOT/$APP_NAME" "$BIN_DIR/youtube-subtitles-downloader"

if [ -f "$SOURCE_DIR/youtube-subtitles-downloader.png" ]; then
    cp "$SOURCE_DIR/youtube-subtitles-downloader.png" \
        "$ICON_DIR/youtube-subtitles-downloader.png"
fi

if [ -f "$SOURCE_DIR/youtube-subtitles-downloader.desktop" ]; then
    sed "s|^Exec=.*|Exec=$INSTALL_ROOT/$APP_NAME|" \
        "$SOURCE_DIR/youtube-subtitles-downloader.desktop" \
        > "$DESKTOP_DIR/youtube-subtitles-downloader.desktop"
    chmod +x "$DESKTOP_DIR/youtube-subtitles-downloader.desktop"
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi

echo "Installed to $INSTALL_ROOT"
echo "Run with: youtube-subtitles-downloader"
