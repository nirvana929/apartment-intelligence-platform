from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.understanding import UnderstandingResult


class ProcedureResult(BaseModel):
    message: str
    phase: str
    cards: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    pending_action: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Procedure(Protocol):
    name: str

    def run(self, frame: ConversationFrame, understanding: UnderstandingResult) -> ProcedureResult:
        ...
