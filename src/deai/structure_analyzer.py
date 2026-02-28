"""StructureAnalyzer – sentence-level structural heuristics."""
import re
from typing import Dict, List, Any


def _split_sentences(text: str) -> List[str]:
    """Basic sentence splitter (handles ., !, ?)."""
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]


class StructureAnalyzer:
    # ------------------------------------------------------------------
    def analyze_sentence_lengths(self, text: str) -> Dict[str, Any]:
        sentences = _split_sentences(text)
        if not sentences:
            return {"count": 0, "mean": 0.0, "min": 0, "max": 0, "std_dev": 0.0, "sentences": []}
        lengths = [len(s.split()) for s in sentences]
        mean = sum(lengths) / len(lengths)
        variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
        std_dev = variance ** 0.5
        return {
            "count": len(sentences),
            "mean": round(mean, 2),
            "min": min(lengths),
            "max": max(lengths),
            "std_dev": round(std_dev, 2),
            "sentences": list(zip(sentences, lengths)),
        }

    # ------------------------------------------------------------------
    def detect_repetitive_starts(self, text: str) -> List[Dict[str, Any]]:
        """Flag sentences that begin with the same word as their predecessor."""
        sentences = _split_sentences(text)
        issues = []
        for i in range(1, len(sentences)):
            prev_word = sentences[i - 1].split()[0].lower().rstrip('.,!?') if sentences[i - 1].split() else ""
            curr_word = sentences[i].split()[0].lower().rstrip('.,!?') if sentences[i].split() else ""
            if prev_word and curr_word == prev_word:
                issues.append({
                    "index": i,
                    "sentence": sentences[i],
                    "repeated_word": curr_word,
                })
        return issues

    # ------------------------------------------------------------------
    def detect_uniform_structure(self, text: str) -> Dict[str, Any]:
        """Detect suspiciously uniform sentence patterns."""
        stats = self.analyze_sentence_lengths(text)
        sentences = _split_sentences(text)

        # Count sentences starting with common AI-pattern words
        ai_starters = ["the", "this", "these", "it", "in", "as", "by", "for", "with"]
        starter_counts: Dict[str, int] = {}
        for s in sentences:
            if s:
                first = s.split()[0].lower().rstrip('.,')
                starter_counts[first] = starter_counts.get(first, 0) + 1

        top_starters = sorted(starter_counts.items(), key=lambda x: -x[1])[:5]

        # Uniformity flag: std_dev < 3 words is suspicious for long texts
        uniform = stats["std_dev"] < 3.0 and stats["count"] > 5

        return {
            "uniform_lengths": uniform,
            "std_dev": stats["std_dev"],
            "mean_length": stats["mean"],
            "top_sentence_starters": top_starters,
            "repetitive_starts": self.detect_repetitive_starts(text),
        }

    # ------------------------------------------------------------------
    def try_spacy(self, text: str) -> Dict[str, Any] | None:
        """Use spaCy for richer analysis if available."""
        try:
            import spacy
            try:
                nlp = spacy.load("en_core_web_sm")
            except OSError:
                return None
            doc = nlp(text[:100_000])  # limit for speed
            sent_lengths = [len(list(sent)) for sent in doc.sents]
            if not sent_lengths:
                return None
            mean = sum(sent_lengths) / len(sent_lengths)
            return {
                "spacy_available": True,
                "sentence_count": len(sent_lengths),
                "mean_token_length": round(mean, 2),
            }
        except ImportError:
            return None
