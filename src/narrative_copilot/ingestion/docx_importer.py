"""
DOCX importer using python-docx.
Extracts headings, paragraphs, and scene separators into normalized manuscript structures.
"""

import io
from pathlib import Path


class DocxImporter:
    """
    Extracts text from DOCX documents and normalizes them into Markdown for structural parsing.
    """

    def import_from_bytes(self, data: bytes) -> str:
        """Parse DOCX byte stream into normalized markdown."""
        try:
            from docx import Document
        except ImportError:
            raise ImportError(
                "python-docx package is required for DOCX manuscript import. Install via `pip install python-docx`."
            )

        file_stream = io.BytesIO(data)
        doc = Document(file_stream)
        lines: list[str] = []

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            style_name = p.style.name.lower() if p.style else ""

            if "heading 1" in style_name or "title" in style_name:
                lines.append(f"\n# {text}\n")
            elif "heading 2" in style_name:
                lines.append(f"\n## {text}\n")
            elif "heading 3" in style_name:
                lines.append(f"\n### {text}\n")
            elif text in ("***", "* * *", "---", "### Scene"):
                lines.append("\n***\n")
            else:
                lines.append(f"{text}\n")

        return "\n".join(lines)

    def import_from_file(self, file_path: str | Path) -> str:
        """Parse DOCX file path into normalized markdown."""
        with open(file_path, "rb") as f:
            return self.import_from_bytes(f.read())
