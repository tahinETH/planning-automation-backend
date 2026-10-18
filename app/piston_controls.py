"""Server checks for Piston parameter deactivation and production cancellation.

The browser owns the calculation. The server rejects writes that bypass the
reviewed rules: a new Pasif assignment with undecided queued work, and
cancellation records that are malformed, altered or carry a client identity.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


def _instant(value: Any) -> datetime | None:
    if not isinstance(value, str) or len(value) < 20:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else None


def _code(value: Any) -> str:
    return str(value or "").strip().upper()


def _pasif_targets(seed: dict[str, Any]) -> set[tuple[str, str, str]]:
    targets: set[tuple[str, str, str]] = set()
    for product in seed.get("products") or []:
        for machine_id in product.get("inactiveMachineIds") or []:
            targets.add(("turning", _code(product.get("product")), str(machine_id)))
    for product in (seed.get("processMasterData") or {}).get("products") or []:
        for parameter in product.get("processes") or []:
            for resource_id in parameter.get("inactiveResourceIds") or []:
                targets.add((str(parameter.get("process")), _code(product.get("product")), str(resource_id)))
    return targets


def assert_pasif_transition(current: dict[str, Any] | None, seed: dict[str, Any]) -> None:
    """Reject a newly Pasif product-resource pair that still has queued work.

    Legacy Pasif pairs already present in the stored revision stay accepted, so
    an existing conflict never blocks unrelated saves or destroys evidence.
    """
    previous = _pasif_targets(current or {})
    added = _pasif_targets(seed) - previous
    if not added:
        return
    problems: list[str] = []
    running = {(job.get("batchId"), job.get("process")) for job in seed.get("processCurrentJobs") or []}
    lots = {lot.get("id"): lot for lot in seed.get("wipLots") or []}
    batches = seed.get("manualBatches") or []
    for process, product, resource_id in sorted(added):
        if process == "turning":
            for batch in batches:
                if batch.get("status") == "planned" and batch.get("machineId") == resource_id and _code(batch.get("product")) == product:
                    problems.append(f"{batch.get('product')} · {str(batch.get('workOrder') or '').strip() or batch.get('id')} · {resource_id} (Torna)")
            continue
        for override in seed.get("processOperationOverrides") or []:
            if override.get("process") != process or override.get("resourceId") != resource_id or override.get("routeMode") == "automatic":
                continue
            if (override.get("batchId"), process) in running:
                continue
            owner = override.get("sourceProduct") or (lots.get(override.get("batchId")) or {}).get("product") \
                or next((b.get("product") for b in batches if b.get("id") == override.get("batchId")), "")
            if _code(owner) == product:
                problems.append(f"{owner} · {override.get('batchId')} · {resource_id} ({process})")
    if problems:
        shown = "; ".join(problems[:5]) + (f" ve {len(problems) - 5} iş daha" if len(problems) > 5 else "")
        raise ValueError(
            "Parametreler: Pasif yapılan atamada kuyruktaki işler için karar gerekiyor. "
            f"{shown}. Uygulamayı yenileyip her iş için karar verin."
        )


CANCELLATION_STATUSES = {"pending", "replacement-approved", "replacement-declined"}
MAX_CLOSED_CANCELLATIONS = 200


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_production_cancellations(current: dict[str, Any] | None, seed: dict[str, Any], actor_id: str, actor_name: str, timestamp: str) -> dict[str, Any]:
    """Validate cancellation records and stamp server identity on new facts.

    Recorded facts (quantities, charge, reason, time) are immutable once saved.
    Only the review may move from pending to a decision; the reviewer is the
    authenticated user. A record cannot disappear while its review is open.
    """
    records = seed.get("productionCancellations")
    previous = {item.get("id"): item for item in (current or {}).get("productionCancellations") or [] if isinstance(item, dict)}
    if records is None:
        if any((item.get("review") or {}).get("status") != "replacement-approved" for item in previous.values()):
            raise ValueError("Üretim iptali kayıtlarını korumak için uygulamayı yenileyip ortak veriyi tekrar yükleyin.")
        return seed
    if not isinstance(records, list):
        raise ValueError("Üretim iptali kayıtları liste olmalıdır.")
    seen: set[str] = set()
    stamped: list[dict[str, Any]] = []
    fact_keys = ("product", "process", "chargeId", "workOrder", "machineId", "assignedQuantity", "completedQuantity", "cancelledQuantity", "reason", "cancelledAt", "orderIds", "orderQuantities", "historyEntryId")
    for raw in records:
        if not isinstance(raw, dict) or raw.get("version") != 1 or not isinstance(raw.get("id"), str) or not raw["id"] or raw["id"] in seen:
            raise ValueError("Üretim iptali kaydı geçersiz veya tekrarlı.")
        seen.add(raw["id"])
        item = dict(raw)
        if item.get("process") != "turning":
            raise ValueError("Yalnız Torna kalan üretimi iptal edilebilir.")
        if not _positive_int(item.get("assignedQuantity")) or not _nonnegative_int(item.get("completedQuantity")) or not _positive_int(item.get("cancelledQuantity")):
            raise ValueError(f"{item.get('product')} iptal adetleri pozitif tam sayı olmalıdır.")
        if item["completedQuantity"] + item["cancelledQuantity"] != item["assignedQuantity"]:
            raise ValueError(f"{item.get('product')} için üretilen + iptal edilen adet atanmış adede eşit olmalıdır.")
        cancelled_at = _instant(item.get("cancelledAt"))
        if cancelled_at is None:
            raise ValueError(f"{item.get('product')} iptal zamanı geçersiz.")
        if not str(item.get("reason") or "").strip():
            raise ValueError(f"{item.get('product')} için iptal nedeni zorunludur.")
        order_ids = item.get("orderIds")
        quantities = item.get("orderQuantities")
        if not isinstance(order_ids, list) or not all(isinstance(x, str) and x for x in order_ids) or len(set(order_ids)) != len(order_ids):
            raise ValueError(f"{item.get('product')} iptal kaydının sipariş bağlantısı geçersiz.")
        if not isinstance(quantities, dict) or set(quantities) != set(order_ids) or not all(_nonnegative_int(quantities[x]) for x in order_ids):
            raise ValueError(f"{item.get('product')} iptal kaydının sipariş adetleri geçersiz.")
        if "historyEntryId" in item and not (item["historyEntryId"] is None or isinstance(item["historyEntryId"], str)):
            raise ValueError(f"{item.get('product')} iptal kaydının üretim arşivi bağlantısı geçersiz.")
        review = item.get("review")
        if not isinstance(review, dict) or review.get("status") not in CANCELLATION_STATUSES:
            raise ValueError(f"{item.get('product')} iptal incelemesi geçersiz.")
        old = previous.get(item["id"])
        if old is None:
            now = _instant(timestamp)
            if now is not None and cancelled_at > now + timedelta(minutes=1):
                raise ValueError(f"{item.get('product')} iptal zamanı gelecekte olamaz.")
            if review["status"] != "pending":
                raise ValueError("Yeni iptal kaydı inceleme bekliyor durumunda olmalıdır.")
            item["recordedBy"] = actor_name or actor_id
            item["recordedById"] = actor_id
            item["review"] = {"status": "pending"}
        else:
            if any(old.get(key) != item.get(key) for key in fact_keys):
                raise ValueError(f"{item.get('product')} iptal kaydının adet, şarj ve neden bilgileri değiştirilemez.")
            item["recordedBy"] = old.get("recordedBy")
            item["recordedById"] = old.get("recordedById")
            old_review = old.get("review") or {}
            if review["status"] == old_review.get("status"):
                item["review"] = dict(old_review)
            elif old_review.get("status") == "pending":
                item["review"] = {"status": review["status"], "reviewedAt": timestamp, "reviewedBy": actor_name or actor_id, "reviewedById": actor_id,
                                  **({"note": str(review["note"])[:500]} if review.get("note") else {})}
            else:
                raise ValueError(f"{item.get('product')} iptal incelemesi zaten sonuçlandı.")
        stamped.append(item)
    for old_id, old in previous.items():
        if old_id not in seen and (old.get("review") or {}).get("status") != "replacement-approved":
            raise ValueError(f"{old.get('product')} için üretimi bekleten iptal kaydı silinemez.")
    # Pending and declined records still withhold production; only approved history is bounded.
    holding = [item for item in stamped if item["review"]["status"] != "replacement-approved"]
    approved = [item for item in stamped if item["review"]["status"] == "replacement-approved"][-MAX_CLOSED_CANCELLATIONS:]
    return {**seed, "productionCancellations": [*holding, *approved]}
