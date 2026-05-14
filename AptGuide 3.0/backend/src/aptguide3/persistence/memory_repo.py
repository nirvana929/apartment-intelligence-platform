from __future__ import annotations

from typing import Protocol


class MemoryRepository(Protocol):
    def save(self, user_id: str, key: str, value: str) -> None: ...
    def load_all(self, user_id: str) -> dict[str, str]: ...
    def delete(self, user_id: str, key: str) -> None: ...


class InMemoryMemoryRepo:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, str]] = {}

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
