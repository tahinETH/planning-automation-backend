"""PST-T03: cancellation review belongs to the same saved production state."""

from copy import deepcopy

import pytest

from app.production_merge import merge_production_refresh
from app.piston_controls import validate_production_cancellations


def cancellation(status="pending"):
    return {
        "id": "cancel-t03", "version": 1, "product": "PISTON-T03", "process": "turning",
        "chargeId": "current:C-04", "workOrder": "WO-T03", "machineId": "C-04",
        "assignedQuantity": 1500, "completedQuantity": 500, "cancelledQuantity": 1000,
        "reason": "Reviewed unmade remainder", "cancelledAt": "2026-09-21T05:00:00Z",
        "orderIds": ["original-order"], "review": {"status": status},
        "orderQuantities": {"original-order": 1500},
    }


def test_t03_local_review_keeps_its_physical_state_during_source_refresh():
    baseline = {"productionCancellations": [cancellation()], "wipLots": [{"id": "physical-500", "availableQuantity": 500}]}
    local = deepcopy(baseline)
    local["productionCancellations"][0]["review"] = {"status": "replacement-declined"}
    source = deepcopy(baseline)
    source["wipLots"] = [{"id": "different-source-lot", "availableQuantity": 700}]
    before = deepcopy((source, local, baseline))

    merged = merge_production_refresh(source, local, baseline)

    assert merged["productionCancellations"] == local["productionCancellations"]
    assert merged["wipLots"] == local["wipLots"]
    assert (source, local, baseline) == before


def test_t03_server_sets_actor_for_record_and_review():
    raw = cancellation()
    raw.update(recordedBy="client-name", recordedById="client-id")
    raw["review"].update(reviewedBy="fake-reviewer", reviewedAt="2099-01-01T00:00:00Z")
    seed = {"productionCancellations": [raw]}
    saved = validate_production_cancellations(None, seed, "actor-id", "Actor", "2026-09-21T06:00:00Z")
    record = saved["productionCancellations"][0]
    assert record["recordedById"] == "actor-id"
    assert record["recordedBy"] == "Actor"
    assert record["review"] == {"status": "pending"}
    reviewed = deepcopy(saved)
    reviewed["productionCancellations"][0]["review"] = {"status": "replacement-approved", "reviewedBy": "client"}
    final = validate_production_cancellations(saved, reviewed, "reviewer-id", "Reviewer", "2026-09-21T07:00:00Z")
    assert final["productionCancellations"][0]["review"] == {"status": "replacement-approved", "reviewedById": "reviewer-id", "reviewedBy": "Reviewer", "reviewedAt": "2026-09-21T07:00:00Z"}


@pytest.mark.parametrize("change", [
    {"completedQuantity": 499},
    {"cancelledAt": "2099-01-01T00:00:00Z"},
    {"cancelledAt": "invalid-time"},
    {"reason": " "},
    {"process": "drilling"},
])
def test_t03_server_rejects_invalid_new_facts_without_mutation(change):
    record = {**cancellation(), **change}
    seed = {"productionCancellations": [record]}
    before = deepcopy(seed)
    with pytest.raises(ValueError):
        validate_production_cancellations(None, seed, "actor", "Actor", "2026-09-21T06:00:00Z")
    assert seed == before


def test_t03_server_cannot_drop_a_declined_review_that_still_holds_demand():
    current = {"productionCancellations": [cancellation("replacement-declined")]}
    with pytest.raises(ValueError):
        validate_production_cancellations(current, {"productionCancellations": []}, "actor", "Actor", "2026-09-21T06:00:00Z")


def test_t03_local_physical_change_keeps_the_associated_pending_review():
    baseline = {"productionCancellations": [cancellation()], "wipLots": [{"id": "physical-500", "availableQuantity": 500}]}
    local = deepcopy(baseline)
    local["wipLots"][0]["availableQuantity"] = 400
    source = deepcopy(baseline)
    source["productionCancellations"][0]["review"] = {"status": "replacement-approved"}

    merged = merge_production_refresh(source, local, baseline)

    assert merged["productionCancellations"] == local["productionCancellations"]
    assert merged["wipLots"] == local["wipLots"]


@pytest.mark.parametrize("quantities", [None, [], {"original-order": "invalid"}, {"original-order": -1}, {"original-order": 1.5}, {"original-order": True}])
def test_t03_server_rejects_invalid_order_snapshot_quantities(quantities):
    record = cancellation()
    record["orderQuantities"] = quantities
    incoming = {"productionCancellations": [record]}
    before = deepcopy(incoming)
    with pytest.raises(ValueError):
        validate_production_cancellations(None, incoming, "actor", "Actor", "2026-09-21T06:00:00Z")
    assert incoming == before


def test_t03_server_preserves_the_saved_history_link():
    record = cancellation()
    record["historyEntryId"] = "physical-history-500"
    current = {"productionCancellations": [record]}
    incoming = deepcopy(current)
    incoming["productionCancellations"][0]["historyEntryId"] = "unrelated-history"
    before = deepcopy(incoming)
    with pytest.raises(ValueError):
        validate_production_cancellations(current, incoming, "actor", "Actor", "2026-09-21T06:00:00Z")
    assert incoming == before


def test_t03_server_rejects_omission_of_a_declined_hold():
    current = {"productionCancellations": [cancellation("replacement-declined")]}
    incoming = {"orders": []}
    before = deepcopy(incoming)
    with pytest.raises(ValueError):
        validate_production_cancellations(current, incoming, "actor", "Actor", "2026-09-21T06:00:00Z")
    assert incoming == before
