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


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    database_path: Path = _path("DATABASE_PATH", BASE_DIR / "data" / "app.sqlite")
    upload_dir: Path = _path("UPLOAD_DIR", BASE_DIR / "data" / "uploads")
    cors_origins: tuple[str, ...] = _csv("CORS_ORIGINS", "http://localhost:3000")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "vardiya")
    session_secret: str = os.getenv("APP_SESSION_SECRET", "development-only-change-me")
    session_days: int = int(os.getenv("SESSION_DAYS", "30"))
    staging_pull_token: str = os.getenv("STAGING_PULL_TOKEN", "").strip()


settings = Settings()
