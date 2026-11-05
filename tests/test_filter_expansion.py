from copy import deepcopy
from io import BytesIO
from zipfile import ZipFile
from datetime import date
from xml.sax.saxutils import escape
import pytest
from app.order_import import parse_order_xlsx, OrderImportError
from app.stock_planning import validate_stock_planning
from app import database
from app.production_area import production_area
from app.config import settings


def test_cf_i05_staging_proxy_accepts_the_app_file_limit_with_multipart_overhead():
    from pathlib import Path
    import re
    from app.order_import import MAX_XLSX_BYTES

    config = (Path(__file__).parents[1] / 'deploy/api-staging.planning.hfgok.com.nginx').read_text()
    block = re.search(r'location\s*=\s*/api/order-imports/preview\s*\{([^}]+)\}', config)
    assert block, 'The order upload needs an explicit staging proxy allowance.'
    limit = re.search(r'client_max_body_size\s+(\d+)m;', block.group(1))
    assert limit and MAX_XLSX_BYTES + 64 * 1024 <= int(limit.group(1)) * 1024 * 1024 <= 2 * MAX_XLSX_BYTES
    assert 'proxy_pass http://127.0.0.1:8003;' in block.group(1)
    assert 'proxy_set_header X-Forwarded-Proto $scheme;' in block.group(1)


def daily_workbook(*, bad_formula=False, duplicate=False, bad_quantity=None, monthly=None):
    def cell(ref, value):
        if isinstance(value, (int, float)):
            return f'<c r="{ref}"><v>{value}</v></c>'
        return f'<c r="{ref}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
    day = (date(2026, 10, 5) - date(1899, 12, 30)).days
    cells = [cell("C2", "309-RBTR"), cell("E2", "309-RBTR"), cell("C3", "Sipariş"), cell("D3", "Teslimat"), cell("E3", "Sipariş"), cell("F3", "Teslimat"), cell("B4", day), cell("C4", bad_quantity if bad_quantity is not None else 100), cell("D4", 20), cell("E4", 50), cell("F4", 10)]
    if duplicate:
        cells.extend([cell("B5", day), cell("C5", 1)])
    if bad_formula:
        cells.append('<c r="C6"><f>SUM(A1:A2)</f></c>')
    stream = BytesIO()
    with ZipFile(stream, "w") as archive:
        archive.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Sevkiyat Planı " sheetId="1" r:id="rId1"/></sheets></workbook>')
        archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        archive.writestr("xl/worksheets/sheet1.xml", f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row>{"".join(cells)}</row></sheetData></worksheet>')
        archive.writestr("xl/vbaProject.bin", b"not executed")
        if monthly is not None:
            # Styles 1 and 2 are the workbook's orange and grey theme fills; 0 is unfilled.
            archive.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Sevkiyat Planı " sheetId="1" r:id="rId1"/><sheet name="Çalışma Günler" sheetId="2" r:id="rId2"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Target="worksheets/sheet2.xml"/></Relationships>')
            archive.writestr("xl/styles.xml", '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fills><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FFFF9900"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor theme="2" tint="-0.5"/></patternFill></fill></fills><cellXfs><xf fillId="0"/><xf fillId="1"/><xf fillId="2"/></cellXfs></styleSheet>')
            columns = "BCDEFGHIJKLM"
            months = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
            def line(number, label, values, style=0):
                return [cell(f"A{number}", label).replace("<c ", f'<c s="{style}" ', 1), *[cell(f"{column}{number}", value) for column, value in zip(columns, values)]]
            sheet = [*line(2, "Day", monthly.get("days", [26, 24, 23, 25, 19, 26, 26, 26, 26, 25, 25, 26.5])), cell("A6", "2026 YILI"), *line(8, "tarih", months),
                     *line(9, "501-RBTR", [9] * 12), *line(18, "DRS Total", [9] * 12),
                     *line(19, "309-RBTR", [100] * 12, monthly.get("external_style", 1)), *line(23, monthly.get("internal_label", "C100 - DRS"), [200] * 11 + [0], 2), *line(26, "ÇF Total", [300] * 12)]
            archive.writestr("xl/worksheets/sheet2.xml", f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row>{"".join(sheet)}</row></sheetData></worksheet>')
    return stream.getvalue()


def test_cf_i08_working_days_sheet_reads_days_and_classifies_rows_by_fill_colour():
    assert "monthlyPlan" not in parse_order_xlsx(daily_workbook(), allow_filter_daily=True)
    plan = parse_order_xlsx(daily_workbook(monthly={}), allow_filter_daily=True)["monthlyPlan"]
    assert plan["year"] == 2026 and plan["workingDays"][4] == 19 and plan["workingDays"][11] == 26.5
    # Rows above DRS Total and the ÇF Total line itself are not Çubuk Filtre product rows.
    assert [(row["label"], row["product"], row["kind"], row["quantities"][0], row["quantities"][11]) for row in plan["rows"]] == [
        ("309-RBTR", "F.00V.P01.309", "external", 100, 100), ("C100 - DRS", "F.00V.C15.100", "internal", 200, 0)]
    for broken in [{"external_style": 0}, {"internal_label": "999 - DRS"}, {"days": [32] + [26] * 11}, {"days": [26.25] + [26] * 11}]:
        with pytest.raises(OrderImportError):
            parse_order_xlsx(daily_workbook(monthly=broken), allow_filter_daily=True)


def test_cf_i04_daily_parser_merges_pairs_and_keeps_source_cells_without_executing_macros():
    result = parse_order_xlsx(daily_workbook(), allow_filter_daily=True)
    assert result["dailyRows"] == [{"date": "2026-10-05", "product": "F.00V.P01.309", "ordered": 150, "delivered": 30, "sourceCells": ["C4", "D4", "E4", "F4"]}]
    with pytest.raises(OrderImportError):
        parse_order_xlsx(daily_workbook())
    for options in [{"bad_formula": True}, {"duplicate": True}, *[{"bad_quantity": value} for value in [-1, 1.5, "NaN", "Infinity", 9007199254740992]]]:
        with pytest.raises(OrderImportError):
            parse_order_xlsx(daily_workbook(**options), allow_filter_daily=True)


def test_cf_i09_saved_working_days_are_validated_for_the_filter_area_only():
    seed = stock_seed()
    seed["filterMonthlyPlan"] = {"sheetName": "Çalışma Günler", "year": 2026, "workingDays": [26] * 11 + [26.5], "sourceFile": "x.xlsm", "importedAt": "2026-10-12T09:00:00Z",
                                 "rows": [{"label": "C100 - DRS", "product": "F.00V.C15.100", "kind": "internal", "quantities": [1] * 12, "sourceRow": 23}]}
    validate_stock_planning(seed)
    for mutate in [lambda plan: plan.update(workingDays=[26] * 11), lambda plan: plan["rows"][0].update(kind="other"), lambda plan: plan["rows"][0].update(product="UNKNOWN"),
                   lambda plan: plan["rows"][0].update(quantities=[-1] * 12), lambda plan: plan.update(year="2026")]:
        broken = deepcopy(seed)
        mutate(broken["filterMonthlyPlan"])
        with pytest.raises(ValueError):
            validate_stock_planning(broken)
    seed["productionArea"] = "torna"
    with pytest.raises(ValueError):
        validate_stock_planning(seed)


def stock_seed():
    return {"productionArea": "cubuk-filtre", "orders": [], "machines": [], "products": [{"product": "F.00V.C15.100", "setupFamily": "cubuk-filtre"}], "filterWaitShifts": 1,
            "processStockSettings": {"version": 1, "limits": [{"groupId": key, "min": 0, "max": 1000} for key in ["form-front", "mill-front", "visual-front", "warehouse"]], "scrap": [], "openingDate": "2026-10-05", "opening": [{"groupId": "form-front", "product": "F.00V.C15.100", "quantity": 1000}]}}


def test_stk_p01_version_admin_atomicity_and_area_isolation(tmp_path, monkeypatch):
    monkeypatch.setitem(settings.__dict__, "database_path", tmp_path / "state.sqlite")
    token = production_area.set("cubuk-filtre")
    try:
        database.init_database()
        seed = stock_seed()
        saved = database.save_planning_state(seed, can_manage_settings=True, stock_planning_version=1)
        assert database.planning_state()["seed"] == saved["seed"]
        bad = deepcopy(saved["seed"]); bad["processStockSettings"]["limits"][0]["max"] = -1
        with pytest.raises(ValueError):
            database.save_planning_state(bad, saved["updatedAt"], can_manage_settings=True, stock_planning_version=1)
        changed = deepcopy(saved["seed"]); changed["filterWaitShifts"] = 2
        with pytest.raises(database.ProtectedSettingsChange):
            database.save_planning_state(changed, saved["updatedAt"], stock_planning_version=1)
        legacy = deepcopy(seed); legacy.pop("processStockSettings"); legacy.pop("filterWaitShifts")
        with pytest.raises(ValueError, match="yenileyin"):
            database.save_planning_state(legacy, saved["updatedAt"], force=True, can_manage_settings=True)
        assert database.planning_state()["seed"] == saved["seed"]
        other = production_area.set("torna")
        try:
            database.init_database()
            assert database.planning_state() is None
        finally:
            production_area.reset(other)
    finally:
        production_area.reset(token)


@pytest.mark.parametrize("mutation", [lambda s: s.update(filterWaitShifts=True), lambda s: s["processStockSettings"]["opening"].append(s["processStockSettings"]["opening"][0]), lambda s: s["processStockSettings"]["opening"][0].update(quantity=1.5), lambda s: s["processStockSettings"]["scrap"].append({"groupId": "form-front", "product": "F.00V.C15.100", "percent": float("nan")})])
def test_stk_p02_invalid_stock_values(mutation):
    seed = stock_seed(); mutation(seed)
    with pytest.raises(ValueError):
        validate_stock_planning(seed)


def test_stk_r01_ravi_reads_saved_stock_and_daily_rows_with_bounded_source():
    from app.ravi.tools import Inspect, inspect_state
    seed = stock_seed()
    seed['dailyCustomerDemand'] = {'fileName': 'synthetic.xlsm', 'sheetName': 'Sevkiyat Planı', 'snapshotDate': '2026-10-05', 'dailyRows': [{'product': 'F.00V.C15.100', 'date': '2026-10-05', 'ordered': i, 'delivered': 0} for i in range(55)]}
    snapshot = {'seed': seed, 'updatedAt': '2026-10-05T09:00:00Z'}
    stock = inspect_state(snapshot, Inspect(collection='process_stock'))
    assert stock['source'] == 'persisted-server'
    assert stock['openingDate'] == '2026-10-05'
    assert stock['rows'][-1]['quantity'] == 1000
    daily = inspect_state(snapshot, Inspect(collection='daily_demand', offset=20))
    assert len(daily['rows']) == 12
    assert daily['nextOffset'] == 32
    assert daily['rows'][0]['ordered'] == 20
    assert daily['workbookSource']['fileName'] == 'synthetic.xlsm'
    assert daily['productionArea'] == 'cubuk-filtre'
