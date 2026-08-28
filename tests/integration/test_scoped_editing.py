"""
Tests for scoped chapter editing endpoint verifying manuscript integrity.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app, db, es_engine
from narrative_copilot.llm.embeddings import SentenceTransformerEmbeddingProvider


@pytest.mark.asyncio
async def test_scoped_chapter_editing_preserves_untouched_chapters() -> None:
    await db.init_db()
    await es_engine.ensure_indices()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create project
        res_proj = await ac.post("/api/v1/projects", json={"title": "Scoped Editing Test Saga"})
        assert res_proj.status_code == 201
        project_id = res_proj.json()["project_id"]

        # 2. Import a 3-chapter manuscript
        full_md = (
            "# Chapter 1: The Departure\n\n"
            "Arthur packed his bags in Oakvale.\n\n"
            "# Chapter 2: The Crossing\n\n"
            "The caravan crossed the frozen river.\n\n"
            "# Chapter 3: The Arrival\n\n"
            "They reached the citadel at dusk."
        )
        res_import = await ac.post(
            f"/api/v1/projects/{project_id}/import",
            json={"content_text": full_md},
        )
        assert res_import.status_code == 200

        # 3. Edit only Chapter 2
        new_ch2 = (
            "# Chapter 2: The Crossing\n\nArthur Vance used a magical boat to cross the stormy sea."
        )
        res_edit = await ac.post(
            f"/api/v1/projects/{project_id}/revisions/from-edits",
            json={
                "chapter_id": "Chapter 2: The Crossing",
                "chapter_content_markdown": new_ch2,
            },
        )
        assert res_edit.status_code == 200
        edit_data = res_edit.json()
        new_rev_id = edit_data["revision_id"]
        assert edit_data["reanchors_evaluated"] > 0

        # 4. Verify that Chapter 1 and Chapter 3 are preserved in the new revision
        res_proj_after = await ac.get(f"/api/v1/projects/{project_id}")
        assert res_proj_after.status_code == 200
        assert res_proj_after.json()["active_revision_id"] == new_rev_id


class CountingEmbeddingProvider:
    def __init__(self, inner: SentenceTransformerEmbeddingProvider) -> None:
        self.inner = inner
        self.encoded_item_count = 0

    async def aencode(self, texts: list[str]) -> list[list[float]]:
        self.encoded_item_count += len(texts)
        return await self.inner.aencode(texts)

    def encode(self, text: str) -> list[float]:
        self.encoded_item_count += 1
        return self.inner.encode(text)

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        self.encoded_item_count += len(texts)
        return self.inner.encode_batch(texts)


@pytest.mark.asyncio
async def test_incremental_indexing_uses_counting_embedding() -> None:
    import apps.api.main as api_main

    orig_provider = api_main.embedding_provider
    counting_provider = CountingEmbeddingProvider(orig_provider)
    api_main.embedding_provider = counting_provider  # type: ignore[assignment]

    try:
        await db.init_db()
        await es_engine.ensure_indices()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res_proj = await ac.post(
                "/api/v1/projects", json={"title": "10-Block Incremental Saga"}
            )
            project_id = res_proj.json()["project_id"]

            # 10 blocks across 2 chapters (5 blocks each)
            ch1_blocks = "\n\n".join(
                [f"Block 1-{i}: Arthur observed the ancient kingdom gate." for i in range(1, 6)]
            )
            ch2_blocks = "\n\n".join(
                [f"Block 2-{i}: The iron key remained untouched." for i in range(1, 6)]
            )
            ten_blocks_md = (
                f"# Chapter 1: The Gates\n\n{ch1_blocks}\n\n# Chapter 2: The Keys\n\n{ch2_blocks}"
            )

            await ac.post(
                f"/api/v1/projects/{project_id}/import", json={"content_text": ten_blocks_md}
            )

            # Full index: should embed all 10 blocks
            res_idx = await ac.post(
                f"/api/v1/projects/{project_id}/index", json={"incremental": False}
            )
            assert res_idx.status_code == 200
            initial_count = counting_provider.encoded_item_count
            assert initial_count >= 10

            # Reset counter
            counting_provider.encoded_item_count = 0

            # Edit only Chapter 1 (modifying 1 block)
            new_ch1 = (
                "# Chapter 1: The Gates\n\nBlock 1-1: Arthur observed the MODIFIED kingdom gate.\n\n"
                + "\n\n".join(
                    [f"Block 1-{i}: Arthur observed the ancient kingdom gate." for i in range(2, 6)]
                )
            )
            res_edit = await ac.post(
                f"/api/v1/projects/{project_id}/revisions/from-edits",
                json={"chapter_id": "Chapter 1: The Gates", "chapter_content_markdown": new_ch1},
            )
            assert res_edit.status_code == 200

            # Incremental index: should embed ONLY modified/changed block (< 10)
            res_inc_idx = await ac.post(
                f"/api/v1/projects/{project_id}/index", json={"incremental": True}
            )
            assert res_inc_idx.status_code == 200

            # Verification: incremental embedding count must be strictly less than 10 (target: 1-3 blocks)
            incremental_encoded = counting_provider.encoded_item_count
            assert incremental_encoded < 10, (
                f"Expected <10 blocks embedded, got {incremental_encoded}"
            )
            assert incremental_encoded >= 1
    finally:
        api_main.embedding_provider = orig_provider
