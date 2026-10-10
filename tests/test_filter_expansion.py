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


def daily_workbook(*, bad_formula=False, duplicate=False, bad_quantity=None):
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
    return stream.getvalue()


def test_cf_i04_daily_parser_merges_pairs_and_keeps_source_cells_without_executing_macros():
    result = parse_order_xlsx(daily_workbook(), allow_filter_daily=True)
    assert result["dailyRows"] == [{"date": "2026-10-05", "product": "F.00V.P01.309", "ordered": 150, "delivered": 30, "sourceCells": ["C4", "D4", "E4", "F4"]}]
    with pytest.raises(OrderImportError):
        parse_order_xlsx(daily_workbook())
    for options in [{"bad_formula": True}, {"duplicate": True}, *[{"bad_quantity": value} for value in [-1, 1.5, "NaN", "Infinity", 9007199254740992]]]:
        with pytest.raises(OrderImportError):
            parse_order_xlsx(daily_workbook(**options), allow_filter_daily=True)


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
