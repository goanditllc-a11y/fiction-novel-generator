"""
novel_engine.py - Novel Generation Engine

Orchestrates the complete novel-creation pipeline:

  Phase 1 – Research  : FREE web research via web_researcher.py using the
                         Wikipedia public API.  No API key or login required.
                         Falls back to built-in genre knowledge if offline.

  Phases 2-5          : Fully local generation via local_generator.py.
                         Characters, world, plot, and chapter outlines are
                         created entirely on the local machine.

  Phase 6 – Chapters  : Written by Ollama (local LLM) if Ollama is running,
                         otherwise by the enhanced local template generator.
                         Both paths produce 3,500+ words per chapter.

  Phase 7 – Compile   : Assembled into a complete, formatted novel document
                         (~350+ pages / 87,500+ words for 25 chapters).

Why Ollama for generation?
──────────────────────────
Ollama runs open-weight LLMs (Llama 3, Mistral, Phi-3, etc.) entirely on the
local machine.  No data leaves the user's computer.  The generated prose is
author-quality because the LLM has learned from millions of published works.
Install Ollama from https://ollama.ai/download and pull any model to activate.

TO EXTEND: Add new generation phases by adding methods to
           local_generator.LocalNovelGenerator and calling them here.
"""

from __future__ import annotations

from typing import Callable, List, Optional

import web_researcher
import ollama_generator
from local_generator import LocalNovelGenerator
from config import OLLAMA_TARGET_WORDS_PER_CHAPTER


# ---------------------------------------------------------------------------
# NovelEngine Class
# ---------------------------------------------------------------------------

class NovelEngine:
    """
    Orchestrates all phases of novel generation and reports progress
    back to the caller via an optional status callback.
    """

    def __init__(
        self,
        status_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.status_callback = status_callback

    def _status(self, message: str) -> None:
        if self.status_callback:
            self.status_callback(message)

    def generate_novel(
        self,
        idea: str,
        genre: str,
        num_chapters: int,
    ) -> dict[str, str]:
        """
        Runs all 7 phases and returns a dict with all generated artefacts.

        Phase 1 uses the Wikipedia public API (no key needed).
        Phase 6 uses Ollama if available, else the enhanced local generator.
        All other phases run entirely locally.

        Returns:
            {
                "novel":            full compiled novel text,
                "research":         research notes,
                "world":            world bible,
                "characters":       character profiles,
                "plot_outline":     plot architecture document,
                "chapter_outlines": per-chapter outline,
            }
        """
        # ── Phase 1: Research (Wikipedia API — no key required) ────────
        self._status("🔍 Phase 1/7: Researching your topic via Wikipedia...")
        research = web_researcher.research_topic(idea, genre)

        # ── Phase 2-5: Local structural generation ─────────────────────
        generator = LocalNovelGenerator(
            idea=idea,
            genre=genre,
            research=research,
            num_chapters=num_chapters,
        )

        # ── Detect Ollama ──────────────────────────────────────────────
        ollama_model: Optional[str] = None
        if ollama_generator.is_available():
            ollama_model = ollama_generator.get_best_model()
            if ollama_model:
                self._status(f"✅ Ollama detected — using model: {ollama_model}")
            else:
                self._status(
                    "⚠️  Ollama is running but has no models pulled.  "
                    "Run: ollama pull llama3.2 — using local generator instead."
                )
        else:
            self._status(
                "ℹ️  Ollama not detected — using built-in local generator.  "
                "Install Ollama from https://ollama.ai for author-quality prose."
            )

        # Build the chapter writer callable for generate_all()
        if ollama_model:
            chapter_writer = self._make_ollama_writer(
                ollama_model, generator, num_chapters
            )
        else:
            chapter_writer = None   # use LocalNovelGenerator.write_chapter()

        # ── Run phases 2-7 via LocalNovelGenerator ─────────────────────
        result = generator.generate_all(
            status_callback=self._status,
            chapter_writer=chapter_writer,
        )

        result["research"] = research
        self._status("✅ Novel generation complete!")
        return result

    def _make_ollama_writer(
        self,
        model: str,
        generator: LocalNovelGenerator,
        total_chapters: int,
    ) -> Callable:
        """
        Returns a chapter_writer callable that uses Ollama for prose generation
        but derives all structural context (characters, world, plot) from the
        LocalNovelGenerator instance.
        """
        chapter_summaries: List[str] = []

        def _writer(
            chapter_index: int,
            outline: dict,
            characters: list,
            world: object,
            plot: dict,
        ) -> str:
            protagonist = next((c for c in characters if c.role == "protagonist"), characters[0])
            antagonist = next((c for c in characters if c.role == "antagonist"), characters[-1])
            supporting = [c.name for c in characters if c.role == "supporting"]
            atm = generator._pick(generator._gd["atmosphere"])  # type: ignore[attr-defined]

            prev_summary = (
                chapter_summaries[-1] if chapter_summaries else ""
            )

            self._status(
                f"✍️  Writing chapter {chapter_index + 1}/{total_chapters} via Ollama"
            )

            chapter_text = ollama_generator.write_chapter(
                model=model,
                chapter_num=chapter_index + 1,
                total_chapters=total_chapters,
                chapter_title=outline["title"],
                beat=outline["beat"],
                protagonist_name=protagonist.name,
                protagonist_trait=protagonist.trait,
                protagonist_flaw=protagonist.flaw,
                protagonist_motivation=protagonist.motivation,
                antagonist_name=antagonist.name,
                supporting_chars=supporting,
                location=outline["location"],
                genre=generator.genre,
                genre_atmosphere=atm,
                plot_summary=plot["premise"],
                previous_chapter_summary=prev_summary,
                target_words=OLLAMA_TARGET_WORDS_PER_CHAPTER,
                status_callback=self._status,
            )

            # Build a brief summary for the next chapter's context
            words = chapter_text.split()
            snippet = " ".join(words[max(0, len(words) - 80):])
            chapter_summaries.append(snippet)

            return chapter_text

        return _writer
