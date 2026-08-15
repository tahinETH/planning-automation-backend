import os
from pathlib import Path

os.environ["DATABASE_PATH"] = "/tmp/selsa-planlama-feedback-test.sqlite"
os.environ["UPLOAD_DIR"] = "/tmp/selsa-planlama-feedback-uploads"
os.environ["ADMIN_PASSWORD"] = "test-password"
os.environ["APP_SESSION_SECRET"] = "test-session-secret-that-is-long-enough"

from fastapi.testclient import TestClient

from app.main import app


def test_feedback_lifecycle():
    Path(os.environ["DATABASE_PATH"]).unlink(missing_ok=True)
    with TestClient(app) as client:
        assert client.post("/api/auth/login", json={"password": "wrong"}).status_code == 401
        login = client.post("/api/auth/login", json={"password": "test-password"})
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['token']}"}
        assert client.get("/api/feedbacks").status_code == 401

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
        loaded_state = client.get("/api/planning-state", headers=headers)
        assert loaded_state.json()["seed"] == seed
        history = client.get("/api/planning-state/history", headers=headers)
        assert history.status_code == 200
        assert history.json()[0]["seed"] == seed
        client.put("/api/planning-state", headers=headers, json={"seed": seed})
        assert len(client.get("/api/planning-state/history", headers=headers).json()) == 1
        updated_seed = {**seed, "wipLots": [{"id": "wip-1", "availableQuantity": 100}]}
        client.put("/api/planning-state", headers=headers, json={"seed": updated_seed})
        revisions = client.get("/api/planning-state/history", headers=headers).json()
        assert len(revisions) == 2
        assert revisions[0]["seed"]["wipLots"][0]["id"] == "wip-1"
