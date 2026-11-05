"""Build an offline opening. Source data is read-only; an existing target is never replaced."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

from .config import settings
from .production_area import AREAS, area_database_path

SCHEMA = """CREATE TABLE IF NOT EXISTS production_handover (
 id TEXT PRIMARY KEY CHECK(id='default'), generation TEXT NOT NULL,
 source_sha256 TEXT NOT NULL, source_revision TEXT NOT NULL,
 imported_at TEXT NOT NULL, metadata_json TEXT NOT NULL
)"""
# These records describe another production authority. They are not source facts.
CONTROL_TABLES = {
    'planning_write_audit', 'planning_write_receipts', 'scenario_owners',
    'scenario_requests', 'scenario_versions', 'publication_previews', 'published_plans',
    'active_plans', 'production_opening', 'production_commands', 'production_handover',
}


def init_handover(db):
    db.execute(SCHEMA)


def generation(db=None):
    if db is not None:
        exists = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='production_handover'").fetchone()
        if not exists:
            return None
        row = db.execute("SELECT generation FROM production_handover WHERE id='default'").fetchone()
        return row[0] if row else None
    path = area_database_path(settings.database_path)
    if not path.exists():
        return None
    with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as source:
        return generation(source)


def _hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _readonly(path):
    db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    return db


def import_offline_opening(source: Path, target: Path, *, area: str, generation_id: str,
                           expected_sha256: str, source_upload_dir: Path | None = None,
                           target_upload_dir: Path | None = None):
    """Copy an approved closed SQLite export to a new production-shaped target.

    Supply the expected export SHA-256 independently. A repeated import returns
    its receipt. Existing target contents and source contents are never overwritten.
    This function does not switch a service, contact a server, or replay operations.
    """
    source, target = Path(source), Path(target)
    if area not in AREAS or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}', generation_id):
        raise ValueError('Invalid area or generation.')
    if not re.fullmatch(r'[a-f0-9]{64}', expected_sha256):
        raise ValueError('An expected SHA-256 is required.')
    if source.is_symlink() or target.is_symlink() or not source.is_file() or source.resolve() == target.resolve():
        raise ValueError('Source and target must be different regular paths.')
    if any(Path(str(source) + suffix).exists() for suffix in ('-wal', '-journal')):
        raise ValueError('Use a closed offline SQLite export without journal sidecars.')
    if _hash(source) != expected_sha256:
        raise ValueError('Source checksum does not match.')
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = target.with_name(target.name + '.import-lock')
    descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(descriptor)
    upload_lock = None
    created_uploads = []
    target_installed = False
    try:
        if target.exists():
            with _readonly(target) as current:
                row = current.execute("SELECT * FROM production_handover WHERE id='default'").fetchone()
                if not row or row['generation'] != generation_id or row['source_sha256'] != expected_sha256 or json.loads(row['metadata_json'])['area'] != area:
                    raise ValueError('Target already exists with another opening.')
                return {'generation': generation_id, 'sourceSha256': expected_sha256, 'replayed': True}
        with tempfile.TemporaryDirectory(prefix='.opening-', dir=target.parent) as scratch:
            temporary = Path(scratch) / 'opening.sqlite'
            env = dict(os.environ, APP_ENV='test', AUTH_TEST_MODE='false', DATABASE_PATH=str(temporary), UPLOAD_DIR=str(Path(scratch) / 'uploads'))
            subprocess.run([sys.executable, '-c', 'from app.database import init_database; init_database()'],
                           cwd=Path(__file__).resolve().parents[1], env=env, check=True, capture_output=True, timeout=60)
            with _readonly(source) as original, sqlite3.connect(temporary) as output:
                output.row_factory = sqlite3.Row
                original.execute('BEGIN')
                if original.execute('PRAGMA quick_check').fetchall()[0][0] != 'ok':
                    raise ValueError('Source SQLite integrity check failed.')
                row = original.execute("SELECT * FROM planning_state WHERE state_key='default'").fetchone()
                if row is None:
                    raise ValueError('Source has no shared opening.')
                seed = json.loads(row['seed_json'])
                if not isinstance(seed, dict) or seed.get('productionArea', 'torna') != area:
                    raise ValueError('Source opening belongs to another area.')
                from .stock_planning import validate_stock_planning
                from .flow_settings import validate_flow_settings
                validate_stock_planning(seed)
                if 'flowSettings' in seed:
                    validate_flow_settings(seed['flowSettings'])
                    if area == 'cubuk-filtre' and seed['flowSettings']['enabled']:
                        raise ValueError('Piston hourly flow cannot be enabled for filter.')
                for field, identity in (('machines', 'id'), ('products', 'product'), ('preferences', 'key'), ('orders', 'id')):
                    records = seed.get(field)
                    if not isinstance(records, list) or any(not isinstance(item, dict) or not isinstance(item.get(identity), str) or not item[identity].strip() for item in records):
                        raise ValueError('Source opening inputs are incomplete.')
                    if field != "preferences" and len({item[identity] for item in records}) != len(records):
                        raise ValueError('Source opening contains duplicate identities.')
                tables = [r[0] for r in original.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
                target_tables = {r[0] for r in output.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                counts = {}
                for table in tables:
                    # Names come from SQLite metadata but remain an explicit identifier.
                    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', table):
                        raise ValueError('Unsupported source table name.')
                    rows = original.execute(f'SELECT * FROM "{table}"').fetchall()
                    if table in CONTROL_TABLES:
                        if rows:
                            raise ValueError('Source contains production control records; review separately.')
                        continue
                    if table not in target_tables:
                        raise ValueError('Source contains an unsupported table.')
                    columns = [r[1] for r in original.execute(f'PRAGMA table_info("{table}")')]
                    supported = {r[1] for r in output.execute(f'PRAGMA table_info("{table}")')}
                    if not set(columns) <= supported or any(not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', c) for c in columns):
                        raise ValueError('Source columns do not match target schema.')
                    names = ','.join('"' + c + '"' for c in columns)
                    output.executemany(f'INSERT INTO "{table}" ({names}) VALUES ({",".join("?" for _ in columns)})', [tuple(r) for r in rows])
                    counts[table] = len(rows)
                attachment_hashes = {}
                staged_uploads = {}
                for attachment in output.execute('SELECT storage_key,size FROM feedback_attachments'):
                    key, size = attachment
                    if not source_upload_dir or not target_upload_dir or not isinstance(key, str) or Path(key).name != key or key in {'.','..'}:
                        raise ValueError('Attachment directories and safe storage keys are required.')
                    source_upload_dir, target_upload_dir = Path(source_upload_dir), Path(target_upload_dir)
                    if source_upload_dir.is_symlink() or target_upload_dir.is_symlink() or source_upload_dir.resolve() == target_upload_dir.resolve():
                        raise ValueError('Attachment source and target must be separate regular directories.')
                    original_file = source_upload_dir / key
                    if original_file.is_symlink() or not original_file.is_file() or original_file.stat().st_size != size:
                        raise ValueError('An attachment is missing or invalid.')
                    digest = _hash(original_file)
                    staged = Path(scratch) / 'attachments' / key
                    staged.parent.mkdir(exist_ok=True, mode=0o700)
                    if key not in staged_uploads:
                        with original_file.open('rb') as src, staged.open('xb') as dst:
                            os.chmod(staged, 0o600)
                            shutil.copyfileobj(src, dst)
                            dst.flush(); os.fsync(dst.fileno())
                    if _hash(staged) != digest:
                        raise ValueError('Attachment copy checksum failed.')
                    staged_uploads[key] = staged
                    attachment_hashes[key] = digest
                from .planning_delta import state_hash
                imported_at = datetime.now(timezone.utc).isoformat()
                metadata = {'area': area, 'sourceRevision': row['updated_at'], 'sourceStateHash': state_hash(seed),
                            'sourceUpdatedBy': {key: row[key] for key in ('updated_by_id', 'updated_by_name') if key in row.keys()},
                            'rowCounts': counts, 'attachmentSha256': attachment_hashes}
                # The source seed is exact. A new revision invalidates old browser plans.
                output.execute("UPDATE planning_state SET updated_at=?,updated_by_id=?,updated_by_name=? WHERE state_key='default'", (imported_at, "system:offline-handover", "Üretim başlangıcı aktarımı"))
                output.execute('INSERT INTO production_opening VALUES(?,?,?,?,?)', ('default', imported_at, imported_at, state_hash(seed), row['seed_json']))
                from .database import _insert_production_archive_snapshot
                _insert_production_archive_snapshot(output, seed, imported_at, 'offline-handover')
                output.execute('INSERT INTO production_handover VALUES(?,?,?,?,?,?)', ('default', generation_id, expected_sha256, row['updated_at'], imported_at, json.dumps(metadata, sort_keys=True)))
                if output.execute('PRAGMA foreign_key_check').fetchall():
                    raise ValueError('Imported references do not reconcile.')
                output.commit()
                if output.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                    raise ValueError('Target SQLite integrity check failed.')
            if _hash(source) != expected_sha256:
                raise ValueError('Source changed during import.')
            os.chmod(temporary, 0o600)
            with temporary.open('rb') as durable:
                os.fsync(durable.fileno())
            if staged_uploads:
                target_upload_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
                if target_upload_dir.is_symlink() or not target_upload_dir.is_dir():
                    raise ValueError('Attachment target must be a regular directory.')
                # Imports for both areas can share one upload root. Hold its lock
                # until DB installation or cleanup so a failed import cannot remove
                # a file that another import has accepted in the meantime.
                candidate_lock = target_upload_dir / '.opening-import-lock'
                upload_descriptor = os.open(candidate_lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                os.close(upload_descriptor)
                upload_lock = candidate_lock
                # Check every collision before installing any new attachment.
                for key in staged_uploads:
                    destination = target_upload_dir / key
                    if destination.is_symlink() or destination.exists() and (not destination.is_file() or _hash(destination) != attachment_hashes[key]):
                        raise ValueError('Attachment target has different contents or is a symlink.')
                for key, staged in staged_uploads.items():
                    destination = target_upload_dir / key
                    if destination.exists():
                        continue
                    os.link(staged, destination)  # No-clobber publication.
                    created_uploads.append(destination)
                upload_folder = os.open(target_upload_dir, os.O_RDONLY)
                try:
                    os.fsync(upload_folder)
                finally:
                    os.close(upload_folder)
            os.link(temporary, target)  # Atomic and refuses an existing target.
            target_installed = True
            folder = os.open(target.parent, os.O_RDONLY)
            try:
                os.fsync(folder)
            finally:
                os.close(folder)
        return {'generation': generation_id, 'sourceSha256': expected_sha256, 'replayed': False}
    finally:
        if not target_installed:
            for destination in reversed(created_uploads):
                destination.unlink(missing_ok=True)
        if upload_lock is not None:
            upload_lock.unlink(missing_ok=True)
        lock.unlink(missing_ok=True)
