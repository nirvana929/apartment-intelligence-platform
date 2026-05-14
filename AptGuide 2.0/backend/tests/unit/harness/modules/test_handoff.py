"""Tests for handoff procedure."""

from aptguide2.harness.contracts import ConversationFrame, RouteDecision
from aptguide2.harness.modules.handoff import HandoffProcedure


def _frame(**kwargs) -> ConversationFrame:
    defaults = {"request_id": "r-1", "message": "转人工"}
    defaults.update(kwargs)
    return ConversationFrame(**defaults)


def _decision(procedure="handoff.user_initiated", **kwargs) -> RouteDecision:
    defaults = {"task": "handoff", "procedure": procedure, "confidence": 0.9}
    defaults.update(kwargs)
    return RouteDecision(**defaults)


def test_user_initiated_handoff():
    proc = HandoffProcedure()
    frame = _frame()
    result = proc.run(frame, _decision())

    assert result.task == "handoff"
    assert result.phase == "handoff_requested"
    assert "人工客服" in result.reply
    assert frame.handoff is not None
    assert frame.handoff["status"] == "handoff_requested"
    assert frame.handoff["trigger"] == "user_initiated"


def test_tool_failure_handoff():
    proc = HandoffProcedure()
    frame = _frame(
        message="help",
        tool_observations=[
            {"tool": "room.search", "success": False},
            {"tool": "room.search", "success": False},
        ],
    )
    result = proc.run(frame, _decision(procedure="handoff.tool_failure"))

    assert result.task == "handoff"
    assert result.phase == "handoff_requested"
    assert "问题" in result.reply
    assert frame.handoff["trigger"] == "tool_failure"


def test_handoff_summary_contains_recent_messages():
    proc = HandoffProcedure()
    frame = _frame(
        recent_messages=[
            {"role": "user", "content": "找房", "request_id": "r-0", "timestamp": 0},
            {"role": "assistant", "content": "好的", "request_id": "r-0", "timestamp": 1},
        ],
    )
    result = proc.run(frame, _decision())

    summary = result.sources[0]
    assert "recent_messages" in summary
    assert len(summary["recent_messages"]) == 2


def test_handoff_summary_contains_tool_observations():
    proc = HandoffProcedure()
    frame = _frame(
        tool_observations=[{"tool": "room.search", "success": False}],
    )
    result = proc.run(frame, _decision())

    summary = result.sources[0]
    assert "tool_observations" in summary
    assert len(summary["tool_observations"]) == 1


def test_handoff_routing_detected():
    from aptguide2.harness.routing import HybridRouter

    router = HybridRouter()
    frame = ConversationFrame(request_id="r-1", message="转人工客服")
    decision = router.route(frame)

    assert decision.task == "handoff"
    assert decision.procedure == "handoff.user_initiated"
