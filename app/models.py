from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    body: str = Field(min_length=1, max_length=20_000)
    page_path: str = Field(default="", max_length=200)
    priority: Literal[1, 2, 3] = 2


class LoginRequest(BaseModel):
    password: str = Field(min_length=1, max_length=500)


class FeedbackUpdate(BaseModel):
    body: str | None = Field(default=None, min_length=1, max_length=20_000)
    status: Literal["active", "resolved", "canceled"] | None = None
    priority: Literal[1, 2, 3] | None = None


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=10_000)


class CommentUpdate(BaseModel):
    body: str = Field(min_length=1, max_length=10_000)


class ScenarioPayload(BaseModel):
    id: str
    name: str
    createdAt: str
    notes: str = ""
    seed: dict[str, Any]
    result: dict[str, Any]


class DataPackagePayload(BaseModel):
    scope: Literal["parameters", "settings", "scenarios"]
    data: Any


class RevisionPayload(BaseModel):
    id: str
    orderId: str
    product: str
    status: str
    createdAt: str
    approvedAt: str
    original: dict[str, Any]
    requested: dict[str, Any]
    impact: dict[str, Any]
    seed: dict[str, Any]
    result: dict[str, Any]


class PlanningStatePayload(BaseModel):
    seed: dict[str, Any]


class DemandImportHistoryPayload(BaseModel):
    id: str = Field(min_length=1, max_length=160)
    importedAt: str
    sourceFile: str = Field(min_length=1, max_length=255)
    snapshotDate: str
    dataset: dict[str, Any]
    summary: dict[str, Any]


class DeliveryPlanWeek(BaseModel):
    label: str = Field(min_length=1, max_length=12)


class DeliveryPlanRow(BaseModel):
    product: str = Field(min_length=1, max_length=100)
    orderQuantity: int = Field(ge=0)
    weeklyQuantities: list[int]


class DeliveryPlanPayload(BaseModel):
    startDate: str
    endDate: str
    category: str = Field(default="Üretim", min_length=1, max_length=100)
    weeks: list[DeliveryPlanWeek]
    rows: list[DeliveryPlanRow]


class OverviewSummary(BaseModel):
    demand: int = Field(ge=0)
    planned: int = Field(ge=0)
    plannedBatchCount: int = Field(ge=0)
    unplannedBatchCount: int = Field(ge=0)
    activeMachineCount: int = Field(ge=0)
    machineCount: int = Field(ge=0)
    machinesWithWorkCount: int = Field(ge=0)
    plannedMachineCount: int = Field(ge=0)


class OverviewQueueRow(BaseModel):
    kind: Literal["current", "planned"]
    position: int = Field(ge=0)
    product: str = Field(max_length=100)
    diameter: str = Field(default="", max_length=40)
    quantity: int = Field(ge=0)
    endDate: str = Field(default="", max_length=40)
    workOrder: str = Field(default="", max_length=120)


class OverviewMachine(BaseModel):
    id: str = Field(min_length=1, max_length=40)
    name: str = Field(default="", max_length=160)
    active: bool
    plannedCount: int = Field(ge=0)
    plannedQuantity: int = Field(ge=0)
    rows: list[OverviewQueueRow]


class OverviewFinding(BaseModel):
    severity: Literal["critical", "warning", "info"]
    title: str = Field(max_length=300)
    detail: str = Field(max_length=2_000)
    target: str = Field(default="", max_length=200)


class OverviewExportPayload(BaseModel):
    generatedAt: str
    createdAt: str = ""
    planState: Literal["planned", "empty"]
    dirty: bool
    summary: OverviewSummary
    machines: list[OverviewMachine]
    findings: list[OverviewFinding] = []
