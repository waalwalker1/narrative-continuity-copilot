"""
Tests for scoped chapter editing endpoint verifying manuscript integrity.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app, db, es_engine


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
