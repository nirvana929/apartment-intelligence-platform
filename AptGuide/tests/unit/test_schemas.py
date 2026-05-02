from aptguide.schemas.request import ChatRequest
from aptguide.schemas.response import ChatResponse, Card


def test_chat_request():
    req = ChatRequest(session_id="test-001", message="押金怎么退？")
    assert req.session_id == "test-001"
    assert req.message == "押金怎么退？"
    assert req.context is None


def test_chat_request_with_context():
    req = ChatRequest(
        session_id="test-001",
        message="预约第一个",
        context={"last_recommendations": [3001, 3002]},
    )
    assert req.context == {"last_recommendations": [3001, 3002]}


def test_chat_response():
    resp = ChatResponse(
        session_id="test-001",
        request_id="req-uuid",
        intent="kb_qa",
        reply="根据规则...",
        cards=[],
        actions=[],
        pending_confirmation=None,
        sources=["KB-RULE-008"],
    )
    assert resp.intent == "kb_qa"
    assert len(resp.sources) == 1


def test_card():
    card = Card(
        type="room",
        room_id=3001,
        title="天河公寓 302",
        rent=2800,
        district="天河区",
        tags=["独卫", "朝南"],
    )
    assert card.type == "room"
    assert card.rent == 2800
