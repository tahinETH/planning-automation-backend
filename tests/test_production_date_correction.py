import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from app import database as db, collaboration as collab
from app.auth import CurrentUser

USER = CurrentUser('date-planner', 'Date Planner', 'date@example.test', 'user')

@pytest.fixture
def world(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'settings', SimpleNamespace(database_path=tmp_path / 'date.sqlite', upload_dir=tmp_path / 'uploads'))
    db.init_database()
    fixture = json.loads((Path(__file__).parent / 'fixtures/date-correction.json').read_text())
    db.save_planning_state(fixture['seed'], can_manage_settings=True, flow_settings_version=1,
        route_placement_version=1, production_split_version=1, process_wait_settings_version=1)
    assert db.planning_state()['seed'] == fixture['seed']
    return fixture

def test_date_j06_atomic_correction_reload_trusted_actor_and_exact_retry(world):
    before = copy.deepcopy(db.planning_state()['seed'])
    result = collab.production_command(world['request'], USER)
    after = db.planning_state()['seed']
    assert after['machines'] == before['machines']
    assert after['manualBatches'] == before['manualBatches']
    assert after['machines'][0]['currentJob']['quantity'] == 1295
    shipped = [r for r in after['productionHistory'] if r['inventoryStatus'] == 'delivered']
    assert len(shipped) == 1 and shipped[0]['completedQuantity'] == 1005
    assert shipped[0]['deliveredAt'] == '2026-11-12'
    assert shipped[0]['deliveredAtPrecision'] == 'day'
    assert not shipped[0].get('deliveredAtTime')
    audit = next(r for r in after['wipMovements'] if r['kind'] == 'dates-corrected')
    assert audit['actor'] == USER.name
    assert audit['dateCorrection']['before'] == before['wipLots'][0]['completedSteps']
    retry = collab.production_command(world['request'], USER)
    assert retry['replayed'] and retry['appliedRevision'] == result['appliedRevision']
    assert db.planning_state()['seed'] == after
    with pytest.raises(HTTPException) as stale:
        collab.production_command({**world['request'], 'requestId': 'duplicate-intent'}, USER)
    assert stale.value.status_code == 409
    assert db.planning_state()['seed'] == after

@pytest.mark.parametrize('invalid', ['order', 'consent', 'missing-process'])
def test_date_j07_invalid_correction_writes_no_state_or_receipt(world, invalid):
    request = copy.deepcopy(world['request'])
    correction = request['command']['args'][0]['dateCorrection']
    if invalid == 'order':
        correction['steps'][1]['end']['value'] = '2026-11-13'
    elif invalid == 'consent':
        correction['confirmedOrder'] = False
    else:
        correction['steps'].pop()
    before = db.planning_state()
    with pytest.raises(HTTPException) as rejected:
        collab.production_command(request, USER)
    assert rejected.value.status_code == 422
    assert db.planning_state() == before
    with db.connection() as conn:
        assert conn.execute('SELECT COUNT(*) FROM production_commands').fetchone()[0] == 0
