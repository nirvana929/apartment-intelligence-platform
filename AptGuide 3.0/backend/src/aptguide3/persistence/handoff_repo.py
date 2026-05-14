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
