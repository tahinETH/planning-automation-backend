"""Validate physical allocations; timing stays in the shared frontend scheduler."""
from math import isfinite


def has_grouped_process_work(seed):
    return any("wipAllocations" in job for job in seed.get("processCurrentJobs", []))


def validate_grouped_process_work(seed):
    lots = seed.get("wipLots", [])
    jobs = seed.get("processCurrentJobs", [])
    allocated = set()
    for job in jobs:
        if "wipAllocations" not in job:
            continue
        invalid = "Birleştirilmiş işin yarı mamül kayıtları ve adetleri uyuşmuyor."
        items = job["wipAllocations"]
        if not isinstance(items, list) or len(items) < 2 or not all(isinstance(item, dict) for item in items):
            raise ValueError(invalid)
        ids = [item.get("lotId") for item in items]
        if not all(isinstance(value, str) and value for value in ids) or len(set(ids)) != len(ids) or ids[0] != job.get("wipLotId") or job.get("batchId") != ids[0]:
            raise ValueError(invalid)
        if job.get("process") not in ("drilling", "deburring", "gkm"):
            raise ValueError(invalid)
        group = []
        total = 0
        for item in items:
            matches = [lot for lot in lots if lot.get("id") == item["lotId"]]
            quantity = item.get("quantity")
            if len(matches) != 1 or type(quantity) is not int or not 0 < quantity <= 2**53 - 1 or item["lotId"] in allocated:
                raise ValueError(invalid)
            lot = matches[0]
            if lot.get("availableQuantity") != quantity or lot.get("nextProcess") != job.get("process") or lot.get("stage") in ("on-hold", "unclassified", "delivered", "scrapped"):
                raise ValueError(invalid)
            if any(lot.get(key) != job.get(key) for key in ("product", "family", "workOrder")):
                raise ValueError(invalid)
            if any(other is not job and (other.get("wipLotId") == lot["id"] or other.get("resourceId") == job.get("resourceId")) for other in jobs):
                raise ValueError(invalid)
            total += quantity
            group.append(lot)
            allocated.add(lot["id"])
        batch = group[0].get("sourceBatchId")
        if batch:
            if any(lot.get("sourceBatchId") != batch for lot in group):
                raise ValueError(invalid)
        elif not str(job.get("workOrder", "")).strip() or any(lot.get("sourceBatchId") for lot in group):
            raise ValueError(invalid)
        remaining = job.get("remainingQuantity")
        if total > 2**53 - 1 or job.get("originalQuantity") != total or type(remaining) is not int or not 0 < remaining <= total:
            raise ValueError(invalid)
        for key in ("start", "end", "readyAt"):
            value = job.get(key)
            if type(value) not in (int, float) or not isfinite(value) or value <= 0:
                raise ValueError(invalid)
        if any(type(lot.get("rolledForwardFrom", lot.get("readyAt"))) not in (int, float) or not isfinite(lot.get("rolledForwardFrom", lot.get("readyAt"))) or job["start"] < lot.get("rolledForwardFrom", lot.get("readyAt")) for lot in group):
            raise ValueError(invalid)
        if job["end"] < job["start"] or job["start"] < job["readyAt"]:
            raise ValueError(invalid)
