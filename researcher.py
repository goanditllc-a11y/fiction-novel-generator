"""
researcher.py - AI-Powered Research Module

This module takes the user's novel idea and uses the Gemini API to perform
deep background research before the writing process begins.

The research covers:
  - Historical / cultural context
  - Genre conventions and tropes (to leverage or subvert)
  - Real-world accuracy checks for settings, technology, science
  - Character archetype ideas
  - Potential themes and conflicts

The returned research document is passed to the novel engine so every
subsequent generation step is grounded and consistent.

TO EXTEND: Add new research sub-sections by extending RESEARCH_PROMPT below.
"""

import google.generativeai as genai  # type: ignore
from config import DEFAULT_MODEL, MAX_OUTPUT_TOKENS, TEMPERATURE, get_api_key


# ---------------------------------------------------------------------------
# Prompt Template
# ---------------------------------------------------------------------------

RESEARCH_PROMPT = """You are an expert literary researcher and creative consultant.
A novelist has come to you with the following idea:

IDEA: {idea}
GENRE: {genre}

Please conduct deep, thorough research to support this novel. Your research report must cover:

1. **Historical & Cultural Context**
   - Relevant time periods, real events, or cultural settings that apply
   - Authentic details a reader would expect

2. **Genre Conventions**
   - Key tropes and narrative devices typical to {genre} fiction
   - Opportunities to subvert expectations in fresh ways

3. **World-Building Foundations**
   - Physical setting possibilities (geography, climate, architecture)
   - Social structures, technology level, or political systems if applicable

4. **Thematic Landscape**
   - Universal themes this idea naturally explores
   - Symbolic motifs worth weaving through the story

5. **Scientific / Technical Accuracy** (if relevant)
   - Any real science, medicine, law, or technology the story may touch
   - Facts the author should get right to maintain reader trust

6. **Character Archetypes & Dynamics**
   - Archetypal character roles that resonate in this genre/idea
   - Potential relationship tensions worth exploring

7. **Conflict & Stakes**
   - Internal and external conflict possibilities
   - What the characters stand to lose—what makes readers care

Please be specific, detailed, and literary in your response. This research will
directly shape the characters, world, and plot of the novel.
"""


# ---------------------------------------------------------------------------
# Main Research Function
# ---------------------------------------------------------------------------

def research_topic(idea: str, genre: str) -> str:
    """
    Uses the Gemini API to perform comprehensive research on the novel idea.

    Args:
        idea:  The user's raw novel idea/prompt text.
        genre: The selected genre string (e.g., "Fantasy", "Sci-Fi").

    Returns:
        A multi-section research document as a plain-text string.

    Raises:
        ValueError: If no API key is configured.
        Exception:  Propagates any API errors so the caller can handle them.
    """
    api_key = get_api_key()
    if not api_key:
        raise ValueError(
            "No Gemini API key found. Please set GEMINI_API_KEY in your .env file."
        )

    # Configure the Gemini client with our API key
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name=DEFAULT_MODEL,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=MAX_OUTPUT_TOKENS,
            temperature=TEMPERATURE,
        ),
    )

    prompt = RESEARCH_PROMPT.format(idea=idea, genre=genre)
    response = model.generate_content(prompt)
    return response.text
