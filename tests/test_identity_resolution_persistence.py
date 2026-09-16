"""ID-PERSIST01: legacy identity quarantine is local, durable and revision-bound.

Synthetic legacy rows are inserted directly: the ordinary save path must not create
such ambiguity. All tests use private temporary SQLite databases, never live data.
"""
import copy
import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import database
from app.auth import create_test_session
from app.main import app


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "settings", SimpleNamespace(database_path=tmp_path / "identity.sqlite", upload_dir=tmp_path / "uploads"))
    database.init_database()
    return database


def synthetic_seed():
    return {
        "products": [{"product": "PART-A"}, {"product": "PART-B"}], "preferences": [], "holidays": [], "calendarEvents": [],
        "orders": [{"id": "order-a", "product": "PART-A", "quantity": 600, "dueDate": "2026-09-25"},
                   {"id": "order-b", "product": "PART-B", "quantity": 200, "dueDate": "2026-09-25"}],
        "machines": [{"id": machine, "currentJob": {"product": "", "quantity": 0}} for machine in ["C-01", "C-02", "C-09"]],
        "manualBatches": [
            {"id": "ambiguous-charge", "product": "PART-A", "workOrder": "WO-LEGACY", "quantity": 600, "machineId": "C-01", "locked": True, "start": 46281, "end": 46282},
            {"id": "unrelated-charge", "product": "PART-B", "workOrder": "WO-OTHER", "quantity": 200, "machineId": "C-02", "locked": True, "start": 46281, "end": 46282},
        ],
        "productionHistory": [
            {"id": "legacy-wip", "product": "PART-A", "workOrder": "WO-LEGACY", "originalQuantity": 600, "completedQuantity": 600, "machineId": "C-09", "process": "turning", "inventoryStatus": "semi-finished"},
            {"id": "legacy-shipped", "product": "PART-A", "workOrder": "WO-LEGACY", "originalQuantity": 600, "completedQuantity": 600, "machineId": "C-09", "process": "turning", "inventoryStatus": "delivered"},
            {"id": "unrelated-shipped", "sourceBatchId": "old-other-charge", "product": "PART-B", "workOrder": "WO-OLD-OTHER", "originalQuantity": 40, "completedQuantity": 40, "machineId": "C-02", "process": "turning", "inventoryStatus": "delivered", "deliveredAtTime": "2026-09-16T09:00:00Z"},
        ],
        "wipLots": [{"id": "legacy-lot", "sourceHistoryEntryId": "legacy-wip", "product": "PART-A", "workOrder": "WO-LEGACY", "originalQuantity": 600, "availableQuantity": 600, "deliveredQuantity": 0, "scrappedQuantity": 0}],
        "wipMovements": [{"id": "legacy-move", "lotId": "legacy-lot", "quantity": 600}],
        "processCurrentJobs": [], "processOperationOverrides": [], "productionInterruptions": [],
        "planningEvents": [{"id": "existing-event", "message": "Existing history"}], "planNeedsRecalculation": False,
        "lastAutomaticPlan": {"id": "old-result"}, "planRunSequence": {"id": "old-sequence"},
    }


@pytest.fixture
def legacy(isolated_db):
    seed = synthetic_seed()
    clean = copy.deepcopy(seed)
    clean["manualBatches"] = clean["manualBatches"][1:]
    saved = database.save_planning_state(clean, expected_updated_at="", mode="operational", can_manage_settings=True, route_placement_version=1)
    # Reproduce a pre-guard database. No ordinary mutation is allowed to introduce it.
    with database.connection() as db:
        db.execute("UPDATE planning_state SET seed_json=? WHERE state_key='default'", (json.dumps(seed),))
    return {"seed": seed, "updatedAt": saved["updatedAt"]}


def snapshot():
    with database.connection() as db:
        names = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return {name: sorted([tuple(row) for row in db.execute(f'SELECT * FROM "{name}"')], key=repr) for name in names}


def save(seed, version, **kwargs):
    return database.save_planning_state(seed, expected_updated_at=version, mode=kwargs.pop("mode", "operational"), can_manage_settings=True, route_placement_version=1, **kwargs)


def request(**changes):
    return {"batchId": "ambiguous-charge", "action": "work-order", "workOrder": "WO-VERIFIED-NEW", "reason": "Reviewed physical charge and traveler", **changes}


@pytest.mark.parametrize("mode", ["planning", "operational"])
def test_unrelated_save_commits_and_reloads_without_erasing_legacy_evidence(legacy, mode):
    incoming = copy.deepcopy(legacy["seed"])
    if mode == "planning":
        incoming["orders"][1]["dueDate"] = "2026-09-26"
    else:
        incoming["productionHistory"][2]["deliveredAtTime"] = "2026-09-16T09:01:00Z"
    saved = save(incoming, legacy["updatedAt"], mode=mode)
    assert saved["updatedAt"] != legacy["updatedAt"]
    assert saved["seed"]["planNeedsRecalculation"] is True
    assert saved["seed"]["manualBatches"] == legacy["seed"]["manualBatches"]
    assert saved["seed"]["productionHistory"][:2] == legacy["seed"]["productionHistory"][:2]
    assert saved["seed"]["wipLots"] == legacy["seed"]["wipLots"]
    assert saved["seed"]["wipMovements"] == legacy["seed"]["wipMovements"]
    assert database.planning_state()["seed"] == saved["seed"]
    if mode == "planning":
        assert next(o for o in database.order_details() if o["id"] == "order-b")["dueDate"] == "2026-09-26"
    else:
        assert saved["seed"]["productionHistory"][2]["deliveredAtTime"] == "2026-09-16T09:01:00Z"


@pytest.mark.parametrize("change", ["quantity", "remove", "machine", "history", "wip", "order", "calendar", "new-conflict"])
def test_protected_changes_and_new_conflicts_fail_without_any_persistence(legacy, change):
    incoming = copy.deepcopy(legacy["seed"])
    if change == "quantity": incoming["manualBatches"][0]["quantity"] = 601
    elif change == "remove": incoming["manualBatches"].pop(0)
    elif change == "machine": incoming["machines"][0]["currentJob"] = {"product": "PART-C", "quantity": 1}
    elif change == "history": incoming["productionHistory"][0]["completedQuantity"] = 599
    elif change == "wip": incoming["wipLots"][0]["availableQuantity"] = 599
    elif change == "order": incoming["orders"][0]["quantity"] = 601
    elif change == "calendar": incoming["calendarEvents"] = [{"id": "closure", "machineId": "C-01"}]
    else: incoming["manualBatches"].append(copy.deepcopy(incoming["manualBatches"][1]))
    before = snapshot()
    with pytest.raises(ValueError): save(incoming, legacy["updatedAt"])
    assert snapshot() == before, "rejection must leave seed, orders, histories and versions untouched"


@pytest.mark.parametrize("mode", ["planning", "operational"])
@pytest.mark.parametrize("version", [None, "stale-version"])
def test_force_does_not_override_required_fresh_revision_while_quarantined(legacy, mode, version):
    before = snapshot()
    with pytest.raises(database.PlanningStateConflict):
        save(copy.deepcopy(legacy["seed"]), version, mode=mode, force=True)
    assert snapshot() == before


def test_normal_save_cannot_create_the_legacy_conflict(isolated_db):
    before = snapshot()
    with pytest.raises(ValueError, match="kimliği belirsiz"):
        save(synthetic_seed(), "")
    assert snapshot() == before


@pytest.mark.parametrize("action", ["work-order", "remove-duplicate"])
def test_server_built_repair_preserves_physical_quantities_and_audits_authenticated_actor(legacy, action):
    before_seed = copy.deepcopy(legacy["seed"])
    repair = request(action=action, confirmedDuplicate=True)
    # A submitted seed must not become the authority for a repair.
    saved = save({"orders": [], "productionHistory": []}, legacy["updatedAt"], identity_resolution=repair, actor_id="reviewer", actor_name="Reviewed User")
    actual = saved["seed"]
    assert actual["orders"] == before_seed["orders"]
    for key in ["machines", "productionHistory", "wipLots", "wipMovements", "productionInterruptions", "processCurrentJobs", "processOperationOverrides"]:
        assert actual[key] == before_seed[key]
    if action == "work-order":
        expected = copy.deepcopy(before_seed["manualBatches"])
        expected[0]["workOrder"] = "WO-VERIFIED-NEW"
        assert actual["manualBatches"] == expected
        assert sum(b["quantity"] for b in actual["manualBatches"]) == 800
    else:
        assert actual["manualBatches"] == before_seed["manualBatches"][1:]
        assert actual["manualBatches"][0]["quantity"] == 200
    assert sum(h["completedQuantity"] for h in actual["productionHistory"]) == 1240
    assert actual["wipLots"][0]["availableQuantity"] == 600
    assert actual["planNeedsRecalculation"] is True
    assert "lastAutomaticPlan" not in actual and "planRunSequence" not in actual
    event = actual["planningEvents"][0]
    assert event["batchId"] == "ambiguous-charge"
    assert event["machineId"] == "C-01"
    assert repair["reason"] in event["message"] and "Reviewed User" in event["message"]
    assert actual["planningEvents"][1:] == before_seed["planningEvents"]
    assert database.planning_state()["seed"] == actual
    assert saved["updatedBy"] == {"id": "reviewer", "name": "Reviewed User"}


@pytest.mark.parametrize("repair", [request(reason=" "), request(workOrder="WO-LEGACY"), request(action="remove-duplicate", confirmedDuplicate=False), request(batchId="missing")])
def test_unconfirmed_or_invalid_repairs_leave_all_records_unchanged(legacy, repair):
    before = snapshot()
    with pytest.raises(ValueError): save({}, legacy["updatedAt"], identity_resolution=repair)
    assert snapshot() == before


def test_stale_repair_is_rejected_even_with_force(legacy):
    before = snapshot()
    with pytest.raises(database.PlanningStateConflict):
        save({}, "old", force=True, identity_resolution=request())
    assert snapshot() == before


def test_endpoint_requires_authentication_and_uses_fresh_server_state(legacy):
    client = TestClient(app)
    payload = {"expectedUpdatedAt": legacy["updatedAt"], **request()}
    before = snapshot()
    assert client.post("/api/planning-state/identity-resolution", json=payload).status_code == 401
    assert snapshot() == before
    headers = {"Authorization": f"Bearer {create_test_session('test-password', 'user')}"}
    stale = client.post("/api/planning-state/identity-resolution", json={**payload, "expectedUpdatedAt": "old"}, headers=headers)
    assert stale.status_code == 409
    assert snapshot() == before
    response = client.post("/api/planning-state/identity-resolution", json={**payload, "actor_id": "forged", "actor_name": "Forged User", "seed": {"orders": []}}, headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["seed"]["manualBatches"][0]["workOrder"] == "WO-VERIFIED-NEW"
    assert body["seed"]["productionHistory"] == legacy["seed"]["productionHistory"]
    assert body["updatedBy"]["id"] != "forged"
    assert "Forged User" not in body["seed"]["planningEvents"][0]["message"]
    assert client.get("/api/planning-state", headers=headers).json()["seed"] == body["seed"]
    repaired = snapshot()
    assert client.post("/api/planning-state/identity-resolution", json=payload, headers=headers).status_code == 409
    assert snapshot() == repaired


def test_repair_failure_after_order_write_rolls_back_seed_history_and_version(legacy, monkeypatch):
    before = snapshot()
    original = database._save_orders

    def fail_after_order_write(db, orders, timestamp, replace=False):
        original(db, orders, timestamp, replace)
        raise ValueError("injected failure after order write")

    monkeypatch.setattr(database, "_save_orders", fail_after_order_write)
    with pytest.raises(ValueError, match="injected failure"):
        save({}, legacy["updatedAt"], identity_resolution=request())
    assert snapshot() == before
