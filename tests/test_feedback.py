import os
from pathlib import Path

os.environ["DATABASE_PATH"] = "/tmp/selsa-planlama-feedback-test.sqlite"
os.environ["UPLOAD_DIR"] = "/tmp/selsa-planlama-feedback-uploads"
os.environ["ADMIN_PASSWORD"] = "test-password"
os.environ["APP_SESSION_SECRET"] = "test-session-secret-that-is-long-enough"

from fastapi.testclient import TestClient

from app.auth import create_test_session
from app.database import connection
from app.main import app


def test_feedback_lifecycle():
    Path(os.environ["DATABASE_PATH"]).unlink(missing_ok=True)
    with TestClient(app) as client:
        assert client.post("/api/auth/login", json={"password": "wrong"}).status_code == 401
        login = client.post("/api/auth/login", json={"password": "test-password"})
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['token']}"}
        user_headers = {"Authorization": f"Bearer {create_test_session('test-password', 'user')}"}
        assert client.get("/api/feedbacks").status_code == 401
        assert client.get("/api/app-updates").status_code == 401
        assert client.get("/api/me", headers=headers).json()["role"] == "admin"
        assert client.get("/api/me", headers=user_headers).json()["role"] == "user"
        assert client.post("/api/app-updates", headers=user_headers, json={"title": "Yetkisiz", "bullets": ["Yayınlanmamalı"]}).status_code == 403
        assert client.post("/api/production-sync/pull", headers=user_headers).status_code == 403
        assert client.post("/api/data-packages/export", headers=user_headers, json={"scope": "settings", "data": {}}).status_code == 403

        update = client.post(
            "/api/app-updates",
            headers=headers,
            json={"title": "Plan ekranı güncellendi", "bullets": ["Termin filtresi eklendi", "Tezgah sıralaması hızlandırıldı"]},
        )
        assert update.status_code == 201
        assert update.json()["seen_at"] is None
        assert client.get("/api/app-updates", headers=headers).json()[0]["bullets"][0] == "Termin filtresi eklendi"
        seen = client.post(f"/api/app-updates/{update.json()['id']}/seen", headers=headers)
        assert seen.status_code == 200
        assert seen.json()["seen_at"] is not None

        created = client.post("/api/feedbacks", headers=headers, json={"body": "C-08 planı kontrol edilmeli", "page_path": "Tezgahlar / C-08", "priority": 1})
        assert created.status_code == 201
        assert created.json()["priority"] == 1
        feedback_id = created.json()["id"]

        commented = client.post(f"/api/feedbacks/{feedback_id}/comments", headers=headers, json={"body": "Hız değerini de kontrol edelim"})
        assert commented.status_code == 201
        assert len(commented.json()["comments"]) == 1

        edited = client.patch(f"/api/feedbacks/{feedback_id}", headers=headers, json={"body": "C-08 kapasitesi kontrol edilmeli"})
        assert edited.json()["body"] == "C-08 kapasitesi kontrol edilmeli"
        assert edited.json()["priority"] == 1

        reprioritized = client.patch(f"/api/feedbacks/{feedback_id}", headers=headers, json={"priority": 3})
        assert reprioritized.status_code == 200
        assert reprioritized.json()["priority"] == 3

        uploaded = client.post(f"/api/feedbacks/{feedback_id}/attachments", headers=headers, files=[("files", ("ekran.png", b"png-data", "image/png"))])
        assert uploaded.status_code == 201
        assert uploaded.json()["attachments"][0]["kind"] == "image"

        voiced = client.post(f"/api/feedbacks/{feedback_id}/attachments", headers=headers, files=[("files", ("not.webm", b"voice-data", "audio/webm"))])
        assert voiced.status_code == 201
        assert {item["kind"] for item in voiced.json()["attachments"]} == {"image", "voice"}

        documented = client.post(
            f"/api/feedbacks/{feedback_id}/attachments",
            headers=headers,
            files=[("files", ("kontrol-notu.docx", b"word-data", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))],
        )
        assert documented.status_code == 201
        assert {item["kind"] for item in documented.json()["attachments"]} == {"image", "voice", "document"}

        unsupported = client.post(
            f"/api/feedbacks/{feedback_id}/attachments",
            headers=headers,
            files=[("files", ("calistir.exe", b"binary", "application/octet-stream"))],
        )
        assert unsupported.status_code == 415

        resolved = client.patch(f"/api/feedbacks/{feedback_id}", headers=headers, json={"status": "resolved"})
        assert resolved.json()["status"] == "resolved"

        listed = client.get("/api/feedbacks", headers=headers)
        assert listed.status_code == 200
        assert listed.json()[0]["priority"] == 3
        assert listed.json()[0]["comments"][0]["body"] == "Hız değerini de kontrol edelim"

        assert client.get("/api/planning-state", headers=headers).json() is None
        seed = {"machines": [{"id": "C-01", "active": True}], "products": [], "preferences": [], "orders": []}
        saved_state = client.put("/api/planning-state", headers=headers, json={"seed": seed})
        assert saved_state.status_code == 200
        assert saved_state.json()["seed"]["machines"][0]["id"] == "C-01"
        assert saved_state.json()["updatedBy"]["id"] == "test-admin"
        forbidden_settings = client.put(
            "/api/planning-state",
            headers=user_headers,
            json={"seed": {**seed, "holidays": [{"name": "Test", "serial": 46000, "workingShifts": 0}]}, "expectedUpdatedAt": saved_state.json()["updatedAt"]},
        )
        assert forbidden_settings.status_code == 403
        with connection() as db:
            saved_hash = db.execute(
                "SELECT state_hash FROM planning_state_history WHERE id=?",
                (saved_state.json()["historyEntry"]["id"],),
            ).fetchone()["state_hash"]
        assert len(saved_hash) == 64
        first_history = saved_state.json()["historyEntry"]
        assert first_history["seed"] == seed
        history = client.get("/api/planning-state/history", headers=headers)
        assert history.status_code == 200
        assert history.json()[0] == first_history
        loaded_state = client.get("/api/planning-state", headers=headers)
        assert loaded_state.json()["seed"] == seed
        first_version = saved_state.json()["updatedAt"]
        newer_seed = {**seed, "machines": [{"id": "C-02", "active": True}]}
        newer_state = client.put("/api/planning-state", headers=headers, json={"seed": newer_seed, "expectedUpdatedAt": first_version})
        assert newer_state.status_code == 200
        assert client.get("/api/planning-state/history", headers=headers).json()[0]["seed"] == newer_seed
        conflict = client.put("/api/planning-state", headers=headers, json={"seed": seed, "expectedUpdatedAt": first_version})
        assert conflict.status_code == 409
        assert conflict.json()["detail"]["current"]["seed"] == newer_seed
        forced = client.put("/api/planning-state", headers=headers, json={"seed": seed, "force": True})
        assert forced.status_code == 200

        # Planning-only writes (including Clear plan and loading a saved
        # scenario) must never be able to replace live production truth.
        live_archive = [{
            "id": "delivered-743-7477",
            "workOrder": "743/7477",
            "product": "R902745121",
            "completedQuantity": 31_000,
            "inventoryStatus": "delivered",
        }]
        operational_seed = {
            **seed,
            "productionHistory": live_archive,
            "wipLots": [{"id": "live-wip"}],
            "wipMovements": [{"id": "live-movement"}],
            "planningEvents": [{"id": "live-event"}],
            "processCurrentJobs": [{"resourceId": "D-01"}],
            "machines": [{
                "id": "C-01",
                "active": True,
                "operationalAvailableStart": 123,
                "currentJob": {"workOrder": "LIVE"},
            }],
        }
        operational = client.put(
            "/api/planning-state",
            headers=headers,
            json={"seed": operational_seed, "expectedUpdatedAt": forced.json()["updatedAt"], "mode": "operational"},
        )
        assert operational.status_code == 200

        stale_planning_seed = {
            **seed,
            "productionHistory": [],
            "wipLots": [],
            "wipMovements": [],
            "planningEvents": [],
            "processCurrentJobs": [],
            "machines": [{"id": "C-01", "active": False, "currentJob": {"workOrder": "STALE"}}],
        }
        protected = client.put(
            "/api/planning-state",
            headers=headers,
            json={"seed": stale_planning_seed, "expectedUpdatedAt": operational.json()["updatedAt"], "mode": "planning"},
        )
        assert protected.status_code == 200
        assert protected.json()["seed"]["productionHistory"] == live_archive
        assert protected.json()["seed"]["wipLots"] == [{"id": "live-wip"}]
        assert protected.json()["seed"]["machines"][0]["active"] is False
        assert protected.json()["seed"]["machines"][0]["currentJob"] == {"workOrder": "LIVE"}
        assert protected.json()["seed"]["machines"][0]["operationalAvailableStart"] == 123

        archive_history = client.get("/api/production-archive/history", headers=headers)
        assert archive_history.status_code == 200
        assert archive_history.json()[0]["productionHistory"] == live_archive
        assert archive_history.json()[0]["source"] == "operational"
