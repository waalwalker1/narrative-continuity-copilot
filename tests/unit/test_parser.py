"""
Unit tests for structural segmentation and manuscript parsing.
"""

from narrative_copilot.schemas import UnitType
from narrative_copilot.structure.parser import ManuscriptParser, compute_text_hash


def test_markdown_parser_chapters_and_blocks() -> None:
    parser = ManuscriptParser()
    md_text = """# Chapter 1: The Dark Forest

Lord Arthur rode into the gloom. The trees whispered in the chill wind.

He paused by the ancient marker stone to check his map.

***

In the second clearing, Evelyn was already waiting.

# Chapter 2: The Hidden Citadel

They reached the gates by twilight.
"""

    units, anchors = parser.parse_markdown(
        text=md_text,
        project_id="proj_test",
        revision_id="rev_test",
        book_title="Test Chronicle",
    )

    # Verify structural units
    book_units = [u for u in units if u.unit_type == UnitType.BOOK]
    chapter_units = [u for u in units if u.unit_type == UnitType.CHAPTER]
    scene_units = [u for u in units if u.unit_type == UnitType.SCENE]
    block_units = [u for u in units if u.unit_type == UnitType.BLOCK]

    assert len(book_units) == 1
    assert len(chapter_units) == 2
    assert len(scene_units) >= 2
    assert len(block_units) == 4
    assert len(anchors) == 4

    # Verify anchor hashes and quotes
    for anc in anchors:
        assert anc.project_id == "proj_test"
        assert anc.revision_id == "rev_test"
        assert anc.text_hash is not None
        assert len(anc.normalized_quote) > 0


def test_compute_text_hash_stability() -> None:
    h1 = compute_text_hash("  Lord Arthur   Vance  ")
    h2 = compute_text_hash("Lord Arthur Vance")
    assert h1 == h2
