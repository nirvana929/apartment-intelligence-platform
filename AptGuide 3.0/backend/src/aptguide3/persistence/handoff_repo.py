from __future__ import annotations

import uuid
from typing import Protocol


class HandoffRepository(Protocol):
    def create(self, session_id: str, reason: str, context: dict) -> str: ...
    def list_open(self) -> list[dict]: ...
    def resolve(self, handoff_id: str) -> None: ...


class InMemoryHandoffRepo:
    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    # -- Legacy sync methods (backward compat) --

    def create(self, session_id: str, reason: str, context: dict) -> str:
        handoff_id = uuid.uuid4().hex[:12]
        self._store[handoff_id] = {
            "handoff_id": handoff_id,
            "session_id": session_id,
            "reason": reason,
            "context": context,
            "status": "open",
        }
        return handoff_id

    def list_open(self) -> list[dict]:
        return [h for h in self._store.values() if h["status"] == "open"]

    def resolve(self, handoff_id: str) -> None:
        record = self._store.get(handoff_id)
        if record is not None:
            record["status"] = "resolved"

    # -- Async contract methods (HandoffRepositoryContract) --

    async def create_ticket(
        self, ticket_id: str, session_id: str, user_id: str, trigger_type: str, summary: dict
    ) -> None:
        self._store[ticket_id] = {
            "ticket_id": ticket_id,
            "session_id": session_id,
            "user_id": user_id,
            "trigger_type": trigger_type,
            "summary": summary,
            "status": "open",
        }

    async def list_tickets(self, status: str = "open") -> list[dict]:
        return [t for t in self._store.values() if t.get("status") == status]
