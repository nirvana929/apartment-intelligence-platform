from __future__ import annotations

from typing import Protocol


class MemoryRepository(Protocol):
    def save(self, user_id: str, key: str, value: str) -> None: ...
    def load_all(self, user_id: str) -> dict[str, str]: ...
    def delete(self, user_id: str, key: str) -> None: ...


class InMemoryMemoryRepo:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, str]] = {}
        self._contract_store: dict[str, dict] = {}  # keyed by memory_id

    # -- Legacy sync methods (backward compat) --

    def save(self, user_id: str, key: str, value: str) -> None:
        self._store.setdefault(user_id, {})[key] = value

    def load_all(self, user_id: str) -> dict[str, str]:
        return dict(self._store.get(user_id, {}))

    def delete(self, user_id: str, key: str) -> None:
        user_data = self._store.get(user_id)
        if user_data is not None:
            user_data.pop(key, None)
            if not user_data:
                del self._store[user_id]

    # -- Async contract methods (MemoryRepositoryContract) --

    async def list_memories(self, user_id: str) -> list[dict]:
        return [
            {"memory_id": mid, "kind": m["kind"], "key_name": m["key_name"], "value_json": m["value_json"]}
            for mid, m in self._contract_store.items()
            if m["user_id"] == user_id
        ]

    async def upsert_memory(
        self, memory_id: str, user_id: str, kind: str, key_name: str, value_json: dict
    ) -> None:
        self._contract_store[memory_id] = {
            "user_id": user_id,
            "kind": kind,
            "key_name": key_name,
            "value_json": value_json,
        }
