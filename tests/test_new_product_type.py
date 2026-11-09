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


@pytest.mark.parametrize("field,label", [
    ("orders", "Siparişler"), ("orderImportGrossOrders", "Siparişler"),
    ("demandTargets", "Siparişler"), ("customerOrderOverrides", "Siparişler"),
    ("manualBatches", "Planlama"), ("savedBatches", "Planlama"),
    ("processCurrentJobs", "Tezgahlar"), ("productionHistory", "Üretim arşivi"),
    ("wipLots", "Yarı mamul"), ("productionInterruptions", "Üretim"),
    ("productionCancellations", "Üretim"),
])
def test_type_j02_used_type_cannot_be_removed_even_with_its_usage(field, label):
    from app.product_type_deletion import assert_product_type_deletion_safe
    before = {"products": [{"product": "TEST-UNUSED"}], field: [{"product": "TEST-UNUSED"}]}
    with pytest.raises(ValueError, match=label):
        assert_product_type_deletion_safe(before, {"products": [], field: []})
    with pytest.raises(ValueError, match=label):
        assert_product_type_deletion_safe({"products": before["products"]}, {"products": [], field: before[field]})


def test_type_j02_other_usage_blocks_process_only_removal():
    from app.product_type_deletion import assert_product_type_deletion_safe
    for usage in [
        {"openingStock": {"TEST-UNUSED": 100}},
        {"processStockSettings": {"opening": [{"product": "TEST-UNUSED", "quantity": 0}]}},
        {"customerDemand": {"products": [{"product": "TEST-UNUSED"}]}},
        {"processOperationOverrides": [{"sourceProduct": "TEST-UNUSED"}]},
        {"machines": [{"currentJob": {"product": "TEST-UNUSED", "quantity": 100}}]},
    ]:
        before = {"processMasterData": {"products": [{"product": "TEST-UNUSED"}]}, **usage}
        with pytest.raises(ValueError, match="silinemez"):
            assert_product_type_deletion_safe(before, {"processMasterData": {"products": []}})


def test_type_j01_unused_type_deletion_persists_with_material_permission_and_keeps_other_records(tmp_path, monkeypatch):
    from app import database
    from types import SimpleNamespace
    monkeypatch.setattr(database, "settings", SimpleNamespace(database_path=tmp_path / "delete-type.sqlite", upload_dir=tmp_path / "uploads"))
    init_database()
    original = {
        "orders": [], "products": [{"product": "TEST-UNUSED"}, {"product": "OTHER"}],
        "processMasterData": {"products": [{"product": "TEST-UNUSED"}, {"product": "OTHER"}]},
        "productWeights": [{"product": "TEST-UNUSED", "productName": "Test", "materialCode": "TEST-STEEL", "materialName": "Test", "grams": 50}],
        "manualBatches": [], "productionHistory": [], "wipLots": [],
    }
    current = save_planning_state(original, can_manage_settings=True)
    removed = deepcopy(current["seed"])
    removed["products"] = [{"product": "OTHER"}]
    removed["processMasterData"]["products"] = [{"product": "OTHER"}]
    removed["productWeights"] = []
    removed["planNeedsRecalculation"] = True
    with pytest.raises(ProtectedSettingsChange):
        save_planning_state(removed, current["updatedAt"], mode="operational")
    assert planning_state()["seed"] == current["seed"]
    saved = save_planning_state(removed, current["updatedAt"], mode="operational", can_manage_settings=True)
    assert planning_state()["seed"] == saved["seed"]
    assert saved["seed"]["products"] == [{"product": "OTHER"}]
    for field in ("orders", "manualBatches", "productionHistory", "wipLots"):
        assert saved["seed"][field] == original[field]
    assert saved["seed"]["planNeedsRecalculation"] is True


@pytest.mark.parametrize("mode", ["operational", "planning"])
def test_type_j05_server_rejects_used_type_deletion_atomically(tmp_path, monkeypatch, mode):
    from app import database
    from types import SimpleNamespace
    monkeypatch.setattr(database, "settings", SimpleNamespace(database_path=tmp_path / "used-type.sqlite", upload_dir=tmp_path / "uploads"))
    init_database()
    current = save_planning_state({"products": [{"product": "TEST-USED"}], "orders": [{"id": "order", "product": "TEST-USED", "quantity": 100}]})
    removed = deepcopy(current["seed"])
    removed["products"] = []
    with pytest.raises(ValueError, match="Siparişler"):
        save_planning_state(removed, current["updatedAt"], mode=mode, can_manage_settings=True)
    assert planning_state()["seed"] == current["seed"]
    assert planning_state()["updatedAt"] == current["updatedAt"]
