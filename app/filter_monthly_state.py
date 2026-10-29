"""Validate saved monthly source evidence; no scheduling or production mutation."""
import json
import math
import re
from datetime import date, datetime, time
from zoneinfo import ZoneInfo
from .filter_monthly_import import RULES, DIRECT, label_key, MAX
from .order_import import FILTER_DAILY_PRODUCTS

def validate_filter_initial_stock_setup(seed):
    audit=seed.get('filterInitialStockSetup')
    if audit is None: return
    def fail(): raise ValueError('Başlangıç sayım kaydı geçersiz.')
    def integer(n): return type(n) is int and 0<=n<=MAX
    if seed.get('productionArea')!='cubuk-filtre' or not isinstance(audit,dict): fail()
    try:
        if date.fromisoformat(audit['cutoffDate']).isoformat()!=audit['cutoffDate']: fail()
        recorded=datetime.fromisoformat(audit['recordedAt'].replace('Z','+00:00'))
        if recorded.tzinfo is None: fail()
    except (KeyError,TypeError,ValueError,AttributeError): fail()
    source=audit.get('sourceRows')
    rows=audit.get('rows')
    known={p.get('product') for p in seed.get('products',[])}
    if not isinstance(source,list) or not 0<len(source)<=100 or not isinstance(rows,list) or len(rows)!=len(source): fail()
    seen=set()
    for row in source:
        if not isinstance(row,dict) or row.get('product') not in known or row['product'] in seen: fail()
        seen.add(row['product'])
        if any(key not in row or row[key] is not None and not integer(row[key]) for key in ('delivered','visual','heat','milling','grinding')): fail()
    reviewed=set()
    for row in rows:
        if not isinstance(row,dict) or row.get('product') not in seen or row['product'] in reviewed or any(not integer(row.get(k)) for k in ('visual','heat','milling','grinding')): fail()
        if row['visual']+row['heat']>MAX or 'delivered' in row and not integer(row['delivered']): fail()
        reviewed.add(row['product'])
    key=json.dumps([audit['cutoffDate'],sorted([[r['product'],r['visual'],r['heat'],r['milling'],r['grinding']] for r in source])],ensure_ascii=False,separators=(',',':'))
    if audit.get('sourceKey')!=key: fail()
    validate_filter_delivery_baseline(audit.get('deliveryBaseline'),known)

def validate_filter_delivery_baseline(baseline,known):
    def fail(): raise ValueError('Teslimat kesim kaydı geçersiz.')
    def integer(n): return type(n) is int and 0<=n<=MAX
    if baseline is not None:
        if not isinstance(baseline,dict) or type(baseline.get('year')) is not int or not 2000<=baseline['year']<=2100: fail()
        try:
            snapshot=date.fromisoformat(baseline['snapshotDate'])
            imported=datetime.fromisoformat(baseline['importedAt'].replace('Z','+00:00'))
            cutoff=datetime.fromisoformat(baseline['shipmentsThrough'].replace('Z','+00:00'))
            if imported.tzinfo is None or cutoff.tzinfo is None or snapshot>imported.astimezone(ZoneInfo('Europe/Istanbul')).date(): fail()
            if cutoff!=min(imported,datetime.combine(snapshot,time(23,59,59,999000),tzinfo=ZoneInfo('Europe/Istanbul'))): fail()
        except (KeyError,ValueError,AttributeError,TypeError): fail()
        handovers=baseline.get('handovers')
        if not isinstance(handovers,list) or len(handovers)>720: fail()
        keys=set()
        for row in handovers:
            if not isinstance(row,dict) or row.get('product') not in known or not isinstance(row.get('month'),str) or not re.fullmatch(str(baseline['year'])+r'-(0[1-9]|1[0-2])',row['month']) or not integer(row.get('quantity')): fail()
            key=(row['product'],row['month'])
            if key in keys: fail()
            keys.add(key)

def validate_filter_monthly_state(seed):
    validate_filter_initial_stock_setup(seed)
    baselines=seed.get('filterMonthlyDeliveryBaselines')
    if baselines is not None:
        if seed.get('productionArea')!='cubuk-filtre' or not isinstance(baselines,list) or len(baselines)>101: raise ValueError('Teslimat kesim listesi geçersiz.')
        seen_years=set()
        for baseline in baselines:
            validate_filter_delivery_baseline(baseline,{p.get('product') for p in seed.get('products',[])})
            if not isinstance(baseline,dict) or baseline['year'] in seen_years: raise ValueError('Teslimat kesim yılı tekrarlı.')
            seen_years.add(baseline['year'])
    data = seed.get('monthlyCustomerDemand')
    if data is None: return
    def fail(): raise ValueError('Aylık müşteri kaynağı, adetleri veya tarihleri geçersiz.')
    def integer(n): return type(n) is int and 0 <= n <= MAX
    def valid_date(s):
        try: return isinstance(s,str) and bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}',s)) and date.fromisoformat(s).isoformat()==s
        except ValueError: return False
    def twelve(xs): return isinstance(xs,list) and len(xs)==12 and all(integer(n) for n in xs)
    def instant(s):
        if not isinstance(s,str): fail()
        try: value=datetime.fromisoformat(s.replace('Z','+00:00'))
        except ValueError: fail()
        if value.tzinfo is None: fail()
        return value
    if seed.get('productionArea') != 'cubuk-filtre' or not isinstance(data,dict) or data.get('format') != 'filter-monthly' or seed.get('dailyCustomerDemand') or seed.get('customerDemand'): fail()
    year=data.get('year'); days=data.get('workingDays')
    if type(year) is not int or not 2000<=year<=2100 or not isinstance(days,list) or len(days)!=12 or any(type(n) not in (int,float) or not math.isfinite(n) or not 0<=n<=31 or n*2%1 for n in days): fail()
    if not all(valid_date(data.get(k)) for k in ('startDate','endDate','snapshotDate')) or data['startDate']>data['endDate'] or any(data[k][:4]!=str(year) for k in ('startDate','endDate')): fail()
    imported=instant(data.get('importedAt')); metadata=seed.get('orderImport') or {}
    if not isinstance(metadata,dict): fail()
    if data['snapshotDate']>imported.astimezone(ZoneInfo('Europe/Istanbul')).date().isoformat(): fail()
    cutoff=instant(metadata.get('shipmentsThrough'))
    baseline=data.get('deliveryBaseline')
    baseline_imported=imported; baseline_snapshot=data['snapshotDate']
    if baseline is not None:
        if not isinstance(baseline,dict) or baseline.get('year')!=year or not valid_date(baseline.get('snapshotDate')): fail()
        baseline_imported=instant(baseline.get('importedAt')); baseline_snapshot=baseline['snapshotDate']
        if baseline_imported>imported or baseline_snapshot>data['snapshotDate']: fail()
        if instant(baseline.get('shipmentsThrough'))!=cutoff: fail()
        baseline_handovers=baseline.get('handovers')
        if not isinstance(baseline_handovers,list) or len(baseline_handovers)>720: fail()
        baseline_keys=set()
        for h in baseline_handovers:
            if not isinstance(h,dict) or not isinstance(h.get('product'),str) or not isinstance(h.get('month'),str) or not re.fullmatch(str(year)+r'-(0[1-9]|1[0-2])',h['month']) or not integer(h.get('quantity')): fail()
            key=(h['product'],h['month'])
            if key in baseline_keys: fail()
            baseline_keys.add(key)
    expected=min(baseline_imported,datetime.combine(date.fromisoformat(baseline_snapshot),time(23,59,59,999000),tzinfo=ZoneInfo('Europe/Istanbul')))
    if instant(metadata.get('importedAt')) != imported or cutoff != expected: fail()
    rows=data.get('rows'); known={p.get('product') for p in seed.get('products',[])}
    if not isinstance(rows,list) or not 0<len(rows)<=60: fail()
    seen=set()
    for row in rows:
        if not isinstance(row,dict) or not isinstance(row.get('product'),str) or row.get('product') not in known or row.get('product') in seen or row.get('kind') not in ('internal','external') or not twelve(row.get('quantities')): fail()
        seen.add(row['product'])
        key=next((k for k in DIRECT+list(RULES) if FILTER_DAILY_PRODUCTS[k]==row['product']),None)
        if key is None: fail()
        inputs=row.get('inputs')
        expected_labels=RULES[key][0] if key in RULES else [key]
        if not isinstance(inputs,list) or len(inputs)!=len(expected_labels): fail()
        labels=[]
        for item in inputs:
            if not isinstance(item,dict) or not isinstance(item.get('label'),str) or not twelve(item.get('quantities')) or not integer(item.get('sourceRow')) or item['sourceRow']==0 and data.get('sourceKind')!='manual': fail()
            labels.append(label_key(item['label']))
        if sorted(labels)!=sorted(expected_labels): fail()
        if key in RULES:
            _,factor,unit,output=RULES[key]
            expected_quantities=[((sum(item['quantities'][m] for item in inputs)*factor+100*unit-1)//(100*unit))*output for m in range(12)]
        else: expected_quantities=inputs[0]['quantities']
        if row['quantities']!=expected_quantities: fail()
    if data.get('sourceKind') not in (None,'manual','upload'): fail()
    originals=data.get('originalRows')
    if originals is not None:
        if not isinstance(originals,list) or len(originals)!=len(rows): fail()
        # Reuse the same source/formula validator without recursive provenance.
        original_data={**data,'rows':originals,'exceptions':[]}
        original_data.pop('originalRows',None)
        validate_filter_monthly_state({**seed,'monthlyCustomerDemand':original_data})
    handovers=data.get('handovers'); exceptions=data.get('exceptions')
    if not isinstance(handovers,list) or len(handovers)>720 or not isinstance(exceptions,list) or len(exceptions)>1000: fail()
    hseen={}
    for row in handovers:
        if not isinstance(row,dict) or not isinstance(row.get('product'),str) or row.get('product') not in seen or not isinstance(row.get('month'),str) or not re.fullmatch(str(year)+r'-(0[1-9]|1[0-2])',row['month']) or not integer(row.get('quantity')): fail()
        key=(row['product'],row['month'])
        if key in hseen or row['quantity']>0 and row['month']>data['snapshotDate'][:7]: fail()
        hseen[key]=row['quantity']
    eseen=set(); allocated={}
    for row in exceptions:
        if not isinstance(row,dict) or not isinstance(row.get('product'),str) or row.get('product') not in seen or not valid_date(row.get('date')) or not data['startDate']<=row['date']<=data['endDate'] or not integer(row.get('quantity')): fail()
        key=(row['product'],row['date'])
        if key in eseen: fail()
        eseen.add(key); month_key=(row['product'],row['date'][:7])
        allocated[month_key]=allocated.get(month_key,0)+row['quantity']
    for row in rows:
        for m,ordered in enumerate(row['quantities']):
            month=f'{year}-{m+1:02d}'; key=(row['product'],month)
            if ordered>0 and data['startDate'][:7]<=month<=data['endDate'][:7] and month<=data['snapshotDate'][:7] and key not in hseen: fail()
            if allocated.get(key,0)>max(0,ordered-hseen.get(key,0)): fail()
    opening=data.get('openingStock')
    if opening is not None:
        if not isinstance(opening,dict) or not valid_date(opening.get('cutoffDate')) or not isinstance(opening.get('rows'),list) or len(opening['rows'])>100: fail()
        stockseen=set()
        for row in opening['rows']:
            if not isinstance(row,dict) or not isinstance(row.get('product'),str) or row.get('product') not in known or row['product'] in stockseen or not all(k in row for k in ('delivered','visual','heat','milling','grinding')) or any(row.get(k) is not None and not integer(row[k]) for k in ('delivered','visual','heat','milling','grinding')): fail()
            stockseen.add(row['product'])

    reconciliation=data.get('stockReconciliation') if not seed.get('filterInitialStockSetup') else None
    if reconciliation is not None:
        if not opening or not isinstance(reconciliation,dict) or reconciliation.get('cutoffDate')!=opening['cutoffDate']: fail()
        instant(reconciliation.get('recordedAt'))
        source_rows=sorted([[r['product'],r['visual'],r['heat'],r['milling'],r['grinding']] for r in reconciliation.get('sourceRows',opening['rows'])])
        source_key=json.dumps([opening['cutoffDate'],source_rows],ensure_ascii=False,separators=(',',':'))
        if reconciliation.get('sourceKey')!=source_key: fail()
        reviewed=reconciliation.get('rows')
        if not isinstance(reviewed,list) or len(reviewed)!=len(opening['rows']): fail()
        reviewed_seen=set()
        for row in reviewed:
            if not isinstance(row,dict) or not isinstance(row.get('product'),str) or row['product'] in reviewed_seen: fail()
            reviewed_seen.add(row['product'])
            original=next((r for r in opening['rows'] if r['product']==row['product']),None)
            if original is None: fail()
            for key in ('visual','heat','milling','grinding'):
                if not integer(row.get(key)): fail()
            if row['visual']+row['heat']>MAX or 'delivered' in row and not integer(row['delivered']): fail()
