from __future__ import annotations

import os
import subprocess
import sys


def run_config_check(body: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["APP_ENV"] = "development"
    return subprocess.run(
        [sys.executable, "-c", f"from app.config import _secret\n{body}"],
        check=False,
        capture_output=True,
        env=environment,
        text=True,
    )


def test_staging_rejects_default_credentials() -> None:
    result = run_config_check(
        "import os\n"
        "os.environ['APP_ENV'] = 'staging'\n"
        "os.environ.pop('ADMIN_PASSWORD', None)\n"
        "_secret('ADMIN_PASSWORD', 'vardiya')\n"
    )

    assert result.returncode != 0
    assert "ADMIN_PASSWORD" in result.stderr


def test_staging_requires_a_long_session_secret() -> None:
    result = run_config_check(
        "import os\n"
        "os.environ['APP_ENV'] = 'staging'\n"
        "os.environ['APP_SESSION_SECRET'] = 'too-short'\n"
        "_secret('APP_SESSION_SECRET', 'development-only-change-me')\n"
    )

    assert result.returncode != 0
    assert "APP_SESSION_SECRET" in result.stderr


def test_staging_accepts_environment_specific_credentials() -> None:
    result = run_config_check(
        "import os\n"
        "os.environ['APP_ENV'] = 'staging'\n"
        "os.environ['APP_SESSION_SECRET'] = 'staging-session-secret-with-32-characters'\n"
        "assert _secret('APP_SESSION_SECRET', 'development-only-change-me') == os.environ['APP_SESSION_SECRET']\n"
    )

    assert result.returncode == 0, result.stderr
