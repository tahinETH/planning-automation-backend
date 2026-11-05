import os
from pathlib import Path
from tempfile import TemporaryDirectory


_test_directory = TemporaryDirectory(prefix="planning-reconciliation-pytest-")
_test_root = Path(_test_directory.name)


# The production application has no password-login route. Tests opt into a
# deterministic local token issuer before app modules are imported.
os.environ["APP_ENV"] = "test"
os.environ["AUTH_TEST_MODE"] = "true"
os.environ["DATABASE_PATH"] = str(_test_root / "app.sqlite")
os.environ["UPLOAD_DIR"] = str(_test_root / "uploads")
os.environ.setdefault("ADMIN_PASSWORD", "test-password")
os.environ.setdefault("APP_SESSION_SECRET", "test-session-secret-that-is-long-enough")
