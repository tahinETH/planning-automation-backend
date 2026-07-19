from __future__ import annotations

import json
import sqlite3
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
            CREATE TABLE IF NOT EXISTS customer_orders (
              order_id TEXT PRIMARY KEY, customer TEXT NOT NULL DEFAULT '', customer_order_no TEXT NOT NULL DEFAULT '',
              due_date TEXT NOT NULL DEFAULT '', priority INTEGER NOT NULL DEFAULT 3,
              order_type TEXT NOT NULL DEFAULT 'Kesin sipariş', allow_partial INTEGER NOT NULL DEFAULT 0,
              partial_delivery_quantity REAL NOT NULL DEFAULT 0, partial_delivery_date TEXT NOT NULL DEFAULT '',
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS order_revisions (
              id TEXT PRIMARY KEY, order_id TEXT NOT NULL, product TEXT NOT NULL, status TEXT NOT NULL,
              created_at TEXT NOT NULL, approved_at TEXT NOT NULL, original_json TEXT NOT NULL,
              request_json TEXT NOT NULL, impact_json TEXT NOT NULL, seed_json TEXT NOT NULL, result_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS planning_state (
              state_key TEXT PRIMARY KEY, seed_json TEXT NOT NULL, updated_at TEXT NOT NULL
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
              author_id TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('image','voice')),
              original_name TEXT NOT NULL, content_type TEXT NOT NULL, size INTEGER NOT NULL,
              storage_key TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS feedbacks_updated_idx ON feedbacks(updated_at DESC);
            CREATE INDEX IF NOT EXISTS feedback_comments_feedback_idx ON feedback_comments(feedback_id, created_at);
            CREATE INDEX IF NOT EXISTS feedback_attachments_feedback_idx ON feedback_attachments(feedback_id, created_at);
            """
        )
        columns = {row["name"] for row in db.execute("PRAGMA table_info(feedbacks)").fetchall()}
        if "priority" not in columns:
            db.execute("ALTER TABLE feedbacks ADD COLUMN priority INTEGER NOT NULL DEFAULT 2")


def _loads(value: str) -> Any:
    return json.loads(value)


def order_details() -> list[dict[str, Any]]:
    with connection() as db:
        rows = db.execute("SELECT * FROM customer_orders").fetchall()
    return [{
        "id": row["order_id"], "dueDate": row["due_date"], "allowPartial": bool(row["allow_partial"]),
        "partialDeliveryQuantity": row["partial_delivery_quantity"], "partialDeliveryDate": row["partial_delivery_date"],
    } for row in rows]


def save_orders(orders: list[dict[str, Any]]) -> None:
    timestamp = now_iso()
    with connection() as db:
        db.executemany(
            """INSERT INTO customer_orders (order_id,due_date,allow_partial,partial_delivery_quantity,partial_delivery_date,updated_at)
            VALUES (?,?,?,?,?,?) ON CONFLICT(order_id) DO UPDATE SET due_date=excluded.due_date,
            allow_partial=excluded.allow_partial,partial_delivery_quantity=excluded.partial_delivery_quantity,
            partial_delivery_date=excluded.partial_delivery_date,updated_at=excluded.updated_at""",
            [(order["id"], order.get("dueDate", ""), int(order.get("allowPartial", False)), order.get("partialDeliveryQuantity", 0), order.get("partialDeliveryDate", ""), timestamp) for order in orders],
        )


def planning_state() -> dict[str, Any] | None:
    with connection() as db:
        row = db.execute("SELECT seed_json, updated_at FROM planning_state WHERE state_key='default'").fetchone()
    if row is None:
        return None
    return {"seed": _loads(row["seed_json"]), "updatedAt": row["updated_at"]}


def save_planning_state(seed: dict[str, Any]) -> dict[str, Any]:
    timestamp = now_iso()
    with connection() as db:
        db.execute(
            """INSERT INTO planning_state(state_key,seed_json,updated_at) VALUES('default',?,?)
            ON CONFLICT(state_key) DO UPDATE SET seed_json=excluded.seed_json,updated_at=excluded.updated_at""",
            (json.dumps(seed, ensure_ascii=False), timestamp),
        )
    return {"seed": seed, "updatedAt": timestamp}


def scenarios() -> list[dict[str, Any]]:
    with connection() as db:
        rows = db.execute("SELECT * FROM scenarios ORDER BY created_at DESC").fetchall()
    return [{"id": row["id"], "name": row["name"], "createdAt": row["created_at"], "notes": row["notes"], "seed": _loads(row["inputs_json"]), "result": _loads(row["result_json"])} for row in rows]


def revisions() -> list[dict[str, Any]]:
    with connection() as db:
        rows = db.execute("SELECT * FROM order_revisions ORDER BY approved_at DESC").fetchall()
    return [{"id": row["id"], "orderId": row["order_id"], "product": row["product"], "status": row["status"], "createdAt": row["created_at"], "approvedAt": row["approved_at"], "original": _loads(row["original_json"]), "requested": _loads(row["request_json"]), "impact": _loads(row["impact_json"]), "seed": _loads(row["seed_json"]), "result": _loads(row["result_json"])} for row in rows]


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
