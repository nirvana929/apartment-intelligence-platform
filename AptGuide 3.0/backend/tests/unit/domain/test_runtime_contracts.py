from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.responses import ChatResponse


def test_conversation_frame_defaults():
    frame = ConversationFrame(message="你好", session_id="s-1")

    assert frame.message == "你好"
    assert frame.session_id == "s-1"
    assert frame.user_id is None
    assert frame.pending_action is None


def test_procedure_result_composes_chat_response_shape():
    result = ProcedureResult(
        message="请补充一下您的需求。",
        phase="clarify",
        metadata={"route": "clarify"},
    )
    response = ChatResponse.from_procedure_result(result)

    assert response.message == "请补充一下您的需求。"
    assert response.phase == "clarify"
    assert response.metadata["route"] == "clarify"
