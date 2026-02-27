"""
novel_engine.py - Novel Generation Engine

This module orchestrates the complete novel-creation pipeline:

  Phase 1 – Research        : Deep background research on the idea
  Phase 2 – World Building  : Setting, locations, world rules
  Phase 3 – Characters      : Full character profiles
  Phase 4 – Plot Architecture: Story arc, subplots, themes, conflicts
  Phase 5 – Chapter Outlines: Per-chapter summaries
  Phase 6 – Chapter Writing : Full prose for every chapter
  Phase 7 – Compilation     : Title page, TOC, dedication, epilogue

Each phase sends real-time status messages back to the GUI via an optional
callback so the progress area stays live.

TO EXTEND: Add a new phase by defining a _build_* method and calling it
           from generate_novel() in the right order.
"""

from __future__ import annotations

import time
from typing import Callable, Optional

import google.generativeai as genai  # type: ignore

import researcher
from config import (
    DEFAULT_MODEL,
    MAX_OUTPUT_TOKENS,
    MIN_WORDS_PER_CHAPTER,
    TEMPERATURE,
    get_api_key,
)


# ---------------------------------------------------------------------------
# Prompt Templates
# ---------------------------------------------------------------------------

WORLD_BUILDING_PROMPT = """You are a master world-builder for {genre} fiction.

Using the research notes below, build a rich, detailed story world for this novel idea:
IDEA: {idea}

RESEARCH NOTES:
{research}

Create a comprehensive World Bible that includes:
1. **Setting Overview** – time period, geography, atmosphere, and tone
2. **Key Locations** – at least 5 vivid, specific places with descriptions
3. **World Rules** – laws of physics/magic/technology/society that govern this world
4. **History & Backstory** – relevant past events that shaped the current world
5. **Culture & Society** – customs, class structures, belief systems, languages
6. **Sensory Details** – sights, sounds, smells, textures that define the world

Be evocative and specific. A great world-bible makes every scene feel lived-in.
"""

CHARACTER_PROMPT = """You are an expert character designer for {genre} fiction.

IDEA: {idea}
WORLD CONTEXT: {world}

Create a full cast of characters. For each character provide:
- Full name and age
- Role in the story (protagonist / antagonist / supporting)
- Physical description (height, build, hair, eyes, distinctive features)
- Personality traits (3–5 core traits with nuance)
- Backstory (formative experiences that shaped who they are)
- Motivation (what they want and why they want it)
- Internal conflict (what holds them back or creates inner turmoil)
- Speech / voice patterns (how they talk, vocabulary, verbal tics)
- Character arc (how they will change by the end)

Create:
- 1 primary protagonist
- 1 primary antagonist (or antagonistic force)
- 2–4 supporting characters

Make every character feel fully human and three-dimensional.
"""

PLOT_PROMPT = """You are a master story architect for {genre} fiction.

IDEA: {idea}
WORLD: {world}
CHARACTERS: {characters}

Design a complete, compelling plot structure. Include:

1. **Story Premise** – one-paragraph hook
2. **Central Conflict** – the core dramatic question
3. **Story Arc** (5-act structure):
   - Act 1: Setup & inciting incident
   - Act 2a: Rising action, obstacles, first plot point
   - Act 2b: Midpoint shift, darkest moment, second plot point
   - Act 3: Climax, falling action, resolution
4. **Subplots** (2–3) – each with its own mini-arc
5. **Themes** – 2–3 central themes explored through plot and character
6. **Foreshadowing** – 3–5 seeds to plant early that pay off later
7. **Emotional Journey** – the reader's intended emotional experience chapter by chapter

Be specific about what happens, not vague. Great plots have clear cause-and-effect chains.
"""

CHAPTER_OUTLINE_PROMPT = """You are a professional novelist structuring a {genre} novel.

IDEA: {idea}
PLOT ARCHITECTURE: {plot}
NUMBER OF CHAPTERS: {num_chapters}

Create a detailed chapter-by-chapter outline. For each of the {num_chapters} chapters provide:
- Chapter number and a working title
- POV character (if using multiple perspectives)
- Scene locations
- Key events that happen (3–5 bullet points)
- Emotional tone and pacing
- How it advances the main plot or a subplot
- A compelling hook for the opening line (concept, not the actual line)
- Where it ends / what propels the reader to the next chapter

The outline should feel like a complete roadmap any writer could follow.
"""

CHAPTER_WRITING_PROMPT = """You are a skilled {genre} novelist writing Chapter {chapter_num} of {total_chapters}.

CHAPTER TITLE: {chapter_title}
CHAPTER OUTLINE: {chapter_outline}

FULL STORY CONTEXT:
- Idea: {idea}
- World: {world_summary}
- Characters: {character_summary}
- Plot Arc: {plot_summary}

Write Chapter {chapter_num} as polished, publication-ready fiction prose.

Requirements:
- Minimum {min_words} words of actual narrative
- Rich, immersive descriptions of setting and atmosphere
- Natural, character-distinct dialogue with dialogue tags and beats
- Interior monologue / emotional depth for POV character
- Varied sentence rhythm—mix short punchy sentences with longer flowing ones
- Show, don't tell—reveal character through action and dialogue
- End the chapter with a hook or emotional beat that pulls the reader forward

Write ONLY the chapter text. Start with "Chapter {chapter_num}: {chapter_title}" as a heading.
"""

COMPILATION_PROMPT = """You are a professional editor compiling a finished {genre} novel.

NOVEL IDEA: {idea}
AUTHOR (leave as "The Author" if unknown): The Author

Write the following front matter for this novel:

1. **Dedication Page** – a heartfelt, fitting dedication (invent a poetic one that matches the novel's themes)
2. **Author's Note / Epilogue** – a brief (200–300 word) author reflection on the themes of the book and what readers might take away

Keep the tone consistent with {genre} fiction. Be literary and genuine.
"""


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
        self._model: Optional[genai.GenerativeModel] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _status(self, message: str) -> None:
        """Sends a status message to the callback if one is registered."""
        if self.status_callback:
            self.status_callback(message)

    def _get_model(self) -> genai.GenerativeModel:
        """Lazily initialises and returns the Gemini model instance."""
        if self._model is None:
            api_key = get_api_key()
            if not api_key:
                raise ValueError(
                    "No Gemini API key found. Please add it via Settings."
                )
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(
                model_name=DEFAULT_MODEL,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                    temperature=TEMPERATURE,
                ),
            )
        return self._model

    def _generate(self, prompt: str) -> str:
        """
        Calls the Gemini API with the given prompt and returns the text.
        Retries only on transient network/rate-limit errors; auth and quota
        errors are raised immediately so the user sees a clear message.
        """
        # Keywords that indicate a transient (retry-able) failure
        _TRANSIENT_KEYWORDS = ("unavailable", "timeout", "rate", "429", "503", "500")

        model = self._get_model()
        for attempt in range(3):
            try:
                response = model.generate_content(prompt)
                return response.text
            except Exception as exc:  # noqa: BLE001
                error_lower = str(exc).lower()
                is_transient = any(kw in error_lower for kw in _TRANSIENT_KEYWORDS)
                if attempt < 2 and is_transient:
                    time.sleep(2 ** attempt)
                else:
                    raise
        return ""  # unreachable, but satisfies type checkers

    # ------------------------------------------------------------------
    # Generation Phases
    # ------------------------------------------------------------------

    def _phase_research(self, idea: str, genre: str) -> str:
        self._status("📚 Phase 1/7: Researching your topic...")
        return researcher.research_topic(idea, genre)

    def _phase_world_building(self, idea: str, genre: str, research: str) -> str:
        self._status("🌍 Phase 2/7: Building the story world...")
        prompt = WORLD_BUILDING_PROMPT.format(
            genre=genre, idea=idea, research=research
        )
        return self._generate(prompt)

    def _phase_characters(self, idea: str, genre: str, world: str) -> str:
        self._status("👥 Phase 3/7: Creating characters...")
        prompt = CHARACTER_PROMPT.format(genre=genre, idea=idea, world=world)
        return self._generate(prompt)

    def _phase_plot(
        self, idea: str, genre: str, world: str, characters: str
    ) -> str:
        self._status("📖 Phase 4/7: Architecting the plot...")
        prompt = PLOT_PROMPT.format(
            genre=genre, idea=idea, world=world, characters=characters
        )
        return self._generate(prompt)

    def _phase_chapter_outlines(
        self, idea: str, genre: str, plot: str, num_chapters: int
    ) -> str:
        self._status("📋 Phase 5/7: Outlining all chapters...")
        prompt = CHAPTER_OUTLINE_PROMPT.format(
            genre=genre, idea=idea, plot=plot, num_chapters=num_chapters
        )
        return self._generate(prompt)

    def _phase_write_chapters(
        self,
        idea: str,
        genre: str,
        world: str,
        characters: str,
        plot: str,
        chapter_outlines: str,
        num_chapters: int,
    ) -> list[str]:
        """Writes each chapter fully, returning a list of chapter text strings."""
        self._status("✍️  Phase 6/7: Writing chapters...")
        chapters: list[str] = []

        # Parse individual chapter outlines from the bulk outline text.
        # We send each chapter's context to keep prompts focused.
        outline_lines = chapter_outlines.split("\n")
        chapter_blocks: list[str] = []
        current_block: list[str] = []

        for line in outline_lines:
            stripped = line.strip()
            if stripped.lower().startswith("chapter") and current_block:
                chapter_blocks.append("\n".join(current_block))
                current_block = [line]
            else:
                current_block.append(line)
        if current_block:
            chapter_blocks.append("\n".join(current_block))

        # Pad or trim so we have exactly num_chapters blocks
        while len(chapter_blocks) < num_chapters:
            chapter_blocks.append(
                f"Chapter {len(chapter_blocks) + 1}: Continue the story."
            )
        chapter_blocks = chapter_blocks[:num_chapters]

        # Summarise long context to stay within token limits
        world_summary = world[:1500] if len(world) > 1500 else world
        char_summary = characters[:1500] if len(characters) > 1500 else characters
        plot_summary = plot[:1500] if len(plot) > 1500 else plot

        for i, outline_block in enumerate(chapter_blocks, start=1):
            self._status(
                f"✍️  Writing chapter {i} of {num_chapters}..."
            )
            # Extract a chapter title from the outline block
            title_line = outline_block.strip().split("\n")[0]
            chapter_title = (
                title_line.replace(f"Chapter {i}:", "")
                .replace(f"Chapter {i} -", "")
                .strip()
                or f"Chapter {i}"
            )

            prompt = CHAPTER_WRITING_PROMPT.format(
                genre=genre,
                chapter_num=i,
                total_chapters=num_chapters,
                chapter_title=chapter_title,
                chapter_outline=outline_block,
                idea=idea,
                world_summary=world_summary,
                character_summary=char_summary,
                plot_summary=plot_summary,
                min_words=MIN_WORDS_PER_CHAPTER,
            )
            chapter_text = self._generate(prompt)
            chapters.append(chapter_text)

        return chapters

    def _phase_compile(
        self,
        idea: str,
        genre: str,
        world: str,
        characters: str,
        plot: str,
        chapter_outlines: str,
        chapters: list[str],
    ) -> str:
        """Assembles all parts into the final novel document."""
        self._status("📦 Phase 7/7: Compiling the final novel...")

        # Generate dedication and epilogue
        front_matter = self._generate(
            COMPILATION_PROMPT.format(genre=genre, idea=idea)
        )

        # Build a table of contents from chapter headings
        toc_lines = ["TABLE OF CONTENTS", "=" * 40]
        for chapter in chapters:
            first_line = chapter.strip().split("\n")[0].strip()
            toc_lines.append(f"  {first_line}")
        toc_lines.append("  Epilogue / Author's Note")
        toc = "\n".join(toc_lines)

        # Assemble the full document
        parts = [
            "=" * 60,
            "FICTION NOVEL",
            "Generated by Fiction Novel Generator",
            "=" * 60,
            "",
            front_matter,
            "",
            toc,
            "",
        ]
        parts += chapters
        parts += [
            "",
            "=" * 60,
            "EPILOGUE / AUTHOR'S NOTE",
            "=" * 60,
            "",
            "— End of Novel —",
        ]

        return "\n\n".join(parts)

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

        Returns:
            {
                "novel":            full compiled novel text,
                "research":         research notes,
                "world":            world bible,
                "characters":       character profiles,
                "plot_outline":     plot architecture document,
                "chapter_outlines": per-chapter outline,
            }

        Raises:
            ValueError: If no API key is configured.
            Exception:  On unrecoverable API errors.
        """
        # Phase 1 – Research
        research = self._phase_research(idea, genre)

        # Phase 2 – World Building
        world = self._phase_world_building(idea, genre, research)

        # Phase 3 – Characters
        characters = self._phase_characters(idea, genre, world)

        # Phase 4 – Plot Architecture
        plot = self._phase_plot(idea, genre, world, characters)

        # Phase 5 – Chapter Outlines
        chapter_outlines = self._phase_chapter_outlines(
            idea, genre, plot, num_chapters
        )

        # Phase 6 – Write Chapters
        chapters = self._phase_write_chapters(
            idea, genre, world, characters, plot, chapter_outlines, num_chapters
        )

        # Phase 7 – Compile
        novel = self._phase_compile(
            idea, genre, world, characters, plot, chapter_outlines, chapters
        )

        self._status("✅ Novel generation complete!")

        return {
            "novel": novel,
            "research": research,
            "world": world,
            "characters": characters,
            "plot_outline": plot,
            "chapter_outlines": chapter_outlines,
        }
