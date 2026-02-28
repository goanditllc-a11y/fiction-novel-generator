"""PromptEditor – dialog for applying AI instructions to selected text."""
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QLineEdit, QPushButton, QProgressBar, QComboBox, QMessageBox
)

from src.ai_editor.model_manager import ModelManager
from src.ai_editor.diff_viewer import DiffViewer

EXAMPLE_PROMPTS = [
    "Make this more suspenseful",
    "Rewrite in first person",
    "Expand with sensory details",
    "Condense to half length",
    "Make tone darker",
    "Improve the pacing",
    "Add more vivid descriptions",
    "Make dialogue more natural",
]


class _WorkerThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, text: str, instruction: str):
        super().__init__()
        self.text = text
        self.instruction = instruction

    def run(self):
        try:
            manager = ModelManager(progress_callback=lambda m: self.progress.emit(m))
            result = manager.run_prompt(self.text, self.instruction)
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))


class PromptEditor(QDialog):
    text_accepted = pyqtSignal(str, str)  # (original, revised)

    def __init__(self, selected_text: str, parent=None):
        super().__init__(parent)
        self.selected_text = selected_text
        self._worker: _WorkerThread | None = None
        self.setWindowTitle("AI Prompt Editor")
        self.resize(700, 500)
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Selected Text (read-only):"))
        self.original_view = QPlainTextEdit()
        self.original_view.setPlainText(self.selected_text)
        self.original_view.setReadOnly(True)
        self.original_view.setMaximumHeight(150)
        layout.addWidget(self.original_view)

        layout.addWidget(QLabel("Instruction:"))
        self.instruction_edit = QLineEdit()
        self.instruction_edit.setPlaceholderText("e.g. Make this more suspenseful")
        layout.addWidget(self.instruction_edit)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Presets:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["-- choose --"] + EXAMPLE_PROMPTS)
        self.preset_combo.currentIndexChanged.connect(self._preset_selected)
        preset_row.addWidget(self.preset_combo)
        layout.addLayout(preset_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # indeterminate
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        self.apply_btn = QPushButton("▶ Apply")
        self.apply_btn.clicked.connect(self._apply)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.apply_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    def _preset_selected(self, idx: int):
        if idx > 0:
            self.instruction_edit.setText(EXAMPLE_PROMPTS[idx - 1])

    def _apply(self):
        instruction = self.instruction_edit.text().strip()
        if not instruction:
            QMessageBox.warning(self, "No instruction", "Please enter an instruction.")
            return
        if not self.selected_text.strip():
            QMessageBox.warning(self, "No text", "No text selected.")
            return

        self.apply_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Running model …")

        self._worker = _WorkerThread(self.selected_text, instruction)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.progress.connect(lambda m: self.status_label.setText(m))
        self._worker.start()

    def _on_finished(self, result: str):
        self.apply_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Done.")
        dlg = DiffViewer(self.selected_text, result, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.accepted_text:
            self.text_accepted.emit(self.selected_text, dlg.accepted_text)
            self.accept()

    def _on_error(self, msg: str):
        self.apply_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("")
        QMessageBox.critical(self, "Error", f"AI model error:\n{msg}")
