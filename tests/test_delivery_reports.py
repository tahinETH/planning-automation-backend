import hashlib
import json
import subprocess
from datetime import datetime
from io import BytesIO
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook

from app import delivery_reports as reports
from app import main


@pytest.fixture
def saved(monkeypatch):
    today = datetime.now(ZoneInfo("Europe/Istanbul")).date().isoformat()
    seed = {"orders": [], "products": [], "preferences": [], "machines": [], "manualBatches": [],
            "productionHistory": [{"id": "shipment", "product": "PART-A", "inventoryStatus": "delivered", "completedQuantity": 80, "deliveredAt": today}]}
    state = {"seed": seed, "updatedAt": "2026-09-16T10:00:00Z"}
    monkeypatch.setattr(reports, "planning_state", lambda: state)
    monkeypatch.setattr(main, "planning_state", lambda: state)
    return state, {"startDate": today, "endDate": today}


@pytest.fixture
def client():
    with TestClient(main.app) as client:
        token = client.post("/api/auth/login", json={"password": "test-password"}).json()["token"]
        client.headers["Authorization"] = f"Bearer {token}"
        yield client


def test_shared_runtime_preview_and_workbook_are_from_saved_state(saved, client):
    state, scope = saved
    request = {"expectedRevision": state["updatedAt"], **scope}
    response = client.post("/api/delivery-plan/preview", json=request)
    assert response.status_code == 200, response.text
    snapshot = response.json()
    assert snapshot["report"]["total"] == 80
    assert snapshot["report"]["remaining"] == 0
    assert snapshot["report"]["complete"] is True
    response = client.post("/api/delivery-plan/export", json={**request, "digest": snapshot["digest"], "calculationDate": snapshot["calculationDate"]})
    assert response.status_code == 200, response.text
    workbook = load_workbook(BytesIO(response.content))
    sheet = workbook["Teslimat Planı"]
    assert sheet["B7"].value == "PART-A"
    assert sum(sheet.cell(7, col).value for col in range(12, sheet.max_column + 1) if type(sheet.cell(7, col).value) is int) == 80
    assert workbook["Rapor doğrulaması"]["B1"].value == state["updatedAt"]
    assert workbook["Rapor doğrulaması"]["B5"].value == snapshot["digest"]


def test_old_client_totals_and_extra_input_cannot_bypass_authority(saved, client):
    state, scope = saved
    assert client.post("/api/delivery-plan/export", json={**scope, "weeks": [], "rows": []}).status_code == 422
    assert client.post("/api/delivery-plan/preview", json={"expectedRevision": state["updatedAt"], **scope, "seed": {}}).status_code == 422
    assert client.post("/api/delivery-plan/preview", json={"expectedRevision": state["updatedAt"], **scope, "startDate": "2026-02-30"}).status_code == 422


def test_revision_and_digest_conflicts_require_new_preview(saved, client):
    state, scope = saved
    request = {"expectedRevision": state["updatedAt"], **scope}
    snapshot = client.post("/api/delivery-plan/preview", json=request).json()
    export = {**request, "digest": snapshot["digest"], "calculationDate": snapshot["calculationDate"]}
    assert client.post("/api/delivery-plan/export", json={**export, "digest": "0" * 64}).status_code == 409
    assert client.post("/api/delivery-plan/export", json={**export, "calculationDate": "2000-01-01"}).status_code == 409
    state["updatedAt"] = "2026-09-16T11:00:00Z"
    assert client.post("/api/delivery-plan/export", json=export).status_code == 409


def test_change_during_runtime_is_rejected(saved, monkeypatch):
    state, scope = saved
    calculate = reports.run_delivery_runtime
    def racing(*args):
        result = calculate(*args)
        state["updatedAt"] = "new"
        return result
    monkeypatch.setattr(reports, "run_delivery_runtime", racing)
    with pytest.raises(reports.DeliveryReportError, match="sırasında"):
        reports.report_snapshot(state["updatedAt"], scope)


def test_undated_material_is_visible_but_cannot_be_certified(saved, client):
    state, scope = saved
    # A positive held lot with no route must be inventoried, never promised on a guessed date.
    state["seed"]["wipLots"] = [{"id": "held", "product": "PART-B", "availableQuantity": 120, "stage": "on-hold", "completedSteps": []}]
    request = {"expectedRevision": state["updatedAt"], **scope}
    response = client.post("/api/delivery-plan/preview", json=request)
    assert response.status_code == 200, response.text
    snapshot = response.json()
    assert snapshot["report"]["undatedQuantity"] == 120
    assert snapshot["report"]["total"] == 80
    assert snapshot["report"]["complete"] is False
    response = client.post("/api/delivery-plan/export", json={**request, "digest": snapshot["digest"], "calculationDate": snapshot["calculationDate"]})
    assert response.status_code == 422


def test_runtime_timeout_is_bounded_and_does_not_fallback(saved, monkeypatch):
    state, scope = saved
    def timeout(*args, **kwargs):
        assert kwargs["timeout"] == 20
        assert "NODE_OPTIONS" not in kwargs["env"]
        assert "shell" not in kwargs
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])
    monkeypatch.setattr(reports.subprocess, "run", timeout)
    with pytest.raises(reports.DeliveryReportError) as error:
        reports.report_snapshot(state["updatedAt"], scope)
    assert error.value.status == 503


def test_runtime_output_schema_and_bundle_integrity_fail_closed(saved, monkeypatch, tmp_path):
    state, scope = saved
    def malformed(*args, **kwargs):
        kwargs["stdout"].write(b'{"error":"", "complete":true}')
    monkeypatch.setattr(reports.subprocess, "run", malformed)
    with pytest.raises(reports.DeliveryReportError):
        reports.report_snapshot(state["updatedAt"], scope)
    runtime = tmp_path / "delivery-runtime.cjs"
    runtime.write_text("invalid")
    runtime.with_suffix(".cjs.json").write_text(json.dumps({"runtimeSha256": hashlib.sha256(b"different").hexdigest()}))
    monkeypatch.setattr(reports, "RUNTIME", runtime)
    with pytest.raises(reports.DeliveryReportError) as error:
        reports.report_snapshot(state["updatedAt"], scope)
    assert error.value.status == 503


def test_export_scope_change_requires_fresh_preview_and_download_preserves_state(saved, client):
    """DEL-EXP01: changed dates cannot reuse a verified file; export is read-only."""
    import copy
    from datetime import date, timedelta
    state, scope = saved
    before = copy.deepcopy(state)
    request = {"expectedRevision": state["updatedAt"], **scope}
    snapshot = client.post("/api/delivery-plan/preview", json=request).json()
    changed = {**request, "endDate": (date.fromisoformat(scope["endDate"]) + timedelta(days=7)).isoformat()}
    stale = client.post("/api/delivery-plan/export", json={**changed, "digest": snapshot["digest"], "calculationDate": snapshot["calculationDate"]})
    assert stale.status_code == 409
    fresh = client.post("/api/delivery-plan/preview", json=changed).json()
    exported = client.post("/api/delivery-plan/export", json={**changed, "digest": fresh["digest"], "calculationDate": fresh["calculationDate"]})
    assert exported.status_code == 200, exported.text
    assert exported.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert f'Teslimat_Plani_{changed["startDate"]}_{changed["endDate"]}.xlsx' in exported.headers["content-disposition"]
    assert exported.content.startswith(b"PK")
    workbook = load_workbook(BytesIO(exported.content))
    assert workbook["Rapor doğrulaması"]["B5"].value == fresh["digest"]
    assert workbook.calculation.fullCalcOnLoad is True
    assert state == before
