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
from app.database import connection
from app.main import app
from app.production_merge import merge_production_refresh


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
    expected_seed = merge_production_refresh(production_seed, local_seed, None)
    source_updated_at = "2026-08-17T12:00:00+00:00"
    production_scenarios = [{
        "id": "prod-scenario-1",
        "name": "Prod senaryosu",
        "createdAt": "2026-08-17T11:00:00+00:00",
        "notes": "Production kaynaklı",
        "seed": production_seed,
        "result": {"state": "planned", "batches": []},
    }]

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
            with connection() as db:
                db.execute(
                    """INSERT INTO scenarios(id,name,created_at,notes,inputs_json,result_json)
                    VALUES(?,?,?,?,?,?)""",
                    ("staging-only", "Staging senaryosu", "2026-08-17T10:00:00+00:00", "Silinmeli", "{}", "{}"),
                )

            upstream_request = httpx.Request("GET", "https://api.planning.hfgok.com/api/production-snapshot")
            upstream_response = httpx.Response(
                200,
                json={"planningState": {"seed": production_seed, "updatedAt": source_updated_at}, "scenarios": production_scenarios},
                request=upstream_request,
            )
            with patch("app.production_sync.httpx.get", return_value=upstream_response) as upstream_get:
                # No baseline proves that this local work can be replaced.
                # The reviewed refresh rule requires an explicit group choice.
                undecided = client.post("/api/production-sync/pull", headers=auth_headers)
                assert undecided.status_code == 409
                assert client.get("/api/planning-state", headers=auth_headers).json()["seed"] == local_seed
                assert {item["id"] for item in client.get("/api/scenarios", headers=auth_headers).json()} == {"staging-only"}
                preview = client.post("/api/production-sync/pull", headers=auth_headers, json={"action": "preview"})
                assert preview.status_code == 200
                review = preview.json()
                pulled = client.post("/api/production-sync/pull", headers=auth_headers, json={
                    "action": "apply",
                    "expected": {key: review[key] for key in ("sourceDigest", "localDigest", "localUpdatedAt", "baselineDigest")},
                    "choices": {"physical": "keep-local", "orders": "keep-local", "annotations": "keep-local"},
                })

            assert pulled.status_code == 200
            assert pulled.json()["planningState"]["seed"] == expected_seed
            assert pulled.json()["sourceUpdatedAt"] == source_updated_at
            assert pulled.json()["sourceUrl"] == "https://api.planning.hfgok.com/api"
            assert {s["id"] for s in pulled.json()["scenarios"]} == {"staging-only", "prod-scenario-1"}
            assert upstream_get.call_count == 3
            upstream_get.assert_called_with(
                "https://api.planning.hfgok.com/api/production-snapshot",
                headers={"X-Staging-Pull-Token": "shared-read-token", "X-Production-Area": "torna"},
                timeout=20.0,
                follow_redirects=False,
            )

            assert client.get("/api/planning-state", headers=auth_headers).json()["seed"] == expected_seed
            assert {s["id"] for s in client.get("/api/scenarios", headers=auth_headers).json()} == {"staging-only", "prod-scenario-1"}
            assert client.get("/api/orders", headers=auth_headers).json() == [{
                "id": "STAGING-ORDER",
                "dueDate": "2026-08-20",
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
            assert client.get("/api/planning-state", headers=auth_headers).json()["seed"] == expected_seed

            missing_scenarios_response = httpx.Response(
                200,
                json={"planningState": {"seed": production_seed, "updatedAt": source_updated_at}},
                request=upstream_request,
            )
            with patch("app.production_sync.httpx.get", return_value=missing_scenarios_response):
                missing_scenarios = client.post("/api/production-sync/pull", headers=auth_headers)
            assert missing_scenarios.status_code == 502
            assert {s["id"] for s in client.get("/api/scenarios", headers=auth_headers).json()} == {"staging-only", "prod-scenario-1"}

            malformed_order_seed = {**production_seed, "orders": [{"dueDate": "2026-09-01"}]}
            malformed_order_response = httpx.Response(
                200,
                json={"planningState": {"seed": malformed_order_seed, "updatedAt": source_updated_at}},
                request=upstream_request,
            )
            with patch("app.production_sync.httpx.get", return_value=malformed_order_response):
                malformed_order = client.post("/api/production-sync/pull", headers=auth_headers)
            assert malformed_order.status_code == 502
            assert client.get("/api/planning-state", headers=auth_headers).json()["seed"] == expected_seed

            with patch("app.production_sync.httpx.get", side_effect=httpx.ConnectError("offline", request=upstream_request)):
                unreachable = client.post("/api/production-sync/pull", headers=auth_headers)
            assert unreachable.status_code == 502
            assert "bağlanılamadı" in unreachable.json()["detail"]
            assert client.get("/api/planning-state", headers=auth_headers).json()["seed"] == expected_seed

            denied_response = httpx.Response(401, json={"detail": "denied"}, request=upstream_request)
            with patch("app.production_sync.httpx.get", return_value=denied_response):
                denied = client.post("/api/production-sync/pull", headers=auth_headers)
            assert denied.status_code == 502
            assert client.get("/api/planning-state", headers=auth_headers).json()["seed"] == expected_seed

            invalid_json_response = httpx.Response(200, content=b"not-json", request=upstream_request)
            with patch("app.production_sync.httpx.get", return_value=invalid_json_response):
                invalid_json = client.post("/api/production-sync/pull", headers=auth_headers)
            assert invalid_json.status_code == 502
            assert "geçerli veri" in invalid_json.json()["detail"]
            assert client.get("/api/planning-state", headers=auth_headers).json()["seed"] == expected_seed

            _set_setting("production_sync_token", "")
            disabled = client.get("/api/production-sync/status", headers=auth_headers)
            assert disabled.json()["enabled"] is False
            assert client.post("/api/production-sync/pull", headers=auth_headers).status_code == 503
            assert client.get("/api/planning-state", headers=auth_headers).json()["seed"] == expected_seed
            _set_setting("production_sync_token", "shared-read-token")

            _set_setting("app_env", "production")
            assert client.post("/api/production-sync/pull", headers=auth_headers).status_code == 403
            assert client.get("/api/production-snapshot", headers={"X-Staging-Pull-Token": "wrong"}).status_code == 401
            snapshot = client.get("/api/production-snapshot", headers={"X-Staging-Pull-Token": "shared-read-token"})
            assert snapshot.status_code == 200
            assert snapshot.json()["planningState"]["seed"] == expected_seed
            assert {s["id"] for s in snapshot.json()["scenarios"]} == {"staging-only", "prod-scenario-1"}
            _set_setting("staging_pull_token", "")
            assert client.get("/api/production-snapshot", headers={"X-Staging-Pull-Token": "shared-read-token"}).status_code == 503
    finally:
        for name, value in originals.items():
            _set_setting(name, value)


def test_local_refresh_reviews_an_empty_database_and_requires_admin(tmp_path, request):
    from app.auth import create_test_session

    fixture_settings = {
        "app_env": "test",
        "auth_test_mode": True,
        "enable_local_production_sync": True,
        "database_path": tmp_path / "local.sqlite",
        "upload_dir": tmp_path / "uploads",
        "production_api_url": "https://source.example/api",
        "production_sync_token": "local-refresh-fixture-token",
    }
    original_settings = {key: getattr(settings, key) for key in fixture_settings}
    for key, value in fixture_settings.items():
        _set_setting(key, value)

    def restore_settings():
        for key, value in original_settings.items():
            _set_setting(key, value)

    request.addfinalizer(restore_settings)
    source = {"machines": [{"id": "L-01"}], "products": [], "preferences": [],
              "orders": [], "productionArea": "cubuk-filtre"}
    response = httpx.Response(
        200, json={"planningState": {"seed": source, "updatedAt": "2026-11-22T09:00:00Z"}, "scenarios": []},
        headers={"X-Production-Area": "cubuk-filtre"},
    )
    admin = {"Authorization": f"Bearer {create_test_session(settings.admin_password)}", "X-Production-Area": "cubuk-filtre"}
    operator = {"Authorization": f"Bearer {create_test_session(settings.admin_password, role='user')}", "X-Production-Area": "cubuk-filtre"}

    with TestClient(app) as client, patch("app.production_sync.httpx.get", return_value=response) as source_get:
        assert client.get("/api/production-sync/status", headers=admin).json() == {
            "appEnv": "test", "target": "local", "enabled": True, "lastSync": None,
        }
        assert client.post("/api/production-sync/pull", headers=operator, json={"action": "preview"}).status_code == 403
        assert client.post("/api/production-sync/pull", headers=admin).status_code == 422
        source_get.assert_not_called()
        preview_response = client.post("/api/production-sync/pull", headers=admin, json={"action": "preview"})
        assert preview_response.status_code == 200
        preview = preview_response.json()
        assert preview["localUpdatedAt"] == "" and preview["localDigest"] is None
        assert client.get("/api/planning-state", headers=admin).json() is None
        assert preview["settingsKeys"]["keptLocal"] == []
        physical = next(group for group in preview["groups"] if group["id"] == "physical")
        assert physical["defaultChoice"] == "use-source"
        assert physical["summary"]["collections"]["machines"]["onlySource"] == 1

        request = {
            "action": "apply",
            "expected": {key: preview[key] for key in ("sourceDigest", "localDigest", "localUpdatedAt", "baselineDigest")},
            "choices": {group["id"]: "use-source" for group in preview["groups"]},
        }
        applied = client.post("/api/production-sync/pull", headers=admin, json=request)
        assert applied.status_code == 200
        assert applied.json()["planningState"]["seed"] == source
        assert applied.json()["backupId"] is None
        assert client.get("/api/planning-state", headers=admin).json()["seed"] == source
        assert client.post("/api/production-sync/pull", headers=admin, json=request).status_code == 409
        assert client.get("/api/planning-state", headers=admin).json()["seed"] == source
        source_get.assert_called_with(
            "https://source.example/api/production-snapshot",
            headers={"X-Staging-Pull-Token": settings.production_sync_token, "X-Production-Area": "cubuk-filtre"},
            timeout=20.0, follow_redirects=False,
        )

        _set_setting("enable_local_production_sync", False)
        assert client.get("/api/production-sync/status", headers=admin).json()["enabled"] is False
        count = source_get.call_count
        assert client.post("/api/production-sync/pull", headers=admin, json={"action": "preview"}).status_code == 403
        assert source_get.call_count == count


def test_refresh_preserves_partial_work_deletions_and_updates_clean_inputs():
    from copy import deepcopy
    base = {"products": [{"product": "A", "rate": 1}], "machines": [{"id": "C1"}],
            "wipLots": [{"id": "lot", "quantity": 100}], "processCurrentJobs": [{"id": "job"}],
            "manualBatches": [{"id": "batch"}], "orders": [{"id": "order"}]}
    local = deepcopy(base)
    local["wipLots"] = [{"id": "lot", "quantity": 40}, {"id": "part", "quantity": 60, "stage": "delivered"}]
    local["processCurrentJobs"] = []
    local["manualBatches"] = []
    source = deepcopy(base)
    source["products"][0]["rate"] = 2
    merged = merge_production_refresh(source, local, base)
    assert merged["products"] == source["products"]
    assert merged["wipLots"] == local["wipLots"]
    assert merged["processCurrentJobs"] == []
    assert merged["manualBatches"] == []
    assert merge_production_refresh(source, merged, source) == merged
    assert merge_production_refresh(source, None, None) == source
    assert merge_production_refresh(source, local, None)["wipLots"] == local["wipLots"]


def test_cf_b5_refresh_takes_monthly_delivery_baselines_with_the_selected_orders():
    from app.production_merge import merge_production_refresh_reviewed, refresh_groups, resolve_refresh_choices, settings_key_differences

    def snapshot(delivered):
        return {"productionArea": "cubuk-filtre", "orders": [], "monthlyCustomerDemand": {"handovers": delivered},
                "filterMonthlyDeliveryBaselines": [{"year": 2026, "handovers": delivered}]}

    source, local, baseline = snapshot(300), snapshot(200), snapshot(100)
    groups = refresh_groups(source, local, baseline)
    orders = next(group for group in groups if group["id"] == "orders")
    assert orders["requiresChoice"]
    assert orders["summary"]["collections"]["filterMonthlyDeliveryBaselines"] == {"onlyLocal": 0, "onlySource": 0, "different": 1}
    assert "filterMonthlyDeliveryBaselines" not in settings_key_differences(source, local, baseline)["keptLocal"]
    for choice, expected in [("keep-local", local), ("use-source", source)]:
        merged = merge_production_refresh_reviewed(source, local, baseline, resolve_refresh_choices(groups, {"orders": choice}))
        assert merged["monthlyCustomerDemand"] == expected["monthlyCustomerDemand"]
        assert merged["filterMonthlyDeliveryBaselines"] == expected["filterMonthlyDeliveryBaselines"]
    assert local == snapshot(200) and source == snapshot(300)
