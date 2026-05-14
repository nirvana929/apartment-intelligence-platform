from __future__ import annotations

from typing import Any, Protocol

from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision
from aptguide2.harness.errors import ProcedureNotFoundError


class Procedure(Protocol):
    def run(self, frame: ConversationFrame, decision: RouteDecision, tool_runtime: Any | None = None) -> ProcedureResult:
        ...


class ProcedureRuntime:
    """Executes registered procedures by route decision."""

    def __init__(self) -> None:
        self._procedures: dict[str, Procedure] = {}

    def register(self, name: str, procedure: Procedure) -> None:
        self._procedures[name] = procedure

    def has(self, name: str) -> bool:
        return name in self._procedures

    def run(self, frame: ConversationFrame, decision: RouteDecision, tool_runtime: Any | None = None) -> ProcedureResult:
        procedure = self._procedures.get(decision.procedure)
        if procedure is None:
            raise ProcedureNotFoundError(f"Procedure not found: {decision.procedure}")
        return procedure.run(frame, decision, tool_runtime=tool_runtime)
