from copy import deepcopy
import pytest
from app.process_wip_group import validate_grouped_process_work
from app.database import connection, init_database, planning_state, save_planning_state, PlanningStateConflict
from app.models import PlanningStatePayload


def group_seed():
    lots = [{"id": f"lot-{i}", "sourceHistoryEntryId": f"history-{i}", "sourceBatchId": "same-charge", "product": "SYNTHETIC", "family": "piston", "workOrder": "1500",
             "availableQuantity": quantity, "originalQuantity": quantity, "deliveredQuantity": 0, "scrappedQuantity": 0, "stage": "drilling-queue", "nextProcess": "drilling", "readyAt": 46000 + i / 24, "completedSteps": []}
            for i, quantity in enumerate([500, 1000])]
    job = {"resourceId": "D-01", "process": "drilling", "batchId": "lot-0", "wipLotId": "lot-0", "product": "SYNTHETIC", "family": "piston", "workOrder": "1500",
           "originalQuantity": 1500, "remainingQuantity": 1500, "readyAt": 46000.1, "start": 46001, "end": 46002,
           "wipAllocations": [{"lotId": lot["id"], "quantity": lot["availableQuantity"]} for lot in lots]}
    return {"orders": [], "machines": [], "wipLots": lots, "processCurrentJobs": [job]}


@pytest.mark.parametrize("invalid", ["duplicate", "quantity", "charge", "work-order", "held", "assigned", "missing", "readiness"])
def test_group_rejects_invalid_physical_assignments(invalid):
    seed = group_seed()
    job = seed["processCurrentJobs"][0]
    if invalid == "duplicate":
        job["wipAllocations"][1]["lotId"] = "lot-0"
    elif invalid == "quantity":
        seed["wipLots"][1]["availableQuantity"] = 999
    elif invalid == "charge":
        seed["wipLots"][1]["sourceBatchId"] = "other"
    elif invalid == "work-order":
        seed["wipLots"][1]["workOrder"] = "other"
    elif invalid == "held":
        seed["wipLots"][1]["stage"] = "on-hold"
    elif invalid == "assigned":
        seed["processCurrentJobs"].append({"resourceId": "D-02", "wipLotId": "lot-1"})
    elif invalid == "missing":
        seed["wipLots"].pop()
    elif invalid == "readiness":
        seed["wipLots"][1]["readyAt"] = 47000
    before = deepcopy(seed)
    with pytest.raises(ValueError, match="Birleştirilmiş"):
        validate_grouped_process_work(seed)
    assert seed == before


def test_group_save_reload_old_client_revision_and_failure_atomicity():
    init_database()
    with connection() as db:
        db.execute("DELETE FROM planning_state")
    try:
        seed = group_seed()
        assert PlanningStatePayload(seed=seed, processWipGroupingVersion=1).processWipGroupingVersion == 1
        with pytest.raises(ValueError, match="uygulamayı yenileyip"):
            save_planning_state(seed, "", mode="operational")
        assert planning_state() is None
        saved = save_planning_state(seed, "", mode="operational", process_wip_grouping_version=1)
        assert saved["seed"]["processCurrentJobs"] == seed["processCurrentJobs"]
        assert saved["seed"]["wipLots"] == seed["wipLots"]
        persisted = planning_state()
        legacy = deepcopy(saved["seed"])
        legacy["processCurrentJobs"][0].pop("wipAllocations")
        with pytest.raises(ValueError, match="uygulamayı yenileyip"):
            save_planning_state(legacy, saved["updatedAt"], mode="operational", force=True)
        broken = deepcopy(saved["seed"])
        broken["wipLots"][1]["availableQuantity"] = 900
        with pytest.raises(ValueError, match="Birleştirilmiş"):
            save_planning_state(broken, saved["updatedAt"], mode="operational", process_wip_grouping_version=1)
        with pytest.raises(PlanningStateConflict):
            save_planning_state(saved["seed"], "stale-revision", mode="operational", force=True, process_wip_grouping_version=1)
        assert planning_state() == persisted
        refreshed = save_planning_state({"orders": [], "machines": []}, saved["updatedAt"], process_wip_grouping_version=1)
        assert refreshed["seed"]["processCurrentJobs"] == seed["processCurrentJobs"]
        assert refreshed["seed"]["wipLots"] == seed["wipLots"]
    finally:
        with connection() as db:
            db.execute("DELETE FROM planning_state")
