"""Physical Torna queue identity; kept in parity with the frontend restore guard."""
import copy


def reconcile_turning_queue(seed, batches):
    inspected = inspect_turning_queue(seed, batches)
    if inspected["conflicts"]:
        raise ValueError(inspected["conflicts"][0]["message"])
    return inspected["reconciledBatches"]


def _recovered_turning_batches(seed):
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
    return batches


def reconcile_turning_seed(seed):
    original = seed.get("manualBatches", [])
    batches = reconcile_turning_queue(seed, _recovered_turning_batches(seed))
    if batches == original:
        return seed
    result = copy.deepcopy(seed)
    result["manualBatches"] = batches
    result.pop("lastAutomaticPlan", None)
    result["planNeedsRecalculation"] = True
    return result


def _key(value):
    return str(value or "").strip().upper()


def inspect_turning_queue(seed, batches=None):
    """Expose all conflicting records without assigning unproven physical identity."""
    batches = seed.get("manualBatches", []) if batches is None else batches
    records = []
    for machine in seed.get("machines", []):
        job = machine.get("currentJob", {})
        if job.get("quantity", 0) > 0:
            records.append(dict(kind="current", id=machine["id"], chargeId=job.get("batchId"), machineId=machine["id"], product=job.get("product", ""), workOrder=job.get("workOrder", ""), quantity=job.get("originalQuantity", job.get("quantity"))))
    for row in seed.get("productionHistory", []):
        if (not row.get("process") or row.get("process") == "turning") and row.get("inventoryStatus") != "voided" and not row.get("interruptionIds"):
            records.append(dict(kind="history", id=row["id"], chargeId=None if row.get("sourceBatchId") == row.get("id") else row.get("sourceBatchId"), machineId=row.get("machineId", ""), product=row.get("product", ""), workOrder=row.get("workOrder", ""), quantity=row.get("originalQuantity"), status=row.get("inventoryStatus")))
    for lot in seed.get("wipLots", []):
        if lot.get("sourceBatchId") and lot.get("sourceBatchId") != lot.get("sourceHistoryEntryId") and not any(h.get("id") == lot.get("sourceHistoryEntryId") and h.get("inventoryStatus") == "voided" for h in seed.get("productionHistory", [])):
            records.append(dict(kind="wip", id=lot["id"], chargeId=lot["sourceBatchId"], machineId="", product=lot.get("product", ""), workOrder=lot.get("workOrder", ""), quantity=lot.get("originalQuantity"), status=lot.get("stage")))
    conflicts, kept = [], []
    for batch in batches:
        duplicates = [b for b in batches if b.get("id") == batch.get("id")]
        exact = [r for r in records if r.get("chargeId") and r["chargeId"] == batch.get("id")]
        legacy = [r for r in records if not r.get("chargeId") and _key(r.get("workOrder")) and _key(r.get("workOrder")) == _key(batch.get("workOrder")) and _key(r.get("product")) == _key(batch.get("product"))]
        reason, evidence = None, []
        if len(duplicates) > 1:
            reason = "duplicate-queue-id"
            evidence = [dict(kind="queue", id=b.get("id", ""), machineId=b.get("machineId", ""), product=b.get("product", ""), workOrder=b.get("workOrder", ""), quantity=b.get("quantity")) for b in duplicates]
        elif exact:
            if any(_key(r.get("product")) != _key(batch.get("product")) for r in exact):
                reason, evidence = "product-mismatch", exact
            else:
                continue
        elif not batch.get("interruptionId") and legacy:
            candidates = [b for b in batches if _key(b.get("workOrder")) == _key(batch.get("workOrder")) and _key(b.get("product")) == _key(batch.get("product"))]
            if len(legacy) != 1 or len(candidates) != 1 or legacy[0].get("quantity") != batch.get("quantity") or legacy[0].get("machineId") != batch.get("machineId"):
                reason, evidence = "legacy-ambiguous", legacy
            else:
                continue
        if reason and reason != "duplicate-queue-id":
            evidence = [*evidence, dict(kind="queue", id=batch.get("id", ""), machineId=batch.get("machineId", ""), product=batch.get("product", ""), workOrder=batch.get("workOrder", ""), quantity=batch.get("quantity"), status="locked" if batch.get("locked") else batch.get("status"))]
        if reason:
            public_records = [{k: v for k, v in r.items() if k != "chargeId" and (k != "status" or v)} for r in evidence]
            message = f'{batch.get("machineId", "")} · {batch.get("workOrder") or batch.get("product", "")}: mevcut üretim/arşiv ile kuyruktaki şarj kimliği belirsiz. İş emri ve şarj kayıtlarını kontrol edin; işlem uygulanmadı.'
            conflicts.append(dict(batchId=batch.get("id", ""), machineId=batch.get("machineId", ""), product=batch.get("product", ""), workOrder=batch.get("workOrder", ""), message=message, reason=reason, records=public_records))
        kept.append(batch)
    return dict(conflicts=conflicts, reconciledBatches=kept)


def turning_identity_scope(seed, batches=None):
    batches = seed.get("manualBatches", []) if batches is None else batches
    conflicts = inspect_turning_queue(seed, batches)["conflicts"]
    products = {_key(p) for c in conflicts for p in [c["product"], *[r["product"] for r in c["records"]]] if _key(p)}
    machines = {m for c in conflicts for m in [c["machineId"], *[r["machineId"] for r in c["records"]]] if m}
    batch_ids, lots, histories = {c["batchId"] for c in conflicts}, set(), set()
    def add(target, value):
        if value:
            target.add(value)
    def related(product):
        return _key(product) in products
    size = -1
    while size != len(machines) + len(batch_ids) + len(lots) + len(histories):
        size = len(machines) + len(batch_ids) + len(lots) + len(histories)
        for b in batches:
            if related(b.get("product")) or b.get("id") in batch_ids or b.get("machineId") in machines:
                add(machines, b.get("machineId")); add(batch_ids, b.get("id"))
        for m in seed.get("machines", []):
            job = m.get("currentJob", {})
            if related(job.get("product")) or job.get("batchId") in batch_ids or m.get("id") in machines:
                add(machines, m.get("id")); add(batch_ids, job.get("batchId")); add(batch_ids, f'current:{m.get("id")}')
        for h in seed.get("productionHistory", []):
            if related(h.get("product")) or h.get("id") in histories or h.get("sourceEntryId") in histories or h.get("sourceBatchId") in batch_ids or any(a.get("lotId") in lots for a in h.get("wipAllocations", [])):
                add(histories, h.get("id")); add(histories, h.get("sourceEntryId")); add(batch_ids, h.get("sourceBatchId"))
                for a in h.get("wipAllocations", []):
                    add(lots, a.get("lotId"))
        for lot in seed.get("wipLots", []):
            if related(lot.get("product")) or lot.get("id") in lots or lot.get("parentLotId") in lots or lot.get("sourceHistoryEntryId") in histories or lot.get("sourceBatchId") in batch_ids:
                add(lots, lot.get("id")); add(lots, lot.get("parentLotId")); add(histories, lot.get("sourceHistoryEntryId")); add(batch_ids, lot.get("sourceBatchId"))
        for job in seed.get("processCurrentJobs", []):
            if related(job.get("product")) or job.get("batchId") in batch_ids or job.get("wipLotId") in lots:
                add(batch_ids, job.get("batchId")); add(lots, job.get("wipLotId"))
        for item in seed.get("productionInterruptions", []):
            if related(item.get("product")) or item.get("chargeId") in batch_ids:
                add(batch_ids, item.get("chargeId"))
                if item.get("process") == "turning":
                    add(machines, item.get("resourceId"))
    return dict(products=sorted(products), machineIds=sorted(machines), batchIds=sorted(batch_ids), lotIds=sorted(lots), historyIds=sorted(histories))


_FROZEN_CONFIGURATION = ("products", "preferences", "restrictions", "holidays", "calendarEvents", "setupSettings", "processMasterData", "savedBatches", "activePlanningScope", "customerDemand", "openingStock", "demandTargets", "orderImport", "orderImportGrossOrders", "customerOrderOverrides")


def _protected_identity_snapshot(seed, scope):
    def p(value):
        return _key(value) in scope["products"]
    def b(value):
        return bool(value and value in scope["batchIds"])
    def l(value):
        return bool(value and value in scope["lotIds"])
    def h(value):
        return bool(value and value in scope["historyIds"])
    return dict(
        configuration={k: seed.get(k) for k in _FROZEN_CONFIGURATION},
        machines=[m for m in seed.get("machines", []) if m.get("id") in scope["machineIds"] or p(m.get("currentJob", {}).get("product")) or b(m.get("currentJob", {}).get("batchId"))],
        manualBatches=[r for r in seed.get("manualBatches", []) if p(r.get("product")) or b(r.get("id")) or r.get("machineId") in scope["machineIds"]],
        productionHistory=[r for r in seed.get("productionHistory", []) if p(r.get("product")) or h(r.get("id")) or h(r.get("sourceEntryId")) or b(r.get("sourceBatchId")) or any(l(a.get("lotId")) for a in r.get("wipAllocations", []))],
        wipLots=[r for r in seed.get("wipLots", []) if p(r.get("product")) or l(r.get("id")) or l(r.get("parentLotId")) or h(r.get("sourceHistoryEntryId")) or b(r.get("sourceBatchId"))],
        wipMovements=[r for r in seed.get("wipMovements", []) if l(r.get("lotId"))],
        productionInterruptions=[r for r in seed.get("productionInterruptions", []) if p(r.get("product")) or b(r.get("chargeId")) or r.get("process") == "turning" and r.get("resourceId") in scope["machineIds"]],
        processCurrentJobs=[r for r in seed.get("processCurrentJobs", []) if p(r.get("product")) or b(r.get("batchId")) or l(r.get("wipLotId"))],
        processOperationOverrides=[r for r in seed.get("processOperationOverrides", []) if b(r.get("batchId")) or l(r.get("batchId"))],
        orders=[r for r in seed.get("orders", []) if p(r.get("product"))],
    )


def assert_turning_identity_transition(before, next_seed):
    previous = inspect_turning_queue(before)["conflicts"]
    if not previous:
        checked = reconcile_turning_seed(next_seed)
        if checked.get("manualBatches", []) != next_seed.get("manualBatches", []):
            raise ValueError("Mevcut veya tamamlanmış şarj kuyrukta tekrar bulunuyor. Ortak veriyi yükleyin.")
        return
    scope = turning_identity_scope(before)
    if _protected_identity_snapshot(before, scope) != _protected_identity_snapshot(next_seed, scope):
        raise ValueError("Bu işlem inceleme bekleyen şarjı veya bağlı kayıtlarını değiştiriyor. Önce İncele ve düzelt ile şarj kaydını doğrulayın.")
    if _recovered_turning_batches(next_seed) != next_seed.get("manualBatches", []):
        raise ValueError("Yarım kalan şarjın kuyruk kaydı korunmalıdır. Ortak veriyi yükleyin.")
    inspected = inspect_turning_queue(next_seed)
    if previous != inspected["conflicts"]:
        raise ValueError("İşlem yeni bir şarj kimliği çakışması oluşturuyor. İncele ve düzelt ile kayıtları doğrulayın.")
    if len(inspected["reconciledBatches"]) != len(next_seed.get("manualBatches", [])):
        raise ValueError("Mevcut veya tamamlanmış şarj kuyrukta tekrar bulunuyor. Ortak veriyi yükleyin.")


def repair_turning_identity(seed, request):
    reason = request.get("reason", "")
    if not isinstance(reason, str) or not reason.strip() or len(reason.strip()) > 2000:
        raise ValueError("Düzeltme nedeni zorunludur ve en fazla 2000 karakter olabilir.")
    rows = [b for b in seed.get("manualBatches", []) if b.get("id") == request.get("batchId")]
    before = inspect_turning_queue(seed)
    target = next((c for c in before["conflicts"] if c["batchId"] == request.get("batchId")), None)
    if len(rows) != 1 or not target or target["reason"] == "duplicate-queue-id":
        raise ValueError("Şarj tek bir kuyruk kaydı olarak doğrulanamıyor. Kayıtları sistem yöneticisiyle inceleyin.")
    row = rows[0]
    if (row.get("interruptionId") or any(i.get("chargeId") == row["id"] for i in seed.get("productionInterruptions", []))
        or any(m.get("currentJob", {}).get("batchId") == row["id"] and m.get("currentJob", {}).get("quantity", 0) > 0 for m in seed.get("machines", []))
        or any(l.get("sourceBatchId") == row["id"] for l in seed.get("wipLots", []))
        or any(j.get("batchId") == row["id"] for j in seed.get("processCurrentJobs", []))
        or any(o.get("batchId") == row["id"] for o in seed.get("processOperationOverrides", []))
        or any(h.get("sourceBatchId") == row["id"] and h.get("sourceBatchId") != h.get("id") for h in seed.get("productionHistory", []))):
        raise ValueError("Başlamış, yarım kalmış veya başka proseslere bağlı şarj bu pencereden düzeltilemez.")
    result = copy.deepcopy(seed)
    if request.get("action") == "work-order":
        work_order = request.get("workOrder", "")
        if not isinstance(work_order, str) or not work_order.strip() or len(work_order.strip()) > 100 or _key(work_order) == _key(row.get("workOrder")):
            raise ValueError("Farklı ve geçerli bir iş emri girin.")
        next(b for b in result["manualBatches"] if b["id"] == row["id"])["workOrder"] = work_order.strip()
    elif request.get("action") == "remove-duplicate":
        if request.get("confirmedDuplicate") is not True or not any(r["kind"] in ("current", "history") and _key(r["product"]) == _key(row.get("product")) and _key(r["workOrder"]) == _key(row.get("workOrder")) for r in target["records"]):
            raise ValueError("Mevcut üretim/arşiv kaydıyla aynı fiziksel iş olduğunu doğrulayın.")
        result["manualBatches"] = [b for b in result["manualBatches"] if b["id"] != row["id"]]
    else:
        raise ValueError("Geçersiz şarj düzeltmesi.")
    after = inspect_turning_queue(result)
    remaining = [c for c in before["conflicts"] if c["batchId"] != row["id"]]
    if after["conflicts"] != remaining or len(after["reconciledBatches"]) != len(result.get("manualBatches", [])):
        raise ValueError("Bu düzeltme çakışmayı güvenle çözmüyor veya başka şarjı etkiliyor. Kayıtları yeniden inceleyin.")
    result["planNeedsRecalculation"] = True
    result.pop("lastAutomaticPlan", None)
    return result
