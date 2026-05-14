from __future__ import annotations

from typing import Protocol


class SessionRepository(Protocol):
    def save(self, session_id: str, data: dict) -> None: ...
    def load(self, session_id: str) -> dict | None: ...
    def delete(self, session_id: str) -> None: ...


class InMemorySessionRepo:
    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def save(self, session_id: str, data: dict) -> None:
        self._store[session_id] = data

    def load(self, session_id: str) -> dict | None:
        return self._store.get(session_id)

    def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)
