"""Three-way source refresh. Local edits win; related operational state moves together."""
from copy import deepcopy
from typing import Any


OPERATIONS = {
    "machines", "productionHistory", "wipLots", "wipMovements", "planningEvents",
    "processCurrentJobs", "chargeJourneyNotes", "manualBatches", "savedBatches",
    "processOperationOverrides", "activePlanRun", "lastAutomaticPlan", "planRunSequence",
    "orders", "customerDemand", "customerOrderOverrides", "orderImport", "orderImportGrossOrders",
}


def merge_production_refresh(source: dict[str, Any], local: dict[str, Any] | None,
                             baseline: dict[str, Any] | None) -> dict[str, Any]:
    if local is None:
        return deepcopy(source)
    # On the first pull there is no evidence that local work is disposable.
    base = baseline or {}
    missing = object()
    operational_changed = any(local.get(k, missing) != base.get(k, missing) for k in OPERATIONS)
    merged = {}
    for key in source.keys() | local.keys() | base.keys():
        changed = local.get(key, missing) != base.get(key, missing)
        keep_local = operational_changed if key in OPERATIONS else changed
        value = local.get(key, missing) if keep_local else source.get(key, missing)
        if value is not missing:
            merged[key] = deepcopy(value)
    return merged
