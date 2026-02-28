"""
researcher.py - Research Module (Gemini-powered, with offline fallback)

This module performs background research before novel generation begins.

PRIMARY PATH (API key configured):
    Makes a SINGLE Gemini API call to gather historical/cultural context,
    genre conventions, thematic ideas, and world-building foundations.
    This research text is then passed to local_generator.py, which uses
    it as raw material for all subsequent generation — no further API
    calls are made.

FALLBACK PATH (no API key):
    Returns a structured, genre-appropriate research stub generated
    entirely locally.  Novel generation continues normally; the output
    will be slightly less grounded in real-world facts but is otherwise
    complete.

NOTE: The Gemini API is used ONLY here (phase 1).  The rest of the
      pipeline (phases 2-7) runs entirely on the local machine.

TO EXTEND: Add new research sub-sections by extending RESEARCH_PROMPT below.
"""

import google.generativeai as genai  # type: ignore
import google.api_core.exceptions as gapi_exc  # type: ignore
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
# Offline fallback
# ---------------------------------------------------------------------------

_GENRE_FALLBACK_RESEARCH = {
    "Fantasy": (
        "RESEARCH NOTES (local fallback — no API key configured)\n\n"
        "1. Historical & Cultural Context\n"
        "   - Medieval and early modern Europe provide rich source material: feudal hierarchies,\n"
        "     knightly codes, ecclesiastical power, agrarian village life.\n"
        "   - Mythologies (Norse, Celtic, Greek) offer archetypal figures and cosmologies.\n\n"
        "2. Genre Conventions\n"
        "   - The Chosen One, the Mentor, the Dark Lord are core archetypes to leverage or subvert.\n"
        "   - Magic systems work best with consistent rules and meaningful costs.\n"
        "   - Epic scope balanced against intimate character moments defines the genre.\n\n"
        "3. World-Building Foundations\n"
        "   - Geography shapes culture: mountain kingdoms breed isolation and pride;\n"
        "     coastal cities breed trade and moral ambiguity.\n"
        "   - Magic as metaphor for power, knowledge, or identity resonates deeply.\n\n"
        "4. Thematic Landscape\n"
        "   - Sacrifice, the corrupting nature of power, the cost of destiny.\n"
        "   - Coming-of-age in an indifferent world.\n\n"
        "5. Character Archetypes\n"
        "   - The reluctant hero; the fallen mentor; the loyal friend who doubts.\n"
        "   - Antagonists work best when they believe they are right.\n\n"
        "6. Conflict & Stakes\n"
        "   - External: the fate of the world, a kingdom, or a family.\n"
        "   - Internal: identity, legacy, the fear of becoming what you fight.\n"
    ),
    "Sci-Fi": (
        "RESEARCH NOTES (local fallback — no API key configured)\n\n"
        "1. Historical & Cultural Context\n"
        "   - The Space Race, Cold War paranoia, and Silicon Valley techno-optimism all\n"
        "     inform the genre's anxieties and dreams.\n"
        "   - Colonialism and its legacy map powerfully onto interplanetary settings.\n\n"
        "2. Genre Conventions\n"
        "   - Hard SF values scientific plausibility; soft SF privileges ideas and character.\n"
        "   - The lone scientist/hero archetype; the corporate or government antagonist.\n"
        "   - First-contact stories interrogate what 'human' means.\n\n"
        "3. World-Building Foundations\n"
        "   - Technology extrapolation: one 'what if' pushed to its logical extreme.\n"
        "   - Social structures under resource scarcity or post-scarcity differ radically.\n\n"
        "4. Thematic Landscape\n"
        "   - What does it mean to be human? The ethics of progress. Isolation vs. connection.\n\n"
        "5. Character Archetypes\n"
        "   - The pragmatist scientist; the idealist explorer; the AI that learns empathy.\n\n"
        "6. Conflict & Stakes\n"
        "   - Survival against indifferent physics; ethical dilemmas with no clean answer.\n"
    ),
    "Mystery": (
        "RESEARCH NOTES (local fallback — no API key configured)\n\n"
        "1. Historical & Cultural Context\n"
        "   - The Golden Age (1920s-30s): country houses, drawing-room logic, social stability.\n"
        "   - Hardboiled tradition: urban corruption, moral ambiguity, the lone detective.\n\n"
        "2. Genre Conventions\n"
        "   - Fair-play: all clues available to the reader before the solution.\n"
        "   - Red herrings must be genuine misdirections, not cheats.\n"
        "   - The detective's method reveals their character.\n\n"
        "3. World-Building Foundations\n"
        "   - Closed communities (villages, ships, snowbound estates) concentrate suspects.\n"
        "   - Class, money, and secrets are the engine of most motives.\n\n"
        "4. Thematic Landscape\n"
        "   - The fragility of social order; the burden of knowledge; justice vs. the law.\n\n"
        "5. Character Archetypes\n"
        "   - The brilliant eccentric; the reliable Watson; the suspect who is hiding\n"
        "     something other than the crime.\n\n"
        "6. Conflict & Stakes\n"
        "   - Intellectual: the puzzle. Moral: what to do with the answer once found.\n"
    ),
    "default": (
        "RESEARCH NOTES (local fallback — no API key configured)\n\n"
        "1. Historical & Cultural Context\n"
        "   - Draw on the specific time and place of your story for authentic detail.\n"
        "   - Social structures, class, and economics shape what characters can and cannot do.\n\n"
        "2. Genre Conventions\n"
        "   - Identify three central genre expectations; decide which to meet and which to subvert.\n"
        "   - Pacing, narrative distance, and tone are genre signals as much as subject matter.\n\n"
        "3. World-Building Foundations\n"
        "   - Ground the story in specific, sensory-rich places.\n"
        "   - Establish rules for what is possible; maintain them consistently.\n\n"
        "4. Thematic Landscape\n"
        "   - The best themes emerge from character, not from authorial statement.\n"
        "   - Identity, belonging, sacrifice, and change are universally resonant.\n\n"
        "5. Character Archetypes\n"
        "   - Every character needs a want (external) and a need (internal) that are in tension.\n"
        "   - Antagonists should believe they are the hero of their own story.\n\n"
        "6. Conflict & Stakes\n"
        "   - The highest stakes are always personal, even when the plot is global.\n"
        "   - What your protagonist stands to lose must be something the reader cares about.\n"
    ),
}


def _local_research_fallback(idea: str, genre: str) -> str:
    """Return a genre-appropriate research stub without any API calls."""
    base = _GENRE_FALLBACK_RESEARCH.get(genre, _GENRE_FALLBACK_RESEARCH["default"])
    return base + f"\nIdea under development: {idea}\n"


# ---------------------------------------------------------------------------
# Main Research Function
# ---------------------------------------------------------------------------

def research_topic(idea: str, genre: str) -> str:
    """
    Uses the Gemini API to perform research on the novel idea (one API call).
    If no API key is configured, returns a local genre-appropriate research stub
    so generation can proceed without an internet connection.

    Args:
        idea:  The user's raw novel idea/prompt text.
        genre: The selected genre string (e.g., "Fantasy", "Sci-Fi").

    Returns:
        A multi-section research document as a plain-text string.

    Raises:
        Exception: On unrecoverable API errors (auth failure, network error, etc.).
                   Missing API key does NOT raise — the local fallback is used instead.
                   Quota / rate-limit errors (429) also use the local fallback instead
                   of raising, so generation always continues.
    """
    api_key = get_api_key()
    if not api_key:
        # No key — use the local fallback and continue
        return _local_research_fallback(idea, genre)

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
    try:
        response = model.generate_content(prompt)
        return response.text
    except (_gapi_exc.ResourceExhausted, _gapi_exc.TooManyRequests) as exc:
        # Free-tier daily or per-minute quota exceeded — use local fallback
        # so the user can still generate a novel without waiting for the quota reset.
        quota_note = (
            "RESEARCH NOTES (API quota exceeded — local fallback used)\n\n"
            "The Gemini API returned a quota-exceeded error (429).  "
            "Novel generation will continue using built-in genre knowledge.\n"
            "To retry with AI research, wait until your free-tier quota resets "
            "(typically at midnight Pacific time) or upgrade your Google AI plan.\n\n"
        )
        return quota_note + _local_research_fallback(idea, genre)
