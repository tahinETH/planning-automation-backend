from copy import deepcopy
import pytest
from app.database import connection, init_database, planning_state, save_planning_state, ProtectedSettingsChange
from app.process_waits import validate_process_wait_settings


def settings():
    return {process: {"enabled": process == "turning", "workdays": 2 if process == "turning" else 0}
            for process in ("turning", "drilling", "deburring", "gkm")}


def test_admin_wait_settings_save_reload_permissions_and_old_client_atomicity():
    init_database()
    with connection() as db:
        db.execute("DELETE FROM planning_state")
    seed = {"orders": [], "processWaitSettings": settings(), "marker": "retained"}
    saved = save_planning_state(seed, can_manage_settings=True, process_wait_settings_version=1)
    assert planning_state()["seed"] == saved["seed"]
    before = planning_state()
    for value in (-1, 1.5, 366, True, "2"):
        invalid = deepcopy(saved["seed"])
        invalid["processWaitSettings"]["turning"]["workdays"] = value
        with pytest.raises(ValueError):
            save_planning_state(invalid, saved["updatedAt"], can_manage_settings=True, process_wait_settings_version=1)
        assert planning_state() == before
    changed = deepcopy(saved["seed"])
    changed["processWaitSettings"]["turning"]["workdays"] = 3
    with pytest.raises(ProtectedSettingsChange):
        save_planning_state(changed, saved["updatedAt"], process_wait_settings_version=1)
    legacy = deepcopy(saved["seed"])
    del legacy["processWaitSettings"]
    with pytest.raises(ValueError, match="yenileyin"):
        save_planning_state(legacy, saved["updatedAt"], can_manage_settings=True)
    assert planning_state() == before
    retained = save_planning_state(legacy, saved["updatedAt"], process_wait_settings_version=1)
    assert retained["seed"]["processWaitSettings"] == settings()
    assert retained["seed"]["marker"] == "retained"


def test_wait_settings_validate_all_rows_and_backup():
    from app.data_package import build_data_package, parse_data_package
    for value in (None, [], {}, {**settings(), "turning": {"enabled": "true", "workdays": 1}}):
        with pytest.raises(ValueError):
            validate_process_wait_settings(value)
    data = {"processWaitSettings": settings(), "holidays": [], "calendarEvents": [], "machines": [], "setupSettings": {}}
    encoded = build_data_package("settings", data)
    assert parse_data_package(encoded, "settings")["processWaitSettings"] == settings()
