"""DiffViewer – side-by-side or unified diff of original vs AI-edited text."""
import difflib

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor, QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QPlainTextEdit, QLabel, QSplitter, QWidget
)


class DiffViewer(QDialog):
    def __init__(self, original: str, revised: str, parent=None):
        super().__init__(parent)
        self.original = original
        self.revised = revised
        self.accepted_text: str | None = None
        self.setWindowTitle("AI Edit – Review Changes")
        self.resize(900, 600)
        self._build_ui()
        self._populate()

    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.addWidget(QLabel("Original"))
        self.left_edit = QPlainTextEdit()
        self.left_edit.setReadOnly(True)
        self.left_edit.setFont(QFont("Courier New", 10))
        ll.addWidget(self.left_edit)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.addWidget(QLabel("Revised"))
        self.right_edit = QPlainTextEdit()
        self.right_edit.setReadOnly(True)
        self.right_edit.setFont(QFont("Courier New", 10))
        rl.addWidget(self.right_edit)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([450, 450])
        layout.addWidget(splitter)

        btn_row = QHBoxLayout()
        accept_btn = QPushButton("✔ Accept Changes")
        accept_btn.clicked.connect(self._accept)
        reject_btn = QPushButton("✘ Reject (Keep Original)")
        reject_btn.clicked.connect(self.reject)
        btn_row.addWidget(accept_btn)
        btn_row.addWidget(reject_btn)
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    def _populate(self):
        orig_lines = self.original.splitlines(keepends=True)
        rev_lines = self.revised.splitlines(keepends=True)

        add_fmt = QTextCharFormat()
        add_fmt.setBackground(QColor("#c8f7c5"))
        del_fmt = QTextCharFormat()
        del_fmt.setBackground(QColor("#fac5c5"))

        matcher = difflib.SequenceMatcher(None, orig_lines, rev_lines, autojunk=False)
        left_text = []
        right_text = []
        left_highlights = []   # (start_line, end_line, format)
        right_highlights = []

        left_line = 0
        right_line = 0

        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op == 'equal':
                for line in orig_lines[i1:i2]:
                    left_text.append(line)
                    right_text.append(line)
                left_line += (i2 - i1)
                right_line += (j2 - j1)
            elif op == 'replace':
                for line in orig_lines[i1:i2]:
                    left_text.append(line)
                for line in rev_lines[j1:j2]:
                    right_text.append(line)
                left_highlights.append((left_line, left_line + (i2 - i1), del_fmt))
                right_highlights.append((right_line, right_line + (j2 - j1), add_fmt))
                left_line += (i2 - i1)
                right_line += (j2 - j1)
            elif op == 'delete':
                for line in orig_lines[i1:i2]:
                    left_text.append(line)
                left_highlights.append((left_line, left_line + (i2 - i1), del_fmt))
                left_line += (i2 - i1)
            elif op == 'insert':
                for line in rev_lines[j1:j2]:
                    right_text.append(line)
                right_highlights.append((right_line, right_line + (j2 - j1), add_fmt))
                right_line += (j2 - j1)

        self.left_edit.setPlainText(''.join(left_text))
        self.right_edit.setPlainText(''.join(right_text))

        self._apply_line_highlights(self.left_edit, left_highlights)
        self._apply_line_highlights(self.right_edit, right_highlights)

    @staticmethod
    def _apply_line_highlights(widget: QPlainTextEdit, highlights):
        doc = widget.document()
        for start_line, end_line, fmt in highlights:
            for ln in range(start_line, end_line):
                block = doc.findBlockByLineNumber(ln)
                if not block.isValid():
                    continue
                cursor = QTextCursor(block)
                cursor.select(QTextCursor.SelectionType.LineUnderCursor)
                cursor.setCharFormat(fmt)

    # ------------------------------------------------------------------
    def _accept(self):
        self.accepted_text = self.revised
        self.accept()
