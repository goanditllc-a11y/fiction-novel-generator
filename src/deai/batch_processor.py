"""BatchProcessor – runs all De-AI steps on a document."""
from typing import Callable, Dict, Any

from src.deai.detector import AIDetector
from src.deai.phrase_cleaner import PhraseCleaner
from src.deai.structure_analyzer import StructureAnalyzer
from src.deai.humanizer import Humanizer

DEFAULT_OPTIONS: Dict[str, bool] = {
    "detect_phrases": True,
    "replace_phrases": True,
    "add_contractions": True,
    "vary_sentence_length": True,
    "vary_sentence_openings": True,
}


class BatchProcessor:
    def __init__(self):
        self._detector = AIDetector()
        self._cleaner = PhraseCleaner()
        self._analyzer = StructureAnalyzer()
        self._humanizer = Humanizer()

    # ------------------------------------------------------------------
    def process_document(
        self,
        text: str,
        options: Dict[str, bool] | None = None,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> tuple[str, Dict[str, Any]]:
        """Run selected De-AI steps.

        Returns
        -------
        (cleaned_text, report_dict)
        """
        opts = {**DEFAULT_OPTIONS, **(options or {})}

        steps = [
            ("detect_phrases",          "Detecting AI phrases …",          None),
            ("replace_phrases",         "Replacing AI phrases …",          None),
            ("add_contractions",        "Adding contractions …",           None),
            ("vary_sentence_openings",  "Varying sentence openings …",     None),
            ("vary_sentence_length",    "Varying sentence lengths …",      None),
        ]
        enabled_steps = [(k, msg) for k, msg, _ in steps if opts.get(k, False)]
        total = len(enabled_steps)

        report: Dict[str, Any] = {
            "original_score": self._detector.score_text(text),
            "changes": [],
        }

        current = text
        for idx, (step_key, msg) in enumerate(enabled_steps):
            if progress_callback:
                progress_callback(idx, total, msg)

            if step_key == "detect_phrases":
                hits = self._detector.detect_ai_phrases(current)
                report["ai_phrase_hits"] = len(hits)
                report["phrases_found"] = [phrase for _, _, phrase, _ in hits]

            elif step_key == "replace_phrases":
                new = self._cleaner.replace_ai_phrases(current)
                if new != current:
                    report["changes"].append("AI phrases replaced")
                    current = new

            elif step_key == "add_contractions":
                new = self._humanizer.add_contractions(current)
                if new != current:
                    report["changes"].append("Contractions added")
                    current = new

            elif step_key == "vary_sentence_openings":
                new = self._humanizer.vary_sentence_openings(current)
                if new != current:
                    report["changes"].append("Sentence openings varied")
                    current = new

            elif step_key == "vary_sentence_length":
                new = self._humanizer.vary_sentence_length(current)
                if new != current:
                    report["changes"].append("Sentence lengths varied")
                    current = new

        if progress_callback:
            progress_callback(total, total, "Scoring final text …")

        report["final_score"] = self._detector.score_text(current)
        report["structure"] = self._analyzer.detect_uniform_structure(current)

        return current, report

    # ------------------------------------------------------------------
    def generate_report(self, report: Dict[str, Any]) -> str:
        lines = [
            "=== De-AI Processing Report ===",
            f"Original AI score : {report.get('original_score', 0):.1%}",
            f"Final AI score    : {report.get('final_score', 0):.1%}",
            f"AI phrases found  : {report.get('ai_phrase_hits', 0)}",
        ]
        changes = report.get("changes", [])
        if changes:
            lines.append("\nChanges applied:")
            for ch in changes:
                lines.append(f"  • {ch}")
        else:
            lines.append("\nNo changes were applied.")

        struct = report.get("structure", {})
        if struct.get("uniform_lengths"):
            lines.append("\n⚠ Sentence lengths are unusually uniform (possible AI pattern).")

        reps = struct.get("repetitive_starts", [])
        if reps:
            lines.append(f"\n⚠ {len(reps)} sentence(s) repeat the same opening word.")

        phrases = report.get("phrases_found", [])
        if phrases:
            unique = sorted(set(phrases))
            lines.append(f"\nPhrases flagged: {', '.join(unique)}")

        return '\n'.join(lines)
