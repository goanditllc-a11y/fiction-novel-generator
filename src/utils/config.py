import json
import os
from src.utils.constants import (
    CONFIG_FILE, APPDATA_DIR, DEFAULT_FONT_SIZE,
    DEFAULT_FONT_FAMILY, DEFAULT_AUTOSAVE_INTERVAL, MAX_RECENT_FILES
)


class Config:
    """Application settings manager that persists settings to JSON."""

    DEFAULTS = {
        "theme": "light",
        "font_size": DEFAULT_FONT_SIZE,
        "font_family": DEFAULT_FONT_FAMILY,
        "autosave_interval": DEFAULT_AUTOSAVE_INTERVAL,
        "autosave_enabled": True,
        "recent_files": [],
        "window_geometry": None,
        "window_state": None,
        "chapter_panel_visible": True,
        "splitter_sizes": None,
    }

    def __init__(self):
        self._data = dict(self.DEFAULTS)
        os.makedirs(APPDATA_DIR, exist_ok=True)
        self.load()

    # ------------------------------------------------------------------
    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                self._data.update(loaded)
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2)
        except OSError:
            pass

    # ------------------------------------------------------------------
    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self.save()

    # ------------------------------------------------------------------
    # Convenience properties
    @property
    def theme(self) -> str:
        return self._data.get("theme", "light")

    @theme.setter
    def theme(self, value: str):
        self.set("theme", value)

    @property
    def font_size(self) -> int:
        return self._data.get("font_size", DEFAULT_FONT_SIZE)

    @font_size.setter
    def font_size(self, value: int):
        self.set("font_size", value)

    @property
    def font_family(self) -> str:
        return self._data.get("font_family", DEFAULT_FONT_FAMILY)

    @font_family.setter
    def font_family(self, value: str):
        self.set("font_family", value)

    @property
    def autosave_interval(self) -> int:
        return self._data.get("autosave_interval", DEFAULT_AUTOSAVE_INTERVAL)

    @autosave_interval.setter
    def autosave_interval(self, value: int):
        self.set("autosave_interval", value)

    @property
    def autosave_enabled(self) -> bool:
        return self._data.get("autosave_enabled", True)

    @autosave_enabled.setter
    def autosave_enabled(self, value: bool):
        self.set("autosave_enabled", value)

    @property
    def recent_files(self) -> list:
        return self._data.get("recent_files", [])

    def add_recent_file(self, path: str):
        files = self.recent_files
        if path in files:
            files.remove(path)
        files.insert(0, path)
        self.set("recent_files", files[:MAX_RECENT_FILES])

    def remove_recent_file(self, path: str):
        files = self.recent_files
        if path in files:
            files.remove(path)
            self.set("recent_files", files)
