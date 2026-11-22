from io import BytesIO

from openpyxl import load_workbook

from app.calendar_export import build_calendar_event_workbook
from app.models import CalendarEventExportPayload


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


def test_calendar_event_export_accepts_filter_quality_and_demand_calendars():
    raw = {
        "generatedAt": "2026-11-22T10:00:00Z",
        "rows": [
            {"eventType": "shift-change", "process": "filter-quality", "workCenterId": "CF-KALITE", "workCenterName": "Kalite bekleme", "name": "Cumartesi kalite", "startDate": "2026-11-28", "endDate": "2026-11-28", "shiftCount": 1, "status": "active", "completedAt": ""},
            {"eventType": "shift-change", "process": "filter-demand", "workCenterId": "CF-DEMAND", "workCenterName": "Aylık ihtiyaç dağılımı", "name": "Yarım gün", "startDate": "2026-11-29", "endDate": "2026-11-29", "shiftCount": 1, "status": "active", "completedAt": ""},
            {"eventType": "shift-change", "process": "filter-wait", "workCenterId": "CF-BEKLEME", "workCenterName": "Çubuk Filtre bekleme takvimi", "name": "Isıl işlem mesaisi", "startDate": "2026-11-30", "endDate": "2026-11-30", "shiftCount": 2, "status": "active", "completedAt": ""},
        ],
    }
    validated = CalendarEventExportPayload.model_validate(raw).model_dump()
    workbook = load_workbook(BytesIO(build_calendar_event_workbook(validated)))
    sheet = workbook["Bakım ve Mesai"]
    assert sheet["B6"].value == "Kalite bekleme"
    assert sheet["B7"].value == "Aylık ihtiyaç dağılımı"
    assert sheet["B8"].value == "Çubuk Filtre bekleme takvimi"
    assert sheet["C6"].value == "CF-KALITE"
    assert sheet["C7"].value == "CF-DEMAND"
