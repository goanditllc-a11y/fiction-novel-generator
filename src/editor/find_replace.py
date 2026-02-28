"""Find & Replace dialog."""
import re

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor
from PyQt6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton,
    QCheckBox, QGridLayout, QHBoxLayout, QVBoxLayout,
    QMessageBox
)


class FindReplaceDialog(QDialog):
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.setWindowTitle("Find & Replace")
        self.setMinimumWidth(450)
        self._last_found_cursor: QTextCursor | None = None
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QGridLayout(self)

        layout.addWidget(QLabel("Find:"), 0, 0)
        self.find_edit = QLineEdit()
        self.find_edit.returnPressed.connect(self.find_next)
        layout.addWidget(self.find_edit, 0, 1)

        layout.addWidget(QLabel("Replace:"), 1, 0)
        self.replace_edit = QLineEdit()
        layout.addWidget(self.replace_edit, 1, 1)

        opts = QHBoxLayout()
        self.case_cb = QCheckBox("Case sensitive")
        self.word_cb = QCheckBox("Whole word")
        self.regex_cb = QCheckBox("Regex")
        opts.addWidget(self.case_cb)
        opts.addWidget(self.word_cb)
        opts.addWidget(self.regex_cb)
        layout.addLayout(opts, 2, 0, 1, 2)

        btn_layout = QHBoxLayout()
        for text, slot in [
            ("Find Next", self.find_next),
            ("Find All", self.find_all),
            ("Replace", self.replace_one),
            ("Replace All", self.replace_all),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout, 3, 0, 1, 2)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label, 4, 0, 1, 2)

    # ------------------------------------------------------------------
    def _build_pattern(self) -> re.Pattern | None:
        term = self.find_edit.text()
        if not term:
            return None
        flags = 0 if self.case_cb.isChecked() else re.IGNORECASE
        if self.regex_cb.isChecked():
            try:
                pat = re.compile(term, flags)
            except re.error as e:
                self.status_label.setText(f"Regex error: {e}")
                return None
        else:
            escaped = re.escape(term)
            if self.word_cb.isChecked():
                escaped = rf'\b{escaped}\b'
            pat = re.compile(escaped, flags)
        return pat

    # ------------------------------------------------------------------
    def _highlight_all(self, matches):
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#FFDD57"))
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        for m in matches:
            c = QTextCursor(self.editor.document())
            c.setPosition(m.start())
            c.setPosition(m.end(), QTextCursor.MoveMode.KeepAnchor)
            c.setCharFormat(fmt)
        cursor.endEditBlock()

    # ------------------------------------------------------------------
    def find_next(self):
        pat = self._build_pattern()
        if pat is None:
            return
        text = self.editor.toPlainText()
        start = self.editor.textCursor().position()
        m = pat.search(text, start)
        if m is None:
            m = pat.search(text)  # wrap around
        if m:
            c = self.editor.textCursor()
            c.setPosition(m.start())
            c.setPosition(m.end(), QTextCursor.MoveMode.KeepAnchor)
            self.editor.setTextCursor(c)
            self._last_found_cursor = c
            self.status_label.setText("")
        else:
            self.status_label.setText("Not found.")

    def find_all(self):
        pat = self._build_pattern()
        if pat is None:
            return
        matches = list(pat.finditer(self.editor.toPlainText()))
        self._highlight_all(matches)
        self.status_label.setText(f"{len(matches)} match(es) highlighted.")

    def replace_one(self):
        c = self.editor.textCursor()
        if c.hasSelection():
            pat = self._build_pattern()
            if pat and pat.fullmatch(c.selectedText()):
                c.insertText(self.replace_edit.text())
        self.find_next()

    def replace_all(self):
        pat = self._build_pattern()
        if pat is None:
            return
        text = self.editor.toPlainText()
        new_text, count = pat.subn(self.replace_edit.text(), text)
        if count:
            c = self.editor.textCursor()
            c.beginEditBlock()
            c.select(QTextCursor.SelectionType.Document)
            c.insertText(new_text)
            c.endEditBlock()
        self.status_label.setText(f"Replaced {count} occurrence(s).")
