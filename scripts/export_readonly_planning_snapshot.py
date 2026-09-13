"""Export only planning_state with SQLite read-only/query-only snapshot isolation.

No application imports, migrations, configuration loading, backups on the server,
or database writes. Redirect stdout into a private local file; never commit it.
"""
import argparse
from contextlib import closing
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sqlite3


def export_snapshot(database: Path) -> dict:
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.execute("PRAGMA query_only=ON")
        db.execute("PRAGMA busy_timeout=5000")
        db.execute("BEGIN")
        row = db.execute("SELECT seed_json, updated_at FROM planning_state WHERE state_key='default'").fetchone()
        if row is None:
            raise ValueError("No default planning state exists")
        snapshot = {
            "capturedAt": datetime.now(timezone.utc).isoformat(),
            "sourceUpdatedAt": row[1],
            "seedSha256": hashlib.sha256(row[0].encode()).hexdigest(),
            "seed": json.loads(row[0]),
        }
        db.rollback()
        return snapshot


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(export_snapshot(args.database), ensure_ascii=False))
