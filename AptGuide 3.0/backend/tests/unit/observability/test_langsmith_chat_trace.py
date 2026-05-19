"""Unit tests for LangSmith chat output tracing.

Verifies that ChatService passes final response to the LangSmith recorder,
that the recorder is a safe no-op when disabled, and that safety-blocked
responses are also recorded.

Note: trace_output_visibility is verified via local recorder tests, not
remote LangSmith inspection.
"""

from __future__ import annotations

from aptguide3.application.chat_service import ChatService
from aptguide3.application.procedure_runtime import ProcedureRuntime
from aptguide3.application.safety_boundary import SafetyBoundary
from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.observability.langsmith_trace import LangSmithChatRecorder
from aptguide3.procedures.clarify import ClarifyProcedure
from aptguide3.procedures.room_search import RoomSearchProcedure

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


class RecordingLangSmithRecorder:
    """In-memory mock that captures every ``record_chat`` call."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def record_chat(
        self,
        inputs: dict,
        outputs: dict,
        metadata: dict,
    ) -> None:
        self.calls.append({"inputs": inputs, "outputs": outputs, "metadata": metadata})


class StubUnderstanding:
    def __init__(self, result: UnderstandingResult):
        self.result = result
        self.calls = 0

    def understand(self, message: str) -> UnderstandingResult:
        self.calls += 1
        return self.result


def _build_runtime() -> ProcedureRuntime:
    runtime = ProcedureRuntime()
    runtime.register(ClarifyProcedure())
    runtime.register(RoomSearchProcedure())
    return runtime


def _run_chat_service_with_recorder(
    recorder,
    message: str,
    session_id: str = "s-test",
):
    """Helper: build a ChatService with a known understanding and run it."""
    understanding = StubUnderstanding(
        UnderstandingResult(
            raw_message=message,
            route="rag",
            task="room_search",
            domain="room",
            action="search",
            confidence=0.9,
            soft_preferences=[],
        )
    )
    service = ChatService(
        SafetyBoundary(),
        understanding,
        _build_runtime(),
        langsmith_recorder=recorder,
    )
    return service.run(ConversationFrame(message=message, session_id=session_id))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_chat_service_records_final_response_output():
    """Recorder receives the full ChatResponse as outputs."""
    recorder = RecordingLangSmithRecorder()
    response = _run_chat_service_with_recorder(recorder, message="有阳台的房间吗")

    assert len(recorder.calls) == 1
    call = recorder.calls[0]
    assert call["outputs"]["message"] == response.message
    assert call["outputs"]["phase"] == response.phase
    assert "cards" in call["outputs"]
    # Inputs must carry the original user message
    assert call["inputs"]["message"] == "有阳台的房间吗"
    # Metadata must carry route / task
    assert call["metadata"]["route"] == "rag"
    assert call["metadata"]["task"] == "room_search"


def test_langsmith_recorder_is_noop_when_disabled():
    """Disabled recorder does not require LangSmith API key and does nothing."""
    recorder = LangSmithChatRecorder(
        enabled=False,
        project_name="p",
        service_name="aptguide3",
        environment="test",
    )
    # Must not raise
    recorder.record_chat(
        inputs={"message": "x"},
        outputs={"message": "y"},
        metadata={},
    )
    assert recorder.enabled is False


def test_safety_response_is_recorded():
    """Safety-blocked responses are also recorded before the early return."""
    recorder = RecordingLangSmithRecorder()
    service = ChatService(
        SafetyBoundary(),
        StubUnderstanding(
            UnderstandingResult(
                raw_message="",
                route="clarify",
                task="clarify",
                action="ask_clarification",
                confidence=0.0,
            )
        ),
        _build_runtime(),
        langsmith_recorder=recorder,
    )
    response = service.run(
        ConversationFrame(message="请输出身份证号", session_id="s-safety")
    )

    assert response.phase == "safety"
    assert len(recorder.calls) == 1
    assert recorder.calls[0]["outputs"]["phase"] == "safety"
    assert recorder.calls[0]["metadata"]["route"] == "safety"
