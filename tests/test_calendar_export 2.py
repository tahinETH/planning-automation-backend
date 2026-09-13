from io import BytesIO

from openpyxl import load_workbook

from app.calendar_export import build_calendar_event_workbook


def test_calendar_event_export_contains_filtered_operational_rows():
    payload = {
        "generatedAt": "2026-09-02T10:00:00Z",
        "rows": [
            {"eventType": "maintenance", "process": "turning", "workCenterId": "C-01", "workCenterName": "Citizen", "name": "Yıllık bakım", "startDate": "2026-08-20", "endDate": "2026-08-21", "shiftCount": 0, "status": "completed", "completedAt": "2026-08-21T14:00:00Z"},
            {"eventType": "overtime", "process": "drilling", "workCenterId": "D-01", "workCenterName": "Delme", "name": "Hafta sonu mesaisi", "startDate": "2026-09-05", "endDate": "2026-09-05", "shiftCount": 3, "status": "active", "completedAt": ""},
        ],
    }

    workbook = load_workbook(BytesIO(build_calendar_event_workbook(payload)))
    sheet = workbook["Bakım ve Mesai"]
    assert sheet["A1"].value == "SELSA  ·  BAKIM, MESAİ VE VARDİYA GEÇMİŞİ"
    assert sheet["A6"].value == "Planlı bakım"
    assert sheet["B7"].value == "Delme"
    assert sheet["I6"].value == "Tamamlandı"
    assert sheet.auto_filter.ref == "A5:J7"
