"""Server-owned permissions for shared planning inputs."""
from __future__ import annotations

from copy import deepcopy
import math


class InputPermissionError(ValueError):
    pass


ADMIN_FIELDS = (
    "setupSettings", "processWaitSettings", "flowSettings", "productWeights",
    "rawMaterialSettings", "processStockSettings", "filterWaitShifts", "filterQualityShifts",
    "openingStock", "filterInitialStockSetup", "filterMonthlyDeliveryBaselines",
)
PRODUCT_FIELDS = {
    "generalMachine", "eligibleMachines", "alternativeMachines", "inactiveMachineIds",
    "batchSize", "dailyRate", "shiftRate", "parameterDailyRate", "diameter", "setupFamily",
    "moq", "source", "customer", "targetWarehouse", "shipmentMultiple", "setupScrapPercent", "productionScrapPercent",
}


def _without(value, fields):
    return {key: item for key, item in value.items() if key not in fields}


def _rows(value, key):
    rows = value or []
    if not isinstance(rows, list) or any(not isinstance(row, dict) or not isinstance(row.get(key), str) for row in rows):
        raise InputPermissionError("Kayıt kimlikleri geçersiz.")
    mapped = {row[key]: row for row in rows}
    if len(mapped) != len(rows):
        raise InputPermissionError("Kayıt kimlikleri tekil olmalıdır.")
    return mapped


def assert_user_configuration(current: dict | None, candidate: dict, *, operational: bool = False) -> None:
    current = current or {}
    for field in ADMIN_FIELDS:
        if current.get(field) != candidate.get(field):
            raise InputPermissionError("Stok, hammadde, SETUP ve akış ayarlarını yalnız yönetici değiştirebilir.")
    if current.get("holidays", []) != candidate.get("holidays", []):
        raise InputPermissionError("Tatil tanımını ve tarihini yalnız yönetici değiştirebilir. Tatil için vardiya ekleyebilirsiniz.")
    machine_fields = {"rates", "shiftFactor"} | ({"currentJob", "availableStart", "operationalAvailableStart"} if operational else set())
    before = _rows(current.get("machines"), "id")
    after = _rows(candidate.get("machines"), "id")
    if list(before) != list(after) or any(_without(row, machine_fields) != _without(after[key], machine_fields) for key, row in before.items()):
        raise InputPermissionError("Tezgah tanımlarını yalnız yönetici değiştirebilir.")
    for key, row in after.items():
        if row.get("shiftFactor") == before[key].get("shiftFactor"):
            continue
        if row.get("shiftFactor") not in (0, 1, 2, 3) or isinstance(row.get("shiftFactor"), bool):
            raise InputPermissionError("Vardiya sayısı 0, 1, 2 veya 3 olmalıdır.")
    old_products = _rows(current.get("products"), "product")
    new_products = _rows(candidate.get("products"), "product")
    if any(key not in new_products for key in old_products):
        raise InputPermissionError("Tipi yalnız yönetici silebilir.")
    for key, row in new_products.items():
        previous = old_products.get(key, {"product": key})
        if _without(previous, PRODUCT_FIELDS) != _without(row, PRODUCT_FIELDS):
            raise InputPermissionError("Proses ve rota parametrelerini yalnız yönetici değiştirebilir.")
    previous_master, next_master = deepcopy(current.get("processMasterData")), deepcopy(candidate.get("processMasterData"))
    for master in (previous_master, next_master):
        if isinstance(master, dict):
            for resource in master.get("resources", []):
                resource.pop("defaultShifts", None)
    if previous_master != next_master:
        raise InputPermissionError("Proses, rota ve iş merkezi tanımlarını yalnız yönetici değiştirebilir.")
    old_resources = _rows((current.get("processMasterData") or {}).get("resources"), "id")
    for resource in (candidate.get("processMasterData") or {}).get("resources", []):
        if resource.get("defaultShifts") == old_resources.get(resource["id"], {}).get("defaultShifts"):
            continue
        shifts = resource.get("defaultShifts")
        if shifts not in (0, 1, 2, 3) or isinstance(shifts, bool):
            raise InputPermissionError("Vardiya sayısı 0, 1, 2 veya 3 olmalıdır.")
    if current.get("calendarEvents", []) == candidate.get("calendarEvents", []):
        return
    holidays = {int(row["serial"]) for row in current.get("holidays", [])}
    resource_ids = set(after) | set(old_resources)
    old_events = _rows(current.get("calendarEvents"), "id")
    new_events = _rows(candidate.get("calendarEvents"), "id")
    if [row for row in old_events.values() if row.get("kind") != "shift"] != [row for row in new_events.values() if row.get("kind") != "shift"]:
        raise InputPermissionError("Planlı bakımı yalnız yönetici değiştirebilir.")
    def non_holiday_shifts(events):
        projection = {}
        for event in events.values():
            if event.get("kind") != "shift":
                continue
            start, end = event.get("start"), event.get("end")
            shifts = event.get("shiftCount")
            if (not isinstance(start, (int, float)) or not isinstance(end, (int, float))
                    or not math.isfinite(start) or not math.isfinite(end) or end < start or end - start > 3660
                    or (event.get("machineId") not in resource_ids and not any(_without(event, {"id", "start", "end"}) == _without(old, {"id", "start", "end"}) for old in old_events.values())) or not isinstance(event.get("name"), str)
                    or shifts not in (0, 1, 2, 3) or isinstance(shifts, bool)):
                raise InputPermissionError("Tatil vardiyası için geçerli tezgah, tarih ve 0–3 vardiya gereklidir.")
            for day in range(int(start), int(end) + 1):
                if day not in holidays:
                    key = (event["machineId"], day)
                    projection.setdefault(key, []).append(_without(event, {"id", "start", "end"}))
        return projection
    if non_holiday_shifts(old_events) != non_holiday_shifts(new_events):
        raise InputPermissionError("Takvimi yalnız yönetici değiştirebilir. Resmi tatil günlerine vardiya ekleyebilirsiniz.")
