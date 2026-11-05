from __future__ import annotations

import os
import subprocess
import sys


def run_config_check(body: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["APP_ENV"] = "development"
    environment.pop("CLERK_ISSUER", None)
    environment.pop("AUTH_TEST_MODE", None)
    return subprocess.run(
        [sys.executable, "-c", body],
        check=False,
        capture_output=True,
        env=environment,
        text=True,
    )


def test_staging_requires_clerk_issuer() -> None:
    result = run_config_check(
        "import os\n"
        "os.environ['APP_ENV'] = 'staging'\n"
        "from app.config import Settings\n"
        "Settings()\n"
    )

    assert result.returncode != 0
    assert "CLERK_ISSUER" in result.stderr


def test_staging_accepts_clerk_configuration() -> None:
    result = run_config_check(
        "import os\n"
        "os.environ['APP_ENV'] = 'staging'\n"
        "os.environ['CLERK_ISSUER'] = 'https://example.clerk.accounts.dev'\n"
        "from app.config import Settings\n"
        "settings = Settings()\n"
        "assert settings.clerk_issuer == os.environ['CLERK_ISSUER']\n"
    )

    assert result.returncode == 0, result.stderr


def test_filter_production_availability_defaults_off_and_needs_explicit_flag():
    for flag in (None, "false", "true"):
        prefix = "import os\nos.environ['APP_ENV']='production'\nos.environ['CLERK_ISSUER']='https://example.clerk.accounts.dev'\n"
        prefix += "os.environ.pop('ENABLE_FILTER_PRODUCTION',None)\n" if flag is None else f"os.environ['ENABLE_FILTER_PRODUCTION']={flag!r}\n"
        expected = flag == "true"
        result = run_config_check(prefix + f"from app.config import Settings\nassert Settings().enable_filter_production is {expected}\n")
        assert result.returncode == 0, result.stderr
