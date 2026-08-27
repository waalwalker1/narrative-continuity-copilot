"""
Unit tests proving that citation rescue is completely eliminated.
Manuscript memory extraction must reject facts, relations, events, rules, and threads
with unknown citations or missing anchors (e.g. FAKE_ANCHOR_999).
"""

from typing import Any

import pytest

from narrative_copilot.memory.extractor import StoryMemoryExtractor
from narrative_copilot.schemas import (
    Entity,
    EntityType,
    FactAssertion,
    RelationAssertion,
    SourceAnchor,
    StoryMemory,
    StoryThread,
    StructuralUnit,
    ThreadStatus,
    TimelineEvent,
    UnitType,
    WorldRule,
)


class MockLLMProviderForRescueTest:
    def __init__(self, raw_memory: StoryMemory) -> None:
        self.raw_memory = raw_memory

    async def generate_structured(
        self, system_instruction: str, evidence_payload: dict[str, Any], response_model: Any
    ) -> StoryMemory:
        return self.raw_memory


@pytest.mark.asyncio
async def test_strictly_rejects_fake_anchor_and_does_not_rescue() -> None:
    # 1 valid manuscript anchor in the document
    valid_anchor = SourceAnchor(
        anchor_id="real_anchor_valid_001",
        project_id="proj_rescue_test",
        revision_id="rev_1",
        chapter_id="chap_1",
        block_id="blk_1",
        char_start=0,
        char_end=20,
        text_hash="hash1",
        normalized_quote="Arthur had blue eyes.",
    )
    unit = StructuralUnit(
        unit_id="blk_1",
        project_id="proj_rescue_test",
        revision_id="rev_1",
        unit_type=UnitType.BLOCK,
        text="Arthur had blue eyes.",
    )

    # Raw memory proposing:
    # - 1 grounded fact citing real_anchor_valid_001
    # - 1 ungrounded fact citing FAKE_ANCHOR_999
    # - 1 ungrounded fact with empty anchor list []
    # - 1 ungrounded relation citing FAKE_ANCHOR_999
    # - 1 ungrounded timeline event citing FAKE_ANCHOR_999
    # - 1 ungrounded world rule citing FAKE_ANCHOR_999
    # - 1 ungrounded story thread citing FAKE_ANCHOR_999
    raw_memory = StoryMemory(
        project_id="proj_rescue_test",
        revision_id="rev_1",
        entities=[
            Entity(
                entity_id="ent_arthur",
                project_id="proj_rescue_test",
                canonical_name="Lord Arthur Vance",
                entity_type=EntityType.CHARACTER,
                evidence_anchor_ids=["real_anchor_valid_001"],
            )
        ],
        facts=[
            FactAssertion(
                fact_id="fact_grounded",
                project_id="proj_rescue_test",
                revision_id="rev_1",
                subject_entity_id="ent_arthur",
                predicate="eye_color",
                value="blue",
                normalized_value="blue",
                evidence_anchor_ids=["real_anchor_valid_001"],
            ),
            FactAssertion(
                fact_id="fact_fake_anchor",
                project_id="proj_rescue_test",
                revision_id="rev_1",
                subject_entity_id="ent_arthur",
                predicate="hair_color",
                value="red",
                normalized_value="red",
                evidence_anchor_ids=["FAKE_ANCHOR_999"],
            ),
            FactAssertion(
                fact_id="fact_empty_anchor",
                project_id="proj_rescue_test",
                revision_id="rev_1",
                subject_entity_id="ent_arthur",
                predicate="handedness",
                value="left-handed",
                normalized_value="left-handed",
                evidence_anchor_ids=[],
            ),
        ],
        relations=[
            RelationAssertion(
                relation_id="rel_fake_anchor",
                project_id="proj_rescue_test",
                revision_id="rev_1",
                subject_entity_id="ent_arthur",
                relation_type="ally_of",
                object_entity_id="ent_unknown",
                evidence_anchor_ids=["FAKE_ANCHOR_999"],
            )
        ],
        timeline_events=[
            TimelineEvent(
                event_id="ev_fake_anchor",
                project_id="proj_rescue_test",
                revision_id="rev_1",
                title="Fake Event",
                summary="Ungrounded event description",
                evidence_anchor_ids=["FAKE_ANCHOR_999"],
            )
        ],
        world_rules=[
            WorldRule(
                rule_id="rule_fake_anchor",
                project_id="proj_rescue_test",
                revision_id="rev_1",
                rule_statement="Fake world rule",
                scope="GLOBAL",
                evidence_anchor_ids=["FAKE_ANCHOR_999"],
            )
        ],
        story_threads=[
            StoryThread(
                thread_id="th_fake_anchor",
                project_id="proj_rescue_test",
                revision_id="rev_1",
                description="Fake thread",
                introduced_at_anchor="FAKE_ANCHOR_999",
                status=ThreadStatus.OPEN,
                update_anchor_ids=["FAKE_ANCHOR_999"],
            )
        ],
    )

    mock_llm = MockLLMProviderForRescueTest(raw_memory)
    extractor = StoryMemoryExtractor(llm_provider=mock_llm)  # type: ignore[arg-type]

    validated_memory = await extractor.extract_memory(
        project_id="proj_rescue_test",
        revision_id="rev_1",
        units=[unit],
        anchors=[valid_anchor],
    )

    # Invariant: ONLY the genuinely grounded fact survived
    assert len(validated_memory.facts) == 1
    assert validated_memory.facts[0].fact_id == "fact_grounded"
    assert validated_memory.facts[0].evidence_anchor_ids == ["real_anchor_valid_001"]

    # Invariant: No citation rescue fell back to valid_anchor for fake/empty facts
    assert not any(f.fact_id == "fact_fake_anchor" for f in validated_memory.facts)
    assert not any(f.fact_id == "fact_empty_anchor" for f in validated_memory.facts)

    # Invariant: Relations, events, rules, and threads with FAKE_ANCHOR_999 are rejected
    assert len(validated_memory.relations) == 0
    assert len(validated_memory.timeline_events) == 0
    assert len(validated_memory.world_rules) == 0
    assert len(validated_memory.story_threads) == 0
