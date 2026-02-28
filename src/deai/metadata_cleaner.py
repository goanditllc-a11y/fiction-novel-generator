"""MetadataCleaner – strips AI-revealing metadata from DOCX files."""
from typing import List


class MetadataCleaner:
    # Keywords that suggest AI-generated content in metadata
    AI_KEYWORDS = [
        "chatgpt", "openai", "gpt-4", "gpt-3", "claude", "anthropic",
        "gemini", "bard", "copilot", "ai-generated", "artificial intelligence",
        "language model", "llm",
    ]

    # ------------------------------------------------------------------
    def clean_docx_metadata(self, filepath: str) -> List[str]:
        """Clean DOCX metadata and return list of fields that were changed."""
        try:
            from docx import Document
        except ImportError:
            raise ImportError("python-docx is required for metadata cleaning.")

        doc = Document(filepath)
        changed = self.strip_ai_properties(doc)
        doc.save(filepath)
        return changed

    # ------------------------------------------------------------------
    def strip_ai_properties(self, doc) -> List[str]:
        """Remove AI tool references from *doc*'s core properties.

        Returns list of property names that were cleared.
        """
        try:
            from docx.oxml.ns import qn
        except ImportError:
            return []

        props = doc.core_properties
        changed: List[str] = []

        # Fields to clear unconditionally (may reveal authoring tool)
        unconditional = ["last_modified_by"]
        for field in unconditional:
            current = getattr(props, field, None)
            if current:
                try:
                    setattr(props, field, "Author")
                    changed.append(field)
                except Exception:
                    pass

        # Fields to clear if they contain AI keywords
        keyword_fields = ["author", "comments", "description", "keywords", "subject", "title"]
        for field in keyword_fields:
            current = getattr(props, field, None) or ""
            if any(kw in current.lower() for kw in self.AI_KEYWORDS):
                try:
                    if field == "author":
                        setattr(props, field, "Author")
                    else:
                        setattr(props, field, "")
                    changed.append(field)
                except Exception:
                    pass

        # Reset revision number
        try:
            props.revision = 1
            changed.append("revision")
        except Exception:
            pass

        return changed
