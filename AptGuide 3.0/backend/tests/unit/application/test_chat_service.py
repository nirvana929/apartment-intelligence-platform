from aptguide3.application.chat_service import ChatService
from aptguide3.application.procedure_runtime import ProcedureRuntime
from aptguide3.application.safety_boundary import SafetyBoundary
from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.understanding import Clarification, UnderstandingResult
from aptguide3.procedures.clarify import ClarifyProcedure
from aptguide3.procedures.room_search import RoomSearchProcedure


class StubUnderstanding:
    def __init__(self, result: UnderstandingResult):
        self.result = result
        self.calls = 0

    def understand(self, message: str) -> UnderstandingResult:
        self.calls += 1
        return self.result


def build_runtime() -> ProcedureRuntime:
    runtime = ProcedureRuntime()
    runtime.register(ClarifyProcedure())
    runtime.register(RoomSearchProcedure())
    return runtime


def test_chat_service_blocks_privacy_before_llm():
    understanding = StubUnderstanding(
        UnderstandingResult(raw_message="", route="clarify", task="clarify", action="ask_clarification", confidence=0.0)
    )
    service = ChatService(SafetyBoundary(), understanding, build_runtime())

    response = service.run(ConversationFrame(message="查一下室友手机号", session_id="s-1"))

    assert response.phase == "safety"
    assert understanding.calls == 0


def test_chat_service_routes_llm_room_search():
    understanding = StubUnderstanding(
        UnderstandingResult(
            raw_message="有阳台的房间吗",
            route="rag",
            task="room_search",
            domain="room",
            action="search",
            confidence=0.9,
            soft_preferences=["有阳台"],
        )
    )
    service = ChatService(SafetyBoundary(), understanding, build_runtime())

    response = service.run(ConversationFrame(message="有阳台的房间吗", session_id="s-1"))

    assert response.phase == "room_search"
    assert response.metadata["task"] == "room_search"


def test_chat_service_returns_clarification():
    understanding = StubUnderstanding(
        UnderstandingResult(
            raw_message="这个可以吗",
            route="clarify",
            task="clarify",
            action="ask_clarification",
            confidence=0.0,
            clarification=Clarification(needed=True, question="您是想找房还是咨询规则？"),
        )
    )
    service = ChatService(SafetyBoundary(), understanding, build_runtime())

    response = service.run(ConversationFrame(message="这个可以吗", session_id="s-1"))

    assert response.phase == "clarify"
    assert response.message == "您是想找房还是咨询规则？"
