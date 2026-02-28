"""Chapter navigator – detects and lists chapter headings."""
import re
from typing import List, Tuple

try:
    from PyQt6.QtCore import pyqtSignal
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
    _QT_AVAILABLE = True
except ImportError:
    _QT_AVAILABLE = False


# -----------------------------------------------------------------------
# Pure-logic helper (importable without Qt for testing)
# -----------------------------------------------------------------------
CHAPTER_PATTERNS = [
    re.compile(r'^\s*(chapter\s+\d+)', re.IGNORECASE | re.MULTILINE),
    re.compile(r'^\s*(chapter\s+(one|two|three|four|five|six|seven|eight|nine|ten'
               r'|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen'
               r'|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy'
               r'|eighty|ninety|hundred))', re.IGNORECASE | re.MULTILINE),
    re.compile(r'^\s*(part\s+(i{1,3}|iv|vi{0,3}|ix|x{1,3}))\b', re.IGNORECASE | re.MULTILINE),
    re.compile(r'^\s*(part\s+(one|two|three|four|five|six|seven|eight|nine|ten))',
               re.IGNORECASE | re.MULTILINE),
    re.compile(r'^\s*(prologue|epilogue|foreword|afterword|introduction|conclusion)',
               re.IGNORECASE | re.MULTILINE),
]


def detect_chapters(text: str) -> List[Tuple[int, str]]:
    """Return list of (char_position, heading_text) sorted by position."""
    results = []
    seen_positions = set()
    for pat in CHAPTER_PATTERNS:
        for m in pat.finditer(text):
            pos = m.start()
            if pos not in seen_positions:
                seen_positions.add(pos)
                results.append((pos, m.group(0).strip()))
    results.sort(key=lambda x: x[0])
    return results


# -----------------------------------------------------------------------
if _QT_AVAILABLE:
    class ChapterNavigator(QWidget):
        chapter_selected = pyqtSignal(int)  # emits char position

        def __init__(self, editor=None, parent=None):
            super().__init__(parent)
            self.editor = editor
            self._chapters: List[Tuple[int, str]] = []
            self._build_ui()

        def _build_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(4, 4, 4, 4)
            layout.addWidget(QLabel("Chapters"))
            self.list_widget = QListWidget()
            self.list_widget.itemClicked.connect(self._on_item_clicked)
            layout.addWidget(self.list_widget)

        def refresh(self, text: str):
            self._chapters = detect_chapters(text)
            self.list_widget.clear()
            for _pos, heading in self._chapters:
                self.list_widget.addItem(QListWidgetItem(heading))

        def _on_item_clicked(self, item: QListWidgetItem):
            row = self.list_widget.row(item)
            if 0 <= row < len(self._chapters):
                pos, _ = self._chapters[row]
                self.chapter_selected.emit(pos)
                if self.editor:
                    cursor = self.editor.textCursor()
                    cursor.setPosition(pos)
                    self.editor.setTextCursor(cursor)
                    self.editor.ensureCursorVisible()
else:
    class ChapterNavigator:  # type: ignore[no-redef]
        """Stub used when PyQt6 is not available."""
        def __init__(self, editor=None, parent=None):
            self.editor = editor
            self._chapters: List[Tuple[int, str]] = []

        def refresh(self, text: str):
            self._chapters = detect_chapters(text)
