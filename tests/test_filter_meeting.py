"""Synthetic 10,000-piece charge: 9,000 recorded, 1,000 still to process."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from app import database as db, collaboration as collab
from app.auth import CurrentUser
from app.planning_delta import state_hash
from app.production_area import production_area
from test_wip_stage_safety import database_contents

USER = CurrentUser('filter-review', 'Review Planner', 'review@example.test', 'user')

@pytest.fixture
def filter_world(tmp_path, monkeypatch):
    token = production_area.set('cubuk-filtre')
    monkeypatch.setattr(db, 'settings', SimpleNamespace(database_path=tmp_path / 'filter.sqlite', upload_dir=tmp_path / 'uploads'))
    db.init_database()
    fixture = json.loads((Path(__file__).parent / 'fixtures/filter-meeting.json').read_text())
    db.save_planning_state(fixture['seed'], can_manage_settings=True, flow_settings_version=1,
        route_placement_version=1, production_split_version=1, process_wait_settings_version=1, stock_planning_version=1, monthly_planning_version=1)
    try:
        yield fixture
    finally:
        production_area.reset(token)


def request(fixture, seed=None, request_id='filter-count'):
    seed = seed or db.planning_state()['seed']
    return dict(requestId=request_id, expectedBasis=state_hash({**seed, 'planningEvents': [], 'chargeJourneyNotes': []}),
        command=fixture['command'])


def test_cf_mtg12_transfer_is_atomic_replayable_and_preserves_recorded_output(filter_world):
    before = copy.deepcopy(db.planning_state()['seed'])
    command = request(filter_world)
    accepted = collab.production_command(command, USER)
    saved = db.planning_state()['seed']
    assert saved['wipLots'] == before['wipLots']
    assert saved['productionHistory'] == before['productionHistory']
    shared_id = before['machines'][0]['currentJob']['sharedCharge']['id']
    queued = [b for b in saved['manualBatches'] if b.get('sharedCharge', {}).get('id') == shared_id]
    running = [m for m in saved['machines'] if m['currentJob'].get('sharedCharge', {}).get('id') == shared_id]
    assert sum(b['quantity'] for b in queued) + sum(m['currentJob']['quantity'] for m in running) == 1000
    assert all(b['machineId'] == 'L-02' for b in queued)
    assert all(m['id'] == 'L-02' for m in running)
    assert saved['machines'][0]['currentJob']['quantity'] == 0
    assert saved['planNeedsRecalculation'] is True
    snapshot = database_contents()
    retry = collab.production_command(command, USER)
    assert retry['replayed'] and retry['appliedRevision'] == accepted['appliedRevision']
    assert database_contents() == snapshot
    with pytest.raises(HTTPException) as stale:
        collab.production_command({**command, 'requestId': 'stale-filter-count'}, USER)
    assert stale.value.status_code == 409
    assert database_contents() == snapshot


def test_cf_mtg13_count_without_output_cannot_release_a_machine(filter_world):
    seed = copy.deepcopy(db.planning_state()['seed'])
    seed['productionHistory'] = []
    seed['wipLots'] = []
    seed['wipMovements'] = []
    db.save_planning_state(seed, db.planning_state()['updatedAt'], mode='operational', can_manage_settings=True,
        flow_settings_version=1, route_placement_version=1, production_split_version=1, process_wait_settings_version=1, stock_planning_version=1, monthly_planning_version=1)
    collab.production_command(request(filter_world), USER)
    saved = db.planning_state()['seed']
    assert saved['machines'][0]['currentJob']['quantity'] == 500
    # The existing count editor recalculates forecast dates. It must not move,
    # resize or rename the waiting portion when actual output is absent.
    identity = lambda rows: [{k: row.get(k) for k in ('id', 'quantity', 'machineId', 'sharedCharge', 'workOrder')} for row in rows]
    assert identity(saved['manualBatches']) == identity(seed['manualBatches'])
    assert saved['productionHistory'] == [] and saved['wipLots'] == []


def test_cf_mtg14_changed_sibling_queue_rejects_without_any_write(filter_world):
    seed = db.planning_state()['seed']
    old = copy.deepcopy(seed)
    old['manualBatches'][0]['quantity'] = 499
    snapshot = database_contents()
    with pytest.raises(HTTPException) as stale:
        collab.production_command(request(filter_world, old), USER)
    assert stale.value.status_code == 409
    assert database_contents() == snapshot
