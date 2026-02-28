"""AutoSave – periodically saves the current document."""
import os
import glob as _glob
from datetime import datetime

try:
    from PyQt6.QtCore import QTimer, QObject, pyqtSignal
    _QT_AVAILABLE = True
except ImportError:
    _QT_AVAILABLE = False

from src.utils.constants import AUTOSAVE_DIR, DEFAULT_AUTOSAVE_INTERVAL


class AutoSave(QObject if _QT_AVAILABLE else object):
    """Saves content periodically and keeps the last *max_versions* copies."""

    if _QT_AVAILABLE:
        saved = pyqtSignal(str)   # emitted with autosave file path

    MAX_VERSIONS = 5

    def __init__(self, get_content_callback, parent=None):
        """
        Parameters
        ----------
        get_content_callback : callable
            Called with no arguments; should return the current document text.
        """
        if _QT_AVAILABLE:
            super().__init__(parent)
        self._get_content = get_content_callback
        self._current_filename: str = "untitled"
        self._enabled: bool = True
        self._interval: int = DEFAULT_AUTOSAVE_INTERVAL  # seconds

        os.makedirs(AUTOSAVE_DIR, exist_ok=True)

        if _QT_AVAILABLE:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._do_save)
            self._timer.start(self._interval * 1000)

    # ------------------------------------------------------------------
    def set_interval(self, seconds: int):
        self._interval = seconds
        if _QT_AVAILABLE:
            self._timer.setInterval(seconds * 1000)

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        if _QT_AVAILABLE:
            if enabled:
                self._timer.start(self._interval * 1000)
            else:
                self._timer.stop()

    def set_filename(self, path: str):
        """Tells autosave which base filename to use."""
        self._current_filename = os.path.splitext(os.path.basename(path))[0] if path else "untitled"

    # ------------------------------------------------------------------
    def _do_save(self):
        if not self._enabled:
            return
        content = self._get_content()
        if not content:
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(AUTOSAVE_DIR, f"{self._current_filename}_{ts}.autosave")
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self._prune_old_saves()
            if _QT_AVAILABLE:
                self.saved.emit(save_path)
        except OSError:
            pass

    def force_save(self):
        """Trigger an immediate autosave."""
        self._do_save()

    # ------------------------------------------------------------------
    def _prune_old_saves(self):
        pattern = os.path.join(AUTOSAVE_DIR, f"{self._current_filename}_*.autosave")
        files = sorted(_glob.glob(pattern))
        while len(files) > self.MAX_VERSIONS:
            try:
                os.remove(files.pop(0))
            except OSError:
                pass

    # ------------------------------------------------------------------
    def list_autosaves(self, filename: str = None) -> list:
        """Return sorted list of autosave paths for *filename* (or current)."""
        base = filename or self._current_filename
        pattern = os.path.join(AUTOSAVE_DIR, f"{base}_*.autosave")
        return sorted(_glob.glob(pattern), reverse=True)

    def restore_latest(self, filename: str = None) -> str | None:
        """Return the content of the most recent autosave, or None."""
        saves = self.list_autosaves(filename)
        if not saves:
            return None
        try:
            with open(saves[0], 'r', encoding='utf-8') as f:
                return f.read()
        except OSError:
            return None
