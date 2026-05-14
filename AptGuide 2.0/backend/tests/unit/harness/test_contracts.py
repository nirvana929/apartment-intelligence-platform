import pytest
from pydantic import ValidationError

from aptguide2.harness.contracts import (
    AptGuideRequest,
    AptGuideResponse,
    ConversationFrame,
    ProcedureResult,
    RouteDecision,
    StageTrace,
)


def test_request_requires_request_id():
    req = AptGuideRequest(request_id="r-1", session_id="s-1", message="找房")
    assert req.request_id == "r-1"
    assert req.message == "找房"
    assert req.harness_version == "harness_v1"


def test_frame_defaults_are_isolated():
    f1 = ConversationFrame(request_id="r-1")
    f2 = ConversationFrame(request_id="r-2")
    f1.last_recommendations.append({"room_id": 1})
    assert f2.last_recommendations == []


def test_route_decision_confidence_bounds():
    with pytest.raises(ValidationError):
        RouteDecision(task="room_search", procedure="rag.room_search", confidence=1.5)


def test_procedure_result_defaults():
    result = ProcedureResult(task="capability", phase="idle", reply="我是租房助手")
    assert result.cards == []
    assert result.sources == []


def test_response_carries_trace_id():
    resp = AptGuideResponse(
        request_id="r-1",
        trace_id="t-1",
        reply="ok",
        phase="idle",
        domain_category="in_domain",
    )
    assert resp.trace_id == "t-1"


def test_stage_trace_defaults():
    stage = StageTrace(stage="routing", strategy="rule_v1")
    assert stage.errors == []
