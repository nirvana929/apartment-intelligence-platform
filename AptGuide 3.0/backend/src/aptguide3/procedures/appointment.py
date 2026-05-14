from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.understanding import UnderstandingResult


class AppointmentProcedure:
    name = "appointment"

    def run(self, frame: ConversationFrame, understanding: UnderstandingResult) -> ProcedureResult:
        return ProcedureResult(
            message="预约看房功能即将上线，目前可通过电话预约。",
            phase="appointment",
            metadata={"route": understanding.route, "task": understanding.task, "domain": understanding.domain},
        )
