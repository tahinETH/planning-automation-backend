"""STG-PERF01: metadata lists and negotiated compression preserve saved data."""
import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from app import database as db
from app.auth import CurrentUser, current_user
from app.main import app
from app.production_area import production_area

USER = CurrentUser('stage-perf', 'Test', 'test@example.test', 'admin')

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'settings', SimpleNamespace(database_path=tmp_path/'stage.sqlite', upload_dir=tmp_path/'uploads'))
    for area in ('torna', 'cubuk-filtre'):
        token = production_area.set(area)
        try:
            db.init_database()
            seed = {'productionArea': area, 'orders': [], 'machines': [], 'products': [], 'preferences': [],
                    'wipLots': [{'id': f'lot-{i}', 'availableQuantity': 10, 'stage': 'drilling-queue'} for i in range(1000)] +
                               [{'id': 'delivered', 'availableQuantity': 5, 'stage': 'delivered'},
                                {'id': 'empty', 'availableQuantity': 0, 'stage': 'drilling-queue'}]}
            db.save_planning_state(seed, can_manage_settings=True, actor_id=USER.id, actor_name=USER.name)
            with db.connection() as conn:
                conn.execute('INSERT INTO order_revisions VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                    ('revision-'+area, 'order-a', 'Widget', 'approved', '2026-10-30', '2026-10-30',
                     '{"quantity":10}', '{"quantity":12}', '{"changed":true}', json.dumps(seed), '{"summary":{"plannedBatchCount":1}}'))
        finally:
            production_area.reset(token)
    monkeypatch.setitem(app.dependency_overrides, current_user, lambda: USER)
    with TestClient(app) as value:
        yield value
    app.dependency_overrides.pop(current_user, None)

@pytest.mark.parametrize('area', ['torna', 'cubuk-filtre'])
def test_metadata_and_selected_detail_preserve_scope_legacy_and_records(client, area):
    headers = {'X-Production-Area': area, 'Accept-Encoding': 'identity'}
    before = client.get('/api/planning-state', headers=headers).json()
    history = client.get('/api/planning-state/history?summary=true', headers=headers)
    revisions = client.get('/api/revisions?summary=true', headers=headers)
    assert history.status_code == revisions.status_code == 200
    assert history.headers['x-production-area'] == area
    row = history.json()[0]
    assert row['openWipCount'] == 1000
    assert row['createdBy'] == {'id': USER.id, 'name': USER.name}
    assert 'seed' not in row
    assert revisions.json()[0]['id'] == 'revision-'+area
    assert revisions.json()[0]['original'] == {'quantity': 10}
    assert revisions.json()[0]['requested'] == {'quantity': 12}
    assert 'seed' not in revisions.json()[0] and 'result' not in revisions.json()[0]
    full_history = client.get('/api/planning-state/history', headers=headers)
    full_revisions = client.get('/api/revisions', headers=headers)
    assert len(history.content) < len(full_history.content)/100
    assert len(revisions.content) < len(full_revisions.content)/100
    detail = client.get('/api/planning-state/history/'+row['id'], headers=headers)
    # A saved history snapshot stays exact; startup may add current setting defaults.
    assert detail.json()['seed'] == full_history.json()[0]['seed']
    assert detail.json()['seed']['wipLots'] == before['seed']['wipLots']
    detail_revision = client.get('/api/revisions/revision-'+area, headers=headers)
    assert detail_revision.json() == full_revisions.json()[0]
    other = 'torna' if area == 'cubuk-filtre' else 'cubuk-filtre'
    assert client.get('/api/revisions/revision-'+other, headers=headers).status_code == 404
    assert client.get('/api/planning-state/history/missing', headers=headers).status_code == 404
    assert client.get('/api/revisions/missing', headers=headers).status_code == 404
    assert client.get('/api/planning-state', headers=headers).json() == before

@pytest.mark.parametrize('area', ['torna', 'cubuk-filtre'])
def test_negotiated_gzip_reduces_wire_bytes_without_changing_json(client, area):
    path = '/api/planning-state/history'
    identity = client.get(path, headers={'X-Production-Area': area, 'Accept-Encoding': 'identity'})
    compressed = client.get(path, headers={'X-Production-Area': area, 'Accept-Encoding': 'gzip'})
    assert compressed.json() == identity.json()
    assert 'content-encoding' not in identity.headers
    assert compressed.headers['content-encoding'] == 'gzip'
    assert 'Accept-Encoding' in compressed.headers['vary']
    assert int(compressed.headers['content-length']) < len(identity.content)/5
    assert compressed.headers['x-production-area'] == area
