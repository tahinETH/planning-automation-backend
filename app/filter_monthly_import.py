"""Read the approved monthly customer format without executing workbook code."""
import re
import unicodedata
from datetime import date, timedelta
from decimal import Decimal
from xml.etree import ElementTree as ET

from .order_import import (OrderImportError, MAIN_NS, MONTH_HEADERS,
    FILTER_DAILY_PRODUCTS, _sheet_paths, _sheet_values, _month_header, _parse_integer)

RULES = {
    'C100-DRS': (['501-RBTR', '003-RBCD'], 103, 15000, 15000),
    '002-DRS': (['001-RBCD', '001-NAP', '001-CTP'], 104, 1000, 1000),
    '081-DRS': (['481-HOP', '481-CTP/NAP', '424-HOP/CTP'], 104, 1000, 1100),
}
DIRECT = ['309-RBTR', '315-BAP', '002-CTP', '245-CTP']
MAX = 9007199254740991

def normalized(value):
    return _month_header(unicodedata.normalize('NFC', value)).replace('i\u0307', 'i')


def label_key(value):
    return re.sub(r'\s+', '', value).upper().replace('İ', 'I')

def parse_filter_monthly(archive, shared):
    paths = {}
    for name, path in _sheet_paths(archive):
        key = normalized(name)
        if key in paths: raise OrderImportError('Sayfa adı tekrarlı veya belirsiz.')
        paths[key] = (name, path)
    chosen = next((paths[key] for key in ('siparis', 'calisma gunler', 'calisma gunleri') if key in paths), None)
    if not chosen:
        raise OrderImportError('Aylık müşteri dosyasında SİPARİŞ veya Çalışma Günler sayfası bulunamadı.')
    name, path = chosen
    sheet = ET.fromstring(archive.read(path))
    values = _sheet_values(sheet, shared)
    text = lambda r,c: values.get(r, {}).get(c, ('', False))[0].strip()
    first_total = next((r for r in sorted(values) if normalized(text(r,'A')) == 'cf total'), None)
    headers = []
    for r, cells in values.items():
        if first_total is not None and r >= first_total: continue
        month_cells = [(normalized(value[0]), column) for column, value in cells.items() if normalized(value[0]) in MONTH_HEADERS]
        if len({key for key, _ in month_cells}) != len(month_cells): raise OrderImportError('Aylık sipariş ay başlığı tekrarlı.')
        months = dict(month_cells)
        if len(months) == 12:
            headers.append((r, [months[m] for m in MONTH_HEADERS]))
    if len(headers) != 1:
        raise OrderImportError('Aylık sipariş: tek bir Ocak–Aralık başlığı gerekir.')
    header, columns = headers[0]
    years = [int(m[1]) for r in values if r < header and (m := re.fullmatch(r'(20\d{2})\s*YILI', text(r,'A').upper()))]
    if len(set(years)) != 1:
        raise OrderImportError('Aylık sipariş yılını kontrol edin.')
    day_rows = [r for r in values if r < header and normalized(text(r,'A')) == 'day']
    if len(day_rows) != 1:
        raise OrderImportError('Aylık iş günü (Day) satırı bulunamadı.')
    try:
        days = [float(text(day_rows[0], c)) for c in columns]
        if any(not 0 <= n <= 31 or n * 2 % 1 for n in days): raise ValueError()
    except ValueError:
        raise OrderImportError('Aylık iş günü 0–31 arasında tam veya yarım gün olmalıdır.') from None
    end = next((r for r in sorted(values) if r > header and normalized(text(r,'A')) == 'cf total'), None)
    if end is None:
        raise OrderImportError('ÇF Total sınırı bulunamadı.')
    labels = {}
    for r in range(header + 1, end):
        key = label_key(text(r,'A'))
        if not key: continue
        if key in labels: raise OrderImportError(f'Aylık sipariş etiketi tekrarlı: {text(r,"A")}')
        labels[key] = r
    def quantities(key):
        if key not in labels: raise OrderImportError(f'Aylık sipariş kaynak satırı eksik: {key}')
        r = labels[key]
        out = []
        for c in columns:
            if not text(r,c): raise OrderImportError(f'{name}!{c}{r}: adet eksik; formül varsa Excel’de hesaplayıp kaydedin. Sıfır adedi açıkça girin.')
            out.append(_parse_integer(*values[r][c], r, 'Aylık kaynak adet'))
        return out
    rows = []
    for key in DIRECT + list(RULES):
        if key not in labels: raise OrderImportError(f'Aylık sipariş ürün satırı eksik: {key}')
        input_keys = RULES[key][0] if key in RULES else [key]
        inputs = [{'label': text(labels[k], 'A') if k in labels else k, 'sourceRow': labels.get(k, 0), 'quantities': quantities(k)} for k in input_keys]
        if key in RULES:
            _, percent, unit, output = RULES[key]
            amounts = []
            for i in range(12):
                total = sum(x['quantities'][i] for x in inputs)
                count = (total * percent + 100 * unit - 1) // (100 * unit)
                amounts.append(count * output)
            rule = f'ceil(sum × {percent}/100 ÷ {unit}) × {output}'
        else:
            amounts, rule = inputs[0]['quantities'], 'direct'
        if any(n > MAX for n in amounts): raise OrderImportError('Aylık hesaplanan adet güvenli sınırı aşıyor.')
        rows.append({'label': text(labels[key],'A'), 'product': FILTER_DAILY_PRODUCTS[key],
            'kind': 'internal' if key in RULES else 'external', 'sourceRow': labels[key],
            'quantities': amounts, 'rule': rule, 'inputs': inputs})
    result = {'format': 'filter-monthly', 'sheetName': name, 'year': years[0], 'workingDays': days, 'rows': rows}
    if 'siparis sablonu' in paths:
        stock_name, stock_path = paths['siparis sablonu']
        stock_sheet = ET.fromstring(archive.read(stock_path))
        stock_values = _sheet_values(stock_sheet, shared)
        uncached = {cell.attrib.get('r') for cell in stock_sheet.iter(f'{{{MAIN_NS}}}c')
                    if cell.find(f'{{{MAIN_NS}}}f') is not None and not cell.findtext(f'{{{MAIN_NS}}}v')}
        stages = {'teslimati gerceklesen': 'delivered', 'gkm onu': 'visual', 'isil islem': 'heat', 'freze onu': 'milling', 'taslama onu': 'grinding'}
        found = {}
        for r, cells in stock_values.items():
            key = normalized(cells.get('A', ('',False))[0])
            if key in stages:
                if stages[key] in found: raise OrderImportError('Stok satırı tekrarlı.')
                found[stages[key]] = r
        if found:
            if set(found) != set(stages.values()): raise OrderImportError('Stok tablosunun proses satırları eksik.')
            candidates = [r for r, cells in stock_values.items() if r < min(found.values()) and any(re.fullmatch(r'(?:F\.[A-Z0-9.]+|2\.433\.084\.\d{3}|2433084\d{3})', value[0].strip().upper()) for col,value in cells.items() if col != 'A')]
            if len(candidates) != 1: raise OrderImportError('Stok tarih / ürün başlığı eksik veya belirsiz.')
            top = candidates[0]
            try:
                raw_date = stock_values[top]['A'][0]
                serial = int(Decimal(raw_date))
                if Decimal(raw_date) != serial: raise ValueError()
                cutoff = date(1899,12,30) + timedelta(days=serial)
                if not 2000 <= cutoff.year <= 2100: raise ValueError()
            except (KeyError, ValueError, ArithmeticError, OverflowError):
                raise OrderImportError('Stok sayım tarihi geçersiz.') from None
            workbook = ET.fromstring(archive.read('xl/workbook.xml'))
            props = workbook.find(f'{{{MAIN_NS}}}workbookPr')
            if props is not None and props.attrib.get('date1904') in {'1','true'}:
                raise OrderImportError('Stok için 1904 tarih sistemi desteklenmiyor.')
            stock_rows, seen = [], set()
            for col, (raw, numeric) in stock_values[top].items():
                if col == 'A' or not raw.strip(): continue
                product = raw.strip().upper()
                if re.fullmatch(r'2433084\d{3}', product): product = f'2.433.084.{product[-3:]}'
                if not re.fullmatch(r'(?:F\.[A-Z0-9.]+|2\.433\.084\.\d{3})', product):
                    raise OrderImportError(f'Stok ürün kodu geçersiz: {raw}')
                if product in seen: raise OrderImportError(f'Stok ürünü tekrarlı: {product}')
                seen.add(product)
                row = {'product': product}
                for stage, r in found.items():
                    if f'{col}{r}' in uncached:
                        raise OrderImportError(f'{stock_name}!{col}{r}: formülün hesaplanmış değeri yok.')
                    cell = stock_values[r].get(col, ('',False))
                    row[stage] = _parse_integer(*cell, r, stage) if cell[0].strip() else None
                stock_rows.append(row)
            result['openingStock'] = {'cutoffDate': cutoff.isoformat(), 'rows': stock_rows}
    return result
