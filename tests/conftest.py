import os


# The production application has no password-login route. Tests opt into a
# deterministic local token issuer before app modules are imported.
os.environ["APP_ENV"] = "test"
os.environ["AUTH_TEST_MODE"] = "true"
os.environ["DATABASE_PATH"] = "/tmp/selsa-planlama-feedback-test.sqlite"
os.environ["UPLOAD_DIR"] = "/tmp/selsa-planlama-feedback-uploads"
os.environ.setdefault("ADMIN_PASSWORD", "test-password")
os.environ.setdefault("APP_SESSION_SECRET", "test-session-secret-that-is-long-enough")
