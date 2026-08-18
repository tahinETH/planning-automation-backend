from pathlib import Path

from fastapi.testclient import TestClient

from app.config import settings
from app.database import save_planning_state
from app.main import app


def _set_setting(name: str, value) -> None:
    object.__setattr__(settings, name, value)


def test_production_snapshot_is_read_only_and_token_gated(tmp_path: Path):
    originals = {
        "app_env": settings.app_env,
        "database_path": settings.database_path,
        "upload_dir": settings.upload_dir,
        "staging_pull_token": settings.staging_pull_token,
    }
    database_path = tmp_path / "production.sqlite"
    seed = {
        "machines": [{"id": "C-01", "active": True}],
        "products": [{"product": "R902700001"}],
        "preferences": [{"key": "R902700001", "machines": ["C-01"]}],
        "orders": [{"id": "ORDER-1", "product": "R902700001"}],
    }

    try:
        _set_setting("app_env", "production")
        _set_setting("database_path", database_path)
        _set_setting("upload_dir", tmp_path / "uploads")
        _set_setting("staging_pull_token", "shared-read-only-token")

        with TestClient(app) as client:
            save_planning_state(seed)

            assert client.get("/api/production-snapshot").status_code == 401
            assert client.get(
                "/api/production-snapshot",
                headers={"X-Staging-Pull-Token": "wrong-token"},
            ).status_code == 401

            response = client.get(
                "/api/production-snapshot",
                headers={"X-Staging-Pull-Token": "shared-read-only-token"},
            )
            assert response.status_code == 200
            assert response.json()["planningState"]["seed"] == seed

            assert client.post(
                "/api/production-snapshot",
                headers={"X-Staging-Pull-Token": "shared-read-only-token"},
            ).status_code == 405

            _set_setting("app_env", "staging")
            assert client.get(
                "/api/production-snapshot",
                headers={"X-Staging-Pull-Token": "shared-read-only-token"},
            ).status_code == 404
    finally:
        for name, value in originals.items():
            _set_setting(name, value)


def test_production_snapshot_rejects_missing_configuration_and_invalid_state(tmp_path: Path):
    originals = {
        "app_env": settings.app_env,
        "database_path": settings.database_path,
        "upload_dir": settings.upload_dir,
        "staging_pull_token": settings.staging_pull_token,
    }

    try:
        _set_setting("app_env", "production")
        _set_setting("database_path", tmp_path / "production-invalid.sqlite")
        _set_setting("upload_dir", tmp_path / "uploads-invalid")
        _set_setting("staging_pull_token", "")

        with TestClient(app) as client:
            assert client.get(
                "/api/production-snapshot",
                headers={"X-Staging-Pull-Token": "any-token"},
            ).status_code == 503

            _set_setting("staging_pull_token", "shared-read-only-token")
            save_planning_state({"machines": [], "products": [], "preferences": []})
            assert client.get(
                "/api/production-snapshot",
                headers={"X-Staging-Pull-Token": "shared-read-only-token"},
            ).status_code == 404
    finally:
        for name, value in originals.items():
            _set_setting(name, value)
