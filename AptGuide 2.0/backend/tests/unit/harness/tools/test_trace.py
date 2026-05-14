from aptguide2.harness.tools.contracts import ToolCallRequest, ToolCallResult, ToolDefinition
from aptguide2.harness.tools.trace import redact_pii, summarize_tool_request, summarize_tool_result


def _definition(**kwargs):
    defaults = dict(
        name="room.search",
        backend="lease",
        permission="public",
        input_schema="RoomSearchInput",
        output_schema="RoomSearchOutput",
    )
    defaults.update(kwargs)
    return ToolDefinition(**defaults)


def test_summarize_success_result():
    result = ToolCallResult.ok_result(
        tool="room.search",
        data={"rooms": [{"id": 1}, {"id": 2}]},
        backend="lease",
        latency_ms=12.5,
    )
    summary = summarize_tool_result(result)
    assert summary["tool"] == "room.search"
    assert summary["ok"] is True
    assert summary["backend"] == "lease"
    assert summary["latency_ms"] == 12.5
    assert summary["result_count"] == 2


def test_summarize_health_result_uses_status():
    result = ToolCallResult.ok_result(
        tool="lease.health",
        data={"healthy": True},
        backend="lease",
        latency_ms=3.0,
        metadata={"status": "healthy"},
    )
    summary = summarize_tool_result(result)
    assert summary["status"] == "healthy"
    assert "result_count" not in summary


def test_summarize_error_result():
    result = ToolCallResult.error_result(
        tool="room.search",
        code="TOOL_TIMEOUT",
        message="timed out",
        recoverable=True,
        backend="lease",
    )
    summary = summarize_tool_result(result)
    assert summary["ok"] is False
    assert summary["error_code"] == "TOOL_TIMEOUT"
    assert summary["recoverable"] is True


def test_summarize_request_redacts_pii():
    request = ToolCallRequest(
        tool="room.search",
        request_id="r-1",
        trace_id="t-1",
        payload={"query": "番禺", "phone": "13800138000"},
    )
    definition = _definition()
    summary = summarize_tool_request(request, definition)
    assert summary["tool"] == "room.search"
    assert summary["trace_id"] == "t-1"
    assert "payload_keys" in summary
    assert "phone" in summary["payload_keys"]


def test_redact_pii_nested():
    data = {"user": {"phone": "123", "name": "test"}, "items": [{"id_card": "abc"}]}
    result = redact_pii(data)
    assert result["user"]["phone"] == "[REDACTED]"
    assert result["user"]["name"] == "test"
    assert result["items"][0]["id_card"] == "[REDACTED]"


def test_summary_never_contains_raw_pii():
    request = ToolCallRequest(
        tool="test",
        request_id="r-1",
        payload={"phone": "13800138000", "email": "test@example.com"},
    )
    definition = _definition()
    summary = summarize_tool_request(request, definition)
    summary_str = str(summary)
    assert "13800138000" not in summary_str
    assert "test@example.com" not in summary_str
