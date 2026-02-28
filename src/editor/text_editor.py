"""NovelTextEditor – QPlainTextEdit subclass optimised for large documents."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QFont, QTextCharFormat, QColor, QTextCursor,
    QAction
)
from PyQt6.QtWidgets import QPlainTextEdit, QMenu


class NovelTextEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._font_size = 12
        self._font_family = "Segoe UI"
        self._apply_font()
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        # Large-document optimisations
        self.document().setMaximumBlockCount(0)  # unlimited

    # ------------------------------------------------------------------
    def _apply_font(self):
        f = QFont(self._font_family, self._font_size)
        self.setFont(f)
        self.document().setDefaultFont(f)

    # ------------------------------------------------------------------
    def set_font_size(self, size: int):
        self._font_size = max(6, min(size, 72))
        self._apply_font()

    def increase_font_size(self):
        self.set_font_size(self._font_size + 1)

    def decrease_font_size(self):
        self.set_font_size(self._font_size - 1)

    def set_font_family(self, family: str):
        self._font_family = family
        self._apply_font()

    # ------------------------------------------------------------------
    def set_line_spacing(self, factor: float):
        """Set line spacing via block format (1.0 = normal, 1.5 = 1.5× etc.)"""
        from PyQt6.QtGui import QTextBlockFormat
        fmt = QTextBlockFormat()
        fmt.setLineHeight(factor * 100, 1)  # 1 = ProportionalHeight
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.mergeBlockFormat(fmt)
        cursor.endEditBlock()

    # ------------------------------------------------------------------
    def highlight_ranges(self, ranges, color: str = "#FFDD57"):
        """Highlight list of (start, end) character ranges."""
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(color))
        for start, end in ranges:
            cursor = QTextCursor(self.document())
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            cursor.setCharFormat(fmt)

    def clear_highlights(self):
        """Remove all extra character formatting."""
        fmt = QTextCharFormat()
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.setCharFormat(fmt)
        cursor.endEditBlock()

    # ------------------------------------------------------------------
    def contextMenuEvent(self, event):
        menu: QMenu = self.createStandardContextMenu()
        menu.addSeparator()
        zoom_in = QAction("Zoom In", self)
        zoom_in.triggered.connect(self.increase_font_size)
        zoom_out = QAction("Zoom Out", self)
        zoom_out.triggered.connect(self.decrease_font_size)
        menu.addAction(zoom_in)
        menu.addAction(zoom_out)
        menu.exec(event.globalPos())

    # ------------------------------------------------------------------
    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.increase_font_size()
            elif delta < 0:
                self.decrease_font_size()
        else:
            super().wheelEvent(event)
