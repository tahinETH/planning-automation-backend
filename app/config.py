from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]


def _csv(name: str, default: str = "") -> tuple[str, ...]:
    return tuple(value.strip() for value in os.getenv(name, default).split(",") if value.strip())


def _path(name: str, default: Path) -> Path:
    raw = os.getenv(name)
    if not raw:
        return default.resolve()
    candidate = Path(raw)
    return (candidate if candidate.is_absolute() else BASE_DIR / candidate).resolve()


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _required_in_deployed_environments(name: str) -> str:
    value = os.getenv(name, "").strip()
    if os.getenv("APP_ENV", "development").lower() in {"staging", "production"} and not value:
        raise RuntimeError(f"{name} must be set when APP_ENV={os.getenv('APP_ENV')}")
    return value


def _auth_test_mode() -> bool:
    enabled = _bool("AUTH_TEST_MODE")
    if enabled and os.getenv("APP_ENV", "development").lower() != "test":
        raise RuntimeError("AUTH_TEST_MODE may only be enabled when APP_ENV=test")
    return enabled


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    database_path: Path = _path("DATABASE_PATH", BASE_DIR / "data" / "app.sqlite")
    upload_dir: Path = _path("UPLOAD_DIR", BASE_DIR / "data" / "uploads")
    cors_origins: tuple[str, ...] = _csv("CORS_ORIGINS", "http://localhost:3000")
    clerk_issuer: str = _required_in_deployed_environments("CLERK_ISSUER").rstrip("/")
    clerk_jwt_key: str = os.getenv("CLERK_JWT_KEY", "").strip().replace("\\n", "\n")
    clerk_authorized_parties: tuple[str, ...] = _csv("CLERK_AUTHORIZED_PARTIES", "http://localhost:3000")
    clerk_admin_user_ids: tuple[str, ...] = _csv("CLERK_ADMIN_USER_IDS")
    auth_test_mode: bool = _auth_test_mode()
    # These values only support isolated automated tests. The route that uses
    # them is never registered in a normal development or deployed process.
    admin_password: str = os.getenv("ADMIN_PASSWORD", "test-password")
    session_secret: str = os.getenv("APP_SESSION_SECRET", "test-session-secret-that-is-long-enough")
    staging_pull_token: str = os.getenv("STAGING_PULL_TOKEN", "").strip()
    production_api_url: str = os.getenv("PRODUCTION_API_URL", "").strip().rstrip("/")
    production_sync_token: str = os.getenv("PRODUCTION_SYNC_TOKEN", "").strip()
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "").strip()
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash").strip() or "deepseek-v4-flash"


settings = Settings()
