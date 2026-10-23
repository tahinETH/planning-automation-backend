"""Regression coverage for the October 2026 performance release."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from contextlib import contextmanager
import re
from threading import Barrier
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app import collaboration as collab
from app import database as db
from app.auth import CurrentUser, current_user


A = CurrentUser("perf-owner", "Owner", "owner@example.test", "admin")
B = CurrentUser("perf-other", "Other", "other@example.test", "user")


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(
        db,
        "settings",
        SimpleNamespace(database_path=tmp_path / "performance.sqlite", upload_dir=tmp_path / "uploads"),
    )
    db.init_database()
    db.save_planning_state({"orders": [], "machines": []}, can_manage_settings=True)


@pytest.fixture
def factory():
    return json.loads((Path(__file__).parent / "fixtures" / "collaboration.json").read_text())


def scenario(name="Draft", seed=None):
    return {
        "id": name.lower().replace(" ", "-"),
        "name": name,
        "createdAt": "2026-10-23T09:00:00Z",
        "notes": "",
        "seed": seed or {"orders": [], "machines": [], "activePlanRun": {"id": "run-a"}},
        "result": {"summary": {"plannedBatchCount": 1}, "planRun": {"id": "run-a"}},
    }


def _client(monkeypatch, user=A):
    from fastapi.testclient import TestClient
    from app.main import app

    monkeypatch.setitem(app.dependency_overrides, current_user, lambda: user)
    return TestClient(app)


def _large_seed(count=4000):
    return {
        "orders": [],
        "machines": [],
        "wipLots": [{"id": f"lot-{index}", "availableQuantity": 10} for index in range(count)],
        "productionHistory": [{"id": f"history-{index}", "quantity": 10} for index in range(count)],
    }


def test_perf_n04_history_and_revision_summaries_omit_large_snapshots(monkeypatch):
    from app.main import app

    large = _large_seed()
    db.save_planning_state(large, can_manage_settings=True, actor_id=A.id, actor_name=A.name)
    state = db.planning_state()
    with db.connection() as conn:
        conn.execute(
            "INSERT INTO order_revisions VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                "revision-a", "order-a", "Widget", "approved", "2026-10-23T09:00:00Z",
                "2026-10-23T09:00:00Z", json.dumps({"quantity": 10}), json.dumps({"quantity": 12}),
                json.dumps({"changed": True}), json.dumps(large), json.dumps({"summary": {"plannedBatchCount": 1}}),
            ),
        )

    monkeypatch.setitem(app.dependency_overrides, current_user, lambda: A)
    client = _client(monkeypatch)
    history = client.get("/api/planning-state/history?summary=true")
    assert history.status_code == 200
    assert history.json()[0]["id"]
    assert history.json()[0]["createdAt"]
    assert history.json()[0]["createdBy"] == {"id": A.id, "name": A.name}
    expected_open_wip = sum(
        1 for lot in state["seed"].get("wipLots", [])
        if lot.get("availableQuantity", 0) > 0 and lot.get("stage") not in ("delivered", "scrapped")
    )
    assert history.json()[0]["openWipCount"] == expected_open_wip
    assert "seed" not in history.json()[0]

    revisions = client.get("/api/revisions?summary=true")
    assert revisions.status_code == 200
    assert len(revisions.json()) == 1
    summary = revisions.json()[0]
    assert summary["id"] == "revision-a"
    assert summary["original"] == {"quantity": 10}
    assert summary["requested"] == {"quantity": 12}
    assert summary["impact"] == {"changed": True}
    assert "seed" not in summary and "result" not in summary
    assert len(json.dumps(summary)) < len(json.dumps(large))

    # Old callers still receive complete snapshots.
    legacy_history = client.get("/api/planning-state/history")
    assert legacy_history.status_code == 200
    assert legacy_history.json()[0]["seed"] == state["seed"]
    legacy_revisions = client.get("/api/revisions")
    assert legacy_revisions.status_code == 200
    assert legacy_revisions.json()[0]["seed"] == large
    assert legacy_revisions.json()[0]["result"] == {"summary": {"plannedBatchCount": 1}}

    detail = client.get(f"/api/planning-state/history/{history.json()[0]['id']}")
    assert detail.status_code == 200
    assert detail.json()["seed"] == state["seed"]
    revision_detail = client.get("/api/revisions/revision-a")
    assert revision_detail.status_code == 200
    assert revision_detail.json()["seed"] == large
    assert client.get("/api/planning-state/history/missing").status_code == 404
    assert client.get("/api/revisions/missing").status_code == 404


def test_perf_n04_collaboration_status_avoids_world_seed_and_hash(monkeypatch):
    original_world = collab._world

    def fail_world(_db):
        raise AssertionError("status read loaded the full world")

    monkeypatch.setattr(collab, "_world", fail_world)
    try:
        status = collab.collaboration_status()
    finally:
        monkeypatch.setattr(collab, "_world", original_world)
    assert status["worldRevision"]
    assert status["publicationId"] is None
    assert status["activePublication"] is None


def test_perf_n04_collaboration_status_keeps_missing_world_conflict():
    with db.connection() as conn:
        conn.execute("DELETE FROM planning_state WHERE state_key='default'")
    with pytest.raises(HTTPException) as error:
        collab.collaboration_status()
    assert error.value.status_code == 409


def test_perf_n04_paged_scenario_list_does_not_select_snapshot_columns(monkeypatch):
    saved = collab.save_scenario(scenario(), A)
    statements = []
    original_connection = collab.connection

    @contextmanager
    def traced_connection():
        with original_connection() as conn:
            conn.set_trace_callback(statements.append)
            yield conn

    monkeypatch.setattr(collab, "connection", traced_connection)
    page = collab.list_scenarios(A, limit=20, offset=0)
    assert page["total"] == 1 and page["hasMore"] is False
    assert page["items"][0]["id"] == saved["id"]
    select_sql = [sql.lower() for sql in statements if sql.lstrip().lower().startswith("select")]
    assert select_sql
    whole_snapshot = re.compile(r"select\s+(?:.*?,\s*)?(?:s\.)?(?:inputs_json|result_json)\s*(?:,|from)\b", re.DOTALL)
    assert all(not whole_snapshot.search(sql) and not re.search(r"select\s+(?:s\.)?\*", sql) for sql in select_sql)
    assert any("json_extract(s.result_json" in sql for sql in select_sql)
    assert "seed" not in page["items"][0] and "result" not in page["items"][0]
    assert collab.list_scenarios(A)[0]["seed"] == saved["seed"]


def test_perf_n04_scenario_pages_keep_owner_shared_and_legacy_visibility():
    owned = collab.save_scenario(scenario("Owned"), A)
    private = collab.save_scenario(scenario("Private"), B)
    shared = collab.save_scenario(scenario("Shared"), B)
    collab.share_scenario(shared["id"], shared["revision"], True, B)
    with db.connection() as conn:
        conn.execute(
            "INSERT INTO scenarios VALUES(?,?,?,?,?,?)",
            ("legacy-list", "Legacy", "2026-10-22T09:00:00Z", "", '{"orders":[],"machines":[]}', '{"summary":{}}'),
        )

    first = collab.list_scenarios(A, limit=2, offset=0)
    second = collab.list_scenarios(A, limit=2, offset=2)
    ids = {item["id"] for item in first["items"] + second["items"]}
    assert first["total"] == 3 and first["hasMore"] is True
    assert second["offset"] == 2 and second["hasMore"] is False
    assert ids == {owned["id"], shared["id"], "legacy-list"}
    assert private["id"] not in ids
    with pytest.raises(HTTPException) as error:
        collab.get_scenario(private["id"], A)
    assert error.value.status_code == 404
    legacy = collab.get_scenario("legacy-list", A)
    assert legacy["legacy"] is True and legacy["canEdit"] is False


def _patch_value(saved, request_id, **delta_fields):
    from app.planning_delta import build_delta

    changed = {**saved["seed"], **delta_fields}
    return {
        "requestId": request_id,
        "revision": saved["revision"],
        "worldRevision": db.planning_state()["updatedAt"],
        "delta": build_delta(saved["seed"], changed),
        "responseMode": "compact-v1",
    }


def test_perf_n05_compact_response_reconstructs_canonical_saved_record(monkeypatch):
    from app.planning_delta import apply_delta, state_hash

    saved = collab.save_scenario(scenario(), A)
    request = _patch_value(saved, "compact-write", activePlanRun={"id": "client-run", "client": True})
    monkeypatch.setattr(collab, "run_domain", lambda request: {
        "seed": {**request["seed"], "activePlanRun": {"id": "server-run", "accepted": True}},
        "result": {"summary": {"plannedBatchCount": 2}, "planRun": {"id": "server-run"}},
    })
    response = collab.patch_scenario(saved["id"], request, A)
    compact = response["scenarioSeedCorrection"]
    result_compact = response["scenarioResultCorrection"]
    assert response["replayed"] is False
    assert set(compact) == {"baseHash", "stateHash", "delta"}
    assert set(result_compact) == {"baseHash", "stateHash", "delta"}
    base = apply_delta(saved["seed"], request["delta"])
    assert compact["baseHash"] == state_hash(base)
    reconstructed = apply_delta(base, compact["delta"])
    canonical = collab.get_scenario(saved["id"], A)
    assert state_hash(reconstructed) == compact["stateHash"] == state_hash(canonical["seed"])
    assert result_compact["baseHash"] == state_hash(saved["result"])
    reconstructed_result = apply_delta(saved["result"], result_compact["delta"])
    assert state_hash(reconstructed_result) == result_compact["stateHash"] == state_hash(canonical["result"])
    assert "seed" not in response["scenario"]
    assert "result" not in response["scenario"]
    assert response["scenario"]["revision"] == canonical["revision"]
    assert canonical["result"] == {"summary": {"plannedBatchCount": 2}, "planRun": {"id": "server-run"}}


def test_perf_n05_legacy_patch_returns_full_record_and_replay_returns_current(monkeypatch):
    saved = collab.save_scenario(scenario(), A)
    request = _patch_value(saved, "legacy-write", activePlanRun={"id": "first-edit"})
    request.pop("responseMode")
    monkeypatch.setattr(collab, "run_domain", lambda value: {"seed": value["seed"], "result": {"summary": {"plannedBatchCount": 2}}})
    accepted = collab.patch_scenario(saved["id"], request, A)
    assert accepted["scenario"]["seed"] == collab.get_scenario(saved["id"], A)["seed"]
    assert accepted["scenario"]["revision"] == 2

    later = collab.get_scenario(saved["id"], A)
    later_request = _patch_value(later, "later-write", activePlanRun={"id": "later-edit"})
    later_request.pop("responseMode")
    collab.patch_scenario(saved["id"], later_request, A)
    replay = collab.patch_scenario(saved["id"], request, A)
    assert replay["replayed"] is True
    assert replay["appliedRevision"] == 2
    assert replay["scenario"]["revision"] == 3
    assert replay["scenario"]["seed"]["activePlanRun"] == {"id": "later-edit"}
    with db.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM scenario_versions WHERE scenario_id=?", (saved["id"],)).fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM scenario_requests WHERE scenario_id=?", (saved["id"],)).fetchone()[0] == 2


def test_perf_n05_legacy_receipt_replays_after_response_mode_changes(monkeypatch):
    saved = collab.save_scenario(scenario(), A)
    legacy_request = _patch_value(saved, "legacy-receipt", activePlanRun={"id": "accepted"})
    legacy_request.pop("responseMode")
    monkeypatch.setattr(collab, "run_domain", lambda value: {"seed": value["seed"], "result": {"summary": {"plannedBatchCount": 1}}})

    accepted = collab.patch_scenario(saved["id"], legacy_request, A)
    assert accepted["replayed"] is False
    assert accepted["scenario"]["revision"] == 2
    assert "seed" in accepted["scenario"]

    negotiated_retry = {**legacy_request, "responseMode": "compact-v1"}
    replay = collab.patch_scenario(saved["id"], negotiated_retry, A)
    assert replay["replayed"] is True
    assert replay["appliedRevision"] == accepted["appliedRevision"] == 2
    assert replay["scenario"] == accepted["scenario"]
    assert "scenarioSeedCorrection" not in replay
    with db.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM scenario_versions WHERE scenario_id=?", (saved["id"],)).fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM scenario_requests WHERE request_id=?", (legacy_request["requestId"],)).fetchone()[0] == 1


def test_perf_n06_same_base_writers_have_one_winner(monkeypatch):
    saved = collab.save_scenario(scenario(), A)
    gate = Barrier(2)

    def validate(request):
        gate.wait(timeout=2)
        return {"seed": request["seed"], "result": {"summary": {"plannedBatchCount": 1}}}

    monkeypatch.setattr(collab, "run_domain", validate)
    requests = [
        _patch_value(saved, "same-base-one", activePlanRun={"id": "one"}),
        _patch_value(saved, "same-base-two", activePlanRun={"id": "two"}),
    ]

    def write(request):
        try:
            return collab.patch_scenario(saved["id"], request, A)
        except HTTPException as error:
            return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(write, requests))
    assert sum(isinstance(result, dict) for result in results) == 1
    assert results.count(409) == 1
    assert collab.get_scenario(saved["id"], A)["revision"] == 2
    with db.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM scenario_versions WHERE scenario_id=?", (saved["id"],)).fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM scenario_requests WHERE scenario_id=?", (saved["id"],)).fetchone()[0] == 1


def test_perf_n06_different_drafts_can_validate_and_save_at_once(monkeypatch):
    first = collab.save_scenario(scenario("First"), A)
    second = collab.save_scenario(scenario("Second"), A)
    gate = Barrier(2)

    def validate(request):
        gate.wait(timeout=2)
        return {"seed": request["seed"], "result": {"summary": {"plannedBatchCount": 1}}}

    monkeypatch.setattr(collab, "run_domain", validate)
    requests = [
        (first, _patch_value(first, "draft-one", activePlanRun={"id": "first"})),
        (second, _patch_value(second, "draft-two", activePlanRun={"id": "second"})),
    ]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda pair: collab.patch_scenario(pair[0]["id"], pair[1], A), requests))
    assert all(result["appliedRevision"] == 2 for result in results)
    assert collab.get_scenario(first["id"], A)["seed"]["activePlanRun"] == {"id": "first"}
    assert collab.get_scenario(second["id"], A)["seed"]["activePlanRun"] == {"id": "second"}


@pytest.mark.parametrize("change", ["world", "revoke", "delete", "draft"])
def test_perf_n06_rechecks_state_after_validation(monkeypatch, change):
    saved = collab.save_scenario(scenario(), A)
    if change == "revoke":
        collab.share_scenario(saved["id"], saved["revision"], True, A)
    request = _patch_value(saved, f"during-validation-{change}", activePlanRun={"id": "candidate"})
    changed = False

    def validate(value):
        nonlocal changed
        if not changed:
            changed = True
            if change == "world":
                db.save_planning_state({"orders": [], "machines": [], "wipLots": [{"id": "new-world"}]}, can_manage_settings=True, actor_id=A.id, actor_name=A.name)
            elif change == "revoke":
                with db.connection() as conn:
                    conn.execute("UPDATE scenario_owners SET owner_id=?,owner_name=?,shared=0 WHERE scenario_id=?", (B.id, B.name, saved["id"]))
            elif change == "delete":
                collab.delete_scenario(saved["id"], collab.get_scenario(saved["id"], A)["revision"], A)
            elif change == "draft":
                collab.save_scenario({**collab.get_scenario(saved["id"], A), "name": "intervening"}, A)
        return {"seed": value["seed"], "result": {"summary": {"plannedBatchCount": 1}}}

    monkeypatch.setattr(collab, "run_domain", validate)
    with pytest.raises(HTTPException) as error:
        collab.patch_scenario(saved["id"], request, A)
    assert error.value.status_code in (403, 404, 409)
    with db.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM scenario_requests WHERE request_id=?", (request["requestId"],)).fetchone()[0] == 0


def test_perf_n06_receipt_insert_failure_rolls_back_draft_and_version(monkeypatch):
    saved = collab.save_scenario(scenario(), A)
    request = _patch_value(saved, "receipt-failure", activePlanRun={"id": "must-roll-back"})
    monkeypatch.setattr(collab, "run_domain", lambda value: {"seed": value["seed"], "result": {"summary": {"plannedBatchCount": 1}}})
    with db.connection() as conn:
        conn.execute(
            "CREATE TRIGGER fail_scenario_receipt BEFORE INSERT ON scenario_requests "
            "BEGIN SELECT RAISE(ABORT, 'receipt insert failure'); END"
        )
    with pytest.raises(Exception, match="receipt insert failure"):
        collab.patch_scenario(saved["id"], request, A)
    assert collab.get_scenario(saved["id"], A) == saved
    with db.connection() as conn:
        row = conn.execute("SELECT name,inputs_json,result_json FROM scenarios WHERE id=?", (saved["id"],)).fetchone()
        assert row["name"] == saved["name"]
        assert json.loads(row["inputs_json"]) == saved["seed"]
        assert json.loads(row["result_json"]) == saved["result"]
        owner = conn.execute("SELECT revision,updated_at FROM scenario_owners WHERE scenario_id=?", (saved["id"],)).fetchone()
        assert owner["revision"] == saved["revision"]
        assert owner["updated_at"] == saved["updatedAt"]
        assert conn.execute("SELECT COUNT(*) FROM scenario_versions WHERE scenario_id=?", (saved["id"],)).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM scenario_requests WHERE scenario_id=?", (saved["id"],)).fetchone()[0] == 0


def _from_world_request(seed, world_revision, request_id="world-copy-request", scenario_id="world-copy"):
    from app.planning_delta import build_delta

    base = collab.planning_only(seed)
    return {
        "id": scenario_id,
        "name": "World copy",
        "requestId": request_id,
        "worldRevision": world_revision,
        "delta": build_delta(base, base),
    }


def test_perf_n05_from_world_creation_is_atomic_and_lost_reply_safe(factory, monkeypatch):
    from app.main import app

    saved_world = db.save_planning_state(
        factory["seed"], can_manage_settings=True, actor_id=A.id, actor_name=A.name,
        flow_settings_version=1, route_placement_version=1, production_split_version=1,
        process_wait_settings_version=1,
    )
    request = _from_world_request(factory["seed"], saved_world["updatedAt"])
    before = db.planning_state()
    client = _client(monkeypatch)

    first = client.post("/api/scenarios/from-world", json=request)
    assert first.status_code == 201, first.text
    accepted = first.json()
    assert accepted["replayed"] is False
    assert accepted["appliedRevision"] == accepted["scenario"]["revision"] == 1
    draft = accepted["scenario"]
    assert draft["ownerId"] == A.id and draft["canEdit"] is True
    assert draft["seed"]["orders"] == before["seed"]["orders"]
    assert draft["seed"]["orders"][0]["quantity"] == 100
    assert draft["seed"]["wipLots"] == []
    assert draft["seed"]["productionHistory"] == []
    assert draft["seed"]["wipMovements"] == []
    assert all(not (machine.get("currentJob") or {}).get("quantity") for machine in draft["seed"]["machines"])
    assert db.planning_state() == before
    assert sum(lot["availableQuantity"] for lot in before["seed"]["wipLots"]) == 200

    # A retry after a lost reply returns the saved full record and adds no version.
    retry = client.post("/api/scenarios/from-world", json=request)
    assert retry.status_code == 201, retry.text
    assert retry.json()["replayed"] is True
    assert retry.json()["appliedRevision"] == 1
    assert retry.json()["scenario"] == draft
    with db.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM scenario_versions WHERE scenario_id=?", (request["id"],)).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM scenario_requests WHERE request_id=?", (request["requestId"],)).fetchone()[0] == 1

    changed_body = {**request, "name": "Changed body"}
    assert client.post("/api/scenarios/from-world", json=changed_body).status_code == 409
    changed_id = {**request, "requestId": "new-id-for-used-scenario"}
    assert client.post("/api/scenarios/from-world", json=changed_id).status_code == 409

    other_client = _client(monkeypatch, B)
    other = other_client.post("/api/scenarios/from-world", json=request)
    assert other.status_code in (403, 404, 409)
    assert "scenario" not in other.json()
    with db.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM scenario_versions WHERE scenario_id=?", (request["id"],)).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM scenario_requests WHERE request_id=?", (request["requestId"],)).fetchone()[0] == 1
    app.dependency_overrides.pop(current_user, None)


def test_perf_n06_from_world_creation_rejects_world_change_during_validation(factory, monkeypatch):
    saved_world = db.save_planning_state(
        factory["seed"], can_manage_settings=True, actor_id=A.id, actor_name=A.name,
        flow_settings_version=1, route_placement_version=1, production_split_version=1,
        process_wait_settings_version=1,
    )
    request = _from_world_request(factory["seed"], saved_world["updatedAt"], "world-change-request", "world-change-draft")

    def change_world(_value):
        db.save_planning_state(
            {"orders": [], "machines": [], "worldMarker": "changed during validation"},
            can_manage_settings=True, actor_id=A.id, actor_name=A.name,
            flow_settings_version=1, route_placement_version=1, production_split_version=1,
            process_wait_settings_version=1,
        )
        return {"seed": collab.planning_only(factory["seed"]), "result": {"summary": {"plannedBatchCount": 0}}}

    monkeypatch.setattr(collab, "run_domain", change_world)
    with pytest.raises(HTTPException) as error:
        collab.create_scenario_from_world(request, A)
    assert error.value.status_code == 409
    with db.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM scenarios WHERE id=?", (request["id"],)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM scenario_versions WHERE scenario_id=?", (request["id"],)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM scenario_requests WHERE request_id=?", (request["requestId"],)).fetchone()[0] == 0


def test_perf_n05_compact_production_command_keeps_receipt_and_physical_history(factory):
    from app import planning_delta

    opening = db.save_planning_state(
        factory["seed"], can_manage_settings=True, actor_id=A.id, actor_name=A.name,
        flow_settings_version=1, route_placement_version=1, production_split_version=1,
        process_wait_settings_version=1,
    )
    command = {**factory["commands"][0], "responseMode": "compact-v1"}
    first = collab.production_command(command, A)
    assert first["replayed"] is False
    assert first["current"]["seed"]["wipLots"][0]["availableQuantity"] == 20
    assert "historyEntry" not in first["current"]
    assert "archiveSnapshot" not in first["current"]

    stored = db.planning_state()
    assert stored["seed"]["wipLots"][0]["availableQuantity"] == 20
    assert stored["seed"]["wipLots"][0]["deliveredQuantity"] == 80
    assert sum(row["quantity"] for row in stored["seed"]["wipMovements"] if row.get("kind") == "delivered") == 80
    assert planning_delta.state_hash(stored["seed"]) != planning_delta.state_hash(opening["seed"])
    with db.connection() as conn:
        history_count = conn.execute("SELECT COUNT(*) FROM planning_state_history").fetchone()[0]
        archive_count = conn.execute("SELECT COUNT(*) FROM production_archive_snapshots").fetchone()[0]
        command_count = conn.execute("SELECT COUNT(*) FROM production_commands").fetchone()[0]
        assert history_count >= 2
        assert archive_count >= 1
        assert command_count == 1
        assert conn.execute("SELECT seed_json FROM planning_state_history ORDER BY created_at DESC LIMIT 1").fetchone()[0]

    # Changing only response negotiation must replay the receipt without another write.
    retry = collab.production_command({k: v for k, v in command.items() if k != "responseMode"}, A)
    assert retry["replayed"] is True
    assert retry["appliedRevision"] == first["appliedRevision"]
    assert retry["current"]["seed"] == stored["seed"]
    assert retry["current"]["seed"]["wipLots"][0]["availableQuantity"] == 20
    with db.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM production_commands").fetchone()[0] == command_count
        assert conn.execute("SELECT COUNT(*) FROM planning_state_history").fetchone()[0] == history_count
        assert conn.execute("SELECT COUNT(*) FROM production_archive_snapshots").fetchone()[0] == archive_count


def test_perf_n05_legacy_production_receipt_replays_with_compact_mode(factory):
    db.save_planning_state(
        factory["seed"], can_manage_settings=True, actor_id=A.id, actor_name=A.name,
        flow_settings_version=1, route_placement_version=1, production_split_version=1,
        process_wait_settings_version=1,
    )
    with db.connection() as conn:
        history_before = conn.execute("SELECT COUNT(*) FROM planning_state_history").fetchone()[0]
    legacy_request = factory["commands"][0]
    accepted = collab.production_command(legacy_request, A)
    assert accepted["replayed"] is False
    assert "historyEntry" in accepted["current"]
    compact_retry = {**legacy_request, "responseMode": "compact-v1"}
    replay = collab.production_command(compact_retry, A)
    assert replay["replayed"] is True
    assert replay["appliedRevision"] == accepted["appliedRevision"]
    assert replay["current"]["seed"]["wipLots"][0]["availableQuantity"] == 20
    with db.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM production_commands").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM planning_state_history").fetchone()[0] == history_before + 1


def test_perf_n05_compact_publication_reply_keeps_history_in_database(factory, monkeypatch):
    from app.main import app

    world = db.save_planning_state(
        factory["seed"], can_manage_settings=True, actor_id=A.id, actor_name=A.name,
        flow_settings_version=1, route_placement_version=1, production_split_version=1,
        process_wait_settings_version=1,
    )
    draft = collab.save_scenario({
        **scenario("Publication draft", collab.planning_only(factory["seed"])),
        "worldRevision": world["updatedAt"],
    }, A)
    preview = collab.publication_preview(draft["id"], {
        "revision": draft["revision"], "worldRevision": world["updatedAt"], "previousId": None,
    }, A)
    client = _client(monkeypatch)
    result = client.post(f"/api/scenarios/{draft['id']}/publish", json={
        "previewId": preview["previewId"], "revision": draft["revision"],
        "worldRevision": world["updatedAt"], "previousId": None, "responseMode": "compact-v1",
    })
    assert result.status_code == 200, result.text
    current = result.json()["current"]
    assert "historyEntry" not in current
    assert "archiveSnapshot" not in current
    with db.connection() as conn:
        history = conn.execute("SELECT seed_json FROM planning_state_history ORDER BY created_at DESC LIMIT 1").fetchone()
        assert history is not None
        assert json.loads(history["seed_json"]) == db.planning_state()["seed"]
        assert conn.execute("SELECT COUNT(*) FROM published_plans WHERE id=?", (result.json()["publicationId"],)).fetchone()[0] == 1
    app.dependency_overrides.pop(current_user, None)
