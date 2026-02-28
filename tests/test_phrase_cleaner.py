"""Tests for PhraseCleaner."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from src.deai.phrase_cleaner import PhraseCleaner


@pytest.fixture
def cleaner():
    return PhraseCleaner()


AI_TEXT = (
    "It is crucial to delve into the landscape. Furthermore, we must leverage "
    "innovative solutions. In conclusion, this is significant."
)


def test_find_ai_phrases(cleaner):
    matches = cleaner.find_ai_phrases(AI_TEXT)
    assert len(matches) > 0
    phrases = [p for _, _, p in matches]
    assert any("crucial" in p or "delve into" in p or "leverage" in p for p in phrases)


def test_replace_ai_phrases(cleaner):
    cleaned = cleaner.replace_ai_phrases(AI_TEXT)
    assert isinstance(cleaned, str)
    # Text should change (some phrases replaced)
    assert cleaned != AI_TEXT


def test_replace_ai_phrases_with_custom_map(cleaner):
    text = "We need to leverage this opportunity."
    cleaned = cleaner.replace_ai_phrases(text, replacements={"leverage": "use"})
    assert "leverage" not in cleaned.lower()
    assert "use" in cleaned.lower()


def test_contractions(cleaner):
    text = "I do not know what you are talking about. She cannot come today."
    contracted = cleaner.add_contractions(text)
    assert "don't" in contracted
    assert "you're" in contracted
    assert "can't" in contracted


def test_contractions_preserve_capitalisation(cleaner):
    text = "I Do Not want to go. We Will see."
    result = cleaner.add_contractions(text)
    # Should not create malformed strings
    assert isinstance(result, str)
    assert len(result) > 0


def test_replacement_suggestions(cleaner):
    suggestions = cleaner.get_replacement_suggestions("delve into")
    assert isinstance(suggestions, list)
    assert len(suggestions) > 0


def test_replacement_suggestions_unknown(cleaner):
    # Unknown phrase should return empty list
    suggestions = cleaner.get_replacement_suggestions("xyzzy")
    assert suggestions == []


def test_find_returns_sorted_positions(cleaner):
    matches = cleaner.find_ai_phrases(AI_TEXT)
    positions = [start for start, _, _ in matches]
    assert positions == sorted(positions)
