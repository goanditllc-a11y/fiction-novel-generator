"""Humanizer – applies stylistic transforms to make text feel more human."""
import re
from typing import Dict, List

from src.deai.phrase_cleaner import PhraseCleaner, _CONTRACTIONS

_SENTENCE_STARTERS = [
    "The", "A", "An", "He", "She", "They", "We", "I",
    "It", "This", "That", "There", "Here",
]

# Formal → informal opener substitutions
_OPENER_SUBS = {
    "In addition,": "Also,",
    "Furthermore,": "What's more,",
    "Moreover,": "Plus,",
    "Additionally,": "On top of that,",
    "Consequently,": "So,",
    "Therefore,": "So,",
    "Nevertheless,": "Still,",
    "Nonetheless,": "Even so,",
    "However,": "But,",
    "In contrast,": "On the other hand,",
    "As a result,": "So,",
    "In summary,": "In short,",
    "To summarize,": "Simply put,",
    "In conclusion,": "To wrap up,",
    "To conclude,": "All in all,",
}


def _split_sentences(text: str) -> List[str]:
    return re.split(r'(?<=[.!?])\s+', text.strip())


class Humanizer:
    def __init__(self):
        self._cleaner = PhraseCleaner()

    # ------------------------------------------------------------------
    def add_contractions(self, text: str) -> str:
        """Replace formal verb forms with contractions."""
        return self._cleaner.add_contractions(text)

    # ------------------------------------------------------------------
    def vary_sentence_openings(self, text: str) -> str:
        """Substitute stiff formal sentence openers with casual alternatives."""
        result = text
        for formal, casual in _OPENER_SUBS.items():
            pat = re.compile(re.escape(formal), re.IGNORECASE)
            result = pat.sub(casual, result)
        return result

    # ------------------------------------------------------------------
    def vary_sentence_length(self, text: str) -> str:
        """Merge some very short sentences and split some very long ones.

        This is a heuristic – it won't always produce perfect prose.
        """
        sentences = _split_sentences(text)
        if len(sentences) < 3:
            return text

        result_sentences = []
        i = 0
        while i < len(sentences):
            s = sentences[i]
            words = s.split()
            # Merge very short sentence (<= 5 words) with the next one
            if len(words) <= 5 and i + 1 < len(sentences):
                next_s = sentences[i + 1]
                # join with a comma instead of period
                merged = s.rstrip('.!?') + ", " + next_s[0].lower() + next_s[1:]
                result_sentences.append(merged)
                i += 2
                continue
            # Split very long sentence (> 35 words) at a conjunction
            if len(words) > 35:
                split_pos = self._find_split_pos(s)
                if split_pos:
                    result_sentences.append(s[:split_pos].strip())
                    result_sentences.append(s[split_pos:].strip().capitalize())
                    i += 1
                    continue
            result_sentences.append(s)
            i += 1

        return ' '.join(result_sentences)

    @staticmethod
    def _find_split_pos(sentence: str) -> int | None:
        """Return char index to split a long sentence, or None."""
        mid = len(sentence) // 2
        conjunctions = [' and ', ' but ', ' yet ', ' so ', ' for ', ' nor ']
        best = None
        for conj in conjunctions:
            idx = sentence.lower().find(conj, mid - 20)
            if idx != -1:
                if best is None or abs(idx - mid) < abs(best - mid):
                    best = idx + 1  # split after the space before conjunction
        return best

    # ------------------------------------------------------------------
    def check_voice_consistency(self, text: str) -> Dict:
        """Return a report on first/third-person voice consistency."""
        first_person = re.findall(r'\b(I|me|my|mine|myself|we|us|our|ours|ourselves)\b', text)
        third_person = re.findall(r'\b(he|him|his|himself|she|her|hers|herself|'
                                   r'they|them|their|theirs|themselves)\b', text, re.IGNORECASE)
        fp_count = len(first_person)
        tp_count = len(third_person)
        total = fp_count + tp_count

        if total == 0:
            dominant = "unknown"
            consistency = 1.0
        elif fp_count >= tp_count:
            dominant = "first_person"
            consistency = round(fp_count / total, 2)
        else:
            dominant = "third_person"
            consistency = round(tp_count / total, 2)

        return {
            "dominant_voice": dominant,
            "consistency_score": consistency,
            "first_person_count": fp_count,
            "third_person_count": tp_count,
            "mixed": consistency < 0.85 and total > 10,
        }
