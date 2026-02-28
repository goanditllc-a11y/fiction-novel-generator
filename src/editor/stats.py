"""Text statistics helpers."""


class TextStats:
    WORDS_PER_PAGE = 250

    def count_words(self, text: str) -> int:
        return len(text.split()) if text.strip() else 0

    def count_chars(self, text: str) -> int:
        return len(text)

    def count_pages(self, text: str) -> float:
        words = self.count_words(text)
        return round(words / self.WORDS_PER_PAGE, 1)

    def get_stats_string(self, text: str) -> str:
        w = self.count_words(text)
        c = self.count_chars(text)
        p = self.count_pages(text)
        return f"Words: {w:,}  |  Characters: {c:,}  |  Pages: {p}"
