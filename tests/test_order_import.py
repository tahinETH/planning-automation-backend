from __future__ import annotations

import os
import zipfile
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

os.environ["DATABASE_PATH"] = "/tmp/selsa-planlama-feedback-test.sqlite"
os.environ["UPLOAD_DIR"] = "/tmp/selsa-planlama-feedback-uploads"
os.environ["ADMIN_PASSWORD"] = "test-password"
os.environ["APP_SESSION_SECRET"] = "test-session-secret-that-is-long-enough"

from fastapi.testclient import TestClient

from app.main import app
from app.order_import import OrderImportError, parse_order_xlsx


def workbook_bytes(rows: list[tuple[str, str]], headers: tuple[str, str] = ("Tip no", "Sipariş Adeti")) -> bytes:
    values = [headers, *rows]
    xml_rows = []
    for row_index, row in enumerate(values, 1):
        cells = []
        for column, value in zip(("A", "B"), row):
            if column == "B" and row_index > 1 and value:
                cells.append(f'<c r="{column}{row_index}"><v>{value}</v></c>')
            else:
                cells.append(f'<c r="{column}{row_index}" t="inlineStr"><is><t>{value}</t></is></c>')
        xml_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    sheet = f'<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{"".join(xml_rows)}</sheetData></worksheet>'
    output = BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("xl/workbook.xml", '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Sayfa1" sheetId="1" r:id="rId1"/></sheets></workbook>')
        archive.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/></Relationships>')
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
    return output.getvalue()


def confirmed_overview_bytes(week_headers: tuple[str, ...] = ("CW 30.2026", "CW 31.2026")) -> bytes:
    def column_name(index: int) -> str:
        value = ""
        while index:
            index, remainder = divmod(index - 1, 26)
            value = chr(65 + remainder) + value
        return value

    columns = {
        "A": "Date",
        "C": "Material",
        "E": "Family of Parts",
        "J": "Unit",
        "Q": "Available quantity",
        "R": "Filter",
        "S": f"< {week_headers[0]}",
    }
    for index, header in enumerate(week_headers):
        columns[column_name(20 + index)] = header
    rows = [
        {
            "A": "20.07.2026",
            "C": "R902745138",
            "E": "PISTON",
            "J": "ST",
            "Q": 5781,
            "R": "Balance (confirmed)",
            "S": 5781,
            "T": -6891,
            "U": -6891,
        },
        {
            "A": "20.07.2026",
            "C": "R902745116",
            "E": "PISTON",
            "J": "ST",
            "Q": 0,
            "R": "Balance (confirmed)",
            "S": -1920,
            "T": -5760,
            "U": -5760,
        },
        {
            "A": "20.07.2026",
            "C": "R-STOCK",
            "E": "CENTER PIN",
            "J": "ST",
            "Q": 100,
            "R": "Balance (confirmed)",
            "S": 100,
            "T": 50,
            "U": 20,
        },
    ]
    for row, balance in zip(rows, (-6891, -5760, 20)):
        for index in range(len(week_headers)):
            row[column_name(20 + index)] = balance

    def cell(reference: str, value: object) -> str:
        if isinstance(value, str):
            return f'<c r="{reference}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
        return f'<c r="{reference}"><v>{value}</v></c>'

    xml_rows = [
        f'<row r="1">{"".join(cell(f"{column}1", value) for column, value in columns.items())}</row>'
    ]
    for row_number, row in enumerate(rows, 2):
        xml_rows.append(f'<row r="{row_number}">{"".join(cell(f"{column}{row_number}", value) for column, value in row.items())}</row>')
    main_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    sheet = f'<?xml version="1.0"?><worksheet xmlns="{main_ns}"><sheetData>{"".join(xml_rows)}</sheetData></worksheet>'
    output = BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("xl/workbook.xml", f'<?xml version="1.0"?><workbook xmlns="{main_ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="3. Overview (confirmed)" sheetId="1" r:id="rId1"/></sheets></workbook>')
        archive.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/></Relationships>')
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
    return output.getvalue()


def test_parses_order_workbook_and_ignores_blank_separators():
    parsed = parse_order_xlsx(workbook_bytes([("R902745116", "3840"), ("", ""), ("R902719052", "0")]))
    assert parsed["rows"] == [{"product": "R902745116", "quantity": 3840}, {"product": "R902719052", "quantity": 0}]
    assert parsed["summary"] == {"productCount": 2, "orderCount": 1, "totalQuantity": 3840, "ignoredBlankRows": 1}


def test_parses_confirmed_overview_as_iso_week_demand_with_monday_and_saturday_dates():
    parsed = parse_order_xlsx(confirmed_overview_bytes())

    assert parsed["format"] == "confirmed-overview"
    assert parsed["calculationModel"] == "net-shortage-v1"
    assert parsed["sheetName"] == "3. Overview (confirmed)"
    assert parsed["snapshotDate"] == "2026-07-20"
    assert parsed["baselineDueDate"] == "2026-07-18"
    assert parsed["summary"] == {
        "productCount": 3,
        "orderCount": 2,
        "totalQuantity": 12651,
        "openingStock": 5881,
        "priorDemand": 1920,
        "firstWeekRequirement": 12651,
        "lastWeekRequirement": 12651,
        "weekCount": 2,
        "firstWeek": "2026-W30",
        "lastWeek": "2026-W31",
        "ignoredBlankRows": 0,
    }
    assert parsed["weeks"][0] == {
        "isoYear": 2026,
        "isoWeek": 30,
        "id": "2026-W30",
        "label": "CW 30.2026",
        "weekStart": "2026-07-20",
        "weekEnd": "2026-07-25",
        "quantity": 10731,
    }
    first = parsed["products"][0]
    assert first["availableQuantity"] == 5781
    assert first["priorDemand"] == 0
    assert first["weeklyDemands"][0]["requiredQuantity"] == 6891
    assert first["weeklyDemands"][0]["quantity"] == 6891
    second = parsed["products"][1]
    assert second["priorDemand"] == 1920
    assert second["weeklyDemands"][0]["quantity"] == 3840
    stock_surplus = parsed["products"][2]
    assert stock_surplus["totalDemand"] == 0
    assert all(week["quantity"] == 0 for week in stock_surplus["weeklyDemands"])


def test_rejects_non_consecutive_confirmed_overview_weeks():
    try:
        parse_order_xlsx(confirmed_overview_bytes(("CW 30.2026", "CW 32.2026")))
        assert False, "week gap should fail"
    except OrderImportError as error:
        assert "kesintisiz" in str(error)


def test_parses_52_consecutive_iso_weeks_across_year_boundary():
    first_monday = date(2026, 9, 28)
    headers = []
    for offset in range(52):
        iso = (first_monday + timedelta(weeks=offset)).isocalendar()
        headers.append(f"CW {iso.week}.{iso.year}")
    parsed = parse_order_xlsx(confirmed_overview_bytes(tuple(headers)))
    assert parsed["summary"]["weekCount"] == 52
    assert parsed["weeks"][0]["id"] == "2026-W40"
    assert parsed["weeks"][0]["weekStart"] == "2026-09-28"
    assert parsed["weeks"][-1]["id"] == "2027-W38"
    assert parsed["weeks"][-1]["weekEnd"] == "2027-09-25"


def test_rejects_duplicate_products_and_wrong_headers():
    try:
        parse_order_xlsx(workbook_bytes([("R902745116", "1"), ("R902745116", "2")]))
        assert False, "duplicate product should fail"
    except OrderImportError as error:
        assert "tekrar ediyor" in str(error)
    try:
        parse_order_xlsx(workbook_bytes([("R902745116", "1")], headers=("Ürün", "Miktar")))
        assert False, "wrong headers should fail"
    except OrderImportError as error:
        assert "Beklenen kolonlar" in str(error)


def test_preview_endpoint_requires_auth_and_returns_summary():
    Path(os.environ["DATABASE_PATH"]).unlink(missing_ok=True)
    content = workbook_bytes([("R902745116", "3840"), ("R902719052", "0")], headers=("Tip no", "Plan Adet"))
    with TestClient(app) as client:
        assert client.post("/api/order-imports/preview", files={"file": ("siparisler.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}).status_code == 401
        login = client.post("/api/auth/login", json={"password": "test-password"})
        headers = {"Authorization": f"Bearer {login.json()['token']}"}
        response = client.post("/api/order-imports/preview", headers=headers, files={"file": ("siparisler.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        assert response.status_code == 200
        assert response.json()["fileName"] == "siparisler.xlsx"
        assert response.json()["summary"]["totalQuantity"] == 3840


def test_order_import_history_persists_dataset_for_rollback():
    Path(os.environ["DATABASE_PATH"]).unlink(missing_ok=True)
    with TestClient(app) as client:
        login = client.post("/api/auth/login", json={"password": "test-password"})
        headers = {"Authorization": f"Bearer {login.json()['token']}"}
        payload = {
            "id": "demand-2026-07-26",
            "importedAt": "2026-07-26T12:00:00Z",
            "sourceFile": "Selsa_yillik.xlsx",
            "snapshotDate": "2026-07-20",
            "dataset": {"format": "confirmed-overview", "weeks": [], "products": []},
            "summary": {"productCount": 0, "weekCount": 0, "totalDemand": 0},
        }
        created = client.post("/api/order-imports/history", headers=headers, json=payload)
        assert created.status_code == 201
        listed = client.get("/api/order-imports/history", headers=headers)
        assert listed.status_code == 200
        assert listed.json()[0]["id"] == payload["id"]
        assert listed.json()[0]["dataset"]["format"] == "confirmed-overview"
