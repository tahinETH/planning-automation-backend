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
    auth_disabled: bool = os.getenv("AUTH_DISABLED", "false").lower() == "true"
    database_path: Path = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "app.sqlite"))).resolve()
    upload_dir: Path = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "data" / "uploads"))).resolve()
    cors_origins: tuple[str, ...] = _csv("CORS_ORIGINS", "http://localhost:3000")
    clerk_issuer_url: str = os.getenv("CLERK_ISSUER_URL", "").rstrip("/")
    clerk_jwks_url: str = os.getenv("CLERK_JWKS_URL", "")
    clerk_audience: str = os.getenv("CLERK_AUDIENCE", "")
    clerk_authorized_parties: tuple[str, ...] = _csv("CLERK_AUTHORIZED_PARTIES")


settings = Settings()

