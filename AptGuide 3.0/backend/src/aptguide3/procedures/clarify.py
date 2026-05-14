from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.understanding import UnderstandingResult


class ClarifyProcedure:
    name = "clarify"

    def run(self, frame: ConversationFrame, understanding: UnderstandingResult) -> ProcedureResult:
        question = understanding.clarification.question or "请补充一下您的需求。"
        return ProcedureResult(
            message=question,
            phase="clarify",
            metadata={"route": understanding.route, "task": understanding.task, "reason": understanding.reason},
        )
