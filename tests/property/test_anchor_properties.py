"""
Property-based tests for anchor invariants using Hypothesis.
"""

from hypothesis import given
from hypothesis import strategies as st

from narrative_copilot.anchors.reanchoring import compute_text_hash
from narrative_copilot.structure.parser import ManuscriptParser


@given(st.text(min_size=1, max_size=500))
def test_text_hash_deterministic_property(text: str) -> None:
    h1 = compute_text_hash(text)
    h2 = compute_text_hash(text)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex string length


@given(
    st.lists(
        st.text(
            alphabet=st.characters(blacklist_categories=("Cc", "Cs", "Zl", "Zp")),
            min_size=5,
            max_size=100,
        ),
        min_size=1,
        max_size=10,
    )
)
def test_parser_block_count_invariant(paragraphs: list[str]) -> None:
    # Filter out empty or whitespace-only paragraphs
    cleaned = [p.strip() for p in paragraphs if p.strip()]
    cleaned = [p for p in cleaned if p]
    if not cleaned:
        return

    md_content = "\n\n".join(cleaned)
    parser = ManuscriptParser()
    units, anchors = parser.parse_markdown(
        text=md_content,
        project_id="prop_proj",
        revision_id="prop_rev",
    )

    block_units = [u for u in units if u.unit_type.value == "block"]
    assert len(block_units) == len(anchors)
    assert len(anchors) == len(cleaned)
