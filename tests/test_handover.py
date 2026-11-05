"""Independent synthetic opening, generation and area-isolation acceptance."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import database, handover
from app.auth import CurrentUser, current_user
from app.config import settings
from app.main import app
from app.production_area import production_area


ADMIN = CurrentUser('handover-admin', 'Synthetic administrator', 'handover-admin@example.test', 'admin')
OPERATOR = CurrentUser('handover-operator', 'Synthetic operator', 'handover-operator@example.test', 'user')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows(path):
    with sqlite3.connect(path) as db:
        names = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        return {name: db.execute(f'SELECT * FROM "{name}" ORDER BY rowid').fetchall() for name in names}


def opening_seed(area):
    return {'productionArea': area, 'machines': [], 'products': [], 'preferences': [],
            'orders': [{'id': 'same-order', 'product': 'synthetic-product', 'quantity': 480 if area == 'torna' else 16000, 'dueDate': '2026-11-30'}],
            'productionHistory': [{'id': 'late-completion', 'product': 'synthetic-product', 'workOrder': 'same-charge',
                                   'completedQuantity': 12, 'originalQuantity': 12, 'completedAt': 46329,
                                   'process': 'turning', 'inventoryStatus': 'semi-finished'}],
            'wipLots': [], 'wipMovements': []}


@pytest.fixture
def source(tmp_path, monkeypatch):
    path = tmp_path / 'source.sqlite'
    monkeypatch.setitem(settings.__dict__, "database_path", path)
    monkeypatch.setitem(settings.__dict__, "upload_dir", tmp_path / 'source-uploads')
    token = production_area.set('torna')
    try:
        database.init_database()
        value = opening_seed('torna')
        # A staging-shaped export contains source facts, not production authority.
        # Insert the synthetic source directly instead of creating a main write receipt.
        with database.connection() as db:
            db.execute('INSERT INTO planning_state VALUES(?,?,?,?,?)', ('default', json.dumps(value), '2026-11-05T09:00:00Z', 'source-operator', 'Synthetic operator'))
        yield path
    finally:
        production_area.reset(token)


def import_source(source, target, **kwargs):
    return handover.import_offline_opening(source, target, area='torna', generation_id='opening-20261105', expected_sha256=digest(source), **kwargs)


def test_ho01_offline_opening_keeps_late_twelve_once_and_repeat_is_noop(source, tmp_path):
    target = tmp_path / 'target.sqlite'
    before_source = digest(source)
    with sqlite3.connect(source) as db:
        before_seed, source_revision = db.execute("SELECT seed_json,updated_at FROM planning_state WHERE state_key='default'").fetchone()
    first = import_source(source, target)
    assert first['replayed'] is False
    after = rows(target)
    with sqlite3.connect(target) as db:
        saved_seed, saved_revision = db.execute("SELECT seed_json,updated_at FROM planning_state WHERE state_key='default'").fetchone()
        ledger = db.execute('SELECT seed_json FROM production_opening').fetchone()[0]
        generation, expected_hash, recorded_revision, metadata = db.execute('SELECT generation,source_sha256,source_revision,metadata_json FROM production_handover').fetchone()
    assert saved_seed == ledger == before_seed
    assert sum(x['completedQuantity'] for x in json.loads(saved_seed)['productionHistory']) == 12
    assert saved_revision != source_revision
    assert (generation, expected_hash, recorded_revision) == ('opening-20261105', before_source, source_revision)
    assert json.loads(metadata)['area'] == 'torna'
    assert after['production_commands'] == []
    assert after['published_plans'] == []
    assert import_source(source, target)['replayed'] is True
    assert rows(target) == after
    assert digest(source) == before_source


@pytest.mark.parametrize('problem', ['checksum', 'area', 'wal', 'journal', 'existing-target', 'control-record', 'same-path', 'source-symlink', 'target-symlink', 'duplicate-order'])
def test_ho02_bad_source_or_target_rejects_without_source_or_target_change(source, tmp_path, problem):
    target = tmp_path / 'target.sqlite'
    source_arg = source
    kwargs = dict(area='torna', generation_id='opening-20261105', expected_sha256=digest(source))
    if problem == 'checksum': kwargs['expected_sha256'] = '0' * 64
    if problem == 'area': kwargs['area'] = 'cubuk-filtre'
    if problem in {'wal', 'journal'}: Path(str(source) + ('-wal' if problem == 'wal' else '-journal')).write_bytes(b'synthetic-sidecar')
    if problem == 'existing-target': target.write_bytes(b'preserve-existing-target')
    if problem == 'control-record':
        with sqlite3.connect(source) as db:
            db.execute("INSERT INTO production_opening VALUES(?,?,?,?,?)", ('default', 'old', 'old', '0' * 64, '{}'))
        kwargs['expected_sha256'] = digest(source)
    if problem == 'duplicate-order':
        with sqlite3.connect(source) as db:
            value = json.loads(db.execute('SELECT seed_json FROM planning_state').fetchone()[0])
            value['orders'].append(deepcopy(value['orders'][0]))
            db.execute('UPDATE planning_state SET seed_json=?', (json.dumps(value),))
        kwargs['expected_sha256'] = digest(source)
    if problem == 'same-path': target = source
    if problem == 'source-symlink':
        source_arg = tmp_path / 'source-link.sqlite'; source_arg.symlink_to(source)
    if problem == 'target-symlink': target.symlink_to(source)
    before_source = source.read_bytes()
    before_target = target.read_bytes() if target.exists() else None
    with pytest.raises((ValueError, sqlite3.DatabaseError)):
        handover.import_offline_opening(source_arg, target, **kwargs)
    assert source.read_bytes() == before_source
    assert (target.read_bytes() if target.exists() else None) == before_target
    assert not target.with_name(target.name + '.import-lock').exists()


def test_ho03_failed_attachment_import_does_not_leave_partial_files(source, tmp_path):
    source_uploads = tmp_path / 'source-uploads'; source_uploads.mkdir(exist_ok=True)
    (source_uploads / 'first.txt').write_bytes(b'first')
    with sqlite3.connect(source) as db:
        db.execute("INSERT INTO feedbacks(id,author_id,author_name,body,created_at,updated_at) VALUES(?,?,?,?,?,?)", ('feedback', 'user', 'Synthetic user', 'Fixture', '2026-11-05', '2026-11-05'))
        for identity, key, size in [('first', 'first.txt', 5), ('second', 'missing.txt', 7)]:
            db.execute('INSERT INTO feedback_attachments VALUES(?,?,?,?,?,?,?,?,?)', (identity, 'feedback', 'user', 'document', key, 'text/plain', size, key, '2026-11-05'))
    target = tmp_path / 'target.sqlite'; uploads = tmp_path / 'target-uploads'
    with pytest.raises(ValueError, match='attachment'):
        import_source(source, target, source_upload_dir=source_uploads, target_upload_dir=uploads)
    assert not target.exists()
    assert not uploads.exists() or list(uploads.iterdir()) == [], 'A rejected import must not install a partial upload set.'


@pytest.fixture
def isolated_api(tmp_path, monkeypatch):
    monkeypatch.setitem(settings.__dict__, "database_path", tmp_path / 'api.sqlite')
    monkeypatch.setitem(settings.__dict__, "upload_dir", tmp_path / 'uploads')
    monkeypatch.setitem(settings.__dict__, "app_env", 'production')
    monkeypatch.setitem(settings.__dict__, "enable_filter_production", True)
    app.dependency_overrides[current_user] = lambda: ADMIN
    with TestClient(app) as client:
        for area in ['torna', 'cubuk-filtre']:
            token = production_area.set(area)
            try:
                database.init_database()
                database.save_planning_state(opening_seed(area), mode='operational', can_manage_settings=True)
                with database.connection() as db:
                    db.execute('INSERT INTO production_handover VALUES(?,?,?,?,?,?)', ('default', f'new-{area}', 'a' * 64, 'source-revision', '2026-11-05', json.dumps({'area': area})))
                    db.execute('INSERT INTO production_opening VALUES(?,?,?,?,?)', ('default', '2026-11-05', 'source-revision', 'a' * 64, json.dumps(opening_seed(area))))
            finally:
                production_area.reset(token)
        yield client
    app.dependency_overrides.pop(current_user, None)


def api_headers(area='torna', generation=None):
    result = {'X-Production-Area': area}
    if generation is not None: result['X-Planning-Generation'] = generation
    return result


@pytest.mark.parametrize('area', ['torna', 'cubuk-filtre'])
@pytest.mark.parametrize('generation', [None, 'old-generation', 'new-other-area'])
def test_ho04_old_generation_rejected_before_mutation_or_receipt(isolated_api, monkeypatch, area, generation):
    def forbidden(*args, **kwargs):
        pytest.fail('Stale generation reached route execution or receipt lookup.')
    from app import collaboration
    monkeypatch.setattr(collaboration, 'production_command', forbidden)
    monkeypatch.setattr(collaboration, 'request_status', forbidden)
    paths = [('POST', '/api/production/commands'), ('POST', '/api/scenarios'),
             ('POST', '/api/scenarios/old/publication-preview'), ('POST', '/api/scenarios/old/publish'),
             ('PATCH', '/api/planning-state'), ('PUT', '/api/planning-state'),
             ('GET', '/api/collaboration/requests/old-success?kind=production'),
             ('GET', '/api/planning-state/transactions/old-pending')]
    token = production_area.set(area)
    try: before = rows(database.settings.database_path if area == 'torna' else database.settings.database_path.with_name('api-cubuk-filtre.sqlite'))
    finally: production_area.reset(token)
    for method, path in paths:
        response = isolated_api.request(method, path, headers=api_headers(area, generation))
        assert response.status_code == 409, (method, path, response.text)
        assert response.json()['detail']['code'] == 'handover-generation'
    target = settings.database_path if area == 'torna' else settings.database_path.with_name('api-cubuk-filtre.sqlite')
    assert rows(target) == before


def test_ho05_current_generation_keeps_identical_ids_and_owner_receipts_area_scoped(isolated_api):
    for area in ['torna', 'cubuk-filtre']:
        headers = api_headers(area, f'new-{area}')
        state = isolated_api.get('/api/planning-state', headers=headers)
        assert state.status_code == 200
        assert state.headers['x-planning-generation'] == f'new-{area}'
        assert state.json()['generation'] == f'new-{area}'
        status = isolated_api.get('/api/collaboration/status', headers=headers).json()
        assert status['generation'] == f'new-{area}'
        payload = {'id': 'same-draft', 'name': area, 'createdAt': '2026-11-05', 'notes': '', 'seed': state.json()['seed'], 'result': {'batches': []}}
        response = isolated_api.post('/api/scenarios', headers=headers, json=payload)
        assert response.status_code == 201, response.text
        assert response.json()['ownerId'] == ADMIN.id
        assert response.json()['name'] == area
        assert isolated_api.get('/api/collaboration/requests/same-request?kind=production', headers=headers).json() == {'committed': False}
    app.dependency_overrides[current_user] = lambda: OPERATOR
    for area in ['torna', 'cubuk-filtre']:
        assert isolated_api.get('/api/scenarios/same-draft', headers=api_headers(area, f'new-{area}')).status_code == 404


def add_attachments(source, directory, files):
    directory.mkdir(exist_ok=True)
    with sqlite3.connect(source) as db:
        db.execute("INSERT INTO feedbacks(id,author_id,author_name,body,created_at,updated_at) VALUES(?,?,?,?,?,?)", ('feedback', 'user', 'Synthetic user', 'Fixture', '2026-11-05', '2026-11-05'))
        for index, (key, content) in enumerate(files.items()):
            (directory / key).write_bytes(content)
            db.execute('INSERT INTO feedback_attachments VALUES(?,?,?,?,?,?,?,?,?)', (f'attachment-{index}', 'feedback', 'user', 'document', key, 'text/plain', len(content), key, '2026-11-05'))


def test_ho06_production_filter_flag_exposes_only_an_imported_opening(tmp_path, monkeypatch):
    path = tmp_path / 'production.sqlite'
    monkeypatch.setitem(settings.__dict__, 'database_path', path)
    monkeypatch.setitem(settings.__dict__, 'upload_dir', tmp_path / 'production-uploads')
    monkeypatch.setitem(settings.__dict__, 'app_env', 'production')
    monkeypatch.setitem(settings.__dict__, 'enable_filter_production', True)
    app.dependency_overrides[current_user] = lambda: ADMIN
    try:
        with TestClient(app) as client:
            assert client.get('/api/me').json()['availableAreas'] == ['torna']
            assert client.get('/api/planning-state', headers=api_headers('cubuk-filtre')).status_code == 400
        # Create an owner-supplied synthetic export, separate from the running stores.
        source = tmp_path / 'filter-source.sqlite'
        with sqlite3.connect(source) as db:
            db.execute('CREATE TABLE planning_state(state_key TEXT PRIMARY KEY,seed_json TEXT,updated_at TEXT,updated_by_id TEXT,updated_by_name TEXT)')
            db.execute('INSERT INTO planning_state VALUES(?,?,?,?,?)', ('default', json.dumps(opening_seed('cubuk-filtre')), 'source-filter-revision', 'source-user', 'Synthetic operator'))
        target = path.with_name('production-cubuk-filtre.sqlite')
        # No initialized empty store may be installed as the accepted production opening.
        if target.exists():
            assert all(not values for name, values in rows(target).items() if name in {'planning_state', 'production_handover', 'production_opening'})
            target.unlink()
        handover.import_offline_opening(source, target, area='cubuk-filtre', generation_id='filter-opening', expected_sha256=digest(source))
        before = rows(target)
        with TestClient(app) as client:
            assert client.get('/api/me').json()['availableAreas'] == ['torna', 'cubuk-filtre']
            response = client.get('/api/planning-state', headers=api_headers('cubuk-filtre'))
            assert response.status_code == 200
            assert response.json()['seed'] == opening_seed('cubuk-filtre')
            assert response.headers['x-planning-generation'] == 'filter-opening'
        assert rows(target) == before, 'Restart must preserve the exact imported opening.'
    finally:
        app.dependency_overrides.pop(current_user, None)


def test_ho07_valid_attachments_match_manifest_and_source_remains_exact(source, tmp_path):
    source_uploads = tmp_path / 'source-uploads'
    add_attachments(source, source_uploads, {'shared.txt': b'accepted', 'own.txt': b'new-file'})
    source_hash = digest(source)
    target = tmp_path / 'target.sqlite'; uploads = tmp_path / 'target-uploads'
    import_source(source, target, source_upload_dir=source_uploads, target_upload_dir=uploads)
    with sqlite3.connect(target) as db:
        metadata = json.loads(db.execute('SELECT metadata_json FROM production_handover').fetchone()[0])
    assert metadata['attachmentSha256'] == {key: hashlib.sha256(value).hexdigest() for key, value in {'shared.txt': b'accepted', 'own.txt': b'new-file'}.items()}
    assert (uploads / 'shared.txt').read_bytes() == b'accepted'
    assert (uploads / 'own.txt').read_bytes() == b'new-file'
    assert digest(source) == source_hash
    assert not (uploads / '.opening-import-lock').exists()


def test_ho08_attachment_collision_never_clobbers_existing_file(source, tmp_path):
    source_uploads = tmp_path / 'source-uploads'
    add_attachments(source, source_uploads, {'first.txt': b'new', 'shared.txt': b'incoming'})
    uploads = tmp_path / 'target-uploads'; uploads.mkdir()
    (uploads / 'shared.txt').write_bytes(b'accepted-by-another-area')
    target = tmp_path / 'target.sqlite'
    with pytest.raises(ValueError, match='different contents'):
        import_source(source, target, source_upload_dir=source_uploads, target_upload_dir=uploads)
    assert not target.exists()
    assert {p.name: p.read_bytes() for p in uploads.iterdir()} == {'shared.txt': b'accepted-by-another-area'}


def test_ho09_final_target_collision_cleans_new_files_and_preserves_accepted_shared_upload(source, tmp_path, monkeypatch):
    source_uploads = tmp_path / 'source-uploads'
    add_attachments(source, source_uploads, {'shared.txt': b'accepted', 'own.txt': b'new-file'})
    uploads = tmp_path / 'target-uploads'; uploads.mkdir()
    (uploads / 'shared.txt').write_bytes(b'accepted')
    target = tmp_path / 'target.sqlite'
    original_link = handover.os.link
    def collide(src, dst):
        if Path(dst) == target:
            target.write_bytes(b'competing-target')
        return original_link(src, dst)
    monkeypatch.setattr(handover.os, 'link', collide)
    with pytest.raises(FileExistsError):
        import_source(source, target, source_upload_dir=source_uploads, target_upload_dir=uploads)
    assert target.read_bytes() == b'competing-target'
    assert {p.name: p.read_bytes() for p in uploads.iterdir()} == {'shared.txt': b'accepted'}


def test_ho10_concurrent_area_imports_share_upload_lock_without_removing_accepted_files(source, tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    source_uploads = tmp_path / 'source-uploads'
    add_attachments(source, source_uploads, {'shared.txt': b'accepted'})
    filter_source = tmp_path / 'filter-source.sqlite'
    filter_source.write_bytes(source.read_bytes())
    with sqlite3.connect(filter_source) as db:
        seed = json.loads(db.execute('SELECT seed_json FROM planning_state').fetchone()[0])
        seed['productionArea'] = 'cubuk-filtre'
        db.execute('UPDATE planning_state SET seed_json=?', (json.dumps(seed),))
    uploads = tmp_path / 'target-uploads'; target = tmp_path / 'piston.sqlite'; filter_target = tmp_path / 'filter.sqlite'
    reached, release = Event(), Event()
    original_link = handover.os.link
    def pause(src, dst):
        if Path(dst) == target:
            reached.set()
            assert release.wait(10), 'Synthetic concurrent import timed out.'
        return original_link(src, dst)
    monkeypatch.setattr(handover.os, 'link', pause)
    with ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(import_source, source, target, source_upload_dir=source_uploads, target_upload_dir=uploads)
        try:
            assert reached.wait(10)
            with pytest.raises(FileExistsError):
                handover.import_offline_opening(filter_source, filter_target, area='cubuk-filtre', generation_id='filter-opening', expected_sha256=digest(filter_source), source_upload_dir=source_uploads, target_upload_dir=uploads)
            assert not filter_target.exists()
            assert (uploads / 'shared.txt').read_bytes() == b'accepted'
        finally:
            release.set()
        assert pending.result()['replayed'] is False
    handover.import_offline_opening(filter_source, filter_target, area='cubuk-filtre', generation_id='filter-opening', expected_sha256=digest(filter_source), source_upload_dir=source_uploads, target_upload_dir=uploads)
    assert (uploads / 'shared.txt').read_bytes() == b'accepted'
    assert target.exists() and filter_target.exists()
    assert not (uploads / '.opening-import-lock').exists()


def test_ho11_existing_archive_and_ordered_preferences_are_preserved(source, tmp_path):
    preferences = [
        {"key": "synthetic-product", "ruleType": "priority", "machines": ["C-01"], "source": "planner-a"},
        {"key": "synthetic-product", "ruleType": "fallback", "machines": ["C-02"], "source": "planner-b"},
    ]
    with sqlite3.connect(source) as db:
        value = json.loads(db.execute('SELECT seed_json FROM planning_state').fetchone()[0])
        value['preferences'] = preferences
        db.execute('UPDATE planning_state SET seed_json=?', (json.dumps(value),))
        db.execute('INSERT INTO production_archive_snapshots VALUES(?,?,?,?,?,?)', ('existing-archive', '[]', hashlib.sha256(b'[]').hexdigest(), 'source-revision', 'synthetic-existing', '2026-11-04'))
    target = tmp_path / 'target.sqlite'
    source_hash = digest(source)
    import_source(source, target)
    with sqlite3.connect(target) as db:
        stored = json.loads(db.execute('SELECT seed_json FROM planning_state').fetchone()[0])
        archive = db.execute('SELECT * FROM production_archive_snapshots WHERE id=?', ('existing-archive',)).fetchone()
        opening = json.loads(db.execute('SELECT seed_json FROM production_opening').fetchone()[0])
    assert stored['preferences'] == opening['preferences'] == preferences
    assert stored == value
    assert archive == ('existing-archive', '[]', hashlib.sha256(b'[]').hexdigest(), 'source-revision', 'synthetic-existing', '2026-11-04')
    assert digest(source) == source_hash


def test_ho12_current_generation_applies_one_real_command_and_old_receipt_cannot_confirm_it(isolated_api):
    fixture = json.loads((Path(__file__).parent / 'fixtures' / 'collaboration.json').read_text())
    token = production_area.set('torna')
    try:
        saved = database.save_planning_state(fixture['seed'], expected_updated_at=database.planning_state()['updatedAt'], can_manage_settings=True, mode='operational', flow_settings_version=1, route_placement_version=1, production_split_version=1, process_wait_settings_version=1)
        with database.connection() as db:
            db.execute('UPDATE production_opening SET world_revision=?,state_hash=?,seed_json=?', (saved['updatedAt'], saved['stateHash'], json.dumps(saved['seed'])))
    finally:
        production_area.reset(token)
    headers = api_headers('torna', 'new-torna')
    command = fixture['commands'][0]
    accepted = isolated_api.post('/api/production/commands', headers=headers, json=command)
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()['replayed'] is False
    after = rows(settings.database_path)
    assert len(after['production_commands']) == 1
    retry = isolated_api.post('/api/production/commands', headers=headers, json=command)
    assert retry.status_code == 200
    assert retry.json()['replayed'] is True
    assert retry.json()['appliedRevision'] == accepted.json()['appliedRevision']
    assert rows(settings.database_path) == after
    status_path = f"/api/collaboration/requests/{command['requestId']}?kind=production"
    for stale in [None, 'old-torna']:
        assert isolated_api.post('/api/production/commands', headers=api_headers('torna', stale), json=command).status_code == 409
        assert isolated_api.get(status_path, headers=api_headers('torna', stale)).status_code == 409
    assert rows(settings.database_path) == after
    assert isolated_api.get(status_path, headers=headers).json()['committed'] is True
    app.dependency_overrides[current_user] = lambda: OPERATOR
    assert isolated_api.get(status_path, headers=headers).json() == {'committed': False}
