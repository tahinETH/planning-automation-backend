import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app import collaboration as collab
from app import database as db
from app.auth import CurrentUser


OWNER = CurrentUser("list-owner", "Owner", "owner@example.test", "user")


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "settings", SimpleNamespace(database_path=tmp_path / "scenario-list.sqlite", upload_dir=tmp_path / "uploads"))
    db.init_database()


def insert_scenario(index, owner="other-owner", shared=True):
    scenario_id = f"list-{index:03}"
    created = f"2026-11-09T{index // 60:02}:{index % 60:02}:00Z"
    with db.connection() as connection:
        connection.execute("INSERT INTO scenarios VALUES(?,?,?,?,?,?)", (scenario_id, scenario_id, created, "", "{}", json.dumps({"summary": {"plannedBatchCount": 1}})))
        if owner is not None:
            connection.execute("INSERT INTO scenario_owners(scenario_id,owner_id,owner_name,revision,updated_at,shared,world_revision) VALUES(?,?,?,?,?,?,?)", (scenario_id, owner, "Synthetic owner", 1, created, int(shared), "world-1"))
    return scenario_id


def test_scn_list01_filter_precedes_page_and_total_for_the_119_record_case():
    for index in range(119):
        insert_scenario(index, OWNER.id if index in (117, 118) else "other-owner", shared=index < 117)
    page = collab.list_scenarios(OWNER, 20, 0, ownership="mine")
    assert page["total"] == 2
    assert [item["id"] for item in page["items"]] == ["list-118", "list-117"]
    assert page["hasMore"] is False
    assert all(item["canEdit"] for item in page["items"])
    shared = collab.list_scenarios(OWNER, 20, 0, ownership="shared")
    assert shared["total"] == 117
    assert len(shared["items"]) == 20
    assert shared["hasMore"] is True
    assert all(not item["canEdit"] for item in shared["items"])


def test_scn_list02_each_filtered_page_advances_and_private_records_stay_hidden():
    mine = [insert_scenario(index, OWNER.id, shared=index == 0) for index in range(25)]
    private = insert_scenario(25, "private-owner", shared=False)
    legacy = insert_scenario(26, None)
    first = collab.list_scenarios(OWNER, 20, 0, ownership="mine")
    second = collab.list_scenarios(OWNER, 20, 20, ownership="mine")
    assert first["total"] == second["total"] == 25
    assert len(first["items"]) == 20 and len(second["items"]) == 5
    assert first["hasMore"] and not second["hasMore"]
    assert {item["id"] for item in first["items"] + second["items"]} == set(mine)
    shared = collab.list_scenarios(OWNER, 20, 0, ownership="shared")
    assert {item["id"] for item in shared["items"]} == {mine[0], legacy}
    assert private not in {item["id"] for item in collab.list_scenarios(OWNER, 100, 0)["items"]}
    with pytest.raises(HTTPException) as error:
        collab.list_scenarios(OWNER, 20, 0, ownership="invalid")
    assert error.value.status_code == 422


def test_scn_list_endpoint_uses_authenticated_owner_and_validates_the_filter(monkeypatch):
    from fastapi.testclient import TestClient
    from app.auth import current_user
    from app.main import app

    mine = insert_scenario(1, OWNER.id, shared=False)
    shared = insert_scenario(2, "other-owner", shared=True)
    insert_scenario(3, "private-owner", shared=False)
    monkeypatch.setitem(app.dependency_overrides, current_user, lambda: OWNER)
    with TestClient(app) as client:
        own_page = client.get("/api/scenarios/list?ownership=mine").json()
        assert own_page["total"] == 1
        assert [item["id"] for item in own_page["items"]] == [mine]
        shared_page = client.get("/api/scenarios/list?ownership=shared").json()
        assert [item["id"] for item in shared_page["items"]] == [shared]
        assert client.get("/api/scenarios/list").json()["total"] == 2
        assert client.get("/api/scenarios/list?ownership=another-user").status_code == 422
