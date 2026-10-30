#!/usr/bin/env python3
"""Generate PNG, ICNS, and ICO application icons from assets/icon.svg."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt  # noqa: E402
from PyQt6.QtGui import QGuiApplication, QImage, QPainter  # noqa: E402
from PyQt6.QtSvg import QSvgRenderer  # noqa: E402


ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SVG_PATH = ASSETS / "icon.svg"


def render_icon(renderer: QSvgRenderer, size: int) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    renderer.render(painter)
    painter.end()
    return image


def save_image(image: QImage, path: Path) -> None:
    if not image.save(str(path), "PNG"):
        raise RuntimeError(f"Could not write {path}")


def build_macos_icns(images: dict[int, QImage]) -> None:
    if sys.platform != "darwin" or shutil.which("iconutil") is None:
        print("Skipping .icns generation (iconutil is only available on macOS).")
        return

    iconset = ASSETS / "icon.iconset"
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir(parents=True)

    icon_files = {
        16: ["icon_16x16.png"],
        32: ["icon_16x16@2x.png", "icon_32x32.png"],
        64: ["icon_32x32@2x.png"],
        128: ["icon_128x128.png"],
        256: ["icon_128x128@2x.png", "icon_256x256.png"],
        512: ["icon_256x256@2x.png", "icon_512x512.png"],
        1024: ["icon_512x512@2x.png"],
    }

    for size, names in icon_files.items():
        for name in names:
            save_image(images[size], iconset / name)

    subprocess.run(
        [
            "iconutil",
            "-c",
            "icns",
            str(iconset),
            "-o",
            str(ASSETS / "icon.icns"),
        ],
        check=True,
    )
    shutil.rmtree(iconset)
    print(f"Wrote {ASSETS / 'icon.icns'}")


def build_windows_ico() -> None:
    try:
        from PIL import Image
    except ImportError:
        print("Pillow is not installed; skipping .ico generation.")
        return

    source = ASSETS / "icon_1024.png"
    with Image.open(source) as image:
        image = image.convert("RGBA")
        image.save(
            ASSETS / "icon.ico",
            sizes=[
                (16, 16),
                (24, 24),
                (32, 32),
                (48, 48),
                (64, 64),
                (128, 128),
                (256, 256),
            ],
        )
    print(f"Wrote {ASSETS / 'icon.ico'}")


def main() -> int:
    if not SVG_PATH.exists():
        print(f"Missing icon source: {SVG_PATH}", file=sys.stderr)
        return 1

    app = QGuiApplication(sys.argv)
    renderer = QSvgRenderer(str(SVG_PATH))
    if not renderer.isValid():
        print(f"Invalid SVG: {SVG_PATH}", file=sys.stderr)
        return 1

    images: dict[int, QImage] = {}
    for size in (16, 32, 64, 128, 256, 512, 1024):
        image = render_icon(renderer, size)
        images[size] = image
        save_image(image, ASSETS / f"icon_{size}.png")

    save_image(images[512], ASSETS / "icon.png")
    save_image(images[1024], ASSETS / "icon_1024.png")

    build_macos_icns(images)
    build_windows_ico()

    app.quit()
    print(f"Wrote PNG icons to {ASSETS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
