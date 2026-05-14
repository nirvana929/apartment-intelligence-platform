from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from aptguide3.domain.procedures import ProcedureResult


class ChatResponse(BaseModel):
    message: str
    phase: str
    cards: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    pending_action: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_procedure_result(cls, result: ProcedureResult) -> ChatResponse:
        return cls(
            message=result.message,
            phase=result.phase,
            cards=result.cards,
            actions=result.actions,
            pending_action=result.pending_action,
            metadata=result.metadata,
        )
