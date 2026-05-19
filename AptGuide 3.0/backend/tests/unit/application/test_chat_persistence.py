from aptguide3.application.chat_service import ChatService
from aptguide3.application.procedure_runtime import ProcedureRuntime
from aptguide3.application.safety_boundary import SafetyBoundary
from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.procedures.clarify import ClarifyProcedure


class StubUnderstanding:
    def __init__(self):
        self.result = UnderstandingResult(
            raw_message="hi",
            route="clarify",
            task="clarify",
            action="ask_clarification",
            confidence=0.99,
        )

    def understand(self, message):
        return self.result


class RecordingMessages:
    def __init__(self):
        self.messages = []

    async def append_message(self, session_id, user_id, request_id, role, content, metadata):
        self.messages.append((role, content, metadata))


def _build_service(message_repo=None):
    runtime = ProcedureRuntime()
    runtime.register(ClarifyProcedure())
    return ChatService(
        SafetyBoundary(),
        StubUnderstanding(),
        runtime,
        message_repo=message_repo,
    )


def test_chat_service_persists_user_and_assistant_messages():
    messages = RecordingMessages()
    service = _build_service(message_repo=messages)
    response = service.run(ConversationFrame(session_id="s1", user_id="u1", message="hi"))
    assert response.message is not None
    assert [m[0] for m in messages.messages] == ["user", "assistant"]


def test_chat_service_works_without_message_repo():
    service = _build_service()
    response = service.run(ConversationFrame(session_id="s1", user_id="u1", message="hi"))
    assert response.message is not None
