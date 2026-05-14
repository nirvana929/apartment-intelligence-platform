import pytest
from pydantic import ValidationError

from aptguide2.harness.tools.contracts import (
    RoomSearchInput,
    ToolCallRequest,
    ToolCallResult,
    ToolDefinition,
)


def test_tool_definition_defaults():
    definition = ToolDefinition(
        name="room.search",
        backend="lease",
        permission="public",
        input_schema="RoomSearchInput",
        output_schema="RoomSearchOutput",
    )
    assert definition.requires_user is False
    assert definition.requires_confirmation is False
    assert definition.timeout_seconds == 5.0
    assert definition.retry.max_attempts == 1


def test_write_tool_requires_confirmation_metadata():
    definition = ToolDefinition(
        name="appointment.create",
        backend="lease",
        permission="user",
        input_schema="AppointmentCreateInput",
        output_schema="AppointmentCreateOutput",
        requires_user=True,
        requires_confirmation=True,
    )
    assert definition.requires_confirmation is True


def test_tool_call_request_carries_trace_context():
    req = ToolCallRequest(
        tool="room.search",
        request_id="r-1",
        trace_id="t-1",
        payload={"max_rent": 1800},
    )
    assert req.trace_id == "t-1"
    assert req.payload["max_rent"] == 1800


def test_tool_result_success_defaults():
    result = ToolCallResult.ok_result(
        tool="room.search",
        data={"rooms": []},
        backend="lease",
        latency_ms=1.2,
    )
    assert result.ok is True
    assert result.error is None
    assert result.metadata["result_count"] == 0


def test_health_result_uses_status_not_result_count():
    result = ToolCallResult.ok_result(
        tool="lease.health",
        data={"healthy": True},
        backend="lease",
        latency_ms=1.2,
        metadata={"status": "healthy"},
    )
    assert result.metadata["status"] == "healthy"
    assert "result_count" not in result.metadata


def test_tool_result_error_envelope():
    result = ToolCallResult.error_result(
        tool="room.search",
        code="TOOL_TIMEOUT",
        message="tool timed out",
        recoverable=True,
        backend="lease",
    )
    assert result.ok is False
    assert result.error.code == "TOOL_TIMEOUT"
    assert result.error.recoverable is True


def test_room_search_input_limit_bounds():
    with pytest.raises(ValidationError):
        RoomSearchInput(limit=0)
