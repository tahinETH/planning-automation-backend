import os

os.environ["DATABASE_PATH"] = "/tmp/selsa-planlama-feedback-test.sqlite"
os.environ["UPLOAD_DIR"] = "/tmp/selsa-planlama-feedback-uploads"
os.environ["ADMIN_PASSWORD"] = "test-password"
os.environ["APP_SESSION_SECRET"] = "test-session-secret-that-is-long-enough"

from fastapi.testclient import TestClient

from app.database import connection
from app.main import app


def _scenario(index: int) -> dict:
    return {
        "id": f"scenario-{index}",
        "name": f"Senaryo {index}",
        "createdAt": f"2026-08-{index + 1:02d}T10:00:00Z",
        "notes": f"Not {index}",
        "seed": {"orders": [], "activePlanRun": {"optimizationGoal": "balanced", "startDate": "2026-08-01", "endDate": "2026-08-31"}},
        "result": {"summary": {"plannedBatchCount": index + 2}, "planRun": {"optimizationGoal": "balanced", "startDate": "2026-08-01", "endDate": "2026-08-31"}},
    }


def test_scenario_list_is_paginated_and_full_body_is_loaded_by_id():
    with TestClient(app) as client:
        with connection() as db:
            db.execute("DELETE FROM scenarios")
        login = client.post("/api/auth/login", json={"password": "test-password"})
        headers = {"Authorization": f"Bearer {login.json()['token']}"}
        for index in range(3):
            assert client.post("/api/scenarios", headers=headers, json=_scenario(index)).status_code == 201

        first_page = client.get("/api/scenarios/list?limit=2&offset=0", headers=headers)
        assert first_page.status_code == 200
        payload = first_page.json()
        assert payload["total"] == 3
        assert payload["hasMore"] is True
        assert [item["id"] for item in payload["items"]] == ["scenario-2", "scenario-1"]
        assert payload["items"][0]["plannedBatchCount"] == 4
        assert "seed" not in payload["items"][0]
        assert "result" not in payload["items"][0]

        second_page = client.get("/api/scenarios/list?limit=2&offset=2", headers=headers).json()
        assert second_page["hasMore"] is False
        assert [item["id"] for item in second_page["items"]] == ["scenario-0"]

        detail = client.get("/api/scenarios/scenario-2", headers=headers)
        assert detail.status_code == 200
        assert detail.json()["seed"]["orders"] == []
        assert detail.json()["result"]["summary"]["plannedBatchCount"] == 4
        assert client.get("/api/scenarios/missing", headers=headers).status_code == 404
