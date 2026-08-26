"""
Structural segmentation engine for long-form manuscripts.
Decomposes manuscripts into Book -> Part -> Chapter -> Scene -> Block hierarchy.
"""

import hashlib
import re
from uuid import uuid4

from narrative_copilot.schemas import SourceAnchor, StructuralUnit, UnitType


def compute_text_hash(text: str) -> str:
    """Compute SHA-256 hash of normalized text."""
    normalized = " ".join(text.strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class ManuscriptParser:
    """
    Parses long-form prose into structured hierarchical units with stable provenance.
    """

    CHAPTER_PATTERNS = [
        re.compile(r"^#+\s+(?:Chapter|Prologue|Epilogue)\b.*$", re.IGNORECASE),
        re.compile(
            r"^(?:Chapter|Prologue|Epilogue)\s+(?:\d+|[IVXLCDM]+|[A-Za-z]+)(?::.*)?$", re.IGNORECASE
        ),
        re.compile(r"^#+\s+([A-Za-z0-9\s':,-]+)$"),
    ]

    PART_PATTERNS = [
        re.compile(r"^#+\s+Part\s+(?:\d+|[IVXLCDM]+|[A-Za-z]+).*$", re.IGNORECASE),
        re.compile(r"^Part\s+(?:\d+|[IVXLCDM]+|[A-Za-z]+).*$", re.IGNORECASE),
    ]

    SCENE_BREAK_PATTERNS = [
        re.compile(r"^\s*(?:\*\s*\*\s*\*|---\s*---|\* \* \*|### Scene|---)\s*$"),
        re.compile(r"^\s*<scene_break\s*/?>\s*$", re.IGNORECASE),
    ]

    def parse_markdown(
        self,
        text: str,
        project_id: str,
        revision_id: str,
        book_title: str | None = None,
        existing_block_ids: list[str] | None = None,
    ) -> tuple[list[StructuralUnit], list[SourceAnchor]]:
        """
        Parse Markdown manuscript text into a list of StructuralUnits and SourceAnchors.
        """
        units: list[StructuralUnit] = []
        anchors: list[SourceAnchor] = []

        lines = text.splitlines()
        if not lines:
            return units, anchors

        # Book unit (root)
        book_id = str(uuid4())
        total_words = len(text.split())
        units.append(
            StructuralUnit(
                unit_id=book_id,
                project_id=project_id,
                revision_id=revision_id,
                unit_type=UnitType.BOOK,
                parent_id=None,
                ordinal=0,
                title=book_title or "Manuscript",
                text="",
                word_count=total_words,
            )
        )

        current_part_id: str | None = None
        current_chapter_id: str | None = None
        current_scene_id: str | None = None

        chapter_ordinal = 0
        scene_ordinal = 0
        block_ordinal = 0

        # Buffer for paragraphs
        current_para_lines: list[str] = []
        block_id_idx = 0

        def get_next_block_id() -> str:
            nonlocal block_id_idx
            if existing_block_ids and block_id_idx < len(existing_block_ids):
                bid = existing_block_ids[block_id_idx]
            else:
                bid = str(uuid4())
            block_id_idx += 1
            return bid

        def flush_paragraph() -> None:
            nonlocal current_para_lines, block_ordinal
            if not current_para_lines:
                return

            para_text = "\n".join(current_para_lines).strip()
            current_para_lines = []

            if not para_text:
                return

            # Ensure we have a default chapter and scene
            ensure_chapter_and_scene()

            block_id = get_next_block_id()
            words = len(para_text.split())
            block_unit = StructuralUnit(
                unit_id=block_id,
                project_id=project_id,
                revision_id=revision_id,
                unit_type=UnitType.BLOCK,
                parent_id=current_scene_id,
                ordinal=block_ordinal,
                title=None,
                text=para_text,
                word_count=words,
            )
            units.append(block_unit)

            anchor = SourceAnchor(
                anchor_id=str(uuid4()),
                project_id=project_id,
                revision_id=revision_id,
                chapter_id=current_chapter_id or book_id,
                scene_id=current_scene_id,
                block_id=block_id,
                char_start=0,
                char_end=len(para_text),
                text_hash=compute_text_hash(para_text),
                normalized_quote=para_text[:300],
                previous_block_hash=None,
                next_block_hash=None,
            )
            anchors.append(anchor)
            block_ordinal += 1

        def ensure_chapter_and_scene() -> None:
            nonlocal current_chapter_id, current_scene_id, chapter_ordinal, scene_ordinal
            if not current_chapter_id:
                chapter_ordinal += 1
                current_chapter_id = str(uuid4())
                units.append(
                    StructuralUnit(
                        unit_id=current_chapter_id,
                        project_id=project_id,
                        revision_id=revision_id,
                        unit_type=UnitType.CHAPTER,
                        parent_id=current_part_id or book_id,
                        ordinal=chapter_ordinal,
                        title="Chapter 1",
                        text="",
                        word_count=0,
                    )
                )

            if not current_scene_id:
                scene_ordinal += 1
                current_scene_id = str(uuid4())
                units.append(
                    StructuralUnit(
                        unit_id=current_scene_id,
                        project_id=project_id,
                        revision_id=revision_id,
                        unit_type=UnitType.SCENE,
                        parent_id=current_chapter_id,
                        ordinal=scene_ordinal,
                        title=f"Scene {scene_ordinal}",
                        text="",
                        word_count=0,
                    )
                )

        for line in lines:
            stripped = line.strip()

            # Check for empty line separating paragraphs
            if not stripped:
                flush_paragraph()
                continue

            # Check for Part heading
            if any(p.match(stripped) for p in self.PART_PATTERNS):
                flush_paragraph()
                current_part_id = str(uuid4())
                part_title = stripped.lstrip("#").strip()
                units.append(
                    StructuralUnit(
                        unit_id=current_part_id,
                        project_id=project_id,
                        revision_id=revision_id,
                        unit_type=UnitType.PART,
                        parent_id=book_id,
                        ordinal=len([u for u in units if u.unit_type == UnitType.PART]) + 1,
                        title=part_title,
                        text="",
                        word_count=0,
                    )
                )
                current_chapter_id = None
                current_scene_id = None
                continue

            # Check for Chapter heading
            if any(p.match(stripped) for p in self.CHAPTER_PATTERNS):
                flush_paragraph()
                chapter_ordinal += 1
                current_chapter_id = str(uuid4())
                chap_title = stripped.lstrip("#").strip()
                units.append(
                    StructuralUnit(
                        unit_id=current_chapter_id,
                        project_id=project_id,
                        revision_id=revision_id,
                        unit_type=UnitType.CHAPTER,
                        parent_id=current_part_id or book_id,
                        ordinal=chapter_ordinal,
                        title=chap_title,
                        text="",
                        word_count=0,
                    )
                )
                # Reset scene for new chapter
                current_scene_id = None
                scene_ordinal = 0
                continue

            # Check for Scene break
            if any(p.match(stripped) for p in self.SCENE_BREAK_PATTERNS):
                flush_paragraph()
                if not current_chapter_id:
                    ensure_chapter_and_scene()
                scene_ordinal += 1
                current_scene_id = str(uuid4())
                units.append(
                    StructuralUnit(
                        unit_id=current_scene_id,
                        project_id=project_id,
                        revision_id=revision_id,
                        unit_type=UnitType.SCENE,
                        parent_id=current_chapter_id,
                        ordinal=scene_ordinal,
                        title=f"Scene {scene_ordinal}",
                        text="",
                        word_count=0,
                    )
                )
                continue

            current_para_lines.append(line)

        # Flush final paragraph
        flush_paragraph()

        # Update previous and next block hashes for all block anchors
        for i, anchor in enumerate(anchors):
            if i > 0:
                anchor.previous_block_hash = anchors[i - 1].text_hash
            if i < len(anchors) - 1:
                anchor.next_block_hash = anchors[i + 1].text_hash

        return units, anchors
