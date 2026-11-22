"""Read the approved monthly customer format without executing workbook code."""
import re
import unicodedata
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
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
_ZERO_TOKENS = {'-', '--', '—', '–', 'NULL', 'N/A', '#N/A', 'NA', 'NONE', 'YOK'}

def normalized(value):
    return _month_header(unicodedata.normalize('NFC', value)).replace('i\u0307', 'i')


def label_key(value):
    return re.sub(r'\s+', '', value).upper().replace('İ', 'I')


def _parse_monthly_quantity(value: str, numeric_cell: bool) -> int:
    """Parse a monthly integer quantity tolerantly: '-' / blank / NULL / invalid -> 0,
    and accept Turkish or English dot/comma thousands separators cleanly."""
    cleaned = re.sub(r'[\s\u00a0]+', '', value.strip())
    if not cleaned or cleaned.upper() in _ZERO_TOKENS:
        return 0
    if numeric_cell:
        try:
            number = Decimal(cleaned)
        except InvalidOperation:
            return 0
    else:
        # Handle Turkish (1.054.900 or 1.054.900,00) and English (1,054,900 or 1,054,900.00)
        # thousands separators without choking on dots or commas.
        if re.fullmatch(r'\d+(?:\.\d{3})+(?:,\d+)?', cleaned):
            normalized_num = cleaned.replace('.', '').replace(',', '.')
        elif re.fullmatch(r'\d+(?:,\d{3})+(?:\.\d+)?', cleaned):
            normalized_num = cleaned.replace(',', '')
        else:
            normalized_num = cleaned.replace(',', '.')
        try:
            number = Decimal(normalized_num)
        except InvalidOperation:
            return 0
    if not number.is_finite():
        return 0
    if number < 0:
        return 0
    if number > MAX:
        raise OrderImportError('Aylık kaynak adet güvenli sınırı aşıyor.')
    return int(number.quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def _extract_year(values, header):
    years = set()
    for r, cells in values.items():
        if r >= header:
            continue
        for raw, _ in cells.values():
            text_val = raw.strip().upper()
            if m := re.fullmatch(r'(20\d{2})\s*YILI', text_val):
                years.add(int(m[1]))
    if len(years) == 1:
        return next(iter(years))
    if len(years) > 1:
        raise OrderImportError('Aylık sipariş yılını kontrol edin.')
    # Fallback: read year from the header date cell (e.g. 2.11.2026 or Excel date serial) in column A.
    header_a, header_numeric = values.get(header, {}).get('A', ('', False))
    header_a = header_a.strip()
    if m := re.fullmatch(r'\d{1,2}[./-]\d{1,2}[./-](20\d{2})', header_a):
        return int(m[1])
    if m := re.fullmatch(r'(20\d{2})[./-]\d{1,2}[./-]\d{1,2}', header_a):
        return int(m[1])
    if header_numeric and header_a:
        try:
            serial = int(Decimal(header_a))
            parsed = date(1899, 12, 30) + timedelta(days=serial)
            if 2000 <= parsed.year <= 2100:
                return parsed.year
        except (ValueError, InvalidOperation, OverflowError):
            pass
    raise OrderImportError('Aylık sipariş yılını kontrol edin.')


def _has_monthly_table(values):
    first_total = next((r for r in sorted(values) if normalized(values.get(r, {}).get('A', ('', False))[0]) == 'cf total'), None)
    if first_total is None:
        return False
    for r, cells in values.items():
        if r >= first_total:
            continue
        months = {normalized(v[0]) for v in cells.values() if normalized(v[0]) in MONTH_HEADERS}
        if len(months) == 12:
            return True
    return False


def parse_filter_monthly(archive, shared):
    paths = {}
    for name, path in _sheet_paths(archive):
        key = normalized(name)
        if key in paths: raise OrderImportError('Sayfa adı tekrarlı veya belirsiz.')
        paths[key] = (name, path)
    # A stock-only legacy template is not a monthly source.
    template = paths.get('siparis sablonu')
    if template:
        template_values = _sheet_values(ET.fromstring(archive.read(template[1])), shared)
        if not any(normalized(v[0]) in MONTH_HEADERS for cells in template_values.values() for v in cells.values()): template = None
    chosen = template or next((paths[key] for key in ('siparis', 'calisma gunler', 'calisma gunleri') if key in paths), None)
    if not chosen:
        fallback = []
        for name, path in paths.values():
            sheet_values = _sheet_values(ET.fromstring(archive.read(path)), shared)
            if _has_monthly_table(sheet_values):
                fallback.append((name, path))
        if len(fallback) == 1:
            chosen = fallback[0]
        elif len(fallback) > 1:
            raise OrderImportError('Aylık müşteri dosyasında birden fazla Ocak–Aralık tablosu bulundu; sayfa adını SİPARİŞ ŞABLONU yapın.')
    if not chosen:
        raise OrderImportError('Aylık müşteri dosyasında SİPARİŞ ŞABLONU, SİPARİŞ veya Çalışma Günler sayfası bulunamadı.')
    name, path = chosen
    sheet = ET.fromstring(archive.read(path))
    values = _sheet_values(sheet, shared)
    uncached_cells = {cell.attrib.get('r') for cell in sheet.iter(f'{{{MAIN_NS}}}c')
                      if cell.find(f'{{{MAIN_NS}}}f') is not None and not cell.findtext(f'{{{MAIN_NS}}}v')}
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
    year = _extract_year(values, header)
    day_rows = [r for r in values if r < header and normalized(text(r,'A')) == 'day']
    if len(day_rows) > 1:
        raise OrderImportError('Aylık iş günü (Day) satırı tekrarlı.')
    if len(day_rows) == 1:
        try:
            days = []
            for c in columns:
                raw_day = text(day_rows[0], c).replace(',', '.')
                n = 0.0 if not raw_day or raw_day in _ZERO_TOKENS else float(raw_day)
                if not 0 <= n <= 31 or n * 2 % 1:
                    raise ValueError()
                days.append(n)
        except ValueError:
            raise OrderImportError('Aylık iş günü 0–31 arasında tam veya yarım gün olmalıdır.') from None
    else:
        days = [0.0] * 12
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
            if f'{c}{r}' in uncached_cells:
                raise OrderImportError(f'{name}!{c}{r}: formülün hesaplanmış değeri yok; Excel’de kaydedin.')
            raw, is_numeric = values.get(r, {}).get(c, ('', False))
            out.append(_parse_monthly_quantity(raw, is_numeric))
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
    result = {'format': 'filter-monthly', 'sheetName': name, 'sourceKind': 'upload', 'year': year, 'workingDays': days, 'rows': rows}
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
                    row[stage] = _parse_integer(*cell, r, stage) if cell[0].strip() else 0
                stock_rows.append(row)
            result['openingStock'] = {'cutoffDate': cutoff.isoformat(), 'rows': stock_rows}
    return result


def build_filter_monthly_template(year):
    """Build the approved monthly Çubuk Filtre order sheet matching the operational layout."""
    from io import BytesIO
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    if type(year) is not int or not 2000 <= year <= 2100:
        raise OrderImportError('Sipariş yılı 2000–2100 arasında olmalıdır.')
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'SİPARİŞ ŞABLONU'
    thin = Side(style='thin', color='000000')
    grid_border = Border(left=thin, right=thin, top=thin, bottom=thin)

    sheet['A1'] = f'{year} YILI'
    sheet['A1'].font = Font(bold=True, size=11, color='000000')
    sheet['A2'] = 'Day'
    sheet['A2'].font = Font(bold=True, size=10, color='595959')

    header_row = 4
    sheet.cell(header_row, 1, date(year, 1, 1))
    sheet.cell(header_row, 1).number_format = 'd.mm.yyyy'
    sheet.cell(header_row, 1).fill = PatternFill('solid', fgColor='FFFF00')
    sheet.cell(header_row, 1).font = Font(bold=True, color='000000')
    sheet.cell(header_row, 1).alignment = Alignment(horizontal='center', vertical='center')
    sheet.cell(header_row, 1).border = grid_border

    months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
    for column, month in enumerate(months, 2):
        day_cell = sheet.cell(2, column, 0)
        day_cell.font = Font(size=10, color='595959')
        day_cell.alignment = Alignment(horizontal='right', vertical='center')
        head_cell = sheet.cell(header_row, column, month)
        head_cell.fill = PatternFill('solid', fgColor='FFFFFF')
        head_cell.font = Font(bold=True, color='000000')
        head_cell.alignment = Alignment(horizontal='center', vertical='center')
        head_cell.border = grid_border

    # Exact row layout matching the approved Çubuk Filtre monthly sheet.
    row_specs = [
        ('410-RBTR', '5B9BD5', '000000', False, None),
        ('501-RBTR', '70AD47', '000000', False, None),
        ('481-HoP', '70AD47', '000000', False, None),
        ('481-CtP/NaP', '70AD47', '000000', False, None),
        ('003-RBCD', '70AD47', '000000', False, None),
        ('001-RBCD', '70AD47', '000000', False, None),
        ('001-NaP', '70AD47', '000000', False, None),
        ('001-CtP', '70AD47', '000000', False, None),
        ('424-HoP/CtP', '70AD47', '000000', False, None),
        ('DRS Total', 'FFFFFF', '000000', True, lambda c: f'=SUM({c}6:{c}13)'),
        ('309-RBTR', 'FF9900', '000000', False, None),
        ('315-BaP', 'FF9900', '000000', False, None),
        ('002-CtP', 'FF9900', '000000', False, None),
        ('245-CtP', 'FF9900', '000000', False, None),
        ('C100 - DRS', '595959', 'FFD966', False, lambda c: f'=ROUNDUP((({c}6+{c}9)*1.03)/15000,0)*15000'),
        ('002 - DRS', '595959', 'FFD966', False, lambda c: f'=ROUNDUP(SUM({c}10:{c}12)*1.04/1000,0)*1000'),
        ('081 - DRS', '595959', 'FFD966', False, lambda c: f'=ROUNDUP((({c}7+{c}8+{c}13)*1.04)/1000,0)*1100'),
        ('ÇF Total', '1F3864', 'FFFFFF', True, lambda c: f'=SUM({c}15:{c}21)'),
        ('Günlük Adet', '1F3864', 'FFFFFF', True, lambda c: f'=IF({c}2>0,ROUND({c}22/{c}2,0),0)'),
    ]

    for row, (label, bg, fg, bold_row, formula_fn) in enumerate(row_specs, header_row + 1):
        label_cell = sheet.cell(row, 1, label)
        label_cell.fill = PatternFill('solid', fgColor=bg)
        label_cell.font = Font(bold=True, color=fg)
        label_cell.alignment = Alignment(horizontal='left', vertical='center')
        label_cell.border = grid_border
        for column in range(2, 14):
            c = get_column_letter(column)
            value = formula_fn(c) if formula_fn else 0
            cell = sheet.cell(row, column, value)
            cell.fill = PatternFill('solid', fgColor=bg)
            cell.font = Font(bold=bold_row, color=fg)
            cell.number_format = '#,##0'
            cell.alignment = Alignment(horizontal='right', vertical='center')
            cell.border = grid_border

    sheet['A25'] = 'Yeşil: DRS kaynak adetleri. Turuncu: doğrudan ÇF ürünleri. Gri: hesaplanan DRS ürünleri. Mavi (410-RBTR): referans satır.'
    sheet['A25'].font = Font(italic=True, size=9, color='595959')
    sheet.column_dimensions['A'].width = 20
    for column in range(2, 14):
        sheet.column_dimensions[get_column_letter(column)].width = 13
    sheet.freeze_panes = 'B5'
    output = BytesIO(); workbook.save(output)
    return output.getvalue()
