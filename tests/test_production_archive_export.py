import os
from io import BytesIO

os.environ["DATABASE_PATH"] = "/tmp/selsa-planlama-feedback-test.sqlite"
os.environ["UPLOAD_DIR"] = "/tmp/selsa-planlama-feedback-uploads"
os.environ["ADMIN_PASSWORD"] = "test-password"
os.environ["APP_SESSION_SECRET"] = "test-session-secret-that-is-long-enough"

from fastapi.testclient import TestClient
from openpyxl import load_workbook

from app.main import app
from app.production_archive_export import build_production_archive_workbook


def archive_payload():
    return {
        "generatedAt": "2026-08-07T09:00:00Z",
        "status": "semi-finished",
        "filtered": True,
        "totalAvailable": 4,
        "rows": [
            {
                "completedAt": "2026-08-06",
                "archivedAt": "2026-08-06T18:20:00Z",
                "machineId": "C-01",
                "machineName": "CITIZEN 1",
                "workOrder": "320-1",
                "product": "R902740",
                "setupFamily": "piston",
                "process": "turning",
                "completedQuantity": 1920,
                "plannedStart": "2026-08-01",
                "plannedEnd": "2026-08-05",
                "deliveryDate": "",
            },
            {
                "completedAt": "2026-08-07",
                "archivedAt": "2026-08-07T11:00:00Z",
                "machineId": "C-02",
                "machineName": "CITIZEN 2",
                "workOrder": "321-1",
                "product": "R902741",
                "setupFamily": "center-pin",
                "process": "drilling",
                "completedQuantity": 960,
                "plannedStart": "2026-08-05",
                "plannedEnd": "2026-08-07",
                "deliveryDate": "",
            },
        ],
    }


def test_production_archive_workbook_contains_visible_rows_and_summary():
    workbook = load_workbook(BytesIO(build_production_archive_workbook(archive_payload())))
    sheet = workbook["Üretim Arşivi"]
    assert sheet["A1"].value == "SELSA  ·  ÜRETİM ARŞİVİ"
    assert sheet["A6"].value == 2
    assert sheet["C6"].value == 2880
    assert sheet["G6"].value == "Filtreli"
    assert sheet["A10"].value == "2026-08-06"
    assert sheet["E10"].value == "R902740"
    assert sheet["F10"].value == "Piston"
    assert sheet["G11"].value == "Delme"
    assert sheet.auto_filter.ref == "A9:K11"
    assert sheet.freeze_panes == "A9"


def test_production_archive_endpoint_is_authenticated_and_returns_excel():
    payload = archive_payload()
    with TestClient(app) as client:
        assert client.post("/api/production-archive/export", json=payload).status_code == 401
        login = client.post("/api/auth/login", json={"password": "test-password"})
        headers = {"Authorization": f"Bearer {login.json()['token']}"}
        response = client.post("/api/production-archive/export", headers=headers, json=payload)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        assert "Uretim_Arsivi_semi-finished" in response.headers["content-disposition"]
        assert response.content.startswith(b"PK")
