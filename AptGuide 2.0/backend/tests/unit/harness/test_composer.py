from aptguide2.harness.composer import ResponseComposer
from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision
from aptguide2.harness.trace import TraceRecorder


def test_composer_builds_response():
    frame = ConversationFrame(request_id="r-1", session_id="s-1", message="你能做什么")
    decision = RouteDecision(
        task="capability",
        procedure="capability.profile",
        confidence=0.9,
        domain_category="in_domain_capability",
    )
    result = ProcedureResult(task="capability", phase="idle", reply="我是租房助手")
    trace = TraceRecorder(trace_id="t-1", request_id="r-1", session_id="s-1").to_trace()

    response = ResponseComposer(include_trace=True).compose(frame, decision, result, trace)
    assert response.reply == "我是租房助手"
    assert response.trace_id == "t-1"
    assert response.domain_category == "in_domain_capability"
    assert response.trace is not None


def test_composer_can_hide_trace():
    frame = ConversationFrame(request_id="r-1", session_id="s-1")
    decision = RouteDecision(task="fallback", procedure="fallback.unknown", confidence=0.5)
    result = ProcedureResult(task="fallback", phase="boundary_declined", reply="暂时无法处理")
    trace = TraceRecorder(trace_id="t-1", request_id="r-1", session_id="s-1").to_trace()

    response = ResponseComposer(include_trace=False).compose(frame, decision, result, trace)
    assert response.trace is None


def test_composer_preserves_cards_actions_pending_and_standard_metadata():
    composer = ResponseComposer()
    frame = ConversationFrame(request_id="r-1", session_id="s-1", message="我的预约")
    decision = RouteDecision(
        task="appointment",
        procedure="appointment.workflow",
        confidence=0.9,
        domain_category="in_domain_task",
        reason="test",
    )
    result = ProcedureResult(
        task="appointment",
        phase="appointment_list",
        reply="您有1条预约记录。",
        cards=[{"type": "appointment_record", "appointment_id": "a-1"}],
        actions=[{"type": "cancel_appointment"}],
        pending_action={"type": "appointment.cancel"},
        sources=[{"title": "预约规则"}],
        metadata={"appointment_count": 1},
    )
    trace = TraceRecorder(trace_id="t-1", request_id="r-1", session_id="s-1").to_trace()

    response = composer.compose(frame, decision, result, trace)

    assert response.cards == result.cards
    assert response.actions == result.actions
    assert response.pending_action == result.pending_action
    assert response.sources == result.sources
    assert response.metadata["appointment_count"] == 1
    assert response.metadata["procedure"] == "appointment.workflow"
    assert response.metadata["task"] == "appointment"
    assert response.metadata["card_count"] == 1
    assert response.metadata["source_count"] == 1
    assert response.metadata["action_count"] == 1
    assert response.metadata["has_pending_action"] is True
