"""Optional, non-blocking Telegram alerting for CPM sync and on-demand refresh errors.

Disabled by default (no-op unless both CPM_ALERT_TELEGRAM_BOT_TOKEN and
CPM_ALERT_TELEGRAM_CHAT_ID are configured). Never blocks HTTP endpoints and
never includes credentials, tokens, SQL text, or private customer data.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import sqlite3
import threading
from typing import Callable
import urllib.request

from ..config import settings
from .config import CpmConfig

logger = logging.getLogger("planning.cpm.alerts")

_ALERT_SCHEMA = """
CREATE TABLE IF NOT EXISTS cpm_alert_state (
    area TEXT PRIMARY KEY,
    incident_open INTEGER NOT NULL DEFAULT 0,
    last_error_code TEXT,
    last_alert_at TEXT,
    last_recovery_at TEXT
);
"""


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def is_alerting_configured(config: CpmConfig) -> bool:
    return bool(config.alert_telegram_bot_token and config.alert_telegram_chat_id)


def _send_telegram_sync(bot_token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    body = json.dumps(
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp.read(256)
    except Exception:
        logger.warning("CPM Telegram alert dispatch failed", exc_info=False)


# Monkeypatchable hook for deterministic tests.
_dispatch_telegram: Callable[[str, str, str], None] = lambda token, chat_id, text: threading.Thread(
    target=_send_telegram_sync,
    args=(token, chat_id, text),
    daemon=True,
    name="cpm-telegram-alert",
).start()


def _ensure_alert_table(conn: sqlite3.Connection) -> None:
    conn.executescript(_ALERT_SCHEMA)


def _area_label(area: str) -> str:
    return "Piston" if area == "torna" else area


def notify_cpm_error(
    config: CpmConfig,
    conn: sqlite3.Connection,
    area: str,
    *,
    trigger_label: str,
    error_code: str,
    error_message: str,
) -> bool:
    """Record incident state and send a cooldown-protected Telegram alert if configured.

    Returns True when an alert was dispatched, False when suppressed or unconfigured.
    """
    _ensure_alert_table(conn)
    now = _now_utc()
    now_iso = now.isoformat()

    row = conn.execute(
        "SELECT incident_open, last_error_code, last_alert_at FROM cpm_alert_state WHERE area = ?",
        (area,),
    ).fetchone()

    if not is_alerting_configured(config):
        conn.execute(
            """
            INSERT INTO cpm_alert_state (area, incident_open, last_error_code, last_alert_at)
            VALUES (?, 1, ?, NULL)
            ON CONFLICT(area) DO UPDATE SET
                incident_open = 1,
                last_error_code = excluded.last_error_code
            """,
            (area, error_code),
        )
        return False

    if row is not None and row["incident_open"] and row["last_error_code"] == error_code:
        last_sent = _parse_iso(row["last_alert_at"])
        if last_sent is not None and (now - last_sent).total_seconds() < config.alert_cooldown_seconds:
            return False

    conn.execute(
        """
        INSERT INTO cpm_alert_state (area, incident_open, last_error_code, last_alert_at)
        VALUES (?, 1, ?, ?)
        ON CONFLICT(area) DO UPDATE SET
            incident_open = 1,
            last_error_code = excluded.last_error_code,
            last_alert_at = excluded.last_alert_at
        """,
        (area, error_code, now_iso),
    )

    env_tag = settings.app_env.upper()
    short_msg = (error_message or "Bilinmeyen CPM hatası").strip()[:300]
    text = (
        f"⚠️ CPM Hata [{env_tag} · {_area_label(area)}]\n"
        f"Tetik: {trigger_label}\n"
        f"Kod: {error_code}\n"
        f"Detay: {short_msg}\n"
        f"Zaman (UTC): {now.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    try:
        _dispatch_telegram(config.alert_telegram_bot_token, config.alert_telegram_chat_id, text)
    except Exception:
        logger.warning("CPM Telegram alert hook raised an error", exc_info=False)
        return False
    return True


def notify_cpm_recovered(
    config: CpmConfig,
    conn: sqlite3.Connection,
    area: str,
    *,
    captured_at: str,
) -> bool:
    """Close an open CPM incident and send a single recovery message if an alert was sent."""
    _ensure_alert_table(conn)
    row = conn.execute(
        "SELECT incident_open, last_alert_at FROM cpm_alert_state WHERE area = ?",
        (area,),
    ).fetchone()
    if row is None or not row["incident_open"]:
        return False

    now = _now_utc()
    now_iso = now.isoformat()
    had_sent_alert = bool(row["last_alert_at"])

    conn.execute(
        """
        UPDATE cpm_alert_state
        SET incident_open = 0, last_error_code = NULL, last_alert_at = NULL, last_recovery_at = ?
        WHERE area = ?
        """,
        (now_iso, area),
    )

    if not had_sent_alert or not is_alerting_configured(config):
        return False

    env_tag = settings.app_env.upper()
    text = (
        f"✅ CPM Bağlantısı Geri Geldi [{env_tag} · {_area_label(area)}]\n"
        f"Son başarılı okuma: {captured_at}\n"
        f"Zaman (UTC): {now.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    try:
        _dispatch_telegram(config.alert_telegram_bot_token, config.alert_telegram_chat_id, text)
    except Exception:
        logger.warning("CPM Telegram recovery hook raised an error", exc_info=False)
        return False
    return True
