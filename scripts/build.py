#!/usr/bin/env python3
"""Build a native desktop bundle for the current operating system."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "packaging" / "YoutubeSubtitlesDownloader.spec"
DIST = ROOT / "dist"
BUILD = ROOT / "build"
APP_NAME = "Youtube Subtitles Downloader"
PLATFORM = platform.system().lower()
MACHINE = platform.machine().lower()


def platform_tag() -> str:
    if PLATFORM == "darwin":
        return "macos-arm64" if MACHINE in {"arm64", "aarch64"} else "macos-x86_64"
    if PLATFORM == "windows":
        return "windows-x64" if MACHINE in {"amd64", "x86_64"} else f"windows-{MACHINE}"
    if PLATFORM == "linux":
        return "linux-x64" if MACHINE in {"amd64", "x86_64"} else f"linux-{MACHINE}"
    return f"{PLATFORM}-{MACHINE}"


def run(command: list[str], **kwargs) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True, **kwargs)


def ensure_tools() -> bool:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print(
            "PyInstaller is not installed.\n"
            f"Install the build dependencies with:\n"
            f"  {sys.executable} -m pip install --break-system-packages "
            "-r requirements-dev.txt",
            file=sys.stderr,
        )
        return False
    return True


def build_icons() -> None:
    run([sys.executable, str(ROOT / "scripts" / "build_icons.py")])


def fetch_ytdlp() -> None:
    run([sys.executable, str(ROOT / "scripts" / "fetch_ytdlp.py")])


def clean() -> None:
    for directory in (DIST, BUILD):
        if directory.exists():
            print(f"Removing {directory}")
            shutil.rmtree(directory)


def run_pyinstaller() -> None:
    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            str(SPEC),
            "--noconfirm",
            "--clean",
            "--distpath",
            str(DIST),
            "--workpath",
            str(BUILD),
        ]
    )


def app_bundle() -> Path:
    return DIST / f"{APP_NAME}.app"


def windows_bundle() -> Path:
    return DIST / APP_NAME


def linux_bundle() -> Path:
    return DIST / APP_NAME


def sign_macos_app(path: Path, identity: str) -> None:
    if shutil.which("codesign") is None:
        print("codesign is not available; skipping signing.")
        return
    run(
        [
            "codesign",
            "--force",
            "--deep",
            "--sign",
            identity,
            str(path),
        ]
    )


def install_macos_app(path: Path) -> None:
    destination = Path("/Applications") / path.name
    applications = Path("/Applications")

    if not applications.exists():
        raise RuntimeError("/Applications does not exist on this system.")
    if not os.access(applications, os.W_OK):
        raise RuntimeError(
            "The current user cannot write to /Applications. "
            "Run the build with an administrator account."
        )

    if destination.exists():
        print(f"Replacing existing {destination}")
        shutil.rmtree(destination)

    print(f"Installing {destination}")
    if shutil.which("ditto"):
        run(["ditto", str(path), str(destination)])
    else:
        shutil.copytree(path, destination, symlinks=True)

    # Ad-hoc signing keeps Apple Silicon happy after copying the bundle.
    sign_macos_app(destination, "-")


def package_macos() -> Path:
    archive = DIST / f"YoutubeSubtitlesDownloader-{platform_tag()}.zip"
    if archive.exists():
        archive.unlink()

    if shutil.which("ditto"):
        run(
            [
                "ditto",
                "-c",
                "-k",
                "--sequesterRsrc",
                "--keepParent",
                str(app_bundle()),
                str(archive),
            ]
        )
    else:
        shutil.make_archive(
            str(archive.with_suffix("")),
            "zip",
            root_dir=DIST,
            base_dir=app_bundle().name,
        )
    return archive


def package_windows() -> Path:
    archive_base = DIST / f"YoutubeSubtitlesDownloader-{platform_tag()}"
    archive = Path(
        shutil.make_archive(
            str(archive_base),
            "zip",
            root_dir=DIST,
            base_dir=windows_bundle().name,
        )
    )
    return archive


def package_linux() -> Path:
    bundle = linux_bundle()
    desktop_file = (
        ROOT / "packaging" / "linux" / "youtube-subtitles-downloader.desktop"
    )
    icon_file = ROOT / "assets" / "icon.png"

    if desktop_file.is_file():
        shutil.copy2(desktop_file, bundle / desktop_file.name)
    if icon_file.is_file():
        shutil.copy2(icon_file, bundle / "youtube-subtitles-downloader.png")

    archive = DIST / f"YoutubeSubtitlesDownloader-{platform_tag()}.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(bundle, arcname=bundle.name)
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install the built macOS app into /Applications",
    )
    parser.add_argument(
        "--no-bundle-ytdlp",
        action="store_true",
        help="Do not download a standalone yt-dlp into the app",
    )
    parser.add_argument(
        "--skip-icons",
        action="store_true",
        help="Reuse committed icon files instead of regenerating them",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove dist/ and build/ before building",
    )
    parser.add_argument(
        "--no-package",
        action="store_true",
        help="Build the app but do not create a zip/tarball",
    )
    parser.add_argument(
        "--sign-identity",
        default="-",
        help="macOS codesign identity (default: ad-hoc '-')",
    )
    args = parser.parse_args()

    if args.install and PLATFORM != "darwin":
        print("--install is only supported on macOS.", file=sys.stderr)
        return 1

    if not ensure_tools():
        return 1

    if args.clean:
        clean()

    if not args.skip_icons:
        build_icons()

    if not args.no_bundle_ytdlp:
        fetch_ytdlp()

    run_pyinstaller()

    if PLATFORM == "darwin":
        if not app_bundle().exists():
            print(f"Build output missing: {app_bundle()}", file=sys.stderr)
            return 1
        sign_macos_app(app_bundle(), args.sign_identity)
        if args.install:
            install_macos_app(app_bundle())
        if not args.no_package:
            print(f"Created {package_macos()}")
    elif PLATFORM == "windows":
        if not windows_bundle().exists():
            print(f"Build output missing: {windows_bundle()}", file=sys.stderr)
            return 1
        if not args.no_package:
            print(f"Created {package_windows()}")
    elif PLATFORM == "linux":
        if not linux_bundle().exists():
            print(f"Build output missing: {linux_bundle()}", file=sys.stderr)
            return 1
        if not args.no_package:
            print(f"Created {package_linux()}")
    else:
        print(f"Unsupported build platform: {PLATFORM}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
