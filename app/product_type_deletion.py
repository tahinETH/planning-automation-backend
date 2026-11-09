"""Keep demand and production references intact when a Piston type is removed."""


def _code(value):
    return value.strip().upper() if isinstance(value, str) else ""


def product_type_deletion_blockers(seed, product):
    target = _code(product)

    def has(rows):
        return any(_code(row.get("product")) == target for row in (rows or []))

    reasons = []
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
    if not before or before.get("productionArea") == "cubuk-filtre":
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
