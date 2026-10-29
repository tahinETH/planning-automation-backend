"""Saved source provenance for the approved filter meeting changes."""
from copy import deepcopy

from app.ravi.tools import Inspect, inspect_state


def test_cf_r01_manual_correction_reports_original_and_effective_inputs_without_mutation():
    source = {'label': '309-RBTR', 'sourceRow': 0, 'quantities': [100] * 12}
    edited = {**source, 'quantities': [200] * 12}
    snapshot = {'updatedAt': 'saved-time', 'seed': {
        'productionArea': 'cubuk-filtre',
        'monthlyCustomerDemand': {
            'sourceKind': 'manual', 'fileName': 'Manuel aylık sipariş', 'year': 2026,
            'rows': [{'product': 'F.00V.P01.309', 'inputs': [edited], 'quantities': [200] * 12}],
            'originalRows': [{'product': 'F.00V.P01.309', 'inputs': [source]}],
        },
    }}
    before = deepcopy(snapshot)
    result = inspect_state(snapshot, Inspect(collection='monthly_demand', query='309'))
    assert result['source'] == 'persisted-server'
    assert result['userSource']['sourceKind'] == 'manual'
    assert result['rows'][0]['inputs'][0]['quantities'][0] == 200
    assert result['rows'][0]['originalInputs'][0]['quantities'][0] == 100
    assert 'Excel hücre adresi yoktur' in result['calculationNote']
    assert snapshot == before


def test_cf_r02_initial_setup_remains_visible_after_monthly_orders_are_cleared():
    audit = {'cutoffDate': '2026-10-18', 'recordedAt': '2026-10-29T08:00:00Z', 'rows': []}
    snapshot = {'updatedAt': 'saved-time', 'seed': {
        'productionArea': 'cubuk-filtre', 'filterInitialStockSetup': audit,
    }}
    before = deepcopy(snapshot)
    result = inspect_state(snapshot, Inspect(collection='summary'))
    assert result['initialStockSetup'] == audit
    assert result['monthlyOrderSource']['sourceKind'] is None
    assert result['source'] == 'persisted-server'
    assert snapshot == before


def test_cf_r03_correction_detail_is_bounded_and_filter_uses_product_identity():
    row = {'product': 'F.00V.P01.309', 'inputs': [{'label': '309', 'quantities': list(range(100))}]}
    snapshot = {'updatedAt': 'saved-time', 'seed': {'monthlyCustomerDemand': {
        'rows': [row, {'product': 'F.00V.P01.315'}], 'originalRows': [row],
    }}}
    result = inspect_state(snapshot, Inspect(collection='monthly_demand', query='309'))
    assert result['total'] == 1
    assert result['rows'][0]['originalInputs'][0]['quantities']['truncated'] is True
    assert len(result['rows'][0]['originalInputs'][0]['quantities']['items']) == 40
