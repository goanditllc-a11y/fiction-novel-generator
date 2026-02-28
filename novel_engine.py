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

import re
from typing import Callable, List, Optional

import web_researcher
import ollama_generator
from local_generator import LocalNovelGenerator
from config import OLLAMA_TARGET_WORDS_PER_CHAPTER


# ---------------------------------------------------------------------------
# Chapter-splitting helpers (used by rewrite_novel)
# ---------------------------------------------------------------------------

def _split_chapters(novel_text: str) -> "list[str]":
    """
    Splits a compiled novel into a list of text blocks, one per chapter
    (plus a leading block for the header / title page if present).

    Chapters are delimited by the '=' * 60 separator lines that
    _compile() inserts between them.
    """
    separator = re.compile(r"={10,}")
    # Use re.split to keep delimiters so we can reconstruct the text
    parts = separator.split(novel_text)
    # Strip empty segments
    return [p.strip() for p in parts if p.strip()]


def _is_chapter_block(block: str) -> bool:
    """Returns True if the block looks like a chapter (starts with 'Chapter N:')."""
    first_line = block.lstrip().split("\n")[0].strip()
    return bool(re.match(r"^Chapter\s+\d+", first_line, re.IGNORECASE))


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

    def rewrite_novel(
        self,
        original_result: dict,
        style_instruction: str,
    ) -> "dict[str, str]":
        """
        Rewrites the prose of every chapter in *original_result* according to
        *style_instruction* while keeping the plot, characters, and structure
        completely intact.

        When Ollama is available each chapter is sent to the LLM with the
        style instruction.  When Ollama is absent the novel is re-generated
        from scratch with the style instruction injected into the idea, which
        produces a new variation rather than a strict prose rewrite.

        Args:
            original_result:    Result dict returned by generate_novel().
            style_instruction:  Free-text style directive, e.g.
                                 "make it more literary and precise" or
                                 "make it darker and more suspenseful".

        Returns:
            A result dict identical in structure to generate_novel()'s output
            plus two extra keys:
              "rewrite_of"         — first 200 chars of the original novel text
              "style_instruction"  — the style directive that was applied
        """
        # ── Detect Ollama ──────────────────────────────────────────────
        ollama_model: Optional[str] = None
        if ollama_generator.is_available():
            ollama_model = ollama_generator.get_best_model()
            if ollama_model:
                self._status(f"✅ Ollama detected — using model: {ollama_model}")
            else:
                self._status(
                    "⚠️  Ollama running but no models pulled — "
                    "re-generating with style hint instead."
                )
        else:
            self._status(
                "ℹ️  Ollama not detected — re-generating novel with style hint.  "
                "Install Ollama from https://ollama.ai for chapter-level rewrites."
            )

        if ollama_model:
            result = self._rewrite_with_ollama(
                original_result, style_instruction, ollama_model
            )
        else:
            result = self._rewrite_via_regeneration(
                original_result, style_instruction
            )

        result["rewrite_of"] = original_result["novel"][:200]
        result["style_instruction"] = style_instruction
        return result

    def _rewrite_with_ollama(
        self,
        original_result: dict,
        style_instruction: str,
        ollama_model: str,
    ) -> "dict[str, str]":
        """Rewrites each chapter individually via Ollama."""
        original_novel = original_result["novel"]
        chapter_blocks = _split_chapters(original_novel)

        if not chapter_blocks:
            # Fallback: rewrite the whole text as a single block
            chapter_blocks = [original_novel]

        total_chapters = sum(1 for b in chapter_blocks if _is_chapter_block(b))
        rewritten: list[str] = []
        header_block: list[str] = []   # preamble before Chapter 1
        chapter_counter = 0

        for block in chapter_blocks:
            # The header/preamble (title page, TOC, etc.) is kept verbatim
            if not _is_chapter_block(block):
                header_block.append(block)
                continue

            chapter_counter += 1
            self._status(
                f"✏️  Rewriting chapter {chapter_counter}/{total_chapters} via Ollama"
            )
            rewritten_ch = ollama_generator.rewrite_chapter(
                model=ollama_model,
                chapter_text=block,
                style_instruction=style_instruction,
                status_callback=self._status,
            )
            rewritten.append(rewritten_ch)

        # Re-assemble: keep original header, replace chapter text
        separator = "\n\n" + "=" * 60 + "\n\n"
        new_novel = separator.join(header_block + rewritten)

        result = dict(original_result)
        result["novel"] = new_novel
        self._status("✅ Chapter-level rewrite complete!")
        return result

    def _rewrite_via_regeneration(
        self,
        original_result: dict,
        style_instruction: str,
    ) -> "dict[str, str]":
        """
        Fallback when Ollama is unavailable: re-runs the full generation
        pipeline with the style instruction woven into the original idea.
        """
        original_idea = original_result.get("idea", "a compelling story")
        enriched_idea = (
            f"{original_idea}\n\n"
            f"[Style directive: {style_instruction}]"
        )
        # Infer chapter count from the original, counting only real chapter blocks
        chapter_count = original_result.get("num_chapters") or sum(
            1 for b in _split_chapters(original_result["novel"]) if _is_chapter_block(b)
        ) or 10
        genre = original_result.get("genre", "General")
        return self.generate_novel(enriched_idea, genre, chapter_count)

    def generate_sequels(
        self,
        original_result: dict,
        sequel_idea: str,
        genre: str,
        num_chapters: int,
        num_versions: int,
    ) -> "list[dict[str, str]]":
        """
        Generates *num_versions* independent sequel drafts for the given
        original novel.  Each version runs the full 7-phase pipeline with
        the original novel's characters and plot woven into the premise, so
        every draft is a genuine continuation that picks up where the
        original left off.

        Args:
            original_result:  The result dict returned by generate_novel().
            sequel_idea:      A user-supplied sequel premise (may be empty).
            genre:            Genre for the sequel (defaults to original genre).
            num_chapters:     Number of chapters in each sequel draft.
            num_versions:     How many independent drafts to generate (1–5).

        Returns:
            A list of result dicts, each identical in structure to the dict
            returned by generate_novel(), plus an extra key:
              "sequel_version"  (int) — 1-based index of this draft.
        """
        # ── Build an enriched idea that includes original-novel context ──
        _CHAR_CTX_LIMIT = 600   # characters of character profiles to include
        _PLOT_CTX_LIMIT = 400   # characters of plot outline to include
        context_parts: list[str] = []
        if original_result.get("characters"):
            context_parts.append(
                "Characters from the original novel:\n"
                + original_result["characters"][:_CHAR_CTX_LIMIT]
            )
        if original_result.get("plot_outline"):
            context_parts.append(
                "Original plot outline:\n"
                + original_result["plot_outline"][:_PLOT_CTX_LIMIT]
            )
        context = "\n\n".join(context_parts)

        if context:
            enriched_idea = (
                f"{sequel_idea}\n\n"
                f"[This is a sequel — continue with the same characters and world.  "
                f"Original novel context:\n{context}]"
            )
        else:
            enriched_idea = sequel_idea

        # ── Generate each version independently ─────────────────────────
        results: list[dict] = []
        for version in range(1, num_versions + 1):
            self._status(
                f"\n{'─' * 40}\n"
                f"📖 Generating sequel version {version}/{num_versions}…\n"
            )
            result = self.generate_novel(enriched_idea, genre, num_chapters)
            result["sequel_version"] = version
            results.append(result)

        return results

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
