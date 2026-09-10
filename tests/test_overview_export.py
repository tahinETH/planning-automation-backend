from io import BytesIO

import pytest

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
    assert [name for name in workbook.sheetnames if "Hammadde" not in name] == ["Genel Bakış", "Torna Saha Planı", "Delme Planı", "Çapak Alma Planı", "GKM Planı", "Plan Kontrolü"]
    sheet = workbook["Genel Bakış"]
    assert sheet["A1"].value == "SELSA  ·  ÜRETİM GENEL BAKIŞ"
    assert sheet["A6"].value == 1000
    assert sheet["G6"].value == 150
    assert sheet["A10"].value.startswith("C-01")
    assert sheet["A13"].value == "Üretimde"
    assert sheet["A13"].fill.fgColor.rgb.endswith("E4F5E4")
    assert workbook["Plan Kontrolü"]["A5"].value == "Kritik"
    assert workbook["Torna Saha Planı"]["A1"].value == "SELSA  ·  TORNA SAHA PLANI"
    assert workbook["Torna Saha Planı"]["D8"].value == 350
    assert workbook["Delme Planı"]["A6"].value == "D-01"

    drilling_payload = {**payload, "selectedProcess": "drilling", "operationPlans": [payload["operationPlans"][1]]}
    drilling_workbook = load_workbook(BytesIO(build_overview_workbook(drilling_payload)))
    assert drilling_workbook.sheetnames == ["Delme Planı", "Delme Hammadde"]
    assert drilling_workbook["Delme Planı"]["A1"].value == "SELSA  ·  DELME GENEL PLANI"






def test_turning_next_jobs_export_has_no_date_limit_in_header():
    payload = {
        "generatedAt": "2026-08-27T10:00:00Z", "createdAt": "", "planState": "planned", "dirty": False,
        "selectedProcess": "turning", "printRange": {"mode": "next-jobs", "startDate": "", "endDate": "", "dayCount": 0},
        "summary": {}, "machines": [],
        "operationPlans": [{"process": "turning", "label": "Torna", "totalQuantity": 100, "totalJobCount": 1, "omittedJobCount": 0, "resources": [{"id": "C-01", "name": "Torna", "rows": [{"status": "planned", "position": 1, "product": "R001", "workOrder": "320-1", "quantity": 100, "setupKey": "23", "startDate": "2026-10-01", "endDate": "2026-10-02"}]}]}],
        "findings": [],
    }

    workbook = load_workbook(BytesIO(build_overview_workbook(payload)))
    assert workbook["Torna Saha Planı"]["A3"].value == "Her tezgâh için sıradaki en fazla 10 iş"


def test_shop_floor_exports_include_diameter_without_reusing_drill_setup():
    for process, label in [("turning", "Torna"), ("deburring", "Çapak Alma"), ("gkm", "GKM")]:
        row = {"status": "current", "position": 1, "product": "R1", "quantity": 100,
               "diameter": "25,5", "setupKey": "4.2", "workOrder": "WO", "startDate": "2026-09-07", "endDate": "2026-09-08"}
        payload = {"selectedProcess": process, "generatedAt": "2026-09-07", "printRange": {"mode": "next-jobs"},
                   "operationPlans": [{"process": process, "label": label, "resources": [{"id": "M1", "rows": [row]}]}]}
        sheet = load_workbook(BytesIO(build_overview_workbook(payload))).worksheets[0]
        assert any(c.value == "Çap" for cells in sheet for c in cells)
        assert any(c.value == "25,5" for cells in sheet for c in cells)
        assert not any(c.value == "4.2" for cells in sheet for c in cells)




def test_legacy_drilling_export_also_omits_diameter():
    payload = {"selectedProcess": "drilling", "operationPlans": [{"process": "drilling", "label": "Delme",
        "resources": [{"id": "D-01", "rows": [{"product": "R1", "diameter": "25,5"}]}]}]}
    sheet = load_workbook(BytesIO(build_overview_workbook(payload))).worksheets[0]
    assert sheet.max_column == 9
    assert not any(cell.value in {"Çap", "25,5"} for row in sheet for cell in row)




@pytest.mark.parametrize("process,label", [("drilling", "Delme"), ("deburring", "Çapak Alma"), ("gkm", "GKM")])
def test_material_requirement_uses_102_percent_and_marks_missing_weights(process, label):
    from app.models import OverviewOperationRow
    row = OverviewOperationRow(status="planned", position=1, product="R902745116", quantity=1980,
                               materialCode="Z170008", unitWeightGrams=181).model_dump()
    missing = {**row, "product": "UNKNOWN", "unitWeightGrams": None}
    payload = {"selectedProcess": process, "dirty": True, "printRange": {"mode": "next-jobs"},
               "operationPlans": [{"process": process, "label": label,
                                   "resources": [{"id": "S-01", "rows": [row, missing]}]}]}
    workbook = load_workbook(BytesIO(build_overview_workbook(payload)), data_only=True)
    sheet = next(sheet for sheet in workbook if "Hammadde" in sheet.title)
    assert sheet["F8"].value == "Z170008"
    assert sheet["G8"].value == 181
    assert sheet["H8"].value == pytest.approx(358.38)
    assert sheet["I8"].value == pytest.approx(7.1676)
    assert sheet["J8"].value == pytest.approx(365.5476)
    assert sheet["J9"].value == "Eksik"
    assert sheet["J10"].value == pytest.approx(365.5476)
    assert "ara toplamı" in sheet["A10"].value
    assert "1 işin ağırlığı bilinmiyor" in sheet["A6"].value
    assert "plan güncel değil" in sheet["A6"].value
    assert "(1 + Iskarta Oranı / 100) / 1000" in sheet["A4"].value


def test_material_totals_preserve_precision_and_station_scope():
    resources = [{"id": station, "rows": [{"product": "R1", "position": i + 1, "quantity": 1,
                                           "unitWeightGrams": 0.1} for i in range(count)]}
                 for station, count in [("S-01", 10), ("S-02", 2)]]
    workbook = load_workbook(BytesIO(build_overview_workbook({"selectedProcess": "gkm", "operationPlans": [
        {"process": "gkm", "label": "GKM", "resources": resources}]})), data_only=True)
    first, second = [sheet for sheet in workbook if "Hammadde" in sheet.title]
    assert first.title == "GKM S-01 Hammadde"
    assert second.title == "GKM S-02 Hammadde"
    assert first["J18"].value == pytest.approx(0.00102)
    assert second["J10"].value == pytest.approx(0.000204)
    assert first["J8"].number_format == "#,##0.000"
    assert "Toplam hammadde" in first["A18"].value




@pytest.mark.parametrize("grams", [0, -1, float("nan"), float("inf")])
def test_export_rejects_invalid_unit_weight(grams):
    from pydantic import ValidationError
    from app.models import OverviewOperationRow
    with pytest.raises(ValidationError):
        OverviewOperationRow(status="planned", position=1, product="R1", quantity=1, unitWeightGrams=grams)


@pytest.mark.parametrize("process,label,columns", [("drilling", "Delme", 7), ("deburring", "Çapak Alma", 8), ("gkm", "GKM", 8)])
@pytest.mark.parametrize("counts", [[63, 2, 0], [90, 93, 1], [0, 0]])
def test_downstream_machines_share_sheet_without_dropping_jobs(process, label, columns, counts):
    resources = [{"id": f"S-{side + 1:02}", "name": f"Station {side}",
                  "rows": [{"product": f"UNIQUE-{side}-{i}", "position": i + 1, "quantity": 10, "diameter": "25,5"}
                           for i in range(count)]} for side, count in enumerate(counts)]
    payload = {"selectedProcess": process, "printRange": {"mode": "date-range", "startDate": "2026-09-07", "endDate": "2026-09-21", "dayCount": 15},
               "operationPlans": [{"process": process, "label": label, "resources": resources}]}
    workbook = load_workbook(BytesIO(build_overview_workbook(payload)))
    floors = [sheet for sheet in workbook if "Hammadde" not in sheet.title]
    assert len(floors) == 1
    sheet = floors[0]
    assert sheet.title == f"{label} Saha Planı"
    assert sheet["A6"].value.startswith("S-01")
    assert sheet.cell(6, columns + 2).value.startswith("S-02")
    exported = [cell.value for row in sheet for cell in row if isinstance(cell.value, str) and cell.value.startswith("UNIQUE-")]
    assert sorted(exported) == sorted(row["product"] for resource in resources for row in resource["rows"])
    assert sheet["A3"].value == "2026-09-07 – 2026-09-21  ·  15 gün"
    assert sheet.print_title_rows == "$1:$5"
    assert ("Çap" in [cell.value for row in sheet for cell in row]) == (process != "drilling")
    if process == "drilling":
        assert not any(cell.value == "25,5" for row in sheet for cell in row)
    if max(counts) > 40:
        assert sheet.row_breaks.brk
        assert sheet.cell(36, 1).value.startswith("S-01")
    if 0 in counts:
        assert any(cell.value == "Seçilen kapsamda planlı iş yok" for row in sheet for cell in row)


def test_turning_materials_are_inline_scoped_and_missing_is_explicit():
    resources = [{"id": f"C-{i}", "rows": [{"product": f"R-{i}-{j}", "position": j + 1, "quantity": 1980,
                   "materialCode": "Z170008", "unitWeightGrams": None if j == 1 else 181} for j in range(11)]} for i in range(17)]
    payload = {"selectedProcess": "turning", "dirty": True, "printRange": {"mode": "next-jobs"},
               "operationPlans": [{"process": "turning", "label": "Torna", "resources": resources}]}
    workbook = load_workbook(BytesIO(build_overview_workbook(payload)), data_only=True)
    assert workbook.sheetnames == ["Torna Saha Planı"]
    sheet = workbook.active
    assert sheet["I7"].value == "Hammadde kodu"
    assert sheet["J7"].value == "Birim ağırlık (g)"
    assert sheet["K7"].value == "İhtiyaç (kg)"
    assert sheet["I8"].value == "Z170008"
    assert sheet["J8"].value == 181
    assert sheet["K8"].value == pytest.approx(365.5476)
    assert sheet["K9"].value == "Eksik"
    assert "Bilinen ara toplam" in sheet["A18"].value
    assert "1 ağırlık eksik" in sheet["A18"].value
    assert "3,289.928" in sheet["A18"].value
    assert "(1 + Iskarta Oranı / 100) / 1000" in sheet["A5"].value
    assert "Plan güncel değil" in sheet["A5"].value
    assert sheet["M6"].value.startswith("C-1")
    assert sheet["W8"].value == pytest.approx(365.5476)
    assert sheet["A64"].value.startswith("C-8")
    products = [cell.value for row in sheet for cell in row if isinstance(cell.value, str) and cell.value.startswith("R-")]
    assert len(products) == 160
    assert [brk.id for brk in sheet.row_breaks.brk] == [63]
    assert sheet.print_area == "'Torna Saha Planı'!$A$1:$W$118"
