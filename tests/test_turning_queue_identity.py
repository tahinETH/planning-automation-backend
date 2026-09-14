import copy
from types import SimpleNamespace
import pytest
from app import database
from app.turning_queue_identity import reconcile_turning_seed


def fixture(legacy=False):
    job = dict(batchId=None if legacy else 'active', product='R902745116', workOrder='WO-A', quantity=2000, originalQuantity=2000, remainingQuantity=1500)
    batch = dict(id='active', machineId='C-05', product=job['product'], workOrder='WO-A', quantity=2000, locked=True, start=46277, end=46282)
    return dict(machines=[dict(id='C-05', currentJob=job)], productionHistory=[], manualBatches=[batch], orders=[dict(id='order', dueDate='2026-09-12')])


@pytest.mark.parametrize('legacy', [False, True])
def test_planning_merge_removes_promoted_charge_keeps_distinct_work_order_and_marks_stale(legacy):
    live = fixture(legacy); live['manualBatches'] = []
    incoming = fixture(legacy); incoming['machines'][0]['currentJob']['workOrder'] = 'OLD'
    later = dict(incoming['manualBatches'][0], id='later', workOrder='WO-B')
    incoming['manualBatches'].append(later)
    before = copy.deepcopy((incoming, live))
    result = database.preserve_live_operations(incoming, live)
    assert result['manualBatches'] == [later]
    assert result['machines'] == live['machines']
    assert result['planNeedsRecalculation'] is True
    assert (incoming, live) == before
    assert reconcile_turning_seed(result) == result


def test_completed_charge_cannot_return_but_partial_output_keeps_its_remainder():
    seed = fixture(); seed['machines'] = []
    seed['productionHistory'] = [dict(id='archive', sourceBatchId='active', product='R902745116', process='turning')]
    assert reconcile_turning_seed(seed)['manualBatches'] == []
    seed['productionHistory'] = [dict(id='partial', workOrder='WO-A', product='R902745116', originalQuantity=200, interruptionIds=['pause'], process='turning')]
    seed['manualBatches'][0].update(quantity=400, interruptionId='pause')
    assert reconcile_turning_seed(seed)['manualBatches'][0]['quantity'] == 400


@pytest.mark.parametrize('force', [False, True])
def test_save_rejects_ambiguous_legacy_atomically_even_when_forced(tmp_path, monkeypatch, force):
    monkeypatch.setattr(database, 'settings', SimpleNamespace(database_path=tmp_path/'test.sqlite', upload_dir=tmp_path/'uploads'))
    database.init_database()
    live=fixture(True);live['manualBatches']=[]
    saved=database.save_planning_state(live, expected_updated_at='', mode='operational')
    history=database.planning_state_history()
    incoming=fixture(True);incoming['manualBatches'][0]['quantity']=1000
    incoming['orders'][0]['dueDate']='2026-10-03'
    with pytest.raises(ValueError, match='kimliği belirsiz'):
        database.save_planning_state(incoming, expected_updated_at=saved['updatedAt'], force=force)
    assert database.planning_state()['seed']==live
    assert database.order_details()[0]['dueDate']=='2026-09-12'
    assert database.planning_state_history()==history


def test_two_sessions_completion_then_forced_stale_plan_and_reload(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'settings', SimpleNamespace(database_path=tmp_path/'test.sqlite', upload_dir=tmp_path/'uploads'))
    database.init_database()
    stale=fixture();stale['machines'][0]['currentJob']['batchId']='previous';stale['machines'][0]['currentJob']['workOrder']='WO-OLD'
    first=database.save_planning_state(stale, expected_updated_at='', mode='operational')
    completed=fixture();completed['manualBatches']=[]
    database.save_planning_state(completed, expected_updated_at=first['updatedAt'], mode='operational')
    with pytest.raises(database.PlanningStateConflict):
        database.save_planning_state(stale, expected_updated_at=first['updatedAt'])
    merged=database.save_planning_state(stale, expected_updated_at=first['updatedAt'], force=True)
    assert merged['seed']['manualBatches']==[]
    assert merged['seed']['machines']==completed['machines']
    assert database.planning_state()['seed']==merged['seed']
    with pytest.raises(ValueError, match='tekrar bulunuyor'):
        database.save_planning_state(fixture(), expected_updated_at=merged['updatedAt'], mode='operational', force=True)
    assert database.planning_state()['updatedAt']==merged['updatedAt']


def test_multiple_legacy_candidates_are_not_silently_deleted():
    seed=fixture(True);seed['manualBatches'].append(dict(seed['manualBatches'][0], id='other'))
    before=copy.deepcopy(seed)
    with pytest.raises(ValueError, match='kimliği belirsiz'):
        reconcile_turning_seed(seed)
    assert seed==before


def test_forced_operational_write_still_requires_current_version(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'settings', SimpleNamespace(database_path=tmp_path/'test.sqlite', upload_dir=tmp_path/'uploads'))
    database.init_database()
    live=fixture();live['manualBatches']=[]
    saved=database.save_planning_state(live, expected_updated_at='', mode='operational')
    with pytest.raises(database.PlanningStateConflict):
        database.save_planning_state(live, expected_updated_at='older', mode='operational', force=True)
    with pytest.raises(ValueError, match='güncel ortak sürüm'):
        database.save_planning_state(live, mode='operational', force=True)
    assert database.planning_state()['updatedAt']==saved['updatedAt']


def test_stale_full_charge_is_replaced_with_only_live_interrupted_remainder():
    seed=fixture();seed['machines']=[]
    remainder=dict(seed['manualBatches'][0], quantity=400, interruptionId='pause')
    seed['productionInterruptions']=[dict(id='pause',chargeId='active',process='turning',remainingQuantity=400,producedQuantity=200,turningBatch=remainder)]
    result=reconcile_turning_seed(seed)
    assert result['manualBatches']==[remainder]
    assert 200+result['manualBatches'][0]['quantity']==600
    result['productionInterruptions'][0]['completedAt']=46283
    assert reconcile_turning_seed(result)['manualBatches']==[]


def test_voided_completion_is_not_live_production_and_does_not_block_its_work_order():
    seed=fixture();seed['machines']=[]
    seed['productionHistory']=[dict(id='voided',sourceBatchId='active',product='R902745116',workOrder='WO-A',machineId='C-08',originalQuantity=2000,inventoryStatus='voided')]
    seed['wipLots']=[dict(id='void-lot',sourceBatchId='active',sourceHistoryEntryId='voided',product='R902745116')]
    assert reconcile_turning_seed(seed)==seed


def test_omitting_a_live_machine_cannot_evade_queue_identity_protection():
    live=fixture();live['manualBatches']=[]
    incoming=fixture();incoming['machines']=[]
    saved=database.preserve_live_operations(incoming,live)
    assert saved['machines']==live['machines']
    assert saved['manualBatches']==[]
