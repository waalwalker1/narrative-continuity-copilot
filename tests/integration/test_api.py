"""
Integration tests for FastAPI REST endpoints.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app


@pytest.mark.asyncio
async def test_api_health_and_readiness() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_health = await ac.get("/health")
        assert res_health.status_code == 200
        assert res_health.json() == {"status": "ok"}

        res_ready = await ac.get("/ready")
        assert res_ready.status_code == 200
        data = res_ready.json()
        assert data["status"] == "ready"
        assert "embedding_provider" in data


@pytest.mark.asyncio
async def test_full_api_author_workflow() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create Project
        res = await ac.post(
            "/api/v1/projects",
            json={"title": "The Whispering Pines", "genre_hint": "Mystery"},
        )
        assert res.status_code == 201
        proj = res.json()
        project_id = proj["project_id"]

        # 2. Import Manuscript
        sample_md = (
            "# Chapter 1: The First Encounter\n\n"
            "Lord Arthur Vance was thirty years old. Arthur had blue eyes.\n\n"
            "# Chapter 2: The Truth Revealed\n\n"
            "Arthur Vance had green eyes."
        )
        res_import = await ac.post(
            f"/api/v1/projects/{project_id}/import",
            json={"format": "markdown", "content_text": sample_md},
        )
        assert res_import.status_code == 200
        assert res_import.json()["units_count"] > 0

        # 3. Index Project
        res_idx = await ac.post(f"/api/v1/projects/{project_id}/index", json={})
        assert res_idx.status_code == 200
        assert res_idx.json()["status"] == "READY"

        # 4. Retrieve Evidence
        res_ret = await ac.post(
            f"/api/v1/projects/{project_id}/retrieve",
            json={"query": "Arthur eyes", "project_id": project_id},
        )
        assert res_ret.status_code == 200
        assert len(res_ret.json()["results"]) > 0

        # 5. Run Continuity Check
        res_check = await ac.post(f"/api/v1/projects/{project_id}/continuity/check")
        assert res_check.status_code == 200
        alerts = res_check.json()
        assert len(alerts) >= 1
        alert_id = alerts[0]["alert_id"]

        # 6. Apply Author Decision (Mark Intentional)
        res_dec = await ac.post(
            f"/api/v1/projects/{project_id}/continuity/alerts/{alert_id}/decision",
            json={"action_type": "MARK_INTENTIONAL", "author_notes": "Magical glamour effect."},
        )
        assert res_dec.status_code == 200
        assert res_dec.json()["status"] == "success"

        # 7. Verify Alert is Suppressed / Intentional
        res_alerts = await ac.get(f"/api/v1/projects/{project_id}/continuity/alerts")
        assert res_alerts.status_code == 200
        saved_alerts = res_alerts.json()
        target_alert = next(a for a in saved_alerts if a["alert_id"] == alert_id)
        assert target_alert["canonical_status"] == "INTENTIONAL_CONTRADICTION"
        assert target_alert["suppressed"] is True
