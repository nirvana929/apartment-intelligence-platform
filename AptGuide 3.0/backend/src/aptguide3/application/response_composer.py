from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.responses import ChatResponse


class ResponseComposer:
    def compose(self, result: ProcedureResult) -> ChatResponse:
        return ChatResponse.from_procedure_result(result)
