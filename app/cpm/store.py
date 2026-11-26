"""Isolated SQLite storage for immutable CPM snapshots, attempts, heartbeats, and on-demand refresh requests.

Never touches either operational planning SQLite database.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
import sqlite3
from typing import Any, Iterator
import uuid

from .alerts import notify_cpm_error, notify_cpm_recovered
from .config import CpmConfig, CpmError, validate_store_path
from .models import (
    CpmCollectorFailurePayload,
    CpmCollectorHeartbeatPayload,
    CpmPistonSnapshotPayload,
)

REFRESH_DEDUPE_SECONDS = 120
REFRESH_EXPIRE_SECONDS = 300
COLLECTOR_ONLINE_SECONDS = 90
MAX_RETAINED_SNAPSHOTS = 96  # ~24 hours at 15-min cadence


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now_utc().isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _canonical_digest(payload: CpmPistonSnapshotPayload) -> str:
    core = {
        "schemaVersion": payload.schemaVersion,
        "area": payload.area,
        "company": payload.company,
        "capturedAt": payload.capturedAt,
        "rawMaterialScope": payload.rawMaterialScope,
        "rawMaterials": [r.model_dump() for r in payload.rawMaterials],
        "productStocks": [r.model_dump() for r in payload.productStocks],
        "workOrders": [r.model_dump() for r in payload.workOrders],
        "parameters": payload.parameters.model_dump(),
    }
    encoded = json.dumps(core, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _summary_counts(payload: CpmPistonSnapshotPayload) -> dict[str, int]:
    return {
        "rawMaterials": len(payload.rawMaterials),
        "productStocks": len(payload.productStocks),
        "workOrders": len(payload.workOrders),
        "bomWeights": len(payload.parameters.bomWeights),
        "cycleTimes": len(payload.parameters.cycleTimes),
        "resources": len(payload.parameters.resources),
    }


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS cpm_snapshots (
            id TEXT PRIMARY KEY,
            area TEXT NOT NULL,
            company TEXT NOT NULL,
            collector_id TEXT NOT NULL,
            trigger_kind TEXT NOT NULL,
            request_id TEXT,
            started_at TEXT NOT NULL,
            captured_at TEXT NOT NULL,
            ingested_at TEXT NOT NULL,
            content_sha256 TEXT NOT NULL,
            summary_json TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_cpm_snapshots_area_digest
            ON cpm_snapshots(area, content_sha256);
        CREATE INDEX IF NOT EXISTS idx_cpm_snapshots_area_ingested
            ON cpm_snapshots(area, ingested_at DESC);

        CREATE TABLE IF NOT EXISTS cpm_attempts (
            id TEXT PRIMARY KEY,
            area TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            trigger_kind TEXT NOT NULL,
            collector_id TEXT NOT NULL,
            status TEXT NOT NULL,
            error_code TEXT,
            error_message TEXT,
            snapshot_id TEXT,
            request_id TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_cpm_attempts_area_time
            ON cpm_attempts(area, recorded_at DESC);

        CREATE TABLE IF NOT EXISTS cpm_refresh_requests (
            id TEXT PRIMARY KEY,
            area TEXT NOT NULL,
            requested_by TEXT NOT NULL,
            requested_at TEXT NOT NULL,
            status TEXT NOT NULL,
            claimed_by TEXT,
            claimed_at TEXT,
            completed_at TEXT,
            snapshot_id TEXT,
            error_message TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_cpm_refresh_area_time
            ON cpm_refresh_requests(area, requested_at DESC);

        CREATE TABLE IF NOT EXISTS cpm_collector_heartbeats (
            collector_id TEXT PRIMARY KEY,
            area TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            vpn_connected INTEGER NOT NULL,
            interval_seconds INTEGER NOT NULL,
            next_scheduled_at TEXT,
            last_error TEXT
        );
        """
    )


@contextmanager
def open_store(config: CpmConfig) -> Iterator[sqlite3.Connection]:
    validate_store_path(config.store_path)
    config.store_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(config.store_path.parent, 0o700)
    except OSError:
        pass
    conn = sqlite3.connect(str(config.store_path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        _init_schema(conn)
        try:
            os.chmod(config.store_path, 0o600)
        except OSError:
            pass
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _expire_stale_requests(conn: sqlite3.Connection, area: str, now: datetime) -> None:
    cutoff = (now - timedelta(seconds=REFRESH_EXPIRE_SECONDS)).isoformat()
    conn.execute(
        """
        UPDATE cpm_refresh_requests
        SET status = 'expired',
            completed_at = ?,
            error_message = COALESCE(error_message, 'Toplayıcı veya VPN yanıt vermediği için istek zaman aşımına uğradı.')
        WHERE area = ? AND status IN ('pending', 'claimed') AND requested_at < ?
        """,
        (now.isoformat(), area, cutoff),
    )


def ingest_snapshot(config: CpmConfig, payload: CpmPistonSnapshotPayload) -> dict[str, Any]:
    now_str = _now_iso()
    digest = _canonical_digest(payload)
    summary = _summary_counts(payload)
    payload_str = json.dumps(payload.model_dump(), ensure_ascii=False, separators=(",", ":"))
    summary_str = json.dumps(summary, ensure_ascii=False, separators=(",", ":"))

    with open_store(config) as conn:
        existing = conn.execute(
            "SELECT id, ingested_at, captured_at FROM cpm_snapshots WHERE area = ? AND content_sha256 = ?",
            (payload.area, digest),
        ).fetchone()
        if existing is not None:
            snapshot_id = existing["id"]
            deduplicated = True
            ingested_at = existing["ingested_at"]
        else:
            snapshot_id = str(uuid.uuid4())
            deduplicated = False
            ingested_at = now_str
            conn.execute(
                """
                INSERT INTO cpm_snapshots (
                    id, area, company, collector_id, trigger_kind, request_id,
                    started_at, captured_at, ingested_at, content_sha256, summary_json, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    payload.area,
                    payload.company,
                    payload.collectorId,
                    payload.triggerKind,
                    payload.requestId,
                    payload.startedAt,
                    payload.capturedAt,
                    ingested_at,
                    digest,
                    summary_str,
                    payload_str,
                ),
            )
            # Prune snapshots beyond bounded retention while always keeping newest rows.
            conn.execute(
                """
                DELETE FROM cpm_snapshots
                WHERE area = ? AND id NOT IN (
                    SELECT id FROM cpm_snapshots WHERE area = ? ORDER BY ingested_at DESC LIMIT ?
                )
                """,
                (payload.area, payload.area, MAX_RETAINED_SNAPSHOTS),
            )

        attempt_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO cpm_attempts (
                id, area, recorded_at, trigger_kind, collector_id, status,
                error_code, error_message, snapshot_id, request_id
            ) VALUES (?, ?, ?, ?, ?, 'succeeded', NULL, NULL, ?, ?)
            """,
            (
                attempt_id,
                payload.area,
                now_str,
                payload.triggerKind,
                payload.collectorId,
                snapshot_id,
                payload.requestId,
            ),
        )

        # Complete matching or older pending/claimed refresh requests for this area.
        if payload.requestId:
            conn.execute(
                """
                UPDATE cpm_refresh_requests
                SET status = 'completed', completed_at = ?, snapshot_id = ?, error_message = NULL
                WHERE area = ? AND (id = ? OR status IN ('pending', 'claimed'))
                """,
                (now_str, snapshot_id, payload.area, payload.requestId),
            )
        else:
            conn.execute(
                """
                UPDATE cpm_refresh_requests
                SET status = 'completed', completed_at = ?, snapshot_id = ?, error_message = NULL
                WHERE area = ? AND status IN ('pending', 'claimed')
                """,
                (now_str, snapshot_id, payload.area),
            )

        notify_cpm_recovered(config, conn, payload.area, captured_at=payload.capturedAt)

    return {
        "snapshotId": snapshot_id,
        "attemptId": attempt_id,
        "deduplicated": deduplicated,
        "capturedAt": payload.capturedAt,
        "ingestedAt": ingested_at,
        "contentSha256": digest,
        "counts": summary,
    }


def record_failure(config: CpmConfig, failure: CpmCollectorFailurePayload) -> dict[str, Any]:
    now_str = _now_iso()
    attempt_id = str(uuid.uuid4())
    with open_store(config) as conn:
        conn.execute(
            """
            INSERT INTO cpm_attempts (
                id, area, recorded_at, trigger_kind, collector_id, status,
                error_code, error_message, snapshot_id, request_id
            ) VALUES (?, ?, ?, ?, ?, 'failed', ?, ?, NULL, ?)
            """,
            (
                attempt_id,
                failure.area,
                now_str,
                failure.triggerKind,
                failure.collectorId,
                failure.errorCode,
                failure.errorMessage,
                failure.requestId,
            ),
        )
        if failure.requestId:
            conn.execute(
                """
                UPDATE cpm_refresh_requests
                SET status = 'failed', completed_at = ?, error_message = ?
                WHERE id = ? AND area = ?
                """,
                (now_str, failure.errorMessage, failure.requestId, failure.area),
            )
        trigger_label = (
            "Anlık yenileme (CPM'den Güncelle)"
            if failure.triggerKind == "on-demand"
            else "15 dk otomatik çekim"
        )
        notify_cpm_error(
            config,
            conn,
            failure.area,
            trigger_label=trigger_label,
            error_code=failure.errorCode,
            error_message=failure.errorMessage,
        )
    return {"attemptId": attempt_id, "recordedAt": now_str, "status": "failed"}


def create_refresh_request(config: CpmConfig, area: str, requested_by: str) -> dict[str, Any]:
    now = _now_utc()
    now_str = now.isoformat()
    dedupe_cutoff = (now - timedelta(seconds=REFRESH_DEDUPE_SECONDS)).isoformat()
    failure_error: CpmError | None = None

    with open_store(config) as conn:
        _expire_stale_requests(conn, area, now)
        collector = _collector_status(conn, area, now)
        if not collector["online"]:
            failure_error = CpmError(
                "collector-offline",
                "CPM toplayıcısı şu an çevrimdışı — taze veri çekilemedi. Son başarılı CPM verisi korunuyor.",
                status_code=503,
            )
        elif not collector["vpnConnected"]:
            failure_error = CpmError(
                "vpn-disconnected",
                "CPM toplayıcısında SELSA VPN kapalı — taze veri çekilemedi. Son başarılı CPM verisi korunuyor.",
                status_code=503,
            )

        if failure_error is not None:
            conn.execute(
                """
                INSERT INTO cpm_attempts (
                    id, area, recorded_at, trigger_kind, collector_id, status,
                    error_code, error_message, snapshot_id, request_id
                ) VALUES (?, ?, ?, 'on-demand', ?, 'failed', ?, ?, NULL, NULL)
                """,
                (
                    str(uuid.uuid4()),
                    area,
                    now_str,
                    collector["collectorId"] or "unavailable",
                    failure_error.code,
                    failure_error.message,
                ),
            )
            notify_cpm_error(
                config,
                conn,
                area,
                trigger_label="Anlık yenileme (CPM'den Güncelle)",
                error_code=failure_error.code,
                error_message=failure_error.message,
            )
        else:
            existing = conn.execute(
                """
                SELECT id, requested_at, status, claimed_by, claimed_at
                FROM cpm_refresh_requests
                WHERE area = ? AND status IN ('pending', 'claimed') AND requested_at >= ?
                ORDER BY requested_at DESC LIMIT 1
                """,
                (area, dedupe_cutoff),
            ).fetchone()
            if existing is not None:
                request_row = dict(existing)
                deduplicated = True
            else:
                req_id = str(uuid.uuid4())
                conn.execute(
                    """
                    INSERT INTO cpm_refresh_requests (
                        id, area, requested_by, requested_at, status
                    ) VALUES (?, ?, ?, ?, 'pending')
                    """,
                    (req_id, area, requested_by, now_str),
                )
                request_row = {
                    "id": req_id,
                    "requested_at": now_str,
                    "status": "pending",
                    "claimed_by": None,
                    "claimed_at": None,
                }
                deduplicated = False

    if failure_error is not None:
        raise failure_error

    return {
        "requestId": request_row["id"],
        "status": request_row["status"],
        "requestedAt": request_row["requested_at"],
        "deduplicated": deduplicated,
        "collectorOnline": collector["online"],
        "vpnConnected": collector["vpnConnected"],
    }


def record_heartbeat(config: CpmConfig, hb: CpmCollectorHeartbeatPayload) -> dict[str, Any]:
    now = _now_utc()
    now_str = now.isoformat()
    pending_request = None

    with open_store(config) as conn:
        _expire_stale_requests(conn, hb.area, now)
        conn.execute(
            """
            INSERT INTO cpm_collector_heartbeats (
                collector_id, area, last_seen_at, vpn_connected, interval_seconds, next_scheduled_at, last_error
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(collector_id) DO UPDATE SET
                area = excluded.area,
                last_seen_at = excluded.last_seen_at,
                vpn_connected = excluded.vpn_connected,
                interval_seconds = excluded.interval_seconds,
                next_scheduled_at = excluded.next_scheduled_at,
                last_error = excluded.last_error
            """,
            (
                hb.collectorId,
                hb.area,
                now_str,
                1 if hb.vpnConnected else 0,
                hb.intervalSeconds,
                hb.nextScheduledAt,
                hb.lastError,
            ),
        )
        if hb.vpnConnected:
            row = conn.execute(
                """
                SELECT id, requested_at, requested_by
                FROM cpm_refresh_requests
                WHERE area = ? AND status = 'pending'
                ORDER BY requested_at ASC LIMIT 1
                """,
                (hb.area,),
            ).fetchone()
            if row is not None:
                conn.execute(
                    """
                    UPDATE cpm_refresh_requests
                    SET status = 'claimed', claimed_by = ?, claimed_at = ?
                    WHERE id = ?
                    """,
                    (hb.collectorId, now_str, row["id"]),
                )
                pending_request = {
                    "requestId": row["id"],
                    "requestedAt": row["requested_at"],
                    "requestedBy": row["requested_by"],
                }

    return {
        "ok": True,
        "serverTime": now_str,
        "refreshIntervalSeconds": config.refresh_interval_seconds,
        "pendingRequest": pending_request,
    }


def _collector_status(conn: sqlite3.Connection, area: str, now: datetime) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT collector_id, last_seen_at, vpn_connected, interval_seconds, next_scheduled_at, last_error
        FROM cpm_collector_heartbeats
        WHERE area = ?
        ORDER BY last_seen_at DESC LIMIT 1
        """,
        (area,),
    ).fetchone()
    if row is None:
        return {
            "online": False,
            "vpnConnected": False,
            "collectorId": None,
            "lastSeenAt": None,
            "intervalSeconds": None,
            "nextScheduledAt": None,
            "lastError": None,
        }
    seen_dt = _parse_iso(row["last_seen_at"])
    online = bool(seen_dt and (now - seen_dt).total_seconds() <= COLLECTOR_ONLINE_SECONDS)
    return {
        "online": online,
        "vpnConnected": bool(row["vpn_connected"]) and online,
        "collectorId": row["collector_id"],
        "lastSeenAt": row["last_seen_at"],
        "intervalSeconds": row["interval_seconds"],
        "nextScheduledAt": row["next_scheduled_at"],
        "lastError": row["last_error"],
    }


def get_status(config: CpmConfig, area: str) -> dict[str, Any]:
    now = _now_utc()
    supported = area == "torna"
    if not supported:
        return {
            "enabled": True,
            "area": area,
            "supported": False,
            "refreshIntervalSeconds": config.refresh_interval_seconds,
            "lastSnapshot": None,
            "lastAttempt": None,
            "activeRequest": None,
            "collector": {
                "online": False,
                "vpnConnected": False,
                "collectorId": None,
                "lastSeenAt": None,
                "intervalSeconds": None,
                "nextScheduledAt": None,
                "lastError": None,
            },
        }

    with open_store(config) as conn:
        _expire_stale_requests(conn, area, now)
        snap = conn.execute(
            """
            SELECT id, company, collector_id, trigger_kind, started_at, captured_at, ingested_at, content_sha256, summary_json
            FROM cpm_snapshots
            WHERE area = ?
            ORDER BY ingested_at DESC LIMIT 1
            """,
            (area,),
        ).fetchone()
        attempt = conn.execute(
            """
            SELECT id, recorded_at, trigger_kind, collector_id, status, error_code, error_message, snapshot_id
            FROM cpm_attempts
            WHERE area = ?
            ORDER BY recorded_at DESC LIMIT 1
            """,
            (area,),
        ).fetchone()
        req = conn.execute(
            """
            SELECT id, requested_at, status, claimed_by, claimed_at, completed_at, snapshot_id, error_message
            FROM cpm_refresh_requests
            WHERE area = ?
            ORDER BY requested_at DESC LIMIT 1
            """,
            (area,),
        ).fetchone()
        collector = _collector_status(conn, area, now)

    last_snapshot = None
    if snap is not None:
        captured_dt = _parse_iso(snap["captured_at"])
        age_seconds = max(0, int((now - captured_dt).total_seconds())) if captured_dt else None
        last_snapshot = {
            "snapshotId": snap["id"],
            "company": snap["company"],
            "collectorId": snap["collector_id"],
            "triggerKind": snap["trigger_kind"],
            "startedAt": snap["started_at"],
            "capturedAt": snap["captured_at"],
            "ingestedAt": snap["ingested_at"],
            "ageSeconds": age_seconds,
            "stale": bool(age_seconds is not None and age_seconds > config.refresh_interval_seconds * 2),
            "contentSha256": snap["content_sha256"],
            "counts": json.loads(snap["summary_json"]),
        }

    last_attempt = (
        {
            "attemptId": attempt["id"],
            "recordedAt": attempt["recorded_at"],
            "triggerKind": attempt["trigger_kind"],
            "collectorId": attempt["collector_id"],
            "status": attempt["status"],
            "errorCode": attempt["error_code"],
            "errorMessage": attempt["error_message"],
            "snapshotId": attempt["snapshot_id"],
        }
        if attempt is not None
        else None
    )

    active_request = (
        {
            "requestId": req["id"],
            "requestedAt": req["requested_at"],
            "status": req["status"],
            "claimedBy": req["claimed_by"],
            "claimedAt": req["claimed_at"],
            "completedAt": req["completed_at"],
            "snapshotId": req["snapshot_id"],
            "errorMessage": req["error_message"],
        }
        if req is not None
        else None
    )

    return {
        "enabled": True,
        "area": area,
        "supported": True,
        "refreshIntervalSeconds": config.refresh_interval_seconds,
        "lastSnapshot": last_snapshot,
        "lastAttempt": last_attempt,
        "activeRequest": active_request,
        "collector": collector,
    }


def get_latest_snapshot(config: CpmConfig, area: str) -> dict[str, Any]:
    status = get_status(config, area)
    if not status["supported"]:
        return {"status": status, "snapshot": None}
    with open_store(config) as conn:
        row = conn.execute(
            """
            SELECT id, ingested_at, content_sha256, payload_json
            FROM cpm_snapshots
            WHERE area = ?
            ORDER BY ingested_at DESC LIMIT 1
            """,
            (area,),
        ).fetchone()
    if row is None:
        return {"status": status, "snapshot": None}
    payload = json.loads(row["payload_json"])
    payload["snapshotId"] = row["id"]
    payload["ingestedAt"] = row["ingested_at"]
    payload["contentSha256"] = row["content_sha256"]
    return {"status": status, "snapshot": payload}
