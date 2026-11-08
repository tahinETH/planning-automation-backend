"""FSM regression examples use synthetic records and the normal HTTP boundary."""
from dataclasses import replace
import copy
import json
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook

from app import database as db, collaboration as collab, main
from app.auth import current_user
from app.calendar_export import build_calendar_event_workbook
from app.production_merge import settings_key_differences, merge_production_refresh_reviewed, REFRESH_GROUPS
from test_collaboration import A, B, isolated, factory, scenario


@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "settings", replace(main.settings, upload_dir=tmp_path / "uploads"))
    main.settings.upload_dir.mkdir(exist_ok=True)
    main.app.dependency_overrides[current_user] = lambda: A
    try:
        yield TestClient(main.app, raise_server_exceptions=False)
    finally:
        main.app.dependency_overrides.pop(current_user, None)


# Protocol fixture values for the stored seed in fixtures/collaboration.json.
# Generated with productionCommandBasis and planningContentHash in the frontend.
# Fixed values let backend CI use its shipped runtime without a frontend checkout.
COMMAND_BASES = {
    "changeWipStage": "5fe22c1efb03873c88ac183ea71ed83e23a50a33cda001dd9d71aa1c33dd9c5e",
    "changeProductionHistoryStatus": "66bf3c0f7745bff1adb0829db7f3932002ccfe62983d1a6dba3c062ee9fd06ee",
}


def command(api, kind, args, request):
    value = dict(kind=kind, args=args)
    return api.post("/api/production/commands", json=dict(requestId=request, expectedBasis=COMMAND_BASES[kind], command=value))


@pytest.mark.parametrize("kind,args", [
    ("changeWipStage", ["lot-a", "delivered", 46000]),
    ("changeWipStage", ["lot-a", "nonsense", 46000]),
    ("changeProductionHistoryStatus", [None, "typo"]),
    ("changeProductionHistoryStatus", [None, "delivered", "2099-12-31"]),
])
def test_sm01_rejected_commands_preserve_world_and_receipts(factory, api, kind, args):
    before = db.planning_state()
    if args[0] is None:
        args[0] = before["seed"]["wipLots"][0]["sourceHistoryEntryId"]
    result = command(api, kind, args, "invalid-command")
    assert result.status_code == 422, result.text
    assert db.planning_state() == before
    assert api.get("/api/collaboration/requests/invalid-command?kind=production").json()["committed"] is False


def test_sm02_stale_share_and_delete_cannot_change_visibility(factory, api):
    saved = api.post("/api/scenarios", json=scenario(factory["seed"])).json()
    url = "/api/scenarios/" + saved["id"]
    assert api.post(url + "/share?revision=1&shared=true").status_code == 200
    assert api.post(url + "/share?revision=2&shared=false").status_code == 200
    assert api.post(url + "/share?revision=2&shared=false").status_code == 409
    assert api.delete(url + "?revision=2").status_code == 409
    assert api.get(url).json()["shared"] is False
    main.app.dependency_overrides[current_user] = lambda: B
    assert api.get(url).status_code == 404


def test_sm03_full_post_cannot_recertify_old_draft(factory, api):
    original = db.planning_state()
    # Trusted server save establishes a previously reviewed draft.
    saved = collab.save_scenario({**scenario(factory["seed"]), "worldRevision": original["updatedAt"]}, A)
    collab.production_command(factory["commands"][0], B)
    world = db.planning_state()
    body = {**saved, "worldRevision": world["updatedAt"]}
    saved = api.post("/api/scenarios", json=body)
    assert saved.status_code == 201, saved.text
    assert saved.json()["worldRevision"] == original["updatedAt"]
    preview = api.post("/api/scenarios/plan-a/publication-preview", json=dict(revision=2, worldRevision=world["updatedAt"], previousId=None))
    assert preview.status_code == 409, preview.text
    changed = {**saved.json(), "seed": {**saved.json()["seed"], "source": "changed contents"}}
    changed = api.post("/api/scenarios", json=changed)
    assert changed.status_code == 201
    assert changed.json()["worldRevision"] == ""


def test_sm05_first_stock_settings_replay_is_identical(api):
    world = db.save_planning_state({"machines": [], "orders": []}, can_manage_settings=True)
    stock = {"version": 1, "limits": [dict(groupId=g, min=0, max=10) for g in ["turning-end", "drilling-end", "visual-front", "warehouse"]], "opening": [], "scrap": []}
    body = dict(version=1, transactionId="stock-first", expectedUpdatedAt=world["updatedAt"], baseHash=world["stateHash"], delta={"set": {"processStockSettings": stock}, "arrays": {}, "remove": []})
    first = api.patch("/api/planning-state", json=body)
    assert first.status_code == 200, first.text
    second = api.patch("/api/planning-state", json=body)
    assert second.status_code == 200, second.text
    assert second.json()["replayed"] is True
    assert second.json()["updatedAt"] == first.json()["updatedAt"]
    changed = copy.deepcopy(body)
    changed["delta"]["set"]["processStockSettings"]["limits"][0]["max"] = 20
    assert api.patch("/api/planning-state", json=changed).status_code == 422


def test_sm05_deleted_creation_receipt_still_acknowledges(factory, api):
    body = dict(id="receipt-demo", name="Demo", requestId="create-demo", worldRevision=db.planning_state()["updatedAt"], delta={"set": {}, "arrays": {}, "remove": []})
    assert api.post("/api/scenarios/from-world", json=body).status_code == 201
    assert api.delete("/api/scenarios/receipt-demo?revision=1").status_code == 200
    receipt = api.get("/api/collaboration/requests/create-demo?kind=draft")
    assert receipt.status_code == 200, receipt.text
    assert receipt.json()["committed"] is True
    replay = api.post("/api/scenarios/from-world", json=body)
    assert replay.status_code == 201, replay.text
    assert replay.json()["deletedScenarioId"] == "receipt-demo"
    assert replay.json()["scenario"] is None
    assert api.get("/api/scenarios/receipt-demo").status_code == 404


def test_sm06_malformed_import_rejected_and_legacy_neighbor_visible(factory, api):
    bad = {**scenario(factory["seed"]), "result": {"summary": {"plannedBatchCount": "bad"}}}
    assert api.post("/api/scenarios", json=bad).status_code == 422
    # Existing historical row from the previously permissive API.
    legacy = collab.save_scenario(bad, A)
    collab.share_scenario(legacy["id"], 1, True, A)
    collab.save_scenario({**scenario(factory["seed"]), "id": "private"}, A)
    main.app.dependency_overrides[current_user] = lambda: B
    reply = api.get("/api/scenarios/list")
    assert reply.status_code == 200, reply.text
    assert [row["id"] for row in reply.json()["items"]] == [legacy["id"]]
    assert reply.json()["items"][0]["plannedBatchCount"] == 0


def test_sm09_concurrent_disjoint_edits_and_resolution_time(api):
    url = "/api/feedbacks/" + api.post("/api/feedbacks", json={"body": "before"}).json()["id"]
    with ThreadPoolExecutor(max_workers=2) as pool:
        replies = list(pool.map(lambda payload: api.patch(url, json=payload), [{"status": "resolved"}, {"body": "after"}]))
    assert all(reply.status_code == 200 for reply in replies)
    row = next(row for row in api.get("/api/feedbacks").json() if url.endswith(row["id"]))
    assert (row["status"], row["body"]) == ("resolved", "after")
    again = api.patch(url, json={"priority": 1}).json()
    assert again["resolved_at"] == row["resolved_at"]
    api.patch(url, json={"status": "active"})
    assert api.patch(url, json={"status": "resolved"}).json()["resolved_at"] > row["resolved_at"]


def test_sm11_first_refresh_preview_matches_actual_key_ownership():
    source = {"processWaitSettings": {"turning": {"enabled": True, "workdays": 1}}}
    local = {}
    preview = settings_key_differences(source, local, None)
    merged = merge_production_refresh_reviewed(source, local, None, {key: "use-source" for key in REFRESH_GROUPS})
    assert "processWaitSettings" in preview["keptLocal"]
    assert "processWaitSettings" not in preview["fromSource"]
    assert "processWaitSettings" not in merged
    for baseline in ({}, source):
        preview = settings_key_differences(source, local, baseline)
        merged = merge_production_refresh_reviewed(source, local, baseline, {key: "use-source" for key in REFRESH_GROUPS})
        for key in preview["fromSource"]:
            assert merged[key] == source[key]


def test_sm13_excel_text_is_literal():
    for name in ["=1+1", "=HYPERLINK(\"https://example.test\")", "Maintenance"]:
        book = load_workbook(BytesIO(build_calendar_event_workbook({"rows": [{"name": name}]})))
        cell = book["Bakım ve Mesai"]["E6"]
        assert cell.value == name
        assert cell.data_type == "s"


def test_sm07_concurrent_fork_and_import_retries_have_one_result(factory, api):
    body = scenario(factory["seed"])
    created = api.post("/api/scenarios", json=body).json()
    with ThreadPoolExecutor(max_workers=2) as pool:
        forks = list(pool.map(lambda _: api.post("/api/scenarios/plan-a/fork?requestId=copy-one"), range(2)))
    assert all(result.status_code == 201 for result in forks)
    assert len({result.json()["id"] for result in forks}) == 1
    assert api.post("/api/scenarios/plan-a/fork?requestId=copy-two").json()["id"] != forks[0].json()["id"]
    assert api.post("/api/scenarios", json=body).json()["revision"] == created["revision"]
    assert api.post("/api/scenarios", json={**body, "notes": "different"}).status_code == 409


def test_sm08_attachment_batch_is_atomic_and_retry_safe(api, monkeypatch):
    body = {"body": "Example", "requestId": "note-one"}
    with ThreadPoolExecutor(max_workers=2) as pool:
        notes = list(pool.map(lambda _: api.post("/api/feedbacks", json=body), range(2)))
    assert all(result.status_code == 201 for result in notes)
    assert len({result.json()["id"] for result in notes}) == 1
    url = "/api/feedbacks/" + notes[0].json()["id"] + "/attachments?requestId=files-one"
    bad = [("files", ("a.txt", b"ok", "text/plain")), ("files", ("empty.txt", b"", "text/plain"))]
    for _ in range(2):
        assert api.post(url, files=bad).status_code == 413
    assert api.get("/api/feedbacks").json()[0]["attachments"] == []
    assert list(main.settings.upload_dir.iterdir()) == []
    files = [("files", ("a.txt", b"ok", "text/plain")), ("files", ("b.txt", b"second", "text/plain"))]
    original = Path.write_bytes
    writes = 0
    def fail_second(path, content):
        nonlocal writes
        writes += 1
        if writes == 2:
            raise OSError("synthetic disk error")
        return original(path, content)
    with monkeypatch.context() as scoped:
        scoped.setattr(Path, "write_bytes", fail_second)
        assert api.post(url, files=files).status_code == 500
    assert list(main.settings.upload_dir.iterdir()) == []
    assert api.get("/api/feedbacks").json()[0]["attachments"] == []
    for _ in range(2):
        assert api.post(url, files=files).status_code == 201
    assert len(api.get("/api/feedbacks").json()[0]["attachments"]) == 2
    assert len(list(main.settings.upload_dir.iterdir())) == 2
    assert api.post(url, files=[("files", ("changed.txt", b"different", "text/plain"))]).status_code == 409


def test_sm10_history_commits_with_official_import_and_is_immutable(api):
    dataset = {"format": "confirmed-overview", "importedAt": "2026-11-07T10:00:00Z",
               "sourceFile": "sample.xlsx", "snapshotDate": "2026-11-07",
               "weeks": [], "products": []}
    record = db._demand_import_record(dataset)
    assert api.post("/api/order-imports/history", json=record).status_code == 409
    assert db.demand_import_history() == []
    db.save_planning_state({"orders": [], "machines": [], "customerDemand": dataset}, can_manage_settings=True)
    assert db.demand_import_history() == [record]
    assert api.post("/api/order-imports/history", json=record).status_code == 201
    assert api.post("/api/order-imports/history", json={**record, "summary": {"totalDemand": 999}}).status_code == 409
    main.app.dependency_overrides[current_user] = lambda: B
    assert api.post("/api/order-imports/history", json=record).status_code == 403
    assert db.demand_import_history() == [record]


def test_sm10_failed_official_transaction_leaves_no_import_history(api, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("synthetic history failure")
    monkeypatch.setattr(db, "_insert_planning_history", fail)
    dataset = {"importedAt": "2026-11-07T10:00:00Z", "sourceFile": "example.xlsx", "snapshotDate": "2026-11-07", "weeks": [], "products": []}
    with pytest.raises(RuntimeError):
        db.save_planning_state({"orders": [], "machines": [], "customerDemand": dataset}, can_manage_settings=True)
    assert db.planning_state() is None
    assert db.demand_import_history() == []


def test_sm13_archive_and_overview_names_remain_literal():
    from app.production_archive_export import build_production_archive_workbook
    from app.overview_export import build_overview_workbook
    outputs = [
        build_production_archive_workbook({"status": "semi-finished", "rows": [{"machineName": "=1+1", "product": "Demo", "completedQuantity": 1}]}),
        build_overview_workbook({"machines": [{"id": "C-01", "name": "=1+1", "rows": [{"product": "=1+1", "kind": "planned"}]}], "summary": {}}),
    ]
    for output in outputs:
        workbook = load_workbook(BytesIO(output))
        cells = [cell for sheet in workbook for row in sheet for cell in row if cell.value == "=1+1"]
        assert cells, "Synthetic name must be present in the actual workbook"
        assert all(cell.data_type == "s" for cell in cells)
