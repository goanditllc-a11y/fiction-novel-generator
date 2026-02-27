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
# AI Model Settings
# ---------------------------------------------------------------------------

# The Gemini model to use for all generation tasks.
# TO EXTEND: Change this to any other supported Gemini model name.
DEFAULT_MODEL: str = "gemini-2.0-flash"

# Maximum output tokens per API call (controls response length).
MAX_OUTPUT_TOKENS: int = 8192

# Temperature controls creativity (0.0 = deterministic, 1.0 = very creative).
TEMPERATURE: float = 0.85

# ---------------------------------------------------------------------------
# Novel Defaults
# ---------------------------------------------------------------------------

# Default number of chapters when the app starts.
DEFAULT_CHAPTERS: int = 10

# Default genre selection in the dropdown.
DEFAULT_GENRE: str = "General"

# Minimum target word count per chapter (used in prompts as guidance).
MIN_WORDS_PER_CHAPTER: int = 1500

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
# API Key
# ---------------------------------------------------------------------------

def get_api_key() -> str:
    """
    Returns the Gemini API key loaded from the .env file.

    Returns an empty string if no key is configured so callers can
    detect and prompt the user.
    """
    return os.getenv("GEMINI_API_KEY", "")
