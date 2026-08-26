"""
Stable provenance and re-anchoring engine.
Preserves citation fidelity and re-aligns anchors across manuscript edits and revisions.
"""

import difflib
import hashlib
from typing import Literal

from pydantic import BaseModel

from narrative_copilot.schemas import SourceAnchor, StructuralUnit, UnitType


class ReanchorResult(BaseModel):
    anchor_id: str
    status: Literal["EXACT_MATCH", "REALIGNED", "TRANSFERRED_BLOCK", "INVALIDATED"]
    confidence: float
    updated_anchor: SourceAnchor | None = None
    reason: str


def compute_text_hash(text: str) -> str:
    """Compute SHA-256 hash of normalized text."""
    normalized = " ".join(text.strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class ReanchoringEngine:
    """
    Re-anchors source citations across manuscript revisions.
    Prioritizes high precision and invalidates low-confidence matches.
    """

    CONFIDENCE_EXACT = 1.0
    CONFIDENCE_SUBSTRING = 0.95
    CONFIDENCE_FUZZY_THRESHOLD = 0.65
    CONFIDENCE_CROSS_BLOCK_THRESHOLD = 0.85

    def reanchor(
        self,
        anchor: SourceAnchor,
        target_revision_id: str,
        target_blocks: list[StructuralUnit],
    ) -> ReanchorResult:
        """
        Re-anchor a single SourceAnchor against the blocks of a target revision.
        """
        # Build block lookup
        blocks_by_id = {b.unit_id: b for b in target_blocks if b.unit_type == UnitType.BLOCK}

        # 1. Exact block ID match
        if anchor.block_id in blocks_by_id:
            target_block = blocks_by_id[anchor.block_id]
            target_text = target_block.text
            target_hash = compute_text_hash(target_text)

            # 1a. Exact text hash match
            if anchor.text_hash == target_hash:
                new_anchor = anchor.model_copy(
                    update={
                        "revision_id": target_revision_id,
                        "chapter_id": target_block.parent_id or anchor.chapter_id,
                    }
                )
                return ReanchorResult(
                    anchor_id=anchor.anchor_id,
                    status="EXACT_MATCH",
                    confidence=self.CONFIDENCE_EXACT,
                    updated_anchor=new_anchor,
                    reason="Block text and hash perfectly preserved.",
                )

            # 1b. Substring match inside modified block
            quote = anchor.normalized_quote.strip()
            if quote and quote in target_text:
                new_start = target_text.find(quote)
                new_end = new_start + len(quote)
                new_anchor = anchor.model_copy(
                    update={
                        "revision_id": target_revision_id,
                        "char_start": new_start,
                        "char_end": new_end,
                        "text_hash": compute_text_hash(quote),
                        "chapter_id": target_block.parent_id or anchor.chapter_id,
                    }
                )
                return ReanchorResult(
                    anchor_id=anchor.anchor_id,
                    status="REALIGNED",
                    confidence=self.CONFIDENCE_SUBSTRING,
                    updated_anchor=new_anchor,
                    reason="Exact quote found at adjusted character offset in block.",
                )

            # 1c. Fuzzy alignment within the same block
            matcher = difflib.SequenceMatcher(None, quote, target_text)
            match = matcher.find_longest_match(0, len(quote), 0, len(target_text))
            if match.size > 0:
                match_ratio = match.size / max(len(quote), 1)
                if match_ratio >= self.CONFIDENCE_FUZZY_THRESHOLD:
                    aligned_quote = target_text[match.b : match.b + match.size]
                    new_anchor = anchor.model_copy(
                        update={
                            "revision_id": target_revision_id,
                            "char_start": match.b,
                            "char_end": match.b + match.size,
                            "normalized_quote": aligned_quote,
                            "text_hash": compute_text_hash(aligned_quote),
                            "chapter_id": target_block.parent_id or anchor.chapter_id,
                        }
                    )
                    return ReanchorResult(
                        anchor_id=anchor.anchor_id,
                        status="REALIGNED",
                        confidence=round(match_ratio, 3),
                        updated_anchor=new_anchor,
                        reason=f"Fuzzy match retained with {match_ratio:.1%} similarity in block.",
                    )

        # 2. Block ID not present or completely altered: search across all blocks
        quote = anchor.normalized_quote.strip()
        best_block: StructuralUnit | None = None
        best_score = 0.0
        best_start = 0
        best_end = 0

        for block in blocks_by_id.values():
            if not quote or not block.text:
                continue

            # Exact quote match in another block (e.g. block split or moved)
            if quote in block.text:
                start = block.text.find(quote)
                best_block = block
                best_score = 0.90
                best_start = start
                best_end = start + len(quote)
                break

            matcher = difflib.SequenceMatcher(None, quote, block.text)
            match = matcher.find_longest_match(0, len(quote), 0, len(block.text))
            if match.size > 0:
                ratio = match.size / max(len(quote), 1)
                if ratio > best_score:
                    best_score = ratio
                    best_block = block
                    best_start = match.b
                    best_end = match.b + match.size

        if best_block and best_score >= self.CONFIDENCE_CROSS_BLOCK_THRESHOLD:
            aligned_quote = best_block.text[best_start:best_end]
            new_anchor = SourceAnchor(
                anchor_id=anchor.anchor_id,
                project_id=anchor.project_id,
                revision_id=target_revision_id,
                chapter_id=best_block.parent_id or anchor.chapter_id,
                scene_id=best_block.parent_id,
                block_id=best_block.unit_id,
                char_start=best_start,
                char_end=best_end,
                text_hash=compute_text_hash(aligned_quote),
                normalized_quote=aligned_quote,
                previous_block_hash=None,
                next_block_hash=None,
            )
            return ReanchorResult(
                anchor_id=anchor.anchor_id,
                status="TRANSFERRED_BLOCK",
                confidence=round(best_score, 3),
                updated_anchor=new_anchor,
                reason=f"Transferred to block {best_block.unit_id} with {best_score:.1%} match.",
            )

        # 3. If confidence is below threshold, invalidate rather than silently drifting
        return ReanchorResult(
            anchor_id=anchor.anchor_id,
            status="INVALIDATED",
            confidence=0.0,
            updated_anchor=None,
            reason="Anchor target was deleted or heavily modified beyond confidence threshold.",
        )

    def reanchor_all(
        self,
        anchors: list[SourceAnchor],
        target_revision_id: str,
        target_blocks: list[StructuralUnit],
    ) -> list[ReanchorResult]:
        """
        Re-anchor a collection of SourceAnchors.
        """
        return [self.reanchor(a, target_revision_id, target_blocks) for a in anchors]
