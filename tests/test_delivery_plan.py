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
from app.models import DeliveryPlanPayload
from app.delivery_plan import DeliveryPlanError
import pytest


def delivery_columns(count: int = 6):
    base = [
        {"label": "KW31\nGerçekleşen", "kind": "actual"},
        {"label": "KW32\nGerçekleşen", "kind": "actual"},
        {"label": "KW33\nGerçekleşen", "kind": "actual"},
        {"label": "KW33'e\nDevreden", "kind": "carryover"},
        {"label": "KW33\nPlan", "kind": "plan"},
        {"label": "KW34\nPlan", "kind": "plan"},
    ]
    return base + [{"label": f"KW{35 + index}\nPlan", "kind": "plan"} for index in range(max(0, count - len(base)))]


def corrected_payload():
    return {
        "startDate": "2026-09-01", "endDate": "2026-09-30", "orderDate": "2026-08-31",
        "sourceFile": "Selsa_w36.xlsx", "demandSource": "customer-snapshot",
        "weeks": [
            {"label": "KW36\nSipariş öncesi\nGerçekleşen", "kind": "actual-before-order"},
            {"label": "KW36\nSipariş sonrası\nGerçekleşen", "kind": "actual-after-order"},
            {"label": "KW36'e\nDevreden", "kind": "carryover"},
            {"label": "KW36\nPlan", "kind": "plan"},
            {"label": "KW37\nSipariş sonrası\nGerçekleşen", "kind": "actual-after-order"},
            {"label": "KW37\nPlan", "kind": "plan"},
        ],
        "rows": [
            {"product": "R902745119", "family": "PISTON", "orderQuantity": 6210, "weeklyQuantities": [0, 4161, 500, 0, 0, 0]},
            {"product": "R902745133", "family": "PISTON", "orderQuantity": 8144, "weeklyQuantities": [0, 1920, 3840, 1920, 0, 1920]},
            {"product": "R902745129", "family": "CENTER PIN", "orderQuantity": 1920, "weeklyQuantities": [0, 2389, 100, 0, 0, 0]},
        ],
    }


def test_snapshot_columns_metadata_and_family_totals_exclude_carryover():
    template = Path(__file__).resolve().parents[1] / "teslimat_plani.xlsx"
    payload = DeliveryPlanPayload.model_validate(corrected_payload()).model_dump()
    content = build_delivery_plan(template, payload)
    workbook = load_workbook(BytesIO(content), data_only=False)
    sheet = workbook["Teslimat Planı"]
    assert sheet["L3"].value.date().isoformat() == "2026-08-31"
    assert sheet["L4"].value == "Selsa_w36.xlsx"
    assert sheet["C7"].value == "PISTON"
    assert sheet["D7"].value == 6210
    assert sheet["E7"].value == "=SUM(M7,P7)"
    assert sheet["F7"].value == "=SUM(O7,Q7)"
    assert sheet["I7"].value == "=SUM(L7,M7,P7)"
    assert sheet["G7"].value == "=E7+F7-D7"
    assert sheet["F53"].value == '=SUMIF(C7:C49,"PISTON",F7:F49)+SUMIF(C7:C49,"PISTON",I7:I49)'
    assert sheet["F54"].value == '=SUMIF(C7:C49,"CENTER PIN",F7:F49)+SUMIF(C7:C49,"CENTER PIN",I7:I49)'
    assert sheet["L6"].fill.fgColor == sheet["M6"].fill.fgColor == sheet["B6"].fill.fgColor
    assert sheet["L6"].font.color != sheet["M6"].font.color
    with ZipFile(BytesIO(content)) as archive:
        assert not any("externalLink" in name for name in archive.namelist())


def test_export_accepts_53_weeks_with_separate_actual_and_plan_columns():
    template = Path(__file__).resolve().parents[1] / "teslimat_plani.xlsx"
    payload = corrected_payload()
    payload.update(startDate="2026-01-01", endDate="2026-12-31", weeks=[{"label": f"KW{i}\n{kind}", "kind": kind} for i in range(1, 54) for kind in ["actual-after-order", "plan"]], rows=[])
    sheet = load_workbook(BytesIO(build_delivery_plan(template, payload)))["Teslimat Planı"]
    assert sheet.cell(6, 117).value == "KW53\nplan"


def test_export_rejects_invalid_quantities_and_does_not_execute_source_text():
    template = Path(__file__).resolve().parents[1] / "teslimat_plani.xlsx"
    payload = corrected_payload()
    payload["rows"][0]["weeklyQuantities"][0] = -1
    with pytest.raises(DeliveryPlanError, match="negatif olmayan tam sayı"):
        build_delivery_plan(template, payload)
    payload["rows"][0]["weeklyQuantities"][0] = 0
    payload["sourceFile"] = "=1+1"
    sheet = load_workbook(BytesIO(build_delivery_plan(template, payload)))["Teslimat Planı"]
    assert sheet["L4"].data_type == "s"
    payload["orderDate"] = ""
    with pytest.raises(DeliveryPlanError, match="sipariş tarihi zorunludur"):
        build_delivery_plan(template, payload)


def test_delivery_plan_uses_corrected_summary_and_weekly_structure():
    template = Path(__file__).resolve().parents[1] / "teslimat_plani.xlsx"
    content = build_delivery_plan(template, {
        "startDate": "2026-07-20",
        "endDate": "2026-08-30",
        "category": "Üretim",
        "weeks": delivery_columns(),
        "rows": [{"product": "R902745116", "orderQuantity": 5760, "weeklyQuantities": [1920, 1920, 0, 0, 1920, 0]}],
    })
    workbook = load_workbook(BytesIO(content), data_only=False)
    sheet = workbook["Teslimat Planı"]
    assert sheet["B7"].value == "R902745116"
    assert sheet["D7"].value == 5760
    assert sheet["E7"].value == "=SUM(L7:N7)"
    assert sheet["F7"].value == "=SUM(P7:Q7)"
    assert sheet["G7"].value == "=E7+F7-D7"
    assert sheet["I7"].value == "=SUM(L7:N7)"
    assert sheet["K7"].value == "R902745116"
    assert [sheet.cell(7, column).value for column in range(12, 18)] == [1920, 1920, 0, 0, 1920, 0]
    assert sheet["B50"].value == "Genel Toplam"
    assert sheet["I50"].value == "=SUM(I7:I49)"
    assert sheet["Q50"].value == "=SUM(Q7:Q49)"
    assert sheet["I50"].fill.fgColor.rgb == "00FFF200"
    assert sheet["I50"].font.color.rgb == "00000000"
    assert sheet["I50"].font.bold is True
    assert sheet["L3"].value == "Belirtilmedi"
    assert sheet["F52"].value == "=F50+I50"
    assert sheet.freeze_panes == "B7"
    assert not list(workbook.defined_names)
    with ZipFile(BytesIO(content)) as archive:
        workbook_xml = archive.read("xl/workbook.xml").decode("utf-8")
    assert "#REF!" not in workbook_xml


def test_delivery_plan_endpoint_returns_an_excel_download():
    payload = {
        "startDate": "2026-07-20", "endDate": "2026-08-30", "category": "Üretim",
        "weeks": delivery_columns(),
        "rows": [{"product": "R902745116", "orderQuantity": 5760, "weeklyQuantities": [1920, 1920, 0, 0, 1920, 0]}],
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
        "weeks": delivery_columns(), "rows": rows,
    })
    sheet = load_workbook(BytesIO(content), data_only=False)["Teslimat Planı"]
    assert sheet["B56"].value == "P050"
    assert sheet["B57"].value == "Genel Toplam"
    assert sheet["D57"].value == "=SUM(D7:D56)"
    assert sheet["G57"].value == "=SUM(G7:G56)"
    assert sheet["I57"].value == "=SUM(I7:I56)"


def test_delivery_plan_expands_week_columns_beyond_the_original_six():
    template = Path(__file__).resolve().parents[1] / "teslimat_plani.xlsx"
    quantities = [100] * 9
    content = build_delivery_plan(template, {
        "startDate": "2026-06-22", "endDate": "2026-08-23", "category": "Üretim",
        "weeks": delivery_columns(9),
        "rows": [{"product": "P001", "orderQuantity": 900, "weeklyQuantities": quantities}],
    })
    sheet = load_workbook(BytesIO(content), data_only=False)["Teslimat Planı"]
    assert sheet["T6"].value == "KW37\nPlan"
    assert sheet["T7"].value == 100
    assert sheet["E7"].value == "=SUM(L7:N7)"
    assert sheet["F7"].value == "=SUM(P7:T7)"
    assert sheet["T50"].value == "=SUM(T7:T49)"
    assert sheet.auto_filter.ref == "B6:T49"
