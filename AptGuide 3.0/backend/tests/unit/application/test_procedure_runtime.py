import pytest

from aptguide3.application.procedure_runtime import ProcedureNotFoundError, ProcedureRuntime
from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.procedures.clarify import ClarifyProcedure
from aptguide3.procedures.kb_qa import KbQaProcedure
from aptguide3.procedures.room_search import RoomSearchProcedure


def test_runtime_dispatches_clarify():
    runtime = ProcedureRuntime()
    runtime.register(ClarifyProcedure())
    frame = ConversationFrame(message="这个可以吗", session_id="s-1")
    understanding = UnderstandingResult(
        raw_message="这个可以吗",
        route="clarify",
        task="clarify",
        action="ask_clarification",
        confidence=0.0,
    )

    result = runtime.run(frame, understanding)

    assert result.phase == "clarify"


def test_runtime_dispatches_room_search_placeholder():
    runtime = ProcedureRuntime()
    runtime.register(RoomSearchProcedure())
    frame = ConversationFrame(message="有阳台的房间吗", session_id="s-1")
    understanding = UnderstandingResult(
        raw_message="有阳台的房间吗",
        route="rag",
        task="room_search",
        domain="room",
        action="search",
        confidence=0.9,
    )

    result = runtime.run(frame, understanding)

    assert result.phase == "room_search"


def test_runtime_dispatches_kb_qa_placeholder():
    runtime = ProcedureRuntime()
    runtime.register(KbQaProcedure())
    frame = ConversationFrame(message="照片是真的吗", session_id="s-1")
    understanding = UnderstandingResult(
        raw_message="照片是真的吗",
        route="rag",
        task="kb_qa",
        domain="policy",
        action="ask_policy",
        confidence=0.9,
    )

    result = runtime.run(frame, understanding)

    assert result.phase == "kb_qa"


def test_missing_procedure_raises():
    runtime = ProcedureRuntime()
    frame = ConversationFrame(message="x", session_id="s")
    understanding = UnderstandingResult(raw_message="x", route="rag", task="room_search", confidence=0.9)

    with pytest.raises(ProcedureNotFoundError):
        runtime.run(frame, understanding)
