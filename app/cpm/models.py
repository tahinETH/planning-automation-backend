"""Strict, bounded payload schemas for Piston CPM snapshots and collector protocol."""
from __future__ import annotations

from datetime import datetime
import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


EXCLUDED_SCRAP_DEPOTS = frozenset({"ISK", "149"})


def _check_finite(value: float, allow_negative: bool = False) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError("Sayısal değer geçersiz.")
    if not allow_negative and value < 0:
        raise ValueError("Negatif değer kabul edilmez.")
    return float(value)


def _check_iso_timestamp(value: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError("Zaman damgası boş olamaz.")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Zaman damgası ISO-8601 formatında olmalıdır.") from exc
    if parsed.tzinfo is None:
        raise ValueError("Zaman damgası saat dilimi içermelidir.")
    return text


def _clean_code(value: str, max_len: int = 40, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError("Kod alanı metin olmalıdır.")
    text = value.strip()
    if not allow_empty and not text:
        raise ValueError("Kod alanı boş olamaz.")
    if len(text) > max_len or any(ord(ch) < 32 for ch in text):
        raise ValueError("Kod alanı geçersiz karakter veya uzunluk içeriyor.")
    return text


class CpmOtherDepotQty(BaseModel):
    model_config = ConfigDict(extra="forbid")

    depotCode: str = Field(..., max_length=24)
    depotName: str = Field("", max_length=120)
    kg: float = Field(...)

    @field_validator("depotCode")
    @classmethod
    def _val_code(cls, v: str) -> str:
        return _clean_code(v, 24)

    @field_validator("kg")
    @classmethod
    def _val_kg(cls, v: float) -> float:
        return _check_finite(v, allow_negative=True)


class CpmRawMaterialRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materialCode: str = Field(..., max_length=40)
    materialName: str = Field("", max_length=200)
    unit: str = Field("KG", max_length=16)
    depot141Kg: float = Field(0.0)
    depot320Kg: float = Field(0.0)
    totalAvailableKg: float = Field(0.0)
    depot250Kg: float = Field(0.0)
    depot960Kg: float = Field(0.0)
    otherDepots: list[CpmOtherDepotQty] = Field(default_factory=list, max_length=32)

    @field_validator("materialCode")
    @classmethod
    def _val_code(cls, v: str) -> str:
        return _clean_code(v, 40)

    @field_validator("depot141Kg", "depot320Kg", "totalAvailableKg", "depot250Kg", "depot960Kg")
    @classmethod
    def _val_num(cls, v: float) -> float:
        return _check_finite(v, allow_negative=True)

    @model_validator(mode="after")
    def _verify_total(self) -> "CpmRawMaterialRow":
        expected = round(self.depot141Kg + self.depot320Kg, 4)
        if abs(self.totalAvailableKg - expected) > 0.01:
            raise ValueError("totalAvailableKg alanı depot141Kg + depot320Kg toplamına eşit olmalıdır.")
        return self


class CpmProductDepotStock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    depotCode: str = Field(..., max_length=24)
    depotName: str = Field("", max_length=120)
    version: str = Field("", max_length=32)
    qty: float = Field(...)

    @field_validator("depotCode")
    @classmethod
    def _val_depot(cls, v: str) -> str:
        return _clean_code(v, 24)

    @field_validator("version")
    @classmethod
    def _val_version(cls, v: str) -> str:
        # Preserve leading zeros and empty string exactly.
        return _clean_code(v, 32, allow_empty=True)

    @field_validator("qty")
    @classmethod
    def _val_qty(cls, v: float) -> float:
        return _check_finite(v, allow_negative=True)


class CpmProductStockRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product: str = Field(..., max_length=40)
    drillingQueueQty: float = Field(0.0)
    deburringQueueQty: float = Field(0.0)
    gkmQueueQty: float = Field(0.0)
    gkmCompletedQty: float = Field(0.0)
    finishedWarehouseQty: float = Field(0.0)
    consignmentQty: float = Field(0.0)
    scrapExcludedQty: float = Field(0.0)
    depots: list[CpmProductDepotStock] = Field(default_factory=list, max_length=64)

    @field_validator("product")
    @classmethod
    def _val_product(cls, v: str) -> str:
        return _clean_code(v, 40)

    @field_validator(
        "drillingQueueQty",
        "deburringQueueQty",
        "gkmQueueQty",
        "gkmCompletedQty",
        "finishedWarehouseQty",
        "consignmentQty",
        "scrapExcludedQty",
    )
    @classmethod
    def _val_qty(cls, v: float) -> float:
        return _check_finite(v, allow_negative=False)


class CpmWorkOrderStage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    isemriNo: str = Field(..., max_length=40)
    version: str = Field("", max_length=32)
    workCenterCode: str = Field(..., max_length=24)
    workCenterName: str = Field("", max_length=120)
    targetQty: float = Field(0.0)
    producedQty: float = Field(0.0)
    scrapQty: float = Field(0.0)
    opStatus: int = Field(0)
    lastMachineCode: str | None = Field(default=None, max_length=32)
    lastMachineName: str | None = Field(default=None, max_length=120)
    lastErpCode: str | None = Field(default=None, max_length=40)
    lastRunAt: str | None = Field(default=None, max_length=64)
    lastShift: str | None = Field(default=None, max_length=32)

    @field_validator("isemriNo", "workCenterCode")
    @classmethod
    def _val_codes(cls, v: str) -> str:
        return _clean_code(v, 40)

    @field_validator("version")
    @classmethod
    def _val_version(cls, v: str) -> str:
        return _clean_code(v, 32, allow_empty=True)

    @field_validator("targetQty", "producedQty", "scrapQty")
    @classmethod
    def _val_qty(cls, v: float) -> float:
        return _check_finite(v, allow_negative=False)


class CpmWorkOrderRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    uretimNo: str = Field(..., max_length=40)
    product: str = Field(..., max_length=40)
    targetQty: float = Field(0.0)
    orderDate: str = Field("", max_length=32)
    orderStatus: int = Field(0)
    currentStage: Literal[
        "not-started",
        "turning-in-progress",
        "drilling-queue",
        "drilling-in-progress",
        "deburring-queue",
        "deburring-in-progress",
        "washing-queue",
        "washing-in-progress",
        "gkm-queue",
        "gkm-in-progress",
        "gkm-completed",
    ]
    turningMachineCode: str | None = Field(default=None, max_length=32)
    turningMachineName: str | None = Field(default=None, max_length=120)
    turningErpCode: str | None = Field(default=None, max_length=40)
    turningProducedQty: float = Field(0.0)
    turningLastRunAt: str | None = Field(default=None, max_length=64)
    stages: list[CpmWorkOrderStage] = Field(default_factory=list, max_length=24)

    @field_validator("uretimNo", "product")
    @classmethod
    def _val_id(cls, v: str) -> str:
        return _clean_code(v, 40)

    @field_validator("targetQty", "turningProducedQty")
    @classmethod
    def _val_qty(cls, v: float) -> float:
        return _check_finite(v, allow_negative=False)


class CpmBomWeightRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product: str = Field(..., max_length=40)
    materialCode: str = Field(..., max_length=40)
    materialName: str = Field("", max_length=200)
    grams: float = Field(...)
    unit: str = Field("GRAM", max_length=16)

    @field_validator("product", "materialCode")
    @classmethod
    def _val_code(cls, v: str) -> str:
        return _clean_code(v, 40)

    @field_validator("grams")
    @classmethod
    def _val_grams(cls, v: float) -> float:
        return _check_finite(v, allow_negative=False)


class CpmCycleTimeRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product: str = Field(..., max_length=40)
    version: str = Field("", max_length=32)
    workCenterCode: str = Field(..., max_length=24)
    resourceCode: str = Field(..., max_length=32)
    resourceName: str = Field("", max_length=120)
    erpWorkCenterCode: str = Field("", max_length=40)
    cycleSeconds: float = Field(...)

    @field_validator("product", "workCenterCode", "resourceCode")
    @classmethod
    def _val_codes(cls, v: str) -> str:
        return _clean_code(v, 40)

    @field_validator("version", "erpWorkCenterCode")
    @classmethod
    def _val_opt(cls, v: str) -> str:
        return _clean_code(v, 40, allow_empty=True)

    @field_validator("cycleSeconds")
    @classmethod
    def _val_sec(cls, v: float) -> float:
        return _check_finite(v, allow_negative=False)


class CpmResourceRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resourceCode: str = Field(..., max_length=32)
    resourceName: str = Field("", max_length=120)
    erpWorkCenterCode: str = Field("", max_length=40)
    active: bool = True

    @field_validator("resourceCode")
    @classmethod
    def _val_code(cls, v: str) -> str:
        return _clean_code(v, 32)

    @field_validator("erpWorkCenterCode")
    @classmethod
    def _val_erp(cls, v: str) -> str:
        return _clean_code(v, 40, allow_empty=True)


class CpmParametersSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bomWeights: list[CpmBomWeightRow] = Field(default_factory=list, max_length=500)
    cycleTimes: list[CpmCycleTimeRow] = Field(default_factory=list, max_length=4000)
    resources: list[CpmResourceRow] = Field(default_factory=list, max_length=200)


class CpmPistonSnapshotPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schemaVersion: Literal[1] = 1
    area: Literal["torna"] = "torna"
    company: Literal["17"] = "17"
    collectorId: str = Field(..., min_length=1, max_length=80)
    triggerKind: Literal["scheduled-15m", "on-demand", "manual"] = "manual"
    requestId: str | None = Field(default=None, max_length=64)
    startedAt: str = Field(..., max_length=64)
    capturedAt: str = Field(..., max_length=64)
    rawMaterialScope: str = Field("141+320", max_length=40)
    rawMaterials: list[CpmRawMaterialRow] = Field(default_factory=list, max_length=200)
    productStocks: list[CpmProductStockRow] = Field(default_factory=list, max_length=500)
    workOrders: list[CpmWorkOrderRow] = Field(default_factory=list, max_length=2000)
    parameters: CpmParametersSection = Field(default_factory=CpmParametersSection)

    @field_validator("startedAt", "capturedAt")
    @classmethod
    def _val_ts(cls, v: str) -> str:
        return _check_iso_timestamp(v)

    @field_validator("collectorId")
    @classmethod
    def _val_collector(cls, v: str) -> str:
        return _clean_code(v, 80)

    @model_validator(mode="after")
    def _check_uniqueness(self) -> "CpmPistonSnapshotPayload":
        rm_codes = [row.materialCode for row in self.rawMaterials]
        if len(rm_codes) != len(set(rm_codes)):
            raise ValueError("Hammadde kodları tekrarlanamaz.")
        prod_codes = [row.product for row in self.productStocks]
        if len(prod_codes) != len(set(prod_codes)):
            raise ValueError("Ürün stok kodları tekrarlanamaz.")
        wo_codes = [row.uretimNo for row in self.workOrders]
        if len(wo_codes) != len(set(wo_codes)):
            raise ValueError("Üretim emri numaraları (URETIMNO) tekrarlanamaz.")
        return self


class CpmCollectorHeartbeatPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    collectorId: str = Field(..., min_length=1, max_length=80)
    area: Literal["torna"] = "torna"
    vpnConnected: bool = False
    intervalSeconds: int = Field(900, ge=60, le=86400)
    nextScheduledAt: str | None = Field(default=None, max_length=64)
    lastError: str | None = Field(default=None, max_length=400)

    @field_validator("collectorId")
    @classmethod
    def _val_collector(cls, v: str) -> str:
        return _clean_code(v, 80)

    @field_validator("nextScheduledAt")
    @classmethod
    def _val_next(cls, v: str | None) -> str | None:
        return _check_iso_timestamp(v) if v else None


class CpmCollectorFailurePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    collectorId: str = Field(..., min_length=1, max_length=80)
    area: Literal["torna"] = "torna"
    triggerKind: Literal["scheduled-15m", "on-demand", "manual"] = "manual"
    requestId: str | None = Field(default=None, max_length=64)
    errorCode: str = Field(..., min_length=1, max_length=64)
    errorMessage: str = Field(..., min_length=1, max_length=500)

    @field_validator("collectorId", "errorCode")
    @classmethod
    def _val_code(cls, v: str) -> str:
        return _clean_code(v, 80)
