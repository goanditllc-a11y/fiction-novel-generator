"""
gui.py - Tkinter GUI for the Fiction Novel Generator

Builds the complete desktop window including:
  - Idea prompt input
  - Genre dropdown
  - Chapter count spinbox
  - Generate button with Ollama status indicator
  - Real-time progress/status area
  - Novel preview (scrollable, read-only)
  - Save / New Novel buttons
  - Settings dialog for Ollama configuration

The generation process runs on a background thread so the GUI never freezes.

TO EXTEND: Add new controls (e.g. writing-style selector) by following the
           pattern used for the genre dropdown below.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Optional

import file_manager
import novel_engine
import ollama_generator
from config import DEFAULT_CHAPTERS, DEFAULT_GENRE, GENRES


# ---------------------------------------------------------------------------
# Main Application Window
# ---------------------------------------------------------------------------

class NovelGeneratorApp(tk.Tk):
    """Root Tkinter window.  All widgets are created in _build_ui()."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Fiction Novel Generator")
        self.geometry("1280x820")
        self.minsize(960, 620)

        self._last_result: Optional[dict] = None
        self._last_idea: str = ""
        self._last_genre: str = ""
        self._last_chapters: int = DEFAULT_CHAPTERS

        style = ttk.Style(self)
        for preferred in ("clam", "alt", "default"):
            if preferred in style.theme_names():
                style.theme_use(preferred)
                break

        self._build_ui()
        # Check Ollama status after the window is drawn
        self.after(300, self._refresh_ollama_status)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ── Top bar ───────────────────────────────────────────────────
        top = ttk.Frame(self, padding=(10, 8))
        top.pack(fill=tk.X)

        ttk.Label(
            top,
            text="✍️  Fiction Novel Generator",
            font=("Segoe UI", 18, "bold"),
        ).pack(side=tk.LEFT)

        ttk.Button(
            top, text="⚙  Settings", command=self._open_settings,
        ).pack(side=tk.RIGHT, padx=4)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # ── Ollama status bar ─────────────────────────────────────────
        status_bar = ttk.Frame(self, padding=(10, 3))
        status_bar.pack(fill=tk.X)

        ttk.Label(status_bar, text="Generation engine:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self._ollama_label = ttk.Label(
            status_bar,
            text="Checking…",
            font=("Segoe UI", 9, "bold"),
            foreground="#888888",
        )
        self._ollama_label.pack(side=tk.LEFT, padx=(4, 0))

        ttk.Button(
            status_bar,
            text="↻ Refresh",
            command=self._refresh_ollama_status,
            width=9,
        ).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(
            status_bar,
            text="  |  No API key required — research uses free Wikipedia API",
            font=("Segoe UI", 9),
            foreground="#555555",
        ).pack(side=tk.LEFT)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # ── Main paned layout ─────────────────────────────────────────
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        left = ttk.Frame(paned, padding=6)
        right = ttk.Frame(paned, padding=6)
        paned.add(left, weight=1)
        paned.add(right, weight=2)

        self._build_left_panel(left)
        self._build_right_panel(right)

    def _build_left_panel(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Novel Idea / Concept:", font=("Segoe UI", 10, "bold")).pack(
            anchor=tk.W
        )
        self.idea_text = scrolledtext.ScrolledText(
            parent, height=8, wrap=tk.WORD, font=("Segoe UI", 10)
        )
        self.idea_text.pack(fill=tk.BOTH, expand=False, pady=(2, 8))
        self.idea_text.insert(
            "1.0",
            "Enter your novel idea here…\n\nExample: A young cartographer discovers "
            "that the maps she draws become real, pulling her into the living landscapes "
            "she creates.",
        )
        self.idea_text.bind("<FocusIn>", self._clear_placeholder)

        # Genre + Chapters row
        opts = ttk.Frame(parent)
        opts.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(opts, text="Genre:").grid(row=0, column=0, sticky=tk.W)
        self.genre_var = tk.StringVar(value=DEFAULT_GENRE)
        ttk.Combobox(
            opts,
            textvariable=self.genre_var,
            values=GENRES,
            state="readonly",
            width=18,
        ).grid(row=0, column=1, padx=(4, 16), sticky=tk.W)

        ttk.Label(opts, text="Chapters:").grid(row=0, column=2, sticky=tk.W)
        self.chapters_var = tk.IntVar(value=DEFAULT_CHAPTERS)
        ttk.Spinbox(
            opts, from_=1, to=50, textvariable=self.chapters_var, width=5,
        ).grid(row=0, column=3, padx=4, sticky=tk.W)

        ttk.Label(
            opts,
            text="(25 chapters ≈ 350+ pages)",
            font=("Segoe UI", 8),
            foreground="#666666",
        ).grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(2, 0))

        # Generate button
        self.generate_btn = ttk.Button(
            parent,
            text="🚀  Research & Generate Novel",
            command=self._start_generation,
        )
        self.generate_btn.pack(fill=tk.X, pady=(0, 8))

        # Action buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(0, 6))

        self.save_btn = ttk.Button(
            btn_frame,
            text="💾  Save Novel",
            command=self._save_novel,
            state=tk.DISABLED,
        )
        self.save_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))

        ttk.Button(
            btn_frame,
            text="🆕  New Novel",
            command=self._new_novel,
        ).pack(side=tk.LEFT, expand=True, fill=tk.X)

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)

        # Progress area
        ttk.Label(parent, text="Status / Progress:", font=("Segoe UI", 10, "bold")).pack(
            anchor=tk.W
        )
        self.status_text = scrolledtext.ScrolledText(
            parent,
            height=12,
            state=tk.DISABLED,
            font=("Consolas", 9),
            wrap=tk.WORD,
            background="#1e1e1e",
            foreground="#d4d4d4",
        )
        self.status_text.pack(fill=tk.BOTH, expand=True, pady=(2, 0))

    def _build_right_panel(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Novel Preview:", font=("Segoe UI", 10, "bold")).pack(
            anchor=tk.W
        )
        self.preview_text = scrolledtext.ScrolledText(
            parent,
            state=tk.DISABLED,
            font=("Georgia", 11),
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=12,
            pady=8,
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True, pady=(2, 0))

    # ------------------------------------------------------------------
    # Ollama status
    # ------------------------------------------------------------------

    def _refresh_ollama_status(self) -> None:
        """Checks Ollama availability and updates the status label."""
        def _check() -> None:
            if ollama_generator.is_available():
                model = ollama_generator.get_best_model()
                if model:
                    txt = f"✅ Ollama ready — model: {model}"
                    col = "#2a7a2a"
                else:
                    txt = "⚠️ Ollama running but no models pulled  (run: ollama pull llama3.2)"
                    col = "#b06000"
            else:
                txt = "ℹ️ Ollama not found — using built-in generator  (install from ollama.ai)"
                col = "#555555"
            self.after(0, self._ollama_label.config, {"text": txt, "foreground": col})

        threading.Thread(target=_check, daemon=True).start()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _clear_placeholder(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        current = self.idea_text.get("1.0", tk.END).strip()
        if current.startswith("Enter your novel idea here"):
            self.idea_text.delete("1.0", tk.END)

    def _open_settings(self) -> None:
        SettingsDialog(self)

    def _start_generation(self) -> None:
        idea = self.idea_text.get("1.0", tk.END).strip()
        if not idea or idea.startswith("Enter your novel idea here"):
            messagebox.showwarning("No Idea", "Please enter a novel idea first.")
            return

        genre = self.genre_var.get()
        try:
            num_chapters = int(self.chapters_var.get())
        except ValueError:
            messagebox.showwarning("Invalid Chapters", "Please enter a valid number of chapters.")
            return

        self.generate_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        self._last_result = None
        self._last_idea = idea
        self._last_genre = genre
        self._last_chapters = num_chapters

        self._set_preview("")
        self._append_status("\n" + "=" * 50 + "\n")
        self._append_status("Starting novel generation…\n")

        threading.Thread(
            target=self._run_generation,
            args=(idea, genre, num_chapters),
            daemon=True,
        ).start()

    def _run_generation(self, idea: str, genre: str, num_chapters: int) -> None:
        def status(msg: str) -> None:
            self.after(0, self._append_status, msg + "\n")

        try:
            engine = novel_engine.NovelEngine(status_callback=status)
            result = engine.generate_novel(idea, genre, num_chapters)
            self.after(0, self._on_generation_complete, result)
        except OSError as exc:
            self.after(0, self._on_generation_error, f"Network or file error:\n{exc}")
        except Exception as exc:  # noqa: BLE001
            self.after(0, self._on_generation_error, f"Unexpected error:\n{exc}")

    def _on_generation_complete(self, result: dict) -> None:
        self._last_result = result
        novel_text = result["novel"]
        word_count = len(novel_text.split())
        pages_est = word_count // 250
        self._set_preview(novel_text)
        self.save_btn.config(state=tk.NORMAL)
        self.generate_btn.config(state=tk.NORMAL)
        self._append_status(
            f"\n🎉 Novel ready!  "
            f"~{word_count:,} words (~{pages_est} pages).  "
            f"Click 'Save Novel' to export.\n"
        )
        messagebox.showinfo(
            "Done!",
            f"Your novel has been generated!\n\n"
            f"~{word_count:,} words (~{pages_est} pages)\n\n"
            f"Click 'Save Novel' to save it.",
        )

    def _on_generation_error(self, error_msg: str) -> None:
        self.generate_btn.config(state=tk.NORMAL)
        self._append_status(f"\n❌ Error: {error_msg}\n")
        messagebox.showerror("Generation Error", error_msg)

    def _save_novel(self) -> None:
        if not self._last_result:
            messagebox.showwarning("Nothing to Save", "Generate a novel first.")
            return
        try:
            saved_dir = file_manager.save_novel(
                novel_text=self._last_result["novel"],
                research=self._last_result.get("research", ""),
                characters=self._last_result.get("characters", ""),
                plot_outline=self._last_result.get("plot_outline", ""),
                idea=self._last_idea,
                genre=self._last_genre,
                num_chapters=self._last_chapters,
            )
            self._append_status(f"\n💾 Saved to: {saved_dir}\n")
            messagebox.showinfo("Saved!", f"Novel saved to:\n{saved_dir}")
        except (OSError, IOError) as exc:
            messagebox.showerror("Save Error", f"Could not write files:\n{exc}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Save Error", str(exc))

    def _new_novel(self) -> None:
        if self._last_result:
            if not messagebox.askyesno("New Novel", "Clear the current novel and start fresh?"):
                return
        self.idea_text.delete("1.0", tk.END)
        self.idea_text.insert(
            "1.0",
            "Enter your novel idea here…\n\nExample: A young cartographer discovers "
            "that the maps she draws become real, pulling her into the living landscapes "
            "she creates.",
        )
        self._set_preview("")
        self._clear_status()
        self.save_btn.config(state=tk.DISABLED)
        self._last_result = None

    # ------------------------------------------------------------------
    # Widget helpers
    # ------------------------------------------------------------------

    def _append_status(self, message: str) -> None:
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message)
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)

    def _clear_status(self) -> None:
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete("1.0", tk.END)
        self.status_text.config(state=tk.DISABLED)

    def _set_preview(self, text: str) -> None:
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        if text:
            self.preview_text.insert("1.0", text)
        self.preview_text.config(state=tk.DISABLED)


# ---------------------------------------------------------------------------
# Settings Dialog
# ---------------------------------------------------------------------------

class SettingsDialog(tk.Toplevel):
    """
    Modal settings dialog.
    Covers Ollama configuration and (optionally) the legacy Gemini API key.
    """

    def __init__(self, parent: tk.Tk) -> None:
        super().__init__(parent)
        self.title("Settings")
        self.resizable(False, False)
        self.grab_set()

        pad = {"padx": 12, "pady": 5}

        # ── Ollama section ─────────────────────────────────────────────
        ttk.Label(
            self,
            text="Ollama — Local LLM (recommended for author-quality prose)",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, **pad)

        ttk.Label(
            self,
            text=(
                "Ollama runs open-weight LLMs entirely on your PC — no API key needed.\n"
                "1. Download and install from https://ollama.ai/download\n"
                "2. Open a terminal and run:  ollama pull llama3.2\n"
                "3. Click 'Refresh' in the main window to activate."
            ),
            foreground="#444444",
            justify=tk.LEFT,
        ).grid(row=1, column=0, columnspan=2, padx=12, pady=(0, 4), sticky=tk.W)

        # Current Ollama status
        if ollama_generator.is_available():
            models = ollama_generator.get_available_models()
            best = ollama_generator.get_best_model()
            status_txt = (
                f"✅ Ollama is running.  Best model: {best}\n"
                f"Available models: {', '.join(models) or 'none'}"
            )
            col = "#2a7a2a"
        else:
            status_txt = (
                "ℹ️ Ollama is not running.  "
                "Install from https://ollama.ai/download for best quality."
            )
            col = "#555555"

        ttk.Label(
            self,
            text=status_txt,
            foreground=col,
            font=("Segoe UI", 9),
        ).grid(row=2, column=0, columnspan=2, padx=12, pady=(0, 8), sticky=tk.W)

        ttk.Separator(self, orient=tk.HORIZONTAL).grid(
            row=3, column=0, columnspan=2, sticky=tk.EW, padx=8, pady=4
        )

        # ── Research section ───────────────────────────────────────────
        ttk.Label(
            self,
            text="Research",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=4, column=0, columnspan=2, sticky=tk.W, **pad)

        ttk.Label(
            self,
            text=(
                "Research uses the free Wikipedia public API — no key or login needed.\n"
                "The app searches Wikipedia automatically based on your novel idea."
            ),
            foreground="#444444",
            justify=tk.LEFT,
        ).grid(row=5, column=0, columnspan=2, padx=12, pady=(0, 8), sticky=tk.W)

        ttk.Button(self, text="Close", command=self.destroy).grid(
            row=6, column=0, columnspan=2, pady=(4, 10)
        )

        self._center(parent)

    def _center(self, parent: tk.Tk) -> None:
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_x(), parent.winfo_y()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

