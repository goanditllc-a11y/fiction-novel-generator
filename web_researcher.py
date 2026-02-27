"""
web_researcher.py - Free Web Research Module (No API Key Required)

Conducts automatic background research using free public web APIs that are
accessible via any standard internet connection — no browser automation,
no API keys, no login required.

Primary source:  Wikipedia REST API (https://en.wikipedia.org/w/api.php)
Secondary info:  Built-in genre/literary context library

How it works
────────────
1. Extract searchable keywords from the user's novel idea and genre.
2. Search Wikipedia for each keyword and fetch the page text.
3. Assemble a structured research document from the Wikipedia extracts plus
   built-in genre conventions and literary context.
4. If the network is unreachable, return a genre-appropriate offline fallback
   so generation always continues without an error.

TO EXTEND: Add new research sources by adding a _fetch_* function and
           calling it from research_topic().  All sources should return
           plain strings and must never raise — use try/except internally.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

try:
    import requests as _req
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

_WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
_TIMEOUT = 12          # seconds per request
_MAX_EXTRACT = 3500    # characters to take from each Wikipedia article
_MAX_ARTICLES = 3      # maximum Wikipedia articles to fetch per novel

_HEADERS = {
    "User-Agent": (
        "FictionNovelGenerator/2.0 "
        "(free creative writing tool; https://github.com/goanditllc-a11y/fiction-novel-generator)"
    )
}

# ---------------------------------------------------------------------------
# Keyword extraction
# ---------------------------------------------------------------------------

_STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "about", "as", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "that", "this",
    "it", "its", "who", "what", "where", "when", "how", "which",
    "i", "my", "me", "we", "our", "you", "your", "he", "she", "his", "her",
    "they", "their", "can", "not", "no", "up", "so", "into", "out", "want",
    "just", "like", "story", "novel", "book", "character", "plot", "write",
    "writing", "fiction", "generate", "idea", "about",
})


def _extract_keywords(idea: str, genre: str) -> List[str]:
    """
    Returns searchable keyword strings derived from *idea* and *genre*.

    Multi-word phrases (e.g. "1920s Paris") are included first because they
    yield more focused Wikipedia results than individual words.
    """
    # Look for quoted phrases first
    phrases = re.findall(r'"([^"]+)"', idea)

    # Find capitalised two-word pairs (likely proper nouns / places)
    pairs = re.findall(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b', idea)
    phrases.extend(pairs)

    # Individual substantive words
    words = [
        w.lower() for w in re.findall(r'\b[a-zA-Z]{4,}\b', idea)
        if w.lower() not in _STOP_WORDS
    ]

    # Combine, de-duplicate, add genre keyword at the front
    seen: set = set()
    combined: List[str] = []
    genre_key = "science fiction" if genre.lower() == "sci-fi" else genre.lower().replace("-", " ")
    for item in ([genre_key] + phrases + words):
        key = item.lower()
        if key not in seen:
            seen.add(key)
            combined.append(item)

    return combined[:8]


# ---------------------------------------------------------------------------
# Wikipedia helpers
# ---------------------------------------------------------------------------

def _wikipedia_search(query: str) -> Optional[str]:
    """Returns the Wikipedia page title that best matches *query*, or None."""
    try:
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": 3,
            "utf8": 1,
            "srprop": "snippet",
        }
        r = _req.get(_WIKIPEDIA_API, params=params, headers=_HEADERS, timeout=_TIMEOUT)
        r.raise_for_status()
        results = r.json().get("query", {}).get("search", [])
        if results:
            return results[0]["title"]
    except Exception:
        pass
    return None


def _wikipedia_extract(title: str) -> str:
    """Returns the plain-text extract of a Wikipedia page, up to *_MAX_EXTRACT* chars."""
    try:
        params = {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "extracts",
            "explaintext": True,
            "exsectionformat": "plain",
            "redirects": True,
        }
        r = _req.get(_WIKIPEDIA_API, params=params, headers=_HEADERS, timeout=_TIMEOUT)
        r.raise_for_status()
        pages = r.json().get("query", {}).get("pages", {})
        for page in pages.values():
            extract = page.get("extract", "")
            if len(extract) > 100:
                extract = re.sub(r"\n{3,}", "\n\n", extract)
                return extract[:_MAX_EXTRACT].strip()
    except Exception:
        pass
    return ""


# ---------------------------------------------------------------------------
# Genre context library (built-in, always available)
# ---------------------------------------------------------------------------

_GENRE_CONTEXT: dict = {
    "Fantasy": (
        "Fantasy fiction builds immersive secondary worlds with internally consistent rules.\n"
        "Key conventions: magic systems with meaningful costs; epic scope balanced with intimate\n"
        "character moments; archetypal journeys (the Chosen One, the Mentor, the Dark Lord) that\n"
        "reward subversion. World-building details — geography, culture, economics, religion —\n"
        "ground readers in the lived reality of the fictional world.\n\n"
        "Narrative craft notes:\n"
        "• Magic as metaphor for power, knowledge, or identity resonates deeply.\n"
        "• Mountain kingdoms breed isolation and fierce independence; coastal cities foster\n"
        "  trade and moral ambiguity; frontier regions attract those fleeing something.\n"
        "• Antagonists in fantasy work best when they believe they are right — and are\n"
        "  partially correct.\n"
        "• The cost of the heroic choice (what the protagonist sacrifices) determines\n"
        "  the emotional weight of the climax."
    ),
    "Sci-Fi": (
        "Science fiction extrapolates present-day science and technology into plausible futures.\n"
        "Hard SF values scientific accuracy; soft SF prioritises ideas and character psychology.\n"
        "The best SF uses speculative settings to illuminate contemporary human concerns.\n\n"
        "Narrative craft notes:\n"
        "• One central 'what if' pushed to its logical extreme is more powerful than many.\n"
        "• Colonialism and its legacy map powerfully onto interplanetary settings.\n"
        "• Technology solves problems and creates equal-and-opposite new ones.\n"
        "• First-contact stories interrogate what 'human' actually means.\n"
        "• AI characters are most interesting when their alien perspective reveals something\n"
        "  true about human behaviour that humans cannot see themselves."
    ),
    "Mystery": (
        "Mystery fiction is built on a puzzle the reader can solve alongside the detective.\n"
        "Fair-play requires that all clues be available to the reader before the solution.\n"
        "Character is revealed through investigative method, not statement.\n\n"
        "Narrative craft notes:\n"
        "• Red herrings must be genuine misdirections grounded in character, not authorial cheats.\n"
        "• Closed communities (villages, ships, snowbound estates) concentrate suspects and\n"
        "  generate the claustrophobia that mystery requires.\n"
        "• The detective's fatal flaw complicates and deepens the investigation.\n"
        "• Class, money, and secrets are the engines of most fictional motives.\n"
        "• The best mysteries use the crime to expose something true about the social world\n"
        "  in which it occurs."
    ),
    "Romance": (
        "Romance fiction traces the development of an emotional relationship toward a\n"
        "satisfying, earned resolution. Internal obstacles (past wounds, self-doubt,\n"
        "fear of vulnerability) matter as much as external ones.\n\n"
        "Narrative craft notes:\n"
        "• The reader must believe both protagonists are worthy of each other.\n"
        "• Misunderstanding works only when both parties have legitimate reasons\n"
        "  for their misapprehension.\n"
        "• Proximity + conflict is the central mechanism: forced together, they cannot avoid\n"
        "  each other and cannot avoid themselves.\n"
        "• Vulnerability is the engine of both conflict and connection.\n"
        "• The grand gesture works only if it costs the gesturing character something real."
    ),
    "Thriller": (
        "Thriller fiction operates on urgency, escalating stakes, and sustained tension.\n"
        "The protagonist is reactive — acted upon as much as acting.\n"
        "Information is revealed in layers, each revelation raising new questions.\n\n"
        "Narrative craft notes:\n"
        "• Ticking clocks and narrowing options drive pacing.\n"
        "• Trust is a liability until proven otherwise; every character has an agenda.\n"
        "• The most dangerous information is what the antagonist already knows about the hero.\n"
        "• Physical danger and psychological danger must alternate to prevent numbness.\n"
        "• Moral complexity distinguishes literary thrillers from pure action: the protagonist\n"
        "  must make choices that cost them something they value."
    ),
    "Horror": (
        "Horror fiction evokes fear, dread, and the uncanny through violation of the\n"
        "safe and familiar. Psychological horror exploits what the reader brings to the text.\n\n"
        "Narrative craft notes:\n"
        "• Establish normality before disrupting it — the reader needs something to lose.\n"
        "• The unknown is more frightening than the described; implication beats explicitness.\n"
        "• Pacing is crucial: build slowly, release tension in measured bursts.\n"
        "• The best horror uses its terrors as metaphors for real-world fears:\n"
        "  body horror for illness; hauntings for grief; possession for addiction.\n"
        "• Characters who make reasonable decisions in unreasonable situations are more\n"
        "  sympathetic than those who make obviously stupid choices."
    ),
    "Historical Fiction": (
        "Historical fiction combines accurate period detail with invented characters and plots.\n"
        "Research grounds the reader; imagination makes the past live.\n\n"
        "Narrative craft notes:\n"
        "• Characters should think within their historical context while remaining\n"
        "  emotionally accessible to modern readers — anachronism in psychology is\n"
        "  a more serious error than anachronism in material detail.\n"
        "• History is written by survivors; the novel can give voice to those who were not.\n"
        "• Honour is currency in most pre-modern settings — spent carefully, lost quickly.\n"
        "• Every alliance is also a threat held in reserve.\n"
        "• The best historical fiction illuminates present concerns through the lens of the past."
    ),
    "Adventure": (
        "Adventure fiction is defined by physical challenge, exploration, and the test\n"
        "of character under extreme pressure.\n\n"
        "Narrative craft notes:\n"
        "• External journey mirrors internal journey; the physical obstacles are metaphors\n"
        "  for the protagonist's psychological barriers.\n"
        "• Companion dynamics — trust, loyalty, the moment of betrayal — are central.\n"
        "• The physical world is as much a character as the people in it.\n"
        "• What you find is rarely what you came looking for.\n"
        "• Momentum is everything: every chapter should end with a new problem or\n"
        "  a new revelation that makes stopping impossible."
    ),
    "Literary Fiction": (
        "Literary fiction prioritises prose style, psychological depth, and thematic complexity.\n"
        "Character interiority is the primary landscape; plot serves character revelation.\n\n"
        "Narrative craft notes:\n"
        "• Language is used precisely and evocatively — every word choice is intentional.\n"
        "• The interior life must be dramatised through specific sensory detail and\n"
        "  concrete action, not by direct statement of emotion.\n"
        "• Subtext (what characters do not say) is as important as text.\n"
        "• The ordinary contains the extraordinary; the specific illuminates the universal.\n"
        "• Structural experimentation (non-linear time, multiple viewpoints, shifts in register)\n"
        "  should serve the story's emotional and thematic needs, not exist for its own sake."
    ),
    "General": (
        "General fiction draws on conventions from multiple genres, grounding the story\n"
        "in recognisable contemporary or realistic settings.\n\n"
        "Narrative craft notes:\n"
        "• Every character needs a want (external goal) and a need (internal emotional\n"
        "  requirement) that are in tension — the story is the exploration of that gap.\n"
        "• Establish rules for what is possible in your world; maintain them consistently.\n"
        "• Ground scenes in specific, sensory-rich places — vague settings produce vague stories.\n"
        "• The best themes emerge from character action, not authorial statement.\n"
        "• Change is the central requirement: the protagonist at the end must be meaningfully\n"
        "  different from the protagonist at the beginning."
    ),
}

# ---------------------------------------------------------------------------
# Offline fallback research (no network required)
# ---------------------------------------------------------------------------

_OFFLINE_FALLBACK: dict = {
    "Fantasy": (
        "RESEARCH NOTES (offline fallback — built-in genre knowledge)\n\n"
        "Historical context: Medieval European society provides rich source material:\n"
        "feudal hierarchies, knightly codes, monastery culture, guild systems, and the tension\n"
        "between church authority and secular power. Norse and Celtic mythologies offer\n"
        "archetypal figures (Odin/the Wanderer, the Trickster, the Sacrifice-King) and\n"
        "cosmologies that underpin much of the genre's inherited structure.\n\n"
        "World-building: Geography shapes culture profoundly. Mountain kingdoms breed isolation\n"
        "and fierce independence. Coastal cities foster trade and moral ambiguity.\n"
        "Frontier regions attract those fleeing something. The map is an argument about power.\n\n"
        "Character archetypes: The reluctant hero who did not ask for this; the fallen mentor\n"
        "who carries a secret cost; the loyal friend who doubts but stays; the antagonist\n"
        "who was once a protagonist before something broke in them.\n\n"
        "Conflict sources: Succession crises; forbidden knowledge; the return of something\n"
        "thought to have been destroyed; a prophecy that can be read two ways; a betrayal\n"
        "inside the alliance everyone depended on."
    ),
    "Sci-Fi": (
        "RESEARCH NOTES (offline fallback — built-in genre knowledge)\n\n"
        "Scientific foundations: The genre's anxiety traditions mirror real-world scientific\n"
        "development — nuclear power, genetic engineering, artificial intelligence, space travel.\n"
        "Each era's SF reflects the technology that most frightened and fascinated its moment.\n\n"
        "Social extrapolation: Resource scarcity vs. post-scarcity produce radically different\n"
        "social structures. Colonialism's logic maps directly onto interplanetary expansion.\n"
        "Corporate power, surveillance states, and information asymmetry are the genre's\n"
        "defining contemporary anxieties.\n\n"
        "Character types: The pragmatist engineer who has made a compromise they live with;\n"
        "the idealist explorer confronting what they find; the AI that develops in\n"
        "unexpected directions; the bureaucrat who is not evil, only following the logic\n"
        "of a broken system.\n\n"
        "Conflict sources: First contact; rogue AI; colony gone silent; weapon disguised as\n"
        "data; the experiment that succeeded in the wrong direction."
    ),
    "default": (
        "RESEARCH NOTES (offline fallback — built-in genre knowledge)\n\n"
        "Narrative fundamentals: Every character needs a want (external goal) and a need\n"
        "(internal emotional requirement) that are in tension. The story is the exploration\n"
        "of that gap. The protagonist changes by the end — meaningfully and permanently.\n\n"
        "Conflict structure: Establish normality, disrupt it with an inciting incident,\n"
        "escalate complications through the midpoint, bring the protagonist to their lowest\n"
        "point, force a defining choice in the climax, show the consequences.\n\n"
        "Prose principles: Ground scenes in specific sensory detail. Vary sentence length\n"
        "for rhythm. Use concrete nouns and active verbs. Avoid excessive adverbs.\n"
        "Show character through action and specific detail, not by stating qualities directly.\n"
        "Subtext (what characters do not say) is as important as text (what they do say).\n\n"
        "Character complexity: Antagonists should believe they are the hero of their own story\n"
        "and have a coherent justification for every choice they make. Supporting characters\n"
        "need their own lives, goals, and opinions that extend beyond their plot function."
    ),
}


# ---------------------------------------------------------------------------
# Research document builder
# ---------------------------------------------------------------------------

def _build_research_doc(
    idea: str,
    genre: str,
    wiki_results: List[Tuple[str, str]],
) -> str:
    """Assembles Wikipedia extracts and genre context into a structured research document."""
    lines: List[str] = [
        f"RESEARCH NOTES — '{idea[:80]}' ({genre})",
        "=" * 60,
        "",
        "Source: Wikipedia public API (https://en.wikipedia.org).  No API key required.",
        "",
    ]

    if wiki_results:
        lines += ["TOPIC RESEARCH (Wikipedia)", "-" * 40, ""]
        for title, extract in wiki_results:
            if extract:
                lines += [f"■ {title}", "", extract.strip(), ""]

    lines += [
        "GENRE & CRAFT CONTEXT",
        "-" * 40,
        "",
        _GENRE_CONTEXT.get(genre, _GENRE_CONTEXT["General"]),
        "",
        "NOVEL IDEA (original prompt)",
        "-" * 40,
        idea,
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def research_topic(idea: str, genre: str) -> str:
    """
    Conducts web-based research using free public APIs and returns a
    structured research document.

    Requires no API key.  Uses the Wikipedia public API which is freely
    accessible via any internet connection.  If the network is unreachable,
    returns a genre-appropriate offline fallback so generation always proceeds.

    Args:
        idea:  The user's raw novel idea/prompt text.
        genre: The selected genre string (e.g., "Fantasy", "Sci-Fi").

    Returns:
        A multi-section research document as a plain-text string.
        Never raises — always returns usable content.
    """
    if not _REQUESTS_AVAILABLE:
        base = _OFFLINE_FALLBACK.get(genre, _OFFLINE_FALLBACK["default"])
        return base + f"\n\nIdea: {idea}\n"

    keywords = _extract_keywords(idea, genre)
    wiki_results: List[Tuple[str, str]] = []

    for keyword in keywords:
        if len(wiki_results) >= _MAX_ARTICLES:
            break
        title = _wikipedia_search(keyword)
        if not title:
            continue
        # Skip if we already have this article (title normalisation)
        if any(t.lower() == title.lower() for t, _ in wiki_results):
            continue
        extract = _wikipedia_extract(title)
        if extract:
            wiki_results.append((title, extract))

    if not wiki_results:
        # Network unavailable or no results — use offline fallback
        base = _OFFLINE_FALLBACK.get(genre, _OFFLINE_FALLBACK["default"])
        return (
            "RESEARCH NOTES (web search returned no results — using built-in genre knowledge)\n\n"
            + base
            + f"\n\nIdea: {idea}\n"
        )

    return _build_research_doc(idea, genre, wiki_results)
