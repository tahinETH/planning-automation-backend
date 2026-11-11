import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from app import database as db
from app.auth import create_test_session, current_user
from app.main import app
from app.planning_delta import build_delta
from fastapi.security import HTTPAuthorizationCredentials


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "settings", SimpleNamespace(database_path=tmp_path / "roles.sqlite", upload_dir=tmp_path / "uploads"))
    db.init_database()
    fixture = json.loads((Path(__file__).parent / "fixtures/collaboration.json").read_text())
    fixture["seed"]["holidays"] = [{"serial": 46300, "name": "Reviewed holiday", "workingShifts": 0}]
    db.save_planning_state(fixture["seed"], can_manage_settings=True, flow_settings_version=1, route_placement_version=1, production_split_version=1, process_wait_settings_version=1)
    return TestClient(app)


def write(client, candidate, role="user", method="patch"):
    current = db.planning_state()
    payload = dict(expectedUpdatedAt=current["updatedAt"], mode="planning", flowSettingsVersion=1, routePlacementVersion=1, productionSplitVersion=1, processWaitSettingsVersion=1, stockPlanningVersion=1, monthlyPlanningVersion=1)
    if method == "patch":
        payload.update(version=1, transactionId="role-check", baseHash=current["stateHash"], delta=build_delta(current["seed"], candidate))
    else:
        payload["seed"] = candidate
    return getattr(client, method)("/api/planning-state", json=payload, headers={"Authorization": "Bearer " + create_test_session("test-password", role)})


@pytest.mark.parametrize("method", ["put", "patch"])
@pytest.mark.parametrize("change", ["parameter", "eligibility", "shift", "process-shift", "order", "order-add", "order-clear", "new-type", "holiday-shift"])
def test_role01_user_can_save_reviewed_inputs_without_changing_production(workspace, method, change):
    original = db.planning_state()
    seed = copy.deepcopy(original["seed"])
    if change == "parameter": seed["products"][0]["shiftRate"] += 1
    if change == "eligibility":
        product = seed["products"][0]
        machine = seed["machines"][-1]
        product["eligibleMachines"] = list(dict.fromkeys([*product.get("eligibleMachines", []), machine["id"]]))
        product["alternativeMachines"] = list(product["eligibleMachines"])
        machine["rates"][product["product"]] = 1800
    if change == "shift": seed["machines"][0]["shiftFactor"] = 2
    if change == "process-shift": seed["processMasterData"]["resources"][0]["defaultShifts"] = 1
    if change == "order": seed["orders"][0]["quantity"] += 20
    if change == "order-add": seed["orders"].append({**seed["orders"][0], "id": "new-planner-order", "quantity": 75})
    if change == "order-clear": seed["orders"] = []
    if change == "new-type": seed["products"].append({"product": "NEW-ROLE", "batchSize": 0, "source": "Web Parametreleri"})
    if change == "holiday-shift": seed["calendarEvents"].append(dict(id="holiday-shift", machineId=seed["machines"][0]["id"], kind="shift", name="Holiday work", start=46300, end=46300, shiftCount=2))
    response = write(workspace, seed, method=method)
    assert response.status_code == 200, response.text
    saved = db.planning_state()["seed"]
    for field in ("manualBatches", "productionHistory", "wipLots", "wipMovements", "processCurrentJobs", "productionInterruptions"):
        assert saved.get(field) == original["seed"].get(field)
    db.init_database()
    assert db.planning_state()["seed"] == saved


@pytest.mark.parametrize("method", ["put", "patch"])
@pytest.mark.parametrize("change", ["holiday", "maintenance", "ordinary-calendar", "setup", "weights", "stock", "delete-type", "machine-name", "machine-window", "new-machine", "route", "process-rate"])
def test_role02_user_cannot_change_admin_configuration_even_with_an_allowed_edit(workspace, method, change):
    original = db.planning_state()
    seed = copy.deepcopy(original["seed"])
    seed["orders"][0]["quantity"] += 1
    if change == "holiday": seed["holidays"] = []
    if change == "maintenance": seed["calendarEvents"].append(dict(id="maintenance", machineId=seed["machines"][0]["id"], kind="maintenance", name="Maintenance", start=46300, end=46300, shiftCount=0))
    if change == "ordinary-calendar": seed["calendarEvents"].append(dict(id="ordinary", machineId=seed["machines"][0]["id"], kind="shift", name="Ordinary day", start=46301, end=46301, shiftCount=2))
    if change == "setup": seed["setupSettings"]["sameDiameterHours"] += 1
    if change == "weights": seed["productWeights"] = []
    if change == "stock": seed["openingStock"] = {"R902745116": 100}
    if change == "delete-type": seed["products"] = []
    if change == "machine-name": seed["machines"][0]["name"] = "Changed"
    if change == "machine-window": seed["machines"][0]["planEnd"] += 1
    if change == "new-machine": seed["machines"].append({**seed["machines"][0], "id": "NEW-MACHINE"})
    if change == "route": seed["processMasterData"]["products"][0]["route"] = ["turning"]
    if change == "process-rate": seed["processMasterData"]["products"][0]["processes"][0]["unitsPerShift"] = {"D-01": 9999}
    response = write(workspace, seed, method=method)
    assert response.status_code == 403, response.text
    assert db.planning_state() == original


def test_role03_holiday_override_keeps_surrounding_calendar_and_maintenance(workspace):
    seed = db.planning_state()["seed"]
    machine = seed["machines"][0]["id"]
    seed["calendarEvents"] = [dict(id="range", machineId=machine, kind="shift", name="Existing", start=46299, end=46301, shiftCount=1), dict(id="maintenance", machineId=machine, kind="maintenance", name="Maintenance", start=46300, end=46300, shiftCount=0)]
    assert write(workspace, seed, "admin", "put").status_code == 200
    candidate = copy.deepcopy(seed)
    candidate["calendarEvents"] = [dict(seed["calendarEvents"][0], end=46299), dict(seed["calendarEvents"][0], id="tail", start=46301), seed["calendarEvents"][1], dict(id="holiday", machineId=machine, kind="shift", name="Holiday", start=46300, end=46300, shiftCount=3)]
    response = write(workspace, candidate)
    assert response.status_code == 200, response.text
    assert db.planning_state()["seed"]["calendarEvents"][2] == seed["calendarEvents"][1]


@pytest.mark.parametrize("method", ["put", "patch"])
def test_mgmt_role02_planner_can_preview_and_save_official_customer_excel(workspace, method):
    from test_order_import import confirmed_overview_bytes
    original = db.planning_state()
    headers = {"Authorization": "Bearer " + create_test_session("test-password", "user")}
    response = workspace.post("/api/order-imports/preview", files={"file": ("customer.xlsx", confirmed_overview_bytes(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}, headers=headers)
    assert response.status_code == 200, response.text
    preview = response.json()
    seed = copy.deepcopy(original["seed"])
    seed["customerDemand"] = {key: preview[key] for key in ("format", "calculationModel", "sheetName", "snapshotDate", "baselineLabel", "baselineDueDate", "weeks", "products")}
    seed["customerDemand"].update(sourceFile="customer.xlsx", importedAt="2026-11-11T09:00:00.000Z",
        activeScope={"startWeekId": preview["weeks"][0]["id"], "endWeekId": preview["weeks"][-1]["id"]})
    seed["orderCatalog"] = [row["product"] for row in preview["products"]]
    seed["orderCatalogName"] = "customer.xlsx"
    template = seed["orders"][0]
    seed["orders"] = [{**template, "id": f"import-{index}", "product": row["product"], "quantity": row["quantity"]} for index, row in enumerate(preview["rows"])]
    seed["planNeedsRecalculation"] = True
    saved_response = write(workspace, seed, method=method)
    assert saved_response.status_code == 200, saved_response.text
    saved = db.planning_state()["seed"]
    assert saved["customerDemand"] == seed["customerDemand"]
    assert [(row["product"], row["quantity"]) for row in saved["orders"]] == [(row["product"], row["quantity"]) for row in preview["rows"]]
    for field in ("machines", "processMasterData", "openingStock", "manualBatches", "productionHistory", "wipLots", "processCurrentJobs"):
        assert saved.get(field) == original["seed"].get(field)
    db.init_database()
    assert db.planning_state()["seed"] == saved


def test_role04_clerk_role_does_not_remove_database_admin_override(workspace):
    token = create_test_session("test-password", "user")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    assert current_user(credentials).role == "user"
    with db.connection(shared=True) as connection:
        connection.execute("INSERT INTO app_user_roles(email,role,updated_at) VALUES(?,?,?)", ("user@example.com", "admin", "2026-11-09"))
    assert current_user(credentials).role == "admin"


@pytest.mark.parametrize("fail_commit", [False, True])
def test_role05_manual_receipt_is_atomic_actor_owned_and_retries_once(workspace, fail_commit):
    from app.planning_delta import state_hash
    original = db.planning_state()
    seed = original["seed"]
    body = {"requestId": "reviewed-receipt", "expectedBasis": state_hash({**seed, "chargeJourneyNotes": [], "planningEvents": []}),
        "command": {"kind": "recordManualArchiveReceipt", "args": [{"id": "manual-100", "product": seed["products"][0]["product"], "process": "drilling", "quantity": 100, "reason": "Verified extra physical pieces"}]}}
    headers = {"Authorization": "Bearer " + create_test_session("test-password", "user")}
    if fail_commit:
        with db.connection() as connection:
            connection.execute("CREATE TRIGGER fail_receipt BEFORE INSERT ON production_commands BEGIN SELECT RAISE(ABORT, 'receipt failure'); END")
        with pytest.raises(Exception, match="receipt failure"):
            workspace.post("/api/production/commands", json=body, headers=headers)
        assert db.planning_state() == original
        return
    first = workspace.post("/api/production/commands", json=body, headers=headers)
    assert first.status_code == 200, first.text
    saved = db.planning_state()
    entry = next(row for row in saved["seed"]["productionHistory"] if row["id"] == "manual-100")
    lot = next(row for row in saved["seed"]["wipLots"] if row["sourceHistoryEntryId"] == "manual-100")
    assert entry["manualReceipt"]["actorId"] == "test-user"
    assert entry["manualReceipt"].get("productionDate") is None
    from app.ravi.tools import Inspect, inspect_state
    inspected = inspect_state(saved, Inspect(collection="production", query="manual-100"))["rows"][0]
    assert inspected["completedAt"] is None and inspected["Üretim tarihi"] == "Bilinmiyor"
    assert inspected["Kayıt zamanı"] == entry["manualReceipt"]["recordedAt"]
    assert lot["completedSteps"] == [] and lot["availableQuantity"] == 100
    assert saved["seed"]["manualBatches"] == seed["manualBatches"]
    assert saved["seed"]["machines"] == seed["machines"]
    retry = workspace.post("/api/production/commands", json=body, headers=headers)
    assert retry.status_code == 200 and retry.json()["replayed"]
    assert db.planning_state() == saved
    db.init_database()
    assert db.planning_state() == saved


@pytest.mark.parametrize("method", ["put", "patch"])
def test_role_tip_unused_materialless_type_deletion_requires_admin(workspace, method):
    seed = copy.deepcopy(db.planning_state()["seed"])
    seed["products"].append({"product": "UNUSED-ROLE-TIP", "batchSize": 0, "source": "Web Parametreleri"})
    assert write(workspace, seed, "admin", "put").status_code == 200
    current = db.planning_state()
    removed = copy.deepcopy(current["seed"])
    removed["products"] = [row for row in removed["products"] if row["product"] != "UNUSED-ROLE-TIP"]
    response = write(workspace, removed, "user", method)
    assert response.status_code == 403
    assert db.planning_state() == current
    response = write(workspace, removed, "admin", method)
    assert response.status_code == 200, response.text
    assert all(row["product"] != "UNUSED-ROLE-TIP" for row in db.planning_state()["seed"]["products"])
