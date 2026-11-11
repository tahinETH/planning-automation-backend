"""Keep demand and production references intact when a type is removed."""

from copy import deepcopy


def _code(value):
    return value.strip().upper() if isinstance(value, str) else ""


def product_type_deletion_blockers(seed, product):
    target = _code(product)

    def has(rows):
        return any(_code(row.get("product")) == target for row in (rows or []))

    def contains_reference(value):
        if isinstance(value, list):
            return any(contains_reference(item) for item in value)
        if isinstance(value, dict):
            return _code(value.get("product")) == target or any(contains_reference(item) for item in value.values())
        return False

    reasons = []
    if any(contains_reference(seed.get(key)) for key in ("dailyCustomerDemand", "monthlyCustomerDemand", "filterInitialStockSetup", "filterMonthlyDeliveryBaselines", "filterMonthlyPlan")):
        reasons.append("Çubuk Filtre: müşteri talebi, sayım veya teslimat kesimi kaydı var.")
    if any(has(seed.get(key)) for key in ("orders", "orderImportGrossOrders", "demandTargets", "customerOrderOverrides")) or has((seed.get("customerDemand") or {}).get("products")):
        reasons.append("Siparişler: sipariş veya müşteri Excel kaydı var.")
    if has(seed.get("manualBatches")) or has(seed.get("savedBatches")):
        reasons.append("Planlama: kayıtlı veya ekranda açık şarj var.")
    if any(_code((m.get("currentJob") or {}).get("product")) == target and (m.get("currentJob") or {}).get("quantity", 0) > 0 for m in seed.get("machines", [])) or has(seed.get("processCurrentJobs")):
        reasons.append("Tezgahlar: çalışan iş var.")
    if has(seed.get("productionHistory")):
        reasons.append("Üretim arşivi: üretim, teslimat veya ıskarta kaydı var.")
    if has(seed.get("wipLots")):
        reasons.append("Yarı mamul: stok veya geçmiş şarj kaydı var.")
    if has(seed.get("productionInterruptions")) or has(seed.get("productionCancellations")):
        reasons.append("Üretim: yarım kalan veya iptal edilen iş kaydı var.")
    if any(_code(row.get("sourceProduct")) == target for row in seed.get("processOperationOverrides", [])):
        reasons.append("Planlama: kayıtlı proses yerleşimi var.")
    stock = seed.get("processStockSettings") or {}
    if any(_code(key) == target and quantity != 0 for key, quantity in (seed.get("openingStock") or {}).items()) or has(stock.get("opening")) or has(stock.get("scrap")):
        reasons.append("Stoklar: başlangıç stoğu veya ürüne özel stok ayarı var.")
    return reasons


def assert_product_type_deletion_safe(before, after):
    if not before:
        return
    removed = set()
    for previous, incoming in (
        (before.get("products", []), after.get("products", [])),
        ((before.get("processMasterData") or {}).get("products", []), (after.get("processMasterData") or {}).get("products", [])),
    ):
        removed.update({_code(row.get("product")) for row in previous} - {_code(row.get("product")) for row in incoming})
    for product in sorted(removed - {""}):
        # Checking both revisions also rejects attempts to remove usage in the same write.
        reasons = list(dict.fromkeys(product_type_deletion_blockers(before, product) + product_type_deletion_blockers(after, product)))
        if reasons:
            raise ValueError(f"{product} silinemez. {' '.join(reasons)}")


def remove_unused_product_type(seed, product):
    """Remove configuration only after checking current demand and physical usage."""
    target = _code(product)
    reasons = product_type_deletion_blockers(seed, target)
    if reasons:
        raise ValueError(f"{target} silinemez. {' '.join(reasons)}")
    next_seed = deepcopy(seed)
    next_seed["products"] = [row for row in seed.get("products", []) if _code(row.get("product")) != target]
    if next_seed.get("processMasterData"):
        next_seed["processMasterData"]["products"] = [row for row in next_seed["processMasterData"].get("products", []) if _code(row.get("product")) != target]
    for field, key in (("preferences", "key"), ("restrictions", "product"), ("productWeights", "product")):
        if field in next_seed:
            next_seed[field] = [row for row in next_seed[field] if _code(row.get(key)) != target]
    if "orderCatalog" in next_seed:
        next_seed["orderCatalog"] = [value for value in next_seed["orderCatalog"] if _code(value) != target]
    for machine in next_seed.get("machines", []):
        machine["rates"] = {key: value for key, value in machine.get("rates", {}).items() if _code(key) != target}
    if "openingStock" in next_seed:
        next_seed["openingStock"] = {key: value for key, value in next_seed["openingStock"].items() if _code(key) != target}
    next_seed["planNeedsRecalculation"] = True
    next_seed.pop("lastAutomaticPlan", None)
    next_seed.pop("planRunSequence", None)
    return next_seed


def preserve_type_retirement(seed, previous):
    """Old clients/backups cannot reactivate a retired type by omitting the flag."""
    seed = deepcopy(seed)
    retired = {_code(row.get("product")) for row in (previous or {}).get("products", []) if row.get("retired") is True}
    for row in seed.get("products", []):
        if "retired" in row and not isinstance(row["retired"], bool):
            raise ValueError("Tip kullanım durumu doğru veya yanlış olmalıdır.")
        if "retired" not in row and _code(row.get("product")) in retired:
            row["retired"] = True
    return seed
