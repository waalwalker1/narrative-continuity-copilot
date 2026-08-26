"""
Unit tests for Entity & Alias resolution and merge protection.
"""

from narrative_copilot.entities.resolver import EntityResolver
from narrative_copilot.schemas import CanonicalStatus, Entity


def test_normalize_name_removes_honorifics() -> None:
    resolver = EntityResolver()
    assert resolver.normalize_name("Lord Arthur Vance") == "arthur vance"
    assert resolver.normalize_name("Dr. Helena Cross, MD") == "helena cross md"
    assert resolver.normalize_name("Captain Marcus Thorne") == "marcus thorne"


def test_nickname_similarity() -> None:
    resolver = EntityResolver()
    sim = resolver.calculate_name_similarity("Elizabeth Bennet", "Lizzy Bennet")
    assert sim >= 0.80


def test_false_merge_prevention_different_characters() -> None:
    resolver = EntityResolver()
    # Mr. Darcy vs Georgiana Darcy
    sim = resolver.calculate_name_similarity("Mr. Darcy", "Georgiana Darcy")
    assert sim < 0.85


def test_entity_merge_unifies_aliases_and_anchors() -> None:
    resolver = EntityResolver()
    e1 = Entity(
        entity_id="e1",
        project_id="p1",
        canonical_name="Arthur Vance",
        aliases=["Artie"],
        evidence_anchor_ids=["anc_1"],
    )
    e2 = Entity(
        entity_id="e2",
        project_id="p1",
        canonical_name="Lord Vance",
        aliases=["The Young Lord"],
        evidence_anchor_ids=["anc_2"],
    )

    merged = resolver.merge_entities(e1, [e2])
    assert merged.canonical_name == "Arthur Vance"
    assert "Lord Vance" in merged.aliases
    assert "Artie" in merged.aliases
    assert "anc_1" in merged.evidence_anchor_ids
    assert "anc_2" in merged.evidence_anchor_ids
    assert merged.canonical_status == CanonicalStatus.AUTHOR_CONFIRMED
