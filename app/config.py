from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
INSECURE_SECRET_VALUES = {"", "vardiya", "change-this-password", "development-only-change-me", "generate-a-long-random-secret"}


def _csv(name: str, default: str = "") -> tuple[str, ...]:
    return tuple(value.strip() for value in os.getenv(name, default).split(",") if value.strip())


def _path(name: str, default: Path) -> Path:
    raw = os.getenv(name)
    if not raw:
        return default.resolve()
    candidate = Path(raw)
    return (candidate if candidate.is_absolute() else BASE_DIR / candidate).resolve()


def _secret(name: str, default: str) -> str:
    value = os.getenv(name, default)
    app_env = os.getenv("APP_ENV", "development").lower()
    insecure = value in INSECURE_SECRET_VALUES or value.startswith("replace-with-")
    if name == "APP_SESSION_SECRET" and len(value) < 32:
        insecure = True
    if app_env in {"staging", "production"} and insecure:
        raise RuntimeError(f"{name} must be set to a non-default value when APP_ENV={app_env}")
    return value


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    database_path: Path = _path("DATABASE_PATH", BASE_DIR / "data" / "app.sqlite")
    upload_dir: Path = _path("UPLOAD_DIR", BASE_DIR / "data" / "uploads")
    cors_origins: tuple[str, ...] = _csv("CORS_ORIGINS", "http://localhost:3000")
    admin_password: str = _secret("ADMIN_PASSWORD", "vardiya")
    session_secret: str = _secret("APP_SESSION_SECRET", "development-only-change-me")
    session_days: int = int(os.getenv("SESSION_DAYS", "30"))


settings = Settings()
