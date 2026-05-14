from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: str | None = None
    action: dict[str, Any] | None = None
    client_context: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    message: str
    phase: str
    cards: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    pending_action: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
