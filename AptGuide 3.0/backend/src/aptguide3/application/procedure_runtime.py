from __future__ import annotations

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import Procedure, ProcedureResult
from aptguide3.domain.understanding import UnderstandingResult


class ProcedureNotFoundError(Exception):
    pass


class ProcedureRuntime:
    def __init__(self) -> None:
        self._procedures: dict[str, Procedure] = {}

    def register(self, procedure: Procedure) -> None:
        self._procedures[procedure.name] = procedure

    def run(self, frame: ConversationFrame, understanding: UnderstandingResult) -> ProcedureResult:
        name = self._procedure_name(understanding)
        procedure = self._procedures.get(name)
        if procedure is None:
            raise ProcedureNotFoundError(name)
        return procedure.run(frame, understanding)

    def _procedure_name(self, understanding: UnderstandingResult) -> str:
        if understanding.route == "clarify":
            return "clarify"
        if understanding.route == "rag":
            return understanding.task
        return understanding.route
