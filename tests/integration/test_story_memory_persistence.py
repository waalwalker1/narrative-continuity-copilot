"""
Integration tests for story memory persistence across entities, facts, relations,
timeline events, world rules, and story threads across repository and API.
"""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app, db, es_engine
from narrative_copilot.persistence.db import Database
from narrative_copilot.persistence.repository import Repository
from narrative_copilot.schemas import (
    Entity,
    EntityType,
    FactAssertion,
    ManuscriptProject,
    ManuscriptRevision,
    RelationAssertion,
    StoryThread,
    ThreadStatus,
    TimelineEvent,
    WorldRule,
)


@pytest.mark.asyncio
async def test_full_story_memory_roundtrip_persistence(tmp_path: Path) -> None:
    db_file = tmp_path / "test_mem.db"
    test_db = Database(f"sqlite+aiosqlite:///{db_file}")
    await test_db.init_db()

    async with test_db.session_scope() as session:
        repo = Repository(session)

        # Create Project & Revision
        proj = ManuscriptProject(project_id="proj_mem_test", title="Memory Test Saga")
        await repo.create_project(proj)

        rev = ManuscriptRevision(
            revision_id="rev_mem_test",
            project_id="proj_mem_test",
            source_hash="hash_test",
            word_count=500,
        )
        await repo.create_revision(rev)
        await repo.update_project_active_revision("proj_mem_test", "rev_mem_test")

        # 1. Entities
        entities = [
            Entity(
                entity_id="ent_arthur",
                project_id="proj_mem_test",
                canonical_name="Lord Arthur Vance",
                entity_type=EntityType.CHARACTER,
                aliases=["Artie", "Lord Vance"],
                evidence_anchor_ids=["anc_1"],
            ),
            Entity(
                entity_id="ent_evelyn",
                project_id="proj_mem_test",
                canonical_name="Lady Evelyn Reed",
                entity_type=EntityType.CHARACTER,
                aliases=["Evie"],
                evidence_anchor_ids=["anc_2"],
            ),
        ]
        await repo.save_entities(entities)

        # 2. Facts
        facts = [
            FactAssertion(
                fact_id="fact_1",
                project_id="proj_mem_test",
                revision_id="rev_mem_test",
                subject_entity_id="ent_arthur",
                predicate="eye_color",
                value="blue",
                normalized_value="blue",
                evidence_anchor_ids=["anc_1"],
            )
        ]
        await repo.save_facts(facts)

        # 3. Relations
        relations = [
            RelationAssertion(
                relation_id="rel_1",
                project_id="proj_mem_test",
                revision_id="rev_mem_test",
                subject_entity_id="ent_arthur",
                relation_type="sibling_of",
                object_entity_id="ent_evelyn",
                evidence_anchor_ids=["anc_1", "anc_2"],
            )
        ]
        await repo.save_relations(relations)

        # 4. Timeline Events
        events = [
            TimelineEvent(
                event_id="ev_1",
                project_id="proj_mem_test",
                revision_id="rev_mem_test",
                title="The Oath of Oakvale",
                summary="Arthur and Evelyn take the knightly oath together.",
                sequence_position=1,
                participant_entity_ids=["ent_arthur", "ent_evelyn"],
                evidence_anchor_ids=["anc_1"],
            )
        ]
        await repo.save_timeline_events(events)

        # 5. World Rules
        rules = [
            WorldRule(
                rule_id="rule_1",
                project_id="proj_mem_test",
                revision_id="rev_mem_test",
                rule_statement="Magic cannot penetrate solid iron.",
                scope="GLOBAL",
                exceptions=["meteoric starmetal"],
                evidence_anchor_ids=["anc_1"],
            )
        ]
        await repo.save_world_rules(rules)

        # 6. Story Threads
        threads = [
            StoryThread(
                thread_id="th_1",
                project_id="proj_mem_test",
                revision_id="rev_mem_test",
                description="The mystery of the stolen signet ring",
                introduced_at_anchor="anc_1",
                status=ThreadStatus.OPEN,
                related_entity_ids=["ent_arthur"],
                update_anchor_ids=["anc_1"],
            )
        ]
        await repo.save_story_threads(threads)

    # Re-open fresh session to verify persistent retrieval
    async with test_db.session_scope() as session2:
        repo2 = Repository(session2)

        loaded_entities = await repo2.get_entities("proj_mem_test")
        assert len(loaded_entities) == 2
        assert loaded_entities[0].canonical_name == "Lord Arthur Vance"

        loaded_facts = await repo2.get_facts("rev_mem_test")
        assert len(loaded_facts) == 1
        assert loaded_facts[0].predicate == "eye_color"

        loaded_relations = await repo2.get_relations("rev_mem_test")
        assert len(loaded_relations) == 1
        assert loaded_relations[0].relation_type == "sibling_of"
        assert loaded_relations[0].object_entity_id == "ent_evelyn"

        loaded_events = await repo2.get_timeline_events("rev_mem_test")
        assert len(loaded_events) == 1
        assert loaded_events[0].title == "The Oath of Oakvale"
        assert "ent_arthur" in loaded_events[0].participant_entity_ids

        loaded_rules = await repo2.get_world_rules("rev_mem_test")
        assert len(loaded_rules) == 1
        assert loaded_rules[0].rule_statement == "Magic cannot penetrate solid iron."
        assert loaded_rules[0].exceptions == ["meteoric starmetal"]

        loaded_threads = await repo2.get_story_threads("rev_mem_test")
        assert len(loaded_threads) == 1
        assert loaded_threads[0].status == ThreadStatus.OPEN
        assert loaded_threads[0].description == "The mystery of the stolen signet ring"


@pytest.mark.asyncio
async def test_api_memory_endpoint_returns_all_models() -> None:
    await db.init_db()
    await es_engine.ensure_indices()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/projects", json={"title": "Endpoint Memory Test"})
        assert res.status_code == 201
        proj_id = res.json()["project_id"]

        sample_md = (
            "# Chapter 1: The Beginning\n\n"
            "Lord Arthur Vance had blue eyes. According to the ancient law: Magic cannot penetrate solid iron."
        )
        await ac.post(f"/api/v1/projects/{proj_id}/import", json={"content_text": sample_md})
        await ac.post(f"/api/v1/projects/{proj_id}/index", json={})

        res_mem = await ac.get(f"/api/v1/projects/{proj_id}/memory")
        assert res_mem.status_code == 200
        mem = res_mem.json()

        assert "entities" in mem
        assert "facts" in mem
        assert "relations" in mem
        assert "timeline_events" in mem
        assert "world_rules" in mem
        assert "story_threads" in mem
        assert len(mem["entities"]) >= 1
        assert len(mem["facts"]) >= 1


@pytest.mark.asyncio
async def test_memory_search_retrieves_all_six_types() -> None:
    """Verifies that Elasticsearch MEMORY_INDEX indexes and retrieves entities, facts, relations, timeline events, world rules, and story threads."""
    await db.init_db()
    await es_engine.ensure_indices()

    proj_id = "proj_6_types_test"
    rev_id = "rev_6_types_test"

    unit_vec = [1.0] + [0.0] * 383
    memory_docs = [
        {
            "doc_id": "ent_1",
            "project_id": proj_id,
            "revision_id": rev_id,
            "memory_type": "entity",
            "subject_entity_id": "ent_1",
            "canonical_text": "Lord Arthur Vance: Lord of Castle Oakvale Artie",
            "vector": unit_vec,
            "entity_ids": ["ent_1"],
            "aliases": ["Artie"],
            "temporal_scope": "GLOBAL",
            "narrative_scope": "GLOBAL_CANON",
            "canonical_status": "PROPOSED",
            "evidence_anchor_ids": ["anc_1"],
        },
        {
            "doc_id": "fact_1",
            "project_id": proj_id,
            "revision_id": rev_id,
            "memory_type": "fact",
            "subject_entity_id": "ent_1",
            "canonical_text": "eye_color: blue",
            "vector": unit_vec,
            "entity_ids": ["ent_1"],
            "aliases": [],
            "temporal_scope": "GLOBAL",
            "narrative_scope": "GLOBAL_CANON",
            "canonical_status": "PROPOSED",
            "evidence_anchor_ids": ["anc_1"],
        },
        {
            "doc_id": "rel_1",
            "project_id": proj_id,
            "revision_id": rev_id,
            "memory_type": "relation",
            "subject_entity_id": "ent_1",
            "canonical_text": "ent_1 sister_of ent_2",
            "vector": unit_vec,
            "entity_ids": ["ent_1", "ent_2"],
            "aliases": [],
            "temporal_scope": "GLOBAL",
            "narrative_scope": "GLOBAL_CANON",
            "canonical_status": "OBSERVED",
            "evidence_anchor_ids": ["anc_1"],
        },
        {
            "doc_id": "event_1",
            "project_id": proj_id,
            "revision_id": rev_id,
            "memory_type": "timeline_event",
            "subject_entity_id": "ent_1",
            "canonical_text": "Battle at the Siege of Dunhaven (Order: 1)",
            "vector": unit_vec,
            "entity_ids": ["ent_1"],
            "aliases": [],
            "temporal_scope": "1",
            "narrative_scope": "GLOBAL_CANON",
            "canonical_status": "OBSERVED",
            "evidence_anchor_ids": ["anc_1"],
        },
        {
            "doc_id": "rule_1",
            "project_id": proj_id,
            "revision_id": rev_id,
            "memory_type": "world_rule",
            "subject_entity_id": "world_rule",
            "canonical_text": "Magic cannot penetrate solid iron (Exceptions: starmetal)",
            "vector": unit_vec,
            "entity_ids": [],
            "aliases": [],
            "temporal_scope": "GLOBAL",
            "narrative_scope": "GLOBAL_CANON",
            "canonical_status": "AUTHOR_CONFIRMED",
            "evidence_anchor_ids": ["anc_1"],
        },
        {
            "doc_id": "thread_1",
            "project_id": proj_id,
            "revision_id": rev_id,
            "memory_type": "story_thread",
            "subject_entity_id": "story_thread",
            "canonical_text": "Lost Crown of Dunhaven: Unresolved quest (Status: OPEN)",
            "vector": unit_vec,
            "entity_ids": ["ent_1"],
            "aliases": [],
            "temporal_scope": "GLOBAL",
            "narrative_scope": "GLOBAL_CANON",
            "canonical_status": "OPEN",
            "evidence_anchor_ids": ["anc_1"],
        },
    ]

    await es_engine.index_memory_bulk(memory_docs)

    # 1. Search for entity
    res_ent = await es_engine.search_memory(
        "Arthur Vance", project_id=proj_id, revision_id=rev_id, memory_types=["entity"]
    )
    assert len(res_ent) >= 1

    # 2. Search for fact
    res_fact = await es_engine.search_memory(
        "blue", project_id=proj_id, revision_id=rev_id, memory_types=["fact"]
    )
    assert len(res_fact) >= 1

    # 3. Search for relation
    res_rel = await es_engine.search_memory(
        "sister_of", project_id=proj_id, revision_id=rev_id, memory_types=["relation"]
    )
    assert len(res_rel) >= 1

    # 4. Search for timeline event
    res_event = await es_engine.search_memory(
        "Dunhaven", project_id=proj_id, revision_id=rev_id, memory_types=["timeline_event"]
    )
    assert len(res_event) >= 1

    # 5. Search for world rule
    res_rule = await es_engine.search_memory(
        "penetrate solid iron",
        project_id=proj_id,
        revision_id=rev_id,
        memory_types=["world_rule"],
    )
    assert len(res_rule) >= 1

    # 6. Search for story thread
    res_thread = await es_engine.search_memory(
        "Lost Crown", project_id=proj_id, revision_id=rev_id, memory_types=["story_thread"]
    )
    assert len(res_thread) >= 1
