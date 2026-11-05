from copy import deepcopy
import pytest
from app.flow_settings import validate_flow_settings
from app.database import connection, init_database, planning_state, save_planning_state, ProtectedSettingsChange
from app.data_package import build_data_package, parse_data_package


def settings():
    return {"version": 1, "enabled": True, "department": "piston", "defaultShifts": 2, "shiftOverrides": [],
            "rules": [{"id": "wash", "family": "piston", "from": "deburring", "to": "gkm", "mode": "static", "minutes": 720, "description": "Yıkama", "active": True}],
            "setupMinutes": {process: {key: 0 for key in ["first", "sameProduct", "sameKey", "differentKey", "differentFamily"]} for process in ["drilling", "deburring", "gkm"]}}


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True, "120", 10081])
def test_flow_rejects_invalid_minutes(value):
    data = settings()
    data["rules"][0]["minutes"] = value
    with pytest.raises(ValueError):
        validate_flow_settings(data)


def test_flow_duplicate_and_backward_rules_are_rejected():
    data = settings()
    data["rules"].append({**data["rules"][0], "id": "other"})
    with pytest.raises(ValueError):
        validate_flow_settings(data)
    data = settings()
    data["rules"][0]["from"] = "gkm"
    with pytest.raises(ValueError):
        validate_flow_settings(data)


def test_flow_roundtrip_admin_protection_legacy_client_and_atomic_failure():
    init_database()
    with connection() as db:
        db.execute("DELETE FROM planning_state")
    data = settings()
    saved = save_planning_state({"orders": [], "flowSettings": data}, can_manage_settings=True, flow_settings_version=1)
    assert planning_state()["seed"]["flowSettings"] == data
    assert parse_data_package(build_data_package("settings", {"flowSettings": data}), "settings")["flowSettings"] == data
    legacy = deepcopy(saved["seed"])
    legacy.pop("flowSettings")
    with pytest.raises(ValueError, match="Saat bazlı"):
        save_planning_state(legacy, saved["updatedAt"], can_manage_settings=True)
    assert planning_state()["seed"] == saved["seed"]
    unauthorized = deepcopy(saved["seed"])
    unauthorized["flowSettings"]["defaultShifts"] = 3
    with pytest.raises(ProtectedSettingsChange):
        save_planning_state(unauthorized, saved["updatedAt"], flow_settings_version=1)
    assert planning_state()["seed"] == saved["seed"]
    invalid = deepcopy(saved["seed"])
    invalid["flowSettings"]["rules"][0]["minutes"] = -1
    with pytest.raises(ValueError):
        save_planning_state(invalid, saved["updatedAt"], can_manage_settings=True, flow_settings_version=1)
    assert planning_state()["seed"] == saved["seed"]
    preserved = save_planning_state(legacy, saved["updatedAt"], can_manage_settings=True, flow_settings_version=1)
    assert preserved["seed"]["flowSettings"] == data
    # Leave the shared test database in legacy mode for unrelated API fixtures.
    with connection() as db:
        db.execute("DELETE FROM planning_state")


def test_piston_flow_cannot_be_enabled_in_cubuk_filtre():
    from app.production_area import production_area
    token = production_area.set("cubuk-filtre")
    try:
        init_database()
        with pytest.raises(ValueError, match="yalnız Piston"):
            save_planning_state({"productionArea": "cubuk-filtre", "flowSettings": settings()}, can_manage_settings=True, flow_settings_version=1)
    finally:
        production_area.reset(token)
