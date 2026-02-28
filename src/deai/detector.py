"""AIDetector – rule-based AI-text detection. No external API calls."""
import re
from typing import List, Tuple

from src.utils.constants import AI_OVERUSED_PHRASES, HEDGING_PHRASES, FORMAL_TRANSITIONS

# Category labels
CAT_OVERUSED = "ai_phrase"
CAT_HEDGE = "hedge"
CAT_TRANSITION = "formal_transition"


class AIDetector:
    """Score and annotate text for likely AI authorship using heuristics."""

    # ------------------------------------------------------------------
    def detect_ai_phrases(self, text: str) -> List[Tuple[int, int, str, str]]:
        """Return list of (start, end, phrase, category) for flagged spans."""
        results = []
        lower = text.lower()

        phrase_lists = [
            (AI_OVERUSED_PHRASES, CAT_OVERUSED),
            (HEDGING_PHRASES, CAT_HEDGE),
            (FORMAL_TRANSITIONS, CAT_TRANSITION),
        ]
        for phrases, category in phrase_lists:
            for phrase in phrases:
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                for m in pattern.finditer(lower):
                    results.append((m.start(), m.end(), phrase, category))

        results.sort(key=lambda x: x[0])
        return results

    # ------------------------------------------------------------------
    def score_text(self, text: str) -> float:
        """Return a float 0.0–1.0 estimating probability of AI generation."""
        if not text.strip():
            return 0.0

        words = text.split()
        word_count = max(len(words), 1)
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentence_count = max(len(sentences), 1)

        # Factor 1: AI phrase density
        hits = self.detect_ai_phrases(text)
        phrase_score = min(len(hits) / (word_count / 10), 1.0)

        # Factor 2: Sentence-length uniformity (low variance → more AI-like)
        sent_lengths = [len(s.split()) for s in sentences if s.strip()]
        if len(sent_lengths) > 2:
            mean = sum(sent_lengths) / len(sent_lengths)
            variance = sum((l - mean) ** 2 for l in sent_lengths) / len(sent_lengths)
            # High variance is human-like; normalise variance to 0–1 then invert
            uniformity_score = max(0.0, 1.0 - min(variance / 100.0, 1.0))
        else:
            uniformity_score = 0.0

        # Factor 3: Hedge word density
        hedge_count = sum(
            1 for p in HEDGING_PHRASES
            if re.search(re.escape(p), text, re.IGNORECASE)
        )
        hedge_score = min(hedge_count / 5.0, 1.0)

        # Factor 4: Formal transition density
        trans_count = sum(
            1 for p in FORMAL_TRANSITIONS
            if re.search(re.escape(p), text, re.IGNORECASE)
        )
        trans_score = min(trans_count / 5.0, 1.0)

        combined = (
            phrase_score * 0.40
            + uniformity_score * 0.30
            + hedge_score * 0.15
            + trans_score * 0.15
        )
        return round(min(combined, 1.0), 3)

    # ------------------------------------------------------------------
    def highlight_ai_patterns(self, text: str) -> List[Tuple[int, int]]:
        """Return list of (start, end) ranges for all flagged spans."""
        return [(s, e) for s, e, _, _ in self.detect_ai_phrases(text)]
