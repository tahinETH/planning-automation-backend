from __future__ import annotations

import json
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from . import knowledge


class Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Search(Arguments):
    query: str = Field(min_length=1, max_length=300)


class Topic(Arguments):
    topic_id: str = Field(min_length=1, max_length=100)


class Source(Arguments):
    path: str = Field(min_length=1, max_length=200)
    start_line: int = Field(default=1, ge=1)
    line_count: int = Field(default=80, ge=1, le=120)


class Inspect(Arguments):
    collection: Literal["summary", "orders", "products", "product_weights", "raw_material_stocks", "machines", "customer_demand", "wip", "production", "batches", "calendar", "process_resources", "process_products", "process_current_jobs", "overrides"]
    query: str = Field(default="", max_length=100)
    offset: int = Field(default=0, ge=0, le=100000)
    week_offset: int = Field(default=0, ge=0, le=1000)


class Navigate(Arguments):
    target_id: str = Field(min_length=1, max_length=100)


DEFINITIONS = {
    "search_knowledge": (Search, "Find app screens, workflows and calculation explanations. Turkish informal queries supported."),
    "read_knowledge": (Topic, "Read a user-facing explanation anchored to Excel headers and visible UI labels."),
    "search_source": (Search, "Find packaged frontend/backend modules and symbols by file/function name. Use before reading unfamiliar implementation."),
    "read_source": (Source, "Privately verify exact shipped behavior; translate findings into Excel/UI business language in the answer. Never execute source."),
    "inspect_state": (Inspect, "Read persisted planning data, not unsaved browser state. Query filters product/ID. customer_demand returns imported Excel headers/balances and file/date, NOT live workbook access. Paginated: offset for product rows, week_offset for 20-week windows; check nextOffset/nextWeekOffset."),
    "propose_navigation": (Navigate, "Offer a registered navigation button for the user to click. This does not navigate or modify anything now."),
}


def definitions() -> list[dict]:
    return [{"type": "function", "function": {"name": name, "description": description, "parameters": model.model_json_schema()}}
            for name, (model, description) in DEFINITIONS.items()]


def bounded(value, depth=0):
    """Limit arbitrary saved text/arrays without ever returning broken JSON."""
    if depth > 8:
        return "[depth limit]"
    if isinstance(value, str):
        return value if len(value) <= 800 else value[:800] + "… [truncated]"
    if isinstance(value, list):
        items = [bounded(item, depth + 1) for item in value[:40]]
        return items if len(value) <= 40 else {"items": items, "total": len(value), "truncated": True}
    if isinstance(value, dict):
        result = {key: bounded(item, depth + 1) for key, item in list(value.items())[:60]}
        if len(value) > 60:
            result["_truncatedKeys"] = len(value) - 60
        return result
    return value


def inspect_state(snapshot: dict | None, args: Inspect) -> dict:
    if snapshot is None:
        return {"source": "persisted-server", "available": False, "reason": "Henüz kaydedilmiş ortak plan yok; tarayıcı bağlamını kullan."}
    seed = snapshot["seed"]
    meta = {"source": "persisted-server", "updatedAt": snapshot["updatedAt"], "available": True}
    if args.collection == "summary":
        demand = seed.get("customerDemand") or {}
        return {**meta, "orderCount": len(seed.get("orders", [])), "machineCount": len(seed.get("machines", [])),
                "orderQuantity": sum(max(0, item.get("quantity", 0)) for item in seed.get("orders", [])),
                "orderSource": bounded({key: demand.get(key) for key in ("sourceFile", "snapshotDate", "importedAt", "activeScope", "calculationModel", "baselineDueDate")}),
                "orderImport": bounded(seed.get("orderImport")), "activePlanRun": bounded(seed.get("activePlanRun")),
                "setupSettings": bounded(seed.get("setupSettings")), "note": "Hesaplanmış frontend sonucu değildir; quantities adet, plan tarihleri Excel serial gün olabilir."}
    collections = {
        "raw_material_stocks": (seed.get("rawMaterialSettings") or {}).get("stocks", []),
        "product_weights": seed.get("productWeights", []),
        "orders": seed.get("orders", []), "products": seed.get("products", []), "machines": seed.get("machines", []),
        "customer_demand": (seed.get("customerDemand") or {}).get("products", []),
        "wip": seed.get("wipLots", []), "production": seed.get("productionHistory", []),
        "batches": seed.get("manualBatches", []), "calendar": seed.get("calendarEvents", []) + seed.get("holidays", []),
        "process_resources": (seed.get("processMasterData") or {}).get("resources", []),
        "process_products": (seed.get("processMasterData") or {}).get("products", []),
        "process_current_jobs": seed.get("processCurrentJobs", []), "overrides": seed.get("customerOrderOverrides", []),
    }
    query = knowledge.normalize(args.query.strip())
    rows = [row for row in collections[args.collection] if not query or query in knowledge.normalize(" ".join(
        str(row.get(key, "")) for key in ("id", "product", "materialCode", "machineId", "resourceId", "workOrder", "sourceBatchId", "name")))]
    selected = []
    for row in rows[args.offset:args.offset + 12]:
        if args.collection == "raw_material_stocks":
            materials = seed.get("rawMaterialSettings") or {}
            projected = {"Hammadde Kodu": row.get("materialCode"), "Ambar stoğu (kg)": row.get("kg"),
                         "Güncelleme Tarihi": materials.get("stockDate"), "Iskarta Oranı (%)": materials.get("scrapPercent", 2),
                         "Birim": "kg", "Ekran": "Ayarlar → Hammadde Bilgileri → Hammadde Tüketim Tablosu"}
        elif args.collection == "product_weights":
            projected = {"Tip no": row.get("product"), "Hammadde kodu": row.get("materialCode"),
                         "Hammadde açıklaması": row.get("materialName"), "Hammadde ağırlığı (g)": row.get("grams"),
                         "Birim": "Gram", "Ekran": "Ayarlar → Hammadde Bilgileri → Ürün Ağırlıkları"}
        elif args.collection == "customer_demand":
            demand = seed.get("customerDemand") or {}
            weeks = row.get("weeklyDemands", [])
            window = weeks[args.week_offset:args.week_offset + 20]
            projected = {"Material": row.get("product"), "Unit": row.get("unit"),
                         "Available quantity": row.get("availableQuantity"),
                         demand.get("baselineLabel") or "< CW …": row.get("baselineBalance"),
                         "weeks": [{"column": week.get("label") or week.get("weekId"), "balance": week.get("balance")} for week in window],
                         "nextWeekOffset": args.week_offset + len(window) if args.week_offset + len(window) < len(weeks) else None}
        else:
            projected = bounded(row)
        if len(json.dumps([*selected, projected], ensure_ascii=False)) > 18000:
            if not selected:
                selected.append({**{key: bounded(value) for key, value in row.items() if not isinstance(value, (dict, list))}, "_truncated": "İç ayrıntılar araç boyut sınırı nedeniyle çıkarıldı."})
            break
        selected.append(projected)
    next_offset = args.offset + len(selected)
    if args.collection == "customer_demand":
        demand = seed.get("customerDemand") or {}
        meta["userSource"] = {"sourceFile": demand.get("sourceFile"), "sheet": "3. Overview (confirmed)",
                              "Date": demand.get("snapshotDate"), "baselineColumn": demand.get("baselineLabel"),
                              "selectedScope": demand.get("activeScope"),
                              "note": "İçe aktarılmış Balance (confirmed) değerleri; dosya canlı açılmadı. Kullanıcı düzeltmeleri ayrıca overrides koleksiyonundadır."}
    return {**meta, "collection": args.collection, "total": len(rows), "rows": selected,
            "nextOffset": next_offset if next_offset < len(rows) else None,
            "note": "İç listeler en fazla 40 kayıt; truncated işaretlerini kontrol et." if any(isinstance(value, dict) and value.get("truncated") for row in selected for value in row.values()) else ("CPM’den elle girilmiş gün başı stokları kg cinsindedir; boş bilinmiyor, sıfır stok yok demektir. Canlı CPM bağlantısı veya sunucuda tüketim tahmini yoktur." if args.collection == "raw_material_stocks" else "Hammadde ağırlıkları gram cinsindedir; boş değer bilinmiyor demektir." if args.collection == "product_weights" else "Miktarlar adet; sayısal tarihler Excel serial günleridir.")}


class ToolSession:
    def __init__(self, snapshot: dict | None, is_admin: bool):
        self.snapshot = snapshot
        self.targets = {target["id"]: target for target in knowledge.navigation_targets(is_admin)}
        self.actions: dict[str, dict] = {}
        self.references: dict[str, dict] = {}
        self.used: list[str] = []

    def cite(self, topic: dict) -> None:
        for source in topic["sources"]:
            key = source["path"] + ":" + source.get("symbol", "")
            self.references[key] = source

    def execute(self, name: str, raw: str) -> dict | list:
        try:
            if name not in DEFINITIONS or len(raw) > 4000:
                raise ValueError("Bilinmeyen araç veya çok uzun argüman")
            args = DEFINITIONS[name][0].model_validate_json(raw)
            self.used.append(name)
            if name == "search_knowledge":
                topics = knowledge.search_topics(args.query)
                for topic in topics:
                    self.cite(topic)
                return [knowledge.for_model(topic) for topic in topics]
            if name == "read_knowledge":
                topic = knowledge.read_topic(args.topic_id)
                self.cite(topic)
                return knowledge.for_model(topic)
            if name == "search_source":
                return knowledge.search_source(args.query)
            if name == "read_source":
                source = knowledge.read_source(args.path, args.start_line, args.line_count)
                self.references[f"{args.path}:{args.start_line}"] = {"path": args.path, "line": args.start_line}
                return source
            if name == "inspect_state":
                return inspect_state(self.snapshot, args)
            if name == "propose_navigation":
                target = self.targets.get(args.target_id)
                if target is None:
                    raise ValueError("Hedef yok veya bu kullanıcı için erişilebilir değil")
                self.actions[target["id"]] = target
                return {"proposed": target, "executed": False, "instruction": "Kullanıcı bu düğmeye basarsa hedef açılır."}
        except (ValueError, ValidationError):
            return {"error": "Geçersiz araç isteği. Şemayı ve izin verilen hedefleri kontrol ederek düzelt."}
        return {"error": "Araç sonucu bulunamadı"}
