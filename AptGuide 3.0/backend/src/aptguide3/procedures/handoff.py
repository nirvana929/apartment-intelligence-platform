from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.understanding import UnderstandingResult


class HandoffProcedure:
    name = "handoff"

    def run(self, frame: ConversationFrame, understanding: UnderstandingResult) -> ProcedureResult:
        return ProcedureResult(
            message="正在为您转接人工客服，请稍候。",
            phase="handoff",
            metadata={"route": understanding.route, "task": understanding.task},
        )
