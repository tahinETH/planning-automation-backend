import json
from copy import deepcopy
import pytest
from app.database import connection, init_database, planning_state, save_planning_state, ProtectedSettingsChange
from app.product_weights import initial_product_weights, validate_product_weights


def test_one_time_weights_migration_preserves_edits_and_older_client_saves():
    init_database()
    with connection() as db:
        db.execute("DELETE FROM planning_state")
    saved = save_planning_state({"orders": [], "marker": "preserve"}, can_manage_settings=True)
    init_database()
    state = planning_state()
    assert len(state["seed"]["productWeights"]) == 65
    assert state["seed"]["marker"] == "preserve"
    state["seed"]["productWeights"][0]["grams"] = 123.456
    saved = save_planning_state(state["seed"], state["updatedAt"], can_manage_settings=True)
    init_database()
    assert planning_state()["seed"]["productWeights"][0]["grams"] == 123.456
    legacy = deepcopy(saved["seed"])
    del legacy["productWeights"]
    result = save_planning_state(legacy, saved["updatedAt"], can_manage_settings=False)
    assert result["seed"]["productWeights"][0]["grams"] == 123.456
    unauthorized = deepcopy(result["seed"])
    unauthorized["productWeights"][0]["grams"] = 999
    with pytest.raises(ProtectedSettingsChange):
        save_planning_state(unauthorized, result["updatedAt"], can_manage_settings=False)
    assert planning_state()["seed"] == result["seed"]


def test_weights_validate_units_values_and_duplicates():
    rows = initial_product_weights()
    assert len(rows) == 65
    assert next(row for row in rows if row["product"] == "R902745116")["grams"] == 181
    validate_product_weights(rows)
    for value in [0, -1, float('nan'), float('inf'), True, "181"]:
        with pytest.raises(ValueError):
            validate_product_weights([{**rows[0], "grams": value}])
    with pytest.raises(ValueError):
        validate_product_weights([rows[0], rows[0]])
    validate_product_weights([{**rows[0], "grams": None}])


def test_weight_backup_and_ravi_use_current_values():
    from io import BytesIO
    from openpyxl import load_workbook
    from app.data_package import build_data_package, parse_data_package
    from app.ravi.tools import Inspect, inspect_state
    rows = initial_product_weights()
    rows[0]["grams"] = 321.123
    data = {"productWeights": rows, "setupSettings": {}}
    content = build_data_package("settings", data)
    assert parse_data_package(content, "settings")["productWeights"] == rows
    sheet = load_workbook(BytesIO(content))["Ürün Ağırlıkları"]
    assert sheet["E2"].value == 321.123
    snapshot = {"seed": data, "updatedAt": "2026-09-07"}
    before = deepcopy(snapshot)
    result = inspect_state(snapshot, Inspect(collection="product_weights", query=rows[0]["product"]))
    assert result["rows"][0]["Hammadde ağırlığı (g)"] == 321.123
    assert result["rows"][0]["Birim"] == "Gram"
    assert snapshot == before
