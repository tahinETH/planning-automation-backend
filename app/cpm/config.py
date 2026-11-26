"""Server configuration for the isolated CPM snapshot store.

Never return token or SQL credentials to callers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hmac
import os
from pathlib import Path

from ..config import settings


DEFAULT_REFRESH_INTERVAL_SECONDS = 900  # 15 minutes
MIN_REFRESH_INTERVAL_SECONDS = 60
MAX_REFRESH_INTERVAL_SECONDS = 86400
DEFAULT_ALERT_COOLDOWN_SECONDS = 1800  # 30 minutes


class CpmError(Exception):
    """Controlled domain/config error for CPM routes."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class CpmConfig:
    enabled: bool
    allow_production: bool
    collector_token: str = field(repr=False)
    refresh_interval_seconds: int
    store_path: Path
    alert_telegram_bot_token: str = field(default="", repr=False)
    alert_telegram_chat_id: str = ""
    alert_cooldown_seconds: int = DEFAULT_ALERT_COOLDOWN_SECONDS


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


def load_config() -> CpmConfig:
    raw_store = os.getenv("CPM_STORE_PATH", "").strip()
    if raw_store:
        candidate = Path(raw_store)
        store_path = (candidate if candidate.is_absolute() else settings.database_path.parent / candidate).resolve()
    else:
        store_path = (settings.database_path.parent / "cpm-source" / "piston_snapshots.sqlite").resolve()
    return CpmConfig(
        enabled=_bool_env("CPM_ENABLED", False),
        allow_production=_bool_env("CPM_ALLOW_PRODUCTION", False),
        collector_token=os.getenv("CPM_COLLECTOR_TOKEN", "").strip(),
        refresh_interval_seconds=_int_env(
            "CPM_REFRESH_INTERVAL_SECONDS",
            DEFAULT_REFRESH_INTERVAL_SECONDS,
            MIN_REFRESH_INTERVAL_SECONDS,
            MAX_REFRESH_INTERVAL_SECONDS,
        ),
        store_path=store_path,
        alert_telegram_bot_token=os.getenv("CPM_ALERT_TELEGRAM_BOT_TOKEN", "").strip(),
        alert_telegram_chat_id=os.getenv("CPM_ALERT_TELEGRAM_CHAT_ID", "").strip(),
        alert_cooldown_seconds=_int_env(
            "CPM_ALERT_COOLDOWN_SECONDS",
            DEFAULT_ALERT_COOLDOWN_SECONDS,
            MIN_REFRESH_INTERVAL_SECONDS,
            MAX_REFRESH_INTERVAL_SECONDS,
        ),
    )


def is_environment_allowed(config: CpmConfig) -> bool:
    env = settings.app_env.lower()
    if env in {"staging", "test", "development"}:
        return config.enabled
    if env == "production":
        return config.enabled and config.allow_production
    return False


def require_enabled(config: CpmConfig) -> None:
    if not is_environment_allowed(config):
        raise CpmError("cpm-disabled", "CPM entegrasyonu bu ortamda etkin değil.", status_code=503)


def verify_collector_token(config: CpmConfig, provided: str | None) -> None:
    require_enabled(config)
    if not config.collector_token:
        raise CpmError("collector-not-configured", "CPM toplayıcı anahtarı yapılandırılmamış.", status_code=503)
    if not provided or not hmac.compare_digest(provided.strip(), config.collector_token):
        raise CpmError("collector-unauthorized", "CPM toplayıcı kimlik doğrulaması başarısız.", status_code=401)


def validate_store_path(path: Path) -> None:
    """Reject any path aliasing either operational planning database."""
    base = settings.database_path
    protected_paths = (
        base,
        base.with_name(f"{base.stem}-cubuk-filtre{base.suffix}"),
    )
    resolved = path.resolve()
    for protected in protected_paths:
        if resolved == protected.resolve():
            raise CpmError("unsafe-store-path", "CPM deposu planlama veritabanı ile aynı dosya olamaz.", status_code=500)
        if path.exists() and protected.exists() and path.samefile(protected):
            raise CpmError("unsafe-store-path", "CPM deposu planlama veritabanı ile aynı dosya olamaz.", status_code=500)
