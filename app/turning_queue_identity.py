"""Physical Torna queue identity; kept in parity with the frontend restore guard."""
import copy


def reconcile_turning_queue(seed, batches):
    def key(value):
        return str(value or "").strip().upper()

    records = []
    for machine in seed.get("machines", []):
        job = machine.get("currentJob", {})
        if job.get("quantity", 0) > 0:
            records.append(dict(id=job.get("batchId"), product=job.get("product"), workOrder=job.get("workOrder"),
                                quantity=job.get("originalQuantity", job.get("quantity")), machineId=machine.get("id")))
    for row in seed.get("productionHistory", []):
        if row.get("process", "turning") == "turning" and row.get("inventoryStatus") != "voided" and not row.get("interruptionIds"):
            records.append(dict(id=None if row.get("sourceBatchId") == row.get("id") else row.get("sourceBatchId"), product=row.get("product"), workOrder=row.get("workOrder"),
                                quantity=row.get("originalQuantity"), machineId=row.get("machineId")))

    for lot in seed.get("wipLots", []):
        if lot.get("sourceBatchId") and lot.get("sourceBatchId") != lot.get("sourceHistoryEntryId") and not any(h.get("id") == lot.get("sourceHistoryEntryId") and h.get("inventoryStatus") == "voided" for h in seed.get("productionHistory", [])):
            records.append(dict(id=lot["sourceBatchId"], product=lot.get("product"), workOrder=lot.get("workOrder"),
                                quantity=lot.get("originalQuantity"), machineId=""))

    def conflict(batch):
        raise ValueError(f'{batch.get("machineId", "")} · {batch.get("workOrder") or batch.get("product", "")}: mevcut üretim/arşiv ile kuyruktaki şarj kimliği belirsiz. İş emri ve şarj kayıtlarını kontrol edin; işlem uygulanmadı.')

    seen, kept = set(), []
    for batch in batches:
        identity = batch.get("id")
        if identity in seen:
            conflict(batch)
        seen.add(identity)
        exact = [r for r in records if r["id"] and r["id"] == identity]
        if exact:
            if any(key(r["product"]) != key(batch.get("product")) for r in exact):
                conflict(batch)
            continue
        if batch.get("interruptionId"):
            kept.append(batch)
            continue
        legacy = [r for r in records if not r["id"] and key(r["workOrder"]) and key(r["workOrder"]) == key(batch.get("workOrder")) and key(r["product"]) == key(batch.get("product"))]
        if legacy:
            candidates = [b for b in batches if key(b.get("workOrder")) == key(batch.get("workOrder")) and key(b.get("product")) == key(batch.get("product"))]
            if len(legacy) != 1 or len(candidates) != 1 or legacy[0]["quantity"] != batch.get("quantity") or legacy[0]["machineId"] != batch.get("machineId"):
                conflict(batch)
            continue
        kept.append(batch)
    return kept


def reconcile_turning_seed(seed):
    original = seed.get("manualBatches", [])
    known = {item["chargeId"] for item in seed.get("productionInterruptions", []) if item.get("process") == "turning" and item.get("chargeId") and item.get("turningBatch")}
    batches = [batch for batch in original if batch.get("id") not in known]
    latest = {}
    for item in seed.get("productionInterruptions", []):
        if item.get("chargeId") in known and item.get("process") == "turning" and not item.get("completedAt"):
            latest[item["chargeId"]] = item
    for identity, item in latest.items():
        if any(m.get("currentJob", {}).get("batchId") == identity and m["currentJob"].get("quantity", 0) > 0 for m in seed.get("machines", [])):
            continue
        matching = next((b for b in original if b.get("id") == identity and b.get("interruptionId") == item["id"] and b.get("quantity") == item["remainingQuantity"]), None)
        batches.append(matching or item["turningBatch"])
    positions = {batch.get("id"): index for index, batch in enumerate(original)}
    batches.sort(key=lambda batch: positions.get(batch.get("id"), len(original)))
    batches = reconcile_turning_queue(seed, batches)
    if batches == original:
        return seed
    result = copy.deepcopy(seed)
    result["manualBatches"] = batches
    result.pop("lastAutomaticPlan", None)
    result["planNeedsRecalculation"] = True
    return result
