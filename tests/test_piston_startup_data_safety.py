"""Piston release: startup must retain existing production and shared records.

Only synthetic temporary SQLite files are used. This tests the real lifespan,
not a live database or a copied migration implementation.
"""
import asyncio
import hashlib
import json
from types import SimpleNamespace

import pytest

from app import database
from app import main
from app.production_area import production_area


def synthetic_seed(legacy_defaults=False):
    seed = {
        "productionArea": "torna", "source": "synthetic-startup-safety", "planNeedsRecalculation": True,
        "orders": [{"id": "order-1500", "product": "PISTON", "quantity": 1500, "dueDate": "2026-10-31"}],
        "machines": [{"id": "C-04", "active": True, "currentJob": {"batchId": "current-1500", "workOrder": "WO-CURRENT",
            "product": "PISTON", "quantity": 1500, "originalQuantity": 1500, "remainingQuantity": 1000,
            "start": 46200, "end": 46202, "remainingAsOf": 46201}}],
        "processCurrentJobs": [{"operationId": "drilling-current", "batchId": "lot-300", "wipLotId": "lot-300", "process": "drilling",
            "resourceId": "D-01", "product": "PISTON", "workOrder": "WO-PROCESS", "originalQuantity": 300, "remainingQuantity": 200,
            "start": 46200, "end": 46202, "remainingAsOf": 46201}],
        "productionHistory": [{"id": "history-450", "sourceBatchId": "old-charge", "product": "PISTON", "workOrder": "WO-CLOSED",
            "machineId": "C-04", "completedQuantity": 450, "originalQuantity": 450, "deliveredQuantity": 353,
            "inventoryStatus": "scrapped", "completedAt": 46199}],
        "wipLots": [{"id": "lot-300", "sourceHistoryEntryId": "history-300", "product": "PISTON", "workOrder": "WO-PROCESS",
            "originalQuantity": 300, "availableQuantity": 300, "deliveredQuantity": 0, "scrappedQuantity": 0, "nextProcess": "drilling"}],
        "wipMovements": [{"id": "movement-353", "lotId": "old-lot", "kind": "delivered", "quantity": 353}],
        "manualBatches": [{"id": "locked-500", "machineId": "C-05", "product": "PISTON", "quantity": 500,
            "workOrder": "WO-LOCKED", "locked": True, "status": "planned", "start": 46203, "end": 46204}],
        "productionInterruptions": [{"id": "partial-500", "chargeId": "locked-500", "process": "turning", "producedQuantity": 100,
            "remainingQuantity": 500, "kind": "partial-completion"}],
        "productionCancellations": [{"id": "cancellation-1000", "version": 1, "process": "turning", "product": "PISTON",
            "chargeId": "cancelled-charge", "machineId": "C-04", "workOrder": "WO-CANCELLED", "assignedQuantity": 1500,
            "completedQuantity": 500, "cancelledQuantity": 1000, "reason": "Synthetic preserved review", "orderIds": ["order-1500"],
            "orderQuantities": {"order-1500": 1500}, "cancelledAt": "2026-10-17T10:00:00Z", "recordedById": "operator",
            "review": {"status": "pending"}}],
        "processWaitSettings": {"version": 1, "pistonTurningToDrillingDays": 0},
        "adviceSettings": {"version": 1, "staleChargeDays": 9},
        "rawMaterialSettings": {"scrapPercent": 7, "stockDate": "2026-10-17", "stocks": [{"materialCode": "SYNTH", "kg": 123}]},
        "productWeights": [],
    }
    if legacy_defaults:
        del seed["rawMaterialSettings"]
        del seed["productWeights"]
    return seed


def table_rows(path):
    import sqlite3
    with sqlite3.connect(path) as db:
        db.row_factory = sqlite3.Row
        names = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        return {name: sorted([dict(row) for row in db.execute(f'SELECT * FROM "{name}"')], key=lambda row: json.dumps(row, sort_keys=True)) for name in names}


def populate(seed):
    text = json.dumps(seed, ensure_ascii=False)
    timestamp = "2026-10-17T10:00:00Z"
    with database.connection() as db:
        db.execute("INSERT INTO planning_state VALUES (?,?,?,?,?)", ("default", text, timestamp, "operator", "Synthetic operator"))
        db.execute("INSERT INTO planning_state_history VALUES (?,?,?,?,?,?)", ("version-1", text, hashlib.sha256(text.encode()).hexdigest(), timestamp, "operator", "Synthetic operator"))
        db.execute("INSERT INTO scenarios VALUES (?,?,?,?,?,?)", ("scenario-1", "Synthetic alternative", timestamp, "Retain", text, '{"batches":[]}'))
        db.execute("INSERT INTO customer_orders(order_id,customer,due_date,delivery_milestones_json,updated_at) VALUES (?,?,?,?,?)", ("order-1500", "Synthetic customer", "2026-10-31", '[{"id":"partial","quantity":353,"date":"2026-10-24"}]', timestamp))
        db.execute("INSERT INTO order_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("revision-1", "order-1500", "PISTON", "approved", timestamp, timestamp, text, "{}", "{}", text, '{"batches":[]}'))
        db.execute("INSERT INTO production_sync_baseline VALUES (?,?)", ("default", text))
        db.execute("INSERT INTO production_sync_state VALUES (?,?,?,?)", ("production", timestamp, timestamp, "synthetic-offline-source"))
        db.execute("INSERT INTO production_archive_snapshots VALUES (?,?,?,?,?,?)", ("archive-existing", "[]", hashlib.sha256(b"[]").hexdigest(), timestamp, "synthetic-history", timestamp))
        db.execute("INSERT INTO app_user_roles VALUES (?,?,?)", ("admin@example.test", "admin", timestamp))
        db.execute("INSERT INTO app_user_roles VALUES (?,?,?)", ("planner@example.test", "user", timestamp))
        db.execute("INSERT INTO feedbacks(id,author_id,author_name,body,created_at,updated_at) VALUES (?,?,?,?,?,?)", ("feedback-1", "operator", "Synthetic operator", "Keep this record", timestamp, timestamp))
        db.execute("INSERT INTO feedback_comments VALUES (?,?,?,?,?,?,?)", ("comment-1", "feedback-1", "operator", "Synthetic operator", "Keep comment", timestamp, timestamp))
        db.execute("INSERT INTO feedback_attachments VALUES (?,?,?,?,?,?,?,?,?)", ("attachment-1", "feedback-1", "operator", "document", "synthetic.txt", "text/plain", 42, "synthetic-key", timestamp))
        db.execute("INSERT INTO app_updates VALUES (?,?,?,?,?)", ("update-1", "Synthetic notice", '["Keep"]', timestamp, timestamp))
        db.execute("INSERT INTO demand_import_history VALUES (?,?,?,?,?,?,?)", ("import-1", timestamp, "synthetic.xlsx", "2026-10-17", '{"rows":[]}', '{"quantity":1500}', timestamp))


@pytest.mark.parametrize("environment", ["production", "staging"])
@pytest.mark.parametrize("legacy_defaults", [False, True])
def test_real_startup_preserves_rows_and_is_idempotent(tmp_path, monkeypatch, environment, legacy_defaults):
    path = tmp_path / "synthetic.sqlite"
    monkeypatch.setattr(database, "settings", SimpleNamespace(database_path=path, upload_dir=tmp_path / "uploads"))
    monkeypatch.setattr(main, "settings", SimpleNamespace(app_env=environment))
    token = production_area.set("torna")
    try:
        # Establish the current staging-base schema; no production file is read.
        database.init_database()
        seed = synthetic_seed(legacy_defaults)
        populate(seed)
        before = table_rows(path)

        async def start():
            async with main.lifespan(main.app):
                pass

        asyncio.run(start())
        after = table_rows(path)
        for table, rows in before.items():
            if table not in ("planning_state", "production_archive_snapshots"):
                assert after[table] == rows, table
        persisted = json.loads(after["planning_state"][0]["seed_json"])
        for key, value in seed.items():
            assert persisted[key] == value, key
        assert after["planning_state"][0]["state_key"] == "default"
        assert after["planning_state"][0]["updated_by_id"] == "operator"
        if not legacy_defaults:
            assert after["planning_state"] == before["planning_state"]
        else:
            assert set(persisted) - set(seed) == {"rawMaterialSettings", "productWeights"}
        assert len(after["production_archive_snapshots"]) == 2
        assert before["production_archive_snapshots"][0] in after["production_archive_snapshots"]
        new_archive = next(row for row in after["production_archive_snapshots"] if row["id"] != "archive-existing")
        assert json.loads(new_archive["archive_json"]) == seed["productionHistory"]
        assert path.with_name("synthetic-cubuk-filtre.sqlite").exists() is (environment == "staging")

        asyncio.run(start())
        assert table_rows(path) == after
    finally:
        production_area.reset(token)


def test_failed_legacy_default_initialization_rolls_back_and_can_retry(tmp_path, monkeypatch):
    path = tmp_path / "synthetic-failed-startup.sqlite"
    monkeypatch.setattr(database, "settings", SimpleNamespace(database_path=path, upload_dir=tmp_path / "uploads"))
    token = production_area.set("torna")
    try:
        database.init_database()
        seed = synthetic_seed(legacy_defaults=True)
        populate(seed)
        before = table_rows(path)
        original = database.initial_product_weights

        def unavailable_weights():
            raise RuntimeError("Synthetic startup failure after raw material initialization")

        monkeypatch.setattr(database, "initial_product_weights", unavailable_weights)
        with pytest.raises(RuntimeError, match="Synthetic startup failure"):
            database.init_database()
        assert table_rows(path) == before
        monkeypatch.setattr(database, "initial_product_weights", original)
        database.init_database()
        persisted = database.planning_state()["seed"]
        for key, value in seed.items():
            assert persisted[key] == value, key
        after = table_rows(path)
        database.init_database()
        assert table_rows(path) == after
    finally:
        production_area.reset(token)
