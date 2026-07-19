from __future__ import annotations

import os
import zipfile
from io import BytesIO
from pathlib import Path

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


def test_parses_order_workbook_and_ignores_blank_separators():
    parsed = parse_order_xlsx(workbook_bytes([("R902745116", "3840"), ("", ""), ("R902719052", "0")]))
    assert parsed["rows"] == [{"product": "R902745116", "quantity": 3840}, {"product": "R902719052", "quantity": 0}]
    assert parsed["summary"] == {"productCount": 2, "orderCount": 1, "totalQuantity": 3840, "ignoredBlankRows": 1}


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
