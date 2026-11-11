import copy
import json
import sqlite3
from io import BytesIO

import pytest
from openpyxl import load_workbook

from app import database as db
from app.auth import create_test_session, current_user, CurrentUser
from app.main import app
from app.parameter_sheet import build_parameter_sheet, parse_parameter_sheet, assignment_rows, SHEET
from app.data_package import DataPackageError
from app.production_area import production_area
from test_role_permissions import workspace, write


def auth(role="user"):
    return {"Authorization": "Bearer " + create_test_session("test-password", role)}


def request(client, code=None, identity="request-one"):
    code = code or db.planning_state()["seed"]["products"][0]["product"]
    response = client.post("/api/type-requests", json={"id": identity, "product": code, "reason": "Duplicate type review"}, headers=auth())
    assert response.status_code == 200, response.text
    return response.json()["request"]


def review(client, identity, decision="retire", role="admin", basis=None):
    current = client.get(f"/api/type-requests/{identity}", headers=auth(role)).json()
    body = {"expectedRevision": current["request"]["revision"], "expectedWorldRevision": basis or current["worldRevision"], "decision": decision, "note": "Reviewed physical records"}
    return client.post(f"/api/type-requests/{identity}/review", json=body, headers=auth(role)), body


def test_mgmt_type01_owner_scope_role_guard_and_idempotent_create(workspace):
    item = request(workspace)
    assert request(workspace) == item
    response, _ = review(workspace, item["id"], role="user")
    assert response.status_code == 403
    app.dependency_overrides[current_user] = lambda: CurrentUser(id="another", name="Another", email="another@example.test", role="user")
    try:
        assert workspace.get("/api/type-requests", headers=auth()).json()["items"] == []
        assert workspace.get(f"/api/type-requests/{item['id']}", headers=auth()).status_code == 404
        assert workspace.post("/api/type-requests", json={"id": item["id"], "product": item["product"], "reason": item["reason"]}, headers=auth()).status_code == 409
    finally:
        app.dependency_overrides.pop(current_user)
    assert workspace.post("/api/type-requests", json={"id": "other-id", "product": item["product"], "reason": "Second"}, headers=auth()).status_code == 409


def test_mgmt_type02_retire_keeps_all_physical_data_and_exact_retry(workspace):
    before = db.planning_state()
    item = request(workspace)
    refused, _ = review(workspace, item["id"], "delete")
    assert refused.status_code == 422
    assert db.planning_state() == before
    response, body = review(workspace, item["id"])
    assert response.status_code == 200, response.text
    saved = db.planning_state()
    assert saved["seed"]["products"][0]["retired"] is True
    for field in ("manualBatches", "orders", "machines", "productionHistory", "wipLots", "processCurrentJobs", "processMasterData", "productWeights"):
        assert saved["seed"].get(field) == before["seed"].get(field)
    assert saved["seed"]["planNeedsRecalculation"] is True
    retry = workspace.post(f"/api/type-requests/{item['id']}/review", json=body, headers=auth("admin"))
    assert retry.status_code == 200 and retry.json()["replayed"]
    assert db.planning_state() == saved
    body["expectedWorldRevision"] = "different"
    assert workspace.post(f"/api/type-requests/{item['id']}/review", json=body, headers=auth("admin")).status_code == 409
    db.init_database()
    assert workspace.get("/api/type-requests", headers=auth()).json()["items"][0]["status"] == "approved"
    assert db.planning_state() == saved
    old_client = copy.deepcopy(saved["seed"])
    del old_client["products"][0]["retired"]
    assert write(workspace, old_client, "admin", "put").status_code == 200
    assert db.planning_state()["seed"]["products"][0]["retired"] is True
    old_client["products"][0]["retired"] = False
    assert write(workspace, old_client, "user", "put").status_code == 403


def test_mgmt_type03_stale_review_reject_delete_unused_and_atomic_failure(workspace):
    seed = db.planning_state()["seed"]
    seed["products"].append({**seed["products"][0], "product": "UNUSED-MGMT"})
    assert write(workspace, seed, "admin", "put").status_code == 200
    item = request(workspace, "UNUSED-MGMT")
    before = db.planning_state()
    response, _ = review(workspace, item["id"], "delete", basis="old-review")
    assert response.status_code == 409
    assert db.planning_state() == before
    with db.connection() as connection:
        connection.execute("CREATE TRIGGER fail_review BEFORE UPDATE ON type_management_requests BEGIN SELECT RAISE(ABORT, 'review failure'); END")
    with pytest.raises(sqlite3.IntegrityError, match="review failure"):
        review(workspace, item["id"], "delete")
    assert db.planning_state() == before
    assert workspace.get(f"/api/type-requests/{item['id']}", headers=auth()).json()["request"]["status"] == "pending"
    with db.connection() as connection:
        connection.execute("DROP TRIGGER fail_review")
    response, _ = review(workspace, item["id"], "delete")
    assert response.status_code == 200, response.text
    assert not any(row["product"] == "UNUSED-MGMT" for row in db.planning_state()["seed"]["products"])
    item = request(workspace, identity="reject-one")
    before = db.planning_state()
    response, _ = review(workspace, item["id"], "reject")
    assert response.status_code == 200 and response.json()["request"]["status"] == "rejected"
    assert db.planning_state() == before


def package(seed):
    return {**{key: seed[key] for key in ("productionArea", "filterCatalogVersion", "processMasterData", "products", "preferences", "restrictions") if key in seed},
            "machineRates": [{"id": row["id"], "rates": row["rates"]} for row in seed["machines"]]}


def edit_sheet(content, edit):
    workbook = load_workbook(BytesIO(content))
    edit(workbook[SHEET])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_mgmt_excel01_visible_cells_control_all_process_rates_and_preserve_other_data(workspace):
    data = package(db.planning_state()["seed"])
    content = build_parameter_sheet(data)
    assert parse_parameter_sheet(content, True)["changes"] == []
    rows = assignment_rows(data)
    assert {row[1] for row in rows} >= {"turning", "drilling", "deburring", "gkm"}
    for process in {row[1] for row in rows}:
        index = next(i for i, row in enumerate(rows, 2) if row[1] == process)
        changed = edit_sheet(content, lambda sheet: setattr(sheet.cell(index, 6), "value", 123.5))
        parsed = parse_parameter_sheet(changed, True)
        assert parsed["base"] == data
        assert len(parsed["changes"]) == 1
        change = parsed["changes"][0]
        assert change["after"][2] == 123.5
        if process == "turning":
            machine = next(row for row in parsed["data"]["machineRates"] if row["id"] == change["resource"])
            assert machine["rates"][change["product"]] == 123.5
            assert parse_parameter_sheet(changed, False)["changes"] == parsed["changes"]
        else:
            with pytest.raises(DataPackageError, match="yalnız yönetici"):
                parse_parameter_sheet(changed, False)
            candidate = copy.deepcopy(db.planning_state()["seed"])
            candidate["processMasterData"] = parsed["data"]["processMasterData"]
            assert write(workspace, candidate, "user", "put").status_code == 403
        assert parsed["data"]["restrictions"] == data["restrictions"]
        assert parsed["data"]["products"] == data["products"] or process == "turning"


@pytest.mark.parametrize("edit", [lambda s: setattr(s.cell(2, 6), "value", "=100+1"), lambda s: setattr(s.cell(2, 6), "value", -1), lambda s: s.delete_rows(2), lambda s: setattr(s.cell(2, 1), "value", "UNKNOWN"), lambda s: setattr(s.cell(2, 4), "value", 999)])
def test_mgmt_excel02_invalid_changes_are_rejected_without_save(workspace, edit):
    before = db.planning_state()
    with pytest.raises(DataPackageError):
        parse_parameter_sheet(edit_sheet(build_parameter_sheet(package(before["seed"])), edit), True)
    assert db.planning_state() == before


def test_mgmt_excel03_area_guard_and_http_preview_never_save(workspace):
    before = db.planning_state()
    content = build_parameter_sheet(package(before["seed"]))
    response = workspace.post("/api/parameter-sheet/import", headers=auth(), files={"file": ("edit.xlsx", content)})
    assert response.status_code == 200, response.text
    assert db.planning_state() == before
    token = production_area.set("cubuk-filtre")
    try:
        with pytest.raises(DataPackageError, match="başka bir üretim"):
            parse_parameter_sheet(content, True)
    finally:
        production_area.reset(token)


def test_mgmt_type06_reactivation_requires_new_manager_review(workspace):
    item = request(workspace)
    assert review(workspace, item["id"])[0].status_code == 200
    second = request(workspace, identity="reactivate-request")
    assert review(workspace, second["id"], "reactivate", role="user")[0].status_code == 403
    response, _ = review(workspace, second["id"], "reactivate")
    assert response.status_code == 200, response.text
    assert db.planning_state()["seed"]["products"][0]["retired"] is False


@pytest.mark.parametrize("field", ["dailyCustomerDemand", "monthlyCustomerDemand", "filterInitialStockSetup", "filterMonthlyDeliveryBaselines", "filterMonthlyPlan"])
def test_mgmt_type07_filter_reference_blocks_deletion(field):
    from app.product_type_deletion import remove_unused_product_type, assert_product_type_deletion_safe
    seed = {"productionArea": "cubuk-filtre", "products": [{"product": "FILTER-USED"}], field: {"rows": [{"product": "FILTER-USED", "quantity": 0}]}}
    with pytest.raises(ValueError, match="Çubuk Filtre"):
        remove_unused_product_type(seed, "FILTER-USED")
    with pytest.raises(ValueError, match="Çubuk Filtre"):
        assert_product_type_deletion_safe(seed, {"productionArea": "cubuk-filtre", "products": []})


def test_mgmt_type08_usage_added_after_inspection_requires_new_review(workspace):
    seed = db.planning_state()["seed"]
    seed["products"].append({**seed["products"][0], "product": "LATER-USED"})
    assert write(workspace, seed, "admin", "put").status_code == 200
    item = request(workspace, "LATER-USED")
    inspected = workspace.get(f"/api/type-requests/{item['id']}", headers=auth("admin")).json()
    assert inspected["blockers"] == []
    seed = db.planning_state()["seed"]
    seed["orders"].append({**seed["orders"][0], "id": "later-demand", "product": "LATER-USED", "quantity": 100})
    assert write(workspace, seed, "user", "put").status_code == 200
    current = db.planning_state()
    response, _ = review(workspace, item["id"], "delete", basis=inspected["worldRevision"])
    assert response.status_code == 409
    response, _ = review(workspace, item["id"], "delete")
    assert response.status_code == 422
    assert db.planning_state() == current


def test_mgmt_excel05_filter_processes_keep_shift_units_route_and_setup():
    from app.data_package import PROCESS_LABELS
    processes = [key for key in PROCESS_LABELS if key not in ("drilling", "deburring", "gkm")]
    data = {"productionArea": "cubuk-filtre", "products": [], "preferences": [], "restrictions": [], "machineRates": [],
        "processMasterData": {"resources": [{"id": f"RESOURCE-{i}", "process": process} for i, process in enumerate(processes)],
            "products": [{"product": "FILTER-ONE", "route": processes, "processes": [{"process": process, "resourcePriority": [f"RESOURCE-{i}"], "unitsPerShift": {f"RESOURCE-{i}": 200}, "setupKey": "KEEP-SETUP", "waitWorkdaysBefore": 2} for i, process in enumerate(processes)]}]}}
    content = build_parameter_sheet(data)
    token = production_area.set("cubuk-filtre")
    try:
        def change(sheet):
            for row in sheet.iter_rows(min_row=2):
                row[5].value = 123.5
        parsed = parse_parameter_sheet(edit_sheet(content, change), True)
        assert len(parsed["changes"]) == len(processes)
        assert parsed["data"]["processMasterData"]["products"][0]["route"] == processes
        for row in parsed["data"]["processMasterData"]["products"][0]["processes"]:
            assert set(row["unitsPerShift"].values()) == {123.5}
            assert row["setupKey"] == "KEEP-SETUP" and row["waitWorkdaysBefore"] == 2
        with pytest.raises(DataPackageError, match="yalnız yönetici"):
            parse_parameter_sheet(edit_sheet(content, change), False)
    finally:
        production_area.reset(token)
