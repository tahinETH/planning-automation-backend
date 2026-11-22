import os
from io import BytesIO
from pathlib import Path

os.environ.setdefault("DATABASE_PATH", "/tmp/selsa-planlama-feedback-test.sqlite")
os.environ.setdefault("UPLOAD_DIR", "/tmp/selsa-planlama-feedback-uploads")
os.environ["ADMIN_PASSWORD"] = "test-password"
os.environ["APP_SESSION_SECRET"] = "test-session-secret-that-is-long-enough"

from fastapi.testclient import TestClient
from openpyxl import load_workbook

from app.data_package import DataPackageError, build_data_package, parse_data_package
from app.main import app


def sample_parameters():
    return {
        "products": [{"product": "R1", "setupFamily": "piston", "batchSize": 1920, "dailyRate": 375, "shiftRate": 125, "parameterDailyRate": 375, "diameter": "17,2", "source": "Test"}],
        "preferences": [{"key": "R1", "machines": ["C-01", "C-02"]}],
        "restrictions": [],
        "machineRates": [{"id": "C-01", "rates": {"R1": 375}}],
    }


def test_data_package_round_trip_and_visible_sheets():
    data = sample_parameters()
    content = build_data_package("parameters", data)
    workbook = load_workbook(BytesIO(content), read_only=True)
    assert {"Bilgi", "Ürün Parametreleri", "Tezgah Öncelikleri", "__SelsaVeri"}.issubset(workbook.sheetnames)
    assert workbook["Ürün Parametreleri"]["B2"].value == "Piston"
    assert parse_data_package(content, "parameters") == data


def test_data_package_rejects_wrong_scope():
    content = build_data_package("parameters", sample_parameters())
    try:
        parse_data_package(content, "settings")
        assert False, "wrong scope should fail"
    except DataPackageError as error:
        assert "Ayarlar" in str(error)


def test_data_package_api_is_authenticated_and_round_trips():
    Path(os.environ["DATABASE_PATH"]).unlink(missing_ok=True)
    with TestClient(app) as client:
        payload = {"scope": "parameters", "data": sample_parameters()}
        assert client.post("/api/data-packages/export", json=payload).status_code == 401
        login = client.post("/api/auth/login", json={"password": "test-password"})
        headers = {"Authorization": f"Bearer {login.json()['token']}"}
        exported = client.post("/api/data-packages/export", headers=headers, json=payload)
        assert exported.status_code == 200
        imported = client.post(
            "/api/data-packages/parameters/import",
            headers=headers,
            files={"file": ("Selsa_Parametreler.xlsx", exported.content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert imported.status_code == 200
        assert imported.json()["data"] == sample_parameters()


def test_cf_b5_complete_workbook_exposes_filter_calendar_stock_and_product_parameters():
    from io import BytesIO
    from openpyxl import load_workbook

    product = "F.00V.C15.100"
    parameters = {"productionArea": "cubuk-filtre", "products": [{"product": product, "setupFamily": "cubuk-filtre",
        "moq": 125, "shipmentMultiple": 25, "setupScrapPercent": 1.5, "productionScrapPercent": 2,
        "eligibleMachines": ["L-01"], "turningSetupMinutes": {"L-01": 120}}], "machineRates": [{"id": "L-01", "rates": {product: 5400}}]}
    settings = {"productionArea": "cubuk-filtre", "filterWaitShifts": 0, "filterQualityShifts": 3, "processStockSettings": {
        "limits": [{"groupId": "warehouse", "min": 1000, "max": 2500}],
        "scrap": [{"groupId": "form-front", "product": product, "percent": 2}],
        "openingDate": "2026-11-01", "opening": [{"groupId": "warehouse", "product": product, "quantity": 1100}]}}
    data = {"version": 1, "productionArea": "cubuk-filtre", "parameters": parameters, "settings": settings}
    content = build_data_package("complete", data)
    workbook = load_workbook(BytesIO(content))
    product_rows = list(workbook["Ürün Parametreleri"].values)
    assert dict(zip(*product_rows))["Min. Sevkiyat"] == 125
    assert dict(zip(*product_rows))["Ayar Iskartası %"] == 1.5
    assert tuple(workbook["Tezgah Öncelikleri"].values)[1] == (product, 1, "L-01", 5400, 120)
    assert [row[2] for row in list(workbook["Çubuk Filtre Takvimleri"].values)[1:]] == [0, 3, 2]
    assert tuple(workbook["Proses Başlangıç Stoğu"].values)[1] == ("Ambar + BB", product, 1100, "2026-11-01")
    assert workbook["__SelsaVeri"].sheet_state == "veryHidden"
    workbook["Ürün Parametreleri"]["A2"] = "Görünür sayfa düzenlemesi"
    edited = BytesIO()
    workbook.save(edited)
    assert parse_data_package(edited.getvalue(), "complete") == data
