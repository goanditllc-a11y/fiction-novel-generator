"""
ollama_generator.py - Local LLM Novel Generation via Ollama

Generates author-quality fiction prose entirely on the local machine
using Ollama (https://ollama.ai).  No internet connection or API key is
required for generation — only the initial research phase uses the web.

HOW IT WORKS
────────────
1. Checks whether Ollama is running at http://localhost:11434
2. Selects the best available model from the user's pulled models
3. Generates each chapter via the Ollama streaming API
4. Returns full chapter text for compilation

INSTALLING OLLAMA
────────────────
1. Download from https://ollama.ai/download (Windows installer available)
2. Run the installer — Ollama starts as a background service automatically
3. Open a Command Prompt and pull a model:

       ollama pull llama3.2        (recommended — ~2GB, good quality)
   or:
       ollama pull mistral         (~4GB, excellent quality)
   or:
       ollama pull llama3.1:8b     (~5GB, best quality for 8GB+ RAM)

4. Ollama will be detected automatically when you next run the app.

RECOMMENDED MODELS (quality vs size)
─────────────────────────────────────
Model               Size    RAM needed   Notes
─────────────────────────────────────────────
llama3.1:8b         5 GB    8 GB         Best overall quality
mistral:7b          4 GB    8 GB         Excellent creative writing
llama3.2:3b         2 GB    4 GB         Good for lower-spec machines
llama3.2            2 GB    4 GB         Same as llama3.2:3b
phi3:medium         2 GB    4 GB         Compact and capable
phi3:mini           1 GB    2 GB         Minimum viable quality

TO EXTEND: Add support for custom Ollama hosts (e.g. a LAN server) by
           changing OLLAMA_HOST in config.py.
"""

from __future__ import annotations

import json
from typing import Callable, List, Optional

try:
    import requests as _req
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

# Ollama server address — change in config.py to use a remote Ollama instance
OLLAMA_HOST = "http://localhost:11434"
_TIMEOUT_CONNECT = 3        # seconds — for availability check
_TIMEOUT_GENERATE = 900     # seconds — max per chapter (15 min)

# Preferred model ranking (highest quality first).
# The first model found in the user's Ollama installation is used.
_PREFERRED_MODELS = [
    "llama3.1:70b",
    "llama3.1:8b",
    "llama3.1",
    "mistral:7b",
    "mistral",
    "llama3.2:3b",
    "llama3.2",
    "phi3:medium",
    "gemma2",
    "phi3",
    "llama3.2:1b",
    "phi3:mini",
    "gemma",
    "llama2",
    "neural-chat",
    "vicuna",
]

# ---------------------------------------------------------------------------
# Availability / model discovery
# ---------------------------------------------------------------------------

def is_available() -> bool:
    """Returns True if Ollama is running and reachable on OLLAMA_HOST."""
    if not _REQUESTS_AVAILABLE:
        return False
    try:
        r = _req.get(f"{OLLAMA_HOST}/api/tags", timeout=_TIMEOUT_CONNECT)
        return r.status_code == 200
    except Exception:
        return False


def get_available_models() -> List[str]:
    """Returns the list of model names currently pulled in Ollama."""
    if not _REQUESTS_AVAILABLE:
        return []
    try:
        r = _req.get(f"{OLLAMA_HOST}/api/tags", timeout=_TIMEOUT_CONNECT)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


def get_best_model() -> Optional[str]:
    """
    Returns the name of the best available Ollama model.

    Prefers higher-quality models; falls back to the first available model
    if none of the preferred models are installed.
    Returns None if Ollama has no models pulled.
    """
    available = get_available_models()
    if not available:
        return None

    # Exact match
    for preferred in _PREFERRED_MODELS:
        if preferred in available:
            return preferred

    # Prefix match (e.g. "llama3.2:latest" matches "llama3.2")
    for preferred in _PREFERRED_MODELS:
        base = preferred.split(":")[0]
        for model in available:
            if model.startswith(base):
                return model

    return available[0]


# ---------------------------------------------------------------------------
# Low-level generation
# ---------------------------------------------------------------------------

def _generate_text(
    model: str,
    prompt: str,
    target_words: int = 3500,
    status_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Calls the Ollama /api/generate endpoint with streaming.

    Streams the response and returns the full generated text.
    Calls *status_callback* with a progress dot every ~250 tokens.
    """
    if not _REQUESTS_AVAILABLE:
        raise RuntimeError(
            "The 'requests' library is not installed.  "
            "Run: pip install requests"
        )

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.82,
            "top_p": 0.92,
            "repeat_penalty": 1.12,
            "num_predict": max(2048, target_words * 2),   # token budget scales with chapter target
        },
    }

    tokens: List[str] = []
    dot_count = 0

    with _req.post(
        f"{OLLAMA_HOST}/api/generate",
        json=payload,
        stream=True,
        timeout=_TIMEOUT_GENERATE,
    ) as response:
        response.raise_for_status()
        for raw_line in response.iter_lines():
            if not raw_line:
                continue
            try:
                data = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            token = data.get("response", "")
            tokens.append(token)
            dot_count += 1
            if status_callback and dot_count % 250 == 0:
                status_callback(".")
            if data.get("done", False):
                break

    return "".join(tokens).strip()


# ---------------------------------------------------------------------------
# Chapter generation
# ---------------------------------------------------------------------------

def write_chapter(
    model: str,
    chapter_num: int,
    total_chapters: int,
    chapter_title: str,
    beat: str,
    protagonist_name: str,
    protagonist_trait: str,
    protagonist_flaw: str,
    protagonist_motivation: str,
    antagonist_name: str,
    supporting_chars: List[str],
    location: str,
    genre: str,
    genre_atmosphere: str,
    plot_summary: str,
    previous_chapter_summary: str,
    target_words: int = 3500,
    status_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Generates a complete novel chapter using the local Ollama LLM.

    Args:
        model:                    Ollama model name (e.g. "llama3.2").
        chapter_num:              1-indexed chapter number.
        total_chapters:           Total number of chapters in the novel.
        chapter_title:            Human-readable chapter title.
        beat:                     Story beat label (e.g. "rising_action").
        protagonist_name:         Protagonist's full name.
        protagonist_trait:        Core positive trait.
        protagonist_flaw:         Fatal flaw.
        protagonist_motivation:   What drives them.
        antagonist_name:          Antagonist's full name.
        supporting_chars:         List of supporting character names.
        location:                 Primary setting for this chapter.
        genre:                    Genre string.
        genre_atmosphere:         Atmospheric description for the setting.
        plot_summary:             One-paragraph summary of the whole story.
        previous_chapter_summary: Brief summary of the previous chapter (or "").
        target_words:             Approximate target word count for the chapter.
        status_callback:          Called with "." tokens to show progress.

    Returns:
        Full chapter text beginning with "Chapter N: Title".
    """
    beat_directions: dict = {
        "exposition": (
            "Establish the protagonist's world with rich, specific sensory detail. "
            "Introduce the protagonist and the emotional wound or unmet need at their core — "
            "show it through action and specific detail, never by stating it directly. "
            "Plant the seeds of the coming disruption. End on a note that hints change is coming."
        ),
        "inciting_incident": (
            "Something irreversibly disrupts the protagonist's normal world and sets the "
            "story in motion. This event should feel both surprising and, in retrospect, "
            "inevitable. The protagonist is forced to respond — their world will never be "
            "the same. End the chapter with them committed to a course of action."
        ),
        "rising_action": (
            "The protagonist pursues their goal and encounters significant obstacles. "
            "Each attempt to solve the problem reveals new complications. "
            "The stakes become clearer and more personal. Show consequences of earlier choices. "
            "The protagonist's flaw begins to cost them ground."
        ),
        "complications": (
            "New information changes what the protagonist believed they understood. "
            "Allies may prove unreliable; the path forward becomes unclear. "
            "The protagonist's flaw actively costs them progress. "
            "At least one thing the reader expected to work must fail in a believable way."
        ),
        "midpoint": (
            "A major revelation reframes the central conflict — something is revealed that "
            "changes the nature of the quest. The protagonist cannot approach the problem "
            "the same way any more. This is often a false victory or a sobering defeat. "
            "Write a scene that feels like an axis around which the entire story turns."
        ),
        "darkest_moment": (
            "The protagonist reaches their lowest point. They lose something crucial — "
            "a key ally, a cherished belief, or their primary strategy. "
            "Write with emotional honesty about failure, despair, and isolation. "
            "The protagonist must sit with the full weight of what has gone wrong. "
            "End with a glimmer — not hope yet, but the smallest possible reason to continue."
        ),
        "climax_buildup": (
            "The protagonist gathers resources, makes hard decisions, and moves toward "
            "the final confrontation with focused intent. Everything learned through the "
            "story is now in play. Raise the tension with a sense of approaching inevitability. "
            "Secondary characters resolve their arcs or step aside."
        ),
        "climax": (
            "The central conflict peaks in a decisive confrontation. "
            "The protagonist must make a defining choice that resolves the central question. "
            "This choice must cost something real. The outcome should feel both surprising "
            "and completely inevitable given everything that has come before. "
            "Write with maximum emotional and dramatic intensity."
        ),
        "resolution": (
            "Show the aftermath of the climax. How has the protagonist changed? "
            "What has been permanently gained and permanently lost? "
            "Resolve secondary character arcs. "
            "End with an image or moment that captures the emotional truth of the entire story — "
            "something that will stay with the reader."
        ),
        "full_arc": (
            "Tell a complete story arc: establish the protagonist's world with sensory richness, "
            "disrupt it with an inciting incident, escalate complications, bring the protagonist "
            "to their lowest point, force a defining choice in the climax, and show the "
            "transformation in the resolution. Compress without summarising — dramatise every beat."
        ),
    }

    position_note = ""
    if chapter_num == 1:
        position_note = (
            "This is the OPENING CHAPTER. Begin in media res or with a scene that immediately "
            "establishes character and world. Do not start with backstory or prologue-style "
            "narration. Drop the reader directly into a specific moment."
        )
    elif chapter_num == total_chapters:
        position_note = (
            f"This is the FINAL CHAPTER ({total_chapters} of {total_chapters}). "
            "Resolve all remaining threads. The last sentence of this chapter is the last "
            "sentence of the novel — make it resonate. Leave the reader with an image "
            "or feeling, not a summary."
        )
    else:
        position_note = (
            f"This is chapter {chapter_num} of {total_chapters}. "
            "End on a note of tension or revelation that makes it impossible to stop reading."
        )

    prev_context = ""
    if previous_chapter_summary:
        prev_context = (
            f"\nThe previous chapter ended with: {previous_chapter_summary}\n"
            "Continue seamlessly from where we left off.\n"
        )

    supporting_list = ", ".join(supporting_chars) if supporting_chars else "none"

    prompt = (
        f"You are writing a {genre} novel at the level of a published literary author — "
        f"think {_genre_author_reference(genre)}. "
        f"Your prose is precise, sensory, psychologically deep, and emotionally honest.\n\n"
        f"Write Chapter {chapter_num}: {chapter_title}\n\n"
        f"NOVEL CONTEXT\n"
        f"─────────────\n"
        f"Genre: {genre}\n"
        f"Setting atmosphere: {genre_atmosphere}\n"
        f"This chapter's primary location: {location}\n"
        f"Protagonist: {protagonist_name} "
        f"(core trait: {protagonist_trait}; "
        f"fatal flaw: {protagonist_flaw}; "
        f"drives them: {protagonist_motivation})\n"
        f"Antagonist: {antagonist_name}\n"
        f"Supporting characters: {supporting_list}\n"
        f"Overall story: {plot_summary}\n"
        f"{prev_context}\n"
        f"CHAPTER POSITION\n"
        f"────────────────\n"
        f"{position_note}\n\n"
        f"DRAMATIC FUNCTION OF THIS CHAPTER\n"
        f"───────────────────────────────────\n"
        f"{beat_directions.get(beat, beat_directions['rising_action'])}\n\n"
        f"WRITING REQUIREMENTS\n"
        f"────────────────────\n"
        f"• Write approximately {target_words} words of fiction prose\n"
        f"• Begin with 'Chapter {chapter_num}: {chapter_title}'\n"
        f"• Use varied sentence structure: mix short punchy sentences with longer flowing ones\n"
        f"• Ground every scene in physical, sensory reality (sight, sound, smell, touch, taste)\n"
        f"• Show character psychology through specific actions and telling details, not by "
        f"stating emotions directly\n"
        f"• Dialogue must reveal character and advance plot simultaneously; avoid on-the-nose "
        f"exposition in speech\n"
        f"• Include at least 3 distinct scenes with purposeful transitions between them\n"
        f"• Subtext: what characters do NOT say is as important as what they say\n"
        f"• Do not include any author notes, preamble, or commentary outside the chapter text\n\n"
        f"Begin writing now:\n\n"
        f"Chapter {chapter_num}: {chapter_title}"
    )

    result = _generate_text(model, prompt, target_words=target_words, status_callback=status_callback)

    # Ensure heading is present
    heading = f"Chapter {chapter_num}: {chapter_title}"
    if not result.startswith("Chapter"):
        result = heading + "\n" + ("─" * 50) + "\n\n" + result
    elif "\n" not in result[:80]:
        result = result[:len(heading)] + "\n" + ("─" * 50) + "\n\n" + result[len(heading):].lstrip()

    return result


def _genre_author_reference(genre: str) -> str:
    """Returns a reference to a style exemplar for the given genre."""
    refs = {
        "Fantasy":            "Ursula K. Le Guin or Patrick Rothfuss",
        "Sci-Fi":             "Ted Chiang or Kim Stanley Robinson",
        "Mystery":            "Tana French or Donna Tartt",
        "Romance":            "Rainbow Rowell or Nora Roberts at her best",
        "Thriller":           "John le Carré or Gillian Flynn",
        "Horror":             "Shirley Jackson or Stephen Graham Jones",
        "Historical Fiction": "Hilary Mantel or Anthony Burgess",
        "Adventure":          "Patrick O'Brian or Cormac McCarthy",
        "Literary Fiction":   "Alice Munro or Kazuo Ishiguro",
        "General":            "Ann Tyler or Richard Russo",
    }
    return refs.get(genre, "a master of the craft")
