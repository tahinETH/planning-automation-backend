from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    body: str = Field(min_length=1, max_length=20_000)
    page_path: str = Field(default="", max_length=200)


class LoginRequest(BaseModel):
    password: str = Field(min_length=1, max_length=500)


class FeedbackUpdate(BaseModel):
    body: str | None = Field(default=None, min_length=1, max_length=20_000)
    status: Literal["active", "resolved", "canceled"] | None = None


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
