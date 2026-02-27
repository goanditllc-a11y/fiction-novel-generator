"""
file_manager.py - Novel File Management

Handles saving completed novels to the organised folder structure:

  novels/
  └── YYYY-MM-DD/
      └── Novel_Title_Sanitized/
          └── v1/
              ├── Novel_Title_v1.txt
              ├── Novel_Title_v1.md
              ├── research_notes.txt
              ├── characters.txt
              ├── plot_outline.txt
              └── metadata.json

If a novel with the same title already exists for today's date the version
is automatically incremented (v1 → v2 → v3 …).

TO EXTEND: Add new output file types by adding another _write_* method and
           calling it inside save_novel().
"""

from __future__ import annotations

import json
import os
import re
from datetime import date
from typing import Optional

from config import NOVELS_DIR


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _sanitize(name: str) -> str:
    """
    Converts an arbitrary string into a safe file/folder name.

    - Strips leading/trailing whitespace
    - Replaces spaces with underscores
    - Removes characters that are invalid in Windows/Linux file names
    - Collapses multiple underscores into one
    - Limits length to 80 characters
    """
    name = name.strip()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^\w\-]", "", name)  # keep word chars, hyphens
    name = re.sub(r"_+", "_", name)
    return name[:80]


def _find_next_version(folder: str) -> int:
    """
    Returns the next available version number inside *folder*.

    Scans for sub-directories named 'v1', 'v2', … and returns max + 1.
    Returns 1 if the folder is empty or doesn't exist yet.
    """
    if not os.path.isdir(folder):
        return 1
    versions = [
        int(d[1:])
        for d in os.listdir(folder)
        if re.fullmatch(r"v\d+", d) and os.path.isdir(os.path.join(folder, d))
    ]
    return max(versions, default=0) + 1


def _extract_title(novel_text: str, idea: str) -> str:
    """
    Tries to extract a title from the novel text.

    The compiled novel starts with lines like:
      ====…
      FICTION NOVEL
      …
    But each chapter prompt is asked to start with 'Chapter N: Title'.
    We look for a 'Title:' pattern or fall back to the first few words of the idea.
    """
    # Look for an explicit title line
    for line in novel_text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("title:"):
            return stripped[6:].strip()

    # Fall back to first 6 words of the idea
    words = idea.split()[:6]
    return " ".join(words) if words else "My_Novel"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_novel(
    novel_text: str,
    research: str,
    characters: str,
    plot_outline: str,
    idea: str,
    genre: str,
    num_chapters: int,
    title: Optional[str] = None,
) -> str:
    """
    Saves all novel artefacts to the organised folder structure.

    Args:
        novel_text:   The full compiled novel (plain text).
        research:     Research notes string.
        characters:   Character profiles string.
        plot_outline: Plot architecture string.
        idea:         The original user idea/prompt.
        genre:        The selected genre.
        num_chapters: Number of chapters generated.
        title:        Optional override for the novel title. If None, the
                      title is extracted from the novel text.

    Returns:
        The absolute path to the version directory where files were saved.
    """
    # Determine title and sanitise it for use in file/folder names
    if not title:
        title = _extract_title(novel_text, idea)
    safe_title = _sanitize(title)

    # Build the path:  novels/YYYY-MM-DD/Title/
    today = date.today().isoformat()
    novel_dir = os.path.join(NOVELS_DIR, today, safe_title)

    # Determine version
    version = _find_next_version(novel_dir)
    version_str = f"v{version}"
    version_dir = os.path.join(novel_dir, version_str)
    os.makedirs(version_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Write files
    # ------------------------------------------------------------------

    # Plain-text novel
    txt_path = os.path.join(version_dir, f"{safe_title}_{version_str}.txt")
    with open(txt_path, "w", encoding="utf-8") as fh:
        fh.write(novel_text)

    # Markdown version — wrap chapters in ## headings
    md_text = _to_markdown(novel_text)
    md_path = os.path.join(version_dir, f"{safe_title}_{version_str}.md")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(md_text)

    # Research notes
    with open(
        os.path.join(version_dir, "research_notes.txt"), "w", encoding="utf-8"
    ) as fh:
        fh.write(research)

    # Character profiles
    with open(
        os.path.join(version_dir, "characters.txt"), "w", encoding="utf-8"
    ) as fh:
        fh.write(characters)

    # Plot outline
    with open(
        os.path.join(version_dir, "plot_outline.txt"), "w", encoding="utf-8"
    ) as fh:
        fh.write(plot_outline)

    # Metadata JSON
    word_count = len(novel_text.split())
    metadata = {
        "title": title,
        "date": today,
        "genre": genre,
        "num_chapters": num_chapters,
        "idea": idea,
        "version": version_str,
        "word_count": word_count,
    }
    with open(
        os.path.join(version_dir, "metadata.json"), "w", encoding="utf-8"
    ) as fh:
        json.dump(metadata, fh, indent=2, ensure_ascii=False)

    return version_dir


def _to_markdown(novel_text: str) -> str:
    """
    Converts plain novel text into a lightly-formatted Markdown document.

    Chapter headings (lines starting with 'Chapter N:') are promoted to
    level-2 Markdown headings. Section dividers are preserved as horizontal
    rules.
    """
    lines = novel_text.splitlines()
    md_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^Chapter \d+", stripped):
            md_lines.append(f"## {stripped}")
        elif stripped.startswith("==="):
            md_lines.append("---")
        else:
            md_lines.append(line)
    return "\n".join(md_lines)
