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


from app.turning_queue_identity import inspect_turning_queue, turning_identity_scope, assert_turning_identity_transition, repair_turning_identity


def conflict_fixture():
    seed = fixture()
    seed['machines'][0]['currentJob'].update(batchId='other-current', product='OTHER', workOrder='OTHER-WO')
    seed['manualBatches'][0].update(id='ambiguous', quantity=1000)
    seed['productionHistory'] = [dict(id='legacy', product='R902745116', workOrder='WO-A', originalQuantity=2000, machineId='C-99', process='turning', inventoryStatus='semi-finished')]
    seed['wipLots'] = [dict(id='root', sourceHistoryEntryId='legacy', product='R902745116', workOrder='WO-A', availableQuantity=2000, completedSteps=[], readyAt=46000)]
    seed['wipMovements'], seed['processCurrentJobs'], seed['processOperationOverrides'] = [], [], []
    return seed


def test_identity_inspection_follows_descendants_with_inconsistent_product_labels():
    seed = conflict_fixture()
    seed['wipLots'].append(dict(id='child', parentLotId='root', sourceHistoryEntryId='other-history', sourceBatchId='linked-charge', product='WRONG-LABEL'))
    seed['processCurrentJobs'].append(dict(batchId='linked-charge', wipLotId='child', product='WRONG-LABEL'))
    before = copy.deepcopy(seed)
    inspected, scope = inspect_turning_queue(seed), turning_identity_scope(seed)
    assert inspected['conflicts'][0]['reason'] == 'legacy-ambiguous'
    assert inspected['conflicts'][0]['records'][0]['id'] == 'legacy'
    assert 'child' in scope['lotIds'] and 'linked-charge' in scope['batchIds'] and 'other-history' in scope['historyIds']
    assert seed == before
    changed = copy.deepcopy(seed); changed['wipLots'][1]['availableQuantity'] = 1
    with pytest.raises(ValueError, match='İncele ve düzelt'):
        assert_turning_identity_transition(seed, changed)


def test_unrelated_operational_records_may_change_while_conflict_scope_is_unchanged():
    seed = conflict_fixture(); changed = copy.deepcopy(seed)
    changed['productionHistory'].append(dict(id='unrelated', product='OTHER-PRODUCT', workOrder='OTHER-WO', completedQuantity=200))
    changed['wipLots'].append(dict(id='unrelated-lot', sourceHistoryEntryId='unrelated', product='OTHER-PRODUCT', availableQuantity=200))
    changed['orders'].append(dict(id='other-order', product='OTHER-PRODUCT', quantity=200, dueDate='2026-09-30'))
    assert_turning_identity_transition(seed, changed)
    assert changed['manualBatches'] == seed['manualBatches']
    assert changed['machines'] == seed['machines']


@pytest.mark.parametrize('edit', ['void', 'unlock', 'quantity', 'readyAt', 'route', 'remove', 'complete', 'calendar'])
def test_ordinary_operations_cannot_erase_or_change_conflict_evidence(edit):
    seed = conflict_fixture(); changed = copy.deepcopy(seed)
    if edit == 'void': changed['productionHistory'][0]['inventoryStatus'] = 'voided'
    if edit == 'unlock': changed['manualBatches'][0]['locked'] = False
    if edit == 'quantity': changed['manualBatches'][0]['quantity'] = 600
    if edit == 'readyAt': changed['wipLots'][0]['readyAt'] += 1
    if edit == 'route': changed['processOperationOverrides'] = [dict(batchId='root', process='gkm', resourceId='G-01')]
    if edit == 'remove': changed['manualBatches'] = []
    if edit == 'complete': changed['machines'][0]['currentJob']['quantity'] = 0
    if edit == 'calendar': changed['calendarEvents'] = [dict(id='holiday', start=46000, end=46001)]
    with pytest.raises(ValueError, match='İncele ve düzelt'):
        assert_turning_identity_transition(seed, changed)


def test_new_conflict_or_exact_duplicate_cannot_enter_an_unrelated_scope():
    seed = conflict_fixture(); changed = copy.deepcopy(seed)
    unrelated = dict(seed['manualBatches'][0], id='new', machineId='C-88', product='OTHER-PRODUCT', workOrder='OTHER-WO')
    changed['manualBatches'].extend([unrelated, dict(unrelated, product='OTHER-PRODUCT-2')])
    with pytest.raises(ValueError, match='yeni bir'):
        assert_turning_identity_transition(seed, changed)
    assert len([c for c in inspect_turning_queue(changed)['conflicts'] if c['reason'] == 'duplicate-queue-id']) == 2
    with pytest.raises(ValueError, match='tek bir'):
        repair_turning_identity(changed, dict(batchId='new', action='work-order', workOrder='FIXED', reason='Reviewed'))
    duplicate = copy.deepcopy(seed)
    duplicate['manualBatches'].append(unrelated)
    duplicate['productionHistory'].append(dict(id='known', sourceBatchId='new', product=unrelated['product']))
    with pytest.raises(ValueError, match='tekrar bulunuyor'):
        assert_turning_identity_transition(seed, duplicate)


def test_reviewed_work_order_repair_preserves_quantity_locks_and_another_conflict():
    seed = conflict_fixture()
    seed['manualBatches'].append(dict(seed['manualBatches'][0], id='second', product='SECOND', workOrder='SECOND-WO', machineId='C-88'))
    seed['productionHistory'].append(dict(id='second-history', product='SECOND', workOrder='SECOND-WO', originalQuantity=2000, machineId='C-89'))
    before = copy.deepcopy(seed)
    repaired = repair_turning_identity(seed, dict(batchId='ambiguous', action='work-order', workOrder='VERIFIED-NEW', reason='Original ticket checked'))
    assert repaired['manualBatches'][0]['workOrder'] == 'VERIFIED-NEW'
    assert inspect_turning_queue(repaired)['conflicts'][0]['batchId'] == 'second'
    assert dict(repaired['manualBatches'][0], workOrder=seed['manualBatches'][0]['workOrder']) == seed['manualBatches'][0]
    assert repaired['productionHistory'] == seed['productionHistory'] and repaired['wipLots'] == seed['wipLots']
    assert seed == before
    with pytest.raises(ValueError, match='İncele ve düzelt'):
        assert_turning_identity_transition(seed, repaired)


def test_duplicate_removal_requires_explicit_confirmation_even_for_locked_rows_and_keeps_physical_records():
    seed = conflict_fixture()
    request = dict(batchId='ambiguous', action='remove-duplicate', reason='Compared the original ticket')
    with pytest.raises(ValueError, match='doğrulayın'):
        repair_turning_identity(seed, request)
    result = repair_turning_identity(seed, dict(request, confirmedDuplicate=True))
    assert result['manualBatches'] == []
    assert result['productionHistory'] == seed['productionHistory'] and result['wipLots'] == seed['wipLots']
    assert seed['manualBatches'][0]['locked'] is True


def test_repair_rejects_no_op_blank_reason_and_referenced_rows_without_mutation():
    seed = conflict_fixture()
    request = dict(batchId='ambiguous', action='work-order', workOrder='NEW', reason='Verified')
    with pytest.raises(ValueError, match='neden'):
        repair_turning_identity(seed, dict(request, reason=' '))
    with pytest.raises(ValueError, match='Farklı'):
        repair_turning_identity(seed, dict(request, workOrder='WO-A'))
    seed['processOperationOverrides'] = [dict(batchId='ambiguous')]
    before = copy.deepcopy(seed)
    with pytest.raises(ValueError, match='bağlı'):
        repair_turning_identity(seed, request)
    assert seed == before


def test_unrelated_interruption_recovery_remains_mandatory_while_another_conflict_exists():
    seed = conflict_fixture()
    remainder = dict(seed['manualBatches'][0], id='remainder', product='OTHER', workOrder='OTHER-WO', machineId='C-88', quantity=400, interruptionId='pause')
    seed['manualBatches'].append(remainder)
    seed['productionInterruptions'] = [dict(id='pause', chargeId='remainder', process='turning', resourceId='C-88', product='OTHER', workOrder='OTHER-WO', producedQuantity=200, remainingQuantity=400, turningBatch=remainder)]
    changed = copy.deepcopy(seed); changed['manualBatches'] = [b for b in changed['manualBatches'] if b['id'] != 'remainder']
    with pytest.raises(ValueError, match='Yarım kalan'):
        assert_turning_identity_transition(seed, changed)
