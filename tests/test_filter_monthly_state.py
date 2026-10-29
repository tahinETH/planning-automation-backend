"""Independent saved-state tests for monthly source quantities and safe saves."""
from copy import deepcopy
import pytest

from app.stock_planning import validate_stock_planning, uses_stock_planning

C100 = 'F.00V.C15.100'
DRS002 = 'F.00V.C15.002'
P081 = '2.433.084.081'


def source(label, quantity, row):
    return {'label': label, 'quantities': [quantity] * 12, 'sourceRow': row}


def monthly_seed():
    data = {'format': 'filter-monthly', 'fileName': 'synthetic.xlsx', 'sheetName': 'SİPARİŞ', 'year': 2026,
            'workingDays': [26] * 11 + [26.5], 'startDate': '2026-10-19', 'endDate': '2026-10-31',
            'snapshotDate': '2026-10-18', 'importedAt': '2026-10-19T09:00:00Z',
            'handovers': [{'product': product, 'month': '2026-10', 'quantity': 0} for product in [C100, DRS002, P081]], 'exceptions': [],
            'rows': [
                {'label': 'C100 - DRS', 'product': C100, 'kind': 'internal', 'sourceRow': 23,
                 'rule': 'ceil(sum × 103/100 ÷ 15000) × 15000', 'quantities': [30000] * 12,
                 'inputs': [source('501-RBTR', 10000, 10), source('003-RBCD', 5000, 13)]},
                {'label': '002 - DRS', 'product': DRS002, 'kind': 'internal', 'sourceRow': 24,
                 'rule': 'ceil(sum × 104/100 ÷ 1000) × 1000', 'quantities': [7000] * 12,
                 'inputs': [source('001-RBCD', 2000, 14), source('001-NaP', 2000, 15), source('001-CtP', 2000, 16)]},
                {'label': '081 - DRS', 'product': P081, 'kind': 'internal', 'sourceRow': 25,
                 'rule': 'ceil(sum × 104/100 ÷ 1000) × 1100', 'quantities': [11000] * 12,
                 'inputs': [source('481-HoP', 3000, 11), source('481-CtP/NaP', 3000, 12), source('424-HoP/CtP', 3000, 17)]},
            ]}
    return {'productionArea': 'cubuk-filtre', 'orders': [], 'machines': [],
            'products': [{'product': product, 'setupFamily': 'cubuk-filtre'} for product in [C100, DRS002, P081]],
            'monthlyCustomerDemand': data,
            'orderImport': {'id': 'monthly-synthetic', 'sourceFile': 'synthetic.xlsx', 'importedAt': data['importedAt'],
                            'shipmentsThrough': '2026-10-18T20:59:59.999Z'}}


def test_cf_ms01_valid_monthly_source_is_recognized_without_mutation():
    seed = monthly_seed()
    before = deepcopy(seed)
    validate_stock_planning(seed)
    assert uses_stock_planning(seed)
    assert seed == before


@pytest.mark.parametrize('field,value', [
    ('format', 'filter-daily'), ('year', True), ('year', 1999), ('year', 2101),
    ('workingDays', [26] * 11), ('workingDays', [26.25] * 12), ('workingDays', [float('nan')] * 12),
    ('startDate', '2026-02-30'), ('startDate', '2026-11-01'), ('startDate', '2025-10-19'),
    ('endDate', '2027-01-01'), ('snapshotDate', '2026-10-20'),
    ('importedAt', 'invalid'), ('importedAt', '2026-10-19T09:00:00'),
    ('rows', []), ('rows', [None]), ('handovers', [None]), ('exceptions', [None]),
])
def test_cf_ms02_invalid_monthly_structure_rejects(field, value):
    seed = monthly_seed()
    seed['monthlyCustomerDemand'][field] = value
    with pytest.raises(ValueError):
        validate_stock_planning(seed)


@pytest.mark.parametrize('row_index,forged', [(0, 15000), (1, 0), (2, 10000)])
def test_cf_ms03_derived_results_must_match_source_inputs(row_index, forged):
    seed = monthly_seed()
    seed['monthlyCustomerDemand']['rows'][row_index]['quantities'][9] = forged
    with pytest.raises(ValueError):
        validate_stock_planning(seed)


@pytest.mark.parametrize('mutation', [
    lambda row: row.update(inputs=[]),
    lambda row: row['inputs'].pop(),
    lambda row: row['inputs'].append(deepcopy(row['inputs'][0])),
    lambda row: row['inputs'][0].update(label='UNKNOWN'),
    lambda row: row['inputs'][0].update(quantities=[-1] * 12),
    lambda row: row['inputs'][0].update(quantities=[None] * 12),
    lambda row: row['inputs'][0].update(quantities=[9007199254740992] * 12),
    lambda row: row.update(quantities=[True] * 12),
    lambda row: row.update(product='UNKNOWN'),
])
def test_cf_ms04_source_provenance_cannot_be_missing_or_forged(mutation):
    seed = monthly_seed()
    mutation(seed['monthlyCustomerDemand']['rows'][0])
    with pytest.raises(ValueError):
        validate_stock_planning(seed)


@pytest.mark.parametrize('field,value', [
    ('shipmentsThrough', '2026-10-19T10:00:00Z'),
    ('shipmentsThrough', '2026-10-18T20:59:59.999'),
    ('shipmentsThrough', 'invalid'),
    ('importedAt', '2026-10-19T10:00:00Z'),
])
def test_cf_ms05_import_cutoff_metadata_must_match_the_saved_source(field, value):
    seed = monthly_seed()
    seed['orderImport'][field] = value
    with pytest.raises(ValueError):
        validate_stock_planning(seed)


def test_cf_ms06_daily_and_monthly_sources_cannot_both_be_active():
    seed = monthly_seed()
    seed['dailyCustomerDemand'] = {'format': 'filter-daily', 'fileName': 'daily.xlsx', 'sheetName': 'Sevkiyat Planı',
        'snapshotDate': '2026-10-18', 'endDate': '2026-10-31', 'importedAt': '2026-10-19T09:00:00Z', 'dailyRows': []}
    with pytest.raises(ValueError):
        validate_stock_planning(seed)


def test_cf_ms07_monthly_source_is_rejected_in_piston_area():
    seed = monthly_seed()
    seed['productionArea'] = 'torna'
    with pytest.raises(ValueError):
        validate_stock_planning(seed)


def test_cf_ms08_duplicate_monthly_product_rejects():
    seed = monthly_seed()
    seed['monthlyCustomerDemand']['rows'].append(deepcopy(seed['monthlyCustomerDemand']['rows'][0]))
    with pytest.raises(ValueError):
        validate_stock_planning(seed)


def test_cf_ms09_old_client_cannot_drop_monthly_source_even_with_force(tmp_path, monkeypatch):
    from app import database
    from app.config import settings
    from app.production_area import production_area
    monkeypatch.setitem(settings.__dict__, 'database_path', tmp_path / 'monthly.sqlite')
    token = production_area.set('cubuk-filtre')
    try:
        database.init_database()
        saved = database.save_planning_state(monthly_seed(), can_manage_settings=True, stock_planning_version=1, monthly_planning_version=1)
        snapshot = deepcopy(database.planning_state())
        old = deepcopy(saved['seed'])
        del old['monthlyCustomerDemand']
        with pytest.raises(ValueError, match='yenileyin'):
            database.save_planning_state(old, saved['updatedAt'], force=True, can_manage_settings=True, stock_planning_version=1)
        assert database.planning_state() == snapshot
        forged = deepcopy(saved['seed'])
        forged['monthlyCustomerDemand']['rows'][0]['quantities'][9] = 0
        with pytest.raises(ValueError):
            database.save_planning_state(forged, saved['updatedAt'], can_manage_settings=True, stock_planning_version=1, monthly_planning_version=1)
        assert database.planning_state() == snapshot
        second = database.save_planning_state(saved['seed'], saved['updatedAt'], can_manage_settings=True, stock_planning_version=1, monthly_planning_version=1)
        assert second['seed'] == saved['seed']
    finally:
        production_area.reset(token)


def test_cf_ms10_request_model_requires_explicit_monthly_client_version():
    from app.models import PlanningStatePayload
    assert PlanningStatePayload(seed=monthly_seed()).monthlyPlanningVersion == 0
    assert PlanningStatePayload(seed=monthly_seed(), monthlyPlanningVersion=1).monthlyPlanningVersion == 1


def test_cf_ms11_selected_current_month_requires_explicit_handover_confirmation():
    seed = monthly_seed()
    seed['monthlyCustomerDemand']['handovers'].pop()
    with pytest.raises(ValueError):
        validate_stock_planning(seed)


def test_cf_ms12_corrected_delivery_preserves_original_source_count():
    seed = monthly_seed()
    seed['monthlyCustomerDemand']['openingStock'] = {'cutoffDate': '2026-10-18', 'rows': [
        {'product': C100, 'delivered': 123, 'visual': None, 'heat': None, 'milling': None, 'grinding': None}]}
    before=deepcopy(seed)
    validate_stock_planning(seed)
    assert seed==before


def test_cf_ms13_absent_stock_field_is_not_an_explicit_blank():
    seed = monthly_seed()
    seed['monthlyCustomerDemand']['openingStock'] = {'cutoffDate': '2026-10-18', 'rows': [
        {'product': C100, 'delivered': 0, 'visual': None, 'heat': None, 'milling': None}]}
    with pytest.raises(ValueError):
        validate_stock_planning(seed)


@pytest.mark.parametrize('collection', ['rows', 'handovers'])
def test_cf_ms14_unhashable_product_value_rejects_with_controlled_validation(collection):
    seed = monthly_seed()
    seed['monthlyCustomerDemand'][collection][0]['product'] = []
    with pytest.raises(ValueError):
        validate_stock_planning(seed)


def test_cf_ms15_legacy_client_cannot_drop_quality_calendar_without_monthly_source(tmp_path, monkeypatch):
    from app import database
    from app.config import settings
    from app.production_area import production_area
    monkeypatch.setitem(settings.__dict__, 'database_path', tmp_path / 'quality.sqlite')
    token = production_area.set('cubuk-filtre')
    try:
        database.init_database()
        seed = monthly_seed()
        del seed['monthlyCustomerDemand']
        seed['filterQualityShifts'] = 3
        saved = database.save_planning_state(seed, can_manage_settings=True, stock_planning_version=1, monthly_planning_version=1)
        snapshot = deepcopy(database.planning_state())
        legacy = deepcopy(saved['seed'])
        del legacy['filterQualityShifts']
        with pytest.raises(ValueError, match='yenileyin'):
            database.save_planning_state(legacy, saved['updatedAt'], force=True, can_manage_settings=True, stock_planning_version=1)
        assert database.planning_state() == snapshot
    finally:
        production_area.reset(token)


def reconciled_seed():
    seed = monthly_seed()
    seed['monthlyCustomerDemand']['openingStock'] = {'cutoffDate': '2026-10-18', 'rows': [
        {'product': C100, 'delivered': 0, 'visual': None, 'heat': 200, 'milling': 300, 'grinding': 400}]}
    # Exact serialized source evidence. Null remains distinct from reviewed zero.
    seed['monthlyCustomerDemand']['stockReconciliation'] = {
        'cutoffDate': '2026-10-18',
        'sourceKey': '["2026-10-18",[["F.00V.C15.100",null,200,300,400]]]',
        'recordedAt': '2026-10-19T10:00:00Z',
        'rows': [{'product': C100, 'visual': 50, 'heat': 200, 'milling': 300, 'grinding': 400}]}
    return seed


def test_cf_ms16_reviewed_stock_accepts_explicit_blank_resolution_without_mutation():
    seed = reconciled_seed()
    before = deepcopy(seed)
    validate_stock_planning(seed)
    assert seed == before


@pytest.mark.parametrize('mutation', [
    lambda data: data.pop('openingStock'),
    lambda data: data['stockReconciliation'].update(cutoffDate='2026-10-17'),
    lambda data: data['stockReconciliation'].update(sourceKey='forged'),
    lambda data: data['stockReconciliation'].update(recordedAt='2026-10-19T10:00:00'),
    lambda data: data['stockReconciliation'].update(rows=[]),
    lambda data: data['stockReconciliation']['rows'][0].update(product='UNKNOWN'),
    lambda data: data['stockReconciliation']['rows'][0].update(visual=None),
    lambda data: data['stockReconciliation']['rows'][0].update(visual=-1),
    lambda data: data['stockReconciliation']['rows'][0].update(visual=True),
    lambda data: data['stockReconciliation']['rows'][0].update(visual=9007199254740991),
    lambda data: data['openingStock']['rows'][0].update(grinding=401),
])
def test_cf_ms17_invalid_stock_review_or_changed_source_rejects_without_mutation(mutation):
    seed = reconciled_seed()
    mutation(seed['monthlyCustomerDemand'])
    before = deepcopy(seed)
    with pytest.raises(ValueError):
        validate_stock_planning(seed)
    assert seed == before


def test_cf_ms18_ravi_monthly_inspection_is_bounded_filtered_and_reads_saved_values():
    from app.ravi.tools import Inspect, inspect_state
    seed = reconciled_seed()
    prototype = deepcopy(seed['monthlyCustomerDemand']['rows'][0])
    seed['monthlyCustomerDemand']['rows'] = []
    for number in range(55):
        row = deepcopy(prototype)
        row['label'] = f'TARGET {number}'
        row['quantities'] = [777 + number] * 12
        seed['monthlyCustomerDemand']['rows'].append(row)
    seed['monthlyCustomerDemand']['rows'].append({**deepcopy(prototype), 'label': 'OTHER', 'product': DRS002})
    snapshot = {'seed': seed, 'updatedAt': '2026-10-19T11:00:00Z'}
    before = deepcopy(snapshot)
    result = inspect_state(snapshot, Inspect(collection='monthly_demand', query='TARGET', offset=20))
    assert result['source'] == 'persisted-server'
    assert result['updatedAt'] == snapshot['updatedAt']
    assert result['productionArea'] == 'cubuk-filtre'
    assert result['total'] == 55
    assert len(result['rows']) == 12
    assert result['nextOffset'] == 32
    assert result['rows'][0]['quantities'] == [797] * 12
    assert result['rows'][0]['inputs'][0]['quantities'] == [10000] * 12
    assert result['userSource']['fileName'] == 'synthetic.xlsx'
    assert result['userSource']['snapshotDate'] == '2026-10-18'
    assert result['userSource']['handovers'][0]['quantity'] == 0
    assert 'yeniden hesaplanan plan değildir' in result['calculationNote']
    assert snapshot == before


def test_cf_ms19_ravi_summary_keeps_monthly_audit_quality_and_server_provenance():
    from app.ravi.tools import Inspect, inspect_state
    seed = reconciled_seed()
    seed['filterQualityShifts'] = 2
    snapshot = {'seed': seed, 'updatedAt': '2026-10-19T11:00:00Z'}
    before = deepcopy(snapshot)
    result = inspect_state(snapshot, Inspect(collection='summary'))
    assert result['source'] == 'persisted-server'
    assert result['monthlyOrderSource']['fileName'] == 'synthetic.xlsx'
    assert result['monthlyOrderSource']['stockReconciliation']['sourceKey'] == seed['monthlyCustomerDemand']['stockReconciliation']['sourceKey']
    assert result['filterQualityShifts'] == 2
    assert result['orderImport']['shipmentsThrough'] == '2026-10-18T20:59:59.999Z'
    assert snapshot == before


def test_cf_ms21_initial_stock_correction_keeps_original_count_evidence():
    seed=reconciled_seed()
    seed['monthlyCustomerDemand']['stockReconciliation']['rows'][0]['heat']=201
    before=deepcopy(seed)
    validate_stock_planning(seed)
    assert seed==before


def test_cf_ms22_order_timestamp_revision_retains_verified_delivery_baseline():
    seed=monthly_seed();data=seed['monthlyCustomerDemand']
    data['deliveryBaseline']={'year':2026,'snapshotDate':data['snapshotDate'],'importedAt':data['importedAt'],'shipmentsThrough':seed['orderImport']['shipmentsThrough'],'handovers':deepcopy(data['handovers'])}
    data['importedAt']='2026-11-03T09:00:00Z';seed['orderImport']['importedAt']=data['importedAt']
    validate_stock_planning(seed)
    data['deliveryBaseline']['shipmentsThrough']='2026-10-19T09:00:00Z'
    with pytest.raises(ValueError):validate_stock_planning(seed)


def test_cf_ms23_initial_audit_survives_cleared_orders_and_rejects_replacement(tmp_path,monkeypatch):
    from app import database
    from app.config import settings
    from app.production_area import production_area
    monkeypatch.setitem(settings.__dict__,'database_path',tmp_path/'initial-once.sqlite')
    token=production_area.set('cubuk-filtre')
    try:
        database.init_database();seed=reconciled_seed()
        audit=deepcopy(seed['monthlyCustomerDemand']['stockReconciliation']);audit['sourceRows']=deepcopy(seed['monthlyCustomerDemand']['openingStock']['rows']);seed['filterInitialStockSetup']=audit
        kwargs={'can_manage_settings':True,'stock_planning_version':1,'monthly_planning_version':1}
        saved=database.save_planning_state(seed,**kwargs)
        cleared=deepcopy(saved['seed']);cleared.pop('monthlyCustomerDemand');cleared.pop('filterInitialStockSetup')
        saved=database.save_planning_state(cleared,saved['updatedAt'],**kwargs)
        assert saved['seed']['filterInitialStockSetup']==audit
        assert 'monthlyCustomerDemand' not in saved['seed']
        validate_stock_planning(saved['seed']);before=deepcopy(database.planning_state())
        forged=deepcopy(saved['seed']);forged['filterInitialStockSetup']['rows'][0]['heat']+=1
        with pytest.raises(ValueError):database.save_planning_state(forged,saved['updatedAt'],**kwargs)
        assert database.planning_state()==before
        with pytest.raises(ValueError,match='yenileyin'):database.save_planning_state(cleared,saved['updatedAt'],can_manage_settings=True,stock_planning_version=1)
        assert database.planning_state()==before
        forged=deepcopy(saved['seed']);forged['filterInitialStockSetup']['sourceKey']='forged'
        with pytest.raises(ValueError):validate_stock_planning(forged)
    finally:production_area.reset(token)


def test_cf_ms24_original_source_provenance_is_bounded_and_formulas_are_validated():
    seed=monthly_seed();data=seed['monthlyCustomerDemand'];data['originalRows']=deepcopy(data['rows'])
    validate_stock_planning(seed)
    data['originalRows'][0]['quantities'][9]=0
    with pytest.raises(ValueError):validate_stock_planning(seed)
    data['originalRows']=[]
    with pytest.raises(ValueError):validate_stock_planning(seed)


def test_cf_ms25_real_save_later_timestamp_new_year_and_delivery_baseline_protection(tmp_path,monkeypatch):
    from app import database
    from app.config import settings
    from app.production_area import production_area
    monkeypatch.setitem(settings.__dict__,'database_path',tmp_path/'baseline-save.sqlite')
    token=production_area.set('cubuk-filtre')
    try:
        database.init_database();seed=monthly_seed();data=seed['monthlyCustomerDemand']
        data['deliveryBaseline']={'year':2026,'snapshotDate':data['snapshotDate'],'importedAt':data['importedAt'],'shipmentsThrough':seed['orderImport']['shipmentsThrough'],'handovers':deepcopy(data['handovers'])}
        kwargs={'can_manage_settings':True,'stock_planning_version':1,'monthly_planning_version':1}
        saved=database.save_planning_state(seed,**kwargs)
        revised=deepcopy(saved['seed']);revised['monthlyCustomerDemand']['importedAt']='2026-11-03T10:00:00Z';revised['orderImport']['importedAt']='2026-11-03T10:00:00Z'
        saved=database.save_planning_state(revised,saved['updatedAt'],**kwargs)
        assert saved['seed']['orderImport']['shipmentsThrough']=='2026-10-18T20:59:59.999Z'
        before=deepcopy(database.planning_state());forged=deepcopy(saved['seed']);forged['monthlyCustomerDemand']['deliveryBaseline']['snapshotDate']='2026-10-17'
        with pytest.raises(ValueError):database.save_planning_state(forged,saved['updatedAt'],**kwargs)
        assert database.planning_state()==before
        following=deepcopy(saved['seed']);data=following['monthlyCustomerDemand'];data['year']=2027
        data['snapshotDate']='2027-10-18';data['startDate']='2027-10-19';data['endDate']='2027-10-31';data['importedAt']='2027-10-19T10:00:00Z'
        for row in data['handovers']:row['month']='2027-10'
        following['orderImport']['importedAt']=data['importedAt'];following['orderImport']['shipmentsThrough']='2027-10-18T20:59:59.999Z'
        data['deliveryBaseline']={'year':2027,'snapshotDate':data['snapshotDate'],'importedAt':data['importedAt'],'shipmentsThrough':following['orderImport']['shipmentsThrough'],'handovers':deepcopy(data['handovers'])}
        saved=database.save_planning_state(following,saved['updatedAt'],**kwargs)
        assert saved['seed']['monthlyCustomerDemand']['deliveryBaseline']['year']==2027
    finally:production_area.reset(token)


def test_cf_ms26_durable_yearly_handover_corrections_validate_without_active_orders(tmp_path,monkeypatch):
    from app import database
    from app.config import settings
    from app.production_area import production_area
    monkeypatch.setitem(settings.__dict__,'database_path',tmp_path/'delivery-corrections.sqlite')
    token=production_area.set('cubuk-filtre')
    try:
        database.init_database();seed=monthly_seed();data=seed['monthlyCustomerDemand']
        baseline={'year':2026,'snapshotDate':data['snapshotDate'],'importedAt':data['importedAt'],'shipmentsThrough':seed['orderImport']['shipmentsThrough'],'handovers':deepcopy(data['handovers'])}
        seed['filterMonthlyDeliveryBaselines']=[baseline];data['deliveryBaseline']=deepcopy(baseline)
        kwargs={'can_manage_settings':True,'stock_planning_version':1,'monthly_planning_version':1}
        saved=database.save_planning_state(seed,**kwargs)
        corrected=deepcopy(saved['seed']);corrected['filterMonthlyDeliveryBaselines'][0]['handovers'][0]['quantity']=123;corrected['monthlyCustomerDemand']['deliveryBaseline']['handovers'][0]['quantity']=123;corrected['monthlyCustomerDemand']['handovers'][0]['quantity']=123
        saved=database.save_planning_state(corrected,saved['updatedAt'],**kwargs)
        cleared=deepcopy(saved['seed']);cleared.pop('monthlyCustomerDemand');cleared.pop('filterMonthlyDeliveryBaselines')
        saved=database.save_planning_state(cleared,saved['updatedAt'],**kwargs)
        assert saved['seed']['filterMonthlyDeliveryBaselines'][0]['handovers'][0]['quantity']==123
        before=deepcopy(database.planning_state());forged=deepcopy(saved['seed']);forged['filterMonthlyDeliveryBaselines'][0]['snapshotDate']='2026-10-17'
        with pytest.raises(ValueError):database.save_planning_state(forged,saved['updatedAt'],**kwargs)
        assert database.planning_state()==before
        forged=deepcopy(saved['seed']);forged['filterMonthlyDeliveryBaselines'][0]['handovers'][0]['quantity']=-1
        with pytest.raises(ValueError):validate_stock_planning(forged)
    finally:production_area.reset(token)
