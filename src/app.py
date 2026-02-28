"""MainWindow – the Fiction Novel Editor application window."""
import os
import sys

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import (
    QAction, QFont, QKeySequence, QIcon, QDragEnterEvent, QDropEvent,
    QTextCursor, QColor
)
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QFileDialog, QMessageBox,
    QStatusBar, QToolBar, QLabel, QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QCheckBox, QProgressBar, QTextEdit, QApplication,
    QMenu
)

from src.editor.text_editor import NovelTextEditor
from src.editor.chapter_navigator import ChapterNavigator
from src.editor.find_replace import FindReplaceDialog
from src.editor.stats import TextStats
from src.file_io.file_handler import FileHandler, UnsupportedFormatError
from src.file_io.autosave import AutoSave
from src.utils.config import Config
from src.utils.constants import (
    APP_NAME, APP_VERSION, SUPPORTED_EXTENSIONS,
    MAX_RECENT_FILES
)

# ── Stylesheets ──────────────────────────────────────────────────────────────
DARK_STYLE = """
QMainWindow, QWidget { background-color: #1e1e1e; color: #d4d4d4; }
QPlainTextEdit, QTextEdit { background-color: #252526; color: #d4d4d4;
    border: 1px solid #3c3c3c; selection-background-color: #264f78; }
QMenuBar { background-color: #323233; color: #cccccc; }
QMenuBar::item:selected { background-color: #094771; }
QMenu { background-color: #252526; color: #cccccc; border: 1px solid #454545; }
QMenu::item:selected { background-color: #094771; }
QToolBar { background-color: #2d2d2d; border-bottom: 1px solid #3c3c3c; }
QStatusBar { background-color: #007acc; color: white; }
QListWidget { background-color: #252526; color: #d4d4d4; border: 1px solid #3c3c3c; }
QListWidget::item:selected { background-color: #094771; }
QPushButton { background-color: #0e639c; color: white; border: none;
    padding: 5px 12px; border-radius: 3px; }
QPushButton:hover { background-color: #1177bb; }
QPushButton:pressed { background-color: #0a4f80; }
QLineEdit, QComboBox { background-color: #3c3c3c; color: #d4d4d4;
    border: 1px solid #555; padding: 3px; }
QCheckBox { color: #d4d4d4; }
QProgressBar { border: 1px solid #555; background-color: #3c3c3c; color: white; }
QProgressBar::chunk { background-color: #007acc; }
QLabel { color: #d4d4d4; }
QSplitter::handle { background-color: #3c3c3c; }
"""

LIGHT_STYLE = """
QMainWindow, QWidget { background-color: #f3f3f3; color: #1e1e1e; }
QPlainTextEdit, QTextEdit { background-color: white; color: #1e1e1e;
    border: 1px solid #c8c8c8; selection-background-color: #add6ff; }
QMenuBar { background-color: #dddddd; }
QMenu { background-color: #f0f0f0; border: 1px solid #c8c8c8; }
QToolBar { background-color: #e8e8e8; border-bottom: 1px solid #c8c8c8; }
QStatusBar { background-color: #007acc; color: white; }
QListWidget { background-color: white; border: 1px solid #c8c8c8; }
QPushButton { background-color: #0078d4; color: white; border: none;
    padding: 5px 12px; border-radius: 3px; }
QPushButton:hover { background-color: #106ebe; }
QProgressBar::chunk { background-color: #0078d4; }
QSplitter::handle { background-color: #c8c8c8; }
"""


# ── De-AI Dialog ─────────────────────────────────────────────────────────────
class DeAIDialog(QDialog):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.original_text = text
        self.result_text: str | None = None
        self.setWindowTitle("De-AI / Humanize Document")
        self.resize(700, 550)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Score banner
        self.score_label = QLabel("AI Score: —")
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.score_label.font()
        font.setPointSize(16)
        font.setBold(True)
        self.score_label.setFont(font)
        layout.addWidget(self.score_label)

        # Options
        opts_layout = QHBoxLayout()
        self.cb_replace   = QCheckBox("Replace AI phrases"); self.cb_replace.setChecked(True)
        self.cb_contract  = QCheckBox("Add contractions");  self.cb_contract.setChecked(True)
        self.cb_vary_open = QCheckBox("Vary openings");     self.cb_vary_open.setChecked(True)
        self.cb_vary_len  = QCheckBox("Vary sentence length")
        for cb in (self.cb_replace, self.cb_contract, self.cb_vary_open, self.cb_vary_len):
            opts_layout.addWidget(cb)
        layout.addLayout(opts_layout)

        # Buttons row
        btn_row = QHBoxLayout()
        self.analyze_btn = QPushButton("▶ Run Analysis")
        self.analyze_btn.clicked.connect(self._run)
        self.apply_btn = QPushButton("✔ Apply Changes")
        self.apply_btn.clicked.connect(self._apply)
        self.apply_btn.setEnabled(False)
        cancel_btn = QPushButton("✘ Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.analyze_btn)
        btn_row.addWidget(self.apply_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.report_view = QTextEdit()
        self.report_view.setReadOnly(True)
        layout.addWidget(self.report_view)

    def _run(self):
        from src.deai.batch_processor import BatchProcessor
        from src.deai.detector import AIDetector

        options = {
            "detect_phrases":         True,
            "replace_phrases":        self.cb_replace.isChecked(),
            "add_contractions":       self.cb_contract.isChecked(),
            "vary_sentence_openings": self.cb_vary_open.isChecked(),
            "vary_sentence_length":   self.cb_vary_len.isChecked(),
        }

        self.analyze_btn.setEnabled(False)
        self.progress.setRange(0, 0)
        self.progress.setVisible(True)

        try:
            processor = BatchProcessor()
            cleaned, report = processor.process_document(
                self.original_text, options,
                progress_callback=lambda s, t, m: self.report_view.append(m)
            )
            self.result_text = cleaned
            report_str = processor.generate_report(report)
            self.report_view.setPlainText(report_str)
            score_pct = int(report.get("final_score", 0) * 100)
            self.score_label.setText(f"AI Score: {score_pct}%")
            self.apply_btn.setEnabled(True)
        except Exception as exc:
            self.report_view.setPlainText(f"Error: {exc}")
        finally:
            self.progress.setVisible(False)
            self.analyze_btn.setEnabled(True)

    def _apply(self):
        self.accept()


# ── MainWindow ────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._config = Config()
        self._file_handler = FileHandler()
        self._stats = TextStats()
        self._current_file: str | None = None
        self._modified = False

        self.setWindowTitle(APP_NAME)
        self.resize(1280, 800)
        self.setAcceptDrops(True)

        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._build_status_bar()
        self._setup_autosave()
        self._apply_theme(self._config.theme)
        self._restore_geometry()
        self._refresh_recent_menu()

    # ── UI construction ──────────────────────────────────────────────────────
    def _build_ui(self):
        self._splitter = QSplitter(Qt.Orientation.Horizontal)

        self._chapter_nav = ChapterNavigator(parent=self)
        self._chapter_nav.setMinimumWidth(150)
        self._chapter_nav.setMaximumWidth(300)

        self._editor = NovelTextEditor(self)
        self._editor.set_font_size(self._config.font_size)
        self._editor.set_font_family(self._config.font_family)
        self._editor.document().contentsChanged.connect(self._on_text_changed)

        self._chapter_nav.chapter_selected.connect(self._navigate_to_chapter)

        self._splitter.addWidget(self._chapter_nav)
        self._splitter.addWidget(self._editor)
        self._splitter.setSizes([200, 1080])
        self.setCentralWidget(self._splitter)

        if self._config.get("splitter_sizes"):
            self._splitter.setSizes(self._config.get("splitter_sizes"))

    # ── Menu ─────────────────────────────────────────────────────────────────
    def _build_menu(self):
        mb = self.menuBar()

        # File
        file_menu = mb.addMenu("&File")
        self._add_action(file_menu, "&New",          self._new_file,     "Ctrl+N")
        self._add_action(file_menu, "&Open…",        self._open_file,    "Ctrl+O")
        self._add_action(file_menu, "&Save",         self._save_file,    "Ctrl+S")
        self._add_action(file_menu, "Save &As…",     self._save_as,      "Ctrl+Shift+S")
        file_menu.addSeparator()
        self._recent_menu = file_menu.addMenu("Recent Files")
        file_menu.addSeparator()
        self._add_action(file_menu, "E&xit",         self.close,         "Alt+F4")

        # Edit
        edit_menu = mb.addMenu("&Edit")
        self._add_action(edit_menu, "&Undo",         self._editor.undo,  "Ctrl+Z")
        self._add_action(edit_menu, "&Redo",         self._editor.redo,  "Ctrl+Y")
        edit_menu.addSeparator()
        self._add_action(edit_menu, "Cu&t",          self._editor.cut,   "Ctrl+X")
        self._add_action(edit_menu, "&Copy",         self._editor.copy,  "Ctrl+C")
        self._add_action(edit_menu, "&Paste",        self._editor.paste, "Ctrl+V")
        edit_menu.addSeparator()
        self._add_action(edit_menu, "&Find & Replace…", self._show_find_replace, "Ctrl+F")

        # View
        view_menu = mb.addMenu("&View")
        self._add_action(view_menu, "Toggle &Chapter Panel", self._toggle_chapter_panel, "Ctrl+\\")
        view_menu.addSeparator()
        self._add_action(view_menu, "&Dark Theme",  lambda: self._apply_theme("dark"))
        self._add_action(view_menu, "&Light Theme", lambda: self._apply_theme("light"))
        view_menu.addSeparator()
        self._add_action(view_menu, "Zoom &In",     self._editor.increase_font_size, "Ctrl+=")
        self._add_action(view_menu, "Zoom &Out",    self._editor.decrease_font_size, "Ctrl+-")

        # Tools
        tools_menu = mb.addMenu("&Tools")
        self._add_action(tools_menu, "AI &Prompt Editor…", self._show_prompt_editor, "Ctrl+Alt+A")
        deai_menu = tools_menu.addMenu("&De-AI / Humanize")
        self._add_action(deai_menu, "Run &Full Analysis",  self._run_deai_full)
        self._add_action(deai_menu, "Detect AI &Patterns", self._detect_ai_patterns)
        self._add_action(deai_menu, "&Clean Phrases",      self._clean_phrases)
        self._add_action(deai_menu, "&Batch Process",      self._run_deai_full)
        self._add_action(deai_menu, "&Metadata Cleaner…",  self._clean_metadata)
        tools_menu.addSeparator()
        self._add_action(tools_menu, "&Word Count",        self._show_word_count)

        # Help
        help_menu = mb.addMenu("&Help")
        self._add_action(help_menu, "&About", self._show_about)

    @staticmethod
    def _add_action(menu: QMenu, label: str, slot, shortcut: str = None) -> QAction:
        action = QAction(label, menu)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    # ── Toolbar ──────────────────────────────────────────────────────────────
    def _build_toolbar(self):
        tb = QToolBar("Main Toolbar", self)
        tb.setIconSize(QSize(20, 20))
        self.addToolBar(tb)

        for label, slot, shortcut in [
            ("New",      self._new_file,            "Ctrl+N"),
            ("Open",     self._open_file,           "Ctrl+O"),
            ("Save",     self._save_file,           "Ctrl+S"),
            ("|",        None,                      None),
            ("Undo",     self._editor.undo,         "Ctrl+Z"),
            ("Redo",     self._editor.redo,         "Ctrl+Y"),
            ("|",        None,                      None),
            ("Find",     self._show_find_replace,   "Ctrl+F"),
            ("|",        None,                      None),
        ]:
            if label == "|":
                tb.addSeparator()
            else:
                act = QAction(label, self)
                if shortcut:
                    act.setShortcut(QKeySequence(shortcut))
                act.triggered.connect(slot)
                tb.addAction(act)

        # Prominent De-AI button
        deai_btn = QPushButton("🤖 De-AI")
        deai_btn.setToolTip("Detect and clean AI-generated patterns")
        deai_btn.setAccessibleName("De-AI")
        deai_btn.setAccessibleDescription("Detect and clean AI-generated patterns")
        deai_btn.clicked.connect(self._run_deai_full)
        tb.addWidget(deai_btn)

    # ── Status bar ───────────────────────────────────────────────────────────
    def _build_status_bar(self):
        sb = self.statusBar()
        self._stats_label = QLabel("Words: 0  |  Characters: 0  |  Pages: 0.0")
        self._autosave_label = QLabel("Autosave: —")
        sb.addWidget(self._stats_label)
        sb.addPermanentWidget(self._autosave_label)

    def _update_status_bar(self):
        text = self._editor.toPlainText()
        self._stats_label.setText(self._stats.get_stats_string(text))

    # ── AutoSave ─────────────────────────────────────────────────────────────
    def _setup_autosave(self):
        self._autosave = AutoSave(
            get_content_callback=self._editor.toPlainText,
            parent=self,
        )
        self._autosave.saved.connect(
            lambda path: self._autosave_label.setText(
                f"Autosaved: {os.path.basename(path)}"
            )
        )
        self._autosave.set_interval(self._config.autosave_interval)
        self._autosave.set_enabled(self._config.autosave_enabled)

    # ── Text changed ─────────────────────────────────────────────────────────
    def _on_text_changed(self):
        self._modified = True
        self._update_status_bar()
        # Refresh chapter list every 2 seconds (debounce)
        if not hasattr(self, '_chapter_timer'):
            self._chapter_timer = QTimer(self)
            self._chapter_timer.setSingleShot(True)
            self._chapter_timer.timeout.connect(
                lambda: self._chapter_nav.refresh(self._editor.toPlainText())
            )
        self._chapter_timer.start(2000)
        self._update_title()

    def _update_title(self):
        base = os.path.basename(self._current_file) if self._current_file else "Untitled"
        mod = " *" if self._modified else ""
        self.setWindowTitle(f"{base}{mod} — {APP_NAME}")

    # ── Navigation ───────────────────────────────────────────────────────────
    def _navigate_to_chapter(self, pos: int):
        cursor = self._editor.textCursor()
        cursor.setPosition(pos)
        self._editor.setTextCursor(cursor)
        self._editor.ensureCursorVisible()
        self._editor.setFocus()

    # ── File actions ─────────────────────────────────────────────────────────
    def _check_unsaved(self) -> bool:
        """Return True if safe to proceed (discard or save changes)."""
        if not self._modified:
            return True
        reply = QMessageBox.question(
            self, "Unsaved Changes",
            "You have unsaved changes. Save before continuing?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Save:
            return self._save_file()
        return reply == QMessageBox.StandardButton.Discard

    def _new_file(self):
        if not self._check_unsaved():
            return
        self._editor.clear()
        self._current_file = None
        self._modified = False
        self._autosave.set_filename("")
        self._update_title()
        self._chapter_nav.refresh("")

    def _open_file(self, path: str = None):
        if not self._check_unsaved():
            return
        if not path:
            exts = " ".join(f"*{e}" for e in SUPPORTED_EXTENSIONS)
            path, _ = QFileDialog.getOpenFileName(
                self, "Open File", "",
                f"Novel Files ({exts});;All Files (*)"
            )
        if not path:
            return
        try:
            content = self._file_handler.load_file(path)
            self._editor.setPlainText(content)
            self._current_file = path
            self._modified = False
            self._autosave.set_filename(path)
            self._config.add_recent_file(path)
            self._refresh_recent_menu()
            self._update_title()
            self._chapter_nav.refresh(content)
        except (UnsupportedFormatError, OSError, Exception) as exc:
            QMessageBox.critical(self, "Open Error", str(exc))

    def _save_file(self) -> bool:
        if not self._current_file:
            return self._save_as()
        try:
            self._file_handler.save_file(self._current_file, self._editor.toPlainText())
            self._modified = False
            self._update_title()
            return True
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", str(exc))
            return False

    def _save_as(self) -> bool:
        exts = " ".join(f"*{e}" for e in SUPPORTED_EXTENSIONS)
        path, _ = QFileDialog.getSaveFileName(
            self, "Save As", "",
            f"Novel Files ({exts});;All Files (*)"
        )
        if not path:
            return False
        self._current_file = path
        return self._save_file()

    # ── Recent files ─────────────────────────────────────────────────────────
    def _refresh_recent_menu(self):
        self._recent_menu.clear()
        for path in self._config.recent_files:
            action = QAction(os.path.basename(path), self)
            action.setData(path)
            action.triggered.connect(lambda checked, p=path: self._open_file(p))
            self._recent_menu.addAction(action)
        if not self._config.recent_files:
            self._recent_menu.addAction("(empty)").setEnabled(False)

    # ── Find & Replace ───────────────────────────────────────────────────────
    def _show_find_replace(self):
        dlg = FindReplaceDialog(self._editor, self)
        dlg.show()

    # ── Chapter panel toggle ─────────────────────────────────────────────────
    def _toggle_chapter_panel(self):
        visible = self._chapter_nav.isVisible()
        self._chapter_nav.setVisible(not visible)
        self._config.set("chapter_panel_visible", not visible)

    # ── Theme ────────────────────────────────────────────────────────────────
    def _apply_theme(self, theme: str):
        self._config.theme = theme
        QApplication.instance().setStyleSheet(
            DARK_STYLE if theme == "dark" else LIGHT_STYLE
        )

    # ── AI Prompt Editor ─────────────────────────────────────────────────────
    def _show_prompt_editor(self):
        from src.ai_editor.prompt_editor import PromptEditor
        cursor = self._editor.textCursor()
        selected = cursor.selectedText() or self._editor.toPlainText()[:2000]
        dlg = PromptEditor(selected, parent=self)
        dlg.text_accepted.connect(self._apply_ai_edit)
        dlg.exec()

    def _apply_ai_edit(self, original: str, revised: str):
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(revised)
        else:
            self._editor.setPlainText(revised)
        self._modified = True

    # ── De-AI actions ────────────────────────────────────────────────────────
    def _run_deai_full(self):
        text = self._editor.toPlainText()
        if not text.strip():
            QMessageBox.information(self, "De-AI", "Document is empty.")
            return
        dlg = DeAIDialog(text, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result_text:
            self._editor.setPlainText(dlg.result_text)
            self._modified = True

    def _detect_ai_patterns(self):
        from src.deai.detector import AIDetector
        text = self._editor.toPlainText()
        if not text.strip():
            return
        detector = AIDetector()
        score = detector.score_text(text)
        ranges = detector.highlight_ai_patterns(text)
        self._editor.clear_highlights()
        self._editor.highlight_ranges([(s, e) for s, e in ranges], color="#FFDD57")
        QMessageBox.information(
            self, "AI Detection",
            f"AI Score: {score:.1%}\n{len(ranges)} pattern(s) highlighted."
        )

    def _clean_phrases(self):
        from src.deai.phrase_cleaner import PhraseCleaner
        text = self._editor.toPlainText()
        cleaned = PhraseCleaner().replace_ai_phrases(text)
        if cleaned != text:
            self._editor.setPlainText(cleaned)
            self._modified = True
            QMessageBox.information(self, "Phrase Cleaner", "AI phrases replaced.")
        else:
            QMessageBox.information(self, "Phrase Cleaner", "No AI phrases found.")

    def _clean_metadata(self):
        if not self._current_file or not self._current_file.endswith('.docx'):
            QMessageBox.warning(self, "Metadata Cleaner",
                                "Metadata cleaning is only available for saved .docx files.")
            return
        from src.deai.metadata_cleaner import MetadataCleaner
        try:
            changed = MetadataCleaner().clean_docx_metadata(self._current_file)
            if changed:
                QMessageBox.information(self, "Metadata Cleaner",
                                        f"Cleaned fields: {', '.join(changed)}")
            else:
                QMessageBox.information(self, "Metadata Cleaner",
                                        "No AI metadata found.")
        except Exception as exc:
            QMessageBox.critical(self, "Metadata Cleaner", str(exc))

    # ── Word count dialog ────────────────────────────────────────────────────
    def _show_word_count(self):
        text = self._editor.toPlainText()
        msg = self._stats.get_stats_string(text)
        QMessageBox.information(self, "Word Count", msg)

    # ── About ────────────────────────────────────────────────────────────────
    def _show_about(self):
        QMessageBox.about(
            self, f"About {APP_NAME}",
            f"<b>{APP_NAME}</b> v{APP_VERSION}<br><br>"
            "A full-featured fiction novel editor with AI editing and De-AI tools."
        )

    # ── Drag & drop ──────────────────────────────────────────────────────────
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if any(path.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                self._open_file(path)
                break

    # ── Close ────────────────────────────────────────────────────────────────
    def closeEvent(self, event):
        if not self._check_unsaved():
            event.ignore()
            return
        self._save_geometry()
        self._autosave.set_enabled(False)
        event.accept()

    # ── Geometry persistence ─────────────────────────────────────────────────
    def _save_geometry(self):
        self._config.set("window_geometry", {
            "x": self.x(), "y": self.y(),
            "w": self.width(), "h": self.height(),
        })
        self._config.set("splitter_sizes", self._splitter.sizes())

    def _restore_geometry(self):
        geom = self._config.get("window_geometry")
        if geom:
            self.setGeometry(geom["x"], geom["y"], geom["w"], geom["h"])
