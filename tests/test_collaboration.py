import copy
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from app import database as db
from app import collaboration as collab
from app.auth import CurrentUser

A = CurrentUser('operator-a', 'A', 'a@example.test', 'admin')
B = CurrentUser('operator-b', 'B', 'b@example.test', 'user')

@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'settings', SimpleNamespace(database_path=tmp_path / 'collaboration.sqlite', upload_dir=tmp_path / 'uploads'))
    db.init_database()

@pytest.fixture
def factory():
    value = json.loads((Path(__file__).parent / 'fixtures' / 'collaboration.json').read_text())
    state = db.save_planning_state(value['seed'], can_manage_settings=True, flow_settings_version=1, route_placement_version=1, production_split_version=1, process_wait_settings_version=1)
    # Use the canonical stored opening state for command fingerprints.
    assert state['seed'] == value['seed']
    return value


def scenario(seed=None):
    return dict(id='plan-a', name='My plan', createdAt='2026-10-21T09:00:00Z', notes='', seed=seed or {'orders': [], 'machines': []}, result={'summary': {'plannedBatchCount': 0}})


def test_col01_private_save_cannot_write_orders_or_factory():
    baseline = db.save_planning_state({'orders': [{'id': 'official', 'dueDate': '2026-10-30'}], 'machines': []}, can_manage_settings=True)
    baseline = db.planning_state()
    saved = collab.save_scenario(scenario({'orders': [{'id': 'hypothesis'}], 'machines': [], 'productionHistory': [{'id': 'invented'}]}), A)
    assert saved['ownerId'] == A.id and saved['revision'] == 1
    assert saved['seed']['productionHistory'] == []
    assert db.planning_state() == baseline
    assert db.order_details()[0]['id'] == 'official'
    assert collab.list_scenarios(B) == []
    with pytest.raises(HTTPException) as e: collab.get_scenario(saved['id'], B)
    assert e.value.status_code == 404


def test_col02_owner_cas_share_fork_and_revoke():
    saved = collab.save_scenario(scenario(), A)
    with pytest.raises(HTTPException): collab.save_scenario({**saved, 'name': 'Takeover'}, B)
    updated = collab.save_scenario({**saved, 'name': 'Reviewed'}, A)
    with pytest.raises(HTTPException) as e: collab.save_scenario(saved, A)
    assert e.value.status_code == 409
    shared = collab.share_scenario(saved['id'], updated['revision'], True, A)
    fork = collab.fork_scenario(saved['id'], B)
    assert fork['ownerId'] == B.id and fork['sourceRevision'] == shared['revision']
    assert fork['id'] != saved['id'] and fork['shared'] is False
    with pytest.raises(HTTPException): collab.delete_scenario(saved['id'], shared['revision'], B)
    collab.share_scenario(saved['id'], shared['revision'], False, A)
    with pytest.raises(HTTPException): collab.get_scenario(saved['id'], B)
    assert collab.get_scenario(fork['id'], B)['name'].endswith('kopya')


def test_col03_legacy_is_visible_but_cannot_be_claimed():
    with db.connection() as conn:
        conn.execute('INSERT INTO scenarios VALUES(?,?,?,?,?,?)', ('legacy', 'Legacy', '2026-10-01', '', '{"orders":[],"machines":[]}', '{"summary":{}}'))
    legacy = collab.get_scenario('legacy', A)
    assert legacy['legacy'] and not legacy['canEdit']
    with pytest.raises(HTTPException): collab.save_scenario(legacy, A)
    with pytest.raises(HTTPException): collab.delete_scenario('legacy', 0, A)
    assert collab.fork_scenario('legacy', A)['sourceId'] == 'legacy'


def test_col04_competing_deliveries_have_one_winner_and_retry_is_idempotent(factory):
    request = factory['commands'][0]
    first = collab.production_command(request, A)
    retry = collab.production_command(request, A)
    assert retry['replayed'] and retry['appliedRevision'] == first['appliedRevision']
    with pytest.raises(HTTPException) as e:
        collab.production_command({**request, 'requestId': 'competing-delivery'}, B)
    assert e.value.status_code == 409
    lot = next(row for row in db.planning_state()['seed']['wipLots'] if row['id'] == 'lot-a')
    assert lot['availableQuantity'] == 20 and lot['deliveredQuantity'] == 80
    assert next(row for row in db.planning_state()['seed']['productionHistory'] if row['id'] == 'void-79')['inventoryStatus'] == 'voided'
    with db.connection() as conn:
        assert conn.execute('SELECT COUNT(*) FROM production_commands').fetchone()[0] == 1
        opening = conn.execute('SELECT seed_json FROM production_opening').fetchone()[0]
        assert json.loads(opening)['wipLots'][0]['availableQuantity'] == 100


def test_col05_independent_lots_do_not_conflict(factory):
    collab.production_command(factory['commands'][0], A)
    collab.production_command(factory['commands'][1], B)
    assert [lot['availableQuantity'] for lot in db.planning_state()['seed']['wipLots']] == [20, 20]


def test_col06_failure_rolls_back_all_records_and_receipt(factory, monkeypatch):
    original = db.planning_state()
    with db.connection() as conn:
        conn.execute("CREATE TRIGGER fail_command BEFORE INSERT ON production_commands BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
    with pytest.raises(Exception, match='injected failure'):
        collab.production_command(factory['commands'][0], A)
    assert db.planning_state() == original
    with db.connection() as conn:
        assert conn.execute('SELECT COUNT(*) FROM production_commands').fetchone()[0] == 0
        assert conn.execute('SELECT COUNT(*) FROM production_opening').fetchone()[0] == 0


def test_col07_publication_requires_admin_and_reviewed_world(factory):
    saved = collab.save_scenario(scenario(factory['seed']), A)
    status = collab.collaboration_status()
    request = dict(revision=saved['revision'], worldRevision=status['worldRevision'], previousId=None)
    with pytest.raises(HTTPException) as e: collab.publish_scenario(saved['id'], request, B)
    assert e.value.status_code == 403
    collab.production_command(factory['commands'][0], A)
    with pytest.raises(HTTPException) as e: collab.publish_scenario(saved['id'], request, A)
    assert e.value.status_code == 409
    assert collab.collaboration_status()['publicationId'] is None


def test_col08_reviewed_publication_preserves_facts_and_is_idempotent(factory):
    original = db.planning_state()
    saved = collab.save_scenario({**scenario(factory['seed']), 'worldRevision': original['updatedAt']}, A)
    preview = collab.publication_preview(saved['id'], dict(revision=saved['revision'], worldRevision=original['updatedAt'], previousId=None), A)
    published = collab.publish_scenario(saved['id'], preview, A)
    retry = collab.publish_scenario(saved['id'], preview, A)
    assert retry['replayed'] and retry['publicationId'] == published['publicationId']
    assert collab.collaboration_status()['publicationId'] == published['publicationId']
    for field in collab.FACTS:
        assert db.planning_state()['seed'].get(field) == original['seed'].get(field)
    with db.connection() as conn:
        assert conn.execute('SELECT COUNT(*) FROM published_plans').fetchone()[0] == 1


def test_col09_change_after_preview_rejects_publication(factory):
    original = db.planning_state()
    saved = collab.save_scenario({**scenario(factory['seed']), 'worldRevision': original['updatedAt']}, A)
    preview = collab.publication_preview(saved['id'], dict(revision=saved['revision'], worldRevision=original['updatedAt'], previousId=None), A)
    collab.production_command(factory['commands'][0], B)
    with pytest.raises(HTTPException) as e: collab.publish_scenario(saved['id'], preview, A)
    assert e.value.status_code == 409
    assert collab.collaboration_status()['publicationId'] is None
    assert db.planning_state()['seed']['wipLots'][0]['availableQuantity'] == 20


def test_col10_private_delta_receipt_and_stale_draft_preserve_all_shared_data(factory):
    original = db.planning_state()
    saved = collab.save_scenario({**scenario(factory['seed']), 'worldRevision': original['updatedAt']}, A)
    value = dict(requestId='draft-write', revision=saved['revision'], worldRevision=original['updatedAt'], delta={'set': {'source': 'private hypothesis'}, 'arrays': {}, 'remove': []})
    accepted = collab.patch_scenario(saved['id'], value, A)
    assert accepted['scenario']['revision'] == 2
    assert collab.patch_scenario(saved['id'], value, A)['replayed']
    with pytest.raises(HTTPException) as e: collab.patch_scenario(saved['id'], {**value, 'requestId': 'other-tab'}, A)
    assert e.value.status_code == 409
    assert db.planning_state() == original
    assert collab.request_status('draft-write', 'draft', B) == {'committed': False}
    assert collab.request_status('draft-write', 'draft', A)['committed']


def test_col11_simultaneous_delivery_transactions_have_one_winner(factory):
    from concurrent.futures import ThreadPoolExecutor
    def deliver(user):
        try:
            return collab.production_command({**factory['commands'][0], 'requestId': user.id}, user)
        except HTTPException as error:
            return error.status_code
    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(deliver, [A, B]))
    assert sum(isinstance(result, dict) for result in results) == 1
    assert results.count(409) == 1
    assert db.planning_state()['seed']['wipLots'][0]['availableQuantity'] == 20


def test_col12_http_actor_scope_and_retired_writers(factory):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.auth import current_user
    app.dependency_overrides[current_user] = lambda: B
    try:
        client = TestClient(app)
        first = client.post('/api/production/commands', json=factory['commands'][0])
        assert first.status_code == 200, first.text
        original = db.planning_state()
        assert client.put('/api/orders', json=[]).status_code == 409
        assert client.put('/api/planning-state', json={'seed': factory['seed'], 'expectedUpdatedAt': original['updatedAt'], 'mode': 'operational'}).status_code == 403
        assert client.post('/api/production/commands', json={**factory['commands'][0], 'actor_id': A.id}).status_code == 422
        assert db.planning_state() == original
        with db.connection() as conn:
            assert conn.execute('SELECT actor_id FROM production_commands').fetchone()[0] == B.id
    finally:
        app.dependency_overrides.pop(current_user, None)


def test_col13_private_plans_are_not_in_shared_snapshot(factory):
    saved = collab.save_scenario(scenario(factory['seed']), A)
    assert all(item['id'] != saved['id'] for item in db.scenarios())
    collab.share_scenario(saved['id'], saved['revision'], True, A)
    assert any(item['id'] == saved['id'] for item in db.scenarios())


def test_col14_official_revision_is_admin_only_and_does_not_publish_a_queue(factory):
    original = db.planning_state()
    with pytest.raises(HTTPException) as e: collab.production_command(factory['revisionCommand'], B)
    assert e.value.status_code == 403
    assert db.planning_state() == original
    changed = collab.production_command(factory['revisionCommand'], A)['current']
    assert changed['seed']['orders'][0]['quantity'] == 120
    assert changed['seed']['manualBatches'] == original['seed']['manualBatches']
    for field in collab.FACTS:
        if field != 'planningEvents': assert changed['seed'].get(field) == original['seed'].get(field)
    assert len(db.revisions()) == 1
    assert db.revisions()[0]['requested']['quantity'] == 120
    collab.production_command(factory['revisionCommand'], A)
    assert len(db.revisions()) == 1


def test_col15_share_fork_publish_and_deliver_keep_facts_and_record_actual_approver(factory):
    original = db.planning_state()
    original_orders = db.order_details()
    source = collab.save_scenario({**scenario(factory['seed']), 'worldRevision': original['updatedAt']}, A)
    source = collab.share_scenario(source['id'], source['revision'], True, A)
    fork = collab.fork_scenario(source['id'], B)
    fork = collab.save_scenario({**fork, 'name': 'B proposal', 'notes': 'Private draft note'}, B)
    assert collab.get_scenario(source['id'], A)['name'] == 'My plan'
    assert fork['sourceId'] == source['id'] and fork['sourceRevision'] == source['revision']
    assert db.planning_state() == original
    assert db.order_details() == original_orders
    fork = collab.share_scenario(fork['id'], fork['revision'], True, B)
    reviewer = CurrentUser('reviewer-c', 'Onaylayan Yönetici', 'c@example.test', 'admin')
    preview = collab.publication_preview(fork['id'], dict(revision=fork['revision'], worldRevision=original['updatedAt'], previousId=None), reviewer)
    result = collab.publish_scenario(fork['id'], {**preview, 'approvedBy': {'id': A.id, 'name': 'Forged name'}}, reviewer)
    approved = result['activePublication']
    assert approved['approvedBy'] == {'id': reviewer.id, 'name': reviewer.name}
    assert approved['scenarioName'] == 'B proposal' and approved['scenarioRevision'] == fork['revision']
    assert approved['approvedAt'] and approved['id'] == result['publicationId']
    assert set(approved) == {'id', 'scope', 'scenarioId', 'scenarioRevision', 'scenarioName', 'approvedBy', 'approvedAt'}
    for field in collab.FACTS:
        assert db.planning_state()['seed'].get(field) == original['seed'].get(field)
    collab.save_scenario({**fork, 'name': 'Changed later'}, B)
    assert collab.collaboration_status()['activePublication'] == approved
    assert collab.request_status(result['publicationId'], 'publication', reviewer)['activePublication'] == approved
    collab.production_command(factory['commands'][0], A)
    assert collab.collaboration_status()['activePublication'] == approved
    assert db.planning_state()['seed']['wipLots'][0]['deliveredQuantity'] == 80
    assert db.planning_state()['seed']['wipLots'][0]['availableQuantity'] == 20
    assert next(row for row in db.planning_state()['seed']['productionHistory'] if row['id'] == 'void-79')['inventoryStatus'] == 'voided'


def test_col16_old_publication_migration_does_not_invent_an_approver_name(factory):
    with db.connection() as conn:
        conn.execute('ALTER TABLE published_plans DROP COLUMN actor_name')
        conn.execute('ALTER TABLE published_plans DROP COLUMN scenario_name')
        conn.execute('INSERT INTO published_plans VALUES(?,?,?,?,?,?,?,?,?)', ('old-publication', 'torna', 'removed-private-plan', 7, 'historical-admin', '2026-10-20T06:00:00Z', None, 'old-world', '{"seed":{"private":"never expose"}}'))
        conn.execute('INSERT INTO active_plans VALUES(?,?)', ('torna', 'old-publication'))
    original = db.planning_state()
    db.init_database()
    db.init_database()
    approved = collab.collaboration_status()['activePublication']
    assert approved['approvedBy'] == {'id': 'historical-admin', 'name': None}
    assert approved['scenarioName'] is None
    assert approved['approvedAt'] == '2026-10-20T06:00:00Z'
    assert approved['scenarioRevision'] == 7
    assert 'seed' not in approved and 'never expose' not in json.dumps(approved)
    assert db.planning_state() == original


def test_col17_no_publication_has_no_assumed_approver(factory):
    assert collab.collaboration_status()['activePublication'] is None


def test_col18_failed_publication_cannot_change_world_or_approval(factory):
    original = db.planning_state()
    saved = collab.save_scenario({**scenario(factory['seed']), 'worldRevision': original['updatedAt']}, A)
    preview = collab.publication_preview(saved['id'], dict(revision=saved['revision'], worldRevision=original['updatedAt'], previousId=None), A)
    with db.connection() as conn:
        conn.execute("CREATE TRIGGER fail_publication BEFORE INSERT ON published_plans BEGIN SELECT RAISE(ABORT, 'injected publication failure'); END")
    with pytest.raises(Exception, match='injected publication failure'):
        collab.publish_scenario(saved['id'], preview, A)
    assert db.planning_state() == original
    assert collab.collaboration_status()['activePublication'] is None
    with db.connection() as conn:
        assert conn.execute('SELECT COUNT(*) FROM published_plans').fetchone()[0] == 0


def test_draft_lock04_shared_unlock_is_durable_scoped_and_retry_safe(factory):
    from app.planning_delta import state_hash
    seed = copy.deepcopy(factory['seed'])
    seed['manualBatches'] = [dict(id='lock-a', machineId='C-04', product='R902745116', workOrder='LOCK-A', quantity=100,
        start=46266, end=46267, status='planned', planColumn=13, sequence=1, locked=True, diameter='10', setupHours=0),
        dict(id='lock-b', machineId='C-05', product='R902745116', workOrder='LOCK-B', quantity=100,
        start=46266, end=46267, status='planned', planColumn=13, sequence=2, locked=True, diameter='10', setupHours=0)]
    world = db.save_planning_state(seed, db.planning_state()['updatedAt'], mode='operational', can_manage_settings=True,
        flow_settings_version=1, route_placement_version=1, production_split_version=1, process_wait_settings_version=1)
    request = dict(requestId='shared-unlock', expectedBasis=state_hash({**world['seed'], 'chargeJourneyNotes': [], 'planningEvents': []}),
        command=dict(kind='setMachineQueueLock', args=['C-04', None]))
    saved = collab.production_command(request, B)
    expected = copy.deepcopy(world['seed']['manualBatches']); expected[0]['locked'] = False
    assert saved['current']['seed']['manualBatches'] == expected
    assert db.planning_state()['seed']['manualBatches'] == expected
    for field in set(collab.FACTS) - {'planningEvents'}:
        assert saved['current']['seed'].get(field) == world['seed'].get(field)
    assert collab.production_command(request, B)['replayed']
    with pytest.raises(HTTPException) as error:
        collab.production_command({**request, 'requestId': 'stale-unlock'}, B)
    assert error.value.status_code == 409
    before = db.planning_state()
    invalid = dict(requestId='missing-machine', expectedBasis=state_hash({**before['seed'], 'chargeJourneyNotes': [], 'planningEvents': []}),
        command=dict(kind='setMachineQueueLock', args=['MISSING', None]))
    with pytest.raises(HTTPException): collab.production_command(invalid, B)
    assert db.planning_state() == before
    with db.connection() as conn:
        assert conn.execute('SELECT COUNT(*) FROM production_commands').fetchone()[0] == 1


def test_draft_ops04_completion_keeps_private_manual_charge_and_rejects_stale_repeat(factory):
    from app.planning_delta import state_hash
    seed = copy.deepcopy(factory['seed'])
    machine = next(m for m in seed['machines'] if m['id'] == 'C-04')
    machine['currentJob'].update(batchId='actual-100', workOrder='ACTUAL-100', product='R902745116',
        quantity=100, originalQuantity=100, remainingQuantity=100, start=46266, end=46267)
    seed['manualBatches'] = [dict(id='shared-200', machineId='C-04', product='R902745116', workOrder='SHARED-200', quantity=200,
        start=46268, end=46269, status='planned', planColumn=13, sequence=1, locked=False, diameter='10', setupHours=0)]
    world = db.save_planning_state(seed, db.planning_state()['updatedAt'], mode='operational', can_manage_settings=True,
        flow_settings_version=1, route_placement_version=1, production_split_version=1, process_wait_settings_version=1)
    draft_seed = copy.deepcopy(world['seed'])
    draft_seed['manualBatches'] = [{**seed['manualBatches'][0], 'id': 'personal-700', 'workOrder': 'PERSONAL-700', 'quantity': 700}]
    draft = collab.save_scenario(scenario(draft_seed), B)
    before_lots = sum(lot['availableQuantity'] for lot in world['seed'].get('wipLots', []))
    request = dict(requestId='draft-completion', expectedBasis=state_hash({**world['seed'], 'chargeJourneyNotes': [], 'planningEvents': []}),
        command=dict(kind='completeCurrentJob', args=['C-04', 46268, 100]))
    saved = collab.production_command(request, B)
    actual = saved['current']['seed']
    assert next(m for m in actual['machines'] if m['id'] == 'C-04')['currentJob']['batchId'] == 'shared-200'
    assert sum(lot['availableQuantity'] for lot in actual['wipLots']) == before_lots + 100
    assert not any(b['id'] == 'personal-700' for b in actual['manualBatches'])
    assert collab.get_scenario(draft['id'], B) == draft
    assert collab.production_command(request, B)['replayed']
    with pytest.raises(HTTPException) as error:
        collab.production_command({**request, 'requestId': 'duplicate-completion'}, B)
    assert error.value.status_code == 409
    assert collab.get_scenario(draft['id'], B) == draft
