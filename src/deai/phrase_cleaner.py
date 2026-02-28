"""PhraseCleaner – replaces AI-typical phrases with human alternatives."""
import re
from typing import List, Tuple, Dict

from src.utils.constants import AI_OVERUSED_PHRASES, HEDGING_PHRASES

# ---------------------------------------------------------------------------
# Built-in replacement suggestions
# ---------------------------------------------------------------------------
_SUGGESTIONS: Dict[str, List[str]] = {
    "delve into": ["explore", "examine", "look into", "dig into"],
    "it's important to note": ["note that", "keep in mind", "remember"],
    "in conclusion": ["to wrap up", "all in all", "finally"],
    "furthermore": ["also", "besides", "what's more", "and"],
    "moreover": ["also", "plus", "on top of that"],
    "it's worth noting": ["note that", "worth mentioning"],
    "dive into": ["get into", "explore", "jump into"],
    "navigate": ["handle", "manage", "work through"],
    "landscape": ["scene", "setting", "world", "environment"],
    "leverage": ["use", "take advantage of", "make use of"],
    "in today's world": ["today", "nowadays", "these days"],
    "crucial": ["key", "vital", "essential", "critical"],
    "foster": ["build", "grow", "encourage", "nurture"],
    "underscores": ["highlights", "shows", "emphasizes"],
    "realm": ["area", "world", "domain", "field"],
    "multifaceted": ["complex", "varied", "many-sided"],
    "holistic": ["overall", "complete", "whole"],
    "paradigm": ["model", "approach", "framework"],
    "synergy": ["teamwork", "collaboration", "combined effect"],
    "tapestry": ["mix", "blend", "fabric"],
    "beacon": ["guide", "light", "symbol"],
    "unwavering": ["steady", "firm", "constant"],
    "testament": ["proof", "sign", "evidence"],
    "groundbreaking": ["new", "pioneering", "novel"],
    "revolutionary": ["radical", "transformative", "new"],
    "transformative": ["life-changing", "powerful", "significant"],
    "cutting-edge": ["latest", "advanced", "modern"],
    "state-of-the-art": ["latest", "advanced", "modern"],
    "robust": ["strong", "solid", "sturdy"],
    "dynamic": ["active", "lively", "energetic"],
    "innovative": ["creative", "new", "fresh"],
    "comprehensive": ["complete", "full", "thorough"],
    "streamline": ["simplify", "speed up", "smooth out"],
    "optimize": ["improve", "fine-tune", "perfect"],
    "utilize": ["use", "employ"],
    "facilitate": ["help", "enable", "support"],
    "demonstrate": ["show", "prove", "display"],
    "implement": ["put in place", "carry out", "apply"],
    "significant": ["major", "big", "important", "notable"],
    "substantial": ["large", "considerable", "major"],
    "somewhat": ["a bit", "slightly", "rather"],
    "arguably": ["one could say", "perhaps", "possibly"],
    "it could be said": ["some say", "one might argue"],
    "perhaps": ["maybe", "possibly"],
    "it seems": ["it looks like", "apparently"],
    "it appears": ["it looks like", "apparently"],
}

# Contractions map: formal → contraction
_CONTRACTIONS: Dict[str, str] = {
    "do not": "don't",
    "does not": "doesn't",
    "did not": "didn't",
    "cannot": "can't",
    "can not": "can't",
    "will not": "won't",
    "would not": "wouldn't",
    "should not": "shouldn't",
    "could not": "couldn't",
    "is not": "isn't",
    "are not": "aren't",
    "was not": "wasn't",
    "were not": "weren't",
    "have not": "haven't",
    "has not": "hasn't",
    "had not": "hadn't",
    "I am": "I'm",
    "you are": "you're",
    "he is": "he's",
    "she is": "she's",
    "it is": "it's",
    "we are": "we're",
    "they are": "they're",
    "I have": "I've",
    "you have": "you've",
    "we have": "we've",
    "they have": "they've",
    "I will": "I'll",
    "you will": "you'll",
    "he will": "he'll",
    "she will": "she'll",
    "we will": "we'll",
    "they will": "they'll",
    "I would": "I'd",
    "you would": "you'd",
    "he would": "he'd",
    "she would": "she'd",
    "we would": "we'd",
    "they would": "they'd",
}


class PhraseCleaner:
    # ------------------------------------------------------------------
    def find_ai_phrases(self, text: str) -> List[Tuple[int, int, str]]:
        """Return list of (start, end, phrase) for AI-typical phrases."""
        results = []
        lower = text.lower()
        all_phrases = AI_OVERUSED_PHRASES + HEDGING_PHRASES
        for phrase in all_phrases:
            pat = re.compile(re.escape(phrase), re.IGNORECASE)
            for m in pat.finditer(lower):
                results.append((m.start(), m.end(), phrase))
        results.sort(key=lambda x: x[0])
        return results

    # ------------------------------------------------------------------
    def get_replacement_suggestions(self, phrase: str) -> List[str]:
        """Return list of human-sounding alternatives for *phrase*."""
        return _SUGGESTIONS.get(phrase.lower(), [])

    # ------------------------------------------------------------------
    def replace_ai_phrases(self, text: str, replacements: Dict[str, str] | None = None) -> str:
        """Replace AI phrases in *text*.

        If *replacements* dict is provided (phrase → replacement), those
        mappings are used; otherwise the first built-in suggestion is used.
        """
        result = text
        # Work backwards through matches to preserve positions
        matches = self.find_ai_phrases(result)
        for start, end, phrase in reversed(matches):
            if replacements and phrase.lower() in {k.lower() for k in replacements}:
                # Find the mapping key (case-insensitive)
                repl = next(v for k, v in replacements.items() if k.lower() == phrase.lower())
            else:
                suggestions = _SUGGESTIONS.get(phrase.lower(), [])
                repl = suggestions[0] if suggestions else phrase
            # Preserve original capitalisation of first letter
            original_fragment = result[start:end]
            if original_fragment and original_fragment[0].isupper():
                repl = repl[0].upper() + repl[1:]
            result = result[:start] + repl + result[end:]
        return result

    # ------------------------------------------------------------------
    def add_contractions(self, text: str) -> str:
        """Replace formal verb forms with contractions."""
        result = text
        for formal, contraction in sorted(_CONTRACTIONS.items(), key=lambda x: -len(x[0])):
            pat = re.compile(re.escape(formal), re.IGNORECASE)
            def _repl(m, c=contraction):
                orig = m.group(0)
                if orig[0].isupper():
                    return c[0].upper() + c[1:]
                return c
            result = pat.sub(_repl, result)
        return result
