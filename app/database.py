from __future__ import annotations

from .production_merge import merge_production_refresh

import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from .config import settings


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(settings.database_path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA busy_timeout = 5000")
    db.execute("PRAGMA synchronous = FULL")
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_database() -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    with connection() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS scenarios (
              id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL,
              notes TEXT NOT NULL DEFAULT '', inputs_json TEXT NOT NULL, result_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS scenarios_created_at_idx ON scenarios(created_at DESC, id DESC);
            CREATE TABLE IF NOT EXISTS customer_orders (
              order_id TEXT PRIMARY KEY, customer TEXT NOT NULL DEFAULT '', customer_order_no TEXT NOT NULL DEFAULT '',
              due_date TEXT NOT NULL DEFAULT '', priority INTEGER NOT NULL DEFAULT 3,
              order_type TEXT NOT NULL DEFAULT 'Kesin sipariş', allow_partial INTEGER NOT NULL DEFAULT 0,
              partial_delivery_quantity REAL NOT NULL DEFAULT 0, partial_delivery_date TEXT NOT NULL DEFAULT '',
              delivery_milestones_json TEXT NOT NULL DEFAULT '[]',
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS order_revisions (
              id TEXT PRIMARY KEY, order_id TEXT NOT NULL, product TEXT NOT NULL, status TEXT NOT NULL,
              created_at TEXT NOT NULL, approved_at TEXT NOT NULL, original_json TEXT NOT NULL,
              request_json TEXT NOT NULL, impact_json TEXT NOT NULL, seed_json TEXT NOT NULL, result_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS planning_state (
              state_key TEXT PRIMARY KEY, seed_json TEXT NOT NULL, updated_at TEXT NOT NULL,
              updated_by_id TEXT NOT NULL DEFAULT '', updated_by_name TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS planning_state_history (
              id TEXT PRIMARY KEY, seed_json TEXT NOT NULL, state_hash TEXT NOT NULL, created_at TEXT NOT NULL,
              created_by_id TEXT NOT NULL DEFAULT '', created_by_name TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS production_sync_baseline (
                state_key TEXT PRIMARY KEY, seed_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS production_sync_state (
              sync_key TEXT PRIMARY KEY, source_updated_at TEXT NOT NULL,
              imported_at TEXT NOT NULL, source_url TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS production_archive_snapshots (
              id TEXT PRIMARY KEY, archive_json TEXT NOT NULL, archive_hash TEXT NOT NULL,
              planning_updated_at TEXT NOT NULL, source TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS demand_import_history (
              id TEXT PRIMARY KEY, imported_at TEXT NOT NULL, source_file TEXT NOT NULL,
              snapshot_date TEXT NOT NULL, dataset_json TEXT NOT NULL, summary_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS app_updates (
              id TEXT PRIMARY KEY, title TEXT NOT NULL, bullets_json TEXT NOT NULL,
              created_at TEXT NOT NULL, seen_at TEXT
            );
            CREATE TABLE IF NOT EXISTS app_user_roles (
              email TEXT PRIMARY KEY COLLATE NOCASE,
              role TEXT NOT NULL CHECK(role IN ('admin','user')),
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS feedbacks (
              id TEXT PRIMARY KEY, author_id TEXT NOT NULL, author_name TEXT NOT NULL,
              page_path TEXT NOT NULL DEFAULT '', body TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','resolved','canceled')),
              priority INTEGER NOT NULL DEFAULT 2 CHECK(priority IN (1,2,3)),
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL, resolved_at TEXT, canceled_at TEXT
            );
            CREATE TABLE IF NOT EXISTS feedback_comments (
              id TEXT PRIMARY KEY, feedback_id TEXT NOT NULL REFERENCES feedbacks(id) ON DELETE CASCADE,
              author_id TEXT NOT NULL, author_name TEXT NOT NULL, body TEXT NOT NULL,
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS feedback_attachments (
              id TEXT PRIMARY KEY, feedback_id TEXT NOT NULL REFERENCES feedbacks(id) ON DELETE CASCADE,
              author_id TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('image','voice','document')),
              original_name TEXT NOT NULL, content_type TEXT NOT NULL, size INTEGER NOT NULL,
              storage_key TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS feedbacks_updated_idx ON feedbacks(updated_at DESC);
            CREATE INDEX IF NOT EXISTS feedback_comments_feedback_idx ON feedback_comments(feedback_id, created_at);
            CREATE INDEX IF NOT EXISTS feedback_attachments_feedback_idx ON feedback_attachments(feedback_id, created_at);
            CREATE INDEX IF NOT EXISTS demand_import_history_imported_idx ON demand_import_history(imported_at DESC);
            CREATE INDEX IF NOT EXISTS planning_state_history_created_idx ON planning_state_history(created_at DESC);
            CREATE INDEX IF NOT EXISTS production_archive_snapshots_created_idx ON production_archive_snapshots(created_at DESC);
            CREATE INDEX IF NOT EXISTS app_updates_created_idx ON app_updates(created_at DESC);
            """
        )
        columns = {row["name"] for row in db.execute("PRAGMA table_info(feedbacks)").fetchall()}
        if "priority" not in columns:
            db.execute("ALTER TABLE feedbacks ADD COLUMN priority INTEGER NOT NULL DEFAULT 2")
        attachment_sql = db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='feedback_attachments'").fetchone()
        if attachment_sql and "'document'" not in (attachment_sql["sql"] or ""):
            db.executescript(
                """
                ALTER TABLE feedback_attachments RENAME TO feedback_attachments_legacy;
                CREATE TABLE feedback_attachments (
                  id TEXT PRIMARY KEY, feedback_id TEXT NOT NULL REFERENCES feedbacks(id) ON DELETE CASCADE,
                  author_id TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('image','voice','document')),
                  original_name TEXT NOT NULL, content_type TEXT NOT NULL, size INTEGER NOT NULL,
                  storage_key TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL
                );
                INSERT INTO feedback_attachments(id,feedback_id,author_id,kind,original_name,content_type,size,storage_key,created_at)
                SELECT id,feedback_id,author_id,kind,original_name,content_type,size,storage_key,created_at
                FROM feedback_attachments_legacy;
                DROP TABLE feedback_attachments_legacy;
                CREATE INDEX IF NOT EXISTS feedback_attachments_feedback_idx ON feedback_attachments(feedback_id, created_at);
                """
            )
        order_columns = {row["name"] for row in db.execute("PRAGMA table_info(customer_orders)").fetchall()}
        if "delivery_milestones_json" not in order_columns:
            db.execute("ALTER TABLE customer_orders ADD COLUMN delivery_milestones_json TEXT NOT NULL DEFAULT '[]'")
        history_columns = {row["name"] for row in db.execute("PRAGMA table_info(planning_state_history)").fetchall()}
        if "state_hash" not in history_columns:
            db.execute("ALTER TABLE planning_state_history ADD COLUMN state_hash TEXT NOT NULL DEFAULT ''")
        history_without_hash = db.execute(
            "SELECT id, seed_json FROM planning_state_history WHERE state_hash=''"
        ).fetchall()
        if history_without_hash:
            db.executemany(
                "UPDATE planning_state_history SET state_hash=? WHERE id=?",
                [
                    (hashlib.sha256(row["seed_json"].encode("utf-8")).hexdigest(), row["id"])
                    for row in history_without_hash
                ],
            )
        if "created_by_id" not in history_columns:
            db.execute("ALTER TABLE planning_state_history ADD COLUMN created_by_id TEXT NOT NULL DEFAULT ''")
        if "created_by_name" not in history_columns:
            db.execute("ALTER TABLE planning_state_history ADD COLUMN created_by_name TEXT NOT NULL DEFAULT ''")
        state_columns = {row["name"] for row in db.execute("PRAGMA table_info(planning_state)").fetchall()}
        if "updated_by_id" not in state_columns:
            db.execute("ALTER TABLE planning_state ADD COLUMN updated_by_id TEXT NOT NULL DEFAULT ''")
        if "updated_by_name" not in state_columns:
            db.execute("ALTER TABLE planning_state ADD COLUMN updated_by_name TEXT NOT NULL DEFAULT ''")
        current_state = db.execute(
            "SELECT seed_json, updated_at FROM planning_state WHERE state_key='default'"
        ).fetchone()
        if current_state is not None:
            _insert_production_archive_snapshot(
                db,
                _loads(current_state["seed_json"]),
                current_state["updated_at"],
                "database-init",
            )


def _loads(value: str) -> Any:
    return json.loads(value)


def order_details() -> list[dict[str, Any]]:
    with connection() as db:
        rows = db.execute("SELECT * FROM customer_orders").fetchall()
    details = []
    for row in rows:
        milestones = _loads(row["delivery_milestones_json"] or "[]")
        if not milestones and row["allow_partial"] and row["partial_delivery_quantity"] and row["partial_delivery_date"]:
            milestones = [{"id": "legacy-partial", "quantity": row["partial_delivery_quantity"], "date": row["partial_delivery_date"]}]
        details.append({
            "id": row["order_id"], "dueDate": row["due_date"], "allowPartial": bool(milestones),
            "partialDeliveryQuantity": milestones[0]["quantity"] if milestones else 0,
            "partialDeliveryDate": milestones[0]["date"] if milestones else "",
            "deliveryMilestones": milestones,
        })
    return details


def save_orders(orders: list[dict[str, Any]]) -> None:
    timestamp = now_iso()
    with connection() as db:
        _save_orders(db, orders, timestamp)


def _save_orders(db: sqlite3.Connection, orders: list[dict[str, Any]], timestamp: str, replace: bool = False) -> None:
    if replace:
        db.execute("DELETE FROM customer_orders")
    db.executemany(
        """INSERT INTO customer_orders (order_id,due_date,allow_partial,partial_delivery_quantity,partial_delivery_date,delivery_milestones_json,updated_at)
        VALUES (?,?,?,?,?,?,?) ON CONFLICT(order_id) DO UPDATE SET due_date=excluded.due_date,
        allow_partial=excluded.allow_partial,partial_delivery_quantity=excluded.partial_delivery_quantity,
        partial_delivery_date=excluded.partial_delivery_date,delivery_milestones_json=excluded.delivery_milestones_json,
        updated_at=excluded.updated_at""",
        [(
            order["id"], order.get("dueDate", ""), int(bool(order.get("deliveryMilestones")) or order.get("allowPartial", False)),
            (order.get("deliveryMilestones") or [{}])[0].get("quantity", order.get("partialDeliveryQuantity", 0)),
            (order.get("deliveryMilestones") or [{}])[0].get("date", order.get("partialDeliveryDate", "")),
            json.dumps(order.get("deliveryMilestones") or [], ensure_ascii=False), timestamp,
        ) for order in orders],
    )


def planning_state() -> dict[str, Any] | None:
    with connection() as db:
        row = db.execute("SELECT seed_json, updated_at, updated_by_id, updated_by_name FROM planning_state WHERE state_key='default'").fetchone()
    if row is None:
        return None
    return {
        "seed": _loads(row["seed_json"]),
        "updatedAt": row["updated_at"],
        "updatedBy": {"id": row["updated_by_id"], "name": row["updated_by_name"]},
    }


def planning_state_history() -> list[dict[str, Any]]:
    with connection() as db:
        rows = db.execute(
            "SELECT id, seed_json, created_at, created_by_id, created_by_name FROM planning_state_history ORDER BY created_at DESC LIMIT 20"
        ).fetchall()
    return [{
        "id": row["id"],
        "seed": _loads(row["seed_json"]),
        "createdAt": row["created_at"],
        "createdBy": {"id": row["created_by_id"], "name": row["created_by_name"]},
    } for row in rows]


def production_archive_history() -> list[dict[str, Any]]:
    """Return the durable, unpruned archive snapshots used for recovery."""
    with connection() as db:
        rows = db.execute(
            """SELECT id, archive_json, archive_hash, planning_updated_at, source, created_at
            FROM production_archive_snapshots ORDER BY created_at DESC"""
        ).fetchall()
    return [{
        "id": row["id"],
        "productionHistory": _loads(row["archive_json"]),
        "archiveHash": row["archive_hash"],
        "planningUpdatedAt": row["planning_updated_at"],
        "source": row["source"],
        "createdAt": row["created_at"],
    } for row in rows]


def production_sync_status() -> dict[str, Any] | None:
    with connection() as db:
        row = db.execute(
            "SELECT source_updated_at, imported_at, source_url FROM production_sync_state WHERE sync_key='production'"
        ).fetchone()
    if row is None:
        return None
    return {
        "sourceUpdatedAt": row["source_updated_at"],
        "importedAt": row["imported_at"],
        "sourceUrl": row["source_url"],
    }


class PlanningStateConflict(RuntimeError):
    def __init__(self, current: dict[str, Any]):
        super().__init__("Planning state was updated by another session.")
        self.current = current


class ProtectedSettingsChange(RuntimeError):
    pass


PROTECTED_SETTINGS_FIELDS = ("holidays", "calendarEvents", "setupSettings")


def protected_settings_changed(incoming: dict[str, Any], current: dict[str, Any] | None) -> bool:
    if current is None:
        return any(incoming.get(field) not in (None, [], {}) for field in PROTECTED_SETTINGS_FIELDS)
    return any(incoming.get(field) != current.get(field) for field in PROTECTED_SETTINGS_FIELDS)


def _insert_planning_history(
    db: sqlite3.Connection,
    seed: dict[str, Any],
    serialized_seed: str,
    timestamp: str,
    prefix: str = "planning",
    actor_id: str = "",
    actor_name: str = "",
) -> dict[str, Any]:
    history_id = f"{prefix}-{uuid.uuid4()}"
    state_hash = hashlib.sha256(serialized_seed.encode("utf-8")).hexdigest()
    db.execute(
        "INSERT INTO planning_state_history(id,seed_json,state_hash,created_at,created_by_id,created_by_name) VALUES(?,?,?,?,?,?)",
        (history_id, serialized_seed, state_hash, timestamp, actor_id, actor_name),
    )
    stale = db.execute(
        "SELECT id FROM planning_state_history ORDER BY created_at DESC LIMIT -1 OFFSET 20"
    ).fetchall()
    if stale:
        db.executemany("DELETE FROM planning_state_history WHERE id=?", [(row["id"],) for row in stale])
    return {"id": history_id, "seed": seed, "createdAt": timestamp, "createdBy": {"id": actor_id, "name": actor_name}}


OPERATIONAL_ROOT_FIELDS = (
    "productionHistory",
    "wipLots",
    "wipMovements",
    "planningEvents",
    "processCurrentJobs",
)


def preserve_live_operations(incoming: dict[str, Any], current: dict[str, Any] | None) -> dict[str, Any]:
    """Apply planning inputs without allowing a stale snapshot to replace factory truth."""
    if current is None:
        return incoming
    merged = json.loads(json.dumps(incoming, ensure_ascii=False))
    for field in OPERATIONAL_ROOT_FIELDS:
        if field in current:
            merged[field] = current[field]

    current_machines = {
        machine.get("id"): machine
        for machine in current.get("machines", [])
        if isinstance(machine, dict) and isinstance(machine.get("id"), str)
    }
    for machine in merged.get("machines", []):
        if not isinstance(machine, dict):
            continue
        live_machine = current_machines.get(machine.get("id"))
        if live_machine is None:
            continue
        if "currentJob" in live_machine:
            machine["currentJob"] = live_machine["currentJob"]
        if "operationalAvailableStart" in live_machine:
            machine["operationalAvailableStart"] = live_machine["operationalAvailableStart"]
    return merged


def _insert_production_archive_snapshot(
    db: sqlite3.Connection,
    seed: dict[str, Any],
    planning_updated_at: str,
    source: str,
) -> dict[str, Any] | None:
    archive = seed.get("productionHistory")
    if not isinstance(archive, list):
        archive = []
    serialized = json.dumps(archive, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    archive_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    latest = db.execute(
        "SELECT archive_hash FROM production_archive_snapshots ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    if latest is not None and latest["archive_hash"] == archive_hash:
        return None
    snapshot_id = f"archive-{uuid.uuid4()}"
    created_at = now_iso()
    db.execute(
        """INSERT INTO production_archive_snapshots
        (id,archive_json,archive_hash,planning_updated_at,source,created_at)
        VALUES(?,?,?,?,?,?)""",
        (snapshot_id, serialized, archive_hash, planning_updated_at, source, created_at),
    )
    return {
        "id": snapshot_id,
        "productionHistory": archive,
        "archiveHash": archive_hash,
        "planningUpdatedAt": planning_updated_at,
        "source": source,
        "createdAt": created_at,
    }


def save_planning_state(
    seed: dict[str, Any],
    expected_updated_at: str | None = None,
    force: bool = False,
    mode: str = "planning",
    actor_id: str = "",
    actor_name: str = "",
    can_manage_settings: bool = False,
) -> dict[str, Any]:
    timestamp = now_iso()
    with connection() as db:
        row = db.execute("SELECT seed_json, updated_at FROM planning_state WHERE state_key='default'").fetchone()
        current = None if row is None else {"seed": _loads(row["seed_json"]), "updatedAt": row["updated_at"]}
        current_updated_at = current["updatedAt"] if current else ""
        if not force and expected_updated_at is not None and current_updated_at != expected_updated_at:
            raise PlanningStateConflict(current or {"seed": None, "updatedAt": ""})
        if not can_manage_settings and protected_settings_changed(seed, current["seed"] if current else None):
            raise ProtectedSettingsChange("Ayarlar yalnızca yöneticiler tarafından değiştirilebilir")
        saved_seed = preserve_live_operations(seed, current["seed"] if current else None) if mode == "planning" else seed
        serialized_seed = json.dumps(saved_seed, ensure_ascii=False)
        db.execute(
            """INSERT INTO planning_state(state_key,seed_json,updated_at,updated_by_id,updated_by_name) VALUES('default',?,?,?,?)
            ON CONFLICT(state_key) DO UPDATE SET seed_json=excluded.seed_json,updated_at=excluded.updated_at,
            updated_by_id=excluded.updated_by_id,updated_by_name=excluded.updated_by_name""",
            (serialized_seed, timestamp, actor_id, actor_name),
        )
        history_entry = _insert_planning_history(db, saved_seed, serialized_seed, timestamp, actor_id=actor_id, actor_name=actor_name)
        archive_snapshot = _insert_production_archive_snapshot(db, saved_seed, timestamp, mode)
    return {"seed": saved_seed, "updatedAt": timestamp, "updatedBy": {"id": actor_id, "name": actor_name}, "historyEntry": history_entry, "archiveSnapshot": archive_snapshot}


def replace_planning_state_from_production(
    seed: dict[str, Any],
    source_updated_at: str,
    source_url: str,
    scenario_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Atomically refresh source data while retaining local edits and operational state."""
    timestamp = now_iso()
    source_seed = seed
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        local_row = db.execute("SELECT seed_json FROM planning_state WHERE state_key='default'").fetchone()
        base_row = db.execute("SELECT seed_json FROM production_sync_baseline WHERE state_key='production'").fetchone()
        seed = merge_production_refresh(source_seed, _loads(local_row["seed_json"]) if local_row else None,
                                        _loads(base_row["seed_json"]) if base_row else None)
        serialized_seed = json.dumps(seed, ensure_ascii=False)
        db.execute("INSERT INTO production_sync_baseline VALUES('production',?) ON CONFLICT(state_key) DO UPDATE SET seed_json=excluded.seed_json",
                   (json.dumps(source_seed, ensure_ascii=False),))
        db.execute(
            """INSERT INTO planning_state(state_key,seed_json,updated_at,updated_by_id,updated_by_name) VALUES('default',?,?,?,?)
            ON CONFLICT(state_key) DO UPDATE SET seed_json=excluded.seed_json,updated_at=excluded.updated_at,
            updated_by_id=excluded.updated_by_id,updated_by_name=excluded.updated_by_name""",
            (serialized_seed, timestamp, "system:production-sync", "Üretim senkronizasyonu"),
        )
        history_entry = _insert_planning_history(
            db,
            seed,
            serialized_seed,
            timestamp,
            "production-sync",
            "system:production-sync",
            "Üretim senkronizasyonu",
        )
        archive_snapshot = _insert_production_archive_snapshot(db, seed, timestamp, "production-sync")
        _save_orders(db, list(seed.get("orders") or []), timestamp, replace=True)
        db.executemany(
            """INSERT OR IGNORE INTO scenarios(id,name,created_at,notes,inputs_json,result_json)
            VALUES(?,?,?,?,?,?)""",
            [(
                scenario["id"],
                scenario["name"],
                scenario["createdAt"],
                scenario["notes"],
                json.dumps(scenario["seed"], ensure_ascii=False),
                json.dumps(scenario["result"], ensure_ascii=False),
            ) for scenario in scenario_records],
        )
        db.execute(
            """INSERT INTO production_sync_state(sync_key,source_updated_at,imported_at,source_url)
            VALUES('production',?,?,?) ON CONFLICT(sync_key) DO UPDATE SET
            source_updated_at=excluded.source_updated_at,imported_at=excluded.imported_at,source_url=excluded.source_url""",
            (source_updated_at, timestamp, source_url),
        )
    scenario_records = scenarios()
    planning_record = {"seed": seed, "updatedAt": timestamp}
    return {
        "planningState": planning_record,
        "sourceUpdatedAt": source_updated_at,
        "importedAt": timestamp,
        "sourceUrl": source_url,
        "historyEntry": history_entry,
        "archiveSnapshot": archive_snapshot,
        "scenarios": scenario_records,
    }


def demand_import_history() -> list[dict[str, Any]]:
    with connection() as db:
        rows = db.execute(
            "SELECT id,imported_at,source_file,snapshot_date,dataset_json,summary_json FROM demand_import_history ORDER BY imported_at DESC LIMIT 20"
        ).fetchall()
    return [{
        "id": row["id"],
        "importedAt": row["imported_at"],
        "sourceFile": row["source_file"],
        "snapshotDate": row["snapshot_date"],
        "dataset": _loads(row["dataset_json"]),
        "summary": _loads(row["summary_json"]),
    } for row in rows]


def save_demand_import_history(record: dict[str, Any]) -> dict[str, Any]:
    timestamp = now_iso()
    with connection() as db:
        db.execute(
            """INSERT INTO demand_import_history(id,imported_at,source_file,snapshot_date,dataset_json,summary_json,created_at)
            VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET imported_at=excluded.imported_at,
            source_file=excluded.source_file,snapshot_date=excluded.snapshot_date,
            dataset_json=excluded.dataset_json,summary_json=excluded.summary_json""",
            (
                record["id"], record["importedAt"], record["sourceFile"], record["snapshotDate"],
                json.dumps(record["dataset"], ensure_ascii=False),
                json.dumps(record["summary"], ensure_ascii=False),
                timestamp,
            ),
        )
        stale = db.execute(
            "SELECT id FROM demand_import_history ORDER BY imported_at DESC LIMIT -1 OFFSET 20"
        ).fetchall()
        if stale:
            db.executemany("DELETE FROM demand_import_history WHERE id=?", [(row["id"],) for row in stale])
    return record


def scenarios() -> list[dict[str, Any]]:
    with connection() as db:
        rows = db.execute("SELECT * FROM scenarios ORDER BY created_at DESC").fetchall()
    return [{"id": row["id"], "name": row["name"], "createdAt": row["created_at"], "notes": row["notes"], "seed": _loads(row["inputs_json"]), "result": _loads(row["result_json"])} for row in rows]


def scenario_summaries(limit: int = 20, offset: int = 0) -> dict[str, Any]:
    safe_limit = max(1, min(100, int(limit)))
    safe_offset = max(0, int(offset))
    with connection() as db:
        total = int(db.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0])
        rows = db.execute(
            """SELECT id,name,created_at,notes,
            COALESCE(json_extract(result_json, '$.summary.plannedBatchCount'), 0) AS planned_batch_count,
            json_extract(result_json, '$.planRun') AS result_plan_run,
            json_extract(inputs_json, '$.activePlanRun') AS seed_plan_run
            FROM scenarios ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?""",
            (safe_limit, safe_offset),
        ).fetchall()
    items = []
    for row in rows:
        raw_plan_run = row["result_plan_run"] or row["seed_plan_run"]
        items.append({
            "id": row["id"],
            "name": row["name"],
            "createdAt": row["created_at"],
            "notes": row["notes"],
            "plannedBatchCount": max(0, int(row["planned_batch_count"] or 0)),
            "planRun": _loads(raw_plan_run) if raw_plan_run else None,
        })
    return {"items": items, "total": total, "limit": safe_limit, "offset": safe_offset, "hasMore": safe_offset + len(items) < total}


def scenario_record(scenario_id: str) -> dict[str, Any] | None:
    with connection() as db:
        row = db.execute("SELECT * FROM scenarios WHERE id=?", (scenario_id,)).fetchone()
    if row is None:
        return None
    return {"id": row["id"], "name": row["name"], "createdAt": row["created_at"], "notes": row["notes"], "seed": _loads(row["inputs_json"]), "result": _loads(row["result_json"])}


def revisions() -> list[dict[str, Any]]:
    with connection() as db:
        rows = db.execute("SELECT * FROM order_revisions ORDER BY approved_at DESC").fetchall()
    return [{"id": row["id"], "orderId": row["order_id"], "product": row["product"], "status": row["status"], "createdAt": row["created_at"], "approvedAt": row["approved_at"], "original": _loads(row["original_json"]), "requested": _loads(row["request_json"]), "impact": _loads(row["impact_json"]), "seed": _loads(row["seed_json"]), "result": _loads(row["result_json"])} for row in rows]


def app_update_record(db: sqlite3.Connection, update_id: str) -> dict[str, Any] | None:
    row = db.execute("SELECT * FROM app_updates WHERE id=?", (update_id,)).fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "title": row["title"],
        "bullets": _loads(row["bullets_json"]),
        "created_at": row["created_at"],
        "seen_at": row["seen_at"],
    }


def all_app_updates() -> list[dict[str, Any]]:
    with connection() as db:
        rows = db.execute("SELECT id FROM app_updates ORDER BY created_at DESC").fetchall()
        return [record for row in rows if (record := app_update_record(db, row["id"])) is not None]


def app_user_role(email: str) -> str | None:
    normalized = email.strip().lower()
    if not normalized:
        return None
    with connection() as db:
        row = db.execute("SELECT role FROM app_user_roles WHERE email=?", (normalized,)).fetchone()
    return str(row["role"]) if row else None


def feedback_record(db: sqlite3.Connection, feedback_id: str) -> dict[str, Any] | None:
    row = db.execute("SELECT * FROM feedbacks WHERE id=?", (feedback_id,)).fetchone()
    if row is None:
        return None
    comments = [dict(item) for item in db.execute("SELECT * FROM feedback_comments WHERE feedback_id=? ORDER BY created_at", (feedback_id,)).fetchall()]
    attachments = []
    for item in db.execute("SELECT * FROM feedback_attachments WHERE feedback_id=? ORDER BY created_at", (feedback_id,)).fetchall():
        attachment = dict(item)
        attachment["url"] = f"/api/attachments/{attachment['id']}/content"
        attachments.append(attachment)
    record = dict(row)
    record["comments"] = comments
    record["attachments"] = attachments
    return record


def all_feedback() -> list[dict[str, Any]]:
    with connection() as db:
        ids = [row["id"] for row in db.execute("SELECT id FROM feedbacks ORDER BY updated_at DESC").fetchall()]
        return [record for feedback_id in ids if (record := feedback_record(db, feedback_id)) is not None]
