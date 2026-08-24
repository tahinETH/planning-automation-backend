from io import BytesIO

from openpyxl import load_workbook

from app.overview_export import build_overview_workbook


def test_general_overview_export_contains_colored_summary_and_machine_tables():
    payload = {
            "generatedAt": "2026-07-30T10:00:00Z",
            "createdAt": "2026-07-30T09:30:00Z",
            "planState": "planned",
            "dirty": False,
            "summary": {
                "demand": 1000,
                "planned": 850,
                "plannedBatchCount": 3,
                "unplannedBatchCount": 1,
                "activeMachineCount": 2,
                "machineCount": 2,
                "machinesWithWorkCount": 2,
                "plannedMachineCount": 2,
            },
            "machines": [
                {
                    "id": "C-01",
                    "name": "CITIZEN 1",
                    "active": True,
                    "plannedCount": 1,
                    "plannedQuantity": 500,
                    "rows": [
                        {"kind": "current", "position": 0, "product": "R902740", "diameter": "23", "quantity": 350, "endDate": "2026-08-01", "workOrder": "320-1"},
                        {"kind": "planned", "position": 1, "product": "R902121", "diameter": "23", "quantity": 500, "endDate": "2026-08-04", "workOrder": ""},
                    ],
                },
                {
                    "id": "C-02",
                    "name": "CITIZEN 2",
                    "active": True,
                    "plannedCount": 2,
                    "plannedQuantity": 350,
                    "rows": [{"kind": "planned", "position": 1, "product": "R902690", "diameter": "20", "quantity": 350, "endDate": "2026-08-06", "workOrder": ""}],
                },
            ],
            "operationPlans": [
                {
                    "process": "turning",
                    "label": "Torna",
                    "totalQuantity": 850,
                    "totalJobCount": 3,
                    "resources": [
                        {
                            "id": "C-01",
                            "name": "CITIZEN 1",
                            "rows": [
                                {"status": "current", "position": 1, "product": "R902740", "workOrder": "320-1", "quantity": 350, "setupKey": "23", "startDate": "2026-07-29", "endDate": "2026-08-01"},
                                {"status": "planned", "position": 2, "product": "R902121", "workOrder": "", "quantity": 500, "setupKey": "23", "startDate": "2026-08-01", "endDate": "2026-08-04"},
                            ],
                        }
                    ],
                },
                {"process": "drilling", "label": "Delme", "totalQuantity": 500, "totalJobCount": 1, "resources": [{"id": "D-01", "name": "Delme", "rows": [{"status": "planned", "position": 1, "product": "R902121", "workOrder": "", "quantity": 500, "setupKey": "4.2", "startDate": "2026-08-04", "endDate": "2026-08-05"}]}]},
                {"process": "deburring", "label": "Çapak Alma", "totalQuantity": 0, "totalJobCount": 0, "resources": []},
                {"process": "gkm", "label": "GKM", "totalQuantity": 0, "totalJobCount": 0, "resources": []},
            ],
            "findings": [{"severity": "critical", "title": "Eksik üretim", "detail": "150 adet eksik.", "target": "Siparişler"}],
    }

    workbook = load_workbook(BytesIO(build_overview_workbook(payload)))
    assert workbook.sheetnames == ["Genel Bakış", "Torna Planı", "Delme Planı", "Çapak Alma Planı", "GKM Planı", "Plan Kontrolü"]
    sheet = workbook["Genel Bakış"]
    assert sheet["A1"].value == "SELSA  ·  ÜRETİM GENEL BAKIŞ"
    assert sheet["A6"].value == 1000
    assert sheet["G6"].value == 150
    assert sheet["A10"].value.startswith("C-01")
    assert sheet["A13"].value == "Üretimde"
    assert sheet["A13"].fill.fgColor.rgb.endswith("E4F5E4")
    assert workbook["Plan Kontrolü"]["A5"].value == "Kritik"
    assert workbook["Torna Planı"]["A1"].value == "SELSA  ·  TORNA GENEL PLANI"
    assert workbook["Torna Planı"]["G6"].value == 350
    assert workbook["Delme Planı"]["A6"].value == "D-01"

    drilling_payload = {**payload, "selectedProcess": "drilling", "operationPlans": [payload["operationPlans"][1]]}
    drilling_workbook = load_workbook(BytesIO(build_overview_workbook(drilling_payload)))
    assert drilling_workbook.sheetnames == ["Delme Planı"]
    assert drilling_workbook["Delme Planı"]["A1"].value == "SELSA  ·  DELME GENEL PLANI"
