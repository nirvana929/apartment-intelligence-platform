from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ConversationFrame(BaseModel):
    message: str
    session_id: str
    user_id: str | None = None
    action: dict[str, Any] | None = None
    client_context: dict[str, Any] = Field(default_factory=dict)
    pending_action: dict[str, Any] | None = None
