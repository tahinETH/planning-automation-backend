import json
from types import SimpleNamespace
import pytest
from app import database as db

@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'settings', SimpleNamespace(database_path=tmp_path / 'audit.sqlite', upload_dir=tmp_path / 'uploads'))
    db.init_database()

def records():
    with db.connection() as conn:
        return [json.loads(r['metadata_json']) for r in conn.execute('SELECT metadata_json FROM planning_write_audit ORDER BY rowid')]

def save(seed, **kw):
    return db.save_planning_state(seed, can_manage_settings=True, actor_id='user', actor_name='Planner', request_id='request-1', session_id='session-1', **kw)

def test_saved_audit_is_atomic_and_payload_free():
    saved = save({'machines': [], 'productionHistory': [{'id': 'private-record', 'note': 'SECRET NOTE'}]})
    row = records()[-1]
    assert row['outcome'] == 'saved'
    assert (row['actorId'], row['requestId'], row['sessionId']) == ('user', 'request-1', 'session-1')
    assert row['resultRevision'] == saved['updatedAt']
    assert row['changes']['productionHistory'] == {'before': 0, 'after': 1}
    assert 'SECRET NOTE' not in json.dumps(row)
    assert 'private-record' not in json.dumps(row)

def test_conflict_logged_after_rollback():
    original = save({'machines': []})
    with pytest.raises(db.PlanningStateConflict):
        save({'machines': [], 'planningEvents': []}, expected_updated_at='stale')
    row = records()[-1]
    assert row['outcome'] == 'conflict'
    assert row['expectedRevision'] == 'stale'
    assert row['currentRevision'] == original['updatedAt']
    assert row['resultRevision'] is None
    assert db.planning_state()['updatedAt'] == original['updatedAt']

def test_audit_failure_rolls_back_and_does_not_mask_conflict(monkeypatch):
    original = save({'machines': []})
    def fail(*args):
        raise RuntimeError('audit unavailable')
    monkeypatch.setattr(db, '_insert_planning_audit', fail)
    with pytest.raises(RuntimeError, match='audit unavailable'):
        save({'machines': [], 'planningEvents': []}, expected_updated_at=original['updatedAt'])
    assert db.planning_state()['updatedAt'] == original['updatedAt']
    with pytest.raises(db.PlanningStateConflict):
        save({'machines': []}, expected_updated_at='stale')

def test_validation_and_identifier_sanitization():
    with pytest.raises(ValueError):
        db.save_planning_state({'machines': [], 'orders': [{'id': ''}]}, can_manage_settings=True,
                               request_id='Bearer secret token', session_id='x' * 129)
    row = records()[-1]
    assert row['outcome'] == 'validation-failed'
    assert row['sessionId'] == ''
    assert row['requestId'] != 'Bearer secret token'
    assert db.planning_state() is None

def test_http_headers_and_authenticated_actor_are_recorded():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.auth import create_test_session
    response = TestClient(app).put('/api/planning-state', json={
        'seed': {'machines': []}, 'expectedUpdatedAt': '', 'actor_id': 'forged'
    }, headers={'Authorization': f"Bearer {create_test_session('test-password', 'admin')}",
                'X-Planning-Request-Id': 'http-request', 'X-Planning-Session-Id': 'http-session'})
    assert response.status_code == 200, response.text
    row = records()[-1]
    assert row['requestId'] == 'http-request'
    assert row['sessionId'] == 'http-session'
    assert row['actorId'] == response.json()['updatedBy']['id']
    assert row['actorId'] != 'forged'
