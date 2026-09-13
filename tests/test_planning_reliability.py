import copy
import importlib.util
import json
from pathlib import Path
import sqlite3

from app.database import preserve_live_operations


def test_live_operation_merge_marks_changed_calculation_stale_without_touching_inputs():
    incoming = {"machines": [{"id": "C-01", "currentJob": {"quantity": 480}}], "productionHistory": [], "planNeedsRecalculation": False}
    live = {"machines": [{"id": "C-01", "currentJob": {"quantity": 240}}], "productionHistory": [{"id": "delivery", "completedQuantity": 240}]}
    before = copy.deepcopy((incoming, live))
    saved = preserve_live_operations(incoming, live)
    assert saved["planNeedsRecalculation"] is True
    assert saved["machines"] == live["machines"]
    assert saved["productionHistory"] == live["productionHistory"]
    assert (incoming, live) == before


def test_unchanged_operations_do_not_invalidate_plan_but_old_clients_preserve_dirty_marker():
    live = {"machines": [], "productionHistory": [], "planNeedsRecalculation": True}
    incoming = {"machines": [], "productionHistory": []}
    assert preserve_live_operations(incoming, live)["planNeedsRecalculation"] is True
    incoming["planNeedsRecalculation"] = False
    assert preserve_live_operations(incoming, live)["planNeedsRecalculation"] is False
    live["planningEvents"] = [{"message": "note"}]
    assert preserve_live_operations(incoming, live)["planNeedsRecalculation"] is False


def test_readonly_export_is_consistent_and_does_not_modify_database(tmp_path):
    source = Path(__file__).resolve().parents[1] / "scripts/export_readonly_planning_snapshot.py"
    spec = importlib.util.spec_from_file_location("readonly_snapshot", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    database = tmp_path / "source.sqlite"
    with sqlite3.connect(database) as db:
        db.execute("CREATE TABLE planning_state(state_key TEXT, seed_json TEXT, updated_at TEXT)")
        db.execute("INSERT INTO planning_state VALUES(?,?,?)", ("default", json.dumps({"orders": [{"quantity": 480}]}), "2026-09-10T12:00:00Z"))
    before = database.read_bytes()
    snapshot = module.export_snapshot(database)
    assert snapshot["seed"]["orders"][0]["quantity"] == 480
    assert snapshot["sourceUpdatedAt"] == "2026-09-10T12:00:00Z"
    assert len(snapshot["seedSha256"]) == 64
    assert database.read_bytes() == before
    assert set(snapshot) == {"capturedAt", "sourceUpdatedAt", "seedSha256", "seed"}


def test_plan_and_order_dates_commit_together_and_conflict_or_failure_rolls_back(tmp_path, monkeypatch):
    from app import database as db_module
    from types import SimpleNamespace
    import pytest

    monkeypatch.setattr(db_module, "settings", SimpleNamespace(database_path=tmp_path / "atomic.sqlite", upload_dir=tmp_path / "uploads"))
    db_module.init_database()
    first = db_module.save_planning_state({"orders": [{"id": "order", "dueDate": "2026-09-05"}]}, expected_updated_at="")
    second = db_module.save_planning_state({"orders": [{"id": "order", "dueDate": "2026-09-12"}]}, expected_updated_at=first["updatedAt"])
    assert db_module.order_details()[0]["dueDate"] == "2026-09-12"
    with pytest.raises(db_module.PlanningStateConflict):
        db_module.save_planning_state({"orders": [{"id": "order", "dueDate": "2026-10-03"}]}, expected_updated_at=first["updatedAt"])
    assert db_module.order_details()[0]["dueDate"] == "2026-09-12"
    assert db_module.planning_state()["seed"] == second["seed"]
    original = db_module._save_orders
    def fail_after_dates(db, orders, timestamp, replace=False):
        original(db, orders, timestamp, replace)
        raise ValueError("injected failure after writing dates")
    monkeypatch.setattr(db_module, "_save_orders", fail_after_dates)
    with pytest.raises(ValueError, match="injected failure"):
        db_module.save_planning_state({"orders": [{"id": "order", "dueDate": "2026-10-03"}]}, expected_updated_at=second["updatedAt"])
    assert db_module.order_details()[0]["dueDate"] == "2026-09-12"
    assert db_module.planning_state()["updatedAt"] == second["updatedAt"]
    assert db_module.planning_state()["seed"] == second["seed"]


def test_interrupted_production_survives_planning_and_source_refresh():
    from app.production_merge import merge_production_refresh
    interruption = {"id": "pause-1", "chargeId": "charge-1", "process": "turning", "resourceId": "C-01", "producedQuantity": 200, "remainingQuantity": 400, "reason": "Çelik bitti"}
    live = {"productionInterruptions": [interruption], "wipLots": [{"id": "lot", "availableQuantity": 200}], "manualBatches": [{"id": "charge-1", "quantity": 400}]}
    incoming = {"productionInterruptions": [], "wipLots": [], "planNeedsRecalculation": False}
    before = copy.deepcopy(live)
    saved = preserve_live_operations(incoming, live)
    assert saved["productionInterruptions"] == [interruption]
    assert saved["planNeedsRecalculation"] is True
    refreshed = merge_production_refresh(incoming, live, {"productionInterruptions": [], "wipLots": []})
    assert refreshed["productionInterruptions"] == [interruption]
    assert refreshed["manualBatches"][0]["quantity"] == 400
    assert live == before


def test_interruption_save_reload_conflict_and_old_client_failure_are_atomic(tmp_path, monkeypatch):
    from app import database as db_module
    from types import SimpleNamespace
    import pytest
    monkeypatch.setattr(db_module, "settings", SimpleNamespace(database_path=tmp_path / "paused.sqlite", upload_dir=tmp_path / "uploads"))
    db_module.init_database()
    seed = {"productionInterruptions": [{"id": "pause-1", "producedQuantity": 200, "remainingQuantity": 400}], "orders": []}
    saved = db_module.save_planning_state(seed, expected_updated_at="", mode="operational")
    assert db_module.planning_state()["seed"] == seed
    with pytest.raises(ValueError, match="Yarım üretim"):
        db_module.save_planning_state({"orders": []}, expected_updated_at=saved["updatedAt"], mode="operational")
    assert db_module.planning_state()["seed"] == seed
    with pytest.raises(db_module.PlanningStateConflict):
        db_module.save_planning_state({"productionInterruptions": [], "orders": []}, expected_updated_at="old", mode="operational")
    assert db_module.planning_state()["updatedAt"] == saved["updatedAt"]
