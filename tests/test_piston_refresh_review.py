"""Synthetic source-refresh review checks. No real source or user data is read."""

from copy import deepcopy
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.auth import create_test_session
from app.config import settings
from app.database import connection
from app.main import app


@pytest.fixture
def refresh_client(tmp_path, monkeypatch):
    overrides = {
        "database_path": tmp_path / "refresh.sqlite", "upload_dir": tmp_path / "uploads",
        "app_env": "staging", "production_api_url": "https://source.invalid/api",
        "production_sync_token": "synthetic-read-token",
    }
    originals = {key: getattr(settings, key) for key in overrides}
    try:
        for key, value in overrides.items():
            object.__setattr__(settings, key, value)
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client
    finally:
        for key, value in originals.items():
            object.__setattr__(settings, key, value)


def auth(role="admin"):
    return {"Authorization": "Bearer " + create_test_session("test-password", role)}


def physical_fixture():
    baseline = {
        "productionArea": "torna", "products": [], "preferences": [], "orders": [],
        "machines": [{"id": "C-01", "currentJob": None}],
        "productionHistory": [], "wipLots": [], "wipMovements": [],
        "processCurrentJobs": [], "productionCancellations": [],
        "chargeJourneyNotes": [], "manualBatches": [], "savedBatches": [],
    }
    local = deepcopy(baseline)
    local["chargeJourneyNotes"] = [{"id": "local-note", "batchId": "unrelated-charge", "note": "Keep this explanation"}]
    source = deepcopy(baseline)
    source["machines"][0]["currentJob"] = {"product": "PISTON", "workOrder": "SOURCE-WORK", "quantity": 500, "remaining": 300}
    source["productionHistory"] = [{"id": "source-delivery", "product": "PISTON", "quantity": 200, "status": "delivered"}]
    return baseline, local, source


def seed_local(seed, baseline):
    with connection() as db:
        db.execute("INSERT INTO planning_state(state_key,seed_json,updated_at) VALUES('default',?,?)",
                   (json.dumps(seed), "2026-10-18T08:00:00Z"))
        if baseline is not None:
            db.execute("INSERT INTO production_sync_baseline VALUES('production',?)", (json.dumps(baseline),))
        db.execute("INSERT INTO scenarios(id,name,created_at,notes,inputs_json,result_json) VALUES(?,?,?,?,?,?)",
                   ("local-scenario", "Local scenario", "2026-10-18T07:00:00Z", "Keep", "{}", "{}"))


def database_snapshot():
    with connection() as db:
        return list(db.iterdump())


@pytest.mark.parametrize("failure", ["offline", "denied", "malformed", "incomplete"])
def test_t16_source_failure_preserves_state_baseline_scenarios_history_and_sync_metadata(refresh_client, monkeypatch, failure):
    baseline, local, _ = physical_fixture()
    seed_local(local, baseline)
    before = database_snapshot()
    requests = []

    def source_get(url, **kwargs):
        requests.append((url, kwargs))
        request = httpx.Request("GET", url)
        if failure == "offline":
            raise httpx.ConnectError("synthetic offline", request=request)
        if failure == "denied":
            return httpx.Response(401, json={}, request=request)
        if failure == "malformed":
            return httpx.Response(200, content=b"not-json", request=request)
        return httpx.Response(200, json={"planningState": {"seed": {}}}, request=request)

    monkeypatch.setattr("app.production_sync.httpx.get", source_get)
    response = refresh_client.post("/api/production-sync/pull", headers=auth())
    assert response.status_code == 502
    assert database_snapshot() == before
    assert len(requests) == 1
    assert requests[0][0] == "https://source.invalid/api/production-snapshot"
    assert requests[0][1]["follow_redirects"] is False
    assert 0 < requests[0][1]["timeout"] <= 20


@pytest.mark.parametrize("role,environment,status", [(None, "staging", 401), ("user", "staging", 403), ("admin", "production", 403)])
def test_t16_pull_permission_and_environment_guards_run_before_source_access(refresh_client, monkeypatch, role, environment, status):
    baseline, local, _ = physical_fixture()
    seed_local(local, baseline)
    before = database_snapshot()
    object.__setattr__(settings, "app_env", environment)

    def forbidden_access(*args, **kwargs):
        pytest.fail("Rejected refresh must not access the source")

    monkeypatch.setattr("app.production_sync.httpx.get", forbidden_access)
    response = refresh_client.post("/api/production-sync/pull", headers=auth(role) if role else {})
    assert response.status_code == status
    assert database_snapshot() == before


def mock_source(monkeypatch, seed, scenarios=None):
    def source_get(url, **kwargs):
        return httpx.Response(200, request=httpx.Request("GET", url), json={
            "planningState": {"seed": deepcopy(seed), "updatedAt": "2026-10-18T09:00:00Z"},
            "scenarios": deepcopy(scenarios or []),
        })
    monkeypatch.setattr("app.production_sync.httpx.get", source_get)


def preview(client):
    response = client.post("/api/production-sync/pull", headers=auth(), json={"action": "preview"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert "groups" in result, "Preview must show review groups, not silently perform the old pull"
    return result


def apply_review(client, review, physical="use-source"):
    return client.post("/api/production-sync/pull", headers=auth(), json={
        "action": "apply",
        "expected": {key: review[key] for key in ("sourceDigest", "localDigest", "localUpdatedAt", "baselineDigest")},
        "choices": {"physical": physical, "orders": "keep-local", "annotations": "keep-local"},
    })


def test_t16_preview_shows_source_current_and_delivery_despite_unrelated_note_without_writing(refresh_client, monkeypatch):
    baseline, local, source = physical_fixture()
    seed_local(local, baseline)
    mock_source(monkeypatch, source)
    before = database_snapshot()
    review = preview(refresh_client)
    assert database_snapshot() == before
    groups = {group["id"]: group for group in review["groups"]}
    assert groups["physical"]["status"] == "source-changed"
    assert groups["annotations"]["status"] == "local-changed"
    physical_summary = groups["physical"]["summary"]
    assert physical_summary["collections"]["productionHistory"]["onlySource"] == 1
    assert physical_summary["collections"]["machines"]["different"] == 1
    assert physical_summary["currentJobMachines"] == ["C-01"]
    assert review["sourceDigest"] and review["baselineDigest"]


@pytest.mark.parametrize("choice", ["keep-local", "use-source"])
def test_t16_review_applies_physical_group_whole_and_keeps_recoverable_prechange_version(refresh_client, monkeypatch, choice):
    baseline, local, source = physical_fixture()
    local["machines"][0]["currentJob"] = {"workOrder": "LOCAL-WORK", "product": "LOCAL", "quantity": 700, "remaining": 500}
    local["wipLots"] = [{"id": "local-physical-lot", "quantity": 200}]
    seed_local(local, baseline)
    mock_source(monkeypatch, source)
    review = preview(refresh_client)
    groups = {group["id"]: group for group in review["groups"]}
    assert groups["physical"]["status"] == "both-changed"
    response = apply_review(refresh_client, review, choice)
    assert response.status_code == 200, response.text
    result = response.json()
    selected = local if choice == "keep-local" else source
    actual = result["planningState"]["seed"]
    for field in ("machines", "wipLots", "productionHistory", "wipMovements", "processCurrentJobs", "productionCancellations"):
        assert actual[field] == selected[field], f"Physical field {field} must follow the reviewed group"
    assert actual["chargeJourneyNotes"] == local["chargeJourneyNotes"]
    assert result["backupId"]
    with connection() as db:
        backup = db.execute("SELECT seed_json FROM production_sync_backup WHERE id=?", (result["backupId"],)).fetchone()
    assert backup and json.loads(backup["seed_json"]) == local


@pytest.mark.parametrize("changed", ["source", "local", "local-same-time", "baseline"])
def test_t16_apply_rejects_stale_source_local_or_baseline_without_any_write(refresh_client, monkeypatch, changed):
    baseline, local, source = physical_fixture()
    seed_local(local, baseline)
    mock_source(monkeypatch, source)
    review = preview(refresh_client)
    if changed == "source":
        source["productionHistory"].append({"id": "new-source-record", "quantity": 1})
    else:
        with connection() as db:
            if changed == "local":
                db.execute("UPDATE planning_state SET updated_at=? WHERE state_key='default'", ("2026-10-18T10:00:00Z",))
            elif changed == "local-same-time":
                newer_local = deepcopy(local)
                newer_local["chargeJourneyNotes"].append({"id": "concurrent-note", "note": "Keep concurrent text"})
                db.execute("UPDATE planning_state SET seed_json=? WHERE state_key='default'", (json.dumps(newer_local),))
            else:
                newer_base = deepcopy(baseline)
                newer_base["orders"] = [{"id": "new-baseline-order"}]
                db.execute("UPDATE production_sync_baseline SET seed_json=?", (json.dumps(newer_base),))
    before = database_snapshot()
    response = apply_review(refresh_client, review)
    assert response.status_code == 409, response.text
    assert database_snapshot() == before


def test_t16_missing_baseline_requires_explicit_review_and_old_client_cannot_claim_success(refresh_client, monkeypatch):
    _, local, source = physical_fixture()
    seed_local(local, None)
    mock_source(monkeypatch, source)
    before = database_snapshot()
    review = preview(refresh_client)
    assert review["baselineDigest"] is None
    physical = next(group for group in review["groups"] if group["id"] == "physical")
    assert physical["status"] == "no-baseline"
    assert physical["defaultChoice"] is None
    assert database_snapshot() == before
    old_client = refresh_client.post("/api/production-sync/pull", headers=auth(), json={})
    assert old_client.status_code == 409
    assert database_snapshot() == before


def test_t16_review_combines_notes_by_identity_and_adds_only_new_scenario_ids(refresh_client, monkeypatch):
    baseline, local, source = physical_fixture()
    local["chargeJourneyNotes"].append({"id": "collision", "note": "Local explanation"})
    source["chargeJourneyNotes"] = [{"id": "collision", "note": "Source explanation"}, {"id": "source-note", "note": "Source only"}]
    seed_local(local, baseline)
    scenarios = [{"id": identity, "name": "Source scenario", "createdAt": "2026-10-18T09:00:00Z",
                  "notes": "source", "seed": source, "result": {"batches": []}}
                 for identity in ("local-scenario", "new-source-scenario")]
    mock_source(monkeypatch, source, scenarios)
    review = preview(refresh_client)
    response = refresh_client.post("/api/production-sync/pull", headers=auth(), json={
        "action": "apply",
        "expected": {key: review[key] for key in ("sourceDigest", "localDigest", "localUpdatedAt", "baselineDigest")},
        "choices": {"physical": "use-source", "orders": "keep-local", "annotations": "combine"},
    })
    assert response.status_code == 200, response.text
    notes = {note["id"]: note["note"] for note in response.json()["planningState"]["seed"]["chargeJourneyNotes"]}
    assert notes == {"local-note": "Keep this explanation", "collision": "Local explanation", "source-note": "Source only"}
    with connection() as db:
        records = {row["id"]: row["name"] for row in db.execute("SELECT id,name FROM scenarios")}
    assert records == {"local-scenario": "Local scenario", "new-source-scenario": "Source scenario"}


def test_t16_source_scenario_change_invalidates_review_even_with_same_seed_revision(refresh_client, monkeypatch):
    baseline, local, source = physical_fixture()
    seed_local(local, baseline)
    source_scenarios = [{"id": "source-scenario", "name": "Original source name", "createdAt": "2026-10-18T09:00:00Z",
                         "notes": "", "seed": source, "result": {"batches": []}}]
    mock_source(monkeypatch, source, source_scenarios)
    review = preview(refresh_client)
    source_scenarios[0]["name"] = "Concurrent source revision"
    before = database_snapshot()
    response = apply_review(refresh_client, review)
    assert response.status_code == 409
    assert database_snapshot() == before


def test_t16_transaction_failure_rolls_back_backup_state_baseline_history_and_scenarios(refresh_client, monkeypatch):
    baseline, local, source = physical_fixture()
    seed_local(local, baseline)
    mock_source(monkeypatch, source)
    review = preview(refresh_client)
    before = database_snapshot()

    def fail_order_write(*args, **kwargs):
        raise RuntimeError("Synthetic database failure after state/history writes")

    monkeypatch.setattr("app.database._save_orders", fail_order_write)
    response = apply_review(refresh_client, review)
    assert response.status_code == 500
    assert database_snapshot() == before


@pytest.mark.parametrize("action", ["preview", "apply"])
def test_t16_production_refresh_is_blocked_for_cf_header_and_each_action(refresh_client, monkeypatch, action):
    baseline, local, _ = physical_fixture()
    seed_local(local, baseline)
    before = database_snapshot()

    def forbidden_access(*args, **kwargs):
        pytest.fail("Deferred CF refresh must not access the production source")

    object.__setattr__(settings, "app_env", "production")
    monkeypatch.setattr("app.production_sync.httpx.get", forbidden_access)
    # The production port has no CF middleware. Its environment guard blocks
    # every source pull, irrespective of an unsupported area header.
    expected = {"sourceDigest": "a" * 64, "localDigest": "b" * 64,
                "localUpdatedAt": "2026-10-18T08:00:00Z", "baselineDigest": "c" * 64}
    response = refresh_client.post("/api/production-sync/pull", headers={**auth(), "X-Production-Area": "cubuk-filtre"},
                                   json={"action": action, "expected": expected, "choices": {}})
    assert response.status_code == 403
    assert database_snapshot() == before


@pytest.mark.parametrize("bad", ["action", "expected-list", "expected-missing", "choices-list", "choice-object"])
def test_t16_malformed_review_request_is_422_before_source_access(refresh_client, monkeypatch, bad):
    baseline, local, source = physical_fixture()
    seed_local(local, baseline)
    mock_source(monkeypatch, source)
    review = preview(refresh_client)
    body = {"action": "apply", "expected": {key: review[key] for key in ("sourceDigest", "localDigest", "localUpdatedAt", "baselineDigest")},
            "choices": {"physical": "use-source"}}
    if bad == "action":
        body["action"] = "overwrite"
    elif bad == "expected-list":
        body["expected"] = []
    elif bad == "expected-missing":
        body["expected"] = {}
    elif bad == "choices-list":
        body["choices"] = ["use-source"]
    else:
        body["choices"] = {"physical": {"take": "source"}}
    before = database_snapshot()

    source_calls = []

    def source_get(url, **kwargs):
        source_calls.append(url)
        return httpx.Response(200, request=httpx.Request("GET", url), json={
            "planningState": {"seed": source, "updatedAt": "2026-10-18T09:00:00Z"}, "scenarios": [],
        })

    monkeypatch.setattr("app.production_sync.httpx.get", source_get)
    response = refresh_client.post("/api/production-sync/pull", headers=auth(), json=body)
    assert response.status_code == 422
    assert not source_calls, "Malformed request must be rejected before source access"
    assert database_snapshot() == before
