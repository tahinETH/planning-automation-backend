#!/usr/bin/env python3
from __future__ import annotations

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
        "CLERK_ISSUER": existing.get("CLERK_ISSUER", production.get("CLERK_ISSUER", "")),
        "CLERK_JWT_KEY": existing.get("CLERK_JWT_KEY", production.get("CLERK_JWT_KEY", "")),
        "CLERK_AUTHORIZED_PARTIES": "https://staging.planning.hfgok.com",
        "CLERK_ADMIN_USER_IDS": existing.get("CLERK_ADMIN_USER_IDS", production.get("CLERK_ADMIN_USER_IDS", "")),
        "PRODUCTION_API_URL": existing.get("PRODUCTION_API_URL", "https://api.planning.hfgok.com/api"),
        "PRODUCTION_SYNC_TOKEN": existing.get("PRODUCTION_SYNC_TOKEN", production.get("STAGING_PULL_TOKEN", "")),
    }
    if not staging["CLERK_ISSUER"]:
        raise RuntimeError("CLERK_ISSUER must be configured in production or the existing staging environment")
    STAGING_ENV.write_text("".join(f"{key}={value}\n" for key, value in staging.items()))
    STAGING_ENV.chmod(0o600)
    print(f"Wrote isolated staging environment to {STAGING_ENV}")


if __name__ == "__main__":
    main()
