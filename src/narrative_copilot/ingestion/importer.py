"""
Unified manuscript ingestion module.
Supports Markdown, Plaintext, and DOCX imports with size limits and security validation.
"""

from pathlib import Path

from narrative_copilot.ingestion.docx_importer import DocxImporter
from narrative_copilot.schemas import SourceAnchor, StructuralUnit
from narrative_copilot.schemas.errors import ErrorCode
from narrative_copilot.structure.parser import ManuscriptParser

MAX_IMPORT_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


class IngestionError(Exception):
    def __init__(self, code: ErrorCode, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class ManuscriptImporter:
    """
    Handles manuscript imports from various formats and generates structural units and anchors.
    """

    def __init__(self) -> None:
        self.parser = ManuscriptParser()
        self.docx_importer = DocxImporter()

    def import_text(
        self,
        content: str,
        format_type: str,
        project_id: str,
        revision_id: str,
        title: str | None = None,
        existing_block_ids: list[str] | None = None,
    ) -> tuple[list[StructuralUnit], list[SourceAnchor], str]:
        """
        Import manuscript from string content.
        """
        format_norm = format_type.lower().strip()
        if format_norm in ("md", "markdown"):
            md_text = content
        elif format_norm in ("txt", "plaintext", "text"):
            # Normalize plain text paragraphs
            md_text = content
        else:
            raise IngestionError(
                ErrorCode.UNSUPPORTED_IMPORT_FORMAT,
                f"Unsupported text import format: {format_type}. Expected 'markdown' or 'plaintext'.",
            )

        units, anchors = self.parser.parse_markdown(
            text=md_text,
            project_id=project_id,
            revision_id=revision_id,
            book_title=title,
            existing_block_ids=existing_block_ids,
        )
        return units, anchors, md_text

    def import_file(
        self,
        file_path: str | Path,
        project_id: str,
        revision_id: str,
        title: str | None = None,
    ) -> tuple[list[StructuralUnit], list[SourceAnchor], str]:
        """
        Import manuscript from a file on disk.
        """
        path = Path(file_path)
        if not path.exists():
            raise IngestionError(ErrorCode.PARSING_ERROR, f"File not found: {file_path}")

        file_size = path.stat().st_size
        if file_size > MAX_IMPORT_FILE_SIZE_BYTES:
            raise IngestionError(
                ErrorCode.FILE_TOO_LARGE,
                f"File size {file_size} exceeds maximum allowed {MAX_IMPORT_FILE_SIZE_BYTES} bytes.",
            )

        suffix = path.suffix.lower()
        if suffix in (".md", ".markdown"):
            content = path.read_text(encoding="utf-8")
            return self.import_text(
                content=content,
                format_type="markdown",
                project_id=project_id,
                revision_id=revision_id,
                title=title or path.stem,
            )
        elif suffix in (".txt", ".text"):
            content = path.read_text(encoding="utf-8")
            return self.import_text(
                content=content,
                format_type="plaintext",
                project_id=project_id,
                revision_id=revision_id,
                title=title or path.stem,
            )
        elif suffix == ".docx":
            md_text = self.docx_importer.import_from_file(path)
            return self.import_text(
                content=md_text,
                format_type="markdown",
                project_id=project_id,
                revision_id=revision_id,
                title=title or path.stem,
            )
        else:
            raise IngestionError(
                ErrorCode.UNSUPPORTED_IMPORT_FORMAT,
                f"Unsupported file extension '{suffix}'. Supported: .md, .txt, .docx",
            )
