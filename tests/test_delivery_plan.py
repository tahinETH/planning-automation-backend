import os
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

os.environ["DATABASE_PATH"] = "/tmp/selsa-planlama-feedback-test.sqlite"
os.environ["UPLOAD_DIR"] = "/tmp/selsa-planlama-feedback-uploads"
os.environ["ADMIN_PASSWORD"] = "test-password"
os.environ["APP_SESSION_SECRET"] = "test-session-secret-that-is-long-enough"

from fastapi.testclient import TestClient
from openpyxl import load_workbook

from app.delivery_plan import build_delivery_plan
from app.main import app


def test_delivery_plan_uses_single_category_and_template_structure():
    template = Path(__file__).resolve().parents[1] / "teslimat_plani.xlsx"
    content = build_delivery_plan(template, {
        "startDate": "2026-07-20",
        "endDate": "2026-08-30",
        "category": "Üretim",
        "weeks": [{"label": f"KW{week}"} for week in range(30, 36)],
        "rows": [{"product": "R902745116", "orderQuantity": 5760, "weeklyQuantities": [1920, 1920, 1920, 0, 0, 0]}],
    })
    workbook = load_workbook(BytesIO(content), data_only=False)
    sheet = workbook["Teslimat Planı"]
    assert sheet["C4"].value == "Üretim"
    assert sheet["B7"].value == "R902745116"
    assert sheet["C7"].value == "=SUM(H7:M7)"
    assert sheet["D7"].value == 5760
    assert [sheet.cell(7, column).value for column in range(8, 14)] == [1920, 1920, 1920, 0, 0, 0]
    assert sheet["O4"].value is None
    assert not list(workbook.defined_names)
    with ZipFile(BytesIO(content)) as archive:
        workbook_xml = archive.read("xl/workbook.xml").decode("utf-8")
    assert "#REF!" not in workbook_xml


def test_delivery_plan_endpoint_returns_an_excel_download():
    payload = {
        "startDate": "2026-07-20", "endDate": "2026-08-30", "category": "Üretim",
        "weeks": [{"label": f"KW{week}"} for week in range(30, 36)],
        "rows": [{"product": "R902745116", "orderQuantity": 5760, "weeklyQuantities": [1920, 1920, 1920, 0, 0, 0]}],
    }
    with TestClient(app) as client:
        assert client.post("/api/delivery-plan/export", json=payload).status_code == 401
        login = client.post("/api/auth/login", json={"password": "test-password"})
        headers = {"Authorization": f"Bearer {login.json()['token']}"}
        response = client.post("/api/delivery-plan/export", headers=headers, json=payload)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        assert response.content.startswith(b"PK")


def test_delivery_plan_expands_when_more_than_template_rows_are_active():
    template = Path(__file__).resolve().parents[1] / "teslimat_plani.xlsx"
    rows = [{"product": f"P{index:03d}", "orderQuantity": index, "weeklyQuantities": [index, 0, 0, 0, 0, 0]} for index in range(1, 51)]
    content = build_delivery_plan(template, {
        "startDate": "2026-07-20", "endDate": "2026-08-30", "category": "Üretim",
        "weeks": [{"label": f"KW{week}"} for week in range(30, 36)], "rows": rows,
    })
    sheet = load_workbook(BytesIO(content), data_only=False)["Teslimat Planı"]
    assert sheet["B56"].value == "P050"
    assert sheet["B57"].value == "Toplam"
    assert sheet["C57"].value == "=SUM(C7:C56)"


def test_delivery_plan_expands_week_columns_beyond_the_original_six():
    template = Path(__file__).resolve().parents[1] / "teslimat_plani.xlsx"
    quantities = [100] * 9
    content = build_delivery_plan(template, {
        "startDate": "2026-06-22", "endDate": "2026-08-23", "category": "Üretim",
        "weeks": [{"label": f"KW{week}"} for week in range(26, 35)],
        "rows": [{"product": "P001", "orderQuantity": 900, "weeklyQuantities": quantities}],
    })
    sheet = load_workbook(BytesIO(content), data_only=False)["Teslimat Planı"]
    assert sheet["P6"].value == "KW34"
    assert sheet["P7"].value == 100
    assert sheet["C7"].value == "=SUM(H7:P7)"
    assert sheet.auto_filter.ref == "B6:P49"
