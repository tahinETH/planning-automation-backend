"""Two authenticated accounts keep proposals separate from shared production.

All records are synthetic. These tests use HTTP routes and the packaged domain
runtime. They do not contact a browser, an identity provider or a live service.
"""
import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import collaboration as collab
from app import database as db
from app.auth import create_test_session
from app.config import settings
from app.main import app
from app.planning_delta import build_delta, state_hash
from app.production_area import production_area


def auth(role="admin", area="torna"):
    return {"Authorization": f"Bearer {create_test_session(settings.admin_password, role)}",
            "X-Production-Area": area}


def ok(response, status=200):
    assert response.status_code == status, response.text
    return response.json()


def queue(seed):
    return [row["id"] for row in sorted(seed["manualBatches"], key=lambda row: row["planColumn"])]


def facts(seed):
    return {field: copy.deepcopy(seed.get(field)) for field in collab.FACTS} | {
        "currentJobs": [copy.deepcopy(row["currentJob"]) for row in seed["machines"]]}


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.setitem(settings.__dict__, "database_path", tmp_path / "reconciliation.sqlite")
    monkeypatch.setitem(settings.__dict__, "upload_dir", tmp_path / "uploads")
    with TestClient(app) as client:
        fixture = json.loads((Path(__file__).parent / "fixtures/collaboration.json").read_text())
        seed = fixture["seed"]
        seed["productionArea"] = "torna"
        seed["manualBatches"] = [dict(id=f"proposal-{index}", machineId="C-04", product="R902745116",
            workOrder=f"PROPOSAL-{index}", quantity=100, start=46280 + index, end=46281 + index,
            status="planned", planColumn=13 + index, sequence=index + 1, locked=False,
            diameter="Ø 19,8", setupHours=0) for index in range(3)]
        seed["planNeedsRecalculation"] = False
        db.save_planning_state(seed, can_manage_settings=True, flow_settings_version=1,
            route_placement_version=1, production_split_version=1, process_wait_settings_version=1)
        token = production_area.set("cubuk-filtre")
        try:
            db.init_database()
            db.save_planning_state({"productionArea": "cubuk-filtre", "orders": [], "machines": []}, can_manage_settings=True)
            other = db.planning_state()
        finally:
            production_area.reset(token)
        yield client, fixture, other


def world(client):
    return ok(client.get("/api/planning-state", headers=auth()))


def draft(client):
    current = world(client)
    return ok(client.post("/api/scenarios/from-world", headers=auth("user"), json={
        "id": "b-private-proposal", "name": "B private proposal", "requestId": "create-b",
        "worldRevision": current["updatedAt"], "delta": {"set": {}, "remove": [], "arrays": {}}}), 201)["scenario"]


def reorder(saved, world_revision, request_id="b-reorder"):
    proposed = copy.deepcopy(saved["seed"])
    proposed["manualBatches"] = [proposed["manualBatches"][2], *proposed["manualBatches"][:2]]
    for index, row in enumerate(proposed["manualBatches"]):
        row["planColumn"] = 13 + index
        row["sequence"] = index + 1
    return {"revision": saved["revision"], "worldRevision": world_revision,
            "requestId": request_id, "delta": build_delta(saved["seed"], proposed)}


def delivery(client, fixture, request_id="a-deliver-12"):
    current = world(client)
    command = copy.deepcopy(fixture["commands"][0])
    command["requestId"] = request_id
    command["command"]["args"][0]["quantity"] = 12
    basis = copy.deepcopy(current["seed"])
    lot = next(row for row in basis["wipLots"] if row["id"] == "lot-a")
    ids = {value for value in [lot["id"], lot.get("sourceHistoryEntryId"), lot.get("sourceBatchId"), lot.get("parentLotId")] if value}
    for field in ["wipLots", "wipMovements", "productionHistory"]:
        basis[field] = [row for row in basis.get(field, []) if any(isinstance(value, str) and value in ids for value in row.values())]
    basis.update(chargeJourneyNotes=[], planningEvents=[], planNeedsRecalculation=False, lastAutomaticPlan=None, planRunSequence=None)
    command["expectedBasis"] = state_hash(basis)
    return command


def assert_balance(current):
    lot = next(row for row in current["seed"]["wipLots"] if row["id"] == "lot-a")
    assert (lot["originalQuantity"], lot["availableQuantity"], lot["deliveredQuantity"]) == (100, 88, 12)
    assert sum(row["quantity"] for row in current["seed"]["wipMovements"] if row["kind"] == "delivered" and row.get("lotId") == "lot-a") == 12


def test_shared_draft01_pre_poll_reorder_accepts_new_production_without_full_world_write(workspace):
    client, fixture, other = workspace
    opening = world(client)
    saved = draft(client)
    # B prepares against W0. A commits W1 before B sends or polls.
    pending = reorder(saved, opening["updatedAt"])
    command = delivery(client, fixture)
    ok(client.post("/api/production/commands", headers=auth(), json=command))
    produced = world(client)
    assert_balance(produced)
    assert produced["updatedAt"] != opening["updatedAt"]
    accepted = ok(client.patch(f"/api/scenarios/{saved['id']}", headers=auth("user"), json=pending))
    current_draft = accepted["scenario"]
    assert current_draft["worldRevision"] == produced["updatedAt"]
    assert queue(current_draft["seed"]) == ["proposal-2", "proposal-0", "proposal-1"]
    assert current_draft["seed"]["planNeedsRecalculation"] is True
    # Personal saves contain no physical records and cannot replace the world.
    assert current_draft["seed"]["wipLots"] == []
    assert current_draft["seed"]["productionHistory"] == []
    assert world(client) == produced
    changed_retry = copy.deepcopy(pending)
    changed_retry["delta"]["set"]["planNeedsRecalculation"] = False
    assert client.patch(f"/api/scenarios/{saved['id']}", headers=auth("user"), json=changed_retry).status_code == 409
    assert world(client) == produced
    reloaded = ok(client.get(f"/api/scenarios/{saved['id']}", headers=auth("user")))
    assert reloaded == current_draft
    composed = collab.run_domain({"action": "compose", "seed": produced["seed"], "draft": reloaded["seed"]})
    assert queue(composed["seed"]) == ["proposal-2", "proposal-0", "proposal-1"]
    assert facts(composed["seed"]) == facts(produced["seed"])
    assert composed["seed"]["planNeedsRecalculation"] is True
    retried = ok(client.patch(f"/api/scenarios/{saved['id']}", headers=auth("user"), json=pending))
    assert retried["replayed"] and retried["appliedRevision"] == accepted["appliedRevision"]
    assert world(client) == produced
    assert ok(client.post("/api/production/commands", headers=auth(), json=command))["replayed"]
    assert world(client) == produced
    assert ok(client.get("/api/planning-state", headers=auth(area="cubuk-filtre"))) == other
    with db.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM production_commands").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM scenario_requests WHERE request_id='b-reorder'").fetchone()[0] == 1


def test_shared_draft02_official_capacity_refresh_and_stale_publication_preserve_delivery(workspace):
    client, fixture, _ = workspace
    opening = world(client)
    saved = draft(client)
    pending = reorder(saved, opening["updatedAt"])
    ok(client.post("/api/production/commands", headers=auth(), json=delivery(client, fixture)))
    produced = world(client)
    changed = copy.deepcopy(produced["seed"])
    next(row for row in changed["machines"] if row["id"] == "C-04")["capacityFactor"] = 0.5
    parameter_patch = dict(version=1, transactionId="official-capacity", expectedUpdatedAt=produced["updatedAt"],
        baseHash=state_hash(produced["seed"]), delta=build_delta(produced["seed"], changed), mode="operational")
    assert client.patch("/api/planning-state", headers=auth("user"), json=parameter_patch).status_code == 403
    assert world(client) == produced
    ok(client.patch("/api/planning-state", headers=auth(), json=parameter_patch))
    official = world(client)
    assert facts(official["seed"]) == facts(produced["seed"])
    accepted = ok(client.patch(f"/api/scenarios/{saved['id']}", headers=auth("user"), json=pending))["scenario"]
    assert next(row for row in accepted["seed"]["machines"] if row["id"] == "C-04")["capacityFactor"] == 0.5
    assert queue(accepted["seed"]) == ["proposal-2", "proposal-0", "proposal-1"]
    assert accepted["seed"]["planNeedsRecalculation"] is True
    accepted = ok(client.post(f"/api/scenarios/{saved['id']}/share?revision={accepted['revision']}&shared=true", headers=auth("user")))
    preview_body = dict(revision=accepted["revision"], worldRevision=official["updatedAt"], previousId=None)
    assert client.post(f"/api/scenarios/{saved['id']}/publication-preview", headers=auth("user"), json=preview_body).status_code == 403
    refused = client.post(f"/api/scenarios/{saved['id']}/publication-preview", headers=auth(), json=preview_body)
    assert refused.status_code in (409, 422), refused.text
    assert world(client) == official
    assert_balance(world(client))
    assert ok(client.get("/api/collaboration/status", headers=auth()))["publicationId"] is None
    # A separate reviewed calculation is required. The frontend domain test
    # checks its arithmetic/order; here the server checks publication and facts.
    reviewed = copy.deepcopy(accepted["seed"])
    reviewed["planNeedsRecalculation"] = False
    published_candidate = collab.run_domain({"action": "publish", "seed": official["seed"], "draft": reviewed})
    patch = dict(revision=accepted["revision"], worldRevision=official["updatedAt"], requestId="reviewed-recalculation",
                 delta=build_delta(accepted["seed"], collab.planning_only(published_candidate["seed"])))
    calculated = ok(client.patch(f"/api/scenarios/{saved['id']}", headers=auth("user"), json=patch))["scenario"]
    preview_body["revision"] = calculated["revision"]
    preview = ok(client.post(f"/api/scenarios/{saved['id']}/publication-preview", headers=auth(), json=preview_body))
    publication = ok(client.post(f"/api/scenarios/{saved['id']}/publish", headers=auth(), json=preview))
    published = world(client)
    assert queue(published["seed"]) == ["proposal-2", "proposal-0", "proposal-1"]
    assert facts(published["seed"]) == facts(official["seed"])
    assert published["seed"]["orders"] == official["seed"]["orders"]
    assert_balance(published)
    assert publication["activePublication"]["approvedBy"]["id"] == "test-admin"
    assert ok(client.post(f"/api/scenarios/{saved['id']}/publish", headers=auth(), json=preview))["replayed"]
    assert world(client) == published


def test_shared_draft03_world_advance_during_normalization_keeps_owner_cas(workspace, monkeypatch):
    client, fixture, _ = workspace
    opening = world(client)
    saved = draft(client)
    pending = reorder(saved, opening["updatedAt"])
    command = delivery(client, fixture)
    original = collab.run_domain
    calls = []

    def interleaved(request):
        result = original(request)
        if request["action"] == "draft":
            calls.append(request)
            if len(calls) == 1:
                # A delivery occurs after B's read snapshot and before B's
                # commit. This is deterministic; no timing guess is used.
                from app.auth import CurrentUser
                collab.production_command(command, CurrentUser("test-admin", "Test Yöneticisi", "admin@example.com", "admin"))
        return result

    monkeypatch.setattr(collab, "run_domain", interleaved)
    accepted = ok(client.patch(f"/api/scenarios/{saved['id']}", headers=auth("user"), json=pending))["scenario"]
    after = world(client)
    assert_balance(after)
    assert accepted["worldRevision"] == after["updatedAt"]
    assert accepted["seed"]["planNeedsRecalculation"] is True
    assert queue(accepted["seed"]) == ["proposal-2", "proposal-0", "proposal-1"]
    assert 2 <= len(calls) <= 4, "A changed world must be normalized again, with bounded work."
    monkeypatch.setattr(collab, "run_domain", original)
    with db.connection() as conn:
        before_versions = conn.execute("SELECT COUNT(*) FROM scenario_versions").fetchone()[0]
    stale = {**pending, "requestId": "stale-same-draft"}
    assert client.patch(f"/api/scenarios/{saved['id']}", headers=auth("user"), json=stale).status_code == 409
    unauthorized = {**pending, "revision": accepted["revision"], "requestId": "take-other-draft"}
    assert client.patch(f"/api/scenarios/{saved['id']}", headers=auth(), json=unauthorized).status_code == 404
    assert client.patch(f"/api/scenarios/{saved['id']}", headers=auth("user", "cubuk-filtre"), json=unauthorized).status_code == 404
    assert client.patch(f"/api/scenarios/{saved['id']}", json=unauthorized).status_code == 401
    assert ok(client.get(f"/api/scenarios/{saved['id']}", headers=auth("user"))) == accepted
    assert world(client) == after
    with db.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM scenario_versions").fetchone()[0] == before_versions


def test_shared_draft07_prepared_publication_refuses_a_later_delivery_without_reverting_facts(workspace):
    client, fixture, _ = workspace
    saved = draft(client)
    saved = ok(client.post(f"/api/scenarios/{saved['id']}/share?revision={saved['revision']}&shared=true", headers=auth("user")))
    preview = ok(client.post(f"/api/scenarios/{saved['id']}/publication-preview", headers=auth(), json={
        "revision": saved["revision"], "worldRevision": world(client)["updatedAt"], "previousId": None}))
    ok(client.post("/api/production/commands", headers=auth("user"), json=delivery(client, fixture)))
    produced = world(client)
    assert_balance(produced)
    refused = client.post(f"/api/scenarios/{saved['id']}/publish", headers=auth(), json=preview)
    assert refused.status_code == 409, refused.text
    assert world(client) == produced
    assert ok(client.get(f"/api/scenarios/{saved['id']}", headers=auth("user"))) == saved
    with db.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM published_plans").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM production_commands").fetchone()[0] == 1


def test_shared_draft08_concurrent_edit_of_the_same_draft_refuses_without_lost_proposals(workspace, monkeypatch):
    client, _, _ = workspace
    opening = world(client)
    saved = draft(client)
    pending = reorder(saved, opening["updatedAt"])
    competing = reorder(saved, opening["updatedAt"], "b-other-tab")
    competing["delta"]["set"]["activePlanningScope"] = {"mode": "orders"}
    original = collab.run_domain
    injected = []

    def interleaved(request):
        normalized = original(request)
        if request["action"] == "draft" and not injected:
            injected.append(True)
            from app.auth import CurrentUser
            injected.append(collab.patch_scenario(saved["id"], competing,
                CurrentUser("test-user", "Test Kullanıcısı", "user@example.com", "user")))
        return normalized

    monkeypatch.setattr(collab, "run_domain", interleaved)
    refused = client.patch(f"/api/scenarios/{saved['id']}", headers=auth("user"), json=pending)
    assert refused.status_code == 409, refused.text
    assert ok(client.get(f"/api/scenarios/{saved['id']}", headers=auth("user"))) == injected[1]["scenario"]
    assert world(client) == opening
    with db.connection() as conn:
        requests = conn.execute("SELECT request_id FROM scenario_requests ORDER BY request_id").fetchall()
        assert [row[0] for row in requests] == ["b-other-tab", "create-b"]


def test_shared_draft12_repeated_world_races_stop_with_425_and_exact_retry_commits_once(workspace, monkeypatch):
    client, _, _ = workspace
    saved = draft(client)
    pending = reorder(saved, world(client)["updatedAt"], "bounded-world-race")
    original = collab.run_domain
    attempts = []

    def advancing_world(request):
        normalized = original(request)
        if request["action"] == "draft":
            attempts.append(True)
            current = db.planning_state()
            changed = copy.deepcopy(current["seed"])
            next(row for row in changed["machines"] if row["id"] == "C-04")["capacityFactor"] = 1 - len(attempts) / 10
            db.save_planning_state(changed, current["updatedAt"], mode="operational", can_manage_settings=True,
                flow_settings_version=1, route_placement_version=1, production_split_version=1, process_wait_settings_version=1)
        return normalized

    monkeypatch.setattr(collab, "run_domain", advancing_world)
    response = client.patch(f"/api/scenarios/{saved['id']}", headers=auth("user"), json=pending)
    assert response.status_code == 425, response.text
    assert len(attempts) == 3, "Repeated world changes must cause bounded work."
    assert ok(client.get(f"/api/scenarios/{saved['id']}", headers=auth("user"))) == saved
    latest_world = world(client)
    with db.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM scenario_requests WHERE request_id=?", (pending["requestId"],)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM scenario_versions WHERE scenario_id=?", (saved["id"],)).fetchone()[0] == 1
    monkeypatch.setattr(collab, "run_domain", original)
    accepted = ok(client.patch(f"/api/scenarios/{saved['id']}", headers=auth("user"), json=pending))
    assert accepted["scenario"]["worldRevision"] == latest_world["updatedAt"]
    assert accepted["scenario"]["seed"]["planNeedsRecalculation"] is True
    assert queue(accepted["scenario"]["seed"]) == ["proposal-2", "proposal-0", "proposal-1"]
    assert ok(client.patch(f"/api/scenarios/{saved['id']}", headers=auth("user"), json=pending))["replayed"] is True
    assert world(client) == latest_world
    with db.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM scenario_requests WHERE request_id=?", (pending["requestId"],)).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM scenario_versions WHERE scenario_id=?", (saved["id"],)).fetchone()[0] == 2


def independent_world(client, fixture):
    seed = copy.deepcopy(fixture["seed"])
    product = {**seed["products"][0], "product": "R902745117", "batchSize": 100}
    seed["products"].append(product)
    machine = next(row for row in seed["machines"] if row["id"] == "C-05")
    machine["currentJob"].update(batchId="independent-100", workOrder="INDEPENDENT-100", product=product["product"],
        quantity=100, originalQuantity=100, remainingQuantity=100, start=46270, end=46275)
    db.save_planning_state(seed, world(client)["updatedAt"], mode="operational", can_manage_settings=True,
        flow_settings_version=1, route_placement_version=1, production_split_version=1, process_wait_settings_version=1)
    return world(client)


@pytest.mark.parametrize("first", ["delivery", "completion"])
def test_shared_ops01_independent_delivery_and_completion_commit_from_the_same_basis_once(workspace, first):
    client, fixture, _ = workspace
    opening = independent_world(client, fixture)
    # These fixed hashes are generated from the canonical synthetic opening
    # with the shipped productionCommandBasis helper. They are protocol fixture
    # values, not another implementation of dependency selection.
    command = delivery(client, fixture)
    command["expectedBasis"] = "0ff891f0517154bfb81914e843f6630e440d57b145bf35c74f18e6030baab0b2"
    completion = dict(requestId="b-independent-completion", expectedBasis="3507f243179410bc9dfd5f078e465447de6636e6a531acd3ea1188eb10993f72",
        command=dict(kind="completeCurrentJob", args=["C-05", 46280, 100]))
    requests = {"delivery": (command, "admin"), "completion": (completion, "user")}
    order = [first, "completion" if first == "delivery" else "delivery"]
    acknowledgements = []
    for kind in order:
        request, role = requests[kind]
        acknowledgements.append(ok(client.post("/api/production/commands", headers=auth(role), json=request)))
    after = world(client)
    assert_balance(after)
    output = [row for row in after["seed"]["productionHistory"] if row.get("sourceBatchId") == "independent-100"]
    assert len(output) == 1 and output[0]["completedQuantity"] == 100
    assert sum(row["availableQuantity"] for row in after["seed"]["wipLots"] if row["product"] == "R902745117") == 100
    assert after["seed"]["orders"] == opening["seed"]["orders"]
    for request, role in requests.values():
        assert ok(client.post("/api/production/commands", headers=auth(role), json=request))["replayed"]
    assert world(client) == after
    for request, role in [(command, "user"), (completion, "admin")]:
        stale = {**request, "requestId": "competing-" + request["requestId"]}
        assert client.post("/api/production/commands", headers=auth(role), json=stale).status_code == 409
    assert world(client) == after
    with db.connection() as conn:
        receipts = conn.execute("SELECT actor_id,request_id,result_revision FROM production_commands ORDER BY sequence").fetchall()
        assert len(receipts) == 2
        assert {row["actor_id"] for row in receipts} == {"test-admin", "test-user"}
        assert [row["result_revision"] for row in receipts] == [row["appliedRevision"] for row in acknowledgements]
