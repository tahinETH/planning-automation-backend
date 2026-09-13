import copy
from types import SimpleNamespace

import pytest

from app import database
from app.production_merge import merge_production_refresh


def test_route_commitments_save_reload_refresh_and_stale_client_rejection(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "settings", SimpleNamespace(database_path=tmp_path / "route.sqlite", upload_dir=tmp_path / "uploads"))
    database.init_database()
    seed = {"orders": [{"id": "order", "quantity": 1200, "dueDate": "2026-09-20"}],
            "manualBatches": [{"id": "charge-Z", "quantity": 600, "routeCommitted": True}],
            "processOperationOverrides": [{"batchId": "charge-Z", "process": "drilling", "resourceId": "D-01", "queueOrder": 0, "routeMode": "priority", "requestedStart": 46200, "sourceProduct": "R-TEST", "routeTargetDate": "2026-09-15"}]}
    before = copy.deepcopy(seed)
    saved = database.save_planning_state(seed, expected_updated_at="", mode="operational", route_placement_version=1)
    assert database.planning_state()["seed"] == seed
    assert database.order_details()[0]["dueDate"] == "2026-09-20"
    refreshed = merge_production_refresh({"orders": []}, seed, {})
    assert refreshed["manualBatches"] == seed["manualBatches"]
    assert refreshed["processOperationOverrides"] == seed["processOperationOverrides"]
    with pytest.raises(ValueError, match="Eski sürüm"):
        database.save_planning_state({"orders": []}, expected_updated_at=saved["updatedAt"], mode="operational")
    with pytest.raises(database.PlanningStateConflict):
        database.save_planning_state({"orders": []}, expected_updated_at="old", route_placement_version=1)
    assert database.planning_state()["seed"] == saved["seed"]
    assert database.planning_state()["updatedAt"] == saved["updatedAt"]
    assert seed == before


def test_route_and_order_save_failure_rolls_back_together(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "settings", SimpleNamespace(database_path=tmp_path / "atomic-route.sqlite", upload_dir=tmp_path / "uploads"))
    database.init_database()
    first = database.save_planning_state({"orders": [{"id": "order", "dueDate": "2026-09-20"}]}, expected_updated_at="")
    original = database._save_orders
    def fail(db, orders, timestamp, replace=False):
        original(db, orders, timestamp, replace)
        raise ValueError("injected failure")
    monkeypatch.setattr(database, "_save_orders", fail)
    with pytest.raises(ValueError, match="injected failure"):
        database.save_planning_state({"orders": [{"id": "order", "dueDate": "2026-09-25"}], "manualBatches": [{"id": "Z", "routeCommitted": True}]}, expected_updated_at=first["updatedAt"], mode="operational", route_placement_version=1)
    assert database.planning_state()["seed"] == first["seed"]
    assert database.planning_state()["updatedAt"] == first["updatedAt"]
    assert database.order_details()[0]["dueDate"] == "2026-09-20"
