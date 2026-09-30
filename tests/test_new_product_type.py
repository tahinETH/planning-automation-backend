from copy import deepcopy

import pytest

from app.database import ProtectedSettingsChange, init_database, planning_state, save_planning_state


def test_new_type_route_and_material_mapping_persist_atomically_with_existing_settings_permission(tmp_path, monkeypatch):
    from app import database
    from types import SimpleNamespace
    monkeypatch.setattr(database, "settings", SimpleNamespace(database_path=tmp_path / "new-type.sqlite", upload_dir=tmp_path / "uploads"))
    init_database()
    current = save_planning_state({"orders": [], "products": [], "processMasterData": {"products": []}}, can_manage_settings=True)
    before = deepcopy(current["seed"])
    incoming = deepcopy(before)
    code = "TEST-NEW-TYPE"
    incoming.setdefault("products", []).append({"product": code, "batchSize": 100, "diameter": "Ø 23", "shiftRate": 200})
    incoming.setdefault("processMasterData", {"products": []})["products"].append({
        "product": code, "family": "piston", "route": ["turning", "drilling"],
        "processes": [{"process": "drilling", "sequence": 1, "setupKey": "Ø6", "waitWorkdaysBefore": 0,
                       "resourcePriority": ["D-01"], "unitsPerShift": {"D-01": 100}}],
    })
    incoming.setdefault("productWeights", []).append({"product": code, "productName": "Test", "materialCode": "TEST-STEEL", "materialName": "Çelik Ø 23", "grams": 50.5})
    incoming["planNeedsRecalculation"] = True
    with pytest.raises(ProtectedSettingsChange):
        save_planning_state(incoming, current["updatedAt"], mode="operational", can_manage_settings=False)
    assert planning_state()["seed"] == before

    saved = save_planning_state(incoming, current["updatedAt"], mode="operational", can_manage_settings=True)
    restored = planning_state()["seed"]
    assert restored["processMasterData"]["products"][-1]["route"] == ["turning", "drilling"]
    assert restored["productWeights"][-1]["grams"] == 50.5
    assert restored["planNeedsRecalculation"] is True
    for field in ("orders", "manualBatches", "wipLots", "productionHistory", "rawMaterialSettings"):
        assert restored.get(field) == before.get(field)

    invalid = deepcopy(restored)
    invalid["productWeights"][-1]["grams"] = -1
    with pytest.raises(ValueError):
        save_planning_state(invalid, saved["updatedAt"], mode="operational", can_manage_settings=True)
    assert planning_state()["seed"] == restored


def test_unused_type_deletion_persists_all_process_parameters_and_materials_together(tmp_path, monkeypatch):
    from app import database
    from types import SimpleNamespace
    monkeypatch.setattr(database, "settings", SimpleNamespace(database_path=tmp_path / "delete-type.sqlite", upload_dir=tmp_path / "uploads"))
    init_database()
    code = "R0027199"
    seed = {"orders": [], "products": [{"product": code}], "orderCatalog": [code],
            "preferences": [{"key": code}], "restrictions": [{"product": code}],
            "processMasterData": {"products": [{"product": code, "route": ["turning", "drilling", "deburring", "gkm"], "processes": [{"process": p} for p in ["drilling", "deburring", "gkm"]]}]},
            "productWeights": [{"product": code, "productName": "Test", "materialCode": "TEST", "materialName": "Çelik", "grams": 50}],
            "manualBatches": [], "wipLots": [], "productionHistory": []}
    current = save_planning_state(seed, can_manage_settings=True)
    deleted = deepcopy(current["seed"])
    for field in ["products", "orderCatalog", "preferences", "restrictions", "productWeights"]:
        deleted[field] = []
    deleted["processMasterData"]["products"] = []
    deleted["planNeedsRecalculation"] = True
    with pytest.raises(ProtectedSettingsChange):
        save_planning_state(deleted, current["updatedAt"], mode="operational", can_manage_settings=False)
    assert planning_state()["seed"] == current["seed"]
    saved = save_planning_state(deleted, current["updatedAt"], mode="operational", can_manage_settings=True)
    assert planning_state()["seed"] == deleted
    assert saved["seed"]["productWeights"] == []  # Empty is explicit; no foundational re-add.
    assert saved["seed"]["processMasterData"]["products"] == []
    from app.database import PlanningStateConflict
    with pytest.raises(PlanningStateConflict):
        save_planning_state(current["seed"], current["updatedAt"], mode="operational", can_manage_settings=True)
    assert planning_state()["seed"] == deleted
    restored = save_planning_state(current["seed"], saved["updatedAt"], mode="operational", can_manage_settings=True)
    assert restored["seed"]["products"] == [{"product": code}]
    assert restored["seed"]["productWeights"][0]["grams"] == 50
