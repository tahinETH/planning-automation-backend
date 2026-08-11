#!/usr/bin/env python3
from __future__ import annotations

import secrets
from pathlib import Path


PRODUCTION_ENV = Path("/root/planning-automation-backend/.env")
STAGING_ENV = Path("/root/planning-automation-backend-staging/.env")


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if line and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def main() -> None:
    production = read_env(PRODUCTION_ENV)
    existing = read_env(STAGING_ENV) if STAGING_ENV.exists() else {}
    staging = {
        "APP_ENV": "staging",
        "DATABASE_PATH": "/root/planning-automation-backend-staging/data/staging.sqlite",
        "UPLOAD_DIR": "/root/planning-automation-backend-staging/data/uploads",
        "CORS_ORIGINS": "https://staging.planning.hfgok.com",
        "ADMIN_PASSWORD": existing.get("ADMIN_PASSWORD", production["ADMIN_PASSWORD"]),
        "APP_SESSION_SECRET": existing.get("APP_SESSION_SECRET", secrets.token_urlsafe(48)),
        "SESSION_DAYS": "7",
    }
    STAGING_ENV.write_text("".join(f"{key}={value}\n" for key, value in staging.items()))
    STAGING_ENV.chmod(0o600)
    print(f"Wrote isolated staging environment to {STAGING_ENV}")


if __name__ == "__main__":
    main()
