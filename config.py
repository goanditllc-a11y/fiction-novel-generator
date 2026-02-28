"""
config.py - Application Configuration

This module centralizes all configurable settings for the Fiction Novel Generator.
Modify values here to change default behavior without touching other files.

TO EXTEND: Add new configuration options here and import them where needed.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file in the project root
load_dotenv()

# ---------------------------------------------------------------------------
# Ollama Local LLM Settings
# ---------------------------------------------------------------------------

# Ollama server address.  Change to a LAN address to use a remote Ollama instance.
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Recommended Ollama model for first-time users (good quality, ~2GB download).
# Run:  ollama pull llama3.2
OLLAMA_RECOMMENDED_MODEL: str = "llama3.2"

# Target words per chapter when using the Ollama LLM generator.
OLLAMA_TARGET_WORDS_PER_CHAPTER: int = 3500

# ---------------------------------------------------------------------------
# Novel Defaults
# ---------------------------------------------------------------------------

# Default number of chapters when the app starts.
# 25 chapters × ~3,500 words/chapter ≈ 87,500 words ≈ 350 pages.
DEFAULT_CHAPTERS: int = 25

# Default genre selection in the dropdown.
DEFAULT_GENRE: str = "General"

# Target word count per chapter for the local (non-Ollama) generator.
# Each chapter is assembled from multiple scene paragraphs to hit this target.
MIN_WORDS_PER_CHAPTER: int = 3500

# Genres available in the GUI dropdown.
# TO EXTEND: Add new genre strings to this list and they'll appear automatically.
GENRES: list[str] = [
    "Fantasy",
    "Sci-Fi",
    "Mystery",
    "Romance",
    "Thriller",
    "Historical Fiction",
    "Horror",
    "Literary Fiction",
    "Adventure",
    "General",
]

# ---------------------------------------------------------------------------
# File / Folder Settings
# ---------------------------------------------------------------------------

# Root directory where all generated novels are saved.
# Resolves to a "novels/" folder next to this config file.
NOVELS_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "novels")

# ---------------------------------------------------------------------------
# Legacy API key (kept for backward compatibility; not used by default)
# ---------------------------------------------------------------------------

def get_api_key() -> str:
    """
    Returns the Gemini API key from the environment (legacy; not used by default).
    Research now uses the free Wikipedia API — no key required.
    """
    return os.getenv("GEMINI_API_KEY", "")
