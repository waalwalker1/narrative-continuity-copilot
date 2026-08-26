"""
Property-based tests for indexing idempotency.
"""

import pytest

from narrative_copilot.retrieval.elasticsearch_client import ElasticsearchEngine


@pytest.mark.asyncio
async def test_indexing_idempotency_over_mock() -> None:
    es = ElasticsearchEngine()
    es.use_mock = True

    doc = {
        "chunk_id": "proj1_rev1_blk1",
        "project_id": "proj1",
        "revision_id": "rev1",
        "text": "The dragon slept beneath the mountain.",
        "text_vector": [0.1] * 384,
    }

    # Index same document multiple times
    await es.index_chunk(doc)
    await es.index_chunk(doc)
    await es.index_chunk(doc)

    # Document count must remain exactly 1
    matching = [d for d in es._mock_chunks.values() if d["project_id"] == "proj1"]
    assert len(matching) == 1
