import copy
import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from app import database as db
from app.main import app
from app.planning_delta import apply_delta, build_delta


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'settings', SimpleNamespace(database_path=tmp_path / 'delta.sqlite', upload_dir=tmp_path / 'uploads'))
    db.init_database()


def baseline():
    return db.save_planning_state({'machines': [], 'orders': [],
        'productionHistory': [{'id': 'history-1', 'inventoryStatus': 'semi-finished', 'completedQuantity': 500}],
        'wipMovements': [{'id': 'move-1', 'quantity': 500}],
        'wipLots': [{'id': 'lot-1', 'availableQuantity': 500}]}, can_manage_settings=True)


def patch(record, delta, tx='tx-1', actor='operator-a', **kwargs):
    return db.save_planning_state({}, record['updatedAt'], mode='operational', actor_id=actor,
        can_manage_settings=True, delta=delta, base_hash=record['stateHash'], transaction_id=tx,
        route_placement_version=1, production_split_version=1, process_wait_settings_version=1,
        flow_settings_version=1, **kwargs)


def changes(**fields):
    return {'set': fields, 'remove': [], 'arrays': {}}


def receipt_count():
    with db.connection() as conn:
        return conn.execute('SELECT count(*) FROM planning_write_receipts').fetchone()[0]


def test_delta_changes_only_named_records_and_preserves_exact_order():
    base = {'notes': 'old', 'keep': {'x': 1}, 'rows': [{'id': 'a', 'qty': 3}, {'id': 'b', 'qty': 7}]}
    delta = {'set': {'notes': 'new'}, 'remove': [], 'arrays': {'rows': {
        'upsert': [{'id': 'c', 'qty': 2}, {'id': 'a', 'qty': 8}], 'remove': ['b'], 'order': ['c', 'a']}}}
    expected = {'notes': 'new', 'keep': {'x': 1}, 'rows': [{'id': 'c', 'qty': 2}, {'id': 'a', 'qty': 8}]}
    untouched = copy.deepcopy(base)
    assert apply_delta(base, delta) == expected
    assert base == untouched


@pytest.mark.parametrize('delta', [
    {'set': {'machines': []}, 'remove': ['machines'], 'arrays': {}},
    {'set': {'__proto__': {}}, 'remove': [], 'arrays': {}},
    {'set': {}, 'remove': [], 'arrays': {'wipLots': {'upsert': [], 'remove': ['absent']}}},
    {'set': {}, 'remove': [], 'arrays': {'wipLots': {'upsert': [], 'remove': [], 'order': []}}},
    {'set': {}, 'remove': [], 'arrays': {'wipLots': {'upsert': [{'id': 'x'}, {'id': 'x'}], 'remove': []}}},
])
def test_invalid_delta_is_failure_atomic(delta):
    original = baseline()
    with pytest.raises(ValueError):patch(original, delta)
    assert db.planning_state()['seed'] == original['seed']
    assert db.planning_state()['updatedAt'] == original['updatedAt']
    assert receipt_count() == 0


def test_two_operators_stale_save_conflicts_and_even_force_cannot_rebase_a_delta():
    original = baseline()
    first = patch(original, changes(planningEvents=[{'id': 'a'}]))
    with pytest.raises(db.PlanningStateConflict):patch(original, changes(planningEvents=[{'id': 'b'}]), actor='operator-b', force=True)
    assert db.planning_state()['updatedAt'] == first['updatedAt']
    assert receipt_count() == 1


def test_wrong_base_hash_rejects_even_when_revision_matches():
    original = baseline()
    with pytest.raises(db.PlanningStateConflict):patch({**original, 'stateHash': '0' * 64}, changes(note='wrong base'))
    assert db.planning_state()['updatedAt'] == original['updatedAt']


def test_lost_response_retry_after_later_writes_does_not_repeat_output_or_recreate_history():
    original = baseline()
    delta = {'set': {}, 'remove': [], 'arrays': {'wipMovements': {
        'upsert': [{'id': 'delivery-1', 'quantity': 200}], 'remove': []}}}
    saved = patch(original, delta)
    later = patch(saved, changes(note='later valid work'), tx='tx-later', actor='operator-b')
    with db.connection() as conn:
        before_history = conn.execute('SELECT count(*) FROM planning_state_history').fetchone()[0]
    replay = patch(original, delta)
    assert replay['replayed'] is True
    assert replay['appliedRevision'] == saved['updatedAt']
    assert replay['updatedAt'] == later['updatedAt']
    assert replay['seed']['note'] == 'later valid work'
    assert [r['id'] for r in replay['seed']['wipMovements']] == ['move-1', 'delivery-1']
    assert receipt_count() == 2
    with db.connection() as conn:
        assert conn.execute('SELECT count(*) FROM planning_state_history').fetchone()[0] == before_history
        receipts = '\n'.join(str(tuple(r)) for r in conn.execute('SELECT * FROM planning_write_receipts'))
    assert 'delivery-1' not in receipts and 'later valid work' not in receipts


def test_same_id_with_different_data_is_rejected_and_receipt_is_scoped_to_actor():
    original = baseline()
    saved = patch(original, changes(note='first'))
    with pytest.raises(ValueError):patch(original, changes(note='other payload'))
    other = patch(saved, changes(note='other operator'), actor='operator-b')
    assert other['replayed'] is False and receipt_count() == 2


@pytest.mark.parametrize('boundary', ['_insert_planning_receipt', '_insert_planning_audit'])
def test_receipt_or_audit_failure_rolls_back_state_history_and_receipt(boundary, monkeypatch):
    original = baseline()
    def fail(*args):raise RuntimeError('storage failure')
    monkeypatch.setattr(db, boundary, fail)
    with pytest.raises(RuntimeError):patch(original, changes(note='must not commit'))
    assert db.planning_state()['updatedAt'] == original['updatedAt']
    assert receipt_count() == 0
    with db.connection() as conn:
        assert conn.execute('SELECT count(*) FROM planning_state_history').fetchone()[0] == 1


def test_ordinary_user_cannot_change_protected_settings_through_delta():
    original = baseline()
    with pytest.raises(db.ProtectedSettingsChange):
        db.save_planning_state({}, original['updatedAt'], actor_id='user', delta=changes(holidays=['2026-10-22']),
            base_hash=original['stateHash'], transaction_id='forged-settings')
    assert db.planning_state()['updatedAt'] == original['updatedAt']


def test_authenticated_patch_uses_server_actor_and_retries_exactly_once():
    from app.auth import create_test_session
    original = baseline()
    headers={'Authorization': f"Bearer {create_test_session('test-password', 'admin')}"}
    payload={'version': 1, 'transactionId': 'http-id', 'expectedUpdatedAt': original['updatedAt'],
             'baseHash': original['stateHash'], 'mode': 'operational', 'delta': changes(note='http save')}
    client=TestClient(app)
    response=client.patch('/api/planning-state',json=payload,headers=headers)
    assert response.status_code==200,response.text
    replay=client.patch('/api/planning-state',json=payload,headers=headers)
    assert replay.status_code==200 and replay.json()['replayed'] is True
    assert replay.json()['updatedAt']==response.json()['updatedAt']
    assert client.patch('/api/planning-state',json={**payload,'actor_id':'forged'},headers=headers).status_code==422
    assert client.patch('/api/planning-state',json=payload).status_code==401


def test_receipt_check_is_read_only_and_scoped_to_authenticated_actor():
    from app.auth import create_test_session
    original=baseline()
    headers={'Authorization':f"Bearer {create_test_session('test-password','admin')}"}
    client=TestClient(app)
    payload={'version':1,'transactionId':'read-receipt','expectedUpdatedAt':original['updatedAt'],
             'baseHash':original['stateHash'],'mode':'operational','delta':changes(note='first')}
    first=client.patch('/api/planning-state',json=payload,headers=headers).json()
    later=patch(db.planning_state(),changes(note='later'),tx='later',actor='another-operator')
    with db.connection() as conn:
        audit_count=conn.execute('SELECT count(*) FROM planning_write_audit').fetchone()[0]
    status=client.get('/api/planning-state/transactions/read-receipt',headers=headers)
    assert status.status_code==200
    assert status.json()['committed'] is True
    assert status.json()['appliedRevision']==first['updatedAt']
    assert status.json()['current']['updatedAt']==later['updatedAt']
    assert db.planning_transaction_status('another-operator','read-receipt')['committed'] is False
    assert client.get('/api/planning-state/transactions/read-receipt').status_code==401
    with db.connection() as conn:
        assert conn.execute('SELECT count(*) FROM planning_write_audit').fetchone()[0]==audit_count
    assert db.planning_state()['updatedAt']==later['updatedAt']


def test_simultaneous_retries_commit_exactly_once_and_competing_actor_conflicts():
    from concurrent.futures import ThreadPoolExecutor
    original=baseline()
    delta=changes(note='one operation')
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:patch(original,delta),range(2)))
    assert sorted(result['replayed'] for result in results)==[False,True]
    assert len({result['appliedRevision'] for result in results})==1
    assert receipt_count()==1
    with db.connection() as conn:
        assert conn.execute('SELECT count(*) FROM planning_state_history').fetchone()[0]==2
    next_base=db.planning_state()
    def competing(actor):
        try:return patch(next_base,changes(note=actor),tx=actor,actor=actor)
        except db.PlanningStateConflict:return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(competing,['a','b']))
    assert sum(result is not None for result in results)==1
    assert receipt_count()==2


def test_bootstrap_and_retry_stay_duplicate_safe_after_history_retention():
    empty={'seed':{},'updatedAt':'','stateHash':''}
    delta=changes(machines=[],orders=[],productionHistory=[{'id':'once','completedQuantity':79}])
    original=patch(empty,delta)
    current=original
    for i in range(25):current=patch(current,changes(note=str(i)),tx=f'next-{i}')
    assert len(db.planning_state_history())==20
    replay=patch(empty,delta)
    assert replay['appliedRevision']==original['updatedAt']
    assert replay['updatedAt']==current['updatedAt']
    assert replay['seed']['productionHistory']==[{'id':'once','completedQuantity':79}]
    assert receipt_count()==26


def test_large_factory_delivery_update_and_ack_are_small_and_preserve_all_other_data():
    from app.auth import create_test_session
    source={'machines':[],'orders':[],
        'productionHistory':[{'id':f'history-{i}','note':'ş'*400,'deliveredQuantity':0} for i in range(2000)],
        'wipLots':[{'id':'voided-79','inventoryStatus':'void','originalQuantity':79,'availableQuantity':0}],
        'wipMovements':[{'id':'void','lotId':'voided-79','quantity':-79}],
        'customerDemand':{'retained':'x'*200000}}
    original=db.save_planning_state(source,can_manage_settings=True)
    desired=copy.deepcopy(original['seed'])
    desired['productionHistory'][-1]['deliveredQuantity']=12
    delta=build_delta(original['seed'],desired)
    payload={'version':1,'transactionId':'delivery-once','expectedUpdatedAt':original['updatedAt'],
             'baseHash':original['stateHash'],'mode':'operational','delta':delta}
    headers={'Authorization':f"Bearer {create_test_session('test-password','user')}"}
    assert len(json.dumps(source,ensure_ascii=False).encode())>1024*1024
    assert len(json.dumps(payload,ensure_ascii=False).encode())<3000
    # Physical record deltas are retired, even when their transport is small.
    # COL04-COL06 verify small delivery intents through the authoritative writer.
    response=TestClient(app).patch('/api/planning-state',json=payload,headers=headers)
    assert response.status_code == 403
    assert db.planning_state()['seed'] == original['seed']
    assert receipt_count() == 0

def test_server_corrections_reconstruct_validated_state_without_full_snapshot():
    original=baseline()
    # Planning publication cannot publish a local physical output over server operations.
    desired=copy.deepcopy(original['seed'])
    desired['productionHistory']=[]
    desired['wipLots']=[]
    delta=build_delta(original['seed'],desired)
    saved=db.save_planning_state({},original['updatedAt'],mode='planning',actor_id='planner',
        can_manage_settings=True,delta=delta,base_hash=original['stateHash'],transaction_id='correction')
    assert saved['seed']['productionHistory']==original['seed']['productionHistory']
    assert saved['seed']['wipLots']==original['seed']['wipLots']
    assert apply_delta(desired,saved['correction'])==saved['seed']
