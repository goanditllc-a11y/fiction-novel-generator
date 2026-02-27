"""
novel_engine.py - Novel Generation Engine

Orchestrates the complete novel-creation pipeline:

  Phase 1 – Research  : ONE Gemini API call via researcher.py to gather
                         background knowledge about the idea and genre.
                         This is the ONLY external API call made per novel.

  Phases 2-7          : Fully local generation via local_generator.py.
                         No further API calls are made.  Characters, world,
                         plot, chapter outlines, chapter prose, and compilation
                         are all produced on the local machine using
                         genre-aware templates and classic story structure.

Why only one API call?
──────────────────────
The original design called Gemini for every phase (world-building, characters,
plot, each individual chapter, compilation) — 13+ calls per 10-chapter novel —
which immediately exhausts the free-tier quota
(GenerateRequestsPerMinutePerProjectPerModel-FreeTier and
 GenerateRequestsPerDayPerProjectPerModel-FreeTier).

By limiting the Gemini call to a single research query and doing all generation
locally, the app works correctly on the free tier indefinitely.

TO EXTEND: Add new local generation phases by adding methods to
           local_generator.LocalNovelGenerator and calling them here.
"""

from __future__ import annotations

from typing import Callable, Optional

import researcher
from local_generator import LocalNovelGenerator


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
        """
        Args:
            status_callback: A function that accepts a string message.
                             Used to stream progress updates to the GUI.
        """
        self.status_callback = status_callback

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _status(self, message: str) -> None:
        """Sends a status message to the callback if one is registered."""
        if self.status_callback:
            self.status_callback(message)

    # ------------------------------------------------------------------
    # Public Entry Point
    # ------------------------------------------------------------------

    def generate_novel(
        self,
        idea: str,
        genre: str,
        num_chapters: int,
    ) -> dict[str, str]:
        """
        Runs all 7 phases and returns a dict with all generated artefacts.

        Phase 1 makes a single Gemini API call (research).
        Phases 2-7 run entirely locally — no further API calls.

        Returns:
            {
                "novel":            full compiled novel text,
                "research":         research notes from Gemini,
                "world":            world bible (local),
                "characters":       character profiles (local),
                "plot_outline":     plot architecture document (local),
                "chapter_outlines": per-chapter outline (local),
            }

        Raises:
            ValueError: If no API key is configured and research is attempted.
            Exception:  On unrecoverable errors.
        """
        # ── Phase 1: Research (single Gemini API call) ─────────────────
        self._status("📚 Phase 1/7: Researching your topic...")
        research = researcher.research_topic(idea, genre)

        # ── Phases 2-7: Fully local generation ─────────────────────────
        generator = LocalNovelGenerator(
            idea=idea,
            genre=genre,
            research=research,
            num_chapters=num_chapters,
        )
        result = generator.generate_all(status_callback=self._status)

        # Attach the research text so it gets saved alongside the novel
        result["research"] = research

        self._status("✅ Novel generation complete!")
        return result
