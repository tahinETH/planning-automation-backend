"""Validate reviewed daily-demand, stock-group and working-wait inputs."""
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo
import math
import re

MAX_INTEGER = 9007199254740991

def _integer(value):
    return type(value) is int and 0 <= value <= MAX_INTEGER

def _date(value):
    return isinstance(value, str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)) and date.fromisoformat(value).isoformat() == value

def uses_stock_planning(seed):
    return any(key in seed for key in ("processStockSettings", "dailyCustomerDemand", "filterMonthlyPlan", "filterWaitShifts")) or any(
        stage.get("calendarMode") for product in (seed.get("processMasterData") or {}).get("products", [])
        for process in product.get("processes", []) for stage in process.get("leadStages", [])
    )

def validate_stock_planning(seed):
    area = seed.get("productionArea", "torna")
    if "filterWaitShifts" in seed and (area != "cubuk-filtre" or type(seed["filterWaitShifts"]) is not int or seed["filterWaitShifts"] not in range(4)):
        raise ValueError("Çubuk Filtre bekleme vardiyası 0–3 olmalıdır.")
    for product in (seed.get("processMasterData") or {}).get("products", []):
        for process in product.get("processes", []):
            for stage in process.get("leadStages", []):
                if "calendarMode" not in stage:
                    continue
                days = stage.get("days")
                if (area != "cubuk-filtre" or stage["calendarMode"] not in ("workdays", "workhours") or type(days) not in (int, float)
                        or not math.isfinite(days) or not 0 <= days <= 366 or stage["calendarMode"] == "workdays" and days != int(days)):
                    raise ValueError("Çalışma takvimi bekleme süresi geçersiz.")
    products = {p.get("product") for p in seed.get("products", [])}
    if "processStockSettings" in seed:
        data = seed["processStockSettings"]
        groups = {"form-front", "mill-front", "visual-front", "warehouse"} if area == "cubuk-filtre" else {"turning-end", "drilling-end", "visual-front", "warehouse"}
        if not isinstance(data, dict) or data.get("version") != 1 or any(not isinstance(data.get(key), list) or len(data[key]) > 1000 for key in ("limits", "scrap", "opening")):
            raise ValueError("Stok ayarları geçersiz.")
        seen = set()
        for row in data["limits"]:
            if not isinstance(row, dict) or row.get("groupId") not in groups or row["groupId"] in seen or not all(_integer(row.get(key)) for key in ("min", "max")) or row["min"] > row["max"]:
                raise ValueError("Stok grup limitleri geçersiz.")
            seen.add(row["groupId"])
        if seen != groups:
            raise ValueError("Stok grup limitleri eksik.")
        for kind in ("scrap", "opening"):
            seen = set()
            for row in data[kind]:
                if not isinstance(row, dict) or row.get("groupId") not in groups or row.get("product") not in products:
                    raise ValueError("Stok grubu / ürünü geçersiz.")
                key = (row["groupId"], row["product"])
                if key in seen:
                    raise ValueError("Stok grubu / ürünü tekrarlı.")
                seen.add(key)
                value = row.get("percent" if kind == "scrap" else "quantity")
                if kind == "opening" and not _integer(value) or kind == "scrap" and (type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value <= 100):
                    raise ValueError("Stok adedi / ıskarta oranı geçersiz.")
        if any(row["quantity"] for row in data["opening"]) and (not _date(data.get("openingDate")) or date.fromisoformat(data["openingDate"]) > datetime.now(ZoneInfo("Europe/Istanbul")).date()):
            raise ValueError("Stok sayım tarihi geçersiz.")
    if seed.get("filterMonthlyPlan") is not None:
        plan = seed["filterMonthlyPlan"]
        twelve = lambda values: isinstance(values, list) and len(values) == 12
        if area != "cubuk-filtre" or not isinstance(plan, dict) or type(plan.get("year")) is not int or not 2000 <= plan["year"] <= 2100 or not twelve(plan.get("workingDays")) \
                or any(type(days) not in (int, float) or not 0 <= days <= 31 or (days * 2) % 1 for days in plan["workingDays"]):
            raise ValueError("Çalışma Günleri yılı / iş günleri geçersiz.")
        rows = plan.get("rows")
        if not isinstance(rows, list) or not 0 < len(rows) <= 60 or any(
                not isinstance(row, dict) or row.get("product") not in products or row.get("kind") not in ("internal", "external")
                or not twelve(row.get("quantities")) or not all(_integer(value) for value in row["quantities"]) for row in rows):
            raise ValueError("Çalışma Günleri ürün satırları geçersiz.")
    if "dailyCustomerDemand" in seed and seed["dailyCustomerDemand"] is not None:
        data = seed["dailyCustomerDemand"]
        if area != "cubuk-filtre" or not isinstance(data, dict) or data.get("format") != "filter-daily" or not all(_date(data.get(key)) for key in ("snapshotDate", "endDate")):
            raise ValueError("Günlük sipariş alanı / tarihleri geçersiz.")
        if data.get("startDate") is not None and (not _date(data["startDate"]) or data["startDate"] > data["endDate"]):
            raise ValueError("Günlük sipariş başlangıç tarihi geçersiz.")
        rows = data.get("dailyRows")
        if not isinstance(rows, list) or len(rows) > 12000:
            raise ValueError("Günlük sipariş satırları geçersiz.")
        seen = set()
        for row in rows:
            if not isinstance(row, dict) or not _date(row.get("date")) or row.get("product") not in products or not all(_integer(row.get(key)) for key in ("ordered", "delivered")):
                raise ValueError("Günlük sipariş adedi / ürünü geçersiz.")
            key = (row["date"], row["product"])
            if key in seen or row["delivered"] > 0 and row["date"] > data["snapshotDate"]:
                raise ValueError("Günlük sipariş tekrarlı veya teslimat kesim tarihinden sonra.")
            seen.add(key)
        metadata = seed.get("orderImport") or {}
        try:
            imported = datetime.fromisoformat(data["importedAt"].replace("Z", "+00:00"))
            cutoff = datetime.fromisoformat(metadata["shipmentsThrough"].replace("Z", "+00:00"))
            if not imported.tzinfo or not cutoff.tzinfo or cutoff > imported:
                raise ValueError()
        except (KeyError, ValueError, TypeError):
            raise ValueError("Günlük sipariş yükleme / teslimat kesim zamanı geçersiz.") from None
