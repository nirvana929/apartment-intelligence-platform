from __future__ import annotations

from typing import Any

from aptguide2.harness.errors import StrategyNotFoundError


class StrategyRegistry:
    """In-memory registry for harness strategies and procedures."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, str], Any] = {}

    def register(self, category: str, name: str, strategy: Any) -> None:
        self._items[(category, name)] = strategy

    def get(self, category: str, name: str) -> Any:
        key = (category, name)
        if key not in self._items:
            raise StrategyNotFoundError(f"Strategy not found: {category}.{name}")
        return self._items[key]

    def names(self, category: str) -> list[str]:
        return sorted(name for (cat, name) in self._items if cat == category)
