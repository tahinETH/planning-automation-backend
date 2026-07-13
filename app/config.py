from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]


def _csv(name: str, default: str = "") -> tuple[str, ...]:
    return tuple(value.strip() for value in os.getenv(name, default).split(",") if value.strip())


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    database_path: Path = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "app.sqlite"))).resolve()
    upload_dir: Path = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "data" / "uploads"))).resolve()
    cors_origins: tuple[str, ...] = _csv("CORS_ORIGINS", "http://localhost:3000")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "vardiya")
    session_secret: str = os.getenv("APP_SESSION_SECRET", "development-only-change-me")
    session_days: int = int(os.getenv("SESSION_DAYS", "30"))


settings = Settings()
