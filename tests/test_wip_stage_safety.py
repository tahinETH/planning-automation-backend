import copy
import json

import pytest
from fastapi import HTTPException
from app import database as db, collaboration as collab
from app.planning_delta import state_hash
from test_production_date_correction import world, USER


def request(seed, kind, args, request_id):
    basis = {**seed, 'chargeJourneyNotes': [], 'planningEvents': []}
    if kind in ('changeWipStage', 'releaseHeldWip'):
        lot = next(row for row in seed['wipLots'] if row['id'] == args[0])
        ids = {lot.get(key) for key in ('id', 'sourceHistoryEntryId', 'sourceBatchId', 'parentLotId')} - {None, ''}
        basis.update(planNeedsRecalculation=False, lastAutomaticPlan=None, planRunSequence=None)
        for key in ('wipLots', 'wipMovements', 'productionHistory'):
            basis[key] = [row for row in seed.get(key, []) if any(isinstance(v, str) and v in ids for v in row.values())]
    return dict(requestId=request_id, expectedBasis=state_hash(basis), command=dict(kind=kind, args=args))


def database_contents():
    with db.connection() as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        return {table: sorted(map(tuple, conn.execute('SELECT * FROM "' + table + '"')), key=repr) for table in tables}


@pytest.mark.parametrize('case', ['reopen', 'backdate', 'repeat', 'partial-repeat'])
def test_wip_safe09_server_rejects_without_state_audit_opening_or_receipt(world, case):
    seed = copy.deepcopy(db.planning_state()['seed'])
    lot = seed['wipLots'][0]
    end = lot['completedSteps'][-1]['end']
    if case in ('repeat', 'partial-repeat'):
        # An older record can already have a queue flag after completion.
        lot.update(stage='gkm-queue', nextProcess='gkm')
        db.save_planning_state(seed, db.planning_state()['updatedAt'], mode='operational', can_manage_settings=True,
            flow_settings_version=1, route_placement_version=1, production_split_version=1, process_wait_settings_version=1)
        command = request(seed, 'finishWipOperation', [dict(lotId=lot['id'], process='gkm', resourceId='V-02',
            resourceName='GKM', quantity=500 if case == 'partial-repeat' else 1005,
            startedAt=lot['readyAt']+1, completedAt=lot['readyAt']+1)], 'repeat-' + case)
    else:
        command = request(seed, 'changeWipStage', [lot['id'], 'gkm-queue' if case == 'reopen' else 'delivery-ready',
            lot['readyAt'] if case == 'reopen' else int(end)-1], case)
    before = database_contents()
    with pytest.raises(HTTPException) as error:
        collab.production_command(command, USER)
    assert error.value.status_code == 422
    assert ('önce olamaz' if case == 'backdate' else 'tamamlanmış') in error.value.detail
    assert database_contents() == before
    assert db.planning_state()['seed']['machines'][0]['currentJob']['quantity'] == 1295


def test_wip_safe10_valid_location_replays_once_and_late_request_cannot_reopen(world):
    seed = db.planning_state()['seed']
    lot = seed['wipLots'][0]
    rejected_later = request(seed, 'changeWipStage', [lot['id'], 'gkm-queue', lot['readyAt']], 'old-reopen')
    accepted_request = request(seed, 'changeWipStage', [lot['id'], 'delivery-ready', int(lot['completedSteps'][-1]['end'])], 'same-day')
    accepted = collab.production_command(accepted_request, USER)
    saved = db.planning_state()
    assert saved['seed']['wipLots'][0]['readyAt'] == lot['completedSteps'][-1]['end']
    assert saved['seed']['wipLots'][0]['completedSteps'] == lot['completedSteps']
    assert saved['seed']['machines'] == seed['machines']
    assert saved['seed']['manualBatches'] == seed['manualBatches']
    assert saved['seed']['planNeedsRecalculation'] is True
    before = database_contents()
    retry = collab.production_command(accepted_request, USER)
    assert retry['replayed'] and retry['appliedRevision'] == accepted['appliedRevision']
    assert database_contents() == before
    with pytest.raises(HTTPException) as stale:
        collab.production_command(rejected_later, USER)
    assert stale.value.status_code == 409
    assert database_contents() == before
