"""
Unit tests for stable provenance and re-anchoring engine.
"""

from narrative_copilot.anchors.reanchoring import ReanchoringEngine, compute_text_hash
from narrative_copilot.schemas import SourceAnchor, StructuralUnit, UnitType


def test_reanchoring_exact_match() -> None:
    engine = ReanchoringEngine()
    text = "Arthur had blue eyes."
    anchor = SourceAnchor(
        anchor_id="anc_1",
        project_id="p1",
        revision_id="rev_1",
        chapter_id="c1",
        block_id="blk_1",
        char_start=0,
        char_end=len(text),
        text_hash=compute_text_hash(text),
        normalized_quote=text,
    )

    blocks = [
        StructuralUnit(
            unit_id="blk_1",
            project_id="p1",
            revision_id="rev_2",
            unit_type=UnitType.BLOCK,
            text=text,
        )
    ]

    result = engine.reanchor(anchor, "rev_2", blocks)
    assert result.status == "EXACT_MATCH"
    assert result.confidence == 1.0
    assert result.updated_anchor is not None
    assert result.updated_anchor.revision_id == "rev_2"


def test_reanchoring_prefix_insertion_realigned() -> None:
    engine = ReanchoringEngine()
    quote = "Arthur had blue eyes."
    anchor = SourceAnchor(
        anchor_id="anc_1",
        project_id="p1",
        revision_id="rev_1",
        chapter_id="c1",
        block_id="blk_1",
        char_start=0,
        char_end=len(quote),
        text_hash=compute_text_hash(quote),
        normalized_quote=quote,
    )

    mutated_text = "Early in the morning, Arthur had blue eyes."
    blocks = [
        StructuralUnit(
            unit_id="blk_1",
            project_id="p1",
            revision_id="rev_2",
            unit_type=UnitType.BLOCK,
            text=mutated_text,
        )
    ]

    result = engine.reanchor(anchor, "rev_2", blocks)
    assert result.status == "REALIGNED"
    assert result.confidence >= 0.95
    assert result.updated_anchor is not None
    assert result.updated_anchor.char_start == mutated_text.find(quote)


def test_reanchoring_deleted_block_invalidated() -> None:
    engine = ReanchoringEngine()
    quote = "Arthur had blue eyes."
    anchor = SourceAnchor(
        anchor_id="anc_1",
        project_id="p1",
        revision_id="rev_1",
        chapter_id="c1",
        block_id="blk_1",
        char_start=0,
        char_end=len(quote),
        text_hash=compute_text_hash(quote),
        normalized_quote=quote,
    )

    blocks = [
        StructuralUnit(
            unit_id="blk_other",
            project_id="p1",
            revision_id="rev_2",
            unit_type=UnitType.BLOCK,
            text="Completely different paragraph about the harvest festival.",
        )
    ]

    result = engine.reanchor(anchor, "rev_2", blocks)
    assert result.status == "INVALIDATED"
    assert result.updated_anchor is None
