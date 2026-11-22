"""Independent synthetic examples for the approved 22 October monthly rules.

All expected amounts below come from the approved business examples. No helper
imports a calculation or mapping from the application under test.
"""
from io import BytesIO
from xml.sax.saxutils import escape
from zipfile import ZipFile

import pytest

from app.order_import import OrderImportError, parse_order_xlsx

MONTHS = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
C100 = 'F.00V.C15.100'
DRS002 = 'F.00V.C15.002'
CTP002 = 'F.00Z.S00.002'
P081 = '2.433.084.081'
P309 = 'F.00V.P01.309'


def cell(ref, value):
    if value is None:
        return ''
    if isinstance(value, tuple):
        formula, cached = value
        return f'<c r="{ref}"><f>{escape(formula)}</f>{"" if cached is None else f"<v>{cached}</v>"}</c>'
    if isinstance(value, (int, float)):
        return f'<c r="{ref}"><v>{value}</v></c>'
    return f'<c r="{ref}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'


def sheet(rows):
    return '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + ''.join(
        f'<row r="{number}">' + ''.join(cell(f'{column}{number}', value) for column, value in values.items()) + '</row>'
        for number, values in rows.items()) + '</sheetData></worksheet>'


def book(sheets):
    stream = BytesIO()
    with ZipFile(stream, 'w') as archive:
        archive.writestr('xl/workbook.xml', '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>' + ''.join(
            f'<sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>' for i, (name, _) in enumerate(sheets, 1)) + '</sheets></workbook>')
        archive.writestr('xl/_rels/workbook.xml.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + ''.join(
            f'<Relationship Id="rId{i}" Target="worksheets/sheet{i}.xml"/>' for i in range(1, len(sheets) + 1)) + '</Relationships>')
        for i, (_, rows) in enumerate(sheets, 1):
            archive.writestr(f'xl/worksheets/sheet{i}.xml', sheet(rows))
    return stream.getvalue()


def monthly_rows(*, header=8, columns='BCDEFGHIJKLM'):
    rows = {2: {'A': 'Day', **dict(zip(columns, [26] * 11 + [26.5]))},
            6: {'A': '2026 YILI'}, header: {'A': 'tarih', **dict(zip(columns, MONTHS))}}
    inputs = [
        ('501-RBTR', [10000] * 12), ('003-RBCD', [5000] * 12),
        ('001-RBCD', [2000] * 12), ('001-NaP', [2000] * 12),
        ('001-CtP', [2000, 2000, 2000, 1000] + [2000] * 8),
        ('481-HoP', [3000] * 12), ('481-CtP/NaP', [3000] * 12), ('424-HoP/CtP', [3000] * 12),
        ('DRS Total', [999999] * 12), ('309-RBTR', [123] * 12),
        ('C100 - DRS', [0] * 12), ('002 - DRS', [0] * 12),
        ('081 - DRS', [0] * 12), ('002-CtP', [222] * 12), ('315-BAP', [333] * 12), ('245-CtP', [444] * 12), ('ÇF Total', [999999] * 12),
    ]
    for number, (label, quantities) in enumerate(inputs, header + 1):
        rows[number] = {'A': label, **dict(zip(columns, quantities))}
    return rows


def parse(rows=None, *, name='SİPARİŞ', extra=()):
    return parse_order_xlsx(book([(name, monthly_rows() if rows is None else rows), *extra]), allow_filter_monthly=True)


def by_product(result):
    return {row['product']: row for row in result['rows']}


def test_cf_mi01_approved_formulas_use_raw_inputs_and_ignore_false_final_zero():
    result = parse()
    assert result['format'] == 'filter-monthly'
    assert result['sheetName'] == 'SİPARİŞ'
    assert result['year'] == 2026
    assert result['workingDays'] == [26] * 11 + [26.5]
    products = by_product(result)
    assert set(products) == {C100, DRS002, P081, P309, CTP002, 'F.00V.P01.315', '2.433.084.245'}
    assert products[C100]['quantities'] == [30000] * 12
    assert products[DRS002]['quantities'][2:4] == [7000, 6000]
    assert products[P081]['quantities'][9] == 11000
    assert products[P309]['quantities'] == [123] * 12
    assert products[CTP002]['quantities'] == [222] * 12
    for product, labels in [(C100, {'501-RBTR', '003-RBCD'}), (DRS002, {'001-RBCD', '001-NaP', '001-CtP'}), (P081, {'481-HoP', '481-CtP/NaP', '424-HoP/CtP'})]:
        row = products[product]
        assert isinstance(row['rule'], str) and row['rule']
        assert {item['label'] for item in row['inputs']} == labels
        assert all(len(item['quantities']) == 12 and item['sourceRow'] > 0 for item in row['inputs'])


def test_cf_mi02_headers_and_labels_control_mapping_after_rows_and_columns_move():
    result = parse(monthly_rows(header=11, columns='DEFGHIJKLMNO'))
    products = by_product(result)
    assert products[DRS002]['quantities'][2:4] == [7000, 6000]
    assert products[P081]['quantities'][9] == 11000
    assert products[P309]['quantities'] == [123] * 12


def test_cf_mi03_source_sheet_has_priority_over_reference_totals():
    reference = monthly_rows()
    for row in reference.values():
        if row.get('A') == '501-RBTR':
            row['B'] = 80000
    result = parse(extra=[('Çalışma Günler', reference)])
    assert result['sheetName'] == 'SİPARİŞ'
    assert by_product(result)[C100]['quantities'][0] == 30000


def test_cf_mi04_working_days_sheet_is_supported_without_source_sheet():
    result = parse(name='Çalışma Günler')
    assert result['sheetName'] == 'Çalışma Günler'
    assert by_product(result)[DRS002]['quantities'][2:4] == [7000, 6000]


@pytest.mark.parametrize('label', ['501-RBTR', '003-RBCD', '001-RBCD', '001-NaP', '001-CtP', '481-HoP', '481-CtP/NaP', '424-HoP/CtP'])
def test_cf_mi05_missing_required_source_label_rejects(label):
    rows = monthly_rows()
    rows = {number: row for number, row in rows.items() if row.get('A') != label}
    with pytest.raises(OrderImportError):
        parse(rows)


def test_cf_mi06_duplicate_raw_label_rejects_even_when_values_match():
    rows = monthly_rows()
    end = next(number for number, row in rows.items() if row.get('A') == 'ÇF Total')
    rows[end + 1] = rows[end]
    rows[end] = dict(rows[9])
    with pytest.raises(OrderImportError):
        parse(rows)


@pytest.mark.parametrize('bad', [9007199254740992, ('SUM(X1:X2)', None)])
def test_cf_mi07_invalid_or_unconfirmed_raw_amount_rejects(bad):
    rows = monthly_rows()
    rows[9]['B'] = bad
    with pytest.raises(OrderImportError):
        parse(rows)


@pytest.mark.parametrize('zero_like', [None, '', '-', ' - ', '—', '–', 'NULL', 'null', '#N/A', 'geçersiz', -10])
def test_cf_mi07b_dash_blank_null_and_invalid_values_default_to_zero(zero_like):
    rows = monthly_rows()
    rows[9]['B'] = zero_like
    rows[10]['B'] = 0
    assert by_product(parse(rows))[C100]['quantities'][0] == 0


def test_cf_mi07c_dot_and_comma_formatted_integers_parse_without_bottlenecks():
    rows = monthly_rows()
    # Mix Turkish dots, English commas, trailing decimal zeros, and float noise on source rows.
    rows[9]['B'] = '451.200'
    rows[10]['B'] = '16,848'
    rows[9]['C'] = '518.400,00'
    rows[10]['C'] = '9,828.00'
    rows[9]['D'] = 499200.0
    rows[10]['D'] = 21060.0000001
    products = by_product(parse(rows))
    # Ocak: ceil((451200+16848)*1.03/15000)*15000 = 495000
    # Şubat: ceil((518400+9828)*1.03/15000)*15000 = 555000
    # Mart: ceil((499200+21060)*1.03/15000)*15000 = 540000
    assert products[C100]['quantities'][:3] == [495000, 555000, 540000]


def test_cf_mi28_operational_layout_without_day_row_and_with_410_and_gunluk_adet_imports():
    # Matches the approved operational Excel layout (no Day row, 410-RBTR at top, Günlük Adet at bottom, custom sheet name).
    rows = {
        1: {'A': '2026 YILI'},
        3: {'A': '2.11.2026', **dict(zip('BCDEFGHIJKLM', MONTHS))},
        4: {'A': '410-RBTR', **dict(zip('BCDEFGHIJKLM', ['86.400'] * 12))},
        5: {'A': '501-RBTR', 'B': '451.200', 'C': '518.400', 'D': '499.200', **{c: '-' for c in 'EFGHIJKLM'}},
        6: {'A': '481-HoP', 'B': '-', 'C': '9.600', 'D': '9.600', **{c: 'NULL' for c in 'EFGHIJKLM'}},
        7: {'A': '481-CtP/NaP', **{c: '-' for c in 'BCDEFGHIJKLM'}},
        8: {'A': '003-RBCD', 'B': '16.848', 'C': '9.828', 'D': '21.060', **{c: 0 for c in 'EFGHIJKLM'}},
        9: {'A': '001-RBCD', 'B': '4.212', 'C': '-', 'D': '4.212', **{c: 0 for c in 'EFGHIJKLM'}},
        10: {'A': '001-NaP', 'B': '-', 'C': '-', 'D': '1.755', **{c: 0 for c in 'EFGHIJKLM'}},
        11: {'A': '001-CtP', 'B': '3.510', 'C': '-', 'D': '-', **{c: 0 for c in 'EFGHIJKLM'}},
        12: {'A': '424-HoP/CtP', 'B': '-', 'C': '-', 'D': '6.000', **{c: 0 for c in 'EFGHIJKLM'}},
        13: {'A': 'DRS Total', **{c: 0 for c in 'BCDEFGHIJKLM'}},
        14: {'A': '309-RBTR', 'B': '483.840', 'C': '414.720', 'D': '432.000', **{c: 0 for c in 'EFGHIJKLM'}},
        15: {'A': '315-BaP', 'B': '34.560', 'C': '17.280', 'D': '34.560', **{c: 0 for c in 'EFGHIJKLM'}},
        16: {'A': '002-CtP', 'B': '-', 'C': '-', 'D': '32.500', **{c: 0 for c in 'EFGHIJKLM'}},
        17: {'A': '245-CtP', 'B': '32.500', 'C': '-', 'D': '-', **{c: 0 for c in 'EFGHIJKLM'}},
        18: {'A': 'C100 - DRS', **{c: 0 for c in 'BCDEFGHIJKLM'}},
        19: {'A': '002 - DRS', **{c: 0 for c in 'BCDEFGHIJKLM'}},
        20: {'A': '081 - DRS', **{c: 0 for c in 'BCDEFGHIJKLM'}},
        21: {'A': 'ÇF Total', **{c: 0 for c in 'BCDEFGHIJKLM'}},
        22: {'A': 'Günlük Adet', **{c: 0 for c in 'BCDEFGHIJKLM'}},
    }
    result = parse_order_xlsx(book([('2026 Plan', rows)]), allow_filter_monthly=True)
    assert result['year'] == 2026
    assert result['workingDays'] == [0.0] * 12
    products = by_product(result)
    assert products[C100]['quantities'][:3] == [495000, 555000, 540000]
    assert products[DRS002]['quantities'][:3] == [9000, 0, 7000]
    assert products[P081]['quantities'][:3] == [0, 11000, 18700]
    assert products[P309]['quantities'][:3] == [483840, 414720, 432000]


def test_cf_mi08_explicit_zero_is_valid_and_formula_cache_is_read_without_execution():
    rows = monthly_rows()
    rows[9]['B'] = ('THIS_IS_NOT_EXECUTED()', 0)
    rows[10]['B'] = 0
    assert by_product(parse(rows))[C100]['quantities'][0] == 0


def test_cf_mi09_safe_individual_values_cannot_overflow_derived_amount():
    rows = monthly_rows()
    rows[9]['B'] = 5000000000000000
    rows[10]['B'] = 5000000000000000
    with pytest.raises(OrderImportError):
        parse(rows)


def test_cf_mi10_exact_rounding_boundary_and_next_piece_are_distinct():
    rows = monthly_rows()
    # The approved 4% allowance gives 104000 at this exact boundary.
    rows[11]['B'] = 100000
    rows[12]['B'] = rows[13]['B'] = 0
    rows[11]['C'] = 100001
    rows[12]['C'] = rows[13]['C'] = 0
    result = by_product(parse(rows))[DRS002]['quantities']
    # This rule uses 4%, independently of C100's 3% allowance.
    assert result[:2] == [104000, 105000]


def test_cf_mi11_explicit_monthly_mode_does_not_change_simple_order_default():
    content = book([('Orders', {1: {'A': 'Tip No', 'B': 'Sipariş Adeti'}, 2: {'A': 'F.00V.P01.309', 'B': 123}})])
    result = parse_order_xlsx(content)
    assert result['format'] == 'simple-orders'
    assert result['rows'] == [{'product': P309, 'quantity': 123}]


def test_cf_mi12_monthly_workbook_is_not_implicitly_accepted_as_daily_or_piston():
    content = book([('SİPARİŞ', monthly_rows())])
    for options in [{}, {'allow_filter_daily': True}]:
        with pytest.raises(OrderImportError):
            parse_order_xlsx(content, **options)


def stock_rows(offset=0):
    # 18 October 2026. The fixed serial is independent of app date helpers.
    from datetime import date
    cutoff = (date(2026, 10, 18) - date(1899, 12, 30)).days
    return {
        31 + offset: {'A': cutoff, 'B': 2433084081, 'C': 'F.00V.P01.315', 'D': 2433084245},
        32 + offset: {'A': 'Teslimatı Gerçekleşen', 'B': 100, 'C': 200, 'D': 0},
        33 + offset: {'A': 'GKM önü', 'B': 300, 'C': 18000},
        34 + offset: {'A': 'Isıl işlem', 'B': 0, 'D': 400},
        35 + offset: {'A': 'Freze Önü', 'B': 500, 'C': 600},
        36 + offset: {'A': 'Taşlama Önü', 'B': 700},
        37 + offset: {'A': 'Toplam', 'B': 999999, 'C': 999999, 'D': 999999},
    }


@pytest.mark.parametrize('offset', [0, 9])
def test_cf_mi13_opening_count_uses_labels_maps_numeric_codes_and_blank_zero(offset):
    result = parse(extra=[('SİPARİŞ ŞABLONU', stock_rows(offset))])
    assert result['openingStock']['cutoffDate'] == '2026-10-18'
    rows = {row['product']: row for row in result['openingStock']['rows']}
    assert rows[P081] == {'product': P081, 'delivered': 100, 'visual': 300, 'heat': 0, 'milling': 500, 'grinding': 700}
    assert rows['F.00V.P01.315'] == {'product': 'F.00V.P01.315', 'delivered': 200, 'visual': 18000, 'heat': 0, 'milling': 600, 'grinding': 0}
    assert rows['2.433.084.245'] == {'product': '2.433.084.245', 'delivered': 0, 'visual': 0, 'heat': 400, 'milling': 0, 'grinding': 0}
    assert all(999999 not in row.values() for row in rows.values())


@pytest.mark.parametrize('bad', [-1, 0.5, 9007199254740992, ('SUM(B1:B2)', None)])
def test_cf_mi14_invalid_opening_count_rejects(bad):
    stock = stock_rows()
    stock[33]['B'] = bad
    with pytest.raises(OrderImportError):
        parse(extra=[('SİPARİŞ ŞABLONU', stock)])


def test_cf_mi15_stock_total_is_not_parsed_as_physical_stock():
    stock = stock_rows()
    stock[37]['B'] = ('INVALID_TOTAL()', None)
    result = parse(extra=[('SİPARİŞ ŞABLONU', stock)])
    assert result['openingStock']['rows'][0]['visual'] == 300


def test_cf_mi16_daily_import_mode_retains_its_existing_pair_sum():
    from datetime import date
    day = (date(2026, 10, 5) - date(1899, 12, 30)).days
    rows = {2: {'C': '309-RBTR', 'E': '309-RBTR'}, 3: {'C': 'Sipariş', 'D': 'Teslimat', 'E': 'Sipariş', 'F': 'Teslimat'},
            4: {'B': day, 'C': 100, 'D': 20, 'E': 50, 'F': 10}}
    result = parse_order_xlsx(book([('Sevkiyat Planı', rows)]), allow_filter_daily=True)
    assert result['format'] == 'filter-daily'
    assert result['dailyRows'] == [{'date': '2026-10-05', 'product': P309, 'ordered': 150, 'delivered': 30, 'sourceCells': ['C4', 'D4', 'E4', 'F4']}]


def test_cf_mi17_endpoint_rejects_monthly_mode_in_piston_area_before_parser(monkeypatch):
    import asyncio
    from fastapi import HTTPException, UploadFile
    from app import main
    from app.production_area import production_area
    token = production_area.set('torna')
    monkeypatch.setattr(main, 'parse_order_xlsx', lambda *args, **kwargs: pytest.fail('Wrong area reached the parser'))
    try:
        with pytest.raises(HTTPException) as error:
            asyncio.run(main.preview_order_import(UploadFile(filename='synthetic.xlsx', file=BytesIO(b'synthetic')), monthly=True, _=None))
        assert error.value.status_code == 422
    finally:
        production_area.reset(token)


def test_cf_mi18_duplicate_stock_product_rejects():
    stock = stock_rows()
    stock[31]['D'] = '2.433.084.081'
    with pytest.raises(OrderImportError):
        parse(extra=[('SİPARİŞ ŞABLONU', stock)])


def test_cf_mi19_missing_stock_stage_cannot_be_silently_zero():
    stock = stock_rows()
    del stock[34]
    with pytest.raises(OrderImportError):
        parse(extra=[('SİPARİŞ ŞABLONU', stock)])


@pytest.mark.parametrize('bad_date', [None, '18/10/2026', 0, 46313.5])
def test_cf_mi20_invalid_stock_cutoff_rejects(bad_date):
    stock = stock_rows()
    stock[31]['A'] = bad_date
    with pytest.raises(OrderImportError):
        parse(extra=[('SİPARİŞ ŞABLONU', stock)])


def test_cf_mi21_english_preamble_and_later_comparison_headers_are_not_second_sources():
    rows = monthly_rows()
    rows[1] = {'A': 'Month', **dict(zip('BCDEFGHIJKLM', ['January', 'Fabruary', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']))}
    rows[40] = {'A': 'Comparison', **dict(zip('BCDEFGHIJKLM', MONTHS))}
    rows[41] = {'A': 'C100 - DRS', **dict(zip('BCDEFGHIJKLM', [999999] * 12))}
    result = by_product(parse(rows))
    assert result[C100]['quantities'] == [30000] * 12
    assert result[DRS002]['quantities'][2:4] == [7000, 6000]


def test_cf_mi22_c100_and_081_round_only_after_the_complete_allowance():
    rows = monthly_rows()
    rows[9]['B'] = 1500000
    rows[10]['B'] = 0
    rows[9]['C'] = 1500001
    rows[10]['C'] = 0
    rows[14]['B'] = 25000
    rows[15]['B'] = rows[16]['B'] = 0
    rows[14]['C'] = 25001
    rows[15]['C'] = rows[16]['C'] = 0
    result = by_product(parse(rows))
    assert result[C100]['quantities'][:2] == [1545000, 1560000]
    assert result[P081]['quantities'][:2] == [28600, 29700]


def test_cf_mi23_duplicate_month_header_cannot_silently_select_the_last_column():
    rows = monthly_rows()
    for row in rows.values():
        if 'B' in row:
            row['N'] = row['B']
        if row.get('A') == '501-RBTR':
            row['N'] = 50000
    with pytest.raises(OrderImportError):
        parse(rows)


def test_cf_mi24_normalized_duplicate_source_sheets_reject_ambiguous_source():
    first = monthly_rows()
    second = monthly_rows()
    second[9]['B'] = 80000
    content = book([('SİPARİŞ', first), ('sipariş', second)])
    with pytest.raises(OrderImportError):
        parse_order_xlsx(content, allow_filter_monthly=True)


def test_cf_mi25_stock_header_is_found_by_date_and_codes_with_a_blank_separator():
    stock = stock_rows()
    stock = {number + 1 if number >= 32 else number: row for number, row in stock.items()}
    result = parse(extra=[('SİPARİŞ ŞABLONU', stock)])
    assert result['openingStock']['cutoffDate'] == '2026-10-18'
    assert result['openingStock']['rows'][0]['visual'] == 300


def test_cf_mi26_template_sheet_is_explicit_source_and_overrides_legacy_source():
    template=monthly_rows(); template[9]['B']=80000
    result=parse(extra=[('SİPARİŞ ŞABLONU',{**template,**stock_rows()})])
    assert result['sheetName']=='SİPARİŞ ŞABLONU'
    assert by_product(result)[C100]['quantities'][0]==90000
    assert result['openingStock']['cutoffDate']=='2026-10-18'


def test_cf_mi27_downloadable_blank_template_round_trips_all_sources_and_derived_rows():
    from app.filter_monthly_import import build_filter_monthly_template
    result=parse_order_xlsx(build_filter_monthly_template(2027),allow_filter_monthly=True)
    assert result['sheetName']=='SİPARİŞ ŞABLONU'
    assert result['year']==2027
    assert len(result['rows'])==7
    assert all(row['quantities']==[0]*12 for row in result['rows'])
    with pytest.raises(OrderImportError):build_filter_monthly_template(1999)


def test_fb_template01_month_totals_include_each_group_once_and_year_is_first():
    from io import BytesIO
    from openpyxl import load_workbook
    from openpyxl.utils import get_column_letter
    from app.filter_monthly_import import build_filter_monthly_template
    content = build_filter_monthly_template(2027)
    workbook = load_workbook(BytesIO(content))
    sheet = workbook.active
    assert sheet['A1'].value == '2027 YILI'
    assert sheet['A5'].value == '410-RBTR'
    assert sheet['A14'].value == 'DRS Total'
    assert sheet['A19'].value == 'C100 - DRS'
    assert sheet['A20'].value == '002 - DRS'
    assert sheet['A21'].value == '081 - DRS'
    assert sheet['A22'].value == 'ÇF Total'
    assert sheet['A23'].value == 'Günlük Adet'
    for index in range(2, 14):
        col = get_column_letter(index)
        assert sheet.cell(14, index).value == f'=SUM({col}6:{col}13)'
        assert sheet.cell(22, index).value == f'=SUM({col}15:{col}21)'
        # Independent monthly example: eight green DRS sources (rows 6-13), four orange direct products (rows 15-18).
        for row in range(6, 14): sheet.cell(row, index, 100)
        for row in range(15, 19): sheet.cell(row, index, 10)
    # Distinct colors: blue (410-RBTR), green (DRS source), orange (direct), grey (derived DRS), dark navy (ÇF Total).
    assert len({sheet['B5'].fill.fgColor.rgb, sheet['B6'].fill.fgColor.rgb, sheet['B15'].fill.fgColor.rgb, sheet['B19'].fill.fgColor.rgb, sheet['B22'].fill.fgColor.rgb}) == 5
    output = BytesIO(); workbook.save(output)
    result = parse_order_xlsx(output.getvalue(), allow_filter_monthly=True)
    # 800 source pieces; 15,000 + 1,000 + 1,100 derived and 4 x 10 direct.
    assert sum(row['quantities'][0] for row in result['rows']) == 17140
    assert all(row['quantities'] == [row['quantities'][0]] * 12 for row in result['rows'])
