from __future__ import annotations

import json
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

View = Literal["planning", "processes", "control", "orders", "machines", "parameters", "settings", "scenarios", "feedback"]


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=6000)


class BrowserContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    view: View
    capturedAt: str = Field(max_length=40)
    navigation: dict[str, Any] = Field(default_factory=dict)
    planning: dict[str, Any] = Field(default_factory=dict)
    screens: dict[str, Any] = Field(default_factory=dict)

    @field_validator("navigation", "planning", "screens")
    @classmethod
    def bounded_data(cls, value: dict) -> dict:
        if len(json.dumps(value, ensure_ascii=False, allow_nan=False)) > 40000:
            raise ValueError("Ekran bağlamı çok büyük")
        return value


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=4000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)
    context: BrowserContext

    @field_validator("message")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Mesaj boş olamaz")
        return value.strip()

    @field_validator("history")
    @classmethod
    def bounded_history(cls, value: list[ChatMessage]) -> list[ChatMessage]:
        if sum(len(item.content) for item in value) > 24000:
            raise ValueError("Konuşma geçmişi çok büyük")
        return value
