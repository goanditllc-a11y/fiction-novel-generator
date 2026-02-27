"""
gui.py - Tkinter GUI for the Fiction Novel Generator

Builds the complete desktop window including:
  - Idea prompt input
  - Genre dropdown
  - Chapter count spinbox
  - Generate button
  - Real-time progress/status area
  - Novel preview (scrollable, read-only)
  - Save / New Novel buttons
  - Settings dialog for API key management

The generation process runs on a background thread so the GUI never freezes.

TO EXTEND: Add new controls (e.g. writing-style selector) by following the
           pattern used for the genre dropdown below.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog, ttk
from typing import Optional

import file_manager
import novel_engine
from config import DEFAULT_CHAPTERS, DEFAULT_GENRE, GENRES


# ---------------------------------------------------------------------------
# Main Application Window
# ---------------------------------------------------------------------------

class NovelGeneratorApp(tk.Tk):
    """
    Root Tkinter window.  All widgets are created in _build_ui().
    """

    def __init__(self) -> None:
        super().__init__()
        self.title("Fiction Novel Generator")
        self.geometry("1200x800")
        self.minsize(900, 600)

        # Holds the last generated novel data so Save works
        self._last_result: Optional[dict[str, str]] = None
        self._last_idea: str = ""
        self._last_genre: str = ""
        self._last_chapters: int = DEFAULT_CHAPTERS

        # Apply a clean ttk theme
        style = ttk.Style(self)
        available = style.theme_names()
        for preferred in ("clam", "alt", "default"):
            if preferred in available:
                style.theme_use(preferred)
                break

        self._build_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Creates and arranges all widgets inside the main window."""

        # ── Top bar: title label ──────────────────────────────────────
        top_frame = ttk.Frame(self, padding=(10, 8))
        top_frame.pack(fill=tk.X)

        ttk.Label(
            top_frame,
            text="✍️  Fiction Novel Generator",
            font=("Segoe UI", 18, "bold"),
        ).pack(side=tk.LEFT)

        ttk.Button(
            top_frame,
            text="⚙  Settings",
            command=self._open_settings,
        ).pack(side=tk.RIGHT, padx=4)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # ── Main paned layout ─────────────────────────────────────────
        # Left panel: inputs + controls
        # Right panel: preview
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        left_frame = ttk.Frame(paned, padding=6)
        right_frame = ttk.Frame(paned, padding=6)
        paned.add(left_frame, weight=1)
        paned.add(right_frame, weight=2)

        # ── Left panel ───────────────────────────────────────────────
        self._build_left_panel(left_frame)

        # ── Right panel ──────────────────────────────────────────────
        self._build_right_panel(right_frame)

    def _build_left_panel(self, parent: ttk.Frame) -> None:
        """Builds the input controls and progress area."""

        # Idea prompt
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
        options_frame = ttk.Frame(parent)
        options_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(options_frame, text="Genre:").grid(row=0, column=0, sticky=tk.W)
        self.genre_var = tk.StringVar(value=DEFAULT_GENRE)
        genre_combo = ttk.Combobox(
            options_frame,
            textvariable=self.genre_var,
            values=GENRES,  # TO EXTEND: Add genres to GENRES list in config.py
            state="readonly",
            width=18,
        )
        genre_combo.grid(row=0, column=1, padx=(4, 16), sticky=tk.W)

        ttk.Label(options_frame, text="Chapters:").grid(row=0, column=2, sticky=tk.W)
        self.chapters_var = tk.IntVar(value=DEFAULT_CHAPTERS)
        ttk.Spinbox(
            options_frame,
            from_=1,
            to=50,
            textvariable=self.chapters_var,
            width=5,
        ).grid(row=0, column=3, padx=4, sticky=tk.W)

        # Generate button
        self.generate_btn = ttk.Button(
            parent,
            text="🚀  Research & Generate Novel",
            command=self._start_generation,
        )
        self.generate_btn.pack(fill=tk.X, pady=(0, 8))

        # Action buttons row
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

        # Progress / status area
        ttk.Label(
            parent, text="Status / Progress:", font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W)
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
        """Builds the novel preview area."""
        ttk.Label(
            parent, text="Novel Preview:", font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W)
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
    # Event Handlers
    # ------------------------------------------------------------------

    def _clear_placeholder(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        """Clears the placeholder text when the idea box is first focused."""
        current = self.idea_text.get("1.0", tk.END).strip()
        if current.startswith("Enter your novel idea here"):
            self.idea_text.delete("1.0", tk.END)

    def _open_settings(self) -> None:
        """Opens a simple dialog where the user can enter/update their API key."""
        SettingsDialog(self)

    def _start_generation(self) -> None:
        """Validates inputs then starts the generation thread."""
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

        # Disable generate button while running
        self.generate_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        self._last_result = None
        self._last_idea = idea
        self._last_genre = genre
        self._last_chapters = num_chapters

        # Clear previous content
        self._set_preview("")
        self._append_status("\n" + "=" * 50 + "\n")
        self._append_status("Starting novel generation…\n")

        # Run on background thread so the GUI stays responsive
        thread = threading.Thread(
            target=self._run_generation,
            args=(idea, genre, num_chapters),
            daemon=True,
        )
        thread.start()

    def _run_generation(self, idea: str, genre: str, num_chapters: int) -> None:
        """
        Runs the novel engine on a background thread.
        Posts all UI updates back to the main thread via after().
        """
        def status(msg: str) -> None:
            self.after(0, self._append_status, msg + "\n")

        try:
            engine = novel_engine.NovelEngine(status_callback=status)
            result = engine.generate_novel(idea, genre, num_chapters)
            self.after(0, self._on_generation_complete, result)
        except ValueError as exc:
            # Missing API key or invalid configuration
            self.after(0, self._on_generation_error, str(exc))
        except OSError as exc:
            # Network or file-system errors
            self.after(0, self._on_generation_error, f"Network or file error:\n{exc}")
        except Exception as exc:  # noqa: BLE001
            # Catch-all so the GUI never crashes — show the error to the user
            self.after(0, self._on_generation_error, f"Unexpected error:\n{exc}")

    def _on_generation_complete(self, result: dict[str, str]) -> None:
        """Called on the main thread when generation finishes successfully."""
        self._last_result = result
        self._set_preview(result["novel"])
        self.save_btn.config(state=tk.NORMAL)
        self.generate_btn.config(state=tk.NORMAL)
        self._append_status("\n🎉 Novel ready! Click 'Save Novel' to export.\n")
        messagebox.showinfo(
            "Done!", "Your novel has been generated!\n\nClick 'Save Novel' to save it."
        )

    def _on_generation_error(self, error_msg: str) -> None:
        """Called on the main thread when generation fails."""
        self.generate_btn.config(state=tk.NORMAL)
        self._append_status(f"\n❌ Error: {error_msg}\n")
        messagebox.showerror("Generation Error", error_msg)

    def _save_novel(self) -> None:
        """Saves the generated novel to disk."""
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
            messagebox.showerror(
                "Save Error",
                f"Could not write files — check disk space and permissions:\n{exc}",
            )
        except Exception as exc:  # noqa: BLE001
            # Catch-all so the GUI never crashes during save
            messagebox.showerror("Save Error", str(exc))

    def _new_novel(self) -> None:
        """Resets the UI for a fresh start."""
        if self._last_result:
            if not messagebox.askyesno(
                "New Novel", "Clear the current novel and start fresh?"
            ):
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
    # Widget Helpers
    # ------------------------------------------------------------------

    def _append_status(self, message: str) -> None:
        """Appends *message* to the status/progress area."""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message)
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)

    def _clear_status(self) -> None:
        """Clears the status/progress area."""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete("1.0", tk.END)
        self.status_text.config(state=tk.DISABLED)

    def _set_preview(self, text: str) -> None:
        """Replaces the novel preview area with *text*."""
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
    A modal dialog that lets the user enter or update their Gemini API key.
    The key is used for a single research call (Phase 1) only — all novel
    generation (phases 2-7) runs locally with no further API calls.
    The key is persisted by rewriting the .env file.
    """

    def __init__(self, parent: tk.Tk) -> None:
        super().__init__(parent)
        self.title("Settings – API Key")
        self.resizable(False, False)
        self.grab_set()  # make modal

        padding = {"padx": 12, "pady": 6}

        ttk.Label(
            self,
            text="Gemini API Key:",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, sticky=tk.W, **padding)

        ttk.Label(
            self,
            text=(
                "The key is used for one research call per novel.\n"
                "All generation (characters, plot, chapters) runs locally — no extra API calls."
            ),
            foreground="#555555",
        ).grid(row=1, column=0, columnspan=2, padx=12, pady=(0, 4), sticky=tk.W)

        # Read existing key from env
        import os
        current_key = os.getenv("GEMINI_API_KEY", "")

        self.key_var = tk.StringVar(value=current_key)
        entry = ttk.Entry(self, textvariable=self.key_var, width=52, show="*")
        entry.grid(row=2, column=0, columnspan=2, **padding)

        self.show_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self,
            text="Show key",
            variable=self.show_var,
            command=lambda: entry.config(show="" if self.show_var.get() else "*"),
        ).grid(row=3, column=0, sticky=tk.W, padx=12)

        ttk.Label(
            self,
            text="Get a free key at: https://aistudio.google.com/app/apikey",
            foreground="blue",
            cursor="hand2",
        ).grid(row=4, column=0, columnspan=2, padx=12, pady=(2, 8), sticky=tk.W)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(0, 10))
        ttk.Button(btn_frame, text="Save", command=self._save).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(
            side=tk.LEFT, padx=6
        )

        self.center_on_parent(parent)

    def center_on_parent(self, parent: tk.Tk) -> None:
        """Centers this dialog over the parent window."""
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_x(), parent.winfo_y()
        w, h = self.winfo_width(), self.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{x}+{y}")

    def _save(self) -> None:
        """Writes the API key to the .env file and updates the environment."""
        import os
        key = self.key_var.get().strip()
        if not key:
            # API key is optional — the app uses a local fallback without one
            messagebox.showinfo(
                "No Key Entered",
                "No API key was entered.\n\n"
                "The app will use built-in genre knowledge for research and generate "
                "your novel entirely locally.\n\n"
                "To enable Gemini-powered research, enter a free key from "
                "https://aistudio.google.com/app/apikey",
                parent=self,
            )
            self.destroy()
            return

        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        # Preserve any other variables that may already be in the .env file
        existing_lines: list[str] = []
        if os.path.isfile(env_path):
            with open(env_path, "r", encoding="utf-8") as fh:
                existing_lines = [
                    ln for ln in fh.readlines() if not ln.startswith("GEMINI_API_KEY")
                ]

        existing_lines.append(f"GEMINI_API_KEY={key}\n")
        with open(env_path, "w", encoding="utf-8") as fh:
            fh.writelines(existing_lines)

        # Apply to current process so it takes effect immediately
        os.environ["GEMINI_API_KEY"] = key

        messagebox.showinfo("Saved", "API key saved successfully!", parent=self)
        self.destroy()
