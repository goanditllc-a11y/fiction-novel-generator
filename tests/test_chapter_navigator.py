"""Tests for chapter detection logic (no Qt required)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from src.editor.chapter_navigator import detect_chapters


NUMERIC_TEXT = """
Some opening text.

Chapter 1

The story begins here.

Chapter 2

More story here.

Chapter 10

And so on.
"""

WORD_TEXT = """
Chapter One

The first chapter.

Chapter Two

The second chapter.

Chapter Three

The third chapter.
"""

ROMAN_TEXT = """
Part I

Introduction part.

Part II

Second section.

Part III

Third section.

Part IV

Fourth section.
"""

SPECIAL_TEXT = """
Prologue

Before the story.

Chapter 1

The main story.

Epilogue

After the story.
"""

MIXED_TEXT = """
Prologue

Some intro.

Part One

First part.

Chapter 1

First chapter.

Chapter Two

Second chapter.

Epilogue

The end.
"""


def test_detect_chapter_numbers():
    chapters = detect_chapters(NUMERIC_TEXT)
    headings = [h.lower() for _, h in chapters]
    assert any("chapter 1" in h for h in headings)
    assert any("chapter 2" in h for h in headings)
    assert any("chapter 10" in h for h in headings)
    assert len(chapters) == 3


def test_detect_chapter_words():
    chapters = detect_chapters(WORD_TEXT)
    headings = [h.lower() for _, h in chapters]
    assert any("chapter one" in h for h in headings)
    assert any("chapter two" in h for h in headings)
    assert any("chapter three" in h for h in headings)
    assert len(chapters) == 3


def test_detect_part_roman_numerals():
    chapters = detect_chapters(ROMAN_TEXT)
    headings = [h.lower() for _, h in chapters]
    assert any("part i" in h for h in headings)
    assert any("part ii" in h for h in headings)
    assert any("part iii" in h for h in headings)
    assert len(chapters) >= 3


def test_detect_prologue_epilogue():
    chapters = detect_chapters(SPECIAL_TEXT)
    headings = [h.lower() for _, h in chapters]
    assert any("prologue" in h for h in headings)
    assert any("epilogue" in h for h in headings)
    assert any("chapter 1" in h for h in headings)


def test_detect_mixed_headings():
    chapters = detect_chapters(MIXED_TEXT)
    assert len(chapters) >= 4


def test_chapters_sorted_by_position():
    chapters = detect_chapters(NUMERIC_TEXT)
    positions = [pos for pos, _ in chapters]
    assert positions == sorted(positions)


def test_empty_text():
    assert detect_chapters("") == []


def test_no_chapters():
    plain = "This is just a regular paragraph with no chapter headings at all."
    assert detect_chapters(plain) == []
