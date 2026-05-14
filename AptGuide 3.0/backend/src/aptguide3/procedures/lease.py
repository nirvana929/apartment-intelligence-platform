from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.understanding import UnderstandingResult


class LeaseProcedure:
    name = "lease"

    def run(self, frame: ConversationFrame, understanding: UnderstandingResult) -> ProcedureResult:
        return ProcedureResult(
            message="租约查询功能即将上线，请联系管家获取租约信息。",
            phase="lease",
            metadata={"route": understanding.route, "task": understanding.task, "domain": understanding.domain},
        )
