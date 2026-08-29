"""
Integration test for cross-revision provenance integrity.
Verifies that retained story-memory objects rewrite evidence citations to target-revision anchors,
preventing stale anchor leakage across revision boundaries.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app, db, es_engine


@pytest.mark.asyncio
async def test_cross_revision_evidence_reanchoring() -> None:
    await db.init_db()
    await es_engine.ensure_indices()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create project
        res_proj = await ac.post("/api/v1/projects", json={"title": "Provenance Test Saga"})
        assert res_proj.status_code == 201
        project_id = res_proj.json()["project_id"]

        # 2. Import 2-chapter manuscript
        manuscript_md = (
            "# Chapter 1: The Old Keep\n\n"
            "Arthur Vance had blue eyes.\n\n"
            "# Chapter 2: The High Tower\n\n"
            "Elena had dark brown hair. According to the ancient lore: Magic cannot penetrate solid iron."
        )

        res_imp = await ac.post(
            f"/api/v1/projects/{project_id}/import", json={"content_text": manuscript_md}
        )
        assert res_imp.status_code == 200

        # 3. Full index (Revision 1)
        res_idx1 = await ac.post(
            f"/api/v1/projects/{project_id}/index", json={"incremental": False}
        )
        assert res_idx1.status_code == 200
        rev1_id = res_idx1.json()["revision_id"]

        # 4. Fetch Revision 1 story memory and anchors
        res_mem1 = await ac.get(f"/api/v1/projects/{project_id}/memory?revision_id={rev1_id}")
        assert res_mem1.status_code == 200
        mem1 = res_mem1.json()

        # Capture base anchor IDs
        base_anchor_ids = set()
        for f in mem1["facts"]:
            for aid in f["evidence_anchor_ids"]:
                base_anchor_ids.add(aid)
        for r in mem1["relations"]:
            for aid in r["evidence_anchor_ids"]:
                base_anchor_ids.add(aid)
        for w in mem1["world_rules"]:
            for aid in w["evidence_anchor_ids"]:
                base_anchor_ids.add(aid)

        assert len(base_anchor_ids) > 0

        # 5. Make scoped edit on Chapter 1 (modifying Chapter 1, leaving Chapter 2 untouched)
        new_ch1 = "# Chapter 1: The Old Keep\n\nArthur Vance had green eyes."
        res_edit = await ac.post(
            f"/api/v1/projects/{project_id}/revisions/from-edits",
            json={"chapter_id": "Chapter 1: The Old Keep", "chapter_content_markdown": new_ch1},
        )
        assert res_edit.status_code == 200
        rev2_id = res_edit.json()["revision_id"]

        # 6. Incremental index on Revision 2
        res_idx2 = await ac.post(
            f"/api/v1/projects/{project_id}/index",
            json={"revision_id": rev2_id, "incremental": True},
        )
        assert res_idx2.status_code == 200

        # 7. Fetch Revision 2 story memory
        res_mem2 = await ac.get(f"/api/v1/projects/{project_id}/memory?revision_id={rev2_id}")
        assert res_mem2.status_code == 200
        mem2 = res_mem2.json()

        # 8. Assertions:
        # Every evidence anchor referenced in Revision 2 must NOT be from Revision 1's anchor pool
        rev2_anchors_referenced = set()
        for f in mem2["facts"]:
            for aid in f["evidence_anchor_ids"]:
                rev2_anchors_referenced.add(aid)
                assert aid not in base_anchor_ids, (
                    f"Stale Revision 1 anchor {aid} leaked into Revision 2 fact!"
                )
        for r in mem2["relations"]:
            for aid in r["evidence_anchor_ids"]:
                rev2_anchors_referenced.add(aid)
                assert aid not in base_anchor_ids, (
                    f"Stale Revision 1 anchor {aid} leaked into Revision 2 relation!"
                )
        for w in mem2["world_rules"]:
            for aid in w["evidence_anchor_ids"]:
                rev2_anchors_referenced.add(aid)
                assert aid not in base_anchor_ids, (
                    f"Stale Revision 1 anchor {aid} leaked into Revision 2 rule!"
                )

        # Retained objects from untouched Chapter 2 should have non-empty valid evidence
        assert len(mem2["facts"]) > 0
