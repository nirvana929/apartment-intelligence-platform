from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.understanding import UnderstandingResult


class MemoryProcedure:
    name = "memory"

    def run(self, frame: ConversationFrame, understanding: UnderstandingResult) -> ProcedureResult:
        return ProcedureResult(
            message="偏好记忆功能即将上线。",
            phase="memory",
            metadata={"route": understanding.route, "task": understanding.task, "action": understanding.action},
        )
