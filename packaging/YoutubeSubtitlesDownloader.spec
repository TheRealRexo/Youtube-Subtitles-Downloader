# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification for macOS, Windows, and Linux builds."""

from pathlib import Path
import os
import sys

SPEC_DIR = Path(SPECPATH).resolve()
ROOT = SPEC_DIR.parent
APP_NAME = "Youtube Subtitles Downloader"
ASSETS = ROOT / "assets"
VENDOR = ROOT / "vendor"


def vendor_binaries():
    binaries = []
    if not VENDOR.is_dir():
        return binaries

    for name in (
        "yt-dlp",
        "yt-dlp.exe",
        "ffmpeg",
        "ffmpeg.exe",
        "ffprobe",
        "ffprobe.exe",
    ):
        path = VENDOR / name
        if path.is_file():
            binaries.append((str(path), "bin"))
    return binaries


datas = [(str(ASSETS), "assets")]
license_path = ROOT / "LICENSE"
if license_path.is_file():
    datas.append((str(license_path), "."))

icon = None
if sys.platform == "darwin":
    icon = str(ASSETS / "icon.icns")
elif os.name == "nt":
    icon = str(ASSETS / "icon.ico")

a = Analysis(
    [str(ROOT / "src" / "youtube_subtitles_downloader" / "__main__.py")],
    pathex=[str(ROOT / "src")],
    binaries=vendor_binaries(),
    datas=datas,
    hiddenimports=["pyperclip"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "pytest",
        "unittest",
        "pydoc",
        "PyQt6.QtQml",
        "PyQt6.QtQuick",
        "PyQt6.QtQuickWidgets",
        "PyQt6.QtWebEngineCore",
        "PyQt6.QtWebEngineWidgets",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=str(ASSETS / "icon.icns"),
        bundle_identifier="com.therealrexo.youtubesubtitlesdownloader",
        info_plist={
            "CFBundleDisplayName": APP_NAME,
            "CFBundleName": APP_NAME,
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "1.0.0",
            "NSHighResolutionCapable": True,
            "NSRequiresAquaSystemAppearance": False,
            "LSMinimumSystemVersion": "12.0",
            "LSApplicationCategoryType": "public.app-category.utilities",
            "NSHumanReadableCopyright": (
                "Copyright (C) 2026 TheRealRexo. "
                "AGPL-3.0-or-later."
            ),
        },
    )
