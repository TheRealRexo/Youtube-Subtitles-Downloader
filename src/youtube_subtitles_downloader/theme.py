"""Dark theme, palette, and platform-aware font helpers."""

from __future__ import annotations

from PyQt6.QtGui import QColor, QFontDatabase, QPalette


MONOSPACE_CANDIDATES = [
    "SF Mono",
    "Menlo",
    "Consolas",
    "Cascadia Mono",
    "DejaVu Sans Mono",
    "Liberation Mono",
    "Courier New",
    "monospace",
]


APP_STYLESHEET = """
QMainWindow,
QWidget#CentralWidget {
    background-color: #121212;
}

QWidget {
    color: #f2f2f2;
    font-family: "SF Pro Text", "Helvetica Neue", "Segoe UI", "Ubuntu",
                 "DejaVu Sans", Arial, sans-serif;
    font-size: 13px;
}

QLabel#TitleLabel {
    color: #ffffff;
    font-size: 25px;
    font-weight: 700;
}

QLabel#SubtitleLabel {
    color: #8f8f8f;
    font-size: 13px;
}

QLabel#FieldLabel {
    color: #b8b8b8;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    padding-top: 2px;
}

QLineEdit {
    background-color: #1e1e1e;
    border: 1px solid #333333;
    border-radius: 8px;
    color: #ffffff;
    min-height: 40px;
    padding: 0 12px;
    selection-background-color: #ff4444;
    selection-color: #ffffff;
}

QLineEdit:hover {
    border: 1px solid #444444;
}

QLineEdit:focus {
    border: 1px solid #ff4444;
}

QLineEdit:disabled {
    color: #777777;
    background-color: #181818;
    border-color: #2a2a2a;
}

QPushButton {
    background-color: #1e1e1e;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    color: #f2f2f2;
    font-weight: 600;
    min-height: 40px;
    padding: 0 16px;
}

QPushButton:hover {
    background-color: #2a2a2a;
    border-color: #505050;
}

QPushButton:pressed {
    background-color: #161616;
}

QPushButton:disabled {
    background-color: #181818;
    border-color: #2a2a2a;
    color: #666666;
}

QPushButton#AnalyzeButton {
    background-color: #0a84ff;
    border: 1px solid #0a84ff;
    color: #ffffff;
    min-width: 132px;
}

QPushButton#AnalyzeButton:hover {
    background-color: #2f95ff;
    border-color: #2f95ff;
}

QPushButton#AnalyzeButton:pressed {
    background-color: #0069d9;
    border-color: #0069d9;
}

QPushButton#AnalyzeButton:disabled {
    background-color: #1c3552;
    border-color: #1c3552;
    color: #7f9ab8;
}

QPushButton#ExtractButton {
    background-color: #ff4444;
    border: 1px solid #ff4444;
    color: #ffffff;
    min-width: 132px;
}

QPushButton#ExtractButton:hover {
    background-color: #ff5c5c;
    border-color: #ff5c5c;
}

QPushButton#ExtractButton:pressed {
    background-color: #d93636;
    border-color: #d93636;
}

QPushButton#ExtractButton:disabled {
    background-color: #3a2020;
    border-color: #3a2020;
    color: #8a6666;
}

QComboBox {
    background-color: #1e1e1e;
    border: 1px solid #333333;
    border-radius: 8px;
    color: #ffffff;
    min-height: 40px;
    padding: 0 12px;
}

QComboBox:hover {
    border: 1px solid #444444;
}

QComboBox:focus {
    border: 1px solid #ff4444;
}

QComboBox:disabled {
    color: #777777;
    background-color: #181818;
    border-color: #2a2a2a;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #b8b8b8;
    height: 0;
    width: 0;
    margin-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #1e1e1e;
    border: 1px solid #3a3a3a;
    color: #ffffff;
    outline: 0;
    selection-background-color: #ff4444;
    selection-color: #ffffff;
}

QListView {
    background-color: #1e1e1e;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    color: #ffffff;
    outline: 0;
    padding: 4px;
}

QListView::item {
    background-color: #1e1e1e;
    border-radius: 4px;
    color: #ffffff;
    min-height: 20px;
    padding: 8px 10px;
}

QListView::item:hover {
    background-color: #2a2a2a;
    color: #ffffff;
}

QListView::item:selected {
    background-color: #ff4444;
    color: #ffffff;
}

QTextEdit#LogView {
    background-color: #0d0d0d;
    border: 1px solid #2c2c2c;
    border-radius: 10px;
    color: #e8e8e8;
    font-family: "SF Mono", "Menlo", "Consolas", "DejaVu Sans Mono",
                 "Courier New", monospace;
    font-size: 12px;
    padding: 12px;
    selection-background-color: #ff4444;
    selection-color: #ffffff;
}

QScrollBar:vertical {
    background: #121212;
    border: none;
    margin: 0;
    width: 12px;
}

QScrollBar::handle:vertical {
    background: #3a3a3a;
    border-radius: 6px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: #505050;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background: #121212;
    border: none;
    height: 12px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #3a3a3a;
    border-radius: 6px;
    min-width: 24px;
}

QScrollBar::handle:horizontal:hover {
    background: #505050;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: none;
}

QLabel#StatusLabel {
    color: #8f8f8f;
    font-size: 12px;
    padding-top: 2px;
}

QMenuBar {
    background-color: #121212;
    color: #f2f2f2;
}

QMenuBar::item {
    background: transparent;
    color: #f2f2f2;
    padding: 4px 10px;
}

QMenuBar::item:selected {
    background-color: #2a2a2a;
    border-radius: 4px;
}

QMenu {
    background-color: #1e1e1e;
    border: 1px solid #3a3a3a;
    color: #f2f2f2;
    padding: 4px;
}

QMenu::item {
    border-radius: 4px;
    padding: 7px 22px 7px 14px;
}

QMenu::item:selected {
    background-color: #ff4444;
    color: #ffffff;
}

QMenu::separator {
    background-color: #333333;
    height: 1px;
    margin: 4px 8px;
}

QToolTip {
    background-color: #1e1e1e;
    border: 1px solid #3a3a3a;
    color: #ffffff;
    padding: 6px;
}
"""


POPUP_STYLESHEET = """
QListView {
    background-color: #1e1e1e;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    color: #ffffff;
    outline: 0;
    padding: 4px;
}

QListView::item {
    background-color: #1e1e1e;
    border-radius: 4px;
    color: #ffffff;
    min-height: 20px;
    padding: 8px 10px;
}

QListView::item:hover {
    background-color: #2a2a2a;
    color: #ffffff;
}

QListView::item:selected {
    background-color: #ff4444;
    color: #ffffff;
}
"""


def monospace_font_family() -> str:
    """Pick the best available monospace font for the current OS."""
    try:
        available = set(QFontDatabase.families())
    except Exception:
        available = set()

    for family in MONOSPACE_CANDIDATES:
        if family in available:
            return family
    return "monospace"


def build_dark_palette() -> QPalette:
    """Return a dark palette so native dialogs and menus match the app."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#121212"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#f2f2f2"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#1e1e1e"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#242424"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#f2f2f2"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#1e1e1e"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#f2f2f2"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#ff4444"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#1e1e1e"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#6f6f6f"))
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Text,
        QColor("#6b6b6b"),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        QColor("#6b6b6b"),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.WindowText,
        QColor("#6b6b6b"),
    )
    return palette
