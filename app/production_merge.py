"""Three-way source refresh. Local edits win; related operational state moves together."""
from .turning_queue_identity import reconcile_turning_seed
from copy import deepcopy
from typing import Any


OPERATIONS = {
    "productionInterruptions", "productionCancellations", "scenarioProvenance",
    "machines", "productionHistory", "wipLots", "wipMovements", "planningEvents",
    "processCurrentJobs", "chargeJourneyNotes", "manualBatches", "savedBatches",
    "processOperationOverrides", "activePlanRun", "lastAutomaticPlan", "planRunSequence", "planNeedsRecalculation",
    "orders", "customerDemand", "customerOrderOverrides", "orderImport", "orderImportGrossOrders",
}


def merge_production_refresh(source: dict[str, Any], local: dict[str, Any] | None,
                             baseline: dict[str, Any] | None) -> dict[str, Any]:
    if local is None:
        return reconcile_turning_seed(deepcopy(source))
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
    return reconcile_turning_seed(merged)


# --- Reviewed refresh (T16) -------------------------------------------------
# Related facts move together in groups. The planner sees a comparison and
# chooses per group; nothing inside a group is merged field by field.

import hashlib
import json

REFRESH_GROUPS: dict[str, dict[str, Any]] = {
    "physical": {
        "label": "Üretim kayıtları ve plan",
        "fields": ("machines", "productionHistory", "wipLots", "wipMovements", "productionInterruptions",
                   "productionCancellations", "processCurrentJobs", "manualBatches", "savedBatches",
                   "processOperationOverrides", "activePlanRun", "lastAutomaticPlan", "planRunSequence",
                   "planNeedsRecalculation", "scenarioProvenance"),
        "choices": ("keep-local", "use-source"),
    },
    "orders": {
        "label": "Siparişler",
        "fields": ("orders", "customerDemand", "customerOrderOverrides", "orderImport", "orderImportGrossOrders"),
        "choices": ("keep-local", "use-source"),
    },
    "annotations": {
        "label": "Plan olayları ve şarj notları",
        "fields": ("planningEvents", "chargeJourneyNotes"),
        "choices": ("keep-local", "use-source", "combine"),
    },
}
GROUPED_FIELDS = {field for group in REFRESH_GROUPS.values() for field in group["fields"]}
_MISSING = object()


def seed_digest(seed: dict[str, Any] | None) -> str | None:
    if seed is None:
        return None
    return hashlib.sha256(json.dumps(seed, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def _group_values(seed: dict[str, Any] | None, fields: tuple[str, ...]) -> dict[str, Any]:
    seed = seed or {}
    return {field: seed[field] for field in fields if field in seed}


def _collection_summary(local: Any, source: Any) -> dict[str, int]:
    def by_id(rows: Any) -> dict[str, str]:
        if not isinstance(rows, list):
            return {}
        return {str(row.get("id")): json.dumps(row, sort_keys=True, ensure_ascii=False) for row in rows if isinstance(row, dict) and row.get("id") is not None}
    left, right = by_id(local), by_id(source)
    return {
        "onlyLocal": len(left.keys() - right.keys()),
        "onlySource": len(right.keys() - left.keys()),
        "different": sum(1 for key in left.keys() & right.keys() if left[key] != right[key]),
    }


def _group_summary(group_id: str, local: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    fields = REFRESH_GROUPS[group_id]["fields"]
    collections = {}
    for field in fields:
        left, right = local.get(field), source.get(field)
        if isinstance(left, list) or isinstance(right, list):
            if left != right:
                collections[field] = _collection_summary(left, right)
        elif left != right:
            collections[field] = {"changed": True}
    summary: dict[str, Any] = {"collections": collections}
    if group_id == "physical":
        local_jobs = {m.get("id"): m.get("currentJob") for m in local.get("machines") or [] if isinstance(m, dict)}
        source_jobs = {m.get("id"): m.get("currentJob") for m in source.get("machines") or [] if isinstance(m, dict)}
        summary["currentJobMachines"] = sorted(str(key) for key in local_jobs.keys() | source_jobs.keys() if local_jobs.get(key) != source_jobs.get(key))
    return summary


def refresh_groups(source: dict[str, Any], local: dict[str, Any] | None, baseline: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Per-group comparison of the local staging state with the production source."""
    rows = []
    for group_id, group in REFRESH_GROUPS.items():
        fields = group["fields"]
        source_values = _group_values(source, fields)
        local_values = _group_values(local, fields) if local is not None else source_values
        base_values = _group_values(baseline, fields) if baseline is not None else None
        if local_values == source_values:
            status, default = "same", "use-source"
        elif base_values is None:
            status, default = "no-baseline", None
        elif local_values == base_values:
            status, default = "source-changed", "use-source"
        elif source_values == base_values:
            status, default = "local-changed", "keep-local"
        else:
            status, default = "both-changed", None
        rows.append({"id": group_id, "label": group["label"], "status": status, "defaultChoice": default,
                     "allowedChoices": list(group["choices"]), "requiresChoice": default is None,
                     "summary": _group_summary(group_id, local_values, source_values)})
    return rows


def settings_key_differences(source: dict[str, Any], local: dict[str, Any] | None, baseline: dict[str, Any] | None) -> dict[str, list[str]]:
    """Ungrouped (parameter/setting) keys: a locally changed key stays local, as before."""
    local = local or {}
    base = baseline or {}
    keys = sorted((source.keys() | local.keys()) - GROUPED_FIELDS)
    local_changed = [key for key in keys if local.get(key, _MISSING) != base.get(key, _MISSING)]
    source_changed = [key for key in keys if source.get(key, _MISSING) != base.get(key, _MISSING)]
    return {
        "keptLocal": [key for key in local_changed if local.get(key, _MISSING) != source.get(key, _MISSING)],
        "fromSource": [key for key in source_changed if key not in local_changed],
        "bothChanged": [key for key in local_changed if key in source_changed and local.get(key, _MISSING) != source.get(key, _MISSING)],
    }


def _combine_by_id(local_rows: Any, source_rows: Any) -> list[Any]:
    """Union of append-only logs by id; the local version wins for the same id."""
    result: list[Any] = []
    seen: set[str] = set()
    for rows in (local_rows if isinstance(local_rows, list) else [], source_rows if isinstance(source_rows, list) else []):
        for row in rows:
            key = str(row.get("id")) if isinstance(row, dict) and row.get("id") is not None else json.dumps(row, sort_keys=True, ensure_ascii=False)
            if key not in seen:
                seen.add(key)
                result.append(deepcopy(row))
    return result


def resolve_refresh_choices(groups: list[dict[str, Any]], choices: dict[str, str] | None) -> dict[str, str]:
    """Explicit choices for required groups; defaults elsewhere. Raises ValueError on a missing or invalid choice."""
    choices = choices or {}
    unknown = set(choices) - set(REFRESH_GROUPS)
    if unknown:
        raise ValueError(f"Bilinmeyen yenileme grubu: {', '.join(sorted(unknown))}.")
    resolved: dict[str, str] = {}
    for group in groups:
        choice = choices.get(group["id"], group["defaultChoice"])
        if choice is None:
            raise ValueError(f"{group['label']} için yerel çalışmayı koru veya üretim verisini kullan seçimi gerekli.")
        if choice not in group["allowedChoices"]:
            raise ValueError(f"{group['label']} için geçersiz seçim: {choice}.")
        resolved[group["id"]] = choice
    return resolved


def merge_production_refresh_reviewed(source: dict[str, Any], local: dict[str, Any] | None,
                                      baseline: dict[str, Any] | None, choices: dict[str, str]) -> dict[str, Any]:
    """Apply resolved group choices. Ungrouped keys keep the existing per-key rule."""
    if local is None:
        return reconcile_turning_seed(deepcopy(source))
    base = baseline or {}
    merged: dict[str, Any] = {}
    for key in (source.keys() | local.keys() | base.keys()) - GROUPED_FIELDS:
        changed = local.get(key, _MISSING) != base.get(key, _MISSING) if baseline is not None else local.get(key, _MISSING) != source.get(key, _MISSING)
        value = local.get(key, _MISSING) if changed else source.get(key, _MISSING)
        if value is not _MISSING:
            merged[key] = deepcopy(value)
    sides = set()
    for group_id, group in REFRESH_GROUPS.items():
        choice = choices[group_id]
        for field in group["fields"]:
            if choice == "combine":
                value: Any = _combine_by_id(local.get(field), source.get(field)) if field in local or field in source else _MISSING
            else:
                value = (local if choice == "keep-local" else source).get(field, _MISSING)
            if value is not _MISSING:
                merged[field] = deepcopy(value)
        if _group_values(local, group["fields"]) != _group_values(source, group["fields"]):
            sides.add(choice)
    # Groups taken from different sides were not calculated together.
    if len(sides) > 1 or ("use-source" in sides and choices.get("physical") == "keep-local"):
        merged["planNeedsRecalculation"] = True
    return reconcile_turning_seed(merged)
