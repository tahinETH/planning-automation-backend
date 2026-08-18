import os
from pathlib import Path
from unittest.mock import patch

import httpx

os.environ.setdefault("DATABASE_PATH", "/tmp/selsa-planlama-production-sync-test.sqlite")
os.environ.setdefault("UPLOAD_DIR", "/tmp/selsa-planlama-production-sync-uploads")
os.environ.setdefault("ADMIN_PASSWORD", "test-password")
os.environ.setdefault("APP_SESSION_SECRET", "test-session-secret-that-is-long-enough")

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def _set_setting(name: str, value) -> None:
    object.__setattr__(settings, name, value)


def test_production_to_staging_sync_is_one_way_and_atomic():
    originals = {
        "app_env": settings.app_env,
        "database_path": settings.database_path,
        "upload_dir": settings.upload_dir,
        "staging_pull_token": settings.staging_pull_token,
        "production_api_url": settings.production_api_url,
        "production_sync_token": settings.production_sync_token,
    }
    database_path = Path("/tmp/selsa-planlama-production-sync-test.sqlite")
    database_path.unlink(missing_ok=True)
    _set_setting("database_path", database_path)
    _set_setting("upload_dir", Path("/tmp/selsa-planlama-production-sync-uploads"))
    _set_setting("app_env", "staging")
    _set_setting("staging_pull_token", "shared-read-token")
    _set_setting("production_api_url", "https://api.planning.hfgok.com/api")
    _set_setting("production_sync_token", "shared-read-token")

    local_seed = {
        "machines": [{"id": "STAGING-C-01", "active": True}],
        "products": [],
        "preferences": [],
        "orders": [{"id": "STAGING-ORDER", "dueDate": "2026-08-20"}],
    }
    production_seed = {
        "machines": [{"id": "PROD-C-01", "active": True}],
        "products": [],
        "preferences": [],
        "orders": [{"id": "PROD-ORDER", "dueDate": "2026-08-31"}],
    }
    source_updated_at = "2026-08-17T12:00:00+00:00"

    try:
        with TestClient(app) as client:
            login = client.post("/api/auth/login", json={"password": settings.admin_password})
            assert login.status_code == 200
            auth_headers = {"Authorization": f"Bearer {login.json()['token']}"}

            assert client.get("/api/production-sync/status").status_code == 401
            status = client.get("/api/production-sync/status", headers=auth_headers)
            assert status.json() == {"appEnv": "staging", "enabled": True, "lastSync": None}
            assert client.get("/api/production-snapshot", headers={"X-Staging-Pull-Token": "shared-read-token"}).status_code == 404

            saved = client.put("/api/planning-state", headers=auth_headers, json={"seed": local_seed})
            assert saved.status_code == 200

            upstream_request = httpx.Request("GET", "https://api.planning.hfgok.com/api/production-snapshot")
            upstream_response = httpx.Response(
                200,
                json={"planningState": {"seed": production_seed, "updatedAt": source_updated_at}},
                request=upstream_request,
            )
            with patch("app.production_sync.httpx.get", return_value=upstream_response) as upstream_get:
                pulled = client.post("/api/production-sync/pull", headers=auth_headers)

            assert pulled.status_code == 200
            assert pulled.json()["planningState"]["seed"] == production_seed
            assert pulled.json()["sourceUpdatedAt"] == source_updated_at
            assert pulled.json()["sourceUrl"] == "https://api.planning.hfgok.com/api"
            upstream_get.assert_called_once_with(
                "https://api.planning.hfgok.com/api/production-snapshot",
                headers={"X-Staging-Pull-Token": "shared-read-token"},
                timeout=20.0,
                follow_redirects=False,
            )

            assert client.get("/api/planning-state", headers=auth_headers).json()["seed"] == production_seed
            assert client.get("/api/orders", headers=auth_headers).json() == [{
                "id": "PROD-ORDER",
                "dueDate": "2026-08-31",
                "allowPartial": False,
                "partialDeliveryQuantity": 0,
                "partialDeliveryDate": "",
                "deliveryMilestones": [],
            }]
            synced_status = client.get("/api/production-sync/status", headers=auth_headers).json()
            assert synced_status["lastSync"]["sourceUpdatedAt"] == source_updated_at
            assert synced_status["lastSync"]["sourceUrl"] == "https://api.planning.hfgok.com/api"

            invalid_response = httpx.Response(200, json={"planningState": {"seed": {}}}, request=upstream_request)
            with patch("app.production_sync.httpx.get", return_value=invalid_response):
                rejected = client.post("/api/production-sync/pull", headers=auth_headers)
            assert rejected.status_code == 502
            assert "staging değiştirilmedi" in rejected.json()["detail"]
            assert client.get("/api/planning-state", headers=auth_headers).json()["seed"] == production_seed

            malformed_order_seed = {**production_seed, "orders": [{"dueDate": "2026-09-01"}]}
            malformed_order_response = httpx.Response(
                200,
                json={"planningState": {"seed": malformed_order_seed, "updatedAt": source_updated_at}},
                request=upstream_request,
            )
            with patch("app.production_sync.httpx.get", return_value=malformed_order_response):
                malformed_order = client.post("/api/production-sync/pull", headers=auth_headers)
            assert malformed_order.status_code == 502
            assert client.get("/api/planning-state", headers=auth_headers).json()["seed"] == production_seed

            with patch("app.production_sync.httpx.get", side_effect=httpx.ConnectError("offline", request=upstream_request)):
                unreachable = client.post("/api/production-sync/pull", headers=auth_headers)
            assert unreachable.status_code == 502
            assert "bağlanılamadı" in unreachable.json()["detail"]
            assert client.get("/api/planning-state", headers=auth_headers).json()["seed"] == production_seed

            denied_response = httpx.Response(401, json={"detail": "denied"}, request=upstream_request)
            with patch("app.production_sync.httpx.get", return_value=denied_response):
                denied = client.post("/api/production-sync/pull", headers=auth_headers)
            assert denied.status_code == 502
            assert client.get("/api/planning-state", headers=auth_headers).json()["seed"] == production_seed

            invalid_json_response = httpx.Response(200, content=b"not-json", request=upstream_request)
            with patch("app.production_sync.httpx.get", return_value=invalid_json_response):
                invalid_json = client.post("/api/production-sync/pull", headers=auth_headers)
            assert invalid_json.status_code == 502
            assert "geçerli veri" in invalid_json.json()["detail"]
            assert client.get("/api/planning-state", headers=auth_headers).json()["seed"] == production_seed

            _set_setting("production_sync_token", "")
            disabled = client.get("/api/production-sync/status", headers=auth_headers)
            assert disabled.json()["enabled"] is False
            assert client.post("/api/production-sync/pull", headers=auth_headers).status_code == 503
            assert client.get("/api/planning-state", headers=auth_headers).json()["seed"] == production_seed
            _set_setting("production_sync_token", "shared-read-token")

            _set_setting("app_env", "production")
            assert client.post("/api/production-sync/pull", headers=auth_headers).status_code == 403
            assert client.get("/api/production-snapshot", headers={"X-Staging-Pull-Token": "wrong"}).status_code == 401
            snapshot = client.get("/api/production-snapshot", headers={"X-Staging-Pull-Token": "shared-read-token"})
            assert snapshot.status_code == 200
            assert snapshot.json()["planningState"]["seed"] == production_seed
            _set_setting("staging_pull_token", "")
            assert client.get("/api/production-snapshot", headers={"X-Staging-Pull-Token": "shared-read-token"}).status_code == 503
    finally:
        for name, value in originals.items():
            _set_setting(name, value)
