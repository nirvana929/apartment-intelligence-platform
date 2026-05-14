"""Tests for lease workflow procedure."""

from aptguide2.harness.contracts import ConversationFrame, RouteDecision
from aptguide2.harness.modules.lease import LeaseWorkflowProcedure
from aptguide2.harness.tools.contracts import ToolCallResult


class CapturingRuntime:
    def __init__(self, result):
        self.result = result
        self.last_request = None

    def execute(self, request):
        self.last_request = request
        return self.result


def _decision() -> RouteDecision:
    return RouteDecision(
        task="lease",
        procedure="lease.workflow",
        confidence=0.9,
        domain_category="in_domain_task",
        reason="test",
    )


def test_lease_list_requires_user_id() -> None:
    proc = LeaseWorkflowProcedure()
    frame = ConversationFrame(request_id="r-1", session_id="s-1", user_id=None, message="我的租约")

    result = proc.run(frame, _decision(), tool_runtime=object())

    assert result.phase == "lease_auth_required"
    assert result.fallback_reason == "missing_user_id"


def test_lease_list_no_tool_runtime() -> None:
    proc = LeaseWorkflowProcedure()
    frame = ConversationFrame(request_id="r-1", session_id="s-1", user_id="u-1", message="我的租约")

    result = proc.run(frame, _decision(), tool_runtime=None)

    assert result.phase == "lease_tool_unavailable"
    assert result.fallback_reason == "tool_runtime_missing"


def test_lease_list_calls_tool_runtime() -> None:
    runtime = CapturingRuntime(
        ToolCallResult.ok_result(
            tool="lease.list_mine",
            data={"leases": [{"lease_id": "l-1", "status": "active"}]},
            backend="lease",
        )
    )
    proc = LeaseWorkflowProcedure()
    frame = ConversationFrame(request_id="r-1", session_id="s-1", user_id="u-1", message="我的租约")

    result = proc.run(frame, _decision(), tool_runtime=runtime)

    assert result.phase == "lease_list"
    assert result.cards[0]["lease_id"] == "l-1"
    assert runtime.last_request.tool == "lease.list_mine"


def test_lease_list_empty() -> None:
    runtime = CapturingRuntime(
        ToolCallResult.ok_result(
            tool="lease.list_mine",
            data={"leases": []},
            backend="lease",
        )
    )
    proc = LeaseWorkflowProcedure()
    frame = ConversationFrame(request_id="r-1", session_id="s-1", user_id="u-1", message="我的租约")

    result = proc.run(frame, _decision(), tool_runtime=runtime)

    assert result.phase == "lease_list_empty"
    assert result.cards == []


def test_lease_list_failure() -> None:
    runtime = CapturingRuntime(
        ToolCallResult.error_result(
            tool="lease.list_mine",
            code="UNKNOWN_TOOL_ERROR",
            message="backend down",
            backend="lease",
        )
    )
    proc = LeaseWorkflowProcedure()
    frame = ConversationFrame(request_id="r-1", session_id="s-1", user_id="u-1", message="我的租约")

    result = proc.run(frame, _decision(), tool_runtime=runtime)

    assert result.phase == "lease_list_failed"
    assert result.fallback_reason == "lease_list_failed"
