"""Disposable code rollback rehearsal. Never restore an operational database."""
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tarfile

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import handover
from app.auth import CurrentUser, current_user
from app.config import settings
from app.main import app

OLD_MAIN = '3a261f1603d399e1e67bf8db462bcea28eb149e7'
ACTOR = CurrentUser('rollback-operator', 'Synthetic operator', 'rollback@example.test', 'user')


def source(path, seed):
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE planning_state(state_key TEXT PRIMARY KEY,seed_json TEXT,updated_at TEXT,updated_by_id TEXT,updated_by_name TEXT)')
        db.execute('INSERT INTO planning_state VALUES(?,?,?,?,?)', ('default', json.dumps(seed), 'synthetic-final-cutoff', 'source-user', 'Synthetic source'))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def backup(source, target):
    with sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True) as original, sqlite3.connect(target) as output:
        original.backup(output)
        assert output.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'


def state_and_receipts(path):
    with sqlite3.connect(path) as db:
        return {
            'seed': json.loads(db.execute("SELECT seed_json FROM planning_state WHERE state_key='default'").fetchone()[0]),
            'commands': db.execute('SELECT * FROM production_commands ORDER BY sequence').fetchall(),
            'opening': db.execute('SELECT * FROM production_opening').fetchall(),
            'generation': db.execute('SELECT * FROM production_handover').fetchall(),
        }


def rehearse(tmp_path, monkeypatch):
    backend = Path(__file__).resolve().parents[1]
    # A source archive is independent of every existing checkout and branch.
    probe = subprocess.run(['git', '-C', str(backend), 'cat-file', '-e', OLD_MAIN + '^{commit}'], capture_output=True)
    assert probe.returncode == 0, 'The reviewed old-main object is required for this rehearsal.'
    old_code = tmp_path / 'old-code'; old_code.mkdir()
    archive = subprocess.run(['git', '-C', str(backend), 'archive', OLD_MAIN], check=True, capture_output=True).stdout
    with tarfile.open(fileobj=BytesIO(archive)) as package:
        package.extractall(old_code, filter='data')
    fixture = json.loads((backend / 'tests' / 'fixtures' / 'collaboration.json').read_text())
    piston = tmp_path / 'candidate.sqlite'; filter_db = tmp_path / 'candidate-cubuk-filtre.sqlite'
    piston_source = tmp_path / 'piston-source.sqlite'; filter_source = tmp_path / 'filter-source.sqlite'
    filter_seed = {'productionArea': 'cubuk-filtre', 'products': [], 'machines': [], 'preferences': [],
                   'orders': [{'id': 'same-order', 'product': 'synthetic-filter', 'quantity': 16000}]}
    handover.import_offline_opening(piston_source, piston, area='torna', generation_id='new-piston', expected_sha256=source(piston_source, fixture['seed']))
    handover.import_offline_opening(filter_source, filter_db, area='cubuk-filtre', generation_id='new-filter', expected_sha256=source(filter_source, filter_seed))
    monkeypatch.setitem(settings.__dict__, 'database_path', piston)
    monkeypatch.setitem(settings.__dict__, 'upload_dir', tmp_path / 'candidate-uploads')
    monkeypatch.setitem(settings.__dict__, 'app_env', 'production')
    monkeypatch.setitem(settings.__dict__, 'enable_filter_production', True)
    app.dependency_overrides[current_user] = lambda: ACTOR
    command = fixture['commands'][0]
    headers = {'X-Production-Area': 'torna', 'X-Planning-Generation': 'new-piston'}
    status_path = f"/api/collaboration/requests/{command['requestId']}?kind=production"
    try:
        # Accept one post-handover physical action using the real runtime and API.
        with TestClient(app) as client:
            accepted = client.post('/api/production/commands', headers=headers, json=command)
            assert accepted.status_code == 200, accepted.text
            assert accepted.json()['replayed'] is False
            assert client.get(status_path, headers=headers).json()['committed'] is True
        after_write = state_and_receipts(piston)
        filter_after = state_and_receipts(filter_db)
        assert len(after_write['commands']) == 1
        # Stop candidate writes. Old code receives private backup copies only.
        old_data = tmp_path / 'rollback-copy'; old_data.mkdir()
        old_piston = old_data / 'app.sqlite'; old_filter = old_data / 'app-cubuk-filtre.sqlite'
        backup(piston, old_piston); backup(filter_db, old_filter)
        old_filter_hash = hashlib.sha256(old_filter.read_bytes()).hexdigest()
        old_probe = '''
import json
from fastapi.testclient import TestClient
from app.main import app
from app.auth import CurrentUser, current_user
app.dependency_overrides[current_user] = lambda: CurrentUser('rollback-operator','Synthetic operator','rollback@example.test','user')
with TestClient(app) as client:
    piston = client.get('/api/planning-state', headers={'X-Production-Area':'torna'})
    selected_filter = client.get('/api/planning-state', headers={'X-Production-Area':'cubuk-filtre'})
    assert piston.status_code == selected_filter.status_code == 200
    assert piston.json()['seed'] == selected_filter.json()['seed']
    assert selected_filter.json()['seed'].get('productionArea','torna') == 'torna'
    assert selected_filter.headers.get('x-production-area') is None
    status = client.get('/api/collaboration/status').json()
    assert 'availableAreas' not in status
print(json.dumps({'oldMainAreaIsolation':False,'filterHeaderIgnored':True,'productionAreasAdvertised':False,'decision':'Do not enable operational writes on this old pair.'}))
'''
        environment = {**os.environ, 'APP_ENV': 'test', 'AUTH_TEST_MODE': 'true',
                       'DATABASE_PATH': str(old_piston), 'UPLOAD_DIR': str(old_data / 'uploads'),
                       'DEEPSEEK_API_KEY': '', 'PRODUCTION_API_URL': '', 'PRODUCTION_SYNC_TOKEN': '', 'STAGING_PULL_TOKEN': ''}
        environment.pop('PYTHONPATH', None)
        result = subprocess.run([sys.executable, '-c', old_probe], cwd=old_code, env=environment, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr
        evidence = json.loads(result.stdout.strip().splitlines()[-1])
        assert evidence['filterHeaderIgnored'] is True
        assert hashlib.sha256(old_filter.read_bytes()).hexdigest() == old_filter_hash
        # The actual candidate stores and accepted receipt are untouched by the rehearsal.
        assert state_and_receipts(piston) == after_write
        assert state_and_receipts(filter_db) == filter_after
        # Resume the compatible candidate. Old clients fail before mutation or receipt.
        with TestClient(app) as client:
            for generation in [None, 'old-generation']:
                stale = {'X-Production-Area': 'torna'}
                if generation: stale['X-Planning-Generation'] = generation
                for response in [client.post('/api/production/commands', headers=stale, json=command), client.get(status_path, headers=stale)]:
                    assert response.status_code == 409
                    assert response.json()['detail']['code'] == 'handover-generation'
            retry = client.post('/api/production/commands', headers=headers, json=command)
            assert retry.status_code == 200
            assert retry.json()['replayed'] is True
            assert retry.json()['appliedRevision'] == accepted.json()['appliedRevision']
            assert client.get('/api/planning-state', headers={'X-Production-Area': 'cubuk-filtre'}).json()['seed'] == filter_seed
        assert state_and_receipts(piston) == after_write
        assert state_and_receipts(filter_db) == filter_after
    finally:
        app.dependency_overrides.pop(current_user, None)

    return {"oldMain": OLD_MAIN, "oldMainServesBothAreas": False,
            "oldFilterHeaderIgnored": True, "postHandoverCommandCount": 1,
            "postHandoverReceiptPreserved": True, "currentGenerationRetryReplayed": True,
            "oldClientCommandStatus": 409, "oldClientReceiptStatus": 409,
            "filterQuantityAfterResume": 16000, "candidateFactsPreserved": True,
            "rehearsalScope": "Disposable synthetic databases and local TestClient only; no service or operational database restore."}


if __name__ == '__main__':
    from tempfile import TemporaryDirectory
    with TemporaryDirectory(prefix='planning-code-rollback-') as directory, pytest.MonkeyPatch.context() as patch:
        print(json.dumps(rehearse(Path(directory), patch), indent=2))
