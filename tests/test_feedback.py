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

        created = client.post("/api/feedbacks", headers=headers, json={"body": "C-08 planı kontrol edilmeli", "page_path": "Tezgahlar / C-08"})
        assert created.status_code == 201
        feedback_id = created.json()["id"]

        commented = client.post(f"/api/feedbacks/{feedback_id}/comments", headers=headers, json={"body": "Hız değerini de kontrol edelim"})
        assert commented.status_code == 201
        assert len(commented.json()["comments"]) == 1

        edited = client.patch(f"/api/feedbacks/{feedback_id}", headers=headers, json={"body": "C-08 kapasitesi kontrol edilmeli"})
        assert edited.json()["body"] == "C-08 kapasitesi kontrol edilmeli"

        uploaded = client.post(f"/api/feedbacks/{feedback_id}/attachments", headers=headers, files=[("files", ("ekran.png", b"png-data", "image/png"))])
        assert uploaded.status_code == 201
        assert uploaded.json()["attachments"][0]["kind"] == "image"

        voiced = client.post(f"/api/feedbacks/{feedback_id}/attachments", headers=headers, files=[("files", ("not.webm", b"voice-data", "audio/webm"))])
        assert voiced.status_code == 201
        assert {item["kind"] for item in voiced.json()["attachments"]} == {"image", "voice"}

        resolved = client.patch(f"/api/feedbacks/{feedback_id}", headers=headers, json={"status": "resolved"})
        assert resolved.json()["status"] == "resolved"

        listed = client.get("/api/feedbacks", headers=headers)
        assert listed.status_code == 200
        assert listed.json()[0]["comments"][0]["body"] == "Hız değerini de kontrol edelim"
