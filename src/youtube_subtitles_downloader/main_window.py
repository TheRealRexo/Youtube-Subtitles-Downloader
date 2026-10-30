"""Main application window."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QStandardPaths, Qt, QUrl
from PyQt6.QtGui import (
    QDesktopServices,
    QFont,
    QIcon,
    QKeySequence,
    QShortcut,
    QTextCursor,
)
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import APP_NAME, __version__
from .resources import resource_path
from .theme import POPUP_STYLESHEET, monospace_font_family
from .workers import AnalyzeWorker, DownloadWorker, ExtractWorker

try:
    import pyperclip
except ImportError:  # pragma: no cover - handled gracefully in the UI
    pyperclip = None


PLACEHOLDER_TEXT = "Analyze link first..."


class SubtitleDownloaderWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()

        self._busy = False
        self._analyzed_url = ""
        self._extracted_language = ""
        self._subtitle_text = ""
        self._last_download_path: Path | None = None

        self._analyze_worker: AnalyzeWorker | None = None
        self._extract_worker: ExtractWorker | None = None
        self._download_worker: DownloadWorker | None = None

        self.setWindowTitle(APP_NAME)
        self.resize(900, 650)
        self.setMinimumSize(750, 550)

        icon_path = resource_path("assets", "icon.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._build_ui()
        self._build_menu()
        self._connect_signals()
        self._reset_language_menu()
        self._refresh_action_states()
        self._set_status("Ready. Paste a YouTube link to begin.")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget(self)
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(24, 22, 24, 18)
        root.setSpacing(14)

        title = QLabel("YouTube Subtitles Downloader")
        title.setObjectName("TitleLabel")
        root.addWidget(title)

        subtitle = QLabel(
            "Extract official or auto-generated captions as clean SRT files."
        )
        subtitle.setObjectName("SubtitleLabel")
        root.addWidget(subtitle)

        url_label = QLabel("VIDEO URL")
        url_label.setObjectName("FieldLabel")
        root.addWidget(url_label)

        url_row = QHBoxLayout()
        url_row.setSpacing(10)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "https://www.youtube.com/watch?v=..."
        )
        self.url_input.setClearButtonEnabled(True)
        self.url_input.setAccessibleName("Video URL")
        self.url_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        url_row.addWidget(self.url_input, 1)

        self.analyze_btn = QPushButton("Analyze Video")
        self.analyze_btn.setObjectName("AnalyzeButton")
        self.analyze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.analyze_btn.setAccessibleName("Analyze Video")
        url_row.addWidget(self.analyze_btn)

        root.addLayout(url_row)

        language_label = QLabel("SUBTITLE LANGUAGE")
        language_label.setObjectName("FieldLabel")
        root.addWidget(language_label)

        language_row = QHBoxLayout()
        language_row.setSpacing(10)

        self.lang_menu = QComboBox()
        self.lang_menu.setObjectName("LanguageCombo")
        self.lang_menu.setAccessibleName("Subtitle language")
        self.lang_menu.setEditable(False)
        self.lang_menu.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.lang_menu.setMaxVisibleItems(14)
        self.lang_menu.setMinimumHeight(40)
        self.lang_menu.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        # Critical macOS fix: use an independent QListView for the popup.
        # Without this, the native popover can expand into a broken,
        # transparent full-screen panel when a video has many languages.
        self.lang_menu.setView(QListView())
        lang_view = self.lang_menu.view()
        lang_view.setObjectName("LanguageListView")
        lang_view.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        lang_view.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        lang_view.setMinimumWidth(360)
        lang_view.setStyleSheet(POPUP_STYLESHEET)
        lang_view.setAlternatingRowColors(False)

        language_row.addWidget(self.lang_menu, 1)

        self.extract_btn = QPushButton("Extract SRT")
        self.extract_btn.setObjectName("ExtractButton")
        self.extract_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.extract_btn.setAccessibleName("Extract SRT")
        self.extract_btn.setEnabled(False)
        language_row.addWidget(self.extract_btn)

        root.addLayout(language_row)

        log_label = QLabel("SUBTITLE OUTPUT")
        log_label.setObjectName("FieldLabel")
        root.addWidget(log_label)

        self.log_view = QTextEdit()
        self.log_view.setObjectName("LogView")
        self.log_view.setReadOnly(True)
        self.log_view.setAcceptRichText(False)
        self.log_view.setFont(QFont(monospace_font_family(), 12))
        self.log_view.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.log_view.setPlaceholderText(
            "Your SRT output will appear here after extraction..."
        )
        self.log_view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        root.addWidget(self.log_view, 1)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setAccessibleName("Copy to Clipboard")
        action_row.addWidget(self.copy_btn, 1)

        self.save_btn = QPushButton("Save File (.srt)")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setAccessibleName("Save File as SRT")
        action_row.addWidget(self.save_btn, 1)

        self.download_btn = QPushButton("Download Video Only")
        self.download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_btn.setAccessibleName("Download Video Only")
        action_row.addWidget(self.download_btn, 1)

        root.addLayout(action_row)

        self.status_label = QLabel("Ready.")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")

        open_downloads_action = file_menu.addAction("Open Downloads Folder")
        open_downloads_action.triggered.connect(self._open_downloads_folder)

        file_menu.addSeparator()

        quit_action = file_menu.addAction("Quit")
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)

        help_menu = self.menuBar().addMenu("&Help")
        about_action = help_menu.addAction(f"About {APP_NAME}")
        about_action.triggered.connect(self._show_about)

    def _connect_signals(self) -> None:
        self.url_input.textChanged.connect(self._on_url_changed)
        self.url_input.returnPressed.connect(self._analyze_video)
        self.analyze_btn.clicked.connect(self._analyze_video)
        self.extract_btn.clicked.connect(self._extract_srt)
        self.copy_btn.clicked.connect(self._copy_to_clipboard)
        self.save_btn.clicked.connect(self._save_srt)
        self.download_btn.clicked.connect(self._download_video)

        QShortcut(
            QKeySequence("Ctrl+Return"), self, activated=self._analyze_video
        )
        QShortcut(
            QKeySequence("Ctrl+Shift+C"),
            self,
            activated=self._copy_to_clipboard,
        )
        QShortcut(
            QKeySequence("Ctrl+Shift+S"), self, activated=self._save_srt
        )

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    @staticmethod
    def _downloads_dir() -> Path:
        location = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DownloadLocation
        )
        if location:
            return Path(location)
        return Path.home() / "Downloads"

    def _set_status(self, message: str, error: bool = False) -> None:
        self.status_label.setText(message)
        color = "#ff6b6b" if error else "#8f8f8f"
        self.status_label.setStyleSheet(f"color: {color};")

    def _refresh_action_states(self) -> None:
        has_output = bool(self._subtitle_text.strip())
        has_url = bool(self.url_input.text().strip())

        self.copy_btn.setEnabled(not self._busy and has_output)
        self.save_btn.setEnabled(not self._busy and has_output)
        self.download_btn.setEnabled(not self._busy and has_url)
        self.extract_btn.setEnabled(
            not self._busy and self.lang_menu.currentData() is not None
        )

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.url_input.setEnabled(not busy)
        self.analyze_btn.setEnabled(not busy)
        self.lang_menu.setEnabled(not busy)
        self._refresh_action_states()

    def _reset_language_menu(self) -> None:
        self.lang_menu.blockSignals(True)
        self.lang_menu.clear()
        self.lang_menu.addItem(PLACEHOLDER_TEXT, None)
        self.lang_menu.setCurrentIndex(0)
        self.lang_menu.blockSignals(False)
        self.extract_btn.setEnabled(False)

    def _populate_language_menu(
        self, official: dict, automatic: dict
    ) -> int:
        sources: dict[str, str] = {}
        for code in official.keys():
            if code:
                sources[str(code)] = "Official"
        for code in automatic.keys():
            if code and str(code) not in sources:
                sources[str(code)] = "Auto"

        self.lang_menu.blockSignals(True)
        self.lang_menu.clear()

        for code in sorted(sources.keys(), key=str.lower):
            self.lang_menu.addItem(f"{code} [{sources[code]}]", code)

        if self.lang_menu.count() == 0:
            self.lang_menu.addItem(PLACEHOLDER_TEXT, None)

        self.lang_menu.setCurrentIndex(0)
        self.lang_menu.blockSignals(False)

        self._refresh_action_states()
        return len(sources)

    def _on_url_changed(self, _text: str) -> None:
        if self._busy:
            return

        # Any URL edit invalidates the previous analysis.
        self._analyzed_url = ""
        self._reset_language_menu()
        self._refresh_action_states()

        if self.url_input.text().strip():
            self._set_status(
                "URL ready. Click Analyze Video to load subtitle languages."
            )
        else:
            self._set_status("Ready. Paste a YouTube link to begin.")

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------
    def _analyze_video(self) -> None:
        if self._busy:
            return

        url = self.url_input.text().strip()
        if not self._is_valid_url(url):
            self._set_status("Enter a valid http(s) YouTube URL.", error=True)
            QMessageBox.warning(
                self,
                "Invalid URL",
                "Please enter a valid http(s) YouTube URL.",
            )
            self.url_input.setFocus()
            return

        self._reset_language_menu()
        self.lang_menu.blockSignals(True)
        self.lang_menu.clear()
        self.lang_menu.addItem("Analyzing video...", None)
        self.lang_menu.blockSignals(False)

        self._analyzed_url = url
        self._set_busy(True)
        self._set_status("Analyzing video metadata...")
        self.log_view.setPlainText(
            "Analyzing video metadata with yt-dlp...\n"
        )

        worker = AnalyzeWorker(url, self)
        self._analyze_worker = worker
        worker.succeeded.connect(self._on_analysis_succeeded)
        worker.failed.connect(self._on_analysis_failed)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(self._clear_analyze_worker)
        worker.start()

    def _clear_analyze_worker(self) -> None:
        self._analyze_worker = None

    def _on_analysis_succeeded(self, metadata: dict) -> None:
        self._set_busy(False)

        if self.url_input.text().strip() != self._analyzed_url:
            self._reset_language_menu()
            self._set_status(
                "The URL changed during analysis. Analyze it again.",
                error=True,
            )
            return

        title = str(metadata.get("title") or "Untitled video")
        official = metadata.get("subtitles") or {}
        automatic = metadata.get("automatic_captions") or {}

        if not isinstance(official, dict):
            official = {}
        if not isinstance(automatic, dict):
            automatic = {}

        count = self._populate_language_menu(official, automatic)

        if count == 0:
            self.log_view.setPlainText(
                f"Video: {title}\n\n"
                "No subtitle tracks were found for this video."
            )
            self._set_status(
                "No subtitle tracks found for this video.", error=True
            )
            return

        self.log_view.setPlainText(
            f"Video: {title}\n"
            f"Official subtitle tracks: {len(official)}\n"
            f"Automatic caption tracks: {len(automatic)}\n\n"
            f"Found {count} available language track(s).\n"
            'Choose a language, then click "Extract SRT".'
        )
        self._set_status(
            f"Found {count} subtitle track(s). Choose a language and extract."
        )

    def _on_analysis_failed(self, message: str) -> None:
        self._set_busy(False)
        self._analyzed_url = ""
        self._reset_language_menu()
        self._refresh_action_states()
        self.log_view.setPlainText(f"Analysis failed:\n\n{message}")
        self._set_status(
            "Analysis failed. Check the URL and try again.", error=True
        )
        QMessageBox.critical(self, "Analysis Failed", message)

    # ------------------------------------------------------------------
    # Subtitle extraction
    # ------------------------------------------------------------------
    def _extract_srt(self) -> None:
        if self._busy:
            return

        url = self.url_input.text().strip()
        language = self.lang_menu.currentData()

        if not self._is_valid_url(url):
            self._set_status("Enter a valid http(s) YouTube URL.", error=True)
            QMessageBox.warning(
                self,
                "Invalid URL",
                "Please enter a valid http(s) YouTube URL.",
            )
            return

        if not language:
            self._set_status(
                "Analyze a video and select a language first.", error=True
            )
            return

        if url != self._analyzed_url:
            self._reset_language_menu()
            self._set_status(
                "Analyze the current URL before extracting subtitles.",
                error=True,
            )
            return

        language = str(language)
        self._subtitle_text = ""
        self._extracted_language = language
        self._set_busy(True)
        self._set_status(f"Extracting {language} subtitles...")
        self.log_view.setPlainText(
            f"Downloading {language} subtitles and converting to SRT...\n"
        )

        worker = ExtractWorker(url, language, self)
        self._extract_worker = worker
        worker.succeeded.connect(self._on_extract_succeeded)
        worker.failed.connect(self._on_extract_failed)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(self._clear_extract_worker)
        worker.start()

    def _clear_extract_worker(self) -> None:
        self._extract_worker = None

    def _on_extract_succeeded(self, raw_text: str, language: str) -> None:
        self._set_busy(False)
        self._subtitle_text = raw_text
        self._extracted_language = language
        self.log_view.setPlainText(raw_text)
        self.log_view.moveCursor(QTextCursor.MoveOperation.Start)
        self._refresh_action_states()

        line_count = len(raw_text.splitlines())
        self._set_status(
            f"Extracted {language} subtitles successfully "
            f"({line_count} lines)."
        )

    def _on_extract_failed(self, message: str) -> None:
        self._set_busy(False)
        self._subtitle_text = ""
        self.log_view.setPlainText(
            f"Subtitle extraction failed:\n\n{message}"
        )
        self._set_status("Subtitle extraction failed.", error=True)
        self._refresh_action_states()
        QMessageBox.critical(self, "Extraction Failed", message)

    # ------------------------------------------------------------------
    # Output actions
    # ------------------------------------------------------------------
    def _copy_to_clipboard(self) -> None:
        if not self._subtitle_text.strip():
            self._set_status("There is no subtitle text to copy.", error=True)
            return

        try:
            if pyperclip is not None:
                pyperclip.copy(self._subtitle_text)
            else:
                QApplication.clipboard().setText(self._subtitle_text)
        except Exception as exc:  # noqa: BLE001 - clipboard backend errors
            self._set_status(f"Could not copy to clipboard: {exc}", error=True)
            QMessageBox.critical(
                self, "Clipboard Error", f"Could not copy to clipboard:\n{exc}"
            )
            return

        self._set_status(
            f"Copied {len(self._subtitle_text)} characters to the clipboard."
        )

    def _save_srt(self) -> None:
        if not self._subtitle_text.strip():
            self._set_status("There is no subtitle text to save.", error=True)
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        language = (
            self._extracted_language
            or str(self.lang_menu.currentData() or "subs")
        )
        downloads = self._downloads_dir()
        try:
            downloads.mkdir(parents=True, exist_ok=True)
        except OSError:
            downloads = Path.home()

        default_path = downloads / f"subtitles_{language}_{timestamp}.srt"
        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Subtitle File",
            str(default_path),
            "SubRip Subtitle (*.srt);;All Files (*)",
        )

        if not selected_path:
            return

        target = Path(selected_path)
        if target.suffix.lower() != ".srt":
            target = Path(f"{target}.srt")

        try:
            target.write_text(self._subtitle_text, encoding="utf-8")
        except OSError as exc:
            self._set_status(f"Could not save the file: {exc}", error=True)
            QMessageBox.critical(
                self, "Save Error", f"Could not save the file:\n{exc}"
            )
            return

        self._set_status(f"Saved subtitle file to {target}.")

    def _download_video(self) -> None:
        if self._busy:
            return

        url = self.url_input.text().strip()
        if not self._is_valid_url(url):
            self._set_status("Enter a valid http(s) YouTube URL.", error=True)
            QMessageBox.warning(
                self,
                "Invalid URL",
                "Please enter a valid http(s) YouTube URL.",
            )
            return

        downloads = self._downloads_dir()
        try:
            downloads.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self._set_status(
                f"Could not create the Downloads folder: {exc}", error=True
            )
            QMessageBox.critical(
                self,
                "Download Error",
                f"Could not create the Downloads folder:\n{exc}",
            )
            return

        self._set_busy(True)
        self._set_status("Downloading video only...")
        if not self._subtitle_text.strip():
            self.log_view.setPlainText(
                "Downloading the video-only stream with yt-dlp...\n"
            )

        worker = DownloadWorker(url, str(downloads), self)
        self._download_worker = worker
        worker.succeeded.connect(self._on_download_succeeded)
        worker.failed.connect(self._on_download_failed)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(self._clear_download_worker)
        worker.start()

    def _clear_download_worker(self) -> None:
        self._download_worker = None

    def _on_download_succeeded(self, path: str) -> None:
        self._set_busy(False)
        self._last_download_path = Path(path)
        if not self._subtitle_text.strip():
            self.log_view.setPlainText(
                f"Video downloaded successfully:\n{path}"
            )
        self._set_status(f"Video saved to {path}.")
        self._show_download_complete(path)

    def _on_download_failed(self, message: str) -> None:
        self._set_busy(False)
        if not self._subtitle_text.strip():
            self.log_view.setPlainText(
                f"Video download failed:\n\n{message}"
            )
        self._set_status("Video download failed.", error=True)
        QMessageBox.critical(self, "Download Failed", message)

    def _show_download_complete(self, path: str) -> None:
        box = QMessageBox(self)
        box.setWindowTitle("Download Complete")
        box.setText(f"Video saved to:\n{path}")
        open_button = box.addButton(
            "Show in Folder", QMessageBox.ButtonRole.ActionRole
        )
        box.addButton(QMessageBox.StandardButton.Ok)
        box.exec()

        if box.clickedButton() is open_button:
            self._reveal_path(Path(path))

    def _reveal_path(self, path: Path) -> None:
        if path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))
        else:
            self._open_downloads_folder()

    def _open_downloads_folder(self) -> None:
        downloads = self._downloads_dir()
        try:
            downloads.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self._set_status(
                f"Could not open Downloads: {exc}", error=True
            )
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(downloads)))

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<b>{APP_NAME}</b><br>"
            f"Version {__version__}<br><br>"
            "Download official and auto-generated YouTube subtitles "
            "as SRT files.<br><br>"
            "Licensed under AGPL-3.0-or-later.",
        )

    # ------------------------------------------------------------------
    # Window lifecycle
    # ------------------------------------------------------------------
    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API name
        active = [
            worker
            for worker in (
                self._analyze_worker,
                self._extract_worker,
                self._download_worker,
            )
            if worker is not None and worker.isRunning()
        ]

        if active:
            answer = QMessageBox.question(
                self,
                "Task In Progress",
                "A background task is still running. "
                "Quit and stop it?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

            for worker in active:
                worker.requestInterruption()
                worker.terminate()
                worker.wait(1500)

        event.accept()
