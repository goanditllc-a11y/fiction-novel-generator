"""Tests for AIDetector."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from src.deai.detector import AIDetector


@pytest.fixture
def detector():
    return AIDetector()


AI_TEXT = (
    "It is crucial to delve into the multifaceted landscape of modern fiction. "
    "Furthermore, one must leverage innovative techniques to foster engagement. "
    "In conclusion, the holistic paradigm underscores transformative storytelling."
)

CLEAN_TEXT = (
    "She walked into the room. He looked up from his book. "
    "The fire crackled softly in the hearth. A dog barked somewhere outside. "
    "She sat down without saying a word."
)


def test_ai_score_returns_float(detector):
    score = detector.score_text(AI_TEXT)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_ai_phrases_detected(detector):
    hits = detector.detect_ai_phrases(AI_TEXT)
    assert len(hits) > 0
    for start, end, phrase, category in hits:
        assert isinstance(start, int)
        assert isinstance(end, int)
        assert end > start
        assert isinstance(phrase, str)
        assert isinstance(category, str)


def test_clean_text_scores_lower(detector):
    ai_score = detector.score_text(AI_TEXT)
    clean_score = detector.score_text(CLEAN_TEXT)
    assert ai_score > clean_score


def test_highlight_patterns(detector):
    ranges = detector.highlight_ai_patterns(AI_TEXT)
    assert isinstance(ranges, list)
    assert len(ranges) > 0
    for start, end in ranges:
        assert end > start


def test_empty_text_returns_zero(detector):
    assert detector.score_text("") == 0.0
    assert detector.detect_ai_phrases("") == []
    assert detector.highlight_ai_patterns("") == []


def test_phrase_categories(detector):
    hits = detector.detect_ai_phrases(AI_TEXT)
    categories = {cat for _, _, _, cat in hits}
    # At least one AI phrase category should appear
    assert "ai_phrase" in categories or "formal_transition" in categories
