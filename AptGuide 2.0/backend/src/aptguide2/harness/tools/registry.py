from __future__ import annotations

from aptguide2.harness.tools.contracts import ToolDefinition
from aptguide2.harness.tools.errors import ToolAlreadyRegisteredError, ToolNotFoundError


class ToolRegistry:
    """In-memory registry for tool definitions."""

    def __init__(self) -> None:
        self._definitions: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        if definition.name in self._definitions:
            raise ToolAlreadyRegisteredError(f"Tool already registered: {definition.name}")
        self._definitions[definition.name] = definition

    def get(self, name: str) -> ToolDefinition:
        if name not in self._definitions:
            raise ToolNotFoundError(f"Tool not found: {name}")
        return self._definitions[name]

    def names(self) -> list[str]:
        return sorted(self._definitions.keys())

    def by_backend(self, backend: str) -> list[ToolDefinition]:
        return [d for d in self._definitions.values() if d.backend == backend]

    def requires_confirmation(self) -> list[ToolDefinition]:
        return [d for d in self._definitions.values() if d.requires_confirmation]
