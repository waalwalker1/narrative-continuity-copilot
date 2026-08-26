"""
Unit tests for Continuity Reasoning, Candidate Generation, Preconditions, and Output Validation.
"""

import pytest

from narrative_copilot.continuity.engine import ContinuityReasoningEngine
from narrative_copilot.llm.deterministic_fixture import DeterministicFixtureLLMProvider
from narrative_copilot.schemas import (
    ConflictClass,
    FactAssertion,
    NarrativeScope,
    SourceAnchor,
    StoryMemory,
    StructuralUnit,
    UnitType,
)


@pytest.mark.asyncio
async def test_end_to_end_continuity_attribute_conflict() -> None:
    llm = DeterministicFixtureLLMProvider()
    engine = ContinuityReasoningEngine(llm)

    anchor_a = SourceAnchor(
        anchor_id="anc_1",
        project_id="proj_1",
        revision_id="rev_1",
        chapter_id="chap_1",
        block_id="blk_1",
        char_start=0,
        char_end=20,
        text_hash="hash_a",
        normalized_quote="Arthur had blue eyes.",
    )
    anchor_b = SourceAnchor(
        anchor_id="anc_2",
        project_id="proj_1",
        revision_id="rev_1",
        chapter_id="chap_2",
        block_id="blk_2",
        char_start=0,
        char_end=20,
        text_hash="hash_b",
        normalized_quote="Arthur had green eyes.",
    )

    block_a = StructuralUnit(
        unit_id="blk_1",
        project_id="proj_1",
        revision_id="rev_1",
        unit_type=UnitType.BLOCK,
        text="Arthur had blue eyes.",
    )
    block_b = StructuralUnit(
        unit_id="blk_2",
        project_id="proj_1",
        revision_id="rev_1",
        unit_type=UnitType.BLOCK,
        text="Arthur had green eyes.",
    )

    fact_a = FactAssertion(
        fact_id="f1",
        project_id="proj_1",
        revision_id="rev_1",
        subject_entity_id="ent_arthur",
        predicate="eye_color",
        value="blue",
        evidence_anchor_ids=["anc_1"],
    )
    fact_b = FactAssertion(
        fact_id="f2",
        project_id="proj_1",
        revision_id="rev_1",
        subject_entity_id="ent_arthur",
        predicate="eye_color",
        value="green",
        evidence_anchor_ids=["anc_2"],
    )

    memory = StoryMemory(
        project_id="proj_1",
        revision_id="rev_1",
        entities=[],
        facts=[fact_a, fact_b],
        relations=[],
        timeline_events=[],
        world_rules=[],
        story_threads=[],
    )

    alerts = await engine.review_continuity(
        memory=memory,
        anchors=[anchor_a, anchor_b],
        units=[block_a, block_b],
    )

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.conflict_class == ConflictClass.ATTRIBUTE_CONTRADICTION
    assert alert.confidence >= 0.90
    assert alert.evidence_a.anchor_id == "anc_1"
    assert alert.evidence_b.anchor_id == "anc_2"
    assert alert.requires_author_review is True


@pytest.mark.asyncio
async def test_dream_scope_does_not_flag_physical_contradiction() -> None:
    llm = DeterministicFixtureLLMProvider()
    engine = ContinuityReasoningEngine(llm)

    anchor_a = SourceAnchor(
        anchor_id="anc_1",
        project_id="proj_1",
        revision_id="rev_1",
        chapter_id="chap_1",
        block_id="blk_1",
        char_start=0,
        char_end=20,
        text_hash="hash_a",
        normalized_quote="Arthur was an honest blacksmith.",
    )
    anchor_b = SourceAnchor(
        anchor_id="anc_2",
        project_id="proj_1",
        revision_id="rev_1",
        chapter_id="chap_2",
        block_id="blk_2",
        char_start=0,
        char_end=20,
        text_hash="hash_b",
        normalized_quote="In a dream, Arthur was a dark sorcerer.",
    )

    block_a = StructuralUnit(
        unit_id="blk_1",
        project_id="proj_1",
        revision_id="rev_1",
        unit_type=UnitType.BLOCK,
        text="Arthur was an honest blacksmith.",
    )
    block_b = StructuralUnit(
        unit_id="blk_2",
        project_id="proj_1",
        revision_id="rev_1",
        unit_type=UnitType.BLOCK,
        text="In a dream, Arthur was a dark sorcerer.",
    )

    fact_a = FactAssertion(
        fact_id="f1",
        project_id="proj_1",
        revision_id="rev_1",
        subject_entity_id="ent_arthur",
        predicate="profession",
        value="blacksmith",
        narrative_scope=NarrativeScope.GLOBAL_CANON,
        evidence_anchor_ids=["anc_1"],
    )
    fact_b = FactAssertion(
        fact_id="f2",
        project_id="proj_1",
        revision_id="rev_1",
        subject_entity_id="ent_arthur",
        predicate="profession",
        value="sorcerer",
        narrative_scope=NarrativeScope.DREAM_OR_VISION,
        evidence_anchor_ids=["anc_2"],
    )

    memory = StoryMemory(
        project_id="proj_1",
        revision_id="rev_1",
        entities=[],
        facts=[fact_a, fact_b],
        relations=[],
        timeline_events=[],
        world_rules=[],
        story_threads=[],
    )

    alerts = await engine.review_continuity(memory, [anchor_a, anchor_b], [block_a, block_b])
    # Dream vs Reality should not create an unverified physical contradiction alert
    assert len(alerts) == 0
